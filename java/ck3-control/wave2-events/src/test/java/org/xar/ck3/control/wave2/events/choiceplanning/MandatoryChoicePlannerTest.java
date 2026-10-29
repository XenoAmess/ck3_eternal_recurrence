package org.xar.ck3.control.wave2.events.choiceplanning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningModel.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

final class MandatoryChoicePlannerTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @TestFactory
    Stream<DynamicTest> originalPlannerProducerGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.java-choice-planning-golden/v1", golden.path("schema").textValue());
        assertEquals(20, golden.path("cases").size());
        return StreamSupport.stream(golden.path("cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
                    byte[] actual = ChoicePlanningJson.plan(JSON.writeValueAsBytes(row.get("request")));
                    if (Set.of("actual_native_catalogue_order","different_instance_not_prior_instance","nested_auto_turn_query").contains(row.path("name").textValue())) {
                        // Preserve the original golden; the user now requires the first displayed disabled row to block.
                        JsonNode blocked=JSON.readTree(actual);
                        assertEquals("first_displayed_native_choice_disabled",blocked.path("reason").textValue());
                        assertTrue(blocked.path("selected_step").isNull());
                        assertEquals(row.path("output").get("policy"),blocked.get("policy"));
                        assertEquals("unknown_mandatory_choice_unavailable",blocked.path("phase").textValue());
                        var decision=blocked.path("mandatory_choice_decision");
                        assertEquals("mechanism_unavailable",decision.path("status").textValue());
                        assertTrue(decision.path("action_token").isNull());assertTrue(decision.path("selected_choice_id").isNull());
                        for(String field:java.util.List.of("choices","blocking_proof","frame_binding","duplicates_removed","excluded","sort_order","window_id","window_type","material_effects_verified"))
                            assertEquals(row.path("output").path("mandatory_choice_decision").path("evidence").get(field),decision.path("evidence").get(field),field);
                        var input=ChoicePlanningJson.decode(JSON.writeValueAsBytes(row.get("request")));
                        var original=input.commands().stream().flatMap(value->value.query().stream()).reduce((a,b)->b).orElseThrow();
                        assertEquals(row.path("output").path("unknown_mandatory_choice_v1").get("native_query_receipt"),JSON.readTree(original.original().json()));
                        assertEquals(row.path("output").path("unknown_mandatory_choice_v1").get("native_window"),JSON.readTree(original.window().orElseThrow().original().json()));
                    } else assertEquals(row.get("output"), JSON.readTree(actual), "unchanged real legacy planner result");
                }));
    }

    @Test
    void boundConsumerPortConsumesRealSelectorAndNeverExposesArbitrarySteps() throws IOException {
        AtomicInteger calls = new AtomicInteger();
        ChoicePlanningPort concrete = new MandatoryChoicePlanner();
        ChoicePlanningPort consumer = input -> { calls.incrementAndGet(); return concrete.plan(input); };
        ObjectNode request = request("actual_native_catalogue_order");
        JsonNode result = JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(request), consumer));
        assertEquals(1, calls.get());
        assertEquals(PublicStep.SELECT.wire(), result.path("selected_step").textValue());
        assertEquals("first-enabled", result.path("unknown_mandatory_choice_v1").path("selection").path("choice_id").textValue());
        assertEquals(Set.of("query-mandatory-choice-v1", "select-mandatory-choice-v1"),
                Set.of(PublicStep.QUERY.wire(), PublicStep.SELECT.wire()));
        Proposal proposal = (Proposal) concrete.plan(ChoicePlanningJson.decode(JSON.writeValueAsBytes(request)));
        assertFalse(proposal.dispatchAttempted()); assertFalse(proposal.replayAllowed()); assertFalse(proposal.materialEffectsVerified());
    }

    @Test
    void malformedWrapperAndActualIntegerTokensCannotBecomeRecommendations() throws IOException {
        ObjectNode missing = request("actual_native_catalogue_order"); missing.remove("commands");
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(JSON.writeValueAsBytes(missing)));
        ObjectNode unknown = request("actual_native_catalogue_order"); unknown.put("native_admitted", true);
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(JSON.writeValueAsBytes(unknown)));
        ObjectNode wrongHistory = request("actual_native_catalogue_order"); wrongHistory.set("commands", JSON.createObjectNode());
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(JSON.writeValueAsBytes(wrongHistory)));
        ObjectNode malformedClaim = request("pending_same_instance_no_second_token");
        ((ObjectNode) malformedClaim.path("commands").get(0).path("result").get("auto_turn")).put("status", true);
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(JSON.writeValueAsBytes(malformedClaim)),
                "a bindable original claim cannot disappear behind a wrong-type status");
        for (String token : new String[] {"true", "1.0", "\"1\""}) {
            String serialized = JSON.writeValueAsString(request("actual_native_catalogue_order"));
            String wrong = serialized.replace("\"queried_native_revision\":100", "\"queried_native_revision\":" + token);
            assertNotEquals(serialized, wrong, "send the original wrong JSON token");
            assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(wrong.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test
    void duplicateKeysTrailingValuesMalformedUtf8AndNonfiniteGeometryReject() throws IOException {
        String input = JSON.writeValueAsString(request("actual_native_catalogue_order"));
        byte[] duplicate = ("{\"schema\":\"duplicate\"," + input.substring(1)).getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(duplicate));
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode((input + " null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(new byte[] {(byte) 0xc3, 0x28}));
        String infinite = input.replace("\"top\":30", "\"top\":1e400");
        assertNotEquals(input, infinite);
        assertThrows(IllegalArgumentException.class, () -> ChoicePlanningJson.decode(infinite.getBytes(StandardCharsets.UTF_8)));
    }

    @Test
    void sdkExtensionContainersAreProjectedRatherThanExactRejected() throws IOException {
        ObjectNode input = request("actual_native_catalogue_order");
        ObjectNode snapshot = (ObjectNode) input.get("snapshot"); snapshot.put("unrelated_sdk_extension", "retained by owning SDK");
        ((ObjectNode) snapshot.get("diagnostics")).put("bridge_version", "future-compatible-container-field");
        JsonNode result = JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(input)));
        assertEquals(PublicStep.SELECT.wire(), result.path("selected_step").textValue());
    }

    @Test
    void typedSameRootFallbackCannotBorrowChangedProvenanceReadinessOrIdentity() throws IOException {
        for (String mutation : new String[] {"backend", "ready", "options", "instance", "revision"}) {
            ObjectNode input = request("actual_p09_same_root_unavailable_event");
            ObjectNode result = (ObjectNode) ((ArrayNode) input.get("commands")).get(0).path("result").path("auto_turn").get("result");
            ObjectNode context = (ObjectNode) result.get("current_event_window_context");
            switch (mutation) {
                case "backend" -> ((ObjectNode) context.get("provenance")).put("backend_id", "unverified-new-build");
                case "ready" -> ((ObjectNode) context.get("readiness")).put("option_presentation_ready", true);
                case "options" -> context.set("options", JSON.createArrayNode());
                case "instance" -> context.put("current_event_instance_id", 54);
                case "revision" -> result.put("queried_native_revision", 616);
                default -> throw new IllegalStateException(mutation);
            }
            assertTrue(JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(input))).isNull(), mutation);
        }
    }

    @Test
    void sameEpisodePendingHoldsWhileOtherEpisodeDoesNotBorrowUnknownClaim() throws IOException {
        ObjectNode request = request("pending_same_instance_no_second_token");
        JsonNode held = JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(request)));
        assertEquals(Phase.PENDING_VERIFICATION.wire(), held.path("phase").textValue());
        assertTrue(held.path("selected_step").isNull());
        ObjectNode source = (ObjectNode) request.path("commands").get(0).path("result").path("auto_turn")
                .path("plan").path("unknown_mandatory_choice_v1").get("frame_binding");
        source.put("episode_run_id", "another-episode");
        JsonNode fresh = JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(request)));
        assertEquals(PublicStep.SELECT.wire(), fresh.path("selected_step").textValue());
    }

    @Test
    void immutableProjectionRetainsSourceQueryEpisodeAndActualRawReceipt() throws IOException {
        ObjectNode request = request("actual_p09_same_root_unavailable_event");
        byte[] raw = JSON.writeValueAsBytes(request); PlanningInput input = ChoicePlanningJson.decode(raw);
        raw[0] = 0; assertThrows(UnsupportedOperationException.class, () -> input.commands().clear());
        Proposal result = (Proposal) new MandatoryChoicePlanner().plan(input);
        assertTrue(result.typedEventFallback());
        assertEquals("native-1128-offline", result.query().orElseThrow().window().orElseThrow().frame().episodeRunId());
        JsonNode original = JSON.readTree(result.query().orElseThrow().original().json());
        assertEquals(request.path("commands").get(1).get("result"), original);
        assertEquals("event_saved_scope_invalid", JSON.readTree(result.typedEventContext().orElseThrow().json()).path("unavailable_reason").textValue());
    }

    @Test
    void independentOverlayRequiresPositiveTypedEventIdentityAndExactRootRelation() throws IOException {
        ObjectNode input = request("actual_native_catalogue_order");
        ObjectNode snapshot = (ObjectNode) input.get("snapshot"); snapshot.putObject("active_event").put("instance_id", 9);
        ((ObjectNode) snapshot.get("top_exclusive_modal_choice_hint")).put("opaque_root_id", "modal-instance-9");
        ObjectNode window = (ObjectNode) input.path("commands").get(0).path("result").get("mandatory_choice");
        ObjectNode relation = window.putObject("typed_window_relation");
        relation.put("status", "independent_top_modal"); relation.put("owner_verified", true);
        relation.put("source", "exact_12004_event_controller_gui_root_and_owner_tree"); relation.put("typed_domain", "event");
        relation.put("typed_window_instance_id", 9); relation.put("top_opaque_root_id", "modal-instance-9");
        relation.put("typed_opaque_root_id", "different-typed-event-root");
        assertEquals(PublicStep.SELECT.wire(), JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(input))).path("selected_step").textValue());
        ((ObjectNode) snapshot.get("active_event")).put("instance_id", 0); relation.put("typed_window_instance_id", 0);
        assertTrue(JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(input))).isNull());
    }

    private static JsonNode golden() throws IOException {
        try (InputStream resource = MandatoryChoicePlannerTest.class.getResourceAsStream("/choiceplanning/producer-golden-v1.json.gz")) {
            if (resource == null) { throw new IOException("committed actual producer golden missing; capture not executed"); }
            try (InputStream input = new GZIPInputStream(resource)) {
                byte[] raw = input.readNBytes(102_401);
                if (raw.length > 102_400) { throw new IOException("golden decompression byte budget exceeded"); }
                String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
                if (!"21d83c7cbfba402360868f963c2ac1d5357a22c1b3ba850a7fe6218c5f5b9f02".equals(sha)) {
                    throw new IOException("actual producer golden byte identity changed");
                }
                return JSON.readTree(raw);
            } catch (GeneralSecurityException error) { throw new IOException("SHA-256 unavailable", error); }
        }
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (name.equals(row.path("name").textValue())) {
                ObjectNode request=(ObjectNode)row.get("request").deepCopy();
                // Unrelated orchestration tests retain an enabled first display; exact old inputs are tested above.
                for(JsonNode command:request.path("commands"))for(JsonNode choice:command.path("result").path("mandatory_choice").path("choices"))
                    if("disabled".equals(choice.path("choice_id").asText()))((ObjectNode)choice).put("visible",false);
                return request;
            }
        }
        throw new IOException("missing actual producer case " + name);
    }
}
