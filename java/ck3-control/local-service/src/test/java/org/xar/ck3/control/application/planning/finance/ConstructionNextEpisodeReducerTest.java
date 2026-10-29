package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Pure production conversion vectors. This fixture cannot construct the private EpisodeDomainInitializationProof. */
final class ConstructionNextEpisodeReducerTest {
    @Test void realFullOriginalBodyAndUnknownKeepTheirOwnActorEpisodeAndProjectAncestry() {
        var input = input();
        var result = ConstructionNextEpisodeReducer.reduce(input);
        for (var field : input.original().original().members().entrySet()) assertEquals(field.getValue(), result.body().get(field.getKey()), field.getKey());
        Obj pending = object(result.body().get("pending"), "original unknown");
        assertEquals(new Text("episode"), pending.get("episode_run_id"));
        assertEquals(new IntegerValue(BigInteger.ONE), pending.get("actor_character_id"));
        assertEquals(new Text("action_state_unknown"), pending.get("status"));
        Obj audit = object(result.body().get(ConstructionNextEpisodeReducer.FIELD), "actual new-baseline audit");
        assertEquals(new Text("next-episode"), audit.get("after_episode_run_id"));
        assertEquals(new Text("unavailable"), object(audit.get("current_projects"), "current project qualification").get("status"));
        assertEquals(new Bool(false), audit.get("actions_replayed"));
        assertEquals(new Bool(false), audit.get("old_projects_rebound"));
        assertEquals(ConstructionNextEpisodeReducer.Qualification.CURRENT_PROJECTS_UNAVAILABLE, result.qualification());
        assertEquals(result.body(), ConstructionLedgerCodec.decodeLedger(encode(result.body())).original());
        assertEquals(result, ConstructionNextEpisodeReducer.reduce(input));
    }
    @Test void differentOriginalBodyOrDriverBytesCannotBorrowMatchingMetadata() {
        var input = input();
        var changed = ConstructionLedgerCodec.decodeLedger(encode(input.original().original().with("pending", Nil.INSTANCE)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(
                changed, input.predecessor(), input.firstSaved(), input.actualSavedSnapshot(), input.current(), input.actualCurrentSnapshot(), input.basis(), input.currentProjects())));
        var foreignDriver = driver(2, "foreign-episode", 55);
        assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(
                input.original(), input.predecessor(), foreignDriver, input.actualSavedSnapshot(), input.current(), input.actualCurrentSnapshot(), input.basis(), input.currentProjects())));
        assertEquals(new Text("action_state_unknown"), object(input.original().original().get("pending"), "old pending").get("status"));
    }
    @Test void wrongNewActorStaleEpisodeAndWrongTypedSavedFrameNeverBecomeReady() {
        var input = input();
        for (Obj wrong : List.of(input.actualSavedSnapshot().with("episode_run_id", new Text("episode")),
                input.actualSavedSnapshot().with("played_character", obj("character_id", new IntegerValue(BigInteger.ONE))),
                input.actualSavedSnapshot().with("revision", new Bool(true)), input.actualSavedSnapshot().with("paused", new Bool(false))))
            assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(
                    input.original(), input.predecessor(), input.firstSaved(), wrong, input.current(), input.actualCurrentSnapshot(), input.basis(), input.currentProjects())));
    }
    @Test void actualCurrentProjectTupleIsObservedSeparatelyWithoutRebindingTheOldUnknown() {
        var input = input();
        Obj tuple = obj("barony_title_id", new IntegerValue(BigInteger.valueOf(9)), "province_id", new IntegerValue(BigInteger.valueOf(10)),
                "building_type_id", new IntegerValue(BigInteger.valueOf(11)), "slot_index", new IntegerValue(BigInteger.ZERO), "active", new Bool(true));
        Obj query = obj("status", new Text("material_source"), "source_frame", obj("episode_run_id", new Text("next-episode"),
                "actor_character_id", new IntegerValue(BigInteger.TWO), "date_raw", new IntegerValue(BigInteger.valueOf(200))),
                "world", obj("active_constructions", new Arr(List.of(tuple))));
        var observed = new ConstructionNextEpisodeReducer.ObservedProjects(reference("actual-material-read", new byte[]{8}), query);
        var result = ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(input.original(), input.predecessor(),
                input.firstSaved(), input.actualSavedSnapshot(), input.current(), input.actualCurrentSnapshot(), input.basis(), observed));
        assertEquals(ConstructionNextEpisodeReducer.Qualification.CURRENT_PROJECTS_OBSERVED, result.qualification());
        assertEquals(input.original().original().get("pending"), result.body().get("pending"));
        Obj audit = object(result.body().get(ConstructionNextEpisodeReducer.FIELD), "NEXT audit");
        assertEquals(query, object(audit.get("current_projects"), "current observation").get("material_query"));
        assertEquals(new IntegerValue(BigInteger.ZERO), audit.get("new_effect_credit"));
        Obj wrongSource = object(query.get("source_frame"), "current source").with("actor_character_id", new IntegerValue(BigInteger.ONE));
        var wrong = new ConstructionNextEpisodeReducer.ObservedProjects(observed.originalReceipt(), query.with("source_frame", wrongSource));
        assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(input.original(),
                input.predecessor(), input.firstSaved(), input.actualSavedSnapshot(), input.current(), input.actualCurrentSnapshot(), input.basis(), wrong)));
    }
    @Test void exactTypedBasisRoundTripsAndRejectsMissingExtraAndWrongIntegerKinds() {
        var basis = input().basis();
        Obj encoded = object(parse(encode(basis.toJson())), "original persisted NEXT basis");
        assertEquals(basis, ConstructionNextEpisodeReducer.Basis.decode(encoded));
        var missing = new java.util.LinkedHashMap<String,Value>(encoded.members()); missing.remove("original_body");
        assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.Basis.decode(new Obj(missing)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.Basis.decode(encoded.with("old_ready", new Bool(true))));
        for (Value wrong : List.of(new Bool(true), new DecimalValue("8.0"), new Text("8"), Nil.INSTANCE))
            assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.Basis.decode(encoded.with("baseline_sequence", wrong)));
        assertEquals("18446744073709551615", ConstructionNextEpisodeReducer.Basis.decode(encoded).originalBody().identity().fileIdDecimal());
    }
    @Test void producerSerdeAndActualPolicyDeferOnlyForeignEpisodeUnknownWhileSameEpisodeReconcilesOriginal() {
        for (boolean restored : List.of(false, true)) {
        var input = input(restored); var reduced = ConstructionNextEpisodeReducer.reduce(input);
        Obj persisted = ConstructionLedgerCodec.decodeLedger(encode(reduced.body())).original();
        var oldRequest = request(input, false); var current = request(input, true);
        var expectation = new ProposalLifecycle.ExpectedPostcondition(1, oldRequest.before(), oldRequest.source(), "construction-test/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        var command = new ActionCommand("legacy-native-request", oldRequest.before(), oldRequest.source(), oldRequest.sessionId(),
                OrdinaryConstructionPolicy.OPERATION, obj(), expectation, new JointBudgetSelector.Claims(java.util.Set.of(), java.util.Set.of(), java.util.Set.of(), java.util.Set.of()), oldRequest.deadline());
        var unknown = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(java.util.Optional.empty(), java.util.Optional.empty(), "software boundary original UNKNOWN", List.of(input.basis().source().sourceRef())));
        var foreign = assertInstanceOf(OrdinaryPolicy.Defer.class, evaluate(current, persisted, unknown));
        assertEquals(object(persisted.get("pending"), "old original"), foreign.evidence().get("construction_previous_episode_pending"));
        assertEquals(new Bool(false), foreign.evidence().get("actions_replayed"));
        assertEquals(new Bool(true), foreign.evidence().get("continue_ordinary_war"));
        assertEquals(new IntegerValue(BigInteger.ZERO), foreign.evidence().get("future_funding_credited_raw"));
        var same = assertInstanceOf(OrdinaryPolicy.ReconcileExisting.class, evaluate(oldRequest, persisted, unknown));
        assertEquals(command.actionId(), same.actionId());
        assertEquals(input.original().pending().orElseThrow().original(), object(persisted.get("pending"), "retained unchanged UNKNOWN"));
        assertFalse(unknown.settled());
        }
    }
    @Test void bothOriginDataShapesUseOnePureTransformAndPreserveOriginalAndCurrentMaterialsSeparately() {
        for (boolean restored : List.of(false, true)) {
            var input = input(restored); var basis = input.basis();
            var decoded = ConstructionNextEpisodeReducer.Basis.decode(object(parse(encode(basis.toJson())), "common basis persisted"));
            assertEquals(basis, decoded);
            var result = ConstructionNextEpisodeReducer.reduce(input);
            Obj audit = object(result.body().get(ConstructionNextEpisodeReducer.FIELD), "common conversion audit");
            assertEquals(new Text(restored ? "RESTORED_FIRST" : "NEXT"), audit.get("origin"));
            assertEquals(input.original().original().get("pending"), result.body().get("pending"));
            assertEquals(basis.toJson().get("original_body"), audit.get("original_body"));
            assertEquals(new IntegerValue(BigInteger.valueOf(restored ? 12 : 8)), audit.get("initialization_sequence"));
            assertEquals(basis.toJson().get("saved_semantic"), audit.get("saved_semantic"));
            assertEquals(basis.toJson().get("current_semantic"), audit.get("current_semantic"));
            Obj query = obj("status", new Text("material_source"), "source_frame", obj("episode_run_id", new Text("next-episode"),
                    "actor_character_id", new IntegerValue(BigInteger.TWO), "date_raw", new IntegerValue(BigInteger.valueOf(200))),
                    "world", obj("active_constructions", new Arr(List.of())));
            var projects = new ConstructionNextEpisodeReducer.ObservedProjects(reference("current-material-read", new byte[]{9}), query);
            var observed = ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(input.original(), input.predecessor(),
                    input.firstSaved(), input.actualSavedSnapshot(), input.current(), input.actualCurrentSnapshot(), decoded, projects));
            assertEquals(ConstructionNextEpisodeReducer.Qualification.CURRENT_PROJECTS_OBSERVED, observed.qualification());
            assertEquals(result.body().get("pending"), observed.body().get("pending"));
            if (restored) {
                assertNotEquals(basis.savedOwner().game(), basis.afterOwner().game());
                assertNotEquals(input.firstSaved().session().bridgePid(), input.current().session().bridgePid());
                assertTrue(basis.currentSemantic().frame().frame().revision().compareTo(basis.savedSemantic().frame().frame().revision()) < 0);
                assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(
                        input.original(), input.predecessor(), input.firstSaved(), input.actualSavedSnapshot(), input.firstSaved(), input.actualSavedSnapshot(), decoded, projects)));
                assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.Basis.decode(decoded.toJson().with("current_semantic", decoded.toJson().get("saved_semantic"))));
                assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.Basis.decode(decoded.toJson().with("initialization_sequence", new IntegerValue(BigInteger.valueOf(8)))));
            }
            for (Value wrong : List.of(new Bool(true), new DecimalValue("12.0"), new Text("12"), Nil.INSTANCE))
                assertThrows(IllegalArgumentException.class, () -> ConstructionNextEpisodeReducer.Basis.decode(decoded.toJson().with("initialization_sequence", wrong)));
        }
    }
    private static OrdinaryPolicy.Decision evaluate(PlanningRequest request, Obj actualBody, ActionReceipt unknown) {
        ExactRef source = request.source().sourceRef(); byte[] bytes = encode(actualBody);
        var document = new FinanceStatePort.Document(FinanceStatePort.Domain.CONSTRUCTION, reference("post-next-body", bytes), bytes);
        var state = new FinanceStatePort(original -> new FinanceStatePort.Head(original.before(), source, List.of(document), List.of(unknown), java.util.Optional.empty()),
                List.of(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION, source,
                        original -> ConstructionLedgerCodec.decodeLedger(original.bytes()).pending().isPresent() ? FinanceStatePort.Pending.PENDING : FinanceStatePort.Pending.CLEAR)));
        var definitions = new FinanceReadContracts(query -> new FinanceReadContracts.Registration(source,
                new FinanceReadContracts.Permission(java.util.Optional.empty(), "software-boundary-query", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY)));
        var reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest original) { throw new AssertionError("retained UNKNOWN cannot dispatch a new native read/action"); }
        };
        var collector = new OrdinaryConstructionCollector(new OrdinaryFinanceCollector(definitions, reads, state),
                original -> { throw new AssertionError("foreign UNKNOWN cannot borrow a current material source"); },
                original -> { throw new AssertionError("foreign UNKNOWN cannot mint available financing"); });
        var policy = new OrdinaryConstructionPolicy(source, collector,
                (original, arguments) -> { throw new AssertionError("retained UNKNOWN cannot prepare a new effect"); },
                (original, draft, ledger, receipt, reason) -> { throw new AssertionError("retained UNKNOWN cannot become a completed receipt"); });
        var draft = new OrdinaryPolicy.Draft("one-life-turn-v1", "current_life_loop", "actual ordinary advance", OrdinaryPolicy.Kind.ORDINARY,
                java.util.Optional.empty(), OrdinaryPolicy.Purpose.DATE_ADVANCE, java.util.Optional.empty(), obj("selected_step", new Text("life-advance")));
        return policy.evaluate(request, draft);
    }
    private static PlanningRequest request(ConstructionNextEpisodeReducer.Input input, boolean next) {
        var owner = next ? input.basis().afterOwner() : input.basis().beforeOwner();
        var frame = next ? input.basis().currentSemantic().frame() : new ProposalLifecycle.ObservationIdentity(owner.machineId(), owner.game(),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.TWO, BigInteger.valueOf(100)),
                        "native:2", BigInteger.TWO, "episode"), 1);
        Obj snapshot = next ? input.actualCurrentSnapshot() : obj("episode_run_id", new Text("episode"), "played_character", obj("character_id", new IntegerValue(BigInteger.ONE), "alive", new Bool(true)),
                "snapshot_id", new Text("native:2"), "revision", new IntegerValue(BigInteger.TWO), "native_revision", new IntegerValue(BigInteger.TWO),
                "date_raw", new IntegerValue(BigInteger.valueOf(100)), "paused", new Bool(true), "map_ready", new Bool(true));
        snapshot = snapshot.with("active_wars", new Arr(List.of())).with("player_armies", new Arr(List.of())).with("active_event", Nil.INSTANCE).with("pending_character_interaction", Nil.INSTANCE);
        return new PlanningRequest(frame, input.basis().source(), owner.sessionId(), Instant.parse("2026-10-24T00:01:00Z"),
                new PlanningObservation(snapshot, List.of(), java.util.Set.of(), java.util.Set.of(), java.util.Optional.empty(), List.of(), java.util.Optional.empty(), java.util.Optional.empty(), false));
    }
    private static ConstructionNextEpisodeReducer.Input input() { return input(false); }
    private static ConstructionNextEpisodeReducer.Input input(boolean restored) {
        Obj unknown = ConstructionCoordinatorPendingTest.original().with("status", new Text("action_state_unknown"));
        Obj old = obj("schema", new Text(ConstructionLedgerCodec.SCHEMA), "pending", unknown, "applied", Nil.INSTANCE,
                "applied_prior", new Arr(List.of()), "old_extension", obj("preserve", new Bool(true)));
        var ledger = ConstructionLedgerCodec.decodeLedger(encode(old));
        var before = driver(1, "episode", 42); var after = driver(2, "next-episode", 55);
        var beforeOwner = new SessionIdentity("construction-test-machine", game(99), "before-session");
        var savedOwner = new SessionIdentity("construction-test-machine", game(100), "saved-session");
        var afterOwner = restored ? new SessionIdentity("construction-test-machine", game(101), "restored-session") : savedOwner;
        var currentDriver = restored ? driver(2, "next-episode", 56) : after;
        ExactRef sourceRef = reference("source", new byte[]{1}); var source = new G2Source(beforeOwner.machineId(), "2026-10-24T00:00:00Z", "1.20.0.4", sourceRef);
        ExactRef oldRef = reference("old-construction", encode(old));
        var bodyRef = new DomainBodies.BodyRef(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA, oldRef,
                new FileIdentity("1", "18446744073709551615", "133000000000000000", "2026-10-24T00:00:00Z", oldRef.bytes()), List.of(sourceRef));
        ExactRef beforeRef = reference("before-driver", before.encode()), firstRef = reference("first-driver", after.encode());
        var frame = new ProposalLifecycle.ObservationIdentity(savedOwner.machineId(), savedOwner.game(),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.TWO, BigInteger.valueOf(7), BigInteger.valueOf(200)),
                        "native:7", BigInteger.valueOf(7), "next-episode"), 1);
        var semantic = new SemanticEvidence(frame, reference("semantic", new byte[]{2}), reference("native", new byte[]{3}),
                reference("stamp", new byte[]{4}), firstRef, Instant.parse("2026-10-24T00:00:00Z"));
        ExactRef materialRef = reference("baseline-material", new byte[]{'{','}'});
        var witness = new CheckpointPair.FileWitness(materialRef, new FileStatIdentity(BigInteger.valueOf(2), "18446744073709551615", "1234567890123456789"));
        
        Obj snapshot = obj("episode_run_id", new Text("next-episode"), "played_character", obj("character_id", new IntegerValue(BigInteger.TWO), "alive", new Bool(true)),
                "snapshot_id", new Text("native:7"), "revision", new IntegerValue(BigInteger.valueOf(7)), "native_revision", new IntegerValue(BigInteger.valueOf(7)),
                "date_raw", new IntegerValue(BigInteger.valueOf(200)), "paused", new Bool(true), "map_ready", new Bool(true));
        var currentFrame = restored ? new ProposalLifecycle.ObservationIdentity(afterOwner.machineId(), afterOwner.game(),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.TWO, BigInteger.valueOf(2), BigInteger.valueOf(200)),
                        "native:2", BigInteger.valueOf(2), "next-episode"), 1) : frame;
        var currentRef = restored ? reference("current-driver", currentDriver.encode()) : firstRef;
        var currentSemantic = restored ? new SemanticEvidence(currentFrame, reference("current-semantic", new byte[]{6}), reference("current-native", new byte[]{7}),
                reference("current-stamp", new byte[]{8}), currentRef, Instant.parse("2026-10-24T00:00:00Z")) : semantic;
        Obj currentSnapshot = restored ? snapshot.with("snapshot_id", new Text("native:2")).with("revision", new IntegerValue(BigInteger.TWO)).with("native_revision", new IntegerValue(BigInteger.TWO)) : snapshot;
        var basis = new ConstructionNextEpisodeReducer.Basis(restored ? ConstructionNextEpisodeReducer.Origin.RESTORED_FIRST : ConstructionNextEpisodeReducer.Origin.NEXT,
                beforeOwner, savedOwner, afterOwner, source, witness, reference("baseline-event", new byte[]{5}), 8, "a".repeat(64),
                restored ? 12 : 8, restored ? "b".repeat(64) : "a".repeat(64), bodyRef, beforeRef, firstRef, semantic, currentRef, currentSemantic);
        return new ConstructionNextEpisodeReducer.Input(ledger, before, after, snapshot, currentDriver, currentSnapshot, basis,
                new ConstructionNextEpisodeReducer.ProjectsUnavailable("actual independent construction query unavailable", java.util.Optional.empty()));
    }
    private static DriverStateSnapshot.Complete driver(long actor, String episode, long bridge) {
        var nil = new DriverStateSnapshot.NullValue();
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("actual-fixture-pipe", bridge, BigInteger.valueOf(actor), episode),
                List.of(), nil, nil, nil, nil, nil, nil, nil);
    }
    private static ExactRef reference(String name, byte[] bytes) { return new ExactRef("D:/fixture/" + name + ".json", bytes.length, ActionCodec.sha256(bytes)); }
    private static GameGeneration game(long pid) { return new GameGeneration(pid, new PythonOnlyUInt64(BigInteger.valueOf(133000000000000000L + pid))); }
}
