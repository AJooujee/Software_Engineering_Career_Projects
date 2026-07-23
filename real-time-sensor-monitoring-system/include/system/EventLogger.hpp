#pragma once

// Standard library used for writing log files.
#include <fstream>

// Standard library used to protect file writes.
#include <mutex>

// Standard library used for log message text.
#include <string>


/**
 * Writes timestamped system events into a log file.
 */
class EventLogger
{
public:
    /**
     * Open or create the selected log file.
     */
    explicit EventLogger(
        const std::string& filePath
    );

    /**
     * Write one event into the log file.
     */
    void log(
        const std::string& level,
        const std::string& eventType,
        const std::string& message
    );

private:
    /**
     * Generate the current local timestamp.
     */
    static std::string createTimestamp();

    // Output stream used to append log records.
    std::ofstream logFile_;

    // Protect the log file if multiple threads write in the future.
    std::mutex logMutex_;
};