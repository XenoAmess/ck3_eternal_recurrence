package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original readonly doctrine/draft queries. Collection readiness never grants creation permission. */
public final class ReligionDoctrineDraftReads {
    private ReligionDoctrineDraftReads() { }
    public enum Group { DATA, DRAFT }
    public enum Kind {
        DOCTRINES(Group.DATA,"doctrines"), DOCTRINE_CATALOGUE(Group.DATA,"doctrine_catalogue"),
        DOCTRINE_KNOWLEDGE(Group.DATA,"doctrine_knowledge"), TENETS(Group.DATA,"tenets"),
        HOSTILITY(Group.DATA,"hostility"), NUMERIC_SPECIAL_PARAMETERS(Group.DATA,"numeric_special_parameters"),
        PERSONAL_PARAMETERS(Group.DATA,"personal_parameters"), REFORM_CONTEXT(Group.DRAFT,"reform_context"),
        AI_REFORM_INPUTS(Group.DRAFT,"ai_reform_inputs"), DRAFT_GROUPS(Group.DRAFT,"draft_groups"),
        DRAFT_DOCTRINE_CHOICES(Group.DRAFT,"draft_doctrine_choices"),
        DRAFT_TENET_CHOICES(Group.DRAFT,"draft_tenet_choices"),
        DRAFT_RESOURCE_COSTS(Group.DRAFT,"draft_resource_costs");
        private final Group group; private final String leaf;
        Kind(Group group,String leaf){this.group=group;this.leaf=leaf;}
        public Group group(){return group;}
        public String method(){return "ck3_query_player_religion_"+leaf+"_v1";}
        public String suffix(){return "player-religion-"+leaf.replace('_','-')+"-v1";}
        public String step(){return "query-"+suffix();}
        public String nested(){return "player_religion_"+leaf;}
        public String domain(){return nested()+"_v1";}
        public String permission(){return "allow_private_player_religion_"+leaf+"_query";}
        public String original(){return nested()+"_private_transport.py";}
        public List<Field> selectorFields(){return switch(this){
            case DOCTRINE_KNOWLEDGE->List.of(Field.DOCTRINE_KEY);
            case TENETS->List.of(Field.TARGET_RITE_ID,Field.TENET_KEY,Field.INCLUDE_KNOWLEDGE_CATALOGUE);
            case HOSTILITY->List.of(Field.TARGET_RITE_ID);
            default->List.of();};}
        public static Kind method(String method){return Arrays.stream(values()).filter(k->k.method().equals(method)).findFirst().orElseThrow(()->new IllegalArgumentException("unlisted original doctrine/draft method"));}
    }
    /** Every optional selector retains missing/null/value before its original native request projection. */
    public record Selection(Kind kind,List<Argument> selectors) {
        public Selection {
            Objects.requireNonNull(kind);selectors=List.copyOf(selectors);
            need(selectors.stream().map(Argument::field).toList().equals(kind.selectorFields()),"original doctrine/draft selector shape differs");
            for(var a:selectors){var v=a.value();if(v instanceof Absent absent){need(absent.presence()!=Presence.VALUE&&(a.field()!=Field.INCLUDE_KNOWLEDGE_CATALOGUE||absent.presence()==Presence.MISSING),"invalid original selector absence");continue;}
                switch(a.field()){
                    case TARGET_RITE_ID->{need(v instanceof IntegerValue,"target Rite must be integral");range(((IntegerValue)v).value(),BigInteger.ZERO,U32);}
                    case DOCTRINE_KEY,TENET_KEY->{need(v instanceof TextValue,"named definition key must be text");var key=((TextValue)v).value();need(!key.isEmpty()&&(a.field()!=Field.TENET_KEY||key.getBytes(StandardCharsets.UTF_8).length<=128),"named definition key outside original field domain");}
                    case INCLUDE_KNOWLEDGE_CATALOGUE->need(v instanceof BooleanValue,"knowledge catalogue selector must be boolean");
                    default->throw new IllegalArgumentException("unlisted original selector");
                }
            }
            if(kind==Kind.HOSTILITY)need(selectors.getFirst().value() instanceof IntegerValue,"hostility requires an explicit full target Rite ID");
            if(kind==Kind.TENETS){boolean target=selectors.get(0).value() instanceof IntegerValue,tenet=selectors.get(1).value() instanceof TextValue;need(target==tenet,"target Rite and named Tenet must be supplied together");}
        }
        public static Selection from(Request request){var kind=Kind.method(request.method().name());return new Selection(kind,kind.selectorFields().stream().map(f->new Argument(f,request.value(f))).toList());}
        public static Selection fixed(Kind kind){return new Selection(kind,List.of());}
        public Value value(Field field){return selectors.stream().filter(a->a.field()==field).findFirst().orElseThrow().value();}
        public Optional<String> doctrineKey(){return kind==Kind.DOCTRINE_KNOWLEDGE&&value(Field.DOCTRINE_KEY) instanceof TextValue t?Optional.of(t.value()):Optional.empty();}
        public Optional<BigInteger> target(){return (kind==Kind.TENETS||kind==Kind.HOSTILITY)&&value(Field.TARGET_RITE_ID) instanceof IntegerValue i?Optional.of(i.value()):Optional.empty();}
        public Optional<String> tenetKey(){return kind==Kind.TENETS&&value(Field.TENET_KEY) instanceof TextValue t?Optional.of(t.value()):Optional.empty();}
        public boolean includeKnowledge(){return kind==Kind.TENETS&&value(Field.INCLUDE_KNOWLEDGE_CATALOGUE) instanceof BooleanValue b&&b.value();}
    }
    public record Sources(ExactRef definition,ExactRef decoder,List<ExactRef> closure){
        public Sources{Objects.requireNonNull(definition);Objects.requireNonNull(decoder);closure=List.copyOf(closure);need(definition.bytes()>0&&decoder.bytes()>0&&!closure.isEmpty()&&closure.size()<=32,"actual configured doctrine/draft source closure required");}
    }
    public record Observed(Selection selection,Frame frame,RawJson nativeEnvelope,RawJson normalized){
        public Observed{Objects.requireNonNull(selection);Objects.requireNonNull(frame);Objects.requireNonNull(nativeEnvelope);Objects.requireNonNull(normalized);}
        public ObjectNode publicResult(){var n=obj(normalized);metadata(n,frame);publicEpochs(n,selection.kind());u64(n,"snapshot_revision",1);publicSignedFields(n,selection.kind());return n;}
    }
    public static ObjectNode selectionArguments(Selection selection){var n=StrictJson.object();for(var a:selection.selectors()){var v=a.value();if(v instanceof Absent absent){if(absent.presence()==Presence.NULL)n.putNull(a.field().wire());}else if(v instanceof IntegerValue i)n.put(a.field().wire(),i.value());else if(v instanceof TextValue t)n.put(a.field().wire(),t.value());else if(v instanceof BooleanValue b)n.put(a.field().wire(),b.value());else throw new IllegalArgumentException("unsupported typed original selector");}return n;}
    public static ObjectNode nativeArguments(Selection selection){var n=StrictJson.object();selection.doctrineKey().ifPresent(key->n.put("doctrine_key",key));selection.target().ifPresent(id->n.put("target_rite_id",id));selection.tenetKey().ifPresent(key->n.put("tenet_key",key));if(selection.includeKnowledge())n.put("include_knowledge_catalogue",true);return n;}
    private static String selectionIdentity(Selection selected){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw(selectionArguments(selected)).bytes()));}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException("required SHA-256 unavailable",impossible);}}
    public static ReadContract<Observed> contract(Selection selected,Sources sources,Admission admission){
        Objects.requireNonNull(selected);Objects.requireNonNull(sources);Objects.requireNonNull(admission);
        java.util.function.Function<PlanningReadReceipt,Observed> decode=receipt->decode(receipt,selected);
        return new ReadContract<>("religion.original.doctrine-draft."+selected.kind().name().toLowerCase(Locale.ROOT)+"."+selectionIdentity(selected),new OperationKey(selected.kind().step()),Optional.empty(),selected.kind().permission(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.definition(),(request,id)->{
            admission.verify(request);
            need(request.arguments().equals(OpportunityJson.object(OpportunityJson.parse(raw(selectionArguments(selected)).bytes()),"doctrine/draft selection")),"original doctrine/draft selector drift");
            return new NativeRequest(selected.kind().step(),Optional.empty(),raw(nativeArguments(selected)));
        },decode,decode);
    }
    public static Observed decode(PlanningReadReceipt receipt,Selection selected){ReligionService.requireGuards(receipt);need(receipt.request().operation().value().equals(selected.kind().step()),"original doctrine/draft operation differs");return normalizeEnvelope(selected,Frame.from(receipt),ReligionService.originalResult(receipt));}
    public static Observed normalizeEnvelope(Selection selected,Frame frame,ObjectNode original){
        var envelope=original.deepCopy();var kind=selected.kind();eq(envelope,"step",kind.step());yes(envelope,"accepted");yes(envelope,"private_build");yes(envelope,"read_only");no(envelope,"advertised");build(envelope,frame);
        eq(envelope,"backend_id","ck3-"+frame.build().version()+"-native-"+kind.suffix());eq(envelope,"domain_key",kind.domain());eq(envelope,"snapshot_revision",frame.nativeRevision());eq(envelope,"date_raw",frame.date());
        if(selected.includeKnowledge())need(frame.build()!=Build.CROZIER2,"Tenet knowledge catalogue requires exact .3/.4");
        ObjectNode value=kind.group()==Group.DATA?ReligionDoctrineDataValidation.normalize(selected,object(field(envelope,kind.nested())),frame):ReligionReformDraftValidation.normalize(kind,object(field(envelope,kind.nested())),frame);
        eq(envelope,"status",bool(value,"available")?"observed":"unavailable");
        if(kind==Kind.DOCTRINE_KNOWLEDGE){String mode=selected.doctrineKey().isPresent()?"by_key":"learned_rows";eq(envelope,"query_mode",mode);value.put("query_mode",mode);}
        if(kind==Kind.NUMERIC_SPECIAL_PARAMETERS)value.set("faith_numeric_final",ReligionDoctrineDataValidation.numericFinal(object(field(envelope,"faith_numeric_final")),frame,value));
        if(kind==Kind.DRAFT_RESOURCE_COSTS){
            need(!envelope.hasNonNull("religion_rite_dynamic_term_observations_12004")&&!envelope.hasNonNull("religion_creation_price_source_12004"),"actual4 creation price/dynamic-term sidecar decoder is not installed");
            if(envelope.has("religion_rite_dynamic_term_observations_12004")){var absent=StrictJson.object().put("status","absent").put("source_ready",false).putNull("observed_q64_raw").put("matching_record_count",0).putNull("selected_record_index").put("reason","term_observations_absent");value.set("religion_rite_dynamic_term_observation_facts_12004",absent);}
        }
        value.put("exact_ck3_build",frame.build().version()).put("exe_sha256",frame.build().sha256());value.set("snapshot_revision",field(envelope,"snapshot_revision"));value.set("query_date_raw",field(envelope,"date_raw"));value.set("backend_id",field(envelope,"backend_id"));value.put("domain_key",kind.domain()).put("status",text(envelope,"status")).put("read_only",true).put("advertised",false);
        return new Observed(selected,frame,raw(envelope),raw(value));
    }
    public static String schema(String original,Frame frame){String build=frame.build().version().replace(".","");if(original.startsWith("ck3_12002_")||(frame.build()==Build.CROZIER4&&original.startsWith("ck3_12003_")))return "ck3_"+build+"_"+original.substring("ck3_12002_".length());return original;}
    public static void nullableBoolean(ObjectNode n,String key){if(!field(n,key).isNull())bool(n,key);}
    public static void nullableText(ObjectNode n,String key){if(!field(n,key).isNull())text(n,key);}
    public static void nullableInteger(ObjectNode n,String key,BigInteger low,BigInteger high){if(!field(n,key).isNull())integer(n,key,low,high);}
    private static void epoch(ObjectNode parent,String key){if(parent.hasNonNull(key)){var child=object(parent.get(key));if(child.has("capture_epoch"))u64(child,"capture_epoch",0);}}
    private static void publicEpochs(ObjectNode n,Kind kind){
        u64(n,"capture_epoch",0);
        if(kind==Kind.DOCTRINES)for(String key:List.of("current_rite","faith_main_rite","boolean_parameters"))epoch(n,key);
        if(kind==Kind.TENETS)for(String key:List.of("target_rite_tenet_comparison","player_tenet_knowledge_catalogue"))epoch(n,key);
        if(kind==Kind.NUMERIC_SPECIAL_PARAMETERS)epoch(n,"faith_numeric_final");
        if(kind==Kind.REFORM_CONTEXT)for(String key:List.of("current_context","current_rite_model","current_creation_window","current_draft_costs","current_doctrine_selection","current_draft_creation_terms"))epoch(n,key);
        if(kind==Kind.DRAFT_RESOURCE_COSTS){epoch(n,"current_draft_window");epoch(object(n.get("base_resource_cost_quote")),"draft_quote");}
    }
    private static void signed(ObjectNode n,String key){if(n.hasNonNull(key))n.put(key,integer(n,key,I64_MIN,I64_MAX).toString());}
    private static void publicSignedFields(ObjectNode n,Kind kind){
        if(kind==Kind.NUMERIC_SPECIAL_PARAMETERS){for(String key:List.of("current_rite","faith_main_rite"))if(n.hasNonNull(key))for(JsonNode row:field(object(n.get(key)),"parameters"))signed(object(row),"raw");var f=object(n.get("faith_numeric_final"));for(String key:List.of("main_rite_adjustment_raw","native_define_raw","final_heresy_threshold_raw"))signed(f,key);}
        if(kind==Kind.REFORM_CONTEXT){var context=object(n.get("current_context"));for(String key:List.of("faith_fervor_raw","spiritual_fulfillment_raw"))signed(context,key);var model=object(n.get("current_rite_model"));for(String key:List.of("divergence_to_main_raw","faith_heresy_threshold_raw"))signed(model,key);var costs=object(n.get("current_draft_costs"));for(String key:List.of("piety_cost_raw","piety_missing_signed_raw"))signed(costs,key);if(n.hasNonNull("current_draft_creation_terms")){var terms=object(n.get("current_draft_creation_terms"));for(String key:List.of("draft_divergence_raw","faith_creation_threshold_raw"))signed(terms,key);}}
        if(kind==Kind.DRAFT_RESOURCE_COSTS){var base=object(n.get("base_resource_cost_quote"));if(base.hasNonNull("native_base_fee_slots_raw")){var values=StrictJson.object().putArray("values");for(JsonNode raw:base.get("native_base_fee_slots_raw")){need(raw.isIntegralNumber(),"native resource slot must be integer");values.add(range(raw.bigIntegerValue(),I64_MIN,I64_MAX).toString());}base.set("native_base_fee_slots_raw",values);}var costs=object(base.get("draft_quote"));for(String key:List.of("piety_cost_raw","piety_missing_signed_raw"))signed(costs,key);}
    }
}
