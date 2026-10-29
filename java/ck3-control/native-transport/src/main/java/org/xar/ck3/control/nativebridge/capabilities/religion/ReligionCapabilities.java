package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels.*;

/** Typed public adapters. The one root supplies the existing action/read coordinators on its held NativeGameTransport. */
public final class ReligionCapabilities {
    public static final String NAVIGATE="navigate-ingame-ui-v1", NAVIGATE_CAPABILITY="game.command.navigate-ingame-ui-v1";
    public enum ReadKind {
        CREATION("query-player-holy-site-creation-context-v1","allow_private_player_holy_site_creation_context_query",ReadContract.WireProfile.G2_PRIVATE_QUERY),
        GHW("query-player-ghw-permissions-v1-private","allow_private_player_ghw_permissions_query",ReadContract.WireProfile.G2_PRIVATE_QUERY),
        DETAIL("query-player-holy-site-decision-detail-v1","allow_private_holy_site_adoption_detail_query",ReadContract.WireProfile.G2_PRIVATE_QUERY),
        COOLDOWN("query-player-holy-site-decision-cooldown-v1","allow_private_holy_site_adoption_detail_query",ReadContract.WireProfile.G2_PRIVATE_QUERY),
        INDULGENCES("query-player-seek-indulgences-terms-v1","allow_private_player_religion_context_query",ReadContract.WireProfile.G2_PRIVATE_QUERY),
        RELIGION_RESULT("query-player-religion-conversion-result-private-v1","allow_private_player_religion_conversion_terms_query",ReadContract.WireProfile.EXECUTE_STEP),
        COUNTY_RESULT("county-conversion-task-result-private-v1","allow_private_player_clergy_appointment_query",ReadContract.WireProfile.EXECUTE_STEP),
        ASSEMBLY("query-confucian-assembly-predicates-v1","allow_private_confucian_readonly_queries",ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY),
        CHALLENGERS("query-confucian-challenger-graph-v1","allow_private_confucian_challenger_queries",ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY),
        TITLE("query-confucian-religious-title-v1","allow_private_confucian_readonly_queries",ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY),
        STRESS("query-current-actor-stress-adjustment-v1","game.query.current-actor-stress-adjustment.v1",ReadContract.WireProfile.EXECUTE_STEP),
        EPIDEMIC("query-player-epidemic-recovery-v1","allow_private_epidemic_recovery_query",ReadContract.WireProfile.EXECUTE_STEP);
        private final String step,permission;private final ReadContract.WireProfile wire;
        ReadKind(String step,String permission,ReadContract.WireProfile wire){this.step=step;this.permission=permission;this.wire=wire;}
        public String step(){return step;}public String permission(){return permission;}public ReadContract.WireProfile wireProfile(){return wire;}
    }
    public enum MutationKind { HOLY_SITE_UI, HOLY_SITE_CREATION_UI, HOLY_SITE_CREATE_ONCE, RELIGION_CONVERSION, COUNTY_TASK }
    public enum MutationSource { UI, CREATION, RELIGION_CONVERSION, COUNTY_TASK }
    public record ReadSource(ReadKind kind,ExactRef source) { public ReadSource{Objects.requireNonNull(kind);Objects.requireNonNull(source);} }
    public record ActionSource(MutationSource kind,ExactRef source) { public ActionSource{Objects.requireNonNull(kind);Objects.requireNonNull(source);} }
    /** Implementations must invoke actual root build/permission qualification, not return a constructor/ACK as evidence. */
    @FunctionalInterface public interface ReadAdmission { void verify(ReadKind kind,PlanningReadRequest actualRequest); }
    @FunctionalInterface public interface MutationAdmission { void verify(MutationKind kind,ActionCommand actualCommand); }
    public record TitleRead(PositiveId title,ReadContract<EpidemicResult> contract) { }

    /** Construct once in the composition root, install every returned contract in the same PlanningReadCoordinator. */
    public static final class Registration implements ActionPorts.PreparationPort {
        private final List<ReadSource> readSources;private final List<ActionSource> actionSources;
        private final ReadAdmission readAdmission;private final MutationAdmission mutationAdmission;
        private final ReadContract<CreationContext> creation;private final ReadContract<GhwPermissions> ghw;
        private final ReadContract<DecisionDetail> detail;private final ReadContract<CooldownResult> cooldown;
        private final ReadContract<IndulgenceTerms> indulgences;private final ReadContract<ConversionResult> religion;
        private final ReadContract<CountyResult> county;private final ReadContract<Assembly> assembly;
        private final ReadContract<ChallengerGraph> challengers;private final ReadContract<ReligiousTitle> title;
        private final ReadContract<Stress> stress;private final ReadContract<EpidemicResult> epidemic;
        private final List<TitleRead> epidemicTitles;
        private final ReadContract<ConversionResult> religionReconciliation;
        private final ReadContract<CountyResult> countyReconciliation;
        public Registration(List<ReadSource> readSources,List<ActionSource> actionSources,
                List<PositiveId> approvedEpidemicTitles,ReadAdmission readAdmission,MutationAdmission mutationAdmission) {
            this.readSources=List.copyOf(readSources);this.actionSources=List.copyOf(actionSources);this.readAdmission=Objects.requireNonNull(readAdmission);this.mutationAdmission=Objects.requireNonNull(mutationAdmission);
            need(readSources.stream().map(ReadSource::kind).distinct().count()==ReadKind.values().length&&readSources.size()==ReadKind.values().length,"one actual source per fixed query required");need(actionSources.stream().map(ActionSource::kind).distinct().count()==MutationSource.values().length&&actionSources.size()==MutationSource.values().length,"one actual source per mutation family required");
            creation=contract(ReadKind.CREATION,HolySiteDecoders::creation);ghw=contract(ReadKind.GHW,ObservationDecoders::ghw);detail=contract(ReadKind.DETAIL,HolySiteDecoders::detail);cooldown=contract(ReadKind.COOLDOWN,HolySiteDecoders::cooldown);indulgences=contract(ReadKind.INDULGENCES,HolySiteDecoders::indulgences);religion=contract(ReadKind.RELIGION_RESULT,ConversionDecoders::religion);county=contract(ReadKind.COUNTY_RESULT,ConversionDecoders::county);assembly=contract(ReadKind.ASSEMBLY,ConfucianDecoders::assembly);challengers=contract(ReadKind.CHALLENGERS,ConfucianDecoders::challengers);title=contract(ReadKind.TITLE,ConfucianDecoders::title);stress=contract(ReadKind.STRESS,ObservationDecoders::stress);
            epidemic=contract(ReadKind.EPIDEMIC,r->ObservationDecoders.epidemic(r,0,argumentInteger(r.request().arguments(),"expected_event_instance_id")));
            religionReconciliation=reconciliationContract(ReadKind.RELIGION_RESULT,ConversionDecoders::religion);
            countyReconciliation=reconciliationContract(ReadKind.COUNTY_RESULT,ConversionDecoders::county);
            need(approvedEpidemicTitles.size()==approvedEpidemicTitles.stream().distinct().count(),"duplicate explicit epidemic title registration");List<TitleRead> titles=new ArrayList<>();for(PositiveId id:approvedEpidemicTitles){String step=ReadKind.EPIDEMIC.step()+"-title-"+id.value();ReadContract<EpidemicResult> c=new ReadContract<>("religion/epidemic-title/"+id.value(),new OperationKey(step),Optional.empty(),ReadKind.EPIDEMIC.permission(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,source(ReadKind.EPIDEMIC),request->{readAdmission.verify(ReadKind.EPIDEMIC,request);exact(argumentNode(request.arguments()),"");return new NativeRequest(step,Optional.empty(),raw(empty()));},r->ObservationDecoders.epidemic(r,id.value(),null));titles.add(new TitleRead(id,c));}epidemicTitles=List.copyOf(titles);
        }
        private ExactRef source(ReadKind kind){return readSources.stream().filter(s->s.kind()==kind).findFirst().orElseThrow().source();}
        private ExactRef source(MutationSource kind){return actionSources.stream().filter(s->s.kind()==kind).findFirst().orElseThrow().source();}
        private <T> ReadContract<T> contract(ReadKind kind,Function<PlanningReadReceipt,T> decode){Optional<String> capability=kind==ReadKind.STRESS?Optional.of(kind.permission()):Optional.empty();return new ReadContract<>("religion/"+kind.name().toLowerCase(java.util.Locale.ROOT),new OperationKey(kind.step()),capability,kind.permission(),capability.isPresent()?ReadContract.PermissionMode.ADVERTISED_CAPABILITY:ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,kind.wireProfile(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source(kind),(request,requestId)->{readAdmission.verify(kind,request);return prepareRead(kind,request);},decode,decode);}
        public List<ReadContract<?>> readContracts(){List<ReadContract<?>> values=new ArrayList<>(List.of(creation,ghw,detail,cooldown,indulgences,religion,county,assembly,challengers,title,stress,epidemic));for(TitleRead value:epidemicTitles)values.add(value.contract());return List.copyOf(values);}
        /** Root passes these exact permissions to its single NativeGameTransport constructor. */
        public List<NativePrivateActionPermission> privateActions(NativePrivateActionPermission.QualificationVerifier religionQualification,NativePrivateActionPermission.QualificationVerifier countyQualification){return List.of(new NativePrivateActionPermission(new OperationKey("submit-player-religion-conversion-private-v1"),"allow_private_player_religion_conversion_terms_query",source(MutationSource.RELIGION_CONVERSION),Registration::validatePrivate,religionQualification),new NativePrivateActionPermission(new OperationKey("county-conversion-task-submit-private-v1"),"allow_private_player_clergy_appointment_query",source(MutationSource.COUNTY_TASK),Registration::validatePrivate,countyQualification));}
        public boolean supports(ActionCommand command){if(command.operation().value().equals("submit-player-religion-conversion-private-v1")||command.operation().value().equals("county-conversion-task-submit-private-v1"))return true;if(!command.operation().value().equals(NAVIGATE))return false;ObjectNode fields=argumentNode(command.arguments());return fields.has("window_kind")&&List.of("holy_site","holy_site_adoption","holy_site_creation").contains(text(fields,"window_kind"));}
        /** Typed Native fields are projected from the unchanged canonical action, which retains replay/once metadata. */
        public NativeRequest prepareNavigation(ActionCommand command,ObjectNode typedNativeFields) {
            need(command.operation().value().equals(NAVIGATE),"actual sole navigation operation required");
            ObjectNode fields=Objects.requireNonNull(typedNativeFields).deepCopy();validateUi(fields);
            MutationKind kind=text(fields,"operation").equals("create_holy_site_once")?MutationKind.HOLY_SITE_CREATE_ONCE:text(fields,"window_kind").equals("holy_site_creation")?MutationKind.HOLY_SITE_CREATION_UI:MutationKind.HOLY_SITE_UI;
            MutationSource source=kind==MutationKind.HOLY_SITE_CREATE_ONCE?MutationSource.CREATION:MutationSource.UI;
            if(kind==MutationKind.HOLY_SITE_CREATE_ONCE){equal(fields,"expected_date_raw",command.before().frame().identity().dateRaw());equal(fields,"expected_player_character_id",command.before().frame().identity().player());}
            mutationAdmission.verify(kind,command);
            return new NativeRequest(NAVIGATE,Optional.of(NAVIGATE_CAPABILITY),raw(fields));
        }
        @Override public NativeRequest prepare(ActionCommand command) {
            need(supports(command),"operation is outside religion registration");ObjectNode fields=argumentNode(command.arguments());
            if(command.operation().value().equals(NAVIGATE))return prepareNavigation(command,fields);
            String step=command.operation().value();boolean conversion=step.equals("submit-player-religion-conversion-private-v1");
            MutationKind kind=conversion?MutationKind.RELIGION_CONVERSION:MutationKind.COUNTY_TASK;
            MutationSource source=conversion?MutationSource.RELIGION_CONVERSION:MutationSource.COUNTY_TASK;
            NativeRequest primitive=new NativeRequest(step,Optional.empty(),raw(fields));validatePrivateUnchecked(primitive);
            boundFields(fields,command.before().frame().identity().nativeRevision(),command.before().frame().revision(),command.before().frame().identity().dateRaw(),command.before().frame().identity().player());
            mutationAdmission.verify(kind,command);return primitive;
        }
        public ReadContract<CreationContext> creationContract(){return creation;}
        public ReadContract<DecisionDetail> detailContract(){return detail;}
        public ReadContract<ConversionResult> conversionResultContract(){return religion;}
        public ReadContract<CountyResult> countyResultContract(){return county;}
        public ReadContract<ConversionResult> conversionReconciliationContract(){return religionReconciliation;}
        public ReadContract<CountyResult> countyReconciliationContract(){return countyReconciliation;}
        private <T> ReadContract<T> reconciliationContract(ReadKind kind,Function<PlanningReadReceipt,T> decoder) {
            need(kind==ReadKind.RELIGION_RESULT||kind==ReadKind.COUNTY_RESULT,"only independent action results allow factual reconciliation");
            return new ReadContract<>("religion/reconciliation/"+kind.name().toLowerCase(java.util.Locale.ROOT),new OperationKey(kind.step()),Optional.empty(),kind.permission(),
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,kind.wireProfile(),ReadContract.GuardMode.RECONCILIATION_OBSERVATION,source(kind),
                    (request,requestId)->{readAdmission.verify(kind,request);return prepareRead(kind,request);},decoder,decoder);
        }
        private static void validatePrivate(NativeRequest request)throws IOException{try{validatePrivateUnchecked(request);}catch(IllegalArgumentException malformed){throw new IOException("private religion typed request invalid",malformed);}}
        private static void validatePrivateUnchecked(NativeRequest request){need(request.requiredCapability().isEmpty(),"private primitive cannot invent capability");ObjectNode n=parse(request.additionalFields());String common="expected_snapshot_revision expected_public_revision expected_date_raw expected_player_character_id action_id";number(n,"expected_snapshot_revision",BigInteger.ONE,U64);number(n,"expected_public_revision",BigInteger.ONE,U64);i32(n,"expected_date_raw");if(request.step().equals("county-conversion-task-submit-private-v1")){need(i32(n,"expected_player_character_id")!=-1,"original County actor sentinel is invalid");}else number(n,"expected_player_character_id",BigInteger.ONE,U32.subtract(BigInteger.ONE));new OwnerId(text(n,"action_id"));if(request.step().equals("submit-player-religion-conversion-private-v1")){exact(n,common+" target_rite_id max_piety_cost_raw");id(n,"target_rite_id");number(n,"max_piety_cost_raw",BigInteger.ZERO,I64_MAX);}else{need(request.step().equals("county-conversion-task-submit-private-v1"),"unregistered private primitive");exact(n,common+" expected_active_task_id expected_incumbent_character_id province_id replace_existing_task");for(String key:List.of("expected_active_task_id","expected_incumbent_character_id","province_id"))number(n,key,BigInteger.ONE,I32_MAX);bool(n,"replace_existing_task");}}
    }
    private final PlanningReadPort reads;private final ActionCoordinatorPort actions;private final Registration registered;
    public ReligionCapabilities(PlanningReadPort reads,ActionCoordinatorPort actions,Registration registered){this.reads=Objects.requireNonNull(reads);this.actions=Objects.requireNonNull(actions);this.registered=Objects.requireNonNull(registered);}
    public PlanningReadResult<CreationContext> query_player_holy_site_creation_context_v1(Context c){build(c,Build.CROZIER4);return read(registered.creation,c,empty());}
    public PlanningReadResult<GhwPermissions> query_player_ghw_permissions_v1(Context c){build(c,Build.CROZIER4);ObjectNode n=empty();n.put("expected_date_raw",c.before().frame().identity().dateRaw());n.put("expected_actor_character_id",c.before().frame().identity().player());n.put("expected_game_pid",c.before().game().pid());n.put("expected_connection_generation",c.connectionGeneration());return read(registered.ghw,c,n);}
    public PlanningReadResult<DecisionDetail> query_player_holy_site_decision_detail_v1(Context c,Decision action,FullId holySite){build(c,Build.CROZIER4);return read(registered.detail,c,empty().put("action",action.wire()).put("holy_site_id",holySite.value()));}
    public PlanningReadResult<CooldownResult> query_player_holy_site_decision_cooldown_v1(Context c,Decision action){build(c,Build.CROZIER4);return read(registered.cooldown,c,empty().put("action",action.wire()));}
    public PlanningReadResult<IndulgenceTerms> query_player_seek_indulgences_terms_v1(Context c,FullId recipient){build(c,Build.CROZIER3);return read(registered.indulgences,c,empty().put("recipient_character_id",recipient.value()));}
    public ActionReceipt submit_player_religion_conversion_private_v1(ActionContext c,FullId targetRite,BigInteger maximumPiety,OwnerId actionId){build(c.frame(),Build.CROZIER3);range(maximumPiety,BigInteger.ZERO,I64_MAX);return action(c,"submit-player-religion-conversion-private-v1",actionBound(c.frame()).put("target_rite_id",targetRite.value()).put("max_piety_cost_raw",maximumPiety).put("action_id",actionId.value()));}
    public PlanningReadResult<ConversionResult> query_player_religion_conversion_result_private_v1(Context c,OwnerId requestId,OwnerId actionId){build(c,Build.CROZIER3);return read(registered.religion,c,actionBound(c).put("submitted_request_id",requestId.value()).put("action_id",actionId.value()));}
    public ActionReceipt submit_county_conversion_task_private_v1(ActionContext c,PositiveId activeTask,PositiveId incumbent,PositiveId province,boolean replaceExisting,OwnerId actionId){return action(c,"county-conversion-task-submit-private-v1",actionBound(c.frame()).put("expected_active_task_id",activeTask.value()).put("expected_incumbent_character_id",incumbent.value()).put("province_id",province.value()).put("replace_existing_task",replaceExisting).put("action_id",actionId.value()));}
    public PlanningReadResult<CountyResult> query_county_conversion_task_result_private_v1(Context c,OwnerId submittedRequestId,OwnerId actionId){return read(registered.county,c,actionBound(c).put("submitted_request_id",submittedRequestId.value()).put("action_id",actionId.value()));}
    public ActionReceipt create_holy_site_once_v1(ActionContext c,PreviewIdentity preview){build(c.frame(),Build.CROZIER4);ObjectNode n=ui("create_holy_site_once","holy_site_creation",BigInteger.ZERO).put("expected_preview_identity_sha256",preview.sha256()).put("expected_date_raw",c.frame().before().frame().identity().dateRaw()).put("expected_player_character_id",c.frame().before().frame().identity().player()).put("expected_connection_generation",c.frame().connectionGeneration());return action(c,NAVIGATE,n);}
    public ActionReceipt open_holy_site_creation_window_v1(ActionContext c){build(c.frame(),Build.CROZIER4);return action(c,NAVIGATE,ui("open_holy_site_creation","holy_site_creation",BigInteger.ZERO));}
    public ActionReceipt select_holy_site_creation_type_v1(ActionContext c,String typeKey){build(c.frame(),Build.CROZIER4);validateTypeKey(typeKey);return action(c,NAVIGATE,ui("select_holy_site_creation_type","holy_site_creation",BigInteger.ZERO).put("type_key",typeKey));}
    public ActionReceipt select_holy_site_creation_barony_v1(ActionContext c,FullId title){build(c.frame(),Build.CROZIER4);return action(c,NAVIGATE,ui("select_holy_site_creation_barony","holy_site_creation",title.value()));}
    public ActionReceipt open_holy_site_window_v1(ActionContext c,FullId holySite){build(c.frame(),Build.CROZIER4);return action(c,NAVIGATE,ui("open_holy_site","holy_site",holySite.value()));}
    public ActionReceipt open_holy_site_adoption_decision_v1(ActionContext c,FullId holySite){build(c.frame(),Build.CROZIER4);return action(c,NAVIGATE,ui("open_holy_site_adoption","holy_site",holySite.value()));}
    public ActionReceipt confirm_holy_site_adoption_decision_v1(ActionContext c,FullId holySite){build(c.frame(),Build.CROZIER4);return action(c,NAVIGATE,ui("confirm_site_adoption","holy_site_adoption",holySite.value()));}
    public ActionReceipt open_holy_site_decision_v1(ActionContext c,Decision action,FullId holySite){build(c.frame(),Build.CROZIER4);return action(c,NAVIGATE,ui("open_holy_site_adoption","holy_site",holySite.value()).put("holy_site_action",action.wire()));}
    public ActionReceipt confirm_holy_site_decision_v1(ActionContext c,Decision action,FullId holySite){build(c.frame(),Build.CROZIER4);return action(c,NAVIGATE,ui("confirm_site_adoption","holy_site_adoption",holySite.value()).put("holy_site_action",action.wire()));}
    public PlanningReadResult<Assembly> query_confucian_assembly_predicates_v1(Context c){return read(registered.assembly,c,empty());}
    public PlanningReadResult<ChallengerGraph> query_confucian_challenger_graph_v1(Context c,List<FullId> faiths){need(faiths.size()>=1&&faiths.size()<=8&&faiths.stream().distinct().count()==faiths.size(),"one to eight distinct full Faith IDs required");ObjectNode n=empty();var a=n.putArray("faith_full_ids");faiths.forEach(f->a.add(f.value()));return read(registered.challengers,c,n);}
    public PlanningReadResult<ReligiousTitle> query_confucian_religious_title_v1(Context c){return read(registered.title,c,empty());}
    public PlanningReadResult<Stress> query_current_actor_stress_adjustment_v1(Context c,int baseAmount){build(c,Build.CROZIER3);need(baseAmount>=-300&&baseAmount<=300,"stress base amount must be -300..300");return read(registered.stress,c,empty().put("base_amount",baseAmount).put("expected_player_character_id",c.before().frame().identity().player()).put("expected_game_pid",c.before().game().pid()).put("expected_connection_generation",c.connectionGeneration()));}
    public PlanningReadResult<EpidemicResult> query_player_epidemic_recovery_private_v1(Context c,EpidemicTarget target){Objects.requireNonNull(target);if(target instanceof EventCounties list)return read(registered.epidemic,c,empty().put("expected_event_instance_id",list.eventInstanceId()));PositiveId title=((ExplicitTitle)target).titleId();TitleRead fixed=registered.epidemicTitles.stream().filter(v->v.title().equals(title)).findFirst().orElseThrow(()->new IllegalArgumentException("explicit epidemic title contract must be installed by the root before querying"));return read(fixed.contract(),c,empty());}
    private <T> PlanningReadResult<T> read(ReadContract<T> contract,Context c,ObjectNode fields){return reads.read(contract,new PlanningReadRequest(c.before(),c.source(),c.sessionId(),contract.operation(),arguments(fields),c.deadline()));}
    private ActionReceipt action(ActionContext c,String step,ObjectNode fields){ActionCommand command=new ActionCommand(c.actionId(),c.frame().before(),c.frame().source(),c.frame().sessionId(),new OperationKey(step),arguments(fields),c.expected(),c.claims(),c.frame().deadline());return actions.execute(command);}
    private static void build(Context context,Build expected){need(context.build()==expected,"method requires exact "+expected.version());}
    private static ObjectNode actionBound(Context c){return empty().put("expected_snapshot_revision",c.before().frame().identity().nativeRevision()).put("expected_public_revision",c.before().frame().revision()).put("expected_date_raw",c.before().frame().identity().dateRaw()).put("expected_player_character_id",c.before().frame().identity().player());}
    private static void boundFields(ObjectNode n,BigInteger nativeRevision,BigInteger publicRevision,BigInteger date,BigInteger actor){equal(n,"expected_snapshot_revision",nativeRevision);equal(n,"expected_public_revision",publicRevision);equal(n,"expected_date_raw",date);equal(n,"expected_player_character_id",actor);}
    private static ObjectNode ui(String operation,String kind,BigInteger id){return empty().put("window_kind",kind).put("subject_id",id).put("operation",operation);}
    private static void validateTypeKey(String value){need(value!=null&&value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length>=1&&value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=160&&value.indexOf('\0')<0,"creation type must retain 1..160 UTF-8 bytes");}
    private static void validateUi(ObjectNode n){String op=text(n,"operation"),kind=text(n,"window_kind");BigInteger id=id(n,"subject_id");String extras="";
        switch(op){case "open_holy_site_creation" -> {need(kind.equals("holy_site_creation")&&id.signum()==0,"creation opening has no subject");}case "select_holy_site_creation_type" -> {need(kind.equals("holy_site_creation")&&id.signum()==0,"type selector has no subject");validateTypeKey(text(n,"type_key"));extras=" type_key";}case "select_holy_site_creation_barony" -> need(kind.equals("holy_site_creation"),"barony selector kind differs");case "open_holy_site" -> need(kind.equals("holy_site"),"HolySite open kind differs");case "open_holy_site_adoption","confirm_site_adoption" -> {need(kind.equals(op.equals("open_holy_site_adoption")?"holy_site":"holy_site_adoption"),"decision route kind differs");if(n.has("holy_site_action")){Decision.parse(text(n,"holy_site_action"));extras=" holy_site_action";}}case "create_holy_site_once" -> {need(kind.equals("holy_site_creation")&&id.signum()==0,"create current player model only");new PreviewIdentity(text(n,"expected_preview_identity_sha256"));i32(n,"expected_date_raw");number(n,"expected_player_character_id",BigInteger.ONE,I32_MAX);number(n,"expected_connection_generation",BigInteger.ONE,U64);extras=" expected_preview_identity_sha256 expected_date_raw expected_player_character_id expected_connection_generation";}default -> throw new IllegalArgumentException("unregistered religion UI operation");}exact(n,"window_kind subject_id operation"+extras);}
    private static NativeRequest prepareRead(ReadKind kind,PlanningReadRequest r){ObjectNode n=argumentNode(r.arguments());String fields="";switch(kind){case CREATION,ASSEMBLY,TITLE -> { }case DETAIL -> {fields="action holy_site_id";Decision.parse(text(n,"action"));id(n,"holy_site_id");}case COOLDOWN -> {fields="action";Decision.parse(text(n,"action"));}case INDULGENCES -> {fields="recipient_character_id";id(n,"recipient_character_id");}case CHALLENGERS -> {fields="faith_full_ids";List<BigInteger> ids=ids(n,"faith_full_ids",8);need(!ids.isEmpty(),"at least one Faith selector required");}case EPIDEMIC -> {fields="expected_event_instance_id";number(n,"expected_event_instance_id",BigInteger.ONE,U64);}case STRESS -> {fields="base_amount expected_player_character_id expected_game_pid expected_connection_generation";number(n,"base_amount",BigInteger.valueOf(-300),BigInteger.valueOf(300));equal(n,"expected_player_character_id",r.before().frame().identity().player());equal(n,"expected_game_pid",BigInteger.valueOf(r.before().game().pid()));number(n,"expected_connection_generation",BigInteger.ONE,U64);}case GHW -> {fields="expected_date_raw expected_actor_character_id expected_game_pid expected_connection_generation";equal(n,"expected_date_raw",r.before().frame().identity().dateRaw());equal(n,"expected_actor_character_id",r.before().frame().identity().player());equal(n,"expected_game_pid",BigInteger.valueOf(r.before().game().pid()));number(n,"expected_connection_generation",BigInteger.ONE,U64);}case COUNTY_RESULT,RELIGION_RESULT -> {fields="expected_snapshot_revision expected_public_revision expected_date_raw expected_player_character_id submitted_request_id action_id";var factual=ReligionJson.factual(r);boundFields(n,factual.frame().identity().nativeRevision(),factual.frame().revision(),factual.frame().identity().dateRaw(),factual.frame().identity().player());new OwnerId(text(n,"submitted_request_id"));new OwnerId(text(n,"action_id"));}}
        exact(n,fields);if(kind==ReadKind.EPIDEMIC)n=empty();return new NativeRequest(kind.step(),kind==ReadKind.STRESS?Optional.of(kind.permission()):Optional.empty(),raw(n));}
    static ObjectNode empty(){return JsonNodeFactory.instance.objectNode();}
    static ObjectNode argumentNode(OpportunityJson.Obj args){return ReligionJson.parse(new RawJson(OpportunityJson.encode(args)));}
    static String argumentText(OpportunityJson.Obj args,String key){return text(argumentNode(args),key);}
    static BigInteger argumentInteger(OpportunityJson.Obj args,String key){return number(argumentNode(args),key,I64_MIN,U64);}
    static List<BigInteger> argumentIds(OpportunityJson.Obj args,String key){return ids(argumentNode(args),key,8);}
    static OpportunityJson.Obj arguments(ObjectNode n){return OpportunityJson.object(OpportunityJson.parse(raw(n).bytes()),"typed religion request");}
    static RawJson raw(ObjectNode node){try{return new RawJson(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(node));}catch(IOException failure){throw new IllegalArgumentException("typed religion serialization failed",failure);}}
    static void verifySource(ExactRef expected){try{SharedSourceFiles.Witness witness=SharedSourceFiles.observe(Path.of(expected.path()));need(witness.source().bytes()==expected.bytes()&&witness.source().sha256().equals(expected.sha256()),"original producer source drift");SharedSourceFiles.assertUnchanged(witness);}catch(IOException failure){throw new IllegalArgumentException("original producer source unavailable",failure);}}
}
