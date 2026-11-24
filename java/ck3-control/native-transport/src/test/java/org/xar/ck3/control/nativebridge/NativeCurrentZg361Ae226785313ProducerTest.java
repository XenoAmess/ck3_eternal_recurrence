package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact C++ NoGame DATA originals, not a Game exchange, actual payment or script-verifier proof. */
final class NativeCurrentZg361Ae226785313ProducerTest {
    private static final BigInteger MAX = NativeWire.UINT64_MAX;
    private static final String OUTPUT = "xar.zg361.ae2.java.requests.output.directory";
    private static final ConcurrentMap<CurrentZg361Ae2.Action,ObjectNode> EXPORTED = new ConcurrentHashMap<>();

    private static byte[] resource(String name, int size, String sha) throws Exception {
        try (var in = NativeCurrentZg361Ae226785313ProducerTest.class.getResourceAsStream(
                "/current267-zg361-ae2-cpp-a1590/"+name)) {
            if (in == null) throw new IOException("Original C++ resource missing: "+name);
            byte[] bytes = in.readAllBytes(); assertEquals(size,bytes.length,name);
            assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),name);
            return bytes;
        }
    }
    private static byte[] original(String name) throws Exception {
        return switch (name) {
            case "cpp-original-request-0.body.json" -> resource(name,759,"f6fb49370f071f80bc9227f8b181c5111e3b659875bf512b55d27cfabe5a55f2");
            case "cpp-original-request-1.body.json" -> resource(name,801,"6fbc0fdcb0848a8335be2898b427f4e3f51b2c9a709764adea73b72c257035b3");
            case "cpp-original-request-2.body.json" -> resource(name,802,"cbd55de5019f1af5ce966ab75bb242d0aa0ea16df6fe2359c7c617bfa0fe1267");
            case "cpp-original-request-3.body.json" -> resource(name,798,"e3445e28dc3ae1e8769b6246fb8c2619dfbf5378f69872eaa8d82f11eddca891");
            case "cpp-original-request-4.body.json" -> resource(name,754,"f5e140dfb92f67b262d93855f36941b8e1794acba76aa96cb5fd01bf769b4c2a");
            case "cpp-original-request-5.body.json" -> resource(name,797,"f835bb6dc7b5bb9c51497cfb854ce1f09ff266a79de417183e95e51e14e38566");
            case "cpp-original-request-6.body.json" -> resource(name,801,"94d03160bd80bee03408b1b979920980e662783d6ec5c80cf50445ef9c55ff8b");
            case "cpp-original-request-7.body.json" -> resource(name,797,"e3f2dcd1cdbd32a62e27c097d83171f6756e0a03db12cf3c8c06ba31fb1022ed");
            case "cpp-response-0.body.json" -> resource(name,1644,"2d088ddf9a4e04bb28aef798a66a749aa26b72f87abf96f63ddd0afcbc197c4e");
            case "cpp-response-1.body.json" -> resource(name,2102,"caef4a82740c16daf4201330b328a0a32396f41e455ef151278b77f1e0c8afd8");
            case "cpp-response-2.body.json" -> resource(name,2116,"589ddea74d4367d9a42ae8146fa4d30f1aaf904600188715816fa914a90f9303");
            case "cpp-response-3.body.json" -> resource(name,1044,"a17df934eda25bc8f9548ea3eb05f697926ff2509f73777698ce689164410445");
            default -> throw new IllegalArgumentException("Unknown original C++ resource");
        };
    }
    private static CurrentZg361Ae2Result response(int index) throws Exception {
        byte[] raw = original("cpp-response-"+index+".body.json");
        var outer = StrictJson.object(NativeWire.parse(raw),Set.of("type","protocol_version","request_id","ok","result"));
        assertEquals("command_result",outer.get("type").textValue()); assertEquals(1,outer.get("protocol_version").intValue());
        assertEquals("cpp-response-"+index,outer.get("request_id").textValue()); assertEquals(20,outer.get("result").size());
        var value = CurrentZg361Ae2Result.decode(new RawJson(NativeWire.token(raw,"result")));
        assertEquals(value,CurrentZg361Ae2Result.decode(value.encode()));
        assertEquals(outer.get("result"),NativeWire.parse(value.encode().bytes()));
        assertEquals(outer.get("ok").booleanValue(),value.successful());
        assertFalse(value.nativeHandled()); assertTrue(outer.get("result").get("addresses_redacted").booleanValue());
        assertEquals(MAX,value.providerGeneration()); assertEquals(MAX,value.querySequence());
        // Request and response IDs are independent originals; no artificial exchange is constructed.
        return value;
    }
    private static ObjectNode filePin(Path path, byte[] bytes) throws Exception {
        assertArrayEquals(bytes,Files.readAllBytes(path));
        return StrictJson.object().put("path",path.toAbsolutePath().normalize().toString()).put("bytes",bytes.length)
                .put("sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static void factory(int index, CurrentZg361Ae2.Action action) throws Exception {
        String name = "cpp-original-request-"+index+".body.json";
        byte[] raw = original(name);
        var expected = StrictJson.object(NativeWire.parse(raw),Set.of("type","protocol_version","request_id","step",
                "actor","target","arguments","deadline_unix_ms"));
        assertEquals("execute_step",expected.get("type").textValue()); assertEquals(1,expected.get("protocol_version").intValue());
        assertEquals("cpp-original-request-"+index,expected.get("request_id").textValue());
        assertTrue(expected.get("deadline_unix_ms").isIntegralNumber()); assertEquals(MAX,expected.get("deadline_unix_ms").bigIntegerValue());
        var args = StrictJson.object(expected.get("arguments"),Set.of("zg361_ae2"));
        var claim = StrictJson.object(args.get("zg361_ae2"),Set.of("schema","game_version","executable_sha256","adapter_id",
                "backend","action","expected_core","provider_generation","query_sequence"));
        assertEquals(action.wire(),claim.get("action").textValue());
        assertTrue(claim.get("provider_generation").isTextual()); assertTrue(claim.get("query_sequence").isTextual());
        BigInteger provider = new BigInteger(claim.get("provider_generation").textValue());
        BigInteger query = new BigInteger(claim.get("query_sequence").textValue());
        assertEquals(action.queryOnly()?BigInteger.ZERO:MAX,provider); assertEquals(action.queryOnly()?BigInteger.ZERO:MAX,query);
        var core = new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentZg361Ae2.readCore(claim.get("expected_core")));
        var request = CurrentZg361Ae2.request(core,action,provider,query);
        assertEquals(CurrentZg361Ae2.STEP,request.step()); assertEquals(action.capability(),request.requiredCapability().orElseThrow());
        // Exercise the actual production encoder; do not replace it with a correct test-only envelope.
        byte[] packet = NativeGameTransport.currentZg361Ae2Packet(expected.get("request_id").textValue(),request,
                expected.get("deadline_unix_ms").bigIntegerValue());
        assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        byte[] body = Arrays.copyOfRange(packet,4,packet.length); assertArrayEquals(packet,NativeWire.packet(body));
        var actual = StrictJson.object(NativeWire.parse(body),Set.of("type","protocol_version","request_id","step",
                "actor","target","arguments","deadline_unix_ms"));
        var comparable = actual.deepCopy(); var actualClaim = (ObjectNode)comparable.get("arguments").get("zg361_ae2");
        assertEquals(claim.get("executable_sha256").textValue().toLowerCase(Locale.ROOT),
                actualClaim.get("executable_sha256").textValue().toLowerCase(Locale.ROOT));
        actualClaim.set("executable_sha256",claim.get("executable_sha256"));
        assertEquals(expected,comparable,"Only legal executable-hash casing may differ");
        var decoded = NativeWire.decodeExecuteRequest(packet);
        assertEquals(expected.get("request_id").textValue(),decoded.requestId()); assertEquals(request.step(),decoded.step());
        assertTrue(decoded.expectedRevision().isEmpty()); assertTrue(decoded.expectedSnapshotRevision().isEmpty());
        assertTrue(actual.get("deadline_unix_ms").isIntegralNumber()); assertEquals(MAX,actual.get("deadline_unix_ms").bigIntegerValue());
        assertEquals(claim.get("expected_core"),actual.get("arguments").get("zg361_ae2").get("expected_core"));
        String configured = System.getProperty(OUTPUT);
        if (configured != null) {
            Path directory = Path.of(configured); Files.createDirectories(directory); String stem = "java-"+action.wire();
            Path bodyPath = directory.resolve(stem+".body.json"), packetPath = directory.resolve(stem+".packet.bin");
            Files.write(bodyPath,body,StandardOpenOption.CREATE_NEW); Files.write(packetPath,packet,StandardOpenOption.CREATE_NEW);
            var item = StrictJson.object().put("action",action.wire()).put("original_request_id",expected.get("request_id").textValue())
                    .put("original_resource",name).put("original_body_sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            item.set("body",filePin(bodyPath,body)); item.set("packet",filePin(packetPath,packet));
            assertNull(EXPORTED.putIfAbsent(action,item),"Each original factory exports only once");
        }
    }
    @AfterAll static void exportActualRequestsIndexWhenConfigured() throws Exception {
        String configured = System.getProperty(OUTPUT); if (configured == null) return;
        assertEquals(8,EXPORTED.size(),"Only the complete eight actual factory packets form an inverse-validation index");
        var index = StrictJson.object().put("schema","xar.zg361-ae2.actual-Java-factory-requests.v1")
                .put("request_count",8).put("original_IDs_and_MAX_deadlines_preserved",true)
                .put("Cplusplus_validation","NOT_RUN_BY_JAVA_FACTORY_TEST");
        var rows = index.putArray("requests");
        for (var action : CurrentZg361Ae2.Action.values()) rows.add(EXPORTED.get(action));
        Files.write(Path.of(configured).resolve("java-requests-index.json"),StrictJson.canonical(index),StandardOpenOption.CREATE_NEW);
    }

    @Test void originalControlsQueryRetainsBothActualNavigationGuardRows() throws Exception {
        var value = response(0); assertEquals(CurrentZg361Ae2.Action.QUERY_CONTROLS,value.action());
        assertEquals(CurrentZg361Ae2Result.Status.AVAILABLE,value.status()); assertEquals(BigInteger.ZERO,value.claimSequence());
        assertFalse(value.effectAttempted()); assertFalse(value.nativeReturned());
        var controls = value.source().orElseThrow().controls().orElseThrow(); assertEquals(2,controls.rows().size());
        assertTrue(controls.modelComplete()); assertTrue(controls.listVisible()); assertFalse(controls.detailVisible());
        assertTrue(controls.selectedControl().isEmpty());
        for (var control : CurrentZg361Ae2Source.Control.values()) {
            var row = controls.row(control).orElseThrow(); assertEquals(control.definitionKey(),row.definitionKey());
            assertTrue(row.nativeCanOpenDetail()); assertTrue(row.openDetailAdmissible());
            assertTrue(row.nativeCanConfirm().isEmpty()); assertFalse(row.confirmAdmissible());
        }
        // native_can_open_detail is actual row/window navigation-guard DATA, not a separate native Can callee.
    }
    @Test void originalEventQueryRetainsAllThreeOwnedTooltipsAndShuffledAuthoredIndices() throws Exception {
        var value = response(1); assertEquals(CurrentZg361Ae2.Action.QUERY_AE2,value.action());
        var events = value.source().orElseThrow().events().orElseThrow(); assertTrue(events.censusComplete());
        var ae2 = events.ae2().orElseThrow(); assertEquals(42,ae2.authoredOptionCount()); assertTrue(ae2.phaseBound());
        assertEquals(List.of(17,15,16),ae2.options().stream().map(CurrentZg361Ae2Source.Option::authoredOptionIndex).toList());
        assertEquals(15,ae2.payNowOption().authoredOptionIndex()); assertEquals("zg361comp.1.ae2.r1",ae2.payNowOption().optionKey());
        assertTrue(ae2.payNowAdmissible()); assertEquals(1,events.census().size());
        assertEquals(ae2.instanceId(),events.census().get(0).instanceId());
        for (var row : ae2.options()) assertEquals("#P actual owned tooltip DATA#!\r\n\t"+row.authoredOptionIndex()+"\0\u0001",row.tooltip());
        assertFalse(value.effectAttempted()); assertEquals(BigInteger.ZERO,value.claimSequence());
    }
    @Test void originalSelectionDispatchKeepsBeforeSourceWithoutClaimingPaymentOrEventAbsence() throws Exception {
        var value = response(2); assertEquals(CurrentZg361Ae2.Action.CHOOSE_PAY_NOW,value.action());
        assertEquals(CurrentZg361Ae2Result.Status.SELECTION_DISPATCHED,value.status()); assertEquals(BigInteger.ONE,value.claimSequence());
        assertTrue(value.effectAttempted()); assertTrue(value.nativeReturned()); assertTrue(value.cleanupKnown());
        byte[] query = original("cpp-response-1.body.json");
        var before = CurrentZg361Ae2Result.decode(new RawJson(NativeWire.token(query,"result")));
        assertEquals(before.source(),value.source());
        assertEquals(1,value.source().orElseThrow().events().orElseThrow().census().size());
    }
    @Test void originalUnknownRetainsActualClaimEntryOwnerAndSourceNull() throws Exception {
        var value = response(3); assertEquals(CurrentZg361Ae2Result.Status.INDETERMINATE,value.status());
        assertTrue(value.effectAttempted()); assertFalse(value.nativeReturned()); assertFalse(value.cleanupKnown());
        assertEquals(BigInteger.TWO,value.claimSequence()); assertFalse(value.sourceAvailable()); assertTrue(value.source().isEmpty());
        assertTrue(value.owner().isPresent()); assertTrue(value.factsBefore().isPresent());
        assertEquals("actual_CPP_serializer_self_owned_DATA_UNKNOWN",value.unavailableReason().orElseThrow());
    }
    @Test void originalFactoryQueryControls() throws Exception { factory(0,CurrentZg361Ae2.Action.QUERY_CONTROLS); }
    @Test void originalFactoryOpenControlsList() throws Exception { factory(1,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST); }
    @Test void originalFactoryOpenPresentDetail() throws Exception { factory(2,CurrentZg361Ae2.Action.OPEN_PRESENT_DETAIL); }
    @Test void originalFactoryConfirmPresent() throws Exception { factory(3,CurrentZg361Ae2.Action.CONFIRM_PRESENT); }
    @Test void originalFactoryQueryAe2() throws Exception { factory(4,CurrentZg361Ae2.Action.QUERY_AE2); }
    @Test void originalFactoryChoosePayNow() throws Exception { factory(5,CurrentZg361Ae2.Action.CHOOSE_PAY_NOW); }
    @Test void originalFactoryOpenVerifyDetail() throws Exception { factory(6,CurrentZg361Ae2.Action.OPEN_VERIFY_DETAIL); }
    @Test void originalFactoryConfirmVerify() throws Exception { factory(7,CurrentZg361Ae2.Action.CONFIRM_VERIFY); }
}
