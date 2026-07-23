// Include the production class being tested.
#include "system/FaultDetector.hpp"

// Include the GoogleTest testing framework.
#include <gtest/gtest.h>


/**
 * Verify that a normal temperature does not create a fault.
 */
TEST(FaultDetectorTests, AcceptsNormalTemperature)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "TEMP-01",
        "TEMPERATURE",
        "2026-07-23T12:00:00Z",
        72.0,
        "F",
        1
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_FALSE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::None);
    EXPECT_EQ(fault.type, "NONE");
}


/**
 * Verify that a warning-level temperature is detected.
 */
TEST(FaultDetectorTests, DetectsTemperatureWarning)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "TEMP-01",
        "TEMPERATURE",
        "2026-07-23T12:00:00Z",
        90.0,
        "F",
        2
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_TRUE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::Warning);
    EXPECT_EQ(fault.type, "TEMPERATURE_OUT_OF_RANGE");
}


/**
 * Verify that a critical temperature is detected.
 */
TEST(FaultDetectorTests, DetectsCriticalTemperature)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "TEMP-01",
        "TEMPERATURE",
        "2026-07-23T12:00:00Z",
        130.0,
        "F",
        3
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_TRUE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::Critical);
    EXPECT_EQ(fault.type, "CRITICAL_TEMPERATURE");
}


/**
 * Verify that a normal voltage does not create a fault.
 */
TEST(FaultDetectorTests, AcceptsNormalVoltage)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "VOLT-01",
        "VOLTAGE",
        "2026-07-23T12:00:00Z",
        12.2,
        "V",
        4
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_FALSE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::None);
}


/**
 * Verify that a warning-level voltage is detected.
 */
TEST(FaultDetectorTests, DetectsVoltageWarning)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "VOLT-01",
        "VOLTAGE",
        "2026-07-23T12:00:00Z",
        13.2,
        "V",
        5
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_TRUE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::Warning);
    EXPECT_EQ(fault.type, "VOLTAGE_OUT_OF_RANGE");
}


/**
 * Verify that a critical voltage is detected.
 */
TEST(FaultDetectorTests, DetectsCriticalVoltage)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "VOLT-01",
        "VOLTAGE",
        "2026-07-23T12:00:00Z",
        15.2,
        "V",
        6
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_TRUE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::Critical);
    EXPECT_EQ(fault.type, "CRITICAL_VOLTAGE");
}


/**
 * Verify that position values outside the simulated boundary are rejected.
 */
TEST(FaultDetectorTests, DetectsPositionOutsideBoundary)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "POS-01",
        "POSITION",
        "2026-07-23T12:00:00Z",
        120.0,
        "unit",
        7
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_TRUE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::Warning);
    EXPECT_EQ(fault.type, "POSITION_OUT_OF_RANGE");
}


/**
 * Verify that motion accepts only binary values.
 */
TEST(FaultDetectorTests, DetectsInvalidMotionState)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "MOTION-01",
        "MOTION",
        "2026-07-23T12:00:00Z",
        2.0,
        "state",
        8
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_TRUE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::Warning);
    EXPECT_EQ(fault.type, "INVALID_MOTION_STATE");
}


/**
 * Verify that unsupported sensor types are rejected.
 */
TEST(FaultDetectorTests, RejectsUnknownSensorType)
{
    const FaultDetector detector{};

    const SensorReading reading{
        "UNKNOWN-01",
        "PRESSURE",
        "2026-07-23T12:00:00Z",
        10.0,
        "psi",
        9
    };

    const Fault fault{
        detector.analyze(reading)
    };

    EXPECT_TRUE(fault.detected);
    EXPECT_EQ(fault.severity, FaultSeverity::Warning);
    EXPECT_EQ(fault.type, "UNKNOWN_SENSOR_TYPE");
}