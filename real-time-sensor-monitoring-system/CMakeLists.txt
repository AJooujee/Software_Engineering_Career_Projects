cmake_minimum_required(VERSION 3.20)

project(
    RealTimeSensorMonitoringSystem
    VERSION 1.0.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(
    sensor_monitor
    src/main.cpp
)

target_include_directories(
    sensor_monitor
    PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)

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