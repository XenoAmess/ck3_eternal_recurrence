package org.xar.ck3.control.warbudget;

import static org.xar.ck3.control.warbudget.BudgetJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.IntNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Single in-process port for unchanged SDK observations; no HTTP/resource/writer authority. */
public final class WarBudgetCodec {
    public static final String SCHEMA = "g2.war-budget-request/v1";
    public enum Operation {
        PRIORITY_EMERGENCY_LEVEL_V1(Set.of("war")),
        OBSERVE_EMERGENCY_POLICY_V1(Set.of("snapshot", "priority", "root", "spending")),
        VALID_SAVED_EMERGENCY_REVISION_V1(Set.of("selected", "source_frame", "snapshot")),
        EMERGENCY_QUOTE_BUDGET_V1(Set.of("snapshot", "policy", "focus", "local", "troops", "price", "contract_months", "root", "normal_finance", "package")),
        OBSERVE_EMERGENCY_RECOVERY_V1(Set.of("snapshot", "ledger", "root"));
        private final Set<String> fields;
        Operation(Set<String> fields) { this.fields = fields; }
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
        static Operation fromJson(JsonNode value) {
            for (Operation operation : values()) { if (text(value, operation.wire())) { return operation; } }
            throw new ContractViolationException("unknown war budget operation");
        }
    }
    /** The dynamic boundary is confined to versioned, checked SDK JSON objects. */
    public record Request(Operation operation, ObjectNode arguments) {
        public Request {
            Objects.requireNonNull(operation); arguments = StrictJson.object(arguments, operation.fields).deepCopy();
            // Legacy unknown fact containers retain null; required operational containers are objects.
            for (String field : operation.fields) {
                if (Set.of("snapshot", "war", "priority", "policy", "selected", "local", "normal_finance", "package", "ledger").contains(field)) {
                    record(arguments.get(field));
                }
            }
        }
        @Override public ObjectNode arguments() { return arguments.deepCopy(); }
        public ObjectNode toJson() {
            ObjectNode row = obj().put("schema", SCHEMA).put("operation", operation.wire()); row.set("arguments", arguments()); return row;
        }
    }
    private WarBudgetCodec() { }
    public static Request parse(byte[] input) {
        ObjectNode row = StrictJson.object(StrictJson.parse(input), Set.of("schema", "operation", "arguments"));
        StrictJson.require(text(row.get("schema"), SCHEMA), "war budget request schema differs");
        return new Request(Operation.fromJson(row.get("operation")), record(row.get("arguments")));
    }
    public static byte[] evaluate(byte[] input) {
        JsonNode result;
        try { result = evaluate(parse(input)); }
        catch (ProjectionDomainRejection error) {
            if (error.getCause() instanceof ContractViolationException original) { throw original; }
            throw error;
        }
        return StrictJson.canonical(result, StrictJson.OUTPUT_MAX_BYTES);
    }
    public static JsonNode evaluate(Request request) {
        Objects.requireNonNull(request); ObjectNode a = request.arguments;
        return switch (request.operation()) {
            case PRIORITY_EMERGENCY_LEVEL_V1 -> IntNode.valueOf(WarEmergencyBudget.priorityLevel(record(a.get("war"))));
            case OBSERVE_EMERGENCY_POLICY_V1 -> WarEmergencyBudget.observePolicy(record(a.get("snapshot")), record(a.get("priority")), a.get("root"), a.get("spending"));
            case VALID_SAVED_EMERGENCY_REVISION_V1 -> WarEmergencyBudget.validSavedRevision(record(a.get("selected")), a.get("source_frame"), record(a.get("snapshot")));
            case EMERGENCY_QUOTE_BUDGET_V1 -> WarEmergencyBudget.quote(record(a.get("snapshot")), record(a.get("policy")), a.get("focus"),
                record(a.get("local")), a.get("troops"), a.get("price"), a.get("contract_months"), a.get("root"), record(a.get("normal_finance")), record(a.get("package")));
            case OBSERVE_EMERGENCY_RECOVERY_V1 -> WarEmergencyBudget.recovery(record(a.get("snapshot")), record(a.get("ledger")), a.get("root"));
        };
    }
}
