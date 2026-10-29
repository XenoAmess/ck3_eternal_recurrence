package org.xar.ck3.control.runtime.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Shared wire description of originals retained by the actual Root writer. Encoding, decoding or
 * matching this record does not establish custody, engine cause, a native effect or an episode.
 * RootOriginals.openQualified and requireCurrent remain mandatory under the actual writer lease.
 */
public record NaturalEngineClockProof(String machineId, Instant observedAtUtc, String writerHeadSha256, ActionReceipt.Outcome clockOutcome,
        boolean replayAuthorized, ExactRef originalDomain, ExactRef clockReceipt, ExactRef clockCommand,
        ExactRef predecessorRoot, ExactRef actualFinalPacket, Optional<ExactRef> completeSourceQualification) {
    public static final String SCHEMA = "xar.java.natural-engine-clock-actor-originals/v2";
    public static final int MAX_BYTES = 65_536;
    private static final Set<String> FIELDS = Set.of("schema", "machine_id", "observed_at_utc", "writer_head_sha256", "clock_outcome",
            "replay_authorized", "original_domain", "clock_receipt", "clock_command", "predecessor_root",
            "actual_final_packet");

    public NaturalEngineClockProof {
        StrictJson.text(machineId); Objects.requireNonNull(observedAtUtc);
        StrictJson.require(writerHeadSha256 != null && writerHeadSha256.matches("[0-9a-f]{64}"),
                "actual writer-head SHA256 required");
        Objects.requireNonNull(clockOutcome);
        // Match the actual Root originalClock producer. UNKNOWN still needs independently retained
        // native poststate/cause and must never become permission to resubmit the clock.
        StrictJson.require(clockOutcome != ActionReceipt.Outcome.REJECTED_CONFIRMED
                && clockOutcome != ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH,
                "definitely rejected clock cannot establish an engine transition");
        StrictJson.require(!replayAuthorized, "natural clock proof never authorizes replay");
        for (ExactRef original : List.of(Objects.requireNonNull(originalDomain), Objects.requireNonNull(clockReceipt),
                Objects.requireNonNull(clockCommand), Objects.requireNonNull(predecessorRoot),
                Objects.requireNonNull(actualFinalPacket))) {
            StrictJson.require(original.bytes() > 0, "nonempty exact original reference required");
        }
        Objects.requireNonNull(completeSourceQualification);
        completeSourceQualification.ifPresent(ref -> StrictJson.require(ref.bytes() > 0, "nonempty exact source qualification required"));
    }

    public NaturalEngineClockProof(String machineId, Instant observedAtUtc, String writerHeadSha256, ActionReceipt.Outcome clockOutcome,
            boolean replayAuthorized, ExactRef originalDomain, ExactRef clockReceipt, ExactRef clockCommand,
            ExactRef predecessorRoot, ExactRef actualFinalPacket, ExactRef completeSourceQualification) {
        this(machineId, observedAtUtc, writerHeadSha256, clockOutcome, replayAuthorized, originalDomain, clockReceipt, clockCommand,
                predecessorRoot, actualFinalPacket, Optional.of(completeSourceQualification));
    }

    public static byte[] encode(NaturalEngineClockProof proof) {
        Objects.requireNonNull(proof);
        ObjectNode row = StrictJson.object().put("schema", SCHEMA)
                .put("machine_id", proof.machineId()).put("observed_at_utc", proof.observedAtUtc().toString())
                .put("writer_head_sha256", proof.writerHeadSha256())
                .put("clock_outcome", proof.clockOutcome().name())
                .put("replay_authorized", proof.replayAuthorized());
        row.set("original_domain", proof.originalDomain().toJson());
        row.set("clock_receipt", proof.clockReceipt().toJson());
        row.set("clock_command", proof.clockCommand().toJson());
        row.set("predecessor_root", proof.predecessorRoot().toJson());
        row.set("actual_final_packet", proof.actualFinalPacket().toJson());
        row.set("complete_source_qualification", ExactRef.optionalToJson(proof.completeSourceQualification()));
        return StrictJson.canonical(row, MAX_BYTES);
    }

    public static NaturalEngineClockProof decode(byte[] original) {
        ObjectNode row = StrictJson.object(StrictJson.parse(original, MAX_BYTES), FIELDS, Set.of("complete_source_qualification"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "actual natural clock proof schema required");
        JsonNode replay = row.get("replay_authorized");
        StrictJson.require(replay.isBoolean(), "actual JSON replay boolean required");
        return new NaturalEngineClockProof(StrictJson.text(row.get("machine_id")),
                instant(row.get("observed_at_utc")),
                StrictJson.text(row.get("writer_head_sha256")),
                ActionReceipt.Outcome.valueOf(StrictJson.text(row.get("clock_outcome"))), replay.booleanValue(),
                ExactRef.fromJson(row.get("original_domain")), ExactRef.fromJson(row.get("clock_receipt")),
                ExactRef.fromJson(row.get("clock_command")), ExactRef.fromJson(row.get("predecessor_root")),
                ExactRef.fromJson(row.get("actual_final_packet")), ExactRef.optionalFromJson(row.get("complete_source_qualification")));
    }

    private static Instant instant(JsonNode value) {
        String text = StrictJson.utc(StrictJson.text(value));
        try { return Instant.parse(text); }
        catch (java.time.format.DateTimeParseException failure) {
            throw new IllegalArgumentException("ISO UTC instant required", failure);
        }
    }

    /** Compares already held originals only; this does not replace actual writer/source revalidation. */
    public void requireBoundTo(String actualMachineId, Instant actualObservedAtUtc, String actualWriterHead, ExactRef actualPredecessorRoot, ExactRef actualPacket) {
        StrictJson.require(machineId.equals(actualMachineId) && observedAtUtc.equals(actualObservedAtUtc)
                && writerHeadSha256.equals(actualWriterHead)
                && predecessorRoot.equals(actualPredecessorRoot) && actualFinalPacket.equals(actualPacket),
                "natural clock proof crossed the actual machine/frame observation time, held writer, predecessor root or actual final packet");
    }
}
