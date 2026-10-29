package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Parsers for the original native result tokens, before construction of immutable domain DTOs. */
public final class InteractionReads {
    private InteractionReads() { }
    public static MarriageChoices marriageChoices(PlanningReadReceipt receipt,Context c) {
        need(receipt.original().nativeOk(),"successful original marriage query required");
        return FamilyMarriageChoicesProjection.decodeNative(receipt.original().originalResultToken().orElseThrow(),c).typed();
    }
    public static TitleOwnLaws titleOwnLaws(PlanningReadReceipt receipt,Context c,FullId title) {
        JsonNode n=result(receipt); eq(n,"step","query-title-own-laws-v1-"+title.value()); yes(n,"accepted"); yes(n,"read_only"); eq(n,"backend_id","native-headless");
        Frame f=frame(n,c); JsonNode v=field(n,"title_own_laws");
        closed(v,"schema","schema_version","game_version","executable_sha256","status","available","unavailable_reason","snapshot_revision","date_raw","actor_character_id","title_id","native_law_count","laws","single_heir_member");
        eq(v,"schema","xar.ck3.title-own-laws.v1"); eq(v,"schema_version",BigInteger.ONE); need(c.build()==Build.CROZIER4,"own-laws source only qualifies actual4"); build(v,"game_version","executable_sha256",c);
        bound(v,c); eq(v,"title_id",BigInteger.valueOf(title.value())); Availability a=availability(v); eq(n,"status",a.available()?"available":"unavailable");
        if(!a.available()) { nil(v,"native_law_count","laws","single_heir_member"); return new TitleOwnLaws(f,title,a,null,null,null); }
        int count=integer(v,"native_law_count",0,256);
        List<OwnLaw> laws=list(v,"laws",256,row->{
            closed(row,"native_definition_id","key"); long id=number(row,"native_definition_id",BigInteger.ZERO,U32).longValueExact(); String key=text(row,"key");
            need(key.length()>0 && key.length()<256 && key.chars().allMatch(ch->ch>=0x21 && ch<=0x7e),"native law key bound differs");
            return new OwnLaw(id,key);
        });
        need(laws.size()==count,"complete native law count required"); boolean member=bool(v,"single_heir_member");
        need(member==laws.stream().anyMatch(l->l.key().equals("single_heir_succession_law")),"single-heir summary differs from actual ordered laws");
        return new TitleOwnLaws(f,title,a,count,laws,member);
    }
    public static PlayerClaims playerClaims(PlanningReadReceipt receipt,Context c,List<Int32Id> titles) {
        JsonNode n=result(receipt); String step="query-player-claims-v1-"+titles.stream().map(t->Integer.toString(t.value())).collect(java.util.stream.Collectors.joining(","));
        eq(n,"step",step); yes(n,"accepted"); yes(n,"read_only"); Frame f=frame(n,c); JsonNode v=field(n,"player_claims");
        eq(v,"schema","xar.ck3.player-claims.v1"); eq(v,"schema_version",BigInteger.ONE); need(c.build()==Build.CROZIER4,"claims only qualify actual4"); build(v,"game_version","executable_sha256",c); bound(v,c);
        List<Long> actual=ids(v,"title_ids",4096); need(actual.equals(titles.stream().map(t->(long)t.value()).toList()),"ordered requested TitleIDs changed");
        Availability a=availability(v); eq(n,"status",a.available()?"available":"unavailable");
        if(!a.available()) { nil(v,"claims"); return new PlayerClaims(f,titles,a,null); }
        List<ClaimRow> rows=list(v,"claims",4096,row->{
            closed(row,"title_id","present","state","strong","implicit"); Int32Id title=new Int32Id(integer(row,"title_id",0,Integer.MAX_VALUE));
            boolean present=bool(row,"present"); Boolean strong=nullableBool(row,"strong"), implicit=nullableBool(row,"implicit");
            String state=text(row,"state");
            if(!present) { need(state.equals("absent") && strong==null && implicit==null,"absent claims must preserve unknown flags"); return new ClaimRow(title,ClaimState.ABSENT,null,null); }
            need(strong!=null && implicit!=null,"present claim needs native flags");
            String expected=(strong?"strong":"weak")+(implicit?"_implicit":"_explicit"); need(state.equals(expected),"claim state differs from raw flags");
            return new ClaimRow(title,ClaimState.valueOf(state.toUpperCase(java.util.Locale.ROOT)),strong,implicit);
        });
        need(rows.size()==titles.size() && rows.stream().map(ClaimRow::title).toList().equals(titles),"claim rows no longer correspond one-to-one");
        return new PlayerClaims(f,titles,a,rows);
    }
    public static TitleHolder titleHolder(PlanningReadReceipt receipt,Context c,Int32Id title) {
        JsonNode n=result(receipt); eq(n,"step","query-title-holder-v1-"+title.value()); yes(n,"accepted"); positive64(n,"query_sequence");
        JsonNode v=field(n,"title_holder"); eq(v,"schema","xar.ck3.title-holder.v1"); eq(v,"schema_version",BigInteger.ONE); bound(v,c); build(v,"game_version","executable_sha256",c); eq(v,"title_id",BigInteger.valueOf(title.value()));
        Availability a=availability(v); eq(n,"status",a.available()?"available":"unavailable"); Frame f=new Frame(c.revision(),c.date(),c.actor(),c.build(),positive64(n,"query_sequence"));
        Optional<String> key=Optional.empty(), keyReason=Optional.empty();
        Tier tier=null; Integer holder=null, immediate=null, top=null; Boolean isPlayer=null,inRealm=null;
        if(a.available()) {
            int rawTier=integer(v,"title_tier_raw",1,6); tier=Tier.values()[rawTier-1]; eq(v,"title_tier_key",tier.name().toLowerCase(java.util.Locale.ROOT));
            holder=nullableInt32(v,"holder_character_id"); immediate=nullableInt32(v,"holder_immediate_liege_character_id"); top=nullableInt32(v,"holder_top_liege_character_id"); isPlayer=bool(v,"holder_is_player"); inRealm=bool(v,"holder_in_player_realm");
            if(holder==null) need(!isPlayer && !inRealm && immediate==null && top==null,"unheld title invented holder relationship");
            else need(top!=null && isPlayer==(c.actor().equals(BigInteger.valueOf(holder))) && (!isPlayer || inRealm),"holder player/realm identity disagrees");
        } else nil(v,"title_tier_raw","title_tier_key","holder_character_id","holder_immediate_liege_character_id","holder_top_liege_character_id","holder_is_player","holder_in_player_realm");
        if(c.build()==Build.CROZIER4 || v.has("title_key_available") || v.has("title_key_status") || v.has("title_key") || v.has("title_key_unavailable_reason")) {
            boolean available=bool(v,"title_key_available"); eq(v,"title_key_status",available?"available":"unavailable");
            if(available) {
                need(a.available(),"unavailable title invented key"); nil(v,"title_key_unavailable_reason"); String s=text(v,"title_key");
                String[] prefixes={"b_","c_","d_","k_","e_","h_"};
                need(s.length()>=3 && s.length()<=1024 && s.matches("[bcdkeh]_[a-z0-9][a-z0-9_]*") && s.startsWith(prefixes[tier.ordinal()]),"canonical tier/key mismatch"); key=Optional.of(s);
            } else { nil(v,"title_key"); keyReason=Optional.of(reason(v,"title_key_unavailable_reason")); }
        }
        return new TitleHolder(f,title,a,tier,holder,isPlayer,inRealm,immediate,top,key,keyReason);
    }
    static void bound(JsonNode v,Context c) { eq(v,"snapshot_revision",c.revision()); eq(v,"date_raw",c.date()); eq(v,"actor_character_id",c.actor()); }
    public static Appointment appointment(PlanningReadReceipt receipt,Context c,AppointmentRequest request) {
        JsonNode n=result(receipt); need(c.build()==Build.CROZIER4,"appointment requires exact actual4"); build(n,"game_version","executable_sha256",c);
        eq(n,"schema","ck3-ingame-ui-window-v1"); eq(n,"status","observed"); eq(n,"window_kind","title_appointment"); eq(n,"window_name","title_appointment");
        for(String k:List.of("available","accepted","window_exists","effective_visible","enabled","paused","application_owner_thread_verified","gui_owner_binding_verified")) yes(n,k);
        no(n,"dispatch_invoked"); no(n,"verification_pending"); eq(n,"native_revision",c.revision()); eq(n,"date_raw",c.date()); eq(n,"played_character_id",c.actor()); positive64(n,"pump_epoch"); number(n,"thread_id",BigInteger.ONE,U32);
        JsonNode v=field(n,"title_appointment"); eq(v,"schema","ck3-current-title-appointment-v1"); yes(v,"available");
        eq(v,"requested_title_id",BigInteger.valueOf(request.title().map(CharacterId::value).orElse(0L))); eq(v,"candidate_offset",BigInteger.valueOf(request.offset())); eq(v,"breakdown_character_id",BigInteger.valueOf(request.breakdown().map(CharacterId::value).orElse(0L)));
        CharacterId current=new CharacterId(id(v,"current_window_title_id")),holder=new CharacterId(id(v,"current_holder_character_id"));
        yes(n,"subject_id_available"); yes(n,"owner_character_id_available"); eq(n,"current_subject_id",BigInteger.valueOf(current.value())); eq(n,"owner_character_id",BigInteger.valueOf(holder.value()));
        String key=text(v,"current_title_key"),law=text(v,"effective_succession_law_key"); need(key.matches("[A-Za-z0-9_]{1,160}") && law.matches("[A-Za-z0-9_]{1,160}"),"native appointment keys malformed");
        if(request.title().isPresent()) {
            long resolved=id(v,"resolved_title_id"); eq(v,"group_first_title_id",BigInteger.valueOf(resolved)); String branch=text(v,"native_group_branch"); need(branch.equals("character_1c0") || branch.equals("character_1d0"),"normalization source branch absent");
            need(bool(v,"requested_resolves_to_current")==(resolved==current.value()),"normalized title equality differs");
            if(resolved==current.value()) { eq(v,"resolved_title_key",key); eq(v,"requested_holder_character_id",BigInteger.valueOf(holder.value())); }
        } else { no(v,"requested_resolves_to_current"); eq(v,"resolved_title_id",BigInteger.ZERO); }
        int count=integer(v,"full_candidate_count",0,4096); eq(v,"source_pool_count",BigInteger.valueOf(count)); yes(v,"ai_control_available"); eq(v,"score_fixed_point_scale",BigInteger.valueOf(100000)); eq(v,"candidate_scope","complete_native_base_list_joined_to_source_pool_and_score_cache");
        int end=Math.min(count,request.offset()+request.limit()); need(request.offset()<=count,"appointment offset exceeds native count"); eq(v,"next_offset",BigInteger.valueOf(end));
        String token=text(v,"pool_consistency_token"); need(token.matches("fnv1a64:[0-9a-f]{16}"),"native pool consistency token differs");
        List<AppointmentCandidate> rows=list(v,"candidates",64,row->{
            CharacterId cid=new CharacterId(id(row,"character_id")); int index=integer(row,"list_index",0,Math.max(0,count-1)), rank=integer(row,"native_rank",-1,count);
            BigInteger score=number(row,"score_raw",I64_MIN,I64_MAX); boolean alive=bool(row,"alive"),human=bool(row,"is_human_player"),ai=bool(row,"is_ai"),present=bool(row,"score_present"); yes(row,"candidate_pool_member");
            need(ai==(!alive || !human) && present==(rank>0),"candidate AI/score provenance differs"); return new AppointmentCandidate(cid,index,rank,score,alive,human,ai,present);
        });
        need(rows.size()==end-request.offset(),"incomplete appointment page"); unique(rows.stream().map(AppointmentCandidate::character).toList(),64); unique(rows.stream().map(AppointmentCandidate::listIndex).toList(),64);
        boolean breakdown=bool(v,"breakdown_available"); boolean invoked=bool(v,"breakdown_getter_invoked"); yes(v,"breakdown_cache_refresh_only"); ScoreNode tree=null;
        if(breakdown) { need(invoked && request.breakdown().isPresent(),"unrequested breakdown"); tree=scoreTree(field(v,"breakdown"),0,new int[]{0,0});
            for(AppointmentCandidate candidate:rows) if(candidate.character().equals(request.breakdown().orElseThrow())) need(candidate.scorePresent() && candidate.scoreRaw().equals(tree.value()),"native breakdown total differs from cached score"); }
        else nil(v,"breakdown");
        Optional<NativeLevel> nativeLevel=Optional.empty();
        if(request.diagnostic().isPresent()) nativeLevel=Optional.of(nativeLevel(field(v,"character_level_diagnostic"),request.diagnostic().orElseThrow(),current));
        else if(v.has("character_level_diagnostic")) nil(v,"character_level_diagnostic");
        return new Appointment(current,holder,key,law,count,end,token,rows,breakdown,tree,nativeLevel);
    }
    private static ScoreNode scoreTree(JsonNode n,int depth,int[] budget) {
        need(depth<=8 && ++budget[0]<=128,"native score tree bound exceeded");
        String a=text(n,"text0"),b=text(n,"text1"),c=text(n,"text2");
        for(String s:List.of(a,b,c)) { int bytes=s.getBytes(java.nio.charset.StandardCharsets.UTF_8).length; need(bytes<=512 && s.indexOf(0)<0,"native score string bound exceeded"); budget[1]+=bytes; }
        need(budget[1]<=12000,"native score total text bound exceeded");
        BigInteger value=number(n,"value_raw",I64_MIN,I64_MAX),factor=number(n,"factor_raw",I64_MIN,I64_MAX);
        int mode=integer(n,"mode",Integer.MIN_VALUE,Integer.MAX_VALUE),flags=integer(n,"flags",0,255);
        List<ScoreNode> children=list(n,"children",128,row->scoreTree(row,depth+1,budget));
        return new ScoreNode(a,b,c,value,factor,mode,flags,children);
    }
    private static NativeLevel nativeLevel(JsonNode n,CharacterId requested,CharacterId title) {
        eq(n,"schema","ck3-appointment-character-native-level-v1"); eq(n,"character_id",BigInteger.valueOf(requested.value())); eq(n,"title_id",BigInteger.valueOf(title.value()));
        boolean available=bool(n,"available"); String reason=available?nullableText(n,"unavailable_reason"):reason(n,"unavailable_reason");
        Integer ordinal=field(n,"native_level_source_ordinal").isNull()?null:integer(n,"native_level_source_ordinal",0,255);
        boolean hasTier=n.has("current_rule_allowed_candidate_tier_ordinal") || n.has("candidate_tier"); Optional<Integer> allowed=Optional.empty(),candidate=Optional.empty();
        if(hasTier) { if(available) { allowed=Optional.of(integer(n,"current_rule_allowed_candidate_tier_ordinal",0,255)); candidate=Optional.of(integer(n,"candidate_tier",0,6)); } else nil(n,"current_rule_allowed_candidate_tier_ordinal","candidate_tier"); }
        if(!available) { nil(n,"resource_extension_present","accumulated_raw","level_cap_raw","native_level","title_tier","required_native_level","meets_native_level_floor"); return new NativeLevel(new Availability(false,reason),requested.value(),title.value(),ordinal,null,null,null,null,null,null,null,allowed,candidate); }
        need(ordinal!=null && ordinal==0 && reason==null,"unsupported native level source"); boolean extension=bool(n,"resource_extension_present");
        BigInteger accumulated=extension?number(n,"accumulated_raw",I64_MIN,I64_MAX):nullableNumber(n,"accumulated_raw",I64_MIN,I64_MAX); Integer cap=field(n,"level_cap_raw").isNull()?null:integer(n,"level_cap_raw",Integer.MIN_VALUE,Integer.MAX_VALUE);
        if(!extension) need(accumulated==null && cap==null,"null extension invented resource data"); else need(cap!=null,"resource extension lacks cap");
        int level=integer(n,"native_level",0,256),tier=integer(n,"title_tier",0,6),floor=integer(n,"required_native_level",Integer.MIN_VALUE,Integer.MAX_VALUE); boolean meets=bool(n,"meets_native_level_floor"); need(meets==(level>=floor) && (extension || level==0),"native level floor/null-extension mismatch");
        return new NativeLevel(new Availability(true,null),requested.value(),title.value(),ordinal,extension,accumulated,cap,level,tier,floor,meets,allowed,candidate);
    }
}
