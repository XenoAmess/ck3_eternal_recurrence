package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.events.EventReadBinding;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind;

/** Pure policy software DATA. Synthetic historical receipts/refs grant no Native or Game authority. */
final class EventFixedWindowHeldPlanning224Test {
    private static final Obj EMPTY = new Obj(Map.of());
    private static final Obj SEED = new Obj(Map.of("fixture_retained_history", new Text("original")));
    private static final BigInteger NATIVE_GENERATION = BigInteger.valueOf(23);
    private static final BigInteger DRIVER_GENERATION = BigInteger.ONE;
    private static final ExactRef RECEIPT = new ExactRef("software-fixed-window-receipt", 1, "b".repeat(64));
    private static final ExactRef FRAME = new ExactRef("software-fixed-window-frame", 1, "c".repeat(64));
    private static final ExactRef CAPABILITIES = new ExactRef("software-fixed-window-capabilities", 1, "d".repeat(64));
    private static final String REQUEST_ID = "software-fixed-window-query";
    private static final String CONTRACT_ID = "software-fixed-window-query/v1";

    @Test void bothFixedWindowQueriesRetainFrozenSnapshotAndOriginalReadHistory() {
        for (WindowKind target : WindowKind.values()) {
            Fixture fixture = new Fixture(target);
            Obj frozen = fixture.request.observations().snapshot();
            byte[] original = OpportunityJson.encode(frozen);
            var decision = assertInstanceOf(OrdinaryPolicy.Replace.class,
                    fixture.policy.evaluate(fixture.request, OrdinaryPolicy.Draft.empty()));
            assertEquals(target.closeStep(), decision.draft().command().orElseThrow().operation().value());
            assertEquals(1, fixture.reads.get());
            assertEquals(1, fixture.owners.get());
            assertEquals(1, fixture.publications.get());
            assertEquals(2, fixture.decodes.get(), "read port and actual receipt binding both decode the original");
            assertNotNull(fixture.original.get());
            assertSame(frozen, fixture.request.observations().snapshot());
            assertArrayEquals(original, OpportunityJson.encode(frozen));
            assertEquals(List.of(SEED), fixture.request.observations().history());
            assertNull(frozen.get(target.publicPrefix() + "_observation"));
        }
    }

    @Test void secondEvaluationCannotInheritThePreviousLocalWindowOverlay() {
        for (WindowKind target : WindowKind.values()) {
            Fixture fixture = new Fixture(target);
            assertInstanceOf(OrdinaryPolicy.Replace.class,
                    fixture.policy.evaluate(fixture.request, OrdinaryPolicy.Draft.empty()));
            fixture.unavailable = true;
            var wait = assertInstanceOf(OrdinaryPolicy.Wait.class,
                    fixture.policy.evaluate(fixture.request, OrdinaryPolicy.Draft.empty()));
            assertEquals("software second query unavailable", wait.reason());
            assertEquals(2, fixture.reads.get(), "a new evaluate call must query again");
            assertEquals(1, fixture.owners.get(), "the first visible result cannot authorize a second close");
            assertEquals(1, fixture.publications.get());
            assertEquals(2, fixture.decodes.get());
            assertEquals(List.of(SEED), fixture.request.observations().history());
            assertNull(fixture.request.observations().snapshot().get(target.publicPrefix() + "_observation"));
        }
    }

    private static final class Fixture {
        final WindowKind target;
        final PlanningRequest request;
        final ReadContract<ArmyWindowCodec.Observation> contract;
        final OrdinaryPolicy policy;
        final AtomicInteger reads = new AtomicInteger(), owners = new AtomicInteger(),
                publications = new AtomicInteger(), decodes = new AtomicInteger();
        final AtomicReference<PlanningReadReceipt> original = new AtomicReference<>();
        final AtomicReference<Obj> published = new AtomicReference<>();
        boolean unavailable;

        Fixture(WindowKind kind) {
            target = kind;
            WindowKind other = kind == WindowKind.RESULTS ? WindowKind.DECLARED_OVERVIEW : WindowKind.RESULTS;
            PlanningRequest seed = PlanningFixtures.request(PlanningFixtures.snapshot(), List.of(SEED),
                    Set.of(new OperationKey(kind.closeStep())));
            Obj snapshot = seed.observations().snapshot().with(other.publicPrefix() + "_observation",
                    normalized(decode(other, seed, false)));
            PlanningRequest base = PlanningFixtures.request(snapshot, List.of(SEED),
                    Set.of(new OperationKey(kind.closeStep())));
            var observed = base.observations();
            request = new PlanningRequest(base.before(), base.source(), base.sessionId(), base.deadline(),
                    new PlanningObservation(snapshot, observed.history(), observed.actionSteps(),
                            Set.of(kind.queryCapability(), kind.closeCapability(), other.queryCapability(), other.closeCapability()),
                            observed.battleSpeedReadiness(), observed.actionFacts(), observed.campaignGoal(),
                            observed.crossRunPlan(), observed.initialLifestyleFocusRequired()));
            OperationKey operation = new OperationKey(kind.queryStep());
            contract = new ReadContract<>(CONTRACT_ID, operation, Optional.of(kind.queryCapability()),
                    "software-fixed-window-query", ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                    ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    request.source().sourceRef(), (actual, id) -> { throw new AssertionError("no Native preparation"); },
                    receipt -> {
                        decodes.incrementAndGet();
                        assertEquals(request.before(), receipt.request().before());
                        return ArmyWindowCodec.decode(army(kind), ArmyWindowCodec.Operation.QUERY,
                                receipt.original().originalFrame().bytes(), receipt.requestId(),
                                new ArmyTypes.Context(receipt.request().before(), receipt.request().source(),
                                        receipt.request().sessionId(), receipt.request().deadline()),
                                NATIVE_GENERATION, DRIVER_GENERATION);
                    });
            PlanningReadPort port = new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual, PlanningReadRequest query) {
                    reads.incrementAndGet();
                    assertSame(contract, actual);
                    assertEquals(request.before(), query.before());
                    assertEquals(request.source(), query.source());
                    assertEquals(request.sessionId(), query.sessionId());
                    assertEquals(request.deadline(), query.deadline());
                    assertEquals(operation, query.operation());
                    assertEquals(EMPTY, query.arguments());
                    if (unavailable) return new PlanningReadResult.Unavailable<>(
                            "software second query unavailable", Optional.empty());
                    PlanningReadReceipt receipt = receipt(query, kind);
                    original.set(receipt);
                    return new PlanningReadResult.Known<>(actual.decode(receipt), receipt, RECEIPT);
                }
            };
            EventReadBinding<ArmyWindowCodec.Observation> binding = EventReadBinding.actualReceiptFamily(
                    operation, operation::equals, (actual, selected) -> {
                        assertSame(request, actual);
                        assertEquals(operation, selected);
                        return new EventReadBinding.ReceiptResolution<>(contract, EMPTY, known -> {
                            publications.incrementAndGet();
                            assertSame(original.get(), known.receipt());
                            assertEquals(RECEIPT, known.originalReceipt());
                            Obj value = normalized(known.value());
                            assertEquals(PlanningFixtures.integer(23), value.get("connection_generation"));
                            assertEquals(PlanningFixtures.integer(1), value.get("queried_connection_generation"));
                            published.set(value);
                            return new EventPolicies.ReadPublication(value, Optional.empty());
                        });
                    });
            OrdinaryCorePolicy.CommandBinding owner = (actual, selected, arguments, plan, purpose, domain) -> {
                owners.incrementAndGet();
                assertSame(request.observations().snapshot(), actual.observations().snapshot());
                assertEquals(request.observations().snapshot(), actual.observations().snapshot());
                assertEquals(request.before(), actual.before());
                assertEquals(request.source(), actual.source());
                assertEquals(request.sessionId(), actual.sessionId());
                assertEquals(request.deadline(), actual.deadline());
                assertEquals(kind.closeStep(), selected.value());
                assertEquals(EMPTY, arguments);
                assertEquals(OrdinaryPolicy.Purpose.WORLD_ACTION, purpose);
                assertTrue(domain.isEmpty());
                List<Obj> history = actual.observations().history();
                assertEquals(2, history.size());
                assertSame(SEED, history.getFirst());
                Obj captured = history.getLast();
                assertEquals(new Text(operation.value()), captured.get("command"));
                assertEquals(new Bool(true), captured.get("ok"));
                assertEquals(new Text(original.get().requestId()), captured.get("native_read_request_id"));
                assertEquals(new Text(original.get().contractId()), captured.get("read_contract_id"));
                assertEquals(OpportunityJson.parse(StrictJson.canonical(RECEIPT.toJson())),
                        captured.get("native_read_original_receipt"));
                assertEquals(published.get(), captured.get("result"));
                return new OrdinaryCorePolicy.Prepared(PlanningFixtures.command(actual, selected, arguments));
            };
            policy = EventPolicies.policies(request.source().sourceRef(), Optional.empty(),
                    (actual, selected, plan, trait) -> { throw new AssertionError("shared owner expected"); },
                    port, List.of(binding), (actual, raw) -> { throw new AssertionError("no event context"); },
                    (actual, retained) -> { throw new AssertionError("no diagnostic capture expected"); }, owner)
                    .stream().filter(row -> row.stage() == PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS)
                    .findFirst().orElseThrow();
        }
    }

    private static PlanningReadReceipt receipt(PlanningReadRequest request, WindowKind kind) {
        var evidence = new GuardEvidence(request.before(), request.source(), request.sessionId(), DRIVER_GENERATION,
                request.operation(), FRAME, CAPABILITIES, "software-fixed-window-authority",
                PlanningFixtures.NOW, request.deadline());
        var guard = new PlanningReadGuard(evidence, true, true, true, "e".repeat(64));
        byte[] bytes = StrictJson.canonical(envelope(kind, true));
        byte[] packet = ByteBuffer.allocate(bytes.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(bytes.length).put(bytes).array();
        var ack = new NativeActionPort.AckReceived(REQUEST_ID, true,
                Optional.of(new RawJson(StrictJson.canonical(envelope(kind, true).get("result")))),
                new RawJson(bytes), packet);
        return new PlanningReadReceipt(request, CONTRACT_ID, REQUEST_ID, guard, guard, ack);
    }

    private static ArmyWindowCodec.Kind army(WindowKind kind) {
        return kind == WindowKind.RESULTS ? ArmyWindowCodec.Kind.RESULTS : ArmyWindowCodec.Kind.OVERVIEW;
    }

    private static ArmyWindowCodec.Observation decode(WindowKind kind, PlanningRequest request, boolean visible) {
        return ArmyWindowCodec.decode(army(kind), ArmyWindowCodec.Operation.QUERY,
                StrictJson.canonical(envelope(kind, visible)), REQUEST_ID,
                new ArmyTypes.Context(request.before(), request.source(), request.sessionId(), request.deadline()),
                NATIVE_GENERATION, DRIVER_GENERATION);
    }

    private static Obj normalized(ArmyWindowCodec.Observation value) {
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value.normalized())), "strict software window");
    }

    private static ObjectNode envelope(WindowKind kind, boolean visible) {
        ObjectNode top = StrictJson.object();
        top.put("type", "command_result").put("protocol_version", 1).put("request_id", REQUEST_ID).put("ok", true);
        ObjectNode owner = top.putObject(army(kind).ownerKey());
        owner.put("request_id", REQUEST_ID).put("ticket_sequence", 7).put("executor_started_sequence", 7)
                .put("completed_sequence", 7).put("pump_epoch", 2).put("thread_id", 11)
                .put("date_raw", 24000).put("connection_generation", NATIVE_GENERATION);
        ObjectNode row = top.putObject("result");
        row.put("schema", kind == WindowKind.RESULTS ? "ck3-war-results-window-v1" : "ck3-war-declared-overview-v1")
                .put("operation", "query").put("window_name", kind == WindowKind.RESULTS ? "war_results" : "war_declared_overview")
                .put("played_character_id", 29829).put("date_raw", 24000).put("native_revision", 1)
                .put("connection_generation", NATIVE_GENERATION).put("pump_epoch", 2).put("thread_id", 11)
                .put("game_version", "1.20.0.4")
                .put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                .put("ticket_sequence", 7).put("available", true).put("accepted", true)
                .put("root_observed", true).put("window_present", visible).put("effective_visible", visible)
                .put("dispatch_attempted", false).put("dispatch_invoked", false).put("native_handled", false)
                .put("post_observed", true).put("post_window_present", visible).put("post_effective_visible", visible)
                .put("scope_unchanged", true).put("closure_verified", false)
                .put("application_owner_thread_verified", true).put("paused", true)
                .put("status", visible ? "visible" : "absent").put("unavailable_reason", "").put("button_name", "")
                .put("request_id", REQUEST_ID).put("root_observation_source", "guarded_top_level_and_complete_owner_tree")
                .put("post_observation_source", "guarded_top_level_and_complete_owner_tree");
        return top;
    }
}
