#pragma once

#include "system/Fault.hpp"
#include "system/SensorReading.hpp"


/**
 * Evaluates validated sensor readings against safety limits.
 */
class FaultDetector
{
public:
    /**
     * Analyze one sensor reading and return its fault status.
     */
    Fault analyze(
        const SensorReading& reading
    ) const;

private:
    /**
     * Evaluate a temperature reading.
     */
    static Fault analyzeTemperature(
        double value
    );

    /**
     * Evaluate a voltage reading.
     */
    static Fault analyzeVoltage(
        double value
    );

    /**
     * Evaluate a position reading.
     */
    static Fault analyzePosition(
        double value
    );

    /**
     * Evaluate a binary motion reading.
     */
    static Fault analyzeMotion(
        double value
    );
};