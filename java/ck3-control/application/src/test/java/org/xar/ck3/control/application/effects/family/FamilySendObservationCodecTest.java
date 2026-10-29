package org.xar.ck3.control.application.effects.family;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION;

/** Pure DATA boundary regressions only. Actual producer-to-writer cases are separately required, never mocked into qualification. */
final class FamilySendObservationCodecTest {
    @Test void fullNativeIdsAndZeroPendingAreSendDataWithoutRelationDayOrSaveCredit() {
        for (var profile : FamilySendObservation.Profile.values()) {
            var values = FamilySendObservation.sendOnlyValues(profile, 0xFE000001L, 0x81000002L, 0);
            FamilySendObservation.requireSendOnlyValues(profile, 0, values);
            assertTrue(values.contains(new ExpectedInteger(new FieldKey("native_pending_full_id"), BigInteger.ZERO)));
            assertTrue(values.contains(new ExpectedBoolean(new FieldKey("outbound_request_effect_observed"), true)));
            for (String field : List.of("native.gameplay_verified", "timeline.advance_verified", "timeline.checkpoint_eligible"))
                assertTrue(values.contains(new ExpectedBoolean(new FieldKey(field), false)));
            assertFalse(values.contains(new ExpectedBoolean(new FieldKey("marriage_relation_verified"), true)));
            assertFalse(values.contains(new ExpectedBoolean(new FieldKey("guardian_relation_verified"), true)));
            assertEquals(values, ProposalLifecycleCodec.values(ProposalLifecycleCodec.encodeValues(values)));
        }
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 0, 2, 0));
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.GUARDIAN, 1, 0xFFFF_FFFFL, 0));
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.GUARDIAN, 1, 2, 0xFFFF_FFFFL));
    }

    @Test void dataCannotGrantRelationCreditChangePendingIdentityOrBorrowAnotherProfile() {
        var marriage = FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 7, 8, 0);
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.requireSendOnlyValues(FamilySendObservation.Profile.GUARDIAN, 0, marriage));
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.requireSendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 1, marriage));
        var incomplete = new ArrayList<>(marriage); incomplete.removeLast();
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.requireSendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 0, incomplete));
        var forged = new ArrayList<>(marriage);
        forged.set(forged.indexOf(new ExpectedBoolean(new FieldKey("marriage_relation_verified"), false)),
                new ExpectedBoolean(new FieldKey("marriage_relation_verified"), true));
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.requireSendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 0, forged));
        var duplicate = new ArrayList<>(marriage); duplicate.add(marriage.getFirst());
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservation.requireSendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 0, duplicate));
    }

    @Test void malformedUntrustedWireIsRejectedBeforeAnyArchivedReadCanBeLoaded() {
        AtomicInteger calls = new AtomicInteger(); var archive = unavailableArchive(calls);
        List<ObjectNode> rejected = new ArrayList<>();
        rejected.add(data().put("schema", "xar.java.family-send-observation/v0"));
        rejected.add(data().put("profile", "ACK"));
        rejected.add(data().put("native_pending_full_id", true));
        rejected.add(data().put("native_pending_full_id", 0.0));
        rejected.add(data().put("native_pending_full_id", "0"));
        rejected.add(data().put("native_pending_full_id", -1));
        rejected.add(data().put("native_pending_full_id", 0xFFFF_FFFFL));
        rejected.add(data().put("definition_stable_hash", false));
        rejected.add(data().put("definition_stable_hash", 1.0));
        rejected.add(data().put("definition_stable_hash", -1));
        rejected.add(data().put("definition_stable_hash", 0x1_0000_0000L));
        ObjectNode missing = data(); missing.remove("before_frame"); rejected.add(missing);
        rejected.add(data().put("host_nonce_stored_by_native", true));
        ObjectNode duplicate = data(); duplicate.withArray("complete_preparation").add(ref("before-read", "c").toJson()); rejected.add(duplicate);
        ObjectNode changed = data(); changed.set("actual", ProposalLifecycleCodec.encodeValues(
                FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 7, 8, 1))); rejected.add(changed);
        ObjectNode aliased = data(); aliased.set("after_storage_ref", aliased.get("before_storage_ref").deepCopy()); rejected.add(aliased);
        ObjectNode unprepared = data(); unprepared.withArray("complete_preparation").removeAll().add(ref("other-original", "9").toJson()); rejected.add(unprepared);
        for (String key : List.of("original_dispatch_ref", "prepared_request_ref", "before_storage_ref", "after_storage_ref")) {
            ObjectNode empty = data(); ((ObjectNode) empty.get(key)).put("bytes", 0); rejected.add(empty);
        }
        for (String key : List.of("before_frame", "after_frame")) {
            ObjectNode empty = data(); ((ObjectNode) empty.get(key).get("native_frame")).put("bytes", 0); rejected.add(empty);
        }
        var fields = data().fieldNames();
        while (fields.hasNext()) {
            String key = fields.next(); ObjectNode absent = data(); absent.remove(key); rejected.add(absent);
            ObjectNode explicitNull = data(); explicitNull.putNull(key); rejected.add(explicitNull);
        }
        for (ObjectNode value : rejected)
            assertThrows(RuntimeException.class, () -> FamilySendObservationCodec.decode(value, archive), value.toString());
        assertEquals(0, calls.get(), "malformed shape/scalars must not reach original archive resolution");
    }

    @Test void bothProfilesRoundTripExactOriginalReadsWithoutQualifyingTheirConstructedData() {
        for (var profile : FamilySendObservation.Profile.values()) {
            ObjectNode wire = data(profile); var archive = dataArchive(wire, false, false, false);
            FamilySendObservation observation = FamilySendObservationCodec.decode(wire, archive);
            assertEquals(profile, observation.profile()); assertEquals(0, observation.nativePendingFullId());
            assertEquals(0, observation.nativeSlotIndex()); assertEquals(observation.before(), observation.after());
            assertEquals(observation.beforeFrame(), observation.afterFrame());
            assertEquals(wire, FamilySendObservationCodec.encode(observation, archive));
            assertEquals(observation, FamilySendObservationCodec.decode(FamilySendObservationCodec.encode(observation, archive), archive));
            assertTrue(observation.beforeStorage().original().custody().isEmpty());
            assertTrue(observation.afterStorage().original().custody().isEmpty());
            // A pure DATA round trip does not create real sampling chronology, native effect or authority.
        }
    }

    @Test void sameContentReadCannotBorrowAnotherCanonicalArchiveLocator() {
        ObjectNode wire = data();
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservationCodec.decode(wire, dataArchive(wire, true, false, false)));
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservationCodec.decode(wire, dataArchive(wire, false, true, false)));
        var original = FamilySendObservationCodec.decode(wire, dataArchive(wire, false, false, false));
        assertThrows(IllegalArgumentException.class, () -> FamilySendObservationCodec.encode(original, dataArchive(wire, false, false, true)));
    }

    @Test void sameSemUnknownAndAckWithoutActualCustodyCannotBecomeSendConfirmed() {
        for (var profile : FamilySendObservation.Profile.values()) {
            ObjectNode wire = data(profile); var identity = ProposalLifecycleCodec.decodeObservation(wire.get("before"));
            var source = G2Wire.source(wire.get("source")); Instant at = Instant.parse("2026-10-24T00:00:00Z");
            var operation = new OperationKey("data-only-send"); String session = StrictJson.text(wire.get("session_id"));
            var expected = new ExpectedPostcondition(POSTCONDITION_VERSION, identity, source, profile.observerSchema(),
                    FamilySendObservation.sendOnlyValues(profile, 7, 8, 0));
            var command = new ActionCommand(StrictJson.text(wire.get("action_id")), identity, source, session, operation,
                    new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), at.plusSeconds(10));
            wire.put("command_body_sha256", ActionCodec.bodySha256(command));
            var observed = FamilySendObservationCodec.decode(wire, dataArchive(wire, false, false, false));
            var guard = new GuardEvidence(identity, source, session, BigInteger.ONE, operation, observed.beforeFrame().nativeFrame(),
                    ref("capability", "9"), "data-only-action-authority", at, at.plusSeconds(10));
            var attempt = new ActionState.Attempt(observed.originalRequestId(), at, guard,
                    new NativeRequest(operation.value(), Optional.empty(), new RawJson(new byte[] {'{', '}'}), observed.completePreparation()));
            var unknown = new NativeActionPort.Unknown(observed.originalRequestId(), "unknown original outcome", new byte[] {1}, Optional.empty());
            var noCustody = new NativeActionPort.AckReceived(observed.originalRequestId(), true, Optional.empty(),
                    new RawJson(new byte[] {'{', '}'}), new byte[] {1});
            assertTrue(assertThrows(IllegalArgumentException.class, () -> observed.validate(command, attempt, unknown))
                    .getMessage().contains("actual original successful ACK/write custody"));
            assertTrue(assertThrows(IllegalArgumentException.class, () -> observed.validate(command, attempt, noCustody))
                    .getMessage().contains("actual original successful ACK/write custody"));
            assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(command, attempt,
                    new ActionState.FamilySendConfirmed(observed)), "DATA-only helper must not settle a native send without the original dispatch");
        }
    }

    @Test void validSameSemDataStillRequiresOriginalReadsAndCannotManufactureAnObservation() {
        AtomicInteger calls = new AtomicInteger(); var archive = unavailableArchive(calls);
        // before/after identity and native frame refs are deliberately identical.
        // DATA compatibility does not create read custody or qualified domain matching.
        assertEquals(data().get("before"), data().get("after"));
        assertEquals(data().get("before_frame"), data().get("after_frame"));
        AssertionError failure = assertThrows(AssertionError.class, () -> FamilySendObservationCodec.decode(data(), archive));
        assertTrue(failure.getMessage().contains("actual original archive lookup required"));
        assertEquals(1, calls.get(), "a valid reference-only payload cannot bypass loading its real read originals");
    }

    private static ActionPorts.OutcomeArchive unavailableArchive(AtomicInteger calls) {
        // Negative-only boundary spy: it never returns a receipt, native ACK, authority or successful proof.
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    calls.incrementAndGet(); throw new AssertionError("actual original archive lookup required: " + method.getName());
                });
    }
    private static ObjectNode data() { return data(FamilySendObservation.Profile.MARRIAGE); }
    private static ObjectNode data(FamilySendObservation.Profile profile) {
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var identity = new ObservationIdentity("fixture-machine", game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7), BigInteger.valueOf(9),
                        BigInteger.valueOf(100)), "fixture-same-sem", BigInteger.valueOf(9), "fixture-episode"), 2);
        var source = new G2Source(identity.machineId(), "2026-10-24T00:00:00Z", "fixture-build", ref("definition-source", "7"));
        ObjectNode value = StrictJson.object().put("schema", FamilySendObservationCodec.SCHEMA).put("profile", profile.name())
                .put("action_id", "data-only-action").put("command_body_sha256", "1".repeat(64))
                .put("original_request_id", "data-only-submit").put("session_id", "data-only-session")
                .put("native_pending_full_id", 0).put("definition_stable_hash", 0xFFFF_FFFFL);
        value.set("original_dispatch_ref", ref("dispatch", "e").toJson()); value.set("prepared_request_ref", ref("prepared", "f").toJson());
        ObjectNode frame = StrictJson.object(); frame.set("native_frame", ref("native", "a").toJson());
        frame.set("driver_facts", ref("facts", "b").toJson());
        value.set("before_frame", frame.deepCopy()); value.set("after_frame", frame.deepCopy());
        value.set("before", ProposalLifecycleCodec.observation(identity)); value.set("after", ProposalLifecycleCodec.observation(identity));
        value.set("source", ProposalLifecycleCodec.source(source));
        value.set("before_storage_ref", ref("before-read", "c").toJson()); value.set("after_storage_ref", ref("after-read", "d").toJson());
        value.putArray("complete_preparation").add(ref("preparation", "8").toJson()).add(ref("before-read", "c").toJson());
        value.set("actual", ProposalLifecycleCodec.encodeValues(FamilySendObservation.sendOnlyValues(profile, 7, 8, 0)));
        return value;
    }
    private static PlanningReadReceipt read(ObjectNode wire, String requestId) {
        var identity = ProposalLifecycleCodec.decodeObservation(wire.get("before"));
        var source = G2Wire.source(wire.get("source")); String session = StrictJson.text(wire.get("session_id"));
        var operation = new OperationKey("data-only-family-storage"); Instant at = Instant.parse("2026-10-24T00:00:00Z");
        var request = new PlanningReadRequest(identity, source, session, operation, new OpportunityJson.Obj(Map.of()), at.plusSeconds(10));
        var guard = new GuardEvidence(identity, source, session, BigInteger.ONE, operation, ref("native", "a"),
                ref("capability", "9"), "data-only-read-authority", at, at.plusSeconds(10));
        var binding = new PlanningReadGuard(guard, true, true, true, "b".repeat(64));
        var ack = new NativeActionPort.AckReceived(requestId, true, Optional.empty(),
                new RawJson(new byte[] {'{', '}'}), new byte[] {1});
        return new PlanningReadReceipt(request, "data-only-family-storage", requestId, binding, binding, ack);
    }
    /** Typed DATA-only archive: it cannot dispatch, preserve evidence, qualify a domain or return a native authority. */
    private static ActionPorts.OutcomeArchive dataArchive(ObjectNode wire, boolean beforeLocatorDrift,
            boolean afterLocatorDrift, boolean substituteBeforeReceipt) {
        PlanningReadReceipt before = read(wire, "before-data-only"), after = read(wire, "after-data-only");
        ExactRef beforeRef = ExactRef.fromJson(wire.get("before_storage_ref")), afterRef = ExactRef.fromJson(wire.get("after_storage_ref"));
        Map<ExactRef, PlanningReadReceipt> reads = Map.of(beforeRef, substituteBeforeReceipt ? after : before, afterRef, after);
        Map<PlanningReadReceipt, ExactRef> refs = Map.of(before, beforeLocatorDrift ? ref("other-before-locator", "c") : beforeRef,
                after, afterLocatorDrift ? ref("other-after-locator", "d") : afterRef);
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> switch (method.getName()) {
                    case "loadRead" -> Optional.ofNullable(reads.get(args[0])).orElseThrow();
                    case "readReferenceOf" -> Optional.ofNullable(refs.get(args[0])).orElseThrow();
                    default -> throw new AssertionError("pure DATA codec called a production archive operation: " + method.getName());
                });
    }
    private static ExactRef ref(String path, String hashByte) { return new ExactRef(path, 1, hashByte.repeat(64)); }
}

