package org.xar.ck3.control.contracts.presentation;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.ArtifactRole;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.OriginalArtifact;

class PresentationContractsTest {
    static final Instant NOW=Instant.parse("2026-10-24T04:10:00Z");
    static ExactRef ref(String name,byte[] raw){
        try{return new ExactRef("D:/software-fixture/"+name,raw.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));}
        catch(Exception e){throw new IllegalStateException(e);}
    }
    static PresentationRequest request(){
        return new PresentationRequest("original-action-request",NOW,
            new PresentationRequest.Owner("software-fixture-machine","session",1234,"18446744073709551615",PresentationRequest.EXECUTABLE_SHA256,"episode","18446744073709551615"),
            new PresentationRequest.Frame("actual-snapshot","18446744073709551615","9007199254740993",7,1066),
            PresentationRequest.Mode.REALM,2,4,6,"18446744073709551615","18446744073709551615",
            Float.floatToRawIntBits(.32f),"",Optional.empty(),List.of(ref("actual-preparation",new byte[]{1})));
    }
    @Test void exactRequestSerdeNativeOffsetsAndUnsignedIdentity(){
        PresentationRequest r=request();assertEquals(r,PresentationRequest.decode(r.encode()));
        assertEquals("18446744073709551615",PresentationRequest.decode(r.encode()).owner().processBirthFiletime());
        byte[] raw=r.nativeBytes();ByteBuffer b=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
        assertEquals(168,raw.length);assertEquals(1,b.getInt(0));assertEquals(7,b.getInt(4));assertEquals(1066,b.getInt(8));
        assertEquals(0,b.getInt(12));assertEquals(-1L,b.getLong(16));assertEquals(-1L,b.getLong(24));assertEquals(Float.floatToRawIntBits(.32f),b.getInt(32));
        assertEquals(1,r.physicalRequestCount());assertEquals(0,r.nativePipeRequestCount());assertEquals(168,r.requestPayloadBytes());
        OriginalArtifact original=new OriginalArtifact(ArtifactRole.REQUEST,raw);raw[0]=9;assertEquals(1,original.bytes()[0]);assertEquals(original,new OriginalArtifact(ArtifactRole.REQUEST,r.nativeBytes()));
    }
    @Test void rejectWrongTypesMissingFieldsNullExtraSchemaAndNativeAlias(){
        var n=request().toJson();n.put("request_sequence",4.0);var a=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(a));
        n=request().toJson();n.put("request_sequence",true);var b=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(b));
        n=request().toJson();n.with("owner").put("process_birth_filetime",1844674407370955161L);var c=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(c));
        n=request().toJson();n.put("schema","xar.java-presentation-request/v0");var d=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(d));
        n=request().toJson();n.put("transport","NATIVE_PIPE");var e=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(e));
        n=request().toJson();n.remove("tracking");var f=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(f));
        n=request().toJson();n.putNull("title_key");var g=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(g));
        n=request().toJson();n.put("native_ok",true);var h=n;assertThrows(RuntimeException.class,()->PresentationRequest.fromJson(h));
    }
    @Test void postedIsSeparateFromAckAndUnknownRetainsOriginal(){
        PresentationRequest r=request();ExactRef payload=ref("request",r.nativeBytes());
        byte[] before=header(r,2,6),after=header(r,4,6);
        var evidence=new OriginalOutcome.PostEvidence(r.owner(),r.requestId(),NOW,2,4,ref("before",before),ref("after",after),payload,Optional.empty());
        var post=new OriginalOutcome.Posted(r,NOW,payload,Optional.empty(),ref("post",evidence.encode()));
        evidence.requireMatches(post);post.verifyOriginal(r.nativeBytes(),Optional.empty(),evidence.encode(),before,after);assertEquals(post,OriginalOutcome.decode(post.encode()));
        var unknown=new OriginalOutcome.Unknown(r,NOW,OriginalOutcome.Phase.ODD_STORED,"write outcome unknown",List.of(payload));
        assertEquals(unknown,OriginalOutcome.decode(unknown.encode()));assertEquals(r.requestId(),unknown.requestId());
        assertFalse(PresentationObservation.class.isAssignableFrom(post.getClass()));
        assertThrows(RuntimeException.class,()->OriginalOutcome.decode(StrictJson.canonical(request().toJson())));
    }
    static byte[] header(PresentationRequest r,long requestSeq,long resultSeq){
        return ByteBuffer.allocate(24).order(ByteOrder.LITTLE_ENDIAN).putInt(PresentationRequest.MAGIC).putInt(1).putInt((int)r.owner().processId()).putInt(0).putInt((int)requestSeq).putInt((int)resultSeq).array();
    }
    static PresentationObservation.Capture capture(PresentationRequest r,long resultSeq,byte[] head,byte[] result,byte[] diag){
        return new PresentationObservation.Capture(r.owner(),NOW,4,resultSeq,resultSeq,ref("header",head),ref("result",result),ref("diag",diag));
    }
    @Test void acknowledgeOnlyOriginalRequestAndEvenFreshResultWithRawBytes(){
        PresentationRequest r=request();byte[] head=header(r,4,8),result=new byte[65640],diag=new byte[168];
        ByteBuffer.wrap(result).order(ByteOrder.LITTLE_ENDIAN).putInt(4).putInt(1);
        var capture=capture(r,8,head,result,diag);
        var actual=PresentationObservation.fromOriginal(r,capture,head,result,diag);
        assertInstanceOf(PresentationObservation.Acknowledged.class,actual);
        assertEquals(PresentationObservation.Status.SUBMITTED,((PresentationObservation.Acknowledged)actual).status());
        assertEquals(actual,PresentationObservation.decode(actual.encode()));
        byte[] changed=result.clone();changed[0]=6;
        assertThrows(RuntimeException.class,()->((PresentationObservation.Acknowledged)actual).verifyOriginal(head,changed,diag));
        ByteBuffer.wrap(result).order(ByteOrder.LITTLE_ENDIAN).putInt(2);
        assertInstanceOf(PresentationObservation.Pending.class,PresentationObservation.fromOriginal(r,capture(r,8,head,result,diag),head,result,diag));
        byte[] odd=header(r,4,9);assertInstanceOf(PresentationObservation.Pending.class,PresentationObservation.fromOriginal(r,capture(r,9,odd,result,diag),odd,result,diag));
        byte[] torn=result.clone();java.util.Arrays.fill(torn,(byte)0xff);new OriginalArtifact(ArtifactRole.RESULT,torn);
        assertInstanceOf(PresentationObservation.Pending.class,PresentationObservation.fromOriginal(r,capture(r,9,odd,torn,diag),odd,torn,diag));
        var changedCapture=new PresentationObservation.Capture(r.owner(),NOW,4,8,10,ref("header",head),ref("torn",torn),ref("diag",diag));
        assertInstanceOf(PresentationObservation.Pending.class,PresentationObservation.fromOriginal(r,changedCapture,head,torn,diag));
        assertThrows(RuntimeException.class,()->PresentationObservation.Status.fromWire(9));
    }
    @Test void originalRolesRejectNativeWireWrongRegionsAndUnboundedPayload(){
        assertThrows(RuntimeException.class,()->new OriginalArtifact(ArtifactRole.HEADER,"{\"type\":\"ack\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(RuntimeException.class,()->new OriginalArtifact(ArtifactRole.REQUEST,new byte[167]));
        assertThrows(RuntimeException.class,()->new OriginalArtifact(ArtifactRole.POST_METADATA,new byte[16385]));
        byte[] raw=request().nativeBytes();ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).putInt(12,1);
        assertDoesNotThrow(()->new OriginalArtifact(ArtifactRole.REQUEST,raw)); // partial-post raw custody is not a posted request
        PresentationOriginals unavailable=new PresentationOriginals(){};
        assertThrows(IllegalStateException.class,()->unavailable.preservePresentationArtifact(new OriginalArtifact(ArtifactRole.REQUEST,request().nativeBytes())));
    }
    @Test void trackedWireSharesOriginalSequenceAndKeepsUInt64AndFiniteScope(){
        var r=request();var tracking=new PresentationRequest.Tracking("18446744073709551615","9007199254740993",22,1066,1067,List.of(new PresentationRequest.Province(2,"b_original")));
        var t=new PresentationRequest(r.requestId(),r.preparedAt(),r.owner(),r.frame(),PresentationRequest.Mode.TRACKED_HOTSPOT,2,4,6,r.expiresUptimeMs(),r.hwnd(),r.paddingFloatBits(),"",Optional.of(tracking),r.preparationEvidence());
        assertEquals(t,PresentationRequest.decode(t.encode()));byte[] raw=t.trackingBytes().orElseThrow();
        assertEquals(4264,raw.length);ByteBuffer b=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
        assertEquals(4,b.getInt(0));assertEquals(1,b.getInt(4));assertEquals(-1L,b.getLong(8));assertEquals(9007199254740993L,b.getLong(16));assertEquals(2,b.getInt(40));
        assertEquals(4432,t.requestPayloadBytes());new OriginalArtifact(ArtifactRole.TRACKING_REQUEST,raw);
        assertEquals(0,PresentationRequest.nextSequence(0xffff_fffeL));
    }
}
