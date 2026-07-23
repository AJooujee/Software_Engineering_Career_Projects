#include "system/EventLogger.hpp"

// Standard library used for date and time values.
#include <chrono>

// Standard library used for local time conversion.
#include <ctime>

// Standard library used to create the log directory automatically.
#include <filesystem>

// Standard library used for timestamp formatting.
#include <iomanip>

// Standard library used for formatted strings.
#include <sstream>

// Standard library used for exceptions.
#include <stdexcept>


EventLogger::EventLogger(
    const std::string& filePath
)
{
    // Convert the supplied file path into a filesystem path.
    const std::filesystem::path logPath{
        filePath
    };

    // Extract the parent directory, such as "logs".
    const std::filesystem::path parentDirectory{
        logPath.parent_path()
    };

    // Create the parent directory when it does not already exist.
    if (!parentDirectory.empty())
    {
        std::error_code directoryError;

        std::filesystem::create_directories(
            parentDirectory,
            directoryError
        );

        if (directoryError)
        {
            throw std::runtime_error(
                "Failed to create the log directory: " +
                directoryError.message()
            );
        }
    }

    // Open the log file in append mode so previous events are preserved.
    logFile_.open(
        logPath,
        std::ios::out | std::ios::app
    );

    if (!logFile_.is_open())
    {
        throw std::runtime_error(
            "Failed to open the system event log: " +
            logPath.string()
        );
    }
}


void EventLogger::log(
    const std::string& level,
    const std::string& eventType,
    const std::string& message
)
{
    // Ensure only one operation writes to the file at a time.
    const std::lock_guard<std::mutex> lock{
        logMutex_
    };

    logFile_
        << createTimestamp()
        << " | "
        << level
        << " | "
        << eventType
        << " | "
        << message
        << '\n';

    // Write the event immediately instead of waiting for program exit.
    logFile_.flush();
}


std::string EventLogger::createTimestamp()
{
    // Get the current system time.
    const auto currentTime{
        std::chrono::system_clock::now()
    };

    // Convert the time point into a C-style time value.
    const std::time_t currentTimeValue{
        std::chrono::system_clock::to_time_t(
            currentTime
        )
    };

    std::tm localTime{};

#ifdef _WIN32
    // Windows uses localtime_s with destination first.
    localtime_s(
        &localTime,
        &currentTimeValue
    );
#else
    // Linux and UNIX use localtime_r.
    localtime_r(
        &currentTimeValue,
        &localTime
    );
#endif

    std::ostringstream timestampStream;

    // Format the timestamp into a readable date and time.
    timestampStream
        << std::put_time(
            &localTime,
            "%Y-%m-%d %H:%M:%S"
        );

    return timestampStream.str();
}