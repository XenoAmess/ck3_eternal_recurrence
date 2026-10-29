package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.ActivityFinalState.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

final class ActivityFinalStateTest {
    private static final Identity ID = new Identity("feast-start-1", 0x0800_0102L, 73, "activity_feast");
    private static final BigInteger STAMP = StrictJson.UINT64_MAX;
    private static final Provenance PROOF = new Provenance(ref("read"), ref("producer"), ref("hello"));

    @Test void independentFinalFlagSurvivesPurgeWithoutGrantingCauseBenefitOrAction() {
        var origin = observation(1); var finalFrame = observation(2); var later = observation(3);
        State state = observe(empty(ID, origin), sample(origin, new Flags(false, false, Optional.of(BigInteger.ZERO))));
        assertEquals(Kind.ACTIVE, state.currentKind()); assertTrue(state.firstFinal().isEmpty());
        state = observe(state, sample(finalFrame, new Flags(true, false, Optional.of(STAMP))));
        assertEquals(Kind.FINAL_UNATTRIBUTED, state.currentKind()); assertTrue(state.observedFinalAt(finalFrame));
        var first = state.firstFinal().orElseThrow();
        assertFalse(first.terminalCauseObserved()); assertFalse(first.benefitObserved()); assertFalse(first.actionAuthorized());
        state = observe(state, sample(later, new Missing()));
        assertEquals(first, state.firstFinal().orElseThrow()); assertEquals(Kind.UNKNOWN, state.currentKind());
        assertFalse(state.observedFinalAt(later)); assertFalse(state.observedFinalAt(finalFrame));
    }

    @Test void missingStampAndUnknownFlagsNeverBecomeTerminalAndBothTrueArePreserved() {
        State state = empty(ID, observation(1));
        state = observe(state, sample(observation(1), new FlagsUnavailable(Optional.of(STAMP))));
        assertEquals(Kind.UNKNOWN, state.currentKind()); assertTrue(state.firstFinal().isEmpty());
        state = observe(state, sample(observation(2), new Flags(false, true, Optional.empty())));
        assertEquals(Kind.FINAL_UNATTRIBUTED, state.currentKind());
        state = observe(state, sample(observation(3), new Flags(true, true, Optional.of(BigInteger.ZERO))));
        Flags both = (Flags)state.latest().orElseThrow().instance(); assertTrue(both.completed()); assertTrue(both.invalidated());
        assertEquals(Optional.of(BigInteger.ZERO), both.rawCompletionStamp());
    }

    @Test void fullIdentityGameBirthEpisodeSourceAndTimeMustRemainExact() {
        State state = empty(ID, observation(2));
        assertThrows(IllegalArgumentException.class, () -> observe(state, sample(observation(1), new Missing())));
        var wrongId = new Identity(ID.originalActionId(), ID.activityFullId() + 0x0100_0000L, 73, ID.typeKey());
        assertThrows(IllegalArgumentException.class, () -> observe(state, new Sample(wrongId, observation(2), new Missing(), PROOF)));
        ObservationIdentity old = observation(2);
        var wrongGame = new ObservationIdentity(old.machineId(), new GameGeneration(42,
                new PythonOnlyUInt64(new BigInteger("9007199254740994"))), old.frame(), old.observationVersion());
        assertThrows(IllegalArgumentException.class, () -> observe(state, sample(wrongGame, new Missing())));
        var wrongEpisode = new ObservationIdentity(old.machineId(), old.game(), new JointBudgetSelector.ProposalFrame(
                old.frame().identity(), old.frame().snapshotId(), old.frame().revision(), "other-episode"), old.observationVersion());
        assertThrows(IllegalArgumentException.class, () -> observe(state, sample(wrongEpisode, new Missing())));
        assertThrows(IllegalArgumentException.class, () -> new Flags(true, false, Optional.of(STAMP.add(BigInteger.ONE))));
        assertThrows(IllegalArgumentException.class, () -> new FlagsUnavailable(Optional.of(BigInteger.ONE.negate())));
    }

    @Test void compactCodecReplaysEveryOriginalSampleAndKeepsUint64AsDecimalText() {
        var first = sample(observation(2), new Flags(true, false, Optional.of(STAMP)));
        var latest = sample(observation(3), new Missing());
        State state = observe(observe(empty(ID, observation(1)), first), latest);
        byte[] encoded = ActivityFinalStateCodec.encode(state); AtomicInteger replays = new AtomicInteger();
        State cold = ActivityFinalStateCodec.decode(encoded, (identity, queried, proof) -> {
            replays.incrementAndGet(); assertEquals(ID, identity); assertEquals(PROOF, proof);
            return queried.equals(first.queried()) ? first : latest;
        });
        assertEquals(2, replays.get()); assertArrayEquals(encoded, ActivityFinalStateCodec.encode(cold));
        assertEquals(STAMP.toString(), StrictJson.parse(encoded).at("/first_final/instance/raw_stamp").textValue());
        assertEquals(state.firstFinal(), cold.firstFinal());
    }

    @Test void coldFlagsAndSourceMetadataCannotQualifyThemselves() {
        var actual = sample(observation(1), new Flags(false, false, Optional.of(BigInteger.ZERO)));
        byte[] encoded = ActivityFinalStateCodec.encode(observe(empty(ID, observation(1)), actual));
        ObjectNode forged = (ObjectNode)StrictJson.parse(encoded);
        ((ObjectNode)forged.at("/latest/instance")).put("completed", true);
        assertThrows(IllegalArgumentException.class, () -> ActivityFinalStateCodec.decode(
                StrictJson.canonical(forged), (identity, queried, proof) -> actual));
        ObjectNode wrongSource = (ObjectNode)StrictJson.parse(encoded);
        ((ObjectNode)wrongSource.at("/latest/provenance/original_read")).put("sha256", "f".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> ActivityFinalStateCodec.decode(
                StrictJson.canonical(wrongSource), (identity, queried, proof) -> actual));
    }

    @Test void persistedStampRejectsNumberBooleanFloatLeadingZeroOverflowAndMissingField() {
        var actual = sample(observation(1), new Flags(false, false, Optional.of(STAMP)));
        byte[] encoded = ActivityFinalStateCodec.encode(observe(empty(ID, observation(1)), actual));
        for (String value : java.util.List.of("18446744073709551615", "true", "1.0", "\"01\"", "\"18446744073709551616\"")) {
            ObjectNode wrong = (ObjectNode)StrictJson.parse(encoded);
            ((ObjectNode)wrong.at("/latest/instance")).set("raw_stamp", StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> ActivityFinalStateCodec.decode(
                    StrictJson.canonical(wrong), (identity, queried, proof) -> actual));
        }
        ObjectNode missing = (ObjectNode)StrictJson.parse(encoded); ((ObjectNode)missing.at("/latest/instance")).remove("raw_stamp");
        assertThrows(IllegalArgumentException.class, () -> ActivityFinalStateCodec.decode(
                StrictJson.canonical(missing), (identity, queried, proof) -> actual));
    }

    @Test void retainedCutPreservesUnknownByteAndCaptureIdentityWithoutPretendingTheObjectIsHosted() {
        var retained = new RetainedFlags(Optional.empty(), Optional.of(255), Optional.of(STAMP),
                STAMP, BigInteger.valueOf(1002));
        var actual = sample(observation(3), retained);
        State state = observe(empty(ID, observation(1)), actual);
        assertEquals(Kind.FINAL_UNATTRIBUTED, state.currentKind());
        assertEquals(actual, state.firstFinal().orElseThrow());
        assertFalse(state.observedFinalAt(observation(3)), "a historical cut is not a current hosted object");
        assertTrue(retained.completedRaw().isEmpty()); assertEquals(255, retained.invalidatedRaw().orElseThrow());
        assertFalse(actual.terminalCauseObserved()); assertFalse(actual.benefitObserved()); assertFalse(actual.actionAuthorized());
        byte[] encoded = ActivityFinalStateCodec.encode(state);
        assertTrue(StrictJson.parse(encoded).at("/latest/instance/completed_raw").isNull());
        assertEquals(STAMP.toString(), StrictJson.parse(encoded).at("/latest/instance/capture_sequence").textValue());
        assertEquals("1002", StrictJson.parse(encoded).at("/latest/instance/captured_date_raw").textValue());
        assertArrayEquals(encoded, ActivityFinalStateCodec.encode(ActivityFinalStateCodec.decode(
                encoded, (identity, queried, proof) -> actual)));
        for (String field : java.util.List.of("capture_sequence", "captured_date_raw")) {
            ObjectNode changed = (ObjectNode) StrictJson.parse(encoded);
            ((ObjectNode) changed.at("/latest/instance")).put(field, "1001");
            assertThrows(IllegalArgumentException.class, () -> ActivityFinalStateCodec.decode(
                    StrictJson.canonical(changed), (identity, queried, proof) -> actual));
        }
        ObjectNode falseInsteadOfUnknown = (ObjectNode) StrictJson.parse(encoded);
        ((ObjectNode) falseInsteadOfUnknown.at("/latest/instance")).put("completed_raw", 0);
        assertThrows(IllegalArgumentException.class, () -> ActivityFinalStateCodec.decode(
                StrictJson.canonical(falseInsteadOfUnknown), (identity, queried, proof) -> actual));
    }

    @Test void retainedCutNeedsANonzeroObservedByteAndTheOriginalStartToQueryDateWindow() {
        for (int raw : java.util.List.of(-1, 256))
            assertThrows(IllegalArgumentException.class, () -> new RetainedFlags(Optional.of(raw), Optional.empty(),
                    Optional.empty(), BigInteger.ONE, BigInteger.valueOf(1002)));
        assertThrows(IllegalArgumentException.class, () -> new RetainedFlags(Optional.empty(), Optional.of(0),
                Optional.of(STAMP), BigInteger.ONE, BigInteger.valueOf(1002)));
        assertThrows(IllegalArgumentException.class, () -> new RetainedFlags(Optional.of(1), Optional.empty(),
                Optional.empty(), BigInteger.ZERO, BigInteger.valueOf(1002)));
        State state = empty(ID, observation(2));
        for (int date : java.util.List.of(1001, 1004)) {
            var retained = new RetainedFlags(Optional.of(1), Optional.empty(), Optional.empty(),
                    BigInteger.ONE, BigInteger.valueOf(date));
            assertThrows(IllegalArgumentException.class, () -> observe(state, sample(observation(3), retained)));
        }
    }

    private static Sample sample(ObservationIdentity source, Instance instance) { return new Sample(ID, source, instance, PROOF); }
    private static ExactRef ref(String name) { return new ExactRef("fixture/" + name + ".json", 1, "1".repeat(64)); }
    private static ObservationIdentity observation(int revision) {
        BigInteger value = BigInteger.valueOf(revision);
        var nativeFrame = new JointBudgetSelector.Frame(BigInteger.valueOf(73), value, BigInteger.valueOf(1000 + revision));
        return new ObservationIdentity("m6-software-fixture", new GameGeneration(42,
                new PythonOnlyUInt64(new BigInteger("9007199254740993"))),
                new JointBudgetSelector.ProposalFrame(nativeFrame, "snapshot-" + revision, value, "episode-1"), 1);
    }
}
