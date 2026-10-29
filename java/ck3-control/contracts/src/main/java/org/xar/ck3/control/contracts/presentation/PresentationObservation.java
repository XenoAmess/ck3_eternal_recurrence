package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Independent mapping result capture. Native acknowledgement does not settle the canonical action. */
public sealed interface PresentationObservation permits PresentationObservation.Pending,PresentationObservation.Acknowledged,PresentationObservation.Unavailable {
    String SCHEMA="xar.java-presentation-observation/v1";
    PresentationRequest request();
    enum Status {
        IDLE(0),SUBMITTED(1),SETTLED(2),CANCELLED(3),STALE_ACTOR(4),PREEMPTED(5),UNAVAILABLE(6),TARGET_CHANGED(7),BOUNDS_AVAILABLE(8),
        WINDOW_UNAVAILABLE(16),CAMERA_RESOLVE_UNAVAILABLE(17),TARGET_WRITE_BLOCKED(18),TRANSIENT_X_UNAVAILABLE(19),TRANSIENT_Z_UNAVAILABLE(20),
        VIEWPORT_UNAVAILABLE(21),BUCKET_TABLE_UNAVAILABLE(22),BUCKET_MATCH_UNAVAILABLE(23),ZOOM_INDEX_UNAVAILABLE(24),ZOOM_STATE_UNAVAILABLE(25),
        ANGLE_STATE_UNAVAILABLE(26),CANONICAL_TARGET_UNAVAILABLE(27),TARGET_READBACK_UNAVAILABLE(28);
        private final int code;Status(int code){this.code=code;}public int wireCode(){return code;}
        public static Status fromWire(long code){for(Status value:values())if(value.code==code)return value;throw new IllegalArgumentException("unknown presentation native status");}
    }
    record Capture(PresentationRequest.Owner owner,Instant observedAt,long observedRequestSequence,long resultSequence,long trailingResultSequence,
            ExactRef originalHeader,ExactRef originalResult,ExactRef originalDiagnostics){
        public Capture {Objects.requireNonNull(owner);Objects.requireNonNull(observedAt);PresentationJson.u32(observedRequestSequence);PresentationJson.u32(resultSequence);PresentationJson.u32(trailingResultSequence);
            PresentationJson.sized(originalHeader,24);PresentationJson.sized(originalResult,65640);PresentationJson.sized(originalDiagnostics,168);}
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.set("owner",owner.toJson());n.put("observed_at",observedAt.toString());
            n.put("observed_request_sequence",observedRequestSequence);n.put("result_sequence",resultSequence);n.put("trailing_result_sequence",trailingResultSequence);
            n.set("original_header",originalHeader.toJson());n.set("original_result",originalResult.toJson());n.set("original_diagnostics",originalDiagnostics.toJson());return n;}
        public static Capture fromJson(JsonNode raw){ObjectNode n=StrictJson.object(raw,Set.of("owner","observed_at","observed_request_sequence","result_sequence","trailing_result_sequence","original_header","original_result","original_diagnostics"));
            return new Capture(PresentationRequest.Owner.fromJson(n.get("owner")),PresentationJson.time(n.get("observed_at")),PresentationJson.u32(n.get("observed_request_sequence")),
                    PresentationJson.u32(n.get("result_sequence")),PresentationJson.u32(n.get("trailing_result_sequence")),PresentationJson.ref(n.get("original_header"),24),PresentationJson.ref(n.get("original_result"),65640),PresentationJson.ref(n.get("original_diagnostics"),168));}
        /** Byte integrity plus wire identity only. Producer separately proves before/after seqlock and native owner custody. */
        public void verifyOriginal(byte[] header,byte[] result,byte[] diagnostics){
            PresentationJson.original(originalHeader,header);PresentationJson.original(originalResult,result);PresentationJson.original(originalDiagnostics,diagnostics);
            ByteBuffer b=ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);
            StrictJson.require(b.getInt()==PresentationRequest.MAGIC&&b.getInt()==1&&Integer.toUnsignedLong(b.getInt())==owner.processId()&&b.getInt()==0
                    &&Integer.toUnsignedLong(b.getInt())==observedRequestSequence&&Integer.toUnsignedLong(b.getInt())==resultSequence,"actual presentation header differs");
        }
    }
    record Pending(PresentationRequest request,Capture capture,String reason) implements PresentationObservation {
        public Pending {matching(request,capture);StrictJson.text(reason);}
    }
    record Acknowledged(PresentationRequest request,Capture capture,long acknowledgedRequestSequence,Status status) implements PresentationObservation {
        public Acknowledged {matching(request,capture);Objects.requireNonNull(status);PresentationJson.u32(acknowledgedRequestSequence);
            StrictJson.require(acknowledgedRequestSequence==request.requestSequence()&&capture.resultSequence()==capture.trailingResultSequence()&&(capture.resultSequence()&1)==0
                    &&capture.resultSequence()!=request.baselineResultSequence(),"fresh even result must acknowledge this original request");
            StrictJson.require(!capture.observedAt().isBefore(request.preparedAt()),"ack cannot precede actual preparation");}
        public void verifyOriginal(byte[] header,byte[] result,byte[] diagnostics){
            capture.verifyOriginal(header,result,diagnostics);ByteBuffer b=ByteBuffer.wrap(result).order(ByteOrder.LITTLE_ENDIAN);
            StrictJson.require(Integer.toUnsignedLong(b.getInt())==acknowledgedRequestSequence&&Integer.toUnsignedLong(b.getInt())==status.wireCode(),"native ACK request/status differs from raw result");
            long countyCount=Integer.toUnsignedLong(b.getInt(16));StrictJson.require(countyCount<=16384,"native county capacity exceeded");
            int coverage=b.getInt(100);StrictJson.require(coverage==0||coverage==1,"native coverage flag is malformed");
            for(int offset=48;offset<96;offset+=4)StrictJson.require(Float.isFinite(b.getFloat(offset)),"nonfinite original camera state");
        }
    }
    record Unavailable(PresentationRequest request,Instant observedAt,String reason,List<ExactRef> originals) implements PresentationObservation {
        public Unavailable {Objects.requireNonNull(request);Objects.requireNonNull(observedAt);StrictJson.text(reason);originals=PresentationJson.refs(originals);}
    }
    private static void matching(PresentationRequest request,Capture capture){Objects.requireNonNull(request);Objects.requireNonNull(capture);
        StrictJson.require(request.owner().equals(capture.owner()),"original observation owner differs");}
    /** Requires actual original bytes; caller still must establish coherent native seqlock/native process custody. */
    static PresentationObservation fromOriginal(PresentationRequest request,Capture capture,byte[] header,byte[] result,byte[] diagnostics){
        matching(request,capture);capture.verifyOriginal(header,result,diagnostics);
        if(capture.resultSequence()!=capture.trailingResultSequence()||(capture.resultSequence()&1)!=0||capture.resultSequence()==request.baselineResultSequence())return new Pending(request,capture,"no_fresh_even_result");
        ByteBuffer b=ByteBuffer.wrap(result).order(ByteOrder.LITTLE_ENDIAN);long ack=Integer.toUnsignedLong(b.getInt());
        if(ack!=request.requestSequence())return new Pending(request,capture,"different_original_request");
        Status status=Status.fromWire(Integer.toUnsignedLong(b.getInt()));
        Acknowledged actual=new Acknowledged(request,capture,ack,status);actual.verifyOriginal(header,result,diagnostics);return actual;
    }
    default ObjectNode toJson(){
        ObjectNode n=PresentationJson.envelope(SCHEMA);n.set("request",request().toJson());
        if(this instanceof Pending v){n.put("kind","PENDING");n.set("capture",v.capture().toJson());n.put("reason",v.reason());}
        else if(this instanceof Acknowledged v){n.put("kind","ACKNOWLEDGED");n.set("capture",v.capture().toJson());n.put("acknowledged_request_sequence",v.acknowledgedRequestSequence());n.put("status",v.status().name());}
        else if(this instanceof Unavailable v){n.put("kind","UNAVAILABLE");n.put("observed_at",v.observedAt().toString());n.put("reason",v.reason());PresentationJson.refs(n,"originals",v.originals());}return n;
    }
    default byte[] encode(){return StrictJson.canonical(toJson());}
    static PresentationObservation decode(byte[] raw){
        JsonNode r=StrictJson.parse(raw);StrictJson.require(r.isObject(),"observation object required");String kind=StrictJson.text(r.get("kind"));
        Set<String> fields=switch(kind){case "PENDING"->Set.of("schema","transport","request","kind","capture","reason");
            case "ACKNOWLEDGED"->Set.of("schema","transport","request","kind","capture","acknowledged_request_sequence","status");
            case "UNAVAILABLE"->Set.of("schema","transport","request","kind","observed_at","reason","originals");default->throw new IllegalArgumentException("unknown presentation observation branch");};
        ObjectNode n=PresentationJson.envelope(r,fields,SCHEMA);PresentationRequest request=PresentationRequest.fromJson(n.get("request"));
        return switch(kind){case "PENDING"->new Pending(request,Capture.fromJson(n.get("capture")),StrictJson.text(n.get("reason")));
            case "ACKNOWLEDGED"->new Acknowledged(request,Capture.fromJson(n.get("capture")),PresentationJson.u32(n.get("acknowledged_request_sequence")),Status.valueOf(StrictJson.text(n.get("status"))));
            case "UNAVAILABLE"->new Unavailable(request,PresentationJson.time(n.get("observed_at")),StrictJson.text(n.get("reason")),PresentationJson.refs(n.get("originals")));default->throw new IllegalStateException();};
    }
}
