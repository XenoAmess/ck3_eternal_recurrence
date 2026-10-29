package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Prepared DATA only. A public constructor never grants central once/post authority. */
public record PresentationRequest(String requestId,Instant preparedAt,Owner owner,Frame frame,Mode mode,
        long previousRequestSequence,long requestSequence,long baselineResultSequence,
        String expiresUptimeMs,String hwnd,int paddingFloatBits,String titleKey,
        Optional<Tracking> tracking,List<ExactRef> preparationEvidence) {
    public static final String SCHEMA="xar.java-presentation-request/v1";
    public static final int MAGIC=0x43524158,VERSION=1,MAPPING_BYTES=131072,REQUEST_BYTES=168,
            RESULT_BYTES=65640,REQUEST_OFFSET=24,RESULT_OFFSET=192,DIAGNOSTICS_BYTES=168,
            DIAGNOSTICS_OFFSET=0x18000,TRACKING_OFFSET=0x18400,TRACKING_REQUEST_BYTES=4264;
    public static final String EXECUTABLE_SHA256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public enum Mode {
        CANCEL(0),REALM(1),HOTSPOT(2),QUERY(3),TRACKED_HOTSPOT(4);
        private final int code; Mode(int code){this.code=code;} public int wireCode(){return code;}
    }
    public record Owner(String machineId,String sessionId,long processId,String processBirthFiletime,
            String executableSha256,String episodeRunId,String connectionGeneration) {
        public Owner {
            StrictJson.text(machineId);StrictJson.text(sessionId);StrictJson.text(episodeRunId);
            StrictJson.require(processId>0&&processId<=0xffff_ffffL,"actual DWORD process identity required");
            PresentationJson.u64(processBirthFiletime,true);PresentationJson.u64(connectionGeneration,false);
            StrictJson.require(EXECUTABLE_SHA256.equals(executableSha256),"reviewed exact1.20.0.4 executable required");
        }
        public ObjectNode toJson(){
            ObjectNode n=StrictJson.object();n.put("machine_id",machineId);n.put("session_id",sessionId);
            n.put("process_id",processId);n.put("process_birth_filetime",processBirthFiletime);
            n.put("executable_sha256",executableSha256);n.put("episode_run_id",episodeRunId);n.put("connection_generation",connectionGeneration);return n;
        }
        public static Owner fromJson(JsonNode raw){
            ObjectNode n=StrictJson.object(raw,Set.of("machine_id","session_id","process_id","process_birth_filetime","executable_sha256","episode_run_id","connection_generation"));
            return new Owner(StrictJson.text(n.get("machine_id")),StrictJson.text(n.get("session_id")),PresentationJson.u32(n.get("process_id")),
                    StrictJson.text(n.get("process_birth_filetime")),StrictJson.text(n.get("executable_sha256")),StrictJson.text(n.get("episode_run_id")),StrictJson.text(n.get("connection_generation")));
        }
    }
    public record Frame(String snapshotId,String revision,String nativeRevision,int actor,int dateRaw){
        public Frame {StrictJson.text(snapshotId);PresentationJson.u64(revision,false);PresentationJson.u64(nativeRevision,false);
            NativeCharacterId.of(actor);StrictJson.require(dateRaw>0,"fresh actual date required");}
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.put("snapshot_id",snapshotId);n.put("revision",revision);
            n.put("native_revision",nativeRevision);n.put("actor",actor);n.put("date_raw",dateRaw);return n;}
        public static Frame fromJson(JsonNode raw){ObjectNode n=StrictJson.object(raw,Set.of("snapshot_id","revision","native_revision","actor","date_raw"));
            return new Frame(StrictJson.text(n.get("snapshot_id")),StrictJson.text(n.get("revision")),StrictJson.text(n.get("native_revision")),PresentationJson.i32(n.get("actor")),PresentationJson.i32(n.get("date_raw")));}
    }
    public record Province(int id,String titleKey){
        public Province {StrictJson.require(id>0&&titleKey!=null&&titleKey.matches("b_[a-zA-Z0-9_]{1,124}"),"original tracking province/barony required");}
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.put("id",id);n.put("title_key",titleKey);return n;}
        public static Province fromJson(JsonNode raw){ObjectNode n=StrictJson.object(raw,Set.of("id","title_key"));return new Province(PresentationJson.i32(n.get("id")),StrictJson.text(n.get("title_key")));}
    }
    public record Tracking(String ownerEpoch,String scopeGeneration,int fullArmyId,int startDateRaw,int maxDateRaw,List<Province> provinces){
        public Tracking {PresentationJson.u64(ownerEpoch,true);PresentationJson.u64(scopeGeneration,true);provinces=List.copyOf(provinces);
            StrictJson.require(fullArmyId>0&&startDateRaw>0&&maxDateRaw>startDateRaw&&(long)maxDateRaw-startDateRaw<=30*24
                    &&!provinces.isEmpty()&&provinces.size()<=32&&provinces.stream().map(Province::id).distinct().count()==provinces.size(),"finite original tracking scope/whitelist required");}
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.put("owner_epoch",ownerEpoch);n.put("scope_generation",scopeGeneration);
            n.put("full_army_id",fullArmyId);n.put("start_date_raw",startDateRaw);n.put("max_date_raw",maxDateRaw);
            var a=n.putArray("provinces");provinces.forEach(p->a.add(p.toJson()));return n;}
        public static Tracking fromJson(JsonNode raw){ObjectNode n=StrictJson.object(raw,Set.of("owner_epoch","scope_generation","full_army_id","start_date_raw","max_date_raw","provinces"));
            JsonNode a=n.get("provinces");StrictJson.require(a.isArray()&&a.size()<=32,"bounded tracking provinces required");var p=new java.util.ArrayList<Province>();a.forEach(item->p.add(Province.fromJson(item)));
            return new Tracking(StrictJson.text(n.get("owner_epoch")),StrictJson.text(n.get("scope_generation")),PresentationJson.i32(n.get("full_army_id")),PresentationJson.i32(n.get("start_date_raw")),PresentationJson.i32(n.get("max_date_raw")),p);}
    }
    public PresentationRequest {
        StrictJson.text(requestId);Objects.requireNonNull(preparedAt);Objects.requireNonNull(owner);Objects.requireNonNull(frame);Objects.requireNonNull(mode);
        PresentationJson.u32(previousRequestSequence);PresentationJson.u32(requestSequence);PresentationJson.u32(baselineResultSequence);
        StrictJson.require((previousRequestSequence&1)==0&&(baselineResultSequence&1)==0
                &&requestSequence==nextSequence(previousRequestSequence),"actual even request/result counters and next original sequence required");
        PresentationJson.u64(expiresUptimeMs,true);PresentationJson.u64(hwnd,true);
        float padding=Float.intBitsToFloat(paddingFloatBits);
        StrictJson.require(Float.isFinite(padding)&&padding>0&&padding<1,"finite native padding required");
        StrictJson.require(titleKey!=null&&titleKey.matches("[a-zA-Z0-9_]{0,127}"),"bounded ASCII title key required");
        if(mode==Mode.HOTSPOT)StrictJson.require(titleKey.matches("[bcdke]_[a-zA-Z0-9_]+"),"canonical hotspot title key required");
        else StrictJson.require(titleKey.isEmpty(),"only native hotspot mode accepts legacy title key");
        tracking=Objects.requireNonNull(tracking);preparationEvidence=PresentationJson.refs(preparationEvidence);
        StrictJson.require(!preparationEvidence.isEmpty(),"actual source-qualified preparation originals required");
        StrictJson.require((mode==Mode.TRACKED_HOTSPOT)==tracking.isPresent(),"tracking extension present exactly for mode4");
        if(tracking.isPresent())StrictJson.require(requestSequence!=0&&tracking.orElseThrow().startDateRaw()==frame.dateRaw(),"tracking original scope must start on this request frame");
    }
    public TransportKind transportKind(){return TransportKind.PRESENTATION_MMAP;}
    public String mappingName(){return "Local\\XarCK3CameraPresentationV1-"+owner.processId();}
    public float padding(){return Float.intBitsToFloat(paddingFloatBits);}
    /** Exactly one original physical request; it consumes zero native gameplay pipe requests. */
    public int physicalRequestCount(){return 1;}
    public int nativePipeRequestCount(){return 0;}
    public int requestPayloadBytes(){return REQUEST_BYTES+(tracking.isPresent()?TRACKING_REQUEST_BYTES:0);}
    public static long nextSequence(long previous){PresentationJson.u32(previous);return (previous+2)&0xffff_fffeL;}
    public byte[] nativeBytes(){
        ByteBuffer b=ByteBuffer.allocate(REQUEST_BYTES).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(mode.wireCode()).putInt(frame.actor()).putInt(frame.dateRaw()).putInt(0)
                .putLong(new java.math.BigInteger(expiresUptimeMs).longValue()).putLong(new java.math.BigInteger(hwnd).longValue()).putInt(paddingFloatBits);
        b.put(titleKey.getBytes(StandardCharsets.US_ASCII));return b.array();
    }
    public Optional<byte[]> trackingBytes(){
        if(tracking.isEmpty())return Optional.empty();Tracking t=tracking.orElseThrow();
        ByteBuffer b=ByteBuffer.allocate(TRACKING_REQUEST_BYTES).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt((int)requestSequence).putInt(t.provinces().size()).putLong(new java.math.BigInteger(t.ownerEpoch()).longValue())
                .putLong(new java.math.BigInteger(t.scopeGeneration()).longValue()).putInt(frame.actor()).putInt(t.fullArmyId()).putInt(t.startDateRaw()).putInt(t.maxDateRaw());
        for(int i=0;i<t.provinces().size();i++){Province p=t.provinces().get(i);b.position(40+i*132);b.putInt(p.id()).put(p.titleKey().getBytes(StandardCharsets.US_ASCII));}
        return Optional.of(b.array());
    }
    public ObjectNode toJson(){
        ObjectNode n=PresentationJson.envelope(SCHEMA);n.put("request_id",requestId);n.put("prepared_at",preparedAt.toString());
        n.set("owner",owner.toJson());n.set("frame",frame.toJson());n.put("mode",mode.name());n.put("previous_request_sequence",previousRequestSequence);
        n.put("request_sequence",requestSequence);n.put("baseline_result_sequence",baselineResultSequence);n.put("expires_uptime_ms",expiresUptimeMs);
        n.put("hwnd",hwnd);n.put("padding_float_bits",Integer.toUnsignedLong(paddingFloatBits));n.put("title_key",titleKey);
        if(tracking.isPresent())n.set("tracking",tracking.orElseThrow().toJson());else n.putNull("tracking");
        PresentationJson.refs(n,"preparation_evidence",preparationEvidence);return n;
    }
    public byte[] encode(){return StrictJson.canonical(toJson());}
    public static PresentationRequest decode(byte[] raw){return fromJson(StrictJson.parse(raw));}
    public static PresentationRequest fromJson(JsonNode raw){
        ObjectNode n=PresentationJson.envelope(raw,Set.of("schema","transport","request_id","prepared_at","owner","frame","mode","previous_request_sequence","request_sequence","baseline_result_sequence","expires_uptime_ms","hwnd","padding_float_bits","title_key","tracking","preparation_evidence"),SCHEMA);
        JsonNode t=n.get("tracking");
        return new PresentationRequest(StrictJson.text(n.get("request_id")),PresentationJson.time(n.get("prepared_at")),Owner.fromJson(n.get("owner")),Frame.fromJson(n.get("frame")),
                Mode.valueOf(StrictJson.text(n.get("mode"))),PresentationJson.u32(n.get("previous_request_sequence")),PresentationJson.u32(n.get("request_sequence")),
                PresentationJson.u32(n.get("baseline_result_sequence")),StrictJson.text(n.get("expires_uptime_ms")),StrictJson.text(n.get("hwnd")),(int)PresentationJson.u32(n.get("padding_float_bits")),
                n.get("title_key").isTextual()?n.get("title_key").textValue():null,t.isNull()?Optional.empty():Optional.of(Tracking.fromJson(t)),PresentationJson.refs(n.get("preparation_evidence")));
    }
}
