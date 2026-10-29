package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.nio.file.Path;
import java.util.EnumMap;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashSet;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real DomainBodies reducer/head -> actual read-only supplier/strict decoders. In-memory I/O doubles, no actual-state claim. */
final class GovernanceStateSupplierTest {
    private static final String COUNCIL_SCHEMA = "xar.ck3.private-council-formal/v1";
    private static final String CROWN_SCHEMA = "unit-original-crown-state/v1";
    private static final class Store implements ContinuityStorePort, ContinuityStorePort.Session {
        final EnumMap<DomainBodies.Slot, DomainBodies.Available> bodies = new EnumMap<>(DomainBodies.Slot.class);
        ContinuityState state; int locks; int mutations; int custodyChecks;
        boolean replayPins; ExactRef forbiddenPin; final List<ExactRef> capturedPins=new ArrayList<>(); int verifiedPins;
        Store() {
            var row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1").put("machine_id", SOURCE.machineId())
                    .put("sequence", 0).put("window_id", 1).put("status", "running").put("start_date_raw", 100)
                    .put("target_days", 1).put("target_date_raw", 124).put("last_settled_cycles", 0).put("last_settled_date_raw", 100);
            state = ContinuityState.fromJson(row, SOURCE.machineId());
        }
        void install(DomainBodies.Slot slot, String schema, byte[] body, List<ExactRef> sources) {
            var payload = new ExactRef("unit-domain-" + slot, body.length, ActionCodec.sha256(body));
            var reference = new DomainBodies.BodyRef(slot, schema, payload,
                    new FileIdentity("1", "2", "133700000000000001", NOW.toString(), body.length), sources);
            state = DomainBodies.reduceImport(state, reference);
            bodies.put(slot, new DomainBodies.Available(reference, body, REF, List.of()));
        }
        @Override public <T> T locked(SessionWork<T> work) throws IOException { locks++; return work.run(this); }
        @Override public void requireWriter(Path writerLock) { custodyChecks++; }
        @Override public Pin capturePin(ExactRef reference, int maximumBytes) throws IOException {
            if(!replayPins)throw new AssertionError("read-only unit does not capture files");
            if(reference.equals(forbiddenPin))throw new IOException("absent historical Java source: "+reference.path());
            capturedPins.add(reference);return new Pin(reference,new FileIdentity("1","2","133700000000000001",NOW.toString(),reference.bytes()));
        }
        @Override public void verifyPin(Pin pin) {
            if(!replayPins)throw new AssertionError("read-only unit does not verify files");
            assertTrue(capturedPins.contains(pin.reference()));verifiedPins++;
        }
        @Override public Head head() { return new Head(state, List.of(), List.of(), List.of(), false); }
        @Override public ExactRef persistedHead() { return REF; }
        @Override public DomainBodies.Read readDomain(DomainBodies.Slot slot) {
            var value = bodies.get(slot); return value == null ? new DomainBodies.Unavailable(DomainBodies.Reason.UNIMPORTED, Optional.of(REF), "unit slot unimported") : value;
        }
        @Override public Prepared preview(Request request) { mutations++; throw new AssertionError("read-only supplier cannot preview a mutation"); }
        @Override public Receipt commit(Prepared prepared) { mutations++; throw new AssertionError("read-only supplier cannot commit"); }
    }
    private static GovernanceStateSupplier supplier(Store store) {
        return new GovernanceStateSupplier(store, Optional.of(GovernanceStateSupplier.cadence(List.of(REF))), Optional.empty(),
                Optional.of(GovernanceStateSupplier.legacyCouncil(COUNCIL_SCHEMA, List.of(REF))),
                Optional.of(GovernanceStateSupplier.legacyCrown(CROWN_SCHEMA, List.of(REF))),
                request -> new Unavailable<>("unit does not qualify a current bridge PID"));
    }
    private static Obj clearCouncil() { return new Obj(java.util.Map.of()).with("schema", new Text(COUNCIL_SCHEMA)).with("pending", Nil.INSTANCE).with("applied", Nil.INSTANCE); }
    private static Obj clearCrown() { return new Obj(java.util.Map.of()).with("pending", Nil.INSTANCE).with("resolved", Nil.INSTANCE).with("retry", Nil.INSTANCE); }
    @Test void absentSlotsStayExplicitlyAbsentAndNeverCreateInitialClearOrOpeningGate() {
        var store = new Store(); var read = supplier(store).read(request()); assertTrue(read instanceof Known<Durable>);
        Durable state = ((Known<Durable>) read).value();
        assertTrue(state.cadence().isEmpty()); assertTrue(state.council().isEmpty()); assertTrue(state.crown().isEmpty()); assertTrue(state.opening().isEmpty());
        assertEquals(1, store.locks); assertEquals(0, store.mutations);
    }
    @Test void importedOriginalBodiesAreDecodedUnderOneActualHeadWithoutPublishing() {
        var store = new Store();
        store.install(DomainBodies.Slot.OPTIONAL_CADENCE, CadenceModels.SCHEMA, CadenceJson.writeState(CadenceModels.State.empty("unit-episode")), List.of(REF));
        store.install(DomainBodies.Slot.COUNCIL, COUNCIL_SCHEMA, encode(clearCouncil()), List.of(REF));
        Obj pending = new Obj(java.util.Map.of()).with("episode_run_id", new Text("unit-episode")).with("ack", new Obj(java.util.Map.of()).with("status", new Text("ack_only")));
        Obj original = clearCrown().with("pending", pending);
        store.install(DomainBodies.Slot.CROWN, CROWN_SCHEMA, encode(original), List.of(REF));
        var read = supplier(store).read(request()); Durable state = ((Known<Durable>) read).value();
        assertTrue(state.cadence().isPresent()); assertEquals(DomainStatus.KNOWN_CLEAR, state.council().orElseThrow().status());
        assertEquals(DomainStatus.PENDING, state.crown().orElseThrow().status());
        assertEquals(original, state.crown().orElseThrow().originalBody()); assertTrue(state.crown().orElseThrow().latest().isEmpty());
        assertEquals(pending, state.crown().orElseThrow().legacyPending().orElseThrow()); assertEquals(1, store.locks); assertEquals(0, store.mutations);
    }
    @Test void historicalProducerTraceIsRetainedButWrongHeadIsRejectedBeforeDecoding() {
        var historical = new ExactRef("unit-unavailable-historical-code", 1, "b".repeat(64));
        var store = new Store(); store.install(DomainBodies.Slot.COUNCIL, COUNCIL_SCHEMA, encode(clearCouncil()), List.of(historical));
        var read = assertInstanceOf(Known.class, supplier(store).read(request()));
        assertEquals(DomainStatus.KNOWN_CLEAR, ((Durable) read.value()).council().orElseThrow().status());
        assertFalse(read.originals().contains(historical));
        assertEquals(List.of(historical),store.bodies.get(DomainBodies.Slot.COUNCIL).reference().producerSources()); assertEquals(0, store.mutations);
        var available = store.bodies.get(DomainBodies.Slot.COUNCIL);
        store.bodies.put(DomainBodies.Slot.COUNCIL, new DomainBodies.Available(available.reference(), available.canonicalBody(),
                new ExactRef("unit-other-head", 1, "c".repeat(64)), List.of()));
        assertThrows(IllegalArgumentException.class, () -> supplier(store).read(request())); assertEquals(0, store.mutations);
    }
    @Test void historicalPendingSurvivesTheActualSupplierAndSerdeWithoutBecomingAReceiptOrClearingUnknown() {
        var historical = new ExactRef("unit-unavailable-historical-code", 1, "b".repeat(64));
        for (var episode : List.of("unit-episode", "another-episode")) {
            var store = new Store();
            Obj pending = new Obj(java.util.Map.of()).with("episode_run_id", new Text(episode))
                    .with("ack", new Obj(java.util.Map.of()).with("status", new Text("ack_only")));
            Obj original = clearCrown().with("pending", pending);
            byte[] body = encode(original);
            store.install(DomainBodies.Slot.CROWN, CROWN_SCHEMA, body, List.of(historical));
            var before = store.state;
            var available = store.bodies.get(DomainBodies.Slot.CROWN);
            var reference = available.reference();
            assertEquals(reference, DomainBodies.BodyRef.fromJson(StrictJson.parse(StrictJson.canonical(reference.toJson()))));
            var read = assertInstanceOf(Known.class, supplier(store).read(request()));
            var domain = ((Durable) read.value()).crown().orElseThrow();
            assertEquals(episode.equals("unit-episode") ? DomainStatus.PENDING : DomainStatus.UNKNOWN, domain.status());
            assertEquals(original, domain.originalBody()); assertEquals(pending, domain.legacyPending().orElseThrow());
            assertTrue(domain.latest().isEmpty()); assertArrayEquals(body, encode(domain.originalBody()));
            assertEquals(original, parse(encode(domain.originalBody())));
            assertTrue(read.originals().contains(reference.payload())); assertFalse(read.originals().contains(historical));
            assertEquals(List.of(historical),reference.producerSources());
            assertSame(before, store.state); assertEquals(REF, store.persistedHead());
            assertEquals(reference, DomainBodies.reference(store.state, DomainBodies.Slot.CROWN).orElseThrow());
            assertArrayEquals(body, store.bodies.get(DomainBodies.Slot.CROWN).canonicalBody());
            assertEquals(1, store.locks); assertEquals(0, store.mutations);
        }
    }
    @Test void historicalTraceDoesNotPermitWrongSlotSchemaOrAReplacedNativeIdentityBeforeDecoder() {
        var historical = new ExactRef("unit-unavailable-historical-code", 1, "b".repeat(64));
        for (int mismatch = 0; mismatch < 3; mismatch++) {
            var store = new Store(); byte[] body = encode(clearCrown());
            store.install(DomainBodies.Slot.CROWN, CROWN_SCHEMA, body, List.of(historical));
            var saved = store.bodies.get(DomainBodies.Slot.CROWN).reference();
            var replaced = new DomainBodies.BodyRef(mismatch == 0 ? DomainBodies.Slot.COUNCIL : saved.slot(),
                    mismatch == 1 ? "wrong-schema" : saved.contractSchema(), saved.payload(),
                    mismatch == 2 ? new FileIdentity("1", "3", "133700000000000001", NOW.toString(), body.length) : saved.identity(),
                    saved.producerSources());
            store.bodies.put(DomainBodies.Slot.CROWN, new DomainBodies.Available(replaced, body, REF, List.of()));
            int[] decoded = {0};
            var contract = new GovernanceStateSupplier.BodyContract<>(DomainBodies.Slot.CROWN, CROWN_SCHEMA, List.of(REF),
                    (org.xar.ck3.control.application.planning.PlanningRequest request, byte[] raw) -> {
                        decoded[0]++; return GovernanceStateSupplier.decodeLegacyCrown(request, raw);
                    });
            var reader = new GovernanceStateSupplier(store, Optional.empty(), Optional.empty(), Optional.empty(), Optional.of(contract),
                    request -> new Unavailable<>("unit retry proof absent"));
            assertThrows(IllegalArgumentException.class, () -> reader.read(request()));
            assertEquals(0, decoded[0]); assertEquals(0, store.mutations);
            assertEquals(saved, DomainBodies.reference(store.state, DomainBodies.Slot.CROWN).orElseThrow());
        }
    }
    @Test void actualStateEvidenceReachesRecordedFeastReplayWithoutReopeningHistoricalJava() throws Exception {
        var historical=new ExactRef("missing-retained-governance.java",1,"b".repeat(64));
        var store=new Store();store.replayPins=true;store.forbiddenPin=historical;
        store.install(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,
                CadenceJson.writeState(CadenceModels.State.empty("unit-episode")),List.of(historical));
        Obj pending=new Obj(Map.of()).with("episode_run_id",new Text("another-episode"))
                .with("ack",new Obj(Map.of()).with("status",new Text("ack_only")));
        store.install(DomainBodies.Slot.CROWN,CROWN_SCHEMA,encode(clearCrown().with("pending",pending)),List.of(historical));
        var reader=supplier(store);var stateBefore=store.state;
        var originalRequest=request();var observation=originalRequest.observations();
        var steps=new HashSet<>(observation.actionSteps());steps.addAll(OrdinaryFeastPolicy.OWNED);
        var request=new PlanningRequest(originalRequest.before(),originalRequest.source(),originalRequest.sessionId(),originalRequest.deadline(),
                new PlanningObservation(observation.snapshot(),observation.history(),steps,observation.bridgeCapabilities(),
                        observation.battleSpeedReadiness(),observation.actionFacts(),observation.campaignGoal(),observation.crossRunPlan(),observation.initialLifestyleFocusRequired()));
        var beforeRead=(Known<Durable>)reader.read(request);
        assertEquals(DomainStatus.UNKNOWN,beforeRead.value().crown().orElseThrow().status());
        FeastObservationSupplier actual=new FeastObservationSupplier() {
            public Read<State> state(PlanningRequest current) {
                var retained=(Known<Durable>)reader.read(current);
                return new Known<>(new State(current.before(),current.sessionId(),retained.value().cadence().orElseThrow(),
                        Optional.empty(),Optional.empty(),List.of(),new Obj(Map.of())),retained.originals());
            }
            public Read<Planner> planner(PlanningRequest current) {return new Known<>(new Planner(ActivityPlannerDiagnostic.Kind.OTHER,new Obj(Map.of())),List.of(REF));}
            public Read<Hosted> hosted(PlanningRequest current) {throw new AssertionError("diagnostic needs no HOSTED");}
            public Read<Obj> root(PlanningRequest current) {throw new AssertionError("diagnostic needs no ROOT");}
            public Read<org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.Spending> spending(PlanningRequest current) {throw new AssertionError("diagnostic needs no spending");}
            public Read<org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.Feast> feast(PlanningRequest current,
                    org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.Spending spending) {throw new AssertionError("diagnostic needs no Start");}
        };
        var cadence=store.bodies.get(DomainBodies.Slot.OPTIONAL_CADENCE);
        var replay=new GovernanceCadenceReplay(()->store,same->assertSame(store,same),(same,ref)->{
            assertSame(store,same);assertEquals(cadence.reference().payload(),ref);return cadence.canonicalBody();});
        var policy=replay.record(new OrdinaryFeastPolicy(REF,replay.observe(actual),(operation,frame,args)->Optional.empty()));
        var produced=assertInstanceOf(OrdinaryPolicy.Annotate.class,policy.evaluate(request,advance(request)));
        var plan=GovernanceCadencePublication.fromDetail(produced.retained().detail()).orElseThrow();
        var evidence=new ArrayList<ExactRef>();evidence.add(REF);evidence.addAll(beforeRead.originals());
        List<ExactRef> exact=evidence.stream().distinct().toList();
        // This actual production consumer physically pins every business original; old code refs fail here.
        var material=replay.replay(store.head(),cadence.reference(),plan,exact);
        assertEquals(List.of(CadenceModels.Domain.FEAST),material.actualReplayedPlan().completeNoActionDomains());
        assertEquals(1,GovernanceCadencePublication.reduce(material.actualReplayedPlan()).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
        assertFalse(store.capturedPins.contains(historical));assertTrue(store.capturedPins.contains(cadence.reference().payload()));
        assertTrue(store.capturedPins.contains(store.bodies.get(DomainBodies.Slot.CROWN).reference().payload()));
        assertEquals(exact,store.capturedPins);assertEquals(exact.size(),store.verifiedPins);
        assertSame(stateBefore,store.state);assertEquals(0,store.mutations);
        assertEquals(List.of(historical),cadence.reference().producerSources());
        assertEquals(DomainStatus.UNKNOWN,((Known<Durable>)reader.read(request)).value().crown().orElseThrow().status());
        var altered=new ArrayList<>(exact);altered.remove(cadence.reference().payload());
        assertThrows(IllegalArgumentException.class,()->replay.replay(store.head(),cadence.reference(),plan,altered));
    }
    @Test void malformedOrMissingFieldsCannotBeDefaultedIntoClearState() {
        var request = request();
        assertThrows(IllegalArgumentException.class, () -> GovernanceStateSupplier.decodeLegacyCrown(request, encode(clearCrown().with("pending", new Bool(false)))));
        assertThrows(IllegalArgumentException.class, () -> GovernanceStateSupplier.decodeLegacyCrown(request, encode(new Obj(java.util.Map.of()).with("pending", Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class, () -> GovernanceStateSupplier.decodeLegacyCouncil(request, encode(clearCouncil().with("schema", new Text("wrong")))));
    }
    @Test void originalAppliedOrColdCurrentLawJsonNeverBecomesJavaMaterialReceipt() {
        Obj resolved = new Obj(java.util.Map.of()).with("status", new Text("cold_current_law_observed")).with("requested_law_observed", new Bool(true)).with("material_result", new Bool(false));
        var state = GovernanceStateSupplier.decodeLegacyCrown(request(), encode(clearCrown().with("resolved", resolved)));
        assertEquals(DomainStatus.KNOWN_CLEAR, state.status()); assertTrue(state.latest().isEmpty()); assertEquals(resolved, state.originalBody().get("resolved"));
        Obj another = new Obj(java.util.Map.of()).with("episode_run_id", new Text("another-episode"));
        assertEquals(DomainStatus.UNKNOWN, GovernanceStateSupplier.decodeLegacyCrown(request(), encode(clearCrown().with("pending", another))).status());
    }
    @Test void anotherEpisodesCadenceNeedsItsProducerTransitionAndRetryDoesNotGuessBridgePid() {
        var store = new Store(); store.install(DomainBodies.Slot.OPTIONAL_CADENCE, CadenceModels.SCHEMA, CadenceJson.writeState(CadenceModels.State.empty("another-episode")), List.of(REF));
        assertThrows(IllegalArgumentException.class, () -> supplier(store).read(request()));
        assertInstanceOf(Unavailable.class, supplier(new Store()).crownRetry(request(), "crown_authority_1"));
    }
    @Test void borrowedStateUsesTheRootSessionAndNeverReacquiresTheWriterLock() {
        var store = new Store(); int[] authorityChecks = {0};
        var scope = new GovernanceBorrowedSession(store, Path.of("unit-writer.lock"), session -> {
            assertSame(store, session); authorityChecks[0]++;
        });
        var reader = new GovernanceStateSupplier(scope, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(),
                request -> new Unavailable<>("unit retry proof absent"));
        assertInstanceOf(Known.class, reader.read(request()));
        assertEquals(0, store.locks); assertEquals(1, authorityChecks[0]); assertEquals(1, store.custodyChecks); assertEquals(0, store.mutations);
    }
    @Test void rejectedExactWriterCustodyDoesNotFallBackToAnotherLockOrClearState() {
        var store = new Store();
        var scope = new GovernanceBorrowedSession(store, Path.of("unit-writer.lock"), session -> { throw new IOException("unit escaped session"); });
        var reader = new GovernanceStateSupplier(scope, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(),
                request -> new Unavailable<>("unit retry proof absent"));
        assertInstanceOf(Unavailable.class, reader.read(request())); assertEquals(0, store.locks); assertEquals(0, store.custodyChecks);
    }
    @Test void legacyRetryPidAndEpisodeCannotReplaceThePrivateCommittedPublicationProof() {
        var store = new Store();
        var scope = new GovernanceBorrowedSession(store, Path.of("unit-writer.lock"), session -> assertSame(store, session));
        var material = new CrownRetryPublication.MaterialPort() {
            @Override public CrownRetryPublication.Material capture(Head head, CrownRetryPublication.Input input, java.time.Instant callerDeadline) {
                throw new AssertionError("missing committed proof cannot capture material");
            }
            @Override public void requireCurrent(Head head, CrownRetryPublication.Input input,
                    org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity current,
                    org.xar.ck3.control.g2.common.G2Source source, java.time.Instant callerDeadline) {
                throw new AssertionError("missing committed proof cannot qualify a legacy retry");
            }
        };
        var publication = new CrownRetryPublication(Path.of("unit-writer.lock"), CROWN_SCHEMA, List.of(REF), List.of(REF), material,
                (evidenceId, body) -> { throw new AssertionError("read adapter cannot publish without a proof"); });
        var frames = GovernanceStateSupplier.verifiedCrownRetryFrames(scope, publication, Optional::empty,
                new CrownRetryDue(store, session -> assertSame(store, session), publication));
        assertInstanceOf(Unavailable.class, frames.read(request()));
        assertInstanceOf(Unavailable.class, frames.due(request())); assertEquals(0, store.locks); assertEquals(0, store.custodyChecks);
    }
    @Test void orderedCadencePlanRetainsAllCompletedDomainsAndRoundTripsBeforeTheRealReducer() {
        var request = request(); var before = CadenceModels.State.empty(request.before().frame().episodeRunId());
        Obj detail = GovernanceCadencePublication.append(new Obj(java.util.Map.of()), CadenceModels.Domain.LIFESTYLE, request, before);
        detail = GovernanceCadencePublication.append(detail, CadenceModels.Domain.COUNCIL, request, before);
        detail = GovernanceCadencePublication.append(detail, CadenceModels.Domain.FEAST, request, before);
        var plan = GovernanceCadencePublication.fromDetail(detail).orElseThrow();
        assertEquals(List.of(CadenceModels.Domain.LIFESTYLE, CadenceModels.Domain.COUNCIL, CadenceModels.Domain.FEAST), plan.completeNoActionDomains());
        assertEquals(plan, GovernanceCadencePublication.decode(GovernanceCadencePublication.encode(plan)));
        var after = GovernanceCadencePublication.reduce(plan);
        for (var domain : plan.completeNoActionDomains()) assertEquals(1, after.row(domain).consecutiveNoAction());
        assertEquals(0, after.row(CadenceModels.Domain.CROWN).consecutiveNoAction()); assertEquals(0, before.row(CadenceModels.Domain.FEAST).consecutiveNoAction());
    }
    @Test void duplicateSameFrameCadenceDoesNotOverwriteOtherDomainsOrEarnAnotherRead() {
        var request = request(); var before = CadenceModels.State.empty(request.before().frame().episodeRunId());
        Obj first = GovernanceCadencePublication.append(new Obj(java.util.Map.of()), CadenceModels.Domain.COUNCIL, request, before);
        Obj same = GovernanceCadencePublication.append(first, CadenceModels.Domain.COUNCIL, request, before);
        assertEquals(first, same);
        assertThrows(IllegalArgumentException.class, () -> GovernanceCadencePublication.append(first, CadenceModels.Domain.FEAST,
                request(10, false, List.of()), before));
        assertThrows(IllegalArgumentException.class, () -> GovernanceCadencePublication.append(
                new Obj(java.util.Map.of()).with("governance_required_cadence_intent", new Obj(java.util.Map.of())), CadenceModels.Domain.FEAST, request, before));
    }
    @Test void cadenceWireRejectsBooleanDomainAndMissingOrWrongSchemaInsteadOfDefaultingToEmpty() {
        var request = request(); var before = CadenceModels.State.empty(request.before().frame().episodeRunId());
        Obj detail = GovernanceCadencePublication.append(new Obj(java.util.Map.of()), CadenceModels.Domain.COUNCIL, request, before);
        Obj plan = object(detail.get(GovernanceCadencePublication.FIELD), "cadence plan");
        assertThrows(IllegalArgumentException.class, () -> GovernanceCadencePublication.decode(encode(plan.with("complete_no_action_domains", new Arr(List.of(new Bool(true)))))));
        assertThrows(IllegalArgumentException.class, () -> GovernanceCadencePublication.decode(encode(plan.with("schema", new Text("wrong")))));
        assertThrows(IllegalArgumentException.class, () -> GovernanceCadencePublication.decode(encode(new Obj(java.util.Map.of()))));
    }
}
