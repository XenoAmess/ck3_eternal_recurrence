package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.prisoners.PrisonerOrdinaryPolicy12004;
import org.xar.ck3.control.application.planning.prisoners.PrisonerActionBinding12004;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Actual original public collection tool; registration retains source-bound ports and never requires a Core. */
public final class RootPrisonerPublicProducts {
    public static final String QUERY="ck3_query_player_prisoner_collection_private_v1";
    public static final String RANSOM="ck3_ransom_player_prisoner_private_v1";
    public static final String RELEASE="ck3_release_player_prisoner_private_v1";
    public record Query(BigInteger expectedRevision,int ransomOrdinal,PrisonerOptionIntent.Arguments intent) {
        public Query {Objects.requireNonNull(expectedRevision);Objects.requireNonNull(intent);
            StrictJson.require(expectedRevision.signum()>0&&expectedRevision.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"public revision must be an exact positive JS-safe integer");
            StrictJson.require(ransomOrdinal>=0&&ransomOrdinal<64,"public ransom ordinal must be 0..63");}
    }
    public record ActionRequest(RawJson collection,long prisonerCharacterId){public ActionRequest{Objects.requireNonNull(collection);
        StrictJson.require(prisonerCharacterId>0&&prisonerCharacterId<0xffff_ffffL,"valid full prisoner ID required");
        StrictJson.require(StrictJson.parse(collection.bytes(),1_048_576).isObject(),"original collection object required");}}
    private RootPrisonerPublicProducts() { }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);StrictJson.require(!registry.frozen(),"public registration is already frozen");
        ExactRef implementation=context.source(RootPrisonerPublicProducts.class);
        ExactRef collectionSource=context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,PrisonerNativeQueries.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,PrisonerActionBinding12004.class);
        context.source(PrisonerPublicPendingCodec12004.class);
        context.source(PrisonerPublicFailure12004.class);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(binding(implementation,request->read(context,collectionSource,request)),
                actionBinding(RANSOM,implementation,request->submit(context,request,PrisonerOrdinaryPolicy12004.RANSOM)),
                actionBinding(RELEASE,implementation,request->submit(context,request,PrisonerOrdinaryPolicy12004.RELEASE))),List.of(),definitionGaps());
    }
    public static RawJson read(RootPublicHandlerProductsFactory.Context context,ExactRef collectionSource,Query request)throws InterruptedException {
        Objects.requireNonNull(context);Objects.requireNonNull(collectionSource);Objects.requireNonNull(request);
        try {return context.withCurrent(root->{
            var actual=context.installed(root).prisoners();var contract=actual.nativeQueries().contract(request.ransomOrdinal());
            StrictJson.require(contract.sourceRef().equals(collectionSource)&&contract.hasPureReplay(),"public query must use the exact installed source-owned pure collection contract");
            var deadline=context.clock().instant().plus(context.observationTimeout());
            var result=root.readCurrent(contract,request.expectedRevision(),PrisonerNativeQueries.arguments(request.intent().options(),request.intent().materialTarget()),deadline);
            if(!(result instanceof PlanningReadResult.Known<RawJson> known)){
                var unavailable=(PlanningReadResult.Unavailable<RawJson>)result;
                throw PrisonerPublicFailure12004.read(unavailable,collectionSource,contract.operation(),deadline);
            }
            var normalized=contract.replay(known.receipt());StrictJson.require(normalized.equals(known.value()),"actual public collection producer/pure original parser differ");
            actual.retainPublicCollection(contract,known);
            return normalized;
        });}catch(IOException unavailable){throw PrisonerPublicFailure12004.local(PrisonerPublicFailure12004.Operation.COLLECTION,unavailable,List.of(collectionSource));}
    }
    public static RawJson submit(RootPublicHandlerProductsFactory.Context context,ActionRequest request,OperationKey operation)throws InterruptedException{
        Objects.requireNonNull(context);Objects.requireNonNull(request);PrisonerActionBinding12004.requireOperation(operation);
        var deadline=context.clock().instant().plus(context.actionTimeout());
        try{return context.withCurrent(root->{var actual=context.installed(root).prisoners();
            return root.executePublicDecision(deadline,
                    (frame,driver,same)->actual.publicDecision(same,frame,request.collection(),request.prisonerCharacterId(),operation,deadline),actual::presentPublic);
        });}catch(IOException failure){throw PrisonerPublicFailure12004.local(PrisonerPublicFailure12004.operation(operation),failure,List.of());}
        catch(IllegalArgumentException failure){throw PrisonerPublicFailure12004.local(PrisonerPublicFailure12004.operation(operation),failure,List.of());}
    }
    /** Public Python defaults null options/target to None; only this boundary deliberately removes those optional nulls. */
    public static Query decode(PublicMcpDirectory.Arguments arguments) {
        Objects.requireNonNull(arguments);StrictJson.require(arguments.presence()==PublicMcpDirectory.Presence.VALUE,"prisoner query requires named arguments including expected_revision");
        JsonNode parsed=StrictJson.parse(arguments.original().orElseThrow().bytes(),1_048_576);var required=new HashSet<String>();required.add("expected_revision");
        for(String optional:List.of("ransom_ordinal","release_option_keys","release_material_target_character_id"))if(parsed.has(optional))required.add(optional);
        ObjectNode row=StrictJson.object(parsed,required);
        BigInteger revision=StrictJson.integer(row.get("expected_revision"),BigInteger.ONE,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER));
        int ordinal=row.has("ransom_ordinal")?(int)StrictJson.integer(row.get("ransom_ordinal"),0,63):0;
        ObjectNode nativeIntent=StrictJson.object();
        for(String optional:List.of("release_option_keys","release_material_target_character_id"))if(row.hasNonNull(optional))nativeIntent.set(optional,row.get(optional));
        return new Query(revision,ordinal,PrisonerOptionIntent.decode(nativeIntent));
    }
    static McpExecutableDirectory.DirectBinding<Query,RawJson> binding(ExactRef actualSource,PublicRoutes.Handler<Query,RawJson> actual) {
        return new McpExecutableDirectory.DirectBinding<>(QUERY,PublicMcpBindings.Kind.DRIVER_DIRECT,Query.class,RawJson.class,Objects.requireNonNull(actual),
                call->decode(call.arguments()),PublicMcpDirectory.CallResult::fromBusinessJson,
                new PublicRoutes.Target(RootPrisonerPublicProducts.class.getName(),"read",Objects.requireNonNull(actualSource)));
    }
    public static ActionRequest decodeAction(PublicMcpDirectory.Arguments arguments){
        StrictJson.require(arguments.presence()==PublicMcpDirectory.Presence.VALUE,"prisoner action requires its collection and target");
        var row=StrictJson.object(StrictJson.parse(arguments.original().orElseThrow().bytes(),1_048_576),java.util.Set.of("collection","prisoner_character_id"));
        StrictJson.require(row.get("collection").isObject(),"original collection object required");
        return new ActionRequest(new RawJson(StrictJson.canonical(row.get("collection"),1_048_576)),StrictJson.integer(row.get("prisoner_character_id"),1,0xffff_fffeL));
    }
    static McpExecutableDirectory.DirectBinding<ActionRequest,RawJson> actionBinding(String name,ExactRef source,PublicRoutes.Handler<ActionRequest,RawJson> actual){
        StrictJson.require(name.equals(RANSOM)||name.equals(RELEASE),"exact original prisoner public action required");
        return new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,ActionRequest.class,RawJson.class,actual,
                call->decodeAction(call.arguments()),PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(RootPrisonerPublicProducts.class.getName(),"submit",source));
    }
    public static List<RootRuntimePublicCatalog.DefinitionGap> definitionGaps() {
        return List.of();
    }
}
