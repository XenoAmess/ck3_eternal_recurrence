package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.application.planning.finance.WarPaymentNodes.*;
import static org.xar.ck3.control.application.planning.finance.WarPaymentNodes.Role.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;

/** Exact raw payment normalization; no maintenance-cost or paid-currency inference. */
public final class WarPaymentExtrasCodec {
    private WarPaymentExtrasCodec() { }
    public static final String JOURNAL_KEY="war_payment_observations_v1", CONTROL_KEY="war_payment_control_v1";
    public static final String WINDOW_CONTRACT="same_owned_process_no_load_v1";
    static final String VERSION="1.20.0.4", SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    static final String GENERIC="generic_wallet_context_v1";
    public enum Mode { ENABLE,DISABLE,QUERY;
        String wire(){return switch(this){case ENABLE->"enable";case DISABLE->"disable";case QUERY->"query";};}
    }
    public static RawJson requestFields(Optional<Mode> sampling,Optional<String> windowContract,String machineId){
        Objects.requireNonNull(sampling);Objects.requireNonNull(windowContract);Objects.requireNonNull(machineId);
        if(sampling.isEmpty()){need(windowContract.isEmpty(),"window contract requires explicit enable");return raw(empty());}
        Mode mode=sampling.orElseThrow();need(windowContract.equals(mode==Mode.ENABLE?Optional.of(WINDOW_CONTRACT):Optional.empty()),"exact enable window contract required");
        ObjectNode out=empty().put("war_payment_sampling",mode.wire()).put("war_payment_machine_id",machineId);
        if(mode==Mode.ENABLE)out.put("war_payment_window_contract",WINDOW_CONTRACT);
        return raw(out);
    }
    public static RawJson normalize(RawJson nativeResult,RawJson actualSnapshot,String machineId,Optional<Mode> sampling){
        Objects.requireNonNull(sampling);Objects.requireNonNull(machineId);
        ObjectNode result=parse(nativeResult),out=empty();
        if(!result.has(JOURNAL_KEY)&&!result.has(CONTROL_KEY)){need(sampling.isEmpty(),"explicit observer control returned no evidence");return raw(out);}
        need(result.has(JOURNAL_KEY),"observer control returned no raw journal");
        ObjectNode j=obj(result.get(JOURNAL_KEY));Check check=new Check(Direction.NATIVE);
        journal(check,j,Optional.of(parse(actualSnapshot)),machineId);out.set(JOURNAL_KEY,j);
        if(sampling.isEmpty())need(!result.has(CONTROL_KEY),"unsolicited observer control result");
        else {ObjectNode c=obj(result.get(CONTROL_KEY));control(check,c,j,sampling.orElseThrow());out.set(CONTROL_KEY,c);}
        return raw(out);
    }
    /** Representation only: callers first normalize against their actual Root snapshot. */
    public static RawJson publicWire(RawJson normalizedExtras){return wire(normalizedExtras,Direction.TO_PUBLIC);}
    public static RawJson nativeWire(RawJson publicExtras){return wire(publicExtras,Direction.FROM_PUBLIC);}
    private static RawJson wire(RawJson extras,Direction direction){
        ObjectNode value=parse(extras);Check check=new Check(direction);
        need(value.size()==0||(value.has(JOURNAL_KEY)&&value.size()==(value.has(CONTROL_KEY)?2:1)),"extras fields");
        if(value.has(JOURNAL_KEY)){
            ObjectNode j=obj(value.get(JOURNAL_KEY));need(j.get("machine_id")!=null&&j.get("machine_id").isTextual(),"journal machine string");
            journal(check,j,Optional.empty(),j.get("machine_id").textValue());
            if(value.has(CONTROL_KEY)){
                ObjectNode c=obj(value.get(CONTROL_KEY));need(c.get("requested")!=null&&c.get("requested").isTextual(),"control mode");
                Mode mode=switch(c.get("requested").textValue()){case "enable"->Mode.ENABLE;case "disable"->Mode.DISABLE;case "query"->Mode.QUERY;default->throw new IllegalArgumentException("war payment unknown control mode");};
                control(check,c,j,mode);
            }
        }
        check.project();return raw(value);
    }
    public static RawJson consumeResource4WalletContexts(RawJson originalJournal,RawJson actualSnapshot,String machineId){
        ObjectNode j=parse(originalJournal);journal(new Check(Direction.NATIVE),j,Optional.of(parse(actualSnapshot)),machineId);
        ObjectNode out=empty();out.set("journal",j);out.set("qualified_resource4_boundaries",WarPaymentResource4Codec.qualified(j));
        out.put("resource_name","unknown").put("maintenance_attribution","unclosed").put("evidence_scope","existing_gateway_original_callback_boundaries_only");return raw(out);
    }
    public static RawJson consumeRaw4GetterObservations(RawJson originalJournal,RawJson actualSnapshot,String machineId){
        ObjectNode j=parse(originalJournal);journal(new Check(Direction.NATIVE),j,Optional.of(parse(actualSnapshot)),machineId);
        ObjectNode out=empty();out.set("journal",j);out.set("qualified_raw4_reads",WarPaymentRaw4Codec.qualified(j));
        out.put("evidence_scope","natural_entry_raw_getter_read_only").put("resource_name","unknown").put("payment_attribution","unclosed");return raw(out);
    }
    static void event(Check c,JsonNode v){c.fields(v,g(Role.U64,"clock_identity sequence"),g(OU32,"thread_id"));}
    static void session(Check c,JsonNode v){c.fields(v,g(U32,"pid"),g(Role.U64,"process_create_time_100ns connection_generation controlled_window_id game_state_identity_witness"),g(OU64,"loaded_game_epoch snapshot_revision native_date_raw"),g(OU32,"player_character_full_id absolute_day_raw"),g(BOOL,"same_owned_process_no_load_window"));}
    static void frame(Check c,JsonNode v){c.fields(v,g(Role.U64,"character wrapper"),g(OU32,"character_id character_magic land_id land_magic army_id army_magic requested_unit_id province_magic province_id"),g(OU64,"character_extension personal_gold_bits wrapper_balance_bits"),g(OU8,"army_1d4"),g(BOOL,"capture_complete"),g(U32,"failed_reads"));}
    static void natural(Check c,JsonNode v){c.fields(v,g(BOOL,"observed"),g(U8,"phase"),g(Role.U64,"actual_entry_rva primary_manager game_state"),g(OU64,"session_identity date_raw"),g(OU32,"absolute_day_raw"),g(NEST,"entry_event"));need(n(v,"phase").intValue()<=2,"unknown natural phase");event(c,v.get("entry_event"));}
    static boolean validEvent(JsonNode v){return nz(v.get("clock_identity"))&&nz(v.get("sequence"))&&present(v,"thread_id");}
    static boolean sameEvent(JsonNode a,JsonNode b){return validEvent(a)&&validEvent(b)&&eq(a,b);}
    static boolean before(JsonNode a,JsonNode b){return validEvent(a)&&validEvent(b)&&eq(a,"clock_identity",b,"clock_identity")&&eq(a,"thread_id",b,"thread_id")&&n(a,"sequence").compareTo(n(b,"sequence"))<0;}
    static boolean sameSession(JsonNode a,JsonNode b){
        if(!nz(a.get("pid"))||!nz(a.get("process_create_time_100ns"))||!nz(a.get("connection_generation"))||!present(a,"player_character_full_id"))return false;
        for(String k:List.of("pid","process_create_time_100ns","connection_generation","player_character_full_id","loaded_game_epoch"))if(!eq(a,k,b,k))return false;
        if(nz(a.get("loaded_game_epoch")))return true;
        return yes(a,"same_owned_process_no_load_window")&&yes(b,"same_owned_process_no_load_window")&&nz(a.get("controlled_window_id"))&&eq(a,"controlled_window_id",b,"controlled_window_id")&&nz(a.get("game_state_identity_witness"))&&eq(a,"game_state_identity_witness",b,"game_state_identity_witness");
    }
    static boolean complete(JsonNode r,JsonNode current){return yes(r,"original_called")&&yes(r,"original_returned")&&!yes(r,"tls_depth_exceeded")&&yes(r.get("before"),"capture_complete")&&yes(r.get("after"),"capture_complete")&&is(r.get("before"),"failed_reads",0)&&is(r.get("after"),"failed_reads",0)&&before(r.get("entry_event"),r.get("returned_event"))&&sameSession(r.get("session_entry"),r.get("session_return"))&&sameSession(r.get("session_entry"),current);}
    static boolean sameCharacter(JsonNode a,JsonNode b){return nz(a.get("character"))&&eq(a,"character",b,"character")&&present(a,"character_id")&&!is(a,"character_id",0xffffffffL)&&eq(a,"character_id",b,"character_id")&&is(a,"character_magic",0x43686172)&&is(b,"character_magic",0x43686172)&&nz(a.get("character_extension"))&&eq(a,"character_extension",b,"character_extension");}
    private static final List<String> VALUES=List.of("value_2c0","value_2c8","value_28","value_30");
    static void genericSnapshot(Check c,JsonNode v){
        c.fields(v,g(OU64,"context_identity_before context_identity_after"),g(OI64,"value_2c0 value_2c8 value_28 value_30"),g(BOOL,"capture_complete context_stable"),g(U32,"failed_reads"));
        boolean stable=nz(v.get("context_identity_before"))&&nz(v.get("context_identity_after"))&&eq(v,"context_identity_before",v,"context_identity_after");
        need(yes(v,"context_stable")==stable,"generic context identity stability");
        if(!nz(v.get("context_identity_before")))for(String k:VALUES)need(!present(v,k),"values without input context");
        boolean complete=stable&&is(v,"failed_reads",0)&&VALUES.stream().allMatch(k->present(v,k));
        need(yes(v,"capture_complete")==complete,"generic context completeness");
    }
    static void genericTrace(Check c,JsonNode v){
        c.fields(v,g(Role.U64,"module_base"),g(U32,"module_image_size reported_frame_count caller_match_count"),g(BOOL,"capture_succeeded truncated parent_in_same_image"),g(OU64,"parent_return_absolute parent_return_rva"),g(NEST,"frames_absolute"));
        ArrayNode frames=list(v.get("frames_absolute"),32);c.u64Array(frames);for(JsonNode f:frames)need(nz(f),"zero parent frame");
        boolean captured=n(v,"reported_frame_count").signum()>0&&n(v,"reported_frame_count").compareTo(BigInteger.valueOf(32))<=0;
        need(yes(v,"capture_succeeded")==captured&&(captured?frames.size()==n(v,"reported_frame_count").intValue():frames.isEmpty()),"parent capture count");
        need(yes(v,"truncated")== (captured&&is(v,"reported_frame_count",32)),"parent truncation");
        BigInteger base=n(v,"module_base"),caller=base.signum()!=0&&base.compareTo(WarPaymentNodes.U64.subtract(BigInteger.valueOf(0x28a6d7c)))<=0?base.add(BigInteger.valueOf(0x28a6d7c)):null;
        int matches=0,index=-1;for(int i=0;i<frames.size();i++)if(caller!=null&&num(frames.get(i)).equals(caller)){matches++;index=i;}
        need(is(v,"caller_match_count",matches),"parent caller count");
        BigInteger parent=matches==1&&index+1<frames.size()?num(frames.get(index+1)):null;
        need(parent==null?!present(v,"parent_return_absolute"):present(v,"parent_return_absolute")&&n(v,"parent_return_absolute").equals(parent),"parent address");
        boolean same=parent!=null&&base.signum()!=0&&n(v,"module_image_size").compareTo(BigInteger.valueOf(0x28a6d7c))>0&&parent.compareTo(base)>=0&&parent.subtract(base).compareTo(n(v,"module_image_size"))<0;
        need(yes(v,"parent_in_same_image")==same&&(same?present(v,"parent_return_rva")&&n(v,"parent_return_rva").equals(parent.subtract(base)):!present(v,"parent_return_rva")),"parent image provenance");
    }
    static void generic(Check c,JsonNode v,JsonNode record){
        c.fields(v,g(U32,"schema_version"),g(Role.U64,"source_entry_rva source_wallet_return_rva"),g(TEXT,"attribution_scope maintenance_attribution"),g(OI64,"before_computed_add_raw"),g(OBOOL,"before_formula_matches_amount"),g(BOOL,"context_values_stable"),g(NEST,"before after parent_trace"));
        need(is(v,"schema_version",1)&&is(v,"source_entry_rva",0x28a6d10)&&is(v,"source_wallet_return_rva",0x28a6d7c)&&v.get("attribution_scope").asText().equals("raw_source_context_and_unwind_parent_only")&&v.get("maintenance_attribution").asText().equals("unclosed"),"generic source/attribution");
        need(is(record,"kind",2)&&is(record,"caller_return_rva",0x28a6d7c),"generic different callback");
        genericSnapshot(c,v.get("before"));genericSnapshot(c,v.get("after"));genericTrace(c,v.get("parent_trace"));
        JsonNode a=v.get("before"),b=v.get("after");BigInteger computed=null;
        if(yes(a,"capture_complete"))computed=n(a,"value_2c0").subtract(n(a,"value_2c8")).subtract(n(a,"value_28").add(n(a,"value_30"))).add(TWO63).mod(TWO64).subtract(TWO63);
        need(computed==null?!present(v,"before_computed_add_raw")&&!present(v,"before_formula_matches_amount"):present(v,"before_computed_add_raw")&&n(v,"before_computed_add_raw").equals(computed)&&present(v,"before_formula_matches_amount")&&yes(v,"before_formula_matches_amount")==computed.equals(n(record,"amount_raw")),"generic arithmetic");
        boolean stable=yes(a,"capture_complete")&&yes(b,"capture_complete")&&eq(a,"context_identity_before",b,"context_identity_before")&&VALUES.stream().allMatch(k->eq(a,k,b,k));
        need(yes(v,"context_values_stable")==stable,"generic values stability");
    }
    static void record(Check c,JsonNode v){
        String nested="entry_event returned_event parent_transition_entry parent_gateway_entry natural_parent_metadata natural_return_metadata session_entry session_return before after";
        if(v!=null&&v.has(GENERIC))nested+=" "+GENERIC;
        if(v!=null&&v.has(WarPaymentResource4Codec.KEY))nested+=" "+WarPaymentResource4Codec.KEY;
        c.fields(v,g(Role.U64,"journal_sequence receiver second_pointer caller_return_rva parent_transition_army parent_gateway_character parent_transition_caller parent_gateway_caller raw_return_bits"),g(U8,"kind"),g(I64,"amount_raw parent_gateway_amount"),g(I32,"resource_kind_raw component_raw parent_gateway_resource parent_gateway_component"),g(BOOL,"original_called original_returned clock_thread_order_matches session_matches natural_parent_matches same_character_after same_wrapper_after personal_wrapper_matches_character source_boarding_call_chain_matches tls_depth_exceeded"),g(NEST,nested));
        need(n(v,"kind").intValue()<5,"record kind");
        for(String k:List.of("entry_event","returned_event","parent_transition_entry","parent_gateway_entry"))event(c,v.get(k));
        for(String k:List.of("natural_parent_metadata","natural_return_metadata"))natural(c,v.get(k));
        for(String k:List.of("session_entry","session_return"))session(c,v.get(k));
        frame(c,v.get("before"));frame(c,v.get("after"));
        if(v.has(GENERIC))generic(c,v.get(GENERIC),v);
        if(v.has(WarPaymentResource4Codec.KEY))WarPaymentResource4Codec.validate(c,v.get(WarPaymentResource4Codec.KEY),v);
    }
    static void journal(Check c,ObjectNode v,Optional<ObjectNode> snapshot,String machine){
        String nested="current_session sampling natural_journal_status records natural_parent_returns qualified_boarding_debits"+(v.has(WarPaymentRaw4Codec.KEY)?" "+WarPaymentRaw4Codec.KEY:"");
        c.fields(v,g(U32,"schema_version steam_build_id install_failure_flags"),g(BOOL,"installed controlled_window_admitted read_complete"),g(Role.U64,"latest_sequence oldest_sequence overwritten publication_failures"),g(TEXT,"machine_id executable_sha256 game_version session_basis balance_boundary maintenance_attribution"),g(NEST,nested));
        need(is(v,"schema_version",1)&&is(v,"steam_build_id",25734779)&&v.get("game_version").textValue().equals(VERSION)&&v.get("executable_sha256").textValue().equalsIgnoreCase(SHA),"journal exact .4 source");
        snapshot.ifPresent(WarPaymentExtrasCodec::build);
        need(v.get("machine_id").textValue().isEmpty()||v.get("machine_id").textValue().equals(machine),"different journal machine");
        need(v.get("balance_boundary").textValue().equals("whole_original_callback_entry_return")&&v.get("maintenance_attribution").textValue().equals("unclosed"),"maintenance attribution promotion");
        JsonNode current=v.get("current_session"),s=v.get("sampling"),ns=v.get("natural_journal_status");session(c,current);
        c.fields(s,g(BOOL,"available capture_enabled busy clear_completed"),g(Role.U64,"epoch active_captures retained_records qualified_records"));
        need(yes(s,"busy")==nz(s.get("active_captures"))&&n(s,"qualified_records").compareTo(n(s,"retained_records"))<=0&&n(s,"retained_records").compareTo(BigInteger.valueOf(512))<=0,"sampling counters");
        need(!yes(s,"clear_completed")||(!yes(s,"capture_enabled")&&!yes(s,"busy")&&is(s,"retained_records",0)),"cleared sampling retains evidence");
        c.fields(ns,g(BOOL,"read_complete"),g(Role.U64,"retained_records overwritten_records failed_appends"));
        ArrayNode records=list(v.get("records"),512);BigInteger previous=BigInteger.ZERO;
        for(JsonNode r:records){record(c,r);BigInteger sequence=n(r,"journal_sequence");need(sequence.compareTo(previous)>0,"retention ordinals");previous=sequence;}
        if(!records.isEmpty())need(n(v,"oldest_sequence").signum()>0&&n(v,"oldest_sequence").compareTo(n(records.get(0),"journal_sequence"))<=0&&previous.compareTo(n(v,"latest_sequence"))<=0,"journal sequence bounds");
        for(JsonNode parent:list(v.get("natural_parent_returns"),64)){
            c.fields(parent,g(BOOL,"original_called original_returned"),g(Role.U64,"raw_return_bits"),g(OU64,"returned_date_raw"),g(OU32,"returned_absolute_day_raw"),g(NEST,"metadata returned_event"));natural(c,parent.get("metadata"));event(c,parent.get("returned_event"));
        }
        for(JsonNode q:list(v.get("qualified_boarding_debits"),512))c.fields(q,g(Role.U64,"writer_sequence transition_sequence gateway_sequence entry_balance_bits returned_balance_bits"),g(U32,"payer_character_id"),g(I32,"account_kind"),g(I64,"requested_amount_raw"),g(OU32,"land_id"),g(BOOL,"returned_balance_matches_requested_sub"));
        String basis=present(current,"loaded_game_epoch")?"source_proved_epoch":yes(v,"controlled_window_admitted")?"same_owned_process_no_load_window":"unqualified";
        need(v.get("session_basis").textValue().equals(basis),"session basis relabeled");
        if(snapshot.isPresent()&&(yes(v,"controlled_window_admitted")||present(current,"loaded_game_epoch")||!v.get("qualified_boarding_debits").isEmpty()))bind(v,snapshot.orElseThrow(),machine);
        need(eq(v.get("qualified_boarding_debits"),expectedDebits(v)),"qualified debit disagrees with raw parent/amount/return evidence");
        if(v.has(WarPaymentRaw4Codec.KEY))WarPaymentRaw4Codec.validate(c,v.get(WarPaymentRaw4Codec.KEY),v);
    }
    static void build(ObjectNode snapshot){
        JsonNode diagnostics=snapshot.get("diagnostics");need(diagnostics!=null&&diagnostics.isObject(),"snapshot build diagnostics");
        JsonNode hello=diagnostics.get("hello");need(hello!=null&&hello.isObject(),"snapshot exact build hello");
        JsonNode version=hello.has("expected_ck3_version")?hello.get("expected_ck3_version"):hello.get("game_version");
        JsonNode hash=hello.has("expected_ck3_sha256")?hello.get("expected_ck3_sha256"):hello.get("executable_sha256");
        need(version!=null&&version.isTextual()&&version.textValue().equals(VERSION)&&hash!=null&&hash.isTextual()&&hash.textValue().equalsIgnoreCase(SHA),"snapshot lacks exact .4 build");
    }
    static void bind(JsonNode journal,JsonNode snapshot,String machine){
        JsonNode current=journal.get("current_session"),actor=obj(snapshot.get("played_character")),diagnostics=obj(snapshot.get("diagnostics"));
        need(n(current,"pid").equals(n(diagnostics,"bridge_pid"))&&n(current,"connection_generation").equals(n(diagnostics,"connection_generation"))
            &&present(current,"player_character_full_id")&&n(current,"player_character_full_id").equals(n(actor,"character_id"))
            &&present(current,"snapshot_revision")&&n(current,"snapshot_revision").equals(n(snapshot,"native_revision"))
            &&present(current,"native_date_raw")&&n(current,"native_date_raw").and(BigInteger.valueOf(0xffffffffL)).equals(n(snapshot,"date_raw").and(BigInteger.valueOf(0xffffffffL)))
            &&journal.get("machine_id").textValue().equals(machine)&&sameSession(current,current),"admitted journal differs from actual process/player/frame");
    }
    static void control(Check c,JsonNode v,JsonNode j,Mode mode){
        c.fields(v,g(TEXT,"requested reason"),g(BOOL,"accepted"));
        need(v.get("requested").textValue().equals(mode.wire())&&!v.get("reason").textValue().isEmpty(),"control belongs to another request");
        JsonNode s=j.get("sampling");
        if(yes(v,"accepted")&&mode==Mode.ENABLE)need(List.of("enabled_controlled_no_load_window","already_enabled").contains(v.get("reason").textValue())&&yes(j,"controlled_window_admitted")&&yes(j,"installed")&&is(j,"install_failure_flags",0)&&yes(s,"available")&&yes(s,"capture_enabled")&&nz(s.get("epoch")),"accepted enable lacks admitted window");
        if(yes(v,"accepted")&&mode==Mode.DISABLE)need(v.get("reason").textValue().equals("disabled")&&!yes(j,"controlled_window_admitted")&&yes(s,"available")&&!yes(s,"capture_enabled")&&!yes(s,"busy")&&yes(s,"clear_completed"),"accepted disable did not clear");
    }
    static boolean naturalMatches(JsonNode r,JsonNode parent,JsonNode current){
        JsonNode p=r.get("natural_parent_metadata"),q=r.get("natural_return_metadata"),s=parent.get("metadata");
        for(JsonNode x:List.of(p,q,s))if(!yes(x,"observed")||!is(x,"phase",2)||!is(x,"actual_entry_rva",0x2a9a570))return false;
        if(!nz(p.get("primary_manager"))||!eq(p,"primary_manager",q,"primary_manager")||!eq(p,"primary_manager",s,"primary_manager")
            ||!nz(p.get("game_state"))||!eq(p,"game_state",q,"game_state")||!eq(p,"game_state",s,"game_state")
            ||!sameEvent(p.get("entry_event"),q.get("entry_event"))||!sameEvent(p.get("entry_event"),s.get("entry_event"))
            ||!before(s.get("entry_event"),r.get("entry_event"))||!before(r.get("returned_event"),parent.get("returned_event"))
            ||!yes(parent,"original_called")||!yes(parent,"original_returned")||!present(p,"date_raw")
            ||!eq(p,"date_raw",q,"date_raw")||!eq(p,"date_raw",s,"date_raw")||!eq(p,"date_raw",parent,"returned_date_raw")
            ||!present(p,"absolute_day_raw")||!eq(p,"absolute_day_raw",q,"absolute_day_raw")||!eq(p,"absolute_day_raw",s,"absolute_day_raw")||!eq(p,"absolute_day_raw",parent,"returned_absolute_day_raw"))return false;
        if(nz(current.get("loaded_game_epoch")))return eq(p,"session_identity",q,"session_identity")&&eq(p,"session_identity",s,"session_identity")&&eq(p,"session_identity",current,"loaded_game_epoch");
        return yes(current,"same_owned_process_no_load_window")&&eq(current,"game_state_identity_witness",p,"game_state")&&!present(p,"session_identity")&&!present(q,"session_identity")&&!present(s,"session_identity");
    }
    static Optional<JsonNode> unique(JsonNode records,long kind,JsonNode event){
        JsonNode found=null;
        for(JsonNode r:records)if(is(r,"kind",kind)&&sameEvent(r.get("entry_event"),event)){if(found!=null)return Optional.empty();found=r;}
        return Optional.ofNullable(found);
    }
    static ArrayNode expectedDebits(JsonNode j){
        ArrayNode result=array();JsonNode current=j.get("current_session"),s=j.get("sampling"),ns=j.get("natural_journal_status");
        if(!(yes(j,"installed")&&is(j,"install_failure_flags",0)&&!j.get("machine_id").textValue().isEmpty()
            &&(present(current,"loaded_game_epoch")||yes(j,"controlled_window_admitted"))&&sameSession(current,current)
            &&yes(j,"read_complete")&&yes(s,"available")&&yes(s,"capture_enabled")&&!yes(s,"busy")&&is(s,"active_captures",0)
            &&is(j,"overwritten",0)&&is(j,"publication_failures",0)&&yes(ns,"read_complete")&&is(ns,"overwritten_records",0)&&is(ns,"failed_appends",0)))return result;
        for(JsonNode w:j.get("records")){
            boolean personal=is(w,"kind",3),land=is(w,"kind",4);JsonNode a=w.get("before"),b=w.get("after");
            if(!((personal||land)&&n(w,"amount_raw").signum()>0&&complete(w,current)&&sameCharacter(a,b)
                &&eq(a,"character_id",current,"player_character_full_id")&&nz(a.get("wrapper"))&&eq(a,"wrapper",b,"wrapper")&&eq(a,"wrapper",w,"receiver")
                &&eq(w,"second_pointer",a,"character")&&present(a,"wrapper_balance_bits")&&present(b,"wrapper_balance_bits")&&is(w,"caller_return_rva",personal?0x28b99b2:0x28b9a6d)))continue;
            if(personal&&(n(a,"character_extension").compareTo(WarPaymentNodes.U64.subtract(BigInteger.valueOf(0xf8)))>0||!n(a,"wrapper").equals(n(a,"character_extension").add(BigInteger.valueOf(0xf8)))))continue;
            if(land&&!(present(a,"land_id")&&!is(a,"land_id",0xffffffffL)&&eq(a,"land_id",b,"land_id")&&is(a,"land_magic",0x4c616e64)&&is(b,"land_magic",0x4c616e64)))continue;
            Optional<JsonNode> gateway=unique(j.get("records"),1,w.get("parent_gateway_entry")),transition=unique(j.get("records"),0,w.get("parent_transition_entry"));
            if(gateway.isEmpty()||transition.isEmpty())continue;
            JsonNode g=gateway.orElseThrow(),t=transition.orElseThrow(),c=t.get("before"),d=t.get("after");
            if(!(complete(g,current)&&complete(t,current)&&is(g,"caller_return_rva",0x24e8f40)&&is(t,"caller_return_rva",0x2a9a8c5)&&sameCharacter(g.get("before"),g.get("after"))
                &&eq(g.get("before"),"character",a,"character")&&eq(g.get("before"),"character_id",a,"character_id")&&eq(g.get("before"),"character_extension",a,"character_extension")
                &&eq(g,"receiver",a,"character")&&is(g,"resource_kind_raw",personal?0:3)&&is(g,"component_raw",3)&&eq(g,"amount_raw",w,"amount_raw")
                &&eq(w,"parent_gateway_character",g,"receiver")&&eq(w,"parent_gateway_caller",g,"caller_return_rva")&&eq(w,"parent_gateway_resource",g,"resource_kind_raw")
                &&eq(w,"parent_gateway_component",g,"component_raw")&&eq(w,"parent_gateway_amount",g,"amount_raw")&&eq(w,"parent_transition_army",g,"parent_transition_army")&&eq(w,"parent_transition_army",t,"receiver")
                &&eq(w,"parent_transition_caller",g,"parent_transition_caller")&&eq(w,"parent_transition_caller",t,"caller_return_rva")&&sameEvent(g.get("parent_transition_entry"),t.get("entry_event"))
                &&before(t.get("entry_event"),g.get("entry_event"))&&before(g.get("entry_event"),w.get("entry_event"))&&before(w.get("returned_event"),g.get("returned_event"))&&before(g.get("returned_event"),t.get("returned_event"))
                &&present(c,"army_id")&&!is(c,"army_id",0xffffffffL)&&eq(c,"army_id",d,"army_id")&&present(c,"army_magic")&&eq(c,"army_magic",d,"army_magic")
                &&present(c,"requested_unit_id")&&eq(c,"requested_unit_id",d,"requested_unit_id")&&present(c,"province_id")&&eq(c,"province_id",d,"province_id")&&is(c,"province_magic",0x50726f76)&&is(d,"province_magic",0x50726f76)&&is(c,"army_1d4",0)))continue;
            boolean natural=false;for(JsonNode parent:j.get("natural_parent_returns"))if(naturalMatches(w,parent,current)&&naturalMatches(g,parent,current)&&naturalMatches(t,parent,current)){natural=true;break;}
            if(!natural||!n(a,"wrapper_balance_bits").subtract(n(w,"amount_raw")).and(WarPaymentNodes.U64).equals(n(b,"wrapper_balance_bits")))continue;
            ObjectNode q=empty();q.set("writer_sequence",w.get("journal_sequence"));q.set("transition_sequence",t.get("journal_sequence"));q.set("gateway_sequence",g.get("journal_sequence"));
            q.put("account_kind",personal?0:3);q.set("payer_character_id",a.get("character_id"));if(land)q.set("land_id",a.get("land_id"));else q.putNull("land_id");
            q.set("requested_amount_raw",w.get("amount_raw"));q.set("entry_balance_bits",a.get("wrapper_balance_bits"));q.set("returned_balance_bits",b.get("wrapper_balance_bits"));q.put("returned_balance_matches_requested_sub",true);result.add(q);
        }
        return result;
    }
}
