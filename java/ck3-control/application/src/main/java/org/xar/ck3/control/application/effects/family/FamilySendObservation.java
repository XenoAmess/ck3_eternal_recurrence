package org.xar.ck3.control.application.effects.family;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/**
 * DATA for the dedicated family-send settlement. A constructor or this structural
 * validation never qualifies native source, full storage, material matching or
 * writer exclusivity. The fixed registered native observer/replay must re-decode
 * BOTH original queries and all actual preparation through the sole domain codec.
 * A send is not a relationship, payment, alliance, gameplay day or SAVE result.
 */
public record FamilySendObservation(Profile profile, String actionId, String commandBodySha256,
        String originalRequestId, ExactRef originalDispatchRef, ExactRef preparedRequestRef,
        NativeEffectEvidence.FrameBasis beforeFrame, NativeEffectEvidence.FrameBasis afterFrame,
        ObservationIdentity before, ObservationIdentity after, G2Source source, String sessionId,
        PlanningReadReceipt beforeStorage, PlanningReadReceipt afterStorage, List<ExactRef> completePreparation,
        long nativePendingFullId, long definitionStableHash, List<ExpectedValue> actual) {
    public enum Profile {
        MARRIAGE(FamilyMarriageSendExpectation.SCHEMA), GUARDIAN("xar.java.family-action-observation/v1");
        private final String schema;
        Profile(String schema) { this.schema = schema; }
        public String observerSchema() { return schema; }
        public String firstIdentityField() { return this == MARRIAGE ? "subject_full_id" : "child_full_id"; }
        public String secondIdentityField() { return this == MARRIAGE ? "candidate_full_id" : "guardian_full_id"; }
    }
    public FamilySendObservation {
        Objects.requireNonNull(profile); StrictJson.text(actionId); StrictJson.text(originalRequestId);
        StrictJson.require(commandBodySha256 != null && commandBodySha256.matches("[a-f0-9]{64}"), "canonical original command digest required");
        nonempty(originalDispatchRef); nonempty(preparedRequestRef);
        Objects.requireNonNull(beforeFrame); Objects.requireNonNull(afterFrame);
        nonempty(beforeFrame.nativeFrame()); nonempty(beforeFrame.driverFacts());
        nonempty(afterFrame.nativeFrame()); nonempty(afterFrame.driverFacts());
        Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(source); StrictJson.text(sessionId);
        Objects.requireNonNull(beforeStorage); Objects.requireNonNull(afterStorage);
        completePreparation = List.copyOf(completePreparation);
        StrictJson.require(!completePreparation.isEmpty() && completePreparation.size() <= 32
                && new HashSet<>(completePreparation).size() == completePreparation.size(), "bounded complete ordered original preparation closure required");
        completePreparation.forEach(FamilySendObservation::nonempty);
        StrictJson.require(nativePendingFullId >= 0 && nativePendingFullId < 0xFFFF_FFFFL, "native pending FullID includes zero and excludes FFFFFFFF");
        StrictJson.require(definitionStableHash >= 0 && definitionStableHash <= 0xFFFF_FFFFL, "exact unsigned32 definition hash required");
        actual = List.copyOf(actual); requireSendOnlyValues(profile, nativePendingFullId, actual);
    }
    /** This native slot is derived from its observed full generation; it is not a host nonce. */
    public int nativeSlotIndex() { return (int) (nativePendingFullId & 0x00FF_FFFFL); }

    /** One exact expected-value contract for every family-send producer and consumer. */
    public static List<ExpectedValue> sendOnlyValues(Profile profile, long firstId, long secondId, long pendingFullId) {
        Objects.requireNonNull(profile); character(firstId); character(secondId);
        StrictJson.require(firstId != secondId, "distinct exact family pair required");
        StrictJson.require(pendingFullId >= 0 && pendingFullId < 0xFFFF_FFFFL, "native pending FullID required");
        List<ExpectedValue> values = new ArrayList<>();
        values.add(integer(profile.firstIdentityField(), firstId)); values.add(integer(profile.secondIdentityField(), secondId));
        values.add(bool("outbound_request_effect_observed", true)); values.add(integer("native_pending_full_id", pendingFullId));
        if (profile == Profile.MARRIAGE) {
            values.add(bool("marriage_relation_verified", false)); values.add(bool("alliance_verified", false)); values.add(bool("fees_verified", false));
        } else values.add(bool("guardian_relation_verified", false));
        values.add(bool("native.gameplay_verified", false)); values.add(bool("timeline.advance_verified", false));
        values.add(bool("timeline.checkpoint_eligible", false)); return List.copyOf(values);
    }

    /**
     * Core structural validation against actual archive originals. This deliberately
     * accepts the identical SEM basis and its old publication timestamp. Query custody,
     * never a relabelled SEM, establishes sampling time. Only successful actual ACK
     * with complete retained write/response custody is supported in this schema cut.
     * A true dispatch Unknown remains Pending until a separate response-free actual
     * write-custody contract is implemented and retained; no ACK is synthesized here.
     */
    public void validate(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        Objects.requireNonNull(command); Objects.requireNonNull(attempt); Objects.requireNonNull(dispatch);
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                && actionId.equals(command.actionId()) && commandBodySha256.equals(ActionCodec.bodySha256(command))
                && originalRequestId.equals(attempt.requestId()) && dispatch.requestId().equals(originalRequestId),
                "family send changed its exact canonical gameplay command or original attempt");
        StrictJson.require(command.expected().observerSchema().equals(profile.observerSchema())
                && before.equals(command.before()) && source.equals(command.source()) && sessionId.equals(command.sessionId()),
                "family send crossed its fixed expected observer/source/session/before frame");
        requireSameDay(before, after);
        StrictJson.require(beforeFrame.nativeFrame().equals(attempt.guard().nativeEvidence()),
                "family send replaced its actual original before native packet");
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived ack && ack.nativeOk()
                && ack.outbound().isPresent() && ack.custody().isPresent(),
                "family-send v1 requires an actual original successful ACK/write custody; Unknown cannot invent one");
        NativeActionPort.AckReceived ack = (NativeActionPort.AckReceived) dispatch;
        ack.custody().orElseThrow().verify(ack, attempt.guard());
        StrictJson.require(attempt.preparedRequest().step().equals(command.operation().value())
                && completePreparation.equals(attempt.preparedRequest().preparationEvidence()),
                "family send changed or truncated the original prepared request closure");
        StrictJson.require(beforeStorage.original().nativeOk() && afterStorage.original().nativeOk()
                && beforeStorage.before().originalBindingSha256().equals(beforeStorage.after().originalBindingSha256())
                && afterStorage.before().originalBindingSha256().equals(afterStorage.after().originalBindingSha256())
                && afterStorage.request().source().equals(source) && afterStorage.request().sessionId().equals(sessionId),
                "family storage query failed, crossed full binding or changed source/session");
        StrictJson.require(beforeStorage.request().origin() instanceof CommandOrigin.Gameplay
                && beforeStorage.request().before().equals(before)
                && beforeStorage.request().source().equals(source) && beforeStorage.request().sessionId().equals(sessionId),
                "family preparation query changed its actual original gameplay frame/source/session");
        for (var guard : List.of(beforeStorage.before(), beforeStorage.after())) {
            StrictJson.require(guard.binding().origin() instanceof CommandOrigin.Gameplay
                    && guard.binding().observed().equals(before)
                    && guard.binding().nativeEvidence().equals(beforeFrame.nativeFrame())
                    && guard.binding().connectionGeneration().equals(attempt.guard().connectionGeneration())
                    && guard.binding().source().equals(source) && guard.binding().sessionId().equals(sessionId),
                    "family preparation query crossed its full original guard");
        }
        StrictJson.require(afterStorage.request().origin() instanceof CommandOrigin.Reconciliation,
                "same-SEM family send requires the actual canonical original-pending reconciliation origin");
        var reconciliation = afterStorage.request().origin().requireReconciliation();
        var pending = reconciliation.pending();
        StrictJson.require(pending.actionId().equals(actionId) && pending.bodySha256().equals(commandBodySha256)
                && pending.requestId().equals(originalRequestId) && pending.originalBefore().equals(before)
                && reconciliation.factual().equals(after) && reconciliation.source().equals(source)
                && reconciliation.sessionId().equals(sessionId) && reconciliation.nativeEvidence().equals(afterFrame.nativeFrame())
                && reconciliation.evidence().observationManifest().equals(afterFrame.driverFacts())
                && reconciliation.connectionGeneration().equals(attempt.guard().connectionGeneration()),
                "family after query lost the actual original pending identity or retained full frame");
        for (var guard : List.of(afterStorage.before(), afterStorage.after())) {
            StrictJson.require(guard.binding().origin() instanceof CommandOrigin.Reconciliation
                    && guard.binding().origin().requireReconciliation().sameGuardFrame(reconciliation)
                    && guard.binding().nativeEvidence().equals(afterFrame.nativeFrame())
                    && guard.binding().source().equals(source) && guard.binding().sessionId().equals(sessionId)
                    && guard.binding().connectionGeneration().equals(reconciliation.connectionGeneration())
                    && guard.originalBindingSha256().equals(reconciliation.bindingSha256()),
                    "family after query changed its actual pending/source/connection/full Driver guard");
        }
        StrictJson.require(!beforeStorage.requestId().equals(originalRequestId) && !afterStorage.requestId().equals(originalRequestId)
                && !beforeStorage.requestId().equals(afterStorage.requestId()), "submission ACK is not an independent storage query");
        NativeRequestChronology.requireBeforeSubmission(beforeStorage, attempt, ack);
        NativeRequestChronology.requireSampledAfter(afterStorage, attempt, ack);
        StrictJson.require(ProposalLifecycle.compare(command.expected(), after, source, profile.observerSchema(), actual)
                == ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "family send did not prove its exact original pair/expectation");
    }

    /** Physical archive validation adds integrity to the exact same shared structural contract; it still grants no native domain qualification. */
    public void validate(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, ActionPorts.OutcomeArchive archive) {
        validate(command, attempt, dispatch); Objects.requireNonNull(archive);
        StrictJson.require(originalDispatchRef.equals(archive.referenceOf(dispatch)) && archive.load(originalDispatchRef).equals(dispatch),
                "family send substituted its archived original dispatch");
        StrictJson.require(preparedRequestRef.equals(archive.requestReferenceOf(attempt.preparedRequest()))
                && archive.loadRequest(preparedRequestRef).equals(attempt.preparedRequest()),
                "family send changed its archived original prepared request");
        NativeRecordedEvidenceVerifier.requireRead(beforeStorage, archive); NativeRecordedEvidenceVerifier.requireRead(afterStorage, archive);
        ExactRef beforeRead = archive.readReferenceOf(beforeStorage), afterRead = archive.readReferenceOf(afterStorage);
        StrictJson.require(archive.loadRead(beforeRead).equals(beforeStorage) && archive.loadRead(afterRead).equals(afterStorage)
                && !beforeRead.equals(afterRead) && completePreparation.contains(beforeRead),
                "both actual independent storage queries and the complete original before baseline must be retained");
    }

    /** Actual originals only; the fixed native domain must additionally replay full roles, options, occupancy and writer exclusion. */
    public OriginalFrames loadFrames(ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader originalFrames) {
        Objects.requireNonNull(archive); Objects.requireNonNull(originalFrames);
        Complete originalBefore = originalFrames.load(beforeFrame, archive), originalAfter = originalFrames.load(afterFrame, archive);
        requireFrame(originalBefore, beforeFrame, before); requireFrame(originalAfter, afterFrame, after);
        StrictJson.require(beforeStorage.before().originalBindingSha256().equals(originalBefore.fullBindingSha256())
                && beforeStorage.after().originalBindingSha256().equals(originalBefore.fullBindingSha256()),
                "family preparation query did not retain its complete original before Driver binding");
        StrictJson.require(originalBefore.connectionGeneration().equals(originalAfter.connectionGeneration()),
                "family send crossed the actual held connection");
        return new OriginalFrames(originalBefore, originalAfter);
    }
    public record OriginalFrames(Complete before, Complete after) {
        public OriginalFrames { Objects.requireNonNull(before); Objects.requireNonNull(after); }
    }

    /** All refs are existing immutable archive objects; this method performs no writes or native requests. */
    public List<ExactRef> references(ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(archive); LinkedHashSet<ExactRef> refs = new LinkedHashSet<>();
        refs.add(originalDispatchRef); refs.add(preparedRequestRef);
        refs.add(beforeFrame.nativeFrame()); refs.add(beforeFrame.driverFacts());
        refs.add(afterFrame.nativeFrame()); refs.add(afterFrame.driverFacts());
        refs.add(archive.readReferenceOf(beforeStorage)); refs.add(archive.readReferenceOf(afterStorage));
        refs.addAll(completePreparation);
        for (var read : List.of(beforeStorage, afterStorage)) for (var original : List.of(read.before().binding(), read.after().binding())) {
            refs.add(original.nativeEvidence()); refs.add(original.capabilityEvidence()); refs.addAll(original.supportingEvidence());
            if (original.origin() instanceof CommandOrigin.Reconciliation) {
                var identity = original.origin().requireReconciliation();
                refs.addAll(identity.evidence().originals()); refs.add(identity.pending().originalReceipt()); refs.add(identity.pending().originalBeforeDriver());
            }
        }
        return List.copyOf(refs);
    }
    private void requireFrame(Complete value, NativeEffectEvidence.FrameBasis basis, ObservationIdentity identity) {
        StrictJson.require(value.identity().equals(identity) && value.source().equals(source) && value.sessionId().equals(sessionId)
                && NativeEffectEvidence.basis(value).equals(basis), "family frame was not rebuilt from its exact original packet and full Driver manifest");
    }
    private static void requireSameDay(ObservationIdentity before, ObservationIdentity after) {
        StrictJson.require(before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.observationVersion() == after.observationVersion()
                && before.frame().episodeRunId().equals(after.frame().episodeRunId())
                && before.frame().identity().player().equals(after.frame().identity().player())
                && before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw())
                && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) >= 0
                && after.frame().revision().compareTo(before.frame().revision()) >= 0,
                "family send crossed Game/player/episode/day/version or regressed an actual frame");
    }
    /** Closed DATA values only; this does not prove a native send or grant settlement authority. */
    public static void requireSendOnlyValues(Profile profile, long pendingId, List<ExpectedValue> actual) {
        Objects.requireNonNull(profile); Objects.requireNonNull(actual);
        String first = profile.firstIdentityField(), second = profile.secondIdentityField();
        ExpectedInteger left = null, right = null;
        for (ExpectedValue value : actual) {
            if (value instanceof ExpectedInteger number && number.field().value().equals(first)) left = number;
            if (value instanceof ExpectedInteger number && number.field().value().equals(second)) right = number;
        }
        StrictJson.require(left != null && right != null, "typed complete family pair is absent");
        List<ExpectedValue> expected = sendOnlyValues(profile, left.value().longValueExact(), right.value().longValueExact(), pendingId);
        StrictJson.require(actual.equals(expected), "family send values must be the complete exact ordered send-only contract");
    }
    private static ExpectedInteger integer(String key, long value) { return new ExpectedInteger(new FieldKey(key), BigInteger.valueOf(value)); }
    private static ExpectedBoolean bool(String key, boolean value) { return new ExpectedBoolean(new FieldKey(key), value); }
    private static void character(long id) { StrictJson.require(id > 0 && id < 0xFFFF_FFFFL, "full unsigned native character identity required"); }
    private static void nonempty(ExactRef ref) { Objects.requireNonNull(ref); StrictJson.require(ref.bytes() > 0, "nonempty actual original archive object required"); }
}

