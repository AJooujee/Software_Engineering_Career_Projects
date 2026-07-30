package com.aj.commandcontrol.parsing;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandType;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.DateTimeException;
import java.time.Instant;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

/**
 * Parses and validates JSON command messages received from
 * the control station.
 */
public final class CommandMessageParser {

    // Jackson object used to parse JSON text.
    private final ObjectMapper objectMapper;

    // Fields currently permitted in a command message.
    // Rejecting unknown fields helps catch misspellings and
    // unexpected message formats.
    private static final Set<String> ALLOWED_FIELDS = Set.of(
        "message_id",
        "command_type",
        "target_id",
        "sequence_number",
        "timestamp",
        "payload"
    );

    /**
     * Create a parser using a standard Jackson ObjectMapper.
     */
    public CommandMessageParser() {
        this.objectMapper = new ObjectMapper();
    }

    /**
     * Parse and validate one JSON command message.
     *
     * @param jsonMessage raw JSON received from the control station
     * @return validated immutable command message
     * @throws CommandValidationException when the message is invalid
     */
    public CommandMessage parse(
        final String jsonMessage
    ) throws CommandValidationException {

        if (jsonMessage == null || jsonMessage.isBlank()) {
            throw new CommandValidationException(
                "Command message cannot be blank."
            );
        }

        final JsonNode rootNode;

        try {
            // Convert the raw JSON string into a Jackson tree.
            rootNode = objectMapper.readTree(jsonMessage);
        } catch (JsonProcessingException error) {
            throw new CommandValidationException(
                "Malformed JSON command message.",
                error
            );
        }

        // The top-level JSON value must be an object.
        if (rootNode == null || !rootNode.isObject()) {
            throw new CommandValidationException(
                "The command message must be a JSON object."
            );
        }

        validateUnknownFields(rootNode);

        final String messageId = requireText(
            rootNode,
            "message_id"
        );

        final String commandTypeText = requireText(
            rootNode,
            "command_type"
        );

        final String targetId = requireText(
            rootNode,
            "target_id"
        );

        final long sequenceNumber = requirePositiveLong(
            rootNode,
            "sequence_number"
        );

        final String timestampText = requireText(
            rootNode,
            "timestamp"
        );

        final CommandType commandType = parseCommandType(
            commandTypeText
        );

        final Instant timestamp = parseTimestamp(
            timestampText
        );

        final Map<String, Object> payload = parsePayload(
            rootNode
        );

        // Build the validated immutable production model.
        try {
            return new CommandMessage(
                messageId,
                commandType,
                targetId,
                sequenceNumber,
                timestamp,
                payload
            );
        } catch (IllegalArgumentException
                 | NullPointerException error) {
            throw new CommandValidationException(
                "Command model validation failed: "
                    + error.getMessage(),
                error
            );
        }
    }

    /**
     * Reject fields that are not part of the command-message contract.
     */
    private static void validateUnknownFields(
        final JsonNode rootNode
    ) throws CommandValidationException {

        final Iterator<String> fieldNames =
            rootNode.fieldNames();

        while (fieldNames.hasNext()) {
            final String fieldName = fieldNames.next();

            if (!ALLOWED_FIELDS.contains(fieldName)) {
                throw new CommandValidationException(
                    "Unknown command field: " + fieldName
                );
            }
        }
    }

    /**
     * Read one required nonblank text field.
     */
    private static String requireText(
        final JsonNode rootNode,
        final String fieldName
    ) throws CommandValidationException {

        final JsonNode fieldNode = rootNode.get(fieldName);

        if (fieldNode == null || fieldNode.isNull()) {
            throw new CommandValidationException(
                "Missing required field: " + fieldName
            );
        }

        if (!fieldNode.isTextual()) {
            throw new CommandValidationException(
                "Field '" + fieldName
                    + "' must contain text."
            );
        }

        final String value = fieldNode.asText().trim();

        if (value.isEmpty()) {
            throw new CommandValidationException(
                "Field '" + fieldName
                    + "' cannot be blank."
            );
        }

        return value;
    }

    /**
     * Read one required positive integer field.
     */
    private static long requirePositiveLong(
        final JsonNode rootNode,
        final String fieldName
    ) throws CommandValidationException {

        final JsonNode fieldNode = rootNode.get(fieldName);

        if (fieldNode == null || fieldNode.isNull()) {
            throw new CommandValidationException(
                "Missing required field: " + fieldName
            );
        }

        if (!fieldNode.isIntegralNumber()) {
            throw new CommandValidationException(
                "Field '" + fieldName
                    + "' must contain an integer."
            );
        }

        if (!fieldNode.canConvertToLong()) {
            throw new CommandValidationException(
                "Field '" + fieldName
                    + "' exceeds the supported integer range."
            );
        }

        final long value = fieldNode.longValue();

        if (value < 1) {
            throw new CommandValidationException(
                "Field '" + fieldName
                    + "' must be greater than zero."
            );
        }

        return value;
    }

    /**
     * Convert command text into a supported CommandType.
     */
    private static CommandType parseCommandType(
        final String commandTypeText
    ) throws CommandValidationException {

        try {
            // Command names use exact enum-style uppercase values.
            return CommandType.valueOf(
                commandTypeText
            );
        } catch (IllegalArgumentException error) {
            throw new CommandValidationException(
                "Unsupported command type: "
                    + commandTypeText,
                error
            );
        }
    }

    /**
     * Convert an ISO-8601 UTC timestamp into an Instant.
     */
    private static Instant parseTimestamp(
        final String timestampText
    ) throws CommandValidationException {

        try {
            return Instant.parse(timestampText);
        } catch (DateTimeException error) {
            throw new CommandValidationException(
                "Field 'timestamp' must contain a valid "
                    + "ISO-8601 UTC timestamp.",
                error
            );
        }
    }

    /**
     * Parse the optional payload object.
     */
    private Map<String, Object> parsePayload(
        final JsonNode rootNode
    ) throws CommandValidationException {

        final JsonNode payloadNode =
            rootNode.get("payload");

        // Missing payload is treated as an empty object.
        if (payloadNode == null || payloadNode.isNull()) {
            return Collections.emptyMap();
        }

        if (!payloadNode.isObject()) {
            throw new CommandValidationException(
                "Field 'payload' must contain a JSON object."
            );
        }

        try {
            final Map<?, ?> convertedPayload =
                objectMapper.convertValue(
                    payloadNode,
                    Map.class
                );

            final Map<String, Object> validatedPayload =
                new HashMap<>();

            for (Map.Entry<?, ?> entry
                : convertedPayload.entrySet()) {

                if (!(entry.getKey() instanceof String key)) {
                    throw new CommandValidationException(
                        "Payload keys must contain text."
                    );
                }

                validatedPayload.put(
                    key,
                    entry.getValue()
                );
            }

            return validatedPayload;
        } catch (IllegalArgumentException error) {
            throw new CommandValidationException(
                "Unable to parse the command payload.",
                error
            );
        }
    }
}