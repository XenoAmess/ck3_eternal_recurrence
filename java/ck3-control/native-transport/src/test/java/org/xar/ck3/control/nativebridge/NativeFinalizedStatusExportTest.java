package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Mandatory cold producer DATA validation, never Game/lease/request-custody construction.
 * Run only with the Native owner's actual accepted receipt. Missing output is a failure, never a skip.
 * No native call, executable invocation, timestamp inference or synthetic Frame is made by this test.
 */
final class NativeFinalizedStatusExportTest {
    private static final String RECEIPT = "xar.native.finalizedStatus1210.receipt";
    private static final long MAX_PIN = 32L * 1024 * 1024, MAX_TOTAL = 128L * 1024 * 1024;
    private static final Set<String> MODES = Set.of("idle", "triggered", "failed", "cleanup-unknown");
    private static final Set<String> EVENTS = Set.of("owner_armed", "body_enter", "body_return", "destroy_enter", "destroy_return",
            "destroy_fault", "typed_result", "readers_in_acquire_window", "release_destroy_barrier", "status_returned",
            "terminal_cancel_returned", "post_returned", "owner_cancelled", "nested_post_requested", "nested_post_returned", "export_complete");
    private record Pin(Path path, long bytes, String sha256) { }
    private record ExportFrame(String role, String requestId, String step, Pin json, Pin packet) { }
    private record Decoded(ExportFrame original, NativeWire.CommandResult packet, JsonNode token) { }

    @Test void actualAcceptedOwnerReceiptAndEveryFinalizedPacketAreMandatory() throws Exception {
        String configured = System.getProperty(RECEIPT);
        if (configured == null || configured.isBlank()) throw new IOException("mandatory actual Native owner receipt absent: -D" + RECEIPT);
        Path receiptPath = absolute(configured);
        JsonNode receipt = parseSmall(receiptPath);
        assertEquals("xar.no-game.finalized-status-export/v1", text(receipt, "schema"));
        assertFalse(flag(receipt, "live")); assertTrue(flag(receipt, "accepted"), "the owner must record an actual successful export");
        var commands = array(receipt, "commands", 128); assertFalse(commands.isEmpty());
        for (JsonNode command : commands) {
            var args = array(command, "args", 128); assertFalse(args.isEmpty());
            for (JsonNode arg : args) assertTrue(arg.isTextual() && !arg.textValue().isBlank());
            assertEquals(BigInteger.ZERO, integer(command, "exit"));
        }
        var pinRows = array(receipt, "pins", 256); assertFalse(pinRows.isEmpty());
        Set<Pin> pins = new HashSet<>(); Set<Path> paths = new HashSet<>(); long total = 0;
        for (JsonNode row : pinRows) {
            Pin pin = pin(row); assertTrue(pins.add(pin)); assertTrue(paths.add(pin.path()), "one path cannot have conflicting originals");
            total = Math.addExact(total, pin.bytes()); assertTrue(total <= MAX_TOTAL); verify(pin);
        }
        JsonNode producer = object(receipt, "producer");
        for (String role : List.of("source", "exe")) assertTrue(pins.contains(pin(object(producer, role))), "producer original omitted from pins");
        var scenarios = array(receipt, "scenarios", 4); assertEquals(4, scenarios.size()); Set<String> modes = new HashSet<>();
        for (JsonNode scenario : scenarios) {
            String mode = text(scenario, "mode"); assertTrue(MODES.contains(mode)); assertTrue(modes.add(mode));
            Pin manifest = pin(object(scenario, "manifest")); assertTrue(pins.contains(manifest));
            JsonNode data = parse(manifest);
            assertEquals(mode, text(data, "mode"));
            Pin executable = pin(object(producer, "exe"));
            assertTrue(commands.stream().anyMatch(command -> actualRun(command, executable.path(), mode, manifest.path().getParent())),
                    "owner receipt must bind the actual executable, mode and output directory to a successful command");
            assertEquals("xar.no-game.status-export-scenario/v1", text(data, "schema"));
            BigInteger generation = new BigInteger(new CrossJsDecimalUInt64(text(data, "generation")).decimal());
            assertTrue(generation.signum() > 0, "all four providers really ARM before their final observation");
            var rows = array(scenario, "frames", 2); assertEquals(2, rows.size()); List<Decoded> decoded = new ArrayList<>(); Set<String> roles = new HashSet<>();
            for (JsonNode row : rows) {
                ExportFrame frame = new ExportFrame(text(row, "role"), text(row, "request_id"), text(row, "step"), pin(object(row, "json")), pin(object(row, "packet")));
                assertTrue(Set.of("query", "terminal_cancel").contains(frame.role())); assertTrue(roles.add(frame.role()));
                assertTrue(pins.contains(frame.json()) && pins.contains(frame.packet()));
                assertEquals(manifest.path().getParent(), frame.json().path().getParent());
                assertEquals(manifest.path().getParent(), frame.packet().path().getParent());
                decoded.add(decode(frame));
            }
            verifyManifestFrames(data, decoded);
            Decoded query = decoded.stream().filter(row -> row.original().role().equals("query")).findFirst().orElseThrow();
            Decoded cancel = decoded.stream().filter(row -> row.original().role().equals("terminal_cancel")).findFirst().orElseThrow();
            assertEquals(ClockStatusRead.STEP, query.original().step());
            assertEquals(ClockStatusRead.CANCEL_PREFIX + generation, cancel.original().step());
            assertNotEquals(query.original().requestId(), cancel.original().requestId());
            Status status = available(query);
            assertEquals(generation, new BigInteger(status.generation().decimal()));
            verifyOutcome(mode, status, cancel);
            verifyEvents(data, mode);
        }
        assertEquals(MODES, modes);
    }

    private static Decoded decode(ExportFrame frame) throws Exception {
        byte[] json = readSmall(frame.json()), packet = readSmall(frame.packet());
        NativeWire.Frame decoded = NativeWire.decode(packet);
        assertInstanceOf(NativeWire.CommandResult.class, decoded);
        NativeWire.CommandResult result = (NativeWire.CommandResult) decoded;
        assertEquals(frame.requestId(), result.requestId());
        assertArrayEquals(json, result.payload().value(), "original UTF-8 must equal the actual LE32 packet payload");
        assertEquals(NativeWire.Presence.VALUE, result.result().presence());
        JsonNode token = StrictJson.parse(result.result().token().orElseThrow().value());
        assertTrue(token.isObject()); assertEquals(frame.step(), text(token, "step"));
        return new Decoded(frame, result, token);
    }

    private static Status available(Decoded decoded) {
        assertTrue(decoded.packet().nativeOk()); assertTrue(flag(decoded.token(), "accepted"));
        assertEquals("available", text(decoded.token(), "status"));
        JsonNode embedded = object(decoded.token(), "tactical_daily_sentinel");
        assertEquals(20, embedded.size(), "the real legacy Status DTO has exactly twenty fields");
        return SentinelObservation.decode(embedded);
    }

    private static void unavailable(Decoded decoded) {
        assertFalse(decoded.packet().nativeOk()); assertFalse(flag(decoded.token(), "accepted"));
        assertEquals("unavailable", text(decoded.token(), "queue_status"));
        assertFalse(decoded.token().has("status"));
        assertFalse(flag(decoded.token(), "effect_attempted"));
        assertFalse(flag(decoded.token(), "full_snapshot_before_verified"));
        assertFalse(flag(decoded.token(), "complete_snapshot")); assertFalse(flag(decoded.token(), "physical_save_confirmed"));
        assertEquals(NativeWire.Presence.VALUE, decoded.packet().error().presence());
        JsonNode error = StrictJson.parse(decoded.packet().error().token().orElseThrow().value());
        assertTrue(error.isTextual()); assertEquals("full_clock_unavailable", error.textValue());
        assertEquals("ck3_1210_full_clock_control_result_v1", text(decoded.token(), "schema"));
        assertFalse(decoded.token().has("tactical_daily_sentinel"), "negative Core result cannot be a success Status");
    }

    private static void verifyOutcome(String mode, Status status, Decoded cancel) {
        boolean failedEvaluation = (status.triggerFlags() & (1L << 15)) != 0;
        switch (mode) {
            case "idle" -> {
                assertEquals(State.IDLE, status.state()); assertFalse(failedEvaluation);
                assertEquals(status, available(cancel), "same generation terminal CANCEL is readonly");
            }
            case "triggered" -> {
                assertEquals(State.TRIGGERED, status.state()); assertTrue(status.pauseObserved());
                assertFalse(status.abnormal()); assertFalse(failedEvaluation);
                assertEquals(status, available(cancel), "all twenty fields must remain the actual published terminal Status");
            }
            case "failed" -> {
                assertEquals(State.FAILED, status.state()); assertTrue(status.abnormal()); assertTrue(failedEvaluation);
                assertEquals(status, available(cancel), "known cleanup preserves the real nested/abort FAILED Status");
                // This is real nested/abort FAILED with bit15: observing its shape never grants cancellation success.
            }
            case "cleanup-unknown" -> {
                assertEquals(State.FAILED, status.state()); assertTrue(status.abnormal()); assertTrue(failedEvaluation);
                unavailable(cancel); // actual resource UNKNOWN is never available passthrough or a replay instruction.
            }
            default -> fail("unsupported Native producer mode");
        }
    }

    private static void verifyManifestFrames(JsonNode data, List<Decoded> decoded) {
        var rows = array(data, "frames", 2); assertEquals(2, rows.size()); Set<String> roles = new HashSet<>();
        for (JsonNode row : rows) {
            String role = text(row, "role"); assertTrue(roles.add(role));
            ExportFrame frame = decoded.stream().filter(value -> value.original().role().equals(role)).findFirst().orElseThrow().original();
            assertEquals(frame.requestId(), text(row, "request_id")); assertEquals(frame.step(), text(row, "step"));
            String stem = role.equals("query") ? "status" : "cancel";
            assertEquals(stem + ".json", text(row, "json_file"));
            assertEquals(stem + ".packet.bin", text(row, "packet_file"));
            assertEquals(text(row, "json_file"), frame.json().path().getFileName().toString());
            assertEquals(text(row, "packet_file"), frame.packet().path().getFileName().toString());
            assertEquals(BigInteger.valueOf(frame.json().bytes()), integer(row, "json_bytes"));
            assertEquals(BigInteger.valueOf(frame.packet().bytes()), integer(row, "packet_bytes"));
        }
        assertEquals(Set.of("query", "terminal_cancel"), roles);
    }

    private static void verifyEvents(JsonNode data, String mode) {
        var events = array(data, "events", 512); assertFalse(events.isEmpty());
        BigInteger previous = BigInteger.ZERO; Set<String> seen = new HashSet<>(); boolean unknown = false;
        for (JsonNode event : events) {
            BigInteger sequence = new BigInteger(new CrossJsDecimalUInt64(text(event, "sequence")).decimal());
            assertTrue(sequence.compareTo(previous) > 0); previous = sequence;
            String name = text(event, "event"); assertTrue(EVENTS.contains(name)); seen.add(name);
            BigInteger thread = integer(event, "thread_id"), callbacks = integer(event, "post_callbacks");
            assertTrue(thread.signum() > 0 && thread.compareTo(BigInteger.valueOf(0xffff_ffffL)) <= 0);
            assertTrue(callbacks.signum() >= 0 && callbacks.compareTo(BigInteger.valueOf(0xffff_ffffL)) <= 0);
            boolean cleanupUnknown = flag(event, "cleanup_unknown"); unknown |= cleanupUnknown;
            if (name.equals("typed_result")) {
                assertTrue(Set.of("none", "borrowed", "owned", "unknown").contains(text(event, "acquisition")));
                assertTrue(Set.of("not_required", "borrowed_preserved", "owned_released", "unknown").contains(text(event, "release")));
                assertTrue(Set.of("not_called", "failed", "succeeded").contains(text(event, "body")));
                if (mode.equals("cleanup-unknown")) assertEquals("unknown", text(event, "release"));
            } else for (String key : List.of("acquisition", "release", "body")) {
                assertTrue(event.has(key) && event.get(key).isNull(), "non-typed events carry explicit null outcomes");
            }
            if (Set.of("status_returned", "terminal_cancel_returned", "export_complete").contains(name)) {
                assertEquals(BigInteger.ZERO, callbacks, "public result follows actual callback rundown");
                assertEquals(mode.equals("cleanup-unknown"), cleanupUnknown);
            }
        }
        assertTrue(seen.containsAll(Set.of("status_returned", "terminal_cancel_returned", "export_complete")));
        assertEquals("export_complete", text(events.get(events.size() - 1), "event"));
        assertEquals(mode.equals("cleanup-unknown"), unknown);
        if (mode.equals("idle")) {
            assertTrue(position(events, "owner_cancelled") < position(events, "status_returned"));
            assertTrue(position(events, "owner_cancelled") < position(events, "terminal_cancel_returned"));
        } else {
            assertTrue(position(events, "body_enter") < position(events, "body_return"));
            assertTrue(position(events, "destroy_enter") < position(events, "readers_in_acquire_window"));
            assertTrue(position(events, "readers_in_acquire_window") < position(events, "release_destroy_barrier"));
            assertTrue(position(events, "release_destroy_barrier") < position(events, "typed_result"));
            assertTrue(position(events, "typed_result") < position(events, "status_returned"));
            assertTrue(position(events, "typed_result") < position(events, "terminal_cancel_returned"));
            assertTrue(seen.contains("post_returned"));
            if (mode.equals("failed")) {
                assertTrue(position(events, "nested_post_requested") < position(events, "nested_post_returned"));
                assertTrue(position(events, "nested_post_returned") < position(events, "release_destroy_barrier"));
            }
        }
        // Sequences are real producer ordering only; they assert neither timestamps nor kernel waiter acquisition.
    }

    private static int position(List<JsonNode> events, String name) {
        for (int index = 0; index < events.size(); index++) if (text(events.get(index), "event").equals(name)) return index;
        throw new AssertionError("mandatory actual producer event absent: " + name);
    }

    private static boolean actualRun(JsonNode command, Path executable, String mode, Path directory) {
        var args = array(command, "args", 128);
        return args.size() == 3 && Path.of(args.get(0).textValue()).equals(executable)
                && args.get(1).textValue().equals(mode) && Path.of(args.get(2).textValue()).equals(directory);
    }

    private static Pin pin(JsonNode row) {
        Path path = absolute(text(row, "path"));
        assertNotEquals("ck3.exe", path.getFileName().toString().toLowerCase(Locale.ROOT), "never read the Game executable");
        BigInteger bytes = integer(row, "bytes");
        assertTrue(bytes.signum() > 0 && bytes.compareTo(BigInteger.valueOf(MAX_PIN)) <= 0);
        String sha = text(row, "sha256"); assertTrue(sha.matches("[0-9a-f]{64}"), "canonical SHA-256 required");
        return new Pin(path, bytes.longValueExact(), sha);
    }

    private static Path absolute(String value) {
        Path path = Path.of(value);
        assertTrue(path.isAbsolute(), "pin paths are explicit absolute originals");
        assertEquals(path, path.normalize(), "pin paths cannot traverse aliases");
        return path;
    }

    private static void verify(Pin pin) throws Exception {
        assertTrue(Files.isRegularFile(pin.path())); assertEquals(pin.bytes(), Files.size(pin.path()));
        MessageDigest digest = MessageDigest.getInstance("SHA-256"); long total = 0;
        try (InputStream input = Files.newInputStream(pin.path())) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = input.read(buffer)) != -1) {
                total += count; assertTrue(total <= pin.bytes()); digest.update(buffer, 0, count);
            }
        }
        assertEquals(pin.bytes(), total); assertEquals(pin.sha256(), HexFormat.of().formatHex(digest.digest()));
    }

    private static byte[] readSmall(Pin pin) throws Exception {
        assertTrue(pin.bytes() <= StrictJson.EXPLICIT_MAX_BYTES);
        byte[] raw = Files.readAllBytes(pin.path()); assertEquals(pin.bytes(), (long) raw.length);
        assertEquals(pin.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        return raw;
    }

    private static JsonNode parse(Pin pin) throws Exception {
        JsonNode node = StrictJson.parse(readSmall(pin), StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(node.isObject()); return node;
    }

    private static JsonNode parseSmall(Path path) throws IOException {
        long bytes = Files.size(path); assertTrue(bytes > 0 && bytes <= StrictJson.EXPLICIT_MAX_BYTES);
        JsonNode node = StrictJson.parse(Files.readAllBytes(path), StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(node.isObject()); return node;
    }

    private static JsonNode object(JsonNode row, String key) {
        JsonNode value = row.get(key); assertNotNull(value, "required field: " + key);
        assertTrue(value.isObject(), "object required: " + key); return value;
    }

    private static List<JsonNode> array(JsonNode row, String key, int maximum) {
        JsonNode value = row.get(key); assertNotNull(value, "required field: " + key);
        assertTrue(value.isArray() && value.size() <= maximum, "bounded array required: " + key);
        List<JsonNode> result = new ArrayList<>(); value.forEach(result::add); return List.copyOf(result);
    }

    private static String text(JsonNode row, String key) {
        JsonNode value = row.get(key); assertNotNull(value, "required field: " + key);
        assertTrue(value.isTextual() && !value.textValue().isBlank(), "nonblank text required: " + key); return value.textValue();
    }

    private static boolean flag(JsonNode row, String key) {
        JsonNode value = row.get(key); assertNotNull(value, "required field: " + key);
        assertTrue(value.isBoolean(), "actual boolean required: " + key); return value.booleanValue();
    }

    private static BigInteger integer(JsonNode row, String key) {
        JsonNode value = row.get(key); assertNotNull(value, "required field: " + key);
        assertTrue(value.isIntegralNumber(), "actual integer required: " + key); return value.bigIntegerValue();
    }
}
