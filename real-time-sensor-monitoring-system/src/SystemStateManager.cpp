#include "system/SystemStateManager.hpp"


void SystemStateManager::update(
    const SensorReading& reading,
    const Fault& fault
)
{
    // Replace the previous status for this sensor with its newest result.
    sensorHealth_[reading.sensorId] = {
        fault.detected,
        fault.severity
    };

    // Recalculate the overall state after every sensor update.
    recalculateState();
}


SystemState SystemStateManager::getState() const
{
    return currentState_;
}


std::size_t SystemStateManager::getActiveFaultCount() const
{
    std::size_t activeFaultCount{0};

    for (const auto& sensorEntry : sensorHealth_)
    {
        if (sensorEntry.second.faulted)
        {
            ++activeFaultCount;
        }
    }

    return activeFaultCount;
}


std::string SystemStateManager::getStateName() const
{
    switch (currentState_)
    {
        case SystemState::Degraded:
            return "DEGRADED";

        case SystemState::SafeMode:
            return "SAFE_MODE";

        case SystemState::Normal:
        default:
            return "NORMAL";
    }
}


void SystemStateManager::recalculateState()
{
    std::size_t activeFaultCount{0};
    bool criticalFaultDetected{false};

    for (const auto& sensorEntry : sensorHealth_)
    {
        const SensorHealth& health{
            sensorEntry.second
        };

        if (!health.faulted)
        {
            continue;
        }

        ++activeFaultCount;

        if (health.severity == FaultSeverity::Critical)
        {
            criticalFaultDetected = true;
        }
    }

    // A critical fault or two simultaneous faults triggers safe mode.
    if (criticalFaultDetected || activeFaultCount >= 2)
    {
        currentState_ = SystemState::SafeMode;
        return;
    }

    // One warning-level fault produces degraded operation.
    if (activeFaultCount == 1)
    {
        currentState_ = SystemState::Degraded;
        return;
    }

    // No active faults means normal operation.
    currentState_ = SystemState::Normal;
}