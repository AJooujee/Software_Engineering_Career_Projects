# ============================================================
# Build stage
# ============================================================

# Use a Java 21 JDK image to compile and test the application.
FROM eclipse-temurin:21-jdk AS builder

# Set the working directory inside the build container.
WORKDIR /workspace

# Copy Gradle Wrapper files first.
# Docker can reuse this layer when application code changes.
COPY gradlew .
COPY gradle ./gradle
COPY build.gradle .
COPY settings.gradle .

# Give the Linux Gradle Wrapper permission to execute.
RUN chmod +x ./gradlew

# Copy production and test source code.
COPY src ./src

# Compile the application and run all JUnit tests.
RUN ./gradlew clean build --no-daemon


# ============================================================
# Runtime stage
# ============================================================

# Use the smaller Java Runtime Environment for execution.
FROM eclipse-temurin:21-jre

# Create a non-root operating-system user.
# Running as non-root reduces container security risk.
RUN useradd \
    --create-home \
    --shell /usr/sbin/nologin \
    commandcontrol

# Set the runtime working directory.
WORKDIR /app

# Copy the application distribution created by Gradle.
COPY --from=builder \
    /workspace/build/distributions/secure-command-control-simulator-1.0.0.tar \
    /tmp/application.tar

# Extract the Gradle application distribution.
RUN tar -xf /tmp/application.tar \
    --strip-components=1 \
    -C /app \
    && rm /tmp/application.tar \
    && mkdir -p /app/logs \
    && chown -R commandcontrol:commandcontrol /app

# Run the application without root privileges.
USER commandcontrol

# Document the TCP port used by CommandServer.
EXPOSE 6060

# Start the Java command server.
ENTRYPOINT ["/app/bin/secure-command-control-simulator"]