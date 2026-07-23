#pragma once

#include "system/Fault.hpp"
#include "system/SensorReading.hpp"

// Standard library used for size values.
#include <cstddef>

// Standard library used for sensor identifiers and state names.
#include <string>

// Standard library used to track sensor health by sensor ID.
#include <unordered_map>


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
    // True when the sensor currently has an active fault.
    bool faulted{false};

    // Current fault severity for the sensor.
    FaultSeverity severity{FaultSeverity::None};
};


/**
 * Tracks active sensor faults and calculates the overall system state.
 */
class SystemStateManager
{
public:
    /**
     * Update health using a complete sensor reading.
     */
    void update(
        const SensorReading& reading,
        const Fault& fault
    );

    /**
     * Update health directly using a sensor identifier.
     *
     * This overload is used for timeout faults because no new
     * SensorReading exists when a sensor stops transmitting.
     */
    void update(
        const std::string& sensorId,
        const Fault& fault
    );

    /**
     * Return the current system operating state.
     */
    SystemState getState() const;

    /**
     * Return the number of currently faulted sensors.
     */
    std::size_t getActiveFaultCount() const;

    /**
     * Return the current state as readable text.
     */
    std::string getStateName() const;

private:
    /**
     * Recalculate the system state using all active faults.
     */
    void recalculateState();

    // Stores health information using sensor ID as the key.
    std::unordered_map<std::string, SensorHealth> sensorHealth_;

    // The system begins in normal operation.
    SystemState currentState_{SystemState::Normal};
};