#pragma once

// Standard library used for text descriptions.
#include <string>


/**
 * Describes the severity of a detected sensor fault.
 */
enum class FaultSeverity
{
    None,
    Warning,
    Critical
};


/**
 * Represents the result of evaluating one sensor reading.
 */
struct Fault
{
    // True when the reading violates a system rule.
    bool detected{false};

    // Severity assigned to the detected fault.
    FaultSeverity severity{FaultSeverity::None};

    // Short machine-readable fault category.
    std::string type{"NONE"};

    // Human-readable description of the fault.
    std::string message{"Sensor reading is within the acceptable range."};
};


/**
 * Convert a fault severity enum into readable text.
 */
inline std::string faultSeverityToString(
    const FaultSeverity severity
)
{
    switch (severity)
    {
        case FaultSeverity::Warning:
            return "WARNING";

        case FaultSeverity::Critical:
            return "CRITICAL";

        case FaultSeverity::None:
        default:
            return "NONE";
    }
}