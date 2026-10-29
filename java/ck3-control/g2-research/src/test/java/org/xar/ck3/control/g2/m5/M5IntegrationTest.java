package org.xar.ck3.control.g2.m5;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.m5.M5Research.ExistingWarPlan;
import org.xar.ck3.control.g2.m5.M5Research.MissingPlan;
import org.xar.ck3.control.g2.m5.M5Research.NullPlan;
import org.xar.ck3.control.g2.m5.M5Research.ObservedPlan;
import org.xar.ck3.control.g2.m5.M5Research.Result;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.planning.ProposalLifecycleFixtures;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreatsCodec;

/** Original saved producer vectors and synthetic consumer edges; no native or ledger qualification. */
final class M5IntegrationTest {
    private static Obj corpus() throws IOException {
        try (var source = M5IntegrationTest.class.getResourceAsStream("/jointintake/producer-golden-v1.json.gz")) {
            assertNotNull(source, "the original real-producer corpus is required; never skip");
            try (var gzip = new GZIPInputStream(source)) {
                return M5PayloadCodec.parseObject(gzip.readAllBytes(), "original producer corpus");
            }
        }
    }

    private static List<Obj> cases() throws IOException {
        return array(corpus().get("cases"), "original producer cases").stream()
                .map(value -> object(value, "original producer case")).toList();
    }

    private static Obj input(String name) throws IOException {
        return cases().stream().filter(value -> new Text(name).equals(value.get("name")))
                .map(value -> object(value.get("input"), "original intake request")).findFirst().orElseThrow();
    }

    private static Result evaluate(Obj intake, ExistingWarPlan plan) {
        byte[] payload = M5PayloadCodec.encodeRequest(new M5PayloadCodec.Request(intake, plan));
        return M5PayloadCodec.decodeResult(M5Research.evaluatePayload(payload));
    }

    private static Obj without(Obj source, String field) {
        Map<String, Value> fields = new LinkedHashMap<>(source.members()); fields.remove(field); return new Obj(fields);
    }

    @Test void completeOriginalProducerCorpusReachesTheRealCollectorSelectorAndSavedConsumer() throws IOException {
        Obj metadata = corpus();
        assertEquals(BigInteger.valueOf(26), integer(metadata.get("original_tests_run"), "actual original tests"));
        assertEquals(BigInteger.ZERO, integer(metadata.get("original_test_failures"), "original failures"));
        assertEquals(BigInteger.ZERO, integer(metadata.get("original_test_errors"), "original errors"));
        int accepted = 0, rejected = 0;
        for (Obj vector : cases()) {
            Obj intake = object(vector.get("input"), "original intake request");
            byte[] request = M5PayloadCodec.encodeRequest(new M5PayloadCodec.Request(intake, new MissingPlan()));
            byte[] originalBytes = request.clone();
            if (new Bool(true).equals(vector.get("accepted"))) {
                byte[] actual = M5Research.evaluatePayload(request);
                Result result = M5PayloadCodec.decodeResult(actual);
                assertEquals(M5PayloadCodec.decodeAnalysis(FormalProposalIntake.collect(encode(intake))), result.intakeAnalysis(),
                        text(vector.get("name"), "case") + ": complete actual Java producer result");
                Obj golden = object(vector.get("expected"), "real Python producer expected result");
                for (Map.Entry<String, Value> field : golden.members().entrySet())
                    assertEquals(field.getValue(), result.intakeAnalysis().get(field.getKey()), text(vector.get("name"), "case") + ":" + field.getKey());
                assertArrayEquals(actual, M5PayloadCodec.encodeResult(result), "durable JSON is canonical and complete");
                assertFalse(M5DecisionConsumer.consume(actual).actionAuthorized());
                accepted++;
            } else {
                assertThrows(IllegalArgumentException.class, () -> M5Research.evaluatePayload(request)); rejected++;
            }
            assertArrayEquals(originalBytes, request, "request bytes remain unchanged");
        }
        assertEquals(18, accepted); assertEquals(7, rejected);
    }

    @Test void actualSnapshotProducerSuppliesBothLeadershipGroupsAndDeduplicatedCrossWarEnemies() throws IOException {
        Obj intake = input("aggregate-all-war-occupation");
        Obj snapshot = object(intake.get("snapshot"), "snapshot");
        List<Value> wars = array(snapshot.get("active_wars"), "active wars");
        Obj first = object(wars.getFirst(), "primary war").with("source", new Text("native"))
                .with("enemy_armies", new Arr(List.of(army(0, 300), army(55, 400))));
        Obj second = object(wars.get(1), "nonprimary war").with("source", new Text("native"))
                .with("player_side", new Text("defender")).with("player_is_primary_war_leader", new Bool(false))
                .with("enemy_armies", new Arr(List.of(army(55, 400), army(56, 500))));
        Obj current = snapshot.with("played_character", object(snapshot.get("played_character"), "player").with("alive", new Bool(true)))
                .with("active_wars", new Arr(List.of(first, second)));
        Result result = evaluate(intake.with("snapshot", current), new MissingPlan());
        assertInstanceOf(ParticipatingWarThreats.Observed.class, result.participatingWars());
        ParticipatingWarThreats.Observed observed = (ParticipatingWarThreats.Observed) result.participatingWars();
        assertEquals(List.of(16777231, 16777232), observed.participatingWarIds());
        assertEquals(List.of(16777231), observed.primaryWarIds());
        assertEquals(List.of(16777232), observed.nonPrimaryWarIds());
        assertEquals(List.of(0, 55, 56), observed.uniqueEnemyArmyIds());
        assertEquals(List.of(16777231, 16777232), observed.enemyArmyMemberships().get(1).warIds());
        assertEquals(new ParticipatingWarThreats.Known(BigInteger.valueOf(1200)), observed.strength());
        assertEquals(BigInteger.valueOf(23), observed.frame().revision());
        assertEquals(BigInteger.valueOf(17), observed.frame().nativeRevision());
        assertEquals(ParticipatingWarThreats.NonParticipantLiegeScope.UNASSESSED_NONPARTICIPANT_LIEGE_WARS,
                observed.nonParticipantLiegeScope());
        assertFalse(observed.actionAuthorized());
    }

    @Test void originalWarPlanAndNonleadingCashPolicyArePreservedWithoutAcquiringCurrentBinding() throws IOException {
        Obj priority = obj(Map.of("cash_protection_priority_war_ids", new Arr(List.of(integerValue(16777232))),
                "primary_war_hostile_union_v1", obj(Map.of("war_ids", new Arr(List.of(integerValue(16777231))))),
                "nonleading_realm_siege_construction_deferred_v1", new Bool(true)));
        Obj originalScope = obj(Map.of("cash_priority_war_id", integerValue(16777232),
                "unique_primary_war_enemy_soldiers", integerValue(777), "battle_win_probability", Nil.INSTANCE));
        Obj plan = obj(Map.of("selected_step", new Text("move-army-71-to-99"), "reason", new Text("original machine reason"),
                "war_spending_priority_v1", priority, "war_decision_reason_scope_v1", originalScope,
                "prior_source_frame", new Text("a retained older plan is not silently current")));
        Result result = evaluate(input("peace-building-gift"), new ObservedPlan(plan));
        M5DecisionConsumer.Consumption consumed = M5DecisionConsumer.consume(result);
        Obj annotated = ((ObservedPlan) consumed.annotatedPlan()).plan();
        for (String field : List.of("selected_step", "reason", "war_spending_priority_v1", "prior_source_frame"))
            assertEquals(plan.get(field), annotated.get(field));
        for (Map.Entry<String, Value> field : originalScope.members().entrySet())
            assertEquals(field.getValue(), consumed.reasonScope().get(field.getKey()));
        assertEquals(new Text("not_established_by_payload"), consumed.reasonScope().get("existing_cash_priority_source_binding"));
        assertEquals(plan, ((ObservedPlan) result.existingWarPlan()).plan(), "original evidence remains independent of its presentation");
        assertFalse(consumed.actionAuthorized());
    }

    @Test void absentNullAndObservedPlanAndReasonScopeRemainDistinctAcrossPersistence() throws IOException {
        List<ExistingWarPlan> plans = List.of(new MissingPlan(), new NullPlan(), new ObservedPlan(obj(Map.of())),
                new ObservedPlan(obj(Map.of("war_decision_reason_scope_v1", Nil.INSTANCE))),
                new ObservedPlan(obj(Map.of("war_decision_reason_scope_v1", obj(Map.of())))));
        List<M5DecisionConsumer.OriginalScopePresence> expected = List.of(
                M5DecisionConsumer.OriginalScopePresence.PLAN_MISSING, M5DecisionConsumer.OriginalScopePresence.PLAN_NULL,
                M5DecisionConsumer.OriginalScopePresence.SCOPE_MISSING, M5DecisionConsumer.OriginalScopePresence.SCOPE_NULL,
                M5DecisionConsumer.OriginalScopePresence.OBSERVED);
        for (int index = 0; index < plans.size(); index++) {
            Result result = evaluate(input("peace-building-gift"), plans.get(index));
            assertEquals(plans.get(index), result.existingWarPlan());
            assertEquals(expected.get(index), M5DecisionConsumer.consume(result).originalScopePresence());
        }
    }

    @Test void wrongFieldMissingFieldRawTokenAndProtocolFailuresAreActualDecodePaths() throws IOException {
        Obj intake = input("peace-building-gift");
        Obj request = M5PayloadCodec.parseObject(M5PayloadCodec.encodeRequest(new M5PayloadCodec.Request(intake, new MissingPlan())), "request");
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeRequest(encode(without(request, "intake_request"))));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeRequest(encode(request.with("typo", Nil.INSTANCE))));
        for (Value invalid : List.of(new Bool(true), integerValue(1), new Text("plan"), new Arr(List.of())))
            assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeRequest(encode(request.with("existing_war_plan", invalid))));
        for (Value invalid : List.of(new Bool(true), new DecimalValue("23.0"), new Text("23"), Nil.INSTANCE)) {
            Obj wrong = intake.with("snapshot", object(intake.get("snapshot"), "snapshot").with("revision", invalid));
            byte[] raw = M5PayloadCodec.encodeRequest(new M5PayloadCodec.Request(wrong, new MissingPlan()));
            assertThrows(IllegalArgumentException.class, () -> M5Research.evaluatePayload(raw));
        }
        for (byte[] invalid : List.of("{\"intake_request\":{},\"intake_request\":{}}".getBytes(StandardCharsets.UTF_8),
                "{}{}".getBytes(StandardCharsets.UTF_8), new byte[] {(byte) 0xc3, 0x28},
                "{\"x\":\"\\ud800\"}".getBytes(StandardCharsets.UTF_8)))
            assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeRequest(invalid));
    }

    @Test void persistedAnalysisCannotLoseRequiredCandidatesOrDivergeFromTheOriginalSelector() throws IOException {
        Result result = evaluate(input("peace-building-gift"), new MissingPlan());
        Obj saved = M5PayloadCodec.parseObject(M5PayloadCodec.encodeResult(result), "saved result");
        for (String field : List.of("analysis", "selector_request", "collected_candidate_ids", "collected_domains", "frame")) {
            Obj wrong = saved.with("intake_analysis", without(result.intakeAnalysis(), field));
            assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(wrong)), field);
        }
        for (String field : List.of("collected_candidate_ids", "collected_domains")) {
            Obj wrong = saved.with("intake_analysis", result.intakeAnalysis().with(field, new Arr(List.of())));
            assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(wrong)), field);
        }
        Obj wrongAnalysis = saved.with("intake_analysis", result.intakeAnalysis().with("analysis", obj(Map.of())));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(wrongAnalysis)));
    }

    @Test void savedSummaryAndParticipantFactsCannotAcquirePermissionOrCrossAFrame() throws IOException {
        Result result = evaluate(input("peace-building-gift"), new MissingPlan());
        Obj saved = M5PayloadCodec.parseObject(M5PayloadCodec.encodeResult(result), "saved result");
        Obj consumption = object(saved.get("decision_consumption"), "consumer");
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("decision_consumption", consumption.with("action_authorized", new Bool(true))))));
        Obj participant = object(saved.get("participating_wars"), "participant facts");
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("participating_wars", participant.with("action_authorized", new Bool(true))))));
        Obj frame = object(participant.get("source_frame"), "participant frame");
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("participating_wars",
                participant.with("source_frame", frame.with("revision", new Text("24")))))));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("scope", obj(Map.of())))));
    }

    @Test void unavailableAndObservedEmptyParticipantScopesDoNotBecomeTheSameFact() throws IOException {
        Obj original = input("peace-building-gift"), snapshot = object(original.get("snapshot"), "snapshot");
        Result unavailable = evaluate(original, new MissingPlan());
        assertInstanceOf(ParticipatingWarThreats.Unavailable.class, unavailable.participatingWars());
        Obj living = snapshot.with("played_character", object(snapshot.get("played_character"), "player").with("alive", new Bool(true)));
        Result empty = evaluate(original.with("snapshot", living), new MissingPlan());
        assertInstanceOf(ParticipatingWarThreats.Observed.class, empty.participatingWars());
        ParticipatingWarThreats.Observed observation = (ParticipatingWarThreats.Observed) empty.participatingWars();
        assertTrue(observation.participatingWarIds().isEmpty());
        assertEquals(new ParticipatingWarThreats.Known(BigInteger.ZERO), observation.strength());
        assertNotEquals(M5PayloadCodec.participatingWars(unavailable.participatingWars()), M5PayloadCodec.participatingWars(empty.participatingWars()));
    }

    @Test void sameFrameStructurallyValidParticipantNumbersAndMembershipCannotReplaceTheOriginalSnapshot() throws IOException {
        Obj original = input("peace-building-gift"), snapshot = object(original.get("snapshot"), "snapshot");
        Obj living = snapshot.with("played_character", object(snapshot.get("played_character"), "player").with("alive", new Bool(true)));
        Result result = evaluate(original.with("snapshot", living), new MissingPlan());
        Obj saved = M5PayloadCodec.parseObject(M5PayloadCodec.encodeResult(result), "saved result");
        Obj participant = object(saved.get("participating_wars"), "participant facts");
        Obj count = object(participant.get("strength"), "known empty strength").with("soldiers", new Text("1"));
        assertDoesNotThrow(() -> ParticipatingWarThreatsCodec.decode(encode(participant.with("strength", count))));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("participating_wars", participant.with("strength", count)))));
        Obj otherWar = participant.with("participating_war_ids", new Arr(List.of(integerValue(999))))
                .with("primary_war_ids", new Arr(List.of(integerValue(999))));
        assertDoesNotThrow(() -> ParticipatingWarThreatsCodec.decode(encode(otherWar)));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("participating_wars", otherWar))));
    }

    @Test void activeWarPersistenceRetainsItsCompleteTypedBudgetAndOriginalCommitmentBinding() throws IOException {
        Result result = evaluate(input("aggregate-all-war-occupation"), new MissingPlan());
        Obj saved = M5PayloadCodec.parseObject(M5PayloadCodec.encodeResult(result), "saved result");
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("intake_analysis",
                without(result.intakeAnalysis(), "war_cash_resource")))));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("intake_analysis",
                result.intakeAnalysis().with("war_cash_resource", obj(Map.of()))))));
        Obj cash = object(result.intakeAnalysis().get("war_cash_resource"), "original war budget");
        Obj changed = cash.with("joint_gold_reserve_raw", new IntegerValue(integer(cash.get("joint_gold_reserve_raw"), "reserve").add(BigInteger.ONE)));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeResult(encode(saved.with("intake_analysis",
                result.intakeAnalysis().with("war_cash_resource", changed)))));
    }

    @Test void originalNestedPlayerIdentityProjectionStillReachesTheSameConsumer() throws IOException {
        Obj original = input("peace-building-gift");
        Obj snapshot = without(object(original.get("snapshot"), "snapshot"), "played_character_id");
        Obj intake = original.with("snapshot", snapshot);
        Result actual = evaluate(intake, new MissingPlan());
        assertEquals(M5PayloadCodec.decodeAnalysis(FormalProposalIntake.collect(encode(intake))), actual.intakeAnalysis());
    }

    @Test void wrapperPreservesLargeEvidenceDecimalKindsAndFullDecimalStringIdentities() throws IOException {
        Obj originalPlan = obj(Map.of("ordinary_extension", new Text("x".repeat(140_000)),
                "file_id", new Text("18446744073709551615"), "creation_filetime", new Text("134371688739143606"),
                "opaque_decimal_evidence", new DecimalValue("1.250"), "opaque_exponent", new DecimalValue("1e0"),
                "opaque_negative_zero", new DecimalValue("-0.0"), "selected_step", Nil.INSTANCE));
        Result result = evaluate(input("peace-building-gift"), new ObservedPlan(originalPlan));
        byte[] saved = M5PayloadCodec.encodeResult(result);
        assertTrue(saved.length > 131072, "the outer result must not inherit the smaller original collector input limit");
        Result decoded = M5PayloadCodec.decodeResult(saved);
        assertEquals(originalPlan, ((ObservedPlan) decoded.existingWarPlan()).plan());
        assertArrayEquals(saved, M5PayloadCodec.encodeResult(decoded));
    }

    @Test void acceptedNearRoleBudgetPlanIsPersistedOnceAndReconstructsTheSameConsumer() throws IOException {
        Obj plan = obj(Map.of("ordinary_extension", new Text("x".repeat(M5PayloadCodec.MAXIMUM_BYTES - 50_000)),
                "selected_step", new Text("unchanged-original-step")));
        byte[] request = M5PayloadCodec.encodeRequest(new M5PayloadCodec.Request(input("peace-building-gift"), new ObservedPlan(plan)));
        assertTrue(request.length < M5PayloadCodec.MAXIMUM_BYTES);
        byte[] response = M5Research.evaluatePayload(request);
        assertTrue(response.length < M5PayloadCodec.MAXIMUM_BYTES, "an accepted plan is not duplicated into the response");
        Result saved = M5PayloadCodec.decodeResult(response);
        assertEquals(plan, ((ObservedPlan) saved.existingWarPlan()).plan());
        M5DecisionConsumer.Consumption consumption = M5DecisionConsumer.consume(saved);
        assertEquals(plan.get("selected_step"), ((ObservedPlan) consumption.annotatedPlan()).plan().get("selected_step"));
        Obj receipt = object(M5PayloadCodec.parseObject(response, "response").get("decision_consumption"), "consumer receipt");
        assertFalse(receipt.members().containsKey("existing_war_plan"));
        assertFalse(receipt.members().containsKey("war_decision_reason_scope_v1"));
        assertEquals(new Text("participating_wars"), receipt.get("participant_observation_source_field"));
    }

    @Test void sharedG2WireReachesTheM5OperationAndRejectsUnversionedOrUnknownDispatch() throws IOException {
        M5PayloadCodec.Request context = new M5PayloadCodec.Request(input("five-family-proposals-original-rank"), new MissingPlan());
        byte[] operation = M5PayloadCodec.encodeContextOperation(context);
        G2Source source = new G2Source("synthetic-test-machine", "2026-10-22T20:45:06Z", "synthetic-no-native-qualification",
                new ExactRef("synthetic-fixture", 0, "0".repeat(64)));
        G2Request request = new G2Request("synthetic-m5-operation", Milestone.M5, source,
                ProjectionJson.object(operation, M5PayloadCodec.MAXIMUM_BYTES));
        G2Response response = new M5Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        G2Response saved = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertEquals(request.requestId(), saved.requestId()); assertEquals(source, saved.source());
        Result actual = M5PayloadCodec.decodeResult(saved.result().bytes());
        assertEquals(5, array(actual.intakeAnalysis().get("collected_candidate_ids"), "original five candidates").size());
        Obj parsed = M5PayloadCodec.parseObject(operation, "operation");
        for (Obj invalid : List.of(without(parsed, "operation"), parsed.with("operation", new Text("submit")),
                parsed.with("schema", new Text("xar.g2-m5-request/v2")), parsed.with("extra", Nil.INSTANCE)))
            assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeOperation(encode(invalid)));
        assertThrows(IllegalArgumentException.class, () -> M5PayloadCodec.decodeOperation(M5PayloadCodec.encodeRequest(context)),
                "the old unversioned inner payload is not a fallback alias");
    }

    @Test void sharedG2LifecycleOperationPreservesUnknownAndBodyConflictWithoutDispatch() {
        ObjectNode input = ProposalLifecycleFixtures.request();
        Obj proposed = lifecycle(input);
        assertEquals(new Text("PROPOSED"), proposed.get("status"));
        Obj proposal = object(proposed.get("proposal"), "proposed lifecycle action");
        String sha = text(proposal.get("body_sha256"), "actual proposed body digest");
        assertEquals(new Bool(false), proposal.get("dispatch_allowed"));
        ObjectNode unknown = input.deepCopy();
        ((ArrayNode) unknown.get("external_facts")).add(ProposalLifecycleFixtures.fact(
                "lifecycle-war0", sha, "UNKNOWN", "DOMAIN", "war", 7));
        Obj deferred = lifecycle(unknown);
        assertEquals(new Text("DEFERRED"), deferred.get("status"));
        assertEquals(new Text("EXISTING_UNKNOWN"), deferred.get("deferred_reason"));
        assertEquals(Nil.INSTANCE, deferred.get("proposal"));
        ObjectNode conflicting = input.deepCopy();
        String changed = sha.equals("f".repeat(64)) ? "e".repeat(64) : "f".repeat(64);
        ((ArrayNode) conflicting.get("external_facts")).add(ProposalLifecycleFixtures.fact(
                "lifecycle-war0", changed, "UNKNOWN", "DOMAIN", "war", 7));
        assertEquals(new Text("BODY_CONFLICT"), lifecycle(conflicting).get("status"));
        for (Obj outcome : List.of(proposed, deferred, lifecycle(conflicting))) {
            assertEquals(new Bool(false), outcome.get("formal_action_ready"));
            assertEquals(new Bool(false), outcome.get("resource_reservation_performed"));
            assertEquals(new Bool(false), outcome.get("intent_durable"));
        }
        ObjectNode larger = input.deepCopy();
        ObjectNode expectedValue = (ObjectNode) larger.get("intents").get(0).get("expected").get("values").get(0);
        expectedValue.put("kind", "TEXT"); expectedValue.put("value", "x".repeat(70_001));
        Obj largeResult = lifecycle(larger);
        assertEquals(new Text("PROPOSED"), largeResult.get("status"));
        assertTrue(encode(largeResult).length > 65_536, "M5 must retain the qualified lifecycle payload boundary");
    }

    private static Obj lifecycle(ObjectNode input) {
        Obj operation = new Obj(Map.of("schema", new Text(M5PayloadCodec.OPERATION_SCHEMA),
                "operation", new Text("proposal_lifecycle"), "request",
                M5PayloadCodec.parseObject(ProposalLifecycleCodec.encodePayload(input), "lifecycle input")));
        G2Request request = new G2Request("synthetic-m5-lifecycle", Milestone.M5, ProposalLifecycleFixtures.source(),
                ProjectionJson.object(encode(operation), M5PayloadCodec.MAXIMUM_BYTES));
        G2Response actual = new M5Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        G2Response saved = G2Wire.decodeResponse(G2Wire.encodeResponse(actual));
        assertArrayEquals(actual.result().bytes(), saved.result().bytes());
        return M5PayloadCodec.parseObject(saved.result().bytes(), "actual G2 lifecycle result");
    }

    private static Obj army(int id, int soldiers) {
        return obj(Map.of("army_id", integerValue(id), "soldiers", integerValue(soldiers)));
    }
    private static IntegerValue integerValue(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Obj obj(Map<String, Value> fields) { return new Obj(fields); }
}
