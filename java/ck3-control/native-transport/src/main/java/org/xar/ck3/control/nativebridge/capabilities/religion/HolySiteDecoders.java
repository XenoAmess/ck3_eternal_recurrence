package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels.*;

public final class HolySiteDecoders {
    private HolySiteDecoders() { }
    static CreationContext creation(PlanningReadReceipt r) {
        JsonNode v=envelope(r,"player_holy_site_creation_context_v1","player_holy_site_creation_context","player-holy-site-creation-context-v1",Build.CROZIER4);
        CreationContext value=creationBody(v,nativeRevision(r),date(r),player(r));status(r,value.frame().availability());return value;
    }
    /** Shared pure component validator. Actual source, HELLO, paused-frame and command-result custody stay with each original caller. */
    public static CreationContext creationBody(JsonNode v,BigInteger nativeRevision,BigInteger dateRaw,BigInteger actorCharacterId) {
        String keys="schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw played_character_id player_faith_id window_present root_present window_faith_id player_faith_matches models_available models_complete available_holy_site_types potential_barony_title_ids enshrinable_artifact_ids selection_available selected_type_key selected_barony_title_id selected_artifact_ids native_rarity_sum_observed native_rarity_sum_raw raw_scale native_enabled_observed native_create_button_enabled bypass_requirements_observed bypass_requirements_raw normal_requirements_legality_observed normal_requirements_can_create create_tooltip_available create_tooltip cached_resource_quote_available cached_resource_vector_raw cached_quote_freshness_observed native_affordability_observed native_affordable rendered_visibility_observed read_only action_ready create_invoked";
        exact(v,keys+(v.has("preview_identity_sha256")?" preview_identity_sha256":""));
        Frame f=creationFrame(v,nativeRevision,dateRaw,actorCharacterId);
        yes(v,"read_only"); for(String key:List.of("action_ready","create_invoked","cached_quote_freshness_observed","native_affordability_observed","rendered_visibility_observed"))no(v,key);
        nil(v,"native_affordable"); equal(v,"raw_scale",BigInteger.valueOf(100000));
        BigInteger faith=nullableId(v,"player_faith_id"), windowFaith=nullableId(v,"window_faith_id");
        Boolean window=nullableBool(v,"window_present"), root=nullableBool(v,"root_present"), matches=nullableBool(v,"player_faith_matches");
        need(f.availability().available()?(window!=null&&root!=null&&matches!=null):(window==null&&root==null&&matches==null),"creation root availability differs");
        need(!Boolean.TRUE.equals(matches)||(faith!=null&&faith.equals(windowFaith)),"creation belongs to another Faith"); need(!Boolean.TRUE.equals(root)||Boolean.TRUE.equals(window),"creation root lacks window");
        boolean models=bool(v,"models_available"), complete=bool(v,"models_complete"), selection=bool(v,"selection_available");
        need(models==complete&&(!f.availability().available()||models),"partial creation models cannot be complete");
        List<TypeCandidate> types=null; List<BigInteger> baronies=null,artifacts=null,selected=null;
        if(models){
            types=array(v,"available_holy_site_types",8192,n->{
                exact(n,"type_key is_selected native_can_pick_observed native_can_pick tooltip_available tooltip");
                String key=nonempty(n,"type_key"); need(key.length()<=1024,"creation type key too long");
                return new TypeCandidate(key,bool(n,"is_selected"),sample(n,"native_can_pick_observed","native_can_pick",ReligionJson::scalarBoolean),sample(n,"tooltip_available","tooltip",ReligionJson::scalarText));
            }); baronies=ids(v,"potential_barony_title_ids",8192); artifacts=ids(v,"enshrinable_artifact_ids",8192);
        }else for(String key:List.of("available_holy_site_types","potential_barony_title_ids","enshrinable_artifact_ids"))nil(v,key);
        String selectedType=nullableText(v,"selected_type_key"); BigInteger selectedBarony=nullableId(v,"selected_barony_title_id");
        if(selection){selected=ids(v,"selected_artifact_ids",8192);need(selectedType==null||!selectedType.isEmpty()&&selectedType.length()<=1024,"selected type malformed");}
        else{need(selectedType==null&&selectedBarony==null,"unobserved creation selection");nil(v,"selected_artifact_ids");}
        Sample<BigInteger> rarity=sample(v,"native_rarity_sum_observed","native_rarity_sum_raw",n->scalar(n,I64_MIN,I64_MAX));
        Sample<Boolean> enabled=sample(v,"native_enabled_observed","native_create_button_enabled",ReligionJson::scalarBoolean);
        Sample<BigInteger> bypass=sample(v,"bypass_requirements_observed","bypass_requirements_raw",n->scalar(n,BigInteger.ZERO,BigInteger.valueOf(255)));
        Sample<Boolean> normal=sample(v,"normal_requirements_legality_observed","normal_requirements_can_create",ReligionJson::scalarBoolean);
        need(!normal.observed()||(enabled.observed()&&bypass.observed()&&bypass.value().signum()==0&&normal.value().equals(enabled.value())),"normal creation legality lacks bypass-zero observation");
        Sample<String> tooltip=sample(v,"create_tooltip_available","create_tooltip",ReligionJson::scalarText);
        Sample<List<BigInteger>> quote=sample(v,"cached_resource_quote_available","cached_resource_vector_raw",n->{need(n.isArray()&&n.size()==10,"ten raw resource slots required");java.util.ArrayList<BigInteger> raw=new java.util.ArrayList<>();for(JsonNode x:n)raw.add(scalar(x,I64_MIN,I64_MAX));return List.copyOf(raw);});
        if(!f.availability().available())need(!models&&!selection&&!rarity.observed()&&!enabled.observed()&&!bypass.observed()&&!normal.observed()&&!tooltip.observed()&&!quote.observed(),"unavailable creation leaked observations");
        Additive<PreviewIdentity> preview=!v.has("preview_identity_sha256")?new Additive<>(Presence.ABSENT,null):v.get("preview_identity_sha256").isNull()?new Additive<>(Presence.NULL,null):new Additive<>(Presence.VALUE,new PreviewIdentity(text(v,"preview_identity_sha256")));
        need(preview.presence()!=Presence.VALUE||f.availability().available(),"unavailable creation invented preview identity");
        return new CreationContext(f,faith,windowFaith,window,root,matches,models,complete,types,baronies,artifacts,selection,selectedType,selectedBarony,selected,rarity,enabled,bypass,normal,tooltip,quote,preview);
    }
    private static Frame creationFrame(JsonNode v,BigInteger nativeRevision,BigInteger dateRaw,BigInteger actorCharacterId) {
        range(nativeRevision,BigInteger.ONE,U64);range(dateRaw,I32_MIN,I32_MAX);range(actorCharacterId,I32_MIN,I32_MAX);need(!actorCharacterId.equals(BigInteger.valueOf(-1)),"signed snapshot actor sentinel is invalid");
        equal(v,"schema","ck3_12004_player_holy_site_creation_context_v1");Build actual=build(v);need(actual==Build.CROZIER4,"creation component requires the exact .4 version/SHA pair");
        BigInteger signedActor=actorCharacterId;
        equal(v,"played_character_id",signedActor);number(v,"played_character_id",I32_MIN,I32_MAX);equal(v,"date_raw",dateRaw);
        return new Frame(actual,number(v,"capture_epoch",BigInteger.ONE,U64),nativeRevision,dateRaw,signedActor,availability(v,"unavailable_reason"));
    }
    static Cooldown cooldownValue(JsonNode v,Decision d) {
        exact(v,"decision_key present expiry_raw current_counter_raw active counter_unit calendar_conversion_observed"); equal(v,"decision_key",d.key()); equal(v,"counter_unit","native_decision_clock_counter");no(v,"calendar_conversion_observed");
        boolean present=bool(v,"present"), active=bool(v,"active");Integer expiry=nullableI32(v,"expiry_raw");int current=i32(v,"current_counter_raw");
        need(present?expiry!=null&&active==(current<expiry):expiry==null&&!active,"native cooldown signed comparison differs");
        return new Cooldown(d.key(),present,expiry,current,active);
    }
    static CooldownResult cooldown(PlanningReadReceipt r) {
        Decision d=Decision.parse(ReligionCapabilities.argumentText(r.request().arguments(),"action"));
        JsonNode v=envelope(r,"player_holy_site_decision_cooldown_v1","player_holy_site_decision_cooldown","player-holy-site-decision-cooldown-v1",Build.CROZIER4);
        Frame f=frame(v,r,"ck3_12004_holy_site_decision_cooldown_v1",Build.CROZIER4,false);equal(v,"action",d.wire());equal(v,"decision_key",d.key());yes(v,"read_only");
        for(String key:List.of("detail_open_required","action_ready","decision_confirm_invoked","adoption_completed_observed"))no(v,key);
        Sample<Cooldown> c=sample(v,"native_decision_cooldown_observed","native_decision_cooldown",n->cooldownValue(n,d));need(c.observed()==f.availability().available(),"cooldown source availability differs");status(r,f.availability());return new CooldownResult(f,d,c);
    }
    static Additive<Description> description(JsonNode v,String name,boolean context) {
        boolean any=v.has(name)||v.has(name+"_available")||v.has(name+"_unavailable_reason"); if(!any)return new Additive<>(Presence.ABSENT,null);
        boolean available=bool(v,name+"_available");String text=nullableText(v,name),reason=nullableText(v,name+"_unavailable_reason");
        need(available?context&&text!=null&&text.getBytes(StandardCharsets.UTF_8).length<=65536&&reason==null:text==null&&reason!=null&&!reason.isEmpty(),"description context/availability differs");
        return new Additive<>(Presence.VALUE,new Description(available,text,reason));
    }
    static DecisionDetail detail(PlanningReadReceipt r) {
        Decision d=Decision.parse(ReligionCapabilities.argumentText(r.request().arguments(),"action"));BigInteger requested=ReligionCapabilities.argumentInteger(r.request().arguments(),"holy_site_id");
        JsonNode v=envelope(r,"player_holy_site_decision_detail_v1","player_holy_site_decision_detail","player-holy-site-decision-detail-v1",Build.CROZIER4);
        equal(v,"action",d.wire());equal(v,"requested_decision_key",d.key());
        return detailBody(r,v,d,requested,"ck3_12004_holy_site_decision_detail_v1");
    }
    public static DecisionDetail adoption(PlanningReadReceipt r) {
        BigInteger requested=ReligionCapabilities.argumentInteger(r.request().arguments(),"holy_site_id");
        JsonNode value=envelope(r,"player_holy_site_adoption_detail_v1","player_holy_site_adoption_detail","player-holy-site-adoption-detail-v1",Build.CROZIER4);
        return detailBody(r,value,Decision.ADOPT,requested,"ck3_12004_holy_site_adoption_detail_v1");
    }
    private static DecisionDetail detailBody(PlanningReadReceipt r,JsonNode v,Decision d,BigInteger requested,String schema) {
        Frame f=frame(v,r,schema,Build.CROZIER4,false);equal(v,"requested_holy_site_id",requested);yes(v,"read_only");
        for(String key:List.of("rendered_visibility_observed","action_ready","decision_confirm_invoked","adoption_completed_observed"))no(v,key);
        String actual=nullableText(v,"decision_key");need(actual==null||actual.equals(d.key()),"actual decision key differs");
        boolean context=v.has("native_detail_context_verified")&&bool(v,"native_detail_context_verified");need(!context||f.availability().available(),"unavailable detail context");
        Sample<ResourceQuote> quote=sample(v,"native_resource_quote_available","native_resource_quote",n->{
            need(context,"quote lacks native detail context");exact(n,"raw_scale resource_vector_raw costs_raw native_affordable");equal(n,"raw_scale",BigInteger.valueOf(100000));
            List<BigInteger> vector=array(n,"resource_vector_raw",10,x->scalar(x,I64_MIN,I64_MAX));need(vector.size()==10,"ten resource slots required");JsonNode c=field(n,"costs_raw");exact(c,"gold prestige piety treasury");
            for(int index:new int[]{0,1,2,6})equal(c,List.of("gold","prestige","piety","treasury").get(index==6?3:index),vector.get(index));
            return new ResourceQuote(vector,vector.get(0),vector.get(1),vector.get(2),vector.get(6),bool(n,"native_affordable"));
        });
        Additive<Description> req=description(v,"native_requirements_description",context),cost=description(v,"native_cost_description",context);
        Additive<Sample<Cooldown>> cooldown=new Additive<>(Presence.ABSENT,null);
        if(v.has("native_decision_cooldown_observed")||v.has("native_decision_cooldown")){
            Sample<Cooldown> sampled=sample(v,"native_decision_cooldown_observed","native_decision_cooldown",n->{need(context,"cooldown lacks detail context");return cooldownValue(n,d);});cooldown=new Additive<>(Presence.VALUE,sampled);
        }
        Boolean can=nullableBool(v,"native_can_confirm"),normalCan=nullableBool(v,"normal_requirements_can_confirm");
        Integer count=null,index=null;BigInteger token=null;Sample<BigInteger> bypass=new Sample<>(false,null);Description tooltip=null;
        if(f.availability().available()){
            need(d.key().equals(actual),"available detail lacks fixed decision definition");equal(v,"decision_option_id",BigInteger.valueOf(-1));equal(v,"detail_actor_id",player(r));equal(v,"current_actor_id",player(r));yes(v,"parameter_and_selection_match");equal(v,"parameter_holy_site_id",requested);equal(v,"selected_holy_site_id",requested);
            count=number(v,"candidate_count",BigInteger.ONE,BigInteger.valueOf(8192)).intValueExact();index=number(v,"selected_index",BigInteger.ZERO,BigInteger.valueOf(count-1L)).intValueExact();token=number(v,"selected_item_token",BigInteger.ZERO,U32);
            yes(v,"detail_present");bool(v,"root_present");need(can!=null,"available native confirmation must be Boolean");bypass=sample(v,"bypass_requirements_observed","bypass_requirements_raw",n->scalar(n,BigInteger.ZERO,BigInteger.valueOf(255)));
            boolean normal=bypass.observed()&&bypass.value().signum()==0;need(bool(v,"normal_requirements_legality_observed")==normal&&(normal?normalCan!=null&&normalCan.equals(can):normalCan==null),"bypass cannot grant normal legality");
            boolean tooltipAvailable=bool(v,"confirm_tooltip_available");String t=nullableText(v,"confirm_tooltip"),reason=nullableText(v,"confirm_tooltip_unavailable_reason");need(tooltipAvailable?t!=null&&t.getBytes(StandardCharsets.UTF_8).length<=65536&&reason==null:t==null&&reason!=null&&!reason.isEmpty(),"confirm tooltip observation differs");tooltip=new Description(tooltipAvailable,t,reason);
        }else need(can==null&&normalCan==null,"unavailable detail cannot invent false legality");
        status(r,f.availability());return new DecisionDetail(f,d,requested,actual,can,normalCan,context,quote,req,cost,cooldown,count,index,token,bypass,tooltip);
    }
    private static Availability group(JsonNode row,String fields) { exact(row,"available reason "+fields);return availability(row,"reason"); }
    static IndulgenceTerms indulgences(PlanningReadReceipt r) {
        BigInteger recipient=ReligionCapabilities.argumentInteger(r.request().arguments(),"recipient_character_id");JsonNode v=envelope(r,"player_seek_indulgences_terms_v1","player_seek_indulgences_terms","player-seek-indulgences-terms-v1",Build.CROZIER3);
        exact(v,"schema game_version executable_sha256 read_only available unavailable_reason capture_epoch date_raw played_character_id definition_key definition_stable_hash identity options shown can_send");Frame f=frame(v,r,"ck3_12003_player_seek_indulgences_terms_v1",Build.CROZIER3,false);yes(v,"read_only");equal(v,"definition_key","seek_indulgences_interaction");BigInteger hash=nullableNumber(v,"definition_stable_hash",BigInteger.ZERO,U32);need(!f.availability().available()||hash!=null,"available indulgence definition hash absent");
        JsonNode n=field(v,"identity");Availability identityAvailable=group(n,"requested_recipient_character_id effective_actor_id effective_recipient_id secondary_actor_id secondary_recipient_id intermediary_id sixth_role_id");equal(n,"requested_recipient_character_id",recipient);
        List<String> roles=List.of("effective_actor_id","effective_recipient_id","secondary_actor_id","secondary_recipient_id","intermediary_id","sixth_role_id");java.util.ArrayList<Integer> roleValues=new java.util.ArrayList<>();for(String key:roles){Integer x=nullableI32(n,key);need(identityAvailable.available()?x!=null:x==null,"indulgence identity sample differs");roleValues.add(x);}
        IndulgenceIdentity identity=new IndulgenceIdentity(identityAvailable,recipient,roleValues.get(0),roleValues.get(1),roleValues.get(2),roleValues.get(3),roleValues.get(4),roleValues.get(5));
        n=field(v,"options");Availability opts=group(n,"declared_count selected_count all_unselected");BigInteger declared=nullableNumber(n,"declared_count",BigInteger.ZERO,U32),selected=nullableNumber(n,"selected_count",BigInteger.ZERO,U32);Boolean unselected=nullableBool(n,"all_unselected");need(opts.available()?declared!=null&&selected!=null&&unselected!=null&&selected.compareTo(declared)<=0&&unselected==(selected.signum()==0):declared==null&&selected==null&&unselected==null,"indulgence selection sample differs");
        IndulgenceBoolean shown=indulgenceBoolean(field(v,"shown")),canSend=indulgenceBoolean(field(v,"can_send"));need(!f.availability().available()||(identityAvailable.available()&&opts.available()&&shown.availability().available()&&canSend.availability().available()&&Boolean.TRUE.equals(unselected)),"available indulgence terms incomplete");status(r,f.availability());return new IndulgenceTerms(f,hash,identity,new IndulgenceOptions(opts,declared,selected,unselected),shown,canSend);
    }
    private static IndulgenceBoolean indulgenceBoolean(JsonNode n) { Availability a=group(n,"value");Boolean value=nullableBool(n,"value");need(a.available()?value!=null:value==null,"unobserved indulgence Boolean must be null");return new IndulgenceBoolean(a,value); }
}
