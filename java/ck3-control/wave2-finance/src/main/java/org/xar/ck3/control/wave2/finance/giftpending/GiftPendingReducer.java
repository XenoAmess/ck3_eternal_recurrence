package org.xar.ck3.control.wave2.finance.giftpending;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ack;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.AppliedReceipt;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Baseline;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.BeginRequest;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingStatus;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ResolvedOutcome;

/** Pure replacement candidates. Only the existing authoritative writer may persist them. */
public final class GiftPendingReducer {
    private GiftPendingReducer() { }
    public static Ledger begin(Ledger ledger, BeginRequest input) {
        StrictJson.require(!ledger.blocksNewSubmission(), "one faction gift is already unresolved");
        StrictJson.require(!ledger.resolvedRequestOutcomes().containsKey(input.requestId()),
                "faction gift request identity is missing or already resolved");
        return new Ledger(Optional.of(new PendingAction(input.requestId(), input.episodeRunId(), input.sourceRoundId(),
                input.sourceProcess(), input.observation(), input.minimumGoldReserveRaw(), input.checkpointSha256BeforeSubmit(),
                PendingStatus.SUBMISSION_STARTED_UNCONFIRMED, Optional.empty())), ledger.resolvedRequestOutcomes());
    }
    public static Ledger markAck(Ledger ledger, String requestId, Ack ack) {
        PendingAction pending = matching(ledger, requestId); Baseline pre = pending.baseline();
        StrictJson.require(ack.requestId().equals(requestId) && ack.sourceFactionId().equals(pre.sourceFactionId())
                && ack.recipientCharacterId().equals(pre.recipientCharacterId()), "faction gift ACK is not a matching pending submission");
        return new Ledger(Optional.of(pending.withState(PendingStatus.SUBMITTED_VERIFICATION_PENDING,
                Optional.of(ack.evidence()))), ledger.resolvedRequestOutcomes());
    }
    public static Ledger markRestore(Ledger ledger, String requestId) {
        PendingAction pending = matching(ledger, requestId);
        return new Ledger(Optional.of(pending.withState(PendingStatus.RESTORE_REQUERY_REQUIRED, pending.ack())),
                ledger.resolvedRequestOutcomes());
    }
    public static Ledger complete(Ledger ledger, String requestId, AppliedReceipt receipt) {
        PendingAction pending = matching(ledger, requestId); Baseline pre = pending.baseline();
        verifyReceipt(pre, requestId, receipt);
        return retire(ledger, requestId, ResolvedOutcome.APPLIED);
    }
    /** Pure terminal candidate only. The original domain producer must independently verify its canonical zero-byte dispatch proof. */
    public static Ledger rejectBeforeDispatch(Ledger ledger,String requestId) {
        return retire(ledger,requestId,ResolvedOutcome.UNCHANGED);
    }
    /** The original same-process material rule, shared by the durable reducer and the application effect observer. */
    public static void verifyReceipt(Baseline pre, String requestId, AppliedReceipt receipt) {
        java.util.Objects.requireNonNull(pre); GiftPendingModel.nonempty(requestId); java.util.Objects.requireNonNull(receipt);
        StrictJson.require(receipt.requestId().equals(requestId)
                && receipt.sourceFactionId().equals(pre.sourceFactionId())
                && receipt.recipientCharacterId().equals(pre.recipientCharacterId())
                && receipt.playerCharacterId().equals(pre.playerCharacterId())
                && receipt.postSnapshotRevision().compareTo(pre.snapshotRevision()) > 0
                && receipt.postNativeSnapshotRevision().compareTo(pre.nativeSnapshotRevision()) > 0
                && receipt.postObservedDateRaw().equals(pre.dateRaw())
                && receipt.postPlayerGoldRaw().equals(pre.playerGoldRaw().subtract(pre.goldCostRaw()))
                && receipt.postGiftOpinionModifierValue().equals(pre.opinionDelta()),
                "faction gift receipt lacks matching independent post-state");
    }
    static Ledger retire(Ledger ledger, String requestId, ResolvedOutcome outcome) {
        matching(ledger, requestId); Map<String, ResolvedOutcome> resolved = new HashMap<>(ledger.resolvedRequestOutcomes());
        resolved.put(requestId, outcome); return new Ledger(Optional.empty(), resolved);
    }
    public static PendingAction matching(Ledger ledger, String requestId) {
        GiftPendingModel.nonempty(requestId);
        StrictJson.require(ledger.pending().isPresent() && ledger.pending().orElseThrow().requestId().equals(requestId),
                "faction gift receipt has no matching unresolved action");
        return ledger.pending().orElseThrow();
    }
}

