package org.xar.ck3.control.wave2.finance.giftpendingframe;

import java.math.BigInteger;
import java.time.Duration;
import java.util.Objects;
import java.util.function.Predicate;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingStatus;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;

/** Pure existing receipt-wait gate. Freshness proves only that the entire ordinary turn may be replanned. */
public final class GiftPendingFramePolicy {
    public static final Duration WAIT_TIMEOUT = Duration.ofSeconds(5);
    private GiftPendingFramePolicy() { }
    public record Frame(BigInteger publicRevision, BigInteger nativeRevision, BigInteger dateRaw,
            String episodeRunId, BigInteger actorCharacterId, boolean actorAlive, boolean paused, boolean mapReady,
            boolean activeEventAbsent, boolean pendingInteractionAbsent, BigInteger bridgePid, BigInteger connectionGeneration) {
        public Frame {
            GiftPendingModel.positive(publicRevision); GiftPendingModel.positive(nativeRevision); GiftPendingModel.nonnegative(dateRaw);
            GiftPendingModel.nonempty(episodeRunId); NativeCharacterId.of(actorCharacterId);
            GiftPendingModel.positive(bridgePid); GiftPendingModel.positive(connectionGeneration);
        }
        public boolean ready() { return actorAlive && paused && mapReady && activeEventAbsent && pendingInteractionAbsent; }
    }
    public record Proof(String pendingRequestId, PendingStatus pendingStatus, ProcessIdentity sourceProcess,
            BigInteger preNativeRevision, Frame sourceFrame, Frame freshFrame) {
        public Proof {
            GiftPendingModel.nonempty(pendingRequestId); Objects.requireNonNull(pendingStatus); Objects.requireNonNull(sourceProcess);
            GiftPendingModel.positive(preNativeRevision); Objects.requireNonNull(sourceFrame); Objects.requireNonNull(freshFrame);
            StrictJson.require(sourceFrame.ready() && freshFrame.ready() && sameOwner(sourceFrame, freshFrame)
                    && sourceFrame.bridgePid().equals(sourceProcess.pid())
                    && sourceFrame.nativeRevision().compareTo(preNativeRevision) <= 0
                    && freshFrame.nativeRevision().compareTo(preNativeRevision) > 0
                    && freshFrame.publicRevision().compareTo(sourceFrame.publicRevision()) > 0,
                    "pending paused frame proof does not qualify a read-only replan");
        }
        public boolean businessSubmissionAttempted() { return false; }
        public boolean receiptQueryAttempted() { return false; }
        public boolean giftSubmissionReplayed() { return false; }
    }
    /** Port to the original driver's existing bounded wait. Implementations must keep original ownership and read semantics. */
    @FunctionalInterface public interface ExistingSnapshotWaitPort {
        Frame await(Frame source, Predicate<Frame> changedOrReady, Duration timeout);
    }
    public static void requireWaitSource(PendingAction pending, Frame source) {
        var pre = pending.baseline();
        StrictJson.require(source.nativeRevision().compareTo(pre.nativeSnapshotRevision()) <= 0
                && source.dateRaw().equals(pre.dateRaw()) && source.episodeRunId().equals(pending.episodeRunId())
                && GiftPendingModel.rawCharacterIdFromPublic(source.actorCharacterId()).equals(pre.playerCharacterId()) && source.ready()
                && source.bridgePid().equals(pending.sourceProcess().pid()),
                "private faction pending frame changed before receipt");
    }
    public static boolean changedOrReady(PendingAction pending, Frame source, Frame current) {
        // Resource values may publish before revision; they are deliberately absent from this predicate.
        return current.nativeRevision().compareTo(pending.baseline().nativeSnapshotRevision()) > 0
                || !current.dateRaw().equals(pending.baseline().dateRaw())
                || !current.episodeRunId().equals(pending.episodeRunId())
                || !current.actorCharacterId().equals(source.actorCharacterId()) || current.actorAlive() != source.actorAlive()
                || !current.paused() || !current.mapReady() || !current.activeEventAbsent() || !current.pendingInteractionAbsent();
    }
    public static Proof acceptFresh(PendingAction pending, Frame source, Frame fresh) {
        requireWaitSource(pending, source);
        StrictJson.require(fresh.ready() && sameOwner(source, fresh)
                && fresh.nativeRevision().compareTo(pending.baseline().nativeSnapshotRevision()) > 0
                && fresh.publicRevision().compareTo(source.publicRevision()) > 0,
                "private faction pending same-date paused revision did not arrive");
        return new Proof(pending.requestId(), pending.status(), pending.sourceProcess(),
                pending.baseline().nativeSnapshotRevision(), source, fresh);
    }
    public static Proof awaitFresh(PendingAction pending, Frame source, ExistingSnapshotWaitPort existingWait) {
        requireWaitSource(pending, source); Objects.requireNonNull(existingWait);
        Frame fresh = existingWait.await(source, current -> changedOrReady(pending, source, current), WAIT_TIMEOUT);
        StrictJson.require(fresh != null, "existing native bounded wait returned no frame"); return acceptFresh(pending, source, fresh);
    }
    private static boolean sameOwner(Frame source, Frame fresh) {
        return source.actorCharacterId().equals(fresh.actorCharacterId()) && source.actorAlive() == fresh.actorAlive()
                && source.dateRaw().equals(fresh.dateRaw()) && source.episodeRunId().equals(fresh.episodeRunId())
                && source.bridgePid().equals(fresh.bridgePid()) && source.connectionGeneration().equals(fresh.connectionGeneration());
    }
}
