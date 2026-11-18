package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.reconciliation.LateOutcome;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Exact C++ packets with synthetic archived correlation DATA; no endpoint, private role or independent status read. */
final class DateSentinelArmResultCppProducerTest {
    private static final String ARM="research-arm-tactical-daily-sentinel-v1-24000-to-24024-speed-5-mode-terminal-a-0";
    private static byte[] read(String path,String property,String name)throws IOException {
        try(var in=DateSentinelArmResultCppProducerTest.class.getResourceAsStream(path+name)){
            if(in!=null)return in.readAllBytes();
        }
        String root=System.getProperty(property);
        if(root==null||root.isBlank()||!Path.of(root).isAbsolute())throw new IOException("NOT_RUN: C++ resource or absolute "+property+" required");
        return Files.readAllBytes(Path.of(root).resolve(name));
    }
    private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    private static byte[] packet(String name)throws Exception {
        byte[] manifest=read("/date-arm1210/","xar.native.date-arm1210.fixtures","ACTUAL-CPP-DATE-STATUS-PACKETS01.json");
        assertEquals(3457,manifest.length);assertEquals("d29e0f2b9b115e6be5894e93f1e17b1159bc5d832f68178e1ee38722968f35b4",sha(manifest));
        for(var row:NativeWire.parse(manifest).get("packets"))if(name.equals(row.get("name").textValue())){
            byte[] raw=read("/date-arm1210/","xar.native.date-arm1210.fixtures",name+".json");
            assertEquals(row.get("bytes").intValue(),raw.length);assertEquals(row.get("sha256").textValue(),sha(raw));return raw;
        }
        throw new IOException("unlisted C++ packet");
    }
    private static ObjectNode tree(byte[] raw)throws IOException{return NativeWire.object(NativeWire.parse(raw));}
    private static ObjectNode result(ObjectNode tree){return (ObjectNode)tree.get("result");}
    private static ObjectNode status(ObjectNode tree){return (ObjectNode)result(tree).get("tactical_daily_sentinel");}
    private static byte[] encode(ObjectNode tree)throws IOException{return org.xar.ck3.control.contracts.FullJsonTree.encode(tree,65536);}
    private static NativeActionPort.AckReceived ack(byte[] raw)throws IOException {
        byte[] framed=NativeWire.packet(raw);var decoded=(NativeWire.CommandResult)NativeWire.decode(framed);
        String step=NativeWire.text(result(tree(raw)).get("step"));
        byte[] request=NativeWire.execute(decoded.requestId(),step,BigInteger.ONE,new byte[]{'{','}'});
        var session=new NativeObservationPort.TransportSession("archived-date-fixture",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),BigInteger.ONE,"archived-date-fixture");
        Instant at=Instant.parse("2026-11-18T00:00:00Z");
        var custody=new NativeRequestChronology(session,UUID.fromString("00000000-0000-0000-0000-000000000001"),decoded.requestId(),
                NativeRequestChronology.PacketIdentity.of(request),NativeRequestChronology.PacketIdentity.of(framed),
                new NativeRequestChronology.Event(BigInteger.ONE,at),new NativeRequestChronology.Event(BigInteger.TWO,at.plusNanos(1)),
                new NativeRequestChronology.Event(BigInteger.valueOf(3),at.plusNanos(2)));
        return new NativeActionPort.AckReceived(decoded.requestId(),decoded.nativeOk(),Optional.of(new RawJson(decoded.result().token().orElseThrow().value())),
                new RawJson(decoded.payload().value()),framed,Optional.of(new NativeActionPort.OutboundPacket(decoded.requestId(),request)),Optional.of(custody));
    }
    @Test void actualCppTwoArmsRetainExactGenerationsAndContentWithoutIndependentConfirmation()throws Exception {
        for(String name:List.of("armed-generation1","armed-generation2")){
            byte[] raw=packet(name);var original=ack(raw);String step=result(tree(raw)).get("step").textValue();
            var assessed=DateSentinelArmResult.decode(original,step);assertEquals(DateSentinelArmResult.Disposition.ARMED,assessed.disposition());
            var actual=assessed.status().orElseThrow();assertEquals(name.endsWith("1")?"1":"2",actual.generation().decimal());
            assertEquals(24000,actual.startingDateRaw());assertEquals(name.endsWith("1")?24024:24048,actual.targetDateRaw());
            assertEquals(5,actual.speed());assertEquals(LateOutcome.Mode.TERMINAL_OR_SENTINEL,actual.mode());
            assertArrayEquals(raw,original.originalFrame().bytes());assertEquals(SentinelObservation.decode(status(tree(raw))),actual);
        }
    }
    @Test void actualQueryTriggeredAndCancelIdleKeepGenerationButCannotMasqueradeAsArmAcks()throws Exception {
        var triggered=SentinelObservation.decode(status(tree(packet("triggered-generation1"))));
        assertEquals(LateOutcome.State.TRIGGERED,triggered.state());assertEquals("1",triggered.generation().decimal());
        assertTrue(triggered.pauseObserved());assertEquals(List.of("date_deadline"),triggered.triggerReasons());
        var cancelled=SentinelObservation.decode(status(tree(packet("cancelled-generation2"))));
        assertEquals(LateOutcome.State.IDLE,cancelled.state());assertEquals("2",cancelled.generation().decimal());
        for(String name:List.of("triggered-generation1","cancelled-generation2"))
            assertThrows(IOException.class,()->DateSentinelArmResult.decode(ack(packet(name)),ARM));
        // Explicit DATA substitution: a later status in an ARM-shaped envelope cannot be promoted to ARMED.
        var later=tree(packet("armed-generation1"));result(later).set("tactical_daily_sentinel",status(tree(packet("triggered-generation1"))));
        assertEquals(DateSentinelArmResult.Disposition.UNKNOWN,DateSentinelArmResult.decode(ack(encode(later)),ARM).disposition());
    }
    @Test void canonicalStepStatusAndClosedSuccessFieldsRejectChangedData()throws Exception {
        for(String field:List.of("generation","starting_date_raw","target_date_raw","speed","army_count","combat_count")){
            var root=tree(packet("armed-generation1"));status(root).put(field,0);
            if(field.equals("army_count")||field.equals("combat_count"))status(root).put(field,1);
            assertThrows(IOException.class,()->DateSentinelArmResult.decode(ack(encode(root)),ARM),field);
        }
        var extra=tree(packet("armed-generation1"));result(extra).put("physical_save_confirmed",false);
        assertThrows(IOException.class,()->DateSentinelArmResult.decode(ack(encode(extra)),ARM));
        for(String step:List.of(ARM.replace("terminal","decision"),ARM.replace("a-0","a-1-12"),ARM.replace("24000","024000"),"pause-map"))
            assertThrows(IOException.class,()->DateSentinelArmResult.decode(ack(packet("armed-generation1")),step));
    }
    @Test void originalTokenCustodyAndOutboundAreMandatoryEvenForRealCppArmedBytes()throws Exception {
        var a=ack(packet("armed-generation1"));
        var changed=new NativeActionPort.AckReceived(a.requestId(),a.nativeOk(),Optional.of(new RawJson(new byte[]{'{','}'})),a.originalFrame(),a.originalPacket(),a.outbound(),a.custody());
        assertThrows(IOException.class,()->DateSentinelArmResult.decode(changed,ARM));
        var missing=new NativeActionPort.AckReceived(a.requestId(),a.nativeOk(),a.originalResultToken(),a.originalFrame(),a.originalPacket(),a.outbound(),Optional.empty());
        assertThrows(IOException.class,()->DateSentinelArmResult.decode(missing,ARM));
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(a,ARM));
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decodeDateArmRejection(a,ARM));
    }
    private static byte[] negative(String name)throws Exception {
        byte[] manifest=read("/date-arm1210/negative/","xar.native.date-arm1210.negative-fixtures","ACTUAL-CPP-DATE-NEGATIVE-PACKETS01.json");
        assertEquals("300f7a34512e1849359d423210e042c71472deb04de8f28407ea7e05e8cea20b",sha(manifest));
        for(var row:NativeWire.parse(manifest).get("packets"))if(name.equals(row.get("name").textValue())){
            byte[] raw=read("/date-arm1210/negative/","xar.native.date-arm1210.negative-fixtures",name+".json");
            assertEquals(row.get("bytes").intValue(),raw.length);assertEquals(row.get("sha256").textValue(),sha(raw));return raw;
        }
        throw new IOException("unlisted C++ negative");
    }
    @Test void actualCppTypedNegativeSerializationsKeepBeforeQueueDistinctFromUnknown()throws Exception {
        // Native production serializer typed scenarios; these do not claim a live/noGame ARM dispatch failed.
        for(String name:List.of("expired","indeterminate","attempted-rejected")){
            byte[] raw=negative(name);var original=ack(raw);var assessed=DateSentinelArmResult.decode(original,ARM);
            assertEquals(name.equals("expired")?DateSentinelArmResult.Disposition.REJECTED_BEFORE_QUEUE:DateSentinelArmResult.Disposition.UNKNOWN,assessed.disposition());
            assertTrue(assessed.status().isEmpty());assertArrayEquals(raw,original.originalFrame().bytes());
            assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(original,ARM));
            var changed=tree(raw);
            if(name.equals("expired"))changed.remove("error");else changed.put("error","full_clock_"+name);
            assertThrows(IOException.class,()->DateSentinelArmResult.decode(ack(encode(changed)),ARM));
        }
    }
    @Test void negativeTupleAndFalseClaimsCannotBecomeBeforeQueueRejection()throws Exception {
        for(String field:List.of("schema","game_version","executable_sha256","adapter_id","backend")){
            var root=tree(negative("expired"));result(root).put(field,"wrong");
            assertThrows(IOException.class,()->DateSentinelArmResult.decode(ack(encode(root)),ARM),field);
        }
        for(String field:List.of("complete_snapshot","physical_save_confirmed")){
            var root=tree(negative("expired"));result(root).put(field,true);
            assertThrows(IOException.class,()->DateSentinelArmResult.decode(ack(encode(root)),ARM),field);
        }
    }
}
