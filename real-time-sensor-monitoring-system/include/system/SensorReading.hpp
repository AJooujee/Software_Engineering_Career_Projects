#pragma once

// Standard library used for fixed-width integer types.
#include <cstdint>

// Standard library used for text fields.
#include <string>


/**
 * Represents one validated sensor message received from Python.
 */
struct SensorReading
{
    // Unique sensor identifier such as TEMP-01.
    std::string sensorId;

    // Sensor category such as TEMPERATURE or VOLTAGE.
    std::string sensorType;

    // UTC timestamp supplied by the Python simulator.
    std::string timestamp;

    // Numeric value produced by the sensor.
    double value{0.0};

    // Unit associated with the value.
    std::string unit;

    // Increasing number used to verify message ordering.
    std::uint64_t sequenceNumber{0};
};