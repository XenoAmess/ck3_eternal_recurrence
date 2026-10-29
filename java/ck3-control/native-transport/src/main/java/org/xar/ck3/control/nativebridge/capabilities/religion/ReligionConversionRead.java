package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionService;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;

/** Exact original five conversion READ producers. Native raw tokens and public decimal projections are separate. */
public final class ReligionConversionRead {
    private ReligionConversionRead() { }
    public enum Kind {
        CHOICES("choices"),INPUTS("inputs"),TERMS("terms"),REASONS("reasons"),OUTCOME("outcome");
        private final String leaf;Kind(String leaf){this.leaf=leaf;}
        public String method(){return "ck3_query_player_religion_conversion_"+leaf+"_v1";}
        public String step(){return "query-player-religion-conversion-"+leaf+"-v1";}
        public String key(){return "player_religion_conversion_"+leaf;}
        public String domain(){return key()+"_v1";}
        public String suffix(){return "player-religion-conversion-"+leaf+"-v1";}
        public String permission(){return "allow_private_player_religion_conversion_"+leaf+"_query";}
        public String schema(PlayerReligionContext.Build build){return schemaFor(build,"religion_conversion_"+leaf+"_v1");}
        public BigInteger maximumTarget(){return this==OUTCOME?U32.subtract(BigInteger.ONE):U32;}
    }
    public record BoundFrame(PlayerReligionContext.Build build,BigInteger dateRaw,BigInteger player){
        public BoundFrame {Objects.requireNonNull(build);range(dateRaw,I32_MIN,I32_MAX);NativeCharacterId.of(player);}
    }
    public record Source(boolean available,String reason,BigInteger captureEpoch,BigInteger dateRaw,BigInteger actor){
        public Source {range(captureEpoch,BigInteger.ZERO,U64);range(dateRaw,I32_MIN,I32_MAX);range(actor,I32_MIN,U32);
            need(available?reason==null:reason!=null&&!reason.isEmpty(),"original availability/reason differs");}
    }
    public record Choice(BigInteger faithId,String faithKey,BigInteger mainRiteId,boolean nativeRulePasses) { }
    public record Gates(Source source,BigInteger requestedTarget,BigInteger target,BigInteger actorFaith,BigInteger targetFaith,
            BigInteger actorReligion,BigInteger targetReligion,BigInteger stateRite,BigInteger stateFaith,BigInteger knowledge,
            Boolean recentlyConverted,Boolean recentFlagRegistered,Boolean sameFaith,Boolean sameReligion,Boolean stateRiteMatch,Boolean stateFaithMatch) { }
    public record Prediction(Source source,BigInteger currentRite,BigInteger target,BigInteger currentBase,BigInteger targetBase,BigInteger change) { }
    public record Fervor(Source source,BigInteger requestedTarget,BigInteger actorFaith,BigInteger targetFaith,BigInteger actorRaw,BigInteger targetRaw) { }
    public record Gate(Source source,BigInteger currentRite,BigInteger currentFaith,BigInteger targetFaith,boolean sameFaith,
            boolean differentRite,Boolean withoutPayment,Boolean withPayment) { }
    public record Cost(Source source,BigInteger targetFaith,Boolean sameFaith,Integer points,BigInteger piety,BigInteger actorPiety,Boolean affordable) { }
    public sealed interface View permits Choices,Inputs,Terms,Reasons,Outcome {
        Source source();RawJson nativeData();Kind kind();
    }
    public record Choices(Source source,Source faithSource,BigInteger currentFaith,List<Choice> choices,
            Source ritesSource,BigInteger ritesFaith,List<BigInteger> rites,RawJson nativeData) implements View {
        public Choices {choices=List.copyOf(choices);rites=List.copyOf(rites);Objects.requireNonNull(nativeData);}
        public Kind kind(){return Kind.CHOICES;}
    }
    public record Inputs(Source source,BigInteger target,Gates gates,Prediction prediction,Optional<Fervor> fervor,RawJson nativeData) implements View {
        public Inputs {fervor=Objects.requireNonNull(fervor);Objects.requireNonNull(nativeData);}
        public Kind kind(){return Kind.INPUTS;}
    }
    public record Terms(Source source,BigInteger target,Boolean canConvert,Gate gate,Cost cost,RawJson nativeData) implements View {public Kind kind(){return Kind.TERMS;}}
    public record Reasons(Source source,BigInteger target,BigInteger currentRite,Boolean validator,boolean blockerText,
            String rawText,String uiText,RawJson nativeData) implements View {public Kind kind(){return Kind.REASONS;}}
    public record Outcome(Source source,BigInteger target,Boolean targetReached,Source actorSource,Source stateSource,
            PlayerReligionContext context,BigInteger piety,BigInteger gold,BigInteger prestige,RawJson nativeData) implements View {public Kind kind(){return Kind.OUTCOME;}}
    private static final String COMMON="schema available unavailable_reason capture_epoch date_raw played_character_id";
    private static final String BUILD=" game_version executable_sha256 read_only";
    private static final String FRAME="capture_epoch date_raw played_character_id";
    private static final String FLAGS="faith_conversion_recently_converted conversion_memory_recently_created recent_convert";
    public static String schemaFor(PlayerReligionContext.Build build,String leaf){return "ck3_"+build.version().replace(".","")+"_"+leaf;}
    private static Source source(JsonNode n,String schema,String fields,boolean zeroEpoch){
        exact(n,fields);equal(n,"schema",schema);
        boolean available=bool(n,"available");String reason=nullableText(n,"unavailable_reason");
        return new Source(available,reason,number(n,"capture_epoch",zeroEpoch?BigInteger.ZERO:BigInteger.ONE,U64),
                number(n,"date_raw",I32_MIN,I32_MAX),number(n,"played_character_id",I32_MIN,U32));
    }
    private static void build(JsonNode n,BoundFrame f,boolean readonly){
        need(PlayerReligionContext.Build.exact(text(n,"game_version"),text(n,"executable_sha256"))==f.build(),"conversion source belongs to another exact connected build");
        if(readonly)yes(n,"read_only");
    }
    private static void current(Source n,BoundFrame f){need(n.dateRaw().equals(f.dateRaw())&&n.actor().equals(f.player()),"conversion source crossed current actor/date");}
    private static void joined(Source child,Source parent){need(child.captureEpoch().equals(parent.captureEpoch())&&child.dateRaw().equals(parent.dateRaw())&&child.actor().equals(parent.actor()),"conversion components crossed original owner pump");}
    private static BigInteger full(JsonNode n,String key){return number(n,key,BigInteger.ZERO,U32);}
    private static BigInteger nullableFull(JsonNode n,String key){return nullableNumber(n,key,BigInteger.ZERO,U32);}
    private static BigInteger raw(JsonNode n,String key){return nullableNumber(n,key,I64_MIN,I64_MAX);}
    private static void scale(JsonNode n){equal(n,"raw_scale",BigInteger.valueOf(100000));}
    private static RawJson retain(JsonNode n){return ReligionCapabilities.raw(object(n).deepCopy());}
    public static View normalize(Kind kind,RawJson original,BoundFrame frame,BigInteger target){
        Objects.requireNonNull(kind);Objects.requireNonNull(original);Objects.requireNonNull(frame);
        if(kind!=Kind.CHOICES)range(target,BigInteger.ZERO,kind.maximumTarget());
        ObjectNode n=parse(original);
        return switch(kind){case CHOICES->choices(n,frame);case INPUTS->inputs(n,frame,target);case TERMS->terms(n,frame,target);case REASONS->reasons(n,frame,target);case OUTCOME->outcome(n,frame,target);};
    }
    private static Choices choices(ObjectNode n,BoundFrame f){
        String built=" game_version executable_sha256";
        Source top=source(n,Kind.CHOICES.schema(f.build()),COMMON+built+" read_only faith_choices current_faith_rites membership_is_legality",false);build(n,f,true);no(n,"membership_is_legality");
        JsonNode faith=field(n,"faith_choices"),rites=field(n,"current_faith_rites");
        Source fs=source(faith,schemaFor(f.build(),"faith_conversion_choices_v1"),COMMON+built+" current_faith_id candidate_source rule_only choices",false);build(faith,f,false);
        Source rs=source(rites,schemaFor(f.build(),"current_faith_rites_v1"),COMMON+built+" read_only faith_id rite_ids membership_is_legality",false);build(rites,f,true);
        yes(faith,"rule_only");equal(faith,"candidate_source","native_world_faith_registry");no(rites,"membership_is_legality");
        BigInteger current=nullableFull(faith,"current_faith_id"),riteFaith=full(rites,"faith_id");
        // Original producer permits legitimate duplicate/full-sentinel entries; do not silently deduplicate.
        JsonNode rows=field(faith,"choices");need(rows.isArray(),"original native choice list required");List<Choice> values=new ArrayList<>();
        for(JsonNode row:rows){exact(row,"faith_id faith_key main_rite_id native_faith_rule_passes");values.add(new Choice(full(row,"faith_id"),text(row,"faith_key"),nullableFull(row,"main_rite_id"),bool(row,"native_faith_rule_passes")));}
        JsonNode ids=field(rites,"rite_ids");need(ids.isArray(),"original Rite list required");List<BigInteger> list=new ArrayList<>();for(JsonNode id:ids)list.add(scalar(id,BigInteger.ZERO,U32));
        for(Source s:List.of(top,fs,rs))if(s.available())current(s,f);
        for(Source s:List.of(fs,rs))if(s.available())joined(s,top);
        need(!top.available()||fs.available()&&rs.available(),"available choices lack a real source component");
        return new Choices(top,fs,current,values,rs,riteFaith,list,retain(n));
    }
    private static Inputs inputs(ObjectNode n,BoundFrame f,BigInteger target){
        String optional=n.has("conversion_fervor")?" conversion_fervor":"";
        Source top=source(n,Kind.INPUTS.schema(f.build()),COMMON+" target_rite_id conversion_gates predicted_base_fulfillment"+optional,false);
        JsonNode g=field(n,"conversion_gates"),p=field(n,"predicted_base_fulfillment");
        Source gs=source(g,schemaFor(f.build(),"religion_conversion_gates_v1"),COMMON+" target_rite_id actor_faith_id target_faith_id actor_religion_id target_religion_id realm_state_rite_id realm_state_faith_id recently_converted recent_flag_key_registered same_faith same_religion state_rite_target_match state_faith_target_match requested_target_rite_id knowledge_level_raw raw_scale",false);
        Source ps=source(p,schemaFor(f.build(),"expected_rite_base_fulfillment_v1"),COMMON+BUILD+" current_rite_id target_rite_id raw_scale current_rite_base_raw target_rite_base_raw expected_base_change_raw is_current_fulfillment is_observed_conversion_gain is_final_ai_desire",false);build(p,f,true);
        equal(n,"target_rite_id",target);equal(g,"requested_target_rite_id",target);equal(p,"target_rite_id",target);scale(g);scale(p);
        Gates gates=new Gates(gs,target,nullableFull(g,"target_rite_id"),nullableFull(g,"actor_faith_id"),nullableFull(g,"target_faith_id"),nullableFull(g,"actor_religion_id"),
                nullableFull(g,"target_religion_id"),nullableFull(g,"realm_state_rite_id"),nullableFull(g,"realm_state_faith_id"),raw(g,"knowledge_level_raw"),
                nullableBool(g,"recently_converted"),nullableBool(g,"recent_flag_key_registered"),nullableBool(g,"same_faith"),nullableBool(g,"same_religion"),nullableBool(g,"state_rite_target_match"),nullableBool(g,"state_faith_target_match"));
        no(p,"is_current_fulfillment");no(p,"is_observed_conversion_gain");no(p,"is_final_ai_desire");
        Prediction predicted=new Prediction(ps,full(p,"current_rite_id"),target,raw(p,"current_rite_base_raw"),raw(p,"target_rite_base_raw"),raw(p,"expected_base_change_raw"));
        for(Source s:List.of(gs,ps))if(s.available()){current(top,f);joined(s,top);}
        if(gs.available())need(target.equals(gates.target())&&gates.knowledge()!=null&&gates.recentlyConverted()!=null&&gates.recentFlagRegistered()!=null
                &&gates.sameFaith()!=null&&gates.sameReligion()!=null&&gates.stateRiteMatch()!=null&&gates.stateFaithMatch()!=null,"available gates lost actual inputs");
        if(ps.available())need(predicted.currentBase()!=null&&predicted.targetBase()!=null&&predicted.change()!=null,"available prediction lost raw values");
        need(!top.available()||gs.available()&&ps.available(),"available conversion inputs lack component");
        Optional<Fervor> fervor=optional.isEmpty()?Optional.empty():Optional.of(fervor(field(n,"conversion_fervor"),f,top,gates,predicted,target));
        return new Inputs(top,target,gates,predicted,fervor,retain(n));
    }
    private static Fervor fervor(JsonNode n,BoundFrame f,Source top,Gates gates,Prediction prediction,BigInteger target){
        need(f.build()!=PlayerReligionContext.Build.CROZIER2,"conversion fervor was not implemented by original exact2 provider");
        Source s=source(n,schemaFor(f.build(),"conversion_fervor_inputs_v1"),COMMON+" read_only requested_target_rite_id actor_faith_id target_faith_id actor_fervor_raw target_fervor_raw raw_scale unit is_final_conversion_cost is_final_conversion_desire",false);
        yes(n,"read_only");scale(n);equal(n,"unit","fervor_points");no(n,"is_final_conversion_cost");no(n,"is_final_conversion_desire");
        equal(n,"requested_target_rite_id",target);current(s,f);joined(s,top);if(gates.source().available())joined(gates.source(),s);if(prediction.source().available())joined(prediction.source(),s);
        BigInteger actor=nullableNumber(n,"actor_faith_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE)),targetFaith=nullableNumber(n,"target_faith_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));
        if(actor!=null&&gates.actorFaith()!=null)need(actor.equals(gates.actorFaith()),"fervor actorFaith differs from observed gates");
        if(targetFaith!=null&&gates.targetFaith()!=null)need(targetFaith.equals(gates.targetFaith()),"fervor targetFaith differs from observed gates");
        if(actor!=null&&targetFaith!=null&&gates.sameFaith()!=null)need(gates.sameFaith()==actor.equals(targetFaith),"fervor sameFaith differs from observed gates");
        BigInteger a=raw(n,"actor_fervor_raw"),t=raw(n,"target_fervor_raw");
        need(s.available()?actor!=null&&targetFaith!=null&&a!=null&&t!=null:a==null&&t==null,"fervor availability/raw sample differs");
        return new Fervor(s,target,actor,targetFaith,a,t);
    }
    private static Terms terms(ObjectNode n,BoundFrame f,BigInteger target){
        String common=COMMON+" target_rite_id";
        Source top=source(n,Kind.TERMS.schema(f.build()),common+BUILD+" can_convert native_blocker_text_available final_gate cost",false);build(n,f,true);i32(n,"played_character_id");equal(n,"target_rite_id",target);no(n,"native_blocker_text_available");
        Boolean can=nullableBool(n,"can_convert");JsonNode g=field(n,"final_gate"),c=field(n,"cost");
        Source gs=source(g,schemaFor(f.build(),"religion_conversion_rite_preview_v1"),common+BUILD+" current_rite_id current_faith_id target_faith_id same_faith different_from_current_rite validator_without_payment validator_with_payment",true);build(g,f,true);
        i32(g,"played_character_id");equal(g,"target_rite_id",target);need(gs.captureEpoch().equals(top.captureEpoch()),"final gate changed original capture epoch");
        Gate gate=new Gate(gs,full(g,"current_rite_id"),full(g,"current_faith_id"),full(g,"target_faith_id"),bool(g,"same_faith"),bool(g,"different_from_current_rite"),nullableBool(g,"validator_without_payment"),nullableBool(g,"validator_with_payment"));
        Source cs=source(c,schemaFor(f.build(),"religion_conversion_cost_v1"),common+" target_faith_id same_faith charge_piety piety_points piety_cost_raw actor_piety_raw can_afford_piety raw_scale final_conversion_legality_observed",true);
        i32(c,"played_character_id");full(c,"target_rite_id");yes(c,"charge_piety");scale(c);no(c,"final_conversion_legality_observed");
        Cost cost=new Cost(cs,nullableFull(c,"target_faith_id"),nullableBool(c,"same_faith"),nullableI32(c,"piety_points"),raw(c,"piety_cost_raw"),raw(c,"actor_piety_raw"),nullableBool(c,"can_afford_piety"));
        if(gs.available()||top.available()){current(top,f);need(gs.dateRaw().equals(top.dateRaw())&&gs.actor().equals(top.actor()),"final gate differs from queried actor/date");}
        if(gs.available())need(gate.withoutPayment()!=null&&gate.withPayment()!=null,"available final gate lacks actual validators");
        if(cs.available()){joined(cs,top);equal(c,"target_rite_id",target);need(cost.targetFaith()!=null&&cost.sameFaith()!=null&&cost.points()!=null&&cost.piety()!=null&&cost.actorPiety()!=null&&cost.affordable()!=null,"available native quote lacks fields");}
        need(top.available()?gs.available()&&cs.available()&&can!=null:can==null,"native terms lost original availability");
        return new Terms(top,target,can,gate,cost,retain(n));
    }
    private static Reasons reasons(ObjectNode n,BoundFrame f,BigInteger target){
        Source s=source(n,Kind.REASONS.schema(f.build()),COMMON+BUILD+" current_rite_id target_rite_id native_paid_validator_passes native_blocker_text_available raw_native_text ui_blocker_text reason_codes_available",false);
        build(n,f,true);i32(n,"played_character_id");equal(n,"target_rite_id",target);BigInteger current=full(n,"current_rite_id");no(n,"reason_codes_available");
        Boolean validator=nullableBool(n,"native_paid_validator_passes");boolean textAvailable=bool(n,"native_blocker_text_available");String raw=nullableText(n,"raw_native_text"),ui=nullableText(n,"ui_blocker_text");
        if(s.available()){current(s,f);need(validator!=null&&textAvailable&&raw!=null&&ui!=null,"available native reasons lack actual verdict/text");}
        else need(validator==null&&!textAvailable&&raw==null&&ui==null,"unavailable reasons invented verdict/text");
        return new Reasons(s,target,current,validator,textAvailable,raw,ui,retain(n));
    }
    private static Outcome outcome(ObjectNode n,BoundFrame f,BigInteger target){
        Source top=source(n,Kind.OUTCOME.schema(f.build()),COMMON+BUILD+" target_rite_id target_reached target_reached_is_identity_only conversion_causality_inferred actor state",false);build(n,f,true);
        JsonNode a=field(n,"actor"),s=field(n,"state");
        Source as=source(a,schemaFor(f.build(),"conversion_outcome_actor_v1"),COMMON+BUILD+" piety_raw gold_raw prestige_raw current_religion raw_scale conversion_causality_inferred",false);build(a,f,true);
        Source ss=source(s,schemaFor(f.build(),"religion_conversion_outcome_state_v1"),COMMON+" knowledge_level_raw spiritual_fulfillment_raw baseline_spiritual_fulfillment_raw "+FLAGS+" requested_target_rite_id target_rite_id raw_scale flag_expiry_unit is_conversion_gain",false);
        PlayerReligionContext context=PlayerReligionContext.decode(field(a,"current_religion"));need(context.exactBuild()==f.build(),"outcome current religion build drift");
        equal(n,"target_rite_id",target);equal(s,"requested_target_rite_id",target);BigInteger st=nullableFull(s,"target_rite_id");need(st==null||st.equals(target),"outcome state target drift");
        Boolean reached=nullableBool(n,"target_reached");yes(n,"target_reached_is_identity_only");no(n,"conversion_causality_inferred");no(a,"conversion_causality_inferred");equal(s,"flag_expiry_unit","native_flag_updates");no(s,"is_conversion_gain");scale(a);scale(s);
        BigInteger piety=raw(a,"piety_raw"),gold=raw(a,"gold_raw"),prestige=raw(a,"prestige_raw");
        boolean complete=raw(s,"knowledge_level_raw")!=null;complete&=raw(s,"spiritual_fulfillment_raw")!=null;complete&=raw(s,"baseline_spiritual_fulfillment_raw")!=null;
        for(String key:FLAGS.split(" ")){JsonNode flag=field(s,key);exact(flag,"key_registered present timed expiry_counter_raw current_counter_raw remaining_updates");
            Boolean registered=nullableBool(flag,"key_registered"),present=nullableBool(flag,"present");nullableBool(flag,"timed");nullableI32(flag,"expiry_counter_raw");nullableI32(flag,"current_counter_raw");raw(flag,"remaining_updates");complete&=registered!=null&&present!=null;}
        Source contextSource=new Source(context.available(),context.unavailableReason(),context.captureEpoch(),BigInteger.valueOf(context.dateRaw()),context.playedCharacterId());
        for(Source child:List.of(as,ss,contextSource))if(child.available()){current(top,f);joined(child,top);}
        need(!as.available()||context.available()&&piety!=null&&gold!=null&&prestige!=null,"available outcome actor lacks actual facts");
        need(!ss.available()||target.equals(st)&&complete,"available outcome state incomplete");
        need(!top.available()||as.available()&&ss.available(),"available outcome lacks actual components");
        return new Outcome(top,target,reached,as,ss,context,piety,gold,prestige,retain(n));
    }
    public static View decode(Kind kind,PlanningReadReceipt receipt){
        ObjectNode e=ReligionService.originalResult(receipt);var build=ReligionService.boundBuild(receipt);BoundFrame f=new BoundFrame(build,date(receipt),player(receipt));
        equal(e,"step",kind.step());yes(e,"accepted");yes(e,"private_build");yes(e,"read_only");no(e,"advertised");
        need(PlayerReligionContext.Build.exact(text(e,"game_version"),text(e,"executable_sha256"))==build,"conversion envelope changed actual connected build");
        equal(e,"backend_id","ck3-"+build.version()+"-native-"+kind.suffix());equal(e,"domain_key",kind.domain());equal(e,"snapshot_revision",nativeRevision(receipt));equal(e,"date_raw",f.dateRaw());
        BigInteger target=kind==Kind.CHOICES?null:full(ReligionCapabilities.argumentNode(receipt.request().arguments()),"target_rite_id");
        View value=normalize(kind,retain(field(e,kind.key())),f,target);equal(e,"status",value.source().available()?"observed":"unavailable");return value;
    }
    /** Exact native originals remain unchanged. This public boundary projects only declared64-bit roles. */
    public static ObjectNode publicData(View view){
        ObjectNode n=parse(view.nativeData()).deepCopy();u64(n,"capture_epoch",view.source().captureEpoch());
        switch(view){
            case Choices v -> {u64(object(n.get("faith_choices")),"capture_epoch",v.faithSource().captureEpoch());u64(object(n.get("current_faith_rites")),"capture_epoch",v.ritesSource().captureEpoch());}
            case Inputs v -> {
                ObjectNode g=object(n.get("conversion_gates")),p=object(n.get("predicted_base_fulfillment"));
                u64(g,"capture_epoch",v.gates().source().captureEpoch());signed(g,"knowledge_level_raw");
                u64(p,"capture_epoch",v.prediction().source().captureEpoch());for(String key:List.of("current_rite_base_raw","target_rite_base_raw","expected_base_change_raw"))signed(p,key);
                v.fervor().ifPresent(raw->{ObjectNode a=object(n.get("conversion_fervor"));u64(a,"capture_epoch",raw.source().captureEpoch());signed(a,"actor_fervor_raw");signed(a,"target_fervor_raw");});
                n.put("read_only",true);
            }
            case Terms v -> {u64(object(n.get("final_gate")),"capture_epoch",v.gate().source().captureEpoch());ObjectNode c=object(n.get("cost"));u64(c,"capture_epoch",v.cost().source().captureEpoch());signed(c,"piety_cost_raw");signed(c,"actor_piety_raw");}
            case Reasons ignored -> { }
            case Outcome v -> {
                ObjectNode a=object(n.get("actor")),s=object(n.get("state")),context=object(a.get("current_religion"));
                u64(a,"capture_epoch",v.actorSource().captureEpoch());u64(s,"capture_epoch",v.stateSource().captureEpoch());u64(context,"capture_epoch",v.context().captureEpoch());
                for(String key:List.of("piety_raw","gold_raw","prestige_raw"))signed(a,key);
                for(String key:List.of("faith_fervor_raw","spiritual_fulfillment_raw"))signed(context,key);
                for(String key:List.of("knowledge_level_raw","spiritual_fulfillment_raw","baseline_spiritual_fulfillment_raw"))signed(s,key);
                for(String key:FLAGS.split(" "))signed(object(s.get(key)),"remaining_updates");
            }
        }
        return n;
    }
    public static ObjectNode present(View view,PlayerReligionContext.Build build,String snapshotId,BigInteger publicRevision,BigInteger nativeRevision,ObjectNode envelope){
        ObjectNode n=publicData(view);
        n.put("exact_ck3_build",build.version());n.put("exe_sha256",build.sha256());n.put("queried_snapshot_id",snapshotId);
        u64(n,"queried_revision",publicRevision);u64(n,"queried_native_revision",nativeRevision);u64(n,"snapshot_revision",nativeRevision);
        n.put("query_date_raw",envelope.get("date_raw").bigIntegerValue());n.set("backend_id",envelope.get("backend_id"));n.set("domain_key",envelope.get("domain_key"));n.set("status",envelope.get("status"));n.put("advertised",false);return n;
    }
    private static void u64(ObjectNode n,String key,BigInteger value){n.put(key,PublicUnsigned64.canonical(value,PublicUnsigned64.Minimum.ZERO));}
    private static void signed(ObjectNode n,String key){JsonNode v=field(n,key);if(!v.isNull())n.put(key,number(n,key,I64_MIN,I64_MAX).toString());}
    public record ReadSource(Kind kind,ExactRef source){public ReadSource{Objects.requireNonNull(kind);Objects.requireNonNull(source);}}
    public static List<ReadContract<View>> contracts(List<ReadSource> sources,ReligionService.ReadAdmission admission){
        sources=List.copyOf(sources);Objects.requireNonNull(admission);
        need(sources.size()==5&&sources.stream().map(ReadSource::kind).distinct().count()==5,"exact five original conversion source contracts required");
        List<ReadContract<View>> result=new ArrayList<>();
        for(ReadSource source:sources){Kind kind=source.kind();result.add(new ReadContract<>("religion/conversion/"+kind.name().toLowerCase(java.util.Locale.ROOT),new OperationKey(kind.step()),
                Optional.empty(),kind.permission(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source.source(),
                (request,requestId)->{admission.verify(request);ObjectNode args=ReligionCapabilities.argumentNode(request.arguments());
                    exact(args,kind==Kind.CHOICES?"":"target_rite_id");if(kind!=Kind.CHOICES)number(args,"target_rite_id",BigInteger.ZERO,kind.maximumTarget());
                    return new NativeRequest(kind.step(),Optional.empty(),ReligionCapabilities.raw(args));},
                receipt->decode(kind,receipt),receipt->decode(kind,receipt)));
        }return List.copyOf(result);
    }
}
