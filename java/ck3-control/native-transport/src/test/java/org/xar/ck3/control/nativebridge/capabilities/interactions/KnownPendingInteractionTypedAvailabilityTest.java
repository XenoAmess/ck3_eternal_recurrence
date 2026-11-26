package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionFixtures.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.application.planning.military.WarCorePlanner;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPolicy.*;

/** Synthetic policy inputs only: no Root context, Installed product, Native provider or Game evidence is created. */
final class KnownPendingInteractionTypedAvailabilityTest {
    private static ContextReadPort unavailable() {
        var build=ExactCk3Build.CK3_1210;
        return KnownPendingInteractionPolicy.typedUnavailable(build.version(),build.executableSha256());
    }
    private static PlanningRequest florin(ObjectNode snapshot) {
        var held=context();var old=held.source();var build=ExactCk3Build.CK3_1210;
        var source=new G2Source(old.machineId(),old.observedAtUtc(),build.version()+"@sha256:"+build.executableSha256(),old.sourceRef());
        return new PlanningRequest(held.before(),source,held.sessionId(),held.deadline(),
                new PlanningObservation(InteractionArguments.app(snapshot),List.of(),steps(),java.util.Set.of(),Optional.empty(),
                        List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static KnownPendingInteractionPolicy policy(ContextReadPort contexts) {
        return KnownPendingInteractionPolicy.withContextReads(SOURCE,contexts,noReads(),PendingInteractionContracts.pending(SOURCE),
                operation->{throw new AssertionError("unavailable context must not select supplemental reads");},
                (request,previous)->{throw new AssertionError("unavailable context must not continue into another same-core action");});
    }
    private static OrdinaryPolicy.Draft readOnly(OrdinaryPolicy.Decision decision,PlanningRequest original) {
        var draft=assertInstanceOf(OrdinaryPolicy.Replace.class,decision).draft();
        assertEquals("pending_character_interaction_evidence_required",draft.phase());
        assertEquals(OrdinaryPolicy.Kind.FOREGROUND,draft.kind());
        assertEquals(OrdinaryPolicy.Purpose.READ_ONLY,draft.purpose());
        assertTrue(draft.command().isEmpty());assertTrue(draft.domain().isEmpty());
        var detail=InteractionArguments.parseApp(draft.detail());
        assertTrue(detail.path("selected_step").isNull());assertEquals(PendingContextCodec.STEP,detail.path("required_step").textValue());
        assertTrue(detail.path("known_policy_handled").booleanValue());
        assertEquals(InteractionArguments.parseApp(original.observations().snapshot()).get("pending_character_interaction"),
                detail.get("pending_character_interaction"));
        assertFalse(detail.has(KnownPendingInteractionPolicy.CANDIDATE));
        assertFalse(detail.has("native_read_original_receipt"));return draft;
    }

    @Test void exactConfiguredNegativeResultHasNoInventedOriginalAndRejectsAllOtherTuples() {
        var build=ExactCk3Build.CK3_1210;var request=florin(snapshot(context()));
        var result=assertInstanceOf(Unavailable.class,unavailable().current(request)).result();
        assertEquals("interaction_native_contract_unmigrated",result.reason());
        assertTrue(result.original().isEmpty());assertTrue(result.decodeFailure().isEmpty());assertTrue(result.observedFailure().isEmpty());
        assertInstanceOf(Unavailable.class,KnownPendingInteractionPolicy.typedUnavailable(build.version(),
                build.executableSha256().toUpperCase(Locale.ROOT)).current(request));
        for(var legacy:InteractionModels.Build.values())
            assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPolicy.typedUnavailable(legacy.version(),legacy.sha256()));
        for(String version:List.of("1.21.0.0","1.21.1","1.21.0 (Florin)",""))
            assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPolicy.typedUnavailable(version,build.executableSha256()));
        assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPolicy.typedUnavailable(build.version(),"0".repeat(64)));
        assertThrows(NullPointerException.class,()->unavailable().current(null));
    }

    @Test void pendingAndNotificationBothRemainReadOnlyEvenWhenAnOldReplyHistoryIsPresent() {
        for(boolean notification:List.of(false,true)) {
            var held=context();var snapshot=snapshot(held);
            ((ObjectNode)snapshot.get("pending_character_interaction")).put("auto_accept_notification",notification);
            snapshot.remove("diagnostics"); // An unavailable branch must never fabricate a legacy native Context.
            var original=florin(snapshot);
            var old=request(held,snapshot(held),wire(held,"spar_with_knight_interaction"),steps());
            var request=original.withHistory(old.observations().history());var history=request.observations().history();
            var policy=policy(unavailable());
            readOnly(policy.evaluateCore(request,OrdinaryPolicy.Draft.empty()),request);
            readOnly(policy.consumeCore(request,OrdinaryPolicy.Draft.empty()),request);
            var peace=assertInstanceOf(MilitaryPlanningDecision.ApplicationDecision.class,
                    policy.leaf(SOURCE).producer().evaluate(request,OrdinaryPolicy.Draft.empty()));
            readOnly(peace.decision(),request);assertEquals(history,request.observations().history());
        }
    }

    @Test void explicitEmptyQueueIsInapplicableAndBothOriginalWarLeavesRemainInstalled() {
        var snapshot=snapshot(context());snapshot.putNull("pending_character_interaction");var request=florin(snapshot);
        var policy=policy(unavailable());
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class,policy.evaluateCore(request,OrdinaryPolicy.Draft.empty()));
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class,policy.consumeCore(request,OrdinaryPolicy.Draft.empty()));
        var leaves=policy.leaves(SOURCE);
        assertEquals(List.of(WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_PRELUDE,
                WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_CONSUMPTION),leaves.stream().map(WarCorePlanner.Leaf::boundary).toList());
        for(var leaf:leaves){assertEquals(SOURCE,leaf.implementationSource());
            assertInstanceOf(MilitaryPlanningDecision.Keep.class,leaf.producer().evaluate(request,OrdinaryPolicy.Draft.empty()));}
    }

    @Test void missingAndWrongTypePendingAreNeverCreditedAsAnEmptyQueue() {
        for(int mode=0;mode<3;mode++) {
            var snapshot=snapshot(context());
            if(mode==0)snapshot.remove("pending_character_interaction");
            else if(mode==1)snapshot.put("pending_character_interaction",false);
            else snapshot.putArray("pending_character_interaction");
            var request=florin(snapshot);var policy=policy(unavailable());
            assertThrows(IllegalArgumentException.class,()->policy.evaluateCore(request,OrdinaryPolicy.Draft.empty()));
            assertThrows(IllegalArgumentException.class,()->policy.consumeCore(request,OrdinaryPolicy.Draft.empty()));
            for(var leaf:policy.leaves(SOURCE))
                assertThrows(IllegalArgumentException.class,()->leaf.producer().evaluate(request,OrdinaryPolicy.Draft.empty()));
        }
    }

    @Test void unavailableCannotBeCachedAndReusedAcrossPlanningBuildSources() {
        var held=context();var valid=florin(snapshot(held));var foreign=request(held,snapshot(held),wire(held,"spar_with_knight_interaction"),steps());
        assertThrows(IllegalArgumentException.class,()->unavailable().current(foreign));
        ContextRead cached=unavailable().current(valid);var policy=policy(ignored->cached);
        assertThrows(IllegalArgumentException.class,()->policy.evaluateCore(foreign,OrdinaryPolicy.Draft.empty()));
        assertThrows(IllegalArgumentException.class,()->policy.consumeCore(foreign,OrdinaryPolicy.Draft.empty()));
        for(var leaf:policy.leaves(SOURCE))
            assertThrows(IllegalArgumentException.class,()->leaf.producer().evaluate(foreign,OrdinaryPolicy.Draft.empty()));
    }

    @Test void activeWarPreludeDoesNotPrepareAReplyAndOnlyConsumptionSelectsReadOnly() {
        var snapshot=snapshot(context());snapshot.withArray("active_wars").addObject().put("war_id",91);
        var request=florin(snapshot);var policy=policy(unavailable());var leaves=policy.leaves(SOURCE);
        var prelude=assertInstanceOf(MilitaryPlanningDecision.Keep.class,
                leaves.getFirst().producer().evaluate(request,OrdinaryPolicy.Draft.empty()));
        assertFalse(InteractionArguments.parseApp(prelude.annotations()).has(KnownPendingInteractionPolicy.CANDIDATE));
        var consumed=assertInstanceOf(MilitaryPlanningDecision.ApplicationDecision.class,
                leaves.getLast().producer().evaluate(request,OrdinaryPolicy.Draft.empty()));
        readOnly(consumed.decision(),request);
    }

    @Test void realWarCoreStopsAtItsLifecycleGuardBeforeConsumingUnavailablePending() {
        var snapshot=snapshot(context());snapshot.withArray("active_wars").addObject().put("war_id",91);var request=florin(snapshot);
        AtomicInteger reads=new AtomicInteger();var negative=unavailable();
        var policy=policy(original->{reads.incrementAndGet();return negative.current(original);});
        var pending=policy.leaves(SOURCE);List<WarCorePlanner.Boundary> visited=new ArrayList<>();List<WarCorePlanner.Leaf> leaves=new ArrayList<>();
        for(var boundary:WarCorePlanner.Boundary.values()) {
            var found=pending.stream().filter(leaf->leaf.boundary()==boundary).findFirst();
            WarCorePlanner.CoreStep step=found.isPresent()?found.orElseThrow().producer():(original,current)->
                    new MilitaryPlanningDecision.Keep(InteractionArguments.app(InteractionJson.F.objectNode()));
            leaves.add(new WarCorePlanner.Leaf(boundary,SOURCE,(original,current)->{
                visited.add(boundary);
                if(boundary==WarCorePlanner.Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE)
                    return new MilitaryPlanningDecision.Hold("fixture-policy","fixture-lifecycle-guard","synthetic lifecycle guard",
                            Optional.empty(),InteractionArguments.app(InteractionJson.F.objectNode()));
                return step.evaluate(original,current);
            }));
        }
        // The real planner's ordering is exercised; these synthetic leaves grant no physical Root readiness.
        var war=new WarCorePlanner(leaves,original->{throw new AssertionError("tactics must follow lifecycle");},
                (original,selected)->{throw new AssertionError("no world command");},noReads(),
                (original,selected)->{throw new AssertionError("no native read");},
                (original,current)->{throw new AssertionError("no continuation");});
        var continued=assertInstanceOf(WarCorePlanner.PreludeContinue.class,war.prelude(request,OrdinaryPolicy.Draft.empty()));
        var guarded=assertInstanceOf(OrdinaryPolicy.Replace.class,war.activeWar(request,continued.draft()));
        assertEquals("fixture-lifecycle-guard",guarded.draft().phase());assertTrue(guarded.draft().command().isEmpty());
        assertEquals(List.of(WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE,
                WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_PRELUDE,WarCorePlanner.Boundary.BATTLE_CONTROL_PRELUDE,
                WarCorePlanner.Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE),visited);
        assertEquals(1,reads.get(),"unavailable context is not consumed before the original lifecycle guard");
    }

    @Test void legacyConstructorsAndTypedAvailableSelectTheSameOriginalReplyAndRejectCrossedBindings() {
        var held=context();var request=request(held,snapshot(held),wire(held,"spar_with_knight_interaction"),steps());
        var contract=PendingInteractionContracts.pending(SOURCE);
        var legacy=new KnownPendingInteractionPolicy(SOURCE,original->held,noReads(),contract,operation->Optional.empty());
        var typed=KnownPendingInteractionPolicy.withContextReads(SOURCE,original->new Available(held),noReads(),contract,operation->Optional.empty());
        var expected=legacy.evaluateCore(request,OrdinaryPolicy.Draft.empty());
        assertEquals(expected,typed.evaluateCore(request,OrdinaryPolicy.Draft.empty()));
        var command=assertInstanceOf(OrdinaryPolicy.Replace.class,expected).draft().command().orElseThrow();
        assertEquals(KnownPendingInteractionRules.Action.REJECT.step(),command.operation().value());
        var sixArgument=new KnownPendingInteractionPolicy(SOURCE,original->held,noReads(),contract,operation->Optional.empty(),
                (original,current)->{throw new AssertionError("ordinary rejection needs no continuation");});
        assertEquals(expected,sixArgument.evaluateCore(request,OrdinaryPolicy.Draft.empty()));
        var changedDeadline=new PlanningRequest(request.before(),request.source(),request.sessionId(),request.deadline().minusSeconds(1),request.observations());
        for(var policy:List.of(legacy,typed,sixArgument))
            assertThrows(IllegalArgumentException.class,()->policy.evaluateCore(changedDeadline,OrdinaryPolicy.Draft.empty()));
        var changedSnapshot=snapshot(held);changedSnapshot.withObjectProperty("diagnostics").put("bridge_pid",124);
        var changed=request(held,changedSnapshot,wire(held,"spar_with_knight_interaction"),steps());
        for(var policy:List.of(legacy,typed,sixArgument))
            assertThrows(IllegalArgumentException.class,()->policy.evaluateCore(changed,OrdinaryPolicy.Draft.empty()));
        assertThrows(NullPointerException.class,()->new Available(null));
    }

    @Test void reviewedExecutionRawShaSourceIsRetainedWithoutInventingAnotherProvenance() {
        var original=florin(snapshot(context()));var build=ExactCk3Build.CK3_1210;
        for(String spelling:List.of(build.executableSha256(),build.executableSha256().toUpperCase(Locale.ROOT))) {
            var prior=original.source();var source=new org.xar.ck3.control.g2.common.G2Source(prior.machineId(),prior.observedAtUtc(),spelling,prior.sourceRef());
            var retained=new PlanningRequest(original.before(),source,original.sessionId(),original.deadline(),original.observations());
            assertInstanceOf(Unavailable.class,unavailable().current(retained));
            readOnly(policy(unavailable()).evaluateCore(retained,OrdinaryPolicy.Draft.empty()),retained);
            assertSame(source,retained.source());assertEquals(spelling,retained.source().exactBuild());
        }
        var prior=original.source();var foreign=new org.xar.ck3.control.g2.common.G2Source(prior.machineId(),prior.observedAtUtc(),"0".repeat(64),prior.sourceRef());
        var crossed=new PlanningRequest(original.before(),foreign,original.sessionId(),original.deadline(),original.observations());
        assertThrows(IllegalArgumentException.class,()->unavailable().current(crossed));
    }
}
