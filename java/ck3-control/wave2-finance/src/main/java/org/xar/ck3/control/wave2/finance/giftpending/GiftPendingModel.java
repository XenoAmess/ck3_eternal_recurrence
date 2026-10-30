package org.xar.ck3.control.wave2.finance.giftpending;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.NativeFactionId;

/** Immutable v1 material. No native submission, file access, or writer authority. */
public final class GiftPendingModel {
    public static final String SCHEMA = "xar.ck3.faction_gift_pending_v1";
    private GiftPendingModel() { }

    public enum PendingStatus {
        SUBMISSION_STARTED_UNCONFIRMED("submission_started_unconfirmed"),
        SUBMITTED_VERIFICATION_PENDING("submitted_verification_pending"),
        RESTORE_REQUERY_REQUIRED("restore_requery_required");
        private final String wire;
        PendingStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ResolvedOutcome {
        APPLIED("applied"), UNCHANGED("unchanged");
        private final String wire;
        ResolvedOutcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ReceiptStatus { MITIGATED, LEFT }

    /** Validated JSON object evidence, retained as immutable JSON text, including extensions. */
    public record ObjectEvidence(String json) {
        public ObjectEvidence {
            StrictJson.require(json != null, "object evidence required");
            StrictJson.require(StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8)).isObject(),
                    "object evidence must be JSON object");
        }
    }
    public record ProcessIdentity(BigInteger pid, String creationDate) {
        public ProcessIdentity { positive(pid); nonempty(creationDate); }
    }
    public record Baseline(BigInteger sourceFactionId, BigInteger recipientCharacterId,
            BigInteger snapshotRevision, BigInteger nativeSnapshotRevision, BigInteger dateRaw,
            BigInteger playerCharacterId, BigInteger playerGoldRaw, BigInteger recipientOpinionOfPlayer,
            BigInteger sourceFactionPowerRaw, BigInteger sourceFactionDiscontentRaw,
            List<BigInteger> sourceFactionMemberCharacterIds, BigInteger goldCostRaw, BigInteger opinionDelta) {
        public Baseline {
            rawSourceFactionId(sourceFactionId); rawCharacterId(recipientCharacterId); positive(snapshotRevision);
            positive(nativeSnapshotRevision); nonnegative(dateRaw); rawCharacterId(playerCharacterId);
            nonnegative(playerGoldRaw); Objects.requireNonNull(recipientOpinionOfPlayer);
            Objects.requireNonNull(sourceFactionPowerRaw); Objects.requireNonNull(sourceFactionDiscontentRaw);
            sourceFactionMemberCharacterIds = rawMemberCharacterIds(sourceFactionMemberCharacterIds);
            StrictJson.require(sourceFactionMemberCharacterIds.contains(recipientCharacterId), "recipient must be original member");
            positive(goldCostRaw); positive(opinionDelta);
        }
    }
    public record PendingAction(String requestId, String episodeRunId, String sourceRoundId,
            ProcessIdentity sourceProcess, Baseline baseline, BigInteger minimumGoldReserveRaw,
            String checkpointSha256BeforeSubmit, PendingStatus status, Optional<ObjectEvidence> ack) {
        public PendingAction {
            nonempty(requestId); nonempty(episodeRunId); round(sourceRoundId);
            Objects.requireNonNull(sourceProcess); Objects.requireNonNull(baseline);
            nonnegative(minimumGoldReserveRaw); digest(checkpointSha256BeforeSubmit);
            StrictJson.require(baseline.playerGoldRaw().subtract(baseline.goldCostRaw()).compareTo(minimumGoldReserveRaw) >= 0,
                    "faction gift pending action facts are incomplete: cash reserve");
            Objects.requireNonNull(status); Objects.requireNonNull(ack);
        }
        public PendingAction withState(PendingStatus next, Optional<ObjectEvidence> evidence) {
            return new PendingAction(requestId, episodeRunId, sourceRoundId, sourceProcess, baseline,
                    minimumGoldReserveRaw, checkpointSha256BeforeSubmit, next, evidence);
        }
    }
    public record Ledger(Optional<PendingAction> pending, Map<String, ResolvedOutcome> resolvedRequestOutcomes) {
        public Ledger {
            Objects.requireNonNull(pending); resolvedRequestOutcomes = Map.copyOf(resolvedRequestOutcomes);
            resolvedRequestOutcomes.forEach((request, outcome) -> { nonempty(request); Objects.requireNonNull(outcome); });
            if (pending.isPresent()) {
                StrictJson.require(!resolvedRequestOutcomes.containsKey(pending.orElseThrow().requestId()),
                        "pending request is already resolved");
            }
        }
        public static Ledger empty() { return new Ledger(Optional.empty(), Map.of()); }
        public boolean blocksNewSubmission() { return pending.isPresent(); }
    }
    public record BeginRequest(String requestId, String episodeRunId, String sourceRoundId,
            ProcessIdentity sourceProcess, Baseline observation, BigInteger minimumGoldReserveRaw,
            String checkpointSha256BeforeSubmit) {
        public BeginRequest {
            // The same constructor is used before any durable replacement by the original writer.
            new PendingAction(requestId, episodeRunId, sourceRoundId, sourceProcess, observation,
                    minimumGoldReserveRaw, checkpointSha256BeforeSubmit,
                    PendingStatus.SUBMISSION_STARTED_UNCONFIRMED, Optional.empty());
        }
    }
    public record Ack(String requestId, BigInteger sourceFactionId, BigInteger recipientCharacterId,
            ObjectEvidence evidence) {
        public Ack { nonempty(requestId); rawSourceFactionId(sourceFactionId); rawCharacterId(recipientCharacterId); Objects.requireNonNull(evidence); }
    }
    /** Same-process material projection; extension fields remain in the original receipt evidence. */
    public record AppliedReceipt(String requestId, ReceiptStatus status, BigInteger sourceFactionId,
            BigInteger recipientCharacterId, BigInteger playerCharacterId, BigInteger postSnapshotRevision,
            BigInteger postNativeSnapshotRevision, BigInteger postObservedDateRaw,
            BigInteger postPlayerGoldRaw, BigInteger postGiftOpinionModifierValue, ObjectEvidence evidence) {
        public AppliedReceipt {
            nonempty(requestId); Objects.requireNonNull(status); rawSourceFactionId(sourceFactionId);
            rawCharacterId(recipientCharacterId); rawCharacterId(playerCharacterId); positive(postSnapshotRevision);
            positive(postNativeSnapshotRevision); nonnegative(postObservedDateRaw); nonnegative(postPlayerGoldRaw);
            Objects.requireNonNull(postGiftOpinionModifierValue); Objects.requireNonNull(evidence);
        }
    }
    public static void nonempty(String value) { StrictJson.text(value); }
    /** Private gift JSON uses raw uint32 FullIDs, with all-ones reserved for absence. */
    public static BigInteger rawCharacterId(BigInteger value) {
        return NativeCharacterId.fromRawUInt32(value).asRawUInt32();
    }
    /** Explicit one-way boundary from the public signed int32 frame; no dual-domain input alias. */
    public static BigInteger rawCharacterIdFromPublic(BigInteger signedValue) {
        return NativeCharacterId.of(signedValue).asRawUInt32();
    }
    public static BigInteger rawSourceFactionId(BigInteger value) {
        return NativeFactionId.fromRawUInt32(value).asRawUInt32();
    }
    /** Explicit public FactionID to private raw32 boundary, distinct from character and title roles. */
    public static BigInteger rawSourceFactionIdFromPublic(BigInteger signedValue) {
        return NativeFactionId.of(signedValue).asRawUInt32();
    }
    public static List<BigInteger> rawMemberCharacterIds(List<BigInteger> values) {
        List<BigInteger> retained = List.copyOf(values);
        BigInteger previous = null;
        for (BigInteger value : retained) {
            rawCharacterId(value);
            StrictJson.require(previous == null || previous.compareTo(value) < 0,
                    "private Gift member identities must be strictly increasing in raw uint32 order");
            previous = value;
        }
        return retained;
    }
    public static void positive(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0, "positive integer required");
    }
    public static void nonnegative(BigInteger value) {
        StrictJson.require(value != null && value.signum() >= 0, "nonnegative integer required");
    }
    public static void round(String value) {
        nonempty(value); StrictJson.require(value.matches("R[\\p{IsDigit}]+"), "round identity required");
    }
    public static void digest(String value) {
        StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase SHA-256 required");
    }
}
