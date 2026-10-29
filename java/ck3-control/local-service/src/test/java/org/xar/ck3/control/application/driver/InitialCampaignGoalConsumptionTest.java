package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software producer/consumer regression. These framed data grant no Native or Root authority. */
final class InitialCampaignGoalConsumptionTest {
    private static final Instant NOW = Instant.parse("2026-10-25T00:00:00Z");
    private static final String EPISODE = "software-initial-ordinary-episode";
    private static final long ACTOR = 29829;
    private static final BigInteger RAW = BigInteger.valueOf(24000);
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    @TempDir Path temporary;

    @Test void initialOrdinaryProducerPersistsGoalAndOrdinaryCoreUsesItBeforeCrossRunWar() throws Exception {
        var actual = frame();
        var produced = InitialDriverState.create(actual, "software-pipe", EPISODE,
                policy(InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION));
        var restored = DriverStateSnapshot.decodeComplete(produced.driver().encode());
        assertArrayEquals(produced.driver().encode(), restored.encode());
        var slot = assertInstanceOf(DriverStateSnapshot.Value.class, restored.campaignGoal());
        var goal = GoalCodec.decodeGoal(slot.json());
        assertEquals(EPISODE, goal.campaignId());
        assertEquals(ACTOR, goal.originCharacterId());
        assertEquals(ACTOR, goal.currentCharacterId());
        assertEquals(0, goal.progress().reconciledSuccessions());
        assertTrue(goal.progress().lastSuccession().isEmpty());
        assertEquals(OrdinaryCampaignGoal.newGoal(EPISODE, ACTOR), goal);

        var war = object("""
            {"priorities":[{"priority":100,"action":"war_expansion","reason":"software prior episode"}]}
            """);
        var withGoal = request(actual, Optional.of(goal), war);
        var withoutGoal = request(actual, Optional.empty(), war);
        assertEquals(Optional.of("war"), OrdinaryCorePolicy.focus(withoutGoal),
                "the prior cross-run plan must make a different choice without the initial goal");
        assertEquals(Optional.of("marriage"), OrdinaryCorePolicy.focus(withGoal),
                "the actual ordinary core must consume the newly persisted campaign goal");
        assertEquals(goal.progress(), OrdinaryCampaignGoal.plan(goal).progress());
        assertEquals(goal, GoalCodec.decodeGoal(GoalCodec.encodeGoal(goal)));
    }

    @Test void initialRogueProducerDoesNotCreateAnOrdinaryCampaignGoal() throws Exception {
        var produced = InitialDriverState.create(frame(), "software-pipe", EPISODE,
                policy(InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE));
        var restored = DriverStateSnapshot.decodeComplete(produced.driver().encode());
        assertInstanceOf(DriverStateSnapshot.NullValue.class, restored.campaignGoal());
        assertInstanceOf(DriverStateSnapshot.Value.class, restored.successionLifecycle());
    }

    private InitialEpisodePolicy policy(InitialEpisodePolicy.Lifecycle kind) throws Exception {
        String setting = kind == InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION
                ? "xar_off" : "xar_on";
        // Explicit supported historical software environment, read by the real policy producer.
        byte[] environment = ("{\"format_version\":1,\"environment_sha256\":\"" + "a".repeat(64)
                + "\",\"rules\":{\"profile\":[{\"rule\":\"xar_enabled\",\"setting\":\""
                + setting + "\"}]}}").getBytes(StandardCharsets.UTF_8);
        Path environmentPath = temporary.resolve(kind.name() + "-environment.json");
        Files.write(environmentPath, environment, StandardOpenOption.CREATE_NEW);
        var original = ControlBuild.FileRef.measure(environmentPath);
        var pact = kind == InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION
                ? InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT : InitialEpisodePolicy.FreshPact.ROGUE_REQUIRED;
        Path policyPath = temporary.resolve(kind.name() + "-policy.json");
        Files.write(policyPath, InitialEpisodePolicy.encode(original, kind, pact), StandardOpenOption.CREATE_NEW);
        var exact = ControlBuild.FileRef.measure(policyPath);
        return InitialEpisodePolicy.readExact(new ExactRef(exact.path(), exact.bytes(), exact.sha256()), original);
    }

    private static NativeObservationPort.ObservedFrame frame() {
        byte[] state = """
            {"paused":true,"map_ready":true,"date_raw":24000,
             "played_character":{"character_id":29829,"alive":true},
             "active_event":null,"pending_character_interaction":null,
             "active_wars":[],"player_armies":[]}
            """.getBytes(StandardCharsets.UTF_8);
        String stateText = new String(state, StandardCharsets.UTF_8);
        byte[] body = ("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"software-snapshot\","
                + "\"revision\":1,\"state\":" + stateText + "}").getBytes(StandardCharsets.UTF_8);
        byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(body.length).put(body).array();
        return new NativeObservationPort.ObservedFrame(
                new NativeObservationPort.TransportSession("software-machine", GAME, BigInteger.ONE, "software-session"),
                "software-snapshot", BigInteger.ONE, new RawJson(state), packet, NOW);
    }

    private static PlanningRequest request(NativeObservationPort.ObservedFrame actual,
            Optional<OrdinaryCampaignGoal.Goal> goal, OpportunityJson.Obj crossRun) {
        var semantic = DriverObservationAssembler.originalNativeState(actual)
                .with("revision", new OpportunityJson.IntegerValue(BigInteger.ONE))
                .with("native_revision", new OpportunityJson.IntegerValue(BigInteger.ONE))
                .with("snapshot_id", new OpportunityJson.Text(actual.snapshotId()))
                .with("episode_run_id", new OpportunityJson.Text(EPISODE));
        var before = new ObservationIdentity(actual.session().machineId(), GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(ACTOR),
                        BigInteger.ONE, RAW), actual.snapshotId(), BigInteger.ONE, EPISODE), 1);
        var source = new ExactRef("software-source", 1, "a".repeat(64));
        return new PlanningRequest(before, new G2Source(before.machineId(), NOW.toString(), "software-build", source),
                actual.session().sessionId(), NOW.plusSeconds(60),
                new PlanningObservation(semantic, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(),
                        goal, Optional.of(crossRun), false));
    }

    private static OpportunityJson.Obj object(String value) {
        return DriverJson.object(value.getBytes(StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES);
    }
}

