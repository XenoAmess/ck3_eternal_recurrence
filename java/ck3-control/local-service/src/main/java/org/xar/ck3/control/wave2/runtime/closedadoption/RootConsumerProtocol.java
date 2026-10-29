package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Shared packets for Root's existing retained session; serialized packets carry no live authority. */
public final class RootConsumerProtocol {
    public static final String COMMAND_SCHEMA = "xar.java-closed-partial-root-consumer-command/v1";
    public static final String CLOSE_SCHEMA = "xar.java-closed-partial-root-consumer-close/v1";
    public static final int MAX_OPERATIONS = 16;
    private static final Set<String> COMMAND_FIELDS = Set.of(
            "schema", "machine_id", "session_nonce", "sequence", "operation", "arguments");
    private static final Set<String> CLOSE_FIELDS = Set.of("schema", "machine_id", "session_nonce");

    private RootConsumerProtocol() { }

    /** Values must be read from the actual live ready descriptor, never a ticket or review nonce. */
    public record Binding(String machineId, String sessionNonce) {
        public Binding {
            StrictJson.text(machineId);
            StrictJson.require(sessionNonce != null && sessionNonce.matches("[0-9a-f]{32}"),
                    "exact live Root consumer session nonce");
        }
    }

    public sealed interface Request permits Consumer, BeginRestoreReads, OpenNativeOwner, OpenColdSession { }

    /** Reuses the original consumer operation and its sole strict argument contract. */
    public record Consumer(OriginalColdConsumerSession.Operation operation) implements Request {
        public Consumer { Objects.requireNonNull(operation); }
    }

    public record BeginRestoreReads(int preparedSequence) implements Request {
        public BeginRestoreReads { sequence(preparedSequence); }
    }
    public record OpenNativeOwner(int preparedSequence) implements Request {
        public OpenNativeOwner { sequence(preparedSequence); }
    }
    public record OpenColdSession(int preparedSequence) implements Request {
        public OpenColdSession { sequence(preparedSequence); }
    }

    public record Command(Binding binding, int sequence, Request request) {
        public Command {
            Objects.requireNonNull(binding); RootConsumerProtocol.sequence(sequence); Objects.requireNonNull(request);
        }
        public String fileName() { return requestFileName(sequence); }
        public ObjectNode toJson() {
            ObjectNode value = base(COMMAND_SCHEMA, binding); value.put("sequence", sequence);
            if (request instanceof Consumer consumer) {
                value.put("operation", consumer.operation().kind().name());
                value.set("arguments", consumer.operation().arguments());
            } else if (request instanceof BeginRestoreReads begin) {
                value.put("operation", "BEGIN_RESTORE_READS");
                value.set("arguments", StrictJson.object().put("prepared_sequence", begin.preparedSequence()));
            } else if (request instanceof OpenNativeOwner open) {
                value.put("operation", "OPEN_NATIVE_OWNER");
                value.set("arguments", StrictJson.object().put("prepared_sequence", open.preparedSequence()));
            } else {
                OpenColdSession open = (OpenColdSession) request;
                value.put("operation", "OPEN_COLD_SESSION");
                value.set("arguments", StrictJson.object().put("prepared_sequence", open.preparedSequence()));
            }
            return value;
        }
        public byte[] wireBytes() { return encode(toJson()); }
    }

    public record Close(Binding binding) {
        public Close { Objects.requireNonNull(binding); }
        public String fileName() { return "close.json"; }
        public ObjectNode toJson() { return base(CLOSE_SCHEMA, binding); }
        public byte[] wireBytes() { return encode(toJson()); }
    }

    /** Consumer entry point: expected binding and sequence belong to the current live server. */
    public static Command decodeCommand(byte[] raw, Binding expected, int expectedSequence) {
        Objects.requireNonNull(expected); sequence(expectedSequence);
        ObjectNode value = StrictJson.object(StrictJson.parse(raw, RecoveryEvidence.MAX_BYTES), COMMAND_FIELDS);
        require(value, "schema", COMMAND_SCHEMA);
        Binding actual = binding(value);
        StrictJson.require(actual.equals(expected), "same live Root consumer machine and session nonce");
        int number = (int) StrictJson.integer(value.get("sequence"), expectedSequence, expectedSequence);
        String operation = StrictJson.text(value.get("operation"));
        Request request;
        if (Set.of("BEGIN_RESTORE_READS", "OPEN_NATIVE_OWNER", "OPEN_COLD_SESSION").contains(operation)) {
            ObjectNode arguments = StrictJson.object(value.get("arguments"), Set.of("prepared_sequence"));
            int prepared = (int) StrictJson.integer(arguments.get("prepared_sequence"), 1, MAX_OPERATIONS);
            request = switch(operation) {
                case "BEGIN_RESTORE_READS" -> new BeginRestoreReads(prepared);
                case "OPEN_NATIVE_OWNER" -> new OpenNativeOwner(prepared);
                default -> new OpenColdSession(prepared);
            };
        } else {
            request = new Consumer(OriginalColdConsumerSession.decodeOperation(value.get("operation"), value.get("arguments")));
        }
        return new Command(actual, number, request);
    }

    public static Close decodeClose(byte[] raw, Binding expected) {
        Objects.requireNonNull(expected);
        ObjectNode value = StrictJson.object(StrictJson.parse(raw, RecoveryEvidence.MAX_BYTES), CLOSE_FIELDS);
        require(value, "schema", CLOSE_SCHEMA);
        Binding actual = binding(value);
        StrictJson.require(actual.equals(expected), "same live Root consumer close machine and session nonce");
        return new Close(actual);
    }

    public static String requestFileName(int sequence) {
        sequence(sequence); return String.format(Locale.ROOT, "%04d.request.json", sequence);
    }

    private static Binding binding(ObjectNode value) {
        return new Binding(StrictJson.text(value.get("machine_id")), StrictJson.text(value.get("session_nonce")));
    }
    private static ObjectNode base(String schema, Binding binding) {
        ObjectNode value = StrictJson.object(); value.put("schema", schema);
        value.put("machine_id", binding.machineId()); value.put("session_nonce", binding.sessionNonce()); return value;
    }
    private static byte[] encode(ObjectNode value) {
        byte[] raw = StrictJson.canonical(value);
        StrictJson.require(raw.length <= RecoveryEvidence.MAX_BYTES, "bounded complete Root consumer packet");
        return raw;
    }
    private static void sequence(int value) {
        StrictJson.require(value >= 1 && value <= MAX_OPERATIONS, "finite Root consumer sequence");
    }
    private static void require(ObjectNode value, String field, String expected) {
        StrictJson.require(StrictJson.text(value.get(field)).equals(expected), "Root consumer " + field);
    }
}
