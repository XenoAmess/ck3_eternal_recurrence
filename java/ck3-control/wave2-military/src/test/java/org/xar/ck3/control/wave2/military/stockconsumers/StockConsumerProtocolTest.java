package org.xar.ck3.control.wave2.military.stockconsumers;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class StockConsumerProtocolTest {
    @Test void sequenceRequiresActualIntegerAndClosedFields() {
        String base = "{\"kind\":\"request\",\"sequence\":1,\"operation\":\"UPDATER_REJECT\",\"row\":null,\"risk\":null,\"raw_json\":\"{}\"}";
        assertEquals(1, ProbeCompiledStockConsumers.decodeMessage(bytes(base)).sequence());
        for (String token : new String[]{"true", "1.0", "1e0", "\"1\"", "0", "2147483648"}) {
            assertThrows(IllegalArgumentException.class, () -> ProbeCompiledStockConsumers.decodeMessage(bytes(
                    base.replace("\"sequence\":1", "\"sequence\":" + token))));
        }
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledStockConsumers.decodeMessage(bytes(
                base.replace("\"kind\":\"request\"", "\"kind\":\"request\",\"extra\":null"))));
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledStockConsumers.decodeMessage(bytes(base + "{}")));
    }
    @Test void rawFloatTokensReachRealSourceFrameDecoderUnchanged() {
        String raw = "{\"schema_version\":1.0}";
        var request = StrictJson.object();
        request.put("kind", "request"); request.put("sequence", 1); request.put("operation", "UPDATER_REJECT");
        request.putNull("row"); request.putNull("risk"); request.put("raw_json", raw);
        var message = ProbeCompiledStockConsumers.decodeMessage(StrictJson.canonical(request));
        assertEquals(raw, message.rawJson());
        assertTrue(ProbeCompiledStockConsumers.dispatch(message).booleanValue());
        request.put("raw_json", "{\"schema_version\":1e0}");
        assertEquals("{\"schema_version\":1e0}", ProbeCompiledStockConsumers.decodeMessage(StrictJson.canonical(request)).rawJson());
    }
    @Test void framesAreBoundedBeforeJsonOrAllocationGrowthAndRequireLf() throws IOException {
        assertArrayEquals(bytes("{}"), ProbeCompiledStockConsumers.readFrame(new ByteArrayInputStream(bytes("{}\n")), 2));
        assertThrows(IOException.class, () -> ProbeCompiledStockConsumers.readFrame(new ByteArrayInputStream(bytes("{}\n")), 1));
        assertThrows(IOException.class, () -> ProbeCompiledStockConsumers.readFrame(new ByteArrayInputStream(bytes("{}")), 2));
        assertNull(ProbeCompiledStockConsumers.readFrame(new ByteArrayInputStream(new byte[0]), 2));
    }
    @Test void effectsCannotAcceptADifferentRiskOrNullState() {
        String malformed = "{\"kind\":\"request\",\"sequence\":1,\"operation\":\"EFFECTS\",\"row\":{},\"risk\":null,\"raw_json\":null}";
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledStockConsumers.decodeMessage(bytes(malformed)));
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledStockConsumers.decodeMessage(bytes(
                malformed.replace("\"EFFECTS\"", "\"UNSUPPORTED\""))));
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledStockConsumers.decodeMessage(
                new byte[]{(byte)0xc3, 0x28}));
    }
    @Test void opaqueFloatingSdkExtensionsReachTypedProducersUnchanged() {
        String base = "{\"status\":\"unavailable\",\"army_id\":11,\"native_carmy_id\":12}";
        for (var operation : new ProbeCompiledStockConsumers.Operation[]{
                ProbeCompiledStockConsumers.Operation.UPDATER, ProbeCompiledStockConsumers.Operation.STOCK,
                ProbeCompiledStockConsumers.Operation.RATE, ProbeCompiledStockConsumers.Operation.RISK,
                ProbeCompiledStockConsumers.Operation.EFFECTS}) {
            var expected = ProbeCompiledStockConsumers.dispatch(request(operation, base));
            for (String token : new String[]{"1.0", "1e0"}) {
                var message = request(operation, base.substring(0, base.length() - 1)
                        + ",\"opaque_sdk_extension\":" + token + "}");
                assertTrue(message.row().path("opaque_sdk_extension").isFloatingPointNumber());
                assertEquals(expected, ProbeCompiledStockConsumers.dispatch(message), operation + ":" + token);
                assertTrue(message.row().path("opaque_sdk_extension").isFloatingPointNumber());
            }
        }
    }
    @Test void nonIntegralDeclaredIdsStillReachAndFailTheirActualDecoder() {
        for (var operation : new ProbeCompiledStockConsumers.Operation[]{
                ProbeCompiledStockConsumers.Operation.UPDATER, ProbeCompiledStockConsumers.Operation.STOCK,
                ProbeCompiledStockConsumers.Operation.RATE, ProbeCompiledStockConsumers.Operation.RISK}) {
            for (String token : new String[]{"true", "1.0", "1e0", "\"11\"", "2147483648"}) {
                var message = request(operation,
                        "{\"status\":\"unavailable\",\"army_id\":" + token + ",\"native_carmy_id\":12}");
                assertThrows(IllegalArgumentException.class, () -> ProbeCompiledStockConsumers.dispatch(message),
                        operation + ":" + token);
            }
        }
    }
    private static ProbeCompiledStockConsumers.Message request(
            ProbeCompiledStockConsumers.Operation operation, String row) {
        String risk = operation == ProbeCompiledStockConsumers.Operation.EFFECTS
                ? new String(StrictJson.canonical(ProbeCompiledStockConsumers.dispatch(
                        request(ProbeCompiledStockConsumers.Operation.RISK, row))), StandardCharsets.UTF_8)
                : "null";
        return ProbeCompiledStockConsumers.decodeMessage(bytes(
                "{\"kind\":\"request\",\"sequence\":1,\"operation\":\"" + operation.name()
                        + "\",\"row\":" + row + ",\"risk\":" + risk + ",\"raw_json\":null}"));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
