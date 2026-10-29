package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.IOException;
import java.net.URI;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignScheduleCodec;

/** Exact produced software fixtures through the one real host, with fresh typed consumers. */
@QuarkusTest
class M7ScheduleHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;

    @Test void actualProducerGoalOrdinaryAndPersistedScheduleChainUsesTheSameHttpProvider() throws IOException {
        byte[] goal = null;
        byte[] goalPlan = null;
        byte[] state = null;
        byte[] ordinary = null;
        try (G2JavaClient client = new G2JavaClient(new G2ClientConfig(
                URI.create("http://127.0.0.1:" + endpoint.getPort()), Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES))) {
            for (String operation : List.of("goal-new", "goal-plan", "new", "read", "ordinary-consume", "plan")) {
                byte[] requestBytes = resource("M7.schedule." + operation + ".request.json");
                byte[] expected = resource("M7.schedule." + operation + ".result.json");
                var request = G2Wire.decodeRequest(requestBytes);
                assertEquals(Milestone.M7, request.milestone());
                var result = client.evaluateWithEvidence(request);
                assertTrue(result.evidence().actualHttpInvoked());
                assertTrue(result.evidence().responseComplete());
                assertEquals(200, result.evidence().httpStatus().orElseThrow());
                assertEquals(request.requestId(), result.response().requestId());
                assertEquals(request.source(), result.response().source());
                byte[] actual = result.response().result().bytes();
                assertArrayEquals(expected, actual, "actual producer bytes via HTTP: " + operation);
                var freshWire = G2Wire.decodeResponse(G2Wire.encodeResponse(result.response()));
                assertArrayEquals(actual, freshWire.result().bytes());
                var input = StrictJson.parse(request.payload().bytes(), StrictJson.EXPLICIT_MAX_BYTES).get("input");
                switch (operation) {
                    case "goal-new" -> {
                        goal = actual;
                        assertArrayEquals(goal, GoalCodec.encodeGoal(GoalCodec.decodeGoal(goal)));
                    }
                    case "goal-plan" -> {
                        assertNotNull(goal);
                        assertEquals(StrictJson.parse(goal), input);
                        goalPlan = actual;
                        assertArrayEquals(goalPlan, GoalCodec.encodePlan(GoalCodec.decodePlan(goalPlan)));
                    }
                    case "new" -> {
                        assertNotNull(goal);
                        state = actual;
                        var fresh = OrdinaryCampaignScheduleCodec.decodeState(state);
                        assertEquals(GoalCodec.decodeGoal(goal), fresh.goal());
                        assertArrayEquals(state, OrdinaryCampaignScheduleCodec.encodeState(fresh));
                    }
                    case "read" -> {
                        assertNotNull(state);
                        assertEquals(StrictJson.parse(state), input);
                        assertArrayEquals(state, actual);
                        assertArrayEquals(actual, OrdinaryCampaignScheduleCodec.encodeState(
                                OrdinaryCampaignScheduleCodec.decodeState(actual)));
                    }
                    case "ordinary-consume" -> {
                        assertNotNull(goal);
                        assertNotNull(goalPlan);
                        assertEquals(StrictJson.parse(goal), input.path("observation").get("goal"));
                        ordinary = actual;
                        var fresh = M7OrdinaryPlanConsumer.decode(ordinary);
                        assertArrayEquals(goalPlan, GoalCodec.encodePlan(fresh.campaignGoalPlanUsed()));
                        assertFalse(fresh.gameActionsSubmitted());
                        assertFalse(fresh.coldAuthorityGranted());
                        assertFalse(fresh.replayAuthorized());
                    }
                    case "plan" -> {
                        assertNotNull(state);
                        assertNotNull(ordinary);
                        assertNotNull(goalPlan);
                        assertEquals(StrictJson.parse(state), input.get("state"));
                        assertEquals(StrictJson.parse(ordinary), input.get("ordinary_plan"));
                        var fresh = OrdinaryCampaignScheduleCodec.decodePlan(actual);
                        assertEquals(M7OrdinaryPlanConsumer.decode(ordinary), fresh.ordinaryPlan());
                        assertArrayEquals(goalPlan, GoalCodec.encodePlan(fresh.ordinaryPlan().campaignGoalPlanUsed()));
                        assertArrayEquals(actual, OrdinaryCampaignScheduleCodec.encodePlan(fresh));
                        assertFalse(fresh.gameActionsSubmitted());
                        assertFalse(fresh.coldAuthorityGranted());
                        assertFalse(fresh.replayAuthorized());
                        assertEquals(0, fresh.savedDayCredit());
                    }
                    default -> throw new IllegalStateException("unlisted retained fixture operation");
                }
            }
        }
        assertNotNull(goal);
        assertNotNull(goalPlan);
        assertNotNull(state);
        assertNotNull(ordinary);
    }

    private static byte[] resource(String name) throws IOException {
        try (var input = M7ScheduleHttpTest.class.getResourceAsStream("/g2-http/" + name)) {
            assertNotNull(input, "actual produced schedule fixture is mandatory; missing is RED: " + name);
            byte[] raw = input.readNBytes(1_048_577);
            assertTrue(raw.length > 0 && raw.length <= StrictJson.EXPLICIT_MAX_BYTES);
            return raw;
        }
    }
}
