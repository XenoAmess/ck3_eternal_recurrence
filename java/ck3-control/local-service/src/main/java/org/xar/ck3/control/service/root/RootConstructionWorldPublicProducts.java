package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;

/** The original public material-world query over the identical pre-Core Finance construction read. No ledger or new domain. */
public final class RootConstructionWorldPublicProducts {
    public static final String NAME="ck3_query_domain_construction_world_private_v1";
    private RootConstructionWorldPublicProducts() { }
    public record Request(BigInteger expectedRevision) {
        public Request {PublicUnsigned64.canonical(Objects.requireNonNull(expectedRevision),PublicUnsigned64.Minimum.ONE);}
    }
    public record Response(RawJson originalMemory) {
        public Response {Objects.requireNonNull(originalMemory);PublicDataJson.object(originalMemory);}
    }
    @FunctionalInterface interface Current {Response read(Request request)throws InterruptedException;}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef source=context.source(RootConstructionWorldPublicProducts.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,FinanceReadContracts.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,PublicDataJson.class);
        context.source(RootRuntimeSelectedSources.Module.CONTRACTS,NativeCharacterId.class);
        context.sourceAt("wave3-development/src/main/java/org/xar/ck3/control/wave3/development/constructionquery/ConstructionQueryCodec.java",ConstructionQueryCodec.class);
        var sameConstruction=context.definitions().construction();
        var binding=binding(source,request->{
            var deadline=context.clock().instant().plus(context.observationTimeout());
            try {return context.withCurrent(root->{
                var installed=context.installed(root);var actual=installed.context();
                if(context.definitions().construction()!=sameConstruction)throw new IOException("public world query lost the identical actual construction Sources");
                var definitions=actual.finance().definitions();var contract=definitions.contract(FinanceReadContracts.Query.CONSTRUCTION);
                if(!actual.readCatalog().containsIdentity(contract))throw new IOException("public world query lacks the same pre-Core source-qualified construction contract");
                return root.withPublicObservation(deadline,(before,known,same)->{
                    requireFrame(before.semantic(),request);
                    var query=new PlanningReadRequest(before.identity(),before.source(),before.sessionId(),contract.operation(),new Obj(java.util.Map.of()),deadline);
                    var result=actual.reads().read(same,contract,query);
                    if(!(result instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> available))
                        throw new IOException("actual native construction world unavailable: "+((PlanningReadResult.Unavailable<FinanceReadContracts.Packet>)result).reason());
                    var packet=available.value();var replay=definitions.decodeOriginal(FinanceReadContracts.Query.CONSTRUCTION,available.receipt(),before.semantic());
                    StrictJson.require(packet.receipt().equals(available.receipt())&&packet.receipt().request().equals(query)
                            &&replay.result().equals(packet.result())&&replay.originalResult().equals(packet.originalResult()),"construction world changed the exact original native packet/decoder");
                    Obj ending=actual.collector().currentHeldRead(same,query,lease->lease.frame().semantic());
                    return finalizeOriginal(request,before.semantic(),ending,new RawJson(packet.originalFrame()),packet.receipt().requestId());
                });
            });}catch(IOException failure){throw new UncheckedIOException(failure);}
        });
        return new RootPublicHandlerProductsFactory.Contribution(List.of(binding),List.of(),List.of());
    }
    static McpExecutableDirectory.DirectBinding<Request,Response> binding(ExactRef source,Current current) {
        return new McpExecutableDirectory.DirectBinding<>(NAME,PublicMcpBindings.Kind.DRIVER_DIRECT,Request.class,Response.class,current::read,
                call->decode(call.arguments().objectOrEmpty()),response->CallResult.fromBusinessJson(encode(response)),
                new PublicRoutes.Target(RootConstructionWorldPublicProducts.class.getName(),"query_domain_construction_world_private_v1",source));
    }
    static Request decode(RawJson arguments) {
        var n=PublicDataJson.object(arguments);StrictJson.require(n.size()==1&&n.has("expected_revision"),"construction world requires exactly expected_revision");
        return new Request(PublicUnsigned64.parse(n.get("expected_revision"),PublicUnsigned64.Minimum.ONE,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL));
    }
    static void requireFrame(Obj snapshot,Request request) {
        var n=OpportunityJson.toNode(snapshot);var played=n.get("played_character");
        StrictJson.require(played!=null&&played.isObject(),"actual observed played character object required");
        NativeCharacterId.fromJson(played.get("character_id"));
        StrictJson.require(n.path("paused").isBoolean()&&n.path("paused").booleanValue()&&n.path("map_ready").isBoolean()&&n.path("map_ready").booleanValue()
                &&n.has("active_event")&&n.get("active_event").isNull()&&n.has("pending_character_interaction")&&n.get("pending_character_interaction").isNull()
                &&n.path("active_wars").isArray()&&n.path("player_armies").isArray()&&played!=null&&played.isObject()
                &&played.path("alive").isBoolean()&&played.get("alive").booleanValue()
                &&n.path("native_revision").isIntegralNumber()&&n.get("native_revision").bigIntegerValue().signum()>0
                &&n.path("snapshot_id").isTextual()&&n.get("snapshot_id").textValue().equals("native:"+n.get("native_revision").bigIntegerValue())
                &&n.path("revision").isIntegralNumber()&&n.get("revision").bigIntegerValue().equals(request.expectedRevision())
                &&n.path("date_raw").isIntegralNumber()&&n.path("episode_run_id").isTextual(),"construction world lacks the original stable admitted paused actor frame");
    }
    /** Reuses the existing full original material-query algorithm, including mode3 and source_red. */
    static Response finalizeOriginal(Request request,Obj before,Obj after,RawJson nativeEnvelope,String originalRequestId) {
        requireFrame(before,request);
        var fields=new java.util.LinkedHashMap<String,Value>();fields.put("schema",new Text(ConstructionQueryCodec.SCHEMA));fields.put("starting_snapshot",before);fields.put("ending_snapshot",after);
        fields.put("native_envelope",DriverJson.object(nativeEnvelope.bytes(),ConstructionQueryCodec.MAX_BYTES));fields.put("expected_revision",new IntegerValue(request.expectedRevision()));fields.put("native_query_request_id",new Text(originalRequestId));fields.put("material_receipt",new Bool(true));fields.put("wartime_observation",new Bool(false));
        RawJson finalized=new RawJson(ConstructionQueryCodec.finalizeObservation(DriverJson.encode(new Obj(fields))));
        var value=PublicDataJson.object(finalized);StrictJson.require(Set.of("material_source","source_red").contains(value.path("status").asText()),"original material-world query did not produce a bound source result");
        return new Response(finalized);
    }
    private static final Set<String> U64=Set.of("revision","native_revision","snapshot_revision","proof_epoch","player_identity","holding_province_identity","province_identity","context_identity","model_identity","storage_identity","data_identity","capture_sequence","query_sequence");
    private static final Set<String> I64=Set.of("player_gold_raw","native_province_monthly_income_raw","native_remaining_work_raw","native_progress_divisor_raw","conditional_aggregate_raw","raw_q64","loaded_key_3f_raw","loaded_publisher_718_raw","owner_factor_raw","factor_before_context","context_factor_raw");
    private static final Set<String> VECTOR=Set.of("cost_raw_native","values_q64");
    public static RawJson encode(Response response) {var n=PublicDataJson.object(response.originalMemory()).deepCopy();project(n,false);return PublicDataJson.encode(n);}
    static Response restore(RawJson wire) {var n=PublicDataJson.object(wire).deepCopy();project(n,true);var response=new Response(PublicDataJson.encode(n));StrictJson.require(encode(response).equals(wire),"noncanonical construction world public representation");return response;}
    private static void project(JsonNode n,boolean restore) {
        if(n instanceof ObjectNode object){var keys=new java.util.ArrayList<String>();object.fieldNames().forEachRemaining(keys::add);for(String key:keys){JsonNode v=object.get(key);if(v.isNull())continue;
            if(U64.contains(key)){if(v.isTextual()&&v.textValue().matches("0[xX][0-9a-fA-F]+"))continue;if(restore)object.put(key,PublicUnsigned64.parse(v,PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.DECIMAL_ONLY));else object.put(key,PublicUnsigned64.canonical(integer(v),PublicUnsigned64.Minimum.ZERO));}
            else if(I64.contains(key)){if(restore)object.put(key,decimal(v));else object.put(key,integer(v).toString());}
            else if(VECTOR.contains(key)){StrictJson.require(v instanceof ArrayNode,"original construction numeric vector required");var a=(ArrayNode)v;for(int i=0;i<a.size();i++)if(!a.get(i).isNull()){if(restore)a.set(i,StrictJson.object().numberNode(decimal(a.get(i))));else a.set(i,StrictJson.object().textNode(integer(a.get(i)).toString()));}}
            else if(v.isIntegralNumber())StrictJson.require(v.bigIntegerValue().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"unclassified unsafe construction world integer at "+key);
            else project(v,restore);
        }}else if(n.isArray())for(var child:n)project(child,restore);
    }
    private static BigInteger integer(JsonNode n){StrictJson.require(n.isIntegralNumber(),"exact construction integer required");return n.bigIntegerValue();}
    private static BigInteger decimal(JsonNode n){StrictJson.require(n.isTextual()&&n.textValue().matches("0|-?[1-9][0-9]*"),"canonical construction integer text required");return new BigInteger(n.textValue());}
}
