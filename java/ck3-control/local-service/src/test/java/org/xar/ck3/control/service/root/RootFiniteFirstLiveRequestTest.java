package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure request/output protocol regressions; these never create a Game or claim forward-day success. */
public final class RootFiniteFirstLiveRequestTest {
    private static RootFiniteFirstLiveRequest request() {
        var startup=new RootStartupInputsProducer.Request(
                new FileRef("D:/ck3-state/test/startup.json",17,"a".repeat(64)),Duration.ofMillis(900));
        return new RootFiniteFirstLiveRequest("first-live-test","test-machine",
                Instant.parse("2026-10-25T18:00:00Z"),Instant.parse("2026-10-25T19:00:00Z"),
                startup,1,Duration.ofSeconds(30));
    }
    private static ObjectNode document() {
        return (ObjectNode)StrictJson.parse(request().encode(),RootFiniteFirstLiveRequest.MAXIMUM_BYTES);
    }
    private static byte[] encode(ObjectNode node) {
        return StrictJson.canonical(node,RootFiniteFirstLiveRequest.MAXIMUM_BYTES);
    }
    @Test public void sharedStartupRequestRoundTripsThroughTheSingleProducerCodec() {
        var expected=request();
        var decoded=RootFiniteFirstLiveRequest.decode(expected.encode());
        assertEquals(expected,decoded);
        assertArrayEquals(expected.encode(),decoded.encode());
        assertArrayEquals(RootStartupInputsProducer.encode(expected.startup()),
                StrictJson.canonical(document().get("startup_inputs"),RootStartupInputsProducer.MAXIMUM_BYTES));
    }
    @Test public void countersRejectBooleansFractionsNullAndOutOfRangeNumbers() {
        for(String value:new String[]{"true","1.0","null","0","36501"}) {
            var node=document();node.set("minimum_forward_saved_days",
                    StrictJson.parse(value.getBytes(StandardCharsets.UTF_8),64));
            assertThrows(IllegalArgumentException.class,()->RootFiniteFirstLiveRequest.decode(encode(node)),value);
        }
        for(String value:new String[]{"true","30000.0","null","0","1800001"}) {
            var node=document();node.set("step_timeout_ms",
                    StrictJson.parse(value.getBytes(StandardCharsets.UTF_8),64));
            assertThrows(IllegalArgumentException.class,()->RootFiniteFirstLiveRequest.decode(encode(node)),value);
        }
    }
    @Test public void nestedStartupStillConsumesTheOriginalStrictContract() {
        var node=document();
        ((ObjectNode)node.get("startup_inputs")).put("close_wait_ms",900.0);
        var fractionalWait=node;
        assertThrows(IllegalArgumentException.class,()->RootFiniteFirstLiveRequest.decode(encode(fractionalWait)));
        node=document();node.putNull("startup_inputs");
        var missingStartup=node;
        assertThrows(IllegalArgumentException.class,()->RootFiniteFirstLiveRequest.decode(encode(missingStartup)));
    }
    @Test public void missingUnknownAndNoncanonicalRequestFieldsAreRejected() {
        var node=document();node.remove("startup_inputs");
        var missing=node;
        assertThrows(IllegalArgumentException.class,()->RootFiniteFirstLiveRequest.decode(encode(missing)));
        node=document();node.put("restore_pair","not-an-authority");
        var extra=node;
        assertThrows(IllegalArgumentException.class,()->RootFiniteFirstLiveRequest.decode(encode(extra)));
        node=document();node.put("observed_at_utc","2026-10-25T18:00:00+00:00");
        var noncanonical=node;
        assertThrows(IllegalArgumentException.class,()->RootFiniteFirstLiveRequest.decode(encode(noncanonical)));
    }
    @Test public void incompleteCliCannotEnterTheOriginalMainOrNeedInjectedHosts() {
        var missing=assertThrows(IOException.class,()->new RootFiniteFirstLiveMain().run());
        assertTrue(missing.getMessage().contains("MISSING_FINITE_FIRST_LIVE_INPUTS"));
        assertThrows(IOException.class,()->RootFiniteFirstLiveRequest.arguments("D:/request.json","01","a".repeat(64)));
        assertThrows(IOException.class,()->RootFiniteFirstLiveRequest.arguments("request.json","17","a".repeat(64)));
        assertThrows(IOException.class,()->RootFiniteFirstLiveRequest.arguments("D:/request.json","17","A".repeat(64)));
    }
    @Test public void realUnconsumedWorkReportsNotRunThroughTheSharedOutputCodec() {
        var work=new RootFiniteFirstLiveWork(RootFiniteFirstLiveRequest.decode(request().encode()));
        var decoded=RootFiniteFirstLiveWork.decodeReport(work.result().toJson());
        assertEquals(request().requestId(),decoded.requestId());
        assertEquals(request().machineId(),decoded.machineId());
        assertEquals(RootFiniteFirstLiveWork.Outcome.NOT_RUN,decoded.outcome());
        assertEquals(work.result().exitCode(),decoded.exitCode());
        assertNotEquals(0,decoded.exitCode());
        assertEquals(0,decoded.forwardSavedDays());
        assertTrue(decoded.pair().isEmpty());
        assertTrue(decoded.restoredOwner().isEmpty());
    }
}
