package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.Optional;
import java.util.TreeMap;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsService;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionService;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeUiParsedReturn;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionCapabilities.ReadKind;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels.CreationContext;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NormalExitSourceInventory;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffObservation;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** One actual pre-Core ART source construction. It installs no second Nav binding, writer or inventory reader. */
public final class RootArtifactsSourcesFactory {
    private RootArtifactsSourcesFactory(){ }
    public static final String COMMAND_SCHEMA="xar.java.artifact-finite-navigation/v1";
    public static final String OBSERVER="xar.java.artifact-navigation-control/v1";
    public static final OperationKey NAVIGATE=new OperationKey("navigate-ingame-ui-v1");
    private static final Set<Method> NAVIGATION=Set.copyOf(EnumSet.of(Method.SELECT_RELIC,Method.RELIC_SLOT,
            Method.ENSHRINE,Method.REMOVE,Method.CREATION_SELECTION));

    /** Every value comes from the identical named Root constructor, including its real retired-runtime custody producer. */
    public record Input(RootRuntimeDefinitions.Inputs sameInputs,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals,RootRuntimeDomainSettings.Bound settings,
            RootSelectedRegistrationConfiguration.Bound registration,NativeLaunchPlan samePlan,
            RootRuntimeStorageGuard sameStorage,RootCoreBoundPorts samePorts,
            OriginalRuntimeHandoffProof.Provider relicOriginals,RootReligionPublicProducts.SharedKernel sameReligion,Clock clock) {
        public Input {
            for(Object value:List.of(sameInputs,selected,originals,settings,registration,samePlan,sameStorage,samePorts,relicOriginals,sameReligion,clock))
                Objects.requireNonNull(value);
        }
    }
    /** M6's public binder may expose precisely this set, independently of the other three original artifact actions. */
    public interface FiniteNavigationActions extends RootArtifactsPublicProducts.ActionProducts {
        Set<Method> supportedMethods();
    }
    public static Set<Method> navigationMethods(){return NAVIGATION;}
    public static Set<GuiService.NavigationSelector> navigationSelectors(){
        var result=new java.util.HashSet<GuiService.NavigationSelector>();
        for(Method method:NAVIGATION)result.add(selector(method));return Set.copyOf(result);
    }
    private static GuiService.NavigationSelector selector(Method method){
        require(NAVIGATION.contains(method),"only the five original artifact Nav selectors belong to this extension");
        return new GuiService.NavigationSelector(method==Method.CREATION_SELECTION?"holy_site_creation":"holy_site",method.operation());
    }

    /** No gui.add* call here: the one RootAdditionalDomains.Prepared constructor performs that installation exactly once. */
    public static RootArtifactsPublicProducts.Prepared prepare(Input actual,RootGuiPublicProducts.Prepared sameGui)throws IOException {
        Objects.requireNonNull(sameGui);Objects.requireNonNull(actual);requireInputs(actual);
        var factory=new Factory(actual,sameGui);
        var prepared=new RootArtifactsPublicProducts.Prepared(new RootArtifactsPublicProducts.Sources(factory.nativeSources(),
                factory.rootSource,List.of(),java.util.Optional.of(new RootArtifactsPublicProducts.ActionFactory(){
                    @Override public Set<Method> supportedMethods(){return factory.actionMethods();}
                    @Override public RootArtifactsPublicProducts.ActionProducts install(RootRuntimeContext same,ArtifactsService service)throws IOException {
                        return factory.actions(same,service);
                    }
                }),
                java.util.Optional.of(factory.navigation()),java.util.Optional.empty()));
        factory.prepared=prepared;
        requireInputs(actual);actual.selected().requireCurrent();actual.selected().requireLoadedClasses(actual.samePlan());
        return prepared;
    }
    public static RootArtifactsPublicProducts.Prepared prepareOrdinary(RootArtifactsPublicProducts.Config config,
            RootGuiPublicProducts.Prepared sameGui,RootReligionPublicProducts.SharedKernel sameReligion,
            RootCoreBoundPorts ports,RootAdditionalDomains.ImplementationMetadata metadata)throws IOException {
        var factory=new Factory(config,sameGui,sameReligion,ports,metadata);
        var prepared=new RootArtifactsPublicProducts.Prepared(new RootArtifactsPublicProducts.Sources(factory.nativeSources(),
                factory.rootSource,List.of(),Optional.of(new RootArtifactsPublicProducts.ActionFactory(){
                    @Override public Set<Method> supportedMethods(){return factory.actionMethods();}
                    @Override public RootArtifactsPublicProducts.ActionProducts install(RootRuntimeContext same,ArtifactsService service)throws IOException {
                        return factory.actions(same,service);
                    }
                }),Optional.of(factory.navigation()),Optional.empty()));
        factory.prepared=prepared;return prepared;
    }
    private static void requireInputs(Input actual)throws IOException {
        actual.settings().requireCurrent(actual.clock());actual.settings().requireManagedRoots(actual.sameStorage());
        actual.originals().requireCurrent(actual.clock());actual.originals().requireQualifiedCut(actual.samePlan());
        actual.registration().requireCurrent(actual.sameInputs(),actual.clock());actual.selected().requireCurrent();
        actual.selected().requireLoadedClasses(actual.samePlan());
        require(actual.registration().configuration().source(RootSelectedRegistrationConfiguration.SourceRole.ORIGINAL_NATIVE_DRIVER)
                .equals(actual.sameInputs().source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER)),
                "artifact and selected original registration use different exact Native driver sources");
        NormalExitSourceInventory.inspect(actual.settings().configuration().normalExit().input());
    }

    /** Strict immutable DATA retained in the existing ActionCommand; it cannot mint a frame or action qualification. */
    public static OpportunityJson.Obj commandArguments(Request request,Complete original){
        Objects.requireNonNull(request);Objects.requireNonNull(original);
        require(NAVIGATION.contains(request.method())&&request.expectedRevision().equals(original.identity().frame().revision()),
                "artifact command must retain its exact original named public request and captured revision");
        NativeFrame frame=ArtifactsService.actualFrame(original);
        require(frame.paused()&&frame.mapReady()&&frame.alive(),"artifact command requires its actual living paused player");
        var selector=selector(request.method());ObjectNode n=StrictJson.object().put("schema",COMMAND_SCHEMA)
                .put("window_kind",selector.windowKind()).put("operation",selector.operation())
                .put("_artifact_method",request.method().originalName()).put("_artifact_full_binding_sha256",original.fullBindingSha256());
        n.set("_artifact_request",ArtifactsCodec.encode(request));n.set("_artifact_original_frame",original.originalEvidence().toJson());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(n)),"original artifact Nav arguments");
    }
    public static Request request(OpportunityJson.Obj arguments){return decodeArguments(arguments).request();}
    private record Arguments(Request request,ExactRef originalFrame,String fullBindingSha256){ }
    private static Arguments decodeArguments(OpportunityJson.Obj arguments){
        ObjectNode n=StrictJson.object(OpportunityJson.toNode(arguments),Set.of("schema","window_kind","operation",
                "_artifact_method","_artifact_full_binding_sha256","_artifact_request","_artifact_original_frame"));
        require(StrictJson.text(n.get("schema")).equals(COMMAND_SCHEMA),"artifact Nav command version differs");
        Request request=ArtifactsCodec.decode(StrictJson.text(n.get("_artifact_method")),n.get("_artifact_request"));
        require(NAVIGATION.contains(request.method()),"another artifact method cannot enter the finite Nav extension");
        var selector=selector(request.method());require(StrictJson.text(n.get("window_kind")).equals(selector.windowKind())
                &&StrictJson.text(n.get("operation")).equals(selector.operation()),"artifact selector differs from its retained original request");
        String digest=StrictJson.text(n.get("_artifact_full_binding_sha256"));require(digest.matches("[0-9a-f]{64}"),"original full frame digest required");
        return new Arguments(request,ExactRef.fromJson(n.get("_artifact_original_frame")),digest);
    }

    public enum ScopeKind { MANAGED_NATIVE_CAMPAIGN_RUN, ONE_LIFE_EPISODE }
    public record LegacyScope(String machineId,long actor,ScopeKind kind,String runId){
        public LegacyScope {
            require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),"known original claim machine required");
            require(actor>0&&actor<=0xfffffffeL&&runId!=null&&!runId.isEmpty()&&runId.length()<=256,"actual original claim actor/run required");
            Objects.requireNonNull(kind);
        }
    }
    public record LegacyFile(String name,RawJson original){
        public LegacyFile {Objects.requireNonNull(original);require(name!=null&&(name.matches("[0-9a-f]{64}\\.pending\\.json")
                ||name.matches("[0-9a-f]{64}\\.relic-action-[A-Za-z0-9_-]{1,96}\\.result\\.json")),"unknown original relic store entry; no partial census");}
    }
    /** Complete old receipt DATA is audited. Neither a date nor a result ACK releases a surviving pending file. */
    public static List<String> legacyBlockers(List<LegacyFile> files,LegacyScope current){
        Objects.requireNonNull(current);var blockers=new ArrayList<String>();var names=new java.util.HashSet<String>();
        for(LegacyFile file:List.copyOf(files)){
            require(names.add(file.name()),"duplicate original relic store name");ObjectNode r=object(file.original());
            boolean pending=file.name().endsWith(".pending.json");var fields=new java.util.HashSet<>(Set.of("schema","machine_id","observed_at_utc",
                    "review_after_utc","protected_until_utc","storage_policy","retention_reason","machine_reader_sha256","request_id","intent",
                    "intent_sha256","cross_generation_replay_guard_sha256","expected_public_revision","expected_native_revision","connection_generation",
                    "automatic_retry","business_outcome_observed"));
            if(!pending)fields.addAll(Set.of("native_result","native_raw_return_receipt"));StrictJson.object(r,fields);
            require(text(r,"schema").equals("holy-site-relic-consumed-intent-v1")&&!bool(r,"automatic_retry")&&!bool(r,"business_outcome_observed"),"old relic receipt cannot authorize retry or business completion");
            Instant.parse(text(r,"observed_at_utc"));Instant.parse(text(r,"review_after_utc"));Instant.parse(text(r,"protected_until_utc"));
            digest(text(r,"machine_reader_sha256"));text(r,"retention_reason");
            var policy=StrictJson.object(r.get("storage_policy"),Set.of("policy_version","policy_sha256","policy_path","protection_max_hours"));
            require(policy.get("policy_version").isTextual(),"original storage policy version must retain its required string type");
            digest(text(policy,"policy_sha256"));text(policy,"policy_path");integer(policy,"protection_max_hours",BigInteger.ONE,BigInteger.valueOf(168));
            String requestId=text(r,"request_id");require(requestId.matches("relic-action-[A-Za-z0-9_-]{1,96}"),"old original protocol request identity differs");
            BigInteger revision=integer(r,"expected_public_revision",BigInteger.ONE,StrictJson.UINT64_MAX);
            integer(r,"expected_native_revision",BigInteger.ONE,StrictJson.UINT64_MAX);
            BigInteger generation=integer(r,"connection_generation",BigInteger.ONE,StrictJson.UINT64_MAX);
            ObjectNode intent=object(r.get("intent"));require(text(intent,"machine_id").equals(text(r,"machine_id"))
                    &&text(intent,"game_version").equals(VERSION)&&text(intent,"executable_sha256").equalsIgnoreCase(EXECUTABLE_SHA256)
                    &&integer(intent,"connection_generation",BigInteger.ONE,StrictJson.UINT64_MAX).equals(generation),"old original intent machine/build/generation differs");
            integer(intent,"date_raw",BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE));long actor=full(intent,"played_character_id");require(actor>0,"old actual actor required");
            Request original=legacyRequest(intent,revision);var scope=object(intent.get("scope"));ScopeKind kind;
            String run;
            if(text(scope,"kind").equals("managed_native_campaign_run")){StrictJson.object(scope,Set.of("kind","managed_run_id"));kind=ScopeKind.MANAGED_NATIVE_CAMPAIGN_RUN;run=text(scope,"managed_run_id");}
            else {StrictJson.object(scope,Set.of("kind","episode_run_id"));require(text(scope,"kind").equals("one_life_episode"),"unknown old original scope");kind=ScopeKind.ONE_LIFE_EPISODE;run=text(scope,"episode_run_id");}
            var originalScope=new LegacyScope(text(r,"machine_id"),actor,kind,run);
            String hash=ActionCodec.sha256(pythonIdentity(intent).getBytes(StandardCharsets.UTF_8));var replay=intent.deepCopy();replay.remove("connection_generation");
            String cross=ActionCodec.sha256(pythonIdentity(replay).getBytes(StandardCharsets.UTF_8));
            require(hash.equals(text(r,"intent_sha256"))&&cross.equals(text(r,"cross_generation_replay_guard_sha256")),"old intent or cross-generation digest differs from complete original fields");
            require(file.name().equals(pending?cross+".pending.json":hash+"."+requestId+".result.json"),"old original receipt filename does not bind its full identity");
            boolean sameScope=originalScope.machineId().equals(current.machineId())&&originalScope.kind()==current.kind()&&originalScope.runId().equals(current.runId());
            // A surviving pending file is never cleared by expiry, a changed date/actor or a result sidecar.
            if(pending){if(sameScope)blockers.add(file.name());}
            else {
                if(!r.get("native_raw_return_receipt").isNull()) {
                    ObjectNode returned=StrictJson.object(r.get("native_raw_return_receipt"),Set.of("path","bytes","sha256","validation_state"));
                    require(Path.of(text(returned,"path")).isAbsolute()&&text(returned,"validation_state").equals("unvalidated"),"old raw return retains only unvalidated original DATA");
                    integer(returned,"bytes",BigInteger.ONE,BigInteger.valueOf(RawJson.MAXIMUM_BYTES));digest(text(returned,"sha256"));
                }
                if(legacyResultUnresolved(object(r.get("native_result")),original)&&sameScope)blockers.add(file.name());
            }
        }
        return List.copyOf(blockers);
    }
    private static Request legacyRequest(ObjectNode intent,BigInteger revision){
        String operation=text(intent,"operation");Method method=NAVIGATION.stream().filter(m->m!=Method.CREATION_SELECTION&&m.operation().equals(operation)).findFirst()
                .orElseThrow(()->new IllegalArgumentException("old consumed relic operation differs"));
        var nativeKeys=new java.util.HashSet<>(Set.of("machine_id","game_version","executable_sha256","connection_generation","scope","date_raw",
                "played_character_id","window_kind","operation","subject_id"));
        var request=StrictJson.object().put("expected_revision",revision.toString()).put("holy_site_id",full(intent,"subject_id"));
        require(text(intent,"window_kind").equals("holy_site"),"old relic window kind differs");
        if(method==Method.RELIC_SLOT){nativeKeys.addAll(Set.of("relic_slot_index","relic_desired_selected"));request.put("slot_index",integer(intent,"relic_slot_index",BigInteger.ZERO,BigInteger.valueOf(4095)));request.put("desired_selected",bool(intent,"relic_desired_selected"));}
        else {nativeKeys.add("relic_artifact_id");request.put("artifact_id",full(intent,"relic_artifact_id"));
            if(method==Method.ENSHRINE||method==Method.REMOVE){nativeKeys.addAll(Set.of("relic_expected_replacing_empty","relic_expected_preview_sha256"));
                boolean empty=bool(intent,"relic_expected_replacing_empty");request.put("expected_replacing_empty",empty);request.put("expected_preview_sha256",text(intent,"relic_expected_preview_sha256"));
                if(!empty){nativeKeys.add("relic_expected_replacing_artifact_id");request.put("expected_replacing_artifact_id",full(intent,"relic_expected_replacing_artifact_id"));}
                if(method==Method.ENSHRINE){nativeKeys.add("relic_expected_effective_slot_index");request.put("expected_effective_slot_index",integer(intent,"relic_expected_effective_slot_index",BigInteger.ZERO,BigInteger.valueOf(4095)));}}
        }
        StrictJson.object(intent,nativeKeys);return ArtifactsCodec.decode(method.originalName(),request);
    }
    private static boolean legacyResultUnresolved(ObjectNode r,Request request){
        StrictJson.object(r,Set.of("available","status","loaded_source_pins_verified","native_dispatch_attempted","dispatch_invoked","verification_pending",
                "already_in_requested_state","selection_postcondition_observed","original_button_enabled_observed","original_button_enabled",
                "actual_button_presentation_observed","button_child_path","frozen_preview_verified","gameplay_command_may_have_been_queued",
                "business_outcome_observed","action_ready","before","after","unavailable_reason"));
        for(String key:List.of("available","loaded_source_pins_verified","native_dispatch_attempted","dispatch_invoked","verification_pending",
                "already_in_requested_state","selection_postcondition_observed","original_button_enabled_observed","actual_button_presentation_observed",
                "frozen_preview_verified","gameplay_command_may_have_been_queued","business_outcome_observed","action_ready"))bool(r,key);
        require(!bool(r,"business_outcome_observed")&&!bool(r,"action_ready"),"old result DATA cannot grant business completion");
        text(r,"status");
        for(String key:List.of("button_child_path","unavailable_reason")){
            JsonNode value=r.get(key);
            require(value!=null&&value.isTextual(),"exact original relic result text required: "+key);
            if(!value.textValue().isEmpty())StrictJson.text(value);
        }
        boolean gameplay=request.method()==Method.ENSHRINE||request.method()==Method.REMOVE,attempted=bool(r,"native_dispatch_attempted");
        require(Set.of("unavailable","acknowledged_verification_pending","dispatch_result_unknown","already_in_requested_state_verification_pending").contains(text(r,"status")),"unknown old original native status");
        require(bool(r,"available")==bool(r,"dispatch_invoked")||bool(r,"already_in_requested_state"),"old availability lacks an original callback ACK");
        require(!bool(r,"dispatch_invoked")||attempted||bool(r,"already_in_requested_state"),"old callback has no actual attempted/already-observed selection");
        require(!attempted||bool(r,"loaded_source_pins_verified")&&bool(r,"verification_pending"),"old native attempt lacks source/pending evidence");
        require(bool(r,"gameplay_command_may_have_been_queued")== (gameplay&&attempted),"old queue uncertainty differs from original native operation");
        if(bool(r,"original_button_enabled_observed"))bool(r,"original_button_enabled");else require(r.get("original_button_enabled").isNull(),"old unobserved button must stay null");
        ObjectNode before=legacySelection(r.get("before")),after=legacySelection(r.get("after"));
        if(gameplay){require(!bool(r,"selection_postcondition_observed")&&!bool(r,"already_in_requested_state"),"old selection cannot become an enshrine/remove business effect");return attempted;}
        if(!attempted&&!bool(r,"gameplay_command_may_have_been_queued"))return false;
        if(!bool(r,"selection_postcondition_observed"))return true;
        require(bool(before,"available")&&bool(after,"available")&&before.get("slot_artifact_ids").equals(after.get("slot_artifact_ids")),"old selection result lacks complete unchanged original inventory");
        if(request instanceof RelicPair pair)require(full(after,"artifact_id")==pair.artifactId()&&before.get("slot_index").equals(after.get("slot_index")),"old selected artifact differs from original request");
        else {var slot=(RelicSlot)request;require(before.get("artifact_id").equals(after.get("artifact_id"))
                &&(after.get("slot_index").isIntegralNumber()&&after.get("slot_index").bigIntegerValue().equals(BigInteger.valueOf(slot.slotIndex())))==slot.desiredSelected(),"old selected slot differs from original request");}
        return false;
    }
    private static ObjectNode legacySelection(JsonNode value){
        var r=StrictJson.object(value,Set.of("available","artifact_id","slot_index","slot_artifact_ids","unavailable_reason"));bool(r,"available");String reason=selectionReason(r);
        if(!r.get("artifact_id").isNull())full(r,"artifact_id");BigInteger slot=r.get("slot_index").isNull()?null:integer(r,"slot_index",BigInteger.ZERO,BigInteger.valueOf(4095));
        if(bool(r,"available")){require(r.get("slot_artifact_ids").isArray()&&r.get("slot_artifact_ids").size()<=4096&&reason.isEmpty(),"old inventory vector/reason is not complete/bounded");
            for(JsonNode item:r.get("slot_artifact_ids"))if(!item.isNull())StrictJson.integer(item,BigInteger.ZERO,new BigInteger("4294967294"));
            require(slot==null||slot.intValueExact()<r.get("slot_artifact_ids").size(),"old selected inventory slot is not an actual row");}
        else require(r.get("slot_artifact_ids").isNull()&&!reason.isEmpty(),"unobserved old inventory must retain its diagnostic and null slots");return r;
    }
    /** Python's original sort_keys/compact/default ensure_ascii identity, not the public JSON presentation grammar. */
    static String pythonIdentity(JsonNode value){
        if(value.isObject()){var fields=new TreeMap<String,JsonNode>();value.properties().forEach(e->fields.put(e.getKey(),e.getValue()));var rows=new ArrayList<String>();
            fields.forEach((key,child)->rows.add(pythonQuote(key)+":"+pythonIdentity(child)));return "{"+String.join(",",rows)+"}";}
        if(value.isTextual())return pythonQuote(value.textValue());
        require(value.isIntegralNumber()||value.isBoolean()||value.isNull(),"old original identity has unsupported JSON type");return value.toString();
    }
    private static String pythonQuote(String value){var result=new StringBuilder().append((char)34);for(int i=0;i<value.length();i++){
        char c=value.charAt(i);if(c==34||c==92)result.append((char)92).append(c);
        else if(c==8)result.append((char)92).append('b');else if(c==9)result.append((char)92).append('t');else if(c==10)result.append((char)92).append('n');
        else if(c==12)result.append((char)92).append('f');else if(c==13)result.append((char)92).append('r');
        else if(c<32||c>126)result.append((char)92).append('u').append(String.format(java.util.Locale.ROOT,"%04x",(int)c));else result.append(c);
    }return result.append((char)34).toString();}
    private static ObjectNode object(RawJson value){return object(StrictJson.parse(value.bytes(),1048576));}
    private static ObjectNode object(JsonNode value){
        if(!(value instanceof ObjectNode object))throw new IllegalArgumentException("actual artifact JSON object required");
        return object;
    }
    private static String text(ObjectNode value,String key){return StrictJson.text(value.get(key));}
    private static String selectionReason(ObjectNode value){
        JsonNode node=value.get("unavailable_reason");require(node!=null&&node.isTextual(),"exact original selection diagnostic text required");
        return node.textValue().isEmpty()?"":StrictJson.text(node);
    }
    private static boolean bool(ObjectNode value,String key){JsonNode n=value.get(key);require(n!=null&&n.isBoolean(),"exact original boolean required: "+key);return n.booleanValue();}
    private static BigInteger integer(ObjectNode value,String key,BigInteger low,BigInteger high){return StrictJson.integer(value.get(key),low,high);}
    private static long full(ObjectNode value,String key){return integer(value,key,BigInteger.ZERO,new BigInteger("4294967294")).longValueExact();}
    private static void digest(String value){require(value.matches("[0-9a-f]{64}"),"canonical original lowercase SHA required");}

    /** Exact source roles, not a filename heuristic or a claim that source presence grants a Native capability. */
    public static String nativePrimary(Method method){return switch(Objects.requireNonNull(method)){
        case PERSONAL_ITEM,PERSONAL_SUBMIT,PERSONAL_POST->"current_player_observers12004.cpp";
        case OPEN,OPEN_POST,CLOSE,CLOSE_QUERY,CLOSE_POST->"player_inventory_window12004_transport.cpp";
        case KNIGHT,SKILLS->"character_skill_effect12004_request.cpp";
        case RELIC_CONTEXT->"ck3_12004_holy_site_relic_context.cpp";
        case RELIC_PERMISSIONS->"ck3_12004_holy_site_relic_permissions.cpp";
        case RELIC_ACTION_CONTEXT->"ck3_12004_holy_site_relic_action_context.cpp";
        case SELECT_RELIC,RELIC_SLOT,ENSHRINE,REMOVE->"holy_site_relic_navigation12004.cpp";
        case CREATION_SELECTION->"holy_site_creation12004_navigation.cpp";
    };}
    private static final List<String> NATIVE=List.of("bridge.cpp","current_player_observers12004.cpp",
            "artifact_personal_use12004.cpp","artifact_personal_use12004_native.cpp","player_inventory_window12004_transport.cpp",
            "player_inventory_window12004_json.cpp","character_skill_effect12004_request.cpp","character_skill_effect12004.cpp",
            "character_skill_effect12004_native.cpp","character_skill_effect12004_json.cpp","character_skill_effect12004_mailbox.cpp",
            "ck3_12004_holy_site_relic_context.cpp","ck3_12004_holy_site_relic_context_json.cpp",
            "ck3_12004_holy_site_relic_permissions.cpp","ck3_12004_holy_site_relic_permissions_json.cpp",
            "ck3_12004_holy_site_relic_action_context.cpp","ck3_12004_holy_site_relic_action_context_json.cpp",
            "ck3_12004_holy_site_relic_recognition_matrix.cpp","ck3_12004_holy_site_relic_recognition_matrix_json.cpp",
            "ck3_12004_holy_site_modifier_aggregate.cpp","ck3_12004_holy_site_modifier_aggregate_json.cpp",
            "ck3_12004_holy_site_relic_actions.cpp","ck3_12004_holy_site_relic_actions_json.cpp",
            "holy_site_relic_navigation12004.cpp","holy_site_relic_request12004.cpp","holy_site_relic_action_preview_adapter12004.cpp",
            "ingame_ui_navigation_v1.cpp","ingame_ui_mailbox_v1.cpp","ck3_12004_ingame_ui.cpp",
            "holy_site_creation12004.cpp","holy_site_creation12004_mailbox.cpp","holy_site_creation12004_json.cpp",
            "holy_site_creation12004_navigation.cpp");
    private static final List<String> PYTHON=List.of("mcp_server.py","service.py","native_driver.py","version_identity.py",
            "faith_observers_private_transport_v1.py","artifact_personal_use_action_private_transport_v1.py",
            "player_inventory_window_private_transport_v1.py","player_inventory_window_close_private_transport_v1.py",
            "character_knight_effectiveness_private_transport_v1.py","character_skill_effects_private_transport_v1.py",
            "player_holy_site_relic_context_private_transport.py","player_holy_site_relic_permissions_private_transport.py",
            "player_holy_site_relic_action_context_private_transport.py","relic_action_private_transport.py",
            "holy_site_relic_recognition_matrix.py","holy_site_relic_rarity_decomposition.py","holy_site_modifier_aggregate_observation.py",
            "holy_site_creation_ui_contract.py","ingame_ui_contract.py","normal_exit_source_inventory_v1.py",
            "g2_private_query_transport.py","nonwar_private_build.py");

    /** Reads the original qualified cut only. Fresh measuring an arbitrary same-named cpp cannot satisfy this selection. */
    static Map<String,ExactRef> nativeSources(Path actualSourceRoot,List<FileRef> qualifiedCut)throws IOException {
        Objects.requireNonNull(actualSourceRoot);var result=new java.util.LinkedHashMap<String,ExactRef>();
        for(String name:NATIVE){Path expected=actualSourceRoot.resolve(name).toRealPath();
            List<FileRef> found=List.copyOf(qualifiedCut).stream().filter(ref->Path.of(ref.path()).toAbsolutePath().normalize()
                    .equals(expected)).toList();
            if(found.size()!=1)throw new IOException("exact artifact native producer missing or duplicated in original qualified cut: "+name);
            FileRef ref=found.getFirst();ref.verify();result.put(name,new ExactRef(ref.path(),ref.bytes(),ref.sha256()));}
        return Map.copyOf(result);
    }

    /** Pure post-control comparison after each packet has passed the single ArtifactsCodec producer decoder. */
    static void verifyRelicSelection(Request request,ObjectNode nativeNavigation,ObjectNode permissions,BigInteger actionEpoch){
        require(request.method()==Method.SELECT_RELIC||request.method()==Method.RELIC_SLOT,"gameplay relic callbacks cannot become selection controls");
        require(integer(permissions,"capture_epoch",BigInteger.ONE,StrictJson.UINT64_MAX).compareTo(actionEpoch)>0,
                "independent relic context must be sampled after the original GUI owner epoch");
        ObjectNode window=object(permissions.get("window_context")),slots=object(permissions.get("site_inventory_slots"));
        ObjectNode nativeAction=object(nativeNavigation.get("holy_site_relic_action"));
        ObjectNode after=legacySelection(nativeAction.get("after"));
        require(bool(window,"available")&&bool(window,"root_present")&&bool(slots,"available")&&bool(after,"available"),"independent same-site window/inventory is unavailable");
        var vector=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();require(slots.get("slots").isArray(),"complete independent relic inventory rows required");
        for(JsonNode row:slots.get("slots"))vector.add(object(row).get("artifact_id"));
        require(vector.equals(after.get("slot_artifact_ids")),"relic inventory changed after the native selection observation");
        long site=request instanceof RelicPair pair?pair.holySiteId():((RelicSlot)request).holySiteId();
        require(full(window,"selected_holy_site_id")==site&&window.get("selected_artifact_id").equals(after.get("artifact_id"))
                &&window.get("selected_slot_index").equals(after.get("slot_index")),"independent relic selection differs from its original observed post-state");
        if(request instanceof RelicPair pair)require(full(window,"selected_artifact_id")==pair.artifactId(),"independent selected artifact differs from requested full ID");
        else {var chosen=(RelicSlot)request;require((window.get("selected_slot_index").isIntegralNumber()
                &&window.get("selected_slot_index").bigIntegerValue().equals(BigInteger.valueOf(chosen.slotIndex())))==chosen.desiredSelected(),"independent selected slot differs from request");}
    }
    /** Preserves actual correlated parsed DATA before any UI/business normalizer. It grants no current or effect qualification. */
    static ExactRef preserveParsedReturn(NativeOutcomeArchive actualArchive,Session same,ActionCommand command,
            ActionState.Attempt attempt,NativeActionPort.AckReceived ack,Complete before)throws IOException {
        Objects.requireNonNull(actualArchive).writer().requireSession(same);
        require(command.operation().equals(NAVIGATE)&&before.identity().equals(command.before())&&before.source().equals(command.source())
                &&before.sessionId().equals(command.sessionId())&&attempt.guard().observed().equals(before.identity())
                &&attempt.guard().source().equals(before.source())&&attempt.guard().sessionId().equals(before.sessionId())
                &&attempt.requestId().equals(ack.requestId()),"parsed UI return crossed its actual command/guard/frame/request");
        ack.custody().orElseThrow(()->new IllegalArgumentException("actual parsed UI return custody absent")).verify(ack,attempt.guard());
        byte[] sent=ack.outbound().orElseThrow(()->new IllegalArgumentException("actual UI outbound packet absent")).originalPacket();
        var request=NativeWire.decodeExecuteRequest(sent);
        require(request.requestId().equals(attempt.requestId())&&request.step().equals(NAVIGATE.value())
                &&request.expectedRevision().equals(Optional.of(before.identity().frame().identity().nativeRevision())),"parsed UI outbound differs from the actual original before frame");
        var response=NativeWire.decode(ack.originalPacket());require(response instanceof NativeWire.CommandResult,"actual parsed UI command_result absent");
        var result=(NativeWire.CommandResult)response;
        require(result.requestId().equals(attempt.requestId())&&result.nativeOk()==ack.nativeOk()
                &&java.util.Arrays.equals(result.payload().value(),ack.originalFrame().bytes()),"parsed UI incoming bytes differ from the actual ACK");
        if(ack.originalResultToken().isPresent())require(result.result().token().isPresent()
                &&java.util.Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),"parsed UI result token differs from original packet");
        else require(result.result().presence()!=NativeWire.Presence.VALUE,"actual ACK lost its original result token");
        RawJson body=NativeUiParsedReturn.encode(sent,ack.originalPacket(),before.semantic());
        NativeUiParsedReturn.decode(body.bytes());
        ExactRef preserved=actualArchive.preserveArtifact(same,body.bytes(),NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
        byte[] readback=actualArchive.readArtifact(same,preserved,NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
        NativeUiParsedReturn.decode(readback);
        require(java.util.Arrays.equals(body.bytes(),readback),"original parsed UI artifact changed during same-writer readback");
        return preserved;
    }
    private sealed interface RuntimeAuthority permits LegacyAuthority,ManagedAuthority {
        RootCoreBoundPorts ports();
        RootReligionPublicProducts.SharedKernel religion();
        void requireCurrent()throws IOException;
    }
    private record LegacyAuthority(Input input) implements RuntimeAuthority {
        @Override public RootCoreBoundPorts ports(){return input.samePorts();}
        @Override public RootReligionPublicProducts.SharedKernel religion(){return input.sameReligion();}
        @Override public void requireCurrent()throws IOException{requireInputs(input);}
    }
    private record ManagedAuthority(RootCoreBoundPorts ports,RootReligionPublicProducts.SharedKernel religion,
            RootArtifactsPublicProducts.Config config) implements RuntimeAuthority {
        private ManagedAuthority {Objects.requireNonNull(ports);Objects.requireNonNull(religion);Objects.requireNonNull(config);}
        @Override public void requireCurrent()throws IOException{ports.requireCore();}
    }
    private static final class Factory {
        private final RuntimeAuthority authority;
        private final RootGuiPublicProducts.Prepared sameGui;
        private final ExactRef definition,decoder,rootSource,factorySource,parsedReturnSource,privateActionSource;
        private final ArtifactsService.Sources actualSources;
        private final RootArtifactsPrivateActions.Prepared privateActions;
        private RootApplicationAssembly.Core privateCore;
        private final IdentityHashMap<RootRuntimeContext,CompositeActions> composites=new IdentityHashMap<>();
        private final Map<Method,ExactRef> producers;
        private final List<ExactRef> closure;
        private final IdentityHashMap<RootRuntimeContext,Runtime> runtimes=new IdentityHashMap<>();
        private RootArtifactsPublicProducts.Prepared prepared;
        Factory(Input input,RootGuiPublicProducts.Prepared sameGui)throws IOException {
            this.authority=new LegacyAuthority(input);this.sameGui=sameGui;var selected=input.selected();
            definition=selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ArtifactsService.class);
            decoder=selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ArtifactsCodec.class);
            rootSource=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootArtifactsPublicProducts.class);
            factorySource=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootArtifactsSourcesFactory.class);
            // This DATA encoder is retained/loaded by the identical whole Root plan. It grants no private Native permission.
            parsedReturnSource=selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeUiParsedReturn.class);
            privateActionSource=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootArtifactsPrivateActions.class);
            var refs=new LinkedHashSet<ExactRef>(List.of(definition,decoder,rootSource,factorySource,
                    selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.class),
                    selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.religion.HolySiteDecoders.class)));
            Path nativeRoot=Path.of(input.originals().source(RootRuntimeNativeOriginals.Role.NATIVE_DISPATCHER).path()).getParent();
            var nativeRefs=RootArtifactsSourcesFactory.nativeSources(nativeRoot,input.samePlan().sources().nativeProof().expected().completeSources());
            for(var entry:nativeRefs.entrySet()) {
                ExactRef ref=entry.getValue();var retained=selected.original(new FileRef(ref.path(),ref.bytes(),ref.sha256()),RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP);
                // Dispatcher remains verified by the identical whole Native cut and Bound originals; avoid a duplicate local pin.
                if(!entry.getKey().equals("bridge.cpp"))refs.add(retained);
            }
            refs.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,OriginalRuntimeHandoffObservation.class));
            Path bridge=Path.of(input.registration().configuration().source(RootSelectedRegistrationConfiguration.SourceRole.ORIGINAL_NATIVE_DRIVER).path()).getParent();
            for(String name:PYTHON)refs.add(selected.original(FileRef.measure(bridge.resolve(name)),RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON));
            var actualInventory=input.settings().configuration().normalExit().input();
            refs.addAll(List.of(actualInventory.inventory(),actualInventory.originalManagedProfile(),actualInventory.immutableOriginalSettingsSnapshot()));
            require(refs.size()<=64,"complete artifact source closure exceeds its existing fixed bound");closure=List.copyOf(refs);
            var actual=new EnumMap<Method,ExactRef>(Method.class);for(Method method:Method.values())actual.put(method,nativeRefs.get(nativePrimary(method)));producers=Map.copyOf(actual);
            actualSources=createNativeSources();privateActions=new RootArtifactsPrivateActions.Prepared(actualSources,privateActionSource);
            require(privateActions.domainRegistrations().isEmpty()&&privateActions.privatePermissions().isEmpty(),
                    "private artifacts must reuse the actual canonical writer and the unique Service permissions");
        }
        Factory(RootArtifactsPublicProducts.Config config,RootGuiPublicProducts.Prepared sameGui,
                RootReligionPublicProducts.SharedKernel sameReligion,RootCoreBoundPorts ports,
                RootAdditionalDomains.ImplementationMetadata metadata) throws IOException {
            Objects.requireNonNull(metadata);this.sameGui=Objects.requireNonNull(sameGui);
            authority=new ManagedAuthority(ports,sameReligion,config);
            definition=metadata.implementation(ArtifactsService.class);decoder=metadata.implementation(ArtifactsCodec.class);
            rootSource=metadata.implementation(RootArtifactsPublicProducts.class);factorySource=metadata.implementation(RootArtifactsSourcesFactory.class);
            parsedReturnSource=metadata.implementation(NativeUiParsedReturn.class);privateActionSource=metadata.implementation(RootArtifactsPrivateActions.class);
            closure=java.util.stream.Stream.of(definition,decoder,rootSource,factorySource,parsedReturnSource,privateActionSource,
                    metadata.implementation(RootManagedSessionScope.class),
                    metadata.implementation(org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.class),
                    metadata.implementation(org.xar.ck3.control.nativebridge.capabilities.religion.HolySiteDecoders.class)).distinct().toList();
            var actual=new EnumMap<Method,ExactRef>(Method.class);for(Method method:Method.values())actual.put(method,definition);
            producers=Map.copyOf(actual);actualSources=createNativeSources();
            privateActions=new RootArtifactsPrivateActions.Prepared(actualSources,privateActionSource);
            require(privateActions.domainRegistrations().isEmpty()&&privateActions.privatePermissions().isEmpty(),
                    "private artifacts reuse the canonical writer and unique Service permissions");
        }
        private ArtifactsService.Sources nativeSources(){return actualSources;}
        private ArtifactsService.Sources createNativeSources(){return new ArtifactsService.Sources(definition,decoder,producers,closure,
                Set.copyOf(EnumSet.allOf(Method.class)),this::frame,this::inventory,(config,hello,guard,request)->{
                    authority.requireCurrent();return authority.ports().qualifyPrivate(config,hello,guard,request);});}
        private RootRuntimeContext current(Complete frame)throws IOException {
            var identity=new SessionIdentity(frame.identity().machineId(),frame.identity().game(),frame.sessionId());
            var context=authority.ports().requireCurrent(authority.ports().borrowedSession(),identity);
            require(context.core()==authority.ports().requireCore()&&context.source().equals(frame.source()),"artifact actual ports crossed Core/Game/source authority");
            context.collector().requireHeldFrame(authority.ports().borrowedSession(),frame);authority.requireCurrent();return context;
        }
        private NativeFrame frame(Complete frame)throws IOException {current(frame);return ArtifactsService.actualFrame(frame);}
        private String inventory(Complete frame)throws IOException {
            var context=current(frame);
            return switch(authority) {
                case LegacyAuthority legacy -> {
                    var proof=NormalExitSourceInventory.accept(legacy.input().settings().configuration().normalExit().input(),context.game());
                    proof.requireCurrent(context.game());yield proof.sha256();
                }
                case ManagedAuthority managed -> switch(managed.config().inventory()) {
                    case RootArtifactsPublicProducts.NativeInventoryDigest digest -> digest.sha256();
                    case RootArtifactsPublicProducts.InventoryDeferred deferred -> throw new IOException("DEFER: native inventory digest unavailable: "+deferred.reason());
                };
            };
        }
        private RootGuiPublicProducts.NavigationDefinition navigation(){
            var controls=Set.of(selector(Method.SELECT_RELIC),selector(Method.RELIC_SLOT),selector(Method.CREATION_SELECTION));
            var pending=Set.of(selector(Method.ENSHRINE),selector(Method.REMOVE));
            var metadata=new RootGuiPublicProducts.NavigationControlMetadata(OBSERVER,controls,pending);
            return new RootGuiPublicProducts.NavigationDefinition(navigationSelectors(),factorySource,Optional.empty(),
                    actual->runtime(actual).extension(),Optional.of(metadata));
        }
        private Set<Method> actionMethods(){return combinedMethods(navigationMethods(),privateActions.supportedMethods());}
        private synchronized RootArtifactsPublicProducts.ActionProducts actions(RootRuntimeContext actual,ArtifactsService service)throws IOException {
            authority.requireCurrent();require(service.sources()==actualSources&&actual.core()==authority.ports().requireCore(),
                    "artifact action aggregation requires identical actual Core, cached Sources and Service");
            CompositeActions prior=composites.get(actual);
            if(prior!=null){require(prior.service==service,"two artifact services for one composite context");return prior;}
            require(composites.size()<64,"bounded artifact aggregate context history exhausted");
            if(privateCore==null){privateActions.bindCore(actual.core());privateCore=actual.core();}
            else require(privateCore==actual.core(),"private artifact producer cannot rebind to another Core");
            Runtime navigation=runtime(actual,service);
            var originalPrivate=privateActions.install(actual,service);
            var installed=new CompositeActions(authority,actual,service,navigation,originalPrivate,actionMethods());
            composites.put(actual,installed);return installed;
        }
        // Root Prepared is acquired before the Factory monitor, matching the install -> actions path.
        private Runtime runtime(RootRuntimeContext actual)throws IOException {
            ArtifactsService sameService=prepared.install(actual).service();return runtime(actual,sameService);
        }
        private synchronized Runtime runtime(RootRuntimeContext actual,ArtifactsService service)throws IOException {
            require(actual.core()==authority.ports().requireCore(),"finite artifact extension belongs to another Core");
            Runtime prior=runtimes.get(actual);if(prior!=null){require(prior.service==service,"two artifact services for one actual context");return prior;}
            require(runtimes.size()<64,"artifact runtime context history exhausted");Runtime result=new Runtime(this,actual,service);
            runtimes.put(actual,result);return result;
        }
    }
    /** Pure composition of two actual finite producers, never an enumeration-based capability claim. */
    static Set<Method> combinedMethods(Set<Method> navigation,Set<Method> originalPrivate) {
        require(Set.copyOf(navigation).equals(navigationMethods()),"actual artifact Nav producer declaration differs");
        require(Set.copyOf(originalPrivate).equals(RootArtifactsPrivateActions.supportedMethods()),
                "actual artifact private producer declaration differs");
        var result=EnumSet.copyOf(navigation);require(java.util.Collections.disjoint(result,originalPrivate),
                "two artifact producers claim the same public action");result.addAll(originalPrivate);return Set.copyOf(result);
    }
    private static <T> List<T> joined(List<T> first,List<T> second) {
        var result=new ArrayList<T>(first);for(T value:second){require(result.stream().noneMatch(prior->prior==value),
                "the same actual installation object was contributed twice");result.add(value);}return List.copyOf(result);
    }
    /** Retain every concrete callable and its object identity; GUI alone still installs the Nav binding. */
    static RootDomainInstallation combinedInstallation(RootDomainInstallation navigation,RootDomainInstallation originalPrivate) {
        Objects.requireNonNull(navigation);Objects.requireNonNull(originalPrivate);require(navigation!=originalPrivate,
                "artifact producer installations must have distinct actual ownership");
        var required=new java.util.HashSet<>(navigation.requiredPending());required.addAll(originalPrivate.requiredPending());
        return new RootDomainInstallation("artifact-actual-navigation-and-private/v1",
                joined(navigation.domainRegistrations(),originalPrivate.domainRegistrations()),
                joined(navigation.reads(),originalPrivate.reads()),joined(navigation.readFamilies(),originalPrivate.readFamilies()),
                joined(navigation.actions(),originalPrivate.actions()),joined(navigation.composites(),originalPrivate.composites()),
                joined(navigation.archived(),originalPrivate.archived()),joined(navigation.actionFamilies(),originalPrivate.actionFamilies()),
                joined(navigation.compositeFamilies(),originalPrivate.compositeFamilies()),
                joined(navigation.frontendAdmissions(),originalPrivate.frontendAdmissions()),
                joined(navigation.pending(),originalPrivate.pending()),required,joined(navigation.policies(),originalPrivate.policies()),
                joined(navigation.completions(),originalPrivate.completions()),joined(navigation.fixedDomains(),originalPrivate.fixedDomains()),
                joined(navigation.familyDomains(),originalPrivate.familyDomains()),joined(navigation.compositeDomains(),originalPrivate.compositeDomains()));
    }
    private static final class CompositeActions implements RootArtifactsPublicProducts.ActionProducts {
        private final RuntimeAuthority authority;private final RootRuntimeContext context;private final ArtifactsService service;
        private final Runtime navigation;private final RootArtifactsPrivateActions.Installed originalPrivate;
        private final Set<Method> methods;private final RootDomainInstallation installation;
        CompositeActions(RuntimeAuthority authority,RootRuntimeContext context,ArtifactsService service,Runtime navigation,
                RootArtifactsPrivateActions.Installed originalPrivate,Set<Method> declared) {
            this.authority=authority;this.context=context;this.service=service;this.navigation=navigation;this.originalPrivate=originalPrivate;
            methods=combinedMethods(navigation.supportedMethods(),originalPrivate.supportedMethods());
            require(methods.equals(declared)&&navigation.privatePermissions().isEmpty()&&originalPrivate.privatePermissions().isEmpty(),
                    "actual artifact aggregate differs from its pre-Core declaration or duplicates Service permissions");
            installation=combinedInstallation(navigation.installation(),originalPrivate.installation());
        }
        @Override public Set<Method> supportedMethods(){return methods;}
        @Override public RootDomainInstallation installation(){return installation;}
        @Override public List<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public Reply execute(RootApplicationSession actualRoot,Request request,Instant deadline)throws IOException,InterruptedException {
            authority.requireCurrent();require(actualRoot==context.actions()&&context.core()==authority.ports().requireCore()
                    &&methods.contains(request.method()),"actual artifact aggregate crossed Root/Core/method ownership");
            if(navigation.supportedMethods().contains(request.method()))return navigation.execute(actualRoot,request,deadline);
            require(originalPrivate.supportedMethods().contains(request.method()),"actual private artifact producer does not own this method");
            return originalPrivate.execute(actualRoot,request,deadline);
        }
    }
    private static final class Runtime implements FiniteNavigationActions {
        private final Factory factory;
        private final RootRuntimeContext context;
        private final ArtifactsService service;
        private final RootDomainInstallation installation;
        private final ThreadLocal<Complete> activeFrame=new ThreadLocal<>();
        private final ThreadLocal<OriginalRuntimeHandoffProof.Lease> originalLease=new ThreadLocal<>();
        private final Optional<RootManagedSessionScope> managedScope;
        Runtime(Factory factory,RootRuntimeContext context,ArtifactsService service)throws IOException {
            this.factory=factory;this.context=context;this.service=service;
            managedScope=factory.authority instanceof ManagedAuthority?Optional.of(RootManagedSessionScope.bind(context,factory.closure)):Optional.empty();
            var pending=new RootDomainIntentPreparation.Binding("artifact-original-once/v1",factory.factorySource,Runtime::supports,(same,command)->{
                try {
                    context.writer().requireSession(same);Complete before=requireActive(command);
                    var prepared=ActionPreparationScope.requirePrepared(same,command);
                    if(request(command.arguments()).method()!=Method.CREATION_SELECTION) {
                        require(prepared.preparationEvidence().size()==1,"complete original relic census missing before INTENT");
                        ExactRef evidence=prepared.preparationEvidence().getFirst();
                        verifyIntentEvidence(command,before,evidence,context.archive().withSession(same));
                        if(managedScope.isPresent()) {
                            var observed=RootManagedSessionScope.decode(material(context.archive().withSession(same),evidence).bytes(),command,factory.closure);
                            require(observed.headSequence()==same.head().state().sequence()&&observed.headDigest().equals(same.head().digest()),
                                    "managed relic observation differs from the actual pre-INTENT writer point");
                            managedScope.orElseThrow().requireFrame(same,before);
                        } else {
                            ObjectNode captured=object(material(context.archive().withSession(same),evidence));
                            require(integer(captured,"capture_head_sequence",BigInteger.ZERO,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)).longValueExact()==same.head().state().sequence()
                                    &&text(captured,"capture_head_sha256").equals(same.head().digest()),"original relic census is not the actual pre-INTENT writer point");
                            census(same,before);
                        }
                    } else require(prepared.preparationEvidence().isEmpty(),"creation selection has no invented relic once store");
                    factory.authority.requireCurrent();requireNoPending(same);
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            installation=new RootDomainInstallation("artifact-finite-navigation",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                    List.of(),List.of(),List.of(),List.of(pending),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        private static boolean supports(ActionCommand command) {
            if(!command.operation().equals(NAVIGATE))return false;
            var node=OpportunityJson.toNode(command.arguments());return node.has("schema")&&node.get("schema").isTextual()
                    &&node.get("schema").textValue().equals(COMMAND_SCHEMA);
        }
        @Override public Set<Method> supportedMethods(){return navigationMethods();}
        @Override public RootDomainInstallation installation(){return installation;}
        @Override public List<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        private SessionIdentity identity(){return new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());}
        private Complete requireActive(ActionCommand command)throws IOException {
            Complete before=activeFrame.get();Arguments args=decodeArguments(command.arguments());
            require(before!=null&&before.identity().equals(command.before())&&before.source().equals(command.source())
                    &&before.sessionId().equals(command.sessionId())&&before.originalEvidence().equals(args.originalFrame())
                    &&before.fullBindingSha256().equals(args.fullBindingSha256()),"finite artifact command escaped its actual private Root capture");
            return before;
        }
        private void requireNoPending(Session same)throws IOException {
            context.writer().requireSession(same);var archive=context.archive().withSession(same);
            require(ContinuityActionJournal.receipts(same.head().state(),archive).stream().allMatch(ActionReceipt::settled),
                    "actual canonical unresolved action remains; artifact navigation cannot resubmit it");
        }
        private Path store(){return context.game().launchPlan().stateDirectory().resolve("native-session").resolve("holy-site-relic-action-intents").toAbsolutePath().normalize();}
        private static Path originalStore(Complete original){
            var paths=OpportunityJson.object(original.semantic().get("capability_session_paths"),"original source-bound Driver paths");
            Path driver=Path.of(OpportunityJson.text(paths.get("driver_state_path"),"original Driver state path"));
            require(driver.isAbsolute()&&driver.normalize().equals(driver)&&driver.getParent()!=null,"original Driver path must retain its complete absolute source");
            return driver.getParent().resolve("holy-site-relic-action-intents");
        }
        @Override public Reply execute(RootApplicationSession root,Request request,Instant deadline)throws IOException,InterruptedException {
            require(root==context.actions()&&context.core()==factory.authority.ports().requireCore(),"artifact actions crossed actual Root/Core");
            require(NAVIGATION.contains(request.method())&&activeFrame.get()==null,"only actual finite artifact navigation may enter Root once");
            if(request.method()==Method.CREATION_SELECTION)return executeRoot(root,request,deadline);
            if(managedScope.isPresent())return managedScope.orElseThrow().withScope(()->executeRoot(root,request,deadline));
            if(!(factory.authority instanceof LegacyAuthority legacy))throw new IOException("actual relic runtime authority is unavailable");
            var result=legacy.input().relicOriginals().withOriginalStore(store(),context.game().machineId(),lease->{
                require(originalLease.get()==null,"original relic lease cannot be replaced");originalLease.set(lease);
                try{return executeRoot(root,request,deadline);}
                catch(InterruptedException failure){Thread.currentThread().interrupt();throw new IOException("artifact navigation interrupted",failure);}
                finally{originalLease.remove();}
            });
            if(result instanceof OriginalRuntimeHandoffProof.Available<Reply> available)return available.value();
            if(result instanceof OriginalRuntimeHandoffProof.Unavailable<Reply> missing)
                throw new IOException("SOURCE_JOIN_REQUIRED: original relic custody "+missing.reason()+": "+missing.detail());
            throw new IOException("original relic custody has no qualified result");
        }
        private Reply executeRoot(RootApplicationSession root,Request request,Instant deadline)throws IOException,InterruptedException {
            try{return root.executePublicDecision(deadline,(frame,driver,same)->{
                require(activeFrame.get()==null,"artifact Root capture cannot nest");activeFrame.set(frame);
                factory.authority.requireCurrent();requireNoPending(same);
                if(managedScope.isPresent()&&request.method()!=Method.CREATION_SELECTION)managedScope.orElseThrow().requireFrame(same,frame);
                var args=commandArguments(request,frame);service.select(frame,request,deadline);
                String id=ActionIds.forDecision(frame.sessionId(),frame.identity(),"artifact-nav:"+ActionCodec.sha256(StrictJson.canonical(ArtifactsCodec.encode(request))));
                var expected=new ExpectedPostcondition(1,frame.identity(),frame.source(),OBSERVER,values());
                var claims=new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("foreground-window"));
                return new RootApplicationSession.SubmitPublicAction<Reply>(new ActionCommand(id,frame.identity(),frame.source(),frame.sessionId(),NAVIGATE,args,expected,claims,deadline));
            },(receipt,archive,same)->publication(same,receipt));}finally{activeFrame.remove();}
        }
        private GuiService.NavigationExtension extension(){
            var preparation=new ActionPorts.PreparationPort(){
                @Override public NativeRequest prepare(ActionCommand command){throw new IllegalStateException("artifact navigation requires original writer/request scope");}
                @Override public NativeRequest prepare(Session same,ActionCommand command,String requestId){
                    try {
                        context.writer().requireSession(same);Complete original=requireActive(command);requireNoPending(same);
                        List<ExactRef> evidence=request(command.arguments()).method()==Method.CREATION_SELECTION?List.of():List.of(intentEvidence(same,command,original));
                        return context.collector().currentOwned(same,identity(),command.deadline(),lease->{
                            Complete actual=lease.frame();require(actual.identity().equals(command.before())&&actual.source().equals(command.source())
                                    &&actual.sessionId().equals(command.sessionId()),"artifact physical frame changed before native preparation");
                            NativeRequest nativeRequest=service.prepare(service.select(actual,request(command.arguments()),command.deadline()),requestId);
                            return new NativeRequest(nativeRequest.step(),nativeRequest.requiredCapability(),nativeRequest.additionalFields(),evidence);
                        });
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                }
            };
            return new GuiService.NavigationExtension(navigationSelectors(),preparation,this::observe,this::verifyArchived,factory.factorySource);
        }
        private static List<ExpectedValue> values(){return List.of(new ExpectedBoolean(new FieldKey("artifact.selection_observed"),true));}
        private ActionPorts.PostconditionResult observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
            var parsed=new java.util.concurrent.atomic.AtomicReference<ExactRef>();
            try {
                if(!(dispatch instanceof NativeActionPort.AckReceived ack))return new ActionPorts.Pending("original artifact dispatch has no verified native ACK",List.of(attempt.guard().nativeEvidence()));
                return context.withSession(same->{var archive=context.archive().withSession(same);
                    Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
                    parsed.set(preserveParsedReturn(context.archive(),same,command,attempt,ack,before));
                    if(!ack.nativeOk())return new ActionPorts.Pending("original UI parsed return retained unvalidated; native ACK is RED",List.of(parsed.get()));
                    verifyOriginals(command,attempt,archive);
                    return context.collector().currentOwned(same,identity(),command.deadline(),lease->{
                        Complete after=lease.frame();Request request=request(command.arguments());
                        Reply reply=service.decodeAction(selection(before,request,command.deadline()),attempt,ack,ArtifactsService.actualFrame(after));
                        PlanningReadReceipt read=postRead(same,after,request,command.deadline());
                        var readRef=archive.readReferenceOf(read);
                        if(request.method()==Method.ENSHRINE||request.method()==Method.REMOVE)
                            return new ActionPorts.Pending("artifact callback may queue gameplay; independent ownership/payment/business effects remain unqualified",List.of(readRef,parsed.get()));
                        verifySelection(command,attempt,ack,before,read,archive,reply);
                        return new ActionPorts.ControlObserved(new ActionState.ControlApplied(read,OBSERVER,values()));
                    });
                });
            }catch(IOException|UncheckedIOException|IllegalArgumentException|IllegalStateException failure){
                return new ActionPorts.Pending("artifact independent post-state unavailable: "+failure.getMessage(),
                        parsed.get()==null?List.of(attempt.guard().nativeEvidence()):List.of(parsed.get()));
            }
        }
        private ArtifactsService.Selection selection(Complete frame,Request request,Instant deadline){
            return new ArtifactsService.Selection(frame,ArtifactsService.actualFrame(frame),request,Optional.empty(),deadline);
        }
        private PlanningReadReceipt postRead(Session same,Complete frame,Request original,Instant deadline)throws IOException {
            if(original instanceof CreationSelection){
                var contract=factory.authority.religion().legacyRegistration().creationContract();
                require(context.readCatalog().containsIdentity(contract),"creation post must use the identical installed M5 contract");
                var known=ReligionService.readKnown(context.reads(),context.archive().withSession(same),same,contract,
                        new ReligionService.ActualFrame(frame,context.transport().originalHello(),deadline),StrictJson.object());
                return known.receipt();
            }
            var selection=service.select(frame,permissions(original,frame.identity().frame().revision()),deadline);
            var result=context.reads().read(same,service.issue(context.readCatalog(),selection),service.request(selection));
            if(result instanceof PlanningReadResult.Known<Reply> known)return known.receipt();
            throw new IOException("actual post-navigation relic permissions unavailable: "+result);
        }
        private static RelicPermissions permissions(Request original,BigInteger revision){
            long site=original instanceof RelicPair r?r.holySiteId():original instanceof RelicSlot r?r.holySiteId():original instanceof Enshrine r?r.holySiteId():((Remove)original).holySiteId();
            return new RelicPermissions(revision,site,new org.xar.ck3.control.contracts.PublicUnsigned64.Missing());
        }
        private void verifyOriginals(ActionCommand command,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive)throws IOException {
            Arguments args=decodeArguments(command.arguments());Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
            require(before.identity().equals(command.before())&&before.source().equals(command.source())&&before.sessionId().equals(command.sessionId())
                    &&before.originalEvidence().equals(args.originalFrame())&&before.fullBindingSha256().equals(args.fullBindingSha256()),"artifact canonical guard differs from original public frame");
            NativeRequest prepared=attempt.preparedRequest();ObjectNode expected=ArtifactsCodec.nativeFields(args.request(),ArtifactsService.actualFrame(before),Optional.empty());
            require(prepared.step().equals(args.request().method().step())&&prepared.requiredCapability().equals(Optional.of("game.command.navigate-ingame-ui-v1"))
                    &&object(prepared.additionalFields()).equals(expected),"artifact actual outbound preparation differs from its sole original producer");
            if(args.request().method()==Method.CREATION_SELECTION)require(prepared.preparationEvidence().isEmpty(),"creation selection has no relic census");
            else {require(prepared.preparationEvidence().size()==1,"original relic census not retained");verifyIntentEvidence(command,before,prepared.preparationEvidence().getFirst(),archive);}
        }
        private void verifySelection(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,Complete before,
                PlanningReadReceipt read,ActionPorts.OutcomeArchive archive,Reply action)throws IOException {
            NativeRecordedEvidenceVerifier.requireRead(read,archive);Request request=request(command.arguments());
            Complete after=RootGuardEvidence.loadFrame(read.before().binding(),archive,context.frameLoader());
            Complete observed=RootGuardEvidence.loadFrame(read.after().binding(),archive,context.frameLoader());
            NativeFrame original=ArtifactsService.actualFrame(before),current=ArtifactsService.actualFrame(after),last=ArtifactsService.actualFrame(observed);
            requireSameNativeOwner(original,current);requireSameNativeOwner(current,last);
            require(after.identity().equals(read.request().before())&&after.source().equals(command.source())&&after.sessionId().equals(command.sessionId()),"independent artifact read belongs to another owner/source");
            require(action.facts().selectionPostconditionObserved()&&!action.facts().gameplayCommandMayHaveBeenQueued(),"native selection ACK lacks an actual requested-state observation");
            ObjectNode nativeBody=object(StrictJson.parse(ack.originalResultToken().orElseThrow().bytes(),StrictJson.EXPLICIT_MAX_BYTES));
            BigInteger actionEpoch=integer(nativeBody,"pump_epoch",BigInteger.ONE,StrictJson.UINT64_MAX);
            if(request instanceof CreationSelection chosen){
                var contract=factory.authority.religion().legacyRegistration().creationContract();
                require(contract.contractId().equals(read.contractId()),"creation post used another registered contract");
                CreationContext value=contract.replay(read);
                require(value.frame().availability().available()&&value.selectionAvailable()&&Boolean.TRUE.equals(value.windowPresent())
                        &&Boolean.TRUE.equals(value.rootPresent())&&Boolean.TRUE.equals(value.playerFaithMatches())
                        &&value.frame().captureEpoch().compareTo(actionEpoch)>0
                        &&value.selectedArtifacts().contains(BigInteger.valueOf(chosen.artifactId()))==chosen.selected(),
                        "independent creation context is not later or does not contain the requested selection");
            } else {
                var query=permissions(request,current.publicRevision());
                Reply decoded=service.decodeRead(selection(after,query,command.deadline()),read);
                require(decoded instanceof RelicPermissionsReply&&decoded.facts().available(),"independent relic permissions are unavailable");
                ObjectNode permissions=decoded.payload().original();
                verifyRelicSelection(request,nativeBody,permissions,actionEpoch);
            }
        }
        private static void requireSameNativeOwner(NativeFrame a,NativeFrame b){
            require(a.gamePid()==b.gamePid()&&a.gameCreationFiletime().equals(b.gameCreationFiletime())&&a.actorCharacterId()==b.actorCharacterId()
                    &&a.episodeRunId().equals(b.episodeRunId())&&a.connectionGeneration().equals(b.connectionGeneration())
                    &&a.executableSha256().equals(b.executableSha256())&&a.nativeRevision().equals(b.nativeRevision())&&a.dateRaw().equals(b.dateRaw())
                    &&b.paused()&&b.mapReady()&&b.alive(),"artifact independent read crossed actual physical/native owner");
        }
        private Reply publication(Session same,ActionReceipt receipt)throws IOException {
            factory.authority.requireCurrent();
            context.writer().requireSession(same);var archive=context.archive().withSession(same);
            ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),receipt,archive);
            ActionState.Attempt attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->new IOException("artifact INTENT remains UNKNOWN; original="+archive.receiptReferenceOf(receipt).path()));
            NativeActionPort.DispatchOutcome dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow(()->new IOException("artifact dispatch remains UNKNOWN; original="+archive.receiptReferenceOf(receipt).path()));
            if(!(dispatch instanceof NativeActionPort.AckReceived ack))throw new IOException("artifact original dispatch has no ACK; never replay "+receipt.command().actionId());
            Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
            ExactRef parsed=preserveParsedReturn(context.archive(),same,receipt.command(),attempt,ack,before);
            verifyOriginals(receipt.command(),attempt,archive);
            PlanningReadReceipt post;
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied control)post=control.read();
            else if(receipt.state() instanceof ActionState.Unknown unknown&&(unknown.evidence().size()==1||unknown.evidence().size()==2)) {
                // One original READ is the explicit retained v16 layout; v17 adds its distinct parsed DATA artifact second.
                // A parsed-only diagnostic fails the archive's strict READ decoder and never becomes a postcondition.
                post=archive.loadRead(unknown.evidence().getFirst());
                if(unknown.evidence().size()==2){ExactRef retained=unknown.evidence().get(1);
                    byte[] original=context.archive().readArtifact(same,retained,RawJson.MAXIMUM_BYTES);
                    byte[] actual=context.archive().readArtifact(same,parsed,RawJson.MAXIMUM_BYTES);
                    require(PublicDataJson.object(new RawJson(original)).equals(PublicDataJson.object(new RawJson(actual))),"retained parsed DATA differs from its actual original packets/snapshot");parsed=retained;}
            }
            else throw new IOException("artifact independent post-state remains UNKNOWN; original="+archive.receiptReferenceOf(receipt).path());
            NativeRecordedEvidenceVerifier.requireRead(post,archive);
            Complete after=RootGuardEvidence.loadFrame(post.before().binding(),archive,context.frameLoader());
            Reply normalized=service.decodeAction(selection(before,request(receipt.command().arguments()),receipt.command().deadline()),attempt,ack,ArtifactsService.actualFrame(after));
            return ArtifactsService.publishAction(normalized,new ArtifactsService.ActionPublication(before,receipt,archive.receiptReferenceOf(receipt),archive.referenceOf(ack),parsed));
        }
        private void verifyArchived(Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
            try {
                ActionState.Attempt attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();verifyOriginals(receipt.command(),attempt,archive);
                if(receipt.state() instanceof ActionState.Settled settled){
                    require(settled.settlement() instanceof ActionState.ControlApplied,"artifact navigation cannot grant business effects");
                    var control=(ActionState.ControlApplied)settled.settlement();
                    require(control.observerSchema().equals(OBSERVER)&&control.actual().equals(values())&&control.supportingReads().isEmpty(),"artifact control contract differs");
                    require(settled.dispatch() instanceof NativeActionPort.AckReceived,"artifact control lacks original ACK");
                    var ack=(NativeActionPort.AckReceived)settled.dispatch();Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
                    Complete after=RootGuardEvidence.loadFrame(control.read().before().binding(),archive,context.frameLoader());
                    Reply reply=service.decodeAction(selection(before,request(receipt.command().arguments()),receipt.command().deadline()),attempt,ack,ArtifactsService.actualFrame(after));
                    verifySelection(receipt.command(),attempt,ack,before,control.read(),archive,reply);
                }
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private LegacyScope scope(Complete before){
            JsonNode semantic=OpportunityJson.toNode(before.semantic()),managed=semantic.get("managed_campaign_run_binding");
            if(managed!=null&&!managed.isNull())return new LegacyScope(before.identity().machineId(),before.identity().frame().identity().player().longValueExact(),
                    ScopeKind.MANAGED_NATIVE_CAMPAIGN_RUN,text(object(managed),"managed_run_id"));
            return new LegacyScope(before.identity().machineId(),before.identity().frame().identity().player().longValueExact(),
                    ScopeKind.ONE_LIFE_EPISODE,before.identity().frame().episodeRunId());
        }
        private ExactRef intentEvidence(Session same,ActionCommand command,Complete before)throws IOException {
            if(managedScope.isEmpty())return census(same,before);
            var managed=managedScope.orElseThrow();managed.requireFrame(same,before);
            return context.archive().withSession(same).preserveMaterial(new RawJson(managed.observe(same,command)));
        }
        private void verifyIntentEvidence(ActionCommand command,Complete before,ExactRef reference,ActionPorts.OutcomeArchive archive)throws IOException {
            if(managedScope.isEmpty()){verifyCensus(command,before,reference,archive);return;}
            byte[] raw=material(archive,reference).bytes();
            var observed=RootManagedSessionScope.decode(raw,command,factory.closure);
            Session same=context.borrowedSession();context.writer().requireSession(same);
            RootManagedSessionScope.verifyArchived(context.core(),same,raw,command,factory.closure,observed.headDigest());
            var captured=same.requireHistoricalState(observed.headSequence(),observed.headDigest());
            require(ContinuityActionJournal.receipts(captured,archive).stream().allMatch(ActionReceipt::settled)
                    &&ContinuityActionJournal.lookup(captured,command.actionId(),archive).isEmpty(),
                    "managed relic observation did not precede a new unclaimed action in the canonical writer");
        }
        private ExactRef census(Session same,Complete before)throws IOException {
            context.writer().requireSession(same);var lease=originalLease.get();
            require(lease!=null,"original relic custody is unavailable; no filesystem absence shortcut");lease.requireCurrent();
            Path directory=store(),parent=directory.getParent();
            var paths=OpportunityJson.object(before.semantic().get("capability_session_paths"),"actual source-bound capability paths");
            Path driver=Path.of(OpportunityJson.text(paths.get("driver_state_path"),"actual original Driver state path"));
            require(driver.isAbsolute()&&driver.getParent()!=null&&driver.toAbsolutePath().normalize().getParent().resolve(directory.getFileName()).equals(directory)
                    &&lease.originalStore().equals(directory)&&lease.machineId().equals(context.game().machineId()),"actual original relic store/machine differs");
            OriginalRuntimeHandoffObservation.decode(OriginalRuntimeHandoffObservation.Scope.RELIC,lease.originalObservation(),directory,lease.machineId(),lease.originalEvidence());
            var parentIdentity=SharedSourceFiles.nativeDirectory(parent);var parentNames=names(parent);
            boolean present=Files.exists(directory,LinkOption.NOFOLLOW_LINKS);
            var directoryIdentity=present?SharedSourceFiles.nativeDirectory(directory):null;List<String> roster=present?names(directory):List.of();
            var archive=context.archive().withSession(same);LegacyScope current=scope(before);
            var manifest=StrictJson.object().put("schema","xar.java.relic-original-once-census/v1").put("machine_id",current.machineId())
                    .put("actor",current.actor()).put("scope_kind",current.kind().name()).put("run_id",current.runId()).put("original_store",directory.toString())
                    .put("directory_present",present).put("capture_head_sha256",same.head().digest()).put("capture_head_sequence",same.head().state().sequence());
            manifest.set("parent_identity",directoryIdentity(parentIdentity));if(present)manifest.set("directory_identity",directoryIdentity(directoryIdentity));else manifest.putNull("directory_identity");
            var parentRoster=manifest.putArray("complete_parent_names");parentNames.forEach(parentRoster::add);
            var complete=manifest.putArray("complete_names");roster.forEach(complete::add);
            manifest.set("original_runtime_observation",archive.preserveMaterial(new RawJson(lease.originalObservation())).toJson());
            var sourceRefs=manifest.putArray("original_runtime_sources");lease.originalEvidence().forEach(ref->sourceRefs.add(ref.toJson()));
            var rows=manifest.putArray("files");var files=new ArrayList<LegacyFile>();var witnesses=new ArrayList<SharedSourceFiles.Witness>();long total=0;
            for(String name:roster){Path path=directory.resolve(name);var witness=SharedSourceFiles.observe(path);
                require(witness.source().bytes()>0&&witness.source().bytes()<=1048576,"original relic file exceeds its finite bound");
                total=Math.addExact(total,witness.source().bytes());require(total<=16777216,"whole original relic census exceeds its finite bound");
                byte[] bytes;try(var input=Files.newInputStream(path,LinkOption.NOFOLLOW_LINKS)){bytes=input.readNBytes(1048577);}
                require(bytes.length==witness.source().bytes()&&ActionCodec.sha256(bytes).equals(witness.source().sha256()),"original relic file changed during capture");
                SharedSourceFiles.assertUnchanged(witness);witnesses.add(witness);var raw=new RawJson(bytes);files.add(new LegacyFile(name,raw));
                var row=rows.addObject().put("name",name).put("native_identity",witness.nativeFile().identityKey());
                row.set("original",new ExactRef(witness.source().path(),witness.source().bytes(),witness.source().sha256()).toJson());row.set("preserved",archive.preserveMaterial(raw).toJson());
            }
            require(SharedSourceFiles.nativeDirectory(parent).equals(parentIdentity)&&names(parent).equals(parentNames)
                    &&Files.exists(directory,LinkOption.NOFOLLOW_LINKS)==present,"original relic parent identity/absence changed");
            if(present)require(SharedSourceFiles.nativeDirectory(directory).equals(directoryIdentity)&&names(directory).equals(roster),"original relic complete roster changed");
            for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);lease.requireCurrent();
            List<String> blockers=legacyBlockers(files,current);var blocked=manifest.putArray("blocking_original_claims");blockers.forEach(blocked::add);
            ExactRef result=archive.preserveMaterial(new RawJson(StrictJson.canonical(manifest)));
            require(blockers.isEmpty(),"original relic UNKNOWN remains; no replay; census="+result.path());return result;
        }
        private void verifyCensus(ActionCommand command,Complete before,ExactRef reference,ActionPorts.OutcomeArchive archive)throws IOException {
            ObjectNode n=StrictJson.object(StrictJson.parse(material(archive,reference).bytes(),StrictJson.EXPLICIT_MAX_BYTES),Set.of("schema","machine_id","actor","scope_kind","run_id","original_store",
                    "directory_present","capture_head_sha256","capture_head_sequence","parent_identity","directory_identity","complete_parent_names","complete_names",
                    "original_runtime_observation","original_runtime_sources","files","blocking_original_claims"));
            Path originalStore=originalStore(before);
            require(text(n,"schema").equals("xar.java.relic-original-once-census/v1")&&text(n,"machine_id").equals(command.before().machineId())
                    &&Path.of(text(n,"original_store")).equals(originalStore),"original relic census version/machine/store differs");
            LegacyScope expected=scope(before),current=new LegacyScope(text(n,"machine_id"),full(n,"actor"),ScopeKind.valueOf(text(n,"scope_kind")),text(n,"run_id"));
            require(current.equals(expected),"original relic census scope differs from the actual original frame");
            digest(text(n,"capture_head_sha256"));integer(n,"capture_head_sequence",BigInteger.ZERO,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER));
            Session same=context.borrowedSession();context.writer().requireSession(same);
            var captured=same.requireHistoricalState(integer(n,"capture_head_sequence",BigInteger.ZERO,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)).longValueExact(),text(n,"capture_head_sha256"));
            require(ContinuityActionJournal.receipts(captured,archive).stream().allMatch(ActionReceipt::settled)
                    &&ContinuityActionJournal.lookup(captured,command.actionId(),archive).isEmpty(),"original census did not precede a new unclaimed command in the actual writer history");
            validateDirectory(n.get("parent_identity"));boolean present=bool(n,"directory_present");
            if(present)validateDirectory(n.get("directory_identity"));else require(n.get("directory_identity").isNull(),"absent old store has no directory identity");
            List<String> parentNames=roster(n.get("complete_parent_names")),names=roster(n.get("complete_names"));
            require(parentNames.contains(originalStore.getFileName().toString())==present&&(!present?names.isEmpty():true),"complete parent roster contradicts original store presence");
            var evidence=new ArrayList<ExactRef>();require(n.get("original_runtime_sources").isArray()&&n.get("original_runtime_sources").size()<=256,"complete retired-runtime source list required");
            for(JsonNode source:n.get("original_runtime_sources"))evidence.add(ExactRef.fromJson(source));
            byte[] retired=material(archive,ExactRef.fromJson(n.get("original_runtime_observation"))).bytes();
            OriginalRuntimeHandoffObservation.decode(OriginalRuntimeHandoffObservation.Scope.RELIC,retired,originalStore,current.machineId(),evidence);
            require(n.get("files").isArray()&&n.get("files").size()==names.size(),"original relic census is partial");
            var files=new ArrayList<LegacyFile>();var actualNames=new ArrayList<String>();long total=0;
            for(JsonNode row:n.get("files")){
                ObjectNode file=StrictJson.object(row,Set.of("name","native_identity","original","preserved"));String name=text(file,"name");
                ExactRef original=ExactRef.fromJson(file.get("original")),preserved=ExactRef.fromJson(file.get("preserved"));
                require(Path.of(original.path()).equals(originalStore.resolve(name))&&original.bytes()>0&&original.bytes()<=1048576
                        &&original.bytes()==preserved.bytes()&&original.sha256().equals(preserved.sha256()),"old file source differs from its archived material");
                String[] ids=text(file,"native_identity").split(":",-1);require(ids.length==3,"original native FileID absent");
                new SharedSourceFiles.DirectoryIdentity(ids[0],ids[1],ids[2]);
                total=Math.addExact(total,original.bytes());require(total<=16777216,"whole original relic census byte bound exceeded");
                actualNames.add(name);files.add(new LegacyFile(name,material(archive,preserved)));
            }
            require(actualNames.equals(names)&&roster(n.get("blocking_original_claims")).isEmpty()&&legacyBlockers(files,current).isEmpty(),"old relic UNKNOWN or partial source census cannot release a new command");
        }
        private static RawJson material(ActionPorts.OutcomeArchive archive,ExactRef ref){
            RawJson raw=archive.loadMaterial(ref);require(ref.bytes()==raw.bytes().length&&ref.sha256().equals(ActionCodec.sha256(raw.bytes())),"exact original archived material changed");return raw;
        }
        private static List<String> names(Path directory)throws IOException {
            var names=new ArrayList<String>();try(var stream=Files.newDirectoryStream(directory)){for(Path path:stream){require(names.size()<512,"complete original directory roster exceeds finite bound");names.add(path.getFileName().toString());}}
            names.sort(String::compareTo);return List.copyOf(names);
        }
        private static List<String> roster(JsonNode node){
            require(node!=null&&node.isArray()&&node.size()<=512,"complete finite original name array required");var result=new ArrayList<String>();
            for(JsonNode item:node){String name=StrictJson.text(item);require(!name.isEmpty()&&!name.contains("/")&&!name.contains("\\")&&!name.equals(".")&&!name.equals(".."),"original roster name invalid");result.add(name);}
            require(new java.util.TreeSet<>(result).size()==result.size()&&result.equals(result.stream().sorted().toList()),"original roster is duplicated or unordered");return List.copyOf(result);
        }
        private static ObjectNode directoryIdentity(SharedSourceFiles.DirectoryIdentity value){return StrictJson.object().put("volume_serial_decimal",value.volumeSerialDecimal()).put("file_id_decimal",value.fileIdDecimal()).put("creation_filetime_decimal",value.creationFiletimeDecimal());}
        private static void validateDirectory(JsonNode node){var n=StrictJson.object(node,Set.of("volume_serial_decimal","file_id_decimal","creation_filetime_decimal"));new SharedSourceFiles.DirectoryIdentity(text(n,"volume_serial_decimal"),text(n,"file_id_decimal"),text(n,"creation_filetime_decimal"));}
    }
}
