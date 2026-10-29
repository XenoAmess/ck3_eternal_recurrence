package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.family.FamilyMarriagePreparationReview;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;

/** Original native payload shapes; no source, writer, Game or business qualification is manufactured. */
final class FamilyMarriageNativeRequestsTest {
    private static FamilyMarriageIntent intent(FamilyMarriageIntent.Route route) {
        return new FamilyMarriageIntent(route,101,303,202,404,route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL,
                route==FamilyMarriageIntent.Route.FIRST_HEIR?List.of(202,203,204,205,206):List.of(),Optional.empty());
    }
    private static ObjectNode plan(FamilyMarriageIntent intent) {
        var n=StrictJson.object().put("schema",FamilyMarriagePreparationReview.SCHEMA).put("selected_step",intent.step());
        switch(intent.route()) {
            case FIRST_HEIR -> {
                var legal=n.putObject("family_marriage_legality").put("observed_first_heir_character_id",303).put("query_sequence",7);
                legal.putArray("native_legal_candidates").addObject().put("candidate_character_id",202).put("recipient_matchmaker_character_id",404);
                n.putObject("family_marriage_choice").put("candidate_character_id",202);
            }
            case FULFILL_BETROTHAL -> {
                n.putObject("current_betrothal_relationship").put("heir_character_id",303).put("betrothed_character_id",202);
                n.putObject("current_betrothal_choice").put("heir_character_id",303).put("candidate_character_id",202)
                        .put("recipient_character_id",404).put("effective_matrilineal_if_accepted",false);
            }
            case CHILD_MATRILINEAL,CHILD_DEFAULT -> {
                String prefix=intent.route()==FamilyMarriageIntent.Route.CHILD_MATRILINEAL?"child_matrilineal":"child_default";
                n.putObject(prefix+"_legality").put("subject_character_id",303).put("query_sequence",7);
                var value=n.putObject(prefix+"_value").put("subject_character_id",303).put("candidate_character_id",202)
                        .put("legality_query_sequence",7).put("request_matrilineal_option",intent.matrilineal());
                value.putObject("row").put("recipient_character_id",404).put("matrilineal_option_selected",intent.matrilineal());
            }
        }
        return n;
    }
    @Test void allFourPrivateRoutesKeepTheOriginalNativeFieldSets() {
        for(var route:FamilyMarriageIntent.Route.values()) {
            var intent=intent(route);RawJson wire=FamilyMarriageNativeRequests.fields(intent,app(plan(intent)));
            JsonNode expected=switch(route) {
                case FIRST_HEIR -> StrictJson.object().put("query_sequence",7).put("candidate_character_id",202);
                case FULFILL_BETROTHAL -> StrictJson.object().put("heir_character_id",303).put("candidate_character_id",202).put("recipient_character_id",404);
                case CHILD_MATRILINEAL,CHILD_DEFAULT -> StrictJson.object().put("legality_query_sequence",7).put("subject_character_id",303).put("candidate_character_id",202);
            };
            assertEquals(expected,StrictJson.parse(wire.bytes()));
            assertArrayEquals(wire.bytes(),FamilyMarriageNativeRequests.fields(intent,app(DriverJson.toNode(app(plan(intent))))).bytes());
        }
    }
    @Test void firstHeirSequencePreservesTheWholeNativeU64Domain() {
        var intent=intent(FamilyMarriageIntent.Route.FIRST_HEIR);var plan=plan(intent);
        ((ObjectNode)plan.get("family_marriage_legality")).put("query_sequence",StrictJson.UINT64_MAX);
        assertEquals(StrictJson.UINT64_MAX,StrictJson.parse(FamilyMarriageNativeRequests.fields(intent,app(plan)).bytes()).get("query_sequence").bigIntegerValue());
    }
    @Test void missingFloatBooleanAndUnboundedNativeSequenceRejectBeforeSubmission() {
        var intent=intent(FamilyMarriageIntent.Route.FIRST_HEIR);
        for(JsonNode invalid:List.of(StrictJson.object().booleanNode(true),StrictJson.object().numberNode(7.0),
                StrictJson.object().numberNode(BigInteger.ZERO),StrictJson.object().numberNode(StrictJson.UINT64_MAX.add(BigInteger.ONE)))) {
            var plan=plan(intent);((ObjectNode)plan.get("family_marriage_legality")).set("query_sequence",invalid);
            assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(plan)));
        }
        var missing=plan(intent);((ObjectNode)missing.get("family_marriage_legality")).remove("query_sequence");
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(missing)));
    }
    @Test void privateFieldProducerRejectsWrongPairRecipientAndDuplicateNativeMembership() {
        var intent=intent(FamilyMarriageIntent.Route.FIRST_HEIR);var changed=plan(intent);
        ((ObjectNode)changed.get("family_marriage_choice")).put("candidate_character_id",203);
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(changed)));
        var duplicate=plan(intent);var rows=assertInstanceOf(ArrayNode.class,duplicate.get("family_marriage_legality").withArray("native_legal_candidates"));rows.add(rows.get(0).deepCopy());
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(duplicate)));
        var foreign=plan(intent);((ObjectNode)foreign.get("family_marriage_legality").get("native_legal_candidates").get(0)).put("recipient_matchmaker_character_id",405);
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(foreign)));
    }
    @Test void childValueMustKeepItsActualSubjectQueryAndSelectedNativeOption() {
        for(var route:List.of(FamilyMarriageIntent.Route.CHILD_MATRILINEAL,FamilyMarriageIntent.Route.CHILD_DEFAULT)) {
            var intent=intent(route);String prefix=route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL?"child_matrilineal":"child_default";
            var mismatch=plan(intent);((ObjectNode)mismatch.get(prefix+"_value")).put("legality_query_sequence",8);
            assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(mismatch)));
            var option=plan(intent);((ObjectNode)option.get(prefix+"_value")).put("request_matrilineal_option",!intent.matrilineal());
            assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(option)));
        }
    }
    @Test void planningProofCannotSubstituteForAnActualReviewedPlan() {
        var intent=intent(FamilyMarriageIntent.Route.FIRST_HEIR);var plan=plan(intent);plan.put("schema","xar.ck3.family-planning-proof/v1");
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(plan)));
        var route=plan(intent);route.put("selected_step",FamilyMarriageIntent.Route.CHILD_DEFAULT.step());
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(route)));
    }
    @Test void publicPairIsInTheCanonicalStepAndKeepsNoInventedExtraFields() {
        var intent=new RulerMarriageIntent("101-202",101,202,Optional.empty());var plan=ruler(intent);
        assertEquals(StrictJson.object(),StrictJson.parse(FamilyMarriageNativeRequests.fields(intent,app(plan)).bytes()));
        var changed=ruler(intent);assertInstanceOf(ArrayNode.class,changed.get("marriage_choices").withArray("arrange_marriage_choices")).removeAll();
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(changed)));
        var duplicate=ruler(intent);var rows=assertInstanceOf(ArrayNode.class,duplicate.get("marriage_choices").withArray("arrange_marriage_choices"));rows.add(rows.get(0).deepCopy());
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageNativeRequests.fields(intent,app(duplicate)));
    }
    private static ObjectNode ruler(RulerMarriageIntent intent) {
        var n=StrictJson.object().put("schema",FamilyMarriageNativeRequests.RULER_PLAN_SCHEMA).put("selected_step",intent.step());
        var row=n.putObject("marriage_choice").put("choice_id",intent.choiceId()).put("played_character_id",101).put("candidate_character_id",202);
        n.putObject("marriage_choices").put("query_sequence",7).putArray("arrange_marriage_choices").add(row.deepCopy());return n;
    }
    private static Obj app(JsonNode value){return DriverJson.object(StrictJson.canonical(value),DriverJson.MAX_NATIVE_BYTES);}
}
