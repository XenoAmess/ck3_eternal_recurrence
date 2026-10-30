package org.xar.ck3.control.wave2.finance.factioncandidate;

import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.contracts.NativeCharacterId;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Pure formal-root and private-preview join, using the existing Java gift decision implementation. */
public final class FactionCandidatePolicy {
    public static final String ROOT_STEP = "query-campaign-root-context-v1";
    public static final String PRIVATE_STEP = "private-query-faction-gift-member-v1";
    public static final int MAX_HISTORY = 256;
    public static final int MAX_IDS = 256;

    private FactionCandidatePolicy() { }

    public enum RootStatus {
        FRAME_UNAVAILABLE("frame_unavailable"), SAME_FRAME_ROOT_NOT_OBSERVED("same_frame_root_not_observed"),
        GOVERNMENT_OUT_OF_SCOPE("government_out_of_scope"), ROOT_FACTION_FACTS_UNKNOWN("root_faction_facts_unknown"),
        KNOWN_EMPTY("known_empty"), TARGETING_PRESENT("targeting_present");
        private final String wire;
        RootStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum RejectionReason {
        NONEMPTY_TARGETING_VECTOR_UNPROVEN("nonempty_targeting_vector_unproven"),
        PRIVATE_QUERY_ENVELOPE_UNKNOWN("private_query_envelope_unknown"),
        NO_DIRECT_LANDED_MEMBER("no_direct_landed_member"),
        NATIVE_PREVIEW_NOT_TERMINAL("native_preview_not_terminal"),
        NATIVE_PREVIEW_RECEIVER_RED("native_preview_receiver_red"),
        NATIVE_OBSERVATION_MISSING("native_observation_missing"),
        ROOT_PRIVATE_MEMBER_OR_FRAME_MISMATCH("root_private_member_or_frame_mismatch");
        private final String wire;
        RejectionReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum PreviewStatus { PREVIEW_READY, NO_LEGAL_CANDIDATE, NO_ELIGIBLE_DIRECT_VASSAL, OTHER }

    /** Exact native CharacterID projection: preserve signed32 values without narrowing or unsigned aliases. */
    public record Frame(BigInteger nativeRevision, BigInteger dateRaw, BigInteger actorId) {
        public Frame {
            positive(nativeRevision, "nativeRevision");
            Objects.requireNonNull(dateRaw, "dateRaw");
            NativeCharacterId.of(actorId);
        }
    }

    public static final class JsonObjectDocument {
        private final byte[] json;
        JsonObjectDocument(byte[] json) { this.json = json.clone(); }
        public byte[] json() { return json.clone(); }
    }

    public record IdVector(Optional<List<BigInteger>> known) {
        public IdVector {
            Objects.requireNonNull(known, "known");
            known = known.map(List::copyOf);
            if (known.isPresent()) {
                List<BigInteger> ids = known.get();
                if (ids.size() > MAX_IDS) {
                    throw new IllegalArgumentException("identity vector must be bounded");
                }
                ids.forEach(NativeCharacterId::of);
            }
        }
    }

    public record RootProjection(JsonObjectDocument original, Optional<Frame> frame,
                                  boolean statusAvailable, boolean playerAlive,
                                  Optional<String> governmentKey, Optional<BigInteger> targetingCount,
                                  IdVector directLandedVassals) {
        public RootProjection {
            Objects.requireNonNull(original, "original");
            Objects.requireNonNull(frame, "frame");
            Objects.requireNonNull(governmentKey, "governmentKey");
            Objects.requireNonNull(targetingCount, "targetingCount");
            Objects.requireNonNull(directLandedVassals, "directLandedVassals");
        }
    }

    public record RootHistory(boolean eligibleResult, RootProjection context) {
        public RootHistory { Objects.requireNonNull(context, "context"); }
    }

    public record RootSearch(Optional<Frame> qualifiedSnapshot, List<RootHistory> histories) {
        public RootSearch {
            Objects.requireNonNull(qualifiedSnapshot, "qualifiedSnapshot");
            histories = List.copyOf(histories);
            if (histories.size() > MAX_HISTORY) throw new IllegalArgumentException("history limit");
        }
    }

    public record RootView(RootStatus status, Optional<RootProjection> root) {
        public RootView {
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(root, "root");
            boolean requiresRoot = status != RootStatus.FRAME_UNAVAILABLE && status != RootStatus.SAME_FRAME_ROOT_NOT_OBSERVED;
            if (requiresRoot != root.isPresent()) throw new IllegalArgumentException("root status/document mismatch");
        }
    }

    public record Observation(JsonObjectDocument original, Optional<Frame> frame,
                               Optional<BigInteger> recipientId, Optional<BigInteger> sourceFactionId) {
        public Observation {
            Objects.requireNonNull(original, "original");
            Objects.requireNonNull(frame, "frame");
            Objects.requireNonNull(recipientId, "recipientId");
            recipientId.ifPresent(NativeCharacterId::of);
            Objects.requireNonNull(sourceFactionId, "sourceFactionId");
        }
    }

    public record PrivatePreview(boolean acceptedEnvelope, PreviewStatus status, boolean hasNativeObject,
                                  boolean receiverReady, Optional<BigInteger> nativeSourceId,
                                  Optional<BigInteger> nativeRecipientId, Optional<Observation> observation) {
        public PrivatePreview {
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(nativeSourceId, "nativeSourceId");
            Objects.requireNonNull(nativeRecipientId, "nativeRecipientId");
            nativeRecipientId.ifPresent(NativeCharacterId::of);
            Objects.requireNonNull(observation, "observation");
        }
    }

    public record CandidateInput(Optional<Frame> snapshot, RootProjection root, PrivatePreview preview,
                                  Optional<BigInteger> minimumGoldReserveRaw) {
        public CandidateInput {
            Objects.requireNonNull(snapshot, "snapshot");
            Objects.requireNonNull(root, "root");
            Objects.requireNonNull(preview, "preview");
            Objects.requireNonNull(minimumGoldReserveRaw, "minimumGoldReserveRaw");
        }
    }

    public sealed interface CandidateResult permits Rejected, Evaluated { }
    public interface GiftDecisionPort {
        FactionGiftChoice choose(JsonObjectDocument observation, BigInteger minimumGoldReserveRaw);
    }
    public record Rejected(RejectionReason reason) implements CandidateResult {
        public Rejected { Objects.requireNonNull(reason, "reason"); }
    }
    public record Evaluated(FactionGiftChoice choice, Observation observation,
                             Optional<BigInteger> minimumGoldReserveRaw) implements CandidateResult {
        public Evaluated {
            Objects.requireNonNull(choice, "choice");
            Objects.requireNonNull(observation, "observation");
            Objects.requireNonNull(minimumGoldReserveRaw, "minimumGoldReserveRaw");
            if (choice instanceof FactionGiftChoice.Selected
                    && (minimumGoldReserveRaw.isEmpty() || minimumGoldReserveRaw.get().signum() < 0)) {
                throw new IllegalArgumentException("selected gift lacks valid reserve");
            }
        }
    }

    public static RootView latestSameFrameRoot(RootSearch input) {
        Objects.requireNonNull(input, "input");
        if (input.qualifiedSnapshot().isEmpty()) return new RootView(RootStatus.FRAME_UNAVAILABLE, Optional.empty());
        Frame snapshot = input.qualifiedSnapshot().get();
        for (int index = input.histories().size() - 1; index >= 0; index--) {
            RootHistory history = input.histories().get(index);
            RootProjection root = history.context();
            if (!history.eligibleResult() || !root.statusAvailable() || !root.playerAlive()
                    || root.frame().filter(snapshot::equals).isEmpty()) continue;
            if (root.governmentKey().filter("feudal_government"::equals).isEmpty()) {
                return new RootView(RootStatus.GOVERNMENT_OUT_OF_SCOPE, Optional.of(root));
            }
            if (root.targetingCount().isEmpty() || root.targetingCount().get().signum() < 0
                    || root.directLandedVassals().known().isEmpty()
                    || root.directLandedVassals().known().get().stream().distinct().count()
                    != root.directLandedVassals().known().get().size()) {
                return new RootView(RootStatus.ROOT_FACTION_FACTS_UNKNOWN, Optional.of(root));
            }
            return new RootView(root.targetingCount().get().signum() == 0
                    ? RootStatus.KNOWN_EMPTY : RootStatus.TARGETING_PRESENT, Optional.of(root));
        }
        return new RootView(RootStatus.SAME_FRAME_ROOT_NOT_OBSERVED, Optional.empty());
    }

    public static CandidateResult choosePrivateCandidate(CandidateInput input, GiftDecisionPort giftDecision) {
        Objects.requireNonNull(input, "input");
        Objects.requireNonNull(giftDecision, "giftDecision");
        if (input.root().targetingCount().isEmpty() || input.root().targetingCount().get().signum() <= 0) {
            return new Rejected(RejectionReason.NONEMPTY_TARGETING_VECTOR_UNPROVEN);
        }
        PrivatePreview preview = input.preview();
        if (!preview.acceptedEnvelope()) return new Rejected(RejectionReason.PRIVATE_QUERY_ENVELOPE_UNKNOWN);
        if (preview.status() == PreviewStatus.NO_ELIGIBLE_DIRECT_VASSAL) return new Rejected(RejectionReason.NO_DIRECT_LANDED_MEMBER);
        if ((preview.status() != PreviewStatus.PREVIEW_READY && preview.status() != PreviewStatus.NO_LEGAL_CANDIDATE)
                || !preview.hasNativeObject()) return new Rejected(RejectionReason.NATIVE_PREVIEW_NOT_TERMINAL);
        if (!preview.receiverReady()) return new Rejected(RejectionReason.NATIVE_PREVIEW_RECEIVER_RED);
        if (preview.observation().isEmpty()) return new Rejected(RejectionReason.NATIVE_OBSERVATION_MISSING);
        Observation observation = preview.observation().get();
        if (observation.recipientId().isEmpty() || observation.sourceFactionId().isEmpty()
                || input.root().directLandedVassals().known().isEmpty()
                || !input.root().directLandedVassals().known().get().contains(observation.recipientId().get())
                || !preview.nativeSourceId().equals(observation.sourceFactionId())
                || !preview.nativeRecipientId().equals(observation.recipientId())
                || input.snapshot().isEmpty() || !input.snapshot().equals(observation.frame())
                || !input.snapshot().equals(input.root().frame())) {
            return new Rejected(RejectionReason.ROOT_PRIVATE_MEMBER_OR_FRAME_MISMATCH);
        }
        FactionGiftChoice choice = input.minimumGoldReserveRaw().isEmpty()
                ? new FactionGiftChoice.Declined(FactionGiftChoice.Reason.ENUMERATION_OR_RESERVE_UNPROVEN)
                : Objects.requireNonNull(giftDecision.choose(observation.original(), input.minimumGoldReserveRaw().get()), "gift decision");
        return new Evaluated(choice, observation, input.minimumGoldReserveRaw());
    }

    private static void positive(BigInteger value, String field) {
        if (Objects.requireNonNull(value, field).signum() <= 0) throw new IllegalArgumentException(field + " must be positive");
    }
}
