package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The actual Core/Host/read producer-consumer path is the persistent RootHostBatchAndCloseActualTest. */
public final class RootStartupInputsProducerTest {
    private static RootStartupInputsProducer.Request request() {
        return new RootStartupInputsProducer.Request(new FileRef("D:/ck3-state/test/startup.json",17,"a".repeat(64)),Duration.ofMillis(900));
    }
    @Test public void exactRequestRoundTripsWithoutSerializingAuthority() {
        var expected=request();byte[] bytes=RootStartupInputsProducer.encode(expected);
        assertEquals(expected,RootStartupInputsProducer.decode(bytes));
        String json=new String(bytes,StandardCharsets.UTF_8);
        assertFalse(json.contains("Core"));assertFalse(json.contains("snapshot"));assertFalse(json.contains("game_date"));
    }
    @Test public void malformedFieldsAndNonIntegerWaitAreRejected() {
        var good=StrictJson.parse(RootStartupInputsProducer.encode(request()),4096);
        for(String value:new String[]{"true","900.0","null","99","30001"}) {
            var changed=good.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed).set("close_wait_ms",StrictJson.parse(value.getBytes(StandardCharsets.UTF_8),4096));
            assertThrows(IllegalArgumentException.class,()->RootStartupInputsProducer.decode(StrictJson.canonical(changed,4096)));
        }
        var missing=good.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)missing).remove("startup");
        assertThrows(IllegalArgumentException.class,()->RootStartupInputsProducer.decode(StrictJson.canonical(missing,4096)));
        var extra=good.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)extra).put("current_game_date","1066.9.15");
        assertThrows(IllegalArgumentException.class,()->RootStartupInputsProducer.decode(StrictJson.canonical(extra,4096)));
    }
    @Test public void missingOrNonCanonicalExternalReferenceNeverCreatesInputs() {
        assertThrows(java.io.IOException.class,()->RootStartupInputsProducer.fromEnvironment(Map.of()));
        assertThrows(java.io.IOException.class,()->RootStartupInputsProducer.fromEnvironment(Map.of(
                RootStartupInputsProducer.REQUEST_ENV,"D:/ck3-state/test/startup-inputs.json",
                RootStartupInputsProducer.REQUEST_ENV+"_BYTES","01",
                RootStartupInputsProducer.REQUEST_ENV+"_SHA256","a".repeat(64))));
        assertThrows(IllegalArgumentException.class,()->new RootStartupInputsProducer.Request(
                new FileRef("D:/ck3-state/test/startup.json",17,"a".repeat(64)),Duration.ofNanos(100000001)));
    }
}
