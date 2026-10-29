package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Exact pending instance, source RVAs, authored options, quote and reply legality. */
public final class PendingContextCodec {
    public static final String STEP="query-pending-character-interaction-context-v1", CAPABILITY="game.command."+STEP;
    private static final List<String> COSTS=List.of("gold","prestige","piety","renown","influence","herd","treasury","treasury_or_gold","merit","barter_goods");
    private static final List<String> RANSOM=List.of("extortionate_gold","extortionate_current_gold","gold","current_gold","favor","influence_send_option","herd_send_option","current_herd","hook");
    private static final List<String> READINESS=List.of("stable_definition_ready","roles_ready","target_type_key_ready","target_typed_identity_ready","send_options_ready","routing_ready","deadline_ready","auto_accept_ready","reply_legality_ready","generic_costs_ready","special_war_binding_ready","special_outcome_terms_ready","structured_terms_ready","same_frame_ready","interaction_semantic_decision_ready");
    private static final List<String> PIN_KEYS=List.of("backend_id","pending_storage_slot_rva","character_storage_slot_rva","expiration_days_rva","local_routing_predicate_rva","reply_validator_rva","auto_accept_trigger_evaluator_rva","cost_evaluator_rva","common_war_relation_rva","target_type_registry_getter_rva","target_type_registry_rva","script_identifier_name_rva","reply_primary_vtable_rva","reply_secondary_vtable_rva","war_victory_special_vtable_rva","war_white_peace_special_vtable_rva","war_defeat_special_vtable_rva");
    private static final List<String> PINS3=List.of("ck3-1.20.0.3-native-pending-character-interaction-context-v1","0x5D1EC80","0x5C67568","0x5C68CFC","0x136D1B0","0x2968490","0x372DF30","0x310CEE0","0x28BC270","0x3795A80","0x54F2AF0","0x3F4F900","0x448BC18","0x448BBE8","0x46C3AA0","0x46C3B10","0x46C3B80");
    private static final List<String> PINS11906=List.of("ck3-1.19.0.6-native-pending-character-interaction-context-v1","0x57BF1C8","0x570C130","0x570F528","0x1266BA0","0x26B3540","0x334C510","0x2CDB7B0","0x2610840","0x33C52B0","0x4FFE290","0x3B58970","0x4082930","0x4082900","0x428EEA8","0x428EF88","0x428EF18");
    private static final List<String> PINS4=List.of("ck3-1.20.0.4-native-pending-character-interaction-context-v1","0x5D1EC80","0x5C67568","0x5C68CFC","0x136D190","0x2968470","0x372DF10","0x310CEC0","0x28BC250","0x3795A60","0x54F2AF0","0x3F4F8E0","0x448BC28","0x448BBF8","0x46C3AB0","0x46C3B20","0x46C3B90");
    private static final Set<String> UNAVAILABLE=Set.of("requires_application_main","state_changed","requires_paused","map_not_ready","unsupported_build","pending_storage_unavailable","pending_generation_mismatch","character_storage_unavailable","played_character_generation_mismatch","pending_roles_unavailable","pending_routing_unavailable","pending_not_routed_to_played_character","pending_reply_state_unavailable","pending_definition_unavailable","pending_target_unavailable","target_type_registry_unavailable","target_type_key_unavailable","send_options_unavailable","send_option_evaluation_unavailable","pending_deadline_unavailable","auto_accept_unavailable","reply_legality_unavailable","structured_costs_unavailable","pending_terms_unavailable","internal_error");
    private static final Set<String> INVALID=Set.of("invalid_pending_interaction_id","invalid_played_character_id","pending_roles_invalid","pending_routing_invalid","pending_definition_invalid","target_type_registry_drift","target_type_index_out_of_bounds","send_option_count_invalid","send_option_count_mismatch","send_option_storage_invalid","send_option_row_invalid","exclusive_send_option_selection_invalid","pending_deadline_invalid","auto_accept_invalid","reply_validator_semantic_mismatch");
    private PendingContextCodec() { }
    private static final Set<String> NATIVE_FIELDS=Set.of("step","accepted","status","query_sequence","snapshot_revision","pending_character_interaction_context","backend_id");
    private static final Set<String> HEADERS=Set.of("queried_snapshot_id","queried_revision","queried_native_revision");
    private static final Set<String> MIRRORS=Set.of("schema","schema_version","date_raw","pending_interaction_id","reason","build","definition","roles","target","send_options","routing","deadline","auto_accept","legality","terms","readiness","provenance");
    /** Only the actual native ReadContract may use this exact seven-field boundary. */
    public static PendingContext decodeNative(RawJson raw,Context c,PendingId requested) {
        JsonNode original=parse(raw);envelope(original,c,true);return decodeEnvelope(original,c,requested);
    }
    /** Explicit historical native/recorded/Driver/public profiles, with no shape aliases or synthesized fields. */
    public static PendingContext decode(RawJson raw,Context c,PendingId requested) {
        JsonNode original=parse(raw);envelope(original,c,false);return decodeEnvelope(original,c,requested);
    }
    private static void envelope(JsonNode original,Context current,boolean nativeOnly) {
        Set<String> keys=new HashSet<>(NATIVE_FIELDS);
        boolean recorded=original.has("queried_snapshot_id"),driver=original.has("pending_character_interaction_context_ready"),exact=original.has("scope");
        boolean legacyRecorded=recorded&&!driver&&!exact&&!original.has("backend_id");
        need(!nativeOnly||!recorded&&!driver&&!exact,"an actual Native result cannot contain Driver/public headers");
        if(!nativeOnly&&recorded)keys.addAll(HEADERS);
        if(!nativeOnly&&legacyRecorded)keys.remove("backend_id");
        if(!nativeOnly&&driver){need(recorded,"the Driver profile requires all original frame headers");keys.addAll(MIRRORS);keys.add("pending_character_interaction_context_ready");}
        if(!nativeOnly&&exact){need(driver,"the exact public profile requires the complete original Driver mirrors");keys.addAll(Set.of("scope","source","binding"));}
        closed(original,keys);
        if(!legacyRecorded)eq(original,"backend_id","native-headless");
        if(recorded){eq(original,"queried_snapshot_id",current.before().frame().snapshotId());eq(original,"queried_revision",current.before().frame().revision());eq(original,"queried_native_revision",current.revision());}
        if(driver){JsonNode context=field(original,"pending_character_interaction_context");
            for(String key:MIRRORS)need(java.util.Objects.equals(field(original,key),field(context,key)),"pending Driver mirror differs from original native context: "+key);
            need(bool(original,"pending_character_interaction_context_ready")==bool(field(context,"readiness"),"interaction_semantic_decision_ready"),"pending Driver readiness differs from its actual typed source");}
        if(exact){eq(original,"scope","exact-pending-character-interaction-context");
            JsonNode source=field(original,"source");closed(source,"game_version","executable_sha256","snapshot_id","revision","native_revision","date_raw","paused","backend_id");
            build(source,"game_version","executable_sha256",current);eq(source,"snapshot_id",current.before().frame().snapshotId());eq(source,"revision",current.before().frame().revision());
            eq(source,"native_revision",current.revision());eq(source,"date_raw",current.date());yes(source,"paused");eq(source,"backend_id","native-headless");
            JsonNode binding=field(original,"binding");closed(binding,"snapshot_id","revision","native_revision","date_raw","pending_interaction_id","expected_revision");
            eq(binding,"snapshot_id",current.before().frame().snapshotId());eq(binding,"revision",current.before().frame().revision());eq(binding,"native_revision",current.revision());eq(binding,"date_raw",current.date());
            need(current.controls().pending()!=null,"exact pending binding requires its actual current instance");eq(binding,"pending_interaction_id",BigInteger.valueOf(current.controls().pending().instance().value()));eq(binding,"expected_revision",current.before().frame().revision());}
    }
    private static PendingContext decodeEnvelope(JsonNode envelope,Context c,PendingId requested) {
         eq(envelope,"step",STEP); yes(envelope,"accepted"); eq(envelope,"snapshot_revision",c.revision()); BigInteger sequence=positive64(envelope,"query_sequence");
        JsonNode n=field(envelope,"pending_character_interaction_context");
        closed(n,"schema","schema_version","status","snapshot_revision","date_raw","pending_interaction_id","reason","build","definition","roles","target","send_options","routing","deadline","auto_accept","legality","terms","readiness","provenance");
        eq(n,"schema","pending-character-interaction-context-v1"); eq(n,"schema_version",BigInteger.ONE); eq(n,"snapshot_revision",c.revision()); eq(n,"date_raw",c.date()); eq(n,"pending_interaction_id",BigInteger.valueOf(requested.value()));
        JsonNode b=field(n,"build"); closed(b,"version","exe_sha256"); build(b,"version","exe_sha256",c);
        List<PendingContext.SourcePin> pins=pins(field(n,"provenance"),c.build()); PendingContext.Status status=enumeration(n,"status",PendingContext.Status.class);
        eq(envelope,"status",status.name().toLowerCase(java.util.Locale.ROOT));
        PendingSummary pending=c.controls().pending(); need(pending!=null && pending.instance().equals(requested),"pending query must match current full signed native instance");
        Frame f=new Frame(c.revision(),c.date(),c.actor(),c.build(),sequence);
        if(status!=PendingContext.Status.AVAILABLE) {
            String reason=stable(n,"reason"); need((status==PendingContext.Status.UNAVAILABLE?UNAVAILABLE:INVALID).contains(reason),"pending reason disagrees with status");
            nil(n,"definition","roles","target","send_options","routing","deadline","auto_accept","terms");
            PendingContext.Legality legality=legality(field(n,"legality"),false,reason);
            PendingContext.Readiness readiness=readiness(field(n,"readiness"),false,false,false,null,false,null,reason);
            return new PendingContext(f,requested,status,reason,null,null,null,null,null,null,null,legality,null,readiness,pins);
        }
        nil(n,"reason");
        JsonNode d=field(n,"definition"); closed(d,"canonical_key","deterministic_key_hash","runtime_ordinal");
        PendingContext.Definition definition=new PendingContext.Definition(stable(d,"canonical_key"),number(d,"deterministic_key_hash",BigInteger.ZERO,U32).longValueExact(),integer(d,"runtime_ordinal",0,Integer.MAX_VALUE));
        JsonNode rs=field(n,"roles"); closed(rs,"actor_character_id","recipient_character_id","secondary_actor_character_id","secondary_recipient_character_id","intermediary_character_id");
        PendingContext.Roles roles=new PendingContext.Roles(role(rs,"actor_character_id",true),role(rs,"recipient_character_id",true),role(rs,"secondary_actor_character_id",false),role(rs,"secondary_recipient_character_id",false),role(rs,"intermediary_character_id",false));
        need(roles.actor()==pending.sender().value(),"pending sender differs from native snapshot mirror");
        PendingContext.Target target=target(field(n,"target"),definition.key()); boolean targetReady=!target.present() || target.identityStatus().equals("available");
        JsonNode options=field(n,"send_options"); closed(options,"exclusive","definition_count","context_count","rows"); boolean exclusive=bool(options,"exclusive"); int count=integer(options,"definition_count",0,256); eq(options,"context_count",BigInteger.valueOf(count));
        List<PendingContext.Option> rows=list(options,"rows",256,row->{
            closed(row,"native_index","numeric_flag_identifier","selected","is_shown","is_valid","canonical_flag_status","canonical_flag_key","canonical_flag_reason");
            int index=integer(row,"native_index",0,Math.max(0,count-1)); String canonicalStatus=text(row,"canonical_flag_status"),key=nullableText(row,"canonical_flag_key"),reason=nullableText(row,"canonical_flag_reason");
            boolean mapped=(definition.key().equals("pay_ransom_interaction") || definition.key().equals("ransom_me_interaction")) && count==9 && canonicalStatus.equals("available") && index<9 && RANSOM.get(index).equals(key) && reason==null;
            boolean unmapped=canonicalStatus.equals("unavailable") && key==null && "numeric_flag_identifier_string_mapping_not_closed".equals(reason);
            need(mapped || unmapped,"pending option canonical string mapping was invented");
            return new PendingContext.Option(index,integer(row,"numeric_flag_identifier",0,Integer.MAX_VALUE),bool(row,"selected"),bool(row,"is_shown"),bool(row,"is_valid"),canonicalStatus,key,reason);
        });
        need(rows.size()==count,"complete authored send-option vector required"); for(int i=0;i<count;i++) need(rows.get(i).nativeIndex()==i,"send-option authored order changed");
        need(!exclusive || rows.stream().filter(PendingContext.Option::selected).count()<=1,"exclusive options selected multiple rows");
        JsonNode rt=field(n,"routing"); closed(rt,"kind","played_character_id","current_responder_role","reply_execution_channel","local_route","auto_accept_notification");
        int kind=integer(rt,"kind",0,2),player=NativeCharacterId.fromJson(field(rt,"played_character_id")).value(); String responder=kind==1?"intermediary":"recipient";
        eq(rt,"current_responder_role",responder); eq(rt,"reply_execution_channel",responder); yes(rt,"local_route"); need(BigInteger.valueOf(player).equals(c.actor()) && player==(kind==1?roles.intermediary():roles.recipient()),"pending local responder differs from actual played identity");
        boolean notification=bool(rt,"auto_accept_notification"); need(notification==pending.autoAcceptNotification(),"notification mirror differs");
        PendingContext.Routing routing=new PendingContext.Routing(kind,player,responder,responder,notification);
        JsonNode dl=field(n,"deadline"); closed(dl,"age_days","expiration_days","remaining_days","expiry_boundary_status"); int age=integer(dl,"age_days",0,Integer.MAX_VALUE),expiration=integer(dl,"expiration_days",1,100000),remaining=integer(dl,"remaining_days",0,Integer.MAX_VALUE);
        need(remaining==Math.max(0,expiration-age),"pending deadline remaining projection differs"); String boundary=age<expiration?"not_reached":"at_or_past_daily_expiry_queue_threshold"; eq(dl,"expiry_boundary_status",boundary);
        JsonNode auto=field(n,"auto_accept"); closed(auto,"status","value","reason"); eq(auto,"status","available"); nil(auto,"reason"); boolean autoAccept=bool(auto,"value");
        PendingContext.Legality legality=legality(field(n,"legality"),true,null);
        if(notification) need(legality.acknowledge().allowed() && !legality.accept().allowed() && !legality.reject().allowed() && !legality.block().allowed(),"notification is acknowledge-only");
        else need(!legality.acknowledge().allowed(),"ordinary pending cannot acknowledge");
        if(autoAccept || roles.actor()==roles.recipient()) need(!legality.reject().allowed() && !legality.block().allowed(),"auto/self reply legality differs");
        PendingContext.Terms terms=terms(field(n,"terms"),definition.key(),roles,routing,rows);
        PendingContext.Readiness readiness=readiness(field(n,"readiness"),true,target.present(),targetReady,target.typedIdentityReason(),terms.war().available(),terms.war().reason(),null);
        return new PendingContext(f,requested,status,null,definition,roles,target,new PendingContext.Options(exclusive,count,rows),routing,new PendingContext.Deadline(age,expiration,remaining,boundary),autoAccept,legality,terms,readiness,pins);
    }
    private static PendingContext.Target target(JsonNode n,String definition) {
        closed(n,"present","raw_type_index","raw_16_bytes_hex","type_key_status","type_key","type_key_reason","typed_identity_status","typed_identity","typed_identity_reason");
        boolean present=bool(n,"present"); int index=integer(n,"raw_type_index",0,65535); String hex=text(n,"raw_16_bytes_hex"); need(hex.matches("[0-9a-fA-F]{32}"),"target must contain exact native 16 bytes");
        byte[] bytes=java.util.HexFormat.of().parseHex(hex); need(Short.toUnsignedInt(ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getShort())==index && present==(index!=0),"target raw native tag differs");
        String key=nullableText(n,"type_key"),identityStatus=text(n,"typed_identity_status"),identity=nullableText(n,"typed_identity"),reason=nullableText(n,"typed_identity_reason");
        if(!present) { eq(n,"type_key_status","absent"); nil(n,"type_key","type_key_reason","typed_identity","typed_identity_reason"); eq(n,"typed_identity_status","absent"); }
        else {
            eq(n,"type_key_status","available"); nil(n,"type_key_reason"); stable(n,"type_key"); boolean war=definition.equals("call_ally_interaction") && index==16 && "war".equals(key);
            if(war && identityStatus.equals("available")) {
                need(reason==null && identity!=null && identity.matches("war:[1-9][0-9]{0,9}"),"typed war target requires canonical identity");
                int id=Integer.parseInt(identity.substring(4)); need(id>0 && ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getInt(8)==id,"typed war full identity differs from original bytes");
            } else { need(identityStatus.equals("unavailable") && identity==null && (war?"war_target_identity_unavailable":"generic_scope_payload_identity_not_closed").equals(reason),"opaque native target invented typed identity"); }
        }
        return new PendingContext.Target(present,index,hex,key,identityStatus,identity,reason);
    }
    private static PendingContext.Legality legality(JsonNode n,boolean available,String topReason) {
        closed(n,"accept","reject","block","acknowledge"); return new PendingContext.Legality(legal(field(n,"accept"),available,topReason),legal(field(n,"reject"),available,topReason),legal(field(n,"block"),available,topReason),legal(field(n,"acknowledge"),available,topReason));
    }
    private static PendingContext.Legal legal(JsonNode n,boolean available,String topReason) {
        closed(n,"status","allowed","reason"); boolean allowed=bool(n,"allowed"); String reason=nullableText(n,"reason");
        if(available) { eq(n,"status","available"); if(allowed) need(reason==null,"allowed reply has failure reason"); else stable(n,"reason"); }
        else { eq(n,"status","unavailable"); need(!allowed && java.util.Objects.equals(reason,topReason),"unavailable reply invented legality"); }
        return new PendingContext.Legal(available,allowed,reason);
    }
    private static PendingContext.Terms terms(JsonNode n,String definition,PendingContext.Roles roles,PendingContext.Routing routing,List<PendingContext.Option> rows) {
        Set<String> fields=Set.of("special_data_present","special_war_binding","structured_costs","structured_exchanges","structured_effect_preview","recipient_ai_acceptance_score","recipient_ai_final_decision");
        if(n.has("ransom_quote")) fields=union(fields,"ransom_quote"); closed(n,fields); boolean special=bool(n,"special_data_present"); PendingContext.WarTerm war=war(field(n,"special_war_binding"),definition,special);
        JsonNode costs=field(n,"structured_costs"); closed(costs,"status","value","reason"); eq(costs,"status","available"); nil(costs,"reason");
        JsonNode cv=field(costs,"value"); closed(cv,"raw_scale","payer_role","application_timing","pending_payment_state","entries"); eq(cv,"raw_scale",BigInteger.valueOf(100000)); eq(cv,"payer_role","actor"); eq(cv,"application_timing","on_send"); eq(cv,"pending_payment_state","already_applied");
        JsonNode entries=field(cv,"entries"); need(entries.isArray() && entries.size()==10,"all ten native cost entries required"); List<BigInteger> rawCosts=new ArrayList<>();
        for(int i=0;i<10;i++) { JsonNode e=entries.get(i); closed(e,"resource_key","raw"); eq(e,"resource_key",COSTS.get(i)); rawCosts.add(number(e,"raw",I64_MIN,I64_MAX)); }
        Optional<PendingContext.Ransom> ransom=n.has("ransom_quote")?Optional.of(ransom(field(n,"ransom_quote"),definition,roles,routing,rows)):Optional.empty();
        return new PendingContext.Terms(special,war,rawCosts,unknown(field(n,"structured_exchanges")),unknown(field(n,"structured_effect_preview")),unknown(field(n,"recipient_ai_acceptance_score")),unknown(field(n,"recipient_ai_final_decision")),ransom);
    }
    private static PendingContext.UnknownTerm unknown(JsonNode n) { closed(n,"status","value","reason"); eq(n,"status","unavailable"); nil(n,"value"); return new PendingContext.UnknownTerm(stable(n,"reason")); }
    private static PendingContext.WarTerm war(JsonNode n,String definition,boolean special) {
        closed(n,"status","value","reason"); boolean known=Set.of("end_war_attacker_victory_interaction","end_war_attacker_white_peace_interaction","end_war_attacker_defeat_interaction").contains(definition);
        if(text(n,"status").equals("unavailable")) {
            nil(n,"value"); String reason=stable(n,"reason"); boolean matches=reason.equals("special_war_binding_not_applicable") && !special && !known
                || reason.equals("special_interaction_subtype_opaque") && special && !known || reason.equals("special_interaction_identity_mismatch") && (special || known)
                || reason.equals("special_war_binding_unavailable") || reason.equals("special_war_roles_mismatch") && special && known;
            need(matches,"special-war unknown reason disagrees with native special data"); return new PendingContext.WarTerm(false,null,reason);
        }
        eq(n,"status","available"); nil(n,"reason"); need(special && known,"available special war lacks known definition/special data");
        JsonNode v=field(n,"value"); closed(v,"special_interaction_kind","absolute_outcome","war_id","actor_war_role","recipient_war_role","binding_source");
        String kind=definition.equals("end_war_attacker_white_peace_interaction")?"end_war_white_peace_interaction":definition;
        String outcome=definition.equals("end_war_attacker_victory_interaction")?"attacker_victory":definition.equals("end_war_attacker_defeat_interaction")?"attacker_defeat":"white_peace";
        eq(v,"special_interaction_kind",kind); eq(v,"absolute_outcome",outcome); eq(v,"binding_source","native_common_war_relation");
        String actor=text(v,"actor_war_role"),recipient=text(v,"recipient_war_role"); need(actor.equals("primary_attacker") && recipient.equals("primary_defender") || actor.equals("primary_defender") && recipient.equals("primary_attacker"),"special-war roles are not opposite primary sides");
        return new PendingContext.WarTerm(true,new PendingContext.War(kind,outcome,integer(v,"war_id",1,Integer.MAX_VALUE),actor,recipient),null);
    }
    private static PendingContext.Ransom ransom(JsonNode n,String definition,PendingContext.Roles roles,PendingContext.Routing routing,List<PendingContext.Option> rows) {
        closed(n,"status","value","reason"); boolean self=definition.equals("ransom_me_interaction"); need(self || definition.equals("pay_ransom_interaction"),"ransom quote wrong definition");
        if(text(n,"status").equals("unavailable")) { nil(n,"value"); return new PendingContext.Ransom(false,stable(n,"reason"),null,null,null,null,null,null,null,null,null,null,Optional.empty()); }
        eq(n,"status","available"); nil(n,"reason"); JsonNode q=field(n,"value");
        Set<String> fields=Set.of("actor_character_id","jailer_character_id","prisoner_character_id","selected_option_index","selected_option_key","gold_raw","raw_scale","amount_source_key","payer_scope","receiver_scope","application_timing","payment_state","amount_is_current_quote","selected_option_shown","selected_option_valid","custody_matches_recipient","hook_selected","decision_input_ready"); if(q.has("ordinary_gold_decision_ready")) fields=union(fields,"ordinary_gold_decision_ready"); closed(q,fields);
        int index=integer(q,"selected_option_index",2,3),prisoner=self?roles.actor():roles.secondaryRecipient(); need(index==2 || self,"pay ransom cannot invent current-payer binding");
        eq(q,"actor_character_id",BigInteger.valueOf(roles.actor())); eq(q,"jailer_character_id",BigInteger.valueOf(roles.recipient())); eq(q,"prisoner_character_id",BigInteger.valueOf(prisoner));
        eq(q,"selected_option_key",RANSOM.get(index)); eq(q,"raw_scale",BigInteger.valueOf(100000)); eq(q,"amount_source_key",index==2?"normal_ransom_cost_value":"current_gold_value");
        eq(q,"payer_scope","puppet_or_actor"); eq(q,"receiver_scope","recipient"); eq(q,"application_timing","on_accept"); eq(q,"payment_state","pending"); yes(q,"amount_is_current_quote"); yes(q,"custody_matches_recipient");
        need(rows.size()==9 && rows.get(index).selected() && roles.recipient()==routing.player() && prisoner>0 && (!self || roles.secondaryRecipient()==-1),"ransom roles or native selection differs");
        for(int i=0;i<9;i++) { need(RANSOM.get(i).equals(rows.get(i).canonicalKey()),"ransom option mapping differs"); if(i<8 && i!=index) need(!rows.get(i).selected(),"ransom multiple payment options selected"); }
        boolean shown=bool(q,"selected_option_shown"),valid=bool(q,"selected_option_valid"),hook=bool(q,"hook_selected"),ready=bool(q,"decision_input_ready");
        need(shown==rows.get(index).shown() && valid==rows.get(index).valid() && hook==rows.get(8).selected() && ready==(shown && valid && !hook),"ransom quote readiness differs from native option rows");
        Optional<Boolean> ordinary=q.has("ordinary_gold_decision_ready")?Optional.of(bool(q,"ordinary_gold_decision_ready")):Optional.empty(); ordinary.ifPresent(v->need(v==ready,"ransom readiness alias disagrees"));
        return new PendingContext.Ransom(true,null,roles.actor(),roles.recipient(),prisoner,index,RANSOM.get(index),number(q,"gold_raw",BigInteger.ZERO,I64_MAX),shown,valid,hook,ready,ordinary);
    }
    private static PendingContext.Readiness readiness(JsonNode n,boolean available,boolean targetPresent,boolean targetReady,String targetReason,boolean warReady,String warReason,String topReason) {
        closed(n,union(Set.copyOf(READINESS),"not_ready_reasons")); List<Boolean> flags=new ArrayList<>(); for(String key:READINESS) flags.add(bool(n,key));
        List<String> reasons=list(n,"not_ready_reasons",64,v->{ need(v.isTextual() && !v.textValue().isEmpty(),"native readiness reason required"); return v.textValue(); }); unique(reasons,64);
        if(!available) need(flags.stream().noneMatch(Boolean::booleanValue) && reasons.equals(List.of(topReason)),"unavailable pending invented readiness");
        else {
            List<Boolean> expected=List.of(true,true,true,targetReady,true,true,true,true,true,true,warReady,false,false,true,false); need(flags.equals(expected),"pending readiness differs from observed domains");
            List<String> expectedReasons=new ArrayList<>(); if(targetPresent && !targetReady) expectedReasons.add("generic_scope_payload_identity_not_closed".equals(targetReason)?"target_generic_scope_payload_identity_not_closed":targetReason);
            if(!warReady) expectedReasons.add(warReason); expectedReasons.addAll(List.of("special_outcome_terms_unavailable","structured_exchanges_unavailable","structured_effect_preview_unavailable")); need(reasons.equals(expectedReasons),"pending readiness reasons differ");
        }
        return new PendingContext.Readiness(flags.get(0),flags.get(1),flags.get(2),flags.get(3),flags.get(4),flags.get(5),flags.get(6),flags.get(7),flags.get(8),flags.get(9),flags.get(10),flags.get(11),flags.get(12),flags.get(13),flags.get(14),reasons);
    }
    private static List<PendingContext.SourcePin> pins(JsonNode n,Build build) {
        closed(n,Set.copyOf(PIN_KEYS)); List<String> expected=switch(build) { case CROZIER4 -> PINS4; case WANDERER6 -> PINS11906; case CROZIER2 -> { List<String> two=new ArrayList<>(PINS3); two.set(0,"ck3-1.20.0.2-native-pending-character-interaction-context-v1"); yield List.copyOf(two); } case CROZIER3 -> PINS3; }; List<PendingContext.SourcePin> out=new ArrayList<>();
        for(int i=0;i<PIN_KEYS.size();i++) { eq(n,PIN_KEYS.get(i),expected.get(i)); out.add(new PendingContext.SourcePin(PIN_KEYS.get(i),expected.get(i))); } return List.copyOf(out);
    }
    private static int role(JsonNode n,String k,boolean required) { int value=integer(n,k,Integer.MIN_VALUE,Integer.MAX_VALUE); return !required && value==-1?-1:NativeCharacterId.of(value).value(); }
    private static String stable(JsonNode n,String k) { String s=text(n,k); need(!s.isEmpty() && s.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=1024 && s.chars().allMatch(ch->ch>=0x20),"bounded stable native key required"); return s; }
}
