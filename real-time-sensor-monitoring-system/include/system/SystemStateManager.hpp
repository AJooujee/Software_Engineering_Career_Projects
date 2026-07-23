#pragma once

#include "system/Fault.hpp"
#include "system/SensorReading.hpp"

// Standard library used to track each sensor's current health.
#include <unordered_map>

// Standard library used for readable state names.
#include <string>


/**
 * Represents the operating state of the monitoring system.
 */
enum class SystemState
{
    Normal,
    Degraded,
    SafeMode
};


/**
 * Stores the current fault condition for one sensor.
 */
struct SensorHealth
{
    bool faulted{false};
    FaultSeverity severity{FaultSeverity::None};
};


/**
 * Tracks active faults and determines the overall system state.
 */
class SystemStateManager
{
public:
    /**
     * Update the stored health condition for one sensor.
     */
    void update(
        const SensorReading& reading,
        const Fault& fault
    );

    /**
     * Return the current system operating state.
     */
    SystemState getState() const;

    /**
     * Return the number of sensors currently reporting faults.
     */
    std::size_t getActiveFaultCount() const;

    /**
     * Convert the current system state into readable text.
     */
    std::string getStateName() const;

private:
    /**
     * Recalculate the system state from all active sensor faults.
     */
    void recalculateState();

    // Stores fault information using the sensor ID as the key.
    std::unordered_map<std::string, SensorHealth> sensorHealth_;

    // System begins in normal operation.
    SystemState currentState_{SystemState::Normal};
};