package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual frontend-only presentation DATA; only the central private permit can authorize foreground IO. */
public record FrontendWindowCaptureRequest(String requestId,Instant preparedAt,Instant deadline,Owner owner,
        ExactRef actualFrontendEvidence,ExactRef sourceRef,List<ExactRef> preparationEvidence,
        Window window,String foregroundRootBefore) {
    public static final String SCHEMA="xar.java-frontend-window-capture-request/v1";
    public record Owner(String machineId,String sessionId,long processId,String processBirthFiletime,
            String actualExecutableSha256,String connectionGeneration) {
        public Owner {
            StrictJson.text(machineId);StrictJson.text(sessionId);PresentationJson.u32(processId);StrictJson.require(processId>0,"actual frontend DWORD PID required");
            PresentationJson.u64(processBirthFiletime,true);PresentationJson.u64(connectionGeneration,false);
            StrictJson.require(actualExecutableSha256!=null&&actualExecutableSha256.matches("[0-9a-f]{64}"),"canonical actual executable SHA required");
        }
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.put("machine_id",machineId);n.put("session_id",sessionId);n.put("process_id",processId);
            n.put("process_birth_filetime",processBirthFiletime);n.put("actual_executable_sha256",actualExecutableSha256);n.put("connection_generation",connectionGeneration);return n;}
        public static Owner fromJson(JsonNode raw){ObjectNode n=StrictJson.object(raw,Set.of("machine_id","session_id","process_id","process_birth_filetime","actual_executable_sha256","connection_generation"));
            return new Owner(StrictJson.text(n.get("machine_id")),StrictJson.text(n.get("session_id")),PresentationJson.u32(n.get("process_id")),
                    StrictJson.text(n.get("process_birth_filetime")),StrictJson.text(n.get("actual_executable_sha256")),StrictJson.text(n.get("connection_generation")));}
    }
    public record ScreenRect(int left,int top,int right,int bottom){
        public ScreenRect {StrictJson.require((long)right-left==2560&&(long)bottom-top==1440,"original exact2560x1440 actual client screen rectangle required");}
        public int width(){return 2560;}public int height(){return 1440;}
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.put("left",left);n.put("top",top);n.put("right",right);n.put("bottom",bottom);return n;}
        public static ScreenRect fromJson(JsonNode raw){ObjectNode n=StrictJson.object(raw,Set.of("left","top","right","bottom"));
            return new ScreenRect(PresentationJson.i32(n.get("left")),PresentationJson.i32(n.get("top")),PresentationJson.i32(n.get("right")),PresentationJson.i32(n.get("bottom")));}
    }
    public record Window(String hwnd,ScreenRect clientRect){
        public Window {PresentationJson.u64(hwnd,true);Objects.requireNonNull(clientRect);}
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.put("hwnd",hwnd);n.set("client_rect",clientRect.toJson());return n;}
        public static Window fromJson(JsonNode raw){ObjectNode n=StrictJson.object(raw,Set.of("hwnd","client_rect"));return new Window(StrictJson.text(n.get("hwnd")),ScreenRect.fromJson(n.get("client_rect")));}
    }
    public FrontendWindowCaptureRequest {
        StrictJson.text(requestId);Objects.requireNonNull(preparedAt);Objects.requireNonNull(deadline);Objects.requireNonNull(owner);
        StrictJson.require(deadline.isAfter(preparedAt),"finite original presentation deadline required");
        StrictJson.require(actualFrontendEvidence!=null&&actualFrontendEvidence.bytes()>0&&sourceRef!=null&&sourceRef.bytes()>0,"actual frontend and selected implementation originals required");
        preparationEvidence=PresentationJson.refs(preparationEvidence);StrictJson.require(!preparationEvidence.isEmpty(),"complete original preparation evidence required");
        Objects.requireNonNull(window);PresentationJson.u64(foregroundRootBefore,false);
    }
    public TransportKind transportKind(){return TransportKind.WIN32_FRONTEND_CAPTURE;}
    public int physicalRequestCount(){return 1;}public int nativePipeRequestCount(){return 0;}
    static ObjectNode envelope(String schema){ObjectNode n=StrictJson.object();n.put("schema",schema);n.put("transport",TransportKind.WIN32_FRONTEND_CAPTURE.name());return n;}
    static ObjectNode envelope(JsonNode raw,Set<String> fields,String schema){ObjectNode n=StrictJson.object(raw,fields);
        StrictJson.require(StrictJson.text(n.get("schema")).equals(schema)&&StrictJson.text(n.get("transport")).equals(TransportKind.WIN32_FRONTEND_CAPTURE.name()),"exact frontend window capture schema/plane required");return n;}
    public ObjectNode toJson(){
        ObjectNode n=envelope(SCHEMA);n.put("request_id",requestId);n.put("prepared_at",preparedAt.toString());n.put("deadline",deadline.toString());n.set("owner",owner.toJson());
        n.set("actual_frontend_evidence",actualFrontendEvidence.toJson());n.set("source_ref",sourceRef.toJson());PresentationJson.refs(n,"preparation_evidence",preparationEvidence);
        n.set("window",window.toJson());n.put("foreground_root_before",foregroundRootBefore);return n;
    }
    public byte[] encode(){return StrictJson.canonical(toJson());}
    public static FrontendWindowCaptureRequest decode(byte[] raw){return fromJson(StrictJson.parse(raw));}
    public static FrontendWindowCaptureRequest fromJson(JsonNode raw){
        ObjectNode n=envelope(raw,Set.of("schema","transport","request_id","prepared_at","deadline","owner","actual_frontend_evidence","source_ref","preparation_evidence","window","foreground_root_before"),SCHEMA);
        return new FrontendWindowCaptureRequest(StrictJson.text(n.get("request_id")),PresentationJson.time(n.get("prepared_at")),PresentationJson.time(n.get("deadline")),Owner.fromJson(n.get("owner")),
                ExactRef.fromJson(n.get("actual_frontend_evidence")),ExactRef.fromJson(n.get("source_ref")),PresentationJson.refs(n.get("preparation_evidence")),Window.fromJson(n.get("window")),StrictJson.text(n.get("foreground_root_before")));
    }
}
