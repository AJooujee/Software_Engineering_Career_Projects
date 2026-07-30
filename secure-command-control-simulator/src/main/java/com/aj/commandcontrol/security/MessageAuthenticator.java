package com.aj.commandcontrol.security;

import com.aj.commandcontrol.model.CommandMessage;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Objects;

/**
 * Verifies HMAC-SHA256 command signatures.
 */
public final class MessageAuthenticator {

    // Environment variable used to load the shared secret.
    public static final String SECRET_ENVIRONMENT_VARIABLE =
        "COMMAND_CONTROL_SHARED_SECRET";

    // Standard Java cryptographic algorithm name.
    private static final String HMAC_ALGORITHM =
        "HmacSHA256";

    // Secret bytes used by the HMAC algorithm.
    private final byte[] secretBytes;

    // Serializer configured to sort payload map keys.
    private final ObjectMapper objectMapper;

    /**
     * Create an authenticator using a supplied shared secret.
     *
     * @param sharedSecret secret shared with the Python control station
     */
    public MessageAuthenticator(
        final String sharedSecret
    ) {
        if (sharedSecret == null
            || sharedSecret.isBlank()) {
            throw new IllegalArgumentException(
                "The command-control shared secret cannot be blank."
            );
        }

        // Require a reasonable minimum secret size for development.
        if (sharedSecret.length() < 16) {
            throw new IllegalArgumentException(
                "The command-control shared secret must contain "
                    + "at least 16 characters."
            );
        }

        this.secretBytes = sharedSecret.getBytes(
            StandardCharsets.UTF_8
        );

        this.objectMapper = new ObjectMapper();

        // Sorting payload keys makes Java and Python produce
        // the same canonical payload JSON.
        this.objectMapper.configure(
            SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS,
            true
        );
    }

    /**
     * Create an authenticator from an environment variable.
     */
    public static MessageAuthenticator fromEnvironment() {
        final String sharedSecret =
            System.getenv(
                SECRET_ENVIRONMENT_VARIABLE
            );

        if (sharedSecret == null
            || sharedSecret.isBlank()) {
            throw new IllegalStateException(
                "Environment variable "
                    + SECRET_ENVIRONMENT_VARIABLE
                    + " is not configured."
            );
        }

        return new MessageAuthenticator(
            sharedSecret
        );
    }

    /**
     * Verify the signature contained in one command.
     *
     * MessageDigest.isEqual performs comparison without exiting
     * as soon as one mismatched byte is found.
     */
    public boolean verify(
        final CommandMessage command
    ) {
        Objects.requireNonNull(
            command,
            "command cannot be null"
        );

        final byte[] expectedSignature =
            calculateSignatureBytes(command);

        final byte[] receivedSignature;

        try {
            receivedSignature = HexFormat.of().parseHex(
                command.getSignature()
            );
        } catch (IllegalArgumentException error) {
            return false;
        }

        return MessageDigest.isEqual(
            expectedSignature,
            receivedSignature
        );
    }

    /**
     * Calculate the expected lowercase hexadecimal signature.
     *
     * This method will also be useful in unit tests.
     */
    public String calculateSignature(
        final CommandMessage command
    ) {
        return HexFormat.of().formatHex(
            calculateSignatureBytes(command)
        );
    }

    /**
     * Calculate raw HMAC-SHA256 bytes for one command.
     */
    private byte[] calculateSignatureBytes(
        final CommandMessage command
    ) {
        try {
            final Mac mac =
                Mac.getInstance(HMAC_ALGORITHM);

            final SecretKeySpec secretKey =
                new SecretKeySpec(
                    secretBytes,
                    HMAC_ALGORITHM
                );

            mac.init(secretKey);

            return mac.doFinal(
                createCanonicalMessage(command)
                    .getBytes(StandardCharsets.UTF_8)
            );
        } catch (GeneralSecurityException error) {
            throw new IllegalStateException(
                "Unable to calculate HMAC-SHA256 signature.",
                error
            );
        }
    }

    /**
     * Build the exact string signed by Java and Python.
     *
     * Each field occupies one line. The signature field itself
     * is intentionally excluded.
     */
    private String createCanonicalMessage(
        final CommandMessage command
    ) {
        final String payloadJson;

        try {
            payloadJson =
                objectMapper.writeValueAsString(
                    command.getPayload()
                );
        } catch (JsonProcessingException error) {
            throw new IllegalStateException(
                "Unable to serialize command payload.",
                error
            );
        }

        return String.join(
            "\n",
            command.getMessageId(),
            command.getCommandType().name(),
            command.getTargetId(),
            Long.toString(command.getSequenceNumber()),
            command.getTimestamp().toString(),
            payloadJson
        );
    }
}