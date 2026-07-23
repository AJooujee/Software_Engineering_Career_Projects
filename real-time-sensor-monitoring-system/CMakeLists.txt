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

# Enable CTest support for automated testing.
include(CTest)

# Load CMake's dependency-management module.
include(FetchContent)

# Download the nlohmann JSON library during configuration.
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
)

# Download GoogleTest during configuration.
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.17.0
)

# Prevent GoogleTest from changing the MSVC runtime-library selection.
set(
    gtest_force_shared_crt
    ON
    CACHE BOOL
    ""
    FORCE
)

# Make both dependencies available to this project.
FetchContent_MakeAvailable(
    nlohmann_json
    googletest
)

# Build reusable business logic as a static library.
#
# This allows both the application and tests to use the same
# production implementations without duplicating source files.
add_library(
    sensor_core
    STATIC
    src/EventLogger.cpp
    src/FaultDetector.cpp
    src/SensorMessageParser.cpp
    src/SystemStateManager.cpp
)

# Expose project headers to targets that link sensor_core.
target_include_directories(
    sensor_core
    PUBLIC
    ${PROJECT_SOURCE_DIR}/include
)

# Link JSON parsing support into the reusable core library.
target_link_libraries(
    sensor_core
    PUBLIC
    nlohmann_json::nlohmann_json
)

# Create the TCP monitoring application.
add_executable(
    sensor_monitor
    src/main.cpp
)

# Link the reusable production logic into the application.
target_link_libraries(
    sensor_monitor
    PRIVATE
    sensor_core
)

# Windows TCP networking requires the Winsock library.
if(WIN32)
    target_link_libraries(
        sensor_monitor
        PRIVATE
        ws2_32
    )
endif()

# Create the unit-test executable.
add_executable(
    sensor_tests
    tests/unit/FaultDetectorTests.cpp
    tests/unit/SensorMessageParserTests.cpp
    tests/unit/SystemStateManagerTests.cpp
)

# Link production code and GoogleTest into the test executable.
target_link_libraries(
    sensor_tests
    PRIVATE
    sensor_core
    GTest::gtest_main
)

# Apply strict warnings to production targets.
if(MSVC)
    target_compile_options(
        sensor_core
        PRIVATE
        /W4
        /permissive-
    )

    target_compile_options(
        sensor_monitor
        PRIVATE
        /W4
        /permissive-
    )
else()
    target_compile_options(
        sensor_core
        PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )

    target_compile_options(
        sensor_monitor
        PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
endif()

# Register every GoogleTest test case with CTest.
include(GoogleTest)

gtest_discover_tests(
    sensor_tests
)