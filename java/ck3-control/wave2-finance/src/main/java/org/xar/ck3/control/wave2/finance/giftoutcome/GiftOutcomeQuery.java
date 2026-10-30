package org.xar.ck3.control.wave2.finance.giftoutcome;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import static org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeModel.*;

/** Existing-session read only orchestration; no gift submission, pending resolver or ledger writer. */
public final class GiftOutcomeQuery {
    private GiftOutcomeQuery() { }
    public interface ExistingDriver {
        Snapshot takeSemanticSnapshot();
        List<HistoryEntry> projectRelevantHistoryUnderOriginalLock(Request request, Snapshot before);
        PairRead readIndependentPair(PairRequest request);
        AlertRead readCurrentAlert(BigInteger expectedRevision);
        void recordObservedCommand(Observed outcome);
    }
    public static final class RevisionMismatchException extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        public RevisionMismatchException() { super("resolved gift outcome revision changed"); }
    }

    public static Outcome query(ExistingDriver driver, Request request) {
        Objects.requireNonNull(driver); Objects.requireNonNull(request);
        Snapshot before = Objects.requireNonNull(driver.takeSemanticSnapshot());
        if (!before.revision().filter(request.expectedRevision()::equals).isPresent()) throw new RevisionMismatchException();
        if (!before.ready()) return unavailable(request, before, Optional.empty(), Reason.CURRENT_PAUSED_PLAYER_UNAVAILABLE);
        List<HistoryEntry> history = List.copyOf(driver.projectRelevantHistoryUnderOriginalLock(request, before));
        Optional<OriginalGift> original = original(history, request.requestId(), before);
        if (original.isEmpty()) return unavailable(request, before, original, Reason.ORIGINAL_APPLIED_GIFT_NOT_IN_CURRENT_EPISODE_HISTORY);
        OriginalGift gift = original.orElseThrow();
        if (before.dateRaw().orElseThrow().compareTo(gift.materialDateRaw()) < 0) {
            return unavailable(request, before, original, Reason.CURRENT_DATE_PRECEDES_ORIGINAL_MATERIAL);
        }
        PairRequest pairRequest = new PairRequest(before.nativeRevision().orElseThrow(), before.dateRaw().orElseThrow(),
                GiftPendingModel.rawCharacterIdFromPublic(before.actorId().orElseThrow()), gift.sourceFactionId(), gift.recipientId());
        PairRead read = Objects.requireNonNull(driver.readIndependentPair(pairRequest));
        if (read instanceof PairUnavailable error) {
            return new Unavailable(request, before, original, Reason.INDEPENDENT_PAIR_UNAVAILABLE, Optional.of(error.error()));
        }
        PairPacket packet = (PairPacket) read;
        PairObservation observed = packet.observation();
        if (!complete(packet, pairRequest)) return unavailable(request, before, original, Reason.INDEPENDENT_PAIR_INCOMPLETE);
        boolean present = observed.factionPresent() == Truth.TRUE;
        if (present && (observed.metricsAvailable() != Truth.TRUE || observed.memberIds().isEmpty())) {
            return unavailable(request, before, original, Reason.CURRENT_FACTION_MATERIAL_INCOMPLETE);
        }
        boolean member = present && (observed.leaderId().filter(gift.recipientId()::equals).isPresent()
                || observed.memberIds().orElseThrow().contains(gift.recipientId()));
        CurrentAlert currentAlert = alert(driver, history, before, request.expectedRevision(), gift.sourceFactionId());
        if (!Objects.requireNonNull(driver.takeSemanticSnapshot()).binding().equals(before.binding())) {
            return unavailable(request, before, original, Reason.CURRENT_PAUSED_FRAME_CHANGED);
        }
        Observed outcome = new Observed(request, before, gift,
                !present ? FactionOutcome.FACTION_KNOWN_ABSENT : member ? FactionOutcome.STILL_MEMBER : FactionOutcome.RECIPIENT_LEFT,
                observed, currentAlert, before.dateRaw().orElseThrow().compareTo(gift.materialDateRaw()) > 0);
        driver.recordObservedCommand(outcome);
        return outcome;
    }

    /** The newest eligible receipt and newest submit are selected independently, exactly as the old producer. */
    public static Optional<OriginalGift> original(List<HistoryEntry> history, String requestId, Snapshot frame) {
        Objects.requireNonNull(history); Objects.requireNonNull(requestId); Objects.requireNonNull(frame);
        PendingHistory pending = null; ReceiptHistory receipt = null;
        for (int index = history.size() - 1; index >= 0; index--) {
            HistoryEntry row = history.get(index);
            if (row.ok() != Truth.TRUE) continue;
            if (receipt == null && row.selectedStep().equals(RECEIPT_STEP) && row.receipt().filter(value -> value.eligible(requestId)).isPresent()) {
                receipt = row.receipt().orElseThrow();
            }
            if (pending == null && row.selectedStep().equals(SUBMIT_STEP)
                    && row.pending().filter(value -> value.requestId().filter(requestId::equals).isPresent()).isPresent()) {
                pending = row.pending().orElseThrow();
            }
            if (pending != null && receipt != null) break;
        }
        Optional<BigInteger> rawActor = frame.actorId().map(GiftPendingModel::rawCharacterIdFromPublic);
        if (pending == null || receipt == null || !pending.episodeRunId().equals(frame.episodeRunId())
                || !pending.actorId().equals(rawActor) || !receipt.actorId().equals(rawActor)
                || !receipt.sourceFactionId().equals(pending.sourceFactionId())
                || !receipt.recipientId().equals(pending.recipientId())
                || receipt.sourceFactionId().isEmpty() || receipt.recipientId().isEmpty()
                || receipt.materialDateRaw().isEmpty()) return Optional.empty();
        return Optional.of(new OriginalGift(requestId, frame.episodeRunId(), rawActor.orElseThrow(),
                receipt.sourceFactionId().orElseThrow(), receipt.recipientId().orElseThrow(), pending.actionDateRaw(),
                receipt.materialDateRaw().orElseThrow(), pending.goldCostRaw(), pending.opinionDelta(), pending.preRecipientOpinion(),
                pending.preFactionPower(), pending.preFactionDiscontent(), receipt.original()));
    }
    private static boolean complete(PairPacket packet, PairRequest request) {
        PairObservation observation = packet.observation();
        return packet.step().filter(PAIR_STEP::equals).isPresent() && packet.accepted() == Truth.TRUE
                && packet.status().filter("independent_read_complete"::equals).isPresent()
                && packet.failureFlags().filter(BigInteger.ZERO::equals).isPresent()
                && observation.available() == Truth.TRUE && observation.paused() == Truth.TRUE
                && observation.snapshotRevision().filter(request.expectedRevision()::equals).isPresent()
                && observation.nativeSnapshotRevision().filter(request.expectedRevision()::equals).isPresent()
                && observation.observedDateRaw().filter(request.expectedDateRaw()::equals).isPresent()
                && observation.playerId().filter(request.expectedPlayerId()::equals).isPresent()
                && observation.factionRequeryComplete() == Truth.TRUE
                && observation.queriedFactionId().filter(request.sourceFactionId()::equals).isPresent()
                && observation.recipientIdentityResolved() == Truth.TRUE
                && observation.recipientId().filter(request.recipientId()::equals).isPresent()
                && observation.recipientOpinionQueryComplete() == Truth.TRUE && observation.recipientOpinion().isPresent()
                && observation.giftOpinionPresent() != Truth.UNKNOWN && observation.factionPresent() != Truth.UNKNOWN;
    }
    private static CurrentAlert alert(ExistingDriver driver, List<HistoryEntry> history, Snapshot before,
                                      BigInteger expectedRevision, BigInteger source) {
        Alert raw = null;
        for (int index = history.size() - 1; index >= 0; index--) {
            HistoryEntry row = history.get(index);
            if (row.ok() == Truth.TRUE && row.directAlert().filter(value -> value.sameFrame(before)).isPresent()) {
                raw = row.directAlert().orElseThrow(); break;
            }
        }
        if (raw == null) {
            AlertRead read = Objects.requireNonNull(driver.readCurrentAlert(expectedRevision));
            if (read instanceof AlertReadUnavailable error) return new AlertUnavailable(error.error());
            raw = ((AlertPacket) read).alert();
        }
        if (!raw.status().filter("available"::equals).isPresent() || !raw.sameFrame(before)
                || raw.sameFrameReady() != Truth.TRUE || raw.targetingRowsReady() != Truth.TRUE
                || raw.stockDangerousReady() != Truth.TRUE || raw.targetingRows().isEmpty()) {
            return new AlertUnavailable("current_alert_not_observed");
        }
        AlertRow match = null;
        for (AlertRow row : raw.targetingRows().orElseThrow()) {
            if (row.factionId().map(GiftPendingModel::rawSourceFactionIdFromPublic).filter(source::equals).isPresent()) {
                if (match != null) return new AlertUnavailable("current_alert_identity_ambiguous");
                match = row;
            }
        }
        return match == null ? new AlertAbsent() : new AlertObserved(match);
    }
    private static Unavailable unavailable(Request request, Snapshot frame, Optional<OriginalGift> original, Reason reason) {
        return new Unavailable(request, frame, original, reason, Optional.empty());
    }
}
