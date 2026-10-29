package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Original fault producer -> retained typed outcome -> public exception. No Native/Game credit. */
final class GuiReadFailureTest {
    @Test void absentOriginalDoesNotInventNativeOutcome() {
        var unavailable = unavailable("actual before guard rejected this query", Optional.empty());
        var failure = GuiReadFailure.from(unavailable);
        assertSame(unavailable, failure.unavailable());
        assertTrue(failure.original().isEmpty());
        assertEquals(GuiReadFailure.Kind.NO_ORIGINAL, failure.kind());
        assertEquals(unavailable.reason(), failure.getMessage());
    }

    @Test void unknownAndZeroDispatchKeepTheirActualDifferentReasons() {
        var unknown = new NativeActionPort.Unknown("q", "actual write interrupted; result unknown", new byte[]{1}, Optional.empty());
        var unknownFailure = GuiReadFailure.from(unavailable("coordinator summary", Optional.of(unknown)));
        assertSame(unknown, unknownFailure.original().orElseThrow());
        assertEquals(GuiReadFailure.Kind.UNKNOWN, unknownFailure.kind());
        assertEquals(unknown.reason(), unknownFailure.getMessage());
        assertFalse(unknownFailure.getMessage().contains("timed out"));
        assertEquals("coordinator summary", unknownFailure.sourceReason());
        var proof = new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0,
                "actual endpoint unavailable before write", Optional.empty());
        var rejected = new NativeActionPort.RejectedBeforeDispatch("q", proof);
        var failure = GuiReadFailure.from(unavailable("coordinator summary", Optional.of(rejected)));
        assertSame(rejected, failure.original().orElseThrow());
        assertEquals(GuiReadFailure.Kind.REJECTED_BEFORE_DISPATCH, failure.kind());
        assertEquals(proof.reason(), failure.getMessage());
    }

    @Test void originalPythonRejectionProducerAgreesIncludingMissingNullAndNonStringError() throws Exception {
        ObjectNode actual = originalFaults();
        for (String key : List.of("text", "empty", "missing", "null", "boolean", "integer", "unicode")) {
            ObjectNode row = (ObjectNode) actual.get(key);
            ObjectNode top = top();
            if (row.has("error")) top.set("error", row.get("error"));
            var ack = ack(top, false);
            var failure = GuiReadFailure.from(unavailable("native query returned unavailable or an unbound ACK", Optional.of(ack)));
            assertEquals(row.get("message").textValue(), failure.getMessage(), key);
            assertEquals(GuiReadFailure.Kind.NATIVE_REFUSAL, failure.kind(), key);
            assertSame(ack, failure.original().orElseThrow(), key);
        }
    }

    @Test void malformedTopSuccessfulAckAndStructuredFaultDoNotBecomeSimpleNativeRefusal() {
        for (String corruption : List.of("request", "protocol_bool", "protocol_float", "ok_integer", "ok_true", "structured", "packet")) {
            ObjectNode top = top().put("error", "native actual error");
            switch (corruption) {
                case "request" -> top.put("request_id", "foreign");
                case "protocol_bool" -> top.put("protocol_version", true);
                case "protocol_float" -> top.put("protocol_version", 1.0);
                case "ok_integer" -> top.put("ok", 0);
                case "ok_true" -> top.put("ok", true);
                case "structured" -> top.putObject("typed_query_failure_v1").put("reason", "actual structured domain error");
                case "packet" -> { }
                default -> throw new AssertionError(corruption);
            }
            var original = ack(top, false);
            if (corruption.equals("packet")) {
                byte[] bad = original.originalPacket(); bad[bad.length - 1] ^= 1;
                original = new NativeActionPort.AckReceived("q", false, Optional.empty(), original.originalFrame(), bad);
            }
            var failure = GuiReadFailure.from(unavailable("actual decode/binding failure", Optional.of(original)));
            assertEquals(GuiReadFailure.Kind.ACK_UNUSABLE, failure.kind(), corruption);
            assertEquals("actual decode/binding failure", failure.getMessage(), corruption);
            assertSame(original, failure.original().orElseThrow(), corruption);
        }
        assertEquals(GuiReadFailure.Kind.ACK_UNUSABLE,
                GuiReadFailure.from(unavailable("later binding failed", Optional.of(ack(top(), true)))).kind());
    }

    @Test void nativeWideNumbersNullEmptyAndDecimalTokensRemainExactInOriginal() {
        String actual = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"q\",\"ok\":false,\"error\":\"source_refused\","
                + "\"native_details\":{\"connection_generation\":18446744073709551615,\"revision\":9007199254740993,"
                + "\"explicit_null\":null,\"empty\":[],\"quote\":1.2300}}";
        byte[] body = actual.getBytes(StandardCharsets.UTF_8);
        var original = new NativeActionPort.AckReceived("q", false, Optional.empty(), new RawJson(body), packet(body));
        var failure = GuiReadFailure.from(unavailable("native unavailable", Optional.of(original)));
        assertEquals(GuiReadFailure.Kind.NATIVE_REFUSAL, failure.kind());
        assertSame(original, failure.original().orElseThrow());
        var retained = (NativeActionPort.AckReceived) failure.original().orElseThrow();
        assertArrayEquals(body, retained.originalFrame().bytes());
        assertArrayEquals(packet(body), retained.originalPacket());
        JsonNode details = StrictJson.parse(retained.originalFrame().bytes()).path("native_details");
        assertEquals(new BigInteger("18446744073709551615"), details.path("connection_generation").bigIntegerValue());
        assertEquals(new BigInteger("9007199254740993"), details.path("revision").bigIntegerValue());
        assertTrue(details.has("explicit_null") && details.get("explicit_null").isNull());
        assertFalse(details.has("absent"));
        assertEquals(0, details.path("empty").size());
        byte[] detached = retained.originalPacket(); detached[0] = 0;
        assertArrayEquals(packet(body), retained.originalPacket());
    }

    private static PlanningReadResult.Unavailable<Object> unavailable(String reason, Optional<NativeActionPort.DispatchOutcome> original) {
        return new PlanningReadResult.Unavailable<>(reason, original);
    }
    private static ObjectNode top() {
        return StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", "q").put("ok", false);
    }
    private static NativeActionPort.AckReceived ack(ObjectNode top, boolean nativeOk) {
        // Floating point malformed-protocol test retains its original JSON token without canonical coercion.
        byte[] body = top.toString().getBytes(StandardCharsets.UTF_8);
        return new NativeActionPort.AckReceived("q", nativeOk, Optional.empty(), new RawJson(body), packet(body));
    }
    private static byte[] packet(byte[] body) {
        return ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
    }

    private static ObjectNode originalFaults() throws Exception {
        Path root = required("xar.repository.root"), python = required("xar.python");
        Path source = root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").toRealPath();
        assertTrue(source.startsWith(root));
        assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603", sha(source));
        String code = """
import ast,copy,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
from xar_autoplayer.bridge.driver import BridgeUnavailableError
source=root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'bridge'/'native_driver.py'
tree=ast.parse(source.read_text(encoding='utf-8-sig'))
node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='_NativeCommandRejectedError')
scope={'BridgeUnavailableError':BridgeUnavailableError,'copy':copy,'json':json}
exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),scope)
rows={}
for key,value in [('text','state_changed'),('empty',''),('missing',None),('null',None),('boolean',False),('integer',18446744073709551615),('unicode','原生拒绝')]:
 row={} if key=='missing' else {'error':value}
 native_error=row.get('error')
 actual=scope['_NativeCommandRejectedError'](native_error if isinstance(native_error,str) else 'unknown error',native_request_id='q')
 row['message']=str(actual);rows[key]=row
print(json.dumps(rows,ensure_ascii=False,allow_nan=False))
""";
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", code, root.toString()).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        FutureTask<byte[]> output = new FutureTask<>(() -> process.getInputStream().readNBytes(65_537));
        FutureTask<byte[]> errors = new FutureTask<>(() -> process.getErrorStream().readNBytes(16_385));
        Thread.ofVirtual().start(output); Thread.ofVirtual().start(errors); process.getOutputStream().close();
        try {
            if (!process.waitFor(30, TimeUnit.SECONDS)) throw new IllegalStateException("original fault producer timed out");
            byte[] out = output.get(5, TimeUnit.SECONDS), err = errors.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || out.length > 65_536 || err.length > 16_384)
                throw new IllegalStateException("original fault producer failed: " + new String(err, StandardCharsets.UTF_8));
            assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603", sha(source));
            JsonNode node = StrictJson.parse(out); assertInstanceOf(ObjectNode.class, node); return (ObjectNode) node;
        } finally {
            if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); }
        }
    }
    private static Path required(String property) throws Exception {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IllegalStateException("required actual original source property missing: " + property);
        Path path = Path.of(value); if (!path.isAbsolute()) throw new IllegalArgumentException("absolute original source path required");
        return path.toRealPath();
    }
    private static String sha(Path source) throws Exception {
        return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
    }
}
