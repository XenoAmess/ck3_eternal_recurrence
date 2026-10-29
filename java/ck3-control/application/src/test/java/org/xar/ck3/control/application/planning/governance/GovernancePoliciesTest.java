package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Production collector DTO -> existing typed policy -> unique command/serde, with real negative boundaries. No runtime qualification. */
final class GovernancePoliciesTest {
    @Test void lifestyleUsesExistingTypedChoiceAndPreservesSourceIdentityInCanonicalCommand() {
        var request = request(); var supplier = new Supplier(request);
        var replacement = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Lifestyle(supplier, REF).evaluate(request, advance(request)));
        var command = replacement.draft().command().orElseThrow();
        assertEquals(GovernancePolicies.PERK, command.operation());
        assertEquals(new Text("cutting_corners_perk"), command.arguments().get("target_key"));
        assertEquals(request.before(), command.before()); assertEquals(request.source(), command.source());
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        assertTrue(command.expected().values().contains(new ExpectedBoolean(new FieldKey("lifestyle.target_perk_owned"), true)));
        assertTrue(command.expected().values().contains(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true)));
        assertEquals(new Text("preserve"), replacement.draft().detail().get("original_marker"));
    }
    @Test void pendingOriginalLifestyleOverridesCooldownBeforeAnyNewNativeRead() {
        Obj pending = new Obj(java.util.Map.of()).with("command", new Text(GovernancePolicies.PERK.value())).with("ok", new Bool(true)).with("result", new Obj(java.util.Map.of()).with("status", new Text("action_state_unknown")).with("episode_run_id", new Text("unit-episode")));
        var request = request(9, false, List.of(pending)); var supplier = new Supplier(request);
        var old = supplier.state;
        var cadence = old.cadence().orElseThrow().with(CadenceModels.Domain.LIFESTYLE, new CadenceModels.Row(0, Optional.of(BigInteger.valueOf(1000)),
                Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty()));
        supplier.state = new Durable(old.observed(), old.sessionId(), Optional.of(cadence), old.opening(), old.council(), old.crown());
        assertInstanceOf(OrdinaryPolicy.Wait.class, new GovernancePolicies.Lifestyle(supplier, REF).evaluate(request, advance(request)));
        assertEquals(0, supplier.lifeReads);
    }
    @Test void missingDurableDomainSlotsNeverBecomeAnEmptyLedger() {
        var request = request(); var supplier = new Supplier(request); supplier.missingState = true;
        var result = assertInstanceOf(OrdinaryPolicy.Stop.class, new GovernancePolicies.Lifestyle(supplier, REF).evaluate(request, advance(request)));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, result.stopReason()); assertEquals(0, supplier.lifeReads);
    }
    @Test void councilTiesUseCharacterIdentityAfterFinalGatesAndRejectNonImprovement() {
        var request = request(); var role = CouncilSelection.Position.STEWARD;
        var parsed = CouncilSelection.decode(request, role, councilRaw(request, role, 10, 12, 12));
        assertEquals(BigInteger.valueOf(30), CouncilSelection.choose(parsed).selected().orElseThrow().characterId());
        var unchanged = CouncilSelection.decode(request, role, councilRaw(request, role, 12, 12, 11));
        assertEquals(CouncilSelection.Outcome.NO_CHANGE, CouncilSelection.choose(unchanged).outcome());
        assertThrows(UnsupportedOperationException.class, () -> parsed.candidates().clear());
    }
    @Test void finalGateExcludedCandidateCannotWinAndEveryNativeRowRemainsEvidence() {
        var request = request(); var role = CouncilSelection.Position.STEWARD; Obj original = councilRaw(request, role, 10, 20, 12);
        Obj gates = object(original.get("council_final_gates"), "gates"); List<Value> rows = array(gates.get("rows"), "rows");
        Obj refused = object(rows.getFirst(), "gate").with("candidate_is_guest", new Bool(true));
        var query = CouncilSelection.decode(request, role, original.with("council_final_gates", gates.with("rows", new Arr(List.of(refused, rows.get(1))))));
        assertEquals(2, query.candidates().size()); assertEquals(BigInteger.valueOf(30), CouncilSelection.choose(query).selected().orElseThrow().characterId());
        assertTrue(query.candidates().getFirst().blockers().contains("candidate_is_guest"));
    }
    @Test void councilEntryValidatesAllRawIntegerTokensMissingFieldsAndCompleteFrame() {
        var request = request(); var role = CouncilSelection.Position.STEWARD; Obj original = councilRaw(request, role, 10, 12, 12);
        Obj payload = object(original.get("council_composition_candidates"), "payload"), frame = object(payload.get("snapshot"), "frame");
        for (Value token : List.of(new Bool(true), new DecimalValue("9.0"), new Text("9")))
            assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role,
                    original.with("council_composition_candidates", payload.with("snapshot", frame.with("public_revision", token)))));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role,
                original.with("council_composition_candidates", payload.with("snapshot", frame.with("native_revision", n(10))))));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role, new Obj(java.util.Map.of()).with("status", new Text("available"))));
    }
    @Test void malformedOptionalTaxIsRejectedByTheSharedNativeContract() {
        var request = request(); var role = CouncilSelection.Position.STEWARD; Obj original = councilRaw(request, role, 12, 12, 11);
        Obj payload = object(original.get("council_composition_candidates"), "payload"), seat = object(payload.get("position"), "seat");
        Obj altered = original.with("council_composition_candidates", payload.with("position", seat.with("current_task_owner_domain_tax_mult_v1", new Text("malformed-optional-evidence"))));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role, altered));
    }
    @Test void coreCouncilUsesItsOriginalPublicActionAndNormalCouncilUsesPrivateFinalGates() {
        var request = request(); var supplier = new Supplier(request); var policy = new GovernancePolicies.Council(supplier, REF);
        var core = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluateCoreCouncil(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(GovernancePolicies.CORE_COUNCIL, core.draft().command().orElseThrow().operation());
        supplier.councils.put(CouncilSelection.Position.STEWARD, CouncilSelection.decode(request, CouncilSelection.Position.STEWARD,
                councilRaw(request, CouncilSelection.Position.STEWARD, 10, 12, 12)));
        var normal = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request)));
        var command = normal.draft().command().orElseThrow(); assertEquals(GovernancePolicies.COUNCIL, command.operation());
        assertTrue(command.expected().values().contains(new ExpectedInteger(new FieldKey("council.incumbent_character_id"), BigInteger.valueOf(30))));
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
    }
    @Test void actualLegacyCouncilProducerProjectsOnlyItsCurrentFollowingWithoutManufacturingAnActionReceipt() {
        var request = request(); var supplier = new Supplier(request); var old = supplier.state;
        Obj progress = new Obj(java.util.Map.of()).with("status", new Text("same_job"))
                .with("progress_change", new Obj(java.util.Map.of()).with("raw", n(-125000)).with("scale", n(100000)));
        Obj applied = new Obj(java.util.Map.of()).with("status", new Text("applied"))
                .with("episode_run_id", new Text(request.before().frame().episodeRunId()))
                .with("next_turn_snapshot_id", new Text(request.before().frame().snapshotId()))
                .with("next_turn_native_revision", new IntegerValue(request.before().frame().identity().nativeRevision()))
                .with("next_turn_date_raw", new IntegerValue(request.before().frame().identity().dateRaw()))
                .with("next_turn_job_progress_observation", new Obj(java.util.Map.of())
                        .with("effect_attribution", new Text("not_observed")).with("following_comparison", progress));
        supplier.councils.put(CouncilSelection.Position.STEWARD, CouncilSelection.decode(request, CouncilSelection.Position.STEWARD,
                councilRaw(request, CouncilSelection.Position.STEWARD, 10, 12, 12)));
        var policy = new GovernancePolicies.Council(supplier, REF);
        for (boolean persists : List.of(false, true)) {
            Obj original = applied.with("next_turn_consumed", new Bool(persists));
            Obj body = new Obj(java.util.Map.of()).with("schema", new Text(GovernanceDomainDocument.COUNCIL_SCHEMA))
                    .with("pending", Nil.INSTANCE).with("applied", original);
            var decoded = GovernanceStateSupplier.decodeLegacyCouncil(request, encode(body));
            assertTrue(decoded.latest().isEmpty(), "the actual production decoder retains original JSON without making an ActionReceipt");
            supplier.state = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), Optional.of(decoded), old.crown());
            var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request))).draft();
            assertEquals(GovernancePolicies.COUNCIL, selected.command().orElseThrow().operation());
            Obj consumed = object(selected.detail().get("council_receipt_consumed"), "actual retained current following");
            assertEquals(original, consumed); assertEquals(new Bool(persists), consumed.get("next_turn_consumed"));
            Obj observed = object(consumed.get("next_turn_job_progress_observation"), "retained job observation");
            assertEquals(progress, observed.get("following_comparison"));
            assertEquals(new Text("not_observed"), observed.get("effect_attribution"));
            for (Obj crossed : List.of(original.with("episode_run_id", new Text("other-episode")),
                    original.with("status", new Text("helper_pending")),
                    original.with("next_turn_snapshot_id", new Text("other-snapshot")),
                    original.with("next_turn_consumed", n(0)),
                    original.with("next_turn_consumed", new Text("false")),
                    original.with("next_turn_consumed", Nil.INSTANCE),
                    original.with("next_turn_native_revision", new Bool(true)),
                    original.with("next_turn_native_revision", new DecimalValue("9.0")),
                    original.with("next_turn_native_revision", new Text("9")),
                    original.with("next_turn_native_revision", n(10)),
                    original.with("next_turn_date_raw", new Bool(true)),
                    original.with("next_turn_date_raw", new DecimalValue("100.0")),
                    original.with("next_turn_date_raw", n(101)))) {
                var stale = GovernanceStateSupplier.decodeLegacyCouncil(request, encode(body.with("applied", crossed)));
                assertTrue(stale.latest().isEmpty());
                supplier.state = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), Optional.of(stale), old.crown());
                var again = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request))).draft();
                assertNull(again.detail().get("council_receipt_consumed"));
                assertEquals(selected.command(), again.command(), "a presentation original never grants a different submission");
            }
        }
    }
    @Test void coreCouncilConsumesActualLegacyPendingBeforeAnyNativeCandidateRead() {
        var request = request(); var supplier = new Supplier(request); var old = supplier.state;
        int[] nativeCoreReads = { 0 };
        var actual = new GovernanceCouncilSupplier(supplier, new GovernanceCouncilSupplier.CouncilReadPort() {
            @Override public Read<CouncilSelection.Query> readPrivate(org.xar.ck3.control.application.planning.PlanningRequest current,
                    CouncilSelection.Position position) { throw new AssertionError("pending core must not query private candidates"); }
            @Override public Read<CouncilSelection.Query> readCore(org.xar.ck3.control.application.planning.PlanningRequest current) {
                nativeCoreReads[0]++;
                throw new AssertionError("pending core must not query public candidates");
            }
        });
        var policy = new GovernancePolicies.Council(actual, REF);
        for (String episode : List.of(request.before().frame().episodeRunId(), "other-episode")) {
            Obj pending = new Obj(java.util.Map.of()).with("stage", new Text("submission_unresolved"))
                    .with("episode_run_id", new Text(episode)).with("action_request_id", new Text("original-council-request"))
                    .with("pre_native_revision", n(8)).with("pre_date_raw", n(100)).with("action_ack", Nil.INSTANCE);
            Obj body = new Obj(java.util.Map.of()).with("schema", new Text(GovernanceDomainDocument.COUNCIL_SCHEMA))
                    .with("pending", pending).with("applied", Nil.INSTANCE);
            var decoded = GovernanceStateSupplier.decodeLegacyCouncil(request, encode(body));
            assertEquals(episode.equals(request.before().frame().episodeRunId()) ? DomainStatus.PENDING : DomainStatus.UNKNOWN,
                    decoded.status());
            assertEquals(pending, decoded.legacyPending().orElseThrow());
            assertEquals(body, decoded.originalBody()); assertTrue(decoded.latest().isEmpty());
            assertEquals(body, parse(encode(decoded.originalBody())), "serde must retain the original unresolved request");
            supplier.state = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), Optional.of(decoded), old.crown());
            assertInstanceOf(OrdinaryPolicy.Wait.class, policy.evaluateCoreCouncil(request, OrdinaryPolicy.Draft.empty()));
            assertEquals(0, nativeCoreReads[0]); assertEquals(0, supplier.councilReads);
            assertEquals(pending, supplier.state.council().orElseThrow().legacyPending().orElseThrow());
        }
        supplier.missingState = true;
        var unavailable = assertInstanceOf(OrdinaryPolicy.Stop.class, policy.evaluateCoreCouncil(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, unavailable.stopReason());
        supplier.missingState = false;
        supplier.state = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), Optional.empty(), old.crown());
        var missing = assertInstanceOf(OrdinaryPolicy.Stop.class, policy.evaluateCoreCouncil(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, missing.stopReason());
        supplier.state = new Durable(request(10, false, List.of()).before(), old.sessionId(), old.cadence(), old.opening(),
                old.council(), old.crown());
        assertThrows(IllegalArgumentException.class, () -> policy.evaluateCoreCouncil(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(0, nativeCoreReads[0]);
    }
    @Test void councilDoesNotReplaceAnExistingEarlierWorldAction() {
        var request = request(); var supplier = new Supplier(request);
        var crown = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Crown(supplier, REF).evaluate(request, advance(request)));
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, new GovernancePolicies.Council(supplier, REF).evaluate(request, crown.draft()));
        assertEquals(0, supplier.councilReads);
    }
    @Test void crownKeepsNativeCurrencyQuoteAndRequiresIndependentLawAndBalances() {
        var request = request(); var supplier = new Supplier(request);
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Crown(supplier, REF).evaluate(request, advance(request)));
        var command = selected.draft().command().orElseThrow(); assertEquals(GovernancePolicies.CROWN, command.operation());
        assertEquals(new Text("crown_authority_1"), command.arguments().get("law_key"));
        assertTrue(command.expected().values().contains(new ExpectedText(new FieldKey("crown.balance_gold_raw"), "900")));
        assertTrue(command.expected().values().contains(new ExpectedText(new FieldKey("crown.effective_law_key"), "crown_authority_1")));
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
    }
    @Test void openingRequeriesTheExactChosenFocusLastAndCreatesOnlyOneCommand() {
        var request = request(9, true, List.of()); var supplier = new Supplier(request);
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Opening(supplier, REF).evaluate(request, OrdinaryPolicy.Draft.empty()));
        var command = selected.draft().command().orElseThrow();
        assertEquals(GovernancePolicies.FOCUS, command.operation()); assertEquals(OrdinaryPolicy.Kind.OPENING_FOCUS, selected.draft().kind());
        assertEquals(new Text(supplier.focusTargets.getLast()), command.arguments().get("target_key"));
        assertEquals(2, supplier.lifeReads); assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
    }
    @Test void openingDateDriftAndCrownUnknownStateDoNotProduceAnotherAction() {
        var request = request(9, true, List.of()); var supplier = new Supplier(request); var old = supplier.state;
        var drift = new OpeningGate("unit-episode", BigInteger.valueOf(99), OpeningStage.AWAIT_SUBMIT, Optional.empty(), Optional.empty());
        supplier.state = new Durable(old.observed(), old.sessionId(), old.cadence(), Optional.of(drift), old.council(), old.crown());
        assertInstanceOf(OrdinaryPolicy.Wait.class, new GovernancePolicies.Opening(supplier, REF).evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(0, supplier.lifeReads);
        supplier.state = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), old.council(),
                Optional.of(new DomainState(DomainStatus.UNKNOWN, Optional.empty(), Optional.empty(), new Obj(java.util.Map.of()))));
        assertInstanceOf(OrdinaryPolicy.Wait.class, new GovernancePolicies.Crown(supplier, REF).evaluate(request, advance(request)));
    }
}

