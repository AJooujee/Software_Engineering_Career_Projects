#pragma once

#include "system/SensorReading.hpp"

// Standard library used for the incoming JSON message.
#include <string>


/**
 * Converts JSON text received through TCP into a SensorReading.
 */
class SensorMessageParser
{
public:
    /**
     * Parse and validate one JSON sensor message.
     *
     * Throws std::runtime_error when a required field is missing,
     * has an incorrect type, or contains an invalid value.
     */
    static SensorReading parse(
        const std::string& jsonMessage
    );
};