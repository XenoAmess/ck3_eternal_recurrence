package org.xar.ck3.control.wave3.planning.datedsummary;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;

/** Same bounded collection domain as the full realm comparison, with exact numeric tokens. */
public final class DatedSummaryCodec {
    private DatedSummaryCodec() { }

    /** Immutable boundary values retain the original null, missing-wrapper refusal and decimal token domain. */
    public record Request(JsonNode feedback, JsonNode currentSourceFrame) {
        public Request {
            StrictJson.require(feedback != null && currentSourceFrame != null, "explicit feedback/current-source JSON values required");
            feedback = feedback.deepCopy(); currentSourceFrame = currentSourceFrame.deepCopy();
        }
        @Override public JsonNode feedback() { return feedback.deepCopy(); }
        @Override public JsonNode currentSourceFrame() { return currentSourceFrame.deepCopy(); }
    }
    public static Request decodeRequest(byte[] input) {
        ObjectNode object = StrictJson.object(parseValue(input), Set.of("feedback", "current_source_frame"));
        return new Request(object.get("feedback"), object.get("current_source_frame"));
    }
    public static DatedRealmSummary.Result projectRequest(Request request) {
        StrictJson.require(request != null, "typed dated summary request required");
        try { return DatedRealmSummary.project(request.feedback(), request.currentSourceFrame()); }
        catch (ContractViolationException refusal) { throw new ProjectionDomainRejection(refusal.getMessage()); }
    }
    public static DatedRealmSummary.Result decode(byte[] input) { return projectRequest(decodeRequest(input)); }
    public static byte[] evaluate(byte[] input) { return encode(decode(input)); }
    public static byte[] encode(DatedRealmSummary.Result result) {
        StrictJson.require(result != null, "typed dated summary required");
        byte[] raw = SdkProjectionJson.encode(stableOrder(result.toJson()), RealmDifferenceCodec.MAX_BYTES);
        parseValue(raw); return raw;
    }
    public static JsonNode parsedResult(DatedRealmSummary.Result result) { return parseValue(encode(result)); }

    // The same fact must have the same bytes before and after feedback serialization.
    // Order object keys only; keep array order and every scalar JSON token category.
    private static JsonNode stableOrder(JsonNode node) {
        if (node instanceof ObjectNode object) {
            ObjectNode result = StrictJson.object();
            TreeSet<String> names = new TreeSet<>();
            object.fieldNames().forEachRemaining(names::add);
            for (String name : names) { result.set(name, stableOrder(object.get(name))); }
            return result;
        }
        if (node instanceof ArrayNode array) {
            ArrayNode result = JsonNodeFactory.instance.arrayNode();
            for (JsonNode value : array) { result.add(stableOrder(value)); }
            return result;
        }
        return node;
    }

    static JsonNode parseValue(byte[] raw) { return StrictJson.parse(raw, RealmDifferenceCodec.MAX_BYTES); }

}

