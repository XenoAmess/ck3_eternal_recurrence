package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.reconciliation.LateOutcome;

/** Actual C++ original bytes, cold DATA only. No Java request chronology, owner or Full receipt is synthesized. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.sentinel64.inputs",matches=".+")
final class Sentinel64OriginalDataTest {
    private final com.fasterxml.jackson.databind.JsonNode input;
    Sentinel64OriginalDataTest()throws Exception {
        input=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.sentinel64.inputs"))));
    }
    private byte[] exact(com.fasterxml.jackson.databind.JsonNode r)throws Exception {
        var ref=ExactRef.fromJson(r);byte[] raw=Files.readAllBytes(Path.of(ref.path()));
        assertEquals(ref.bytes(),raw.length);assertEquals(ref.sha256(),ActionCodec.sha256(raw));return raw;
    }
    private byte[] packet(String name)throws Exception {
        byte[] raw=exact(input.path("originals").path(name).path("json"));
        byte[] packet=exact(input.path("originals").path(name).path("packet"));
        assertArrayEquals(raw,Arrays.copyOfRange(packet,4,packet.length));assertArrayEquals(NativeWire.packet(raw),packet);return packet;
    }
    private NativeActionPort.AckReceived ack(String name)throws Exception {
        byte[] packet=packet(name);var row=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        return new NativeActionPort.AckReceived(row.requestId(),row.nativeOk(),Optional.of(new RawJson(row.result().token().orElseThrow().value())),new RawJson(row.payload().value()),packet);
    }
    @Test void actualBb3SevenDayArmStatusAndCoreCancelOriginalsRemainStrictColdData()throws Exception {
        byte[] requestPacket=packet("arm-request");var request=NativeWire.decodeExecuteRequest(requestPacket);
        var rawRequest=StrictJson.parse(Arrays.copyOfRange(requestPacket,4,requestPacket.length));
        assertEquals("research-arm-tactical-daily-sentinel-v1-53176992-to-53177160-speed-5-mode-terminal-a-0",request.step());
        var produced=FullSnapshotDateSentinelArm.request(ExactCk3Build.CK3_1210_STEAM_26757580,request.step(),"native:42",BigInteger.valueOf(42),Instant.ofEpochMilli(1005000));
        assertEquals(rawRequest.path("date_sentinel_arm"),StrictJson.parse(produced.additionalFields().bytes()).path("date_sentinel_arm"));
        var armAck=ack("arm-result");var arm=AdvancePrimitives.acknowledgedSentinel(armAck,request.step());
        assertEquals(LateOutcome.State.ARMED,arm.state());assertEquals("1",arm.generation().decimal());
        assertEquals(168,arm.targetDateRaw()-arm.startingDateRaw());assertEquals(5,arm.speed());assertEquals(0,arm.completedDailyTicks());
        var before=ClockStatusRead.decode(ack("before-status"));assertEquals(arm,before);
        var cancelled=AdvancePrimitives.acknowledgedSentinel(ack("cancel-result"),ClockStatusRead.CANCEL_PREFIX+"1");
        var after=ClockStatusRead.decode(ack("independent-after-status"));
        assertEquals(cancelled,after);assertEquals(LateOutcome.State.IDLE,after.state());assertEquals(arm.generation(),after.generation());
        assertEquals(arm.startingDateRaw(),after.startingDateRaw());assertEquals(arm.targetDateRaw(),after.targetDateRaw());
        assertEquals(0,after.completedDailyTicks());assertEquals(53176992,after.lastObservedDateRaw());
        assertThrows(IOException.class,()->DateSentinelArmResult.decode(armAck,request.step()),"cold packet must not mint missing original Java request chronology");
        var rejected=ack("rejected-full-drift");assertFalse(rejected.nativeOk());
        var negative=StrictJson.parse(rejected.originalResultToken().orElseThrow().bytes());
        assertEquals("stale_full_snapshot",negative.path("queue_status").textValue());
        assertFalse(negative.path("effect_attempted").booleanValue());assertFalse(negative.path("full_snapshot_before_verified").booleanValue());
        assertThrows(IOException.class,()->DateSentinelArmResult.decode(rejected,request.step()));
        byte[] corePacket=packet("independent-after-core");var core=StrictJson.parse(Arrays.copyOfRange(corePacket,4,corePacket.length));
        assertTrue(core.path("core_available").booleanValue());assertFalse(core.path("application_main_observed").booleanValue());
        assertFalse(core.path("complete_snapshot").booleanValue());assertEquals(53176992,core.path("date_raw").intValue());
        assertEquals(ExactCk3Build.CK3_1210_STEAM_26757580.executableSha256().toUpperCase(java.util.Locale.ROOT),core.path("executable_sha256").textValue());
    }
}
