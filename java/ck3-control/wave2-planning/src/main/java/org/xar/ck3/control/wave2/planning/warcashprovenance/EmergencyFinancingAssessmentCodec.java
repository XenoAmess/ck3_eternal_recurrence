package org.xar.ck3.control.wave2.planning.warcashprovenance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import static org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment.*;
import static org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapModels.*;

/** JSON boundary for the same current-input evaluation used by the ordinary construction consumer. */
public final class EmergencyFinancingAssessmentCodec {
    public static final String REQUEST_SCHEMA = "xar.emergency-financing-assessment.request.v1";
    public static final String RESULT_SCHEMA = "xar.emergency-financing-assessment.v1";
    private EmergencyFinancingAssessmentCodec() { }

    public record Request(Input gapInput, LoanFinancingCodec.LoanInput loanInput, PendingObservation pending,
            Optional<LoanFinancingCodec.PlanningFrame> currentPlanningFrame) {
        public Request {
            java.util.Objects.requireNonNull(gapInput); java.util.Objects.requireNonNull(loanInput);
            java.util.Objects.requireNonNull(pending);
            java.util.Objects.requireNonNull(currentPlanningFrame);
        }
    }
    public static Request decode(byte[] bytes) {
        ObjectNode request = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "gap_request", "loan_request", "pending_observation"));
        require(REQUEST_SCHEMA.equals(StrictJson.text(request.get("schema"))), "unknown emergency financing request schema");
        Input input = FinancingGapCodec.decode(SdkProjectionJson.encode(request.get("gap_request")));
        JsonNode loan = request.get("loan_request");
        LoanFinancingCodec.LoanInput projected = loan.isNull() ? new LoanFinancingCodec.NotProvided()
                : LoanFinancingCodec.decodeAndProject(SdkProjectionJson.encode(loan));
        return new Request(input, projected, pending(request.get("pending_observation")),
                currentPlanningFrame(input.frame(), request.path("gap_request").path("snapshot")));
    }
    public static Assessment assess(Request request) {
        return EmergencyFinancingAssessment.assess(request.gapInput(), request.loanInput(), request.pending(), request.currentPlanningFrame());
    }
    public static byte[] evaluate(byte[] bytes) { return encode(assess(decode(bytes))); }

    public static byte[] encode(Assessment result) {
        ObjectNode node = StrictJson.object(); node.put("schema", RESULT_SCHEMA);
        node.set("source_frame", frame(result.sourceFrame()));
        node.set("planning_source_frame", result.planningSourceFrame().<JsonNode>map(EmergencyFinancingAssessmentCodec::planningFrame)
                .orElseGet(() -> StrictJson.object().nullNode()));
        node.set("gap", StrictJson.parse(FinancingGapCodec.encode(result.gap())));
        putInteger(node, "actual_wallet_raw", result.actualWalletRaw()); node.put("raw_scale", 100000);
        ObjectNode loan = node.putObject("loan");
        loan.put("status", result.loan().status().name()); loan.put("eligibility", result.loan().eligibility().name());
        putLong(loan, "prospective_principal_raw", result.loan().prospectivePrincipalRaw());
        if (result.loan().declaredCostsRaw().isPresent()) {
            var costs = loan.putArray("declared_costs_raw"); result.loan().declaredCostsRaw().orElseThrow().forEach(costs::add);
        } else loan.putNull("declared_costs_raw");
        loan.put("complete_loan_terms_verified", false); loan.put("typed_debt_readback_verified", false);
        loan.put("independently_attributed_received_funds_verified", false); loan.put("submit_planned", false);
        ObjectNode cancel = node.putObject("cancellation"); cancel.put("status", result.cancellation().name());
        cancel.put("current_active_project_independently_observed", false); cancel.putNull("refund_quote_raw");
        cancel.put("submit_planned", false);
        node.set("pending_observation", pending(result.pending())); node.put("replay_guard", result.replay().name());
        node.put("unreceived_funding_credited_raw", 0); node.putNull("selected_action"); node.put("submit_planned", false);
        node.put("optional_construction_may_use_prospective_funding", false);
        node.put("continue_existing_war_action", true); node.put("future_funding_receipt_must_keep_same_procurement_epoch", true);
        return StrictJson.canonical(node);
    }

    /** Round-trip parser verifies all immutable flags; persisted assessments can never assert a funding/action grant. */
    public static Assessment decodeResult(byte[] bytes) {
        JsonNode node = StrictJson.parse(bytes);
        require(node.isObject() && RESULT_SCHEMA.equals(StrictJson.text(node.get("schema"))), "unknown emergency financing result schema");
        ObjectNode loan = StrictJson.object(node.get("loan"), Set.of("status", "eligibility", "prospective_principal_raw",
                "declared_costs_raw", "complete_loan_terms_verified", "typed_debt_readback_verified",
                "independently_attributed_received_funds_verified", "submit_planned"));
        JsonNode costs = loan.get("declared_costs_raw"); Optional<List<Long>> observedCosts = Optional.empty();
        if (!costs.isNull()) {
            require(costs.isArray() && costs.size() == 10, "ten signed cost slots or null required");
            List<Long> values = new ArrayList<>(); for (JsonNode value : costs) values.add(integer64(value));
            observedCosts = Optional.of(List.copyOf(values));
        }
        JsonNode principal = loan.get("prospective_principal_raw");
        LoanReview review = new LoanReview(LoanStatus.valueOf(StrictJson.text(loan.get("status"))),
                Eligibility.valueOf(StrictJson.text(loan.get("eligibility"))),
                principal.isNull() ? OptionalLong.empty() : OptionalLong.of(integer64(principal)), observedCosts);
        ObjectNode cancel = StrictJson.object(node.get("cancellation"), Set.of("status", "current_active_project_independently_observed",
                "refund_quote_raw", "submit_planned"));
        Assessment result = new Assessment(readFrame(node.get("source_frame")), readPlanningFrame(node.get("planning_source_frame")),
                FinancingGapCodec.decodeResult(StrictJson.canonical(node.get("gap"))), nullableInteger(node.get("actual_wallet_raw")),
                review, CancellationStatus.valueOf(StrictJson.text(cancel.get("status"))), pending(node.get("pending_observation")),
                ReplayGuard.valueOf(StrictJson.text(node.get("replay_guard"))));
        require(node.equals(StrictJson.parse(encode(result))), "financing result fields or invariant flags changed");
        return result;
    }
    private static PendingObservation pending(JsonNode node) {
        require(node != null, "pending_observation is required (explicit null when its reader is unavailable)");
        if (node.isNull()) return PendingObservation.seamUnavailable();
        require(node.isObject(), "pending observation object required");
        String status = StrictJson.text(node.get("status"));
        if (status.equals("no_pending_action")) {
            StrictJson.object(node, Set.of("status")); return new NoPendingAction();
        }
        StrictJson.object(node, Set.of("status", "kind", "action_id", "procurement_epoch"));
        return new PendingAction(FundingKind.valueOf(StrictJson.text(node.get("kind"))),
                StrictJson.text(node.get("action_id")), StrictJson.text(node.get("procurement_epoch")), SubmissionState.valueOf(status));
    }
    private static JsonNode pending(PendingObservation pending) {
        if (pending instanceof PendingUnavailable) return StrictJson.object().nullNode();
        ObjectNode node = StrictJson.object();
        if (pending instanceof NoPendingAction) return node.put("status", "no_pending_action");
        PendingAction action = (PendingAction) pending; node.put("status", action.state().name());
        node.put("kind", action.kind().name()); node.put("action_id", action.actionId()); node.put("procurement_epoch", action.procurementEpoch());
        return node;
    }
    private static ObjectNode frame(ObservedFrame value) {
        ObjectNode node = StrictJson.object(); node.put("played_character_id", value.playedCharacterId());
        node.put("native_revision", value.nativeRevision()); node.put("date_raw", value.dateRaw());
        node.put("snapshot_id", value.snapshotId()); node.put("revision", value.revision()); node.put("episode_run_id", value.episodeRunId());
        return node;
    }
    private static Optional<LoanFinancingCodec.PlanningFrame> currentPlanningFrame(ObservedFrame frame, JsonNode snapshot) {
        JsonNode pid = snapshot.path("diagnostics").path("bridge_pid"), generation = snapshot.path("diagnostics").path("connection_generation");
        if (!snapshot.path("paused").isBoolean() || !snapshot.path("paused").booleanValue()
                || !snapshot.path("map_ready").isBoolean() || !snapshot.path("map_ready").booleanValue()
                || !pid.isIntegralNumber() || pid.bigIntegerValue().signum() <= 0
                || !generation.isIntegralNumber() || generation.bigIntegerValue().signum() < 0) return Optional.empty();
        return Optional.of(new LoanFinancingCodec.PlanningFrame(frame.snapshotId(), frame.revision(), frame.nativeRevision(), frame.dateRaw(),
                frame.playedCharacterId(), frame.episodeRunId(), pid.bigIntegerValue(), generation.bigIntegerValue()));
    }
    private static ObjectNode planningFrame(LoanFinancingCodec.PlanningFrame frame) {
        ObjectNode node = StrictJson.object().put("snapshot_id", frame.snapshotId()).put("revision", frame.revision())
                .put("native_revision", frame.nativeRevision()).put("date_raw", frame.dateRaw()).put("actor_character_id", frame.actorCharacterId())
                .put("episode_run_id", frame.episodeRunId()).put("bridge_pid", frame.bridgePid()).put("connection_generation", frame.connectionGeneration());
        return node;
    }
    private static Optional<LoanFinancingCodec.PlanningFrame> readPlanningFrame(JsonNode value) {
        require(value != null, "nullable planning_source_frame required"); if (value.isNull()) return Optional.empty();
        ObjectNode node = StrictJson.object(value, Set.of("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id",
                "episode_run_id", "bridge_pid", "connection_generation"));
        return Optional.of(new LoanFinancingCodec.PlanningFrame(StrictJson.text(node.get("snapshot_id")), integer(node.get("revision")),
                integer(node.get("native_revision")), integer(node.get("date_raw")), integer(node.get("actor_character_id")),
                StrictJson.text(node.get("episode_run_id")), integer(node.get("bridge_pid")), integer(node.get("connection_generation"))));
    }
    private static ObservedFrame readFrame(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id"));
        return new ObservedFrame(integer(node.get("played_character_id")), integer(node.get("native_revision")), integer(node.get("date_raw")),
                StrictJson.text(node.get("snapshot_id")), integer(node.get("revision")), StrictJson.text(node.get("episode_run_id")));
    }
    private static Optional<BigInteger> nullableInteger(JsonNode value) {
        require(value != null, "nullable actual wallet is required"); return value.isNull() ? Optional.empty() : Optional.of(integer(value));
    }
    private static void putInteger(ObjectNode node, String key, Optional<BigInteger> value) {
        if (value.isPresent()) node.put(key, value.orElseThrow()); else node.putNull(key);
    }
    private static void putLong(ObjectNode node, String key, OptionalLong value) {
        if (value.isPresent()) node.put(key, value.getAsLong()); else node.putNull(key);
    }
    private static BigInteger integer(JsonNode value) {
        require(value != null && value.isIntegralNumber(), "actual integer token required"); return value.bigIntegerValue();
    }
    private static long integer64(JsonNode value) { return StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
