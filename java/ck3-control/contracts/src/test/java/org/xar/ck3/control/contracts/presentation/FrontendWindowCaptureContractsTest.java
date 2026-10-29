package org.xar.ck3.control.contracts.presentation;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

class FrontendWindowCaptureContractsTest {
    static final Instant NOW=Instant.parse("2026-10-24T04:40:00Z");
    static ExactRef ref(byte[] raw){try{return new ExactRef("D:/software-fixture/original",raw.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));}
        catch(Exception e){throw new IllegalStateException(e);}}
    static FrontendWindowCaptureRequest request(){
        ExactRef original=ref(new byte[]{1});
        return new FrontendWindowCaptureRequest("original-window-request",NOW,NOW.plusSeconds(10),
            new FrontendWindowCaptureRequest.Owner("software-fixture","frontend-session",42,"18446744073709551615","1".repeat(64),"9007199254740993"),
            original,original,List.of(original),new FrontendWindowCaptureRequest.Window("18446744073709551615",
                new FrontendWindowCaptureRequest.ScreenRect(-2560,-1440,0,0)),"18446744073709551615");
    }
    static FrontendWindowCaptureOutcome verified(){
        var r=request();return new FrontendWindowCaptureOutcome(r,ref(r.encode()),FrontendWindowCaptureOutcome.Status.VERIFIED,Optional.of(NOW),NOW,
                r.window(),Optional.of(r.window()),r.foregroundRootBefore(),Optional.of(r.window().hwnd()),Optional.of(FrontendWindowCaptureOutcome.ActivationMode.ALREADY_FOREGROUND),
                0,0,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),List.of());
    }
    @Test void frontendOnlyRoundtripPreservesNegativeScreenAndFullUint64(){
        var r=request();assertEquals(r,FrontendWindowCaptureRequest.decode(r.encode()));
        assertFalse(r.toJson().has("actor"));assertFalse(r.toJson().has("episode"));assertEquals(0,r.nativePipeRequestCount());assertEquals(TransportKind.WIN32_FRONTEND_CAPTURE,r.transportKind());
        var actual=verified();actual.verifyOriginalRequest(r.encode());assertEquals(actual,FrontendWindowCaptureOutcome.decode(actual.encode()));
        assertTrue(actual.presentationOnly());assertFalse(actual.usesOcr());assertFalse(actual.usesMouse());assertFalse(actual.usesKeyboard());
        assertThrows(RuntimeException.class,()->FrontendWindowCaptureRequest.decode(PresentationContractsTest.request().encode()));
        assertThrows(RuntimeException.class,()->PresentationRequest.decode(r.encode()));
    }
    @Test void rejectMissingBoolFloatWrongPlaneUint64AndOverflowRect(){
        var n=request().toJson();n.put("transport","PRESENTATION_MMAP");var a=n;assertThrows(RuntimeException.class,()->FrontendWindowCaptureRequest.fromJson(a));
        n=request().toJson();n.remove("actual_frontend_evidence");var b=n;assertThrows(RuntimeException.class,()->FrontendWindowCaptureRequest.fromJson(b));
        n=request().toJson();n.with("owner").put("process_id",42.0);var c=n;assertThrows(RuntimeException.class,()->FrontendWindowCaptureRequest.fromJson(c));
        n=request().toJson();n.with("window").put("hwnd",true);var d=n;assertThrows(RuntimeException.class,()->FrontendWindowCaptureRequest.fromJson(d));
        n=request().toJson();n.with("owner").put("process_birth_filetime","018446744073709551615");var e=n;assertThrows(RuntimeException.class,()->FrontendWindowCaptureRequest.fromJson(e));
        assertThrows(RuntimeException.class,()->new FrontendWindowCaptureRequest.ScreenRect(Integer.MAX_VALUE,0,Integer.MIN_VALUE+2559,1440));
        assertThrows(RuntimeException.class,()->new FrontendWindowCaptureRequest.ScreenRect(0,0,2559,1440));
    }
    @Test void actualZeroWriteRejectionIsSeparateFromUnknownAndAttachedSuccess(){
        var r=request();var unknown=new FrontendWindowCaptureOutcome(r,ref(r.encode()),FrontendWindowCaptureOutcome.Status.UNKNOWN,Optional.of(NOW),NOW,
            r.window(),Optional.empty(),r.foregroundRootBefore(),Optional.empty(),Optional.empty(),0,0,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("foreground result unknown"),List.of());
        assertEquals(unknown,FrontendWindowCaptureOutcome.decode(unknown.encode()));
        var n=unknown.toJson();n.put("status","OBSERVED_REJECTED");var rejected=n;assertThrows(RuntimeException.class,()->FrontendWindowCaptureOutcome.decode(StrictJson.canonical(rejected)));
        n=verified().toJson();n.put("mode","ATTACHED_FOREGROUND_THREAD");n.put("attached_foreground_thread",99);n.put("detach_succeeded",false);var bad=n;
        assertThrows(RuntimeException.class,()->FrontendWindowCaptureOutcome.decode(StrictJson.canonical(bad)));
        var original=verified().toJson();original.put("mode","ATTACHED_FOREGROUND_THREAD");original.put("attached_foreground_thread",99);original.put("detach_succeeded",true);
        assertEquals(FrontendWindowCaptureOutcome.ActivationMode.ATTACHED_FOREGROUND_THREAD,FrontendWindowCaptureOutcome.decode(StrictJson.canonical(original)).mode().orElseThrow());
    }
}
