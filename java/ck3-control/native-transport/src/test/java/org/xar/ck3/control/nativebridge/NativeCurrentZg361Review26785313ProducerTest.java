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

/** Three actual C++ NoGame originals only; no live review or four localized conditions are invented. */
final class NativeCurrentZg361Review26785313ProducerTest {
    private static final BigInteger MAX = NativeWire.UINT64_MAX;
    private static final String OUTPUT = "xar.zg361.review.java.requests.output.directory";
    private static final ConcurrentMap<CurrentZg361Ae2.Action,ObjectNode> EXPORTED = new ConcurrentHashMap<>();

    private static byte[] original(String name) throws Exception {
        int size; String sha;
        switch (name) {
            case "cpp-review-response-0.body.json" -> { size=1577; sha="89212d762ecad673d8049d9456ca0eddd637678993a6b06f910fed030ad52f7e"; }
            case "cpp-review-original-request-0.body.json" -> { size=777; sha="91621d2bea70a06dcf6d624850e7e32f5a998d9626049f476135ccd1f2136b81"; }
            case "cpp-review-original-request-1.body.json" -> { size=808; sha="75f5f9c22f2e23d7bf4560b53ce91de3cd45428607173aed3cb5b5ee2ec55ebb"; }
            default -> throw new IllegalArgumentException("Unknown genuine C++ review resource");
        }
        try (var in = NativeCurrentZg361Review26785313ProducerTest.class.getResourceAsStream(
                "/current267-zg361-review-cpp-a1617/"+name)) {
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
        String name="cpp-review-original-request-"+index+".body.json";
        byte[] raw=original(name);
        var expected=StrictJson.object(NativeWire.parse(raw),Set.of("type","protocol_version","request_id","step",
                "actor","target","arguments","deadline_unix_ms"));
        assertEquals("execute_step",expected.get("type").textValue()); assertEquals(1,expected.get("protocol_version").intValue());
        assertEquals("cpp-review-original-request-"+index,expected.get("request_id").textValue());
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

    @AfterAll static void exportTwoActualRequestPacketsWhenConfigured() throws Exception {
        String configured=System.getProperty(OUTPUT); if (configured==null) return;
        assertEquals(2,EXPORTED.size());
        var index=StrictJson.object().put("schema","xar.zg361-review.actual-Java-factory-requests.v1")
                .put("request_count",2).put("original_IDs_and_MAX_deadlines_preserved",true)
                .put("Cplusplus_inverse_validation","NOT_RUN_BY_JAVA_FACTORY_TEST");
        var rows=index.putArray("requests");
        for (var action:List.of(CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL))
            rows.add(EXPORTED.get(action));
        Files.write(Path.of(configured).resolve("java-review-requests-index.json"),StrictJson.canonical(index),StandardOpenOption.CREATE_NEW);
    }

    @Test void originalCppReviewResponsePreservesCompleteActualNativeTextAndTwentyFieldReadonlyResult() throws Exception {
        byte[] raw=original("cpp-review-response-0.body.json");
        var outer=StrictJson.object(NativeWire.parse(raw),Set.of("type","protocol_version","request_id","ok","result"));
        assertEquals("command_result",outer.get("type").textValue()); assertEquals(1,outer.get("protocol_version").intValue());
        assertEquals("cpp-review-response-0",outer.get("request_id").textValue()); assertTrue(outer.get("ok").booleanValue());
        var value=CurrentZg361Ae2Result.decode(new RawJson(NativeWire.token(raw,"result")));
        assertEquals(value,CurrentZg361Ae2Result.decode(value.encode()));
        assertEquals(outer.get("result"),NativeWire.parse(value.encode().bytes()));
        assertEquals(20,outer.get("result").size()); assertEquals(CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,value.action());
        assertEquals(CurrentZg361Ae2Result.Status.AVAILABLE,value.status()); assertTrue(value.successful());
        assertEquals(MAX,value.providerGeneration()); assertEquals(MAX,value.querySequence()); assertEquals(BigInteger.ZERO,value.claimSequence());
        assertFalse(value.effectAttempted()); assertFalse(value.nativeReturned()); assertFalse(value.nativeHandled()); assertTrue(value.cleanupKnown());
        assertTrue(value.unavailableReason().isEmpty()); assertTrue(value.owner().isPresent()); assertTrue(value.factsBefore().isPresent());
        var source=value.source().orElseThrow(); assertEquals(CurrentZg361Ae2Source.Kind.REVIEW,source.kind());
        assertEquals(3,source.encode().size()); assertTrue(source.controls().isEmpty()); assertTrue(source.events().isEmpty());
        var review=source.review().orElseThrow(); assertTrue(review.requirementsComplete()); assertTrue(review.selectedReview());
        assertTrue(review.hasRequirements().orElseThrow()); assertFalse(review.openDetailAdmissible());
        assertEquals("#P actual self-owned native serializer DATA#!\r\n\t\0\u0001",review.requirementsDescription().orElseThrow());
        // This self-owned text is original NoGame DATA, not the four actual localized review conditions.
    }
    @Test void originalFactoryQueryReviewRequirements() throws Exception { factory(0,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS); }
    @Test void originalFactoryOpenReviewDetail() throws Exception { factory(1,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL); }
}
