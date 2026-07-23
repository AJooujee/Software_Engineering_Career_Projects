#include "system/FaultDetector.hpp"

// Standard library used for formatted values in fault messages.
#include <string>


Fault FaultDetector::analyze(
    const SensorReading& reading
) const
{
    if (reading.sensorType == "TEMPERATURE")
    {
        return analyzeTemperature(reading.value);
    }

    if (reading.sensorType == "VOLTAGE")
    {
        return analyzeVoltage(reading.value);
    }

    if (reading.sensorType == "POSITION")
    {
        return analyzePosition(reading.value);
    }

    if (reading.sensorType == "MOTION")
    {
        return analyzeMotion(reading.value);
    }

    // Unknown sensor types are rejected as warning-level faults.
    return {
        true,
        FaultSeverity::Warning,
        "UNKNOWN_SENSOR_TYPE",
        "The system received an unsupported sensor type."
    };
}


Fault FaultDetector::analyzeTemperature(
    const double value
)
{
    // Extreme temperatures are classified as critical.
    if (value < 32.0 || value > 120.0)
    {
        return {
            true,
            FaultSeverity::Critical,
            "CRITICAL_TEMPERATURE",
            "Temperature exceeded the critical safety limit."
        };
    }

    // Temperatures outside the normal operating range are warnings.
    if (value < 65.0 || value > 85.0)
    {
        return {
            true,
            FaultSeverity::Warning,
            "TEMPERATURE_OUT_OF_RANGE",
            "Temperature is outside the normal operating range."
        };
    }

    return {};
}


Fault FaultDetector::analyzeVoltage(
    const double value
)
{
    // Extreme voltage values can threaten the entire system.
    if (value < 10.0 || value > 14.5)
    {
        return {
            true,
            FaultSeverity::Critical,
            "CRITICAL_VOLTAGE",
            "Voltage exceeded the critical safety limit."
        };
    }

    // Values outside the expected operating range produce warnings.
    if (value < 11.5 || value > 12.8)
    {
        return {
            true,
            FaultSeverity::Warning,
            "VOLTAGE_OUT_OF_RANGE",
            "Voltage is outside the normal operating range."
        };
    }

    return {};
}


Fault FaultDetector::analyzePosition(
    const double value
)
{
    // Position must remain within the simulated physical boundary.
    if (value < 0.0 || value > 100.0)
    {
        return {
            true,
            FaultSeverity::Warning,
            "POSITION_OUT_OF_RANGE",
            "Position is outside the permitted boundary."
        };
    }

    return {};
}


Fault FaultDetector::analyzeMotion(
    const double value
)
{
    // Motion is represented by only two valid states: 0 or 1.
    if (value != 0.0 && value != 1.0)
    {
        return {
            true,
            FaultSeverity::Warning,
            "INVALID_MOTION_STATE",
            "Motion value must be either 0 or 1."
        };
    }

    return {};
}