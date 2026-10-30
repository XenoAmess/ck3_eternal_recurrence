package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Specified player-child enumeration, preserving original native rows and explicit diagnostic branches. */
public final class FamilyChildMarriageSubject {
    public static final String STEP="query-player-child-marriage-subject-v1-private",SCHEMA="xar.ck3.player-child-marriage-subject.v1";
    private FamilyChildMarriageSubject() { }
    public record Binding(Context context,int subject,boolean diagnoseFamilyArrays){
        public Binding{Objects.requireNonNull(context);need(subject>0,"positive native child subject required");range(context.revision(),BigInteger.ONE,U64);need(context.actor().signum()>0&&context.actor().compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0&&context.controls().paused()&&context.controls().mapReady()&&context.controls().alive(),"child subject needs paused living-player map");need(context.source().exactBuild().equalsIgnoreCase(context.build().sha256()),"child subject exact source SHA differs");}
    }
    public enum Extra {INTERMEDIARY,NATIVE_RANK,HEIR_AGE,CANDIDATE_AGE,PLAYED_DYNASTY,HEIR_DYNASTY,CANDIDATE_DYNASTY,REALM_BACKED}
    public record Candidate(HeirMarriageCandidate value,Set<Extra> supplied){public Candidate{Objects.requireNonNull(value);supplied=Set.copyOf(supplied);}}
    public record Diagnostics(int capacity,int scanned,Optional<MarriageDiagnostics> completeNative){public Diagnostics{Objects.requireNonNull(completeNative);}}
    public record Sample(int character,boolean generationValid) { }
    public record Slot(int offset,boolean headerReadable,boolean dataPresent,int capacity,int count,boolean nativeShape,boolean sampleReadable,List<Sample> samples){public Slot{samples=List.copyOf(samples);}}
    public record Probe(int playedCharacter,boolean spouseReadable,int primarySpouse,List<Slot> slots){public Probe{slots=List.copyOf(slots);}}
    public record NativeFields(boolean childVerified,Integer age,Integer threshold,Boolean adult,Integer house,Integer dynasty,Integer employer,Boolean bilateral,Integer betrothed,Integer primarySpouse,List<Integer> spouses,List<Candidate> candidates,Diagnostics diagnostics,Integer roleMismatches){public NativeFields{spouses=spouses==null?null:List.copyOf(spouses);candidates=List.copyOf(candidates);}}
    public record Observation(Binding binding,BigInteger querySequence,Availability availability,NativeFields fields,Optional<Probe> probe,RawJson original){
        public Observation{Objects.requireNonNull(binding);range(querySequence,BigInteger.ONE,U64);Objects.requireNonNull(availability);Objects.requireNonNull(fields);Objects.requireNonNull(probe);Objects.requireNonNull(original);}
        public List<Candidate> nativeLegalCandidates(){return fields.candidates().stream().filter(c->c.value().nativeLegal()).toList();}
    }
    private static final Set<String> REQUIRED=Set.of(("step accepted private_build read_only advertised native_revision query_sequence subject_source subject_character_id status unavailable_reason player_child_verified adult_measure_raw adult_threshold_raw adult house_id dynasty_id employer_character_id bilateral_verified betrothed_character_id primary_spouse_character_id spouse_character_ids family_candidates arrange_marriage_diagnostics").split(" "));
    private static final Set<String> BASE_CANDIDATE=Set.of("played_character_id","subject_character_id","candidate_character_id","recipient_matchmaker_character_id","complete_can_send","recipient_ai_accept_raw","recipient_answer_status_raw","recipient_answer_allows_send");
    private static final List<String> EXTRA_NAMES=List.of("intermediary_character_id","native_rank","heir_adult_measure_raw","candidate_adult_measure_raw","played_dynasty_id","heir_dynasty_id","candidate_dynasty_id","realm_backed_actor_recipient");
    private static void extras(JsonNode n,Set<String> required,Set<String> optional){object(n);Set<String> actual=new HashSet<>();n.fieldNames().forEachRemaining(actual::add);need(actual.containsAll(required)&&optional.containsAll(actual.stream().filter(k->!required.contains(k)).toList()),"wrong or missing child subject fields");}
    private static Integer optionalInt(JsonNode n,String key,int low,int high){return field(n,key).isNull()?null:integer(n,key,low,high);}
    public static Observation decode(RawJson raw,Binding binding){
        ObjectNode n=parse(raw);extras(n,REQUIRED,Set.of("family_array_diagnostic","family_subject_role_mismatches"));eq(n,"step",STEP);yes(n,"accepted");yes(n,"private_build");yes(n,"read_only");no(n,"advertised");eq(n,"subject_source","specified_player_child");eq(n,"native_revision",binding.context().revision());eq(n,"subject_character_id",BigInteger.valueOf(binding.subject()));
        String state=text(n,"status");need(state.equals("available")||state.equals("unavailable"),"child subject status differs");boolean available=state.equals("available");String reason=nullableText(n,"unavailable_reason");need(available?reason==null:reason!=null&&!reason.isEmpty(),"child subject reason/readiness differs");
        boolean verified=bool(n,"player_child_verified");Integer age=optionalInt(n,"adult_measure_raw",Short.MIN_VALUE,Short.MAX_VALUE),threshold=optionalInt(n,"adult_threshold_raw",Integer.MIN_VALUE,Integer.MAX_VALUE);Boolean adult=nullableBool(n,"adult");Integer house=optionalInt(n,"house_id",0,Integer.MAX_VALUE),dynasty=optionalInt(n,"dynasty_id",0,Integer.MAX_VALUE),employer=optionalInt(n,"employer_character_id",1,Integer.MAX_VALUE),betrothed=optionalInt(n,"betrothed_character_id",1,Integer.MAX_VALUE),primary=optionalInt(n,"primary_spouse_character_id",1,Integer.MAX_VALUE);Boolean bilateral=nullableBool(n,"bilateral_verified");
        List<Integer> spouses=field(n,"spouse_character_ids").isNull()?null:list(n,"spouse_character_ids",Integer.MAX_VALUE,value->{need(value.isIntegralNumber(),"spouse exact native integer required");return range(value.bigIntegerValue(),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();});
        List<Candidate> candidates=list(n,"family_candidates",Integer.MAX_VALUE,row->candidate(row,binding.context(),binding.subject()));unique(candidates.stream().map(c->c.value().character()).toList(),Integer.MAX_VALUE);Diagnostics diagnostics=diagnostics(field(n,"arrange_marriage_diagnostics"));Integer mismatches=n.has("family_subject_role_mismatches")?optionalInt(n,"family_subject_role_mismatches",Integer.MIN_VALUE,Integer.MAX_VALUE):null;
        if(available){need(verified&&age!=null&&Objects.equals(threshold,16)&&Objects.equals(adult,age>=16)&&Boolean.TRUE.equals(bilateral)&&spouses!=null&&diagnostics.scanned()==diagnostics.capacity(),"available specified child lacks demanded native operands");unique(spouses,Integer.MAX_VALUE);need(betrothed==null||!Objects.equals(betrothed,primary)&&!spouses.contains(betrothed),"native betrothal conflicts with current spouse");}
        else need(!verified&&candidates.isEmpty(),"unavailable specified child invented verified candidates");
        Optional<Probe> probe;if(binding.diagnoseFamilyArrays())probe=Optional.of(probe(field(n,"family_array_diagnostic"),binding));else{need(!n.has("family_array_diagnostic")||n.get("family_array_diagnostic").isNull(),"unsolicited player family-array diagnostic");probe=Optional.empty();}
        NativeFields fields=new NativeFields(verified,age,threshold,adult,house,dynasty,employer,bilateral,betrothed,primary,spouses,candidates,diagnostics,mismatches);return new Observation(binding,positive64(n,"query_sequence"),new Availability(available,reason),fields,probe,raw);
    }
    static Candidate candidate(JsonNode n,Context context,int subject){
        extras(n,BASE_CANDIDATE,Set.copyOf(EXTRA_NAMES));Set<Extra> supplied=new HashSet<>();for(int i=0;i<EXTRA_NAMES.size();i++)if(n.has(EXTRA_NAMES.get(i)))supplied.add(Extra.values()[i]);
        if(supplied.size()==EXTRA_NAMES.size())return new Candidate(FamilyMarriageCandidateCodec.decodeCompleteCandidate(n,context,subject),supplied);
        eq(n,"played_character_id",context.actor());eq(n,"subject_character_id",BigInteger.valueOf(subject));yes(n,"complete_can_send");int answer=integer(n,"recipient_answer_status_raw",0,2);boolean allowed=bool(n,"recipient_answer_allows_send");need(allowed==(answer!=2),"child candidate answer admission differs");if(n.has("native_rank"))nil(n,"native_rank");
        HeirMarriageCandidate value=new HeirMarriageCandidate(new CharacterId(integer(n,"candidate_character_id",1,Integer.MAX_VALUE)),new CharacterId(integer(n,"recipient_matchmaker_character_id",1,Integer.MAX_VALUE)),n.has("intermediary_character_id")?integer(n,"intermediary_character_id",-1,Integer.MAX_VALUE):-1,allowed,number(n,"recipient_ai_accept_raw",I64_MIN,I64_MAX),answer,n.has("heir_adult_measure_raw")?FamilyMarriageCandidateCodec.small(n,"heir_adult_measure_raw"):null,n.has("candidate_adult_measure_raw")?FamilyMarriageCandidateCodec.small(n,"candidate_adult_measure_raw"):null,n.has("played_dynasty_id")?FamilyMarriageCandidateCodec.dynasty(n,"played_dynasty_id"):null,n.has("heir_dynasty_id")?FamilyMarriageCandidateCodec.dynasty(n,"heir_dynasty_id"):null,n.has("candidate_dynasty_id")?FamilyMarriageCandidateCodec.dynasty(n,"candidate_dynasty_id"):null,n.has("realm_backed_actor_recipient")?nullableBool(n,"realm_backed_actor_recipient"):null);
        return new Candidate(value,supplied);
    }
    private static Diagnostics diagnostics(JsonNode n){
        object(n);Set<String> names=new HashSet<>();n.fieldNames().forEachRemaining(names::add);if(names.equals(Set.of("storage_capacity","slots_scanned")))return new Diagnostics(integer(n,"storage_capacity",Integer.MIN_VALUE,Integer.MAX_VALUE),integer(n,"slots_scanned",Integer.MIN_VALUE,Integer.MAX_VALUE),Optional.empty());
        MarriageDiagnostics full=MarriageDiagnostics.decode(n);return new Diagnostics(full.storageCapacity(),full.slotsScanned(),Optional.of(full));
    }
    private static Probe probe(JsonNode n,Binding binding){
        closed(n,"available","played_character_id","spouse_readable","primary_spouse_character_id","slots");yes(n,"available");eq(n,"played_character_id",binding.context().actor());List<Integer> offsets=binding.context().build()==Build.CROZIER2||binding.context().build()==Build.CROZIER3?List.of(0x20,0x38):List.of(0x20,0x30,0x40,0x50,0x60,0x70);
        List<Slot> slots=list(n,"slots",offsets.size(),row->{closed(row,"offset","header_readable","data_pointer_present","capacity","count","native_int_array_shape","sample_readable","samples");List<Sample> samples=list(row,"samples",16,s->{closed(s,"character_id","generation_valid");return new Sample(integer(s,"character_id",Integer.MIN_VALUE,Integer.MAX_VALUE),bool(s,"generation_valid"));});return new Slot(integer(row,"offset",Integer.MIN_VALUE,Integer.MAX_VALUE),bool(row,"header_readable"),bool(row,"data_pointer_present"),integer(row,"capacity",Integer.MIN_VALUE,Integer.MAX_VALUE),integer(row,"count",Integer.MIN_VALUE,Integer.MAX_VALUE),bool(row,"native_int_array_shape"),bool(row,"sample_readable"),samples);});
        need(slots.stream().map(Slot::offset).toList().equals(offsets),"family diagnostic native offset order differs");return new Probe(integer(n,"played_character_id",1,Integer.MAX_VALUE),bool(n,"spouse_readable"),integer(n,"primary_spouse_character_id",Integer.MIN_VALUE,Integer.MAX_VALUE),slots);
    }
    public static RawJson verifyOriginal(Observation value){need(decode(value.original(),value.binding()).equals(value),"specified child differs from original native packet");return value.original();}
    public static OpportunityJson.Obj project(Observation value){
        verifyOriginal(value);Binding b=value.binding();Context c=b.context();ObjectNode raw=parse(value.original()),out=F.objectNode().put("schema",SCHEMA).put("schema_version",1).put("exact_ck3_build",c.build().version()).put("read_only",true).put("advertised",false).put("native_revision",c.revision()).put("played_character_id",c.actor()).put("subject_character_id",b.subject()).put("query_sequence",value.querySequence()).put("status",value.availability().available()?"available":"unavailable").put("unavailable_reason",value.availability().reason());
        if(c.build()!=Build.WANDERER6)out.put("exe_sha256",c.build().sha256());if(b.diagnoseFamilyArrays())out.set("family_array_diagnostic",raw.get("family_array_diagnostic"));
        if(value.availability().available()){
            for(String key:List.of("player_child_verified","adult_measure_raw","adult_threshold_raw","adult","house_id","dynasty_id","employer_character_id","betrothed_character_id","primary_spouse_character_id","spouse_character_ids","bilateral_verified"))out.set(key,raw.get(key));out.set("candidates",raw.get("family_candidates"));var legal=out.putArray("native_legal_candidates");for(JsonNode row:raw.get("family_candidates"))if(integer(row,"recipient_answer_status_raw",0,2)!=2)legal.add(row);out.set("diagnostics",raw.get("arrange_marriage_diagnostics"));if(raw.has("family_subject_role_mismatches"))out.set("family_subject_role_mismatches",raw.get("family_subject_role_mismatches"));else out.putNull("family_subject_role_mismatches");
        }return InteractionArguments.app(out);
    }
}
