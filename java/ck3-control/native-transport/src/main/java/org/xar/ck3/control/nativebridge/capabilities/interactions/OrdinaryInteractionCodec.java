package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Same owned native context and final education intent as the production ordinary-interaction producer. */
public final class OrdinaryInteractionCodec {
    public static final String QUERY_STEP="query-character-interaction-ordinary-v1", INITIATE_STEP="initiate-character-interaction-ordinary-v1";
    public static final String QUERY_CAPABILITY="game.query.character-interaction-ordinary.v1", INITIATE_CAPABILITY="game.command.initiate-character-interaction-ordinary-v1";
    private static final List<String> COSTS=List.of("gold","prestige","piety","renown","influence","herd","treasury","treasury_or_gold","merit","barter_goods");
    private static final Set<String> COMMON=Set.of("schema","status","source","read_only","exact_build","executable_sha256","snapshot_revision","date_raw","game_pid","connection_generation",
        "player_character_id","recipient_id","interaction_key","source_code_pins_verified","actor_binding_verified","recipient_binding_verified","owner_thread_verified","tls_verified","frame_verified","owner_thread_id","owner_pump_epoch","business_postcondition_verified");
    private static final Set<String> TERMS=Set.of("actor_alive","recipient_alive","definition_stable_hash","declared_option_count","selected_option_count","special_payload_present","shown","can_send","costs_raw","auto_accept","recipient_score_raw","intermediary_score_raw","outer_answer_status");
    private OrdinaryInteractionCodec() { }
    public static RawJson request(Context c,OrdinaryRequest r,boolean initiating) {
        need(c.controls().paused() && c.controls().mapReady() && c.controls().alive(),"ordinary interaction needs actual living paused map");
        if(initiating) need(!c.controls().activeEvent() && c.controls().pending()==null,"ordinary initiation requires no event or incoming interaction");
        ObjectNode n=InteractionJson.common(c).put("interaction_key",r.interaction().value()).put("recipient_id",r.recipient().value());
        if(r.education().isPresent()) {
            EducationIntent e=r.education().orElseThrow();
            if(initiating) need(e.child().isPresent() && e.guardian().isPresent() && e.options().isPresent(),"education initiation requires exact pair and option intent");
            e.child().ifPresent(id->n.put("child_full_id",id.value())); e.guardian().ifPresent(id->n.put("guardian_full_id",id.value()));
            e.options().ifPresent(keys->{ var a=n.putArray("requested_option_keys"); for(InteractionKey key:keys) a.add(key.value()); });
        } else need(!initiating || !r.interaction().value().equals("educate_child_interaction"),"education initiation requires actual materialized request intent");
        return encode(n);
    }
    public static OrdinaryContext query(RawJson raw,Context c,OrdinaryRequest r) {
        JsonNode n=parse(raw); envelope(n,c,QUERY_STEP,true); JsonNode payload=field(n,"character_interaction_ordinary_context"); OrdinaryContext context=context(payload,c,r,positive64(n,"query_sequence"),true);
        eq(n,"status",context.availability().available()?"available":"unavailable"); return context;
    }
    public static OrdinaryContext context(JsonNode n,Context c,OrdinaryRequest r,BigInteger sequence) {
        return context(n,c,r,sequence,false);
    }
    private static OrdinaryContext context(JsonNode n,Context c,OrdinaryRequest r,BigInteger sequence,boolean query) {
        boolean outgoingRequired=query && c.build()==Build.CROZIER4 && r.interaction().value().equals("educate_child_interaction");
        need(n.has(FamilyOutgoingCodec.GROUP)==outgoingRequired,"actual4 education query requires family outgoing storage; initiation preflight forbids it");
        Set<String> keys=new HashSet<>(COMMON); keys.addAll(TERMS); keys.addAll(Set.of("effective_roles","cost_scale","cost_order","native_context_available","ordinary_context_supported","active_event_present","incoming_interaction_present","ready_to_initiate","unavailable_reason","unsupported_reason"));
        for(String optional:List.of("education_option_rows","education_request_materialization","request_guardian_skill_inputs_v1")) if(n.has(optional)) keys.add(optional);
        if(outgoingRequired) keys.add(FamilyOutgoingCodec.GROUP);
        closed(n,keys); String status=text(n,"status"); need(status.equals("available") || status.equals("unavailable"),"ordinary context status differs");
        OrdinaryProofs proofs=common(n,c,r,"ck3-character-interaction-ordinary-context-v1","native_current_ordinary_interaction_context_"+c.build().version(),true);
        boolean available=status.equals("available"), contextAvailable=bool(n,"native_context_available"),supported=bool(n,"ordinary_context_supported"),active=bool(n,"active_event_present"),incoming=bool(n,"incoming_interaction_present"),ready=bool(n,"ready_to_initiate");
        need(active==c.controls().activeEvent() && incoming==(c.controls().pending()!=null),"ordinary modal binding differs");
        eq(n,"cost_scale",BigInteger.valueOf(100000));
        List<String> costOrder=list(n,"cost_order",10,v->{ need(v.isTextual(),"native resource key required"); return v.textValue(); }); need(costOrder.equals(COSTS),"ordered resource vector changed");
        JsonNode roles=field(n,"effective_roles"); closed(roles,"actor_id","recipient_id","secondary_actor_id","secondary_recipient_id","intermediary_id","sixth_role_id");
        Roles role=new Roles(nullableId(roles,"actor_id"),nullableId(roles,"recipient_id"),nullableId(roles,"secondary_actor_id"),nullableId(roles,"secondary_recipient_id"),nullableId(roles,"intermediary_id"),nullableId(roles,"sixth_role_id"));
        Optional<EducationOptions> rows=Optional.empty(); Optional<EducationMaterialization> material=Optional.empty();
        if(n.has("education_option_rows")) rows=Optional.of(educationOptions(field(n,"education_option_rows"),c,r,available));
        if(n.has("education_request_materialization")) material=Optional.of(materialization(field(n,"education_request_materialization"),c,r,available,role,rows));
        if(n.has("request_guardian_skill_inputs_v1")) validateGuardianSkills(field(n,"request_guardian_skill_inputs_v1"),c,r,available,role);
        if(outgoingRequired) GuardianOutgoingCodec.group(field(n,FamilyOutgoingCodec.GROUP),c,r,n,sequence);
        Frame frame=new Frame(c.revision(),c.date(),c.actor(),c.build(),sequence);
        if(!available) {
            for(String key:TERMS) nil(n,key);
            nil(roles,"actor_id","recipient_id","secondary_actor_id","secondary_recipient_id","intermediary_id","sixth_role_id");
            need(!contextAvailable && !supported && !ready,"unavailable ordinary context invented readiness");
            return new OrdinaryContext(frame,r,new Availability(false,reason(n,"unavailable_reason")),proofs,role,null,false,false,active,incoming,false,reason(n,"unsupported_reason"),rows,material);
        }
        nil(n,"unavailable_reason"); need(proofs.complete() && contextAvailable,"ordinary available context lacks actual proofs");
        long hash=number(n,"definition_stable_hash",BigInteger.ZERO,U32).longValueExact(),declared=number(n,"declared_option_count",BigInteger.ZERO,U32).longValueExact(),selected=number(n,"selected_option_count",BigInteger.ZERO,U32).longValueExact();
        need(selected<=declared && role.actor()!=null && role.recipient()!=null,"ordinary effective roles/options incomplete");
        List<BigInteger> costs=list(n,"costs_raw",10,v->{ need(v.isIntegralNumber(),"raw native resource must remain exact integer"); return range(v.bigIntegerValue(),I64_MIN,I64_MAX); }); need(costs.size()==10,"complete native ten-resource vector required");
        OrdinaryTerms terms=new OrdinaryTerms(bool(n,"actor_alive"),bool(n,"recipient_alive"),hash,declared,selected,bool(n,"special_payload_present"),bool(n,"shown"),bool(n,"can_send"),costs,bool(n,"auto_accept"),number(n,"recipient_score_raw",I64_MIN,I64_MAX),number(n,"intermediary_score_raw",I64_MIN,I64_MAX),integer(n,"outer_answer_status",0,2));
        boolean requested=material.isPresent() && (material.orElseThrow().child()!=null || material.orElseThrow().guardian()!=null || material.orElseThrow().optionKeys()!=null);
        boolean honored=!requested || material.orElseThrow().availability().available();
        boolean education=c.build()==Build.CROZIER4 && r.interaction().value().equals("educate_child_interaction") && rows.isPresent() && rows.orElseThrow().availability().available() && material.isPresent() && material.orElseThrow().availability().available();
        boolean actualSupported=!terms.specialPayload() && honored && ((declared==0 && selected==0) || education);
        need(supported==actualSupported,"ordinary support summary differs from actual owned context");
        String unsupported=supported?nullableText(n,"unsupported_reason"):reason(n,"unsupported_reason"); need(!supported || unsupported==null,"supported context carries unsupported reason");
        boolean actualReady=supported && terms.actorAlive() && terms.recipientAlive() && terms.shown() && terms.canSend() && !active && !incoming; need(ready==actualReady,"ordinary ready summary differs from native final terms");
        return new OrdinaryContext(frame,r,new Availability(true,null),proofs,role,terms,contextAvailable,supported,active,incoming,ready,unsupported,rows,material);
    }
    public static OrdinaryInitiation initiation(RawJson raw,Context c,OrdinaryRequest r) {
        JsonNode n=parse(raw); envelope(n,c,INITIATE_STEP,false); JsonNode a=field(n,"character_interaction_ordinary_initiation");
        closed(a,union(COMMON,"native_call_completed","dispatch_invoked","native_queue_result","queue_submitted","verification_pending","postcondition_verified","reason","preflight_context"));
        OrdinaryProofs proofs=common(a,c,r,"ck3-character-interaction-ordinary-initiation-v1","native_current_ordinary_interaction_command_"+c.build().version(),false);
        OrdinaryContext preflight=context(field(a,"preflight_context"),c,r,positive64(n,"query_sequence"));
        boolean completed=bool(a,"native_call_completed"),dispatched=bool(a,"dispatch_invoked"),queued=bool(a,"queue_submitted"),pending=bool(a,"verification_pending"); no(a,"postcondition_verified");
        QueueResult queue=enumeration(a,"native_queue_result",QueueResult.class); need(queued==(queue==QueueResult.SUBMITTED) && pending==dispatched,"ordinary receipt queue/pending classification differs");
        eq(a,"status",dispatched?"pending":"not_dispatched"); eq(n,"status",dispatched?"pending":"not_dispatched");
        if(dispatched) need(queue!=QueueResult.NOT_ATTEMPTED && proofs.complete() && preflight.readyToInitiate(),"ordinary dispatch lacks actual final ready context");
        else need(queue==QueueResult.NOT_ATTEMPTED && !queued,"non-dispatch invented queue result");
        String reason=queue==QueueResult.SUBMITTED?nullableText(a,"reason"):reason(a,"reason");
        if(queue==QueueResult.SUBMITTED) need(completed && reason==null,"submitted ordinary queue receipt inconsistent");
        return new OrdinaryInitiation(preflight,completed,dispatched,queue,queued,pending,reason);
    }
    private static OrdinaryProofs common(JsonNode n,Context c,OrdinaryRequest r,String schema,String source,boolean readOnly) {
        need(c.build()==Build.CROZIER3 || c.build()==Build.CROZIER4,"ordinary interaction exact source only qualifies .3/.4");
        eq(n,"schema",schema); eq(n,"source",source); need(bool(n,"read_only")==readOnly,"ordinary read-only marker differs"); build(n,"exact_build","executable_sha256",c);
        eq(n,"snapshot_revision",c.revision()); eq(n,"date_raw",c.date()); eq(n,"game_pid",BigInteger.valueOf(c.before().game().pid())); eq(n,"connection_generation",c.connectionGeneration()); eq(n,"player_character_id",c.actor()); eq(n,"recipient_id",BigInteger.valueOf(r.recipient().value())); eq(n,"interaction_key",r.interaction().value()); no(n,"business_postcondition_verified");
        return new OrdinaryProofs(bool(n,"source_code_pins_verified"),bool(n,"actor_binding_verified"),bool(n,"recipient_binding_verified"),bool(n,"owner_thread_verified"),bool(n,"tls_verified"),bool(n,"frame_verified"),number(n,"owner_thread_id",BigInteger.ZERO,U32).longValueExact(),u64(n,"owner_pump_epoch"));
    }
    private static void envelope(JsonNode n,Context c,String step,boolean readOnly) {
        String payload=readOnly?"character_interaction_ordinary_context":"character_interaction_ordinary_initiation";
        closed(n,"step","accepted","status","read_only","query_sequence","snapshot_revision","date_raw","game_pid","connection_generation","backend_id",payload);
        eq(n,"step",step); yes(n,"accepted"); need(bool(n,"read_only")==readOnly,"ordinary envelope read-only mismatch"); eq(n,"backend_id","native-headless");
        eq(n,"snapshot_revision",c.revision()); eq(n,"date_raw",c.date()); eq(n,"game_pid",BigInteger.valueOf(c.before().game().pid())); eq(n,"connection_generation",c.connectionGeneration()); positive64(n,"query_sequence");
    }
    private static void education(Context c,OrdinaryRequest r) { need(c.build()==Build.CROZIER4 && r.interaction().value().equals("educate_child_interaction"),"education extension requires actual .4 education context"); }
    private static EducationOptions educationOptions(JsonNode n,Context c,OrdinaryRequest r,boolean contextAvailable) {
        education(c,r); closed(n,"status","rows","unavailable_reason"); String status=text(n,"status"); boolean available=status.equals("available"); need(available || status.equals("unavailable"),"education option status differs");
        List<EducationOption> rows=list(n,"rows",4096,row->{
            closed(row,"declared_ordinal","flag_full_u32","canonical_flag_key","selected","bank_value_u8","ordinal_selected");
            int ordinal=integer(row,"declared_ordinal",0,Integer.MAX_VALUE); long flag=number(row,"flag_full_u32",BigInteger.ZERO,U32).longValueExact(); String key=nullableText(row,"canonical_flag_key"); if(key!=null) new InteractionKey(key);
            int bank=integer(row,"bank_value_u8",0,255); boolean selected=bool(row,"selected"),ordinalSelected=bool(row,"ordinal_selected"); need(ordinalSelected==(bank==1),"education ordinal byte mismatch");
            return new EducationOption(ordinal,flag,key,selected,bank,ordinalSelected);
        });
        if(!available) { need(rows.isEmpty(),"unavailable education options must remain empty"); return new EducationOptions(new Availability(false,reason(n,"unavailable_reason")),rows); }
        nil(n,"unavailable_reason"); need(contextAvailable,"available education rows lack owned context");
        for(int i=0;i<rows.size();i++) {
            EducationOption row=rows.get(i); need(row.ordinal()==i,"education authored order changed"); EducationOption first=row;
            for(int j=0;j<i;j++) if(rows.get(j).flag()==row.flag()) { first=rows.get(j); break; }
            need(row.selected()==(first.bankByte()==1),"duplicate education flag must use first bank getter byte");
        }
        return new EducationOptions(new Availability(true,null),rows);
    }
    private static EducationMaterialization materialization(JsonNode n,Context c,OrdinaryRequest r,boolean contextAvailable,Roles roles,Optional<EducationOptions> rows) {
        education(c,r); closed(n,"status","child_full_id","guardian_full_id","requested_option_keys","pair_matches","option_keys_match","unavailable_reason");
        Long child=nullableId(n,"child_full_id"),guardian=nullableId(n,"guardian_full_id"); need((child==null)==(guardian==null),"materialized education pair incomplete");
        List<String> options=field(n,"requested_option_keys").isNull()?null:list(n,"requested_option_keys",4096,v->{ need(v.isTextual(),"education option key must be a string"); return new InteractionKey(v.textValue()).value(); });
        Boolean pair=nullableBool(n,"pair_matches"),keys=nullableBool(n,"option_keys_match"); if(child==null) need(pair==null,"absent education pair invented match"); if(options==null) need(keys==null,"absent education options invented match");
        EducationIntent expected=r.education().orElse(new EducationIntent(Optional.empty(),Optional.empty(),Optional.empty()));
        need(java.util.Objects.equals(child,expected.child().map(CharacterId::value).orElse(null)) && java.util.Objects.equals(guardian,expected.guardian().map(CharacterId::value).orElse(null)) && java.util.Objects.equals(options,expected.options().map(v->v.stream().map(InteractionKey::value).toList()).orElse(null)),"education materialization must echo exact requested pair and option intent");
        boolean available=text(n,"status").equals("available"); if(!available) { eq(n,"status","unavailable"); return new EducationMaterialization(new Availability(false,reason(n,"unavailable_reason")),child,guardian,options,pair,keys); }
        nil(n,"unavailable_reason"); need(contextAvailable && rows.isPresent() && rows.orElseThrow().availability().available(),"education materialization lacks post-validate rows");
        if(child!=null) need(Boolean.TRUE.equals(pair) && java.util.Objects.equals(child,roles.secondaryRecipient()) && java.util.Objects.equals(guardian,roles.secondaryActor()),"materialized education roles differ from final native roles");
        if(options!=null) need(Boolean.TRUE.equals(keys),"native requested option match not established");
        return new EducationMaterialization(new Availability(true,null),child,guardian,options,pair,keys);
    }
    private static void validateGuardianSkills(JsonNode n,Context c,OrdinaryRequest r,boolean available,Roles roles) {
        education(c,r); need(available,"guardian skills require available context"); Set<String> keys=Set.of("schema","role_source","child_character_id","character_id","owning_native_revision","binding_status","unavailable_reason","skills");
        for(String optional:List.of("education_traits","education_culture_parameters","total_martial_callback_v1")) if(n.has(optional)) keys=union(keys,optional);
        closed(n,keys); eq(n,"schema","request_guardian_skill_inputs_v1"); eq(n,"role_source","request_guardian_secondary_actor"); eq(n,"owning_native_revision",c.revision());
        Long child=nullableId(n,"child_character_id"),guardian=nullableId(n,"character_id"); need(java.util.Objects.equals(child,roles.secondaryRecipient()) && java.util.Objects.equals(guardian,roles.secondaryActor()),"guardian skill source final role mismatch");
        String binding=text(n,"binding_status"); need(Set.of("resolved","known_null","unavailable").contains(binding),"guardian skill binding status differs");
        if(binding.equals("resolved")) { need(child!=null && child!=0 && guardian!=null && guardian!=0,"resolved guardian role missing"); nil(n,"unavailable_reason"); }
        else if(binding.equals("known_null")) { need(guardian==null,"known-null guardian role changed"); eq(n,"unavailable_reason","request_guardian_role_known_null"); }
        else reason(n,"unavailable_reason");
        JsonNode skills=field(n,"skills"); closed(skills,"diplomacy","martial","stewardship","intrigue","learning");
        for(String key:List.of("diplomacy","martial","stewardship","intrigue","learning")) sample(field(skills,key),binding,false);
        if(n.has("education_traits")) { JsonNode traits=field(n,"education_traits"); closed(traits,"intellect_good_3","intellect_good_2","intellect_good_1","shrewd"); for(String key:List.of("intellect_good_3","intellect_good_2","intellect_good_1","shrewd")) sample(field(traits,key),binding,true); }
        if(n.has("total_martial_callback_v1")) { JsonNode total=field(n,"total_martial_callback_v1"); closed(total,"source","target_character_id","available","value","unavailable_reason"); eq(total,"source","native_character_total_skill_callback"); need(java.util.Objects.equals(nullableId(total,"target_character_id"),guardian),"total martial callback target differs"); sampleValue(total,binding,false); }
        if(n.has("education_culture_parameters")) { JsonNode culture=field(n,"education_culture_parameters"); closed(culture,"culture_full_id","available","better_ward_education","unavailable_reason"); BigInteger cultureId=nullableNumber(culture,"culture_full_id",BigInteger.ZERO,U32);
            if(bool(culture,"available")) { need(binding.equals("resolved") && cultureId!=null && cultureId.compareTo(U32)<0,"available guardian culture unbound"); bool(culture,"better_ward_education"); nil(culture,"unavailable_reason"); }
            else { nil(culture,"better_ward_education"); reason(culture,"unavailable_reason"); } }
    }
    private static void sample(JsonNode n,String binding,boolean booleanValue) { closed(n,"available","value","unavailable_reason"); sampleValue(n,binding,booleanValue); }
    private static void sampleValue(JsonNode n,String binding,boolean booleanValue) {
        if(bool(n,"available")) { need(binding.equals("resolved"),"available guardian sample lacks resolved roles"); if(booleanValue) bool(n,"value"); else integer(n,"value",Integer.MIN_VALUE,Integer.MAX_VALUE); nil(n,"unavailable_reason"); }
        else { nil(n,"value"); reason(n,"unavailable_reason"); }
    }
}
