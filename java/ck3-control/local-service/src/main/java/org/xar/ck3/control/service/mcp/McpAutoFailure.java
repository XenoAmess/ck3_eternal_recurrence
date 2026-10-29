package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Bounded diagnostic projection of actual retained outbound/ACK bytes; it grants no retry or world credit. */
public final class McpAutoFailure extends RuntimeException {
    private final CallResult result;
    private McpAutoFailure(org.xar.ck3.control.application.session.AutoFailureDiagnostic actual) {
        super(actual.message());ObjectNode envelope=McpJson.object();
        envelope.putArray("content").addObject().put("type","text").put("text","Error executing tool ck3_auto_turn: "+actual.message());
        ObjectNode body=envelope.putObject("structuredContent").put("error_type",actual.kind().errorType());
        body.putObject("diagnostics").set(actual.kind().key(),McpJson.object(McpJson.parse(actual.diagnostic().bytes())));
        envelope.put("isError",true).put("resultType","complete");result=new CallResult(McpJson.encode(envelope));
    }
    public static McpAutoFailure fromDiagnostic(org.xar.ck3.control.application.session.AutoFailureDiagnostic actual,ActionReceipt receipt) {
        actual.require(receipt);return new McpAutoFailure(actual);
    }
    private McpAutoFailure(String message,ObjectNode diagnostic,Optional<ObjectNode> retry) {
        super(message);ObjectNode body=McpJson.object().put("error_type","NativeCommandRejectedError");
        ObjectNode diagnostics=body.putObject("diagnostics");diagnostics.set("native_command_rejection",diagnostic);
        retry.ifPresent(value -> diagnostics.set("campaign_root_readonly_retry_v1",value));
        ObjectNode envelope=McpJson.object();envelope.putArray("content").addObject().put("type","text").put("text","Error executing tool ck3_auto_turn: "+message);
        envelope.set("structuredContent",body);envelope.put("isError",true).put("resultType","complete");result=new CallResult(McpJson.encode(envelope));
    }
    public CallResult result() {return result;}
    /** UNKNOWN stays canonical UNKNOWN. Only a retained matched native false ACK can produce this diagnostic. */
    public static Optional<McpAutoFailure> fromReceipt(ActionReceipt actual) {
        Optional<AckReceived> ack=actual.ack();
        if(ack.isEmpty() || ack.orElseThrow().nativeOk() || ack.orElseThrow().outbound().isEmpty()) return Optional.empty();
        try {return Optional.of(fromAck(ack.orElseThrow()));}
        catch(IllegalArgumentException malformedOriginal) {return Optional.empty();}
    }
    static McpAutoFailure fromAck(AckReceived actual) {
        McpJson.require(!actual.nativeOk() && actual.outbound().isPresent(),"actual rejected ACK and retained outbound required");
        ObjectNode request=packet(actual.outbound().orElseThrow().originalPacket());ObjectNode response=packet(actual.originalPacket());
        McpJson.require(response.equals(McpJson.parse(actual.originalFrame().bytes())),"retained original ACK token/frame differs");
        McpJson.require(is(request,"type","execute_step") && one(request.get("protocol_version")) && is(request,"request_id",actual.requestId())
                && is(response,"type","command_result") && one(response.get("protocol_version")) && is(response,"request_id",actual.requestId())
                && response.has("ok") && response.get("ok").isBoolean() && !response.get("ok").booleanValue(),"retained rejection is not this exact request/protocol");
        var cut=new Cut();ObjectNode diagnostic=McpJson.object().put("diagnostic_only",true);
        nullableText(diagnostic,"native_request_id",cut.text(request.get("request_id"),160));
        nullableText(diagnostic,"native_step",cut.text(request.get("step"),96));
        JsonNode expected=request.get("expected_revision");
        if(uint64(expected))diagnostic.put("expected_native_revision",expected.bigIntegerValue().toString());else diagnostic.putNull("expected_native_revision");
        nullableText(diagnostic,"native_error",cut.text(response.get("error"),512));
        JsonNode thin=response.get("campaign_root_preflight_failure_v1");
        if(thin!=null) {
            List<String> predicates=List.of("revision_matches","worker_ready","previous_present","observed_read","observed_equal");
            boolean valid=thin.isObject() && is(thin,"query_type","campaign") && thin.path("stage").isTextual() && uint64(thin.get("request_native_revision"))
                    && uint64(thin.get("worker_native_revision")) && thin.path("predicates").isObject()
                    && predicates.stream().allMatch(field -> thin.get("predicates").path(field).isBoolean()) && thin.path("read_attempted").isBoolean()
                    && thin.path("truncated").isBoolean() && List.of("cached_scalars","observed_scalars","differing_fields").stream()
                    .allMatch(field -> thin.has(field) && (thin.get(field).isNull() || thin.get(field).isTextual()));
            if(valid) {
                ObjectNode projection=diagnostic.putObject("campaign_root_preflight_failure_v1").put("query_type","campaign");
                nullableText(projection,"stage",cut.text(thin.get("stage"),96));
                projection.put("request_native_revision",thin.get("request_native_revision").bigIntegerValue().toString());
                projection.put("worker_native_revision",thin.get("worker_native_revision").bigIntegerValue().toString());
                ObjectNode values=projection.putObject("predicates");predicates.forEach(field -> values.set(field,thin.get("predicates").get(field).deepCopy()));
                projection.set("read_attempted",thin.get("read_attempted").deepCopy());
                nullableText(projection,"cached_scalars",cut.opaque(thin.get("cached_scalars"),1536));
                nullableText(projection,"observed_scalars",cut.opaque(thin.get("observed_scalars"),1536));
                nullableText(projection,"differing_fields",cut.opaque(thin.get("differing_fields"),768));
                projection.set("truncated",thin.get("truncated").deepCopy());
                for(String optional:List.of("cached_scalars","observed_scalars","differing_fields"))
                    if(McpJson.encode(diagnostic).length>4096 && !projection.get(optional).isNull()) {projection.putNull(optional);cut.truncated=true;}
            } else diagnostic.put("thin_schema_invalid",true);
        }
        if(cut.truncated)diagnostic.put("projection_truncated",true);
        while(McpJson.encode(diagnostic).length>4096) {
            String error=diagnostic.path("native_error").asText("");McpJson.require(!error.isEmpty(),"finite rejection identity projection exceeds bound");
            diagnostic.put("native_error",cut.text(McpJson.parse(McpJson.quote(error)),Math.max(0,error.getBytes(StandardCharsets.UTF_8).length/2)));
            diagnostic.put("projection_truncated",true);
        }
        Optional<ObjectNode> retry=Optional.empty();
        String error=response.path("error").asText("");
        if(is(request,"step","query-campaign-root-context-v1") && Set.of("campaign-root snapshot changed or is not ready","application-main typed query failed or its snapshot changed").contains(error)
                && uint64(expected) && expected.bigIntegerValue().signum()>0 && actual.requestId().length()<=160) {
            retry=Optional.of(McpJson.object().put("schema","xar.campaign-root-readonly-retry-diagnostic/v1").put("diagnostic_only",true)
                    .put("status","evidence_absent").put("retry_authorized",false).put("source_native_revision",expected.bigIntegerValue().toString())
                    .put("evidence_truncated",false).put("evidence_meaning","no_supported_record; retry_entry_or_attempt_unknown"));
        }
        return new McpAutoFailure(error.isEmpty()?"native command rejected":error,diagnostic,retry);
    }
    private static ObjectNode packet(byte[] framed) {
        McpJson.require(framed.length>=5,"original framed packet required");int length=ByteBuffer.wrap(framed,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        McpJson.require(length>0 && length<=McpJson.BODY_MAX && framed.length==length+4,"exact original native packet length required");
        return McpJson.object(McpJson.parse(Arrays.copyOfRange(framed,4,framed.length)));
    }
    private static boolean one(JsonNode value) {return value!=null && value.isIntegralNumber() && value.bigIntegerValue().equals(java.math.BigInteger.ONE);}
    private static boolean uint64(JsonNode value) {return value!=null && value.isIntegralNumber() && value.bigIntegerValue().signum()>=0 && value.bigIntegerValue().bitLength()<=64;}
    private static boolean is(JsonNode row,String field,String value) {return row!=null && row.isObject() && row.has(field) && row.get(field).isTextual() && value.equals(row.get(field).textValue());}
    private static void nullableText(ObjectNode row,String field,String value) {if(value==null)row.putNull(field);else row.put(field,value);}
    private static final class Cut {
        boolean truncated;
        String text(JsonNode value,int bytes) {
            if(value==null || !value.isTextual()) return null;String original=value.textValue();StringBuilder out=new StringBuilder();int used=0;
            for(int offset=0;offset<original.length();) {int code=original.codePointAt(offset);String next=new String(Character.toChars(code));int size=next.getBytes(StandardCharsets.UTF_8).length;
                if(used+size>bytes) {truncated=true;break;}out.append(next);used+=size;offset+=Character.charCount(code);}
            return out.toString();
        }
        String opaque(JsonNode value,int bytes) {if(value==null || value.isNull())return null;if(!value.isTextual() || value.textValue().getBytes(StandardCharsets.UTF_8).length>bytes) {truncated=true;return null;}return value.textValue();}
    }
}
