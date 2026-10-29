package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Test/capture boundary for original C++ whole-query bytes. Never manufactures native input. */
public final class CombatWholeWire {
    public static final int RAW_MAX_BYTES = 16 * 1024 * 1024;
    public static final int REFERENCE_MAX_BYTES = 8192;
    public static final List<String> SCENE_NAMES = List.of(
            "absent-combat-rule24-pins-available-mode0",
            "absent-combat-rule24-pins-available-mode4-external-target",
            "absent-combat-rule24-missing-c8-pin",
            "absent-combat-rule24-missing-mode",
            "active-highbit-attacker-main",
            "active-fullid-zero-defender-pursuit",
            "active-selected-army-fallback-neither",
            "active-both-memberships-manager-duplicates-done",
            "phase0-below-threshold", "phase0-above-threshold",
            "phase0-forced-threshold-undemanded", "phase0-day-wrap",
            "missing-demanded-phase", "missing-demanded-side-roster");
    public static final String QUALIFICATION =
            "genuine whole ReadArmyStrengthsForScope+AppendArmyStrengthV1; fourteen new scenes times two scopes and two repeated high-bit originalArmy occurrences; global capture once across scopes and receiver pins once/query; fake world/readmemory, ordinary scope/evaluator/getter callbacks and consumer Service frame synthetic; no whole row or leaf transplant; raw combat observer executes zero native calls/writes; no game execution";
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private CombatWholeWire() { }

    public record FileReference(Path path, long bytes, String sha256) {
        public FileReference {
            Objects.requireNonNull(path);
            require(path.isAbsolute() && path.normalize().equals(path), "normalized absolute input path required");
            require(bytes > 0 && bytes <= RAW_MAX_BYTES, "finite original input reference required");
            require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "actual lowercase SHA-256 required");
        }
    }

    /** JsonNode remains inside the test transport boundary and never escapes as mutable shared state. */
    public record Scene(String name, ObjectNode originalWholeRow) {
        public Scene {
            require(SCENE_NAMES.contains(name), "unknown original native scene");
            originalWholeRow = Objects.requireNonNull(originalWholeRow).deepCopy();
        }
        @Override public ObjectNode originalWholeRow() { return originalWholeRow.deepCopy(); }
    }

    public record Parsed(List<Scene> scenes, String qualification, byte[] originalBytes) {
        public Parsed {
            scenes = List.copyOf(scenes);
            require(QUALIFICATION.equals(qualification), "original C++ qualification mismatch");
            originalBytes = originalBytes.clone();
        }
        @Override public byte[] originalBytes() { return originalBytes.clone(); }
    }

    public static FileReference reference(byte[] raw) throws IOException {
        ObjectNode value = object(parseJson(raw, REFERENCE_MAX_BYTES));
        require(fields(value).equals(Set.of("path", "bytes", "sha256")), "exact native reference fields required");
        JsonNode size = value.get("bytes");
        require(size.isIntegralNumber() && size.canConvertToLong(), "exact native byte count required");
        return new FileReference(Path.of(text(value.get("path"))), size.longValue(), text(value.get("sha256")));
    }

    public static byte[] readPinned(FileReference ref, Path approvedRoot) throws IOException {
        Path root = approvedRoot.toRealPath();
        require(!Files.isSymbolicLink(ref.path()), "native input must not be a symbolic link");
        Path actual = ref.path().toRealPath();
        require(actual.startsWith(root) && !actual.equals(root), "native input escapes approved task root");
        BasicFileAttributes before = Files.readAttributes(actual, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        require(before.isRegularFile() && before.size() == ref.bytes(), "native input size or kind changed");
        byte[] raw;
        try (var stream = Files.newInputStream(actual)) { raw = stream.readNBytes(RAW_MAX_BYTES + 1); }
        BasicFileAttributes after = Files.readAttributes(actual, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        require(raw.length == ref.bytes() && raw.length <= RAW_MAX_BYTES
                && before.size() == after.size()
                && before.lastModifiedTime().equals(after.lastModifiedTime())
                && Objects.equals(before.fileKey(), after.fileKey()), "native input changed during read");
        require(sha256(raw).equals(ref.sha256()), "original native bytes differ from retained reference");
        return raw;
    }

    public static Parsed parse(byte[] originalBytes) throws IOException {
        ObjectNode wire = object(parseJson(originalBytes, RAW_MAX_BYTES));
        require(fields(wire).equals(Set.of("samples", "qualification")), "exact original whole-wire root required");
        String qualification = text(wire.get("qualification"));
        require(QUALIFICATION.equals(qualification), "original C++ qualification mismatch");
        ObjectNode samples = object(wire.get("samples"));
        require(fields(samples).equals(Set.copyOf(SCENE_NAMES)), "all fourteen exact original scenes required");
        List<Scene> scenes = new ArrayList<>();
        for (String name : SCENE_NAMES) {
            ObjectNode row = object(samples.get(name));
            exact(row.get("army_id"), 11);
            exact(row.get("current_soldiers"), 20);
            exact(row.get("maximum_soldiers"), 40);
            exact(row.get("ai_base_power_raw"), 4_000_000);
            exact(row.get("regiment_count"), 1);
            require(row.get("scope_role") != null && "player".equals(text(row.get("scope_role")))
                    && row.get("war_ids") != null && row.get("war_ids").isArray() && row.get("war_ids").isEmpty(),
                    "original first C++ whole-query scope changed");
            object(row.get(CombatRolesCodec.MEMBER));
            object(row.get("current_army_flag31_inputs_v1"));
            object(row.get("current_post_admission_refresh_inputs_v1"));
            scenes.add(new Scene(name, row));
        }
        return new Parsed(scenes, qualification, originalBytes);
    }

    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("required SHA-256 unavailable", error); }
    }

    static JsonNode parseJson(byte[] raw, int maximum) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= maximum, "bounded nonempty raw UTF-8 required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode value = JSON.readTree(text);
            require(value != null, "JSON value required");
            return value;
        } catch (CharacterCodingException error) { throw new IllegalArgumentException("malformed native UTF-8", error); }
    }
    private static ObjectNode object(JsonNode value) {
        require(value instanceof ObjectNode, "original native JSON object required"); return (ObjectNode) value;
    }
    private static Set<String> fields(ObjectNode value) {
        Set<String> result = new HashSet<>(); value.fieldNames().forEachRemaining(result::add); return Set.copyOf(result);
    }
    private static String text(JsonNode value) {
        require(value != null && value.isTextual() && !value.textValue().isEmpty(), "actual nonempty JSON string required");
        return value.textValue();
    }
    private static void exact(JsonNode value, long expected) {
        require(value != null && value.isIntegralNumber() && value.canConvertToLong() && value.longValue() == expected,
                "original whole-row integer changed or is not an integer token");
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
