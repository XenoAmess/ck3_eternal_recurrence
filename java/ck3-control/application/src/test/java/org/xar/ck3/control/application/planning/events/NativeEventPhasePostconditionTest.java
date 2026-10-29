package org.xar.ck3.control.application.planning.events;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventtraits.*;

/** Exercises the actual observer projection with public 900/native 51 split and independent later raw leaf. */
final class NativeEventPhasePostconditionTest {
    private static final ExactRef REF = new ExactRef("synthetic-native-read", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("fixture-machine", "2026-10-23T17:00:00Z", "1.20.0.4", REF);
    private static ObservationIdentity identity(int revision, int nativeRevision) {
        return new ObservationIdentity("fixture-machine", new GameGeneration(101, new PythonOnlyUInt64(BigInteger.ONE)),
            new ProposalFrame(new Frame(BigInteger.valueOf(29829), BigInteger.valueOf(nativeRevision), BigInteger.valueOf(53144520)),
                "p" + revision, BigInteger.valueOf(revision), "fixture-episode"), 1);
    }
    private static ExpectedPostcondition expected(boolean material) {
        var values = new ArrayList<ExpectedValue>(List.of(new ExpectedInteger(new FieldKey("old_instance_id"), BigInteger.valueOf(17)),
            new ExpectedBoolean(new FieldKey("old_instance_advanced"), true), new ExpectedInteger(new FieldKey("actor_id"), BigInteger.valueOf(29829)),
            new ExpectedText(new FieldKey("connection_generation_decimal"), "7")));
        if (material) {
            values.add(new ExpectedBoolean(new FieldKey("trait_lifestyle_poet_added"), true));
            values.add(new ExpectedInteger(new FieldKey("event_effect_native_index"), BigInteger.ZERO));
        }
        return new ExpectedPostcondition(1, identity(900, 51), SOURCE, NativeEventPostconditionPort.EVENT_SCHEMA, values);
    }
    private static EventEffectPhase.Phases poet(int index) {
        return EventEffectPhase.classify(PoetTraitOutcome.EVENT, new EventEffectPhase.SourceBinding("1.20.0.4", EventEffectPhase.EXE,
            PoetTraitOutcome.SOURCE_PATH, PoetTraitOutcome.SOURCE_SHA256), index).orElseThrow();
    }
    private static OpportunityJson.Obj arguments(EventEffectPhase.Phases phases) {
        var args = StrictJson.object();
        if (phases != null) args.set("event_effect_phase", StrictJson.parse(EventEffectPhase.encode(phases)));
        var frame = new PoetTraitOutcome.PublicFrame("p900", BigInteger.valueOf(900), new EventTraitMembership.Frame(BigInteger.valueOf(51), 53144520, 29829));
        args.set("event_material_postcondition", StrictJson.parse(PoetTraitOutcome.encode(new PoetTraitOutcome.Ready(new PoetTraitOutcome.Binding(PoetTraitOutcome.Choice.POET, frame)))));
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)), "synthetic command");
    }
    private static NativeEventPostconditionPort.BoundSnapshot after(boolean hasPoet) {
        var raw = StrictJson.object(); raw.put("snapshot_id", "p902").put("revision", 902).put("native_revision", 53).put("date_raw", 53144520)
            .put("episode_run_id", "fixture-episode").put("paused", true).put("map_ready", true).putNull("active_event");
        var actor = raw.putObject("played_character"); actor.put("character_id", 29829);
        actor.set("event_trait_membership", StrictJson.parse(EventTraitMembershipCodec.encode(new EventTraitMembership.Available(
            new EventTraitMembership.Frame(BigInteger.valueOf(53), 53144520, 29829), new EventTraitMembership.Traits(hasPoet, false)))));
        raw.putObject("diagnostics").put("bridge_pid", 101).put("connection_generation", 7);
        return new NativeEventPostconditionPort.BoundSnapshot(identity(902, 53), SOURCE, "fixture-session",
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(raw)), "synthetic independent read"), "read-after", Instant.parse("2026-10-23T17:00:01Z"), REF);
    }
    @Test void exactSelectedPhasePlusIndependentFalseToTrueCanSatisfyDedicatedMaterial() {
        assertTrue(NativeEventPostconditionPort.project(identity(900, 51), SOURCE, "fixture-session", expected(true), arguments(poet(0)), after(true)).isPresent());
        assertTrue(NativeEventPostconditionPort.project(identity(900, 51), SOURCE, "fixture-session", expected(true), arguments(poet(0)), after(false)).isEmpty());
    }
    @Test void missingPhaseWrongChoiceAndImmediateHealthNeverSatisfyPoetMaterial() {
        var health = EventEffectPhase.classify("health.1101", new EventEffectPhase.SourceBinding("1.20.0.4", EventEffectPhase.EXE,
            EventEffectPhase.HEALTH_PATH, EventEffectPhase.HEALTH_SHA), 0).orElseThrow();
        for (var args : List.of(arguments(null), arguments(poet(1)), arguments(health)))
            assertTrue(NativeEventPostconditionPort.project(identity(900, 51), SOURCE, "fixture-session", expected(true), args, after(true)).isEmpty());
        assertTrue(NativeEventPostconditionPort.project(identity(900, 51), SOURCE, "fixture-session", expected(false), arguments(health), after(false)).isPresent());
    }
    @Test void unknownContinuationCanObserveWindowOnlyWithoutAnySourcePhaseFact() {
        assertTrue(NativeEventPostconditionPort.project(identity(900, 51), SOURCE, "fixture-session", expected(false),
            OpportunityJson.object(OpportunityJson.parse("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)), "synthetic unknown"), after(false)).isPresent());
    }
}
