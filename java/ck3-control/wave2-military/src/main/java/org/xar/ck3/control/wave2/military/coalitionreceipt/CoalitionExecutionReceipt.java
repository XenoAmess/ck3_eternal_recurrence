package org.xar.ck3.control.wave2.military.coalitionreceipt;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.coalition.CoalitionRiskJsonAdapter;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.Observation;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.ObservationStatus;

/** Actual independent TOP execution receipt boundary; never an endpoint, cache writer or action permit. */
public final class CoalitionExecutionReceipt {
    public static final String STEP = "query-prewar-force-coalition-coverage-v2";
    public static final String DOMAIN_KEY = "prewar_force_coalition_coverage_v2";
    private static final Set<String> TOP_FIELDS = Set.of("type", "protocol_version", "request_id", "ok", "execution_receipt", "result");
    private static final Set<String> RECEIPT_FIELDS = Set.of("ticket", "query_sequence", "capture_epoch");
    private static final Set<String> RESULT_FIELDS = Set.of("step", "accepted", "status", "private_build", "read_only", "advertised", "domain_key", DOMAIN_KEY);

    private CoalitionExecutionReceipt() { }

    public record Receipt(BigInteger ticket, BigInteger querySequence, BigInteger captureEpoch) {
        public Receipt {
            uint64(ticket); uint64(querySequence); uint64(captureEpoch);
            require(ticket.equals(querySequence), "actual execution sequence differs from ticket");
        }
        public ObjectNode toJson() {
            return StrictJson.object().put("ticket", ticket).put("query_sequence", querySequence).put("capture_epoch", captureEpoch);
        }
    }

    /** Constructor is private: only the complete TOP validator can create this receipt binding. */
    public static final class ValidatedCommandResult {
        private final String requestId;
        private final Receipt receipt;
        private final ObservationStatus status;
        private final JsonNode unvalidatedBody;

        private ValidatedCommandResult(String requestId, Receipt receipt, ObservationStatus status, JsonNode body) {
            this.requestId = requestId;
            this.receipt = receipt;
            this.status = status;
            unvalidatedBody = body.deepCopy();
        }
        public String requestId() { return requestId; }
        public Receipt receipt() { return receipt; }
        public ObservationStatus status() { return status; }
        /** Body remains unvalidated. Deep copy preserves float, integer, null and extension token kinds. */
        public JsonNode unvalidatedBodyCopy() { return unvalidatedBody.deepCopy(); }
        public ObjectNode exportIndependentBinding() { return receipt.toJson().put("request_id", requestId); }
        public ObjectNode resultJson() {
            ObjectNode result = StrictJson.object().put("step", STEP).put("accepted", true).put("status", status.wire())
                    .put("private_build", false).put("read_only", true).put("advertised", true).put("domain_key", DOMAIN_KEY);
            result.set(DOMAIN_KEY, unvalidatedBodyCopy());
            return result;
        }
        public ObjectNode commandResultJson() {
            ObjectNode result = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                    .put("request_id", requestId).put("ok", true);
            result.set("execution_receipt", receipt.toJson()); result.set("result", resultJson());
            return result;
        }
    }

    /** Validated domain paired with its actual receipt. Outer connection/episode/before-after checks remain required. */
    public static final class CurrentBody {
        private final ValidatedCommandResult command;
        private final Observation observation;
        private CurrentBody(ValidatedCommandResult command, Observation observation) {
            this.command = command; this.observation = observation;
        }
        public ValidatedCommandResult command() { return command; }
        public Observation observation() { return observation; }
    }

    public static ValidatedCommandResult validate(JsonNode frame, String expectedRequestId) {
        ObjectNode root = inputObject(frame, TOP_FIELDS);
        require(expectedRequestId != null && !expectedRequestId.isEmpty(), "nonempty fresh expected request ID required");
        require(text(root.get("type")).equals("command_result") && text(root.get("request_id")).equals(expectedRequestId),
                "command_result request/type mismatch");
        inputInteger(root.get("protocol_version"), 1, 1);
        inputTrue(root.get("ok"));
        ObjectNode rawReceipt = inputObject(root.get("execution_receipt"), RECEIPT_FIELDS);
        Receipt receipt = new Receipt(uint64(rawReceipt.get("ticket")), uint64(rawReceipt.get("query_sequence")), uint64(rawReceipt.get("capture_epoch")));
        ObjectNode rawResult = inputObject(root.get("result"), RESULT_FIELDS);
        require(text(rawResult.get("step")).equals(STEP) && text(rawResult.get("domain_key")).equals(DOMAIN_KEY), "formal domain/step mismatch");
        inputTrue(rawResult.get("accepted")); inputTrue(rawResult.get("read_only")); inputTrue(rawResult.get("advertised"));
        require(rawResult.get("private_build").isBoolean() && !rawResult.get("private_build").booleanValue(), "formal result cannot be private");
        String status = text(rawResult.get("status"));
        require(status.equals("available") || status.equals("partial"), "formal result status malformed");
        return new ValidatedCommandResult(expectedRequestId, receipt,
                status.equals("available") ? ObservationStatus.AVAILABLE : ObservationStatus.PARTIAL, rawResult.get(DOMAIN_KEY));
    }

    public static CurrentBody normalizeAgainstLease(ValidatedCommandResult command, JsonNode projectedSnapshot,
                                                     JsonNode expectedDeclaration, BigInteger expectedCaptureEpoch) {
        Objects.requireNonNull(command, "actual validated command result required");
        Observation observation = CoalitionRiskJsonAdapter.normalize(command.unvalidatedBodyCopy(), projectedSnapshot, expectedDeclaration,
                command.exportIndependentBinding(), command.requestId(), expectedCaptureEpoch);
        require(command.status() == observation.status(), "outer result status differs from actual normalized domain");
        return new CurrentBody(command, observation);
    }

    /** Lossy command-history data only. This cannot mint CurrentBody, a receipt binding, or a query lease. */
    public static final class HistoryProjection {
        private final boolean accepted;
        private final ObservationStatus status;
        private final String requestId;
        private final Receipt receipt;
        private final String declarationId;
        private final Long actorLower;
        private final Long enemyUpper;
        private final boolean coverageComplete;
        private final boolean initialReady;
        private final int ownerRows;
        private HistoryProjection(boolean accepted, ObservationStatus status, String requestId, Receipt receipt,
                                  String declarationId, Long actorLower, Long enemyUpper,
                                  boolean coverageComplete, boolean initialReady, int ownerRows) {
            this.accepted = accepted; this.status = status; this.requestId = requestId; this.receipt = receipt;
            this.declarationId = declarationId; this.actorLower = actorLower; this.enemyUpper = enemyUpper;
            this.coverageComplete = coverageComplete; this.initialReady = initialReady; this.ownerRows = ownerRows;
        }
    }

    /** Named projection of the real enriched query result, deliberately weaker than TOP or current-body validation. */
    public static HistoryProjection historyProjection(JsonNode result) {
        require(result instanceof ObjectNode, "enriched history result object required");
        JsonNode domain = result.get(DOMAIN_KEY);
        require(domain instanceof ObjectNode, "enriched history domain object required");
        ObjectNode receipt = inputObject(result.get("execution_receipt"), RECEIPT_FIELDS);
        Receipt execution = new Receipt(uint64(receipt.get("ticket")), uint64(receipt.get("query_sequence")), uint64(receipt.get("capture_epoch")));
        String status = text(result.get("status"));
        require(status.equals("available") || status.equals("partial"), "history result status malformed");
        JsonNode owners = domain.get("owner_forces");
        require(owners != null && owners.isArray(), "history owner forces array required");
        return new HistoryProjection(bool(result.get("accepted")),
                status.equals("available") ? ObservationStatus.AVAILABLE : ObservationStatus.PARTIAL,
                inputText(result.get("native_request_id")), execution, inputText(domain.get("declaration_id")),
                nullableCount(domain.get("actor_lower_soldiers")), nullableCount(domain.get("enemy_upper_soldiers")),
                bool(domain.get("enemy_force_coverage_complete")), bool(domain.get("complete_initial_participants_ready")), owners.size());
    }

    /** Current typed output and real enriched-query output share exactly one lossy serializer. */
    public static ObjectNode historySummary(CurrentBody current) {
        Objects.requireNonNull(current, "actual normalized current body required");
        Observation observation = current.observation();
        return historySummary(new HistoryProjection(true, observation.status(), current.command().requestId(), current.command().receipt(),
                observation.declarationId(), observation.actorLowerSoldiers(), observation.enemyUpperSoldiers(),
                observation.enemyForceCoverageComplete(), observation.completeInitialParticipantsReady(), observation.ownerForces().size()));
    }

    public static ObjectNode historySummary(HistoryProjection projection) {
        Objects.requireNonNull(projection, "typed lossy history projection required");
        ObjectNode result = StrictJson.object().put("schema", "prewar-force-coalition-v2-history-summary-v1").put("schema_version", 1)
                .put("step", STEP).put("accepted", projection.accepted).put("status", projection.status.wire()).put("read_only", true)
                .put("full_result_preserved", false).put("unavailable_reason", "domain_details_omitted_from_command_history")
                .put("native_request_id", projection.requestId);
        result.set("execution_receipt", projection.receipt.toJson());
        result.put("declaration_id", projection.declarationId).put("enemy_force_coverage_complete", projection.coverageComplete)
                .put("complete_initial_participants_ready", projection.initialReady).put("owner_force_rows", projection.ownerRows);
        put(result, "actor_lower_soldiers", projection.actorLower); put(result, "enemy_upper_soldiers", projection.enemyUpper);
        return result;
    }

    private static boolean bool(JsonNode value) {
        require(value != null && value.isBoolean(), "actual history boolean required");
        return value.booleanValue();
    }
    private static Long nullableCount(JsonNode value) {
        require(value != null, "nullable history count missing");
        return value.isNull() ? null : inputInteger(value, 0, Long.MAX_VALUE);
    }

    private static String text(JsonNode value) {
        require(value != null && value.isTextual(), "actual string required");
        return value.textValue();
    }
    private static BigInteger uint64(JsonNode value) { return inputInteger(value, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static void uint64(BigInteger value) {
        require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 receipt value required");
    }
    private static void put(ObjectNode result, String name, Long value) {
        if (value == null) result.putNull(name); else result.put(name, value);
    }
    private static void require(boolean condition, String reason) { if (!condition) throw new ProjectionDomainRejection("prewar v2 receipt " + reason); }

    // These wrappers contain only the shared input primitive; no algorithm, result construction or encoder is caught.
    private static ObjectNode inputObject(JsonNode value, Set<String> fields) {
        try { return StrictJson.object(value, fields); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static long inputInteger(JsonNode value, long minimum, long maximum) {
        try { return StrictJson.integer(value, minimum, maximum); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static BigInteger inputInteger(JsonNode value, BigInteger minimum, BigInteger maximum) {
        try { return StrictJson.integer(value, minimum, maximum); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static String inputText(JsonNode value) {
        try { return StrictJson.text(value); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static void inputTrue(JsonNode value) {
        try { StrictJson.trueValue(value); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
}
