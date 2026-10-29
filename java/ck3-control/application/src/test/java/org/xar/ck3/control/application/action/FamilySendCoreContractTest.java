package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** DATA and refusal vectors. These records have no query custody or domain authority and cannot commit. */
final class FamilySendCoreContractTest {
    private static final ExactRef DISPATCH = ref("dispatch", "d"), PREPARED = ref("prepared", "e"),
            BEFORE_READ = ref("before-read", "f"), AFTER_READ = ref("after-read", "1");
    private static ExactRef ref(String path, String hash) { return new ExactRef("D:/family-send-data/" + path, 1, hash.repeat(64)); }
    record Vector(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived dispatch,
            FamilySendObservation observation) {
        ActionReceipt receipt() { return new ActionReceipt(1, 4, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.FamilySendConfirmed(observation))); }
    }
    static Vector vector() {
        var original = ActionCoordinatorTest.command("send-data", "pause-map");
        var command = new ActionCommand(original.actionId(), original.before(), original.source(), original.sessionId(), original.operation(),
                original.arguments(), FamilyMarriageSendExpectation.expected(original.before(), original.source(), 7, 8), original.claims(), original.deadline());
        var prepared = new NativeRequest(command.operation().value(), Optional.empty(), new RawJson(new byte[]{'{', '}'}), List.of(BEFORE_READ));
        var attempt = new ActionState.Attempt("original-send", ActionCoordinatorTest.NOW, ActionCoordinatorTest.guard(command, ActionCoordinatorTest.NOW), prepared);
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), true, Optional.empty(), new RawJson(new byte[]{'{', '}'}), new byte[]{1});
        var basis = new NativeEffectEvidence.FrameBasis(attempt.guard().nativeEvidence(), ActionCoordinatorTest.BASIS);
        var observation = new FamilySendObservation(FamilySendObservation.Profile.MARRIAGE, command.actionId(), ActionCodec.bodySha256(command),
                attempt.requestId(), DISPATCH, PREPARED, basis, basis, command.before(), command.before(), command.source(), command.sessionId(),
                ActionCoordinatorTest.read("before-storage", ActionCoordinatorTest.NOW.minusSeconds(1)),
                ActionCoordinatorTest.read("after-storage", ActionCoordinatorTest.NOW.plusSeconds(1)), List.of(BEFORE_READ), 0, 73,
                FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 7, 8, 0));
        return new Vector(command, attempt, ack, observation);
    }
    private static ActionPorts.OutcomeArchive dataArchive(Vector value) {
        // This has no writer, preservation method, native source, guard verifier or successful domain callback.
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> switch (method.getName()) {
                    case "referenceOf" -> { assertEquals(value.dispatch(), args[0]); yield DISPATCH; }
                    case "requestReferenceOf" -> { assertEquals(value.attempt().preparedRequest(), args[0]); yield PREPARED; }
                    case "readReferenceOf" -> {
                        if (value.observation().beforeStorage().equals(args[0])) yield BEFORE_READ;
                        assertEquals(value.observation().afterStorage(), args[0]); yield AFTER_READ;
                    }
                    case "load" -> { assertEquals(DISPATCH, args[0]); yield value.dispatch(); }
                    case "loadRequest" -> { assertEquals(PREPARED, args[0]); yield value.attempt().preparedRequest(); }
                    case "loadRead" -> {
                        if (BEFORE_READ.equals(args[0])) yield value.observation().beforeStorage();
                        assertEquals(AFTER_READ, args[0]); yield value.observation().afterStorage();
                    }
                    default -> throw new AssertionError("DATA-only archive cannot grant or preserve authority: " + method.getName());
                });
    }
    @Test void sameSemDataRoundtripHasSeparateSendOutcomeAndNoBusinessOrDayProjection() {
        var value = vector(); var archive = dataArchive(value); byte[] encoded = ActionReceiptCodec.encodeReceipt(value.receipt(), archive);
        assertEquals(ActionReceiptCodec.FAMILY_SEND_SCHEMA, StrictJson.text(StrictJson.parse(encoded, ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES).get("schema")));
        var restored = ActionReceiptCodec.decodeReceipt(encoded, archive); assertEquals(value.receipt(), restored);
        assertEquals(ActionReceipt.Outcome.SEND_CONFIRMED, restored.outcome()); assertTrue(restored.settled());
        assertTrue(restored.applied().isEmpty()); assertTrue(ActionEffects.observation(restored).isEmpty());
        assertFalse(restored.visibleGameplay()); assertFalse(restored.eligibleAdvance());
        assertEquals(value.command().before(), value.observation().after());
        assertEquals(ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH,
                ProposalLifecycle.compare(value.command().expected(), value.observation().after(), value.command().source(),
                        value.observation().profile().observerSchema(), value.observation().actual()));
    }
    @Test void olderReceiptSchemasCannotCarryTypedSendAndUnknownFieldsCannotExtendIt() {
        var value = vector(); var archive = dataArchive(value);
        var row = (ObjectNode) StrictJson.parse(ActionReceiptCodec.encodeReceipt(value.receipt(), archive), ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
        for (String schema : List.of(ActionReceiptCodec.SCHEMA, ActionReceiptCodec.EVOLVED_SCHEMA, ActionReceiptCodec.PROVENANCE_SCHEMA)) {
            var downgraded = row.deepCopy().put("schema", schema);
            assertThrows(IllegalArgumentException.class, () -> ActionReceiptCodec.decodeReceipt(StrictJson.canonical(downgraded), archive));
        }
        var extended = row.deepCopy(); ((ObjectNode) extended.path("state").path("settlement")).put("relation_completed", true);
        assertThrows(IllegalArgumentException.class, () -> ActionReceiptCodec.decodeReceipt(StrictJson.canonical(extended), archive));
    }
    @Test void invalidNativeScalarTypesAreRefusedAtTheReceiptBoundary() {
        var value = vector(); var archive = dataArchive(value);
        var row = (ObjectNode) StrictJson.parse(ActionReceiptCodec.encodeReceipt(value.receipt(), archive), ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
        for (int mutation = 0; mutation < 4; mutation++) {
            var changed = row.deepCopy(); var observation = (ObjectNode) changed.path("state").path("settlement").path("observation");
            switch (mutation) {
                case 0 -> observation.put("native_pending_full_id", false);
                case 1 -> observation.put("native_pending_full_id", 0.0);
                case 2 -> observation.put("definition_stable_hash", "73");
                case 3 -> observation.remove("after_storage_ref");
                default -> throw new AssertionError();
            }
            assertThrows(IllegalArgumentException.class, () -> ActionReceiptCodec.decodeReceipt(StrictJson.canonical(changed), archive));
        }
    }
    @Test void constructedDataCannotSettleWithoutActualOriginalDispatchAndQueryCustody() {
        var value = vector(); var settlement = new ActionState.FamilySendConfirmed(value.observation());
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(value.command(), value.attempt(), settlement));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(value.command(), value.attempt(), value.dispatch(), settlement));
        var unknown = new NativeActionPort.Unknown(value.attempt().requestId(), "actual response is unknown", new byte[0], Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(value.command(), value.attempt(), unknown, settlement));
        var parent = new CompositeExecution("family-parent-data", ActionCoordinatorTest.NOW, value.attempt().guard(), List.of());
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validateComposite(value.command(), parent, settlement));
    }
    @Test void sameSemCannotBeRelabelledAsAppliedAndUnknownStillCannotResubmit() {
        var value = vector(); var effect = new ActionState.EffectObservation(value.command().before(), value.command().source(), value.command().sessionId(),
                value.command().expected().observerSchema(), value.observation().actual(), "independent-data-read", ActionCoordinatorTest.NOW.plusSeconds(1), ActionCoordinatorTest.AFTER);
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(value.command(), value.attempt(), value.dispatch(), new ActionState.Applied(effect)));
        var pending = new ActionReceipt(1, 3, value.command(), ActionCodec.bodySha256(value.command()),
                new ActionState.Unknown(Optional.of(value.attempt()), Optional.of(value.dispatch()), "retained same-SEM pending", List.of()));
        assertThrows(IllegalArgumentException.class, () -> ActionTransitions.validate(Optional.of(pending), value.command(), pending.bodySha256(), new ActionState.Submitting(value.attempt())));
    }
}
