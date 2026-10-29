package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;
import org.xar.ck3.control.wave2.runtime.savedproof.RetainedClosedMeasurement;

/** Actual new-basis consumer. It grants closed saved inputs only, never a warm attachment or Game action. */
public final class ClosedColdInputsConsumer {
    public static final String QUALIFICATION_SCHEMA = "xar.java-closed-partial-cold-inputs-qualification/v1";
    public static final String INPUTS_SCHEMA = "xar.java-closed-partial-cold-inputs/v1";
    public static final String SCOPE = "CLOSED_SAVED_INPUTS_ONLY_NEW_WARM_ATTACHMENT_REQUIRED";
    public static final String RETAINED_SCOPE = "RETAINED_CLOSED_SAVED_INPUTS_FOR_RESTORE_VALIDATION_ONLY";
    private ClosedColdInputsConsumer() { }
    @FunctionalInterface public interface CanonicalReceiptSource {
        /** Existing coordinator's requireCurrentCached().canonicalReceipt(); no second measurement. */
        RecoveryEvidence current();
    }
    public static final class Prepared {
        private final byte[] basis;
        private final OriginalWriterTransaction.Evaluation evaluation;
        private final OriginalWriterTransaction.Committed committed;
        private final RecoveryEvidence canonical;
        private Prepared(byte[] basis, OriginalWriterTransaction.Evaluation evaluation,
                OriginalWriterTransaction.Committed committed, RecoveryEvidence canonical) {
            this.basis = basis.clone(); this.evaluation = evaluation; this.committed = committed; this.canonical = canonical;
        }
        public byte[] basisBytes() { return basis.clone(); }
        public byte[] qualificationBytes(ExactRef publishedBasisRef) {
            StrictJson.require(publishedBasisRef.bytes() == basis.length
                    && publishedBasisRef.sha256().equals(RecoveryEvidence.sha256(basis)), "actual published basis bytes");
            return StrictJson.canonical(qualification(this, publishedBasisRef), StrictJson.OUTPUT_MAX_BYTES);
        }
    }
    public record Qualified(byte[] wireBytes) {
        public Qualified { wireBytes = wireBytes.clone(); }
        @Override public byte[] wireBytes() { return wireBytes.clone(); }
        public boolean grantsWarmAttachment() { return false; }
        public long gameDayCredit() { return 0; }
    }
    public static Prepared prepare(ClosedAdoptionMaterial.CurrentSource current, OriginalWriterTransaction.Committed committed,
            CanonicalReceiptSource canonicalSource) {
        OriginalWriterTransaction.Evaluation evaluation = OriginalWriterTransaction.evaluate(current.current());
        StrictJson.require(committed.inputDigest().equals(evaluation.candidate().inputDigest())
                && committed.businessDigest().equals(evaluation.businessDigest()) && committed.processExit().kernelExitObserved()
                && committed.processExit().exitCode() == 0, "actual original writer terminal and same current prerequisite authority");
        OriginalWriterTransaction.validateReadback(committed.target(), evaluation, committed.head(), committed.event(), committed.index());
        for (ExactRef reference : java.util.List.of(committed.head().evidence().reference(), committed.event().evidence().reference(), committed.index().evidence().reference())) {
            evaluation.material().sourceVerifier().verify(reference);
        }
        RecoveryPrerequisiteVerifier.Verified proof = evaluation.prerequisites(); RecoveryEvidence canonical = canonicalSource.current();
        StrictJson.require(canonical.reference().equals(proof.canonicalCheckpointProof()), "same actually measured SDK receipt, not a shape-only replacement");
        evaluation.material().sourceVerifier().verify(canonical.reference());
        ObjectNode canonicalValue = object(canonical); equal(canonicalValue, "machine_id", evaluation.material().input().machineId());
        StrictJson.text(canonicalValue.get("pipe_name"));
        ObjectNode basis = object(evaluation.material().input().savedBasis()); ObjectNode refs = node(basis.get("refs"));
        refs.set("driver", proof.driver().toJson()); refs.set("save", proof.save().toJson());
        refs.set("checkpoint_validator", proof.validatorSource().toJson()); refs.set("driver_close", canonical.reference().toJson());
        refs.set("closure", evaluation.material().publishedEpoch().reference().toJson());
        refs.set("next", evaluation.material().input().actualNext().reference().toJson());
        refs.set("ledger", committed.head().evidence().reference().toJson());
        basis.set("driver_identity", proof.driverIdentity().toJson()); basis.set("save_identity", proof.saveIdentity().toJson());
        basis.put("next_sequence", proof.unknownSequence() + 1);
        JsonNode unknownValue = basis.get("unknown_requests"); StrictJson.require(unknownValue instanceof ArrayNode, "explicit unknown history array");
        ArrayNode unknown = (ArrayNode) unknownValue;
        Set<Long> sequences = new java.util.HashSet<>();
        for (JsonNode entry : unknown) { StrictJson.require(sequences.add(number(node(entry), "sequence", 1)), "unique original unknown sequence"); }
        StrictJson.require(sequences.add(proof.unknownSequence()) && unknown.size() < 64, "new UNKNOWN retained exactly once");
        ObjectNode failure = unknown.addObject(); failure.put("sequence", proof.unknownSequence());
        failure.set("evidence_ref", evaluation.material().input().failedAuto().reference().toJson()); failure.put("status", "unknown");
        failure.put("replayed", false); failure.put("cycle_credit", 0); failure.put("day_credit", 0);
        validateBasis(basis, evaluation);
        return new Prepared(StrictJson.canonical(basis), evaluation, committed, canonical);
    }
    public static Qualified qualifyPublished(ClosedAdoptionMaterial.CurrentSource current, OriginalWriterTransaction.Committed committed,
            CanonicalReceiptSource canonical, RecoveryEvidence publishedBasis, RecoveryEvidence publishedQualification) {
        Prepared prepared = prepare(current, committed, canonical);
        StrictJson.require(java.util.Arrays.equals(prepared.basisBytes(), publishedBasis.bytes())
                && java.util.Arrays.equals(prepared.qualificationBytes(publishedBasis.reference()), publishedQualification.bytes()),
                "actual source-bound new basis and distinct qualification producer bytes");
        prepared.evaluation.material().sourceVerifier().verify(publishedBasis.reference());
        prepared.evaluation.material().sourceVerifier().verify(publishedQualification.reference());
        return wire(prepared,publishedBasis.reference(),publishedQualification.reference(),SCOPE);
    }

    /** Historical closed facts from an already verified original transaction, never current Driver qualification. */
    static Qualified qualifyRetained(Prepared prepared, RetainedClosedMeasurement retained,
            RecoveryEvidence publishedBasis, RecoveryEvidence publishedQualification) throws java.io.IOException {
        var history = retained.requireHistoricalInputs(); var evaluation = prepared.evaluation; var proof = evaluation.prerequisites();
        StrictJson.require(!history.currentDriverQualified() && !history.grantsWarmAttachment()
                && history.machineId().equals(evaluation.material().input().machineId())
                && history.historicalDriver().equals(proof.driver()) && history.historicalDriverIdentity().equals(proof.driverIdentity())
                && history.save().equals(proof.save()) && history.saveIdentity().equals(proof.saveIdentity())
                && history.validatorSource().equals(proof.validatorSource()) && history.checkpointDigest().equals(proof.checkpointDigest())
                && history.canonicalReceipt().equals(prepared.canonical),"same registered original historical measurement and closed writer proof");
        StrictJson.require(java.util.Arrays.equals(prepared.basisBytes(),publishedBasis.bytes())
                && java.util.Arrays.equals(prepared.qualificationBytes(publishedBasis.reference()),publishedQualification.bytes()),
                "actual original published closed basis and qualification remain immutable");
        var material = evaluation.material(); var verify = material.sourceVerifier();
        for (ExactRef ref : material.input().metadataSources()) { verify.verify(ref); }
        verify.verify(material.publishedEpoch().reference()); verify.verify(material.publishedPrefix().reference());
        var sources = material.sources();
        for (RecoveryEvidence evidence : java.util.List.of(sources.sdkClosed(),sources.gameExit(),sources.supervisorClosed(),
                sources.recordingClosed(),sources.captureClosed(),sources.screenReleased())) { verify.verify(evidence.reference()); }
        for (var task : sources.tasks()) {
            verify.verify(task.spec().reference()); verify.verify(task.closed().reference()); verify.verify(task.unregistered().reference());
        }
        for (var cycle : sources.settledCycles()) { verify.verify(cycle.auto().reference()); verify.verify(cycle.metrics().reference()); }
        StrictJson.require(ClosedPartialBusinessAuthority.verify(material.input(),sources,material.business(),verify).equals(evaluation.businessDigest()),
                "same independently verified immutable closed business prefix");
        OriginalWriterTransaction.validateReadback(prepared.committed.target(),evaluation,prepared.committed.head(),prepared.committed.event(),prepared.committed.index());
        // The canonical path may legitimately advance during restore; its immutable original event and index remain authoritative history.
        verify.verify(prepared.committed.event().evidence().reference()); verify.verify(prepared.committed.index().evidence().reference());
        verify.verify(publishedBasis.reference()); verify.verify(publishedQualification.reference()); verify.verify(prepared.canonical.reference());
        retained.requireHistoricalInputs();
        return wire(prepared,publishedBasis.reference(),publishedQualification.reference(),RETAINED_SCOPE);
    }

    private static Qualified wire(Prepared prepared, ExactRef basisRef, ExactRef qualificationRef, String scope) {
        ObjectNode wire = StrictJson.object(); wire.put("schema", INPUTS_SCHEMA);
        wire.put("machine_id", prepared.evaluation.material().input().machineId()); wire.set("basis_ref", basisRef.toJson());
        wire.set("validation_ref", qualificationRef.toJson());
        wire.put("basis_digest", RecoveryEvidence.sha256(prepared.basis));
        wire.set("seed", object(prepared.evaluation.material().business().savedSeed()));
        wire.set("governance", object(prepared.evaluation.material().business().savedGovernance()));
        wire.set("checkpoint", node(wire.get("seed")).get("actual_saved_checkpoint").deepCopy());
        wire.set("ledger", prepared.committed.head().value()); wire.set("closed", closed(prepared));
        wire.put("qualification_scope", scope); wire.put("new_game_day_credit", 0); wire.put("new_ordinary_cycle_credit", 0);
        wire.put("original_actions_replayed", false); wire.put("grants_new_warm_attachment", false);
        return new Qualified(ClosedAdoptionJson.encode(wire));
    }
    private static ObjectNode qualification(Prepared prepared, ExactRef basisRef) {
        var evaluation = prepared.evaluation; var proof = evaluation.prerequisites();
        ObjectNode row = StrictJson.object(); row.put("schema", QUALIFICATION_SCHEMA);
        row.put("machine_id", evaluation.material().input().machineId()); row.put("observed_at_utc", evaluation.material().input().observedAtUtc());
        row.set("basis_ref", basisRef.toJson()); row.set("driver_ref", proof.driver().toJson()); row.set("save_ref", proof.save().toJson());
        row.set("driver_identity_after", proof.driverIdentity().toJson()); row.set("save_identity_after", proof.saveIdentity().toJson());
        row.set("validator_source_ref", proof.validatorSource().toJson());
        row.set("epoch_ref", evaluation.material().publishedEpoch().reference().toJson()); row.set("settled_prefix_ref", evaluation.material().publishedPrefix().reference().toJson());
        row.set("canonical_checkpoint_proof", prepared.canonical.reference().toJson());
        row.set("committed_head_ref", prepared.committed.head().evidence().reference().toJson());
        row.put("input_digest", evaluation.candidate().inputDigest()); row.put("business_digest", evaluation.businessDigest());
        row.put("qualification_scope", SCOPE); row.put("new_game_day_credit", 0); row.put("new_ordinary_cycle_credit", 0);
        row.put("grants_new_warm_attachment", false); return row;
    }
    private static ObjectNode closed(Prepared prepared) {
        var material = prepared.evaluation.material(); ObjectNode row = StrictJson.object();
        row.set("closure_ref", material.publishedEpoch().reference().toJson());
        row.set("sdk_closed_ref", material.sources().sdkClosed().reference().toJson());
        ObjectNode game = object(material.sources().gameExit()), old = node(object(material.input().predecessor()).get("game_binding"));
        ObjectNode identity = row.putObject("old_game"); identity.set("pid", game.get("pid"));
        identity.put("creation_filetime", game.get("creation_filetime").bigIntegerValue().toString()); identity.set("creation_date", old.get("creation_date"));
        row.put("next_sequence", number(object(material.input().actualNext()), "next_sequence", 1));
        ArrayNode processes = row.putArray("sdk_processes");
        for (JsonNode process : object(material.sources().sdkClosed()).get("processes")) {
            ObjectNode value = node(process), target = processes.addObject();
            for (String key : Set.of("role", "pid", "executable", "exit_code")) { target.set(key, value.get(key)); }
            target.put("creation_filetime", value.get("creation_filetime").bigIntegerValue().toString());
        }
        row.put("observed_at_utc", material.input().observedAtUtc()); row.put("pipe_name", StrictJson.text(object(prepared.canonical).get("pipe_name"))); return row;
    }
    private static void validateBasis(ObjectNode basis, OriginalWriterTransaction.Evaluation evaluation) {
        StrictJson.object(basis, Set.of("schema", "machine_id", "observed_at_utc", "origin", "frame", "completed_cycles", "checkpoint", "campaign_goal_anchor",
                "refs", "identity_schema", "driver_identity", "save_identity", "next_sequence", "progress", "unknown_requests", "sidecars",
                "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed", "power_loss_durability"));
        equal(basis, "schema", "xar.current-saved-basis/v1"); equal(basis, "machine_id", evaluation.material().input().machineId());
        equal(basis, "identity_schema", FileStatIdentity.SCHEMA); equal(basis, "power_loss_durability", "not_asserted");
        StrictJson.integer(basis.get("ordinary_cycle_credit"), 0, 0); StrictJson.integer(basis.get("game_day_credit"), 0, 0);
        SettledQueryClassifier.falseValue(basis.get("original_actions_replayed")); SavedFrame frame = SavedFrame.fromJson(basis.get("frame"));
        ObjectNode progress = node(basis.get("progress")), checkpoint = node(basis.get("checkpoint"));
        StrictJson.require(number(basis, "completed_cycles", 0) == number(progress, "settled_cycles", 0)
                && frame.dateRaw() == number(progress, "settled_date_raw", 0) && frame.dateRaw() == number(checkpoint, "saved_date_raw", 0), "one actual saved frontier");
        ObjectNode refs = StrictJson.object(basis.get("refs"), Set.of("settled_state", "seed", "governance", "semantic_response", "save_response", "settled_full_response",
                "driver", "save", "driver_close", "closure", "ledger", "next", "origin_ledger", "wall_origin", "checkpoint_validator"));
        refs.elements().forEachRemaining(ExactRef::fromJson);
        StrictJson.require(FileStatIdentity.fromJson(basis.get("driver_identity"), FileStatIdentity.SCHEMA).equals(evaluation.prerequisites().driverIdentity())
                && FileStatIdentity.fromJson(basis.get("save_identity"), FileStatIdentity.SCHEMA).equals(evaluation.prerequisites().saveIdentity()), "current measured stat identities");
        for (JsonNode entry : basis.get("unknown_requests")) {
            ObjectNode row = StrictJson.object(entry, Set.of("sequence", "evidence_ref", "status", "replayed", "cycle_credit", "day_credit"));
            long sequence = number(row, "sequence", 1); StrictJson.require(sequence < number(basis, "next_sequence", 1), "unknown below consumed NEXT");
            equal(row, "status", "unknown"); SettledQueryClassifier.falseValue(row.get("replayed"));
            StrictJson.integer(row.get("cycle_credit"), 0, 0); StrictJson.integer(row.get("day_credit"), 0, 0); ExactRef.fromJson(row.get("evidence_ref"));
        }
    }
    private static ObjectNode object(RecoveryEvidence evidence) { return node(StrictJson.parse(evidence.bytes())); }
    private static ObjectNode node(JsonNode value) { return SettledQueryClassifier.object(value); }
    private static void equal(ObjectNode row, String key, String expected) { SettledQueryClassifier.equal(row, key, expected); }
    private static long number(ObjectNode row, String key, long min) { return SettledQueryClassifier.number(row, key, min); }
}
