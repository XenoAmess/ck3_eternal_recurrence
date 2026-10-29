package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;
import org.xar.ck3.control.vanilla.schemesway.SwayScheduleWire;

/** Only the native read boundary is doubled; the factory, raw consumer and original scheduler are production. */
public final class OrdinarySwayFactoryTest {
    private static final ExactRef REF = new ExactRef("fixture:explicit-synthetic", 1, "1".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-23T17:00:00Z");
    private static final OrdinarySwayService.Capabilities ENABLED = new OrdinarySwayService.Capabilities(true, true, true);

    @Test void installedRootReadFeedsRealFactoryPolicyAndPreservesDifferentPublicNativeRevisions() {
        var request = request(); var nativeRead = new Reads(root()); var storage = new AtomicInteger();
        ActionCommand selected = selected(policy(nativeRead, storage, Ledger.empty(), ENABLED), request);
        var staged = OrdinarySwayPolicy.restoreStaged(selected);
        assertEquals(Job.QUERY_SELECTED_TARGET, staged.decision().job().orElseThrow());
        assertEquals(Optional.of(900L), staged.decision().targetCharacterId());
        assertEquals(BigInteger.valueOf(4), staged.frame().publicRevision());
        assertEquals(BigInteger.valueOf(3), staged.frame().nativeRevision());
        assertEquals(request.before(), nativeRead.last.before()); assertEquals(1, nativeRead.calls);
        assertEquals(1, storage.get()); assertFalse(staged.decision().submitAllowed());
    }

    @Test void disabledCapabilitiesAndEarlierActionCauseNoNativeOrStorageWork() {
        var request = request(); var nativeRead = new Reads(root()); var storage = new AtomicInteger();
        var disabled = policy(nativeRead, storage, Ledger.empty(), new OrdinarySwayService.Capabilities(true, false, false));
        assertInstanceOf(OrdinaryPolicy.Keep.class, disabled.evaluate(request, previous(request, "life-advance")));
        var enabled = policy(nativeRead, storage, Ledger.empty(), ENABLED);
        assertInstanceOf(OrdinaryPolicy.Keep.class, enabled.evaluate(request, previous(request, "select-event-option-0")));
        assertEquals(0, nativeRead.calls); assertEquals(0, storage.get());
    }

    @Test void unavailableRootPreservesPendingReconciliationWithoutCreatingAnotherStart() {
        var request = request(); var nativeRead = new Reads(root()); nativeRead.unavailable = true;
        var ledger = new Ledger(Optional.of(new Pending("original-unknown", 7, 900)), Optional.empty());
        var staged = OrdinarySwayPolicy.restoreStaged(selected(policy(nativeRead, new AtomicInteger(), ledger, ENABLED), request));
        assertEquals(Job.RECONCILE_PENDING, staged.decision().job().orElseThrow());
        assertEquals(Optional.of("original-unknown"), staged.decision().actionId());
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy(nativeRead, new AtomicInteger(), Ledger.empty(), ENABLED)
                .evaluate(request, previous(request, "life-advance")));
    }

    @Test void unboundFrameTokenOrGuardCannotReachTheLazyLedgerReader() {
        for (String failure : List.of("token", "guard", "step", "projection", "ack", "request")) {
            var nativeRead = new Reads(root()); nativeRead.failure = failure; var storage = new AtomicInteger();
            var request = request();
            assertInstanceOf(OrdinaryPolicy.Keep.class, policy(nativeRead, storage, Ledger.empty(), ENABLED)
                    .evaluate(request, previous(request, "life-advance")), failure);
            assertEquals(0, storage.get(), failure);
        }
    }

    @Test void nullMissingAndEmptyFrontierRemainDistinctAndMalformedIdsCannotCreateJobs() {
        for (String missing : List.of("missing", "null")) {
            ObjectNode value = root(); ObjectNode context = (ObjectNode)value.get("campaign_root_context");
            if (missing.equals("missing")) context.remove("direct_landed_vassal_character_ids");
            else context.putNull("direct_landed_vassal_character_ids");
            var request = request();
            assertInstanceOf(OrdinaryPolicy.Keep.class, policy(new Reads(value), new AtomicInteger(), Ledger.empty(), ENABLED)
                    .evaluate(request, previous(request, "life-advance")));
        }
        ObjectNode empty = root(); ((ObjectNode)empty.get("campaign_root_context")).putArray("direct_landed_vassal_character_ids");
        assertEquals(Job.COMPLETE_NO_RELATION, OrdinarySwayPolicy.restoreStaged(selected(
                policy(new Reads(empty), new AtomicInteger(), Ledger.empty(), ENABLED), request())).decision().job().orElseThrow());
        for (JsonNode bad : List.of(StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse("900.0".getBytes(StandardCharsets.UTF_8)), StrictJson.parse("0".getBytes(StandardCharsets.UTF_8)))) {
            ObjectNode value = root(); ((ObjectNode)value.get("campaign_root_context"))
                    .putArray("direct_landed_vassal_character_ids").add(bad);
            var request = request();
            assertInstanceOf(OrdinaryPolicy.Keep.class, policy(new Reads(value), new AtomicInteger(), Ledger.empty(), ENABLED)
                    .evaluate(request, previous(request, "life-advance")));
        }
    }

    @Test void lazyInputIdentityDriftAndStaleNativeRootRemainOptionalUnavailable() {
        var request = request(); var nativeRead = new Reads(root());
        var foreign = new ObservationIdentity(request.before().machineId(), request.before().game(),
                new ProposalFrame(request.before().frame().identity(), "foreign-snapshot", BigInteger.valueOf(4), "episode:fixture"), 1);
        var policy = OrdinarySwayPolicyFactory.create(REF, nativeRead, definition(),
                ignored -> Optional.of(new OrdinarySwayReadSource.BoundInputs(foreign,
                        new OrdinarySwayService.Inputs(Ledger.empty(), Optional.empty()))), ignored -> ENABLED,
                OrdinarySwayFactoryTest::expected);
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy.evaluate(request, previous(request, "life-advance")));
        ObjectNode stale = root(); ((ObjectNode)stale.get("campaign_root_context")).put("snapshot_revision", 2);
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy(new Reads(stale), new AtomicInteger(), Ledger.empty(), ENABLED)
                .evaluate(request, previous(request, "life-advance")));
    }

    @Test void originalProducerGoldenPassesTheNewReadConsumerAndOriginalSchedulerWithoutCopiedBodies() throws Exception {
        try (var stream = getClass().getResourceAsStream("/schemesway/producer-golden-v1.json")) {
            assertNotNull(stream, "the unchanged original producer fixture must be wired to application tests");
            JsonNode input = StrictJson.parse(stream.readAllBytes(), 262144).get("plan_cases").get(0).get("input");
            Request original = SwayScheduleWire.decode(StrictJson.canonical(input));
            Frame frame = original.frame().orElseThrow(); var request = request(frame);
            ObjectNode result = StrictJson.object(); result.put("step", OrdinarySwayReadSource.ROOT.value()); result.put("accepted", true);
            result.set("campaign_root_context", input.get("root"));
            var policy = OrdinarySwayPolicyFactory.create(REF, new Reads(result), definition(),
                    ignored -> Optional.of(new OrdinarySwayReadSource.BoundInputs(request.before(),
                            new OrdinarySwayService.Inputs(original.ledger(), original.state()))), ignored -> ENABLED,
                    OrdinarySwayFactoryTest::expected);
            var actual = OrdinarySwayPolicy.restoreStaged(selected(policy, request)).decision();
            assertArrayEquals(SwayScheduleWire.encode(plan(original)), SwayScheduleWire.encode(actual));
        }
    }

    @Test void wrongInstalledDefinitionIsRejectedBeforeAnyRead() {
        var wrong = new ReadContract<Obj>("fixture:wrong", new OperationKey("query-unrelated"), Optional.empty(),
                "fixture:private", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY,
                REF, input -> new NativeRequest(input.operation().value(), Optional.empty(), new RawJson(encode(input.arguments()))),
                receipt -> object(parse(receipt.original().originalResultToken().orElseThrow().bytes()), "result"));
        assertThrows(IllegalArgumentException.class, () -> new OrdinarySwayReadSource(new Reads(root()), wrong,
                ignored -> Optional.empty(), ignored -> ENABLED));
    }

    @Test void largeActualRootUsesTheFullNativeBoundaryAndDoesNotBecomeUnavailableAtProposalSize() {
        ObjectNode result = root(); result.put("unrelated_preserved_native_root", "x".repeat(131073));
        var request = request();
        assertEquals(Job.QUERY_SELECTED_TARGET, OrdinarySwayPolicy.restoreStaged(selected(
                policy(new Reads(result), new AtomicInteger(), Ledger.empty(), ENABLED), request)).decision().job().orElseThrow());
    }

    private static OrdinarySwayPolicy policy(Reads nativeRead, AtomicInteger storage, Ledger ledger,
            OrdinarySwayService.Capabilities capabilities) {
        return OrdinarySwayPolicyFactory.create(REF, nativeRead, definition(), request -> {
            storage.incrementAndGet(); return Optional.of(new OrdinarySwayReadSource.BoundInputs(request.before(),
                    new OrdinarySwayService.Inputs(ledger, Optional.empty())));
        }, ignored -> capabilities, OrdinarySwayFactoryTest::expected);
    }
    private static ReadContract<Obj> definition() {
        return new ReadContract<>("fixture:registered-root", OrdinarySwayReadSource.ROOT, Optional.of("fixture:root-capability"),
                "fixture:root-permission", ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                REF, input -> new NativeRequest(input.operation().value(), Optional.of("fixture:root-capability"), new RawJson(encode(input.arguments()))),
                receipt -> DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(), DriverJson.MAX_NATIVE_BYTES));
    }
    private static ObjectNode root() {
        ObjectNode result = StrictJson.object(); result.put("step", OrdinarySwayReadSource.ROOT.value()); result.put("accepted", true);
        result.putObject("campaign_root_context").put("status", "available").put("player_character_id", 7)
                .put("player_character_alive", true).put("snapshot_revision", 3).put("date_raw", 1000)
                .putArray("direct_landed_vassal_character_ids").add(900);
        return result;
    }
    private static PlanningRequest request() {
        return request(new Frame("fixture:public-4", BigInteger.valueOf(4), BigInteger.valueOf(3), BigInteger.valueOf(1000),
                7, true, true, true, Context.CLEAR));
    }
    private static PlanningRequest request(Frame original) {
        var identity = new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(
                BigInteger.valueOf(original.actorCharacterId()), original.nativeRevision(), original.dateRaw());
        var frame = new ProposalFrame(identity, original.snapshotId(), original.publicRevision(), "episode:fixture");
        var before = new ObservationIdentity("xenoamess-full-tower-eb9d2c1186",
                new GameGeneration(73, new PythonOnlyUInt64(new BigInteger("134370000000000001"))), frame, 1);
        var source = new G2Source(before.machineId(), NOW.toString(), "1.20.0.4", REF);
        ObjectNode snapshot = StrictJson.object(); snapshot.put("snapshot_id", frame.snapshotId()); snapshot.put("episode_run_id", frame.episodeRunId());
        snapshot.put("revision", frame.revision()); snapshot.put("native_revision", identity.nativeRevision()); snapshot.put("date_raw", identity.dateRaw());
        snapshot.put("paused", true); snapshot.put("map_ready", true); snapshot.putArray("active_wars"); snapshot.putArray("player_armies");
        snapshot.putNull("active_event"); snapshot.putNull("pending_character_interaction");
        snapshot.putObject("played_character").put("character_id", original.actorCharacterId()).put("alive", true);
        var observations = new PlanningObservation(object(parse(StrictJson.canonical(snapshot)), "snapshot"), List.of(),
                Set.of(OrdinarySwayPolicy.OPERATION), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "fixture:session", NOW.plusSeconds(20), observations);
    }
    private static ExpectedPostcondition expected(PlanningRequest request, OrdinarySwayService.Staged ignored) {
        return new ExpectedPostcondition(1, request.before(), request.source(), "fixture:only-unit-effect/v1",
                List.of(new ExpectedBoolean(new FieldKey("fixture.observed"), true)));
    }
    private static OrdinaryPolicy.Draft previous(PlanningRequest request, String operation) {
        var command = new ActionCommand("fixture:earlier", request.before(), request.source(), request.sessionId(), new OperationKey(operation),
                new Obj(Map.of()), expected(request, null), new Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        return new OrdinaryPolicy.Draft("fixture:earlier", operation, "declared synthetic prior selection", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new Obj(Map.of()));
    }
    private static ActionCommand selected(OrdinarySwayPolicy policy, PlanningRequest request) {
        return assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, previous(request, "life-advance")))
                .draft().command().orElseThrow();
    }

    private static final class Reads implements PlanningReadPort {
        final ObjectNode value; int calls; String failure = ""; boolean unavailable; PlanningReadRequest last;
        Reads(ObjectNode value) { this.value = value; }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            calls++; last = request;
            if (unavailable) return new PlanningReadResult.Unavailable<>("fixture:native-read-unavailable", Optional.empty());
            contract.prepare(request, "fixture:read");
            ObjectNode result = value.deepCopy(); if (failure.equals("step")) result.put("step", "query-other");
            ObjectNode envelope = StrictJson.object(); envelope.put("type", "command_result"); envelope.put("protocol_version", 1);
            envelope.put("request_id", failure.equals("request") ? "fixture:foreign-read" : "fixture:read");
            envelope.put("ok", true); envelope.set("result", result);
            ObjectNode token = result.deepCopy(); if (failure.equals("token")) token.put("extra", true);
            var binding = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE, request.operation(),
                    REF, REF, "fixture:sole-authority", NOW, NOW.plusSeconds(20));
            var before = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
            var after = new PlanningReadGuard(binding, true, true, true, (failure.equals("guard") ? "b" : "a").repeat(64));
            byte[] originalFrame = StrictJson.canonical(envelope, StrictJson.EXPLICIT_MAX_BYTES);
            var ack = new NativeActionPort.AckReceived("fixture:read", !failure.equals("ack"),
                    Optional.of(new RawJson(StrictJson.canonical(token, StrictJson.EXPLICIT_MAX_BYTES))),
                    new RawJson(originalFrame), originalFrame);
            var receipt = new PlanningReadReceipt(request, contract.contractId(), "fixture:read", before, after, ack);
            T decoded = contract.decode(receipt);
            if (failure.equals("projection")) {
                ObjectNode changed = token.deepCopy(); changed.put("altered_projection", true);
                var alteredAck = new NativeActionPort.AckReceived("fixture:read", true, Optional.of(new RawJson(StrictJson.canonical(changed, StrictJson.EXPLICIT_MAX_BYTES))),
                        ack.originalFrame(), ack.originalPacket());
                var altered = new PlanningReadReceipt(request, contract.contractId(), "fixture:read", before, after, alteredAck);
                decoded = contract.decode(altered);
            }
            return new PlanningReadResult.Known<>(decoded, receipt, REF);
        }
    }
}
