package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Full current marriage value wire shared by the five-heir projection and one-child value read. */
public final class FamilyMarriageValue {
    private FamilyMarriageValue() { }
    public enum Mode {
        FIRST_HEIR("query-first-heir-candidate-alliance-projection-v1-private","xar.ck3.first-heir-candidate-alliance-projection.v1",5),
        CHILD("query-player-child-marriage-value-v1-private","xar.ck3.player-child-marriage-value.v1",1);
        private final String step,schema; private final int rows;
        Mode(String step,String schema,int rows) {this.step=step;this.schema=schema;this.rows=rows;}
        public String step() {return step;} public String schema() {return schema;} public int rows() {return rows;}
    }
    public enum Failure {NONE,BINDING_UNAVAILABLE,FRAME_CHANGED,IDENTITY_CHANGED,ROLE_CHANGED,FINAL_LEGALITY_CHANGED,
        PROJECTION_UNAVAILABLE,OUTCOME_UNAVAILABLE,HEIR_RELATIONSHIP_UNAVAILABLE,LINEAGE_UNAVAILABLE,
        SEX_SELECTOR_UNAVAILABLE,SELECTED_OPTION_UNAVAILABLE,GENERIC_COST_UNAVAILABLE,UNKNOWN}
    public enum ProjectionFailure {NONE,EXACT_BUILD_NOT_ADMITTED,BINDING_UNAVAILABLE,SIGNATURE_MISMATCH,INVALID_INPUT,
        CONTEXT_ROLES_MISMATCH,OPTION_ID_UNAVAILABLE,NATIVE_VECTOR_INVALID,ROW_IDENTITY_MISMATCH,UNKNOWN}
    public enum OutcomeFailure {NONE,EXACT_BUILD_NOT_ADMITTED,BINDING_MISMATCH,SIGNATURE_MISMATCH,MEMORY_READER_UNAVAILABLE,
        INVALID_INPUT,SECONDARY_PAIR_IDENTITY_MISMATCH,RUNTIME_THRESHOLD_UNAVAILABLE,OPTION_IDENTIFIER_UNAVAILABLE,OUTCOME_SAMPLE_DRIFT,UNKNOWN}
    public enum Outcome {MARRIAGE,BETROTHAL}
    public record Candidate(int characterId,int recipientId) {
        public Candidate {need(characterId>0 && recipientId>0,"positive native candidate/recipient int32 required");}
    }
    /** Data binding; installed producer additionally reopens and validates the original legality receipt. */
    public record Binding(Mode mode,Context context,BigInteger legalityQuerySequence,int subjectId,
                          List<Candidate> candidates,boolean requestMatrilineal,Optional<Lineage> childLineage) {
        public Binding {
            Objects.requireNonNull(mode);Objects.requireNonNull(context);Objects.requireNonNull(childLineage);
            range(legalityQuerySequence,BigInteger.ONE,U64);need(subjectId>0,"actual subject int32 required");
            candidates=List.copyOf(candidates);need(candidates.size()==mode.rows(),"exact marriage query row count required");
            unique(candidates.stream().map(Candidate::characterId).toList(),mode.rows());
            need(mode==Mode.CHILD || childLineage.isEmpty(),"first-heir projection has no child lineage override");
            need(context.build()==Build.CROZIER4 && context.source().exactBuild().equals(context.build().version()),
                    "full value wire requires current exact4 source epoch");
        }
    }
    public record Costs(long gold,long prestige,long piety,long renown,long influence,long herd,long treasury,
                        long treasuryOrGold,long merit,long barterGoods) { }
    public record Fertility(boolean extensionPresent,boolean gateEvaluated,Boolean gateAllows,long effectiveRaw) {
        public Fertility {
            need(gateEvaluated==extensionPresent && (gateEvaluated?gateAllows!=null:gateAllows==null),"native fertility gate domain differs");
            need(Boolean.TRUE.equals(gateAllows) || effectiveRaw==0,"closed native fertility gate invented effective value");
        }
    }
    public record Adult(boolean adult,short measure,int threshold) {
        public Adult {need(adult==(measure>=threshold),"native adult sample disagrees with threshold");}
    }
    public record Relationship(OptionalInt betrothed,OptionalInt primarySpouse,List<Integer> spouses) {
        public Relationship {
            Objects.requireNonNull(betrothed);Objects.requireNonNull(primarySpouse);spouses=List.copyOf(spouses);
            need((betrothed.isEmpty() || betrothed.getAsInt()>0) && (primarySpouse.isEmpty() || primarySpouse.getAsInt()>0),"invalid nullable native partner");
            need(spouses.stream().allMatch(id->id>0),"positive native spouses required");unique(spouses,65536);
            need(primarySpouse.isEmpty() || spouses.contains(primarySpouse.getAsInt()),"native primary spouse absent from complete spouse vector");
        }
    }
    public record Lineage(OptionalInt house,OptionalInt dynasty) {
        public Lineage {
            Objects.requireNonNull(house);Objects.requireNonNull(dynasty);
            need((house.isEmpty() || house.getAsInt()>=0) && (dynasty.isEmpty() || dynasty.getAsInt()>=0)
                    && (dynasty.isEmpty() || house.isPresent()),"native house/dynasty nullable identity differs");
        }
    }
    public record Pair(int first,int second,boolean alreadyAllied,boolean bothHaveRealmData,boolean wouldAttempt) {
        public Pair {need(first>0 && second>0 && first!=second && wouldAttempt==(!alreadyAllied && bothHaveRealmData),"native potential alliance pair differs");}
    }
    public record FinalLegality(boolean requestedMatrilineal,Boolean selectedReadback,boolean sampled,Boolean canSend,
                                OptionalLong aiAccept,OptionalInt answer) {
        public FinalLegality {
            Objects.requireNonNull(aiAccept);Objects.requireNonNull(answer);
            need(requestedMatrilineal?selectedReadback!=null:selectedReadback==null,"selected native option readback domain differs");
            need(sampled?canSend!=null:canSend==null,"final legality sampling domain differs");
            need(aiAccept.isPresent()==answer.isPresent() && (sampled || aiAccept.isEmpty()),"partial native recipient acceptance differs");
            need(answer.isEmpty() || (answer.getAsInt()>=0 && answer.getAsInt()<=2),"native final answer outside 0/1/2");
        }
        public boolean positiveSend() {return sampled && Boolean.TRUE.equals(canSend) && aiAccept.isPresent()
                && aiAccept.getAsLong()>0 && answer.isPresent() && answer.getAsInt()!=2;}
    }
    public record Value(Costs costs,Outcome outcome,Adult heirAdult,Adult candidateAdult,Fertility heirFertility,
                        Fertility candidateFertility,OptionalLong fertilityFloor,OptionalInt heirScorerAgeOverride,
                        OptionalInt candidateScorerAgeOverride,OptionalInt candidateScorerAgeUpper,boolean grandWedding,
                        Relationship heirRelationship,Relationship candidateRelationship,Lineage playedLineage,
                        Lineage heirLineage,Lineage candidateLineage,int heirSexSelector,int candidateSexSelector,
                        boolean effectiveMatrilineal,boolean selectedMatrilineal,List<Pair> possiblePairs) {
        public Value {
            for(Object required:List.of(costs,outcome,heirAdult,candidateAdult,heirFertility,candidateFertility,fertilityFloor,
                    heirScorerAgeOverride,candidateScorerAgeOverride,candidateScorerAgeUpper,heirRelationship,candidateRelationship,
                    playedLineage,heirLineage,candidateLineage))Objects.requireNonNull(required);
            possiblePairs=List.copyOf(possiblePairs);need(possiblePairs.size()<=3,"native alliance projection pair bound differs");
            need((heirSexSelector==0 || heirSexSelector==1) && (candidateSexSelector==0 || candidateSexSelector==1),"native sex selectors differ");
            need(effectiveMatrilineal==(heirSexSelector==candidateSexSelector?heirSexSelector!=0:selectedMatrilineal),"native effective lineality differs");
            need(outcome==(heirAdult.adult() && candidateAdult.adult() && !grandWedding?Outcome.MARRIAGE:Outcome.BETROTHAL),"native outcome/adult breakdown differs");
        }
    }
    public record Row(int actorId,int subjectId,Candidate candidate,Failure failure,ProjectionFailure projectionFailure,
                      OutcomeFailure outcomeFailure,FinalLegality finalLegality,Optional<Value> value) {
        public Row {
            need(actorId>0 && subjectId>0,"positive native marriage roles required");
            for(Object required:List.of(candidate,failure,projectionFailure,outcomeFailure,finalLegality,value))Objects.requireNonNull(required);
            need(value.isPresent()==(failure==Failure.NONE),"native value status/failure differs");
            if(value.isPresent())need(projectionFailure==ProjectionFailure.NONE && outcomeFailure==OutcomeFailure.NONE,"available native value carries failure");
            if(failure==Failure.OUTCOME_UNAVAILABLE)need(outcomeFailure!=OutcomeFailure.NONE,"missing native outcome failure");
        }
        public boolean available() {return value.isPresent();}
    }
    public record Observation(Binding binding,boolean available,List<Row> rows,RawJson original) {
        public Observation {
            Objects.requireNonNull(binding);Objects.requireNonNull(original);rows=List.copyOf(rows);
            need(rows.size()==binding.mode().rows() && available==rows.stream().allMatch(Row::available),"native aggregate marriage status differs");
        }
    }
    public static Observation decode(RawJson raw,Binding binding) {
        JsonNode n=parse(raw);closed(n,"step","accepted","private_build","read_only","advertised","native_revision","legality_query_sequence","status","rows");
        eq(n,"step",binding.mode().step());yes(n,"accepted");yes(n,"private_build");yes(n,"read_only");no(n,"advertised");
        eq(n,"native_revision",binding.context().revision());eq(n,"legality_query_sequence",binding.legalityQuerySequence());
        List<Row> rows=list(n,"rows",binding.mode().rows(),FamilyMarriageValue::row);
        need(rows.size()==binding.candidates().size(),"native marriage row count changed");Value first=null;
        for(int i=0;i<rows.size();i++) {
            Row row=rows.get(i);need(BigInteger.valueOf(row.actorId()).equals(binding.context().actor()) && row.subjectId()==binding.subjectId()
                    && row.candidate().equals(binding.candidates().get(i)),"native marriage five-role identity/order differs");
            need(row.finalLegality().requestedMatrilineal()==binding.requestMatrilineal(),"native requested lineality differs");
            if(row.available()) {
                Value value=row.value().orElseThrow();
                if(binding.mode()==Mode.CHILD && binding.requestMatrilineal())need(Boolean.TRUE.equals(row.finalLegality().selectedReadback()) && value.selectedMatrilineal()
                        && row.finalLegality().positiveSend(),"requested matrilineal read lacks actual selected/final-positive native terms");
                binding.childLineage().ifPresent(lineage->need(lineage.equals(value.heirLineage()),"child lineage differs from original verified subject"));
                if(first!=null)need(first.heirAdult().equals(value.heirAdult()) && first.heirRelationship().equals(value.heirRelationship())
                        && first.playedLineage().equals(value.playedLineage()) && first.heirLineage().equals(value.heirLineage())
                        && first.heirSexSelector()==value.heirSexSelector(),"native shared heir inputs changed between candidate rows");
                else first=value;
            }
        }
        return new Observation(binding,status(n,"status"),rows,raw);
    }
    public static RawJson verifyOriginal(Observation observation) {
        need(decode(observation.original(),observation.binding()).equals(observation),"marriage value differs from original native packet");return observation.original();
    }
    /** Original Python public shape; derived branches are emitted only for the five-candidate projection. */
    public static OpportunityJson.Obj project(Observation observation) {
        verifyOriginal(observation);Binding binding=observation.binding();ObjectNode n=parse(observation.original());
        ObjectNode out=F.objectNode().put("schema",binding.mode().schema()).put("exact_ck3_build",binding.context().build().version())
                .put("exe_sha256",binding.context().build().sha256()).put("read_only",true).put("advertised",false)
                .put("status",observation.available()?"available":"unavailable").put("native_revision",binding.context().revision())
                .put("legality_query_sequence",binding.legalityQuerySequence());
        if(binding.mode()==Mode.FIRST_HEIR) {
            out.put("schema_version",1);var rows=out.putArray("rows");
            for(int i=0;i<observation.rows().size();i++) {
                ObjectNode row=object(n.get("rows").get(i)).deepCopy();derive(row,observation.rows().get(i));rows.add(row);
            }
        } else {
            out.put("played_character_id",binding.context().actor()).put("subject_character_id",binding.subjectId())
                    .put("candidate_character_id",binding.candidates().getFirst().characterId()).put("request_matrilineal_option",binding.requestMatrilineal());
            out.set("row",n.get("rows").get(0));
        }
        return InteractionArguments.app(out);
    }
    private static Row row(JsonNode n) {
        closed(n,"actor_character_id","heir_character_id","candidate_character_id","recipient_character_id","status",
                "requested_matrilineal_option","selected_option_readback","final_legality_sampled","complete_can_send",
                "recipient_ai_accept_raw","recipient_answer_status_raw","generic_costs","failure","projection_failure","outcome_failure",
                "predicted_outcome_if_accepted","heir_is_adult","candidate_is_adult","heir_adult_measure_raw","candidate_adult_measure_raw",
                "heir_adult_threshold_raw","candidate_adult_threshold_raw","heir_native_fertility","candidate_native_fertility",
                "native_candidate_fertility_floor_raw","heir_native_scorer_age_override_raw","candidate_native_scorer_age_override_raw",
                "native_candidate_scorer_age_upper_raw","grand_wedding_option_selected","heir_betrothed_character_id",
                "heir_primary_spouse_character_id","heir_spouse_character_ids","candidate_betrothed_character_id",
                "candidate_primary_spouse_character_id","candidate_spouse_character_ids","played_house_id","played_dynasty_id",
                "heir_house_id","heir_dynasty_id","candidate_house_id","candidate_dynasty_id","heir_sex_selector_raw",
                "candidate_sex_selector_raw","effective_matrilineal_if_accepted","matrilineal_option_selected","possible_alliance_pairs");
        boolean available=status(n,"status");
        FinalLegality finalLegality=new FinalLegality(bool(n,"requested_matrilineal_option"),nullableBool(n,"selected_option_readback"),
                bool(n,"final_legality_sampled"),nullableBool(n,"complete_can_send"),optionalLong(n,"recipient_ai_accept_raw"),optionalInt(n,"recipient_answer_status_raw",0,2));
        Optional<Value> value;
        if(available)value=Optional.of(new Value(costs(field(n,"generic_costs")),nativeEnum(n,"predicted_outcome_if_accepted",Outcome.class),
                adult(n,"heir"),adult(n,"candidate"),fertility(field(n,"heir_native_fertility")),fertility(field(n,"candidate_native_fertility")),
                optionalLong(n,"native_candidate_fertility_floor_raw"),optionalInt(n,"heir_native_scorer_age_override_raw",Short.MIN_VALUE,Short.MAX_VALUE),
                optionalInt(n,"candidate_native_scorer_age_override_raw",Short.MIN_VALUE,Short.MAX_VALUE),optionalInt(n,"native_candidate_scorer_age_upper_raw",Integer.MIN_VALUE,Integer.MAX_VALUE),
                bool(n,"grand_wedding_option_selected"),relationship(n,"heir"),relationship(n,"candidate"),lineage(n,"played"),lineage(n,"heir"),lineage(n,"candidate"),
                integer(n,"heir_sex_selector_raw",0,1),integer(n,"candidate_sex_selector_raw",0,1),bool(n,"effective_matrilineal_if_accepted"),bool(n,"matrilineal_option_selected"),pairs(n)));
        else {
            nil(n,"generic_costs","predicted_outcome_if_accepted","heir_is_adult","candidate_is_adult","heir_adult_measure_raw","candidate_adult_measure_raw",
                    "heir_adult_threshold_raw","candidate_adult_threshold_raw","heir_native_fertility","candidate_native_fertility","native_candidate_fertility_floor_raw",
                    "heir_native_scorer_age_override_raw","candidate_native_scorer_age_override_raw","native_candidate_scorer_age_upper_raw","grand_wedding_option_selected",
                    "heir_betrothed_character_id","heir_primary_spouse_character_id","heir_spouse_character_ids","candidate_betrothed_character_id",
                    "candidate_primary_spouse_character_id","candidate_spouse_character_ids","played_house_id","played_dynasty_id","heir_house_id","heir_dynasty_id",
                    "candidate_house_id","candidate_dynasty_id","heir_sex_selector_raw","candidate_sex_selector_raw","effective_matrilineal_if_accepted","matrilineal_option_selected");
            need(pairs(n).isEmpty(),"unavailable native marriage value claims alliance pairs");value=Optional.empty();
        }
        return new Row(integer(n,"actor_character_id",1,Integer.MAX_VALUE),integer(n,"heir_character_id",1,Integer.MAX_VALUE),
                new Candidate(integer(n,"candidate_character_id",1,Integer.MAX_VALUE),integer(n,"recipient_character_id",1,Integer.MAX_VALUE)),
                nativeEnum(n,"failure",Failure.class),nativeEnum(n,"projection_failure",ProjectionFailure.class),nativeEnum(n,"outcome_failure",OutcomeFailure.class),finalLegality,value);
    }
    private static Costs costs(JsonNode n) {
        closed(n,"raw_scale","payer_role","application_timing","gold_raw","prestige_raw","piety_raw","renown_raw","influence_raw","herd_raw","treasury_raw","treasury_or_gold_raw","merit_raw","barter_goods_raw");
        eq(n,"raw_scale",BigInteger.valueOf(100000));eq(n,"payer_role","actor");eq(n,"application_timing","on_send");
        return new Costs(signed(n,"gold_raw"),signed(n,"prestige_raw"),signed(n,"piety_raw"),signed(n,"renown_raw"),signed(n,"influence_raw"),
                signed(n,"herd_raw"),signed(n,"treasury_raw"),signed(n,"treasury_or_gold_raw"),signed(n,"merit_raw"),signed(n,"barter_goods_raw"));
    }
    private static Fertility fertility(JsonNode n) {
        closed(n,"source","extension_present","native_gate_evaluated","native_gate_allows","effective_raw");eq(n,"source","native_marriage_fertility_input");
        return new Fertility(bool(n,"extension_present"),bool(n,"native_gate_evaluated"),nullableBool(n,"native_gate_allows"),signed(n,"effective_raw"));
    }
    private static Adult adult(JsonNode n,String role) {return new Adult(bool(n,role+"_is_adult"),(short)integer(n,role+"_adult_measure_raw",Short.MIN_VALUE,Short.MAX_VALUE),integer(n,role+"_adult_threshold_raw",Integer.MIN_VALUE,Integer.MAX_VALUE));}
    private static Relationship relationship(JsonNode n,String role) {
        return new Relationship(optionalInt(n,role+"_betrothed_character_id",1,Integer.MAX_VALUE),optionalInt(n,role+"_primary_spouse_character_id",1,Integer.MAX_VALUE),
                list(n,role+"_spouse_character_ids",65536,id->{need(id.isIntegralNumber(),"native spouse integer required");return range(id.bigIntegerValue(),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}));
    }
    private static Lineage lineage(JsonNode n,String role) {return new Lineage(optionalInt(n,role+"_house_id",0,Integer.MAX_VALUE),optionalInt(n,role+"_dynasty_id",0,Integer.MAX_VALUE));}
    private static List<Pair> pairs(JsonNode n) {
        return list(n,"possible_alliance_pairs",3,p->{closed(p,"first_character_id","second_character_id","already_allied","both_have_realm_data","would_attempt_if_accepted");
            return new Pair(integer(p,"first_character_id",1,Integer.MAX_VALUE),integer(p,"second_character_id",1,Integer.MAX_VALUE),bool(p,"already_allied"),bool(p,"both_have_realm_data"),bool(p,"would_attempt_if_accepted"));});
    }
    private static boolean status(JsonNode n,String key) {String status=text(n,key);need(status.equals("available") || status.equals("unavailable"),"native marriage status differs");return status.equals("available");}
    private static <E extends Enum<E>> E nativeEnum(JsonNode n,String key,Class<E> type) {
        E value=enumeration(n,key,type);need(text(n,key).equals(value.name().toLowerCase(java.util.Locale.ROOT)),"canonical native enum spelling required: "+key);return value;
    }
    private static long signed(JsonNode n,String key) {return number(n,key,I64_MIN,I64_MAX).longValueExact();}
    private static OptionalLong optionalLong(JsonNode n,String key) {return field(n,key).isNull()?OptionalLong.empty():OptionalLong.of(signed(n,key));}
    private static OptionalInt optionalInt(JsonNode n,String key,int low,int high) {return field(n,key).isNull()?OptionalInt.empty():OptionalInt.of(integer(n,key,low,high));}
    private static void derive(ObjectNode n,Row row) {
        ObjectNode fertility=n.putObject("candidate_native_fertility_floor_comparison_v1").put("source","derived_signed_native_fertility_floor_comparison").put("ready",false);fertility.putNull("passes");
        ObjectNode heir=n.putObject("heir_native_scorer_effective_age_v1").put("source","derived_native_scorer_effective_age").put("ready",false);heir.putNull("effective_raw");
        ObjectNode candidate=n.putObject("candidate_native_scorer_effective_age_v1").put("source","derived_native_scorer_effective_age").put("ready",false);candidate.putNull("effective_raw");
        ObjectNode branch=n.putObject("candidate_native_scorer_age_branch_v1").put("source","derived_native_scorer_age_branch").put("ready",false);branch.putNull("passes");branch.putNull("selector_zero_bypass");
        ObjectNode first=branch.putObject("first_comparison").put("ready",false);first.putNull("passes");
        ObjectNode second=branch.putObject("second_comparison").put("ready",false);second.putNull("passes");second.putNull("subject_adult_deficit_raw");second.putNull("adjusted_candidate_age_raw");
        if(!row.available())return;Value value=row.value().orElseThrow();
        if(value.fertilityFloor().isPresent())fertility.put("ready",true).put("passes",value.candidateFertility().effectiveRaw()>value.fertilityFloor().getAsLong());
        OptionalInt heirAge=effectiveAge(value.heirScorerAgeOverride(),value.heirAdult(),heir),candidateAge=effectiveAge(value.candidateScorerAgeOverride(),value.candidateAdult(),candidate);
        branch.put("selector_zero_bypass",value.candidateSexSelector()==0);
        if(value.candidateSexSelector()==0) {branch.put("ready",true).put("passes",true);return;}
        if(candidateAge.isEmpty() || value.candidateScorerAgeUpper().isEmpty())return;
        int upper=value.candidateScorerAgeUpper().getAsInt();boolean firstPass=candidateAge.getAsInt()<=upper;first.put("ready",true).put("passes",firstPass);
        if(!firstPass) {branch.put("ready",true).put("passes",false);return;}
        if(heirAge.isEmpty())return;
        // Java int subtraction deliberately keeps the native signed32 wrapping used by the original producer.
        int deficit=heirAge.getAsInt()<value.heirAdult().threshold()?value.heirAdult().threshold()-heirAge.getAsInt():0;
        int adjusted=candidateAge.getAsInt()-deficit;boolean passes=adjusted<=upper;
        second.put("ready",true).put("passes",passes).put("subject_adult_deficit_raw",deficit).put("adjusted_candidate_age_raw",adjusted);
        branch.put("ready",true).put("passes",passes);
    }
    private static OptionalInt effectiveAge(OptionalInt override,Adult actual,ObjectNode output) {
        if(override.isEmpty())return OptionalInt.empty();int value=override.getAsInt()>=0?override.getAsInt():actual.measure();
        output.put("ready",true).put("effective_raw",value);return OptionalInt.of(value);
    }
}
