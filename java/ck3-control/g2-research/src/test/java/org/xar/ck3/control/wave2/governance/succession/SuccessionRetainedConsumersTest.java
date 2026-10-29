package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m3.M3Research;

final class SuccessionRetainedConsumersTest {
    @Test
    void opaqueFloatingRepresentationsCompareAsBusinessValuesWithoutWeakeningGuards() throws Exception {
        String resource = "original-retained-consumer-golden.json";
        byte[] artifact = resourceBytes(resource);
        JsonNode captured = golden(resource);
        G2Source source = new G2Source(captured.path("machine_id").textValue(), captured.path("observed_at_utc").textValue(),
                "offline-original-producer-fixture", new ExactRef("/g2/m3/" + resource, artifact.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(artifact))));
        List<List<String>> metadataCases = List.of(
                List.of("{\"value\":1e2}", "{\"value\":100.0}"),
                List.of("{\"nested\":[-0.0,{\"value\":1e2}],\"nullable\":null}",
                        "{\"nested\":[0.0,{\"value\":100.0}],\"nullable\":null}"),
                List.of("{\"value\":1e2}", "{\"value\":101.0}"),
                List.of("{\"value\":1e2}", "{\"value\":\"100.0\"}"),
                List.of("{\"nullable\":null}", "{}"),
                List.of("{\"values\":[1.0,2.0]}", "{\"values\":[2.0,1.0]}"));
        for (int scenario = 0; scenario < metadataCases.size(); scenario++) {
            ObjectNode incoming = request(resource, "cases", "current_complete_root_keeps_retained_estate");
            JsonNode previousOpaque = org.xar.ck3.control.contracts.FullJsonTree.parse(
                    metadataCases.get(scenario).get(0).getBytes(StandardCharsets.UTF_8), SuccessionCodec.MAX_BYTES);
            JsonNode currentOpaque = org.xar.ck3.control.contracts.FullJsonTree.parse(
                    metadataCases.get(scenario).get(1).getBytes(StandardCharsets.UTF_8), SuccessionCodec.MAX_BYTES);
            object(incoming.at("/state/expectation/title_expectations/0/title")).set("opaque", previousOpaque);
            object(incoming.at("/turn_bundle/succession_state/value/partition/value/title_heirs/0/title")).set("opaque", currentOpaque);
            object(incoming.at("/campaign_root_result/campaign_root_context/held_title_partition/0/title")).set("opaque", currentOpaque);
            JsonNode originalState = incoming.get("state").deepCopy();
            JsonNode result = evaluate(SuccessionCodec.parse(SuccessionCodec.encode(incoming)));
            boolean changed = scenario >= 2;
            assertEquals(changed ? "invalidated" : "unchanged", result.path("status").textValue());
            assertEquals(changed, result.path("invalidated").booleanValue());
            assertEquals(changed, result.path("refresh_required").booleanValue());
            assertEquals(0, result.path("queries_performed").intValue());
            assertFalse(result.path("submission_authorized").booleanValue());
            if (changed) {
                assertEquals(1, result.path("changed_fields").size());
                assertEquals("title_expectations", result.path("changed_fields").get(0).textValue());
                assertTrue(result.at("/state/expectation").isNull());
                assertTrue(result.at("/state/reconciliation").isNull());
            } else {
                assertEquals(0, result.path("changed_fields").size());
                assertEquals(originalState, result.get("state"), "representation-only change must preserve all detached retained state");
                JsonNode persisted = SuccessionCodec.parse(SuccessionCodec.encode(result));
                assertEquals(previousOpaque, persisted.at("/state/expectation/title_expectations/0/title/opaque"));
            }
            assertWireResult(source, "m3-opaque-equivalence-" + scenario, incoming, result);
        }
        ObjectNode sourceMismatch = request(resource, "cases", "current_complete_root_keeps_retained_estate");
        object(sourceMismatch.at("/turn_bundle/succession_state/value/partition/value/title_heirs/0/title")).put("opaque", 1);
        object(sourceMismatch.at("/campaign_root_result/campaign_root_context/held_title_partition/0/title")).put("opaque", 2);
        assertThrows(IllegalArgumentException.class, () -> evaluate(sourceMismatch), "completed root and bundle provenance still match exactly");
        ObjectNode wrongActor = request(resource, "cases", "current_complete_root_keeps_retained_estate");
        object(wrongActor.get("snapshot")).put("episode_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> evaluate(wrongActor));
        ObjectNode seed = request(resource, "cases", "current_complete_root_keeps_retained_estate");
        JsonNode originalHeir = seed.at("/state/expectation/title_expectations/0/first_heir_character_id");
        assertTrue(originalHeir.isIntegralNumber(), "actual complete retained heir fixture required");
        var nodes = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance;
        for (JsonNode invalid : List.of(nodes.booleanNode(true), nodes.numberNode(originalHeir.doubleValue()))) {
            ObjectNode wrongHeir = seed.deepCopy();
            object(wrongHeir.at("/state/expectation/title_expectations/0")).set("first_heir_character_id", invalid);
            assertThrows(IllegalArgumentException.class, () -> evaluate(wrongHeir));
        }
    }

    @Test
    void actualJavaProducerOutputFlowsThroughAllFourOriginalReaderOracles() throws IOException {
        JsonNode golden = golden("original-producer-golden.json");
        JsonNode seed = request("original-producer-golden.json", "consumer_cases", "restore_complete").get("expectation");
        JsonNode produced = null;
        for (JsonNode row : golden.path("producer_cases")) {
            if ("retain".equals(row.path("request").path("operation").textValue()) && seed.equals(row.get("expected"))) {
                produced = SuccessionCodec.parse(SuccessionPlanningProducer.apply(SuccessionCodec.encode(row.get("request"))));
                assertEquals(row.get("expected"), produced, "actual producer result must equal the complete original seed");
                break;
            }
        }
        assertNotNull(produced, "actual original producer case matching the complete reader seed is required");
        int linked = 0;
        for (JsonNode row : golden.path("consumer_cases")) {
            if (!List.of("restore_complete", "retained_reader_complete", "wal_complete_business", "saved_basis_complete")
                    .contains(row.path("name").textValue())) { continue; }
            ObjectNode incoming = object(row.get("request")).deepCopy();
            switch (incoming.path("operation").textValue()) {
                case "restore", "retained_reader" -> incoming.set("expectation", produced.deepCopy());
                case "wal_business" -> object(incoming.get("fields")).set("succession_expectation", produced.deepCopy());
                case "saved_basis_flags" -> object(incoming.get("flags")).set("succession_expectation", produced.deepCopy());
                default -> throw new IllegalArgumentException("unexpected retained reader operation");
            }
            JsonNode persistedInput = SuccessionCodec.parse(SuccessionCodec.encode(incoming));
            JsonNode consumed = evaluate(persistedInput);
            assertEquals(row.get("expected"), consumed, "actual producer -> reader -> complete original oracle: " + row.path("name").textValue());
            assertEquals(consumed, SuccessionCodec.parse(SuccessionCodec.encode(consumed)), "actual reader result survives persistence");
            linked++;
        }
        assertEquals(4, linked, "restore/retained reader/WAL/saved flags must all consume the actual Java producer result");
    }

    @Test
    void opaqueTitleNumbersSurviveActualProducerAndRetainedWireWithinEachSavedDomain() throws Exception {
        String resource = "original-producer-golden.json";
        JsonNode captured = golden(resource);
        JsonNode seed = request(resource, "consumer_cases", "restore_complete").get("expectation");
        ObjectNode originalRetain = null;
        for (JsonNode row : captured.path("producer_cases")) {
            if ("retain".equals(row.path("request").path("operation").textValue()) && seed.equals(row.get("expected"))) {
                originalRetain = object(row.get("request")).deepCopy();
                break;
            }
        }
        assertNotNull(originalRetain, "actual complete retain producer fixture required");
        byte[] artifact = resourceBytes(resource);
        G2Source source = new G2Source(captured.path("machine_id").textValue(), captured.path("observed_at_utc").textValue(),
                "offline-original-producer-fixture", new ExactRef("/g2/m3/" + resource, artifact.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(artifact))));
        List<String> metadataCases = List.of(
                "{\"negative_zero\":-0.0,\"finite\":1e2,\"integral\":9007199254740991,\"nullable\":null}",
                "{\"negative_zero\":-0.0,\"huge\":1e999,\"integral\":9007199254740991,\"nullable\":null}",
                "{\"negative_zero\":-0.0,\"finite\":1e2,\"integral\":9007199254740993,\"nullable\":null}");
        for (int scenario = 0; scenario < metadataCases.size(); scenario++) {
            JsonNode opaque = org.xar.ck3.control.contracts.FullJsonTree.parse(
                    metadataCases.get(scenario).getBytes(StandardCharsets.UTF_8), SuccessionCodec.MAX_BYTES);
            ObjectNode producer = originalRetain.deepCopy();
            object(producer.at("/turn_bundle/succession_state/value/partition/value/title_heirs/0/title"))
                    .set("opaque", opaque);
            JsonNode produced = SuccessionCodec.parse(SuccessionPlanningProducer.apply(SuccessionCodec.encode(producer)));
            assertEquals(produced, SuccessionCodec.parse(SuccessionCodec.normalize(SuccessionCodec.encode(produced))));
            assertWireResult(source, "m3-opaque-producer-" + scenario, producer, produced);
            assertWireResult(source, "m3-opaque-freeze-" + scenario, legacyRequest(producer), produced);
            for (String name : List.of("restore_complete", "retained_reader_complete", "wal_complete_business", "saved_basis_complete")) {
                ObjectNode incoming = request(resource, "consumer_cases", name);
                String operation = incoming.path("operation").textValue();
                switch (operation) {
                    case "restore", "retained_reader" -> incoming.set("expectation", produced.deepCopy());
                    case "wal_business" -> object(incoming.get("fields")).set("succession_expectation", produced.deepCopy());
                    case "saved_basis_flags" -> object(incoming.get("flags")).set("succession_expectation", produced.deepCopy());
                    default -> throw new IllegalArgumentException("unexpected original reader operation");
                }
                if (operation.equals("saved_basis_flags") && scenario != 0) {
                    assertThrows(IllegalArgumentException.class, () -> evaluate(incoming),
                            "existing saved flags reject nonfinite float and unsafe integer independently");
                    G2Request rejected = new G2Request("m3-opaque-rejected-" + scenario, Milestone.M3, source,
                            ProjectionJson.object(SuccessionCodec.encode(incoming), M3Research.MAXIMUM_BYTES));
                    assertThrows(IllegalArgumentException.class, () -> new M3Research().evaluate(
                            G2Wire.decodeRequest(G2Wire.encodeRequest(rejected))));
                    continue;
                }
                JsonNode persisted = SuccessionCodec.parse(SuccessionCodec.encode(incoming));
                JsonNode consumed = evaluate(persisted);
                JsonNode expectation = switch (operation) {
                    case "restore", "retained_reader" -> consumed;
                    case "wal_business", "saved_basis_flags" -> consumed.get("succession_expectation");
                    default -> throw new IllegalArgumentException("unexpected original reader operation");
                };
                JsonNode retainedOpaque = expectation.path("title_expectations").get(0).path("title").get("opaque");
                assertEquals(opaque, retainedOpaque, name + " preserves all opaque tokens");
                assertEquals("-0.0", retainedOpaque.get("negative_zero").toString());
                assertTrue(retainedOpaque.get("negative_zero").isFloatingPointNumber());
                assertFalse(retainedOpaque.get("negative_zero").isIntegralNumber());
                assertTrue(retainedOpaque.get("integral").isIntegralNumber());
                String floatingField = retainedOpaque.has("huge") ? "huge" : "finite";
                assertEquals(retainedOpaque.has("huge") ? "1e999" : "1e2", retainedOpaque.get(floatingField).toString());
                assertTrue(retainedOpaque.get(floatingField).isFloatingPointNumber());
                assertTrue(retainedOpaque.get("nullable").isNull());
                assertFalse(retainedOpaque.has("missing"));
                assertEquals(consumed, SuccessionCodec.parse(SuccessionCodec.encode(consumed)), "actual retained result survives cold JSON");
                assertWireResult(source, "m3-opaque-reader-" + scenario + "-" + name, incoming, consumed);
            }
        }
    }

    @Test
    void signedActualRetainProducerPersistsAcrossAllFourReadersAndCommonWire() throws Exception {
        String resource = "original-producer-golden.json";
        JsonNode captured = golden(resource);
        JsonNode seed = request(resource, "consumer_cases", "restore_complete").get("expectation");
        ObjectNode originalRetain = null;
        for (JsonNode row : captured.path("producer_cases")) {
            if ("retain".equals(row.path("request").path("operation").textValue()) && seed.equals(row.get("expected"))) {
                originalRetain = object(row.get("request")).deepCopy();
                break;
            }
        }
        assertNotNull(originalRetain, "actual complete retain producer fixture required");
        int originalPredecessor = seed.path("predecessor_character_id").intValue();
        int originalPrimaryHeir = seed.path("expected_successor_character_id").intValue();
        byte[] artifact = resourceBytes(resource);
        G2Source source = new G2Source(captured.path("machine_id").textValue(), captured.path("observed_at_utc").textValue(),
                "offline-original-producer-fixture", new ExactRef("/g2/m3/" + resource, artifact.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(artifact))));
        int[][] pairs = {{2, 0}, {2, -2}, {2, Integer.MIN_VALUE}, {2, Integer.MAX_VALUE},
                {0, 3}, {-2, 3}, {Integer.MIN_VALUE, 3}};
        int linked = 0;
        for (int scenario = 0; scenario < pairs.length; scenario++) {
            int predecessor = pairs[scenario][0], successor = pairs[scenario][1];
            ObjectNode producer = originalRetain.deepCopy();
            ObjectNode snapshot = object(producer.get("snapshot"));
            snapshot.put("episode_character_id", predecessor);
            JsonNode played = snapshot.get("played_character");
            if (played != null && !played.isNull()) { object(played).put("character_id", predecessor); }
            ObjectNode bundle = object(producer.get("turn_bundle"));
            object(bundle.at("/ruler_state/value")).put("character_id", predecessor);
            object(bundle.at("/succession_state/value/primary_title_heir_character_id")).put("value", successor);
            JsonNode originalRows = originalRetain.at("/turn_bundle/succession_state/value/partition/value/title_heirs");
            JsonNode incomingRows = bundle.at("/succession_state/value/partition/value/title_heirs");
            for (JsonNode row : incomingRows) {
                JsonNode role = row.get("first_heir_character_id");
                if (!role.isNull() && role.intValue() == originalPrimaryHeir) {
                    object(row).put("first_heir_character_id", successor);
                }
            }
            ObjectNode unchangedInput = producer.deepCopy();
            JsonNode produced = SuccessionCodec.parse(SuccessionPlanningProducer.apply(SuccessionCodec.encode(producer)));
            assertEquals(unchangedInput, producer, "actual producer must not mutate caller input");
            assertEquals(predecessor, produced.path("predecessor_character_id").intValue());
            assertEquals(predecessor, produced.at("/binding/episode_character_id").intValue());
            assertEquals(successor, produced.path("expected_successor_character_id").intValue());
            assertEquals(originalRows.size(), produced.path("title_expectations").size());
            for (int index = 0; index < originalRows.size(); index++) {
                JsonNode originalRow = originalRows.get(index), actualRow = produced.path("title_expectations").get(index);
                assertEquals(originalRow.get("title"), actualRow.get("title"), "typed title identity/order and metadata stay unchanged");
                assertEquals(originalRow.get("primary"), actualRow.get("primary"));
                JsonNode originalRole = originalRow.get("first_heir_character_id");
                if (originalRole.isNull()) { assertTrue(actualRow.get("first_heir_character_id").isNull()); }
                else { assertEquals(originalRole.intValue() == originalPrimaryHeir ? successor : originalRole.intValue(),
                        actualRow.get("first_heir_character_id").intValue(), "alternate heirs remain original roles"); }
            }
            assertWireResult(source, "m3-signed-producer-" + scenario, producer, produced);
            assertWireResult(source, "m3-signed-public-freeze-" + scenario, legacyRequest(producer), produced);
            for (String name : List.of("restore_complete", "retained_reader_complete", "wal_complete_business", "saved_basis_complete")) {
                ObjectNode incoming = request(resource, "consumer_cases", name);
                String operation = incoming.path("operation").textValue();
                switch (operation) {
                    case "restore" -> {
                        incoming.set("expectation", produced.deepCopy());
                        incoming.put("episode_character_id", predecessor);
                        incoming.set("episode_run_id", produced.path("binding").get("episode_run_id"));
                    }
                    case "retained_reader" -> incoming.set("expectation", produced.deepCopy());
                    case "wal_business", "saved_basis_flags" -> {
                        ObjectNode fields = object(incoming.get(operation.equals("wal_business") ? "fields" : "flags"));
                        fields.set("succession_expectation", produced.deepCopy());
                        JsonNode episode = fields.get("episode_character_id");
                        if (episode != null && episode.isIntegralNumber() && episode.intValue() == originalPredecessor) {
                            fields.put("episode_character_id", predecessor);
                        }
                    }
                    default -> throw new IllegalArgumentException("unexpected original reader operation");
                }
                JsonNode persisted = SuccessionCodec.parse(SuccessionCodec.encode(incoming));
                JsonNode consumed = evaluate(persisted);
                JsonNode retained = switch (operation) {
                    case "restore", "retained_reader" -> consumed;
                    case "wal_business", "saved_basis_flags" -> consumed.get("succession_expectation");
                    default -> throw new IllegalArgumentException("unexpected original reader operation");
                };
                assertEquals(predecessor, retained.path("predecessor_character_id").intValue(), name);
                assertEquals(predecessor, retained.at("/binding/episode_character_id").intValue(), name);
                assertEquals(successor, retained.path("expected_successor_character_id").intValue(), name);
                assertEquals(produced.get("title_expectations"), retained.get("title_expectations"), name);
                assertEquals(consumed, SuccessionCodec.parse(SuccessionCodec.encode(consumed)), "actual consumer result survives serialization");
                assertWireResult(source, "m3-signed-reader-" + scenario + "-" + name, incoming, consumed);
                linked++;
            }
        }
        assertEquals(28, linked, "all seven actual producer role pairs must reach all four retained readers");
    }

    @Test
    void completedRootAndWarmReadersPreserveModernPrimaryRolesWithoutInventingAnEstateEpoch() throws Exception {
        String resource = "original-retained-consumer-golden.json";
        JsonNode captured = golden(resource);
        byte[] artifact = resourceBytes(resource);
        G2Source source = new G2Source(captured.path("machine_id").textValue(), captured.path("observed_at_utc").textValue(),
                "offline-original-retained-fixture", new ExactRef("/g2/m3/" + resource, artifact.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(artifact))));
        boolean currentSeen = false, warmSeen = false;
        int scenarios = 0;
        for (JsonNode row : captured.path("cases")) {
            boolean current = "current_complete_root_keeps_retained_estate".equals(row.path("name").textValue());
            boolean warm = "warm_refresh".equals(row.path("request").path("operation").textValue())
                    && "source_epoch_refresh_required".equals(row.path("expected").path("status").textValue());
            if (!current && !warm) { continue; }
            currentSeen |= current; warmSeen |= warm;
            for (int successor : new int[] {0, -2, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
                ObjectNode incoming = object(row.get("request")).deepCopy();
                mapRetainedRootPrimaryRole(incoming, successor);
                JsonNode persisted = SuccessionCodec.parse(SuccessionCodec.encode(incoming));
                JsonNode actual = evaluate(persisted);
                assertEquals(row.path("expected").get("status"), actual.get("status"));
                assertEquals(row.path("expected").get("invalidated"), actual.get("invalidated"));
                assertEquals(row.path("expected").get("refresh_required"), actual.get("refresh_required"));
                assertEquals(0, actual.path("queries_performed").intValue());
                assertTrue(actual.path("submission_authorized").isBoolean());
                assertFalse(actual.path("submission_authorized").booleanValue());
                if (warm) {
                    assertTrue(actual.at("/state/expectation").isNull());
                    assertTrue(actual.at("/state/reconciliation").isNull());
                    assertFalse(actual.path("estate_change_inferred").booleanValue());
                    assertEquals(persisted.at("/state/expectation/binding"), actual.get("previous_source_binding"));
                } else {
                    assertEquals(successor, actual.at("/state/expectation/expected_successor_character_id").intValue());
                    assertEquals(persisted.at("/state/expectation"), actual.at("/state/expectation"));
                }
                assertEquals(actual, SuccessionCodec.parse(SuccessionCodec.encode(actual)));
                assertWireResult(source, "m3-signed-root-" + scenarios, persisted, actual);
                scenarios++;
            }
        }
        assertTrue(currentSeen && warmSeen, "actual original complete and warm source-epoch fixtures required");
        assertTrue(scenarios >= 8, "all four signed heirs must reach each actual completed-root reader");
    }

    @Test
    void completedRootAndWarmValidateEveryTailRoleThroughDirectAndCommonWireConsumers() throws Exception {
        String resource = "original-retained-consumer-golden.json";
        JsonNode captured = golden(resource);
        byte[] artifact = resourceBytes(resource);
        G2Source source = new G2Source(captured.path("machine_id").textValue(), captured.path("observed_at_utc").textValue(),
                "offline-original-retained-fixture", new ExactRef("/g2/m3/" + resource, artifact.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(artifact))));
        int readers = 0, accepted = 0, rejected = 0;
        for (JsonNode row : captured.path("cases")) {
            boolean current = "current_complete_root_keeps_retained_estate".equals(row.path("name").textValue());
            boolean warm = "warm_refresh".equals(row.path("request").path("operation").textValue())
                    && "source_epoch_refresh_required".equals(row.path("expected").path("status").textValue());
            if (!current && !warm) { continue; }
            readers++;
            ObjectNode seed = object(row.get("request")).deepCopy();
            assertEquals(row.path("expected").get("status"), evaluate(seed).get("status"), "unmodified source is a valid precondition");
            for (int role : new int[] {0, -2, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
                ObjectNode incoming = seed.deepCopy();
                ((com.fasterxml.jackson.databind.node.ArrayNode) incoming.at("/campaign_root_result/campaign_root_context/primary_title_succession_character_ids")).add(role);
                JsonNode persisted = SuccessionCodec.parse(SuccessionCodec.encode(incoming));
                JsonNode actual = evaluate(persisted);
                assertEquals(row.path("expected").get("status"), actual.get("status"));
                assertEquals(0, actual.path("queries_performed").intValue());
                assertFalse(actual.path("submission_authorized").booleanValue());
                assertWireResult(source, "m3-signed-tail-" + accepted, persisted, actual);
                accepted++;
            }
            for (String token : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "2.0", "\"2\"", "null")) {
                ObjectNode incoming = seed.deepCopy();
                JsonNode invalid = org.xar.ck3.control.contracts.FullJsonTree.parse(token.getBytes(StandardCharsets.UTF_8), 32);
                ((com.fasterxml.jackson.databind.node.ArrayNode) incoming.at("/campaign_root_result/campaign_root_context/primary_title_succession_character_ids")).add(invalid);
                JsonNode persisted = SuccessionCodec.parse(SuccessionCodec.encode(incoming));
                assertThrows(IllegalArgumentException.class, () -> evaluate(persisted), token + " in " + row.path("name").textValue());
                G2Request rejectedWire = new G2Request("m3-rejected-tail-" + rejected, Milestone.M3, source,
                        ProjectionJson.object(SuccessionCodec.encode(persisted), M3Research.MAXIMUM_BYTES));
                assertThrows(IllegalArgumentException.class, () -> new M3Research().evaluate(
                        G2Wire.decodeRequest(G2Wire.encodeRequest(rejectedWire))), token + " must remain an invalid raw role through common wire");
                rejected++;
            }
        }
        assertTrue(readers >= 2 && accepted == readers * 4 && rejected == readers * 8);
    }

    private static void mapRetainedRootPrimaryRole(ObjectNode incoming, int successor) {
        ObjectNode expectation = object(incoming.at("/state/expectation"));
        JsonNode previous = expectation.get("expected_successor_character_id");
        assertTrue(previous != null && previous.isIntegralNumber(), "actual retained primary role fixture required");
        int oldHeir = previous.intValue();
        expectation.put("expected_successor_character_id", successor);
        for (JsonNode row : expectation.path("title_expectations")) {
            JsonNode role = row.get("first_heir_character_id");
            if (!role.isNull() && role.intValue() == oldHeir) { object(row).put("first_heir_character_id", successor); }
        }
        ObjectNode root = object(incoming.at("/campaign_root_result/campaign_root_context"));
        com.fasterxml.jackson.databind.node.ArrayNode heirs = (com.fasterxml.jackson.databind.node.ArrayNode) root.get("primary_title_succession_character_ids");
        assertFalse(heirs.isEmpty());
        heirs.set(0, com.fasterxml.jackson.databind.node.IntNode.valueOf(successor));
        for (JsonNode row : root.path("held_title_partition")) {
            JsonNode role = row.get("first_heir_character_id");
            if (!role.isNull() && role.intValue() == oldHeir) { object(row).put("first_heir_character_id", successor); }
        }
        ObjectNode bundle = object(incoming.get("turn_bundle"));
        object(bundle.at("/succession_state/value/primary_title_heir_character_id")).put("value", successor);
        for (JsonNode row : bundle.at("/succession_state/value/partition/value/title_heirs")) {
            JsonNode role = row.get("first_heir_character_id");
            if (!role.isNull() && role.intValue() == oldHeir) { object(row).put("first_heir_character_id", successor); }
        }
    }

    @TestFactory
    Stream<DynamicTest> originalProducerToEveryRetainedReader() throws IOException {
        JsonNode golden = golden("original-producer-golden.json");
        assertEquals("xar.g2.m3.original-producer-golden/v1", golden.path("schema").textValue());
        assertTrue(golden.path("source_refs_unchanged").booleanValue());
        assertTrue(golden.path("consumer_cases").size() >= 7, "full/null original readers required");
        return positive(golden.path("consumer_cases"));
    }

    @TestFactory
    Stream<DynamicTest> originalReadersRejectWrongEpisodePendingAndWrongTokens() throws IOException {
        JsonNode golden = golden("original-producer-golden.json");
        assertTrue(golden.path("consumer_rejected").size() >= 4);
        return negative(golden.path("consumer_rejected"));
    }

    @TestFactory
    Stream<DynamicTest> actualCompletedServiceRootToInvalidationAndWarmConsumers() throws IOException {
        JsonNode golden = golden("original-retained-consumer-golden.json");
        assertEquals("xar.g2.m3.original-retained-consumer-golden/v1", golden.path("schema").textValue());
        assertTrue(golden.path("source_refs_unchanged").booleanValue());
        assertTrue(golden.path("synthetic_fixture").booleanValue());
        assertTrue(golden.path("observations").path("service_complete_root_calls").intValue() >= 2);
        assertEquals(0, golden.path("observations").path("gameplay_submissions").intValue());
        assertTrue(golden.path("cases").size() >= 6);
        return positive(golden.path("cases"));
    }

    @TestFactory
    Stream<DynamicTest> actualRootConsumersPreserveRejectedActorEpisodeFrameAndPartialCases() throws IOException {
        JsonNode golden = golden("original-retained-consumer-golden.json");
        assertTrue(golden.path("rejected").size() >= 7);
        return negative(golden.path("rejected"));
    }

    @Test
    void walMaskExcludesOnlyFourOriginalFrameLeavesAndRetainsTypesAndBusiness() throws IOException {
        ObjectNode request = request("original-producer-golden.json", "consumer_cases", "wal_complete_business");
        JsonNode original = evaluate(request);
        ObjectNode next = request.deepCopy();
        ObjectNode binding = object(next.path("fields").path("succession_expectation").path("binding"));
        binding.put("snapshot_id", "native:next").put("revision", 99).put("native_revision", 100).put("date_raw", 200);
        assertEquals(original, evaluate(next));
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw")) {
            assertFalse(original.path("succession_expectation").path("binding").has(key));
        }
        assertEquals(100, original.path("succession_expectation").path("binding").path("episode_character_id").intValue());
        assertTrue(original.has("nullable_extension") && original.get("nullable_extension").isNull());
        assertTrue(original.path("empty_extension").isArray() && original.path("empty_extension").isEmpty());
        ObjectNode changed = request.deepCopy(); object(changed.path("fields")).put("episode_character_id", true);
        assertNotEquals(original, evaluate(changed), "business bool does not equal its integer representation");
        ObjectNode extra = request.deepCopy(); object(extra.path("fields")).putNull("new_scalar");
        assertNotEquals(original, evaluate(extra));
    }

    @Test
    void flagsRetainMissingNullEmptyAndSafeJsonIntegerBoundaries() throws IOException {
        ObjectNode request = request("original-producer-golden.json", "consumer_cases", "saved_basis_complete");
        for (String field : List.of("managed_restore_transaction", "rollback_war_failure", "succession_expectation",
                "rollback_war_failures", "session_binding_present")) {
            ObjectNode missing = request.deepCopy(); object(missing.get("flags")).remove(field);
            assertThrows(IllegalArgumentException.class, () -> evaluate(missing), field);
        }
        ObjectNode emptyNull = request.deepCopy(); object(emptyNull.get("flags")).putNull("rollback_war_failures");
        assertThrows(IllegalArgumentException.class, () -> evaluate(emptyNull));
        ObjectNode unsafe = request.deepCopy();
        object(unsafe.path("flags").path("succession_expectation").path("binding")).put("revision", BigInteger.ONE.shiftLeft(53));
        assertThrows(IllegalArgumentException.class, () -> evaluate(unsafe), "saved basis retains its original safe JSON domain");
    }

    @Test
    void completedRootBundleAndSourceCannotBeSwappedDespiteMatchingPublishedRevision() throws IOException {
        ObjectNode request = request("original-retained-consumer-golden.json", "cases", "current_complete_root_keeps_retained_estate");
        ObjectNode query = request.deepCopy(); ObjectNode source = object(query.path("turn_bundle").path("source"));
        source.put("query_sequence", source.get("query_sequence").bigIntegerValue().add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> evaluate(query));
        ObjectNode titles = request.deepCopy();
        JsonNode row = titles.path("turn_bundle").path("succession_state").path("value").path("partition").path("value").path("title_heirs").get(0);
        object(row.path("title")).put("title_id", 99993);
        assertThrows(IllegalArgumentException.class, () -> evaluate(titles));
        ObjectNode scope = request.deepCopy(); object(scope.path("turn_bundle").path("source")).put("capability", "some-other-root");
        assertThrows(IllegalArgumentException.class, () -> evaluate(scope));
    }

    @Test
    void newWireWrapperRejectsAuthorityFieldsDuplicateTokensAndWrongEpisodeTypes() throws IOException {
        ObjectNode base = request("original-producer-golden.json", "consumer_cases", "restore_complete");
        ObjectNode extra = base.deepCopy(); extra.put("submission_authorized", true);
        assertThrows(IllegalArgumentException.class, () -> evaluate(extra));
        for (String token : List.of("true", "100.0", "\"100\"")) {
            String wire = new String(SuccessionCodec.encode(base), StandardCharsets.UTF_8);
            String malformed = wire.replace("\"episode_character_id\":100", "\"episode_character_id\":" + token);
            assertNotEquals(wire, malformed);
            assertThrows(IllegalArgumentException.class, () -> SuccessionRetainedConsumers.apply(malformed.getBytes(StandardCharsets.UTF_8)));
        }
        String wire = new String(SuccessionCodec.encode(base), StandardCharsets.UTF_8);
        String duplicate = wire.substring(0, wire.length() - 1) + ",\"operation\":\"restore\"}";
        assertThrows(IllegalArgumentException.class, () -> SuccessionRetainedConsumers.apply(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SuccessionRetainedConsumers.apply((wire + "{}").getBytes(StandardCharsets.UTF_8)));
    }

    @Test
    void everyOriginalReaderTraversesTheCommonWireAndM3DomainWithoutLosingSource() throws Exception {
        for (String resource : List.of("original-producer-golden.json", "original-retained-consumer-golden.json")) {
            byte[] artifact = resourceBytes(resource); JsonNode captured = golden(resource);
            G2Source source = new G2Source(captured.path("machine_id").textValue(), captured.path("observed_at_utc").textValue(),
                    "offline-original-producer-fixture", new ExactRef("/g2/m3/" + resource, artifact.length,
                            HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(artifact))));
            String group = resource.equals("original-producer-golden.json") ? "consumer_cases" : "cases";
            for (JsonNode row : captured.path(group)) {
                G2Request request = new G2Request("m3-wire-" + row.path("name").textValue(), Milestone.M3, source,
                        ProjectionJson.object(SuccessionCodec.encode(row.get("request")), M3Research.MAXIMUM_BYTES));
                G2Request incoming = G2Wire.decodeRequest(G2Wire.encodeRequest(request));
                var response = G2Wire.decodeResponse(G2Wire.encodeResponse(new M3Research().evaluate(incoming)));
                assertEquals(request.requestId(), response.requestId());
                assertEquals(Milestone.M3, response.milestone());
                assertEquals(source, response.source(), "machine/time/build/exact source ref survive both wire boundaries");
                assertEquals(row.get("expected"), SuccessionCodec.parse(response.result().bytes()));
            }
            if (resource.equals("original-producer-golden.json")) {
                for (String producerGroup : List.of("producer_cases", "freshness_cases")) {
                    for (JsonNode row : captured.path(producerGroup)) {
                        assertWireResult(source, "m3-existing-" + row.path("name").textValue(), row.get("request"), row.get("expected"));
                        if (producerGroup.equals("producer_cases")) {
                            ObjectNode pure = legacyRequest(row.get("request"));
                            assertWireResult(source, "m3-pure-" + row.path("name").textValue(), pure, row.get("expected"));
                            if ("retain".equals(row.path("request").path("operation").textValue())) {
                                ObjectNode normalize = SuccessionCodec.objectNode();
                                normalize.put("schema", SuccessionConsumerPort.SCHEMA).put("operation", "normalize");
                                normalize.set("expectation", row.get("expected"));
                                assertWireResult(source, "m3-normalize-" + row.path("name").textValue(), normalize, row.get("expected"));
                            }
                        }
                    }
                }
            }
        }
    }

    private static void assertWireResult(G2Source source, String id, JsonNode payload, JsonNode expected) {
        G2Request request = new G2Request(id, Milestone.M3, source,
                ProjectionJson.object(SuccessionCodec.encode(payload), M3Research.MAXIMUM_BYTES));
        var response = G2Wire.decodeResponse(G2Wire.encodeResponse(new M3Research().evaluate(
                G2Wire.decodeRequest(G2Wire.encodeRequest(request)))));
        assertEquals(request.requestId(), response.requestId());
        assertEquals(source, response.source());
        assertEquals(expected, SuccessionCodec.parse(response.result().bytes()));
    }

    private static ObjectNode legacyRequest(JsonNode producer) {
        ObjectNode request = SuccessionCodec.objectNode(); request.put("schema", SuccessionConsumerPort.SCHEMA);
        if ("retain".equals(producer.path("operation").textValue())) {
            request.put("operation", "freeze"); request.set("turn_bundle", producer.get("turn_bundle"));
            request.set("episode_run_id", producer.path("snapshot").get("episode_run_id"));
            request.set("episode_character_id", producer.path("snapshot").get("episode_character_id"));
        } else {
            request.put("operation", "reconcile"); request.set("expectation", producer.get("expectation"));
            request.set("post_snapshot", producer.get("snapshot")); request.set("post_turn_bundle", producer.get("turn_bundle"));
        }
        return request;
    }

    private static Stream<DynamicTest> positive(JsonNode cases) {
        return StreamSupport.stream(cases.spliterator(), false).map(row -> DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
            JsonNode request = row.get("request"); byte[] wire = SuccessionCodec.encode(request);
            JsonNode result = SuccessionCodec.parse(SuccessionRetainedConsumers.apply(wire));
            assertEquals(row.get("expected"), result);
            assertEquals(request, SuccessionCodec.parse(wire), "caller inputs unchanged");
            if (request.path("operation").textValue().equals("invalidate") || request.path("operation").textValue().equals("warm_refresh")) {
                if (!result.isNull()) {
                    assertFalse(result.path("submission_authorized").booleanValue());
                    assertEquals(0, result.path("queries_performed").intValue());
                }
            }
        }));
    }
    private static Stream<DynamicTest> negative(JsonNode cases) {
        return StreamSupport.stream(cases.spliterator(), false).map(row -> DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
            assertTrue(row.path("error_type").isTextual(), "real original rejection required");
            assertThrows(IllegalArgumentException.class, () -> evaluate(row.get("request")));
        }));
    }
    private static JsonNode evaluate(JsonNode request) { return SuccessionCodec.parse(SuccessionRetainedConsumers.apply(SuccessionCodec.encode(request))); }
    private static ObjectNode request(String resource, String cases, String name) throws IOException {
        for (JsonNode row : golden(resource).path(cases)) {
            if (name.equals(row.path("name").textValue())) { return object(row.get("request")).deepCopy(); }
        }
        throw new IllegalArgumentException("missing actual original case: " + name);
    }
    private static ObjectNode object(JsonNode value) {
        if (value instanceof ObjectNode object) { return object; }
        throw new IllegalArgumentException("test object required");
    }
    private static JsonNode golden(String resource) throws IOException {
        // The artifact groups several bounded requests; each request still goes through the production boundary.
        return org.xar.ck3.control.contracts.FullJsonTree.parse(resourceBytes(resource), org.xar.ck3.control.contracts.FullJsonTree.MAXIMUM_BYTES);
    }
    private static byte[] resourceBytes(String resource) throws IOException {
        try (InputStream input = SuccessionRetainedConsumersTest.class.getResourceAsStream("/g2/m3/" + resource)) {
            assertNotNull(input, "actual original producer capture required; missing environment cannot be a skip or stub");
            return input.readAllBytes();
        }
    }
}
