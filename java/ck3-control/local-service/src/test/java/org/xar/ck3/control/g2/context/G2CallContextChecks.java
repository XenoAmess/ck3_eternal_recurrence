package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Finite synthetic Root producer tests. These fixtures never identify a real Game. */
public final class G2CallContextChecks {
    private static final int BUDGET = 65_536;
    private static final String MACHINE = "synthetic-context-fixture-no-game";
    private static final String VERSION = "synthetic-product-fixture";
    private static final String EXE_SHA = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
    private static final byte[] PAYLOAD = utf8("{\"operation\":\"context-probe\",\"input\":{\"raw\":1.0,\"identity\":18446744073709551615,\"null\":null,\"empty\":[],\"source_path\":\"Z:/never-read-from-body\"}}");
    private static int checks;
    private G2CallContextChecks() { }

    public static void main(String[] args) throws IOException {
        run();
        if (args.length == 1) { export(Path.of(args[0])); }
        else { check(args.length == 0, "zero args or one finite export directory"); }
        System.out.println("G2 call-context synthetic producer checks PASS " + checks);
    }

    public static void run() {
        ProjectionJson payload = ProjectionJson.object(PAYLOAD, BUDGET);
        G2CallContextProducer.RootBinding missing = new G2CallContextProducer.RootBinding();
        unavailable(missing.context(Milestone.M1, payload), G2CallContextProducer.Reason.ROOT_PROVIDER_MISSING);
        Fixture fixture = new Fixture();
        G2RetainedNativeSourceProvider producer = fixture.provider();
        G2CallContextProducer.RootBinding root = new G2CallContextProducer.RootBinding();
        root.install(producer); root.install(producer);
        ProjectionJson padded = ProjectionJson.object(utf8(" \n{} \t"), BUDGET);
        rejects(() -> root.context(Milestone.M1, padded));
        rejects(() -> new G2CallContextWire.Input(Milestone.M1, padded));
        unavailable(producer.context(Milestone.M1, padded), G2CallContextProducer.Reason.SOURCE_REJECTED);
        rejects(() -> root.context(Milestone.M1, ProjectionJson.object(utf8("{} "), BUDGET)));
        rejects(() -> root.install(fixture.provider()));
        G2CallContextProducer.Context first = available(root.context(Milestone.M1, payload));
        check(first.source().machineId().equals(MACHINE), "machine derives from qualified Root owner");
        check(first.source().observedAtUtc().equals("2026-10-22T20:00:01Z"), "UTC derives from original row");
        check(first.source().exactBuild().equals(VERSION + "@sha256:" + EXE_SHA), "build derives from exact EXE measurement and native hello");
        check(first.source().sourceRef().equals(fixture.nativeRef), "original Native artifact exact ref");
        check(first.requestId().startsWith("g2:M1:23:" + fixture.nativeRef.sha256().substring(0, 16) + ":"), "request binds actual parent sequence and artifact");
        check(first.payloadSha256().equals(G2RetainedNativeSourceProvider.sha256(PAYLOAD)), "actual original payload SHA");
        G2CallContextProducer.Context second = available(root.context(Milestone.M1, payload));
        check(!first.requestId().equals(second.requestId()) && first.source().equals(second.source()), "unique ordinal never restamps retained source");
        check(first.equals(G2CallContextWire.decodeContext(G2CallContextWire.encodeContext(first))), "context persistence roundtrip");
        byte[] input = input(PAYLOAD);
        G2CallContextWire.Input decoded = G2CallContextWire.decodeInput(input);
        check(decoded.milestone() == Milestone.M1 && Arrays.equals(decoded.payload().bytes(), PAYLOAD), "wire preserves decimal/uint64/null/empty raw payload span");
        G2Request request = new G2Request(first.requestId(), decoded.milestone(), first.source(), decoded.payload());
        check(request.equals(G2Wire.decodeRequest(G2Wire.encodeRequest(request))), "actual shared host request consumer roundtrip");
        rejects(() -> G2CallContextWire.decodeInput(utf8("{\"milestone\":\"G2-M1\",\"payload\":{},\"source_ref\":{\"path\":\"Z:/forbidden\"}}")));
        rejects(() -> G2CallContextWire.decodeInput(utf8("{\"milestone\":\"G2-M1\",\"payload\":{},\"payload\":{}}")));
        rejects(() -> G2CallContextWire.decodeInput(utf8("{\"milestone\":true,\"payload\":{}}")));
        rejects(() -> G2CallContextWire.decodeInput(utf8("{\"milestone\":\"G2-M1\",\"payload\":null}")));
        rejects(() -> G2CallContextWire.decodeInput(utf8("{\"milestone\":\"G2-M1\",\"payload\":[]}")));
        rejects(() -> G2CallContextWire.decodeInput(utf8("{\"milestone\":\"G2-M1\"}")));
        rejects(() -> G2CallContextWire.decodeInput(utf8("{\"milestone\":\"G2-M1\",\"payload\":{}}{}")));
        byte[] context = G2CallContextWire.encodeContext(first);
        rejects(() -> G2CallContextWire.decodeContext(utf8(new String(context, StandardCharsets.UTF_8).replace("\"schema\":\"xar.g2-call-context/v1\"", "\"schema\":true"))));
        G2CallContextProducer.RootBinding misbound = new G2CallContextProducer.RootBinding();
        misbound.install((milestone, original) -> new G2CallContextProducer.Available(new G2CallContextProducer.Context(
                first.source(), first.requestId(), "0".repeat(64))));
        unavailable(misbound.context(Milestone.M1, payload), G2CallContextProducer.Reason.SOURCE_REJECTED);

        Fixture noSession = new Fixture(); noSession.current = Optional.empty();
        unavailable(noSession.provider().context(Milestone.M1, payload), G2CallContextProducer.Reason.CURRENT_SESSION_UNAVAILABLE);
        Fixture noSource = new Fixture(); noSource.selected = Optional.empty();
        unavailable(noSource.provider().context(Milestone.M1, payload), G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING);
        Fixture changed = new Fixture();
        G2RetainedNativeSourceProvider.Session before = changed.current.orElseThrow();
        changed.current = Optional.of(new G2RetainedNativeSourceProvider.Session(before.machineId(), before.sessionId(),
                new G2RetainedNativeSourceProvider.GameIdentity(1234, "18446744073709551614"), before.episodeRunId(),
                before.connectionGeneration(), before.executable(), before.executableFileId(), before.executableMtimeNs()));
        unavailable(changed.provider().context(Milestone.M1, payload), G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED);
        Fixture unreadable = new Fixture(); unreadable.ioFailure = true;
        unavailable(unreadable.provider().context(Milestone.M1, payload), G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED);
        Fixture drift = new Fixture(); drift.bytes.put(drift.nativeRef, utf8("{}"));
        unavailable(drift.provider().context(Milestone.M1, payload), G2CallContextProducer.Reason.SOURCE_REJECTED);
        Fixture midflight = new Fixture(); midflight.changeSessionOnRead = true;
        unavailable(midflight.provider().context(Milestone.M1, payload), G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED);
        rejectedNative("\"sequence\":23", "\"sequence\":true");
        rejectedNative("\"sequence\":23", "\"sequence\":23.0");
        rejectedNative("\"bridge_pid\":1234", "\"bridge_pid\":1234.0");
        rejectedNative("\"revision\":42", "\"revision\":42.0");
        rejectedNative("\"connection_generation\":9007199254740993", "\"connection_generation\":9007199254740993.0");
        rejectedNative("\"ck3_build_match\":true", "\"ck3_build_match\":1");
        rejectedNative("\"episode_run_id\":\"synthetic-episode\"", "\"episode_run_id\":\"other-episode\"");
        rejectedNative("\"result_type\":\"complete\"", "\"result_type\":\"partial\"");
        rejectedNative("\"is_error\":false", "\"is_error\":true");
        rejectedNative("\"expected_ck3_version\":\"" + VERSION + "\"", "\"expected_ck3_version\":null");
        rejectedNative("\"expected_ck3_version\":\"" + VERSION + "\"", "\"game_version\":\"" + VERSION + "\"");
        rejectedNative("2026-10-22T20:00:01Z", "not-a-date");
        rejectedNative("2026-10-22T20:00:01Z", "2026-10-22T19:59:59Z");
        rejectedMeasurement("\"machine_id\":\"" + MACHINE + "\"", "\"machine_id\":\"another-machine\"");
        rejectedMeasurement("\"stable_during_read\":true", "\"stable_during_read\":false");
        rejectedMeasurement("\"file_id_decimal\":\"18446744073709551617\"", "\"file_id_decimal\":\"18446744073709551616\"");
        rejectedMeasurement("\"raw_version\":\"" + VERSION + "\"", "\"raw_version\":\"unrelated-version\"");
        rejectedMeasurement("2026-10-22T20:00:00Z", "2026-10-22T20:00:02Z");
        rejects(() -> new G2RetainedNativeSourceProvider.GameIdentity(1234, "01"));
        rejects(() -> new G2RetainedNativeSourceProvider.GameIdentity(1234, "18446744073709551616"));
        Fixture narrow = new Fixture();
        unavailable(new G2RetainedNativeSourceProvider(narrow, new G2RetainedNativeSourceProvider.Limits(1, 1)).context(Milestone.M1, payload),
                G2CallContextProducer.Reason.SOURCE_REJECTED);
        check(fixture.reads == 8, "two accepted contexts read only the two explicit refs twice each");
    }

    private static void rejectedNative(String before, String after) {
        Fixture fixture = new Fixture(); fixture.replaceNative(before, after);
        unavailable(fixture.provider().context(Milestone.M1, ProjectionJson.object(PAYLOAD, BUDGET)), G2CallContextProducer.Reason.SOURCE_REJECTED);
    }
    private static void rejectedMeasurement(String before, String after) {
        Fixture fixture = new Fixture(); fixture.replaceMeasurement(before, after);
        unavailable(fixture.provider().context(Milestone.M1, ProjectionJson.object(PAYLOAD, BUDGET)), G2CallContextProducer.Reason.SOURCE_REJECTED);
    }
    private static void export(Path root) throws IOException {
        Files.createDirectory(root);
        Fixture fixture = new Fixture();
        G2CallContextProducer.Context context = available(fixture.provider().context(Milestone.M1, ProjectionJson.object(PAYLOAD, BUDGET)));
        Files.write(root.resolve("context-input.json"), input(PAYLOAD));
        Files.write(root.resolve("context-result.json"), G2CallContextWire.encodeContext(context));
        Files.write(root.resolve("evaluate-request.json"), G2Wire.encodeRequest(new G2Request(context.requestId(), Milestone.M1,
                context.source(), ProjectionJson.object(PAYLOAD, BUDGET))));
        Files.write(root.resolve("original-synthetic-native.json"), fixture.bytes.get(fixture.nativeRef));
        Files.write(root.resolve("original-synthetic-exe-measurement.json"), fixture.bytes.get(fixture.measurementRef));
        ObjectNode manifest = StrictJson.object();
        manifest.put("schema", "xar.g2-call-context-synthetic-vector/v1"); manifest.put("machine_id", MACHINE);
        manifest.put("qualification", "synthetic-only; zero Game/Driver/SAVE/live-source credit");
        manifest.put("source_ref_path", fixture.nativeRef.path()); manifest.put("source_ref_bytes", fixture.nativeRef.bytes());
        manifest.put("source_ref_sha256", fixture.nativeRef.sha256()); manifest.put("checks", checks);
        Files.write(root.resolve("synthetic-manifest.json"), StrictJson.canonical(manifest, BUDGET));
    }
    private static byte[] input(byte[] payload) {
        return utf8("{\"milestone\":\"G2-M1\",\"payload\":" + new String(payload, StandardCharsets.UTF_8) + "}");
    }
    private static G2CallContextProducer.Context available(G2CallContextProducer.Result result) {
        check(result instanceof G2CallContextProducer.Available, "expected available source: " + result);
        return ((G2CallContextProducer.Available) result).context();
    }
    private static void unavailable(G2CallContextProducer.Result result, G2CallContextProducer.Reason reason) {
        check(result instanceof G2CallContextProducer.Unavailable unavailable && unavailable.reason() == reason,
                "expected typed unavailable " + reason + ": " + result);
    }
    private static void rejects(Runnable action) {
        try { action.run(); } catch (IllegalArgumentException | IllegalStateException expected) { checks++; return; }
        throw new AssertionError("expected strict rejection");
    }
    private static void check(boolean accepted, String message) { if (!accepted) { throw new AssertionError(message); } checks++; }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    private static final class Fixture implements G2RetainedNativeSourceProvider.RootOwnedSources {
        private final Map<ExactRef, byte[]> bytes = new HashMap<>();
        private Optional<G2RetainedNativeSourceProvider.Session> current;
        private Optional<G2RetainedNativeSourceProvider.RetainedArtifact> selected;
        private ExactRef nativeRef;
        private ExactRef measurementRef;
        private int reads;
        private boolean ioFailure;
        private boolean changeSessionOnRead;
        private Fixture() {
            ExactRef exe = new ExactRef("synthetic:/fixture/game.exe", 91, EXE_SHA);
            current = Optional.of(new G2RetainedNativeSourceProvider.Session(MACHINE, "synthetic-session",
                    new G2RetainedNativeSourceProvider.GameIdentity(1234, "18446744073709551615"), "synthetic-episode",
                    "9007199254740993", exe, "18446744073709551617", "1234567890123456789"));
            byte[] nativeRow = utf8("{\"started_at_utc\":\"2026-10-22T20:00:00Z\",\"ended_at_utc\":\"2026-10-22T20:00:01Z\",\"elapsed_seconds\":1.0,\"request\":{\"sequence\":23,\"tool\":\"ck3_semantic_snapshot\",\"arguments\":{}},\"result\":{\"meta\":{},\"content\":[],\"is_error\":false,\"result_type\":\"complete\",\"structured_content\":{\"snapshot_id\":\"synthetic-snapshot\",\"revision\":42,\"native_revision\":43,\"date_raw\":123,\"episode_run_id\":\"synthetic-episode\",\"diagnostics\":{\"bridge_pid\":1234,\"connection_generation\":9007199254740993,\"hello\":{\"pid\":1234,\"connection_generation\":9007199254740993,\"ck3_build_match\":true,\"expected_ck3_version\":\"" + VERSION + "\",\"expected_ck3_sha256\":\"" + EXE_SHA + "\"}}}},\"mcp_result_projection_json_utf8_bytes\":0}");
            byte[] measurement = utf8("{\"schema\":\"xar.resume56-current-game-files-readonly-observation/v1\",\"machine_id\":\"" + MACHINE + "\",\"observed_at_utc\":\"2026-10-22T20:00:00Z\",\"observations\":[{\"label\":\"game_exe\",\"path\":\"synthetic:/fixture/game.exe\",\"bytes\":91,\"sha256\":\"" + EXE_SHA + "\",\"file_id_decimal\":\"18446744073709551617\",\"mtime_ns_decimal\":\"1234567890123456789\",\"stable_during_read\":true},{\"label\":\"launcher_settings\",\"stable_during_read\":true,\"raw_version\":\"" + VERSION + "\"}]}");
            String original = new String(nativeRow, StandardCharsets.UTF_8);
            int resultStart = original.indexOf("\"result\":") + "\"result\":".length();
            int resultEnd = original.indexOf(",\"mcp_result_projection_json_utf8_bytes\":");
            int projectionBytes = utf8(original.substring(resultStart, resultEnd)).length;
            nativeRow = utf8(original.replace("\"mcp_result_projection_json_utf8_bytes\":0",
                    "\"mcp_result_projection_json_utf8_bytes\":" + projectionBytes));
            nativeRef = register("synthetic:/fixture/original-native-row.json", nativeRow);
            measurementRef = register("synthetic:/fixture/original-exe-measurement.json", measurement);
            select();
        }
        private ExactRef register(String path, byte[] raw) {
            ExactRef ref = new ExactRef(path, raw.length, G2RetainedNativeSourceProvider.sha256(raw)); bytes.put(ref, raw); return ref;
        }
        private void select() {
            selected = Optional.of(new G2RetainedNativeSourceProvider.RetainedArtifact(current.orElseThrow(), nativeRef,
                    measurementRef, "ck3_semantic_snapshot"));
        }
        private void replaceNative(String before, String after) {
            String raw = new String(bytes.get(nativeRef), StandardCharsets.UTF_8); check(raw.contains(before), "mutation matches source token");
            String replaced = raw.replace(before, after);
            int resultStart = replaced.indexOf("\"result\":") + "\"result\":".length();
            int resultEnd = replaced.indexOf(",\"mcp_result_projection_json_utf8_bytes\":");
            int projectionBytes = utf8(replaced.substring(resultStart, resultEnd)).length;
            replaced = replaced.replaceAll("\"mcp_result_projection_json_utf8_bytes\":[0-9]+", "\"mcp_result_projection_json_utf8_bytes\":" + projectionBytes);
            nativeRef = register(nativeRef.path(), utf8(replaced)); select();
        }
        private void replaceMeasurement(String before, String after) {
            String raw = new String(bytes.get(measurementRef), StandardCharsets.UTF_8); check(raw.contains(before), "mutation matches measured token");
            measurementRef = register(measurementRef.path(), utf8(raw.replace(before, after))); select();
        }
        private G2RetainedNativeSourceProvider provider() {
            return new G2RetainedNativeSourceProvider(this, new G2RetainedNativeSourceProvider.Limits(BUDGET, BUDGET));
        }
        @Override public Optional<G2RetainedNativeSourceProvider.Session> currentSession() { return current; }
        @Override public Optional<G2RetainedNativeSourceProvider.RetainedArtifact> selectedSource(Milestone milestone, ProjectionJson payload) { return selected; }
        @Override public byte[] readExact(ExactRef reference, int maximumBytes) throws IOException {
            reads++;
            if (ioFailure) { throw new IOException("synthetic retained source unavailable"); }
            byte[] value = bytes.get(reference);
            if (value == null || value.length > maximumBytes) { throw new IOException("reference outside explicit synthetic Root registry"); }
            if (changeSessionOnRead) { current = Optional.empty(); }
            return value.clone();
        }
    }
}
