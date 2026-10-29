package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Arrays;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original parsed UI request/result plus complete before DATA; no source or effect authority. */
public final class NativeUiParsedReturn {
    private NativeUiParsedReturn() { }
    public static final String SCHEMA = "xar.ck3.native-ui-original-parsed-return/v1";
    /** Whole UTF-8 wrapper, including both original payloads and full before. Never a per-part allowance. */
    public static final int MAXIMUM_ARTIFACT_BYTES = RawJson.MAXIMUM_BYTES;
    private static final Set<String> FIELDS = Set.of("schema", "validation_state", "wire_bytes_preserved", "request",
            "original_parsed_command_result", "actual_pre_submission_snapshot");
    private static final Set<String> STEPS = Set.of("navigate-ingame-ui-v1", "query-ingame-ui-window-v1");

    /** The explicit complete-material lane retains long numeric and decimal tokens from the full before. */
    public static RawJson encode(byte[] originalRequestPacket, byte[] originalResultPacket,
            OpportunityJson.Obj actualPreSubmissionSnapshot) throws IOException {
        Objects.requireNonNull(actualPreSubmissionSnapshot);
        var request = NativeWire.decodeExecuteRequest(originalRequestPacket);
        var parsed = NativeWire.decode(originalResultPacket);
        StrictJson.require(STEPS.contains(request.step()), "original UI parsed-return record belongs only to its two exact native steps");
        StrictJson.require(parsed instanceof NativeWire.CommandResult, "original UI parsed command_result required");
        var result = (NativeWire.CommandResult) parsed;
        StrictJson.require(result.requestId().equals(request.requestId()), "original UI parsed-return request/result identity differs");
        OpportunityJson.Obj requestBody = DriverJson.object(Arrays.copyOfRange(originalRequestPacket, Integer.BYTES,
                originalRequestPacket.length), MAXIMUM_ARTIFACT_BYTES);
        OpportunityJson.Obj resultBody = DriverJson.object(result.payload().value(), MAXIMUM_ARTIFACT_BYTES);
        var body = new OpportunityJson.Obj(Map.of(
                "schema", new OpportunityJson.Text(SCHEMA),
                "validation_state", new OpportunityJson.Text("unvalidated"),
                "wire_bytes_preserved", new OpportunityJson.Bool(false),
                "request", requestBody,
                "original_parsed_command_result", resultBody,
                "actual_pre_submission_snapshot", actualPreSubmissionSnapshot));
        RawJson encoded = PublicDataJson.encodeFullMaterial(body);
        StrictJson.require(encoded.bytes().length <= MAXIMUM_ARTIFACT_BYTES,
                "complete original UI parsed-return exceeds its finite whole-artifact capacity");
        return encoded;
    }

    /** Sole complete-material wrapper parser. Original Native request/result admission remains independent. */
    public static OpportunityJson.Obj decode(byte[] actualArtifact) {
        RawJson material = RawJson.fullMaterial(Objects.requireNonNull(actualArtifact));
        StrictJson.require(material.bytes().length <= MAXIMUM_ARTIFACT_BYTES, "UI parsed-return artifact exceeds whole capacity");
        OpportunityJson.Obj body = DriverJson.object(material.bytes(), MAXIMUM_ARTIFACT_BYTES);
        StrictJson.require(body.members().keySet().equals(FIELDS), "exact complete UI parsed-return wrapper fields required");
        StrictJson.require(SCHEMA.equals(OpportunityJson.text(body.get("schema"), "schema"))
                && "unvalidated".equals(OpportunityJson.text(body.get("validation_state"), "validation_state")),
                "original unvalidated UI parsed-return wrapper required");
        StrictJson.require(body.get("wire_bytes_preserved") instanceof OpportunityJson.Bool preserved && !preserved.value(),
                "parsed UI wrapper cannot claim original wire-byte preservation");
        OpportunityJson.Obj request = OpportunityJson.object(body.get("request"), "request");
        OpportunityJson.Obj result = OpportunityJson.object(body.get("original_parsed_command_result"), "original_parsed_command_result");
        OpportunityJson.object(body.get("actual_pre_submission_snapshot"), "actual_pre_submission_snapshot");
        StrictJson.require(STEPS.contains(OpportunityJson.text(request.get("step"), "step")), "foreign parsed UI step");
        StrictJson.require(OpportunityJson.text(request.get("request_id"), "request_id")
                .equals(OpportunityJson.text(result.get("request_id"), "request_id")), "parsed UI wrapper request/result identity differs");
        return body;
    }

    /** Exact public parsed-return artifact role; canonical ACK references remain separate. */
    public static ObjectNode reference(ExactRef preserved) {
        Objects.requireNonNull(preserved);
        StrictJson.require(preserved.bytes() > 0 && preserved.bytes() <= MAXIMUM_ARTIFACT_BYTES,
                "parsed UI artifact reference exceeds its declared whole capacity");
        ObjectNode result = preserved.toJson(); result.put("validation_state", "unvalidated"); return result;
    }
}
