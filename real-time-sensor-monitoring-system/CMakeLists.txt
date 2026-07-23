# Require a modern version of CMake.
cmake_minimum_required(VERSION 3.20)

# Define the project name, version, description, and language.
project(
    RealTimeSensorMonitoringSystem
    VERSION 1.0.0
    DESCRIPTION "Real-time multi-sensor monitoring and fault-tolerant system"
    LANGUAGES CXX
)

# Require the C++17 language standard.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Disable compiler-specific language extensions.
set(CMAKE_CXX_EXTENSIONS OFF)

# Create the main executable from the C++ source file.
add_executable(
    sensor_monitor
    src/main.cpp
)

# Allow source files to include headers from the include directory.
target_include_directories(
    sensor_monitor
    PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)

# Windows socket programming requires the Winsock library.
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