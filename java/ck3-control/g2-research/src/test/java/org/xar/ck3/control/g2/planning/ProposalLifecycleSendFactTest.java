package org.xar.ck3.control.g2.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Pure actual planner/codec consumers. Synthetic external DATA never qualifies a native send or relationship. */
final class ProposalLifecycleSendFactTest {
    @Test void exactConfirmedSendIsAlreadyRecordedWithoutAppliedOrUnknownReclassification() {
        var request = ProposalLifecycleFixtures.request(); var first = proposed(request);
        facts(request).add(ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(),
                "SEND_CONFIRMED", "GLOBAL", "war", -1));
        var plan = assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), ProposalLifecycleFixtures.source()));
        assertEquals(DeferredReason.ALREADY_RECORDED, plan.reason());
        var fact = plan.blockingFacts().getFirst(); assertEquals(ExternalState.SEND_CONFIRMED, fact.state());
        assertFalse(fact.unresolved()); assertNotEquals(ExternalState.APPLIED_CONFIRMED, fact.state());
        assertEquals(plan, ProposalLifecycleCodec.evaluate(raw(request), ProposalLifecycleFixtures.source()));
    }

    @Test void terminalSendDoesNotKeepGlobalDomainOrResourceUnknownIsolation() {
        for (String scope : List.of("GLOBAL", "DOMAIN", "CLAIMS")) {
            var request = ProposalLifecycleFixtures.request();
            facts(request).add(ProposalLifecycleFixtures.fact("other-send", "1".repeat(64), "SEND_CONFIRMED", scope, "war", 7));
            var plan = assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(request), ProposalLifecycleFixtures.source()));
            assertFalse(plan.action().dispatchAllowed()); assertFalse(plan.action().intentDurable());
        }
    }

    @Test void unrelatedUnknownRemainsAnUnresolvedBarrierBesideAConfirmedSend() {
        var request = ProposalLifecycleFixtures.request();
        facts(request).add(ProposalLifecycleFixtures.fact("other-send", "1".repeat(64), "SEND_CONFIRMED", "GLOBAL", "war", -1));
        facts(request).add(ProposalLifecycleFixtures.fact("other-unknown", "2".repeat(64), "UNKNOWN", "GLOBAL", "war", -1));
        var plan = assertInstanceOf(Deferred.class, ProposalLifecycleCodec.evaluate(raw(request), ProposalLifecycleFixtures.source()));
        assertEquals(DeferredReason.EXISTING_UNKNOWN, plan.reason());
        assertEquals(List.of(ExternalState.UNKNOWN), plan.blockingFacts().stream().map(ExternalFact::state).toList());
        assertTrue(plan.blockingFacts().getFirst().unresolved());
    }

    @Test void fullProducerAndCommonWirePreserveTheDistinctSendFactWithoutSubmissionCredit() {
        var request = ProposalLifecycleFixtures.request(); var first = proposed(request);
        facts(request).add(ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(),
                "SEND_CONFIRMED", "GLOBAL", "war", -1));
        var input = ProposalLifecycleCodec.decode(raw(request), ProposalLifecycleFixtures.source());
        var fact = input.externalFacts().getFirst();
        assertEquals(ProposalLifecycleCodec.FACT_SCHEMA, ProposalLifecycleCodec.fact(fact).get("schema").textValue());
        assertEquals(fact, ProposalLifecycleCodec.decodeFact(ProposalLifecycleCodec.fact(fact)));
        byte[] result = ProposalLifecycleCodec.evaluateG2Payload(raw(request), ProposalLifecycleFixtures.source());
        var actual = G2Wire.decodeResponse(G2Wire.encodeResponse(new G2Response("send-fact", Milestone.M5,
                ProposalLifecycleFixtures.source(), ProjectionJson.value(result, ProjectionJson.MAX_BYTES))));
        assertArrayEquals(result, actual.result().bytes());
        var row = StrictJson.parse(actual.result().bytes(), ProposalLifecycleCodec.MAX_BYTES);
        assertEquals("DEFERRED", row.get("status").textValue());
        assertEquals("ALREADY_RECORDED", row.get("deferred_reason").textValue());
        assertEquals("SEND_CONFIRMED", row.at("/blocking_facts/0/state").textValue());
        for (String field : List.of("formal_action_ready", "resource_reservation_performed", "intent_durable")) {
            assertTrue(row.has(field)); assertFalse(row.get(field).booleanValue());
        }
        assertTrue(row.get("proposal").isNull());
    }

    @Test void allHistoricalStatesRetainTheirExactMeaningAndClosedSerialization() {
        for (ExternalState state : ExternalState.values()) {
            var fact = ProposalLifecycleCodec.decodeFact(ProposalLifecycleFixtures.fact("historical-fact", "3".repeat(64),
                    state.name(), "GLOBAL", "war", -1));
            assertEquals(state, fact.state());
            assertEquals(state == ExternalState.UNKNOWN || state == ExternalState.ACK_RECEIVED, fact.unresolved());
            assertEquals(fact, ProposalLifecycleCodec.decodeFact(ProposalLifecycleCodec.fact(fact)));
            var historical = ProposalLifecycleCodec.fact(fact); historical.remove("schema");
            assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeFact(historical));
            if (state == ExternalState.SEND_CONFIRMED)
                assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeHistoricalFactV1(historical));
            else assertEquals(fact, ProposalLifecycleCodec.decodeHistoricalFactV1(historical));
        }
        for (String invalid : List.of("send_confirmed", "SEND", "APPLIED", "", "NEW_TERMINAL")) {
            var fact = ProposalLifecycleFixtures.fact("bad-state", "4".repeat(64), invalid, "GLOBAL", "war", -1);
            assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeFact(fact));
        }
        var wrongType = ProposalLifecycleFixtures.fact("bad-state", "4".repeat(64), "SEND_CONFIRMED", "GLOBAL", "war", -1);
        wrongType.put("state", true); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeFact(wrongType));
        wrongType.putNull("state"); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeFact(wrongType));
        wrongType.remove("state"); assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeFact(wrongType));
        var wrongSchema = ProposalLifecycleFixtures.fact("bad-schema", "4".repeat(64), "SEND_CONFIRMED", "GLOBAL", "war", -1);
        wrongSchema.put("schema", "xar.java-action-external-fact/v1");
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeFact(wrongSchema));
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeHistoricalFactV1(wrongSchema));
    }

    @Test void confirmedSendStillRejectsBodyConflictsAndForeignGameFacts() {
        var request = ProposalLifecycleFixtures.request(); var first = proposed(request);
        facts(request).add(ProposalLifecycleFixtures.fact(first.action().body().actionId(), first.action().bodySha256(),
                "SEND_CONFIRMED", "GLOBAL", "war", -1));
        ((ObjectNode) request.at("/intents/0/expected/values/0")).put("value", false);
        var conflict = assertInstanceOf(Conflict.class, ProposalLifecycleCodec.evaluate(raw(request), ProposalLifecycleFixtures.source()));
        assertEquals(first.action().bodySha256(), conflict.priorBodySha256());
        ((ObjectNode) request.at("/external_facts/0/origin/game")).put("pid", 99);
        assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.evaluate(raw(request), ProposalLifecycleFixtures.source()));
    }

    private static ArrayNode facts(ObjectNode request) { return (ArrayNode) request.get("external_facts"); }
    private static byte[] raw(ObjectNode value) { return ProposalLifecycleCodec.encodePayload(value); }
    private static Proposed proposed(ObjectNode value) {
        return assertInstanceOf(Proposed.class, ProposalLifecycleCodec.evaluate(raw(value), ProposalLifecycleFixtures.source()));
    }
}
