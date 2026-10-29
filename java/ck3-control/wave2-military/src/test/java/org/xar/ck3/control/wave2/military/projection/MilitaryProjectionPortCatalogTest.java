package org.xar.ck3.control.wave2.military.projection;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;

/** Existing original vectors enter the registered domain codecs through the same raw-byte ABI as Quarkus. */
final class MilitaryProjectionPortCatalogTest {
    private static final Set<ProjectionOperation> COALITION_ROLES = Set.of(
            ProjectionOperation.MILITARY_DECLARATION_CATALOGUE,
            ProjectionOperation.MILITARY_HOLY_COST_SELECTED,
            ProjectionOperation.MILITARY_HOLY_COST_NORMALIZE,
            ProjectionOperation.MILITARY_COALITION_NORMALIZE,
            ProjectionOperation.MILITARY_COALITION_RISK,
            ProjectionOperation.MILITARY_PREWAR_ADMISSION);

    @Test void standardDiscoveryRegistersAllSixActualTypedRolesAtTheirExistingLimits() {
        ProjectionDispatcher dispatcher = dispatcher();
        var coalitionProfiles = dispatcher.profiles().stream()
                .filter(profile -> COALITION_ROLES.contains(profile.operation())).toList();
        assertEquals(6, coalitionProfiles.size());
        for (var profile : coalitionProfiles) {
            assertEquals(65_536, profile.inputMaximumBytes());
            assertEquals(65_536, profile.outputMaximumBytes());
        }
    }

    @Test void originalProducerVectorsCrossEveryRegisteredDomainApplication() throws IOException {
        ProjectionDispatcher dispatcher = dispatcher();
        int checks = 0;
        for (JsonNode row : fixture("/declarationcontract/original-producer-golden01.json", 32_768).path("catalogues")) {
            byte[] raw = ("{\"value\":" + row.get("raw_input_json").textValue() + "}").getBytes(StandardCharsets.UTF_8);
            ProjectionResult result = dispatch(dispatcher, ProjectionOperation.MILITARY_DECLARATION_CATALOGUE, raw);
            if (row.path("expected").path("accepted").booleanValue()) {
                equal(row.path("expected").get("rows"), succeeded(result));
            } else assertInstanceOf(ProjectionResult.Rejected.class, result);
            checks++;
        }
        JsonNode holy = fixture("/holycost/original-producer-golden01.json", 65_536);
        for (JsonNode row : holy.path("cases")) {
            if (!row.path("expected").path("java_accepted").booleanValue()) continue;
            ObjectNode input = holy.path("base").deepCopy();
            for (JsonNode edit : row.path("edits")) apply(input, edit);
            ObjectNode payload = StrictJson.object();
            payload.set("snapshot", input.get("snapshot")); payload.set("declaration_id", input.get("declaration_id"));
            ProjectionOperation operation;
            if (row.path("mode").textValue().equals("select")) operation = ProjectionOperation.MILITARY_HOLY_COST_SELECTED;
            else {
                operation = ProjectionOperation.MILITARY_HOLY_COST_NORMALIZE;
                payload.set("value", input.get("context")); payload.set("selected_declaration", input.get("selected"));
            }
            equal(row.path("expected").get("output"), succeeded(dispatch(dispatcher, operation, StrictJson.canonical(payload))));
            checks++;
        }
        JsonNode coalition = fixture("/coalition/original-producer-golden01.json", 81_920);
        for (JsonNode row : coalition.path("cases")) {
            if (!row.path("expected").path("accepted").booleanValue()) continue;
            ObjectNode input = coalition.path("base").deepCopy();
            for (JsonNode edit : row.path("edits")) apply(input, edit);
            ObjectNode payload = StrictJson.object();
            payload.set("value", input.get("domain")); payload.set("snapshot", input.get("snapshot"));
            payload.set("expected_declaration", input.get("declaration"));
            payload.set("expected_request_binding", input.get("receipt"));
            payload.set("expected_request_id", input.get("request_id"));
            payload.set("expected_capture_epoch", input.get("expected_capture_epoch"));
            if (row.path("expected").has("normalized")) {
                equal(row.path("expected").get("normalized"), succeeded(dispatch(dispatcher,
                        ProjectionOperation.MILITARY_COALITION_NORMALIZE, StrictJson.canonical(payload))));
                checks++;
            }
            payload.set("policy", input.get("policy"));
            equal(row.path("expected").get("risk"), succeeded(dispatch(dispatcher,
                    ProjectionOperation.MILITARY_COALITION_RISK, StrictJson.canonical(payload))));
            checks++;
        }
        JsonNode prewar = fixture("/prewaradmission/original-producer-golden.json", 65_536);
        ObjectNode base = prewar.path("base_request").deepCopy();
        base.remove("schema");
        ObjectNode expected = prewar.path("cases").get(0).path("expected").deepCopy();
        equal(expected, succeeded(dispatch(dispatcher, ProjectionOperation.MILITARY_PREWAR_ADMISSION, StrictJson.canonical(base))));
        ObjectNode snapshot = (ObjectNode) base.get("snapshot");
        snapshot.put("unrelated_rich_sdk_extension", "retained by actual consumer outside the explicit Java projection");
        ((ObjectNode) snapshot.get("played_character")).put("unrelated_character_name", "original SDK data");
        equal(expected, succeeded(dispatch(dispatcher, ProjectionOperation.MILITARY_PREWAR_ADMISSION, StrictJson.canonical(base))));
        checks += 2;
        assertTrue(checks >= 90, "actual original producer branches must execute all six ports");
    }

    @Test void rawFloatBoolAndUnknownDoNotAcquireReceiptOrReplayAuthority() throws IOException {
        ProjectionDispatcher dispatcher = dispatcher();
        JsonNode prewar = fixture("/prewaradmission/original-producer-golden.json", 65_536);
        ObjectNode input = prewar.path("base_request").deepCopy(); input.remove("schema");
        String original = new String(StrictJson.canonical(input), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1500.0", "1.5e3", "\"1500\"")) {
            String raw = original.replace("\"actor_lower_soldiers\":1500", "\"actor_lower_soldiers\":" + token);
            assertNotEquals(original, raw);
            JsonNode result = succeeded(dispatch(dispatcher, ProjectionOperation.MILITARY_PREWAR_ADMISSION, raw.getBytes(StandardCharsets.UTF_8)));
            assertFalse(result.path("declare_admitted").booleanValue());
            assertEquals("force_coalition_coverage_invalid", result.path("reason").textValue());
            assertTrue(result.get("required_prewar_force_coalition_query").isNull());
        }
        ObjectNode envelope = (ObjectNode) input.path("snapshot").get("prewar_force_coalition_coverage_v2_query");
        envelope.put("status", "partial");
        JsonNode result = succeeded(dispatch(dispatcher, ProjectionOperation.MILITARY_PREWAR_ADMISSION, StrictJson.canonical(input)));
        assertFalse(result.path("declare_admitted").booleanValue());
        assertTrue(result.get("required_prewar_force_coalition_query").isNull());
        for (var profile : dispatcher.profiles().stream()
                .filter(profile -> COALITION_ROLES.contains(profile.operation())).toList()) {
            assertInstanceOf(ProjectionResult.Rejected.class,
                    dispatch(dispatcher, profile.operation(), "{}".getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test void completeModuleDiscoveryHasExactlyTheDeclaredRolesAndPreservesExceptionalCaps() {
        ProjectionDispatcher dispatcher = dispatcher();
        Set<ProjectionOperation> expected = Set.of(
                ProjectionOperation.MILITARY_DECLARATION_CATALOGUE,
                ProjectionOperation.MILITARY_HOLY_COST_SELECTED,
                ProjectionOperation.MILITARY_HOLY_COST_NORMALIZE,
                ProjectionOperation.MILITARY_COALITION_NORMALIZE,
                ProjectionOperation.MILITARY_COALITION_RISK,
                ProjectionOperation.MILITARY_PREWAR_ADMISSION,
                ProjectionOperation.MILITARY_ARMY_INVENTORY,
                ProjectionOperation.MILITARY_ROUTE_WINDOW,
                ProjectionOperation.MILITARY_ROUTE_STEP,
                ProjectionOperation.MILITARY_ACTUAL_SCOPE,
                ProjectionOperation.MILITARY_ACTUAL_QUERY,
                ProjectionOperation.MILITARY_UPDATER_WRITES,
                ProjectionOperation.MILITARY_STOCK_SUPPLY,
                ProjectionOperation.MILITARY_NEXT_FLEET_RATE,
                ProjectionOperation.MILITARY_CALLBACK_SUPPLY_RISK,
                ProjectionOperation.MILITARY_CALLBACK_SOLDIER_EFFECTS,
                ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE,
                ProjectionOperation.MILITARY_COMBAT_ROLES_PROJECT,
                ProjectionOperation.MILITARY_COMMANDER_QUALITY_PROPOSE,
                ProjectionOperation.MILITARY_COMMANDER_QUALITY_ADMIT_OBSERVED,
                ProjectionOperation.MILITARY_COMMANDER_QUALITY_PLAN,
                ProjectionOperation.MILITARY_COMMANDER_QUALITY_PLAN_NEXT,
                ProjectionOperation.MILITARY_WAR_RESULTS_PLAN,
                ProjectionOperation.MILITARY_WAR_OVERVIEW_PLAN,
                ProjectionOperation.MILITARY_WAR_RESULTS_PRESENCE,
                ProjectionOperation.MILITARY_WAR_OVERVIEW_PRESENCE,
                ProjectionOperation.MILITARY_WAR_RESULTS_QUERY_FRAME,
                ProjectionOperation.MILITARY_WAR_OVERVIEW_QUERY_FRAME,
                ProjectionOperation.MILITARY_WAR_RESULTS_NORMALIZE,
                ProjectionOperation.MILITARY_WAR_RESULTS_SOURCE_OWNER,
                ProjectionOperation.MILITARY_DEJURE_BASELINE_NORMALIZE,
                ProjectionOperation.MILITARY_WAR_EXIT_TERMS_NORMALIZE,
                ProjectionOperation.MILITARY_SUPPLY_CONSUMER,
                ProjectionOperation.MILITARY_HOLY_REINFORCEMENT,
                ProjectionOperation.MILITARY_HOLY_HIRE,
                ProjectionOperation.MILITARY_COUNTY_ENTRY_NORMALIZE,
                ProjectionOperation.MILITARY_CURRENT_MOVEMENT_NORMALIZE,
                ProjectionOperation.MILITARY_PRESTORE_PROJECT,
                ProjectionOperation.MILITARY_DISEMBARK_NORMALIZE,
                ProjectionOperation.MILITARY_DISEMBARK_PROJECT,
                ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS,
                ProjectionOperation.MILITARY_DAILY_QUEUE_TRANSFER,
                ProjectionOperation.MILITARY_ARMY_SELECTOR,
                ProjectionOperation.MILITARY_CONSUMER_TRANSFER);
        assertEquals(expected, dispatcher.profiles().stream().map(profile -> profile.operation())
                .collect(Collectors.toUnmodifiableSet()));
        assertEquals(44, dispatcher.profiles().size());
        var queue = dispatcher.profiles().stream()
                .filter(profile -> profile.operation() == ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS)
                .findFirst().orElseThrow();
        assertEquals(65_546, queue.inputMaximumBytes());
        assertEquals(65_536, queue.outputMaximumBytes());
        var transfer = dispatcher.profiles().stream()
                .filter(profile -> profile.operation() == ProjectionOperation.MILITARY_CONSUMER_TRANSFER)
                .findFirst().orElseThrow();
        assertEquals(131_072, transfer.inputMaximumBytes());
        assertEquals(65_536, transfer.outputMaximumBytes());
    }

    private static ProjectionDispatcher dispatcher() {
        List<ServiceLoader.Provider<ProjectionPortCatalog>> providers = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type() == MilitaryProjectionPortCatalog.class).toList();
        assertEquals(1, providers.size(), "military coordinator must merge this provider once into the existing descriptor");
        return ProjectionDispatcher.fromCatalogs(List.of(providers.getFirst().get()));
    }
    private static ProjectionResult dispatch(ProjectionDispatcher dispatcher, ProjectionOperation operation, byte[] payload) {
        return dispatcher.dispatch(ProjectionWire.encodeCall(new ProjectionCall(
                new ProjectionCall.Identity("military-original-vector", operation),
                ProjectionJson.object(payload, ProjectionJson.MAX_BYTES))));
    }
    private static JsonNode succeeded(ProjectionResult result) {
        return StrictJson.parse(assertInstanceOf(ProjectionResult.Succeeded.class, result).result().bytes());
    }
    private static void equal(JsonNode expected, JsonNode actual) {
        assertEquals(new String(StrictJson.canonical(expected), StandardCharsets.UTF_8),
                new String(StrictJson.canonical(actual), StandardCharsets.UTF_8));
    }
    private static JsonNode fixture(String path, int maximum) throws IOException {
        try (InputStream input = MilitaryProjectionPortCatalogTest.class.getResourceAsStream(path)) {
            assertNotNull(input, "mandatory actual original producer bytes " + path);
            byte[] bytes = input.readNBytes(maximum + 1);
            assertTrue(bytes.length <= maximum);
            return StrictJson.parse(bytes, maximum);
        }
    }
    private static void apply(ObjectNode request, JsonNode edit) {
        JsonNode path = edit.get("path"); JsonNode parent = request;
        for (int index = 0; index < path.size() - 1; index++) {
            JsonNode key = path.get(index); parent = key.isTextual() ? parent.get(key.textValue()) : parent.get(key.intValue());
        }
        JsonNode key = path.get(path.size() - 1);
        if (edit.path("remove").asBoolean()) {
            if (parent instanceof ObjectNode object) object.remove(key.textValue()); else ((ArrayNode) parent).remove(key.intValue());
        } else {
            JsonNode value = StrictJson.parse(edit.get("value_json").textValue().getBytes(StandardCharsets.UTF_8));
            if (parent instanceof ObjectNode object) object.set(key.textValue(), value); else ((ArrayNode) parent).set(key.intValue(), value);
        }
    }
}

