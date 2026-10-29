package org.xar.ck3.control.application.readiness;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

final class EventPoliciesRegressionTest {
    private static OpportunityJson.Obj object(String raw) { return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8), 65536); }
    private static PlanningRequest request(boolean firstEnabled) {
        var original = NativeReadinessRegressionTest.fixture(NativeReadinessRegressionTest.STATE
                .replace("\"active_event\":null", "\"active_event\":{\"instance_id\":71,\"option_count\":2}"));
        String dateRaw=OpportunityJson.integer(original.frame().semantic().get("date_raw"), "actual frame date_raw").toString();
        String context = """
            {"status":"available","current_event_instance_id":71,"snapshot_revision":9,"date_raw":10660101,
            "event_definition_key":"unknown.event.1","options":[
            {"rendered_index":0,"native_option_index":1,"shown":true,"enabled":FIRST,"resolved_name":"first displayed"},
            {"rendered_index":1,"native_option_index":0,"shown":true,"enabled":true,"resolved_name":"second displayed"}]}
            """.replace("10660101",dateRaw).replace("FIRST", Boolean.toString(firstEnabled));
        OpportunityJson.Obj history = object("{\"command\":\"query-current-event-window-context-v1\",\"ok\":true,\"result\":{"
                + "\"step\":\"query-current-event-window-context-v1\",\"accepted\":true,\"status\":\"available\","
                + "\"snapshot_revision\":9,\"date_raw\":" + dateRaw + ",\"current_event_instance_id\":71,"
                + "\"queried_snapshot_id\":\"snapshot-9\",\"queried_revision\":2,\"queried_native_revision\":9,\"current_event_window_context\":" + context + "}}");
        var observation = new PlanningObservation(original.frame().semantic(), List.of(history),
                Set.of(new OperationKey("select-event-option-1"), new OperationKey("select-event-option-2")), Set.of(), Optional.empty(), List.of(),
                Optional.empty(), Optional.of(object("{\"campaign_contract\":\"retained\"}")), true);
        return new PlanningRequest(original.frame().identity(), original.frame().source(), original.frame().sessionId(),
                Instant.parse("2030-01-01T00:00:00Z"), observation);
    }
    // Pure policy DATA: source-bound observation fields are explicit; no Game or READ success is minted.
    private static OpportunityJson.Obj fixedWindowObservation(OpportunityJson.Obj snapshot,
            org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind kind, boolean visible) {
        var node = org.xar.ck3.control.contracts.StrictJson.object();
        node.put("sdk_validation_schema", kind.sourceSchema());
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
            node.set("queried_" + key, OpportunityJson.toNode(snapshot.get(key)));
        node.set("queried_actor_character_id", OpportunityJson.toNode(OpportunityJson.object(snapshot.get("played_character"), "player").get("character_id")));
        node.set("queried_connection_generation", OpportunityJson.toNode(OpportunityJson.object(snapshot.get("diagnostics"), "diagnostics").get("connection_generation")));
        node.put("available", true).put("post_observed", true).put("scope_unchanged", true);
        node.put("post_window_present", visible).put("post_effective_visible", visible);
        return object(node.toString());
    }
    private static PlanningRequest fixedWindowRequest(Set<String> caps,
            Optional<org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind> unknown) {
        var original = NativeReadinessRegressionTest.fixture(NativeReadinessRegressionTest.STATE);
        var snapshot = original.frame().semantic();
        for (var kind : org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind.values())
            if (unknown.isEmpty() || unknown.orElseThrow() != kind)
                snapshot = snapshot.with(kind.publicPrefix() + "_observation", fixedWindowObservation(snapshot, kind, false));
        var observation = new PlanningObservation(snapshot, List.of(), Set.of(), caps, Optional.empty(), List.of(),
                Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(original.frame().identity(), original.frame().source(), original.frame().sessionId(),
                Instant.parse("2030-01-01T00:00:00Z"), observation);
    }
    private static OrdinaryPolicy fixedWindowPolicy(PlanningRequest request,
            List<org.xar.ck3.control.application.planning.events.EventReadBinding<?>> bindings) {
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest actual) {
                throw new AssertionError("unavailable typed source must reject before a Native read");
            }
        };
        return EventPolicies.policies(request.source().sourceRef(), Optional.empty(), (a,b,c,d) -> Optional.empty(),
                reads, bindings, (a,b) -> Optional.empty(), (a,b) -> { },
                (a,b,c,d,e,f) -> { throw new AssertionError("read collector cannot acquire a world action"); })
                .stream().filter(row -> row.stage() == PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS).findFirst().orElseThrow();
    }

    private static OrdinaryPolicy policy(PlanningRequest request) {
        return policy(request, (actual, retained) -> { throw new AssertionError("No blocked capture expected"); }, true);
    }
    private static OrdinaryPolicy policy(PlanningRequest request, org.xar.ck3.control.application.planning.events.EventIncidentCapturePort capture, boolean expectedAvailable) {
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest actual) {
                throw new AssertionError("the actual same-frame history must be consumed without another query");
            }
        };
        return EventPolicies.policies(request.source().sourceRef(), Optional.empty(), (current, operation, plan, material) ->
                expectedAvailable ? Optional.of(new ProposalLifecycle.ExpectedPostcondition(1, current.before(), current.source(), "native-event-test/v1",
                        List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.window_closed"), true)))) : Optional.empty(),
                reads, List.of(), (current, raw) -> {
                    OpportunityJson.Obj checked = object(new String(RetainedJson.encode(raw), StandardCharsets.UTF_8));
                    if (!(checked.get("status") instanceof OpportunityJson.Text status) || !status.value().equals("available")) return Optional.empty();
                    for (OpportunityJson.Value option : OpportunityJson.array(checked.get("options"), "options")) {
                        OpportunityJson.Obj row = OpportunityJson.object(option, "option");
                        OpportunityJson.integer(row.get("rendered_index"), "rendered_index");
                        OpportunityJson.integer(row.get("native_option_index"), "native_option_index");
                        OpportunityJson.bool(row.get("shown"), "shown"); OpportunityJson.bool(row.get("enabled"), "enabled");
                    }
                    return Optional.of(raw);
                }, capture,(actual,operation,args,originalPlan,purpose,domain)->{throw new AssertionError("event continuation must retain its dedicated native expectation/incident route");})
                .stream().filter(row -> row.stage() == PlanningStage.EVENT_AND_INTERACTION_CONTINUATION).findFirst().orElseThrow();
    }
    @Test void unfamiliarEventWithoutRegistryContinuesUsingFirstActualDisplayMappingAndRetainsWholeCapture() {
        PlanningRequest request = request(true);
        var decision = policy(request).evaluate(request, OrdinaryPolicy.Draft.empty());
        var replacement = assertInstanceOf(OrdinaryPolicy.Replace.class, decision);
        var command = replacement.draft().command().orElseThrow();
        assertEquals("select-event-option-2", command.operation().value());
        assertEquals(request.before(), command.before());
        assertEquals(command.arguments(), replacement.draft().detail());
        assertEquals(BigInteger.valueOf(71), OpportunityJson.integer(command.arguments().get("event_instance_id"), "instance"));
        assertEquals(BigInteger.TWO, OpportunityJson.integer(command.arguments().get("option_number"), "number"));
        assertEquals(BigInteger.ONE, OpportunityJson.integer(command.arguments().get("native_option_index"), "native"));
        assertEquals(BigInteger.ZERO, OpportunityJson.integer(command.arguments().get("rendered_index"), "rendered"));
        assertNotNull(replacement.draft().detail().get("unhandled_event_fallback"));
        assertTrue(request.observations().initialLifestyleFocusRequired());
        assertTrue(request.observations().crossRunPlan().isPresent());
    }
    @Test void firstDisplayedDisabledDoesNotSkipToLaterEnabledNativeOption() {
        PlanningRequest request = request(false);
        var captured = new java.util.ArrayList<OpportunityJson.Obj>();
        assertInstanceOf(OrdinaryPolicy.Wait.class, policy(request, (actual, retained) -> { assertSame(request, actual); captured.add(retained); }, true).evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(1, captured.size());
        var plan = captured.getFirst(); assertSame(OpportunityJson.Nil.INSTANCE, plan.get("selected_step"));
        var fallback = OpportunityJson.object(plan.get("unhandled_event_fallback"), "fallback");
        var selection = OpportunityJson.object(fallback.get("selection"), "selection");
        assertEquals(BigInteger.ZERO, OpportunityJson.integer(selection.get("rendered_index"), "rendered"));
        assertEquals(BigInteger.ONE, OpportunityJson.integer(selection.get("native_option_index"), "native"));
        assertFalse(OpportunityJson.bool(selection.get("enabled"), "enabled"));
    }
    @Test void explicitDedicatedBlockedPolicyRetainsPriorityOverGenericContinuation() {
        PlanningRequest request = request(true);
        var previous = new OrdinaryPolicy.Draft("dedicated", "active_event_dedicated_blocked", "native prerequisite absent",
                OrdinaryPolicy.Kind.FOREGROUND, Optional.empty(), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(),
                object("{\"dedicated_policy_blocked\":true,\"full_original_plan\":{\"kept\":null}}"));
        assertInstanceOf(OrdinaryPolicy.Wait.class, policy(request).evaluate(request, previous));
    }
    @Test void materialPolicyFailureRetainsItsOriginalDiagnosisThenUsesFirstDisplayedContinuation() {
        for(boolean firstEnabled:List.of(true,false)) {
            PlanningRequest request=request(firstEnabled);var captured=new java.util.ArrayList<OpportunityJson.Obj>();
            var original=object("{\"material_policy_blocked\":true,\"event_decision\":{\"status\":\"blocked\",\"unavailable_reason\":\"same_frame_material_unavailable\"},\"event_material_postcondition\":{\"status\":\"unavailable\",\"starting_value\":null}}");
            var previous=new OrdinaryPolicy.Draft("registered","active_event_registry_material_observation_blocked","same-frame material absent",
                    OrdinaryPolicy.Kind.FOREGROUND,Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),original);
            var decision=policy(request,(actual,retained)->captured.add(retained),true).evaluate(request,previous);
            assertFalse(captured.isEmpty());
            var diagnostic=OpportunityJson.object(captured.getFirst().get("unhandled_native_window_diagnostic"),"diagnostic");
            assertEquals(original,diagnostic.get("original_plan"));
            if(firstEnabled) {
                var replacement=assertInstanceOf(OrdinaryPolicy.Replace.class,decision);
                assertEquals("select-event-option-2",replacement.draft().command().orElseThrow().operation().value());
                assertNull(replacement.draft().command().orElseThrow().arguments().get("event_material_postcondition"));
            } else {
                assertInstanceOf(OrdinaryPolicy.Wait.class,decision);
                assertEquals(2,captured.size(),"original material diagnosis and actual disabled first display both remain inspectable");
                assertSame(OpportunityJson.Nil.INSTANCE,captured.getLast().get("selected_step"));
            }
        }
    }
    @Test void missingPostconditionCapturesUnsubmittedCandidateWithoutInventingAnAction() {
        PlanningRequest request = request(true); var captured = new java.util.ArrayList<OpportunityJson.Obj>();
        assertInstanceOf(OrdinaryPolicy.Stop.class, policy(request, (actual, plan) -> captured.add(plan), false).evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(1, captured.size()); var retained = captured.getFirst();
        assertSame(OpportunityJson.Nil.INSTANCE, retained.get("selected_step"));
        assertEquals("select-event-option-2", OpportunityJson.text(retained.get("unsubmitted_candidate_step"), "candidate"));
        assertNotNull(retained.get("unhandled_event_fallback"));
    }
    @Test void missingNativeReadContractCapturesActualWindowAndTypedDiagnosis() {
        for(boolean advertised:List.of(false,true)) {
        PlanningRequest old = request(true); var observations = old.observations();
        var steps=new java.util.HashSet<>(observations.actionSteps());
        if(advertised)steps.add(new OperationKey("query-current-event-window-context-v1"));
        PlanningRequest request = new PlanningRequest(old.before(), old.source(), old.sessionId(), old.deadline(),
                new PlanningObservation(observations.snapshot(), List.of(), steps, observations.bridgeCapabilities(),
                        observations.battleSpeedReadiness(), observations.actionFacts(), observations.campaignGoal(), observations.crossRunPlan(), observations.initialLifestyleFocusRequired()));
        var captured = new java.util.ArrayList<OpportunityJson.Obj>();
        var stopped=assertInstanceOf(OrdinaryPolicy.Stop.class, policy(request, (actual, plan) -> captured.add(plan), true).evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertTrue(stopped.reason().contains(advertised?"no exact typed read binding":"does not advertise required typed query"));
        assertEquals(1, captured.size());
        var diagnostic = OpportunityJson.object(captured.getFirst().get("unhandled_native_window_diagnostic"), "diagnostic");
        assertEquals("xar.unhandled-native-window-diagnostic/v1", OpportunityJson.text(diagnostic.get("schema"), "schema"));
        assertSame(OpportunityJson.Nil.INSTANCE, diagnostic.get("selection"));
        assertEquals(BigInteger.valueOf(71), OpportunityJson.integer(diagnostic.get("current_event_instance_id"), "instance"));
        assertNotNull(diagnostic.get("origin")); assertEquals(observations.snapshot(), diagnostic.get("snapshot"));
        }
    }
    @Test void missingActualCaptureProducerCannotSilentlyLoseDisabledWindow() {
        PlanningRequest request = request(false);
        assertInstanceOf(OrdinaryPolicy.Stop.class, policy(request,
                org.xar.ck3.control.application.planning.events.EventIncidentCapturePort.unavailable(), true).evaluate(request, OrdinaryPolicy.Draft.empty()));
    }
@Test void installedTypedFixedWindowReadDoesNotRequireWorldActionStep() {
    for (var kind : org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind.values()) {
        var counter = new java.util.concurrent.atomic.AtomicInteger(0);
        var binding = org.xar.ck3.control.application.planning.events.EventReadBinding.actualReceiptFamily(
            new org.xar.ck3.control.application.action.OperationKey(kind.queryStep()),
            (selected) -> selected.equals(new org.xar.ck3.control.application.action.OperationKey(kind.queryStep())),
            (actual, selected) -> {
                counter.incrementAndGet();
                throw new IllegalArgumentException("actual typed window source unavailable");
            });
        var request = fixedWindowRequest(java.util.Set.of(kind.queryCapability(), kind.closeCapability()), java.util.Optional.of(kind));
        var originalSnapshot = request.observations().snapshot();
        var policy = fixedWindowPolicy(request, java.util.List.of(binding));
        var decision = policy.evaluate(request, OrdinaryPolicy.Draft.empty());
        var waiting = assertInstanceOf(OrdinaryPolicy.Stop.class, decision, decision.toString());
        assertTrue(waiting.reason().contains("actual typed window source unavailable"));
        assertEquals(originalSnapshot, request.observations().snapshot());
        assertEquals(1, counter.get());
        assertTrue(request.observations().actionSteps().isEmpty());
    }
}

@Test void fixedWindowReadNeedsActualCapabilityAndInstalledBinding() {
    for (var kind : org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind.values()) {
        var counter = new java.util.concurrent.atomic.AtomicInteger(0);
        var binding = org.xar.ck3.control.application.planning.events.EventReadBinding.actualReceiptFamily(
            new org.xar.ck3.control.application.action.OperationKey(kind.queryStep()),
            (selected) -> selected.equals(new org.xar.ck3.control.application.action.OperationKey(kind.queryStep())),
            (actual, selected) -> {
                counter.incrementAndGet();
                throw new IllegalArgumentException("actual typed window source unavailable");
            });
        var requestCloseOnly = fixedWindowRequest(java.util.Set.of(kind.closeCapability()), java.util.Optional.of(kind));
        var policyCloseOnly = fixedWindowPolicy(requestCloseOnly, java.util.List.of(binding));
        var decisionCloseOnly = policyCloseOnly.evaluate(requestCloseOnly, OrdinaryPolicy.Draft.empty());
        assertInstanceOf(OrdinaryPolicy.Wait.class, decisionCloseOnly);
        assertEquals(0, counter.get());

        var requestBothCaps = fixedWindowRequest(java.util.Set.of(kind.queryCapability(), kind.closeCapability()), java.util.Optional.of(kind));
        var policyEmptyBindings = fixedWindowPolicy(requestBothCaps, java.util.List.of());
        var decisionEmptyBindings = policyEmptyBindings.evaluate(requestBothCaps, OrdinaryPolicy.Draft.empty());
        assertInstanceOf(OrdinaryPolicy.Wait.class, decisionEmptyBindings);
        assertEquals(0, counter.get());
    }
}
    @Test void sourceBoundAbsentWindowsDoNotIssueReadsOrCreateAnAction() {
        var caps = new java.util.HashSet<String>();
        for (var kind : org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind.values()) {
            caps.add(kind.queryCapability()); caps.add(kind.closeCapability());
        }
        var request = fixedWindowRequest(caps, Optional.empty());
        var binding = org.xar.ck3.control.application.planning.events.EventReadBinding.<EventPolicies.ReadPublication>actualReceiptFamily(
                new OperationKey("query-war-results-window-v1"), op -> true,
                (actual, selected) -> { throw new AssertionError("known absence cannot acquire another query"); });
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, fixedWindowPolicy(request, List.of(binding)).evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertTrue(request.observations().actionSteps().isEmpty());
    }
    @Test void visibleWindowCannotAcquireCloseAuthorityFromItsReadBinding() {
        var kind = org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind.RESULTS;
        var request = fixedWindowRequest(Set.of(kind.queryCapability(), kind.closeCapability()), Optional.empty());
        var old = request.observations();
        var snapshot = old.snapshot().with(kind.publicPrefix() + "_observation", fixedWindowObservation(old.snapshot(), kind, true));
        var visible = new PlanningRequest(request.before(), request.source(), request.sessionId(), request.deadline(),
                new PlanningObservation(snapshot, old.history(), old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(),
                        old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), old.initialLifestyleFocusRequired()));
        var binding = org.xar.ck3.control.application.planning.events.EventReadBinding.<EventPolicies.ReadPublication>actualReceiptFamily(
                new OperationKey(kind.queryStep()), op -> true,
                (actual, selected) -> { throw new AssertionError("visible window needs the original close action authority"); });
        assertInstanceOf(OrdinaryPolicy.Wait.class, fixedWindowPolicy(visible, List.of(binding)).evaluate(visible, OrdinaryPolicy.Draft.empty()));
        assertTrue(visible.observations().actionSteps().isEmpty());
    }
    @Test void unavailableTypedReadsKeepTheirOriginalReasonThroughEveryBindingAndOrdinaryCollector() {
        for (var kind : org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind.values()) {
            var request=fixedWindowRequest(Set.of(kind.queryCapability()),Optional.of(kind));
            var operation=new OperationKey(kind.queryStep());
            var prepared=new java.util.concurrent.atomic.AtomicInteger();
            var contract=new ReadContract<org.xar.ck3.control.application.action.RawJson>("window-diagnostic-test",operation,
                    Optional.of(kind.queryCapability()),kind.queryCapability(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                    ReadContract.WireProfile.EXECUTE_STEP,request.source().sourceRef(),actual->{
                        prepared.incrementAndGet();throw new AssertionError("unavailable guard cannot prepare a Native query");
                    },receipt->{throw new AssertionError("unavailable cannot decode into Known");});
            var arguments=new OpportunityJson.Obj(java.util.Map.of());
            var bindings=List.of(
                new org.xar.ck3.control.application.planning.events.EventReadBinding<>(
                    new org.xar.ck3.control.application.effects.NativeEventEffects.MaterialQuery<>(contract,value->value,ignored->arguments),
                    (actual,value)->{throw new AssertionError("unavailable cannot publish material");}),
                org.xar.ck3.control.application.planning.events.EventReadBinding.actualReceipt(contract,ignored->arguments,
                    known->{throw new AssertionError("unavailable cannot publish a receipt");}),
                org.xar.ck3.control.application.planning.events.EventReadBinding.actualReceiptFamily(operation,operation::equals,
                    (actual,selected)->new org.xar.ck3.control.application.planning.events.EventReadBinding.ReceiptResolution<>(contract,arguments,
                        known->{throw new AssertionError("unavailable cannot publish a family");})));
            for(var binding:bindings) {
                String reason="read lifecycle diagnostic unavailable: original before-read source rejected "+kind.queryStep();
                var calls=new java.util.concurrent.atomic.AtomicInteger();
                var original=new java.util.concurrent.atomic.AtomicReference<PlanningReadResult.Unavailable<?>>();
                PlanningReadPort reads=new PlanningReadPort(){
                    @Override public <T> PlanningReadResult<T> read(ReadContract<T> installed,PlanningReadRequest actual){
                        assertSame(contract,installed);assertEquals(request.before(),actual.before());calls.incrementAndGet();
                        var missing=new PlanningReadResult.Unavailable<T>(reason,Optional.empty());original.set(missing);return missing;
                    }
                };
                var outcome=binding.read(reads,request,operation,(a,b)->{});
                var unavailable=assertInstanceOf(org.xar.ck3.control.application.planning.events.EventReadBinding.Unavailable.class,outcome);
                assertSame(original.get(),unavailable.result());assertTrue(unavailable.result().original().isEmpty());
                var policy=EventPolicies.policies(request.source().sourceRef(),Optional.empty(),(a,b,c,d)->Optional.empty(),
                        reads,List.of(binding),(a,b)->Optional.empty(),(a,b)->{},
                        (a,b,c,d,e,f)->{throw new AssertionError("an unavailable read grants no world action");})
                        .stream().filter(row->row.stage()==PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS).findFirst().orElseThrow();
                assertEquals(reason,assertInstanceOf(OrdinaryPolicy.Wait.class,policy.evaluate(request,OrdinaryPolicy.Draft.empty())).reason());
                assertEquals(2,calls.get());assertEquals(0,prepared.get());assertTrue(request.observations().history().isEmpty());
                assertTrue(request.observations().actionSteps().isEmpty());
            }
        }
    }
}
