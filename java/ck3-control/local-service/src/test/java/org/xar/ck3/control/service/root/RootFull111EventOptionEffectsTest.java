package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionState.Attempt;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeActionPort.OutboundPacket;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.NativeRequestChronology.Event;
import org.xar.ck3.control.application.action.NativeRequestChronology.PacketIdentity;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.*;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

final class RootFull111EventOptionEffectsTest {
    private static final Instant BASE = Instant.parse("2026-11-27T04:00:00Z");
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final int ACTOR = -16777215;
    private static final int DATE = 53144328;
    private static final int INSTANCE = 7;
    private static final String RENDERER = "renderer-21", PREPARE = "prepare-21", SELECT = "select-21";
    private static final String FRESH = "fresh-21", QUEUE = "queue-21";
    private static final TransportSession SESSION = new TransportSession("event-option-software",
            new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), BigInteger.valueOf(21), "test-session");
    private static final UUID EPOCH = new UUID(21, 42);
    private static final Target TARGET = new Target(INSTANCE, ACTOR, "bookmark.1070", 4);
    private static final BigInteger REVISION = BigInteger.valueOf(12);

    @Test void requiresBothFreshFullAndCompleteAbsentQueueInOriginalOrder() throws Exception {
        var original = fixture(13);
        var queue = queue(5, 30, false, BASE.plusSeconds(60));
        assertEquals(TARGET, original.prove(queue).target());
        assertThrows(ContractViolationException.class, () -> original.prove(queue(5, 30, true, BASE.plusSeconds(60))));
        // This queue is after SELECT but was issued before the original fresh Full ACK.
        assertThrows(ContractViolationException.class, () -> original.prove(queue(5, 21, false, BASE.plusSeconds(60))));
        assertThrows(ContractViolationException.class, () -> original.prove(queue(3, 30, false, BASE.plusSeconds(60))));
        assertThrows(ContractViolationException.class, () -> original.prove(queue(5, 30, false, BASE.plusSeconds(125))));
        assertThrows(ContractViolationException.class, () -> fixture(12).prove(queue));
    }

    @Test void rejectsAnAfterPacketWithoutTheIndependentReadCorrelation() throws Exception {
        var proof = fixture(13);
        var other = snapshot("a-foreign-fresh-request", 13, proof.received());
        assertThrows(IOException.class, () -> RootFull111EventOptionEffects.requireQueue(proof.attempt(), proof.select(),
                proof.fresh(), proof.before(), other, proof.received(), queue(5, 30, false, BASE.plusSeconds(60))));
    }

    @Test void preservesDistinctReferencesAndTheExactIndependentOccurrence() {
        var select = ref(1);
        var full = ref(2);
        var queue = ref(3);
        var proof = new RootFull111EventOptionEffects.Originals(select, full, event(30), queue);
        assertEquals(proof, RootFull111EventOptionEffects.Originals.decode(proof.encode()));
        assertThrows(IllegalArgumentException.class, () -> new RootFull111EventOptionEffects.Originals(select, full, event(30), select));
        var changed = (ObjectNode) StrictJson.parse(proof.encode().bytes());
        changed.put("snapshot_order", "030");
        assertThrows(ContractViolationException.class, () -> RootFull111EventOptionEffects.Originals.decode(
                new RawJson(StrictJson.canonical(changed))));
    }

    private static Fixture fixture(int afterRevision) throws IOException {
        var request = request(Action.SELECT, BASE.plusSeconds(30));
        var nativeRequest = request.selectionRequest();
        var outbound = NativeWire.execute(SELECT, Action.SELECT.step(), REVISION, nativeRequest.additionalFields().bytes());
        var select = ack(SELECT, outbound, option(true, 3, false), 10, 12);
        var identity = new ObservationIdentity(SESSION.machineId(), SESSION.game(), new ProposalFrame(
                new Frame(BigInteger.valueOf(ACTOR), REVISION, BigInteger.valueOf(DATE)), "native:12", BigInteger.ONE, "event-software"), 1);
        var source = new G2Source(identity.machineId(), BASE.toString(), BUILD.executableSha256(), ref(1));
        var guard = new GuardEvidence(identity, source, SESSION.sessionId(), SESSION.connectionGeneration(),
                new OperationKey(Action.SELECT.step()), ref(1), ref(2), "fixture", BASE, request.deadline());
        var attempt = new Attempt(SELECT, BASE, guard, nativeRequest);
        var received = event(22);
        var freshResult = StrictJson.object().put("schema", NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id", FRESH)
                .put("snapshot_id", "native:" + afterRevision).put("revision", afterRevision);
        var fresh = ack(FRESH, NativeWire.execute(FRESH, NativeFreshSnapshotPort.STEP, BigInteger.ZERO, new byte[]{'{', '}'}),
                freshResult, 20, 24);
        return new Fixture(attempt, select, fresh, snapshot("", 12, event(8)), snapshot(FRESH, afterRevision, received), received);
    }

    private static Request request(Action action, Instant until) {
        boolean queue = action == Action.QUERY_QUEUE;
        return new Request(action, new CoreFrame.Partial(BUILD, new CoreFrame.Prefix(DATE, 1, true, 0, true, true, ACTOR, true)),
                TARGET, new Lineage(REVISION, RENDERER, BigInteger.valueOf(3), BigInteger.TEN, Optional.of(PREPARE),
                    BigInteger.ONE, queue ? Optional.of(SELECT) : Optional.empty(), queue ? BigInteger.TWO : BigInteger.ZERO), until);
    }

    private static AckReceived queue(int ticket, int order, boolean present, Instant until) throws IOException {
        return ack(QUEUE, request(Action.QUERY_QUEUE, until).readPacket(QUEUE), option(false, ticket, present), order, order + 2);
    }

    private static ObjectNode option(boolean select, int ticket, boolean present) {
        var result = StrictJson.object().put("schema", CurrentFull111EventOption.RESULT_SCHEMA).put("game_version", BUILD.version())
                .put("executable_sha256", BUILD.executableSha256()).put("adapter_id", BUILD.coreFrameAdapterId())
                .put("backend", "ck3-1.21.0.3-native-application-main-lyd").put("action", select ? "select" : "query_queue")
                .put("status", select ? "selection_dispatched" : "available").put("source_available", true).put("cleanup_known", true)
                .put("effect_attempted", select).put("native_returned", select).put("addresses_redacted", true).putNull("unavailable_reason");
        result.putObject("facts_before").put("date_raw", DATE).put("speed", 1).put("paused", true).put("local_player_id", 0)
                .put("map_ready", true).put("has_played_character", true).put("played_character_id", ACTOR).put("played_character_alive", true);
        result.putObject("owner").put("connection_generation", "21").put("ticket_sequence", Integer.toString(ticket))
                .put("pump_epoch", "14").put("thread_id", 3);
        result.putObject("target").put("instance_id", INSTANCE).put("recipient_character_id", ACTOR)
                .put("definition_key", TARGET.definitionKey()).put("authored_option_index", TARGET.authoredOptionIndex());
        result.putObject("lineage").put("source_revision", "12").put("renderer_request_id", RENDERER)
                .put("renderer_provider_generation", "3").put("renderer_query_sequence", "10").put("prepare_request_id", PREPARE)
                .put("lease_sequence", "1").put("effect_request_id", SELECT).put("claim_sequence", "2");
        if (select) result.putNull("queue");
        else {
            var instances = result.putObject("queue").put("complete", true).put("count", present ? 1 : 0)
                    .put("target_state", present ? "present" : "absent").putArray("instance_ids");
            if (present) instances.add(INSTANCE);
        }
        return result;
    }

    private static AckReceived ack(String id, byte[] outbound, ObjectNode result, int entered, int received) throws IOException {
        var envelope = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true);
        envelope.set("result", result);
        var raw = new RawJson(StrictJson.canonical(envelope));
        var packet = NativeWire.packet(raw.bytes());
        var decoded = (NativeWire.CommandResult) NativeWire.decode(packet);
        var chronology = new NativeRequestChronology(SESSION, EPOCH, id, PacketIdentity.of(outbound), PacketIdentity.of(packet),
                event(entered), event(entered + 1), event(received));
        return new AckReceived(id, true, decoded.result().token().map(value -> new RawJson(value.value())), raw, packet,
                Optional.of(new OutboundPacket(id, outbound)), Optional.of(chronology));
    }

    private static ObservedFrame snapshot(String request, int revision, Event received) throws IOException {
        var row = StrictJson.object().put("type", "state_snapshot").put("protocol_version", 1)
                .put("snapshot_id", "native:" + revision).put("revision", revision);
        if (!request.isEmpty()) row.put("read_request_id", request);
        row.putObject("state").putNull("active_event");
        byte[] packet = NativeWire.packet(StrictJson.canonical(row));
        var snapshot = (NativeWire.Snapshot) NativeWire.decode(packet);
        return new ObservedFrame(SESSION, snapshot.snapshotId(), snapshot.revision(), new RawJson(snapshot.state().value()), packet, received.observedAt());
    }

    private static Event event(int index) { return new Event(BigInteger.valueOf(index), BASE.plusMillis(index)); }
    private static ExactRef ref(int index) { return new ExactRef("D:/software-original-" + index, 1, Integer.toString(index).repeat(64)); }

    private record Fixture(Attempt attempt, AckReceived select, AckReceived fresh, ObservedFrame before, ObservedFrame after, Event received) {
        Request prove(AckReceived queue) throws IOException {
            return RootFull111EventOptionEffects.requireQueue(attempt, select, fresh, before, after, received, queue);
        }
    }
}
