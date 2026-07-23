#include "system/SensorMessageParser.hpp"

// Third-party JSON library downloaded through CMake.
#include <nlohmann/json.hpp>

// Standard library used for exceptions.
#include <stdexcept>

// Standard library used for readable error messages.
#include <string>


SensorReading SensorMessageParser::parse(
    const std::string& jsonMessage
)
{
    try
    {
        // Convert the incoming JSON text into a JSON object.
        const nlohmann::json parsedMessage{
            nlohmann::json::parse(jsonMessage)
        };

        // Verify that every required field is present.
        const char* requiredFields[] = {
            "sensor_id",
            "sensor_type",
            "timestamp",
            "value",
            "unit",
            "sequence_number"
        };

        for (const char* fieldName : requiredFields)
        {
            if (!parsedMessage.contains(fieldName))
            {
                throw std::runtime_error(
                    std::string{"Missing required field: "} +
                    fieldName
                );
            }
        }

        // Verify that text fields contain strings.
        if (!parsedMessage.at("sensor_id").is_string() ||
            !parsedMessage.at("sensor_type").is_string() ||
            !parsedMessage.at("timestamp").is_string() ||
            !parsedMessage.at("unit").is_string())
        {
            throw std::runtime_error(
                "One or more text fields contain an invalid type."
            );
        }

        // Verify that the sensor value is numeric.
        if (!parsedMessage.at("value").is_number())
        {
            throw std::runtime_error(
                "The value field must contain a number."
            );
        }

        // Verify that the sequence number is an unsigned integer.
        if (!parsedMessage.at("sequence_number").is_number_unsigned() &&
            !parsedMessage.at("sequence_number").is_number_integer())
        {
            throw std::runtime_error(
                "The sequence_number field must contain an integer."
            );
        }

        SensorReading reading{};

        // Copy validated JSON fields into the C++ data structure.
        reading.sensorId =
            parsedMessage.at("sensor_id").get<std::string>();

        reading.sensorType =
            parsedMessage.at("sensor_type").get<std::string>();

        reading.timestamp =
            parsedMessage.at("timestamp").get<std::string>();

        reading.value =
            parsedMessage.at("value").get<double>();

        reading.unit =
            parsedMessage.at("unit").get<std::string>();

        reading.sequenceNumber =
            parsedMessage.at("sequence_number").get<std::uint64_t>();

        // Reject empty identifiers and sensor types.
        if (reading.sensorId.empty())
        {
            throw std::runtime_error(
                "The sensor_id field cannot be empty."
            );
        }

        if (reading.sensorType.empty())
        {
            throw std::runtime_error(
                "The sensor_type field cannot be empty."
            );
        }

        return reading;
    }
    catch (const nlohmann::json::exception& error)
    {
        throw std::runtime_error(
            std::string{"Invalid JSON message: "} +
            error.what()
        );
    }
}