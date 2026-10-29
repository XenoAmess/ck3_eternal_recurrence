package org.xar.ck3.control.wave2.development.constructionintent;

import java.math.BigInteger;
import java.util.Objects;

/** Pure projection of the existing construction action. This class cannot select or submit actions. */
public final class ConstructionIntentContinuity {
    public static final String SCHEMA = "xar.ck3.construction_selected_intent_continuity_v1";
    public static final String SUBMIT_STEP = "private-submit-player-construction-v1";
    public static final String RECEIPT_STEP = "private-query-player-construction-receipt-v1";

    private ConstructionIntentContinuity() { }

    public enum Evidence {
        TRUE, FALSE, UNKNOWN;

        public static Evidence of(Boolean value) {
            return value == null ? UNKNOWN : value ? TRUE : FALSE;
        }

        public Boolean nullableBoolean() {
            return this == UNKNOWN ? null : this == TRUE;
        }
    }

    public enum SourceRole {
        PRIOR_ACTION_RECEIPT_QUERY("prior_action_receipt_query"),
        SUBMISSION_RESULT("submission_result"), UNKNOWN("unknown"),
        PREVIOUS_CONSTRUCTION_RECEIPT("previous_construction_receipt");

        private final String wire;
        SourceRole(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum IntentOutcome {
        UNKNOWN("unknown"), REQUESTED_OBSERVED("requested_construction_observed"),
        DIFFERENT_OBSERVED("different_construction_observed"),
        RESTORED("restored_before_original_action"),
        NOT_APPLIED_AFTER_RESTORE("original_action_not_applied_after_restore"),
        PENDING("independent_material_result_pending");

        private final String wire;
        IntentOutcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Python v1 tests exact int types without a width/range restriction. */
    public record CandidateIds(BigInteger baronyTitleId, BigInteger provinceId,
                               BigInteger buildingTypeId, BigInteger slotIndex) {
        public static CandidateIds unknown() { return new CandidateIds(null, null, null, null); }
        public boolean complete() {
            return baronyTitleId != null && provinceId != null && buildingTypeId != null && slotIndex != null;
        }
    }

    /** Null identity components mean unavailable, as in the original v1 projection. */
    public record Identity(String actionRequestId, String episodeRunId, BigInteger actorCharacterId,
                           CandidateIds candidate) {
        public Identity {
            actionRequestId = nonempty(actionRequestId);
            episodeRunId = nonempty(episodeRunId);
            Objects.requireNonNull(candidate, "identity candidate");
        }
        public static Identity unknown() { return new Identity(null, null, null, CandidateIds.unknown()); }
    }

    /** Original producer status is retained, including statuses unknown to this version. */
    public record ProducerResult(Identity identity, String status, Evidence postconditionVerified,
                                 Evidence requestedPostconditionVerified,
                                 Evidence materialPostconditionVerified,
                                 CandidateIds observedMaterialCandidate, boolean candidatePresent) {
        public ProducerResult {
            status = nonempty(status);
            Objects.requireNonNull(identity, "result identity");
            Objects.requireNonNull(postconditionVerified, "postcondition evidence");
            Objects.requireNonNull(requestedPostconditionVerified, "requested evidence");
            Objects.requireNonNull(materialPostconditionVerified, "material evidence");
        }
    }

    public record ResultFields(String producerStatus, Evidence producerPostconditionVerified,
                               Evidence producerRequestedPostconditionVerified,
                               Evidence producerMaterialPostconditionVerified,
                               Evidence requestedConstructionVerified, Evidence materialConstructionVerified,
                               Evidence restorationVerified, CandidateIds observedMaterialCandidate,
                               IntentOutcome intentOutcome) {
        public ResultFields {
            Objects.requireNonNull(producerPostconditionVerified);
            Objects.requireNonNull(producerRequestedPostconditionVerified);
            Objects.requireNonNull(producerMaterialPostconditionVerified);
            Objects.requireNonNull(requestedConstructionVerified);
            Objects.requireNonNull(materialConstructionVerified);
            Objects.requireNonNull(restorationVerified);
            Objects.requireNonNull(intentOutcome);
        }

        private ResultFields unbound() {
            return new ResultFields(producerStatus, producerPostconditionVerified,
                    producerRequestedPostconditionVerified, producerMaterialPostconditionVerified,
                    Evidence.UNKNOWN, Evidence.UNKNOWN, Evidence.UNKNOWN,
                    observedMaterialCandidate, IntentOutcome.UNKNOWN);
        }
    }

    public record SelectedProjection(SourceRole sourceRole, String selectedStep, String deferredSelectedStep,
                                     Identity originalAction, Identity observedAction,
                                     Evidence actionIdentityMatches, Evidence actorIdentityMatches,
                                     Evidence candidateIdentityMatches, Evidence selectedQueryPerformedNewSubmission,
                                     ResultFields result) {
        public SelectedProjection {
            Objects.requireNonNull(sourceRole);
            Objects.requireNonNull(originalAction);
            Objects.requireNonNull(observedAction);
            Objects.requireNonNull(actionIdentityMatches);
            Objects.requireNonNull(actorIdentityMatches);
            Objects.requireNonNull(candidateIdentityMatches);
            Objects.requireNonNull(selectedQueryPerformedNewSubmission);
            Objects.requireNonNull(result);
        }
    }

    public record ConsumedProjection(Identity originalAction, ResultFields result) {
        public ConsumedProjection {
            Objects.requireNonNull(originalAction);
            Objects.requireNonNull(result);
        }
    }

    public static SelectedProjection projectSelected(String selectedStep, Identity original,
                                                      ProducerResult observed, String deferredSelectedStep) {
        Objects.requireNonNull(original, "pending action");
        Objects.requireNonNull(observed, "typed result");
        String step = nonempty(selectedStep);
        Evidence actionMatch = all(equal(original.actionRequestId(), observed.identity().actionRequestId()),
                equal(original.episodeRunId(), observed.identity().episodeRunId()));
        Evidence actorMatch = equal(original.actorCharacterId(), observed.identity().actorCharacterId());
        CandidateIds first = original.candidate();
        CandidateIds second = observed.identity().candidate();
        Evidence candidateMatch = all(equal(first.baronyTitleId(), second.baronyTitleId()),
                equal(first.provinceId(), second.provinceId()),
                equal(first.buildingTypeId(), second.buildingTypeId()), equal(first.slotIndex(), second.slotIndex()));
        SourceRole role = RECEIPT_STEP.equals(step) ? SourceRole.PRIOR_ACTION_RECEIPT_QUERY
                : SUBMIT_STEP.equals(step) ? SourceRole.SUBMISSION_RESULT : SourceRole.UNKNOWN;
        ResultFields fields = resultFields(observed);
        boolean bound = actionMatch == Evidence.TRUE && actorMatch != Evidence.FALSE
                && candidateMatch != Evidence.FALSE;
        if (fields.requestedConstructionVerified() == Evidence.TRUE) {
            bound = bound && actorMatch == Evidence.TRUE && candidateMatch == Evidence.TRUE;
        }
        if (role == SourceRole.UNKNOWN || !bound) { fields = fields.unbound(); }
        return new SelectedProjection(role, step, nonempty(deferredSelectedStep), original, observed.identity(),
                actionMatch, actorMatch, candidateMatch,
                RECEIPT_STEP.equals(step) ? Evidence.FALSE : Evidence.UNKNOWN, fields);
    }

    public static ConsumedProjection projectConsumed(ProducerResult receipt) {
        Objects.requireNonNull(receipt, "receipt");
        Identity identity = receipt.identity();
        ResultFields fields = resultFields(receipt);
        boolean complete = identity.actionRequestId() != null && identity.episodeRunId() != null;
        if (fields.requestedConstructionVerified() == Evidence.TRUE) {
            complete = complete && identity.actorCharacterId() != null && identity.candidate().complete();
        }
        return new ConsumedProjection(identity, complete ? fields : fields.unbound());
    }

    private static ResultFields resultFields(ProducerResult result) {
        Evidence requested = Evidence.UNKNOWN;
        Evidence material = Evidence.UNKNOWN;
        Evidence restoration = Evidence.UNKNOWN;
        IntentOutcome outcome = IntentOutcome.UNKNOWN;
        String status = result.status();
        if ("applied".equals(status) && result.postconditionVerified() == Evidence.TRUE) {
            if (result.requestedPostconditionVerified() != Evidence.FALSE
                    && result.materialPostconditionVerified() != Evidence.FALSE) {
                requested = Evidence.TRUE;
                material = Evidence.TRUE;
                outcome = IntentOutcome.REQUESTED_OBSERVED;
            }
        } else if ("observed_mismatched_construction".equals(status)) {
            if (result.requestedPostconditionVerified() == Evidence.FALSE
                    && result.materialPostconditionVerified() == Evidence.TRUE) {
                requested = Evidence.FALSE;
                material = Evidence.TRUE;
                outcome = IntentOutcome.DIFFERENT_OBSERVED;
            }
        } else if ("restored_before_action".equals(status) && result.postconditionVerified() == Evidence.TRUE) {
            requested = Evidence.FALSE;
            material = Evidence.FALSE;
            restoration = Evidence.TRUE;
            outcome = IntentOutcome.RESTORED;
        } else if ("not_applied_after_restore".equals(status)) {
            if (result.requestedPostconditionVerified() == Evidence.FALSE
                    && result.materialPostconditionVerified() == Evidence.FALSE) {
                requested = Evidence.FALSE;
                material = Evidence.FALSE;
                outcome = IntentOutcome.NOT_APPLIED_AFTER_RESTORE;
            }
        } else if ("submitted_verification_pending".equals(status) || "action_state_unknown".equals(status)) {
            outcome = IntentOutcome.PENDING;
        }
        CandidateIds observedMaterial = "applied".equals(status) && material == Evidence.TRUE
                ? result.candidatePresent() ? result.identity().candidate() : null
                : result.observedMaterialCandidate();
        return new ResultFields(status, result.postconditionVerified(), result.requestedPostconditionVerified(),
                result.materialPostconditionVerified(), requested, material, restoration, observedMaterial, outcome);
    }

    private static String nonempty(String value) { return value == null || value.isEmpty() ? null : value; }

    private static Evidence equal(Object first, Object second) {
        return first == null || second == null ? Evidence.UNKNOWN : Evidence.of(first.equals(second));
    }

    private static Evidence all(Evidence... values) {
        boolean unknown = false;
        for (Evidence value : values) {
            if (value == Evidence.FALSE) { return Evidence.FALSE; }
            unknown |= value == Evidence.UNKNOWN;
        }
        return unknown ? Evidence.UNKNOWN : Evidence.TRUE;
    }
}
