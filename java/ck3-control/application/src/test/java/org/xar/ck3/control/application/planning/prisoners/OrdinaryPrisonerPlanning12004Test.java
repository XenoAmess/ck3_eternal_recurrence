package org.xar.ck3.control.application.planning.prisoners;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.*;

/** Entirely synthetic source/endpoint/writer doubles. No fixture is a live native or persisted ledger receipt. */
final class OrdinaryPrisonerPlanning12004Test {
    private static final String SHA = "a".repeat(64);
    private static final ExactRef REF = new ExactRef("C:/unit/original.json", 1, SHA);
    private static final Instant NOW = Instant.parse("2026-10-23T15:00:00Z");
    private static final long[] IDS = {54235, 56063};
    private static final long PLAYER = 29829;
    private static final BigInteger NATIVE = BigInteger.valueOf(1014);
    private static final int DATE = 53286360;
    private static final OperationKey ROOT = new OperationKey("query-campaign-root-context-v1");
    private static final List<PrisonerVanillaResearch.InteractionTree> TREES = Arrays.stream(PrisonerVanillaResearch.Interaction.values())
            .map(value -> new PrisonerVanillaResearch.InteractionTree(value, new PrisonerVanillaResearch.Span(0, 1, 1, 1), List.of())).toList();
    private static final PrisonerVanillaResearch.Catalog CATALOG = new PrisonerVanillaResearch.Catalog(
            new PrisonerVanillaResearch.Source(new G2Source("unit-machine", NOW.toString(), "1.20.0.4",
                    new ExactRef("C:/unit/stock.txt", PrisonerVanillaResearch.STOCK_BYTES, PrisonerVanillaResearch.STOCK_SHA256)),
                    PrisonerVanillaResearch.EXE_SHA256), TREES, List.of());

    @Test void serviceBundleBindsOnceAndMissingBindingNeverManufacturesANativeContract()throws Exception {
        Fixture fixture=new Fixture();var detached=new Queries(fixture.queries.collections(),Map.of());
        assertThrows(IllegalArgumentException.class,detached::requireTurnBundleBound);
        assertThrows(IllegalArgumentException.class,()->detached.readTurnBundle(fixture.request));
        detached.bindTurnBundle(fixture.queries::readTurnBundle);detached.requireTurnBundleBound();
        var value=assertInstanceOf(ObservedTurnBundle.class,detached.readTurnBundle(fixture.request));
        assertEquals(fixture.request.before(),value.before());assertEquals(REF,value.originalRoot());
        assertEquals(StrictJson.parse(bundle().bytes()),StrictJson.parse(value.value().bytes()));
        assertThrows(IllegalArgumentException.class,()->detached.bindTurnBundle(fixture.queries::readTurnBundle));
    }

    @Test void fullCollectorAndExistingFormalSelectorProduceOneExactRansomProposal() {
        Fixture fixture = new Fixture();
        var result = fixture.policy(PlanningStage.PRISONER_RANSOM).evaluate(fixture.request, idle());
        ActionCommand command = assertInstanceOf(Replace.class, result).draft().command().orElseThrow();
        assertEquals(PrisonerOrdinaryPolicy12004.RANSOM, command.operation());
        assertEquals(BigInteger.valueOf(54235), OpportunityJson.integer(command.arguments().get("prisoner_character_id"), "prisoner"));
        assertEquals(List.of(collectionStep(0), collectionStep(1), collectionStep(0)), fixture.calls);
        assertFalse(OpportunityJson.bool(assertInstanceOf(Replace.class, result).draft().detail().get("prisoner_material_result"), "material_result"));
        assertArrayEquals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(ActionCodec.decodeCommand(ActionCodec.encodeCommand(command))));
    }
    @Test void changedFinalQuoteNeverTurnsIntoAnotherSubmit() {
        Fixture fixture = new Fixture(); fixture.changeFinalQuote = true;
        var result = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RANSOM).evaluate(fixture.request, idle()));
        assertTrue(result.draft().command().isEmpty()); assertEquals(0, fixture.commandBindings);
    }
    @Test void absentCatalogDoesNotInventNativeLegalityOrRansom() {
        Fixture fixture = new Fixture(); fixture.catalog = Optional.empty();
        var result = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RANSOM).evaluate(fixture.request, idle()));
        assertTrue(result.draft().command().isEmpty()); assertEquals(0, fixture.commandBindings);
    }
    @Test void releaseUsesLatestAcceptedOrdinalAndFinalOriginalRead() {
        Fixture fixture = new Fixture(); fixture.release = true; fixture.ransom = false;
        var result = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RELEASE).evaluate(fixture.request, idle()));
        assertEquals(PrisonerOrdinaryPolicy12004.RELEASE, result.draft().command().orElseThrow().operation());
        assertEquals(List.of(collectionStep(1)), fixture.calls);
        assertEquals(BigInteger.ZERO, OpportunityJson.integer(result.draft().command().orElseThrow().arguments().get("release_option_mask_bits"), "mask"));
    }
    @Test void unreadableRansomQuoteInRetainedHistoryDoesNotBecomeFreeRelease() {
        for (String reason : List.of("quote_unavailable", "payer_gold_read_unavailable", "final_legality_unavailable")) {
            Fixture fixture = new Fixture(); fixture.release = true; fixture.ransom = false;
            ObjectNode observed = wire(1, true, false, 0, false);
            ((ObjectNode) observed.path("player_prisoner_collection").path("prisoners").get(1)).set("ransom_quote_preview", unavailable(reason));
            fixture.request = withHistory(fixture.request, List.of(history(observed)));
            var collector = new PrisonerCollector12004(fixture.bindings());
            var frame = PrisonerCollector12004.frame(fixture.request);
            var selected = collector.retainedReleaseEntries(fixture.request, frame).getFirst();
            assertFalse(PrisonerCollector12004.positiveRansomPriority(selected, frame), "retained command preparation keeps its original predicate");
            assertFalse(collector.retainedReleaseReady(fixture.request));
            var result = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RELEASE).evaluate(fixture.request, idle()));
            assertTrue(result.draft().command().isEmpty()); assertEquals(0, fixture.commandBindings); assertTrue(fixture.calls.isEmpty());
            assertTrue(OpportunityJson.text(result.draft().detail().get("prisoner_observation_unavailable"), "unavailable").contains(reason));
        }
    }
    @Test void unreadableFinalRansomQuoteDoesNotBecomeFreeRelease() {
        for (String reason : List.of("quote_unavailable", "payer_gold_read_unavailable", "final_legality_unavailable")) {
            Fixture fixture = new Fixture(); fixture.release = true; fixture.ransom = false; fixture.refreshedQuoteFailure = reason;
            var result = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RELEASE).evaluate(fixture.request, idle()));
            assertTrue(result.draft().command().isEmpty()); assertEquals(0, fixture.commandBindings);
            assertEquals(List.of(collectionStep(1)), fixture.calls);
            assertTrue(OpportunityJson.text(result.draft().detail().get("prisoner_observation_unavailable"), "unavailable").contains(reason));
        }
    }
    @Test void observedNativeNoRansomOpportunityStillPermitsRelease() {
        for (String reason : List.of("final_can_send_false", "extortionate_final_can_send_false", "payer_below_one_gold")) {
            Fixture fixture = new Fixture(); fixture.release = true; fixture.ransom = false; fixture.refreshedQuoteFailure = reason;
            ObjectNode observed = wire(1, true, false, 0, false);
            ((ObjectNode) observed.path("player_prisoner_collection").path("prisoners").get(1)).set("ransom_quote_preview", unavailable(reason));
            fixture.request = withHistory(fixture.request, List.of(history(observed)));
            assertTrue(new PrisonerCollector12004(fixture.bindings()).retainedReleaseReady(fixture.request));
            var result = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RELEASE).evaluate(fixture.request, idle()));
            assertEquals(PrisonerOrdinaryPolicy12004.RELEASE, result.draft().command().orElseThrow().operation());
            assertEquals(List.of(collectionStep(1)), fixture.calls);
        }
    }
    @Test void observedRansomRefusalStillHasNoPriorityOverRelease() {
        Fixture fixture = new Fixture(); fixture.release = true; fixture.ransom = false;
        ObjectNode observed = wire(1, true, true, 500, false);
        var frame = new FrameBinding(NATIVE, DATE, PLAYER, IDS[1]);
        ((ObjectNode) observed.path("player_prisoner_collection").path("prisoners").get(1)).set("ransom_quote_preview", PrisonerVanillaResearch.quoteJson(
                new PrisonerVanillaResearch.AvailableQuote(frame, BigInteger.valueOf(77), 73001, PrisonerVanillaResearch.Option.GOLD, 500, -10, 2)));
        fixture.request = withHistory(fixture.request, List.of(history(observed)));
        assertTrue(new PrisonerCollector12004(fixture.bindings()).retainedReleaseReady(fixture.request));
        var result = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RELEASE).evaluate(fixture.request, idle()));
        assertEquals(PrisonerOrdinaryPolicy12004.RELEASE, result.draft().command().orElseThrow().operation());
    }
    @Test void positiveRansomKeepsPriorityOverAcceptedFreeRelease() {
        Fixture fixture = new Fixture(); fixture.release = true;
        assertInstanceOf(Keep.class, fixture.policy(PlanningStage.PRISONER_RELEASE).evaluate(fixture.request, idle()));
        assertEquals(0, fixture.commandBindings);
    }
    @Test void releaseWithoutRetainedOfferNeverInventsUnconditionalDiscovery() {
        Fixture fixture = new Fixture();
        assertInstanceOf(PrisonerCollector12004.Empty.class, new PrisonerCollector12004(fixture.bindings()).collectRelease(fixture.request));
        assertTrue(fixture.calls.isEmpty());
    }
    @Test void distinctOrdinalOrderUsesLastActualHistoryOccurrenceRatherThanOrdinalMagnitude() {
        Fixture fixture = new Fixture();
        fixture.request = withHistory(fixture.request, List.of(history(wire(1, true, false, 0, false)), history(wire(0, true, false, 0, false))));
        var collector = new PrisonerCollector12004(fixture.bindings());
        var entries = collector.retainedReleaseEntries(fixture.request, PrisonerCollector12004.frame(fixture.request));
        assertEquals(List.of(1, 0), entries.stream().map(entry -> entry.collection().selectedOrdinal()).toList());
        fixture.request = withHistory(fixture.request, List.of(history(wire(1, true, false, 0, false)), history(wire(0, true, false, 0, false)), history(wire(1, false, false, 0, false))));
        entries = collector.retainedReleaseEntries(fixture.request, PrisonerCollector12004.frame(fixture.request));
        assertEquals(List.of(0, 1), entries.stream().map(entry -> entry.collection().selectedOrdinal()).toList());
        assertFalse(PrisonerCollector12004.acceptedRelease(entries.getLast(), PrisonerCollector12004.frame(fixture.request)));
        assertTrue(fixture.calls.isEmpty());
    }
    @Test void explicitNullEmptyOrUnpairedReleaseIntentNeverBecomesUnconditional() {
        Fixture fixture = new Fixture();
        for (int variant = 0; variant < 4; variant++) {
            ObjectNode wire = wire(0, true, false, 0, false);
            if (variant == 0) wire.putNull("queried_release_option_keys").put("queried_release_option_mask_bits", 0);
            if (variant == 1) { wire.putArray("queried_release_option_keys"); wire.put("queried_release_option_mask_bits", 0); }
            if (variant == 2) wire.put("queried_release_option_mask_bits", 0);
            if (variant == 3) wire.putArray("queried_release_option_keys").add("demand_conversion");
            fixture.request = withHistory(fixture.request, List.of(history(wire)));
            assertInstanceOf(PrisonerCollector12004.Unavailable.class, new PrisonerCollector12004(fixture.bindings()).collectRelease(fixture.request));
        }
        assertTrue(fixture.calls.isEmpty());
    }
    @Test void formalRansomRequiresActuallyPositivePlayerDynastyAndRejectsEqualWrongTypes() {
        for (int variant = 0; variant < 4; variant++) {
            ObjectNode wire = wire(0, false, true, 500, false); ObjectNode value = (ObjectNode) wire.get("player_prisoner_collection");
            if (variant == 0) value.putNull("played_dynasty_id");
            if (variant == 1) value.put("played_dynasty_id", 0);
            if (variant == 2) value.put("played_dynasty_id", true);
            if (variant == 3) value.put("played_dynasty_id", 174.0);
            assertThrows(IllegalArgumentException.class, () -> org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.read(StrictJson.canonical(wire),
                    new org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Frame(BigInteger.valueOf(37), NATIVE, DATE, PLAYER, List.of()), IDS[0], CATALOG));
        }
    }
    @Test void missingDomainLedgerDoesNotBecomeEmptyAndPendingNeverReplays() {
        Fixture missing = new Fixture(); missing.ledger = new LedgerUnavailable("domain body unavailable");
        var result = assertInstanceOf(Replace.class, missing.policy(PlanningStage.PRISONER_RANSOM).evaluate(missing.request, idle()));
        assertTrue(result.draft().command().isEmpty()); assertTrue(missing.calls.isEmpty());
        Fixture pending = new Fixture();
        pending.ledger = new KnownLedger(REF, Optional.empty(), Optional.of(new Pending(Family.RANSOM,
                new OpportunityJson.Obj(Map.of("stage", new OpportunityJson.Text("submission_unresolved"))), REF)));
        result = assertInstanceOf(Replace.class, pending.policy(PlanningStage.PRISONER_RANSOM).evaluate(pending.request, idle()));
        assertTrue(result.draft().command().isEmpty()); assertTrue(pending.calls.isEmpty());
        assertNotNull(result.draft().detail().get("prisoner_ransom_pending"));
    }
    @Test void unavailableObserverAndChangedCommandFactoryCannotAuthorizeSubmit() {
        Fixture missing = new Fixture(); missing.observer = false;
        assertTrue(assertInstanceOf(Replace.class, missing.policy(PlanningStage.PRISONER_RANSOM).evaluate(missing.request, idle())).draft().command().isEmpty());
        Fixture wrong = new Fixture(); wrong.wrongFactory = true;
        assertTrue(assertInstanceOf(Replace.class, wrong.policy(PlanningStage.PRISONER_RANSOM).evaluate(wrong.request, idle())).draft().command().isEmpty());
    }
    @Test void incompleteOrdinalAndFullGenerationDriftRemainUnavailable() {
        Fixture missing = new Fixture(); missing.failOrdinal = 1;
        assertInstanceOf(PrisonerCollector12004.Unavailable.class, new PrisonerCollector12004(missing.bindings()).collect(missing.request));
        Fixture drift = new Fixture(); drift.drift = true;
        assertInstanceOf(PrisonerCollector12004.Unavailable.class, new PrisonerCollector12004(drift.bindings()).collect(drift.request));
    }
    @Test void integerLookingFloatOrBooleanCollectionCountIsRejected() {
        Fixture fixture = new Fixture(); fixture.badCount = true;
        assertInstanceOf(PrisonerCollector12004.Unavailable.class, new PrisonerCollector12004(fixture.bindings()).collect(fixture.request));
        fixture.badCount = false; fixture.booleanCount = true;
        assertInstanceOf(PrisonerCollector12004.Unavailable.class, new PrisonerCollector12004(fixture.bindings()).collect(fixture.request));
    }
    @Test void actualWarWithoutItsExactReadBindingDoesNotMeanNoRetention() {
        Fixture fixture = new Fixture(); fixture.request = request(true);
        assertInstanceOf(PrisonerCollector12004.Unavailable.class, new PrisonerCollector12004(fixture.bindings()).collect(fixture.request));
        assertTrue(fixture.calls.isEmpty());
    }
    @Test void foregroundAndSelectedWorldActionRetainOriginalPriority() {
        Fixture fixture = new Fixture();
        var previous = new Draft("unit", "urgent", "urgent work", Kind.FOREGROUND, Optional.empty(), Purpose.READ_ONLY, Optional.empty(), EMPTY);
        assertInstanceOf(NotApplicable.class, fixture.policy(PlanningStage.PRISONER_RELEASE).evaluate(fixture.request, previous));
        assertTrue(fixture.calls.isEmpty());
    }
    @Test void preflightRunsExistingPureProducerThenRequiresExactWriterReadback() {
        Fixture fixture = new Fixture();
        var policy = new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, REF, fixture.bindings());
        var result = assertInstanceOf(Replace.class, policy.evaluate(fixture.request, idle()));
        assertEquals(1, fixture.records); assertTrue(result.draft().command().isEmpty());
        assertEquals("xar.ck3.succession-expectation/v1", OpportunityJson.text(
                OpportunityJson.object(result.draft().detail().get("succession_expectation"), "expectation").get("schema"), "schema"));
        fixture = new Fixture(); fixture.wrongReadback = true;
        assertInstanceOf(Wait.class, new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, REF, fixture.bindings()).evaluate(fixture.request, idle()));
    }
    @Test void terminalCannotReconstructTheMissingPredeathEstate() {
        Fixture fixture = new Fixture(); var snapshot = fixture.request.observations().snapshot()
                .with("one_life_terminal_reason", new OpportunityJson.Text("played_character_changed"));
        fixture.request = withSnapshot(fixture.request, snapshot);
        var result = assertInstanceOf(Stop.class, new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, REF, fixture.bindings()).evaluate(fixture.request, idle()));
        assertEquals(PlanningResult.StopReason.NATURAL_SUCCESSION_REQUIRED, result.stopReason()); assertTrue(fixture.calls.isEmpty());
    }
    @Test void exactReadFactoryRejectsRequestFieldOverrideAndPreservesRawToken() {
        Fixture fixture = new Fixture(); var contract = fixture.queries.collections().getFirst();
        var request = new PlanningReadRequest(fixture.request.before(), fixture.request.source(), "unit-session", contract.operation(),
                new OpportunityJson.Obj(Map.of("release_option_mask_bits", new OpportunityJson.IntegerValue(BigInteger.ONE))), NOW.plusSeconds(60));
        assertThrows(IllegalArgumentException.class, () -> contract.prepare(request, "unit-read"));
        RawJson token = new RawJson("{\"x\":18446744073709551615}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertArrayEquals(token.bytes(), new RawJson(token.bytes()).bytes());
    }
    @Test void currentRetainedAcceptedReleaseDefersOnlyInitialRootAndTailKeepsItsPriority() {
        Fixture fixture = new Fixture(); fixture.release = true; fixture.ransom = false;
        ObjectNode collection = wire(1, true, false, 0, false).put("queried_snapshot_id", "public:37").put("queried_revision", 37);
        ObjectNode history = StrictJson.object().put("ok", true).put("command", collectionStep(1)); history.set("result", collection);
        var old = fixture.request.observations();
        fixture.request = new PlanningRequest(fixture.request.before(), fixture.request.source(), fixture.request.sessionId(), fixture.request.deadline(),
                new PlanningObservation(old.snapshot(), List.of(object(StrictJson.canonical(history))), old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(),
                        old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), false));
        var preflight = assertInstanceOf(Replace.class, new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, REF, fixture.bindings()).evaluate(fixture.request, idle()));
        assertTrue(OpportunityJson.bool(preflight.draft().detail().get("succession_deferred_root_required"), "deferred")); assertTrue(fixture.calls.isEmpty());
        var release = assertInstanceOf(Replace.class, fixture.policy(PlanningStage.PRISONER_RELEASE_DISCOVERY).evaluate(fixture.request, preflight.draft()));
        assertInstanceOf(Keep.class, new SuccessionOrdinaryPolicy12004(PlanningStage.DEFERRED_SUCCESSION_ROOT, REF, fixture.bindings()).evaluate(fixture.request, release.draft()));
        assertEquals(1, fixture.calls.size()); assertEquals(0, fixture.records);
    }
    @Test void absentSoleWriterNeverTreatsPureProjectionOrReadAckAsPersisted() {
        Fixture fixture = new Fixture(); fixture.missingWriter = true;
        assertInstanceOf(Wait.class, new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, REF, fixture.bindings()).evaluate(fixture.request, idle()));
        assertEquals(1, fixture.records); assertEquals(0, fixture.commandBindings);
    }

    @Test void malformedEmptyCollectionFlagsAreUnavailableRatherThanAQueryCrash() {
        Fixture fixture = new Fixture(); fixture.malformedEmpty = true;
        assertInstanceOf(PrisonerCollector12004.Unavailable.class, new PrisonerCollector12004(fixture.bindings()).collect(fixture.request));
        assertEquals(1, fixture.calls.size()); assertEquals(0, fixture.commandBindings);
    }
    @Test void earlierDifferentOrdinalAcceptedOfferRetainsInitialRootPriority() {
        Fixture fixture = new Fixture();
        ObjectNode accepted = wire(0, true, false, 0, false).put("queried_snapshot_id", "public:37").put("queried_revision", 37);
        ObjectNode rejected = wire(1, false, false, 0, false).put("queried_snapshot_id", "public:37").put("queried_revision", 37);
        ObjectNode first = StrictJson.object().put("ok", true).put("command", collectionStep(0)); first.set("result", accepted);
        ObjectNode last = StrictJson.object().put("ok", true).put("command", collectionStep(1)); last.set("result", rejected);
        var old = fixture.request.observations();
        fixture.request = new PlanningRequest(fixture.request.before(), fixture.request.source(), fixture.request.sessionId(), fixture.request.deadline(),
                new PlanningObservation(old.snapshot(), List.of(object(StrictJson.canonical(first)), object(StrictJson.canonical(last))),
                        old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(), old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), false));
        var result = assertInstanceOf(Replace.class, new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, REF, fixture.bindings()).evaluate(fixture.request, idle()));
        assertTrue(OpportunityJson.bool(result.draft().detail().get("succession_deferred_root_required"), "deferred"));
        assertTrue(fixture.calls.isEmpty());
    }
    @Test void importedExplicitNullBodiesReadClearWithoutInitializationOrWrites() {
        BodyStore bodies = new BodyStore(); var result = new PrisonerDomainBodyReader12004(bodies, "unit-machine").read(request(false));
        var known = assertInstanceOf(KnownLedger.class, result); assertTrue(known.release().isEmpty()); assertTrue(known.ransom().isEmpty());
        assertEquals(4, bodies.reads); assertEquals(0, bodies.writes);
    }
    @Test void unimportedDomainSlotIsUnavailableAndCannotBecomeEmpty() {
        BodyStore bodies = new BodyStore(); bodies.missing = true;
        assertInstanceOf(LedgerUnavailable.class, new PrisonerDomainBodyReader12004(bodies, "unit-machine").read(request(false)));
        assertEquals(0, bodies.writes);
    }
    @Test void priorGameWithSameRobertIdCannotQualifyTheCurrentEpisode() {
        BodyStore bodies=new BodyStore();bodies.foreignEpoch=true;
        assertInstanceOf(LedgerUnavailable.class,new PrisonerDomainBodyReader12004(bodies,"unit-machine").read(request(false)));
        assertEquals(0,bodies.writes);
    }
    @Test void changedHeadOrBodyDuringPairReadIsUnavailable() {
        BodyStore bodies = new BodyStore(); bodies.drift = true;
        assertInstanceOf(LedgerUnavailable.class, new PrisonerDomainBodyReader12004(bodies, "unit-machine").read(request(false)));
        assertEquals(0, bodies.writes);
    }
    @Test void importedPendingKeepsOriginalAndRejectsForeignActorOrMissingField() {
        BodyStore bodies = new BodyStore(); bodies.pending = true;
        var known = assertInstanceOf(KnownLedger.class, new PrisonerDomainBodyReader12004(bodies, "unit-machine").read(request(false)));
        assertTrue(known.ransom().isPresent()); assertEquals(new OpportunityJson.Text("submission_unresolved"), known.ransom().orElseThrow().original().get("stage"));
        bodies.foreign = true;
        assertInstanceOf(LedgerUnavailable.class, new PrisonerDomainBodyReader12004(bodies, "unit-machine").read(request(false)));
        bodies.foreign = false; bodies.missingPending = true;
        assertInstanceOf(LedgerUnavailable.class, new PrisonerDomainBodyReader12004(bodies, "unit-machine").read(request(false)));
    }
    private static final class BodyStore implements DomainBodies.Store {
        boolean missing, drift, pending, foreign, missingPending,foreignEpoch; int reads, writes;
        @Override public DomainBodies.Read read(DomainBodies.Slot slot) {
            reads++;
            if (missing) return new DomainBodies.Unavailable(DomainBodies.Reason.UNIMPORTED, Optional.empty(), "unit body was not imported");
            Family family=slot==DomainBodies.Slot.PRISONER_RELEASE?Family.RELEASE:Family.RANSOM;
            var request=request(false);var owner=new PrisonerEpisodeLedger12004.Owner(
                    new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(request.before().machineId(),foreignEpoch?
                            new GameGeneration(4243,new PythonOnlyUInt64(new BigInteger("133000000000000001"))):request.before().game(),request.sessionId()),
                    PLAYER,request.before().frame().episodeRunId(),request.source());
            ObjectNode body=(ObjectNode)StrictJson.parse(PrisonerEpisodeLedger12004.fresh(family,owner,REF).bytes());
            if (slot == DomainBodies.Slot.PRISONER_RANSOM) {
                if (pending) body.putObject("pending").put("stage", "submission_unresolved").put("player_character_id", foreign ? 999 : PLAYER)
                        .put("prisoner_character_id",IDS[0]).put("pre_native_revision", 1013).put("pre_date_raw", DATE).put("payer_character_id",73000)
                        .put("selected_option","gold").put("amount_is_acceptance_time_quote",false).put("quoted_gold_raw",500).put("pre_player_gold_raw",10000000).put("material_result",false);
                if (missingPending) body.remove("pending");
            }
            byte[] bytes = StrictJson.canonical(body); var payload = new ExactRef("C:/unit/" + slot + ".json", bytes.length, ActionCodec.sha256(bytes));
            var identity = new WriterContracts.FileIdentity("1", "2", "133000000000000000", NOW.toString(), bytes.length);
            var reference = new DomainBodies.BodyRef(slot, PrisonerEpisodeLedger12004.contractSchema(family), payload, identity, List.of(REF));
            ExactRef head = drift && reads > 2 ? new ExactRef("C:/unit/head.json", 1, "b".repeat(64)) : REF;
            return new DomainBodies.Available(reference, bytes, head, List.of());
        }
        @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request) {
            writes++; throw new AssertionError("read adapter cannot preview import");
        }
        @Override public WriterContracts.Receipt commitImport(DomainBodies.PreparedImport prepared) {
            writes++; throw new AssertionError("read adapter cannot commit import");
        }
    }
    private static Draft idle() { return new Draft("unit", "ordinary", "advance if no action", Kind.ORDINARY, Optional.empty(),
            Purpose.DATE_ADVANCE, Optional.empty(), new OpportunityJson.Obj(Map.of("original_plan", new OpportunityJson.Text("retained")))); }
    @Test void olderAcceptedSameOrdinalCannotOverrideItsLatestRejectedRead() {
        Fixture fixture = new Fixture();
        ObjectNode accepted = wire(0, true, false, 0, false).put("queried_snapshot_id", "public:37").put("queried_revision", 37);
        ObjectNode rejected = wire(0, false, false, 0, false).put("queried_snapshot_id", "public:37").put("queried_revision", 37);
        ObjectNode first = StrictJson.object().put("ok", true).put("command", collectionStep(0)); first.set("result", accepted);
        ObjectNode last = StrictJson.object().put("ok", true).put("command", collectionStep(0)); last.set("result", rejected);
        var old = fixture.request.observations();
        fixture.request = new PlanningRequest(fixture.request.before(), fixture.request.source(), fixture.request.sessionId(), fixture.request.deadline(),
                new PlanningObservation(old.snapshot(), List.of(object(StrictJson.canonical(first)), object(StrictJson.canonical(last))),
                        old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(), old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), false));
        var result = assertInstanceOf(Replace.class, new SuccessionOrdinaryPolicy12004(PlanningStage.SUCCESSION_PREFLIGHT, REF, fixture.bindings()).evaluate(fixture.request, idle()));
        assertNotNull(result.draft().detail().get("succession_expectation"));
        assertEquals(List.of(ROOT.value()), fixture.calls); assertEquals(1, fixture.records);
    }
    private static PlanningRequest request(boolean war) {
        ObjectNode snapshot = StrictJson.object().put("snapshot_id", "public:37").put("episode_run_id", "episode")
                .put("episode_character_id", PLAYER).put("revision", 37).put("native_revision", 1014).put("date_raw", DATE)
                .put("paused", true).put("map_ready", true).put("one_life_terminal", false);
        snapshot.putNull("one_life_terminal_reason"); snapshot.putNull("active_event"); snapshot.putNull("pending_character_interaction");
        snapshot.putObject("played_character").put("character_id", PLAYER).put("alive", true);
        snapshot.putObject("played_character_gold").put("raw", 10000000).put("scale", 100000);
        snapshot.putObject("succession_lifecycle").put("lifecycle", "ordinary_campaign_succession");
        snapshot.putArray("player_armies");
        var wars = snapshot.putArray("active_wars"); if (war) wars.addObject().put("war_id", 16777231);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(PLAYER), NATIVE,
                BigInteger.valueOf(DATE)), "public:37", BigInteger.valueOf(37), "episode");
        var before = new ProposalLifecycle.ObservationIdentity("unit-machine", new GameGeneration(4242,
                new PythonOnlyUInt64(new BigInteger("133000000000000000"))), frame, 1);
        G2Source source = new G2Source("unit-machine", NOW.toString(), "1.20.0.4@sha256:" + PrisonerVanillaResearch.EXE_SHA256, REF);
        var observations = new PlanningObservation(object(StrictJson.canonical(snapshot)), List.of(),
                Set.of(PrisonerOrdinaryPolicy12004.RELEASE, PrisonerOrdinaryPolicy12004.RANSOM, ROOT), Set.of(), Optional.empty(), List.of(),
                Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "unit-session", NOW.plusSeconds(60), observations);
    }
    private static PlanningRequest withSnapshot(PlanningRequest request, OpportunityJson.Obj snapshot) {
        var old = request.observations();
        return new PlanningRequest(request.before(), request.source(), request.sessionId(), request.deadline(),
                new PlanningObservation(snapshot, old.history(), old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(), old.actionFacts(),
                        old.campaignGoal(), old.crossRunPlan(), old.initialLifestyleFocusRequired()));
    }
    private static PlanningRequest withHistory(PlanningRequest request, List<OpportunityJson.Obj> history) {
        var old = request.observations();
        return new PlanningRequest(request.before(), request.source(), request.sessionId(), request.deadline(), new PlanningObservation(
                old.snapshot(), history, old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(), old.actionFacts(), old.campaignGoal(),
                old.crossRunPlan(), old.initialLifestyleFocusRequired()));
    }
    private static OpportunityJson.Obj history(ObjectNode wire) {
        wire.put("queried_snapshot_id", "public:37").put("queried_revision", 37);
        ObjectNode row = StrictJson.object().put("ok", true).put("command", wire.get("step").textValue()); row.set("result", wire);
        return object(StrictJson.canonical(row));
    }
    private static ObjectNode unavailable(String reason) {
        return StrictJson.object().put("private_build", true).put("read_only", true).put("advertised", false).put("action_surface_present", false)
                .put("status", "unavailable").put("unavailable_reason", reason);
    }
    private static ObjectNode wire(int ordinal, boolean release, boolean ransom, long amount, boolean drift) {
        ObjectNode envelope = StrictJson.object().put("status", "available").put("accepted", true).put("private_build", true)
                .put("read_only", true).put("advertised", false).put("backend_id", "native-headless").put("snapshot_revision", 1014)
                .put("step", collectionStep(ordinal)).put("query_sequence", 10 + ordinal).put("observation_revision", 77);
        ObjectNode value = envelope.putObject("player_prisoner_collection").put("schema", "player-prisoner-collection-private-v1")
                .put("schema_version", 6).put("status", "available").putNull("unavailable_reason").put("snapshot_revision", 1014)
                .put("played_character_id", PLAYER).put("date_raw", DATE).put("collection_complete", true).put("total_count", 2).put("returned_count", 2)
                .put("played_house_id", 174).put("played_dynasty_id", 174).put("played_dread_raw", 0);
        var rows = value.putArray("prisoners");
        for (int index = 0; index < 2; index++) {
            long prisoner = IDS[index] + (drift && index == 0 && ordinal == 1 ? 16777216 : 0);
            ObjectNode row = rows.addObject().put("source_ordinal", index).put("prisoner_character_id", prisoner)
                    .put("collection_owner_character_id", PLAYER).put("jailer_character_id", PLAYER).put("custody_relation_verified", true)
                    .putNull("house_id").putNull("dynasty_id").put("same_house", false).put("same_dynasty", false)
                    .put("is_child_of_played_character", false).putNull("primary_title_tier_raw");
            var frame = new FrameBinding(NATIVE, DATE, PLAYER, prisoner);
            row.set("unconditional_release_preview", index == ordinal && release ? ReleasePreviewCodec12003.toNode(
                    new ReleasePreview12003.Available(frame, BigInteger.valueOf(77), new Definition(123, 1), true,
                            new Costs(Arrays.stream(Resource.values()).map(resource -> new CostEntry(resource, 0)).toList()))) : unavailable("not_evaluated"));
            row.set("ransom_quote_preview", index == ordinal && ransom ? PrisonerVanillaResearch.quoteJson(
                    new PrisonerVanillaResearch.AvailableQuote(frame, BigInteger.valueOf(77), 73000 + index,
                            PrisonerVanillaResearch.Option.GOLD, amount, 0, 0)) : unavailable(index == ordinal ? "final_can_send_false" : "not_evaluated"));
        }
        return envelope;
    }
    private static RawJson bundle() {
        ObjectNode bundle = StrictJson.object().put("schema", "xar.ck3.turn-bundle/v1").put("status", "partial");
        bundle.putObject("binding").put("snapshot_id", "public:37").put("revision", 37).put("native_revision", 1014).put("date_raw", DATE);
        bundle.putObject("ruler_state").put("status", "available").putObject("value").put("character_id", PLAYER).put("alive", true);
        var succession = bundle.putObject("succession_state").put("status", "available").putObject("value");
        succession.putObject("primary_title_heir_character_id").put("status", "available").put("value", 30470);
        var partition = succession.putObject("partition").put("status", "available").putObject("value").put("risk_state", "single_successor");
        partition.putArray("title_heirs").addObject().put("first_heir_character_id", 30470).put("primary", true)
                .putObject("title").put("title_id", 524).put("tier_raw", 3);
        return new RawJson(StrictJson.canonical(bundle));
    }
    private static ReadContract<RawJson> privateQuery(String id, OperationKey operation, String permission,
            ExactRef source, ReadContract.WireProfile profile, OpportunityJson.Obj fields) {
        return new ReadContract<>(id, operation, Optional.empty(), permission, ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                profile, source, request -> { StrictJson.require(request.arguments().equals(EMPTY), "fixture query cannot override its fields");
                    return new NativeRequest(operation.value(), Optional.empty(), new RawJson(OpportunityJson.encode(fields))); },
                receipt -> receipt.original().originalResultToken().orElseThrow());
    }
    private static final class Fixture implements PlanningReadPort {
        PlanningRequest request = request(false);
        boolean release, changeFinalQuote, drift, badCount, booleanCount, wrongReadback, wrongFactory, missingWriter, malformedEmpty;
        boolean ransom = true, observer = true;
        String refreshedQuoteFailure;
        int failOrdinal = -1, commandBindings, records;
        Optional<PrisonerVanillaResearch.Catalog> catalog = Optional.of(CATALOG);
        LedgerView ledger = new KnownLedger(REF, Optional.empty(), Optional.empty());
        final List<String> calls = new ArrayList<>();
        final Map<Integer, Integer> counts = new HashMap<>();
        final Queries queries;
        Fixture() {
            List<ReadContract<RawJson>> contracts = new ArrayList<>();
            for (int ordinal = 0; ordinal < 64; ordinal++) contracts.add(privateQuery("unit-collection-" + ordinal,
                    new OperationKey(collectionStep(ordinal)), "unit-private-read", REF, ReadContract.WireProfile.EXECUTE_STEP, EMPTY));
            queries = new Queries(contracts, Map.of());
            queries.bindTurnBundle(input->{
                // Synthetic DATA original for this pure policy fixture; never a native bundle contract or Root qualification.
                calls.add(ROOT.value());
                var original=new PlanningReadRequest(input.before(),input.source(),input.sessionId(),ROOT,EMPTY,input.deadline());
                var token=new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
                var ack=new NativeActionPort.AckReceived("unit-root-original",true,Optional.of(token),token,new byte[]{1});
                var guard=new PlanningReadGuard(new GuardEvidence(input.before(),input.source(),input.sessionId(),BigInteger.ONE,
                        ROOT,REF,REF,"unit-only-root-data",NOW,NOW.plusSeconds(60)),true,true,true,SHA);
                var receipt=new PlanningReadReceipt(original,"unit-root-original","unit-root-original",guard,guard,ack);
                return new ObservedTurnBundle(input.before(),input.source(),input.sessionId(),bundle(),receipt,REF);
            });
        }
        Bindings bindings() {
            return new Bindings(this, queries, catalog, ignored -> ledger, (input, operation, arguments, claims, original) -> {
                commandBindings++;
                if (!observer) return Optional.empty();
                var expected = new ProposalLifecycle.ExpectedPostcondition(1, input.before(), input.source(), "unit-independent-postcondition/v1",
                        List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("prisoner.released"), true)));
                return Optional.of(new ActionCommand("unit-proposal", input.before(), input.source(), input.sessionId(), operation,
                        wrongFactory ? EMPTY : arguments, expected, claims, input.deadline()));
            }, (input, value) -> {
                records++;
                if (missingWriter) return new RecordUnavailable("unit writer is absent");
                return new Recorded(input.before(), REF, wrongReadback ? new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)) : value.produced());
            });
        }
        PrisonerOrdinaryPolicy12004 policy(PlanningStage stage) {
            if (stage != PlanningStage.PRISONER_RANSOM && release && request.observations().history().isEmpty())
                request = withHistory(request, List.of(history(wire(0, release, ransom, 500, false)), history(wire(1, release, ransom, 300, false))));
            return new PrisonerOrdinaryPolicy12004(stage, REF, bindings());
        }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest input) {
            contract.prepare(input, "unit-read"); calls.add(contract.operation().value()); RawJson value;
            if (contract.operation().equals(ROOT)) value = bundle();
            else {
                int ordinal = -1;
                for (int index = 0; index < 64; index++) if (collectionStep(index).equals(contract.operation().value())) ordinal = index;
                if (ordinal == failOrdinal) return new PlanningReadResult.Unavailable<>("unit native read unavailable", Optional.empty());
                int count = counts.merge(ordinal, 1, Integer::sum);
                ObjectNode wire = wire(ordinal, release, ransom, ordinal == 0 ? 500 + (changeFinalQuote && count > 1 ? 1 : 0) : 300, drift);
                if (refreshedQuoteFailure != null) ((ObjectNode) wire.path("player_prisoner_collection").path("prisoners").get(ordinal)).set("ransom_quote_preview", unavailable(refreshedQuoteFailure));
                if (malformedEmpty) {
                    ObjectNode empty = (ObjectNode) wire.get("player_prisoner_collection");
                    empty.put("returned_count", 0).put("total_count", 0).putArray("prisoners"); wire.remove("advertised");
                }
                if (badCount) ((ObjectNode) wire.get("player_prisoner_collection")).put("returned_count", 2.0);
                if (booleanCount) ((ObjectNode) wire.get("player_prisoner_collection")).put("returned_count", true);
                value = new RawJson(StrictJson.canonical(wire));
            }
            var ack = new NativeActionPort.AckReceived("unit-read", true, Optional.of(value),
                    new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)), new byte[]{1});
            var guard = new PlanningReadGuard(new GuardEvidence(input.before(), input.source(), input.sessionId(), BigInteger.ONE,
                    input.operation(), REF, REF, "unit-only", NOW, NOW.plusSeconds(60)), true, true, true, SHA);
            var receipt = new PlanningReadReceipt(input, contract.contractId(), "unit-read", guard, guard, ack);
            return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, REF);
        }
    }
}
