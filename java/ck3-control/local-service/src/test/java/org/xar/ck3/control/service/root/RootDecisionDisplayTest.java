package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
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
        assertEquals("xar.java-root-decision-text/v1", StrictJson.text(binding.get("schema")));
        assertEquals("TEXT_PUBLISHED", StrictJson.text(binding.get("status")));
        assertEquals(publication, StrictJson.integer(binding.get("publication"), 0, StrictJson.MAX_SAFE_INTEGER));
        assertEquals(DecisionDisplayTest.NOW.toString(), StrictJson.text(binding.get("written_at_utc")));
        assertEquals(command.origin().machineId(), StrictJson.text(binding.get("machine_id")));
        assertEquals(command.sessionId(), StrictJson.text(binding.get("session_id")));
        assertEquals(command.origin().game(), GameGeneration.fromJson(binding.get("game")));
        assertTrue(binding.get("game").get("creation_filetime").isTextual());
        assertEquals(command.origin().game().creationFiletime().value().toString(),
                StrictJson.text(binding.get("game").get("creation_filetime")));
        ObjectNode publisher = StrictJson.object(binding.get("publisher"), Set.of("pid", "start_instant_utc", "executable"));
        ProcessHandle process = ProcessHandle.current();
        ProcessHandle.Info info = process.info();
        assertEquals(process.pid(), StrictJson.integer(publisher.get("pid"), 1, StrictJson.MAX_SAFE_INTEGER));
        assertEquals(info.startInstant().orElseThrow().toString(), StrictJson.text(publisher.get("start_instant_utc")));
        assertEquals(info.command().orElseThrow(), StrictJson.text(publisher.get("executable")));
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
}
