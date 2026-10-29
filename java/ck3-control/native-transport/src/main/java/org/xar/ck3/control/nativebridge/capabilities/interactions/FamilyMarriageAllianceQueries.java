package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding.Authority;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding.Selection;
import org.xar.ck3.control.application.planning.family.FamilyPorts.Query;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageResults.*;

/** Three distinct source-qualified native reads, sharing the complete alliance codec and original material authority. */
public final class FamilyMarriageAllianceQueries {
    private FamilyMarriageAllianceQueries() { }
    public record Definitions(ExactRef family,ExactRef matrilineal,ExactRef defaultAlliance){
        public Definitions{for(ExactRef ref:List.of(family,matrilineal,defaultAlliance))need(ref.bytes()>0,"actual native alliance producer definition required");}
    }
    public record Contracts(ReadContract<Obj> family,ReadContract<Obj> matrilineal,ReadContract<Obj> defaultAlliance){
        public Contracts{for(ReadContract<Obj> c:List.of(family,matrilineal,defaultAlliance))Objects.requireNonNull(c);}
        public List<ReadContract<Obj>> all(){return List.of(family,matrilineal,defaultAlliance);}
        public ReadContract<Obj> forRoute(Route route){return switch(route){case FAMILY->family;case MATRILINEAL->matrilineal;case DEFAULT->defaultAlliance;};}
    }
    public record Arguments(Context context,Resolved resolved,FamilyMarriageAlliance.Binding binding,FamilyDomainReadBinding originalDomain,Obj canonical){
        public Arguments{Objects.requireNonNull(context);Objects.requireNonNull(resolved);Objects.requireNonNull(binding);Objects.requireNonNull(originalDomain);Objects.requireNonNull(canonical);}
    }
    public static Contracts contracts(Definitions definitions,Authority authority){
        Objects.requireNonNull(definitions);Objects.requireNonNull(authority);
        return new Contracts(contract(Route.FAMILY,definitions.family(),authority),contract(Route.MATRILINEAL,definitions.matrilineal(),authority),contract(Route.DEFAULT,definitions.defaultAlliance(),authority));
    }
    public static String contractId(Route route){return "family/alliance/"+route.name().toLowerCase(java.util.Locale.ROOT)+"/v1";}
    public static String permission(Route route){return switch(route){case FAMILY->"source_qualified_first_heir_marriage_alliance_result_v1";case MATRILINEAL->"source_qualified_player_child_matrilineal_alliance_result_v1";case DEFAULT->"source_qualified_player_child_default_alliance_result_v1";};}
    public static Query query(Route route){return switch(route){case FAMILY->Query.FAMILY_ALLIANCE;case MATRILINEAL->Query.MATRILINEAL_ALLIANCE;case DEFAULT->Query.DEFAULT_ALLIANCE;};}
    public static Slot slot(Route route){return switch(route){case FAMILY->Slot.FAMILY;case MATRILINEAL->Slot.CHILD_MATRILINEAL;case DEFAULT->Slot.DEFAULT_MARRIAGE;};}
    private static ReadContract<Obj> contract(Route route,ExactRef source,Authority authority){
        return new ReadContract<>(contractId(route),query(route).operation(),Optional.empty(),permission(route),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
            ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(request,id)->{
                Arguments arguments=arguments(request,route);verifyCurrent(authority,request,arguments);
                return new NativeRequest(FamilyMarriageAlliance.step(route),Optional.empty(),nativeFields(arguments.binding()));
            },receipt->decodeOriginal(receipt,route,authority),receipt->decodeOriginal(receipt,route,authority));
    }
    /** Root calls its same-writer canonicalArguments first, then passes that exact result with the actual projected context. */
    public static Obj canonicalArguments(Context context,Obj domainCanonicalFlat){
        Objects.requireNonNull(context);ObjectNode flat=object(OpportunityJson.toNode(domainCanonicalFlat));
        closed(flat,"expected_revision","resolved","original_domain");eq(flat,"expected_revision",context.before().frame().revision());
        object(field(flat,"resolved"));FamilyDomainReadBinding.fromJson(application(object(field(flat,"original_domain"))));ObjectNode body=InteractionArguments.body(context);
        for(String name:List.of("expected_revision","resolved","original_domain"))body.set(name,field(flat,name));return application(body);
    }
    public static Arguments arguments(PlanningReadRequest request,Route route){
        need(request.operation().equals(query(route).operation()),"alliance registered operation differs");Context context=InteractionArguments.context(request);
        ObjectNode body=InteractionArguments.parseApp(request.arguments());closed(body,"group_context","expected_revision","resolved","original_domain");
        eq(body,"expected_revision",request.before().frame().revision());object(field(body,"original_domain"));
        Obj resolvedBody=application(object(field(body,"resolved")));Resolved resolved=FamilyMarriageResults.decodeResolved(route,resolvedBody);
        FamilyDomainReadBinding originalDomain=FamilyDomainReadBinding.fromJson(application(object(field(body,"original_domain"))));
        need(originalDomain.slot()==slot(route),"alliance original resolved domain slot differs from its exact route");
        need(context.build()==Build.CROZIER4&&request.source().exactBuild().equals(context.build().version()),"live/replayed native alliance contract requires its original exact current .4 source");
        need(context.controls().paused()&&context.controls().mapReady()&&context.controls().alive(),"alliance requires original paused living map controls");
        return new Arguments(context,resolved,FamilyMarriageAlliance.binding(context,resolved),originalDomain,request.arguments());
    }
    /** The shared EXECUTE_STEP transport supplies expected_revision from the actual request; additional fields cannot replace it. */
    public static RawJson nativeFields(FamilyMarriageAlliance.Binding binding){
        ObjectNode fields=F.objectNode().put("played_character_id",binding.actor())
            .put("recipient_character_id",binding.recipient()).put("heir_character_id",binding.subject()).put("candidate_character_id",binding.candidate());return encode(fields);
    }
    public static FamilyMarriageAlliance.Observation typedOriginal(PlanningReadReceipt receipt,Route route,Authority authority){
        Objects.requireNonNull(receipt);Arguments args=arguments(receipt.request(),route);need(receipt.contractId().equals(contractId(route))&&receipt.original().nativeOk()&&receipt.original().originalResultToken().isPresent(),"actual successful installed alliance receipt/token required");
        for(var guard:List.of(receipt.before(),receipt.after()))need(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
            &&guard.binding().source().equals(receipt.request().source())&&guard.binding().sessionId().equals(receipt.request().sessionId())
            &&guard.binding().operation().equals(query(route).operation())&&guard.binding().observed().equals(receipt.request().before())
            &&guard.binding().connectionGeneration().equals(args.context().connectionGeneration()),"alliance original paused actor/source/frame drift");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
            &&receipt.before().binding().authorityId().equals(receipt.after().binding().authorityId())
            &&receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()),"alliance original before/after authority or connection drift");
        JsonNode originalFrame=parse(receipt.original().originalFrame());closed(originalFrame,"type","protocol_version","request_id","ok","result");
        eq(originalFrame,"type","command_result");eq(originalFrame,"protocol_version",java.math.BigInteger.ONE);eq(originalFrame,"request_id",receipt.requestId());yes(originalFrame,"ok");
        need(field(originalFrame,"result").equals(result(receipt)),"alliance original frame differs from its actual retained result token");
        try{authority.verifyOriginal(receipt,args.originalDomain(),Selection.RESOLVED,args.resolved().original());}catch(IOException failure){throw new UncheckedIOException(failure);}
        return FamilyMarriageAlliance.decodeNative(receipt.original().originalResultToken().orElseThrow(),args.binding());
    }
    /** Pure original-read replay: no current-state lookup, native query, proposal submit or material mutation. */
    public static Obj decodeOriginal(PlanningReadReceipt receipt,Route route,Authority authority){return FamilyMarriageAlliance.project(typedOriginal(receipt,route,authority));}
    private static void verifyCurrent(Authority authority,PlanningReadRequest request,Arguments args){
        try{authority.verifyCurrent(request,args.originalDomain(),Selection.RESOLVED,args.resolved().original());}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static Obj application(ObjectNode value){return DriverJson.object(value.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
}
