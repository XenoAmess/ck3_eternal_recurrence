package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.DateTimeException;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicLong;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;

/**
 * Sole source producer over already retained original Native observation rows.
 * Root owns selection, current process/session observation and the exact reader.
 * No JSON request path creates reader, retention, Native or action authority.
 */
public final class G2RetainedNativeSourceProvider implements G2CallContextProducer.Provider {
    public static final int MAX_NATIVE_ARTIFACT_BYTES = 32 * 1024 * 1024;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(MAX_NATIVE_ARTIFACT_BYTES).build())
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final String BUILD_OBSERVATION_SCHEMA = "xar.resume56-current-game-files-readonly-observation/v1";

    public record GameIdentity(long pid, String creationFiletime) {
        public GameIdentity {
            StrictJson.require(pid > 0 && pid <= 4_294_967_295L, "exact positive Game PID required");
            decimal(creationFiletime, BigInteger.ONE, StrictJson.UINT64_MAX);
        }
    }
    /** Root's existing current-session observer supplies these facts; this is no process probe. */
    public record Session(String machineId, String sessionId, GameIdentity game, String episodeRunId,
            String connectionGeneration, ExactRef executable, String executableFileId, String executableMtimeNs) {
        public Session {
            StrictJson.require(machineId != null && machineId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"), "explicit source machine required");
            StrictJson.text(sessionId); Objects.requireNonNull(game); StrictJson.text(episodeRunId);
            decimal(connectionGeneration, BigInteger.ZERO, StrictJson.UINT64_MAX); Objects.requireNonNull(executable);
            decimal(executableFileId, BigInteger.ZERO, BigInteger.ONE.shiftLeft(128).subtract(BigInteger.ONE));
            decimal(executableMtimeNs, BigInteger.ZERO, StrictJson.UINT64_MAX);
        }
    }
    /** Captured by the Root retainer at original Native arrival, never restamped by a pure caller. */
    public record RetainedArtifact(Session retainedSession, ExactRef nativeObservation,
            ExactRef executableObservation, String expectedTool) {
        public RetainedArtifact {
            Objects.requireNonNull(retainedSession); Objects.requireNonNull(nativeObservation);
            Objects.requireNonNull(executableObservation); StrictJson.text(expectedTool);
        }
    }
    public record Limits(int nativeArtifactBytes, int executableObservationBytes) {
        public Limits {
            StrictJson.require(nativeArtifactBytes > 0 && nativeArtifactBytes <= MAX_NATIVE_ARTIFACT_BYTES
                    && executableObservationBytes > 0 && executableObservationBytes <= StrictJson.EXPLICIT_MAX_BYTES,
                    "Root finite reader budgets required");
        }
    }
    public interface RootOwnedSources {
        Optional<Session> currentSession();
        Optional<RetainedArtifact> selectedSource(Milestone milestone, ProjectionJson originalPayload);
        /** Existing Root allowlist reader must check file identity before/after its bounded exact read. */
        byte[] readExact(ExactRef reference, int maximumBytes) throws IOException;
    }
    private final RootOwnedSources owner;
    private final Limits limits;
    private final AtomicLong calls = new AtomicLong();
    public G2RetainedNativeSourceProvider(RootOwnedSources owner, Limits limits) {
        this.owner = Objects.requireNonNull(owner); this.limits = Objects.requireNonNull(limits);
    }

    @Override public G2CallContextProducer.Result context(Milestone milestone, ProjectionJson payload) {
        Objects.requireNonNull(milestone); Objects.requireNonNull(payload);
        try {
            G2CallContextProducer.requirePayloadToken(payload);
            Optional<Session> current = owner.currentSession();
            if (current.isEmpty()) { return unavailable(G2CallContextProducer.Reason.CURRENT_SESSION_UNAVAILABLE, "Root has no qualified current session"); }
            Optional<RetainedArtifact> selected = owner.selectedSource(milestone, payload);
            if (selected.isEmpty()) { return unavailable(G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING, "actual retained Native source is missing"); }
            Session session = current.orElseThrow(); RetainedArtifact source = selected.orElseThrow();
            if (!session.equals(source.retainedSession())) { return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "retained source belongs to another Root session/Game"); }
            byte[] raw = exact(source.nativeObservation(), limits.nativeArtifactBytes());
            ObjectNode row = StrictJson.object(parse(raw), Set.of("started_at_utc", "ended_at_utc", "elapsed_seconds",
                    "request", "result", "mcp_result_projection_json_utf8_bytes"));
            String observed = instant(row.get("ended_at_utc"));
            String started = instant(row.get("started_at_utc"));
            StrictJson.require(!Instant.parse(started).isAfter(Instant.parse(observed)), "source timestamps reversed");
            StrictJson.require(!row.has("client_error") && row.has("request") && row.has("result"), "completed original owner response required");
            ObjectNode request = StrictJson.object(row.get("request"), Set.of("sequence", "tool", "arguments"));
            object(request.get("arguments"));
            StrictJson.require(source.expectedTool().equals(StrictJson.text(request.get("tool"))), "original Native tool differs");
            BigInteger parentSequence = StrictJson.integer(request.get("sequence"), BigInteger.ONE, BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER));
            ObjectNode result = StrictJson.object(row.get("result"), Set.of("meta", "content", "structured_content", "is_error", "result_type"));
            StrictJson.require(StrictJson.integer(row.get("mcp_result_projection_json_utf8_bytes"), 1, limits.nativeArtifactBytes())
                    == projectionBytes(raw), "original owner result projection byte count differs");
            StrictJson.require(result.get("is_error").isBoolean() && !result.get("is_error").booleanValue()
                    && "complete".equals(StrictJson.text(result.get("result_type"))), "complete successful Native result required");
            ObjectNode snapshot = object(result.get("structured_content"));
            StrictJson.text(snapshot.get("snapshot_id"));
            StrictJson.integer(snapshot.get("revision"), BigInteger.ZERO, StrictJson.UINT64_MAX);
            StrictJson.integer(snapshot.get("native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
            StrictJson.integer(snapshot.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            StrictJson.require(session.episodeRunId().equals(StrictJson.text(snapshot.get("episode_run_id"))), "source episode differs");
            ObjectNode diagnostics = object(snapshot.get("diagnostics")); ObjectNode hello = object(diagnostics.get("hello"));
            StrictJson.require(StrictJson.integer(diagnostics.get("bridge_pid"), 1, 4_294_967_295L) == session.game().pid()
                    && StrictJson.integer(hello.get("pid"), 1, 4_294_967_295L) == session.game().pid(), "Native source Game PID differs");
            BigInteger generation = decimal(session.connectionGeneration(), BigInteger.ZERO, StrictJson.UINT64_MAX);
            StrictJson.require(generation.equals(StrictJson.integer(diagnostics.get("connection_generation"), BigInteger.ZERO, StrictJson.UINT64_MAX))
                    && generation.equals(StrictJson.integer(hello.get("connection_generation"), BigInteger.ZERO, StrictJson.UINT64_MAX)), "Native source connection differs");
            StrictJson.trueValue(hello.get("ck3_build_match"));
            String version = StrictJson.text(hello.get("expected_ck3_version"));
            String nativeSha = StrictJson.text(hello.get("expected_ck3_sha256")).toLowerCase(java.util.Locale.ROOT);
            String measuredVersion = measuredBuild(source.executableObservation(), session, observed);
            StrictJson.require(version.equals(measuredVersion) && nativeSha.equals(session.executable().sha256()),
                    "Native hello and actual exact EXE measurement disagree");
            if (!owner.currentSession().equals(Optional.of(session))) {
                return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "Root session changed during source qualification");
            }
            // Re-read only the two explicitly selected, already retained non-Driver/SAVE artifacts.
            StrictJson.require(java.util.Arrays.equals(raw, exact(source.nativeObservation(), limits.nativeArtifactBytes())), "retained source changed during production");
            long ordinal = calls.incrementAndGet();
            if (ordinal < 1 || ordinal > StrictJson.MAX_SAFE_INTEGER) { return unavailable(G2CallContextProducer.Reason.REQUEST_SEQUENCE_EXHAUSTED, "G2 source request sequence exhausted"); }
            String requestId = "g2:" + milestone.name() + ":" + parentSequence + ":"
                    + source.nativeObservation().sha256().substring(0, 16) + ":" + ordinal;
            G2Source provenance = new G2Source(session.machineId(), observed, version + "@sha256:" + nativeSha, source.nativeObservation());
            return new G2CallContextProducer.Available(new G2CallContextProducer.Context(provenance, requestId, sha256(payload.bytes())));
        } catch (IOException error) {
            return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "Root retained artifact exact read failed");
        } catch (DateTimeException error) {
            return unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED, "retained source timestamp is invalid");
        } catch (IllegalArgumentException error) {
            return unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED, diagnostic(error));
        }
    }
    private String measuredBuild(ExactRef reference, Session session, String nativeObservedAt) throws IOException {
        byte[] raw = exact(reference, limits.executableObservationBytes()); ObjectNode measurement = object(parse(raw));
        StrictJson.require(BUILD_OBSERVATION_SCHEMA.equals(StrictJson.text(measurement.get("schema")))
                && session.machineId().equals(StrictJson.text(measurement.get("machine_id"))), "explicit same-machine EXE observation required");
        StrictJson.require(!Instant.parse(instant(measurement.get("observed_at_utc"))).isAfter(Instant.parse(nativeObservedAt)),
                "EXE observation cannot be restamped after Native source");
        JsonNode observations = measurement.get("observations"); StrictJson.require(observations != null && observations.isArray(), "actual file observation array required");
        ObjectNode executable = null; ObjectNode launcher = null;
        for (JsonNode value : observations) {
            ObjectNode row = object(value); String label = StrictJson.text(row.get("label"));
            if (label.equals("game_exe")) { StrictJson.require(executable == null, "unique EXE observation required"); executable = row; }
            if (label.equals("launcher_settings")) { StrictJson.require(launcher == null, "unique product version observation required"); launcher = row; }
        }
        StrictJson.require(executable != null && launcher != null, "actual EXE and product version observations required");
        StrictJson.trueValue(executable.get("stable_during_read")); StrictJson.trueValue(launcher.get("stable_during_read"));
        ExactRef actualExe = new ExactRef(StrictJson.text(executable.get("path")),
                StrictJson.integer(executable.get("bytes"), 1, StrictJson.MAX_SAFE_INTEGER), StrictJson.text(executable.get("sha256")));
        StrictJson.require(actualExe.equals(session.executable())
                && session.executableFileId().equals(StrictJson.text(executable.get("file_id_decimal")))
                && session.executableMtimeNs().equals(StrictJson.text(executable.get("mtime_ns_decimal"))), "Root current executable identity differs from actual measurement");
        String version = StrictJson.text(launcher.get("raw_version"));
        StrictJson.require(java.util.Arrays.equals(raw, exact(reference, limits.executableObservationBytes())), "EXE measurement changed during production");
        return version;
    }
    private byte[] exact(ExactRef reference, int maximum) throws IOException {
        StrictJson.require(reference.bytes() > 0 && reference.bytes() <= maximum, "Root retained source byte budget");
        byte[] raw = owner.readExact(reference, maximum);
        StrictJson.require(raw != null && raw.length == reference.bytes() && reference.sha256().equals(sha256(raw)), "retained source exact bytes/SHA differ");
        return raw;
    }
    private static JsonNode parse(byte[] raw) throws IOException {
        StrictJson.require(raw.length > 0 && !(raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf), "original UTF8 without BOM required");
        for (byte value : raw) { StrictJson.require(value != 0, "original UTF8 source contains NUL"); }
        String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        return JSON.readTree(text);
    }
    private static long projectionBytes(byte[] raw) throws IOException {
        try (JsonParser parser = JSON.getFactory().createParser(raw)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "owner row object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String field = parser.currentName(); parser.nextToken();
                if ("result".equals(field)) {
                    long start = parser.currentTokenLocation().getByteOffset();
                    parser.skipChildren(); parser.finishToken();
                    return parser.currentLocation().getByteOffset() - start;
                }
                parser.skipChildren();
            }
            throw new IllegalArgumentException("original owner result span missing");
        }
    }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "source object required"); return (ObjectNode) node; }
    private static String instant(JsonNode node) {
        String raw = StrictJson.text(node); Instant instant = Instant.parse(raw);
        StrictJson.require(raw.endsWith("Z") || raw.endsWith("+00:00"), "source UTC observation required"); return instant.toString();
    }
    private static BigInteger decimal(String raw, BigInteger minimum, BigInteger maximum) {
        StrictJson.require(raw != null && raw.matches("0|[1-9][0-9]{0,39}"), "canonical decimal identity required");
        BigInteger value = new BigInteger(raw); StrictJson.require(value.compareTo(minimum) >= 0 && value.compareTo(maximum) <= 0, "decimal identity range"); return value;
    }
    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("JDK SHA-256 unavailable", impossible); }
    }
    private static G2CallContextProducer.Unavailable unavailable(G2CallContextProducer.Reason reason, String detail) {
        return new G2CallContextProducer.Unavailable(reason, detail);
    }
    private static String diagnostic(IllegalArgumentException error) {
        String value = error.getMessage() == null ? "retained source contract rejected" : error.getMessage();
        return value.substring(0, Math.min(512, value.length()));
    }
}
