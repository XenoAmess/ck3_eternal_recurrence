package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Executes the actual original lock and mechanical transport on owned small source fixtures.
 * This suite never constructs a Native permission or starts a Native/Game process. */
class OriginalWriterReadOnlyHandoffTest {
    @TempDir Path temporary;
    private record Fixture(Path head, Path event, Path index, byte[] originalHead,
            ExactRef writer, WindowsFileWriterSession.Settings settings, Map<Path,byte[]> retained) { }

    private static Path explicit(String property, String fallback) {
        String value = System.getProperty(property,fallback);
        assertNotNull(value,"required explicit finite fixture input: " + property);
        Path path = Path.of(value).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(path) || Files.isDirectory(path));
        return path;
    }
    private static ExactRef reference(Path path) throws IOException {
        byte[] raw = Files.readAllBytes(path);
        return new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }
    private static byte[] sourceFixture(String name, String sha) throws IOException {
        try (var stream = OriginalWriterReadOnlyHandoffTest.class.getResourceAsStream("/" + name)) {
            assertNotNull(stream,"required preserved small source fixture " + name);
            byte[] raw = stream.readNBytes(RecoveryEvidence.MAX_BYTES + 1);
            assertTrue(raw.length <= RecoveryEvidence.MAX_BYTES); assertEquals(sha,RecoveryEvidence.sha256(raw));
            return raw;
        }
    }
    private Fixture fixture() throws IOException {
        Path repo = explicit("xar.repo",System.getenv("XAR_REPO_ROOT"));
        Path transport = explicit("xar.recovery.transport",repo.resolve("tools/g2_saved_campaign/current_saved_continuity_v1.py").toString());
        Path python = explicit("xar.python",System.getenv().getOrDefault("XAR_ORACLE_PYTHON",repo.resolve("tools/.venv/Scripts/python.exe").toString()));
        Path fixtureRepo = temporary.resolve("repo"), modules = fixtureRepo.resolve("tools/g2_saved_campaign");
        Files.createDirectories(modules);
        Path mechanical = modules.resolve("current_saved_continuity_v1.py"); Files.copy(transport,mechanical);
        Path coldOwner = modules.resolve("root_current_saved_campaign_cold_owner_v1.py");
        Files.copy(repo.resolve("tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py"),coldOwner);
        Path output = temporary.resolve("processes"); Files.createDirectory(output);
        Path writer = temporary.resolve("original-writer.py");
        Files.write(writer,sourceFixture("n46-frozen-writer-source.actual.txt","6b0ece99075e425f84ad732e3112cf5ccdc883bbb09a884aa94e0df411e9ff6e"));
        byte[] head = sourceFixture("n46-head240.actual.json","86af210b06d5d60b2d1f6ac5f1f0a6d31098b518583da06270596a71b068463a");
        Path canonical = temporary.resolve("ROOT-CONTINUITY-WINDOW.json"); Files.write(canonical,head);
        Path events = temporary.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"); Files.createDirectory(events);
        // These envelopes test only transport/lock mechanics. They grant no reducer or Native qualification.
        Path event = events.resolve("00000240.json"), index = events.resolve("source-" + "a".repeat(64) + ".json");
        Files.writeString(event,"{\"mechanical_fixture_only\":true}\n");
        Files.writeString(index,"{\"mechanical_fixture_only\":true}\n");
        Map<Path,byte[]> retained = new HashMap<>();
        for (var pin : Map.of(
                "n46-raw-state.actual.json","7d62a0c1cf55f29094b8418aa1f716e1b966f03ddc4ab6e826ec415268d1066f",
                "n46-raw-governance.actual.json","d1e5ca6463f0e9e3d46fffc4abfca5df1b190af0840786fb794bdbe261f4d6c5",
                "n46-next11559.actual.json","cecd7459be3d764f3696af3d0bd7c1092c72a8c57252a8e55704a2b8879695fc",
                "n46-prior-basis.actual.json","4b53ffa1a422df36cd18d29f47737fed8417a257ff42d2dc4b7093de56d27afa").entrySet()) {
            Path target = temporary.resolve(pin.getKey()); byte[] raw = sourceFixture(pin.getKey(),pin.getValue());
            Files.write(target,raw); retained.put(target,raw);
        }
        Map<String,String> environment = ClosedAdoptionMain.sessionEnvironment(fixtureRepo,repo,output,System.getenv());
        var settings = new WindowsFileWriterSession.Settings(python,fixtureRepo,output,128L << 20,Duration.ofSeconds(20),
                Instant.now().plusSeconds(40),environment,reference(mechanical),reference(coldOwner),() -> { });
        return new Fixture(canonical,event,index,head,reference(writer),settings,Map.copyOf(retained));
    }
    private static ObjectNode request(Fixture fixture) {
        var request = StrictJson.object(); request.put("schema","xar.java-original-writer-handoff-request/v1");
        request.put("machine_id","source-fixture-only"); request.put("canonical_path",fixture.head().toString());
        request.set("writer_source_ref",fixture.writer().toJson()); request.set("expected_committed",StrictJson.parse(fixture.originalHead()));
        request.put("source_key","a".repeat(64)); request.put("input_digest","b".repeat(64)); request.put("session_nonce","c".repeat(32));
        return request;
    }
    private static ObjectNode release() {
        var release = StrictJson.object(); release.put("schema","xar.java-original-writer-handoff-release/v1");
        release.put("machine_id","source-fixture-only"); release.put("input_digest","b".repeat(64));
        release.put("session_nonce","c".repeat(32)); release.put("release",true); return release;
    }
    private static void unchanged(Fixture fixture) throws IOException {
        assertArrayEquals(fixture.originalHead(),Files.readAllBytes(fixture.head()));
        assertEquals("{\"mechanical_fixture_only\":true}\n",Files.readString(fixture.event()));
        if (Files.exists(fixture.index())) { assertEquals("{\"mechanical_fixture_only\":true}\n",Files.readString(fixture.index())); }
        assertFalse(Files.exists(fixture.event().resolveSibling("00000241.json")));
        var head = StrictJson.parse(fixture.originalHead());
        assertEquals(240,head.get("sequence").intValue()); assertEquals("repair_required",head.get("status").textValue());
        for (var retained : fixture.retained().entrySet()) { assertArrayEquals(retained.getValue(),Files.readAllBytes(retained.getKey())); }
        var state = StrictJson.parse(Files.readAllBytes(fixture.head().resolveSibling("n46-raw-state.actual.json")));
        assertEquals(5189,state.get("completed_cycles").intValue());
        assertEquals(5190,state.get("pending_cycle").get("global_turn").intValue());
        assertEquals(11558,state.get("pending_cycle").get("auto_sequence").intValue());
        assertEquals("auto_unsettled",state.get("pending_cycle").get("stage").textValue());
        var basis = StrictJson.parse(Files.readAllBytes(fixture.head().resolveSibling("n46-prior-basis.actual.json")));
        assertEquals("native-40526-1bec95182886",basis.get("frame").get("episode_run_id").textValue());
        assertEquals(5628,(basis.get("frame").get("date_raw").longValue()-basis.get("origin").get("start_date_raw").longValue())/24);
        assertEquals(11559,StrictJson.parse(Files.readAllBytes(fixture.head().resolveSibling("n46-next11559.actual.json"))).get("next_sequence").intValue());
    }
    @Test void originalNativeWriterLockRemainsHeldUntilExactReleaseAndNeverAppends() throws Exception {
        Fixture fixture = fixture(); var process = WindowsFileWriterSession.start(fixture.settings(),WindowsFileWriterSession.Mode.WRITER);
        try {
            OriginalWriterTransaction.send(process.stdin(),request(fixture));
            var locked = OriginalWriterTransaction.read(process.stdout());
            assertEquals("xar.java-original-writer-handoff-locked/v1",locked.get("schema").textValue());
            var head = OriginalWriterTransaction.Document.decode(locked.get("readback").get("head"));
            assertArrayEquals(fixture.originalHead(),head.evidence().bytes());
            Path lock = fixture.head().resolveSibling("ROOT-CONTINUITY-WINDOW.lock");
            try (var channel = FileChannel.open(lock,StandardOpenOption.READ,StandardOpenOption.WRITE)) {
                assertNull(channel.tryLock(0,1,false),"the original Python writer holds its real OS byte lock");
            }
            OriginalWriterTransaction.send(process.stdin(),release());
            var released = OriginalWriterTransaction.read(process.stdout());
            assertEquals("xar.java-original-writer-handoff-released/v1",released.get("schema").textValue());
            for (String field : Set.of("ledger_modified","original_actions_replayed","raw_pending_modified")) {
                assertTrue(released.get(field).isBoolean()); assertFalse(released.get(field).booleanValue());
            }
            process.closeOwnedInput(); assertEquals(0,process.awaitActualExit().exitCode());
            assertTrue(process.actualCommandResult().orElseThrow().passed());
            try (var channel = FileChannel.open(lock,StandardOpenOption.READ,StandardOpenOption.WRITE); var acquired = channel.tryLock(0,1,false)) {
                assertNotNull(acquired,"actual zero exit released the original OS lock");
            }
            unchanged(fixture);
        } catch (Exception | Error failure) { OriginalProcessCleanup.suppressing(process,failure); throw failure; }
    }
    private static void rejectedActualExit(WindowsFileWriterSession process) {
        assertThrows(IOException.class,process::awaitActualExit,"negative original writer exits reject through the actual managed API");
        var terminal=process.actualCommandResult().orElseThrow();
        assertNotEquals(0,terminal.exitCode());assertNull(terminal.stopReason());assertEquals(0,terminal.accounting().activeProcesses());
    }
    @Test void changedExpectedHeadFailsBeforeLockedHandoffAndCannotResetHead() throws Exception {
        Fixture fixture = fixture(); var request = request(fixture);
        ((ObjectNode)request.get("expected_committed")).put("sequence",239);
        var process = WindowsFileWriterSession.start(fixture.settings(),WindowsFileWriterSession.Mode.WRITER);
        OriginalWriterTransaction.send(process.stdin(),request); process.closeOwnedInput();
        assertThrows(IOException.class,() -> OriginalWriterTransaction.read(process.stdout()));
        rejectedActualExit(process); unchanged(fixture);
    }
    @Test void integerReleaseIsRejectedInsideActualWriterLockWithoutAppend() throws Exception {
        Fixture fixture = fixture(); var process = WindowsFileWriterSession.start(fixture.settings(),WindowsFileWriterSession.Mode.WRITER);
        OriginalWriterTransaction.send(process.stdin(),request(fixture)); OriginalWriterTransaction.read(process.stdout());
        var release = release(); release.put("release",1); OriginalWriterTransaction.send(process.stdin(),release); process.closeOwnedInput();
        assertThrows(IOException.class,() -> OriginalWriterTransaction.read(process.stdout()));
        rejectedActualExit(process); unchanged(fixture);
    }
    @Test void missingOriginalIndexIsUnavailableAndCannotCreateRecoveryOutputs() throws Exception {
        Fixture fixture = fixture(); Files.delete(fixture.index());
        var process = WindowsFileWriterSession.start(fixture.settings(),WindowsFileWriterSession.Mode.WRITER);
        OriginalWriterTransaction.send(process.stdin(),request(fixture)); process.closeOwnedInput();
        assertThrows(IOException.class,() -> OriginalWriterTransaction.read(process.stdout()));
        rejectedActualExit(process); assertFalse(Files.exists(fixture.index())); unchanged(fixture);
    }
}
