package org.xar.ck3.control.wave2.finance.giftpending;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Baseline;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ObjectEvidence;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ResolvedOutcome;

/** Actual pure cold classifier. A targeting-vector disappearance is never resolution evidence. */
public final class GiftColdRecovery {
    private GiftColdRecovery() { }
    public enum Presence { MISSING, NULL, VALUE }
    public record Read<T>(Presence presence, T value) {
        public Read {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) { throw new IllegalArgumentException("read presence mismatch"); }
        }
        public static <T> Read<T> missing() { return new Read<>(Presence.MISSING, null); }
        public static <T> Read<T> nil() { return new Read<>(Presence.NULL, null); }
        public static <T> Read<T> of(T value) { return new Read<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean is(T expected) { return presence == Presence.VALUE && Objects.equals(value, expected); }
        public boolean known() { return presence == Presence.VALUE; }
    }
    public record PostObservation(Read<BigInteger> snapshotRevision, Read<BigInteger> nativeSnapshotRevision,
            Read<BigInteger> observedDateRaw, Read<BigInteger> playerCharacterId, Read<Boolean> playerResourcesQueryComplete,
            Read<BigInteger> playerGoldRaw, Read<Boolean> recipientIdentityResolved, Read<BigInteger> recipientCharacterId,
            Read<Boolean> recipientAlive, Read<Boolean> recipientOpinionQueryComplete, Read<BigInteger> recipientOpinionOfPlayer,
            Read<Boolean> giftOpinionPresent, Read<BigInteger> giftOpinionModifierValue,
            Read<Boolean> sourceFactionRequeryComplete, Read<BigInteger> queriedSourceFactionId,
            Read<Boolean> sourceFactionPresent, Read<Boolean> sourceFactionMetricsAvailable,
            Read<Boolean> sourceFactionTargetingPlayer, Read<BigInteger> sourceFactionPowerRaw,
            Read<BigInteger> sourceFactionDiscontentRaw, Read<List<BigInteger>> sourceFactionMemberCharacterIds,
            ObjectEvidence evidence) {
        public PostObservation {
            if (sourceFactionMemberCharacterIds.known()) {
                sourceFactionMemberCharacterIds = Read.of(List.copyOf(sourceFactionMemberCharacterIds.value()));
            }
            Objects.requireNonNull(evidence);
        }
    }
    public record Recovery(Read<BigInteger> schemaVersion, Read<String> status, Read<Boolean> privateBuild,
            Read<Boolean> advertised, Read<Boolean> newProcessConfirmed, Read<String> newRoundId,
            Read<BigInteger> newBridgePid, Read<String> newBridgeCreationDate, Read<String> episodeRunId,
            Read<Boolean> paused, Read<Boolean> mapReady, Read<Boolean> independentFactionStorageLookupComplete,
            Read<Boolean> independentRecipientLookupComplete, Read<Boolean> selectedFromCurrentTargetingVector,
            Read<Boolean> saveIsPreActionCheckpoint, Read<String> selectedSaveSha256, Read<PostObservation> postObservation) { }
    public enum Reason {
        INDEPENDENT_POST_OBSERVATION_MISSING("independent_post_observation_missing"),
        PROCESS_OR_INDEPENDENT_ENTITY_FACTS_UNPROVEN("process_or_independent_entity_facts_unproven"),
        MATERIAL_OUTCOME_NOT_DISTINGUISHABLE("material_outcome_not_distinguishable"),
        INDEPENDENT_GOLD_GIFT_AND_FACTION_READBACK("independent_gold_gift_and_faction_readback"),
        PRE_ACTION_SAVE_AND_INDEPENDENT_WORLD_FACTS_MATCH("pre_action_save_and_independent_world_facts_match");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public sealed interface Result permits Applied, Unchanged, Unresolved {
        Reason reason();
        default boolean publicCapabilityAdvertised() { return false; }
        /** UNCHANGED authorizes selection of a different identity; the old identity remains retired. */
        default boolean actionRetryAllowed() { return this instanceof Unchanged; }
        default boolean originalRequestReplayAllowed() { return false; }
    }
    public record Applied(String requestId, String newRoundId, BigInteger newBridgePid,
            String newBridgeCreationDate, PostObservation postObservation, Read<Boolean> threatResolved) implements Result {
        @Override public Reason reason() { return Reason.INDEPENDENT_GOLD_GIFT_AND_FACTION_READBACK; }
    }
    public record Unchanged(String requestId, String newRoundId, BigInteger newBridgePid) implements Result {
        @Override public Reason reason() { return Reason.PRE_ACTION_SAVE_AND_INDEPENDENT_WORLD_FACTS_MATCH; }
    }
    public record Unresolved(Reason reason) implements Result {
        public Unresolved {
            if (reason != Reason.INDEPENDENT_POST_OBSERVATION_MISSING
                    && reason != Reason.PROCESS_OR_INDEPENDENT_ENTITY_FACTS_UNPROVEN
                    && reason != Reason.MATERIAL_OUTCOME_NOT_DISTINGUISHABLE) {
                throw new IllegalArgumentException("unresolved reason required");
            }
        }
    }
    public record Resolution(Result result, Ledger ledger) { }

    public static Result evaluate(PendingAction pending, Recovery recovery) {
        Objects.requireNonNull(pending); Objects.requireNonNull(recovery);
        if (!recovery.postObservation().known()) { return unknown(Reason.INDEPENDENT_POST_OBSERVATION_MISSING); }
        PostObservation post = recovery.postObservation().value(); Baseline pre = pending.baseline();
        if (!(recovery.schemaVersion().is(BigInteger.ONE) && recovery.status().is("independent_read_complete")
                && recovery.privateBuild().is(true) && recovery.advertised().is(false) && recovery.newProcessConfirmed().is(true)
                && round(recovery.newRoundId()) && !recovery.newRoundId().is(pending.sourceRoundId())
                && positive(recovery.newBridgePid()) && text(recovery.newBridgeCreationDate())
                && !(recovery.newBridgePid().is(pending.sourceProcess().pid())
                     && recovery.newBridgeCreationDate().is(pending.sourceProcess().creationDate()))
                && recovery.episodeRunId().is(pending.episodeRunId()) && recovery.paused().is(true) && recovery.mapReady().is(true)
                && positive(post.snapshotRevision()) && positive(post.nativeSnapshotRevision())
                && post.observedDateRaw().is(pre.dateRaw()) && post.playerCharacterId().is(pre.playerCharacterId())
                && post.playerResourcesQueryComplete().is(true) && post.recipientIdentityResolved().is(true)
                && post.recipientCharacterId().is(pre.recipientCharacterId()) && post.recipientAlive().is(true)
                && post.recipientOpinionQueryComplete().is(true) && post.sourceFactionRequeryComplete().is(true)
                && post.queriedSourceFactionId().is(pre.sourceFactionId())
                && recovery.independentFactionStorageLookupComplete().is(true)
                && recovery.independentRecipientLookupComplete().is(true)
                && recovery.selectedFromCurrentTargetingVector().is(false) && nonnegative(post.playerGoldRaw())
                && post.giftOpinionPresent().known() && post.sourceFactionPresent().known())) {
            return unknown(Reason.PROCESS_OR_INDEPENDENT_ENTITY_FACTS_UNPROVEN);
        }
        if (post.playerGoldRaw().is(pre.playerGoldRaw().subtract(pre.goldCostRaw()))
                && post.giftOpinionPresent().is(true) && post.giftOpinionModifierValue().is(pre.opinionDelta())
                && (post.sourceFactionPresent().is(false) || post.sourceFactionMetricsAvailable().is(true))) {
            Read<Boolean> threat = Read.nil();
            if (post.sourceFactionPresent().is(false)) { threat = Read.of(true); }
            else if (post.sourceFactionMemberCharacterIds().known() && post.sourceFactionTargetingPlayer().known()) {
                threat = Read.of(!(post.sourceFactionTargetingPlayer().is(true)
                        && post.sourceFactionMemberCharacterIds().value().contains(pre.recipientCharacterId())));
            }
            return new Applied(pending.requestId(), recovery.newRoundId().value(), recovery.newBridgePid().value(),
                    recovery.newBridgeCreationDate().value(), post, threat);
        }
        if (recovery.saveIsPreActionCheckpoint().is(true)
                && recovery.selectedSaveSha256().is(pending.checkpointSha256BeforeSubmit())
                && post.playerGoldRaw().is(pre.playerGoldRaw()) && post.giftOpinionPresent().is(false)
                // Python .get treats both absent and null modifier as None on this branch.
                && !post.giftOpinionModifierValue().known()
                && post.recipientOpinionOfPlayer().is(pre.recipientOpinionOfPlayer())
                && post.sourceFactionPresent().is(true) && post.sourceFactionTargetingPlayer().is(true)
                && post.sourceFactionMetricsAvailable().is(true) && post.sourceFactionPowerRaw().is(pre.sourceFactionPowerRaw())
                && post.sourceFactionDiscontentRaw().is(pre.sourceFactionDiscontentRaw())
                && post.sourceFactionMemberCharacterIds().is(pre.sourceFactionMemberCharacterIds())) {
            return new Unchanged(pending.requestId(), recovery.newRoundId().value(), recovery.newBridgePid().value());
        }
        return unknown(Reason.MATERIAL_OUTCOME_NOT_DISTINGUISHABLE);
    }
    public static Resolution resolve(Ledger ledger, String requestId, Recovery recovery) {
        Result result = evaluate(GiftPendingReducer.matching(ledger, requestId), recovery);
        Ledger candidate = switch (result) {
            case Applied ignored -> GiftPendingReducer.retire(ledger, requestId, ResolvedOutcome.APPLIED);
            case Unchanged ignored -> GiftPendingReducer.retire(ledger, requestId, ResolvedOutcome.UNCHANGED);
            case Unresolved ignored -> ledger;
        };
        return new Resolution(result, candidate);
    }
    private static Result unknown(Reason reason) { return new Unresolved(reason); }
    private static boolean positive(Read<BigInteger> value) { return value.known() && value.value().signum() > 0; }
    private static boolean nonnegative(Read<BigInteger> value) { return value.known() && value.value().signum() >= 0; }
    private static boolean text(Read<String> value) { return value.known() && !value.value().isEmpty(); }
    private static boolean round(Read<String> value) { return text(value) && value.value().matches("R[\\p{IsDigit}]+"); }
}
