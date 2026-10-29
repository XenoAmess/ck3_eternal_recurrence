package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual fixture producer -> both new physical archive consumers and the sole v11 proof codec.
 * Missing actual Root inputs remain a hard NOT_RUN_REQUIRED failure. */
final class NativeOutcomeArchiveFixtureProofTest {
    @Test void actualFirstMapAndCommittedEntryProofsRetainAllOriginalRolesThroughArchiveAndReentry() throws Exception {
        var providers = ServiceLoader.load(FixtureCompositeActualTest.InputsProducer.class).stream().toList();
        if (providers.size() != 1)
            throw new IllegalStateException("MISSING_ACTUAL_ROOT_FIXTURE_COMPOSITE_INPUTS_NOT_RUN: archive-proof31");
        var input = java.util.Objects.requireNonNull(providers.getFirst().get().open(FixtureCompositeActualTest.Scenario.COMPLETE));
        var context = input.catalog().context();
        assertSame(context.writer(), input.menu().writer);
        ActionReceipt originalParent = input.menu().execute(input.parent());
        var complete = assertInstanceOf(ActionState.FixtureBusinessCompleted.class,
                assertInstanceOf(ActionState.CompositeSettled.class, originalParent.state()).settlement()).observation();
        ActionReceipt originalStart = complete.evidence().originalStart();
        var first = assertInstanceOf(ActionState.FixtureStarted.class,
                assertInstanceOf(ActionState.Settled.class, originalStart.state()).settlement()).observation();
        List<String> attemptsBefore = context.writer().locked(same -> {
            var archive = context.archive().withSession(same);
            var snapshot = context.core().actions().withFrozen(same, lease -> lease.snapshot());
            assertTrue(snapshot.actions().contains(originalStart)); assertTrue(snapshot.actions().contains(originalParent));
            for (ActionReceipt original : List.of(originalStart, originalParent)) {
                ExactRef receipt = archive.receiptReferenceOf(original);
                assertEquals(original, archive.loadReceipt(receipt));
                byte[] encoded = ActionReceiptCodec.encodeReceipt(original, archive);
                assertEquals(ActionReceiptCodec.FIXTURE_SCHEMA, StrictJson.text(StrictJson.parse(encoded).get("schema")));
                assertEquals(original, ActionReceiptCodec.decodeReceipt(encoded, archive));
                assertArrayEquals(encoded, ActionReceiptCodec.encodeReceipt(archive.loadReceipt(receipt), archive));
                assertFalse(original.visibleGameplay()); assertFalse(original.eligibleAdvance());
            }
            assertEquals(first, FixtureProofCodec.start(FixtureProofCodec.start(first, archive), archive));
            assertEquals(complete, FixtureProofCodec.business(FixtureProofCodec.business(complete, archive), archive));
            ExactRef independentRead = archive.referenceOf(first.independentRead());
            assertEquals(first.independentRead(), archive.load(independentRead));
            assertNotEquals(first.independentRead().requestId(), originalStart.ack().orElseThrow().requestId());
            for (ExactRef ref : first.references()) requireOriginal(same, ref);
            for (ExactRef ref : complete.references()) requireOriginal(same, ref);
            assertNotEquals(complete.entryPrepared(), complete.entryReceipt());
            return snapshot.actions().stream().flatMap(value -> ActionTransitions.attempt(value.state()).stream())
                    .map(ActionState.Attempt::requestId).sorted().toList();
        });
        assertEquals(originalParent, input.menu().execute(input.parent()));
        context.writer().locked(same -> {
            var after = context.core().actions().withFrozen(same, lease -> lease.snapshot());
            assertEquals(attemptsBefore, after.actions().stream().flatMap(value -> ActionTransitions.attempt(value.state()).stream())
                    .map(ActionState.Attempt::requestId).sorted().toList());
            return null;
        });
    }

    private static void requireOriginal(ContinuityStorePort.Session same, ExactRef ref) throws IOException {
        assertTrue(ref.bytes() > 0 && ref.bytes() <= WriterContracts.MAX_PIN_BYTES);
        int maximum = Math.toIntExact(ref.bytes());
        var pin = same.capturePin(ref, maximum);
        byte[] bytes = same.readPinned(pin, maximum); same.verifyPin(pin);
        assertEquals(ref.bytes(), bytes.length); assertEquals(ref.sha256(), ActionCodec.sha256(bytes));
    }
}
