package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.ResourceAccessMode;
import org.junit.jupiter.api.parallel.ResourceLock;
import org.junit.jupiter.api.parallel.Resources;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.presentation.DecisionDisplay;
import org.xar.ck3.control.application.presentation.DecisionDisplayTest;
import org.xar.ck3.control.application.presentation.DecisionDisplayText;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual file-observer regressions; no desktop operation or recorded-draw claim. */
final class RootDecisionDisplayTest {
    private static final Clock CLOCK = Clock.fixed(DecisionDisplayTest.NOW, ZoneOffset.UTC);

    @Test
    @ResourceLock(value = Resources.SYSTEM_PROPERTIES, mode = ResourceAccessMode.READ_WRITE)
    void publishesActualPreparingThenUnknownWithProcessAndGameBinding(@TempDir Path stateRoot) throws Exception {
        String previousHeadless = System.getProperty("java.awt.headless");
        try {
            System.setProperty("java.awt.headless", "true");
            assertEquals("true", System.getProperty("java.awt.headless"));
            try (var viewer = new RootDecisionDisplay(CLOCK, stateRoot)) {
                assertEquals(0, viewer.status().publication());
                assertFalse(Files.exists(textPath(stateRoot)));
                assertFalse(Files.exists(bindingPath(stateRoot)));
                noUi(viewer.status());
                ActionCommand command = DecisionDisplayTest.command("file-before-unknown", "pause-map");
                assertDoesNotThrow(() -> viewer.feed().preparing(command, List::of, false));
                long preparingPublication = viewer.feed().snapshot().publication();
                assertTrue(preparingPublication > 0);
                String before = boundText(viewer, stateRoot, command);
                assertTrue(before.contains("准备执行"));
                assertTrue(before.contains("尚未确认提交"));
                assertDoesNotThrow(() -> viewer.feed().returned(DecisionDisplayTest.unknown(command, "original-request", 4)));
                assertTrue(viewer.feed().snapshot().publication() > preparingPublication);
                String after = boundText(viewer, stateRoot, command);
                assertTrue(after.startsWith(DecisionDisplayText.TITLE));
                assertTrue(after.contains("原操作结果仍待确认"));
                assertTrue(after.contains("不能重复提交"));
                assertFalse(after.contains("original-request"));
            }
        } finally {
            if (previousHeadless == null) {
                System.clearProperty("java.awt.headless");
            } else {
                System.setProperty("java.awt.headless", previousHeadless);
            }
        }
        assertEquals(previousHeadless, System.getProperty("java.awt.headless"));
    }

    @Test void closePreservesPublishedFilesAndRejectsLaterObserverWrites(@TempDir Path stateRoot) throws Exception {
        var viewer = new RootDecisionDisplay(CLOCK, stateRoot);
        ActionCommand original = DecisionDisplayTest.command("file-before-close", "pause-map");
        viewer.feed().preparing(original, List::of, false);
        boundText(viewer, stateRoot, original);
        byte[] text = Files.readAllBytes(textPath(stateRoot));
        byte[] binding = Files.readAllBytes(bindingPath(stateRoot));
        viewer.close();
        ActionCommand later = DecisionDisplayTest.command("file-after-close", "pause-map");
        assertDoesNotThrow(() -> viewer.feed().preparing(later, List::of, false));
        assertEquals(DecisionDisplay.Delivery.UNAVAILABLE, viewer.feed().snapshot().delivery());
        assertTrue(viewer.status().unavailable().orElseThrow().contains("closed"));
        noUi(viewer.status());
        assertArrayEquals(text, Files.readAllBytes(textPath(stateRoot)));
        assertArrayEquals(binding, Files.readAllBytes(bindingPath(stateRoot)));
    }

    @Test void actualIoFailureDoesNotEscapeAndNextPublicationRecoversOnSameInstance(@TempDir Path stateRoot) throws Exception {
        Path obstruction = stateRoot.resolve("decision-display");
        Files.createFile(obstruction);
        try (var viewer = new RootDecisionDisplay(CLOCK, stateRoot)) {
            ActionCommand failed = DecisionDisplayTest.command("file-io-failure", "pause-map");
            assertDoesNotThrow(() -> viewer.feed().preparing(failed, List::of, false));
            assertDoesNotThrow(() -> viewer.feed().returned(DecisionDisplayTest.unknown(failed, "failed-observer-request", 1)));
            assertEquals(DecisionDisplay.Delivery.UNAVAILABLE, viewer.feed().snapshot().delivery());
            assertTrue(viewer.status().unavailable().isPresent());
            noUi(viewer.status());
            assertTrue(Files.isRegularFile(obstruction));
            long failedPublication = viewer.feed().snapshot().publication();
            Files.delete(obstruction);
            ActionCommand recovered = DecisionDisplayTest.command("file-io-recovery", "pause-map");
            assertDoesNotThrow(() -> viewer.feed().preparing(recovered, List::of, false));
            assertTrue(viewer.feed().snapshot().publication() > failedPublication);
            boundText(viewer, stateRoot, recovered);
            assertDoesNotThrow(() -> viewer.feed().returned(DecisionDisplayTest.unknown(recovered, "recovered-observer-request", 2)));
            String text = boundText(viewer, stateRoot, recovered);
            assertTrue(text.contains("原操作结果仍待确认"));
            assertTrue(text.contains("不能重复提交"));
        }
    }

    private static String boundText(RootDecisionDisplay viewer, Path stateRoot, ActionCommand command) throws Exception {
        assertEquals(DecisionDisplay.Delivery.RENDERER_UPDATED, viewer.feed().snapshot().delivery());
        noUi(viewer.status());
        assertTrue(viewer.status().unavailable().isEmpty());
        long publication = viewer.feed().snapshot().publication();
        assertEquals(publication, viewer.status().publication());
        Path textFile = textPath(stateRoot);
        byte[] textBytes = Files.readAllBytes(textFile);
        assertTrue(textBytes.length > 0 && textBytes.length <= 32_768);
        assertFalse(textBytes.length >= 3 && textBytes[0] == (byte) 0xef
                && textBytes[1] == (byte) 0xbb && textBytes[2] == (byte) 0xbf);
        String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(textBytes)).toString();
        byte[] bindingBytes = Files.readAllBytes(bindingPath(stateRoot));
        assertTrue(bindingBytes.length > 0 && bindingBytes.length <= 16_384);
        ObjectNode binding = StrictJson.object(StrictJson.parse(bindingBytes, 16_384), Set.of(
                "schema", "status", "publication", "written_at_utc", "machine_id", "session_id", "game", "publisher",
                "decision_text_file", "text_bytes", "text_sha256", "creates_desktop_window", "OBS_draw_ack", "screen_draw_verified"));
        assertEquals("xar.java-root-decision-text/v2", StrictJson.text(binding.get("schema")));
        assertEquals("TEXT_PUBLISHED", StrictJson.text(binding.get("status")));
        assertEquals(publication, StrictJson.integer(binding.get("publication"), 0, StrictJson.MAX_SAFE_INTEGER));
        assertEquals(DecisionDisplayTest.NOW.toString(), StrictJson.text(binding.get("written_at_utc")));
        assertEquals(command.origin().machineId(), StrictJson.text(binding.get("machine_id")));
        assertEquals(command.sessionId(), StrictJson.text(binding.get("session_id")));
        assertEquals(command.origin().game(), GameGeneration.fromJson(binding.get("game")));
        assertTrue(binding.get("game").get("creation_filetime").isTextual());
        assertEquals(command.origin().game().creationFiletime().value().toString(),
                StrictJson.text(binding.get("game").get("creation_filetime")));
        ObjectNode publisher = StrictJson.object(binding.get("publisher"), Set.of("pid", "start_instant_utc", "executable",
                "instance_started_nano_time", "instance_started_at_utc", "instance_id"));
        ProcessHandle process = ProcessHandle.current();
        ProcessHandle.Info info = process.info();
        assertEquals(process.pid(), StrictJson.integer(publisher.get("pid"), 1, StrictJson.MAX_SAFE_INTEGER));
        assertEquals(info.startInstant().orElseThrow().toString(), StrictJson.text(publisher.get("start_instant_utc")));
        assertEquals(info.command().orElseThrow(), StrictJson.text(publisher.get("executable")));
        String instanceId = StrictJson.text(publisher.get("instance_id"));
        assertEquals(instanceId, UUID.fromString(instanceId).toString());
        String instanceNano = StrictJson.text(publisher.get("instance_started_nano_time"));
        assertEquals(instanceNano, Long.toString(Long.parseLong(instanceNano)));
        assertEquals(DecisionDisplayTest.NOW.toString(), StrictJson.text(publisher.get("instance_started_at_utc")));
        assertEquals(textFile.toAbsolutePath().normalize().toString(), StrictJson.text(binding.get("decision_text_file")));
        assertEquals(textBytes.length, StrictJson.integer(binding.get("text_bytes"), 0, 32_768));
        assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(textBytes)),
                StrictJson.text(binding.get("text_sha256")));
        for (String flag : List.of("creates_desktop_window", "OBS_draw_ack", "screen_draw_verified")) {
            assertTrue(binding.get(flag).isBoolean());
            assertFalse(binding.get(flag).booleanValue());
        }
        return text;
    }

    private static Path textPath(Path root) { return root.resolve("decision-display/current.txt"); }
    private static Path bindingPath(Path root) { return root.resolve("decision-display/current.binding.json"); }
    private static void noUi(RootDecisionDisplay.UiStatus status) {
        assertTrue(status.headless().isEmpty());
        assertFalse(status.showing());
        assertFalse(status.focusable());
        assertFalse(status.autoRequestFocus());
        assertFalse(status.alwaysOnTop());
        assertFalse(status.componentTextUpdated());
        assertFalse(status.screenDrawVerified());
    }
    @TempDir Path root;
    private static final Instant NOW = Instant.parse("2026-10-26T19:00:00Z");

    private Clock clock() { return Clock.fixed(NOW, ZoneOffset.UTC); }
    private static ActionCommand command(String id, String operation) {
        var ref = new ExactRef("D:/display-software-vector/source.json", 1, "a".repeat(64));
        var source = new G2Source("display-software-vector", NOW.toString(), "1.20.0.4", ref);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(), game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        StrictJson.UINT64_MAX.subtract(BigInteger.ONE), BigInteger.valueOf(24000)),
                        "display-vector", StrictJson.UINT64_MAX, "episode-display"), 1);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "display-vector/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(id, before, source, "display-session", new OperationKey(operation),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()),
                NOW.plusSeconds(30));
    }
    private static ActionReceipt unknown(ActionCommand original, String request, long sequence) {
        var evidence = original.source().sourceRef();
        var guard = new GuardEvidence(original.before(), original.source(), original.sessionId(), BigInteger.ONE,
                original.operation(), evidence, evidence, "display-vector", NOW, original.deadline());
        var attempt = new ActionState.Attempt(request, NOW, guard, new NativeRequest(original.operation().value(),
                Optional.empty(), new RawJson(new byte[]{'{','}'})));
        return new ActionReceipt(1, sequence, original, ActionCodec.bodySha256(original),
                new ActionState.Unknown(Optional.of(attempt), Optional.empty(), "software transport completion unknown", List.of(evidence)));
    }
    private JsonNode manifest() throws Exception {
        return StrictJson.parse(Files.readAllBytes(root.resolve("decision-display/current.binding.json")));
    }
    private byte[] text() throws Exception { return Files.readAllBytes(root.resolve("decision-display/current.txt")); }

    @Test void actualTypedBeforeAndUnknownPublishBoundUtf8TextWithoutDesktopOrDrawCredit() throws Exception {
        try (var publisher = new RootDecisionDisplay(clock(), root)) {
            var command = command("publisher-action", "pause-map");
            publisher.feed().preparing(command, List::of, false);
            String before = new String(text(), StandardCharsets.UTF_8);
            assertTrue(before.contains("准备执行"));
            assertTrue(before.contains("尚未确认提交"));
            publisher.feed().returned(unknown(command, "original-native-request", 4));
            byte[] bytes = text();
            String after = new String(bytes, StandardCharsets.UTF_8);
            assertTrue(after.startsWith(DecisionDisplayText.TITLE + "\n"));
            assertTrue(after.contains("原操作结果仍待确认"));
            assertTrue(after.contains("不能重复提交"));
            assertTrue(after.contains("近期记录"));
            assertFalse(after.contains("original-native-request"));
            assertFalse(after.contains("134000000000000001"));
            var binding = manifest();
            assertEquals("xar.java-root-decision-text/v2", binding.path("schema").asText());
            assertEquals("TEXT_PUBLISHED", binding.path("status").asText());
            assertEquals(bytes.length, binding.path("text_bytes").intValue());
            assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),
                    binding.path("text_sha256").asText());
            assertEquals(root.resolve("decision-display/current.txt").toString(), binding.path("decision_text_file").asText());
            var game = StrictJson.object(binding.get("game"), Set.of("pid", "creation_filetime"));
            assertEquals(command.before().game().pid(), StrictJson.integer(game.get("pid"), 1, 4_294_967_295L));
            assertEquals(command.before().game().creationFiletime().value().toString(),
                    StrictJson.text(game.get("creation_filetime")));
            assertFalse(binding.path("creates_desktop_window").booleanValue());
            assertFalse(binding.path("OBS_draw_ack").booleanValue());
            assertFalse(binding.path("screen_draw_verified").booleanValue());
            var process = binding.path("publisher");
            assertEquals(ProcessHandle.current().pid(), process.path("pid").longValue());
            assertEquals(process.path("instance_id").asText(), UUID.fromString(process.path("instance_id").asText()).toString());
            Long.parseLong(process.path("instance_started_nano_time").asText());
            StrictJson.utc(process.path("instance_started_at_utc").asText());
            assertEquals(DecisionDisplay.Delivery.RENDERER_UPDATED, publisher.feed().snapshot().delivery());
            assertFalse(publisher.status().showing());
            assertFalse(publisher.status().alwaysOnTop());
            assertFalse(publisher.status().componentTextUpdated());
            assertFalse(publisher.status().screenDrawVerified());
        }
    }

    @Test void serialObjectsInSameJvmHaveDistinctOrderedInstancesAndKeepTheirLocalCounters() throws Exception {
        JsonNode before;
        try (var first = new RootDecisionDisplay(clock(), root)) {
            var command = command("first-publisher", "pause-map");
            first.feed().preparing(command, List::of, false);
            first.feed().returned(unknown(command, "first-request", 4));
            before = manifest();
            assertEquals(2, before.path("publication").longValue());
        }
        try (var second = new RootDecisionDisplay(clock(), root)) {
            second.feed().preparing(command("second-publisher", "pause-map"), List::of, false);
            var after = manifest();
            assertEquals(1, after.path("publication").longValue());
            assertEquals(before.path("game"), after.path("game"));
            assertEquals(before.path("publisher").path("pid"), after.path("publisher").path("pid"));
            assertEquals(before.path("publisher").path("start_instant_utc"), after.path("publisher").path("start_instant_utc"));
            assertEquals(before.path("publisher").path("executable"), after.path("publisher").path("executable"));
            assertNotEquals(before.path("publisher").path("instance_id"), after.path("publisher").path("instance_id"));
            long earlier = Long.parseLong(before.path("publisher").path("instance_started_nano_time").asText());
            long later = Long.parseLong(after.path("publisher").path("instance_started_nano_time").asText());
            assertTrue(later - earlier > 0); // Same JVM, a bounded test interval; signed subtraction handles wrap.
            assertEquals(before.path("publisher").path("instance_started_at_utc"), after.path("publisher").path("instance_started_at_utc"));
        }
    }

    @Test void closedPublisherReportsUnavailableWithoutWritingOrReopening() throws Exception {
        var publisher = new RootDecisionDisplay(clock(), root);
        publisher.close();
        publisher.feed().preparing(command("closed-publisher", "pause-map"), List::of, false);
        assertEquals(DecisionDisplay.Delivery.UNAVAILABLE, publisher.feed().snapshot().delivery());
        assertTrue(publisher.status().unavailable().orElseThrow().contains("closed"));
        assertFalse(Files.exists(root.resolve("decision-display/current.txt")));
        assertFalse(Files.exists(root.resolve("decision-display/current.binding.json")));
        assertFalse(publisher.status().showing());
        assertFalse(publisher.status().screenDrawVerified());
    }

}
