package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Strict failed-read DATA encoding over the existing guard/request/outcome archive contracts. */
public final class PlanningReadFailureCodec {
    private static final String SCHEMA = "xar.planning-read-failure/v1";
    private PlanningReadFailureCodec() { }
    public static ExactRef preserve(PlanningReadFailure failure, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(failure); Objects.requireNonNull(archive);
        archive.verifyReadFailureOriginals(failure);
        var arguments = new RawJson(OpportunityJson.encode(failure.request().arguments()));
        ExactRef argumentsRef = archive.preserveMaterial(arguments);
        RawJson encoded = encode(failure, argumentsRef);
        ExactRef actual = archive.preserveMaterial(encoded);
        StrictJson.require(Arrays.equals(encoded.bytes(), archive.loadMaterial(actual).bytes()),
                "failed-read material did not retain its exact encoded bytes");
        return actual;
    }
    public static PlanningReadFailure load(ExactRef original, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(original); Objects.requireNonNull(archive);
        var raw = archive.loadMaterial(original);
        var row = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("schema", "request", "contract_id",
                "request_id", "before", "after", "original_ref", "prepared_ref", "head_sequence", "head_digest"));
        StrictJson.require(StrictJson.text(row.get("schema")).equals(SCHEMA), "exact failed-read DATA schema required");
        var requestNode = StrictJson.object(row.get("request"),
                Set.of("before", "source", "session_id", "operation", "deadline", "arguments_ref"));
        ExactRef argumentsRef = ExactRef.fromJson(requestNode.get("arguments_ref"));
        var arguments = OpportunityJson.object(OpportunityJson.parseComplete(archive.loadMaterial(argumentsRef).bytes(), PlanningReadRequest.MAX_ARGUMENT_BYTES),
                "actual failed-read arguments");
        ExactRef outcomeRef = ExactRef.fromJson(row.get("original_ref"));
        ExactRef preparedRef = ExactRef.fromJson(row.get("prepared_ref"));
        String sequence = StrictJson.text(row.get("head_sequence"));
        StrictJson.require(sequence.matches("0|[1-9][0-9]*"), "canonical decimal failed-read head sequence required");
        var result = new PlanningReadFailure(CommandOriginCodec.planningRequest(requestNode, arguments),
                StrictJson.text(row.get("contract_id")), StrictJson.text(row.get("request_id")),
                CommandOriginCodec.planningGuard(row.get("before")), CommandOriginCodec.planningGuard(row.get("after")),
                archive.loadRequest(preparedRef), archive.load(outcomeRef), outcomeRef, preparedRef,
                new BigInteger(sequence).longValueExact(), StrictJson.text(row.get("head_digest")));
        archive.verifyReadFailureOriginals(result);
        StrictJson.require(Arrays.equals(raw.bytes(), encode(result, argumentsRef).bytes()),
                "failed-read material is not its exact canonical request/guards/originals encoding");
        return result;
    }
    private static RawJson encode(PlanningReadFailure failure, ExactRef argumentsRef) {
        var row = StrictJson.object(); row.put("schema", SCHEMA);
        row.set("request", CommandOriginCodec.planningRequest(failure.request(), argumentsRef));
        row.put("contract_id", failure.contractId()); row.put("request_id", failure.requestId());
        row.set("before", CommandOriginCodec.planningGuard(failure.before()));
        row.set("after", CommandOriginCodec.planningGuard(failure.after()));
        row.set("original_ref", failure.originalRef().toJson()); row.set("prepared_ref", failure.preparedRef().toJson());
        row.put("head_sequence", Long.toString(failure.headSequence())); row.put("head_digest", failure.headDigest());
        return new RawJson(StrictJson.canonical(row));
    }
}
