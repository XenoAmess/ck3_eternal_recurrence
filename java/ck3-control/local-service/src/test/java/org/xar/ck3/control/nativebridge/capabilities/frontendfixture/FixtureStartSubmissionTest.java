package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual old producer receipts enter the one current strict Java decoder; no receipt creates live permission. */
final class FixtureStartSubmissionTest {
    private static JsonNode oracle()throws IOException {
        try(var input=FixtureStartSubmissionTest.class.getResourceAsStream("/frontend-fixture/python-producer-oracle04.json")) {
            assertNotNull(input,"original real producer oracle is mandatory");return StrictJson.parse(input.readAllBytes(),1<<20);
        }
    }
    @Test void allThreeActualOriginalProducersRoundtripIncludingExplicitNullAndScenarioModel()throws Exception {
        int count=0;
        for(JsonNode row:oracle().get("submissions")) {
            JsonNode original=row.get("receipt");var result=FixtureStartSubmission.fromJson(original);
            assertArrayEquals(StrictJson.canonical(original,1<<20),StrictJson.canonical(result.toJson(),1<<20));assertFalse(result.postconditionVerified());assertFalse(result.fixtureTargetIdentityProven());
            assertEquals(result,FixtureStartSubmission.fromJson(StrictJson.parse(StrictJson.canonical(result.toJson(),1<<20),1<<20)));count++;
        }
        assertEquals(3,count);
    }
    @Test void missingNullWrongTypesAndClaimedPostSuccessAreRejectedByRealConsumer()throws Exception {
        ObjectNode original=(ObjectNode)oracle().get("submissions").get(0).get("receipt");
        for(String key:List.of("schema_version","accepted","binding","policy_binding","before","selected_candidate","acknowledgement","selection_acknowledgement")) {
            ObjectNode missing=original.deepCopy();missing.remove(key);assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(missing),key);
            if(!key.equals("selection_acknowledgement")){ObjectNode nil=original.deepCopy();nil.putNull(key);assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(nil),key);}
        }
        for(String key:List.of("postcondition_verified","fixture_target_identity_proven","uses_ocr","uses_keyboard","uses_mouse")) {
            ObjectNode claimed=original.deepCopy();claimed.put(key,true);assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(claimed),key);
        }
        ObjectNode bool=original.deepCopy();bool.put("schema_version",true);assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(bool));
        ObjectNode real=original.deepCopy();((ObjectNode)real.get("binding")).put("connection_generation",2.0);assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(real));
        ObjectNode zero=original.deepCopy();((ObjectNode)zero.get("binding")).put("bridge_pid",0);assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(zero));
        ObjectNode extra=original.deepCopy();extra.put("allow_retry",true);assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(extra));
    }
    @Test void scenarioCannotCrossProfileTargetBuildClaimOrStartPrimitive()throws Exception {
        ObjectNode original=(ObjectNode)oracle().get("submissions").get(2).get("receipt");
        for(String key:List.of("profile_id","requested_character_name_key")) {
            ObjectNode bad=original.deepCopy();bad.put(key,"other");assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(bad));
        }
        ObjectNode wrong=original.deepCopy();((ObjectNode)wrong.get("acknowledgement")).put("step","activate-frontend-start-selected-bookmark-v1");
        assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(wrong));
        ObjectNode target=original.deepCopy();((ObjectNode)((ObjectNode)target.get("policy_binding")).get("frontend_target")).put("start_date_raw",true);
        assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(target));
        ObjectNode mixed=original.deepCopy();mixed.set("policy_binding",oracle().get("submissions").get(0).get("receipt").get("policy_binding"));
        assertThrows(IllegalArgumentException.class,()->FixtureStartSubmission.fromJson(mixed));
    }
    @Test void originalUnknownResultsNeverRepeatSetterOrStartAcrossSameAndReconnectedDriver()throws Exception {
        int cases=0;
        for(JsonNode row:oracle().get("unknown_no_replay")) {
            Set<String> writes=new HashSet<>();for(JsonNode call:row.get("calls"))if(!call.asText().startsWith("probe-"))assertTrue(writes.add(call.asText()),"old real producer repeated a mutation");
            assertTrue(row.get("replacement_calls").isEmpty());assertEquals("FileExistsError",row.get("errors").get(2).asText());cases++;
        }
        assertEquals(5,cases);
    }
    @Test void nativeSelectedDiagnosticFieldsAreRetainedAcrossRealSerde()throws Exception {
        ObjectNode original=(ObjectNode)oracle().get("submissions").get(0).get("receipt").deepCopy();
        ObjectNode selected=(ObjectNode)original.get("selected_candidate");selected.put("step","query-frontend-selected-1066-feudal-candidate-v1");
        selected.put("accepted",true);selected.put("route","bookmarks");selected.put("query_sequence",7);selected.put("backend_id","native-headless");
        assertArrayEquals(StrictJson.canonical(original,1<<20),StrictJson.canonical(FixtureStartSubmission.fromJson(original).toJson(),1<<20));
    }
    @Test void actualWireWhitespaceDoesNotChangeEmbeddedJsonDomainDuringPersistence()throws Exception {
        var source=FixtureStartSubmission.fromJson(oracle().get("submissions").get(2).get("receipt"));
        var selected=source.selectedCandidate();
        var actualSelected=new FixtureStartSubmission.Selected(selected.kind(),selected.bookmarkGroupKey(),selected.bookmarkKey(),selected.characterNameKey(),
                selected.governmentKey(),selected.startDateRaw(),selected.nativeModel().map(FixtureStartSubmissionTest::spaced),selected.diagnostics());
        var actual=new FixtureStartSubmission(source.kind(),source.binding(),source.policyBinding(),spaced(source.before()),actualSelected,
                source.bookmarkAcknowledgement().map(FixtureStartSubmissionTest::spaced),source.selectionAcknowledgement().map(FixtureStartSubmissionTest::spaced),spaced(source.acknowledgement()));
        assertEquals(source,actual);assertEquals(actual,FixtureStartSubmission.fromJson(StrictJson.parse(StrictJson.canonical(actual.toJson(),1<<20),1<<20)));
    }
    private static org.xar.ck3.control.application.action.RawJson spaced(org.xar.ck3.control.application.action.RawJson raw) {
        return new org.xar.ck3.control.application.action.RawJson((" \n"+new String(raw.bytes(),StandardCharsets.UTF_8)+"\n ").getBytes(StandardCharsets.UTF_8));
    }
}
