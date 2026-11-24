package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** One actual C++ serializer response; no Native request, popup identity or exchange is synthesized. */
final class NativeCurrentLivingDisplayedOptions26785313ProducerTest {
    private static byte[] original(String name,String expectedSha) throws Exception {
        try(var in=NativeCurrentLivingDisplayedOptions26785313ProducerTest.class.getResourceAsStream(
                "/current267-living-displayed-options-cpp-a01/"+name)) {
            assertNotNull(in,"Portable original missing");
            byte[] raw=in.readAllBytes();
            assertEquals(expectedSha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            return raw;
        }
    }

    @Test void actualCppDisplayedSubsetRetainsFullDefinitionAndOriginalAvailableActions() throws Exception {
        byte[] body=original("response-ui-management-displayed-subset.body.json",
                "40c4877970a57238793e766022406bbb2d62d199f654f0858ba33bc3a51c5eb6");
        byte[] packet=original("response-ui-management-displayed-subset.packet.bin",
                "5936c2a3893f7c59b808a8b8c3da6e0815574708254c8081509fcf34106675e9");
        assertEquals(2719,body.length);assertEquals(2723,packet.length);
        assertEquals(body.length,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        assertArrayEquals(body,Arrays.copyOfRange(packet,4,packet.length));
        var envelope=StrictJson.object(NativeWire.parse(body),Set.of("type","protocol_version","request_id","ok","result"));
        assertEquals("command_result",envelope.get("type").textValue());
        assertEquals("living-displayed-subset-original-response-01",envelope.get("request_id").textValue());
        assertEquals(1,envelope.get("protocol_version").intValue());assertTrue(envelope.get("ok").booleanValue());
        var actual=CurrentLivingUiResult.decode(new RawJson(StrictJson.canonical(envelope.get("result"))));
        assertEquals(envelope.get("result"),NativeWire.parse(actual.encode().bytes()));
        assertEquals(CurrentLivingUi.Action.QUERY_EVENTS,actual.action());
        assertEquals(CurrentLivingUiResult.Status.AVAILABLE,actual.status());
        assertFalse(actual.effectAttempted());assertFalse(actual.nativeReturned());assertTrue(actual.cleanupKnown());
        var source=actual.source().orElseThrow();var census=source.events().orElseThrow();
        assertTrue(census.censusComplete());assertTrue(census.completeBindings());
        assertEquals(1,census.events().size());var event=census.events().get(0);
        assertEquals("xalw.10",event.definitionKey());assertEquals(71,event.instanceId());
        assertEquals(10,event.authoredOptionCount());assertEquals(4,event.options().size());
        assertEquals(List.of(0,1,4,9),event.options().stream().map(CurrentLydSource.EventOption::authoredOptionIndex).toList());
        assertEquals("A\0B\n",event.description());assertEquals(3,census.fixedActions().size());
        assertTrue(source.actionAdmissible(CurrentLivingUi.Action.FEED_COMMON));
        for(var action:List.of(CurrentLivingUi.Action.FEED_MASTERWORK,CurrentLivingUi.Action.FEED_FAMED,
                CurrentLivingUi.Action.FEED_ILLUSTRIOUS,CurrentLivingUi.Action.CLOSE_MANAGEMENT))
            assertFalse(source.actionAdmissible(action));
        assertEquals(406L,census.bindings().get(0).target().artifactFullId().orElseThrow());
    }
}
