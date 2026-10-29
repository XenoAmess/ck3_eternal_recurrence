package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exercises the same producer/parser used by the live Root consumer server, without opening a session. */
class RootConsumerProtocolTest {
    private static final RootConsumerProtocol.Binding LIVE = new RootConsumerProtocol.Binding("synthetic-machine", "a".repeat(32));
    private static final ExactRef PLAN = new ExactRef("D:/synthetic/plan.json", 7, "b".repeat(64));
    private static final ExactRef QUOTE = new ExactRef("D:/synthetic/quote.json", 9, "c".repeat(64));
    private static final Path RUNTIME = Path.of("D:/synthetic/runtime");

    private static RootConsumerProtocol.Command command() {
        return new RootConsumerProtocol.Command(LIVE, 1, new RootConsumerProtocol.Consumer(new OriginalColdConsumerSession.ColdInputs()));
    }
    private static RootConsumerProtocol.Command decode(ObjectNode value) {
        // Preserve intentionally invalid float tokens until they reach the actual consumer parser.
        return RootConsumerProtocol.decodeCommand(value.toString().getBytes(StandardCharsets.UTF_8), LIVE, 1);
    }

    @Test void everyExistingOperationAndRestoreTransitionRoundTripsThroughTheSharedWire() {
        List<OriginalColdConsumerSession.Operation> operations = List.of(
                new OriginalColdConsumerSession.ColdInputs(), new OriginalColdConsumerSession.SdkClosure(),
                new OriginalColdConsumerSession.LoadColdInputs(RUNTIME), new OriginalColdConsumerSession.WarmInputs(RUNTIME),
                new OriginalColdConsumerSession.Prepared(RUNTIME, "d".repeat(32), "e".repeat(32)),
                new OriginalColdConsumerSession.Compose(PLAN), new OriginalColdConsumerSession.ColdOwner(PLAN, QUOTE));
        int sequence = 0;
        for (var operation : operations) {
            var expected = new RootConsumerProtocol.Command(LIVE, ++sequence, new RootConsumerProtocol.Consumer(operation));
            var actual = RootConsumerProtocol.decodeCommand(expected.wireBytes(), LIVE, sequence);
            assertEquals(expected, actual); assertArrayEquals(expected.wireBytes(), actual.wireBytes());
        }
        var begin = new RootConsumerProtocol.Command(LIVE, 8, new RootConsumerProtocol.BeginRestoreReads(5));
        assertEquals(begin, RootConsumerProtocol.decodeCommand(begin.wireBytes(), LIVE, 8));
        assertEquals("0008.request.json", begin.fileName());
    }

    @Test void ticketOrChallengeNonceAndAnotherMachineCannotSelectTheLiveSession() {
        var value = command().toJson(); value.put("session_nonce", "f".repeat(32));
        assertThrows(ContractViolationException.class, () -> decode(value));
        value.put("session_nonce", LIVE.sessionNonce()); value.put("machine_id", "another-machine");
        assertThrows(ContractViolationException.class, () -> decode(value));
        assertThrows(ContractViolationException.class, () -> new RootConsumerProtocol.Binding("synthetic-machine", "A".repeat(32)));
        assertThrows(ContractViolationException.class, () -> new RootConsumerProtocol.Binding("synthetic-machine", "a".repeat(31)));
    }

    @Test void sequenceRejectsReplayGapBooleanFloatingPointTextNullAndOutOfRangeTokens() {
        String valid = new String(command().wireBytes(), StandardCharsets.UTF_8);
        for (String token : List.of("0", "2", "17", "true", "1.0", "\"1\"", "null")) {
            byte[] raw = valid.replace("\"sequence\":1", "\"sequence\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeCommand(raw, LIVE, 1), token);
        }
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeCommand(command().wireBytes(), LIVE, 0));
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.requestFileName(17));
    }

    @Test void missingUnknownAndNullableFieldsDoNotGainCommandAuthority() {
        for (String field : List.of("schema", "machine_id", "session_nonce", "sequence", "operation", "arguments")) {
            ObjectNode value = command().toJson(); value.remove(field);
            assertThrows(ContractViolationException.class, () -> decode(value), field);
        }
        ObjectNode extra = command().toJson(); extra.put("approved", true);
        assertThrows(ContractViolationException.class, () -> decode(extra));
        ObjectNode args = command().toJson(); args.putNull("arguments");
        assertThrows(ContractViolationException.class, () -> decode(args));
        ObjectNode schema = command().toJson(); schema.put("schema", "xar.java-closed-partial-root-consumer-command/v2");
        assertThrows(ContractViolationException.class, () -> decode(schema));
    }

    @Test void operationArgumentsStillUseTheOriginalSoleStrictContract() {
        ObjectNode value = command().toJson(); value.put("operation", "SAVE");
        assertThrows(ContractViolationException.class, () -> decode(value));
        value.put("operation", "COLD_INPUTS"); value.set("arguments", StrictJson.object().put("ready", true));
        assertThrows(ContractViolationException.class, () -> decode(value));
        value.put("operation", "PREPARED"); value.set("arguments", StrictJson.object().put("runtime_root", RUNTIME.toString())
                .put("attempt_nonce", "d".repeat(32)));
        assertThrows(ContractViolationException.class, () -> decode(value));
    }

    @Test void restoreSequenceUsesStrictIntegerShapeAndDoesNotAcceptAnAuthorityFlag() {
        var begin = new RootConsumerProtocol.Command(LIVE, 1, new RootConsumerProtocol.BeginRestoreReads(1));
        String valid = new String(begin.wireBytes(), StandardCharsets.UTF_8);
        for (String token : List.of("0", "17", "true", "5.0", "\"5\"", "null")) {
            byte[] raw = valid.replace("\"prepared_sequence\":1", "\"prepared_sequence\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeCommand(raw, LIVE, 1), token);
        }
        ObjectNode value = command().toJson(); value.put("operation", "BEGIN_RESTORE_READS");
        value.set("arguments", StrictJson.object().put("prepared_sequence", 1).put("qualified", true));
        assertThrows(ContractViolationException.class, () -> decode(value));
    }

    @Test void closeRoundTripCannotBorrowAnotherSessionOrCarryCommandFields() {
        var close = new RootConsumerProtocol.Close(LIVE);
        assertEquals(close, RootConsumerProtocol.decodeClose(close.wireBytes(), LIVE));
        assertEquals("close.json", close.fileName());
        ObjectNode wrong = close.toJson(); wrong.put("session_nonce", "f".repeat(32));
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeClose(StrictJson.canonical(wrong), LIVE));
        ObjectNode extra = close.toJson(); extra.put("sequence", 1);
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeClose(StrictJson.canonical(extra), LIVE));
        ObjectNode missing = close.toJson(); missing.remove("machine_id");
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeClose(StrictJson.canonical(missing), LIVE));
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeClose(command().wireBytes(), LIVE));
    }

    @Test void serializationReturnsIndependentBytesAndObjects() {
        var packet = command(); byte[] original = packet.wireBytes();
        byte[] changed = packet.wireBytes(); changed[0] = '[';
        packet.toJson().put("machine_id", "mutated");
        assertArrayEquals(original, packet.wireBytes()); assertEquals(packet, RootConsumerProtocol.decodeCommand(original, LIVE, 1));
    }

    @Test void duplicateFieldsTrailingDataAndOversizedPacketsFailInTheProductionParser() {
        String raw = new String(command().wireBytes(), StandardCharsets.UTF_8);
        String duplicate = raw.replace("\"sequence\":1", "\"sequence\":1,\"sequence\":1");
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeCommand(duplicate.getBytes(StandardCharsets.UTF_8), LIVE, 1));
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeCommand((raw + "true").getBytes(StandardCharsets.UTF_8), LIVE, 1));
        assertThrows(ContractViolationException.class, () -> RootConsumerProtocol.decodeCommand((" ".repeat(65537) + raw).getBytes(StandardCharsets.UTF_8), LIVE, 1));
    }

    @Test void openNativeOwnerRoundTripsWithoutAllowingJsonToSupplyAuthorityOrPreparedSuccess() {
        var open = new RootConsumerProtocol.Command(LIVE,1,new RootConsumerProtocol.OpenNativeOwner(5));
        assertEquals(open,RootConsumerProtocol.decodeCommand(open.wireBytes(),LIVE,1));
        String valid = new String(open.wireBytes(),StandardCharsets.UTF_8);
        for (String token : List.of("0","17","true","5.0","\"5\"","null")) {
            byte[] raw = valid.replace("\"prepared_sequence\":5","\"prepared_sequence\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class,() -> RootConsumerProtocol.decodeCommand(raw,LIVE,1),token);
        }
        ObjectNode changed = open.toJson();
        ((ObjectNode)changed.get("arguments")).put("root_approved",true);
        assertThrows(ContractViolationException.class,() -> decode(changed));
        ObjectNode missing = open.toJson(); ((ObjectNode)missing.get("arguments")).remove("prepared_sequence");
        assertThrows(ContractViolationException.class,() -> decode(missing));
    }
    @Test void limitedColdSessionWireCannotSupplyGameOrNativeAuthority() {
        var open=new RootConsumerProtocol.Command(LIVE,1,new RootConsumerProtocol.OpenColdSession(5));
        assertEquals(open,RootConsumerProtocol.decodeCommand(open.wireBytes(),LIVE,1));
        var extra=open.toJson(); ((ObjectNode)extra.get("arguments")).put("game_approved",true);
        assertThrows(ContractViolationException.class,()->decode(extra));
        var wrong=open.toJson(); ((ObjectNode)wrong.get("arguments")).put("prepared_sequence",5.0);
        assertThrows(ContractViolationException.class,()->decode(wrong));
    }
}
