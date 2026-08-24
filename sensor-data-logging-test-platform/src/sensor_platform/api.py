"""REST API for sensor simulation, storage, and hardware testing."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from sensor_platform.analysis import FaultDetector
from sensor_platform.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from sensor_platform.hardware_testing import HardwareTestRunner
from sensor_platform.models import SensorReading, SensorType
from sensor_platform.repository import SensorReadingRepository
from sensor_platform.simulator import SensorSimulator


class SimulationRequest(BaseModel):
    """Configuration accepted by simulation and hardware-test endpoints."""

    count: int = Field(default=10, ge=1, le=1000)
    warning_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    fault_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    seed: int = 42


class SensorReadingResponse(BaseModel):
    """JSON representation of one analyzed sensor reading."""

    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    status: str

    @classmethod
    def from_domain(
        cls,
        reading: SensorReading,
    ) -> "SensorReadingResponse":
        """Convert a domain reading into an API response."""

        return cls(
            sensor_id=reading.sensor_id,
            sensor_type=reading.sensor_type.value,
            value=reading.value,
            unit=reading.unit,
            timestamp=reading.timestamp,
            status=reading.status.value,
        )


class HealthSummaryResponse(BaseModel):
    """Aggregated status counts returned by the API."""

    total_readings: int
    normal_count: int
    warning_count: int
    fault_count: int
    health_score: float


class SimulationResponse(BaseModel):
    """Response returned after generating and storing readings."""

    generated_count: int
    summary: HealthSummaryResponse
    readings: list[SensorReadingResponse]


@contextmanager
def open_repository(
    database_path: str | Path,
) -> Iterator[SensorReadingRepository]:
    """Open a database repository and always release its engine."""

    engine = create_database_engine(database_path)

    try:
        initialize_database(engine)
        yield SensorReadingRepository(
            create_session_factory(engine)
        )
    finally:
        engine.dispose()


def validate_rates(request: SimulationRequest) -> None:
    """Reject probabilities whose combined total exceeds 100 percent."""

    if request.warning_rate + request.fault_rate > 1:
        raise HTTPException(
            status_code=422,
            detail="warning_rate and fault_rate cannot total more than 1",
        )


def generate_analyzed_readings(
    request: SimulationRequest,
) -> tuple[list[SensorReading], HealthSummaryResponse]:
    """Generate readings for all sensor types and analyze their health."""

    validate_rates(request)
    raw_readings: list[SensorReading] = []

    for index, sensor_type in enumerate(SensorType):
        simulator = SensorSimulator(
            sensor_id=f"{sensor_type.value}-001",
            sensor_type=sensor_type,
            seed=request.seed + index,
        )
        raw_readings.extend(
            simulator.generate_batch(
                count=request.count,
                warning_rate=request.warning_rate,
                fault_rate=request.fault_rate,
            )
        )

    detector = FaultDetector()
    results = detector.analyze_many(raw_readings)
    summary = detector.summarize(results)

    readings = [result.reading for result in results]

    return readings, HealthSummaryResponse(
        total_readings=summary.total_readings,
        normal_count=summary.normal_count,
        warning_count=summary.warning_count,
        fault_count=summary.fault_count,
        health_score=summary.health_score,
    )


def create_app(
    database_path: str | Path = Path("data") / "sensor_data.db",
) -> FastAPI:
    """Create an API application connected to the selected database."""

    application = FastAPI(
        title="Sensor Data Logging & Hardware Test API",
        description=(
            "Generate, analyze, store, and test simulated hardware "
            "sensor readings."
        ),
        version="1.0.0",
    )

    @application.get("/health")
    def health_check() -> dict[str, str]:
        """Confirm that the API process is running."""

        return {"status": "healthy"}

    @application.post(
        "/api/v1/simulations",
        response_model=SimulationResponse,
        status_code=201,
    )
    def create_simulation(
        request: SimulationRequest,
    ) -> SimulationResponse:
        """Generate analyzed readings and save them to SQLite."""

        readings, summary = generate_analyzed_readings(request)

        with open_repository(database_path) as repository:
            repository.save_many(readings)

        return SimulationResponse(
            generated_count=len(readings),
            summary=summary,
            readings=[
                SensorReadingResponse.from_domain(reading)
                for reading in readings
            ],
        )

    @application.get(
        "/api/v1/readings",
        response_model=list[SensorReadingResponse],
    )
    def list_readings(
        limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    ) -> list[SensorReadingResponse]:
        """Return stored readings from oldest to newest."""

        with open_repository(database_path) as repository:
            readings = repository.list_all(limit=limit)

        return [
            SensorReadingResponse.from_domain(reading)
            for reading in readings
        ]

    @application.get(
        "/api/v1/summary",
        response_model=HealthSummaryResponse,
    )
    def get_summary() -> HealthSummaryResponse:
        """Calculate health metrics for every stored reading."""

        with open_repository(database_path) as repository:
            readings = repository.list_all()

        detector = FaultDetector()
        summary = detector.summarize(
            detector.analyze_many(readings)
        )

        return HealthSummaryResponse(
            total_readings=summary.total_readings,
            normal_count=summary.normal_count,
            warning_count=summary.warning_count,
            fault_count=summary.fault_count,
            health_score=summary.health_score,
        )

    @application.post("/api/v1/hardware-tests")
    def run_hardware_test(
        request: SimulationRequest,
    ) -> dict[str, object]:
        """Generate data and return an automated pass/fail report."""

        readings, _ = generate_analyzed_readings(request)
        report = HardwareTestRunner().run(readings)

        return report.to_dict()

    return application


# Uvicorn imports this application object when starting the API server.
app = create_app()
