package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.awt.EventQueue;
import java.io.IOException;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.presentation.DecisionDisplay;
import org.xar.ck3.control.application.presentation.DecisionDisplayTest;
import org.xar.ck3.control.application.presentation.DecisionDisplayText;

/** Exercises the real audience component; no top-level window, desktop action or screen-draw credit. */
final class RootDecisionDisplayTest {
    @Test void actualTypedBeforeAndUnknownUpdateTheProductionTextComponentOnTheEdt() throws Exception {
        AtomicReference<RootDecisionDisplay.Content> actual = new AtomicReference<>();
        EventQueue.invokeAndWait(() -> actual.set(new RootDecisionDisplay.Content()));
        DecisionDisplay feed = new DecisionDisplay(Clock.fixed(DecisionDisplayTest.NOW, ZoneOffset.UTC), snapshot -> {
            try { EventQueue.invokeAndWait(() -> actual.get().showText(DecisionDisplayText.render(snapshot))); }
            catch (Exception failure) { throw new IOException("software EDT update failed", failure); }
        }, failure -> fail(failure.reason()));
        var command = DecisionDisplayTest.command("viewer-action", "pause-map");
        feed.preparing(command, List::of, false);
        AtomicReference<String> before = new AtomicReference<>();
        EventQueue.invokeAndWait(() -> before.set(actual.get().text.getText()));
        assertTrue(before.get().contains("准备执行"));
        assertTrue(before.get().contains("尚未确认提交"));
        feed.returned(DecisionDisplayTest.unknown(command, "original-native-request", 4));
        AtomicReference<String> after = new AtomicReference<>();
        EventQueue.invokeAndWait(() -> after.set(actual.get().text.getText()));
        assertTrue(after.get().startsWith(DecisionDisplayText.TITLE));
        assertTrue(after.get().contains("原操作结果仍待确认"));
        assertTrue(after.get().contains("不能重复提交"));
        assertTrue(after.get().contains("近期记录"));
        assertFalse(after.get().contains("original-native-request"));
        assertFalse(after.get().contains("134000000000000001"));
        assertFalse(actual.get().text.isEditable());
        assertFalse(actual.get().text.isFocusable());
        assertFalse(actual.get().isShowing()); // A component update is deliberately not claimed as screen draw.
    }
    @Test void closedActualBackendReportsUnavailableWithoutOpeningOrReopeningAWindow() throws IOException {
        var viewer = new RootDecisionDisplay(Clock.fixed(DecisionDisplayTest.NOW, ZoneOffset.UTC));
        assertTrue(viewer.status().headless().isEmpty());
        viewer.close();
        viewer.feed().preparing(DecisionDisplayTest.command("closed-viewer", "pause-map"), List::of, false);
        assertEquals(DecisionDisplay.Delivery.UNAVAILABLE, viewer.feed().snapshot().delivery());
        assertTrue(viewer.status().unavailable().orElseThrow().contains("closed"));
        assertFalse(viewer.status().showing());
        assertFalse(viewer.status().componentTextUpdated());
        assertFalse(viewer.status().screenDrawVerified());
    }
}

