package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.family.FamilyMarriagePreparationReview;
import org.xar.ck3.control.application.planning.family.FamilyNativePreparation.VerifiedBasis;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Exact original five marriage wire producers. The Root fresh-reader owns qualification and archive custody. */
public final class FamilyMarriageNativeRequests {
    public static final String RULER_PLAN_SCHEMA="xar.ck3.family-ruler-marriage-prepared-plan/v1";
    public static final String RULER_CAPABILITY="game.command.arrange-marriage-N";
    private FamilyMarriageNativeRequests() { }

    /** No planningProof is read. Every field comes from the separately rebuilt actual reviewed plan. */
    public static NativeRequest prepare(ActionCommand command,VerifiedBasis actual) {
        Objects.requireNonNull(command);Objects.requireNonNull(actual);
        need(command.origin() instanceof CommandOrigin.Gameplay,"marriage send needs its original gameplay origin");
        JsonNode snapshot=DriverJson.toNode(actual.snapshot());
        need(booleanValue(snapshot.get("paused"))&&booleanValue(snapshot.get("map_ready")),"actual paused map preparation required");
        long played=character(snapshot.path("played_character").get("character_id"));
        need(BigInteger.valueOf(played).equals(command.before().frame().identity().player()),"fresh snapshot and immutable played identity differ");
        Obj plan=actual.preparedPlan().orElseThrow(()->new IllegalArgumentException("actual fresh reviewed marriage plan is absent"));
        JsonNode intent=DriverJson.toNode(command.arguments());
        if(FamilyMarriageIntent.SCHEMA.equals(StrictJson.text(intent.get("schema")))) {
            FamilyMarriageIntent selected=FamilyMarriageIntent.fromJson(command.arguments());
            need(selected.step().equals(command.operation().value())&&selected.actorId()==played,"actual private route or played intent changed");
            return new NativeRequest(selected.step(),Optional.empty(),fields(selected,plan));
        }
        RulerMarriageIntent selected=RulerMarriageIntent.fromJson(command.arguments());
        need(selected.step().equals(command.operation().value())&&selected.actorId()==played,"actual public route or played intent changed");
        return new NativeRequest(selected.step(),RULER_CAPABILITY,fields(selected,plan));
    }
    /** Pure rederivation: the caller independently validates the manifest and every retained original. */
    public static void verifyOriginal(ActionCommand command,NativeRequest retained,VerifiedBasis actual) {
        NativeRequest expected=prepare(command,actual);Objects.requireNonNull(retained);
        need(retained.step().equals(expected.step())&&retained.requiredCapability().equals(expected.requiredCapability())
                &&StrictJson.parse(retained.additionalFields().bytes()).equals(StrictJson.parse(expected.additionalFields().bytes())),
                "original prepared marriage wire differs from the actual fresh plan");
    }
    public static RawJson fields(FamilyMarriageIntent intent,Obj reviewedPlan) {
        Objects.requireNonNull(intent);JsonNode plan=DriverJson.toNode(Objects.requireNonNull(reviewedPlan));
        text(plan,"schema",FamilyMarriagePreparationReview.SCHEMA);text(plan,"selected_step",intent.step());
        var wire=StrictJson.object();
        switch(intent.route()) {
            case FIRST_HEIR -> {
                JsonNode legality=object(plan,"family_marriage_legality"),choice=object(plan,"family_marriage_choice");
                same(legality,"observed_first_heir_character_id",intent.subjectId());same(choice,"candidate_character_id",intent.candidateId());
                JsonNode rows=legality.get("native_legal_candidates");need(rows!=null&&rows.isArray(),"complete actual legal candidate array required");
                JsonNode selected=null;for(JsonNode row:rows)if(character(row.get("candidate_character_id"))==intent.candidateId()) {
                    need(selected==null,"actual native legal candidate is ambiguous");selected=row;
                }
                need(selected!=null,"selected candidate absent from actual native legal source");
                same(selected,"recipient_matchmaker_character_id",intent.recipientId());
                wire.put("query_sequence",sequence(legality,"query_sequence")).put("candidate_character_id",intent.candidateId());
            }
            case FULFILL_BETROTHAL -> {
                JsonNode relation=object(plan,"current_betrothal_relationship"),choice=object(plan,"current_betrothal_choice");
                same(relation,"heir_character_id",intent.subjectId());same(relation,"betrothed_character_id",intent.candidateId());
                same(choice,"heir_character_id",intent.subjectId());same(choice,"candidate_character_id",intent.candidateId());same(choice,"recipient_character_id",intent.recipientId());
                need(booleanValue(choice.get("effective_matrilineal_if_accepted"))==intent.matrilineal(),"actual current betrothal lineality changed");
                wire.put("heir_character_id",intent.subjectId()).put("candidate_character_id",intent.candidateId()).put("recipient_character_id",intent.recipientId());
            }
            case CHILD_MATRILINEAL,CHILD_DEFAULT -> {
                String prefix=intent.route()==FamilyMarriageIntent.Route.CHILD_MATRILINEAL?"child_matrilineal":"child_default";
                JsonNode legality=object(plan,prefix+"_legality"),value=object(plan,prefix+"_value"),row=object(value,"row");
                same(legality,"subject_character_id",intent.subjectId());same(value,"subject_character_id",intent.subjectId());
                same(value,"candidate_character_id",intent.candidateId());same(row,"recipient_character_id",intent.recipientId());
                need(sequence(value,"legality_query_sequence").equals(sequence(legality,"query_sequence")),"actual selected child value borrowed another native subject query");
                need(booleanValue(value.get("request_matrilineal_option"))==intent.matrilineal()
                        &&booleanValue(row.get("matrilineal_option_selected"))==intent.matrilineal(),"actual selected child option changed");
                wire.put("legality_query_sequence",sequence(legality,"query_sequence")).put("subject_character_id",intent.subjectId()).put("candidate_character_id",intent.candidateId());
            }
        }
        return new RawJson(StrictJson.canonical(wire));
    }
    /** Public native action carries its selected pair in the canonical step and has no extra wire fields. */
    public static RawJson fields(RulerMarriageIntent intent,Obj reviewedPlan) {
        Objects.requireNonNull(intent);JsonNode plan=DriverJson.toNode(Objects.requireNonNull(reviewedPlan));
        text(plan,"schema",RULER_PLAN_SCHEMA);text(plan,"selected_step",intent.step());
        JsonNode choice=object(plan,"marriage_choice");text(choice,"choice_id",intent.choiceId());
        same(choice,"played_character_id",intent.actorId());same(choice,"candidate_character_id",intent.candidateId());
        // The unique complete original query, not a cached choice or action ACK, must retain this exact membership.
        JsonNode query=object(plan,"marriage_choices");sequence(query,"query_sequence");
        JsonNode choices=query.get("arrange_marriage_choices");need(choices!=null&&choices.isArray(),"complete original public choices required");
        int found=0;for(JsonNode row:choices)if(intent.choiceId().equals(StrictJson.text(row.get("choice_id")))) {
            same(row,"played_character_id",intent.actorId());same(row,"candidate_character_id",intent.candidateId());found++;
        }
        need(found==1,"selected public pair is absent or ambiguous in actual complete native choices");
        return new RawJson(StrictJson.canonical(StrictJson.object()));
    }
    private static JsonNode object(JsonNode parent,String name){JsonNode value=parent.get(name);need(value!=null&&value.isObject(),"actual reviewed object required: "+name);return value;}
    private static long character(JsonNode n){return StrictJson.integer(n,1,0xFFFF_FFFEL);}
    private static void same(JsonNode node,String name,long expected){need(character(node.get(name))==expected,"fresh reviewed marriage identity changed: "+name);}
    private static BigInteger sequence(JsonNode node,String name){return StrictJson.integer(node.get(name),BigInteger.ONE,StrictJson.UINT64_MAX);}
    private static void text(JsonNode node,String name,String expected){need(expected.equals(StrictJson.text(node.get(name))),"fresh reviewed marriage field differs: "+name);}
    private static void need(boolean value,String reason){StrictJson.require(value,reason);}
    private static boolean booleanValue(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "exact JSON boolean required");
        return value.booleanValue();
    }

}
