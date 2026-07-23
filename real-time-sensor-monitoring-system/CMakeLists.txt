# Require a modern version of CMake.
cmake_minimum_required(VERSION 3.20)

# Define the project name, version, and programming language.
project(
    RealTimeSensorMonitoringSystem
    VERSION 1.0.0
    DESCRIPTION "Real-time multi-sensor monitoring and fault-tolerant system"
    LANGUAGES CXX
)

# Require the C++17 language standard.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Disable compiler-specific C++ extensions.
set(CMAKE_CXX_EXTENSIONS OFF)

# Load CMake's dependency-download module.
include(FetchContent)

# Download the nlohmann/json library during CMake configuration.
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
)

# Make the JSON library available to the current project.
FetchContent_MakeAvailable(
    nlohmann_json
)

# Create the main sensor monitoring executable.
add_executable(
    sensor_monitor
    src/main.cpp
    src/FaultDetector.cpp
    src/SensorMessageParser.cpp
    src/SystemStateManager.cpp
)

# Allow the source files to include project header files.
target_include_directories(
    sensor_monitor
    PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)

# Link the JSON library to the executable.
target_link_libraries(
    sensor_monitor
    PRIVATE
    nlohmann_json::nlohmann_json
)

# Windows TCP networking requires the Winsock library.
if(WIN32)
    target_link_libraries(
        sensor_monitor
        PRIVATE
        ws2_32
    )
endif()

# Enable strict compiler warnings.
if(MSVC)
    target_compile_options(
        sensor_monitor
        PRIVATE
        /W4
        /permissive-
    )
else()
    target_compile_options(
        sensor_monitor
        PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
endif()