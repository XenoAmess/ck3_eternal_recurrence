package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
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
import org.xar.ck3.control.contracts.semantic.NativeFull111OrdinaryEvent;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.*;
import org.xar.ck3.control.nativebridge.CurrentFull111EventRenderer;
import org.xar.ck3.control.nativebridge.CurrentLyd;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

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
    private static final String PLANNED = "planned-renderer-21";
    private static final Instant PLANNED_UNTIL = BASE.plusSeconds(8), REFRESHED_UNTIL = BASE.plusSeconds(46);

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

    @Test void laterSameReceiverQueueUsesTheRecoveryObservationWindow() throws Exception {
        var proof = fixture(13, 129_990);
        var queue = queue(5, 130_010, false, BASE.plusSeconds(131));
        assertThrows(ContractViolationException.class, () -> proof.prove(queue));
        assertEquals(TARGET, RootFull111EventOptionEffects.requireQueue(proof.attempt(), proof.select(), proof.fresh(),
                proof.before(), proof.after(), proof.received(), queue, BASE.plusSeconds(132)).target());
        assertThrows(ContractViolationException.class, () -> RootFull111EventOptionEffects.requireQueue(proof.attempt(),
                proof.select(), proof.fresh(), proof.before(), proof.after(), proof.received(), queue, BASE.plusSeconds(130)));
    }

    @Test void recoveryKeepsTheExactUnresolvedCommandAndAcknowledgement() throws Exception {
        var proof = fixture(13);
        var guard = proof.attempt().guard();
        var expected = new ExpectedPostcondition(1, guard.observed(), guard.source(), RootFull111EventOptionEffects.SCHEMA,
                List.of(new ExpectedBoolean(new FieldKey("event_queue_absent"), true)));
        var command = new ActionCommand("event-original", guard.observed(), guard.source(), guard.sessionId(), guard.operation(),
                new OpportunityJson.Obj(java.util.Map.of()), expected, new Claims(Set.of(), Set.of(), Set.of(), Set.of()),
                BASE.plusSeconds(180));
        var pending = new ActionReceipt(1, 7, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.of(proof.attempt()), Optional.of(proof.select()), "complete queue unavailable", List.of()));
        RootFull111EventOptionEffects.requirePendingOriginal(pending, command, proof.attempt(), proof.select());
        var noAcknowledgement = new ActionReceipt(1, 7, command, pending.bodySha256(),
                new ActionState.Unknown(Optional.of(proof.attempt()), Optional.empty(), "write outcome unavailable", List.of()));
        assertThrows(ContractViolationException.class, () ->
                RootFull111EventOptionEffects.requirePendingOriginal(noAcknowledgement, command, proof.attempt(), proof.select()));
        var differentAcknowledgement = selectAck(request(Action.SELECT, BASE.plusSeconds(30)), 4, 13);
        assertThrows(ContractViolationException.class, () ->
                RootFull111EventOptionEffects.requirePendingOriginal(pending, command, proof.attempt(), differentAcknowledgement));
    }

    @Test void failedIndependentReadKeepsItsActualAckAndOptionalFrameAsPendingEvidence() throws Exception {
        var proof = fixture(13);
        var pendingArchive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(
                ActionPorts.OutcomeArchive.class.getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class},
                (proxy, method, arguments) -> switch (method.getName()) {
                    case "preserve" -> {
                        assertSame(proof.fresh(), arguments[0]);
                        yield ref(4);
                    }
                    case "preserveNativeFrame" -> {
                        assertSame(proof.after(), arguments[0]);
                        yield ref(5);
                    }
                    default -> throw new AssertionError(method);
                });
        var originalFailure = new NativeFreshSnapshotPort.Unavailable(proof.fresh(), "original frame missing at ACK");
        var missing = RootFull111EventOptionEffects.pendingAfterRead(proof.attempt(), originalFailure.reason(), pendingArchive, originalFailure);
        assertEquals(List.of(proof.attempt().guard().nativeEvidence(), ref(4)),
                assertInstanceOf(ActionPorts.Pending.class, missing.result()).evidence());
        assertTrue(missing.compatibleResult().isEmpty());

        var invalidFrame = new NativeFreshSnapshotPort.Unavailable(proof.fresh(), "original frame rejected",
                Optional.of(proof.after()), Optional.of(proof.received()));
        var withFrame = RootFull111EventOptionEffects.pendingAfterRead(proof.attempt(), invalidFrame.reason(), pendingArchive, invalidFrame);
        assertEquals(List.of(proof.attempt().guard().nativeEvidence(), ref(4), ref(5)),
                assertInstanceOf(ActionPorts.Pending.class, withFrame.result()).evidence());
        assertTrue(withFrame.compatibleResult().isEmpty());
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

    @Test void acceptsTheSameStockSourceAfterPlanningEvidenceExpiresWithinTheOrdinaryCommand() throws Exception {
        var fixture = preparedSelection();
        var planned = plannedRenderer(false);
        var renewed = refreshedRenderer("first stock choice", false, 10, EPOCH);
        assertEquals(PLANNED_UNTIL, CurrentFull111EventOption.rendererDeadline(planned));
        assertEquals(REFRESHED_UNTIL, CurrentFull111EventOption.rendererDeadline(renewed));
        fixture.verify(BASE.plusSeconds(60), planned, renewed, fixture.selected());
    }

    @Test void independentPreparedLifetimeCoversDurablePublicationAfterRendererExpires() throws Exception {
        var planned = plannedRenderer(false);
        var rendered = refreshedRenderer("first stock choice", false, 10, EPOCH);
        var leased = preparedSelection(BASE.plusSeconds(90));
        var originalSelect = selectAck(leased.selection(), 4, 70_000);
        leased.verify(BASE.plusSeconds(90), planned, rendered, originalSelect);
        assertThrows(ContractViolationException.class, () ->
                leased.verify(BASE.plusSeconds(90), planned, rendered, selectAck(leased.selection(), 4, 90_000)));
        assertThrows(ContractViolationException.class, () ->
                leased.verify(BASE.plusSeconds(80), planned, rendered, originalSelect));
        var outOfBound = preparedSelection(BASE.plusMillis(100_001));
        assertThrows(ContractViolationException.class, () -> outOfBound.verify(BASE.plusSeconds(120), planned,
                rendered, selectAck(outOfBound.selection(), 4, 70_000)));
    }

    @Test void rejectsDriftEarlierVisibleOptionAndForeignOrReusedRendererLineage() throws Exception {
        var fixture = preparedSelection();
        var planned = plannedRenderer(false);
        var selected = fixture.selected();
        var commandUntil = BASE.plusSeconds(60);
        var changedText = refreshedRenderer("changed stock choice", false, 10, EPOCH);
        assertThrows(ContractViolationException.class, () -> fixture.verify(commandUntil, planned, changedText, selected));
        var foreign = refreshedRenderer("first stock choice", false, 10, new UUID(22, 43));
        assertThrows(ContractViolationException.class, () -> fixture.verify(commandUntil, planned, foreign, selected));
        var reused = refreshedRenderer("first stock choice", false, 8, EPOCH);
        assertThrows(ContractViolationException.class, () -> fixture.verify(commandUntil, planned, reused, selected));
        var earlierVisible = refreshedRenderer("first stock choice", true, 10, EPOCH);
        var earlierVisibleAtPlanning = plannedRenderer(true);
        assertThrows(ContractViolationException.class, () -> fixture.verify(commandUntil, earlierVisibleAtPlanning, earlierVisible, selected));
    }

    @Test void rejectsExpiredNativeWriteEvenWithLiveOrdinaryCommandAndRefusesLateLeaseBeyondCommand() throws Exception {
        var fixture = preparedSelection();
        var planned = plannedRenderer(false);
        var renewed = refreshedRenderer("first stock choice", false, 10, EPOCH);
        assertThrows(ContractViolationException.class, () -> fixture.verify(BASE.plusSeconds(45), planned, renewed, fixture.selected()));
        var expired = selectAck(fixture.selection(), 4, 46_000);
        assertThrows(ContractViolationException.class, () -> fixture.verify(BASE.plusSeconds(60), planned, renewed, expired));
        var quotePastExpiry = renderer(PLANNED, PLANNED_UNTIL, "first stock choice", false, 8, 1, 8_000, EPOCH);
        assertThrows(ContractViolationException.class, () -> fixture.verify(BASE.plusSeconds(60), quotePastExpiry, renewed, fixture.selected()));
        var extendedCutoff = BASE.plusMillis(47_001);
        var extended = preparedSelection(extendedCutoff);
        var rendererWithExtendedLease = renderer(RENDERER, extendedCutoff, "first stock choice", false, 10, 2, 39_000, EPOCH);
        assertThrows(ContractViolationException.class, () -> extended.verify(BASE.plusSeconds(60), planned, rendererWithExtendedLease, extended.selected()));
    }

    private static Fixture fixture(int afterRevision) throws IOException {
        return fixture(afterRevision, 20);
    }

    private static Fixture fixture(int afterRevision, int freshEntered) throws IOException {
        var request = request(Action.SELECT, BASE.plusSeconds(30));
        var nativeRequest = request.selectionRequest();
        var select = selectAck(request, 3, 10);
        var identity = new ObservationIdentity(SESSION.machineId(), SESSION.game(), new ProposalFrame(
                new Frame(BigInteger.valueOf(ACTOR), REVISION, BigInteger.valueOf(DATE)), "native:12", BigInteger.ONE, "event-software"), 1);
        var source = new G2Source(identity.machineId(), BASE.toString(), BUILD.executableSha256(), ref(1));
        var guard = new GuardEvidence(identity, source, SESSION.sessionId(), SESSION.connectionGeneration(),
                new OperationKey(Action.SELECT.step()), ref(1), ref(2), "fixture", BASE, request.deadline());
        var attempt = new Attempt(SELECT, BASE, guard, nativeRequest);
        var received = event(freshEntered + 2);
        var freshResult = StrictJson.object().put("schema", NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id", FRESH)
                .put("snapshot_id", "native:" + afterRevision).put("revision", afterRevision);
        var fresh = ack(FRESH, NativeWire.execute(FRESH, NativeFreshSnapshotPort.STEP, BigInteger.ZERO, new byte[]{'{', '}'}),
                freshResult, freshEntered, freshEntered + 4);
        return new Fixture(attempt, select, fresh, snapshot("", 12, event(8)), snapshot(FRESH, afterRevision, received), received);
    }

    private static Request request(Action action, Instant until) {
        boolean queue = action == Action.QUERY_QUEUE;
        boolean leased = action != Action.PREPARE;
        return new Request(action, new CoreFrame.Partial(BUILD, new CoreFrame.Prefix(DATE, 1, true, 0, true, true, ACTOR, true)),
                TARGET, new Lineage(REVISION, RENDERER, BigInteger.valueOf(3), BigInteger.TEN,
                    leased ? Optional.of(PREPARE) : Optional.empty(), leased ? BigInteger.ONE : BigInteger.ZERO,
                    queue ? Optional.of(SELECT) : Optional.empty(), queue ? BigInteger.TWO : BigInteger.ZERO), until);
    }

    private static PreparedSelection preparedSelection() throws IOException {
        return preparedSelection(REFRESHED_UNTIL);
    }

    private static PreparedSelection preparedSelection(Instant cutoff) throws IOException {
        var selection = request(Action.SELECT, cutoff);
        var prepare = request(Action.PREPARE, cutoff);
        var prepareAck = ack(PREPARE, prepare.readPacket(PREPARE), option(Action.PREPARE, 3, false), 40_000, 40_002);
        return new PreparedSelection(selection, prepareAck, selectAck(selection, 4, 41_000));
    }

    private static AckReceived selectAck(Request select, int ticket, int order) throws IOException {
        var outbound = NativeWire.execute(SELECT, Action.SELECT.step(), REVISION, select.selectionRequest().additionalFields().bytes());
        return ack(SELECT, outbound, option(Action.SELECT, ticket, false), order, order + 2);
    }

    private static AckReceived plannedRenderer(boolean earlierVisible) throws IOException {
        return renderer(PLANNED, PLANNED_UNTIL, "first stock choice", earlierVisible, 8, 1, 10, EPOCH);
    }

    private static AckReceived refreshedRenderer(String text, boolean earlierVisible, int querySequence, UUID epoch) throws IOException {
        return renderer(RENDERER, REFRESHED_UNTIL, text, earlierVisible, querySequence, 2, 39_000, epoch);
    }

    private static AckReceived renderer(String id, Instant until, String text, boolean earlierVisible, int querySequence,
            int ticket, int order, UUID epoch) throws IOException {
        var common = option(Action.PREPARE, ticket, false);
        var result = StrictJson.object().put("schema", "ck3.full111.ordinary_event_renderer_result.v1").put("game_version", BUILD.version())
                .put("executable_sha256", BUILD.executableSha256()).put("adapter_id", BUILD.coreFrameAdapterId())
                .put("backend", "ck3-1.21.0.3-native-application-main-lyd").put("action", CurrentLyd.Action.QUERY_EVENTS.wire())
                .put("status", "available").put("source_available", true).put("cleanup_known", true).put("addresses_redacted", true)
                .put("provider_generation", "3").put("query_sequence", Integer.toString(querySequence)).putNull("unavailable_reason");
        result.set("facts_before", common.get("facts_before"));
        result.set("owner", common.get("owner"));
        var options = result.putObject("source").put("instance_id", INSTANCE).put("recipient_character_id", ACTOR)
                .put("definition_key", TARGET.definitionKey()).put("authored_option_count", 5).putArray("options");
        options.addObject().put("authored_option_index", 1).put("native_can_select", true).put("widget_visible", earlierVisible)
                .put("widget_enabled", false).put("text", "earlier stock choice").put("disabled_reason", "blocked");
        options.addObject().put("authored_option_index", TARGET.authoredOptionIndex()).put("native_can_select", true)
                .put("widget_visible", true).put("widget_enabled", true).put("text", text).put("disabled_reason", "");
        var outbound = CurrentFull111EventRenderer.queryPacket(id, request(Action.PREPARE, until).core(), INSTANCE, until);
        return ack(id, outbound, result, order, order + 2, epoch);
    }

    private static AckReceived queue(int ticket, int order, boolean present, Instant until) throws IOException {
        return ack(QUEUE, request(Action.QUERY_QUEUE, until).readPacket(QUEUE), option(Action.QUERY_QUEUE, ticket, present), order, order + 2);
    }

    private static ObjectNode option(Action action, int ticket, boolean present) {
        boolean select = action == Action.SELECT;
        var result = StrictJson.object().put("schema", CurrentFull111EventOption.RESULT_SCHEMA).put("game_version", BUILD.version())
                .put("executable_sha256", BUILD.executableSha256()).put("adapter_id", BUILD.coreFrameAdapterId())
                .put("backend", "ck3-1.21.0.3-native-application-main-lyd").put("action", action.name().toLowerCase(java.util.Locale.ROOT))
                .put("status", select ? "selection_dispatched" : "available").put("source_available", true).put("cleanup_known", true)
                .put("effect_attempted", select).put("native_returned", select).put("addresses_redacted", true).putNull("unavailable_reason");
        result.putObject("facts_before").put("date_raw", DATE).put("speed", 1).put("paused", true).put("local_player_id", 0)
                .put("map_ready", true).put("has_played_character", true).put("played_character_id", ACTOR).put("played_character_alive", true);
        result.putObject("owner").put("connection_generation", "21").put("ticket_sequence", Integer.toString(ticket))
                .put("pump_epoch", "14").put("thread_id", 3);
        result.putObject("target").put("instance_id", INSTANCE).put("recipient_character_id", ACTOR)
                .put("definition_key", TARGET.definitionKey()).put("authored_option_index", TARGET.authoredOptionIndex());
        var lineage = result.putObject("lineage").put("source_revision", "12").put("renderer_request_id", RENDERER)
                .put("renderer_provider_generation", "3").put("renderer_query_sequence", "10").put("prepare_request_id", PREPARE)
                .put("lease_sequence", "1");
        if (action == Action.PREPARE) lineage.putNull("effect_request_id").put("claim_sequence", "0");
        else lineage.put("effect_request_id", SELECT).put("claim_sequence", "2");
        if (action != Action.QUERY_QUEUE) result.putNull("queue");
        else {
            var instances = result.putObject("queue").put("complete", true).put("count", present ? 1 : 0)
                    .put("target_state", present ? "present" : "absent").putArray("instance_ids");
            if (present) instances.add(INSTANCE);
        }
        return result;
    }

    private static AckReceived ack(String id, byte[] outbound, ObjectNode result, int entered, int received) throws IOException {
        return ack(id, outbound, result, entered, received, EPOCH);
    }

    private static AckReceived ack(String id, byte[] outbound, ObjectNode result, int entered, int received, UUID epoch) throws IOException {
        var envelope = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true);
        envelope.set("result", result);
        var raw = new RawJson(StrictJson.canonical(envelope));
        var packet = NativeWire.packet(raw.bytes());
        var decoded = (NativeWire.CommandResult) NativeWire.decode(packet);
        var chronology = new NativeRequestChronology(SESSION, epoch, id, PacketIdentity.of(outbound), PacketIdentity.of(packet),
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

    private record PreparedSelection(Request selection, AckReceived prepared, AckReceived selected) {
        void verify(Instant commandUntil, AckReceived planned, AckReceived renewed, AckReceived selected) throws IOException {
            RootFull111EventOptionEffects.requirePreparedRenderers(commandUntil, BASE, selection,
                    new NativeFull111OrdinaryEvent(INSTANCE, 5), planned, renewed, prepared, selected);
        }
    }

    private record Fixture(Attempt attempt, AckReceived select, AckReceived fresh, ObservedFrame before, ObservedFrame after, Event received) {
        Request prove(AckReceived queue) throws IOException {
            return RootFull111EventOptionEffects.requireQueue(attempt, select, fresh, before, after, received, queue);
        }
    }
}
