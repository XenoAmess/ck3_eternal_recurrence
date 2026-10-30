package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageResults.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Three actual source-qualified read contracts. Archive replay never invokes live admission or a native query. */
public final class FamilyMarriageResultQueries {
    /** Root delegates these to the single typed FamilyDomainReadBinding.Authority, under its held writer. */
    public interface Authority {
        void verifyCurrent(PlanningReadRequest request,Route route,Obj canonicalArguments);
        void verifyOriginal(PlanningReadReceipt receipt,Route route,Obj canonicalArguments);
    }
    public interface Originals { PlanningReadReceipt loadRead(ExactRef originalReceipt); ExactRef referenceOf(PlanningReadReceipt original); }
    public record Sources(ExactRef family,ExactRef child) {
        public Sources {Objects.requireNonNull(family);Objects.requireNonNull(child);need(family.bytes()>0&&child.bytes()>0,"actual result source refs required");}
        public ExactRef forRoute(Route route){return route==Route.FAMILY?family:child;}
    }
    public record Arguments(Pending pending,boolean cold,boolean materialRecheck,Optional<ExactRef> coldOriginalRead,Obj original) {
        public Arguments {Objects.requireNonNull(pending);Objects.requireNonNull(coldOriginalRead);Objects.requireNonNull(original);need(cold==coldOriginalRead.isPresent(),"only cold result carries its actual relationship read");need(!materialRecheck||cold,"material recheck must be cold");}
    }
    public record Definitions(ReadContract<Obj> family,ReadContract<Obj> matrilineal,ReadContract<Obj> defaults) {
        public Definitions {Objects.requireNonNull(family);Objects.requireNonNull(matrilineal);Objects.requireNonNull(defaults);}
        public ReadContract<Obj> forRoute(Route route){return switch(route){case FAMILY->family;case MATRILINEAL->matrilineal;case DEFAULT->defaults;};}
        public List<ReadContract<Obj>> all(){return List.of(family,matrilineal,defaults);}
    }
    private final Authority authority;
    private final FamilyRootBinding.Originals roots;
    private final Originals originals;
    private final ReadContract<Obj> actualChildSubject;
    private final Definitions definitions;
    public FamilyMarriageResultQueries(Sources sources,Authority authority,FamilyRootBinding.Originals roots,
            Originals originals,ReadContract<Obj> actualChildSubject) {
        this.authority=Objects.requireNonNull(authority);this.roots=Objects.requireNonNull(roots);this.originals=Objects.requireNonNull(originals);
        this.actualChildSubject=Objects.requireNonNull(actualChildSubject);
        need(actualChildSubject.operation().value().equals(FamilyChildMarriageSubject.STEP)&&actualChildSubject.hasPureReplay(),"result must share the installed complete child subject/replay producer");
        definitions=new Definitions(contract(Route.FAMILY,sources),contract(Route.MATRILINEAL,sources),contract(Route.DEFAULT,sources));
    }
    public Definitions definitions(){return definitions;}
    public static String contractId(Route route){return "interactions:family-marriage-result:"+route.name().toLowerCase(java.util.Locale.ROOT);}
    private ReadContract<Obj> contract(Route route,Sources sources) {
        return new ReadContract<>(contractId(route),new OperationKey(route.step()),Optional.empty(),route.permission(),
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                sources.forRoute(route),(request,requestId)->{
                    Context c=InteractionArguments.context(request);Arguments args=arguments(route,request.arguments(),c);
                    authority.verifyCurrent(request,route,request.arguments());verifyColdProof(args,c,Optional.empty());
                    return new NativeRequest(route.step(),Optional.empty(),nativeFields(c,args.pending(),args.cold()));
                },receipt->decode(route,receipt),receipt->replay(route,receipt));
    }
    /** Root first adds its original_domain binding and, when cold, executes the actual root/child producer. */
    public static Obj canonicalArguments(Context context,Obj domainBoundFlat,Optional<ExactRef> actualColdRead) {
        Objects.requireNonNull(context);Objects.requireNonNull(actualColdRead);
        ObjectNode flat=InteractionArguments.parseApp(domainBoundFlat);
        need(flat.has("original_domain"),"result canonical arguments require the actual Root domain binding");
        need(!flat.has("group_context")&&!flat.has("cold_original_read"),"result canonical context/proof already supplied");
        ObjectNode out=InteractionArguments.body(context);out.setAll(flat);
        if(actualColdRead.isPresent())InteractionArguments.ref(out.putObject("cold_original_read"),actualColdRead.orElseThrow());else out.putNull("cold_original_read");
        Obj value=InteractionArguments.app(out);Route route=routeForPending(object(field(out,"pending")));arguments(route,value,context);return value;
    }
    public static Arguments arguments(Route route,Obj original,Context context) {
        ObjectNode n=InteractionArguments.parseApp(original);
        var expected=new java.util.HashSet<>(List.of("pending","cold","expected_revision","original_domain","group_context","cold_original_read"));
        if(n.has("material_recheck"))expected.add("material_recheck");closed(n,expected);
        eq(n,"expected_revision",context.before().frame().revision());
        // Only the shared Root FamilyDomainReadBinding codec interprets original_domain; Authority consumes that one codec.
        FamilyDomainReadBinding domain=FamilyDomainReadBinding.fromJson(InteractionArguments.app(object(field(n,"original_domain"))));
        need(domain.slot()==switch(route){case FAMILY->Slot.FAMILY;case MATRILINEAL->Slot.CHILD_MATRILINEAL;case DEFAULT->Slot.DEFAULT_MARRIAGE;},"result original domain slot differs from route");
        Pending pending=decodePending(route,InteractionArguments.app(object(field(n,"pending"))));
        boolean cold=bool(n,"cold"),recheck=n.has("material_recheck")&&bool(n,"material_recheck");
        Optional<ExactRef> proof=field(n,"cold_original_read").isNull()?Optional.empty():Optional.of(InteractionArguments.ref(field(n,"cold_original_read")));
        requireFrame(context,pending,cold);return new Arguments(pending,cold,recheck,proof,original);
    }
    public Obj decode(Route route,PlanningReadReceipt receipt) {return interpret(route,receipt);}
    public Obj replay(Route route,PlanningReadReceipt receipt) {return interpret(route,receipt);}
    private Obj interpret(Route route,PlanningReadReceipt receipt) {
        Context c=guard(route,receipt);Arguments args=arguments(route,receipt.request().arguments(),c);
        authority.verifyOriginal(receipt,route,receipt.request().arguments());verifyColdProof(args,c,Optional.of(receipt.before().binding().observedAt()));
        Observation observation=FamilyMarriageResults.decode(receipt.original().originalResultToken().orElseThrow(),c,args.pending(),args.cold());
        ObjectNode result=object(OpportunityJson.toNode(project(observation,c)));
        result.put("queried_snapshot_id",c.before().frame().snapshotId()).put("queried_revision",c.before().frame().revision()).put("queried_native_revision",c.revision());
        return InteractionArguments.app(result);
    }
    private void verifyColdProof(Arguments args,Context c,Optional<java.time.Instant> resultObservedAt) {
        if(!args.cold())return;
        ExactRef reference=args.coldOriginalRead().orElseThrow();
        if(args.pending().route()==Route.FAMILY) {
            var root=Objects.requireNonNull(roots.read(reference));need(root.originalReceipt().equals(reference),"cold first-heir archive returned a different original");
            requireProofChronology(root.receipt(),resultObservedAt);
            var binding=FamilyRootBinding.fromOriginal(root,c).binding();
            need(binding.observedFirstHeir().isPresent()&&BigInteger.valueOf(binding.observedFirstHeir().getAsLong()).equals(args.pending().subjectCharacterId()),
                    "cold result changed actual primary first heir");
        } else {
            PlanningReadReceipt original=Objects.requireNonNull(originals.loadRead(reference));
            need(originals.referenceOf(original).equals(reference),"cold child archive custody differs from its exact original reference");
            requireProofChronology(original,resultObservedAt);
            need(original.contractId().equals(actualChildSubject.contractId())&&original.request().operation().equals(actualChildSubject.operation()),"cold child proof is not the identical installed subject route");
            need(original.request().before().equals(c.before())&&original.request().source().equals(c.source())&&original.request().sessionId().equals(c.sessionId()),"cold child proof crossed source/session/frame");
            Context originalContext=InteractionArguments.context(original.request());
            need(originalContext.build()==c.build()&&originalContext.connectionGeneration().equals(c.connectionGeneration())&&originalContext.controls().equals(c.controls()),"cold child proof differs from actual control/build/connection context");
            var child=FamilyChildMarriageQueries.decodeSubject(original);
            need(child.availability().available()&&child.fields().childVerified()&&child.binding().subject()==args.pending().subjectCharacterId().intValueExact(),"cold child proof lacks actual verified child");
            Obj projected=actualChildSubject.replay(original);JsonNode value=OpportunityJson.toNode(projected);
            eq(value,"schema",FamilyChildMarriageSubject.SCHEMA);eq(value,"status","available");yes(value,"player_child_verified");
            eq(value,"played_character_id",c.actor());eq(value,"subject_character_id",args.pending().subjectCharacterId());eq(value,"native_revision",c.revision());
        }
    }
    private static void requireProofChronology(PlanningReadReceipt proof,Optional<java.time.Instant> resultObservedAt) {
        if(resultObservedAt.isPresent())need(!proof.after().binding().observedAt().isAfter(resultObservedAt.orElseThrow()),"cold relationship proof query postdates the original result query");
    }
    private static Context guard(Route route,PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);PlanningReadRequest request=receipt.request();Context c=InteractionArguments.context(request);
        need(receipt.contractId().equals(contractId(route))&&request.operation().value().equals(route.step())&&receipt.original().nativeOk(),"original source-qualified result contract differs");
        need(c.source().exactBuild().equalsIgnoreCase(c.build().sha256()),"result context source SHA differs");
        for(var guard:List.of(receipt.before(),receipt.after()))need(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
                &&guard.binding().observed().equals(c.before())&&guard.binding().source().equals(c.source())&&guard.binding().sessionId().equals(c.sessionId())
                &&guard.binding().operation().equals(request.operation())&&guard.binding().connectionGeneration().equals(c.connectionGeneration()),
                "result original guards differ from actual paused map/frame/source");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"result original read guard changed");
        JsonNode frame=parse(receipt.original().originalFrame());closed(frame,"type","protocol_version","request_id","ok","result");
        eq(frame,"type","command_result");eq(frame,"protocol_version",BigInteger.ONE);eq(frame,"request_id",receipt.requestId());yes(frame,"ok");
        need(field(frame,"result").equals(result(receipt)),"result original frame differs from exact retained result token");
        return c;
    }
    private static Route routeForPending(JsonNode pending) {
        String schema=text(pending,"schema");for(Route route:Route.values())if(route.schema().equals(schema))return route;
        throw new IllegalArgumentException("unknown actual family result pending schema");
    }
}


