// Include the production parser being tested.
#include "system/SensorMessageParser.hpp"

// Include the GoogleTest testing framework.
#include <gtest/gtest.h>

// Include standard exceptions for EXPECT_THROW.
#include <stdexcept>


/**
 * Verify that a complete valid JSON message is parsed correctly.
 */
TEST(SensorMessageParserTests, ParsesValidSensorMessage)
{
    const std::string jsonMessage{
        R"({
            "sensor_id": "TEMP-01",
            "sensor_type": "TEMPERATURE",
            "timestamp": "2026-07-23T12:00:00Z",
            "value": 72.5,
            "unit": "F",
            "sequence_number": 42
        })"
    };

    const SensorReading reading{
        SensorMessageParser::parse(jsonMessage)
    };

    EXPECT_EQ(reading.sensorId, "TEMP-01");
    EXPECT_EQ(reading.sensorType, "TEMPERATURE");
    EXPECT_EQ(reading.timestamp, "2026-07-23T12:00:00Z");
    EXPECT_DOUBLE_EQ(reading.value, 72.5);
    EXPECT_EQ(reading.unit, "F");
    EXPECT_EQ(reading.sequenceNumber, 42U);
}


/**
 * Verify that malformed JSON is rejected.
 */
TEST(SensorMessageParserTests, RejectsMalformedJson)
{
    const std::string jsonMessage{
        R"({"sensor_id": "TEMP-01",)"
    };

    EXPECT_THROW(
        SensorMessageParser::parse(jsonMessage),
        std::runtime_error
    );
}


/**
 * Verify that a missing required field is rejected.
 */
TEST(SensorMessageParserTests, RejectsMissingSensorId)
{
    const std::string jsonMessage{
        R"({
            "sensor_type": "TEMPERATURE",
            "timestamp": "2026-07-23T12:00:00Z",
            "value": 72.5,
            "unit": "F",
            "sequence_number": 1
        })"
    };

    EXPECT_THROW(
        SensorMessageParser::parse(jsonMessage),
        std::runtime_error
    );
}


/**
 * Verify that a nonnumeric sensor value is rejected.
 */
TEST(SensorMessageParserTests, RejectsInvalidValueType)
{
    const std::string jsonMessage{
        R"({
            "sensor_id": "TEMP-01",
            "sensor_type": "TEMPERATURE",
            "timestamp": "2026-07-23T12:00:00Z",
            "value": "high",
            "unit": "F",
            "sequence_number": 1
        })"
    };

    EXPECT_THROW(
        SensorMessageParser::parse(jsonMessage),
        std::runtime_error
    );
}


/**
 * Verify that an invalid sequence-number type is rejected.
 */
TEST(SensorMessageParserTests, RejectsInvalidSequenceNumberType)
{
    const std::string jsonMessage{
        R"({
            "sensor_id": "TEMP-01",
            "sensor_type": "TEMPERATURE",
            "timestamp": "2026-07-23T12:00:00Z",
            "value": 72.5,
            "unit": "F",
            "sequence_number": "one"
        })"
    };

    EXPECT_THROW(
        SensorMessageParser::parse(jsonMessage),
        std::runtime_error
    );
}


/**
 * Verify that an empty sensor identifier is rejected.
 */
TEST(SensorMessageParserTests, RejectsEmptySensorId)
{
    const std::string jsonMessage{
        R"({
            "sensor_id": "",
            "sensor_type": "TEMPERATURE",
            "timestamp": "2026-07-23T12:00:00Z",
            "value": 72.5,
            "unit": "F",
            "sequence_number": 1
        })"
    };

    EXPECT_THROW(
        SensorMessageParser::parse(jsonMessage),
        std::runtime_error
    );
}