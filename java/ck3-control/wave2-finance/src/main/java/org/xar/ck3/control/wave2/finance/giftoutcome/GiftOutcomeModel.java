package org.xar.ck3.control.wave2.finance.giftoutcome;

import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Immutable decision projection of the existing resolved-gift observer. */
public final class GiftOutcomeModel {
    public static final String STEP = "query-resolved-faction-gift-outcome-v1";
    public static final String SCHEMA = "xar.ck3.resolved_faction_gift_outcome.v1";
    public static final String SUBMIT_STEP = "private-submit-faction-gift-member-v1";
    public static final String RECEIPT_STEP = "private-query-faction-gift-receipt-v1";
    public static final String PAIR_STEP = "private-query-faction-gift-cold-recovery-v1";
    public static final String ALERT_STEP = "query-player-faction-alerts-v1";
    private GiftOutcomeModel() { }

    public enum Truth { TRUE, FALSE, UNKNOWN }
    public enum FactionOutcome {
        STILL_MEMBER("still_member"), RECIPIENT_LEFT("recipient_left"), FACTION_KNOWN_ABSENT("faction_known_absent");
        private final String wire;
        FactionOutcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Reason {
        CURRENT_PAUSED_PLAYER_UNAVAILABLE("current_paused_player_unavailable"),
        ORIGINAL_APPLIED_GIFT_NOT_IN_CURRENT_EPISODE_HISTORY("original_applied_gift_not_in_current_episode_history"),
        CURRENT_DATE_PRECEDES_ORIGINAL_MATERIAL("current_date_precedes_original_material"),
        INDEPENDENT_PAIR_UNAVAILABLE("independent_pair_unavailable"),
        INDEPENDENT_PAIR_INCOMPLETE("independent_pair_incomplete"),
        CURRENT_FACTION_MATERIAL_INCOMPLETE("current_faction_material_incomplete"),
        CURRENT_PAUSED_FRAME_CHANGED("current_paused_frame_changed");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Canonical, immutable JSON evidence. Domain decisions use the typed projection beside it. */
    public static final class WireValue {
        private final byte[] json;
        WireValue(byte[] json) { this.json = Objects.requireNonNull(json, "json").clone(); }
        public byte[] json() { return json.clone(); }
        @Override public boolean equals(Object other) {
            return other instanceof WireValue value && Arrays.equals(json, value.json);
        }
        @Override public int hashCode() { return Arrays.hashCode(json); }
    }

    public record Request(String requestId, BigInteger expectedRevision) {
        public Request {
            nonempty(requestId, "requestId"); Objects.requireNonNull(expectedRevision, "expectedRevision");
        }
    }
    public record Snapshot(Optional<String> snapshotId, Optional<BigInteger> revision,
                           Optional<BigInteger> nativeRevision, Optional<BigInteger> dateRaw,
                           Optional<String> episodeRunId, Truth paused, Truth mapReady,
                           Optional<BigInteger> actorId, Truth actorAlive,
                           WireValue activeEvent, WireValue pendingInteraction) {
        public Snapshot {
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(episodeRunId); Objects.requireNonNull(paused);
            Objects.requireNonNull(mapReady); Objects.requireNonNull(actorId); Objects.requireNonNull(actorAlive);
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingInteraction);
        }
        public boolean ready() {
            return paused == Truth.TRUE && mapReady == Truth.TRUE && actorAlive == Truth.TRUE
                    && nativeRevision.isPresent() && dateRaw.isPresent() && actorId.isPresent();
        }
        /** The exact original _binding fields; episode is intentionally not part of this binding. */
        public Binding binding() {
            return new Binding(snapshotId, revision, nativeRevision, dateRaw, paused, mapReady,
                    actorId, actorAlive, activeEvent, pendingInteraction);
        }
    }
    public record Binding(Optional<String> snapshotId, Optional<BigInteger> revision,
                          Optional<BigInteger> nativeRevision, Optional<BigInteger> dateRaw,
                          Truth paused, Truth mapReady, Optional<BigInteger> actorId, Truth actorAlive,
                          WireValue activeEvent, WireValue pendingInteraction) { }

    public record PendingHistory(Optional<String> requestId, Optional<String> episodeRunId,
                                 Optional<BigInteger> actorId, Optional<BigInteger> sourceFactionId,
                                 Optional<BigInteger> recipientId, Optional<BigInteger> actionDateRaw,
                                 Optional<BigInteger> goldCostRaw, Optional<BigInteger> opinionDelta,
                                 Optional<BigInteger> preRecipientOpinion,
                                 Optional<BigInteger> preFactionPower, Optional<BigInteger> preFactionDiscontent) {
        public PendingHistory {
            Objects.requireNonNull(requestId); Objects.requireNonNull(episodeRunId); Objects.requireNonNull(actorId);
            Objects.requireNonNull(sourceFactionId); Objects.requireNonNull(recipientId); Objects.requireNonNull(actionDateRaw);
            Objects.requireNonNull(goldCostRaw); Objects.requireNonNull(opinionDelta); Objects.requireNonNull(preRecipientOpinion);
            Objects.requireNonNull(preFactionPower); Objects.requireNonNull(preFactionDiscontent);
        }
    }
    public record ReceiptHistory(Optional<String> requestId, Optional<BigInteger> schemaVersion,
                                 Optional<String> status, Truth postconditionVerified, Truth mitigationApplied,
                                 Optional<BigInteger> actorId, Optional<BigInteger> sourceFactionId,
                                 Optional<BigInteger> recipientId, Optional<BigInteger> materialDateRaw,
                                 WireValue original) {
        public ReceiptHistory {
            Objects.requireNonNull(requestId); Objects.requireNonNull(schemaVersion); Objects.requireNonNull(status);
            Objects.requireNonNull(postconditionVerified); Objects.requireNonNull(mitigationApplied); Objects.requireNonNull(actorId);
            Objects.requireNonNull(sourceFactionId); Objects.requireNonNull(recipientId); Objects.requireNonNull(materialDateRaw);
            Objects.requireNonNull(original);
        }
        boolean eligible(String request) {
            return requestId.filter(request::equals).isPresent()
                    && schemaVersion.filter(BigInteger.ONE::equals).isPresent()
                    && status.filter(value -> value.equals("mitigated") || value.equals("left")).isPresent()
                    && postconditionVerified == Truth.TRUE && mitigationApplied == Truth.TRUE;
        }
    }
    public record HistoryEntry(String selectedStep, Truth ok, Optional<PendingHistory> pending,
                               Optional<ReceiptHistory> receipt, Optional<Alert> directAlert) {
        public HistoryEntry {
            Objects.requireNonNull(selectedStep); Objects.requireNonNull(ok); Objects.requireNonNull(pending);
            Objects.requireNonNull(receipt); Objects.requireNonNull(directAlert);
        }
    }
    public record OriginalGift(String requestId, Optional<String> episodeRunId, BigInteger actorId,
                               BigInteger sourceFactionId, BigInteger recipientId,
                               Optional<BigInteger> actionDateRaw, BigInteger materialDateRaw,
                               Optional<BigInteger> goldCostRaw, Optional<BigInteger> opinionDelta,
                               Optional<BigInteger> preRecipientOpinion, Optional<BigInteger> preFactionPower,
                               Optional<BigInteger> preFactionDiscontent, WireValue receipt) {
        public OriginalGift {
            nonempty(requestId, "requestId"); Objects.requireNonNull(episodeRunId); positive(actorId); positive(sourceFactionId);
            positive(recipientId); Objects.requireNonNull(actionDateRaw); Objects.requireNonNull(materialDateRaw);
            Objects.requireNonNull(goldCostRaw); Objects.requireNonNull(opinionDelta); Objects.requireNonNull(preRecipientOpinion);
            Objects.requireNonNull(preFactionPower); Objects.requireNonNull(preFactionDiscontent); Objects.requireNonNull(receipt);
        }
    }
    public record PairRequest(BigInteger expectedRevision, BigInteger expectedDateRaw,
                              BigInteger expectedPlayerId, BigInteger sourceFactionId, BigInteger recipientId) {
        public PairRequest {
            Objects.requireNonNull(expectedRevision); Objects.requireNonNull(expectedDateRaw);
            positive(expectedPlayerId); positive(sourceFactionId); positive(recipientId);
        }
    }
    public record PairObservation(Truth available, Truth paused, Optional<BigInteger> snapshotRevision,
                                  Optional<BigInteger> nativeSnapshotRevision, Optional<BigInteger> observedDateRaw,
                                  Optional<BigInteger> playerId, Truth factionRequeryComplete,
                                  Optional<BigInteger> queriedFactionId, Truth factionPresent, Truth metricsAvailable,
                                  Optional<BigInteger> leaderId, Optional<List<BigInteger>> memberIds,
                                  Truth recipientIdentityResolved, Optional<BigInteger> recipientId,
                                  Truth recipientOpinionQueryComplete, Optional<BigInteger> recipientOpinion,
                                  Truth giftOpinionPresent, WireValue original) {
        public PairObservation {
            Objects.requireNonNull(available); Objects.requireNonNull(paused); Objects.requireNonNull(snapshotRevision);
            Objects.requireNonNull(nativeSnapshotRevision); Objects.requireNonNull(observedDateRaw); Objects.requireNonNull(playerId);
            Objects.requireNonNull(factionRequeryComplete); Objects.requireNonNull(queriedFactionId); Objects.requireNonNull(factionPresent);
            Objects.requireNonNull(metricsAvailable); Objects.requireNonNull(leaderId);
            memberIds = Objects.requireNonNull(memberIds).map(List::copyOf);
            Objects.requireNonNull(recipientIdentityResolved); Objects.requireNonNull(recipientId);
            Objects.requireNonNull(recipientOpinionQueryComplete); Objects.requireNonNull(recipientOpinion);
            Objects.requireNonNull(giftOpinionPresent); Objects.requireNonNull(original);
        }
    }
    public sealed interface PairRead permits PairPacket, PairUnavailable { }
    public record PairPacket(Optional<String> step, Truth accepted, Optional<String> status,
                             Optional<BigInteger> failureFlags, PairObservation observation) implements PairRead {
        public PairPacket { Objects.requireNonNull(step); Objects.requireNonNull(accepted); Objects.requireNonNull(status);
            Objects.requireNonNull(failureFlags); Objects.requireNonNull(observation); }
    }
    public record PairUnavailable(String error) implements PairRead {
        public PairUnavailable { Objects.requireNonNull(error); }
    }
    public record AlertRow(Optional<BigInteger> factionId, WireValue original) {
        public AlertRow { Objects.requireNonNull(factionId); Objects.requireNonNull(original); }
    }
    public record Alert(Optional<String> status, Optional<BigInteger> snapshotRevision, Optional<BigInteger> dateRaw,
                        Optional<BigInteger> playerId, Truth sameFrameReady, Truth targetingRowsReady,
                        Truth stockDangerousReady, Optional<List<AlertRow>> targetingRows) {
        public Alert {
            Objects.requireNonNull(status); Objects.requireNonNull(snapshotRevision); Objects.requireNonNull(dateRaw);
            Objects.requireNonNull(playerId); Objects.requireNonNull(sameFrameReady); Objects.requireNonNull(targetingRowsReady);
            Objects.requireNonNull(stockDangerousReady); targetingRows = Objects.requireNonNull(targetingRows).map(List::copyOf);
        }
        boolean sameFrame(Snapshot frame) {
            return snapshotRevision.equals(frame.nativeRevision()) && dateRaw.equals(frame.dateRaw())
                    && playerId.equals(frame.actorId());
        }
    }
    public sealed interface AlertRead permits AlertPacket, AlertReadUnavailable { }
    public record AlertPacket(Alert alert) implements AlertRead { public AlertPacket { Objects.requireNonNull(alert); } }
    public record AlertReadUnavailable(String error) implements AlertRead { public AlertReadUnavailable { Objects.requireNonNull(error); } }
    public sealed interface CurrentAlert permits AlertObserved, AlertAbsent, AlertUnavailable { }
    public record AlertObserved(AlertRow row) implements CurrentAlert { public AlertObserved { Objects.requireNonNull(row); } }
    public record AlertAbsent() implements CurrentAlert { }
    public record AlertUnavailable(String reason) implements CurrentAlert { public AlertUnavailable { Objects.requireNonNull(reason); } }
    public sealed interface Outcome permits Unavailable, Observed { Request request(); Snapshot frame(); Optional<OriginalGift> original(); }
    public record Unavailable(Request request, Snapshot frame, Optional<OriginalGift> original,
                              Reason reason, Optional<String> observerError) implements Outcome {
        public Unavailable {
            Objects.requireNonNull(request); Objects.requireNonNull(frame); Objects.requireNonNull(original);
            Objects.requireNonNull(reason); Objects.requireNonNull(observerError);
            if (observerError.isPresent() && reason != Reason.INDEPENDENT_PAIR_UNAVAILABLE) throw new IllegalArgumentException("observer error branch");
        }
    }
    public record Observed(Request request, Snapshot frame, OriginalGift gift, FactionOutcome factionOutcome,
                           PairObservation currentObservation, CurrentAlert currentAlert, boolean followupDateAdvanced) implements Outcome {
        public Observed {
            Objects.requireNonNull(request); Objects.requireNonNull(frame); Objects.requireNonNull(gift);
            Objects.requireNonNull(factionOutcome); Objects.requireNonNull(currentObservation); Objects.requireNonNull(currentAlert);
            if (!frame.ready() || !request.requestId().equals(gift.requestId())
                    || !frame.actorId().filter(gift.actorId()::equals).isPresent()
                    || !frame.episodeRunId().equals(gift.episodeRunId())
                    || followupDateAdvanced != (frame.dateRaw().orElseThrow().compareTo(gift.materialDateRaw()) > 0)) {
                throw new IllegalArgumentException("observed gift frame mismatch");
            }
        }
        @Override public Optional<OriginalGift> original() { return Optional.of(gift); }
        public boolean attributedToGift() { return false; }
        public boolean giftSubmitPerformed() { return false; }
        public boolean pendingResolutionPerformed() { return false; }
    }
    private static void nonempty(String value, String field) {
        if (Objects.requireNonNull(value, field).isEmpty() || value.codePointCount(0, value.length()) > 32768) throw new IllegalArgumentException(field);
    }
    private static void positive(BigInteger value) {
        if (Objects.requireNonNull(value).signum() <= 0) throw new IllegalArgumentException("positive identity required");
    }
}
