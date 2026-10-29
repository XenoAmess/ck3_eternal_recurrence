package org.xar.ck3.control.contracts.projection;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;

final class ProjectionPayloadSpanTest {
    private static final ProjectionOperation OP = ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE;
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ProjectionCall call(byte[] payload) { return new ProjectionCall(new ProjectionCall.Identity("payload-span", OP), ProjectionJson.object(payload, ProjectionJson.MAX_BYTES)); }
    @Test void encodedOriginalPayloadRetainsEveryLeadingAndTrailingJsonWhitespaceByte() {
        for (String payload : List.of("{}", " \t\r\n{}\r\n\t ", " \n{\"text\":\"汉字\",\"nested\":{}} \r\n")) {
            byte[] original = bytes(payload);
            assertArrayEquals(original, ProjectionWire.decodeCall(ProjectionWire.encodeCall(call(original))).payload().bytes());
        }
    }
    @Test void registeredBudgetCountsOriginalRawBytesAtTheExactBoundaryAndBeforeDecode() {
        byte[] atLimit = bytes("{}" + " ".repeat(65534)), over = bytes(" \n{}" + " ".repeat(65533));
        assertEquals(65536, atLimit.length); assertEquals(65537, over.length);
        AtomicInteger decoded = new AtomicInteger();
        assertInstanceOf(ProjectionResult.Succeeded.class, dispatcher(65536, decoded).dispatch(ProjectionWire.encodeCall(call(atLimit))));
        assertEquals(1, decoded.get());
        var refused = assertInstanceOf(ProjectionResult.Rejected.class, dispatcher(65536, decoded).dispatch(ProjectionWire.encodeCall(call(over))));
        assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE, refused.error().code()); assertEquals(1, decoded.get());
        assertInstanceOf(ProjectionResult.Succeeded.class, dispatcher(1 << 20, decoded).dispatch(ProjectionWire.encodeCall(call(over))));
        assertEquals(2, decoded.get());
    }
    @Test void fieldOrderAndEscapedFieldSpellingKeepOnlyThePayloadValueSpan() {
        String field = "pay" + (char) 92 + "u006c" + "oad";
        String raw = "{\"" + field + "\" : \t{}\r\n, \"operation\":\"" + OP.wire() + "\",\"request_id\":\"payload-span\",\"schema_version\":1,\"schema\":\"" + ProjectionCall.SCHEMA + "\"}";
        assertArrayEquals(bytes(" \t{}\r\n"), ProjectionWire.decodeCall(bytes(raw)).payload().bytes());
        assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeCall(bytes(raw + "{}")));
    }
    private static ProjectionDispatcher dispatcher(int budget, AtomicInteger decoded) {
        ProjectionPort<byte[], Integer> port = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public int inputMaximumBytes() { return budget; }
            @Override public int outputMaximumBytes() { return 65536; }
            @Override public byte[] decode(byte[] raw) { decoded.incrementAndGet(); return raw; }
            @Override public Integer project(byte[] raw) { return raw.length; }
            @Override public byte[] encode(Integer result) { return bytes("{}"); }
        };
        return new ProjectionDispatcher(List.of(RegisteredProjection.of(port)));
    }
}
