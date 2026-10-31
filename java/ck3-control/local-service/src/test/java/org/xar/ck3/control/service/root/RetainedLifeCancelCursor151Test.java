package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual historical cursor DATA; does not exercise private-token/native authorization. */
final class RetainedLifeCancelCursor151Test {
    private static ActionReceipt actual() throws IOException {
        try (var in = RetainedLifeCancelCursor151Test.class.getResourceAsStream("/root-cancel151/actual385-parent.json")) {
            assertNotNull(in, "the immutable actual385 fixture must be present");
            // Unknown composite decoding preserves ExactRef metadata without opening its historical files.
            var parent = ActionReceiptCodec.decodeReceipt(in.readAllBytes(), null);
            assertEquals(385, parent.sequence());
            assertEquals("33fd500369d760cc28a07900a36b10a2544a96b1fb24e9fe4da78cc127d5f379", parent.bodySha256());
            assertInstanceOf(ActionState.CompositeUnknown.class, parent.state());
            return parent;
        }
    }
    private static ActionCommand child(ActionReceipt parent, String step) {
        var command = parent.command();
        var operation = new OperationKey(step);
        var empty = new OpportunityJson.Obj(Map.of());
        return new ActionCommand("cursor151-child", command.before(), command.source(), command.sessionId(),
                operation, empty, AdvancePrimitives.expected(command.before(), command.source(), operation, empty),
                command.claims(), command.deadline().plusSeconds(300));
    }
    @Test void actualUnknownAcceptsOnlyTypedCancellationCursorData() throws IOException {
        var parent = actual();
        var cancel = child(parent, ClockStatusRead.CANCEL_PREFIX + "1");
        assertTrue(cancel.deadline().isAfter(parent.command().deadline()));
        assertTrue(RootDerivedChildAuthority.retainedLifeCancel(parent, cancel));
        assertSame(((ActionState.CompositeUnknown) parent.state()).execution(), RootDerivedChildAuthority.executionFor(parent, cancel));
    }
    @Test void actualUnknownDoesNotAdmitArmResumeOrForeignHandlerCursor() throws IOException {
        var parent = actual();
        for (var step : List.of("research-arm-tactical-daily-sentinel-v1-53144328-to-53144520-speed-5-mode-terminal-a-0", "resume-map")) {
            var other = child(parent, step);
            assertFalse(RootDerivedChildAuthority.retainedLifeCancel(parent, other));
            assertThrows(IllegalArgumentException.class, () -> RootDerivedChildAuthority.executionFor(parent, other));
        }
        var old = ((ActionState.CompositeUnknown) parent.state()).execution();
        var foreign = new CompositeExecution("foreign-handler151", old.startedAt(), old.guard(), old.children());
        var changed = new ActionReceipt(parent.version(), parent.sequence(), parent.command(), parent.bodySha256(),
                new ActionState.CompositeUnknown(foreign, "cursor151 foreign handler", List.of()));
        assertThrows(IllegalArgumentException.class, () -> RootDerivedChildAuthority.executionFor(changed, child(parent, ClockStatusRead.CANCEL_PREFIX + "1")));
    }
    @Test void ordinaryRunningParentKeepsItsOriginalCursor() throws IOException {
        var parent = actual();
        var cursor = ((ActionState.CompositeUnknown) parent.state()).execution();
        var running = new ActionReceipt(parent.version(), parent.sequence(), parent.command(), parent.bodySha256(),
                new ActionState.CompositeRunning(cursor));
        assertSame(cursor, RootDerivedChildAuthority.executionFor(running, child(parent, ClockStatusRead.CANCEL_PREFIX + "1")));
    }
}
