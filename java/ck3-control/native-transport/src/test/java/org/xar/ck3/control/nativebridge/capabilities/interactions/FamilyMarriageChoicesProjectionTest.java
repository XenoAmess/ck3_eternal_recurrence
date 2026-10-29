package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Synthetic wire boundary cases; full actual coordinator/typed-to-family projection is Root integration work. */
final class FamilyMarriageChoicesProjectionTest {
    private static Context context() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z"); var source=new G2Source("synthetic-ruler-machine",now.toString(),"1.20.0.4",new ExactRef("synthetic/source",1,"a".repeat(64)));
        var f=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(7),BigInteger.valueOf(53146848)),"native:7",BigInteger.valueOf(56),"synthetic-text");
        return new Context(new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),f,1),
                source,"synthetic-ruler-session",BigInteger.TWO,Build.CROZIER4,now.plusSeconds(30),new ControlFrame(true,true,true,1,19L,101,"synthetic-ruler-episode",false,null,null,List.of()));
    }
    private static ObjectNode packet() {
        var n=InteractionJson.F.objectNode().put("step",FamilyMarriageChoicesProjection.STEP).put("accepted",true).put("status","available").put("query_sequence",11);
        n.putArray("arrange_marriage_choices").addObject().put("choice_id","101-202").put("played_character_id",101).put("candidate_character_id",202);
        var d=n.putObject("arrange_marriage_diagnostics").put("storage_capacity",2).put("slots_scanned",2).put("empty_slots",0).put("live_candidates",2)
                .put("dead_candidates",0).put("self_candidates",0).put("generation_mismatch_candidates",0).put("contexts_constructed",2)
                .put("context_construct_failures",0).put("native_validate_true",1).put("native_validate_false",1);
        d.putArray("validation_false_samples").addObject().put("slot_index",1).put("candidate_character_id",303).put("actor_character_id",101)
                .put("recipient_character_id",303).put("secondary_actor_character_id",101).put("secondary_recipient_character_id",303).put("intermediary_character_id",-1);
        return n;
    }
    @Test void completeDiagnosticsAndCanonicalChoiceSurviveTheTypedReadProjection() {
        var decoded=FamilyMarriageChoicesProjection.decodeNative(raw(packet()),context());
        assertEquals(new MarriageChoice("101-202",101,202),decoded.typed().choices().getFirst());
        assertEquals(2,decoded.diagnostics().slotsScanned()); assertEquals(1,decoded.diagnostics().nativeValidateFalse());
        assertEquals(-1,decoded.diagnostics().validationFalseSamples().getFirst().intermediary());
        assertEquals(decoded,FamilyMarriageChoicesProjection.decodeNative(decoded.original(),context()));
    }
    @Test void emptyCompleteNativeEnumerationIsDifferentFromUnavailableOrMissingRows() {
        var n=packet(); n.putArray("arrange_marriage_choices");
        ((ObjectNode)n.get("arrange_marriage_diagnostics")).put("native_validate_true",0).put("native_validate_false",2);
        assertTrue(FamilyMarriageChoicesProjection.decodeNative(raw(n),context()).choices().isEmpty());
        n.put("status","unavailable"); reject(n);
        n=packet(); n.putNull("arrange_marriage_choices"); reject(n);
        n=packet(); n.remove("arrange_marriage_choices"); reject(n);
    }
    @Test void wrongTypesSourcePairIdentityAndIncompleteEnumerationAreRefused() {
        var n=packet(); choice(n).put("candidate_character_id",true); reject(n);
        n=packet(); choice(n).put("candidate_character_id",202.0); reject(n);
        n=packet(); choice(n).put("played_character_id",102).put("choice_id","102-202"); reject(n);
        n=packet(); choice(n).put("choice_id","101-203"); reject(n);
        n=packet(); ((ObjectNode)n.get("arrange_marriage_diagnostics")).put("slots_scanned",1); reject(n);
        n=packet(); ((ObjectNode)n.get("arrange_marriage_diagnostics")).remove("dead_candidates"); reject(n);
        n=packet(); n.put("postcondition_verified",true); reject(n);
    }
    @Test void duplicatePairsAndDiagnosticSamplesOutsideStorageCannotBeAccepted() {
        var n=packet(); ((com.fasterxml.jackson.databind.node.ArrayNode)n.get("arrange_marriage_choices")).add(choice(n).deepCopy()); reject(n);
        n=packet(); ((ObjectNode)n.get("arrange_marriage_diagnostics").get("validation_false_samples").get(0)).put("slot_index",2); reject(n);
        n=packet(); choice(n).put("unknown_role",999); reject(n);
    }
    private static ObjectNode choice(ObjectNode n) { return (ObjectNode)n.get("arrange_marriage_choices").get(0); }
    private static RawJson raw(JsonNode n) { return new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)); }
    private static void reject(ObjectNode n) { assertThrows(IllegalArgumentException.class,()->FamilyMarriageChoicesProjection.decodeNative(raw(n),context())); }
}
