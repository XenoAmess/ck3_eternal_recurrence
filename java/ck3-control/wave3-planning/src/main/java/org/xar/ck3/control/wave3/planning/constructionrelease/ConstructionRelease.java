package org.xar.ck3.control.wave3.planning.constructionrelease;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Frame;
import org.xar.ck3.control.wave2.runtime.creationtime.ProcessCreationTime;

/** Exact old-receipt release predicate for new M5 construction candidates, never an action acknowledgement. */
public final class ConstructionRelease {
    private ConstructionRelease() { }
    public enum AppliedStatus { APPLIED, OTHER, MISSING, NULL }
    public enum Flag { TRUE, FALSE, MISSING, NULL }
    public sealed interface PriorReceipt permits NoReceipt, Receipt { }
    public enum NoReceipt implements PriorReceipt { INSTANCE }
    public record Details(AppliedStatus status, Flag postconditionVerified, Optional<BigInteger> actorCharacterId,
                          Optional<BigInteger> postBridgePid, Optional<String> originalPostCreationDate,
                          Optional<BigInteger> postNativeRevision, Optional<BigInteger> postDateRaw) {
        public Details {
            Objects.requireNonNull(status); Objects.requireNonNull(postconditionVerified); Objects.requireNonNull(actorCharacterId);
            Objects.requireNonNull(postBridgePid); Objects.requireNonNull(originalPostCreationDate);
            Objects.requireNonNull(postNativeRevision); Objects.requireNonNull(postDateRaw);
        }
    }
    /** Details are required only for the current episode; foreign receipt content remains unused. */
    public record Receipt(Optional<String> episodeRunId, Optional<Details> details) implements PriorReceipt {
        public Receipt { Objects.requireNonNull(episodeRunId); Objects.requireNonNull(details); }
    }
    /** Raw, observed PID/birth spelling. This is not measured process proof or a live-process qualification. */
    public record ProcessIdentity(BigInteger pid, String originalCreationDate) {
        public ProcessIdentity {
            if (pid == null || pid.signum() <= 0) { throw new IllegalArgumentException("positive exact process PID required"); }
            if (originalCreationDate == null || originalCreationDate.isEmpty() || originalCreationDate.length() > 32768) {
                throw new IllegalArgumentException("bounded original process birth spelling required");
            }
        }
    }
    public sealed interface ProcessObservation permits ObservedIdentity, IdentityUnavailable, IdentityUnused { }
    public record ObservedIdentity(ProcessIdentity identity) implements ProcessObservation { public ObservedIdentity { Objects.requireNonNull(identity); } }
    public enum IdentityUnavailable implements ProcessObservation { INSTANCE }
    public enum IdentityUnused implements ProcessObservation { INSTANCE }
    @FunctionalInterface public interface ProcessIdentityReader { ProcessObservation observe(); }
    public enum Status { NO_CURRENT_EPISODE_RECEIPT, HELD, RELEASED }
    public enum Reason {
        no_same_episode_receipt, process_observation_unavailable, status_not_applied, postcondition_unverified,
        actor_mismatch, process_mismatch, post_frame_unavailable, native_frame_not_later, date_not_later, released_later_frame
    }
    public record Decision(Status status, Reason reason) {
        public Decision { Objects.requireNonNull(status); Objects.requireNonNull(reason); }
        public boolean blocksCandidate() { return status == Status.HELD; }
        public boolean formalActionReady() { return false; }
    }

    public static Decision assess(Frame current, PriorReceipt prior, ProcessObservation process) {
        Objects.requireNonNull(current); Objects.requireNonNull(prior); Objects.requireNonNull(process);
        if (!sameEpisode(current, prior)) { return new Decision(Status.NO_CURRENT_EPISODE_RECEIPT, Reason.no_same_episode_receipt); }
        if (!(process instanceof ObservedIdentity observed)) { return held(Reason.process_observation_unavailable); }
        Details details = ((Receipt) prior).details.orElseThrow(() -> new IllegalArgumentException("matching episode requires declared receipt details"));
        if (details.status != AppliedStatus.APPLIED) { return held(Reason.status_not_applied); }
        if (details.postconditionVerified != Flag.TRUE) { return held(Reason.postcondition_unverified); }
        if (details.actorCharacterId.isEmpty() || !details.actorCharacterId.orElseThrow().equals(current.player())) { return held(Reason.actor_mismatch); }
        if (details.postBridgePid.isEmpty() || details.originalPostCreationDate.isEmpty()
                || !observed.identity.pid.equals(details.postBridgePid.orElseThrow())
                || !sameOriginalBirth(observed.identity.originalCreationDate, details.originalPostCreationDate.orElseThrow())) {
            return held(Reason.process_mismatch);
        }
        if (details.postNativeRevision.isEmpty() || details.postDateRaw.isEmpty()) { return held(Reason.post_frame_unavailable); }
        if (current.nativeRevision().compareTo(details.postNativeRevision.orElseThrow()) <= 0) { return held(Reason.native_frame_not_later); }
        if (current.dateRaw().compareTo(details.postDateRaw.orElseThrow()) <= 0) { return held(Reason.date_not_later); }
        return new Decision(Status.RELEASED, Reason.released_later_frame);
    }

    /** Preserve the original early return and reader-before-receipt-check order within the current episode. */
    public static Decision assessFromReader(Frame current, PriorReceipt prior, Optional<ProcessIdentityReader> reader) {
        Objects.requireNonNull(reader);
        if (!sameEpisode(current, prior)) { return new Decision(Status.NO_CURRENT_EPISODE_RECEIPT, Reason.no_same_episode_receipt); }
        ProcessObservation process = reader.isEmpty() ? IdentityUnavailable.INSTANCE : reader.orElseThrow().observe();
        return assess(current, prior, process == null ? IdentityUnavailable.INSTANCE : process);
    }
    public static boolean sameEpisode(Frame current, PriorReceipt prior) {
        Objects.requireNonNull(current); Objects.requireNonNull(prior);
        return prior instanceof Receipt receipt && receipt.episodeRunId.isPresent()
                && receipt.episodeRunId.orElseThrow().equals(current.episodeRunId());
    }
    private static boolean sameOriginalBirth(String first, String second) {
        // Exact spelling equality is part of the original receipt ABI, including opaque historical fixture spellings.
        return first.equals(second) || ProcessCreationTime.same(first, second);
    }
    private static Decision held(Reason reason) { return new Decision(Status.HELD, reason); }
}
