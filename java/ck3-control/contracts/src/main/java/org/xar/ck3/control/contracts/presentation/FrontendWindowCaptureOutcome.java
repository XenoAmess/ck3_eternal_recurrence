package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Win32 presentation facts. No NativeWire ACK, gameplay effect or pixel/native route qualification. */
public record FrontendWindowCaptureOutcome(FrontendWindowCaptureRequest request,ExactRef originalRequest,
        Status status,Optional<Instant> writeEnteredAt,Instant observedAt,
        FrontendWindowCaptureRequest.Window windowBefore,Optional<FrontendWindowCaptureRequest.Window> windowAfter,
        String foregroundBefore,Optional<String> foregroundAfter,Optional<ActivationMode> mode,
        long attachedForegroundThread,long attachedTargetThread,Optional<Boolean> detachSucceeded,
        Optional<String> directActivationError,Optional<String> attachedActivationError,Optional<String> failure,List<ExactRef> originals) {
    public static final String SCHEMA="xar.java-frontend-window-capture-outcome/v1";
    public enum Status { UNKNOWN,OBSERVED_REJECTED,VERIFIED }
    public enum ActivationMode { ALREADY_FOREGROUND,DIRECT,ATTACHED_FOREGROUND_THREAD }
    public FrontendWindowCaptureOutcome {
        Objects.requireNonNull(request);StrictJson.require(originalRequest!=null&&originalRequest.bytes()>0,"actual original prepared request reference required");
        Objects.requireNonNull(status);writeEnteredAt=Objects.requireNonNull(writeEnteredAt);Objects.requireNonNull(observedAt);
        Objects.requireNonNull(windowBefore);windowAfter=Objects.requireNonNull(windowAfter);
        PresentationJson.u64(foregroundBefore,false);foregroundAfter=Objects.requireNonNull(foregroundAfter);foregroundAfter.ifPresent(v->PresentationJson.u64(v,false));
        mode=Objects.requireNonNull(mode);PresentationJson.u32(attachedForegroundThread);PresentationJson.u32(attachedTargetThread);
        detachSucceeded=Objects.requireNonNull(detachSucceeded);directActivationError=Objects.requireNonNull(directActivationError);attachedActivationError=Objects.requireNonNull(attachedActivationError);
        failure=Objects.requireNonNull(failure);directActivationError.ifPresent(StrictJson::text);attachedActivationError.ifPresent(StrictJson::text);failure.ifPresent(StrictJson::text);
        originals=PresentationJson.refs(originals);
        StrictJson.require(windowBefore.equals(request.window())&&foregroundBefore.equals(request.foregroundRootBefore()),"outcome changed actual preflight original");
        StrictJson.require(!observedAt.isBefore(request.preparedAt()),"outcome predates original preparation");
        writeEnteredAt.ifPresent(t->StrictJson.require(!t.isBefore(request.preparedAt())&&!t.isAfter(observedAt),"actual presentation chronology differs"));
        if(status==Status.OBSERVED_REJECTED)StrictJson.require(writeEnteredAt.isEmpty()&&failure.isPresent(),"only actual zero-write rejection may release the posting boundary");
        if(status==Status.UNKNOWN)StrictJson.require(failure.isPresent(),"unresolved original failure reason required; never retry");
        if(status==Status.VERIFIED){
            StrictJson.require(writeEnteredAt.isPresent()&&failure.isEmpty()&&windowAfter.isPresent()&&windowAfter.orElseThrow().equals(windowBefore)
                    &&foregroundAfter.isPresent()&&foregroundAfter.orElseThrow().equals(windowBefore.hwnd())&&mode.isPresent(),"verified actual stable foreground/client facts required");
            if(mode.orElseThrow()==ActivationMode.ALREADY_FOREGROUND)StrictJson.require(foregroundBefore.equals(windowBefore.hwnd()),"already-foreground requires actual original equality");
            if(mode.orElseThrow()==ActivationMode.ATTACHED_FOREGROUND_THREAD)
                StrictJson.require(attachedForegroundThread>0&&detachSucceeded.equals(Optional.of(true)),"verified attached activation requires actual successful detach");
            else StrictJson.require(attachedForegroundThread==0&&attachedTargetThread==0&&detachSucceeded.isEmpty()&&attachedActivationError.isEmpty(),"nonattached activation cannot invent thread/detach facts");
        }
    }
    public String requestId(){return request.requestId();}
    public TransportKind transportKind(){return TransportKind.WIN32_FRONTEND_CAPTURE;}
    public boolean presentationOnly(){return true;}public boolean usesOcr(){return false;}public boolean usesKeyboard(){return false;}public boolean usesMouse(){return false;}
    public void verifyOriginalRequest(byte[] bytes){PresentationJson.original(originalRequest,bytes);StrictJson.require(java.util.Arrays.equals(bytes,request.encode()),"actual prepared window request differs");}
    public ObjectNode toJson(){
        ObjectNode n=FrontendWindowCaptureRequest.envelope(SCHEMA);n.set("request",request.toJson());n.set("original_request",originalRequest.toJson());n.put("status",status.name());
        if(writeEnteredAt.isPresent())n.put("write_entered_at",writeEnteredAt.orElseThrow().toString());else n.putNull("write_entered_at");n.put("observed_at",observedAt.toString());
        n.set("window_before",windowBefore.toJson());if(windowAfter.isPresent())n.set("window_after",windowAfter.orElseThrow().toJson());else n.putNull("window_after");
        n.put("foreground_before",foregroundBefore);if(foregroundAfter.isPresent())n.put("foreground_after",foregroundAfter.orElseThrow());else n.putNull("foreground_after");
        if(mode.isPresent())n.put("mode",mode.orElseThrow().name());else n.putNull("mode");n.put("attached_foreground_thread",attachedForegroundThread);n.put("attached_target_thread",attachedTargetThread);
        if(detachSucceeded.isPresent())n.put("detach_succeeded",detachSucceeded.orElseThrow());else n.putNull("detach_succeeded");
        nullable(n,"direct_activation_error",directActivationError);nullable(n,"attached_activation_error",attachedActivationError);nullable(n,"failure",failure);PresentationJson.refs(n,"originals",originals);return n;
    }
    private static void nullable(ObjectNode n,String key,Optional<String> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
    private static Optional<String> nullableText(ObjectNode n,String key){JsonNode v=n.get(key);return v.isNull()?Optional.empty():Optional.of(StrictJson.text(v));}
    public byte[] encode(){return StrictJson.canonical(toJson());}
    public static FrontendWindowCaptureOutcome decode(byte[] bytes){
        ObjectNode n=FrontendWindowCaptureRequest.envelope(StrictJson.parse(bytes),Set.of("schema","transport","request","original_request","status","write_entered_at","observed_at",
                "window_before","window_after","foreground_before","foreground_after","mode","attached_foreground_thread","attached_target_thread","detach_succeeded",
                "direct_activation_error","attached_activation_error","failure","originals"),SCHEMA);
        Optional<Boolean> detached;if(n.get("detach_succeeded").isNull())detached=Optional.empty();else {StrictJson.require(n.get("detach_succeeded").isBoolean(),"exact nullable detach boolean required");detached=Optional.of(n.get("detach_succeeded").booleanValue());}
        return new FrontendWindowCaptureOutcome(FrontendWindowCaptureRequest.fromJson(n.get("request")),ExactRef.fromJson(n.get("original_request")),Status.valueOf(StrictJson.text(n.get("status"))),
                n.get("write_entered_at").isNull()?Optional.empty():Optional.of(PresentationJson.time(n.get("write_entered_at"))),PresentationJson.time(n.get("observed_at")),
                FrontendWindowCaptureRequest.Window.fromJson(n.get("window_before")),n.get("window_after").isNull()?Optional.empty():Optional.of(FrontendWindowCaptureRequest.Window.fromJson(n.get("window_after"))),
                StrictJson.text(n.get("foreground_before")),nullableText(n,"foreground_after"),n.get("mode").isNull()?Optional.empty():Optional.of(ActivationMode.valueOf(StrictJson.text(n.get("mode")))),
                PresentationJson.u32(n.get("attached_foreground_thread")),PresentationJson.u32(n.get("attached_target_thread")),detached,nullableText(n,"direct_activation_error"),nullableText(n,"attached_activation_error"),nullableText(n,"failure"),PresentationJson.refs(n.get("originals")));
    }
}
