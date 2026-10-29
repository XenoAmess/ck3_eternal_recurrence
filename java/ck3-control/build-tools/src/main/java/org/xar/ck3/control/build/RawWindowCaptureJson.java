package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Shared strict records and bounded exact originals, with no coercing alternate parser. */
public final class RawWindowCaptureJson {
    private RawWindowCaptureJson() { }
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    public record Original(FileRef reference, byte[] bytes) {
        public Original { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    public static Original readOriginal(Path path, int maximumBytes) throws IOException {
        if (!path.isAbsolute() || !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(path)
                || Files.size(path) < 1 || Files.size(path) > maximumBytes) throw new IOException("bounded ordinary original required");
        byte[] raw;
        try (InputStream input = Files.newInputStream(path)) { raw = input.readNBytes(maximumBytes + 1); }
        if (raw.length < 1 || raw.length > maximumBytes || Files.size(path) != raw.length) throw new IOException("original grew or changed length");
        return new Original(reference(path, raw), raw);
    }
    public static <T> T decode(byte[] raw, Class<T> type, int maximumBytes) throws IOException {
        if (raw == null || raw.length == 0 || raw.length > maximumBytes) throw new IOException("bounded nonempty exact JSON required");
        return JSON.readValue(raw, type);
    }
    public static byte[] encode(Event value) throws IOException {
        return JSON.writeValueAsBytes(new JournalEntry(kindOf(value), java.time.Instant.now().toString(), value));
    }
    public static byte[] encode(Body value) throws IOException { return JSON.writeValueAsBytes(value); }
    public static byte[] encode(Result value) throws IOException { return JSON.writeValueAsBytes(value); }
    public static byte[] encode(CaptureOutcome value) throws IOException { return JSON.writeValueAsBytes(value); }
    public static byte[] encode(RawWindowLocatorContract.Body value) throws IOException { return JSON.writeValueAsBytes(value); }
    public static byte[] encode(RawWindowLocatorContract.Request value) throws IOException { return JSON.writeValueAsBytes(value); }
    public static byte[] encode(Request value) throws IOException { return JSON.writeValueAsBytes(value); }
    public static byte[] encode(Admission value) throws IOException { return JSON.writeValueAsBytes(value); }
    public static byte[] encode(CliFailure value) throws IOException { return JSON.writeValueAsBytes(value); }
    public record CliFailure(String schema, String machineId, String observedAtUtc, String status, String error) { }
    public record JournalEntry(EventKind event, String observedAtUtc, Event value) {
        public JournalEntry { java.time.Instant.parse(observedAtUtc); require(kindOf(value) == event, "exact journal event tag/value pair required"); }
    }
    public static CaptureRequest decodeRequest(byte[] raw) throws IOException {
        String schema = text(tree(raw).get("schema"));
        return switch (schema) {
            case RawWindowCaptureContract.REQUEST_SCHEMA -> decode(raw, Request.class, 65_536);
            case RawWindowLocatorContract.REQUEST_SCHEMA -> decode(raw, RawWindowLocatorContract.Request.class, 65_536);
            default -> throw new IOException("unknown capture request schema; no compatibility alias");
        };
    }
    /** One original line only; a partial line or unknown event is rejected, never repaired into success. */
    public static JournalEntry decodeJournalLine(byte[] raw) throws IOException {
        if (raw == null || raw.length == 0 || raw.length > 4096) throw new IOException("bounded complete journal line required");
        var root = object(JSON.readTree(raw), "event", "observed_at_utc", "value"); EventKind kind = EventKind.valueOf(text(root.get("event")));
        Event value = switch (kind) {
            case STARTED -> typed(root.get("value"), Started.class); case BEFORE -> typed(root.get("value"), Before.class);
            case INTENT -> typed(root.get("value"), Intent.class); case READ_OBSERVED -> typed(root.get("value"), ReadObserved.class);
            case RAW_OBSERVED -> typed(root.get("value"), RawObserved.class); case AFTER -> typed(root.get("value"), After.class);
            case FINISHED -> typed(root.get("value"), Finished.class);
            case LOCATOR_INTENT -> typed(root.get("value"), RawWindowLocatorContract.Intent.class);
            case LOCATOR_READ -> typed(root.get("value"), RawWindowLocatorContract.ReadObserved.class);
            case LOCATOR_CANDIDATE -> typed(root.get("value"), RawWindowLocatorContract.CandidateObserved.class);
            case LOCATOR_PROGRESS -> typed(root.get("value"), RawWindowLocatorContract.Progress.class);
            case LOCATOR_BEFORE -> typed(root.get("value"), RawWindowLocatorContract.Before.class);
            case LOCATOR_AFTER -> typed(root.get("value"), RawWindowLocatorContract.After.class);
            case LOCATOR_FINISHED -> typed(root.get("value"), RawWindowLocatorContract.Finished.class);
        };
        return new JournalEntry(kind, text(root.get("observed_at_utc")), value);
    }
    public static byte[] exactBytes(FileRef reference, int maximumBytes) throws IOException {
        if (reference.bytes() < 1 || reference.bytes() > maximumBytes) throw new IOException("bounded original exact reference required");
        Path path = Path.of(reference.path());
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(path)
                || Files.size(path) != reference.bytes()) throw new IOException("exact original is absent or has changed length");
        byte[] raw = readOriginal(path, maximumBytes).bytes();
        if (raw.length != reference.bytes() || !hash(raw).equals(reference.sha256()) || Files.size(path) != reference.bytes())
            throw new IOException("exact original byte length/SHA-256 drift");
        return raw;
    }
    public static FileRef reference(Path path, byte[] raw) { return new FileRef(path.toAbsolutePath().normalize().toString(), raw.length, hash(raw)); }
    public static String hash(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    static ObjectNode object(JsonNode node, String... expected) throws IOException {
        if (!(node instanceof ObjectNode object)) throw new IOException("exact source object required");
        Set<String> actual = new HashSet<>(); object.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(Set.of(expected))) throw new IOException("source proof fields differ from its one versioned contract"); return object;
    }
    static String text(JsonNode node) throws IOException {
        if (node == null || !node.isTextual() || node.textValue().isEmpty() || node.textValue().length() > 32768)
            throw new IOException("bounded original JSON string required"); return node.textValue();
    }
    static long integer(JsonNode node) throws IOException {
        if (node == null || !node.isIntegralNumber() || !node.canConvertToLong()) throw new IOException("exact JSON integer required");
        long value = node.longValue(); if (value < 0 || value > SAFE) throw new IOException("safe nonnegative JSON integer required"); return value;
    }
    static JsonNode tree(byte[] raw) throws IOException { return JSON.readTree(raw); }
    static <T> T typed(JsonNode node, Class<T> type) throws IOException { return JSON.treeToValue(node, type); }
}
