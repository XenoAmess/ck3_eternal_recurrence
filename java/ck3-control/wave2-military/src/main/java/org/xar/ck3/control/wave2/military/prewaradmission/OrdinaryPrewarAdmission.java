package org.xar.ck3.control.wave2.military.prewaradmission;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.coalition.CoalitionRiskJsonAdapter;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionGate.Assessable;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionGate.RequiredQuery;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionGate.Stopped;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Field;

/** Real composition of the independent outer lease and the complete Java coalition risk validator. */
public final class OrdinaryPrewarAdmission {
    public static final String CAPABILITY = "game.command.query-prewar-force-coalition-coverage-v2-N";

    private OrdinaryPrewarAdmission() { }

    public enum Status {
        UNKNOWN("unknown"), QUALIFIED("qualified"), RISK_REJECTED("risk_rejected");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status fromWire(String value) {
            for (Status status : values()) { if (status.wire.equals(value)) { return status; } }
            throw new IllegalArgumentException("unknown coalition risk status");
        }
    }

    public enum Reason {
        CURRENT_SNAPSHOT_REQUIRED("current_snapshot_required"),
        CURRENT_PAUSED_LIVING_ACTOR_REQUIRED("current_paused_living_actor_required"),
        CURRENT_NATIVE_BUILD_REQUIRED("current_native_build_required"),
        CURRENT_SNAPSHOT_BINDING_REQUIRED("current_snapshot_binding_required"),
        CURRENT_DECLARATION_IDENTITY_REQUIRED("current_declaration_identity_required"),
        CURRENT_FORCE_COALITION_QUERY_REQUIRED("current_force_coalition_query_required"),
        FORCE_COALITION_QUERY_SCOPE_STALE("force_coalition_query_scope_stale"),
        FORCE_COALITION_QUERY_NOT_ACCEPTED("force_coalition_query_not_accepted"),
        INDEPENDENT_FORCE_COALITION_RECEIPT_REQUIRED("independent_force_coalition_receipt_required"),
        FORCE_COALITION_COVERAGE_PARTIAL("force_coalition_coverage_partial"),
        FORCE_COALITION_COVERAGE_INVALID("force_coalition_coverage_invalid"),
        REQUIRED_CURRENT_INVENTORY_EVIDENCE_UNAVAILABLE("required_current_inventory_evidence_unavailable"),
        COMPLETE_CURRENT_INVENTORY_FORCE_MARGIN_PASSED("complete_current_inventory_force_margin_passed"),
        ACTOR_CURRENT_INVENTORY_FLOOR_IS_ZERO("actor_current_inventory_floor_is_zero"),
        COMPLETE_CURRENT_INVENTORY_FORCE_MARGIN_INSUFFICIENT("complete_current_inventory_force_margin_insufficient"),
        CURRENT_SELECTED_NATIVE_DECLARATION_LEGALITY_REQUIRED("current_selected_native_declaration_legality_required");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Reason fromWire(String value) {
            for (Reason reason : values()) { if (reason.wire.equals(value)) { return reason; } }
            throw new IllegalArgumentException("unknown ordinary prewar reason");
        }
    }

    public record Result(Status status, boolean declareAdmitted, boolean forceRiskQualified, Reason reason,
            RequiredQuery requiredQuery, Field<CoalitionRiskJsonAdapter.Assessment> forceRisk, Field<String> diagnostic) {
        public Result {
            Objects.requireNonNull(status); Objects.requireNonNull(reason);
            Objects.requireNonNull(forceRisk); Objects.requireNonNull(diagnostic);
        }
    }

    public static Result assess(PrewarAdmissionInput input) {
        var gate = PrewarAdmissionGate.evaluate(input);
        if (gate instanceof Stopped stopped) {
            return new Result(Status.UNKNOWN, false, false, Reason.fromWire(stopped.reason().wire()),
                    stopped.requiredQuery(), Field.missing(), Field.missing());
        }
        Assessable assessable = (Assessable) gate;
        var snapshot = assessable.input().snapshot().value();
        var query = snapshot.query().value();
        final CoalitionRiskJsonAdapter.Assessment assessment;
        try {
            ObjectNode binding = query.executionReceipt().value().copy();
            binding.put("request_id", query.nativeRequestId().value());
            assessment = CoalitionRiskJsonAdapter.assess(query.coverage().value().copy(),
                    PrewarAdmissionCodec.snapshotNode(snapshot), PrewarAdmissionCodec.declarationNode(input.declaration()),
                    binding, query.nativeRequestId().value());
        } catch (IllegalArgumentException error) {
            return new Result(Status.UNKNOWN, false, false, Reason.FORCE_COALITION_COVERAGE_INVALID,
                    null, Field.missing(), Field.of(Objects.requireNonNullElse(error.getMessage(), error.getClass().getSimpleName())));
        }
        var risk = assessment.risk();
        Status status = Status.fromWire(risk.status().wire());
        Reason reason = Reason.fromWire(risk.reason().wire());
        boolean finalLegal = Boolean.TRUE.equals(assessment.finalCanSend());
        boolean admitted = status == Status.QUALIFIED && risk.forceRiskQualified() && finalLegal;
        if (status == Status.QUALIFIED && !finalLegal) {
            status = Status.UNKNOWN;
            reason = Reason.CURRENT_SELECTED_NATIVE_DECLARATION_LEGALITY_REQUIRED;
        }
        return new Result(status, admitted, risk.forceRiskQualified(), reason, null, Field.of(assessment), Field.missing());
    }

    public static byte[] encodeResult(Result result) {
        ObjectNode root = StrictJson.object().put("status", result.status().wire()).put("declare_admitted", result.declareAdmitted())
                .put("force_risk_qualified", result.forceRiskQualified()).put("reason", result.reason().wire());
        if (result.requiredQuery() == null) {
            root.putNull("required_prewar_force_coalition_query");
        } else {
            RequiredQuery query = result.requiredQuery();
            root.set("required_prewar_force_coalition_query", StrictJson.object().put("declaration_id", query.declarationId())
                    .put("expected_revision", query.expectedRevision()).put("profile", query.profile()));
        }
        if (result.forceRisk().hasValue()) { root.set("force_risk", result.forceRisk().value().riskJson()); }
        if (result.diagnostic().hasValue()) { root.put("diagnostic", result.diagnostic().value()); }
        return StrictJson.canonical(root);
    }
}
