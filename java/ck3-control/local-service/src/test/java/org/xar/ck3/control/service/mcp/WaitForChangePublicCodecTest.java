package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

final class WaitForChangePublicCodecTest {
    private static RawJson raw(String body){return new RawJson(body.getBytes(StandardCharsets.UTF_8));}
    private static WaitForChangePublicCodec.Request request(String body){return WaitForChangePublicCodec.decode(PublicBindings.present(raw(body)));}

    @Test void actualWaitArgumentProducerRoundTripsRevisionAndTimeoutPresenceWithoutAnAlias() {
        for(String body:List.of("{\"after_revision\":\"0\"}",
                "{\"after_revision\":\"18446744073709551615\",\"timeout_seconds\":10}",
                "{\"after_revision\":\"900719925474099312345678901234567890\",\"timeout_seconds\":1.000000001}")) {
            var decoded=request(body);
            assertEquals(decoded,WaitForChangePublicCodec.decode(PublicBindings.present(WaitForChangePublicCodec.encode(decoded))));
        }
        var missing=request("{\"after_revision\":\"1\"}");
        var explicit=request("{\"after_revision\":\"1\",\"timeout_seconds\":10}");
        assertTrue(missing.timeout().isEmpty());assertEquals(Duration.ofSeconds(10),missing.effectiveTimeout());
        assertEquals(Optional.of(Duration.ofSeconds(10)),explicit.timeout());assertNotEquals(missing,explicit);
        assertFalse(McpJson.object(McpJson.parse(WaitForChangePublicCodec.encode(missing).bytes())).has("timeout_seconds"));
        assertTrue(McpJson.object(McpJson.parse(WaitForChangePublicCodec.encode(explicit).bytes())).has("timeout_seconds"));
    }
    @Test void revisionTypeFieldsAndNonrepresentableTimeoutFailBeforeAnyProviderCanBeCalled() {
        for(String revision:List.of("1","1.0","true","null","\"01\"","\"-1\"","\"+1\"","\" 1\"","\"1e2\""))
            assertThrows(IllegalArgumentException.class,()->request("{\"after_revision\":"+revision+"}"));
        for(String timeout:List.of("true","false","null","\"10\"","0","-1","0.0000000001","1e400","9007199254740992"))
            assertThrows(IllegalArgumentException.class,()->request("{\"after_revision\":\"1\",\"timeout_seconds\":"+timeout+"}"));
        for(String body:List.of("{}","{\"expected_revision\":\"1\"}",
                "{\"after_revision\":\"1\",\"expected_revision\":\"1\"}",
                "{\"after_revision\":\"1\",\"after_revision\":\"2\"}"))
            assertThrows(IllegalArgumentException.class,()->request(body));
        assertThrows(IllegalArgumentException.class,()->WaitForChangePublicCodec.decode(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->WaitForChangePublicCodec.decode(new PublicBindings.Null()));
    }
    @Test void callerWaitAndFinalCaptureDeadlinesStayDistinctWithoutClippingTheRequestedWait() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");
        Clock clock=Clock.fixed(now,ZoneOffset.UTC);
        var request=request("{\"after_revision\":\"7\",\"timeout_seconds\":180.000000001}");
        var actual=WaitForChangePublicCodec.deadlines(request,clock,Duration.ofSeconds(3));
        assertEquals(now.plusSeconds(180).plusNanos(1),actual.waitUntil());
        assertEquals(now.plusSeconds(183).plusNanos(1),actual.captureUntil());
        assertThrows(IllegalArgumentException.class,()->WaitForChangePublicCodec.deadlines(request,clock,Duration.ZERO));
        var tooLong=new WaitForChangePublicCodec.Request(BigInteger.ZERO,Optional.of(Duration.ofSeconds(Long.MAX_VALUE)));
        assertThrows(IllegalArgumentException.class,()->WaitForChangePublicCodec.deadlines(tooLong,clock,Duration.ofSeconds(1)));
    }
}
