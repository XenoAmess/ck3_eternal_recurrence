package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningWire;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreatsCodec;

/** Software boundary cases for the same installed policy. Commands remain unexecuted fixture bodies. */
final class M5WartimeObservationBoundaryTest {
    private static final ExactRef SOURCE = new ExactRef("software-m5-boundary-policy", 1, "d".repeat(64));
    private static final Instant DEADLINE = Instant.parse("2026-10-25T00:01:00Z");

    @Test void malformedWarIdentityCannotRemoveTheIndependentlyPreparedWarExitOrInventAnAssessment() {
        Obj snapshot = snapshot();
        Obj war = war(snapshot).with("war_id", new Bool(true));
        snapshot = snapshot.with("active_wars", new Arr(List.of(war)));
        PlanningRequest request = request(snapshot);
        OrdinaryPolicy.Draft original = draft(request);
        String originalBody = ActionCodec.bodySha256(original.command().orElseThrow());

        OrdinaryPolicy.Draft retained = annotate(request, original);
        assertRetained(original, retained, originalBody);
        Obj joint = object(retained.detail().get("m5_joint_wartime_observation"));
        assertEquals(new Text("source_red"), joint.get("status"));
        assertEquals(new Bool(false), joint.get("formal_action_ready"));
        ParticipatingWarThreats.UnavailableNonPrimaryRisk risk = assertInstanceOf(
                ParticipatingWarThreats.UnavailableNonPrimaryRisk.class, risk(retained));
        assertEquals(ParticipatingWarThreats.Reason.DISTINCT_NATIVE_PARTICIPATING_WAR_IDENTITY_UNAVAILABLE, risk.reason());
        assertFalse(risk.actionAuthorized());
        assertFalse(risk.politicalAndTerritorialConsequencesAssessed());
        assertFalse(risk.unraisedReservesBounded());
        assertRoundTrip(request, retained);
    }

    @Test void absentEnemyArrayRemainsUnavailableWhileUnknownSoldiersKeepTheObservedNonprimaryIdentity() {
        Obj current = snapshot();
        Obj war = war(current);
        var missingEnemyFields = new LinkedHashMap<>(war.members());
        missingEnemyFields.remove("enemy_armies");
        Obj noEnemies = current.with("active_wars", new Arr(List.of(new Obj(missingEnemyFields))));
        PlanningRequest absentRequest = request(noEnemies);
        OrdinaryPolicy.Draft absentPrior = draft(absentRequest);
        OrdinaryPolicy.Draft unavailable = annotate(absentRequest, absentPrior);
        assertRetained(absentPrior, unavailable, ActionCodec.bodySha256(absentPrior.command().orElseThrow()));
        assertEquals(ParticipatingWarThreats.Reason.PUBLISHED_ENEMY_ARMY_ARRAY_UNAVAILABLE,
                assertInstanceOf(ParticipatingWarThreats.UnavailableNonPrimaryRisk.class, risk(unavailable)).reason());

        Obj enemyWithoutSoldiers = new Obj(Map.of("army_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(55))));
        Obj knownScope = current.with("active_wars", new Arr(List.of(war.with("enemy_armies", new Arr(List.of(enemyWithoutSoldiers))))));
        PlanningRequest knownRequest = request(knownScope);
        OrdinaryPolicy.Draft knownPrior = draft(knownRequest);
        OrdinaryPolicy.Draft observed = annotate(knownRequest, knownPrior);
        assertRetained(knownPrior, observed, ActionCodec.bodySha256(knownPrior.command().orElseThrow()));
        ParticipatingWarThreats.ObservedNonPrimaryRisk risk = assertInstanceOf(
                ParticipatingWarThreats.ObservedNonPrimaryRisk.class, risk(observed));
        assertEquals(List.of(12), risk.nonPrimaryWarIds());
        assertEquals(ParticipatingWarThreats.NonPrimaryRiskStatus.UNASSESSED, risk.status());
        assertEquals(BigInteger.valueOf(23), risk.frame().revision());
        assertEquals(BigInteger.valueOf(17), risk.frame().nativeRevision());
        assertFalse(risk.actionAuthorized());
        assertFalse(risk.politicalAndTerritorialConsequencesAssessed());
        assertRoundTrip(knownRequest, observed);
    }

    @Test void disabledOrForegroundObservationCannotReplaceTheExistingChoiceOrCreateRiskEvidence() {
        PlanningRequest request = request(snapshot());
        OrdinaryPolicy.Draft prior = draft(request);
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, new M5WartimeObservationPolicy(SOURCE, false).evaluate(request, prior));
        Obj foreground = snapshot().with("pending_character_interaction", new Obj(Map.of("status", new Text("present"))));
        PlanningRequest foregroundRequest = request(foreground);
        OrdinaryPolicy.Draft foregroundPrior = draft(foregroundRequest);
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, new M5WartimeObservationPolicy(SOURCE, true)
                .evaluate(foregroundRequest, foregroundPrior));
        for (OrdinaryPolicy.Draft original : List.of(prior, foregroundPrior)) {
            assertFalse(original.detail().members().containsKey("m5_nonprimary_war_risk"));
            assertFalse(original.detail().members().containsKey("m5_joint_wartime_observation"));
        }
    }

    private static OrdinaryPolicy.Draft annotate(PlanningRequest request, OrdinaryPolicy.Draft prior) {
        return assertInstanceOf(OrdinaryPolicy.Annotate.class, new M5WartimeObservationPolicy(SOURCE, true)
                .evaluate(request, prior)).retained();
    }
    private static ParticipatingWarThreats.NonPrimaryRisk risk(OrdinaryPolicy.Draft draft) {
        return ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(OpportunityJson.encode(draft.detail().get("m5_nonprimary_war_risk")));
    }
    private static void assertRetained(OrdinaryPolicy.Draft original, OrdinaryPolicy.Draft retained, String body) {
        assertSame(original.command().orElseThrow(), retained.command().orElseThrow());
        assertEquals(body, ActionCodec.bodySha256(retained.command().orElseThrow()));
        assertEquals(original.policy(), retained.policy()); assertEquals(original.phase(), retained.phase());
        assertEquals(original.reason(), retained.reason()); assertEquals(original.kind(), retained.kind());
        assertEquals(original.purpose(), retained.purpose()); assertEquals(original.domain(), retained.domain());
        original.detail().members().forEach((field, value) -> assertEquals(value, retained.detail().get(field)));
        assertFalse(original.detail().members().containsKey("m5_nonprimary_war_risk"));
    }
    private static void assertRoundTrip(PlanningRequest request, OrdinaryPolicy.Draft retained) {
        var selected = new PlanningResult.ActionSelected(retained.command().orElseThrow(),
                new PlanTrace(request.before(), List.of(), Optional.of(retained)));
        assertEquals(selected, PlanningWire.decodeResult(PlanningWire.encodeResult(selected)));
    }
    private static Obj snapshot() {
        return DriverJson.object("""
                {"played_character_id":29829,"native_revision":17,"date_raw":53202168,
                 "snapshot_id":"m5-boundary-fixture","revision":23,"episode_run_id":"m5-boundary-episode",
                 "paused":true,"map_ready":true,"played_character":{"character_id":29829,"alive":true},
                 "player_armies":[],"active_wars":[{"war_id":12,"source":"native","player_side":"defender",
                 "player_is_primary_war_leader":false,"enemy_armies":[{"army_id":55,"soldiers":400}]}]}
                """.getBytes(StandardCharsets.UTF_8), 8192);
    }
    private static Obj war(Obj snapshot) {
        return object(OpportunityJson.array(snapshot.get("active_wars"), "fixture wars").getFirst());
    }
    private static PlanningRequest request(Obj snapshot) {
        var source = new G2Source("software-m5-boundary-no-game", "2026-10-25T00:00:00Z", "1.20.0.4", SOURCE);
        var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(17), BigInteger.valueOf(53202168));
        var frame = new JointBudgetSelector.ProposalFrame(identity, "m5-boundary-fixture", BigInteger.valueOf(23), "m5-boundary-episode");
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new PlanningRequest(before, source, "software-m5-boundary-session", DEADLINE,
                new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static OrdinaryPolicy.Draft draft(PlanningRequest request) {
        var operation = new OperationKey("software-independent-war-exit");
        var command = new ActionCommand("software-war-exit-original", request.before(), request.source(), request.sessionId(), operation,
                new Obj(Map.of("war_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(12)))),
                new ExpectedPostcondition(1, request.before(), request.source(), "software-war-exit-post/v1",
                        List.of(new ExpectedBoolean(new FieldKey("native.fixture_outcome"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        Obj detail = new Obj(Map.of("selected_step", new Text(operation.value()), "explicit_null", Nil.INSTANCE,
                "independent_native_permissions", new Text("not_assessed_by_observer")));
        return new OrdinaryPolicy.Draft("original-war-exit", "original-independent-war-exit", "original-independent-choice",
                OrdinaryPolicy.Kind.WAR_EXIT, Optional.of(command), OrdinaryPolicy.Purpose.WORLD_ACTION, Optional.of(Domain.war), detail);
    }
    private static Obj object(OpportunityJson.Value value) { return OpportunityJson.object(value, "fixture object"); }
}
