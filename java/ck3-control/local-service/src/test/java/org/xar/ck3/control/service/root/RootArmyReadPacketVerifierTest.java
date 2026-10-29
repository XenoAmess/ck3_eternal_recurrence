package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalOriginalInputs;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads;

/** Real transport encoders/parsers on software packet DATA; no receive chronology is invented. */
final class RootArmyReadPacketVerifierTest {
    @TempDir Path temporary;
    private static final String ID = "army-packet-data";
    private static final BigInteger REVISION = new BigInteger("18446744073709551615");
    private static final RawJson EMPTY = new RawJson(new byte[]{'{','}'});
    private static ArmyTypes.Context context() {
        var ref = new ExactRef("software-army-packet-data", 1, "a".repeat(64));
        var source = new G2Source("software-army-packet-data", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(77)), "native:" + REVISION, BigInteger.ONE, "army-packet-data-episode");
        return new ArmyTypes.Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "army-packet-data-session", Instant.parse("2026-10-25T00:00:00Z"));
    }
    private static PlanningReadReceipt receipt(OperationKey operation, RawJson args, byte[] outbound, byte[] packet,
            RawJson payload, RawJson result) {
        var context = context();
        var request = new PlanningReadRequest(context.before(), context.source(), context.sessionId(), operation,
                DriverJson.object(args.bytes(), DriverJson.MAX_NATIVE_BYTES), context.deadline());
        var guard = new GuardEvidence(context.before(), context.source(), context.sessionId(), BigInteger.ONE, operation,
                context.source().sourceRef(), context.source().sourceRef(), "software-packet-data-only", Instant.parse("2026-10-24T00:00:00Z"), context.deadline());
        var before = new PlanningReadGuard(guard, true, true, true, "b".repeat(64));
        var ack = new NativeActionPort.AckReceived(ID, true, Optional.of(result), payload, packet,
                Optional.of(new NativeActionPort.OutboundPacket(ID, outbound)));
        return new PlanningReadReceipt(request, "software-packet-data-only", ID, before, before, ack);
    }
    private static RawJson result() { return new RawJson(StrictJson.canonical(StrictJson.object().put("query_sequence", REVISION).put("available", true))); }
    private static RawJson payload(RawJson result) {
        var row = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", ID).put("ok", true);
        row.set("result", StrictJson.parse(result.bytes())); return new RawJson(StrictJson.canonical(row));
    }
    private static PlanningReadReceipt valid(OperationKey operation, RawJson args) throws Exception {
        var result = result(); var payload = payload(result);
        return receipt(operation, args, NativeWire.execute(ID, operation.value(), REVISION, args.bytes()), NativeWire.packet(payload.bytes()), payload, result);
    }
    @Test void actualWireEncodeDecodeKeepsAllFiveReadPacketsButNeverMintsReceiveCustody() throws Exception {
        for (String literal : List.of("query-province-local-siege-v1-73", "query-defender-de-jure-exit-terms-v1-77",
                "query-war-prisoner-release-pairs-v1-77", "query-raiktor-war-bound-loss-cleanup-v1-77", "query-h2743-preaction-existing-truce-v1")) {
            var operation = new OperationKey(literal); var original = valid(operation, EMPTY);
            RootArmyReadPacketVerifier.requirePackets(context(), operation, EMPTY, original);
            var missing = assertThrows(IllegalArgumentException.class, () -> RootArmyReadPacketVerifier.require(context(), operation, EMPTY, original));
            assertTrue(missing.getMessage().contains("custody"));
            assertTrue(original.original().custody().isEmpty());
        }
    }
    @Test void exactOutboundFieldsAndOriginalByteTokensCannotBorrowEquivalentOrForeignData() throws Exception {
        var operation = new OperationKey("query-province-local-siege-v1-73");
        var args = new RawJson(StrictJson.canonical(StrictJson.object().put("expected_native_revision", REVISION)));
        var original = valid(operation, args);
        RootArmyReadPacketVerifier.requirePackets(context(), operation, args, original);
        assertThrows(IllegalArgumentException.class, () -> RootArmyReadPacketVerifier.requirePackets(context(), operation, EMPTY, original));
        var result = result(); var payload = payload(result);
        for (byte[] outbound : List.of(NativeWire.execute(ID, operation.value(), BigInteger.ONE, args.bytes()),
                NativeWire.execute(ID, "query-province-local-siege-v1-74", REVISION, args.bytes()),
                NativeWire.executePrivateQuery(ID, operation.value(), REVISION, args.bytes()))) {
            var changed = receipt(operation, args, outbound, original.original().originalPacket(), payload, result);
            assertThrows(IllegalArgumentException.class, () -> RootArmyReadPacketVerifier.requirePackets(context(), operation, args, changed));
        }
        var alteredToken = new RawJson(StrictJson.canonical(StrictJson.object().put("query_sequence", 1).put("available", true)));
        var changed = receipt(operation, args, original.original().outbound().orElseThrow().originalPacket(), original.original().originalPacket(), payload, alteredToken);
        assertThrows(IllegalArgumentException.class, () -> RootArmyReadPacketVerifier.requirePackets(context(), operation, args, changed));
        byte[] malformed = original.original().originalPacket(); malformed[0] ^= 1;
        var badFrame = receipt(operation, args, original.original().outbound().orElseThrow().originalPacket(), malformed, payload, result);
        assertThrows(java.io.UncheckedIOException.class, () -> RootArmyReadPacketVerifier.requirePackets(context(), operation, args, badFrame));
    }
    @Test void actualOriginalLocalSiegeProducersCrossTransportParserNormalizerAndPublicSerde() throws Exception {
        var corpus = ArmyWarSupplementalOriginalInputs.capture(temporary); int checked = 0;
        for (var vector : corpus.path("cases")) {
            if (!vector.path("kind").textValue().equals("local")) continue;
            checked++;
            var snapshot = vector.path("before"); var nativeResult = new RawJson(StrictJson.canonical(vector.path("raw")));
            var source = context().source(); var nativeRevision = snapshot.path("native_revision").bigIntegerValue();
            var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(snapshot.path("played_character").path("character_id").bigIntegerValue(), nativeRevision, snapshot.path("date_raw").bigIntegerValue()), snapshot.path("snapshot_id").textValue(), snapshot.path("revision").bigIntegerValue(), snapshot.path("episode_run_id").textValue());
            var identity = new ObservationIdentity(source.machineId(), context().before().game(), frame, 1);
            var operation = new OperationKey(vector.path("raw").path("step").textValue());
            var observations = new PlanningObservation(DriverJson.object(StrictJson.canonical(snapshot), DriverJson.MAX_NATIVE_BYTES), List.of(), Set.of(), Set.of(ArmyWarSupplementalReads.capability(ArmyWarSupplementalReads.Kind.LOCAL_SIEGE)), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
            var selected = new ArmyWarSupplementalReads.Selection(new PlanningRequest(identity, source, "original-local-software-data", context().deadline(), observations), operation);
            var actual = selected.context(); var args = ArmyWarSupplementalReads.arguments(selected);
            var request = new PlanningReadRequest(identity, source, actual.sessionId(), operation, args, actual.deadline());
            var guard = new GuardEvidence(identity, source, actual.sessionId(), snapshot.path("diagnostics").path("connection_generation").bigIntegerValue(), operation, source.sourceRef(), source.sourceRef(), "original-local-software-data", Instant.parse("2026-10-24T00:00:00Z"), actual.deadline());
            var bound = new PlanningReadGuard(guard, true, true, true, "b".repeat(64));
            var payload = payload(nativeResult);
            var ack = new NativeActionPort.AckReceived(ID, true, Optional.of(nativeResult), payload, NativeWire.packet(payload.bytes()), Optional.of(new NativeActionPort.OutboundPacket(ID, NativeWire.execute(ID, operation.value(), nativeRevision, EMPTY.bytes()))));
            var receipt = new PlanningReadReceipt(request, "original-local-software-data", ID, bound, bound, ack);
            RootArmyReadPacketVerifier.requirePackets(actual, operation, EMPTY, receipt);
            assertThrows(IllegalArgumentException.class, () -> RootArmyReadPacketVerifier.require(actual, operation, EMPTY, receipt), "packet fixture must never invent receive chronology");
            var normalized = ArmyWarSupplementalReadCodec.normalizeLocalSiege(selected, nativeResult);
            assertEquals(DriverJson.object(StrictJson.canonical(vector.path("expected")), DriverJson.MAX_NATIVE_BYTES), DriverJson.object(normalized.normalizedResult().bytes(), DriverJson.MAX_NATIVE_BYTES));
            var publicResult = ArmyWarSupplementalReadCodec.fullDriverResult(normalized);
            assertEquals(publicResult, new RawJson(DriverJson.encode(DriverJson.fromNode(StrictJson.parse(publicResult.bytes())))));
            assertEquals(vector.path("raw").path("query_sequence").bigIntegerValue().toString(), StrictJson.parse(publicResult.bytes()).path("query_sequence").textValue());
            assertEquals(nativeResult, normalized.nativeResult());
        }
        assertEquals(8, checked, "all eight real local-siege original producer cases are mandatory");
    }
}
