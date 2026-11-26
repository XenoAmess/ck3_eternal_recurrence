package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.lang.reflect.Proxy;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionEffects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.CompositeExecution;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PhysicalStatusIdentity;
import org.xar.ck3.control.application.action.PhysicalStatusIdentityCodec;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.PortableRecoveryDataArchive;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Original interrupted Life DATA and a test-only model of the source-owned expiry wire field. */
final class LifeExpiredPartialAdvanceEvidenceDataTest {
    @Test void originalAckedUnknownTimelineRemainsUnqualifiedAfterItsDeadline() throws Exception {
        try (var resource = getClass().getResourceAsStream("/org/xar/ck3/control/application/session/source56-interrupted-recovery-prefix.json.gz")) {
            assertNotNull(resource);
            try (var gzip = new GZIPInputStream(resource)) {
                byte[] fixture = gzip.readNBytes(1 << 20);
                assertTrue(fixture.length < 1 << 20);
                var data = FullJsonTree.parse(fixture, 1 << 20);
                var row = ContinuityJson.parseObject(Base64.getDecoder().decode(data.get("head").textValue()), 1 << 20);
                var archive = new PortableRecoveryDataArchive(same -> { throw new AssertionError("fixture makes no writer call"); }, (ref, maximum) -> {
                    var material = data.path("artifacts").get(ref.sha256());
                    assertNotNull(material);
                    return Base64.getDecoder().decode(material.textValue());
                }).proxy();
                var actions = ContinuityActionJournal.receipts(ContinuityState.fromJson(row, row.get("machine_id").textValue()), archive);
                var parent = ContinuityBatchJournal.readOnlyLifeRecoveryRoot(actions).orElseThrow();
                var children = ActionTransitions.composite(parent.state()).orElseThrow().children().stream()
                        .map(binding -> actions.stream().filter(receipt -> receipt.command().actionId().equals(binding.actionId())).findFirst().orElseThrow()).toList();
                var deadline = parent.command().deadline();

                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, children, deadline));
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, children, deadline.plusNanos(1)));
                assertEquals(55, children.getLast().sequence());
                assertInstanceOf(ActionState.Unknown.class, children.getLast().state());
                assertTrue(children.getLast().ack().orElseThrow().nativeOk());
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, children.reversed(), deadline.plusNanos(1)));
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, List.of(children.getFirst()), deadline.plusNanos(1)));
                assertEquals(ActionReceipt.Outcome.UNRESOLVED, parent.outcome());
                assertEquals(ActionReceipt.Outcome.UNRESOLVED, children.getLast().outcome());
                assertFalse(parent.eligibleAdvance());
                assertEquals(deadline, parent.command().deadline());
                assertFalse(LifeExpiredPartialAdvanceEvidence.terminalShape(parent));
                assertTrue(LifeExpiredPartialAdvanceEvidence.readTerminalData(parent, archive).isEmpty());

                // Only the future receipt role is modeled here. These refs have no
                // originals in this fixture and cannot pass production archive replay.
                var legacyResume = children.getLast();
                var attempt = ActionTransitions.attempt(legacyResume.state()).orElseThrow();
                var unqualifiedFixtureCore = new ResumeCoreObservation(
                        new ExactRef("fixture/before-core", 1, "5".repeat(64)),
                        new ExactRef("fixture/core-ack", 1, "6".repeat(64)), legacyResume.command().deadline());
                var futureReceiptShape = new ActionReceipt(legacyResume.version(), legacyResume.sequence(), legacyResume.command(),
                        legacyResume.bodySha256(), new ActionState.Settled(attempt, legacyResume.ack().orElseThrow(),
                                new ActionState.ResumeCoreApplied(unqualifiedFixtureCore)));
                assertTrue(LifeExpiredPartialAdvanceEvidence.accepts(parent,
                        List.of(children.getFirst(), futureReceiptShape), deadline.plusNanos(1)));
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent,
                        List.of(children.getFirst(), futureReceiptShape), deadline));
                checkTerminalData(parent, children.getFirst(), legacyResume, futureReceiptShape);

                var plan = AdvancePlan.decode(parent.command());
                var status = ClockStatusRead.decode(ack(token(1 << 15, "evaluation_failure")));
                BigInteger partialDate = BigInteger.valueOf(53179944);
                assertEquals(24L, LifeExpiredPartialAdvanceEvidence.partialDays(plan, status, partialDate));
                var wrongPause = token(1 << 15, "evaluation_failure");
                ((ObjectNode) wrongPause.get("tactical_daily_sentinel")).put("pause_observed", false);
                assertThrows(IllegalArgumentException.class, () ->
                        LifeExpiredPartialAdvanceEvidence.partialDays(plan, ClockStatusRead.decode(ack(wrongPause)), partialDate));
                for (var rejected : List.of(plan.startingDateRaw(), plan.targetDateRaw(),
                        plan.targetDateRaw().add(AdvancePlan.DAY), partialDate.add(BigInteger.ONE),
                        partialDate.subtract(AdvancePlan.DAY))) {
                    assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.partialDays(plan, status, rejected));
                }
            }
        }
    }

    private static void checkTerminalData(ActionReceipt parent, ActionReceipt arm,
            ActionReceipt oldResume, ActionReceipt futureResume) throws IOException {
        var command = parent.command();
        var execution = ((ActionState.CompositeUnknown) parent.state()).execution();
        var time = command.deadline().plusSeconds(1);
        var before = command.before();
        var startNative = proofRef("start-native", '1');
        var endNative = proofRef("end-native", '2');
        var facts = proofRef("driver", '3');
        var sem = proofRef("semantic", '4');
        var revision = before.frame().identity().nativeRevision().add(BigInteger.TEN);
        var after = new ObservationIdentity(before.machineId(), before.game(),
                new ProposalFrame(new Frame(before.frame().identity().player(), revision, BigInteger.valueOf(53179944)),
                        "native:" + revision, before.frame().revision().add(BigInteger.ONE), before.frame().episodeRunId()), before.observationVersion());
        var basis = new ObservationProvenance.FreshSnapshotQuery("fixture-full", proofRef("full-ack", '5'), event(3, time),
                new ObservationProvenance.LiveAfterSetter(proofRef("resume-ack", '6')));
        var semantic = new Obj(Map.ofEntries(
                Map.entry("snapshot_id", new Text(after.frame().snapshotId())),
                Map.entry("revision", new IntegerValue(after.frame().revision())),
                Map.entry("native_revision", new IntegerValue(revision)),
                Map.entry("date_raw", new IntegerValue(after.frame().identity().dateRaw())),
                Map.entry("episode_run_id", new Text(after.frame().episodeRunId())),
                Map.entry("played_character", new Obj(Map.of("character_id", new IntegerValue(after.frame().identity().player()),
                        "alive", new Bool(true)))),
                Map.entry("paused", new Bool(true)), Map.entry("map_ready", new Bool(true)),
                Map.entry("speed", new IntegerValue(BigInteger.valueOf(5))),
                Map.entry("active_event", Nil.INSTANCE), Map.entry("pending_character_interaction", Nil.INSTANCE),
                Map.entry("one_life_terminal_reason", Nil.INSTANCE), Map.entry("active_wars", new Arr(List.of())),
                Map.entry("player_armies", new Arr(List.of())), Map.entry("diagnostics", new Obj(Map.of()))));
        var ending = new AdvanceObservationPort.Frame(after, command.source(), command.sessionId(), semantic,
                basis, event(3, time).observedAt(), endNative);
        var start = new LifeAdvanceEvidence.FrameRecord(before, new ObservationProvenance.Push(before.frame().snapshotId(),
                before.frame().identity().nativeRevision(), startNative), execution.guard().observedAt(), startNative, facts, sem);
        var end = new LifeAdvanceEvidence.FrameRecord(after, basis, ending.observedAt(), endNative, facts, sem);
        var status = fixtureExpiryRead(parent, ending);

        var valid = terminalFixture(parent, arm, futureResume, status, start, end);
        var receipt = terminalReceipt(parent, execution, ending, valid.reference(), AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS);
        assertTrue(LifeExpiredPartialAdvanceEvidence.terminalShape(receipt));
        assertTrue(receipt.visibleGameplay());
        assertFalse(receipt.eligibleAdvance());
        var settlement = ((ActionState.CompositeSettled) receipt.state()).settlement();
        ActionEffects.validateComposite(command, execution, settlement);
        ActionEffects.validateCompositeChildren(command, execution, settlement, List.of(arm, futureResume));
        assertFalse(receipt.applied().orElseThrow().observation().actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("timeline.checkpoint_eligible"), true)));
        var data = LifeExpiredPartialAdvanceEvidence.readTerminalData(receipt, valid.archive()).orElseThrow();
        assertEquals(parent, data.original());
        assertEquals(List.of(arm, futureResume), data.children());
        assertEquals(start, data.starting());
        assertEquals(end, data.ending());
        assertEquals(status, data.status());
        assertTrue(AdvanceResult.compatibleResult(receipt, valid.archive()).isEmpty());
        var noFrameBytes = new LifeExpiredPartialAdvanceEvidence(valid.archive(), (ignored, frame, archive) -> {
            throw new AssertionError("inexact frame bytes must be rejected before reconstruction");
        }, new AdvancePrimitiveArchivedReplay((frame, archive) -> {
            throw new AssertionError("inexact frame bytes must be rejected before child replay");
        }));
        assertThrows(IllegalArgumentException.class, () -> noFrameBytes.verifyTerminal(receipt, data));

        var old = terminalFixture(parent, arm, oldResume, status, start, end);
        var former = terminalReceipt(parent, execution, ending, old.reference(), AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS);
        assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.readTerminalData(former, old.archive()));
        var mismatched = terminalReceipt(parent, execution, ending, valid.reference(), AdvanceClock.ProgressStatus.POSTCONDITION);
        assertFalse(LifeExpiredPartialAdvanceEvidence.terminalShape(mismatched));
        var badBytes = terminalReceipt(parent, execution, ending, proofRef("different-terminal", '8'),
                AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS);
        assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.readTerminalData(badBytes, valid.archive()));
    }

    private static PlanningReadReceipt fixtureExpiryRead(ActionReceipt parent, AdvanceObservationPort.Frame ending) throws IOException {
        var command = parent.command();
        var identity = ending.identity();
        var transport = new TransportSession(identity.machineId(), identity.game(), BigInteger.valueOf(22), command.sessionId());
        var hello = proofRef("hello", '7');
        var physical = new PhysicalStatusIdentity(transport, identity.frame().snapshotId(), identity.frame().identity().nativeRevision(),
                command.source(), ending.originalEvidence(), hello, proofRef("heartbeat", '8'), Optional.empty(), Optional.empty(), ending.observedAt());
        var step = new OperationKey(ClockStatusRead.STEP);
        var deadline = ending.observedAt().plusSeconds(15);
        var guard = new GuardEvidence(new CommandOrigin.PhysicalStatusOnly(physical), command.source(), command.sessionId(),
                transport.connectionGeneration(), step, ending.originalEvidence(), hello, "expiry-fixture-physical", ending.observedAt(),
                deadline, List.of(hello));
        var readGuard = new PlanningReadGuard(guard, new PlanningReadGuard.PhysicalStatus(physical),
                PhysicalStatusIdentityCodec.bindingSha256(physical));
        var request = PlanningReadRequest.newStatusOnly(physical, step, new Obj(Map.of()), deadline);
        var id = "fixture-expiry-status";
        var token = token(1 << 15, "evaluation_failure");
        token.putObject(LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_FIELD)
                .put("schema", LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_SCHEMA)
                .put("generation", 2).put("original_deadline_unix_ms", command.deadline().toEpochMilli()).put("failure_flags", 32)
                .put("armed", false).put("shutdown_safe", true).put("access_cleanup_unknown", false);
        var wireRequest = StrictJson.object().put("type", "execute_step").put("protocol_version", 1).put("request_id", id)
                .put("step", step.value()).put("expected_revision", physical.nativeRevision());
        var wireResponse = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true);
        wireResponse.set("result", token);
        byte[] out = NativeWire.packet(StrictJson.canonical(wireRequest));
        byte[] in = NativeWire.packet(StrictJson.canonical(wireResponse));
        var time = ending.observedAt();
        var custody = new NativeRequestChronology(transport, UUID.fromString("8c799220-1674-4572-9dca-7a0e40d20b49"),
                id, NativeRequestChronology.PacketIdentity.of(out), NativeRequestChronology.PacketIdentity.of(in),
                event(5, time), event(6, time), event(7, time));
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(StrictJson.canonical(token))),
                new RawJson(StrictJson.canonical(wireResponse)), in, Optional.of(new NativeActionPort.OutboundPacket(id, out)), Optional.of(custody));
        return new PlanningReadReceipt(request, PhysicalStatusIdentity.CONTRACT_ID, id, readGuard, readGuard, ack);
    }

    private record TerminalFixture(ExactRef reference, ActionPorts.OutcomeArchive archive) { }

    /** Portable capture of the terminal DATA format. The installed cold replay still requires full immutable originals. */
    private static TerminalFixture terminalFixture(ActionReceipt parent, ActionReceipt arm, ActionReceipt resume,
            PlanningReadReceipt status, LifeAdvanceEvidence.FrameRecord start, LifeAdvanceEvidence.FrameRecord end) {
        var parentRef = proofRef("parent", 'a');
        var armRef = proofRef("arm", 'b');
        var resumeRef = proofRef("resume", 'c');
        var statusRef = proofRef("status", 'd');
        var expiry = new RawJson(DriverJson.encode(new Obj(Map.of(
                "schema", new Text(LifeExpiredPartialAdvanceEvidence.SCHEMA), "parent_receipt", ref(parentRef),
                "child_receipts", new Arr(List.of(ref(armRef), ref(resumeRef))), "status_read", ref(statusRef),
                "ending", LifeAdvanceEvidence.frame(end)))));
        var expiryRef = new ExactRef("fixture/expiry", expiry.bytes().length, ActionCodec.sha256(expiry.bytes()));
        var wrapper = new RawJson(DriverJson.encode(new Obj(Map.of("schema", new Text(LifeExpiredPartialAdvanceEvidence.TERMINAL_SCHEMA),
                "expiry", ref(expiryRef), "starting", LifeAdvanceEvidence.frame(start)))));
        var wrapperRef = new ExactRef("fixture/terminal", wrapper.bytes().length, ActionCodec.sha256(wrapper.bytes()));
        var receipts = Map.of(parentRef, parent, armRef, arm, resumeRef, resume);
        var refs = Map.of(parent, parentRef, arm, armRef, resume, resumeRef);
        var archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class}, (ignored, method, args) -> switch (method.getName()) {
                    case "loadMaterial" -> expiryRef.equals(args[0]) ? expiry : wrapper;
                    case "loadReceipt" -> receipts.get(args[0]);
                    case "receiptReferenceOf" -> refs.get(args[0]);
                    case "loadNativeFrame" -> new byte[]{1};
                    case "loadRead" -> status;
                    case "readReferenceOf" -> statusRef;
                    case "referenceOf" -> new ExactRef("fixture/actual-status-ack", status.original().originalPacket().length,
                            ActionCodec.sha256(status.original().originalPacket()));
                    default -> throw new AssertionError(method.getName());
                });
        return new TerminalFixture(wrapperRef, archive);
    }

    private static Value ref(ExactRef ref) {
        return DriverJson.fromNode(ref.toJson());
    }

    private static ActionReceipt terminalReceipt(ActionReceipt parent, CompositeExecution execution,
            AdvanceObservationPort.Frame ending, ExactRef reference, AdvanceClock.ProgressStatus progress) {
        var effect = LifeAdvanceComposite.observation(parent.command(), AdvancePlan.decode(parent.command()), ending,
                progress, null, List.of(reference));
        return new ActionReceipt(parent.version(), parent.sequence() + 1, parent.command(), parent.bodySha256(),
                new ActionState.CompositeSettled(execution, new ActionState.Applied(effect)));
    }

    private static ExactRef proofRef(String path, char digest) {
        return new ExactRef("fixture/" + path, 1, String.valueOf(digest).repeat(64));
    }

    @Test void fullReadNeedsSameHeldSetterOrAnExactNewConnectionWatch() {
        var game = new org.xar.ck3.control.contracts.GameGeneration(50372,
                new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.valueOf(134401544348311914L)));
        var session = new TransportSession("fixture-machine", game, BigInteger.valueOf(16), "fixture-session");
        var newConnection = new TransportSession(session.machineId(), game, BigInteger.valueOf(17), session.sessionId());
        var differentGame = new TransportSession(session.machineId(),
                new org.xar.ck3.control.contracts.GameGeneration(50373, game.creationFiletime()),
                newConnection.connectionGeneration(), session.sessionId());
        var oldEpoch = UUID.fromString("8c799220-1674-4572-9dca-7a0e40d20b45");
        var newEpoch = UUID.fromString("8c799220-1674-4572-9dca-7a0e40d20b46");
        var resume = chronology(session, oldEpoch, "resume", 10);
        var full = chronology(session, oldEpoch, "full", 20);
        var reconnected = chronology(newConnection, newEpoch, "full-reconnected", 20);
        var foreign = chronology(differentGame, newEpoch, "full-foreign", 20);
        var parentRef = new ExactRef("fixture/parent", 1, "1".repeat(64));
        var coreReceipt = new ExactRef("fixture/core-resume", 1, "2".repeat(64));
        var positiveAck = new ExactRef("fixture/resume-ack", 1, "3".repeat(64));
        var live = new ObservationProvenance.LiveAfterSetter(positiveAck);
        var watch = new ObservationProvenance.SameGameWatch(parentRef, coreReceipt);
        assertDoesNotThrow(() -> LifeExpiredPartialAdvanceEvidence.requireFreshBasis(live, parentRef, coreReceipt, positiveAck, resume, full));
        assertDoesNotThrow(() -> LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, coreReceipt, positiveAck, resume, reconnected));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(live, parentRef, coreReceipt, positiveAck, resume, reconnected));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, coreReceipt, positiveAck, resume, full));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, coreReceipt, positiveAck, resume, foreign));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, positiveAck, positiveAck, resume, reconnected));
        var oldCold = new ObservationProvenance.ColdAfterAcknowledgement(coreReceipt);
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(oldCold, parentRef, coreReceipt, positiveAck, resume, reconnected));
    }

    private static NativeRequestChronology chronology(TransportSession session, UUID epoch, String id, long order) {
        var packet = new NativeRequestChronology.PacketIdentity(1,"4".repeat(64));
        var time = Instant.parse("2026-11-26T11:18:01Z");
        return new NativeRequestChronology(session, epoch, id, packet, packet,
                event(order,time),event(order+1,time),event(order+2,time));
    }

    private static NativeRequestChronology.Event event(long order, Instant time) {
        return new NativeRequestChronology.Event(BigInteger.valueOf(order),time.plusNanos(order));
    }

    @Test void legacyFailedStatusAndHeartbeatFlagsProveNoExpiry() {
        var legacy = token(32, "combat_unavailable");
        var heartbeat = legacy.putObject("heartbeat");
        heartbeat.put("failure_flags", 32).put("armed", false).put("shutdown_safe", true);
        assertTrue(LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(legacy)).isEmpty());
    }

    @Test void onlyTheVersionedDisarmedSameGenerationFieldCanSupplyExpiryFacts() {
        var source = token(1 << 15, "evaluation_failure");
        source.putObject(LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_FIELD)
                .put("schema", LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_SCHEMA)
                .put("generation", 2).put("original_deadline_unix_ms", 1795691880125L).put("failure_flags", 32)
                .put("armed", false).put("shutdown_safe", true).put("access_cleanup_unknown", false);
        var actual = LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(source)).orElseThrow();
        assertEquals(BigInteger.TWO, actual.generation());
        assertEquals(1795691880125L, actual.nativeDeadlineMillis());

        assertRejected(source, "generation", 3);
        assertRejected(source, "failure_flags", 33);
        assertRejected(source, "original_deadline_unix_ms", 0);
        assertRejected(source, "armed", true);
        assertRejected(source, "shutdown_safe", false);
        assertRejected(source, "access_cleanup_unknown", true);
    }

    private static void assertRejected(ObjectNode source, String field, boolean value) {
        var changed = source.deepCopy();
        ((ObjectNode) changed.get(LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_FIELD)).put(field, value);
        assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(changed)));
    }

    private static void assertRejected(ObjectNode source, String field, int value) {
        var changed = source.deepCopy();
        ((ObjectNode) changed.get(LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_FIELD)).put(field, value);
        assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(changed)));
    }

    private static ObjectNode token(int flags, String reason) {
        var slot = new Status(State.FAILED, new CrossJsDecimalUInt64("2"), 53179368, 53180088, 53179944, 53179944, 5,
                Mode.TERMINAL_OR_SENTINEL, 0, 0, 24, 0, flags, List.of(reason), -144, 0, true, true, false, true);
        var value = StrictJson.object().put("step", ClockStatusRead.STEP).put("accepted", true).put("status", "available");
        value.set("tactical_daily_sentinel", SentinelObservation.toJson(slot));
        return value;
    }

    private static NativeActionPort.AckReceived ack(ObjectNode token) {
        byte[] raw = StrictJson.canonical(token);
        var body = new RawJson(raw);
        return new NativeActionPort.AckReceived("fixture-status", true, Optional.of(body), body, raw);
    }
}
