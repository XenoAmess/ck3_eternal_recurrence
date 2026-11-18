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
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Original C++ ACK bytes plus explicitly synthetic archived correlation metadata. No live endpoint custody, Full, Permit or private receipt is made. */
final class FullSnapshotClockControlResultCppProducerTest {
    private static final String RESOURCE="/org/xar/ck3/control/nativebridge/full-clock1210/";
    private record Sample(String name,int bytes,String sha){ }
    private static final List<Sample> SAMPLES=List.of(
            new Sample("submitted",531,"77f8f6680338ebda5030ed01a53ffcf66d0f942d5e61d4547561f988899209ef"),
            new Sample("save",670,"39b71f7ec0baf811e18256cc1cac2fdf4b2e8e6523370b8ef41b77d57485e264"),
            new Sample("expired",553,"378077bfec96774029e25ce1e74708de53c7df63b1e8fd3cbd5b763944346e2a"),
            new Sample("indeterminate",533,"fc9b6e338c2fb775950830e0a2c8437df6c862c4a9c406635cf9feb595f2ffd0"),
            new Sample("attempted-rejected",529,"40b1407689e45d5ba4c18309c83f81382b0d381120545dae66ba75e80adfac71"));
    private static byte[] resource(String name)throws IOException {
        try(var in=FullSnapshotClockControlResultCppProducerTest.class.getResourceAsStream(RESOURCE+name)){
            if(in!=null)return in.readAllBytes();
        }
        String root=System.getProperty("xar.native.full-clock1210.fixtures");
        if(root==null||root.isBlank()||!Path.of(root).isAbsolute())throw new IOException("NOT_RUN: classpath full-clock1210 resources or absolute fixture fallback required");
        return Files.readAllBytes(Path.of(root).resolve(name));
    }
    private static byte[] packet(String name)throws Exception {
        byte[] manifest=resource("FULL-CLOCK-ACK-PRODUCER01.json");
        assertEquals(3873,manifest.length);assertEquals("58055e9ba6216b74c8b36227e428922245551fd427d95422aa7d3e4e89109025",sha(manifest));
        var sample=SAMPLES.stream().filter(value->value.name().equals(name)).findFirst().orElseThrow();
        byte[] raw=resource("full-clock-ack-"+name+"01.json");assertEquals(sample.bytes(),raw.length);assertEquals(sample.sha(),sha(raw));return raw;
    }
    private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    private static byte[] encode(ObjectNode object)throws IOException{return org.xar.ck3.control.contracts.FullJsonTree.encode(object,65536);}
    private static ObjectNode tree(byte[] bytes)throws IOException{return NativeWire.object(NativeWire.parse(bytes));}
    private static ObjectNode result(ObjectNode root)throws IOException{return NativeWire.object(root.get("result"));}
    private static NativeRequestChronology correlation(byte[] request,byte[] response,String id){
        // Historical public DATA values only. These event labels do not claim a Java endpoint performed any operation.
        var session=new NativeObservationPort.TransportSession("archived-clock-fixture",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),BigInteger.ONE,"archived-clock-fixture");
        Instant at=Instant.parse("2026-11-18T00:00:00Z");
        return new NativeRequestChronology(session,UUID.fromString("00000000-0000-0000-0000-000000000001"),id,
                NativeRequestChronology.PacketIdentity.of(request),NativeRequestChronology.PacketIdentity.of(response),
                new NativeRequestChronology.Event(BigInteger.ONE,at),new NativeRequestChronology.Event(BigInteger.TWO,at.plusNanos(1)),
                new NativeRequestChronology.Event(BigInteger.valueOf(3),at.plusNanos(2)));
    }
    private static NativeActionPort.AckReceived ack(byte[] raw)throws IOException {
        byte[] framed=NativeWire.packet(raw);var decoded=(NativeWire.CommandResult)NativeWire.decode(framed);
        String step=NativeWire.text(result(tree(raw)).get("step"));
        byte[] request=NativeWire.execute(decoded.requestId(),step,BigInteger.ONE,new byte[]{'{','}'});
        return new NativeActionPort.AckReceived(decoded.requestId(),decoded.nativeOk(),
                Optional.of(new RawJson(decoded.result().token().orElseThrow().value())),new RawJson(decoded.payload().value()),framed,
                Optional.of(new NativeActionPort.OutboundPacket(decoded.requestId(),request)),Optional.of(correlation(request,framed,decoded.requestId())));
    }
    private static FullSnapshotClockControlResult.Assessment assess(String name)throws Exception {
        byte[] raw=packet(name);var original=ack(raw);byte[] before=original.originalPacket();
        var assessment=FullSnapshotClockControlResult.decode(original,NativeWire.text(result(tree(raw)).get("step")));
        assertArrayEquals(before,original.originalPacket());assertArrayEquals(raw,original.originalFrame().bytes());
        var wire=(NativeWire.CommandResult)NativeWire.decode(original.originalPacket());
        assertArrayEquals(wire.result().token().orElseThrow().value(),original.originalResultToken().orElseThrow().bytes());return assessment;
    }
    private static void reject(String sample,Consumer<ObjectNode> change)throws Exception {
        var root=tree(packet(sample));change.accept(root);var original=ack(encode(root));
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(original,"save".equals(sample)?"save-checkpoint":"set-speed-3"));
    }

    @Test void actualCppSubmittedAndSaveAcksRetainSubmissionWithoutClaimingAnyPhysicalSave()throws Exception {
        var submitted=assess("submitted");assertEquals(FullSnapshotClockControlResult.Disposition.SUBMITTED,submitted.disposition());
        assertEquals("set-speed-3",submitted.step());assertEquals("submitted",submitted.queueStatus());
        assertTrue(submitted.effectAttempted());assertTrue(submitted.fullBeforeVerified());assertTrue(submitted.submission().isEmpty());
        var save=assess("save");assertEquals(FullSnapshotClockControlResult.Disposition.SUBMITTED,save.disposition());
        assertEquals("save-checkpoint",save.step());var actual=save.submission().orElseThrow();
        assertEquals(BigInteger.valueOf(19),actual.sequence());assertEquals("xar_checkpoint",actual.requestedSaveName());
        assertEquals(123456,actual.dateRaw());assertEquals("submitted",actual.status());assertEquals("xar_checkpoint",actual.saveName());
        var raw=result(tree(packet("save")));assertFalse(raw.get("complete_snapshot").booleanValue());assertFalse(raw.get("physical_save_confirmed").booleanValue());
    }

    @Test void actualCppExpiredProvesOnlyTheExplicitBeforeQueueRejectionAndPreservesItsError()throws Exception {
        var expired=assess("expired");assertEquals(FullSnapshotClockControlResult.Disposition.REJECTED_BEFORE_QUEUE,expired.disposition());
        assertEquals("expired",expired.queueStatus());assertFalse(expired.effectAttempted());assertFalse(expired.fullBeforeVerified());
        assertTrue(expired.submission().isEmpty());assertEquals("full_clock_expired",tree(packet("expired")).get("error").textValue());
    }

    @Test void actualCppIndeterminateAndAttemptedRejectionStayUnknownEvenWithNativeOkFalse()throws Exception {
        for(String name:List.of("indeterminate","attempted-rejected")){
            var assessed=assess(name);assertEquals(FullSnapshotClockControlResult.Disposition.UNKNOWN,assessed.disposition());
            assertFalse(ack(packet(name)).nativeOk());assertTrue(assessed.submission().isEmpty());
            assertFalse(tree(packet(name)).has("error"));
        }
        assertFalse(assess("indeterminate").effectAttempted(),"indeterminate false does not prove zero queue entry");
        assertTrue(assess("attempted-rejected").effectAttempted(),"a failed native result cannot erase the recorded effect attempt");
    }

    @Test void packetTokenOutboundAndRetainedChronologyCorrelationsCannotBeSubstituted()throws Exception {
        var original=ack(packet("submitted"));
        var badToken=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),Optional.of(new RawJson(new byte[]{'{','}'})),
                original.originalFrame(),original.originalPacket(),original.outbound(),original.custody());
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(badToken,"set-speed-3"));
        var missing=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),original.originalResultToken(),original.originalFrame(),
                original.originalPacket(),original.outbound(),Optional.empty());
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(missing,"set-speed-3"));
        byte[] other=NativeWire.execute(original.requestId(),"set-speed-4",BigInteger.ONE,new byte[]{'{','}'});
        var badHash=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),original.originalResultToken(),original.originalFrame(),
                original.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket(original.requestId(),other)),original.custody());
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(badHash,"set-speed-3"));
        var wrongStep=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),original.originalResultToken(),original.originalFrame(),
                original.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket(original.requestId(),other)),Optional.of(correlation(other,original.originalPacket(),original.requestId())));
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(wrongStep,"set-speed-3"));
        var badEnvelope=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),original.originalResultToken(),new RawJson(new byte[]{'{','}'}),
                original.originalPacket(),original.outbound(),original.custody());
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(badEnvelope,"set-speed-3"));
        assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(original,"normal-exit-application-v1"));
    }

    @Test void malformedTuplesFalseClaimsUnknownStatusAndInconsistentErrorsCannotBecomeAQueueDisposition()throws Exception {
        reject("submitted",root->resultUnchecked(root).put("schema","ck3_1210_core_clock_control_result_v1"));
        reject("submitted",root->resultUnchecked(root).put("game_version","1.21.0.0"));
        reject("submitted",root->resultUnchecked(root).put("executable_sha256",ExactCk3Build.CK3_12004.executableSha256()));
        reject("submitted",root->resultUnchecked(root).put("adapter_id","ck3-1.20.0.4-msvc-x64"));
        reject("submitted",root->resultUnchecked(root).put("backend","native-headless"));
        reject("submitted",root->resultUnchecked(root).put("complete_snapshot",true));
        reject("submitted",root->resultUnchecked(root).put("physical_save_confirmed",true));
        reject("submitted",root->resultUnchecked(root).put("effect_attempted",false));
        reject("submitted",root->resultUnchecked(root).put("full_snapshot_before_verified",false));
        reject("submitted",root->resultUnchecked(root).put("accepted",false));
        reject("submitted",root->resultUnchecked(root).put("queue_status","invented_no_effect"));
        reject("submitted",root->resultUnchecked(root).put("effect_attempted",1));
        reject("submitted",root->resultUnchecked(root).put("future_alias",true));
        reject("submitted",root->root.put("error","full_clock_rejected"));
        reject("expired",root->root.put("error","full_clock_rejected"));
        reject("expired",root->root.remove("error"));
        reject("indeterminate",root->root.put("error","full_clock_indeterminate"));
    }

    @Test void saveFieldsAreClosedAndAnAlreadySatisfiedDataVariantStillCannotBecomeNoopOrRetryPermission()throws Exception {
        reject("save",root->resultUnchecked(root).put("save_name","other_save"));
        reject("save",root->resultUnchecked(root).put("status","confirmed"));
        reject("save",root->((ObjectNode)resultUnchecked(root).get("submission")).put("sequence",0));
        reject("save",root->((ObjectNode)resultUnchecked(root).get("submission")).put("sequence",new BigInteger("18446744073709551616")));
        reject("save",root->((ObjectNode)resultUnchecked(root).get("submission")).put("sequence",true));
        reject("save",root->((ObjectNode)resultUnchecked(root).get("submission")).put("date_raw",2147483648L));
        reject("save",root->((ObjectNode)resultUnchecked(root).get("submission")).put("requested_save_name","other_save"));
        reject("save",root->resultUnchecked(root).remove("submission"));
        reject("submitted",root->resultUnchecked(root).put("save_name","xar_checkpoint"));
        // Conservative classification of a hypothetical DATA variant; this is not another Native positive oracle.
        var satisfied=tree(packet("submitted"));resultUnchecked(satisfied).put("queue_status","already_satisfied").put("effect_attempted",false);
        var assessed=FullSnapshotClockControlResult.decode(ack(encode(satisfied)),"set-speed-3");
        assertEquals(FullSnapshotClockControlResult.Disposition.UNKNOWN,assessed.disposition());assertFalse(assessed.effectAttempted());
    }
    private static ObjectNode resultUnchecked(ObjectNode root){return (ObjectNode)root.get("result");}
}
