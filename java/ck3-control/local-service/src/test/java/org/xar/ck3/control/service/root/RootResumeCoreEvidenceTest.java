package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.FullSnapshotClockControlResult;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original packet shape and chronology fixtures for the installed verifier, without a Game or writer. */
final class RootResumeCoreEvidenceTest {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final Instant TIME = Instant.parse("2026-11-26T11:09:00Z");
    private static final Instant END = TIME.plusSeconds(15);
    private static final BigInteger START = BigInteger.valueOf(53179368);
    private static final BigInteger TARGET = START.add(AdvancePlan.DAY.multiply(BigInteger.TEN));
    private static final TransportSession SESSION = new TransportSession("fixture-machine",
            new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), BigInteger.ONE, "fixture-session");
    private static final UUID EPOCH = UUID.fromString("8c799220-1674-4572-9dca-7a0e40d20b45");

    @Test void theIndependentCoreConfirmsOnlyTheRunningOriginalActorWithinItsWindow() throws IOException {
        var fixture = fixture();
        var running = prefix(START.add(AdvancePlan.DAY).intValueExact(), false, 73);
        assertEquals(running, fixture.verify(core(running, SESSION, EPOCH, 20), END));
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(prefix(START.intValueExact(), true, 73), SESSION, EPOCH, 20), END));
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(prefix(START.intValueExact(), false, 74), SESSION, EPOCH, 20), END));
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(prefix(TARGET.intValueExact() + 24, false, 73), SESSION, EPOCH, 20), END));
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(running, SESSION, EPOCH, 20), TIME.plusSeconds(3)));
    }

    @Test void aNewConnectionOrAnEarlierReadCannotCompleteTheOriginalResume() throws IOException {
        var fixture = fixture();
        var running = prefix(START.intValueExact(), false, 73);
        var reconnected = new TransportSession(SESSION.machineId(), SESSION.game(), BigInteger.TWO, SESSION.sessionId());
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(running, reconnected, EPOCH, 20), END));
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(running, SESSION, UUID.randomUUID(), 20), END));
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(running, SESSION, EPOCH, 10), END));
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(core(running, SESSION, EPOCH, 20), END.plusNanos(1)));
    }

    private record Fixture(ActionCommand parent, ActionCommand child, ActionState.Attempt attempt, AckReceived resume,
            DriverObservationAssembler.Complete before) {
        CoreFrame.Prefix verify(AckReceived sample, Instant deadline) throws IOException {
            return RootResumeCoreEvidence.verify(parent, child, attempt, resume, sample, deadline, before);
        }
    }

    private static Fixture fixture() throws IOException {
        var sourceRef = new ExactRef("test/source", 1, "1".repeat(64));
        var source = new G2Source(SESSION.machineId(), TIME.toString(), BUILD.executableSha256(), sourceRef);
        var factual = new ProposalFrame(new Frame(BigInteger.valueOf(73), BigInteger.ONE, START),
                "native:1", BigInteger.ONE, "fixture-episode");
        var identity = new ObservationIdentity(SESSION.machineId(), SESSION.game(), factual, 1);
        var claims = new Claims(Set.of(),Set.of(),Set.of(),Set.of());
        var cap = new CampaignDeadline.Cap("test-campaign", CampaignDeadline.CALENDAR_PROFILE, START,
                TARGET, TARGET, TARGET.add(AdvancePlan.DAY), TARGET, CampaignDeadline.Status.ADVANCE);
        var plan = new AdvancePlan(START, TARGET, 10, 5, "fixture-campaign", false,
                AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, Optional.of(cap));
        var parent = new ActionCommand("life-fixture", identity, source, SESSION.sessionId(), new OperationKey("life-advance"),
                new OpportunityJson.Obj(Map.of(AdvancePlan.KEY, plan.json())),
                new ExpectedPostcondition(1, identity, source, AdvancePlan.OBSERVER, plan.expected()), claims, END);
        var step = new OperationKey("resume-map");
        var args = new OpportunityJson.Obj(Map.of());
        var child = new ActionCommand("resume-fixture", identity, source, SESSION.sessionId(), step, args,
                AdvancePrimitives.expected(identity, source, step, args), claims, END);
        var guard = new GuardEvidence(identity, source, SESSION.sessionId(), BigInteger.ONE, step, sourceRef, sourceRef,
                "fixture-guard", TIME, END);
        var prepared = AdvancePrimitives.prepareRequest(child, BUILD);
        var attempt = new ActionState.Attempt("resume-request", TIME, guard, prepared);
        var result = StrictJson.object().put("schema", FullSnapshotClockControlResult.SCHEMA)
                .put("game_version", BUILD.version()).put("executable_sha256", BUILD.executableSha256())
                .put("adapter_id", BUILD.coreFullAdapterId()).put("backend", BUILD.coreFullBackend()).put("step", step.value())
                .put("accepted", true).put("queue_status", "submitted").put("effect_attempted", true)
                .put("full_snapshot_before_verified", true).put("complete_snapshot", false).put("physical_save_confirmed", false);
        var resume = ack(attempt.requestId(), step.value(), BigInteger.ONE, prepared.additionalFields().bytes(), result,
                SESSION, EPOCH, 10, TIME);
        var semantic = new OpportunityJson.Obj(Map.of("paused", new OpportunityJson.Bool(true),
                "map_ready", new OpportunityJson.Bool(true), "local_player_id", new OpportunityJson.IntegerValue(BigInteger.ONE)));
        var before = new DriverObservationAssembler.Complete(identity, source, SESSION.sessionId(), BigInteger.ONE,
                semantic, sourceRef, TIME, "a".repeat(64));
        return new Fixture(parent, child, attempt, resume, before);
    }

    private static CoreFrame.Prefix prefix(int date, boolean paused, int actor) {
        return new CoreFrame.Prefix(date, 5, paused, 1, true, true, actor, true);
    }

    private static AckReceived core(CoreFrame.Prefix prefix, TransportSession session, UUID epoch, long order) throws IOException {
        var result = NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD, prefix)).bytes()));
        return ack("core-request", CoreFrame.STEP, BigInteger.ZERO, new byte[]{'{','}'}, result,
                session, epoch, order, TIME.plusSeconds(3));
    }

    private static AckReceived ack(String id, String step, BigInteger revision, byte[] fields, ObjectNode result,
            TransportSession session, UUID epoch, long order, Instant stamp) throws IOException {
        byte[] request = NativeWire.execute(id, step, revision, fields);
        var envelope = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true);
        envelope.set("result", result);
        var payload = new RawJson(StrictJson.canonical(envelope));
        byte[] response = NativeWire.packet(payload.bytes());
        var chronology = new NativeRequestChronology(session, epoch, id,
                NativeRequestChronology.PacketIdentity.of(request), NativeRequestChronology.PacketIdentity.of(response),
                new NativeRequestChronology.Event(BigInteger.valueOf(order), stamp),
                new NativeRequestChronology.Event(BigInteger.valueOf(order + 1), stamp),
                new NativeRequestChronology.Event(BigInteger.valueOf(order + 2), stamp));
        return new AckReceived(id, true, Optional.of(new RawJson(StrictJson.canonical(result))), payload, response,
                Optional.of(new NativeActionPort.OutboundPacket(id, request)), Optional.of(chronology));
    }
}
