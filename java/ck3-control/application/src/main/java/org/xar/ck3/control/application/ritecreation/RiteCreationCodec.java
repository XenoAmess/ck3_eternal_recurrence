package org.xar.ck3.control.application.ritecreation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;

/** One runtime-checked original public/request/result boundary; immutable native bytes are never rewritten. */
public final class RiteCreationCodec {
    private static final Set<String> ENVELOPE=Set.of("step","accepted","private_build","advertised","status","snapshot_revision","date_raw","read_only","domain_key","backend_id","game_version","executable_sha256","rite_creation_action");
    private static final Set<String> LEAF=Set.of("schema","operation","available","status","unavailable_reason","frame","draft","modal","full_can","quote","preview_identity_available","preview_identity","complete_command_payload_observed","original_writer_inputs_observed","native_command_text_bytes","native_command_text_sha256","native_dispatch_attempted","dispatch_invoked","verification_pending","original_writer_may_have_been_queued","business_outcome_observed","already_in_requested_state","selection_or_name_postcondition_observed","draft_open_postcondition_observed","native_once_claimed","action_id");
    private RiteCreationCodec() { }
    public static Query query(RawJson original){ObjectNode n=object(original);shape(n,Set.of("expected_revision","expected_source_rite_id"),Set.of());return new Query(publicU64(get(n,"expected_revision")),source(get(n,"expected_source_rite_id")));}
    public static Execute execute(RawJson original){
        ObjectNode n=object(original);RiteCreation op=parseRiteCreation(text(get(n,"operation")));need(op!=RiteCreation.PREVIEW,"public execute does not accept preview");
        Set<String> selectors=switch(op){case SELECT_CORE_TENET->Set.of("core_slot_index","tenet_key");case SELECT_DOCTRINE->Set.of("group_key","doctrine_key");case SET_NAME_FIELD->Set.of("name_field","text");case PREPARE_CONFIRMATION,CONFIRM_ONCE->Set.of("expected_preview_identity","expected_outcome_kind");default->Set.of();};
        var required=new HashSet<>(Set.of("operation","expected_revision","expected_source_rite_id"));required.addAll(selectors);
        // MCP's omitted optional selectors and explicit null are equivalent before the original private request_fields boundary.
        Set<String> optional=new HashSet<>(Set.of("core_slot_index","tenet_key","group_key","doctrine_key","name_field","text","expected_preview_identity","expected_outcome_kind"));optional.removeAll(selectors);
        shape(n,required,optional);for(String field:optional)if(n.has(field))need(n.get(field).isNull(),"irrelevant Rite selector must be absent or null: "+field);
        Write write=switch(op){case OPEN_CREATE_DRAFT->new OpenCreate();case OPEN_EDIT_CURRENT_RITE_DRAFT->new OpenEdit();case SELECT_CORE_TENET->new CoreTenet(integer(get(n,"core_slot_index"),0,63).intValueExact(),definition(get(n,"tenet_key")));case SELECT_DOCTRINE->new Doctrine(definition(get(n,"group_key")),definition(get(n,"doctrine_key")));case SET_NAME_FIELD->new Name(NameField.parse(text(get(n,"name_field"))),text(get(n,"text")));case PREPARE_CONFIRMATION->new Prepare(identity(get(n,"expected_preview_identity")),Outcome.parse(text(get(n,"expected_outcome_kind"))));case CONFIRM_ONCE->new Confirm(identity(get(n,"expected_preview_identity")),Outcome.parse(text(get(n,"expected_outcome_kind"))));default->throw new IllegalArgumentException("not a finite Rite write");};
        return new Execute(publicU64(get(n,"expected_revision")),source(get(n,"expected_source_rite_id")),write);
    }
    public static Collect collect(RawJson original){ObjectNode n=object(original);shape(n,Set.of("action_request_id"),Set.of("timeout_seconds"));JsonNode seconds=n.get("timeout_seconds");need(seconds==null||seconds.isNumber(),"Rite timeout must be a finite JSON number, never bool/null/text");return new Collect(new ActionId(text(get(n,"action_request_id"))),timeout(seconds==null?BigDecimal.ZERO:seconds.decimalValue()));}
    public static Frame frame(Complete actual,Scope independentlyVerifiedScope){
        ObjectNode n=node(actual.semantic()),d=object(get(n,"diagnostics")),hello=object(get(d,"hello")),player=object(get(n,"played_character"));
        yes(get(n,"paused"));yes(get(n,"map_ready"));yes(get(player,"alive"));yes(get(hello,"ck3_build_match"));
        equal(get(hello,"expected_ck3_version"),VERSION);need(text(get(hello,"expected_ck3_sha256")).equalsIgnoreCase(SHA),"Rite requires exact original .4 executable");equal(get(hello,"game_adapter_id"),"ck3-1.20.0.4-msvc-x64");
        equal(get(n,"snapshot_id"),actual.identity().frame().snapshotId());equal(get(n,"revision"),actual.identity().frame().revision());equal(get(n,"native_revision"),actual.identity().frame().identity().nativeRevision());equal(get(n,"date_raw"),actual.identity().frame().identity().dateRaw());
        BigInteger connection=uint64(get(d,"connection_generation")),nativeRevision=uint64(get(n,"native_revision"));need(connection.equals(actual.connectionGeneration()),"actual Driver connection differs");
        long pid=integer(get(hello,"pid"),1,0xffff_ffffL).longValueExact();int actor=integer(get(player,"character_id"),1,Integer.MAX_VALUE).intValueExact();need(pid==actual.identity().game().pid()&&BigInteger.valueOf(actor).equals(actual.identity().frame().identity().player()),"actual Rite owner/player differs");
        if(independentlyVerifiedScope instanceof EpisodeScope scope)equal(get(n,"episode_run_id"),scope.episode());
        else {equal(get(n,"episode_projection"),"native_campaign");need(get(n,"episode_run_id").isNull(),"managed campaign must not manufacture an episode");}
        return new Frame(actual.identity().frame().snapshotId(),uint64(get(n,"revision")),nativeRevision,connection,pid,actor,integer(get(n,"date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact(),independentlyVerifiedScope);
    }
    public static Obj nativeFields(NativeFields fields,Frame frame){
        ObjectNode n=empty().put("operation",fields.operation().wire()).put("expected_source_rite_id",fields.source().value());
        fields.write().ifPresent(write->selectors(n,write));
        fields.originalProtocolRequestId().ifPresent(v->n.put("action_id",v));
        n.put("expected_connection_generation",frame.connectionGeneration()).put("expected_date_raw",frame.dateRaw()).put("expected_player_character_id",frame.actor());return obj(n);
    }
    public static RawJson execution(Execute request){ObjectNode n=empty().put("operation",request.action().operation().wire()).put("expected_revision",request.expectedRevision().toString()).put("expected_source_rite_id",request.source().value());selectors(n,request.action());return raw(n);}
    private static void selectors(ObjectNode n,Write write){switch(write){case OpenCreate ignored->{ }case OpenEdit ignored->{ }case CoreTenet v->n.put("core_slot_index",v.slot()).put("tenet_key",v.tenet().value());case Doctrine v->n.put("group_key",v.group().value()).put("doctrine_key",v.doctrine().value());case Name v->n.put("name_field",v.field().wire()).put("text",v.text());case Prepare v->n.put("expected_preview_identity",v.preview().value()).put("expected_outcome_kind",v.outcome().wire());case Confirm v->n.put("expected_preview_identity",v.preview().value()).put("expected_outcome_kind",v.outcome().wire());}}
    /** Same original Native result proof used for query, synchronous action ACK and retained late result. */
    public static Result result(RawJson original,ExpectedNativeBinding binding,NativeFields fields){
        ObjectNode n=object(original);shape(n,ENVELOPE,Set.of());equal(get(n,"step"),STEP);yes(get(n,"accepted"));yes(get(n,"private_build"));no(get(n,"advertised"));equal(get(n,"domain_key"),CAPABILITY);equal(get(n,"backend_id"),BACKEND);equal(get(n,"game_version"),VERSION);need(text(get(n,"executable_sha256")).equalsIgnoreCase(SHA),"foreign Rite native result build");
        need(bool(get(n,"read_only"))==(fields.operation()==RiteCreation.PREVIEW),"Rite read/write branch changed");equal(get(n,"snapshot_revision"),binding.nativeRevision());equal(get(n,"date_raw"),binding.nativeDate());
        ObjectNode leaf=object(get(n,"rite_creation_action"));var required=new HashSet<>(LEAF);required.removeAll(Set.of("status","already_in_requested_state","selection_or_name_postcondition_observed","draft_open_postcondition_observed","native_once_claimed"));shape(leaf,required,Set.of("status","already_in_requested_state","selection_or_name_postcondition_observed","draft_open_postcondition_observed","native_once_claimed"));
        equal(get(leaf,"schema"),SCHEMA);equal(get(leaf,"operation"),fields.operation().wire());if(leaf.has("status"))equal(leaf.get("status"),text(get(n,"status")));
        for(String key:List.of("already_in_requested_state","selection_or_name_postcondition_observed","draft_open_postcondition_observed","native_once_claimed"))if(leaf.has(key))bool(leaf.get(key));no(get(leaf,"business_outcome_observed"));
        ObjectNode f=object(get(leaf,"frame"));shape(f,Set.of("connection_generation","native_revision","capture_epoch","date_raw","played_character_id"),Set.of());
        equal(get(f,"connection_generation"),binding.connectionGeneration());equal(get(f,"native_revision"),binding.nativeRevision());equal(get(f,"date_raw"),binding.nativeDate());equal(get(f,"played_character_id"),binding.nativeActor());
        NativeFrame frame=new NativeFrame(uint64(get(f,"connection_generation")),uint64(get(f,"native_revision")),uint64(get(f,"capture_epoch")),binding.nativeDate().intValueExact(),binding.nativeActor().intValueExact());
        Draft draft=draft(get(leaf,"draft"));if(draft.observed())need(draft.source().equals(Optional.of(fields.source())),"actual source Rite differs from original request");
        ObjectNode m=object(get(leaf,"modal"));shape(m,Set.of("observed","stage","kind","active","same_draft_window_bound","native_can_accept"),Set.of());Modal modal=new Modal(bool(get(m,"observed")),ModalStage.parse(text(get(m,"stage"))),nullable(m,"kind",v->ModalKind.parse(text(v))),nullable(m,"active",RiteCreationCodec::bool),nullable(m,"same_draft_window_bound",RiteCreationCodec::bool),nullable(m,"native_can_accept",RiteCreationCodec::bool));
        ObjectNode c=object(get(leaf,"full_can"));shape(c,Set.of("observed","can_create","can_edit","create_reason","edit_reason"),Set.of());FullCan can=new FullCan(bool(get(c,"observed")),nullable(c,"can_create",RiteCreationCodec::bool),nullable(c,"can_edit",RiteCreationCodec::bool),nullable(c,"create_reason",RiteCreationCodec::text),nullable(c,"edit_reason",RiteCreationCodec::text));
        ObjectNode q=object(get(leaf,"quote"));shape(q,Set.of("observed","piety_cost_raw","piety_missing_signed_raw","has_enough_piety","raw_scale"),Set.of());equal(get(q,"raw_scale"),BigInteger.valueOf(100000));Quote quote=new Quote(bool(get(q,"observed")),nullable(q,"piety_cost_raw",RiteCreationCodec::signed64),nullable(q,"piety_missing_signed_raw",RiteCreationCodec::signed64),nullable(q,"has_enough_piety",RiteCreationCodec::bool));
        Optional<Identity> preview=nullable(leaf,"preview_identity",RiteCreationCodec::identity);need(bool(get(leaf,"preview_identity_available"))==preview.isPresent(),"native preview identity presence differs");
        Optional<String> action=nullable(leaf,"action_id",RiteCreationCodec::text);need(action.equals(fields.originalProtocolRequestId()),"original native action request identity changed");
        return new Result(fields.operation(),bool(get(leaf,"available")),text(get(n,"status")),nullable(leaf,"unavailable_reason",RiteCreationCodec::text),frame,draft,modal,can,quote,preview,bool(get(leaf,"complete_command_payload_observed")),bool(get(leaf,"original_writer_inputs_observed")),nullable(leaf,"native_command_text_bytes",RiteCreationCodec::uint64),nullable(leaf,"native_command_text_sha256",RiteCreationCodec::identity),bool(get(leaf,"native_dispatch_attempted")),bool(get(leaf,"dispatch_invoked")),bool(get(leaf,"verification_pending")),bool(get(leaf,"original_writer_may_have_been_queued")),action,original);
    }
    private static Draft draft(JsonNode raw){
        ObjectNode d=object(raw);shape(d,Set.of("observed","source_rite_id","source_faith_id","actor_faith_id","actual_outcome_kind","names","selected_core_tenets","selected_doctrines"),Set.of("names_observed","selected_core_tenets_observed","selected_doctrines_observed","editing_owned_current_rite","native_create_faith_or_reform"));
        for(String flag:List.of("names_observed","selected_core_tenets_observed","selected_doctrines_observed"))if(d.has(flag))bool(d.get(flag));for(String flag:List.of("editing_owned_current_rite","native_create_faith_or_reform"))if(d.has(flag)&&!d.get(flag).isNull())bool(d.get(flag));
        ObjectNode names=get(d,"names").isNull()?empty().putNull("name").putNull("adjective").putNull("adherent").putNull("adherent_plural").putNull("description"):object(get(d,"names"));shape(names,Set.of("name","adjective","adherent","adherent_plural","description"),Set.of());
        Names typedNames=new Names(nullable(names,"name",RiteCreationCodec::text),nullable(names,"adjective",RiteCreationCodec::text),nullable(names,"adherent",RiteCreationCodec::text),nullable(names,"adherent_plural",RiteCreationCodec::text),nullable(names,"description",RiteCreationCodec::text));
        Optional<List<Tenet>> tenets=nullable(d,"selected_core_tenets",v->array(v,item->{ObjectNode t=object(item);shape(t,Set.of("slot_index","tenet_key"),Set.of());return new Tenet(integer(get(t,"slot_index"),0,63).intValueExact(),definition(get(t,"tenet_key")));}));
        Optional<List<SelectedDoctrine>> doctrines=nullable(d,"selected_doctrines",v->array(v,item->{ObjectNode t=object(item);shape(t,Set.of("group_key","doctrine_key"),Set.of());return new SelectedDoctrine(definition(get(t,"group_key")),definition(get(t,"doctrine_key")));}));
        if(d.has("selected_core_tenets_observed"))need(bool(d.get("selected_core_tenets_observed"))==tenets.isPresent(),"original tenet presence/observation differs");if(d.has("selected_doctrines_observed"))need(bool(d.get("selected_doctrines_observed"))==doctrines.isPresent(),"original doctrine presence/observation differs");
        if(d.has("names_observed")&&bool(d.get("names_observed")))need(typedNames.complete(),"observed names contain missing native fields");
        return new Draft(bool(get(d,"observed")),nullable(d,"source_rite_id",RiteCreationCodec::source),nullable(d,"source_faith_id",RiteCreationCodec::source),nullable(d,"actor_faith_id",RiteCreationCodec::source),nullable(d,"actual_outcome_kind",v->Outcome.parse(text(v))),typedNames,tenets,doctrines);
    }
    public static RawJson publicResult(Result actual,Frame source,ActionId action,ExactRef retainedNativeReceipt,boolean knownNoDispatchReleased,boolean collecting){
        ObjectNode n=object(actual.original()).deepCopy();n.put("business_outcome_verified",false).put("action_ready",false).put("automatic_retry",false).put("source_and_runtime_qualification_distinct",true)
                .put("known_no_dispatch_intent_released",knownNoDispatchReleased).put("native_result_receipt",retainedNativeReceipt.path()).put("action_request_id",action.value());
        if(collecting)n.put("status_scope","original_request_result_only_not_current_legality");else{n.put("queried_revision",source.publicRevision().toString()).put("uses_mouse",false).put("uses_keyboard",false).put("uses_ocr",false);if(source.scope() instanceof EpisodeScope scope)n.put("episode_run_id",scope.episode());else n.putNull("episode_run_id");}
        public64(n);return raw(n);
    }
    /** A legacy imported result has its actual Native binding, not a fabricated public snapshot or canonical action receipt. */
    public static RawJson retainedResult(Result actual,ActionId action,ExactRef retainedNativeReceipt,boolean released){ObjectNode n=object(actual.original()).deepCopy();n.put("business_outcome_verified",false).put("action_ready",false).put("automatic_retry",false).put("source_and_runtime_qualification_distinct",true).put("known_no_dispatch_intent_released",released).put("native_result_receipt",retainedNativeReceipt.path()).put("action_request_id",action.value()).put("status_scope","original_request_result_only_not_current_legality");public64(n);return raw(n);}
    public static RawJson pending(ActionId action,boolean knownNoDispatch){return raw(empty().put("status",knownNoDispatch?"known_no_dispatch":"pending_unknown").put("action_request_id",action.value()).put("known_no_dispatch_intent_released",knownNoDispatch).put("automatic_retry",false).put("business_outcome_verified",false).put("action_ready",false));}
    private static void public64(ObjectNode n){
        for(String key:List.of("snapshot_revision"))if(n.has(key)&&!n.get(key).isNull())n.put(key,uint64(n.get(key)).toString());
        ObjectNode leaf=object(get(n,"rite_creation_action")),frame=object(get(leaf,"frame"));for(String key:List.of("connection_generation","native_revision","capture_epoch"))frame.put(key,uint64(get(frame,key)).toString());
        if(!get(leaf,"native_command_text_bytes").isNull())leaf.put("native_command_text_bytes",uint64(get(leaf,"native_command_text_bytes")).toString());
        ObjectNode quote=object(get(leaf,"quote"));for(String key:List.of("piety_cost_raw","piety_missing_signed_raw"))if(!get(quote,key).isNull())quote.put(key,Long.toString(signed64(get(quote,key))));
    }
    public static ObjectNode object(RawJson original){return node(DriverJson.object(original.bytes(),DriverJson.MAX_NATIVE_BYTES));}
    public static ObjectNode node(Obj value){return object(OpportunityJson.toNode(value));}
    public static Obj obj(ObjectNode value){return DriverJson.object(raw(value).bytes(),DriverJson.MAX_NATIVE_BYTES);}
    public static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value,StrictJson.EXPLICIT_MAX_BYTES));}
    public static ObjectNode empty(){return (ObjectNode)OpportunityJson.toNode(new Obj(java.util.Map.of()));}
    public static ObjectNode object(JsonNode value){need(value instanceof ObjectNode,"exact original Rite object required");return (ObjectNode)value;}
    public static JsonNode get(ObjectNode object,String key){need(object.has(key),"missing original Rite field: "+key);return object.get(key);}
    public static void shape(ObjectNode n,Set<String> required,Set<String> optional){Set<String> names=new HashSet<>();n.fieldNames().forEachRemaining(names::add);need(names.containsAll(required)&&names.stream().allMatch(k->required.contains(k)||optional.contains(k)),"wrong/missing/unknown Rite fields: "+names);}
    public static String text(JsonNode value){need(value!=null&&value.isTextual(),"exact Rite string required");return value.textValue();}
    public static boolean bool(JsonNode value){need(value!=null&&value.isBoolean(),"exact Rite boolean required");return value.booleanValue();}
    public static void yes(JsonNode value){need(bool(value),"original Rite proof must be true");}public static void no(JsonNode value){need(!bool(value),"original Rite business/readiness proof must remain false");}
    public static void equal(JsonNode value,String expected){need(text(value).equals(expected),"Rite text identity differs");}public static void equal(JsonNode value,BigInteger expected){need(integer(value,BigInteger.valueOf(Long.MIN_VALUE),U64).equals(expected),"Rite actual numeric identity/frame differs");}
    public static BigInteger integer(JsonNode n,long low,long high){return integer(n,BigInteger.valueOf(low),BigInteger.valueOf(high));}
    public static BigInteger integer(JsonNode n,BigInteger low,BigInteger high){need(n!=null&&n.isIntegralNumber(),"exact integer token required; bool/float/string invalid");BigInteger v=n.bigIntegerValue();need(v.compareTo(low)>=0&&v.compareTo(high)<=0,"Rite integer outside declared native bounds");return v;}
    public static BigInteger uint64(JsonNode value){return integer(value,BigInteger.ONE,U64);}
    public static BigInteger publicU64(JsonNode value){if(value!=null&&value.isTextual()){String s=value.textValue();need(s.matches("[1-9][0-9]*"),"canonical positive public uint64 required");BigInteger exact=new BigInteger(s);revision(exact);return exact;}return integer(value,1,9_007_199_254_740_991L);}
    public static long signed64(JsonNode value){return integer(value,Long.MIN_VALUE,Long.MAX_VALUE).longValueExact();}
    public static SourceRite source(JsonNode value){return new SourceRite(integer(value,0,0xffff_fffeL).longValueExact());}public static Definition definition(JsonNode value){return new Definition(text(value));}public static Identity identity(JsonNode value){return new Identity(text(value));}
    public static <T> Optional<T> nullable(ObjectNode n,String key,Function<JsonNode,T> parse){JsonNode value=get(n,key);return value.isNull()?Optional.empty():Optional.of(parse.apply(value));}
    private static <T> List<T> array(JsonNode value,Function<JsonNode,T> parse){need(value.isArray()&&value.size()<=64,"bounded actual selected Rite rows required");List<T> out=new ArrayList<>();value.forEach(v->out.add(parse.apply(v)));return List.copyOf(out);}
}
