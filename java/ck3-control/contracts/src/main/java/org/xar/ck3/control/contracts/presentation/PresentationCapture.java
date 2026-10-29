package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.Base64;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Bounded raw physical capture. No fabricated ExactRef, writer or completed-camera claim. */
public record PresentationCapture(PresentationIntent intent,Optional<PresentationIntent.Prepared> prepared,
        Kind kind,OriginalOutcome.Phase phase,String reason,Instant observedAt,byte[] afterHeader,
        Optional<NativeSample> sample) {
    public static final String SCHEMA="xar.java-auto-camera-capture/v1";
    public enum Kind { NOT_ATTEMPTED, NOT_POSTED, POSTED, UNKNOWN }
    public record NativeSample(Instant observedAt,byte[] header,byte[] result,byte[] diagnostics,
            long trailingResultSequence,Optional<byte[]> trackingHeader,Optional<byte[]> trackingResult) {
        public NativeSample {
            Objects.requireNonNull(observedAt);header=header.clone();result=result.clone();diagnostics=diagnostics.clone();
            Objects.requireNonNull(trackingHeader);Objects.requireNonNull(trackingResult);
            trackingHeader=trackingHeader.map(value->value.clone());trackingResult=trackingResult.map(value->value.clone());
            StrictJson.require(header.length==24&&result.length==65640&&diagnostics.length==168,"complete original camera sample required");
            PresentationJson.u32(trailingResultSequence);
            StrictJson.require(trackingHeader.isPresent()==trackingResult.isPresent(),"tracking sample preserves both original regions");
            trackingHeader.ifPresent(b->StrictJson.require(b.length==40,"exact original tracking capability header required"));
            trackingResult.ifPresent(b->StrictJson.require(b.length==80,"exact bounded tracking result required"));
        }
        @Override public byte[] header(){return header.clone();}
        @Override public byte[] result(){return result.clone();}
        @Override public byte[] diagnostics(){return diagnostics.clone();}
        @Override public Optional<byte[]> trackingHeader(){return trackingHeader.map(value->value.clone());}
        @Override public Optional<byte[]> trackingResult(){return trackingResult.map(value->value.clone());}
    }
    public PresentationCapture {
        Objects.requireNonNull(intent);Objects.requireNonNull(prepared);Objects.requireNonNull(kind);Objects.requireNonNull(phase);
        StrictJson.text(reason);StrictJson.require(reason.length()<=1000,"bounded actual presentation diagnostic required");
        Objects.requireNonNull(observedAt);afterHeader=afterHeader.clone();Objects.requireNonNull(sample);
        StrictJson.require(afterHeader.length==0||afterHeader.length==24,"complete or unavailable after header required");
        StrictJson.require(kind==Kind.NOT_ATTEMPTED?prepared.isEmpty():prepared.isPresent(),"physical attempt must retain its actual preparation");
        prepared.ifPresent(p->StrictJson.require(java.util.Arrays.equals(p.intent().encode(),intent.encode()),"capture crossed its original intent"));
        StrictJson.require(kind!=Kind.POSTED||afterHeader.length==24,"proved publication requires actual after header");
        StrictJson.require(sample.isEmpty()||prepared.isPresent(),"native sample requires original physical preparation");
    }
    @Override public byte[] afterHeader(){return afterHeader.clone();}
    private static String encode(byte[] b){return Base64.getEncoder().encodeToString(b);}
    private static byte[] bytes(JsonNode n,int max){StrictJson.require(n!=null&&n.isTextual()&&n.textValue().length()<=(max+2)/3*4,"bounded raw camera bytes required");
        byte[] b=Base64.getDecoder().decode(n.textValue());StrictJson.require(b.length<=max,"raw camera byte cap exceeded");return b;}
    public ObjectNode toJson(){
        var n=StrictJson.object().put("schema",SCHEMA);n.set("intent",intent.toJson());n.put("kind",kind.name()).put("phase",phase.name()).put("reason",reason)
                .put("observed_at",observedAt.toString()).put("after_header",encode(afterHeader));
        if(prepared.isEmpty())n.putNull("prepared");else{
            var p=prepared.orElseThrow();var q=StrictJson.object().put("observed_at",p.observedAt().toString()).put("previous",p.previous()).put("sequence",p.sequence()).put("baseline",p.baseline())
                    .put("expires_uptime_ms",p.expiresUptimeMs()).put("hwnd",p.hwnd()).put("header",encode(p.header()));
            if(p.tracking().isPresent())q.set("tracking",p.tracking().orElseThrow().toJson());else q.putNull("tracking");n.set("prepared",q);
        }
        if(sample.isEmpty())n.putNull("sample");else{
            var s=sample.orElseThrow();var q=StrictJson.object().put("observed_at",s.observedAt().toString()).put("header",encode(s.header())).put("result",encode(s.result()))
                    .put("diagnostics",encode(s.diagnostics())).put("trailing_result_sequence",s.trailingResultSequence());
            if(s.trackingHeader().isPresent()){q.put("tracking_header",encode(s.trackingHeader().orElseThrow()));q.put("tracking_result",encode(s.trackingResult().orElseThrow()));}
            else{q.putNull("tracking_header");q.putNull("tracking_result");}n.set("sample",q);
        }return n;
    }
    public byte[] encode(){return org.xar.ck3.control.contracts.FullJsonTree.encode(toJson(),131072);}
    public static PresentationCapture decode(byte[] raw){
        var n=StrictJson.object(StrictJson.parse(raw,131072),Set.of("schema","intent","kind","phase","reason","observed_at","after_header","prepared","sample"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(n.get("schema"))),"exact original camera capture schema required");var intent=PresentationIntent.fromJson(n.get("intent"));
        Optional<PresentationIntent.Prepared> prepared=Optional.empty();var p=n.get("prepared");
        if(!p.isNull()){var q=StrictJson.object(p,Set.of("observed_at","previous","sequence","baseline","expires_uptime_ms","hwnd","header","tracking"));var t=q.get("tracking");
            prepared=Optional.of(new PresentationIntent.Prepared(intent,Instant.parse(StrictJson.text(q.get("observed_at"))),PresentationJson.u32(q.get("previous")),PresentationJson.u32(q.get("sequence")),
                    PresentationJson.u32(q.get("baseline")),StrictJson.text(q.get("expires_uptime_ms")),StrictJson.text(q.get("hwnd")),t.isNull()?Optional.empty():Optional.of(PresentationRequest.Tracking.fromJson(t)),bytes(q.get("header"),24)));}
        Optional<NativeSample> sample=Optional.empty();var s=n.get("sample");
        if(!s.isNull()){var q=StrictJson.object(s,Set.of("observed_at","header","result","diagnostics","trailing_result_sequence","tracking_header","tracking_result"));var h=q.get("tracking_header");var r=q.get("tracking_result");
            sample=Optional.of(new NativeSample(Instant.parse(StrictJson.text(q.get("observed_at"))),bytes(q.get("header"),24),bytes(q.get("result"),65640),bytes(q.get("diagnostics"),168),
                    PresentationJson.u32(q.get("trailing_result_sequence")),h.isNull()?Optional.empty():Optional.of(bytes(h,40)),r.isNull()?Optional.empty():Optional.of(bytes(r,80))));}
        return new PresentationCapture(intent,prepared,Kind.valueOf(StrictJson.text(n.get("kind"))),OriginalOutcome.Phase.valueOf(StrictJson.text(n.get("phase"))),
                StrictJson.text(n.get("reason")),Instant.parse(StrictJson.text(n.get("observed_at"))),bytes(n.get("after_header"),24),sample);
    }
}
