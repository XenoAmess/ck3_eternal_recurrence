package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable presentation intent. Its public DATA never authorizes a physical post. */
public record PresentationIntent(String requestId, Instant createdAt, PresentationRequest.Owner owner,
        PresentationRequest.Frame frame, PresentationRequest.Mode mode, String titleKey,
        Optional<Scope> tracking, Instant deadline) {
    public static final String SCHEMA="xar.java-auto-camera-intent/v1";
    public record Scope(String generation,int armyId,int start,int end,List<PresentationRequest.Province> provinces) {
        public Scope {
            PresentationJson.u64(generation,true);provinces=List.copyOf(provinces);
            StrictJson.require(armyId>0&&start>0&&end>start&&(long)end-start<=720&&!provinces.isEmpty()
                    &&provinces.size()<=32&&provinces.stream().map(PresentationRequest.Province::id).distinct().count()==provinces.size(),
                    "finite actual armed camera scope required");
        }
        public ObjectNode toJson(){var n=StrictJson.object().put("generation",generation).put("army_id",armyId).put("start",start).put("end",end);
            var a=n.putArray("provinces");provinces.forEach(p->a.add(p.toJson()));return n;}
        public static Scope fromJson(JsonNode raw){var n=StrictJson.object(raw,Set.of("generation","army_id","start","end","provinces"));
            var a=n.get("provinces");StrictJson.require(a.isArray()&&a.size()<=32,"finite tracking provinces required");
            var p=new java.util.ArrayList<PresentationRequest.Province>();a.forEach(v->p.add(PresentationRequest.Province.fromJson(v)));
            return new Scope(StrictJson.text(n.get("generation")),PresentationJson.i32(n.get("army_id")),PresentationJson.i32(n.get("start")),PresentationJson.i32(n.get("end")),p);}
    }
    public PresentationIntent {
        StrictJson.text(requestId);Objects.requireNonNull(createdAt);Objects.requireNonNull(owner);Objects.requireNonNull(frame);
        Objects.requireNonNull(mode);Objects.requireNonNull(titleKey);Objects.requireNonNull(tracking);Objects.requireNonNull(deadline);
        StrictJson.require(deadline.isAfter(createdAt)&&!deadline.isAfter(createdAt.plusSeconds(120)),"finite original camera deadline required");
        StrictJson.require(mode==PresentationRequest.Mode.HOTSPOT?titleKey.matches("[bcdke]_[A-Za-z0-9_]{1,124}"):titleKey.isEmpty(),"finite camera title selector required");
        StrictJson.require((mode==PresentationRequest.Mode.TRACKED_HOTSPOT)==tracking.isPresent(),"tracking present exactly for mode4");
        tracking.ifPresent(scope->StrictJson.require(scope.start()==frame.dateRaw(),"armed tracking starts on the actual source frame"));
    }
    public ObjectNode toJson(){var n=StrictJson.object().put("schema",SCHEMA).put("request_id",requestId).put("created_at",createdAt.toString());
        n.set("owner",owner.toJson());n.set("frame",frame.toJson());n.put("mode",mode.name()).put("title_key",titleKey).put("deadline",deadline.toString());
        if(tracking.isPresent())n.set("tracking",tracking.orElseThrow().toJson());else n.putNull("tracking");return n;}
    public byte[] encode(){return StrictJson.canonical(toJson());}
    public static PresentationIntent fromJson(JsonNode raw){var n=StrictJson.object(raw,Set.of("schema","request_id","created_at","owner","frame","mode","title_key","deadline","tracking"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(n.get("schema"))),"exact automatic camera intent schema required");var t=n.get("tracking");
        return new PresentationIntent(StrictJson.text(n.get("request_id")),Instant.parse(StrictJson.text(n.get("created_at"))),
                PresentationRequest.Owner.fromJson(n.get("owner")),PresentationRequest.Frame.fromJson(n.get("frame")),
                PresentationRequest.Mode.valueOf(StrictJson.text(n.get("mode"))),n.get("title_key").isTextual()?n.get("title_key").textValue():null,
                t.isNull()?Optional.empty():Optional.of(Scope.fromJson(t)),Instant.parse(StrictJson.text(n.get("deadline"))));}
    /** Actual physical preparation captured on the IO worker; it contains no archive references. */
    public record Prepared(PresentationIntent intent,Instant observedAt,long previous,long sequence,long baseline,
            String expiresUptimeMs,String hwnd,Optional<PresentationRequest.Tracking> tracking,byte[] header) {
        public Prepared {
            Objects.requireNonNull(intent);Objects.requireNonNull(observedAt);Objects.requireNonNull(tracking);header=header.clone();
            StrictJson.require(header.length==24&&sequence==PresentationRequest.nextSequence(previous),"actual even header and next sequence required");
            PresentationJson.u32(previous);PresentationJson.u32(baseline);PresentationJson.u64(expiresUptimeMs,true);PresentationJson.u64(hwnd,true);
            StrictJson.require((previous&1)==0&&(baseline&1)==0&&tracking.isPresent()==intent.tracking().isPresent(),"untorn physical preparation required");
            tracking.ifPresent(t->{var s=intent.tracking().orElseThrow();StrictJson.require(t.scopeGeneration().equals(s.generation())&&t.fullArmyId()==s.armyId()&&t.startDateRaw()==s.start()&&t.maxDateRaw()==s.end()&&t.provinces().equals(s.provinces()),"captured tracking changed original armed scope");});
            StrictJson.require(!observedAt.isBefore(intent.createdAt())&&observedAt.isBefore(intent.deadline()),"physical preparation outside original intent deadline");
            var b=ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);
            StrictJson.require(b.getInt()==PresentationRequest.MAGIC&&b.getInt()==1&&Integer.toUnsignedLong(b.getInt())==intent.owner().processId()&&b.getInt()==0
                    &&Integer.toUnsignedLong(b.getInt())==previous&&Integer.toUnsignedLong(b.getInt())==baseline,"captured native mapping header identity differs");
        }
        @Override public byte[] header(){return header.clone();}
        public int paddingBits(){return Float.floatToRawIntBits(intent.mode()==PresentationRequest.Mode.REALM?.32f:.15f);}
        public byte[] requestBytes(){var b=ByteBuffer.allocate(168).order(ByteOrder.LITTLE_ENDIAN);b.putInt(intent.mode().wireCode()).putInt(intent.frame().actor())
                .putInt(intent.frame().dateRaw()).putInt(0).putLong(new BigInteger(expiresUptimeMs).longValue()).putLong(new BigInteger(hwnd).longValue())
                .putInt(paddingBits()).put(intent.titleKey().getBytes(StandardCharsets.US_ASCII));return b.array();}
        public Optional<byte[]> trackingBytes(){if(tracking.isEmpty())return Optional.empty();var t=tracking.orElseThrow();var b=ByteBuffer.allocate(4264).order(ByteOrder.LITTLE_ENDIAN);
            b.putInt((int)sequence).putInt(t.provinces().size()).putLong(new BigInteger(t.ownerEpoch()).longValue()).putLong(new BigInteger(t.scopeGeneration()).longValue())
                    .putInt(intent.frame().actor()).putInt(t.fullArmyId()).putInt(t.startDateRaw()).putInt(t.maxDateRaw());
            for(int i=0;i<t.provinces().size();i++){var p=t.provinces().get(i);b.position(40+i*132);b.putInt(p.id()).put(p.titleKey().getBytes(StandardCharsets.US_ASCII));}return Optional.of(b.array());}
        public PresentationRequest canonical(List<ExactRef> actualPreparationOriginals){return new PresentationRequest(intent.requestId(),observedAt,intent.owner(),intent.frame(),intent.mode(),
                previous,sequence,baseline,expiresUptimeMs,hwnd,paddingBits(),intent.titleKey(),tracking,actualPreparationOriginals);}
    }
}
