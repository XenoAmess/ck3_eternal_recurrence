package org.xar.ck3.control.admission.closedpartial;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryReducer;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;
import org.xar.ck3.control.recovery.RecoveryPreview;

/** Post-writer-readback pure proposal. It cannot perform or authorize the original commit. */
public final class ClosedPartialColdBasisPreview {
    public static final String QUALIFICATION_SCHEMA = "xar.closed-partial-full-basis-proposal/v1";
    private ClosedPartialColdBasisPreview() { }
    public sealed interface Outcome permits Unavailable, Rejected, Candidate {
        default boolean ready() { return false; }
        default boolean grantsColdLaunch() { return false; }
    }
    public record Unavailable(String reason) implements Outcome {
        public Unavailable { StrictJson.text(reason); }
    }
    public record Rejected(String reason) implements Outcome {
        public Rejected { StrictJson.text(reason); }
    }
    public record Candidate(byte[] proposedBasis, byte[] proposalQualification) implements Outcome {
        public Candidate { proposedBasis = proposedBasis.clone(); proposalQualification = proposalQualification.clone(); }
        @Override public byte[] proposedBasis() { return proposedBasis.clone(); }
        @Override public byte[] proposalQualification() { return proposalQualification.clone(); }
    }

    /**
     * The host must obtain actualCommittedHead from the original writer's successful
     * commit and fresh source-bound readback. This method checks its exact semantic
     * bytes against the sole recovery reducer, and re-invokes the same provider.
     */
    public static Outcome preview(ClosedFailureRecoveryInput input, ClosedPartialSources sources,
            RecoveryEvidence epoch, RecoveryEvidence prefix, RecoveryEvidence actualCommittedHead,
            ClosedPartialAdmissionVerifier.OriginalSdkVerifier originalSdk) {
        try {
            ClosedPartialAdmissionVerifier provider = new ClosedPartialAdmissionVerifier(sources, epoch, prefix, originalSdk);
            String inputDigest = ClosedFailureRecoveryReducer.inputDigest(input);
            RecoveryPrerequisiteVerifier.Check checked = provider.verify(input, inputDigest);
            if (checked instanceof RecoveryPrerequisiteVerifier.Unavailable missing) { return new Unavailable(missing.reason()); }
            if (checked instanceof RecoveryPrerequisiteVerifier.Rejected rejected) { return new Rejected(rejected.reason()); }
            if (!(checked instanceof RecoveryPrerequisiteVerifier.Verified proof)) { throw new IllegalStateException("proof branch"); }
            // The immutable input and just-observed proof are used by this one pure
            // reduction only. Do not reread a large Driver/SAVE twice per proposal.
            RecoveryPreview recovery = ClosedFailureRecoveryReducer.preview(input, (sameInput, sameDigest) -> {
                StrictJson.require(sameInput.equals(input) && sameDigest.equals(inputDigest), "same scoped actual proof/input");
                return proof;
            });
            if (recovery instanceof RecoveryPreview.Unavailable missing) { return new Unavailable(missing.reason()); }
            if (recovery instanceof RecoveryPreview.Rejected rejected) { return new Rejected(rejected.reason()); }
            if (!(recovery instanceof RecoveryPreview.Candidate candidate)) { throw new IllegalStateException("recovery branch"); }
            ObjectNode head = object(actualCommittedHead);
            StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(head), candidate.committedState()),
                    "original writer committed head must be actually read back, not a projected before/after alias");
            ObjectNode basis = object(input.savedBasis()); ObjectNode refs = ClosedPartialEpochCodec.object(basis.get("refs"));
            refs.set("driver", proof.driver().toJson()); refs.set("save", proof.save().toJson());
            refs.set("checkpoint_validator", proof.validatorSource().toJson());
            refs.set("driver_close", proof.canonicalCheckpointProof().toJson());
            refs.set("closure", epoch.reference().toJson()); refs.set("next", input.actualNext().reference().toJson());
            refs.set("ledger", actualCommittedHead.reference().toJson());
            basis.set("driver_identity", proof.driverIdentity().toJson()); basis.set("save_identity", proof.saveIdentity().toJson());
            basis.put("next_sequence", proof.unknownSequence() + 1);
            // Original saved seed/governance/frame/checkpoint/origin/goal anchor remain the original clean saved frontier.
            byte[] basisBytes = StrictJson.canonical(basis);
            ObjectNode qualification = StrictJson.object(); qualification.put("schema", QUALIFICATION_SCHEMA);
            qualification.put("machine_id", input.machineId()); qualification.put("observed_at_utc", input.observedAtUtc());
            qualification.put("input_digest", candidate.inputDigest());
            qualification.put("proposed_basis_sha256", RecoveryEvidence.sha256(basisBytes));
            qualification.set("prior_basis", input.savedBasis().reference().toJson());
            qualification.set("closed_epoch", epoch.reference().toJson());
            qualification.set("settled_prefix", prefix.reference().toJson());
            qualification.set("original_sdk_checkpoint", proof.canonicalCheckpointProof().toJson());
            qualification.set("actual_committed_head", actualCommittedHead.reference().toJson());
            qualification.put("expected_committed_sequence", candidate.expectedSequence() + 1);
            qualification.put("ready", false); qualification.put("new_game_day_credit", 0);
            qualification.put("new_ordinary_cycle_credit", 0); qualification.put("raw_pending_modified", false);
            qualification.put("qualification_scope", "PURE_POST_COMMIT_BASIS_PROPOSAL_ORIGINAL_COLD_CONSUMER_ADAPTER_REQUIRED");
            return new Candidate(basisBytes, StrictJson.canonical(qualification, StrictJson.OUTPUT_MAX_BYTES));
        } catch (ContractViolationException error) {
            return new Rejected(error.getMessage());
        }
    }
    private static ObjectNode object(RecoveryEvidence evidence) {
        return ClosedPartialEpochCodec.object(StrictJson.parse(evidence.bytes()));
    }
}
