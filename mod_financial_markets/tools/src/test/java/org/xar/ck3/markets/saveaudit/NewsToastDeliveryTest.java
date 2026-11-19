package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.io.CleanupMode;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveDecoder;
import org.xar.ck3.save.SaveJson;

/** Declared software observations/physical text SAVE, real JSON/Inspection/decoder/stream pipeline. */
final class NewsToastDeliveryTest {
    @TempDir Path directory;
    private int nextFile;
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final String ENTRY = "50331650";
    private static final String EXE = "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC";
    private static Path repository() { return Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent(); }
    private static Path java() {
        Path windows = Path.of(System.getProperty("java.home"), "bin", "java.exe");
        return Files.isRegularFile(windows) ? windows : Path.of(System.getProperty("java.home"), "bin", "java");
    }
    private static ObjectNode scope(String name, String kind, int tag, String id) {
        ObjectNode value = JSON.objectNode(); value.put("name", name); value.put("kind", kind); value.put("observed_tag", tag);
        value.put("identity_available", true); value.put("identity", id); value.putNull("unavailable_reason"); return value;
    }
    private static ObjectNode toast(int viewer, int actor) {
        ObjectNode t = JSON.objectNode();
        t.put("schema", "ck3_1210_current_interface_toast_result_v1"); t.put("step", "query-current-interface-toast-v1");
        t.put("game_version", "1.21.0"); t.put("executable_sha256", EXE); t.put("adapter_id", "ck3-1.21.0-msvc-x64");
        t.put("backend", "ck3-1.21.0-native-headless-main-thread"); t.put("status", "available"); t.put("accepted", true);
        t.put("snapshot_id", "native:11"); t.put("native_revision", "11"); t.put("connection_generation", "3");
        t.put("query_sequence", "9007199254740993"); t.put("owner_thread_id", 77);
        for (String name : List.of("application_main_observed", "full_snapshot_before_verified", "full_snapshot_after_verified", "source_abi_pins_verified", "read_only")) t.put(name, true);
        for (String name : List.of("effect_attempted", "recipient_identity_available", "news_origin_available", "delivery_confirmed")) t.put(name, false);
        t.put("stage", "visible"); t.put("completed_application_frame", "9007199254740995"); t.put("queue_count", 1);
        t.put("title", "software-owned news title"); t.put("description", "declared software observation; no Game delivery");
        t.putArray("saved_gui_scopes"); var scopes = t.putArray("saved_script_scopes");
        scopes.add(scope("xfm_news_display_entry", "story", 22, ENTRY));
        scopes.add(scope("xfm_news_recipient", "character", 4, Integer.toString(viewer)));
        scopes.add(scope("xfm_news_actor", "character", 4, Integer.toString(actor)));
        t.putNull("unavailable_reason"); t.put("public_revision", "3"); t.put("game_pid", 42); t.put("viewer_played_character_id", viewer); t.put("date_raw", 53144328);
        return t;
    }
    private NewsToastDelivery.Request request(ObjectNode toast, String scene) throws Exception {
        Path observation = directory.resolve("toast-" + nextFile++ + ".json");
        Files.write(observation, SaveJson.write(toast)); Path save = directory.resolve("save-" + nextFile++ + ".ck3"); Files.writeString(save, scene);
        return new NewsToastDelivery.Request(1, "software-news-join-fixture", repository().toString(), FilePins.pin(observation), FilePins.pin(save), FilePins.pin(java()));
    }
    private static SaveDecoder.Launcher child(boolean fail, AtomicInteger calls) {
        return (executable, input) -> {
            calls.incrementAndGet();
            return new ProcessBuilder(executable.toString(), "-Xms16m", "-Xmx64m", "-cp", System.getProperty("surefire.test.class.path", System.getProperty("java.class.path")),
                    Child.class.getName(), input.toString(), Boolean.toString(fail)).start();
        };
    }
    public static final class Child {
        private Child() { }
        public static void main(String[] args) throws IOException { System.out.print(Files.readString(Path.of(args[0]))); if (Boolean.parseBoolean(args[1])) System.exit(7); }
    }
    private static String value(String name, long n) {
        return "{flag=" + name + " data={type=value" + (n == 0 ? "" : " identity=" + BigInteger.valueOf(n).multiply(BigInteger.valueOf(100000))) + "}}";
    }
    private static String ref(String name, String type, String id) { return "{flag=" + name + " data={type=" + type + " identity=" + id + "}}"; }
    private static String scene(long actorBits) {
        String actor = Long.toString(actorBits);
        String source = "76={story_cycle=xfm_finance_account variables={data={" + value("xfm_news_fact_counter", 7) + value("xfm_news_last_fact", 7)
                + value("xfm_news_kind", 5) + value("xfm_news_scene", 13) + ref("xfm_news_actor", "char", actor) + "}}}";
        String entry = ENTRY + "={story_cycle=xfm_news_entry variables={data={" + value("xfm_news_id", 9) + value("xfm_news_event_id", 7)
                + value("xfm_news_kind", 5) + value("xfm_news_day", 0) + value("xfm_news_scene", 13) + ref("xfm_news_source", "story", "76")
                + ref("xfm_news_actor", "char", actor) + "}}}";
        return "meta_data={version=\"1.21.0\" save_game_version=19 meta_date=1066.9.15 nested={checked=yes}} stories={active={" + source + entry + "}}";
    }

    @Test void realInspectionTwiceVerifiesExactNewsSourceAndFullMetadata() throws Exception {
        AtomicInteger calls = new AtomicInteger(); NewsToastDelivery.Request request = request(toast(31254, 42), scene(42));
        NewsToastDelivery.Report report = NewsToastDelivery.inspect(request, child(false, calls));
        assertEquals(NewsToastDelivery.Assessment.LOCAL_NATIVE_JOIN_MATCH, report.assessment()); assertTrue(report.sourceJoinMatched());
        assertEquals(3, calls.get()); assertEquals(3, report.passes().size());
        assertEquals(2, report.passes().get(0).selected().size()); assertEquals(3, report.passes().get(1).selected().size());
        assertEquals(report.passes().get(1).selected(), report.passes().get(2).selected());
        assertEquals("7", report.entries().getFirst().eventId()); assertNotEquals(report.entries().getFirst().eventId(), report.toast().identity().nativeRevision());
        assertEquals("0", report.entries().getFirst().day()); assertEquals("76", report.sources().getFirst().storyId());
        assertFalse(report.deliveryConfirmed()); assertFalse(report.allHumanDeliveryConfirmed()); assertFalse(report.gameStarted()); assertFalse(report.financialCertified());
        assertEquals(report, SaveJson.read(SaveJson.write(report), NewsToastDelivery.Report.class));
        assertFalse(report.producers().auditSources().isEmpty()); assertFalse(report.passes().getFirst().producer().loadedCode().isEmpty());
    }
    @Test void signedCharacterBitsAndZeroArePreservedAtActualReaderBoundary() throws Exception {
        for (int actor : List.of(0, -2147483646, Integer.MAX_VALUE)) {
            AtomicInteger calls = new AtomicInteger(); var report = NewsToastDelivery.inspect(request(toast(actor, actor), scene(Integer.toUnsignedLong(actor))), child(false, calls));
            assertEquals(NewsToastDelivery.Assessment.LOCAL_NATIVE_JOIN_MATCH, report.assessment()); assertEquals(actor, report.entries().getFirst().actorCharacterId());
            assertEquals(actor, report.sources().getFirst().actorCharacterId()); assertEquals(actor, report.toast().identity().viewerCharacterId());
        }
    }
    @Test void unsigned64CharacterReferenceIsNotGuessedOrReducedModulo32() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.inspect(request(toast(-2, -2), scene(42).replace("type=char identity=42", "type=char identity=18446744073709551614")), child(false, calls)));
    }
    @Test void hiddenPendingEmptyAndUnavailableCannotReadSaveOrClaimDelivery() throws Exception {
        for (String stage : List.of("hidden", "visible_pending_frame", "empty", "unavailable")) {
            ObjectNode t = toast(31254, 42); t.put("stage", stage);
            if (stage.equals("empty") || stage.equals("unavailable")) {
                t.put("queue_count", 0); t.put("title", ""); t.put("description", ""); t.putArray("saved_gui_scopes"); t.putArray("saved_script_scopes");
            }
            if (stage.equals("unavailable")) { t.put("status", "unavailable"); t.put("accepted", false); t.put("completed_application_frame", "0"); t.put("unavailable_reason", "toast_mailbox_not_completed"); }
            AtomicInteger calls = new AtomicInteger(); var report = NewsToastDelivery.inspect(request(t, scene(42)), child(false, calls));
            assertEquals(0, calls.get()); assertEquals(NewsToastDelivery.Assessment.UNAVAILABLE, report.assessment()); assertFalse(report.sourceJoinMatched());
            assertEquals(report, SaveJson.read(SaveJson.write(report), NewsToastDelivery.Report.class));
            assertTrue(report.entries().isEmpty()); assertTrue(report.sources().isEmpty());
        }
    }
    @Test void onlyActualNamedRolesCanJoinViewerAndActor() throws Exception {
        ObjectNode t = toast(31254, 42); ((ObjectNode)t.get("saved_script_scopes").get(1)).put("name", "CHARACTER");
        AtomicInteger calls = new AtomicInteger(); var missing = NewsToastDelivery.inspect(request(t, scene(42)), child(false, calls));
        assertEquals(NewsToastDelivery.Reason.REQUIRED_NAMED_IDENTITY_UNAVAILABLE, missing.reason()); assertEquals(0, calls.get());
        t = toast(31254, 42); ((ObjectNode)t.get("saved_script_scopes").get(1)).put("identity", "31255");
        var foreign = NewsToastDelivery.inspect(request(t, scene(42)), child(false, calls));
        assertEquals(NewsToastDelivery.Reason.RECIPIENT_DIFFERS_FROM_VIEWER, foreign.reason()); assertEquals(0, calls.get());
        t = toast(31254, 42); ObjectNode unknown = (ObjectNode)t.get("saved_script_scopes").get(1);
        unknown.put("kind", "unsupported"); unknown.put("observed_tag", 36); unknown.put("identity_available", false);
        unknown.putNull("identity"); unknown.put("unavailable_reason", "scope_tag_not_admitted");
        var unavailable = NewsToastDelivery.inspect(request(t, scene(42)), child(false, calls));
        assertEquals(NewsToastDelivery.Reason.REQUIRED_NAMED_IDENTITY_UNAVAILABLE, unavailable.reason()); assertEquals(0, calls.get());
        assertEquals(unavailable, SaveJson.read(SaveJson.write(unavailable), NewsToastDelivery.Report.class));
        var actor = NewsToastDelivery.inspect(request(toast(31254, 41), scene(42)), child(false, new AtomicInteger()));
        assertEquals(NewsToastDelivery.Reason.ACTOR_DIFFERS_FROM_NEWS, actor.reason()); assertFalse(actor.sourceJoinMatched());
    }
    @Test void currentSourceEventAndFactFieldsMustMatchImmutableEntry() throws Exception {
        String later = scene(42).replace("flag=xfm_news_fact_counter data={type=value identity=700000}", "flag=xfm_news_fact_counter data={type=value identity=800000}");
        var report = NewsToastDelivery.inspect(request(toast(31254, 42), later), child(false, new AtomicInteger()));
        assertEquals(NewsToastDelivery.Reason.SOURCE_EVENT_NO_LONGER_CURRENT, report.reason());
        String changed = scene(42).replaceFirst("flag=xfm_news_scene data=\\{type=value identity=1300000", "flag=xfm_news_scene data={type=value identity=1400000");
        report = NewsToastDelivery.inspect(request(toast(31254, 42), changed), child(false, new AtomicInteger()));
        assertEquals(NewsToastDelivery.Reason.SOURCE_FACT_DIFFERS_FROM_NEWS, report.reason()); assertFalse(report.sourceJoinMatched());
    }
    @Test void actualCompleteMetadataDuplicateBlockCannotHideBehindDirectScalarScope() throws Exception {
        for (String metadata : List.of("version=\"1.20.0.4\" save_game_version=19", "version=\"1.21.0\" save_game_version=18", "version=\"1.21.0\" version={bad=yes} save_game_version=19")) {
            String save = scene(42).replace("version=\"1.21.0\" save_game_version=19", metadata);
            assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.inspect(request(toast(31254, 42), save), child(false, new AtomicInteger())));
        }
    }
    @Test void decodeFailureAndSelectedRecordDriftCannotPublishPartialJoin() throws Exception {
        var request = request(toast(31254, 42), scene(42));
        assertThrows(IOException.class, () -> NewsToastDelivery.inspect(request, child(true, new AtomicInteger())));
        AtomicInteger calls = new AtomicInteger();
        SaveDecoder.Launcher drift = (executable, input) -> new ProcessBuilder(executable.toString(), "-Xms16m", "-Xmx64m", "-cp",
                System.getProperty("surefire.test.class.path", System.getProperty("java.class.path")), DriftChild.class.getName(), input.toString(), Integer.toString(calls.incrementAndGet())).start();
        assertThrows(IOException.class, () -> NewsToastDelivery.inspect(request, drift)); assertEquals(3, calls.get());
    }
    public static final class DriftChild {
        private DriftChild() { }
        public static void main(String[] args) throws IOException {
            String value = Files.readString(Path.of(args[0]));
            if (args[1].equals("3")) value = value.replace("flag=xfm_news_day data={type=value}", "flag=xfm_news_day data={type=value identity=100000}");
            System.out.print(value);
        }
    }
    @Test void actualJsonCodecRejectsAliasesTypesInvalidIdsAndForgedClaims() throws Exception {
        for (String id : List.of("-1", "01", "-0", "2147483648", "-2147483649")) {
            ObjectNode t = toast(31254, 42); ((ObjectNode)t.get("saved_script_scopes").get(1)).put("identity", id);
            assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(t)));
        }
        for (String key : List.of("delivery_confirmed", "recipient_identity_available", "news_origin_available", "effect_attempted")) {
            ObjectNode t = toast(31254, 42); t.put(key, true); assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(t)));
        }
        for (String sha : List.of(EXE.toLowerCase(java.util.Locale.ROOT), "0".repeat(64))) {
            ObjectNode wrongExe = toast(31254, 42); wrongExe.put("executable_sha256", sha);
            assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(wrongExe)), "exact SDK canonical SHA required: " + sha);
        }
        ObjectNode badRevision = toast(31254, 42); badRevision.put("native_revision", 11);
        assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(badRevision)));
        ObjectNode badViewer = toast(31254, 42); badViewer.put("viewer_played_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(badViewer)));
        ObjectNode alias = toast(31254, 42); alias.set("saved_script_scope_names", alias.remove("saved_script_scopes"));
        assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(alias)));
        ObjectNode tooMany = toast(31254, 42); var many = tooMany.putArray("saved_script_scopes");
        for (int i = 0; i < 64; i++) many.add(scope("scope_" + i, "story", 22, ENTRY));
        tooMany.withArray("saved_gui_scopes").add(scope("extra", "story", 22, ENTRY));
        assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(tooMany)));
        ObjectNode conflicting = toast(31254, 42); conflicting.withArray("saved_gui_scopes").add(scope("xfm_news_display_entry", "story", 22, "50331651"));
        assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(conflicting)));
        ObjectNode invalidStory = toast(31254, 42); ((ObjectNode)invalidStory.get("saved_script_scopes").get(0)).put("identity", "4294967295");
        assertThrows(IllegalArgumentException.class, () -> NewsToastDelivery.readToast(SaveJson.write(invalidStory)));
        String duplicate = new String(SaveJson.write(toast(31254, 42)), java.nio.charset.StandardCharsets.UTF_8).replaceFirst("\\{", "{\"stage\":\"visible\",");
        assertThrows(IOException.class, () -> NewsToastDelivery.readToast(duplicate.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void actualProducerPacketCanFeedSameStrictJavaBoundaryWithDeclaredSoftwarePublicBinding(
            @TempDir(cleanup = CleanupMode.ON_SUCCESS) Path sdkDirectory) throws Exception {
        // Only the actual SDK contract normalizer may adapt Native wire to its
        // public DTO. The Full/public binding below is explicitly software.
        String actual = System.getenv("XAR_TOAST_CPP_PRODUCER_PACKET");
        Path packet;
        if (actual == null) {
            ObjectNode raw = toast(31254, 42);
            raw.remove(List.of("public_revision", "game_pid", "viewer_played_character_id", "date_raw"));
            ObjectNode software = JSON.objectNode(); software.put("type", "command_result"); software.put("protocol_version", 1);
            software.put("request_id", "toast-fixture"); software.put("ok", true); software.set("result", raw);
            packet = sdkDirectory.resolve("declared-software-packet.json"); Files.write(packet, SaveJson.write(software));
        } else packet = Path.of(actual).toAbsolutePath().normalize();
        byte[] originalBytes = NewsToastDelivery.readBounded(packet, 256 * 1024);
        JsonNode original = SaveJson.read(originalBytes, JsonNode.class);
        Path shared = Path.of(System.getProperty("xfm.shared.source", repository().toString())).toAbsolutePath().normalize();
        Path exporter = repository().resolve("mod_financial_markets/tools/src/test/resources/saveaudit/normalize_toast_sdk.py");
        Path stdout = sdkDirectory.resolve("actual-sdk-public-toast.stdout.json"), stderr = sdkDirectory.resolve("actual-sdk-public-toast.stderr.json");
        var process = new ProcessBuilder(System.getProperty("xfm.python", "python"), "-B", "-X", "utf8", exporter.toString(),
                "--shared-source", shared.toString(), "--packet", packet.toString(), "--input-kind",
                actual == null ? "declared-software-packet" : "cpp-producer-original")
                .directory(shared.toFile()).redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        boolean completed;
        try { completed = process.waitFor(30, TimeUnit.SECONDS); }
        finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); } }
        String diagnostic = Files.exists(stderr) ? new String(NewsToastDelivery.readBounded(stderr, 64 * 1024), java.nio.charset.StandardCharsets.UTF_8) : "missing stderr";
        assertTrue(completed, "SDK normalizer timed out; stdout=" + stdout + "; stderr=" + stderr + ": " + diagnostic);
        assertEquals(0, process.exitValue(), "SDK normalizer failed; stdout=" + stdout + "; stderr=" + stderr + ": " + diagnostic);
        assertArrayEquals(originalBytes, NewsToastDelivery.readBounded(packet, 256 * 1024), "whole original packet must remain byte-identical");
        JsonNode provenance = SaveJson.read(diagnostic.getBytes(java.nio.charset.StandardCharsets.UTF_8), JsonNode.class);
        assertEquals("xfm-test-actual-sdk-normalizer-export-v1", provenance.get("schema").textValue());
        assertEquals(FilePins.pin(packet).sha256(), provenance.get("input_sha256").textValue());
        assertTrue(provenance.get("software_public_binding").booleanValue());
        assertFalse(provenance.get("driver_service_executed").booleanValue()); assertFalse(provenance.get("game_started").booleanValue());
        assertFalse(provenance.get("delivery_confirmed").booleanValue());
        assertEquals(3, provenance.get("sdk_sources").size());
        for (String leaf : List.of("gui_window_tree_contract", "frontend_gui_route_contract", "version_identity")) {
            Path source = shared.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/" + leaf + ".py");
            assertTrue(provenance.get("sdk_sources").findValuesAsText("sha256").contains(FilePins.pin(source).sha256()), "actual SDK source required: " + source);
        }
        byte[] normalizedBytes = NewsToastDelivery.readBounded(stdout, 256 * 1024);
        JsonNode normalized = SaveJson.read(normalizedBytes, JsonNode.class);
        assertEquals(EXE, normalized.get("executable_sha256").textValue(), "actual SDK canonical SHA must reach Java unchanged");
        var parsed = NewsToastDelivery.readToast(normalizedBytes);
        assertEquals(NewsToastDelivery.Stage.VISIBLE, parsed.stage());
        if (actual != null) {
            assertEquals("50331650", parsed.scriptScopes().get(0).identity()); assertEquals("-2147483646", parsed.scriptScopes().get(1).identity());
        } else assertEquals(ENTRY, parsed.scriptScopes().get(0).identity());
        assertNull(original.get("result").get("public_revision"));
    }
    @Test void namedCommandUsesRealVerifierReaderAndCreateOnlyReport() throws Exception {
        var request = request(toast(31254, 42), scene(42)); Path inputs = directory.resolve("inputs.json"), output = directory.resolve("report.json");
        Files.write(inputs, SaveJson.write(request)); AtomicInteger calls = new AtomicInteger();
        String[] argv = {"--inputs", inputs.toString(), "--output", output.toString()};
        assertEquals(0, NewsToastAuditCommand.run(argv, child(false, calls))); assertEquals(3, calls.get());
        JsonNode report = SaveJson.read(Files.readAllBytes(output), JsonNode.class);
        assertTrue(report.get("sourceJoinMatched").booleanValue()); assertFalse(report.get("deliveryConfirmed").booleanValue());
        assertEquals(1, NewsToastAuditCommand.run(argv, child(false, calls))); assertEquals(3, calls.get());
        assertEquals(1, NewsToastAuditCommand.run(new String[]{"--inputs", inputs.toString(), "--bad", output.toString()}, child(false, calls)));
    }
}
