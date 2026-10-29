package org.xar.ck3.control.wave2.military.reliefrelevance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegeCodec;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevancePolicy.Assessment;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevancePolicy.Request;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevancePolicy.WarObjectives;

/** Both projections consume the same document and exact selected nodes; no externally asserted membership. */
public final class ReliefRelevanceCodec {
    private ReliefRelevanceCodec() { }
    public static byte[] evaluate(byte[] raw) { return encodeAssessment(ReliefRelevancePolicy.assess(decode(raw))); }
    public static Request decode(byte[] raw) { return decodeNode(StrictJson.parse(raw)); }
    public static Request decodeNode(JsonNode node) {
        ObjectNode root = StrictJson.object(node, Set.of("schema", "frame"));
        StrictJson.require(ReliefRelevancePolicy.INPUT_SCHEMA.equals(StrictJson.text(root.get("schema"))), "unsupported relief relevance schema");
        JsonNode frameNode = root.get("frame"); RealmSiegePolicy.Request frame = RealmSiegeCodec.decodeNode(frameNode);
        List<WarObjectives> traversal = new ArrayList<>();
        if (frame.snapshot().activeWars() != null) {
            for (JsonNode war : frameNode.get("snapshot").get("active_wars")) { traversal.add(new WarObjectives(objectives(war.get("war_objective_province_ids")))); }
        }
        JsonNode war = candidateWarNode(frameNode, frame), enemy = candidateEnemyNode(frameNode, frame, war);
        return new Request(frame, war == null ? null : objectives(war.get("war_objective_province_ids")),
                enemy == null ? null : integer(enemy.get("siege_province_holder_character_id")), traversal);
    }

    public static byte[] encodeRequest(Request request) {
        ObjectNode frame = (ObjectNode) StrictJson.parse(RealmSiegeCodec.encodeRequest(request.realmFrame()));
        if (request.realmFrame().snapshot().activeWars() != null) {
            JsonNode wars = frame.get("snapshot").get("active_wars");
            for (int index = 0; index < request.activeWarObjectivesInStoredOrder().size(); index++) {
                objectivesNode((ObjectNode) wars.get(index), request.activeWarObjectivesInStoredOrder().get(index).provinceIds());
            }
        }
        JsonNode war = candidateWarNode(frame, request.realmFrame()), enemy = candidateEnemyNode(frame, request.realmFrame(), war);
        if (war instanceof ObjectNode value) { objectivesNode(value, request.candidateWarObjectiveProvinceIds()); }
        if (enemy instanceof ObjectNode value) { value.put("siege_province_holder_character_id", request.candidateEnemySiegeProvinceHolderCharacterId()); }
        ObjectNode result = StrictJson.object(); result.put("schema", ReliefRelevancePolicy.INPUT_SCHEMA); result.set("frame", frame);
        return StrictJson.canonical(result);
    }

    public static byte[] encodeAssessment(Assessment assessment) {
        ObjectNode result = StrictJson.object(); result.put("schema", ReliefRelevancePolicy.OUTPUT_SCHEMA);
        result.put("candidate_siege_relief_relevant", assessment.candidateSiegeReliefRelevant());
        ArrayNode objectives = result.putArray("objective_province_ids_in_stored_traversal");
        assessment.objectiveProvinceIdsInStoredTraversal().forEach(objectives::add);
        return StrictJson.canonical(result, StrictJson.OUTPUT_MAX_BYTES);
    }

    private static JsonNode candidateWarNode(JsonNode node, RealmSiegePolicy.Request request) {
        RealmSiegePolicy.WarReference reference = request.candidateWarRef(); if (reference == null) { return null; }
        JsonNode rows = reference.collection() == RealmSiegePolicy.WarCollection.ACTIVE_WARS
                ? node.get("snapshot").get("active_wars") : node.get("detached_wars");
        return rows.get(reference.index());
    }
    private static JsonNode candidateEnemyNode(JsonNode node, RealmSiegePolicy.Request request, JsonNode war) {
        RealmSiegePolicy.EnemyReference reference = request.candidateEnemyRef(); if (reference == null) { return null; }
        JsonNode rows = reference.collection() == RealmSiegePolicy.EnemyCollection.CANDIDATE_WAR_ENEMIES
                ? war == null ? null : war.get("enemy_armies") : node.get("detached_enemies");
        StrictJson.require(rows != null, "selected enemy reference must have a document-owned container");
        return rows.get(reference.index());
    }
    private static List<BigInteger> objectives(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isArray(), "objective integer array required"); List<BigInteger> result = new ArrayList<>();
        for (JsonNode value : node) { BigInteger parsed = integer(value); StrictJson.require(parsed != null, "objective province cannot be null"); result.add(parsed); }
        return result;
    }
    private static BigInteger integer(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isIntegralNumber(), "exact integer required; no bool, float or string"); return node.bigIntegerValue();
    }
    private static void objectivesNode(ObjectNode parent, List<BigInteger> values) {
        if (values == null) { parent.putNull("war_objective_province_ids"); }
        else { ArrayNode array = parent.putArray("war_objective_province_ids"); values.forEach(array::add); }
    }
}
