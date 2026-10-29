package org.xar.ck3.control.warbudget.projection;

import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.warbudget.WarBudgetCodec;

/** Existing pure policy entry; this port supplies no native source, transport or submission authority. */
public final class WarBudgetProjectionPort implements ProjectionPort<WarBudgetCodec.Request, JsonNode> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.WAR_BUDGET_EVALUATE; }
    @Override public WarBudgetCodec.Request decode(byte[] rawPayload) { return WarBudgetCodec.parse(rawPayload); }
    @Override public JsonNode project(WarBudgetCodec.Request input) {
        try { return WarBudgetCodec.evaluate(input); }
        catch (ContractViolationException cause) {
            var rejection = new ProjectionDomainRejection(cause.getMessage());
            rejection.initCause(cause); throw rejection;
        }
    }
    @Override public byte[] encode(JsonNode result) { return StrictJson.canonical(result, outputMaximumBytes()); }
    @Override public int inputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
    @Override public int outputMaximumBytes() { return StrictJson.OUTPUT_MAX_BYTES; }
}
