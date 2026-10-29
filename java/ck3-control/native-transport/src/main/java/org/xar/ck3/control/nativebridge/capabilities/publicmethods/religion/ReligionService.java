package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionCapabilities.ReadKind;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;

/** Actual READ adapters over the existing typed Religion algorithms. No mutation, retry, or gameplay qualification is created here. */
public final class ReligionService {
    @FunctionalInterface public interface ReadAdmission { void verify(PlanningReadRequest request); }
    public interface Component {
        List<String> methods();
        Response invoke(Session borrowed,ActualFrame actual,Request request);
    }
    public record ExistingReads(PlayerReligionContextRead religion, PlayerHolyOrderContextRead holyOrders) {
        public ExistingReads { Objects.requireNonNull(religion);Objects.requireNonNull(holyOrders); }
    }
    public record FixedRead(ReadKind kind, ReadContract<?> contract) { public FixedRead {Objects.requireNonNull(kind);Objects.requireNonNull(contract);} }
    public record ActualFrame(Complete frame, NativeWire.Hello hello, Instant deadline) {
        public ActualFrame {
            Objects.requireNonNull(frame);Objects.requireNonNull(hello);Objects.requireNonNull(deadline);
            StrictJson.require(hello.pid()==frame.identity().game().pid()&&hello.connectionGeneration().equals(frame.connectionGeneration())
                    &&hello.buildMatch()&&hello.adapterStatus().equals("ready"),"Religion original HELLO differs from its current actual frame");
        }
    }
    private final PlanningReadPort reads;
    private final ActionPorts.OutcomeArchive archive;
    private final List<FixedRead> fixed;
    private final Supplier<ExistingReads> existing;
    private final List<Component> components;
    public ReligionService(PlanningReadPort actualReads,ActionPorts.OutcomeArchive actualArchive,List<FixedRead> actualFixed,Supplier<ExistingReads> actualExisting) {
        this(actualReads,actualArchive,actualFixed,actualExisting,List.of());
    }
    public ReligionService(PlanningReadPort actualReads,ActionPorts.OutcomeArchive actualArchive,List<FixedRead> actualFixed,Supplier<ExistingReads> actualExisting,List<Component> actualComponents) {
        reads=Objects.requireNonNull(actualReads);archive=Objects.requireNonNull(actualArchive);fixed=List.copyOf(actualFixed);existing=Objects.requireNonNull(actualExisting);
        components=List.copyOf(actualComponents);var methods=new java.util.HashSet<String>(actualReadNames());
        for(var component:components)for(String method:component.methods())StrictJson.require(method.startsWith("ck3_query_")&&methods.add(method)&&ReligionCodec.methods().stream().anyMatch(m->m.name().equals(method)),"duplicate or non-READ Religion service component method");
        StrictJson.require(fixed.size()==ReadKind.values().length&&fixed.stream().map(FixedRead::kind).distinct().count()==fixed.size(),"exact twelve original Religion READs required");
    }
    /** Returns only an identical already-installed component. This lookup creates no installation or authority. */
    public <T extends Component> Optional<T> component(Class<T> actualType)throws IOException {
        Objects.requireNonNull(actualType);
        var matching=components.stream().filter(actualType::isInstance).map(actualType::cast).toList();
        if(matching.size()>1)throw new IOException("multiple installed Religion components match the requested actual type: "+actualType.getName());
        return matching.isEmpty()?Optional.empty():Optional.of(matching.getFirst());
    }
    /** The old decoders below are original-only pure validators. Wrapping adds explicit replay without copying their algorithms. */
    public static List<FixedRead> fixedReads(ReligionCapabilities.Registration original) {
        var result=new ArrayList<FixedRead>();
        for(ReadKind kind:ReadKind.values()) {
            ReadContract<?> found=original.readContracts().stream().filter(c->c.operation().value().equals(kind.step())).findFirst().orElseThrow();
            result.add(new FixedRead(kind,withOriginalReplay(found)));
        }
        return List.copyOf(result);
    }
    private static <T> ReadContract<T> withOriginalReplay(ReadContract<T> original) {
        if(original.hasPureReplay())return original;
        return new ReadContract<>(original.contractId(),original.operation(),original.requiredCapability(),original.permissionKey(),original.permissionMode(),original.wireProfile(),
                original.guardMode(),original.sourceRef(),original::prepare,original::decode,original::decode);
    }
    public static List<String> actualReadNames() {
        return List.of("ck3_query_player_holy_site_creation_context_v1","ck3_query_player_ghw_permissions_v1",
                "ck3_query_player_holy_site_decision_detail_v1","ck3_query_player_holy_site_decision_cooldown_v1",
                "ck3_query_player_seek_indulgences_terms_v1","ck3_query_player_religion_conversion_result_private_v1",
                "ck3_query_county_conversion_task_result","ck3_query_confucian_assembly_predicates_v1",
                "ck3_query_confucian_challenger_graph_v1","ck3_query_confucian_religious_title_v1",
                "ck3_query_current_actor_stress_adjustment_v1",
                "ck3_query_player_religion_context_v1","ck3_query_player_holy_order_context_v1");
    }
    public Response invoke(Session same,ActualFrame actual,Request request) {
        Objects.requireNonNull(same);Objects.requireNonNull(request);
        var frame=actual.frame();StrictJson.require(frame.identity().frame().revision().equals(request.expectedRevision()),"Religion expected public revision is stale");
        String name=request.method().name();
        if(!actualReadNames().contains(name)){
            var selected=components.stream().filter(component->component.methods().contains(name)).toList();
            StrictJson.require(selected.size()==1,"no unique installed Religion READ component for this declaration");
            return selected.getFirst().invoke(same,actual,request);
        }
        if(name.equals("ck3_query_player_religion_context_v1")) {
            var provider=existing.get().religion();var result=read(same,provider.contract(),actual,empty());
            var business=PlayerReligionContextRead.flattened(result.value());return new Response(request.method(),ReligionCodec.raw(ReligionCodec.publicResult(request.method(),business)));
        }
        if(name.equals("ck3_query_player_holy_order_context_v1")) {
            var provider=existing.get().holyOrders();var result=read(same,provider.contract(),actual,empty());
            var business=PlayerHolyOrderContextRead.flattened(result.value());return new Response(request.method(),ReligionCodec.raw(ReligionCodec.publicResult(request.method(),business)));
        }
        ReadKind kind=kind(name);exactBuild(kind,actual.hello());ObjectNode args=arguments(kind,actual,request);
        ReadContract<?> contract=fixed.stream().filter(f->f.kind()==kind).findFirst().orElseThrow().contract();
        return presentRead(kind,actual,request,read(same,contract,actual,args));
    }
    /** Pure public projection of the already decoded original READ. It grants no source, Native or Game authority. */
    public static <T> Response presentRead(ReadKind selected,ActualFrame actual,Request request,PlanningReadResult.Known<T> original) {
        Objects.requireNonNull(selected);Objects.requireNonNull(actual);Objects.requireNonNull(request);Objects.requireNonNull(original);
        StrictJson.require(kind(request.method().name())==selected&&actual.frame().identity().frame().revision().equals(request.expectedRevision()),"Religion public projection changed the original method/revision");
        var read=original.receipt().request();
        StrictJson.require(read.operation().value().equals(selected.step())&&read.origin() instanceof CommandOrigin.Gameplay
                &&read.before().equals(actual.frame().identity())&&read.source().equals(actual.frame().source())&&read.sessionId().equals(actual.frame().sessionId()),"Religion public projection changed its original source frame");
        Class<?> expected=switch(selected){
            case CREATION->ReligionModels.CreationContext.class;case GHW->ReligionModels.GhwPermissions.class;case DETAIL->ReligionModels.DecisionDetail.class;
            case COOLDOWN->ReligionModels.CooldownResult.class;case INDULGENCES->ReligionModels.IndulgenceTerms.class;case RELIGION_RESULT->ReligionModels.ConversionResult.class;
            case COUNTY_RESULT->ReligionModels.CountyResult.class;case ASSEMBLY->ReligionModels.Assembly.class;case CHALLENGERS->ReligionModels.ChallengerGraph.class;
            case TITLE->ReligionModels.ReligiousTitle.class;case STRESS->ReligionModels.Stress.class;case EPIDEMIC->ReligionModels.EpidemicResult.class;
        };
        StrictJson.require(expected.isInstance(original.value()),"Religion typed original decoder returned another result family");exactBuild(selected,actual.hello());
        ObjectNode business=present(selected,actual,request,original.value(),originalResult(original.receipt()));
        return new Response(request.method(),ReligionCodec.raw(ReligionCodec.publicResult(request.method(),business)));
    }
    private <T> PlanningReadResult.Known<T> read(Session same,ReadContract<T> contract,ActualFrame actual,ObjectNode fields) {
        return readKnown(reads,archive,same,contract,actual,fields);
    }
    public static <T> PlanningReadResult.Known<T> readKnown(PlanningReadPort reads,ActionPorts.OutcomeArchive archive,Session same,ReadContract<T> contract,ActualFrame actual,ObjectNode fields) {
        Objects.requireNonNull(reads);Objects.requireNonNull(archive);Objects.requireNonNull(same);Objects.requireNonNull(contract);Objects.requireNonNull(actual);Objects.requireNonNull(fields);
        var f=actual.frame();var args=OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(fields).bytes()),"Religion native arguments");
        var request=new PlanningReadRequest(f.identity(),f.source(),f.sessionId(),contract.operation(),args,actual.deadline());
        return readKnownRequest(reads,archive,same,contract,request);
    }
    public static <T> PlanningReadResult.Known<T> readKnownRequest(PlanningReadPort reads,ActionPorts.OutcomeArchive archive,Session same,ReadContract<T> contract,PlanningReadRequest request) {
        Objects.requireNonNull(reads);Objects.requireNonNull(archive);Objects.requireNonNull(same);Objects.requireNonNull(contract);Objects.requireNonNull(request);
        PlanningReadResult<T> result=reads.read(same,contract,request);
        if(!(result instanceof PlanningReadResult.Known<T> known))throw new IllegalStateException("actual Religion READ unavailable: "+((PlanningReadResult.Unavailable<T>)result).reason());
        StrictJson.require(known.receipt().request().equals(request)&&known.receipt().contractId().equals(contract.contractId()),"Religion producer changed original request/contract");
        StrictJson.require(archive.withSession(same).readReferenceOf(known.receipt()).equals(known.originalReceipt()),"Religion original READ was not retained by this actual writer");
        requireGuards(known.receipt());originalResult(known.receipt());
        return known;
    }
    public static void requireGuards(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        boolean reconciliation=receipt.request().origin() instanceof CommandOrigin.Reconciliation;
        StrictJson.require(!reconciliation||List.of("query-player-religion-conversion-result-private-v1","county-conversion-task-result-private-v1").contains(receipt.request().operation().value()),"ordinary Religion READ cannot borrow reconciliation authority");
        ReadContract.GuardMode required=reconciliation?ReadContract.GuardMode.RECONCILIATION_OBSERVATION:ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP;
        for(var guard:List.of(receipt.before(),receipt.after()))StrictJson.require(guard.guardMode()==required
                &&receipt.request().origin().acceptsGuard(guard.binding().origin())&&guard.binding().source().equals(receipt.request().source())
                &&guard.binding().sessionId().equals(receipt.request().sessionId())&&(reconciliation||guard.paused()&&guard.mapReady()&&guard.playerAlive()),"Religion READ crossed its actual source-bound origin frame");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                &&receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration())
                &&receipt.before().binding().capabilityEvidence().equals(receipt.after().binding().capabilityEvidence()),"Religion READ original modal/HELLO/source binding changed");
    }
    public static ObjectNode originalResult(PlanningReadReceipt receipt) {
        requireGuards(receipt);
        try {
            requireOriginalOutbound(receipt);
            NativeWire.Frame decoded=NativeWire.decode(receipt.original().originalPacket());
            StrictJson.require(decoded instanceof NativeWire.CommandResult,"Religion original packet must be command_result");var packet=(NativeWire.CommandResult)decoded;
            StrictJson.require(packet.requestId().equals(receipt.requestId())&&packet.nativeOk()&&receipt.original().nativeOk()
                    &&java.util.Arrays.equals(packet.payload().value(),receipt.original().originalFrame().bytes()),"Religion original request/frame/native status drift");
            ObjectNode frame=ReligionCodec.object(new RawJson(packet.payload().value()));
            StrictJson.object(frame,java.util.Set.of("type","protocol_version","request_id","ok","result"));
            StrictJson.require(frame.get("result") instanceof ObjectNode,"Religion original result object required");ObjectNode result=(ObjectNode)frame.get("result");
            StrictJson.require(receipt.original().originalResultToken().isPresent()&&ReligionCodec.object(receipt.original().originalResultToken().orElseThrow()).equals(result),"Religion original result token differs from complete Native packet");
            return result.deepCopy();
        }catch(IOException failure){throw new IllegalArgumentException("malformed original Religion Native packet",failure);}
    }
    private static void requireOriginalOutbound(PlanningReadReceipt receipt)throws IOException {
        var original=receipt.original().outbound().orElseThrow(()->new IOException("actual retained Religion READ outbound packet required"));
        var wire=NativeWire.decodeExecuteRequest(original.originalPacket());var request=receipt.request();
        var factual=request.origin() instanceof CommandOrigin.Reconciliation?request.reconciliationBefore():request.before();
        BigInteger nativeRevision=factual.frame().identity().nativeRevision();
        StrictJson.require(original.requestId().equals(receipt.requestId())&&wire.requestId().equals(receipt.requestId())&&wire.step().equals(request.operation().value()),"Religion READ outbound request/step drift");
        StrictJson.require(wire.expectedRevision().isPresent()||wire.expectedSnapshotRevision().isPresent(),"Religion READ lost its native revision profile");
        wire.expectedRevision().ifPresent(value->StrictJson.require(value.equals(nativeRevision),"Religion outbound expected_revision used a public or foreign revision"));
        wire.expectedSnapshotRevision().ifPresent(value->StrictJson.require(value.equals(nativeRevision),"Religion outbound expected_snapshot_revision drift"));
        ObjectNode expected=ReligionCodec.object(new RawJson(OpportunityJson.encode(request.arguments())));
        expected.remove("expected_snapshot_revision");
        if(request.operation().value().equals("query-player-clergy-appointment-v1"))expected.put("expected_public_revision",factual.frame().revision());
        if(List.of("query-player-pilgrimage-activities-v1-private","query-player-pilgrimage-planner-v1-private").contains(request.operation().value())){
            expected.put("expected_date_raw",factual.frame().identity().dateRaw()).put("expected_actor_character_id",factual.frame().identity().player()).put("expected_activity_key","activity_pilgrimage");
            if(request.operation().value().equals("query-player-pilgrimage-planner-v1-private")){
                JsonNode option=expected.remove("option_key");StrictJson.require(option!=null&&option.isTextual(),"actual pilgrimage selector option required");expected.set("expected_option_key",option);
            }
        }
        if(request.operation().value().equals("query-player-epidemic-recovery-v1"))expected.remove("expected_event_instance_id");
        StrictJson.require(ReligionCodec.object(new RawJson(wire.normalizedAdditionalFields().value())).equals(expected),"Religion outbound domain selectors differ from the actual typed request");
    }
    /** Delegates the existing actual HELLO/source decoder, including .2/.3/.4; it does not infer build from a payload. */
    public static PlayerReligionContext.Build boundBuild(PlanningReadReceipt receipt) {requireGuards(receipt);return PlayerReligionContextRead.connectedBuild(receipt);}
    /** Python json.loads uses binary64 floats. Reopen only the already validated identical packet bytes for those typed numeric consumers. */
    public static ObjectNode originalResultBinary64(PlanningReadReceipt receipt) {
        originalResult(receipt);
        try{
            var factory=com.fasterxml.jackson.core.JsonFactory.builder().enable(com.fasterxml.jackson.core.StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
            var parser=new com.fasterxml.jackson.databind.ObjectMapper(factory).enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
            JsonNode frame=parser.readTree(receipt.original().originalFrame().bytes());
            StrictJson.require(frame!=null&&frame.isObject()&&frame.get("result") instanceof ObjectNode,"validated original binary64 result object required");
            return ((ObjectNode)frame.get("result")).deepCopy();
        }catch(IOException failure){throw new IllegalArgumentException("validated original Religion binary64 packet malformed",failure);}
    }
    private static ReadKind kind(String name) { return switch(name) {
        case "ck3_query_player_holy_site_creation_context_v1" -> ReadKind.CREATION;
        case "ck3_query_player_ghw_permissions_v1" -> ReadKind.GHW;
        case "ck3_query_player_holy_site_decision_detail_v1" -> ReadKind.DETAIL;
        case "ck3_query_player_holy_site_decision_cooldown_v1" -> ReadKind.COOLDOWN;
        case "ck3_query_player_seek_indulgences_terms_v1" -> ReadKind.INDULGENCES;
        case "ck3_query_player_religion_conversion_result_private_v1" -> ReadKind.RELIGION_RESULT;
        case "ck3_query_county_conversion_task_result" -> ReadKind.COUNTY_RESULT;
        case "ck3_query_confucian_assembly_predicates_v1" -> ReadKind.ASSEMBLY;
        case "ck3_query_confucian_challenger_graph_v1" -> ReadKind.CHALLENGERS;
        case "ck3_query_confucian_religious_title_v1" -> ReadKind.TITLE;
        case "ck3_query_current_actor_stress_adjustment_v1" -> ReadKind.STRESS;
        case "ck3_query_player_epidemic_recovery_private_v1" -> ReadKind.EPIDEMIC;
        default -> throw new IllegalArgumentException("not an installed original Religion READ");
    }; }
    private static void exactBuild(ReadKind kind,NativeWire.Hello hello) {
        String version= switch(kind) {case CREATION,GHW,DETAIL,COOLDOWN->"1.20.0.4";case INDULGENCES,RELIGION_RESULT,STRESS->"1.20.0.3";default->null;};
        if(version!=null) {
            var build=java.util.Arrays.stream(ReligionModels.Build.values()).filter(b->b.version().equals(version)).findFirst().orElseThrow();
            StrictJson.require(build.sha256().equalsIgnoreCase(hello.gameSha256()),"original Religion method requires exact "+version);
        }
    }
    private static ObjectNode arguments(ReadKind kind,ActualFrame actual,Request request) {
        ObjectNode n=empty();var f=actual.frame();var id=f.identity();var identity=id.frame().identity();
        switch(kind) {
            case CREATION, ASSEMBLY, TITLE -> { }
            case DETAIL -> n.put("action",request.text(Field.ACTION)).put("holy_site_id",request.integer(Field.HOLY_SITE_ID));
            case COOLDOWN -> n.put("action",request.text(Field.ACTION));
            case INDULGENCES -> n.put("recipient_character_id",request.integer(Field.RECIPIENT_CHARACTER_ID));
            case CHALLENGERS -> {var rows=n.putArray("faith_full_ids");((IdsValue)request.value(Field.FAITH_FULL_IDS)).values().forEach(rows::add);}
            case GHW -> n.put("expected_date_raw",identity.dateRaw()).put("expected_actor_character_id",identity.player()).put("expected_game_pid",id.game().pid()).put("expected_connection_generation",f.connectionGeneration());
            case STRESS -> n.put("base_amount",request.integer(Field.BASE_AMOUNT)).put("expected_player_character_id",identity.player()).put("expected_game_pid",id.game().pid()).put("expected_connection_generation",f.connectionGeneration());
            case RELIGION_RESULT, COUNTY_RESULT -> n.put("expected_snapshot_revision",identity.nativeRevision()).put("expected_public_revision",id.frame().revision()).put("expected_date_raw",identity.dateRaw()).put("expected_player_character_id",identity.player())
                    .put("submitted_request_id",request.text(kind==ReadKind.RELIGION_RESULT?Field.REQUEST_ID:Field.SUBMITTED_REQUEST_ID)).put("action_id",request.text(Field.ACTION_ID));
            case EPIDEMIC -> {
                StrictJson.require(ReligionCodec.optionalInteger(request,Field.REQUESTED_TITLE_ID,BigInteger.ZERO).signum()==0,"explicit title READ requires its actual finite installed contract family; no dynamic native step is invented");
                n.put("expected_event_instance_id",request.integer(Field.EXPECTED_EVENT_INSTANCE_ID));
            }
        }
        return n;
    }
    private static ObjectNode present(ReadKind kind,ActualFrame actual,Request request,Object typed,ObjectNode envelope) {
        var f=actual.frame();ObjectNode result;
        if(kind==ReadKind.RELIGION_RESULT) {StrictJson.require(typed instanceof ReligionModels.ConversionResult,"original conversion decoder result required");return conversion((ReligionModels.ConversionResult)typed,actual,envelope);}
        if(kind==ReadKind.COUNTY_RESULT) {StrictJson.require(typed instanceof ReligionModels.CountyResult,"original county decoder result required");return county((ReligionModels.CountyResult)typed,actual,envelope);}
        if(kind==ReadKind.ASSEMBLY||kind==ReadKind.CHALLENGERS||kind==ReadKind.TITLE) {
            result=empty().put("schema","ck3-confucian-readonly-public-v1").put("operation",kind==ReadKind.ASSEMBLY?"assembly_predicates":kind==ReadKind.TITLE?"religious_title":"challenger_graph");
            result.set("native_result",envelope.deepCopy());result.put("date_raw",f.identity().frame().identity().dateRaw()).put("game_pid",f.identity().game().pid()).put("connection_generation",decimal(f.connectionGeneration())).put("player_character_id",f.identity().frame().identity().player()).put("business_postcondition_verified",false).put("full_product_acceptance_credit",false);
        } else if(kind==ReadKind.STRESS||kind==ReadKind.EPIDEMIC) {
            result=envelope.deepCopy();
            if(kind==ReadKind.STRESS)result.put("current_actor_stress_adjustment_ready","available".equals(envelope.path("status").textValue()));
            else result.put("queried_event_instance_id",request.integer(Field.EXPECTED_EVENT_INSTANCE_ID));
        } else {
            String payload=switch(kind) {case CREATION->"player_holy_site_creation_context";case GHW->"player_ghw_permissions";case DETAIL->"player_holy_site_decision_detail";case COOLDOWN->"player_holy_site_decision_cooldown";case INDULGENCES->"player_seek_indulgences_terms";default->throw new IllegalArgumentException("wrong flattened Religion presentation");};
            StrictJson.require(envelope.get(payload) instanceof ObjectNode,"validated Religion nested result required");result=((ObjectNode)envelope.get(payload)).deepCopy();provenance(result,actual);
            result.set("snapshot_revision",envelope.get("snapshot_revision"));result.set("backend_id",envelope.get("backend_id"));result.set("domain_key",envelope.get("domain_key"));result.set("status",envelope.get("status"));result.put("advertised",false);
        }
        metadata(result,actual);return result;
    }
    private static ObjectNode county(ReligionModels.CountyResult value,ActualFrame actual,ObjectNode envelope) {
        return county(value,actualBuild(actual),envelope);
    }
    private static ObjectNode county(ReligionModels.CountyResult value,PlayerReligionContext.Build build,ObjectNode envelope) {
        var owner=value.owner();ObjectNode result=empty().put("schema","xar.ck3.county-conversion-task-independent-result.v1");provenance(result,build);
        String status=value.materialObserved()?"task_assignment_material_observed":submitStatus(owner.status());
        result.put("status",status).put("request_id",owner.requestId().value()).put("action_id",owner.request().actionId().value()).put("player_character_id",owner.playerId()).put("province_id",owner.request().province().value());
        putNullable(result,"target_county_title_id",owner.targetCounty());result.put("material_result",value.materialObserved()).put("verification_pending",value.verificationPending());putNullable(result,"actual_task_id_unchanged",value.taskIdUnchanged());putNullable(result,"actual_task_assignment_matches",value.assignmentMatches());result.put("task_assignment_material_observed",value.materialObserved()).put("county_conversion_completed",false);
        ObjectNode originalOwner=(ObjectNode)envelope.get("submission"),originalResult=(ObjectNode)envelope.get("independent_result");result.set("before_task",originalOwner.get("before"));result.set("after_task",originalResult.get("after"));result.set("owner_submission",originalOwner.deepCopy());result.set("owner_result",originalResult.deepCopy());result.put("automatic_retry",false).put("advertised",false);return ReligionConversionActions.projectCountyResult(value,result);
    }
    private static ObjectNode conversion(ReligionModels.ConversionResult value,ActualFrame actual,ObjectNode envelope) {
        return conversion(value,actualBuild(actual),envelope);
    }
    private static ObjectNode conversion(ReligionModels.ConversionResult value,PlayerReligionContext.Build build,ObjectNode envelope) {
        var owner=value.owner();ObjectNode result=empty().put("schema","xar.ck3.player-religion-conversion-independent-result.v1");provenance(result,build);
        boolean queued=owner.status()==ReligionModels.SubmitStatus.QUEUED_VERIFICATION_PENDING;
        result.put("status",!queued?owner.status()==ReligionModels.SubmitStatus.ALREADY_TARGET_NOOP?"noop_preexisting_target_match":"rejected_before_submit":value.materialObserved()?"converted_material_verified":"submitted_verification_pending");
        result.put("request_id",owner.requestId().value()).put("action_id",owner.request().actionId().value()).put("target_rite_id",owner.request().targetRite().value()).put("material_result",value.materialObserved()).put("verification_pending",value.verificationPending());
        result.set("owner_submission",envelope.get("submission").deepCopy());result.set("owner_result",envelope.get("independent_result").deepCopy());result.put("automatic_retry",false).put("advertised",false);
        if(queued) {
            result.put("player_character_id",owner.playerId());putNullable(result,"target_already_reached_before",value.preexisting());putNullable(result,"actual_rite_changed",value.riteChanged());putNullable(result,"actual_target_reached_after",value.targetReached());putNullable(result,"actual_target_faith_reached_after",value.faithReached());
            putNullable(result,"piety_net_delta_raw",value.pietyDelta());putNullable(result,"gold_net_delta_raw",value.goldDelta());putNullable(result,"prestige_net_delta_raw",value.prestigeDelta());result.put("quoted_base_piety_cost_raw",owner.paidTerms().pietyCost());
            ObjectNode net=result.putObject("actual_net_resources_raw");putNullable(net,"piety_raw",value.pietyDelta());putNullable(net,"gold_raw",value.goldDelta());putNullable(net,"prestige_raw",value.prestigeDelta());
            result.put("request_associated_conversion_material_observed",value.materialObserved()).put("raw_scale",100000).put("base_payment_observed",false).putNull("native_base_piety_charge_raw").put("native_execute_observed",false).put("conversion_causality_inferred",false);
            result.set("before_outcome",envelope.get("submission").get("before"));result.set("after_outcome",envelope.get("independent_result").get("after"));
        }
        return ReligionConversionActions.projectConversionResult(value,result);
    }
    public static ObjectNode presentConversion(ReligionModels.ConversionResult value,ActualFrame actual,ObjectNode envelope) {
        return ReligionCodec.publicResult(ReligionCodec.method("ck3_query_player_religion_conversion_result_private_v1"),conversion(value,actual,envelope));
    }
    public static ObjectNode presentCounty(ReligionModels.CountyResult value,ActualFrame actual,ObjectNode envelope) {
        return ReligionCodec.publicResult(ReligionCodec.method("ck3_query_county_conversion_task_result"),county(value,actual,envelope));
    }
    public static ObjectNode presentConversion(ReligionModels.ConversionResult value,PlayerReligionContext.Build build,ObjectNode envelope) {
        return ReligionCodec.publicResult(ReligionCodec.method("ck3_query_player_religion_conversion_result_private_v1"),conversion(value,build,envelope));
    }
    public static ObjectNode presentCounty(ReligionModels.CountyResult value,PlayerReligionContext.Build build,ObjectNode envelope) {
        return ReligionCodec.publicResult(ReligionCodec.method("ck3_query_county_conversion_task_result"),county(value,build,envelope));
    }
    private static String submitStatus(ReligionModels.SubmitStatus status) {return status.name().toLowerCase(java.util.Locale.ROOT);}
    private static void putNullable(ObjectNode n,String key,BigInteger value){if(value==null)n.putNull(key);else n.put(key,value);}
    private static void putNullable(ObjectNode n,String key,Integer value){if(value==null)n.putNull(key);else n.put(key,value);}
    private static void putNullable(ObjectNode n,String key,Boolean value){if(value==null)n.putNull(key);else n.put(key,value);}
    private static void provenance(ObjectNode n,ActualFrame actual) {
        provenance(n,actualBuild(actual));
    }
    private static PlayerReligionContext.Build actualBuild(ActualFrame actual){return java.util.Arrays.stream(PlayerReligionContext.Build.values()).filter(b->b.sha256().equalsIgnoreCase(actual.hello().gameSha256())).findFirst().orElseThrow(()->new IllegalArgumentException("unknown original Religion exact-build SHA"));}
    private static void provenance(ObjectNode n,PlayerReligionContext.Build build){Objects.requireNonNull(build);n.put("exact_ck3_build",build.version()).put("exe_sha256",build.sha256().toUpperCase(java.util.Locale.ROOT));}
    private static void metadata(ObjectNode n,ActualFrame actual) {var f=actual.frame();n.put("queried_snapshot_id",f.identity().frame().snapshotId()).put("queried_revision",decimal(f.identity().frame().revision())).put("queried_native_revision",decimal(f.identity().frame().identity().nativeRevision()));}
    private static String decimal(BigInteger value){return PublicUnsigned64.canonical(value,PublicUnsigned64.Minimum.ZERO);}
    private static ObjectNode empty(){return StrictJson.object();}
}
