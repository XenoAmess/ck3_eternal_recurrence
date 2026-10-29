package org.xar.ck3.control.g2.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetCodec;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

final class ProposalLifecycleTest {
    @Test void realOriginalEvaluationCreatesOnlyAProposedBoundaryWithoutReservationOrDispatch() {
        ObjectNode request = ProposalLifecycleFixtures.request(); Input input = ProposalLifecycleCodec.decode(raw(request), source());
        Proposed plan = assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(request), source()));
        assertEquals(JointBudgetSelector.select(input.evaluationInput()), plan.evaluation()); assertEquals("war0", plan.action().body().candidate().candidateId());
        assertFalse(plan.action().dispatchAllowed()); assertFalse(plan.action().intentDurable()); assertFalse(plan.evaluation().formalActionReady());
        assertEquals(ProposalLifecycleCodec.bodyDigest(plan.action().body()), plan.action().bodySha256());
        assertEquals(source(), plan.action().body().source());
    }
    @Test void actualCommonWireRoundtripPreservesTheCanonicalResultAndExactUnsignedBirthString() {
        byte[] result = ProposalLifecycleCodec.evaluateG2Payload(raw(ProposalLifecycleFixtures.request()), source());
        G2Response response = new G2Response("lifecycle-roundtrip", Milestone.M5, source(), ProjectionJson.value(result, ProjectionJson.MAX_BYTES));
        G2Response consumed = G2Wire.decodeResponse(G2Wire.encodeResponse(response)); assertArrayEquals(result, consumed.result().bytes());
        assertEquals(source(), consumed.source()); JsonNode row = StrictJson.parse(consumed.result().bytes(), ProposalLifecycleCodec.MAX_BYTES);
        assertEquals("PROPOSED", row.get("status").textValue()); assertTrue(row.at("/proposal/body/observed/game/creation_filetime").isTextual());
        assertEquals("18446744073709551615", row.at("/proposal/body/observed/game/creation_filetime").textValue());
        assertArrayEquals(result, StrictJson.canonical(row, ProposalLifecycleCodec.MAX_BYTES));
    }
    @Test void sameUnknownStaysBlockedEvenWhenExpectedFieldsAlreadyMatch() {
        ObjectNode request = ProposalLifecycleFixtures.request(); Proposed first = proposed(request);
        ((ArrayNode) request.get("external_facts")).add(ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(), "UNKNOWN", "GLOBAL", "war", -1));
        assertEquals(ObservationComparison.EXPECTED_FIELDS_MATCH, compare(first.action().body().expected(), first.action().body().observed(), source(), "xar.synthetic-observation/v1", first.action().body().expected().values()));
        Deferred next = assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), source())); assertEquals(DeferredReason.EXISTING_UNKNOWN, next.reason());
        assertEquals(ExternalState.UNKNOWN, next.blockingFacts().getFirst().state());
        assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), source()), "repeat planning does not become a second submission");
    }
    @Test void aDifferentBodyForTheSameActionIdIsAConflictAndDoesNotReplaceTheOriginalFact() {
        ObjectNode request = ProposalLifecycleFixtures.request(); Proposed first = proposed(request);
        ObjectNode fact = ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(), "UNKNOWN", "GLOBAL", "war", -1);
        ((ArrayNode) request.get("external_facts")).add(fact);
        ((ObjectNode) request.at("/intents/0/expected/values/0")).put("value", false);
        Conflict conflict = assertInstanceOf(Conflict.class, ProposalLifecycleCodec.evaluate(raw(request), source()));
        assertEquals(first.action().bodySha256(), conflict.priorBodySha256()); assertNotEquals(conflict.priorBodySha256(), conflict.proposedBodySha256()); assertEquals("UNKNOWN", fact.get("state").textValue());
    }
    @Test void ackReceivedCannotStandForVerifiedEffectAndConfirmedFactsCannotBeReplayed() {
        for (String state : List.of("ACK_RECEIVED", "APPLIED_CONFIRMED", "REJECTED_CONFIRMED")) {
            ObjectNode request = ProposalLifecycleFixtures.request(); Proposed first = proposed(request);
            ((ArrayNode) request.get("external_facts")).add(ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(), state, "GLOBAL", "war", -1));
            Deferred plan = assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), source()));
            assertEquals(state.equals("ACK_RECEIVED") ? DeferredReason.EXISTING_UNKNOWN : DeferredReason.ALREADY_RECORDED, plan.reason());
        }
    }
    @Test void unknownIsolationOnlyAllowsProvenIndependentPlanningAndNeverReclassifiesTheFact() {
        ObjectNode request = ProposalLifecycleFixtures.request();
        ArrayNode facts = (ArrayNode) request.get("external_facts"); facts.add(ProposalLifecycleFixtures.fact("other-action", "1".repeat(64), "UNKNOWN", "DOMAIN", "building", -1));
        assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(request), source()));
        facts.removeAll(); facts.add(ProposalLifecycleFixtures.fact("other-action", "1".repeat(64), "UNKNOWN", "CLAIMS", "war", 999));
        assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(request), source()));
        facts.removeAll(); facts.add(ProposalLifecycleFixtures.fact("other-action", "1".repeat(64), "UNKNOWN", "CLAIMS", "war", 7));
        assertEquals(DeferredReason.EXISTING_UNKNOWN, assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), source())).reason());
        facts.removeAll(); facts.add(ProposalLifecycleFixtures.fact("other-action", "1".repeat(64), "UNKNOWN", "GLOBAL", "building", -1));
        assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), source()));
    }
    @Test void expectedComparisonRejectsSourceBuildVersionGameEpisodeAndBackwardsFrameDrift() {
        Proposed first = proposed(ProposalLifecycleFixtures.request()); ProposedBody body = first.action().body(); ExpectedPostcondition expected = body.expected(); ObservationIdentity before = body.observed();
        G2Source changed = new G2Source(source().machineId(), source().observedAtUtc(), "other-build", source().sourceRef());
        assertEquals(ObservationComparison.SOURCE_DRIFT, compare(expected, before, changed, expected.observerSchema(), expected.values()));
        ObservationIdentity version = new ObservationIdentity(before.machineId(), before.game(), before.frame(), 2);
        assertEquals(ObservationComparison.STALE_VERSION, compare(expected, version, source(), expected.observerSchema(), expected.values()));
        ObservationIdentity game = new ObservationIdentity(before.machineId(), new GameGeneration(8, new PythonOnlyUInt64(BigInteger.ONE)), before.frame(), before.observationVersion());
        assertEquals(ObservationComparison.GAME_OR_EPISODE_DRIFT, compare(expected, game, source(), expected.observerSchema(), expected.values()));
        var frame = before.frame(); var episode = new JointBudgetSelector.ProposalFrame(frame.identity(), frame.snapshotId(), frame.revision(), "other-episode");
        assertEquals(ObservationComparison.GAME_OR_EPISODE_DRIFT, compare(expected, new ObservationIdentity(before.machineId(), before.game(), episode, 1), source(), expected.observerSchema(), expected.values()));
        var old = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(frame.identity().player(), BigInteger.ONE, frame.identity().dateRaw()), frame.snapshotId(), frame.revision(), frame.episodeRunId());
        assertEquals(ObservationComparison.STALE_VERSION, compare(expected, new ObservationIdentity(before.machineId(), before.game(), old, 1), source(), expected.observerSchema(), expected.values()));
    }
    @Test void missingExpectedInputAndMissingAssessmentStayExplicitWithoutInventingAProposal() {
        ObjectNode request = ProposalLifecycleFixtures.request(); ((ArrayNode) request.get("intents")).removeAll();
        assertEquals(DeferredReason.MISSING_EXPECTED_POSTCONDITION, assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), source())).reason());
        ((ArrayNode) request.at("/joint_budget_request/assessments")).removeAll();
        assertEquals(DeferredReason.MISSING_ASSESSMENTS, assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), source())).reason());
    }
    @Test void strictVersionsBirthIdentityMissingAndExtraFieldsCannotBeCoercedIntoAProposal() {
        for (String token : List.of("true", "1.0", "\"1\"", "null", "2")) {
            String valid = new String(raw(ProposalLifecycleFixtures.request()), StandardCharsets.UTF_8);
            String invalid = valid.replace("\"version\":1", "\"version\":" + token);
            assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(invalid.getBytes(StandardCharsets.UTF_8), source()));
        }
        ObjectNode extra = ProposalLifecycleFixtures.request(); extra.put("allow_submit", true); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(extra), source()));
        ObjectNode missing = ProposalLifecycleFixtures.request(); missing.remove("external_facts"); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(missing), source()));
        ObjectNode birth = ProposalLifecycleFixtures.request(); ((ObjectNode) birth.at("/observation/game")).put("creation_filetime", 1L);
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(birth), source()));
        G2Source zero = new G2Source(source().machineId(), source().observedAtUtc(), source().exactBuild(), new ExactRef("no-original", 0, "0".repeat(64)));
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(ProposalLifecycleFixtures.request()), zero));
    }
    @Test void explicitNullAbsentBooleanAndIntegerObservationsRemainDistinctAndRoundtrip() {
        ObjectNode request = ProposalLifecycleFixtures.request(); ArrayNode values = (ArrayNode) request.at("/intents/0/expected/values"); values.removeAll();
        values.addObject().put("field", "null_field").put("kind", "NULL").putNull("value"); values.addObject().put("field", "missing_field").put("kind", "ABSENT");
        values.addObject().put("field", "count").put("kind", "INTEGER").put("value", 1);
        Proposed proposed = proposed(request); byte[] encoded = ProposalLifecycleCodec.encode(proposed); JsonNode consumed = StrictJson.parse(encoded, ProposalLifecycleCodec.MAX_BYTES);
        assertEquals("NULL", consumed.at("/proposal/body/expected/values/0/kind").textValue()); assertTrue(consumed.at("/proposal/body/expected/values/0/value").isNull());
        assertFalse(consumed.at("/proposal/body/expected/values/1").has("value"));
        ((ObjectNode) values.get(2)).put("value", true); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(request), source()));
    }
    @Test void completeLifecycleProducerAndWireConsumerAcceptAbove64KiBWithinTheExplicitRoleBudget() {
        ObjectNode request = ProposalLifecycleFixtures.request(); ObjectNode value = (ObjectNode) request.at("/intents/0/expected/values/0"); value.put("kind", "TEXT"); value.put("value", "x".repeat(70_001));
        byte[] input = raw(request); assertTrue(input.length > 65536); assertTrue(input.length < ProposalLifecycleCodec.MAX_BYTES);
        byte[] result = ProposalLifecycleCodec.evaluateG2Payload(input, source()); assertTrue(result.length > 65536);
        G2Response response = G2Wire.decodeResponse(G2Wire.encodeResponse(new G2Response("large-lifecycle", Milestone.M5, source(), ProjectionJson.value(result, ProjectionJson.MAX_BYTES))));
        assertArrayEquals(result, response.result().bytes()); assertEquals(70_001, StrictJson.parse(response.result().bytes(), ProposalLifecycleCodec.MAX_BYTES).at("/proposal/body/expected/values/0/value").textValue().length());
        byte[] tooLarge = new String(input, StandardCharsets.UTF_8).replace("x".repeat(70_001), "x".repeat(ProposalLifecycleCodec.MAX_BYTES)).getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(tooLarge, source()));
    }
    @Test void malformedDuplicateAndTrailingPayloadsAreRejectedByTheActualProducer() {
        String valid = new String(raw(ProposalLifecycleFixtures.request()), StandardCharsets.UTF_8);
        String duplicate = valid.replaceFirst("\\{", "{\"schema\":\"duplicate\",");
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(duplicate.getBytes(StandardCharsets.UTF_8), source()));
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate((valid + " {}").getBytes(StandardCharsets.UTF_8), source()));
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(new byte[] {(byte) 0xc3, (byte) 0x28}, source()));
    }
    @Test void nativeAndWriterEvidenceIsImmutableInputAndNotCreatedOrSettledByPlanning() {
        ObjectNode request = ProposalLifecycleFixtures.request(); Proposed first = proposed(request);
        ((ArrayNode) request.get("external_facts")).add(ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(), "UNKNOWN", "GLOBAL", "war", -1));
        Input input = ProposalLifecycleCodec.decode(raw(request), source()); assertThrows(UnsupportedOperationException.class, () -> input.externalFacts().clear());
        assertThrows(UnsupportedOperationException.class, () -> input.intents().clear());
        Plan plan = ProposalLifecycle.plan(input, ProposalLifecycleCodec::bodyDigest); assertInstanceOf(Deferred.class, plan); assertEquals(ExternalState.UNKNOWN, input.externalFacts().getFirst().state());
        assertArrayEquals(JointBudgetCodec.encode(JointBudgetSelector.select(input.evaluationInput())), JointBudgetCodec.encode(plan.evaluation()));
    }
    @Test void aPriorFactFromAnotherGameCannotBeSilentlyAppliedOrDropped() {
        ObjectNode request = ProposalLifecycleFixtures.request(); ObjectNode fact = ProposalLifecycleFixtures.fact("other-action", "1".repeat(64), "UNKNOWN", "GLOBAL", "war", -1);
        ((ObjectNode) fact.at("/origin/game")).put("pid", 8); ((ArrayNode) request.get("external_facts")).add(fact);
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(request), source()));
    }
    @Test void serializationRejectsAValidLookingDigestThatDoesNotBindTheOriginalBody() {
        Proposed first = proposed(ProposalLifecycleFixtures.request());
        Proposed forged = new Proposed(first.evaluation(), new ProposedAction(first.action().body(), "f".repeat(64)));
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.encode(forged));
    }
    @Test void producerRejectsUnpairedUnicodeAndAcceptsLargePairedUnicodeWithoutTheOldTextCap() {
        ObjectNode request = ProposalLifecycleFixtures.request(); ObjectNode value = (ObjectNode) request.at("/intents/0/expected/values/0"); value.put("kind", "TEXT"); value.put("value", "sentinel");
        String valid = new String(raw(request), StandardCharsets.UTF_8); String unpaired = valid.replace("sentinel", "\\ud800");
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(unpaired.getBytes(StandardCharsets.UTF_8), source()));
        value.put("value", "\ud83d\ude00".repeat(35_001)); byte[] input = raw(request); assertTrue(input.length > 65536);
        JsonNode result = StrictJson.parse(ProposalLifecycleCodec.evaluateG2Payload(input, source()), ProposalLifecycleCodec.MAX_BYTES);
        String actual = result.at("/proposal/body/expected/values/0/value").textValue(); assertEquals(35_001, actual.codePointCount(0, actual.length()));
    }
    @Test void refreshingSourceMetadataCannotDisguiseAnExistingUnknownAsTheSameActionBody() {
        ObjectNode request = ProposalLifecycleFixtures.request(); Proposed first = proposed(request);
        ((ArrayNode) request.get("external_facts")).add(ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(), "UNKNOWN", "GLOBAL", "war", -1));
        G2Source refreshed = new G2Source(source().machineId(), "2026-10-22T00:00:01Z", source().exactBuild(), source().sourceRef());
        assertInstanceOf(Conflict.class, ProposalLifecycleCodec.evaluate(raw(request), refreshed));
        assertEquals("UNKNOWN", request.at("/external_facts/0/state").textValue());
    }
    @Test void nativeExtensionDecimalIsProjectedByTheOriginalBudgetCodecRatherThanRejectedByANewGlobalIntegerRule() {
        ObjectNode request = ProposalLifecycleFixtures.request(); Proposed original = proposed(request);
        for (double token : List.of(1.0, 1.25)) {
            ((ObjectNode) request.at("/joint_budget_request/snapshot")).put("opaque_native_decimal", token);
            Proposed projected = proposed(request); assertEquals(original.evaluation(), projected.evaluation()); assertEquals(original.action(), projected.action());
        }
        for (double token : List.of(1.0, 1.25)) {
            ((ObjectNode) request.at("/joint_budget_request/assessments/0")).put("benefit_units", token);
            assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(request), source()));
        }
    }
    @Test void newObservationIdentityUsesCanonicalDecimalStringsWhileTheOriginalBudgetAbiRemainsNumeric() {
        ObjectNode request = ProposalLifecycleFixtures.request(); BigInteger maximum = new BigInteger("18446744073709551615");
        replaceRevisions(request.get("joint_budget_request"), maximum);
        assertTrue(request.at("/joint_budget_request/intake/native_revision").isIntegralNumber());
        Proposed plan = proposed(request); ObjectNode observed = ProposalLifecycleCodec.observation(plan.action().body().observed());
        assertEquals(plan.action().body().observed(), ProposalLifecycleCodec.decodeObservation(observed));
        for (String name : List.of("played_character_id", "native_revision", "date_raw", "revision")) assertTrue(observed.get("frame").get(name).isTextual());
        assertEquals(maximum.toString(), observed.at("/frame/native_revision").textValue());
        byte[] result = ProposalLifecycleCodec.encode(plan);
        G2Response consumed = G2Wire.decodeResponse(G2Wire.encodeResponse(new G2Response("max-revision", Milestone.M5, source(), ProjectionJson.value(result, ProjectionJson.MAX_BYTES))));
        assertEquals(maximum.toString(), StrictJson.parse(consumed.result().bytes(), ProposalLifecycleCodec.MAX_BYTES).at("/proposal/body/observed/frame/revision").textValue());
        ObjectNode frame = (ObjectNode) observed.get("frame"); frame.put("native_revision", 2L);
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeObservation(observed));
        frame.put("native_revision", "02"); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeObservation(observed));
        frame.put("native_revision", maximum.add(BigInteger.ONE).toString()); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeObservation(observed));
    }
    @Test void newNumericExpectedValuesAndExternalFactIdsRejectTheUnsafeJavaScriptIntegerRange() {
        ObjectNode request = ProposalLifecycleFixtures.request(); ObjectNode value = (ObjectNode) request.at("/intents/0/expected/values/0"); value.put("kind", "INTEGER");
        BigInteger maximum = BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER);
        for (BigInteger accepted : List.of(maximum, maximum.negate())) { value.put("value", accepted); assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(request), source())); }
        for (BigInteger rejected : List.of(maximum.add(BigInteger.ONE), maximum.add(BigInteger.ONE).negate())) {
            value.put("value", rejected); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(request), source()));
            assertThrows(IllegalArgumentException.class, () -> new ExpectedInteger(new FieldKey("count"), rejected));
        }
        ObjectNode normal = ProposalLifecycleFixtures.request(); ObjectNode fact = ProposalLifecycleFixtures.fact("other-action", "1".repeat(64), "UNKNOWN", "CLAIMS", "war", 7);
        ((ArrayNode) fact.at("/claims/army_ids")).removeAll().add(maximum.add(BigInteger.ONE)); ((ArrayNode) normal.get("external_facts")).add(fact);
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(normal), source()));
    }
    private static void replaceRevisions(JsonNode value, BigInteger revision) {
        if (value instanceof ObjectNode object) {
            if (object.has("native_revision")) object.put("native_revision", revision);
            if (object.has("revision")) object.put("revision", revision);
        }
        if (value.isContainerNode()) value.forEach(child -> replaceRevisions(child, revision));
    }
    private static Proposed proposed(ObjectNode request) { return assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(request), source())); }
    private static byte[] raw(ObjectNode value) { return ProposalLifecycleCodec.encodePayload(value); }
    private static G2Source source() { return ProposalLifecycleFixtures.source(); }
}
