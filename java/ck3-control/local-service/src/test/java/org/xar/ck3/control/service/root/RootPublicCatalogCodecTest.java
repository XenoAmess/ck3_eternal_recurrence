package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ResourceDescriptor;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.Arguments;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.Presence;
import org.xar.ck3.control.application.planning.sway.SwayPublicCodec;
import org.xar.ck3.control.application.planning.sway.SwayObservationReads;
import org.xar.ck3.control.service.mcp.MarriageChoicesPublicCodec;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCallCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Original captured declarations/descriptors feed the actual runtime producer and strict reader. */
final class RootPublicCatalogCodecTest {
    private static RawJson resource(String name) throws Exception {
        try (var input = RootPublicCatalogCodecTest.class.getResourceAsStream(name)) {
            assertNotNull(input, "required original public source fixture is absent"); return new RawJson(input.readAllBytes());
        }
    }
    private static RootPublicCatalogCodec.PublicCatalog original() throws Exception {
        var catalog = McpCoverage.readCatalog(resource("/mcp/original-tool-catalog.json"));
        var admission = catalog.declarations().stream().map(value -> new McpCoverage.Decision(value.name(),
                McpCoverage.Admission.UNMIGRATED, value.source(), "actual source fixture remains unmigrated")).toList();
        var tools = new ArrayList<ToolDescriptor>();
        for (JsonNode row : StrictJson.parse(resource("/mcp/original-executable-descriptors.json").bytes()).get("descriptors"))
            tools.add(new ToolDescriptor(row.get("name").textValue(), raw(row)));
        var resources = new ArrayList<ResourceDescriptor>();
        for (JsonNode row : StrictJson.parse(resource("/mcp/original-protocol-golden.json").bytes()).get("resources"))
            resources.add(new ResourceDescriptor(row.get("uri").textValue(), raw(row)));
        return new RootPublicCatalogCodec.PublicCatalog(catalog, admission, tools, resources);
    }
    @Test void actualRuntimeDocumentProducerAndReaderPreserveOriginalDescriptorJsonDomain() throws Exception {
        var original = original(); var tools = new ArrayList<>(original.tools()); var first = tools.getFirst();
        tools.set(0, new ToolDescriptor(first.name(), new RawJson(("\n  " + new String(first.original().bytes(), StandardCharsets.UTF_8) + "\n").getBytes(StandardCharsets.UTF_8))));
        var noncanonical = new RootPublicCatalogCodec.PublicCatalog(original.catalog(), original.admission(), tools, original.resources());
        var documents = RootPublicCatalogCodec.encode(noncanonical); var read = RootPublicCatalogCodec.decode(documents);
        assertTrue(RootPublicCatalogCodec.equivalent(noncanonical, read));
        assertFalse(noncanonical.tools().getFirst().original().equals(read.tools().getFirst().original()));
        assertEquals(noncanonical.catalog(), read.catalog()); assertEquals(noncanonical.admission(), read.admission());
    }
    @Test void originalMissingMethodsRemainExactPreNativeGapsAndNoRegistryBecomesReady() throws Exception {
        var original = original(); var registry = new PublicBindings();
        var products = new RootRuntimePublicCatalog.HandlerProducts(registry, List.of(), List.of(),Optional.empty(),Optional.empty());
        var missing = RootRuntimePublicCatalog.definitionGaps(original, products);
        assertEquals(original.catalog().declarations().size(), missing.size());
        assertTrue(missing.stream().anyMatch(value -> value.identity().equals("ck3_query_vanilla_event_knowledge_v1")));
        assertTrue(registry.coverage().installed().isEmpty()); assertFalse(registry.frozen());
        assertEquals(missing, RootRuntimePublicCatalog.definitionGaps(original, products));
    }
    @Test void admittedOriginalOfflineToolWithoutActualHandlerAndDescriptorStillRefuses() throws Exception {
        var original = original(); String name = "ck3_query_vanilla_event_knowledge_v1";
        var admission = original.admission().stream().map(value -> value.name().equals(name)
                ? new McpCoverage.Decision(name, McpCoverage.Admission.ADMITTED, value.actualAdmissionProducer(), "actual caller needs the complete offline producer") : value).toList();
        var requested = new RootPublicCatalogCodec.PublicCatalog(original.catalog(), admission, original.tools(), original.resources());
        var missing = RootRuntimePublicCatalog.definitionGaps(requested,
                new RootRuntimePublicCatalog.HandlerProducts(new PublicBindings(), List.of(), List.of(),Optional.empty(),Optional.empty()));
        assertTrue(missing.contains(new RootRuntimePublicCatalog.DefinitionGap(name, "actual original descriptor is missing")));
        assertTrue(missing.contains(new RootRuntimePublicCatalog.DefinitionGap(name, "actual typed direct method is missing")));
    }
    @Test void conditionalExclusionMetadataWithoutTheSamePrivateIssuedConfigurationRemainsIncomplete() throws Exception {
        var original=original();var declaration=original.catalog().declarations().stream().filter(value->!value.conditions().isEmpty()).findFirst().orElseThrow();
        var admission=original.admission().stream().map(value->value.name().equals(declaration.name())
                ?new McpCoverage.Decision(value.name(),McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION,value.actualAdmissionProducer(),"a condition label is not a private-issued same-input proof"):value).toList();
        var requested=new RootPublicCatalogCodec.PublicCatalog(original.catalog(),admission,original.tools(),original.resources());
        var registry=new PublicBindings();var products=new RootRuntimePublicCatalog.HandlerProducts(registry,List.of(),List.of(),Optional.empty(),Optional.empty());
        assertTrue(RootRuntimePublicCatalog.definitionGaps(requested,products).stream().anyMatch(value->value.identity().equals(declaration.name())&&value.reason().contains("actual Java configuration producer")));
        assertTrue(registry.coverage().installed().isEmpty());assertFalse(registry.frozen());
    }
    @Test void actualSettlementAdapterIsReservedWhileUnsuppliedControllerActionsRemainGaps() throws Exception {
        var original=original(); var names=java.util.Set.of("ck3_settle_one_life","ck3_start_next_episode","ck3_restore_checkpoint");
        var admission=original.admission().stream().map(value->names.contains(value.name())
                ?new McpCoverage.Decision(value.name(),McpCoverage.Admission.ADMITTED,value.actualAdmissionProducer(),"metadata alone cannot supply the missing original controller or full-width producer") :value).toList();
        var requested=new RootPublicCatalogCodec.PublicCatalog(original.catalog(),admission,original.tools(),original.resources());
        var registry=new PublicBindings();var gaps=RootRuntimePublicCatalog.definitionGaps(requested,
                new RootRuntimePublicCatalog.HandlerProducts(registry,List.of(),List.of(),Optional.empty(),Optional.empty()));
        for(String name:List.of("ck3_start_next_episode","ck3_restore_checkpoint"))
            assertTrue(gaps.contains(new RootRuntimePublicCatalog.DefinitionGap(name,"actual typed service handler is missing")),name);
        assertFalse(gaps.contains(new RootRuntimePublicCatalog.DefinitionGap("ck3_settle_one_life","actual typed service handler is missing")));
        assertTrue(gaps.contains(new RootRuntimePublicCatalog.DefinitionGap("ck3_settle_one_life","actual original descriptor is missing")));
        assertTrue(registry.coverage().installed().isEmpty());assertFalse(registry.frozen());
    }
    @Test void runtimeEntryRejectsWrongMissingAndNonIntegerSourceFieldsAndCannotExcludeUnconditionalTools() throws Exception {
        var original = original(); var encoded = RootPublicCatalogCodec.encode(original);
        for (int variant = 0; variant < 4; variant++) {
            var root = PublicDataJson.object(encoded.admission());
            var decision = (ObjectNode) root.get("decisions").get(0);
            switch (variant) {
                case 0 -> decision.remove("name");
                case 1 -> decision.put("admission", true);
                case 2 -> ((ObjectNode) decision.get("actual_admission_producer")).put("bytes", true);
                case 3 -> decision.put("unexpected_alias", "ignored");
                default -> throw new AssertionError();
            }
            var invalid = new RootPublicCatalogCodec.Documents(encoded.catalog(), raw(root), encoded.tools(), encoded.resources());
            assertThrows(IllegalArgumentException.class, () -> RootPublicCatalogCodec.decode(invalid));
        }
        String unconditional = original.catalog().declarations().stream().filter(value -> value.conditions().isEmpty()).findFirst().orElseThrow().name();
        var excluded = original.admission().stream().map(value -> value.name().equals(unconditional)
                ? new McpCoverage.Decision(value.name(), McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION,
                        value.actualAdmissionProducer(), "a JSON label cannot remove an unconditional original operation") : value).toList();
        assertThrows(IllegalArgumentException.class, () -> new RootPublicCatalogCodec.PublicCatalog(
                original.catalog(), excluded, original.tools(), original.resources()));
    }
    /** Deliberate schema-unit fixtures mirror the pinned Python annotations; these are not a new original capture. */
    @Test void exactSwayDescriptorWidthRulesReachActualConsumerWithoutStringifyingBoundedFields() {
        for (String name : List.of("ck3_finish_active_scheme_sway_private_v1",
                "ck3_query_active_scheme_sway_completion_execution_private_v1",
                "ck3_query_active_scheme_sway_completion_termination_private_v1")) {
            boolean finish = name.contains("finish_");
            ToolDescriptor original = widthFixture(name, false, !finish);
            ToolDescriptor executable = RootPublicCatalogCodec.executableTool(original);
            JsonNode originalTree = StrictJson.parse(original.original().bytes());
            for (JsonNode revision : List.of(token("1"), token("9007199254740991"),
                    token("\"18446744073709551615\""))) {
                var request = StrictJson.object(); request.set("expected_revision", revision);
                request.put("target_character_id", 123).put("scheme_instance_id", 16777217);
                if (finish) request.put("scheme_instance_generation", 1); else request.put("after_sequence", "18446744073709551615");
                executable.validateArguments(arguments(request));
                if (finish) {
                    var actual = SwayPublicCodec.decodeFinish(raw(request));
                    assertEquals(revision.isTextual() ? new BigInteger(revision.textValue()) : revision.bigIntegerValue(), actual.expectedRevision());
                    assertTrue(StrictJson.parse(SwayPublicCodec.encodeFinishRequest(actual).bytes()).get("target_character_id").isIntegralNumber());
                } else {
                    var kind = name.contains("execution") ? SwayObservationReads.Kind.EXECUTION : SwayObservationReads.Kind.TERMINATION;
                    var actual = SwayPublicCodec.decodeJournal(kind, raw(request));
                    assertEquals(new BigInteger("18446744073709551615"), actual.afterSequence());
                    assertTrue(StrictJson.parse(SwayPublicCodec.encodeJournalRequest(actual).bytes()).get("scheme_instance_id").isIntegralNumber());
                }
                if (!finish || revision.isTextual()) assertThrows(IllegalArgumentException.class, () -> original.validateArguments(arguments(request)));
                else original.validateArguments(arguments(request));
            }
            assertEquals(originalTree, StrictJson.parse(original.original().bytes()));
            for (String token : List.of("null", "true", "1.0", "9007199254740992", "\"0\"", "\"01\"", "\"18446744073709551616\"", "\"+1\"", "\"1\\n\"")) {
                var request = StrictJson.object(); request.set("expected_revision", token(token));
                request.put("target_character_id", 123).put("scheme_instance_id", 16777217);
                if (finish) request.put("scheme_instance_generation", 1);
                assertThrows(IllegalArgumentException.class, () -> executable.validateArguments(arguments(request)), token);
            }
        }
    }
    @Test void exactOptionDescriptorKeepsMissingNullAndStringOnlyConsumerContract() {
        var original = widthFixture("ck3_select_event_option", true, false);
        var executable = RootPublicCatalogCodec.executableTool(original);
        for (String json : List.of("{\"option_number\":1}", "{\"option_number\":1,\"expected_revision\":null}",
                "{\"option_number\":1,\"expected_revision\":\"0\"}",
                "{\"option_number\":1,\"expected_revision\":\"18446744073709551615\"}")) {
            var request = raw(token(json)); executable.validateArguments(arguments(token(json)));
            var actual = EventOptionPublicCodec.decode(PublicBindings.present(request));
            assertEquals(token(json), StrictJson.parse(EventOptionPublicCodec.encodeRequest(actual).bytes()));
        }
        for (String token : List.of("1", "true", "1.0", "\"00\"", "\"18446744073709551616\"")) {
            var request = StrictJson.object().put("option_number", 1); request.set("expected_revision", token(token));
            assertThrows(IllegalArgumentException.class, () -> executable.validateArguments(arguments(request)));
        }
    }
    @Test void exactMarriageDescriptorPreservesNullableSafeNumberOrDecimalConsumerAndNoOtherArguments() {
        var executable = RootPublicCatalogCodec.executableTool(widthFixture("ck3_query_arrange_marriage_choices", true, false));
        for (String json : List.of("{}", "{\"expected_revision\":null}", "{\"expected_revision\":0}",
                "{\"expected_revision\":9007199254740991}", "{\"expected_revision\":\"18446744073709551615\"}")) {
            var tree = token(json); executable.validateArguments(arguments(tree));
            var actual = MarriageChoicesPublicCodec.decode(PublicBindings.present(raw(tree)));
            executable.validateArguments(arguments(PublicDataJson.object(MarriageChoicesPublicCodec.encodeRequest(actual))));
        }
        for (String bad : List.of("true", "1.0", "9007199254740992", "\"01\"", "\"-1\"", "\"18446744073709551616\"")) {
            var request = StrictJson.object(); request.set("expected_revision", token(bad));
            assertThrows(IllegalArgumentException.class, () -> executable.validateArguments(arguments(request)));
        }
    }
    @Test void actualSaveRequestConsumerAcceptsPreciselyTheExecutableDescriptorWidthDomain() {
        var executable=RootPublicCatalogCodec.executableTool(widthFixture("ck3_save_checkpoint",true,false));
        for(String json:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":0}",
                "{\"expected_revision\":9007199254740991}","{\"expected_revision\":\"18446744073709551615\"}")) {
            var tree=token(json);executable.validateArguments(arguments(tree));
            var request=CheckpointPublicCodec.decode(PublicBindings.present(raw(tree)));
            var encoded=CheckpointPublicCodec.encodeRequest(request);executable.validateArguments(arguments(PublicDataJson.object(encoded)));
            assertEquals(request,CheckpointPublicCodec.decode(PublicBindings.present(encoded)));
        }
        for(String bad:List.of("true","1.0","9007199254740992","\"01\"","\"-1\"","\"18446744073709551616\"")) {
            var request=StrictJson.object();request.set("expected_revision",token(bad));
            assertThrows(IllegalArgumentException.class,()->executable.validateArguments(arguments(request)));
            assertThrows(IllegalArgumentException.class,()->CheckpointPublicCodec.decode(PublicBindings.present(raw(request))));
        }
    }
    @Test void actualPendingRequestCodecsUseStringRevisionAndKeepSignedGenerationIdsAndBooleanChoice() {
        for(boolean reply:List.of(true,false)) {
            String name=reply?"ck3_reply_pending_character_interaction":"ck3_acknowledge_pending_character_interaction";
            var descriptor=StrictJson.object().put("name",name);var schema=descriptor.putObject("inputSchema").put("type","object");
            var properties=schema.putObject("properties");var required=schema.putArray("required");
            var revisions=properties.putObject("expected_revision").putArray("anyOf"); revisions.addObject().put("type","integer");revisions.addObject().put("type","null");
            properties.putObject("interaction_instance_id").put("type","integer"); required.add("interaction_instance_id");
            if(reply){properties.putObject("accept").put("type","boolean");required.add("accept");}
            var executable=RootPublicCatalogCodec.executableTool(new ToolDescriptor(name,raw(descriptor)));
            for(String revision:List.of("null","\"0\"","\"18446744073709551615\"")) {
                var request=StrictJson.object().put("interaction_instance_id",Integer.MIN_VALUE);request.set("expected_revision",token(revision));if(reply)request.put("accept",false);
                executable.validateArguments(arguments(request));
                PendingInteractionPublicCodec.Request actual=reply?PendingInteractionPublicCodec.decodeReply(PublicBindings.present(raw(request)))
                        :PendingInteractionPublicCodec.decodeAcknowledge(PublicBindings.present(raw(request)));
                var encoded=PublicDataJson.object(PendingInteractionPublicCodec.encodeRequest(actual));assertTrue(encoded.get("interaction_instance_id").isIntegralNumber());
                assertEquals(Integer.MIN_VALUE,encoded.get("interaction_instance_id").intValue());
                executable.validateArguments(arguments(encoded));
            }
            var numeric=StrictJson.object().put("interaction_instance_id",1).put("expected_revision",1);if(reply)numeric.put("accept",false);
            assertThrows(IllegalArgumentException.class,()->executable.validateArguments(arguments(numeric)));
        }
    }
    private record ArmyDescriptorCase(PublicMethod method, String arguments) { }
    @Test void allThirteenArmyDescriptorConsumersAcceptTheirExistingCanonicalWidthCodecAndKeepBoundedNumbers() {
        // Mirrors the native Army owner's exact small request fixtures; native producer proof remains in that owner's tests.
        var cases = List.of(new ArmyDescriptorCase(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, "{}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1, "{\"toward_character_id\":1}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1, "{}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, "{\"subject_public_cunit_id\":0}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_BATTLE_TRANSITION_V1, "{\"combat_id\":1}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, "{\"prior_combat_id\":1,\"subject_public_cunit_id\":0,\"after_terminal_sequence\":\"18446744073709551615\",\"character_ids\":[]}"),
                new ArmyDescriptorCase(PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1, "{\"selected_public_cunit_id\":0,\"target_province_id\":1}"),
                new ArmyDescriptorCase(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, "{\"selected_public_cunit_id\":0,\"expected_combat_id\":1,\"expected_side_index\":0,\"expected_scope\":\"full_side\",\"target_province_id\":1,\"candidate_token\":\"original-candidate-token-0123456789\"}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1, "{}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1, "{}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1, "{}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1, "{\"army_id\":0,\"target_province_id\":1}"),
                new ArmyDescriptorCase(PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1, "{\"selected_public_cunit_id\":0}"));
        assertEquals(13, cases.size());
        for (var fixture : cases) {
            boolean optional = fixture.method() == PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1 || fixture.method() == PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1;
            var request = (ObjectNode) token(fixture.arguments()); request.put("expected_revision", "18446744073709551615");
            var original = armyDescriptor(fixture.method(), request, optional); var executable = RootPublicCatalogCodec.executableTool(original);
            executable.validateArguments(arguments(request));
            var actual = ArmyCallCodec.decode(fixture.method(), raw(request)); var encoded = ArmyCallCodec.encode(actual);
            executable.validateArguments(arguments(PublicDataJson.object(encoded)));
            assertEquals(actual, ArmyCallCodec.decode(fixture.method(), encoded));
            if (optional) {
                var absent = request.deepCopy(); absent.remove("expected_revision"); executable.validateArguments(arguments(absent));
                ArmyCallCodec.decode(fixture.method(), raw(absent));
                var nil = request.deepCopy().putNull("expected_revision"); executable.validateArguments(arguments(nil));
                ArmyCallCodec.decode(fixture.method(), raw(nil));
            }
            request.properties().forEach(entry -> { if (entry.getValue().isIntegralNumber())
                assertTrue(PublicDataJson.object(encoded).get(entry.getKey()).isIntegralNumber(), entry.getKey()); });
            assertThrows(IllegalArgumentException.class, () -> original.validateArguments(arguments(request)));
            for (String bad : List.of("true", "1.0", "9007199254740992", "\"01\"", "\"18446744073709551616\"")) {
                var invalid = request.deepCopy(); invalid.set("expected_revision", token(bad));
                assertThrows(IllegalArgumentException.class, () -> executable.validateArguments(arguments(invalid)));
            }
        }
    }
    private static ToolDescriptor armyDescriptor(PublicMethod method, ObjectNode request, boolean optionalRevision) {
        String name = "ck3_" + method.pythonName(); var descriptor = StrictJson.object().put("name", name);
        var schema = descriptor.putObject("inputSchema").put("type", "object").put("additionalProperties", false);
        var properties = schema.putObject("properties"); var required = schema.putArray("required");
        request.properties().forEach(entry -> {
            String field = entry.getKey(); var property = properties.putObject(field);
            boolean sequence = field.equals("after_terminal_sequence");
            if ((field.equals("expected_revision") && optionalRevision) || sequence) {
                var alternatives = property.putArray("anyOf"); alternatives.addObject().put("type", "integer"); alternatives.addObject().put("type", "null"); property.putNull("default");
            } else if (field.equals("expected_revision") || entry.getValue().isIntegralNumber()) property.put("type", "integer");
            else if (entry.getValue().isArray()) property.put("type", "array").putObject("items").put("type", "integer");
            else property.put("type", "string");
            if (!sequence && !field.equals("character_ids") && !(field.equals("expected_revision") && optionalRevision)
                    && !(method == PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1 && field.equals("target_province_id"))) required.add(field);
        });
        return new ToolDescriptor(name, raw(descriptor));
    }
    private static ToolDescriptor widthFixture(String name, boolean nullable, boolean journal) {
        var descriptor = StrictJson.object().put("name", name); var schema = descriptor.putObject("inputSchema").put("type", "object");
        var properties = schema.putObject("properties"); var required = schema.putArray("required");
        var revision = properties.putObject("expected_revision");
        if (nullable) { revision.putArray("anyOf").addObject().put("type", "integer"); ((com.fasterxml.jackson.databind.node.ArrayNode)revision.get("anyOf")).addObject().put("type", "null"); revision.putNull("default");
            if (name.equals("ck3_select_event_option")) { properties.putObject("option_number").put("type", "integer"); required.add("option_number"); } }
        else { revision.put("type", "integer"); required.add("expected_revision");
            properties.putObject("target_character_id").put("type", "integer"); required.add("target_character_id");
            properties.putObject("scheme_instance_id").put("type", "integer"); required.add("scheme_instance_id");
            if (journal) properties.putObject("after_sequence").put("type", "integer").put("default", 0);
            else { properties.putObject("scheme_instance_generation").put("type", "integer"); required.add("scheme_instance_generation"); }
        }
        return new ToolDescriptor(name, raw(descriptor));
    }
    private static Arguments arguments(JsonNode value) { return new Arguments(Presence.VALUE, Optional.of(raw(value))); }
    private static JsonNode token(String json) { return StrictJson.parse(json.getBytes(StandardCharsets.UTF_8)); }
    private static RawJson raw(JsonNode value) { return PublicDataJson.encode(value); }
}
