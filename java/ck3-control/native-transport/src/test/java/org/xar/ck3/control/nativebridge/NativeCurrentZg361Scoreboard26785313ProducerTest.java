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

/** Five actual C++ NoGame bodies; independent request/response IDs are not an exchange or live open/close proof. */
final class NativeCurrentZg361Scoreboard26785313ProducerTest {
    private static final BigInteger MAX = NativeWire.UINT64_MAX;
    private static final String OUTPUT = "xar.zg361.scoreboard.java.requests.output.directory";
    private static final ConcurrentMap<CurrentZg361Ae2.Action,ObjectNode> EXPORTED = new ConcurrentHashMap<>();

    private static byte[] original(String name) throws Exception {
        int size; String sha;
        switch (name) {
            case "cpp-scoreboard-original-request-0.body.json" -> { size=772; sha="d9d23a9c9e2c1ae55f7f600808d9bd32fb659604b07e307f89acb973c5400d71"; }
            case "cpp-scoreboard-original-request-1.body.json" -> { size=809; sha="ed92bdc02edfbc582c04cd04e3b7959717190e5c7f70b1c27a17b5bbc7b91afb"; }
            case "cpp-scoreboard-original-request-2.body.json" -> { size=810; sha="0956b125ebbfd4328102c6a82961c75bc1dc6c0d5aa02d3c92a3174650bff2fa"; }
            case "cpp-scoreboard-response-0.body.json" -> { size=1360; sha="0505c771363b2d32136d53d3860b5ae32d21aaf7d2ec51ee4855ab7bc0bd0f40"; }
            case "cpp-scoreboard-response-1.body.json" -> { size=1367; sha="3eaabb53987bb2b3beb426812a69fc83d2ff3f01d100cfc4d61f176a4e29b4e9"; }
            default -> throw new IllegalArgumentException("Unknown genuine C++ scoreboard resource");
        }
        try (var in = NativeCurrentZg361Scoreboard26785313ProducerTest.class.getResourceAsStream(
                "/current267-zg361-scoreboard-cpp-a1681/"+name)) {
            if (in==null) throw new IOException("Missing original C++ resource: "+name);
            byte[] bytes=in.readAllBytes(); assertEquals(size,bytes.length,name);
            assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),name);
            return bytes;
        }
    }

    private static ObjectNode filePin(Path path, byte[] bytes) throws Exception {
        assertArrayEquals(bytes,Files.readAllBytes(path));
        return StrictJson.object().put("path",path.toAbsolutePath().normalize().toString()).put("bytes",bytes.length)
                .put("sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }

    private static void factory(int index, CurrentZg361Ae2.Action action) throws Exception {
        String name="cpp-scoreboard-original-request-"+index+".body.json";
        byte[] raw=original(name);
        var expected=StrictJson.object(NativeWire.parse(raw),Set.of("type","protocol_version","request_id","step",
                "actor","target","arguments","deadline_unix_ms"));
        assertEquals("execute_step",expected.get("type").textValue()); assertEquals(1,expected.get("protocol_version").intValue());
        assertEquals("cpp-scoreboard-original-request-"+index,expected.get("request_id").textValue());
        assertTrue(expected.get("deadline_unix_ms").isIntegralNumber()); assertEquals(MAX,expected.get("deadline_unix_ms").bigIntegerValue());
        var args=StrictJson.object(expected.get("arguments"),Set.of("zg361_ae2"));
        var claim=StrictJson.object(args.get("zg361_ae2"),Set.of("schema","game_version","executable_sha256","adapter_id",
                "backend","action","expected_core","provider_generation","query_sequence"));
        assertEquals(action.wire(),claim.get("action").textValue());
        assertTrue(claim.get("provider_generation").isTextual()); assertTrue(claim.get("query_sequence").isTextual());
        BigInteger provider=new BigInteger(claim.get("provider_generation").textValue());
        BigInteger query=new BigInteger(claim.get("query_sequence").textValue());
        assertEquals(action.queryOnly()?BigInteger.ZERO:MAX,provider); assertEquals(action.queryOnly()?BigInteger.ZERO:MAX,query);
        var core=new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentZg361Ae2.readCore(claim.get("expected_core")));
        var request=CurrentZg361Ae2.request(core,action,provider,query);
        assertEquals(action.capability(),request.requiredCapability().orElseThrow());
        // Actual production encoder: a test-only correct strict8 envelope must not conceal packer regressions.
        byte[] packet=NativeGameTransport.currentZg361Ae2Packet(expected.get("request_id").textValue(),request,
                expected.get("deadline_unix_ms").bigIntegerValue());
        assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        byte[] body=Arrays.copyOfRange(packet,4,packet.length); assertArrayEquals(packet,NativeWire.packet(body));
        var actual=StrictJson.object(NativeWire.parse(body),Set.of("type","protocol_version","request_id","step",
                "actor","target","arguments","deadline_unix_ms"));
        var comparable=actual.deepCopy(); var actualClaim=(ObjectNode)comparable.get("arguments").get("zg361_ae2");
        assertEquals(claim.get("executable_sha256").textValue().toLowerCase(Locale.ROOT),
                actualClaim.get("executable_sha256").textValue().toLowerCase(Locale.ROOT));
        actualClaim.set("executable_sha256",claim.get("executable_sha256"));
        assertEquals(expected,comparable,"Only legal executable SHA casing may differ; original ID/deadline/types stay exact");
        var decoded=NativeWire.decodeExecuteRequest(packet);
        assertEquals(expected.get("request_id").textValue(),decoded.requestId()); assertEquals(request.step(),decoded.step());
        assertTrue(decoded.expectedRevision().isEmpty()); assertTrue(decoded.expectedSnapshotRevision().isEmpty());
        String configured=System.getProperty(OUTPUT);
        if (configured!=null) {
            Path directory=Path.of(configured); Files.createDirectories(directory); String stem="java-"+action.wire();
            Path bodyPath=directory.resolve(stem+".body.json"),packetPath=directory.resolve(stem+".packet.bin");
            Files.write(bodyPath,body,StandardOpenOption.CREATE_NEW); Files.write(packetPath,packet,StandardOpenOption.CREATE_NEW);
            var row=StrictJson.object().put("action",action.wire()).put("original_request_id",expected.get("request_id").textValue())
                    .put("original_resource",name).put("original_body_sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            row.set("body",filePin(bodyPath,body)); row.set("packet",filePin(packetPath,packet));
            assertNull(EXPORTED.putIfAbsent(action,row),"Each actual factory exports once");
        }
    }

    @AfterAll static void exportThreeActualRequestPacketsWhenConfigured() throws Exception {
        String configured=System.getProperty(OUTPUT); if (configured==null) return;
        assertEquals(3,EXPORTED.size());
        var index=StrictJson.object().put("schema","xar.zg361-scoreboard.actual-Java-factory-requests.v1")
                .put("request_count",3).put("original_IDs_and_MAX_deadlines_preserved",true)
                .put("Cplusplus_inverse_validation","NOT_RUN_BY_JAVA_FACTORY_TEST");
        var rows=index.putArray("requests");
        for (var action:List.of(CurrentZg361Ae2.Action.QUERY_SCOREBOARD,CurrentZg361Ae2.Action.OPEN_SCOREBOARD,CurrentZg361Ae2.Action.CLOSE_SCOREBOARD))
            rows.add(EXPORTED.get(action));
        Files.write(Path.of(configured).resolve("java-scoreboard-requests-index.json"),StrictJson.canonical(index),StandardOpenOption.CREATE_NEW);
    }

    private static CurrentZg361Ae2Result response(int index) throws Exception {
        byte[] raw=original("cpp-scoreboard-response-"+index+".body.json");
        var outer=StrictJson.object(NativeWire.parse(raw),Set.of("type","protocol_version","request_id","ok","result"));
        assertEquals("command_result",outer.get("type").textValue()); assertEquals(1,outer.get("protocol_version").intValue());
        assertEquals("cpp-scoreboard-response-"+index,outer.get("request_id").textValue()); assertTrue(outer.get("ok").booleanValue());
        var value=CurrentZg361Ae2Result.decode(new RawJson(NativeWire.token(raw,"result")));
        assertEquals(value,CurrentZg361Ae2Result.decode(value.encode()));
        assertEquals(outer.get("result"),NativeWire.parse(value.encode().bytes()));
        assertEquals(20,outer.get("result").size()); assertEquals(MAX,value.providerGeneration()); assertEquals(MAX,value.querySequence());
        assertTrue(value.cleanupKnown()); assertFalse(value.nativeHandled()); assertTrue(value.unavailableReason().isEmpty());
        assertEquals(CurrentZg361Ae2Source.Kind.SCOREBOARD,value.source().orElseThrow().kind());
        assertEquals(3,outer.get("result").get("source").size());
        assertEquals(12,outer.get("result").get("source").get("scoreboard").size());
        assertEquals(36423,value.factsBefore().orElseThrow().playedCharacterId());
        return value;
    }
    @Test void originalCppQueryPreservesClosedModalAndActualOpenEntryData() throws Exception {
        var value=response(0);
        assertEquals(CurrentZg361Ae2.Action.QUERY_SCOREBOARD,value.action()); assertEquals(CurrentZg361Ae2Result.Status.AVAILABLE,value.status());
        assertEquals(BigInteger.ZERO,value.claimSequence()); assertFalse(value.effectAttempted()); assertFalse(value.nativeReturned());
        var snapshot=value.source().orElseThrow().scoreboard().orElseThrow();
        assertTrue(snapshot.complete()); assertFalse(snapshot.modalVisible()); assertEquals(7,snapshot.windowNodes());
        assertEquals("zg361_scoreboard_entry_managed",snapshot.openEntry().orElseThrow()); assertTrue(snapshot.openAdmissible());
    }
    @Test void originalCppCloseDispatchKeepsVisibleImmutableBeforeSourceNotAnAfterClaim() throws Exception {
        var value=response(1);
        assertEquals(CurrentZg361Ae2.Action.CLOSE_SCOREBOARD,value.action()); assertEquals(CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,value.status());
        assertEquals(BigInteger.ONE,value.claimSequence()); assertTrue(value.effectAttempted()); assertTrue(value.nativeReturned());
        var snapshot=value.source().orElseThrow().scoreboard().orElseThrow();
        assertTrue(snapshot.modalVisible()); assertTrue(snapshot.closeAdmissible()); assertEquals(3,snapshot.modalChildren());
    }
    @Test void originalCppQueryRequestMatchesActualJavaFactoryAndProductionPacket() throws Exception { factory(0,CurrentZg361Ae2.Action.QUERY_SCOREBOARD); }
    @Test void originalCppOpenRequestMatchesActualJavaFactoryAndProductionPacket() throws Exception { factory(1,CurrentZg361Ae2.Action.OPEN_SCOREBOARD); }
    @Test void originalCppCloseRequestMatchesActualJavaFactoryAndProductionPacket() throws Exception { factory(2,CurrentZg361Ae2.Action.CLOSE_SCOREBOARD); }
}
