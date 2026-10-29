package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;

/** Mandatory real Root-fixture hook. This utility never constructs a fake Completion, source capability or writer. */
public final class DirectWindowServiceGateAssertions {
    private DirectWindowServiceGateAssertions() { }
    public static void originalOwnerQueryDeferralBlocksSdkAndGenericAtTheActualService(
            ContinuityWriter actualWriter, ContinuityStorePort.Session same, ArmyOrdinaryActionService actualService,
            ArmyCalls.Frame selected, ArmyTypes.Context actualScope, Complete actualSameFrame, Complete actualNewFrame,
            ActionReceipt canonicalResolved, ActionPorts.OutcomeArchive boundArchive, FrameLoader actualFrames) throws Exception {
        actualWriter.requireSession(same);
        var head = same.head();
        assertEquals(canonicalResolved, ContinuityActionJournal.lookup(head.state(), canonicalResolved.command().actionId(), boundArchive).orElseThrow());
        var original = NativeDirectFixedWindowObservation.load(canonicalResolved, boundArchive, actualFrames);
        var resolution = original.ownerResolution().orElseThrow();
        assertTrue(resolution.retryDeferredForNativeFrame(), "actual private owner query must reproduce the original deferred-frame predicate");
        assertTrue(canonicalResolved.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.DirectFixedWindowCompleted);
        assertEquals(actualScope.before(), actualSameFrame.identity());
        var before = actualSameFrame.identity().frame().identity();
        assertFalse(before.nativeRevision().equals(actualNewFrame.identity().frame().identity().nativeRevision())
                && before.dateRaw().equals(actualNewFrame.identity().frame().identity().dateRaw()), "actual next frame must differ in original Native revision or date");
        var generic = assertThrows(IllegalArgumentException.class, () -> actualService.prepareDirectFixedWindowCommand(same, selected, actualScope,
                "fixture-direct-deferred-new-caller"));
        assertTrue(generic.getMessage().contains("close retry deferred for this original Native frame"));
        assertEquals(head, same.head(), "deferred generic close cannot write INTENT or another canonical action");
        var sdk = assertThrows(IllegalArgumentException.class, () -> actualService.prepareCommand(same, selected, actualScope,
                "fixture-sdk-deferred-new-caller"));
        assertTrue(sdk.getMessage().contains("close retry deferred for this original Native frame"));
        assertEquals(head, same.head(), "changing profile cannot bypass the original window lifetime");
        var nextCall = new ArmyCalls.Frame(selected.method(), new ArmyCalls.Revision(new ArmyTypes.Present<>(actualNewFrame.identity().frame().revision())));
        assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectDirectWindowDeferred(List.of(canonicalResolved), nextCall, actualNewFrame, boundArchive, actualFrames),
                "new Native frame only releases this latch; it grants no command readiness or authority");
        actualWriter.requireSession(same); assertEquals(head, same.head());
    }
}
