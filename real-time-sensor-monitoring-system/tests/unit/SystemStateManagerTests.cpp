// Include the production state manager being tested.
#include "system/SystemStateManager.hpp"

// Include the GoogleTest testing framework.
#include <gtest/gtest.h>


/**
 * Verify that the system begins in NORMAL state.
 */
TEST(SystemStateManagerTests, StartsInNormalState)
{
    const SystemStateManager manager{};

    EXPECT_EQ(manager.getState(), SystemState::Normal);
    EXPECT_EQ(manager.getStateName(), "NORMAL");
    EXPECT_EQ(manager.getActiveFaultCount(), 0U);
}


/**
 * Verify that one warning-level fault causes DEGRADED state.
 */
TEST(SystemStateManagerTests, OneWarningCausesDegradedState)
{
    SystemStateManager manager{};

    const Fault warningFault{
        true,
        FaultSeverity::Warning,
        "TEMPERATURE_OUT_OF_RANGE",
        "Temperature warning."
    };

    manager.update(
        "TEMP-01",
        warningFault
    );

    EXPECT_EQ(manager.getState(), SystemState::Degraded);
    EXPECT_EQ(manager.getStateName(), "DEGRADED");
    EXPECT_EQ(manager.getActiveFaultCount(), 1U);
}


/**
 * Verify that one critical fault causes SAFE_MODE.
 */
TEST(SystemStateManagerTests, OneCriticalFaultCausesSafeMode)
{
    SystemStateManager manager{};

    const Fault criticalFault{
        true,
        FaultSeverity::Critical,
        "CRITICAL_TEMPERATURE",
        "Critical temperature."
    };

    manager.update(
        "TEMP-01",
        criticalFault
    );

    EXPECT_EQ(manager.getState(), SystemState::SafeMode);
    EXPECT_EQ(manager.getStateName(), "SAFE_MODE");
    EXPECT_EQ(manager.getActiveFaultCount(), 1U);
}


/**
 * Verify that two warning-level faults cause SAFE_MODE.
 */
TEST(SystemStateManagerTests, TwoWarningsCauseSafeMode)
{
    SystemStateManager manager{};

    const Fault warningFault{
        true,
        FaultSeverity::Warning,
        "OUT_OF_RANGE",
        "Warning-level fault."
    };

    manager.update(
        "TEMP-01",
        warningFault
    );

    EXPECT_EQ(manager.getState(), SystemState::Degraded);

    manager.update(
        "VOLT-01",
        warningFault
    );

    EXPECT_EQ(manager.getState(), SystemState::SafeMode);
    EXPECT_EQ(manager.getActiveFaultCount(), 2U);
}


/**
 * Verify that clearing a fault returns the system to NORMAL.
 */
TEST(SystemStateManagerTests, ClearingFaultReturnsToNormal)
{
    SystemStateManager manager{};

    const Fault warningFault{
        true,
        FaultSeverity::Warning,
        "OUT_OF_RANGE",
        "Warning-level fault."
    };

    const Fault clearedFault{};

    manager.update(
        "TEMP-01",
        warningFault
    );

    EXPECT_EQ(manager.getState(), SystemState::Degraded);

    manager.update(
        "TEMP-01",
        clearedFault
    );

    EXPECT_EQ(manager.getState(), SystemState::Normal);
    EXPECT_EQ(manager.getStateName(), "NORMAL");
    EXPECT_EQ(manager.getActiveFaultCount(), 0U);
}


/**
 * Verify that clearing one of two faults moves SAFE_MODE to DEGRADED.
 */
TEST(SystemStateManagerTests, ClearingOneOfTwoFaultsCausesDegradedState)
{
    SystemStateManager manager{};

    const Fault warningFault{
        true,
        FaultSeverity::Warning,
        "OUT_OF_RANGE",
        "Warning-level fault."
    };

    const Fault clearedFault{};

    manager.update(
        "TEMP-01",
        warningFault
    );

    manager.update(
        "VOLT-01",
        warningFault
    );

    EXPECT_EQ(manager.getState(), SystemState::SafeMode);

    manager.update(
        "TEMP-01",
        clearedFault
    );

    EXPECT_EQ(manager.getState(), SystemState::Degraded);
    EXPECT_EQ(manager.getActiveFaultCount(), 1U);
}