package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.UUID;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsDriverResult.NumericResult;

/**
 * Complete numeric Driver-result sidecars and finite transcript summaries.
 * No Native query, action, canonical writer, public-number reverse conversion or retry authority.
 * Caller installs the actual state-directory/settings, original lock and finite storage guard.
 */
public final class ArmyQueryHistoryStore {
    public static final String SUMMARY_SCHEMA="xar.ck3.army-query-history-summary.v1";
    public static final String REFERENCE_KIND="complete-driver-army-query-result-json-v1";
    private static final int CHUNK=1024*1024;
    private static final List<String> RESULT_FIELDS=List.of("step","accepted","status","backend_id","query_sequence",
            "queried_snapshot_id","queried_revision","queried_native_revision","army_strengths_profile","army_observed_phase_coverage");
    private static final List<String> ARMY_FIELDS=List.of("army_id","status","scope_role","native_carmy_id","owner_character_id",
            "war_ids","current_soldiers","maximum_soldiers","ai_base_power_raw","ai_base_power_scale","unavailable_reason");

    public record Settings(Path evidenceDirectory,long limitBytes) {
        public Settings {absolute(evidenceDirectory);if(limitBytes<0)throw new IllegalArgumentException("Army sidecar limit must be explicitly nonnegative");}
    }
    @FunctionalInterface public interface AdmissionGuard {void requireCurrent()throws IOException;}
    @FunctionalInterface public interface Output {int write(byte[] bytes,int offset,int length)throws IOException;}
    @FunctionalInterface public interface WriteBody {Written write(Output output)throws IOException;}
    public record Written(long bytes,String sha256) {
        public Written {if(bytes<0||sha256==null||!sha256.matches("[0-9a-f]{64}"))throw new IllegalArgumentException("actual written byte count and digest required");}
    }
    public record StoredFile(Path path,long bytes,String sha256) {
        public StoredFile {absolute(path);new Written(bytes,sha256);}
    }
    /** Real I/O boundary. Implementations must retain failed/partial creates, never overwrite or clean them up. */
    public interface ArtifactIO {
        long existingFlatBytes(Path folder)throws IOException;
        StoredFile writeExclusive(Path target,long maximumLogicalBytes,WriteBody body)throws IOException;
    }
    public static final class SidecarIOException extends IOException {
        private static final long serialVersionUID=1L;
        private final boolean errnoPresent;
        private final int errnoValue;
        public SidecarIOException(String message,OptionalInt errno,IOException cause){super(message,cause);Objects.requireNonNull(errno);this.errnoPresent=errno.isPresent();this.errnoValue=errno.orElse(0);}
        public OptionalInt errno(){return errnoPresent?OptionalInt.of(errnoValue):OptionalInt.empty();}
    }
    private static final class Exhausted extends IOException {
        private static final long serialVersionUID=1L;
        Exhausted(String message){super(message);}
    }

    /** Only this installed store issues a result; DATA does not grant Root or Game qualification. */
    public sealed abstract static class Result permits Disabled,FullStored,AdmissionRejected,BudgetExhausted,IoError,AlreadyCompact {
        private final ArmyQueryHistoryStore owner;
        private final NumericResult input;
        private final RawJson summary;
        private Result(ArmyQueryHistoryStore owner,NumericResult input,RawJson summary){this.owner=owner;this.input=input;this.summary=summary;}
        public final RawJson summary(){return summary;}
        public final RawJson publicSummary(){return ArmyQueryHistoryStore.publicSummary(summary);}
        public final Settings settings(){return owner.settings;}
        public final boolean issuedBy(ArmyQueryHistoryStore actual){return owner==actual;}
        public final Optional<NumericResult> input(){return Optional.ofNullable(input);}
        public final void requireInput(NumericResult actual){if(input==null||input!=actual)throw new IllegalArgumentException("sidecar result belongs to a different actual numeric Driver result");}
    }
    public static final class Disabled extends Result {private Disabled(ArmyQueryHistoryStore s,NumericResult i,RawJson r){super(s,i,r);}}
    public static final class FullStored extends Result {
        private final StoredFile reference;
        private FullStored(ArmyQueryHistoryStore s,NumericResult i,RawJson r,StoredFile f){super(s,i,r);reference=f;}
        public StoredFile reference(){return reference;}
    }
    public static final class AdmissionRejected extends Result {private AdmissionRejected(ArmyQueryHistoryStore s,NumericResult i,RawJson r){super(s,i,r);}}
    public static final class BudgetExhausted extends Result {private BudgetExhausted(ArmyQueryHistoryStore s,NumericResult i,RawJson r){super(s,i,r);}}
    public static final class IoError extends Result {private IoError(ArmyQueryHistoryStore s,NumericResult i,RawJson r){super(s,i,r);}}
    public static final class AlreadyCompact extends Result {private AlreadyCompact(ArmyQueryHistoryStore s,RawJson r){super(s,null,r);}}
    public record CompactInput(RawJson original) {
        public CompactInput {Objects.requireNonNull(original);if(!isCompact(original))throw new IllegalArgumentException("original compact Army summary required");}
    }

    private final Settings settings;
    private final Optional<AdmissionGuard> admission;
    private final ArtifactIO io;
    private boolean initialized;
    private long used;
    public ArmyQueryHistoryStore(Settings settings,AdmissionGuard admission,ArtifactIO io) {
        this(settings,Optional.of(Objects.requireNonNull(admission)),io);
    }
    public ArmyQueryHistoryStore(Settings settings,Optional<AdmissionGuard> admission,ArtifactIO io) {
        this.settings=Objects.requireNonNull(settings);this.admission=Objects.requireNonNull(admission);this.io=Objects.requireNonNull(io);
    }
    public Settings settings(){return settings;}
    /** Revalidate the same installed live admission before publishing captured DATA. No I/O or new authority.
     * Optional.empty preserves the original unguarded DATA case; Root installers supply their actual guard.
     * Read-only cold replay must not call this live check or record a new sidecar.
     */
    public void requireCurrentAdmission()throws IOException {
        if(admission.isPresent())admission.orElseThrow().requireCurrent();
    }
    /** Admission precedes both compact pass-through and limit-zero handling, as in the original producer. */
    public synchronized Result record(CompactInput compact) {
        Objects.requireNonNull(compact);
        try {requireCurrentAdmission();}
        catch(IllegalArgumentException|IOException error){return new AdmissionRejected(this,null,summary(ArmyJson.parse(compact.original().bytes()),null,"sidecar_admission_rejected",admissionDiagnostic(error)));}
        return new AlreadyCompact(this,new RawJson(compact.original().bytes()));
    }
    public synchronized Result record(NumericResult input) {
        Objects.requireNonNull(input);
        try {requireCurrentAdmission();}
        catch(IllegalArgumentException|IOException error){return new AdmissionRejected(this,input,summary(finite(input),null,"sidecar_admission_rejected",admissionDiagnostic(error)));}
        ObjectNode finite=finite(input);
        if(settings.limitBytes()==0)return new Disabled(this,input,summary(finite,null,"sidecar_disabled_by_session_budget",
                ArmyJson.empty().put("limit_bytes",0).put("charged_bytes",0)));
        try {
            if(!initialized){
                long existing=io.existingFlatBytes(settings.evidenceDirectory());
                if(existing<0)throw new IOException("existing Army sidecar bytes are negative");
                used=existing;initialized=true;
            }
            if(used>=settings.limitBytes())throw new Exhausted("Army sidecar quota exhausted");
            Path target=settings.evidenceDirectory().resolve("army-query-"+UUID.randomUUID().toString().replace("-","")+".json");
            long quote=Math.min(settings.limitBytes()-used,WriterContracts.MAX_PIN_BYTES);
            // The only full serialization is lazy and belongs to the actual numeric producer.
            byte[] original=input.original().bytes();
            Written[] actualWrite={null};
            boolean[] entered={false};
            StoredFile reference=io.writeExclusive(target,quote,out->{
                if(entered[0])throw new IOException("sidecar write body invoked more than once");
                entered[0]=true;
                actualWrite[0]=write(out,original);return actualWrite[0];
            });
            if(actualWrite[0]==null||!reference.path().equals(target)||reference.bytes()!=actualWrite[0].bytes()
                    ||!reference.sha256().equals(actualWrite[0].sha256()))throw new IOException("sidecar port lost its actual complete write or physical target");
            return new FullStored(this,input,summary(finite,reference,null,null),reference);
        }catch(Exhausted error){
            return new BudgetExhausted(this,input,summary(finite,null,"sidecar_budget_exhausted",budgetDiagnostic()));
        }catch(IOException error){
            ObjectNode diagnostic=budgetDiagnostic().put("error_type",error.getClass().getSimpleName()).put("message",truncate(message(error),2048));
            if(error instanceof SidecarIOException actual&&actual.errno().isPresent())diagnostic.put("errno",actual.errno().getAsInt());else diagnostic.putNull("errno");
            return new IoError(this,input,summary(finite,null,"sidecar_io_error",diagnostic));
        }
    }
    private Written write(Output out,byte[] original)throws IOException {
        MessageDigest digest=digest();long written=0;int offset=0;
        while(offset<original.length){
            int take=Math.min(CHUNK,original.length-offset);
            // Newline participates in the final original 1MiB buffered flush.
            if(take<CHUNK){byte[] finalChunk=new byte[take+1];System.arraycopy(original,offset,finalChunk,0,take);finalChunk[take]=10;
                charge(finalChunk.length);int n=out.write(finalChunk,0,finalChunk.length);if(n!=finalChunk.length)throw new IOException("short JSON sidecar write");
                digest.update(finalChunk);written+=n;offset=original.length;return new Written(written,HexFormat.of().formatHex(digest.digest()));}
            charge(take);int n=out.write(original,offset,take);if(n!=take)throw new IOException("short JSON sidecar write");
            digest.update(original,offset,take);written+=n;offset+=take;
        }
        byte[] newline={10};charge(1);if(out.write(newline,0,1)!=1)throw new IOException("short JSON sidecar write");digest.update(newline);written++;
        return new Written(written,HexFormat.of().formatHex(digest.digest()));
    }
    private void charge(int bytes)throws Exhausted {
        if(bytes>settings.limitBytes()-used)throw new Exhausted("admitted output byte budget exhausted");
        used+=bytes;
    }
    private ObjectNode budgetDiagnostic(){ObjectNode d=ArmyJson.empty().put("limit_bytes",settings.limitBytes());if(initialized)d.put("charged_bytes",used);else d.putNull("charged_bytes");return d;}
    private ObjectNode admissionDiagnostic(Exception error){return ArmyJson.empty().put("limit_bytes",settings.limitBytes()).put("reason",truncate(message(error),1000));}

    /** Finite Core/header projection. It does not encode/copy any regiments, phase stages or complete result. */
    static ObjectNode finite(NumericResult input) {
        var actual=input.source();var original=actual.original();var frame=actual.selection().snapshot().binding();
        ObjectNode result=ArmyJson.empty().put("step",ArmyStrengths.STEP).put("accepted",true)
                .put("status",ArmyStrengthsCodec.wire(actual.status())).put("backend_id",original.backendId())
                .put("query_sequence",original.sequence()).put("queried_snapshot_id",frame.snapshotId())
                .put("queried_revision",frame.publicRevision()).put("queried_native_revision",frame.nativeRevision())
                .put("army_strengths_profile",original.profile().wire()).put("army_observed_phase_coverage",original.profile().coverage());
        ArrayNode rows=result.putArray("army_strengths");
        actual.selected().forEach(row->rows.add(select(ArmyStrengthsCodec.coreJson(row.core()),ARMY_FIELDS)));
        return result;
    }
    /** Original summary field contract; missing, explicit null and malformed/non-array rows stay distinct. */
    public static RawJson buildSummary(RawJson numeric,Optional<StoredFile> reference,Optional<String> reason,Optional<ObjectNode> diagnostic) {
        ObjectNode source=ArmyJson.parse(Objects.requireNonNull(numeric).bytes());
        for(String key:List.of("query_sequence","queried_revision","queried_native_revision"))if(source.hasNonNull(key)&&!source.get(key).isIntegralNumber())throw new IllegalArgumentException("numeric original Driver counter required");
        JsonNode rows=source.get("army_strengths");
        if(rows!=null&&rows.isArray())for(JsonNode row:rows)if(row.isObject()&&row.hasNonNull("ai_base_power_raw")&&!row.get("ai_base_power_raw").isIntegralNumber())throw new IllegalArgumentException("numeric original Army power required");
        return summary(source,reference.orElse(null),reason.orElse(null),diagnostic.orElse(null));
    }
    private static RawJson summary(ObjectNode source,StoredFile reference,String reason,ObjectNode diagnostic) {
        ObjectNode out=select(source,RESULT_FIELDS);out.put("history_summary_schema",SUMMARY_SCHEMA);
        JsonNode rows=source.get("army_strengths");
        if(rows!=null&&rows.isArray()){out.put("army_count",rows.size());ArrayNode armies=out.putArray("armies");
            for(JsonNode row:rows)armies.add(row.isObject()?select((ObjectNode)row,ARMY_FIELDS):ArmyJson.empty().put("malformed_row",true));
        }else{out.putNull("army_count");out.putNull("armies");}
        out.put("full_result_preserved",reference!=null);
        if(reference!=null)out.putObject("raw_result_reference").put("path",reference.path().toString()).put("bytes",reference.bytes())
                .put("sha256",reference.sha256()).put("kind",REFERENCE_KIND).put("wire_bytes_preserved",false);
        else{if(reason==null)out.putNull("unavailable_reason");else out.put("unavailable_reason",reason);if(diagnostic!=null)out.set("history_storage_diagnostic",diagnostic.deepCopy());}
        return new RawJson(ArmyJson.bytes(out));
    }
    public static boolean isCompact(RawJson value){return SUMMARY_SCHEMA.equals(ArmyJson.parse(value.bytes()).path("history_summary_schema").asText());}
    /** Sole declared public roles for this finite summary; it never reconstructs an internal numeric result. */
    public static RawJson publicSummary(RawJson original) {
        ObjectNode out=ArmyJson.parse(original.bytes());if(!SUMMARY_SCHEMA.equals(out.path("history_summary_schema").asText()))throw new IllegalArgumentException("Army history summary schema differs");
        for(String key:List.of("query_sequence","queried_revision","queried_native_revision"))decimal(out,key,false);
        if(out.get("armies") instanceof ArrayNode rows)for(JsonNode row:rows)if(row instanceof ObjectNode object)decimal(object,"ai_base_power_raw",true);
        if(out.get("raw_result_reference") instanceof ObjectNode reference)decimal(reference,"bytes",false);
        if(out.get("history_storage_diagnostic") instanceof ObjectNode diagnostic)for(String key:List.of("limit_bytes","charged_bytes"))decimal(diagnostic,key,false);
        return new RawJson(ArmyJson.bytes(out));
    }
    private static void decimal(ObjectNode row,String key,boolean signed){
        if(!row.hasNonNull(key))return;JsonNode value=row.get(key);
        if(!value.isIntegralNumber()||value.bigIntegerValue().bitLength()>(signed?63:64)||(!signed&&value.bigIntegerValue().signum()<0))
            throw new IllegalArgumentException("exact declared Army summary integer role required: "+key);
        row.put(key,value.bigIntegerValue().toString());
    }
    private static ObjectNode select(ObjectNode row,List<String> fields){ObjectNode out=ArmyJson.empty();for(String key:fields)if(row.has(key))out.set(key,row.get(key).deepCopy());return out;}
    private static Path absolute(Path path){Objects.requireNonNull(path);if(!path.isAbsolute()||!path.equals(path.normalize())||path.getParent()==null)throw new IllegalArgumentException("actual absolute normalized evidence path required");return path;}
    private static String message(Exception error){return error.getMessage()==null?error.toString():error.getMessage();}
    private static String truncate(String value,int length){return value.codePointCount(0,value.length())<=length?value:value.substring(0,value.offsetByCodePoints(0,length));}
    private static MessageDigest digest(){try{return MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}

    /** Actual create-only filesystem implementation under the original finite allocation authority. */
    public static final class GuardedFileIO implements ArtifactIO {
        private final StorageWriteGuard storage;
        private final Path originalLock;
        public GuardedFileIO(StorageWriteGuard storage,Path originalLock){this.storage=Objects.requireNonNull(storage);this.originalLock=absolute(originalLock);}
        public StorageWriteGuard storageGuard(){return storage;}
        public Path originalLock(){return originalLock;}
        @Override public long existingFlatBytes(Path folder)throws IOException {
            absolute(folder);if(!Files.exists(folder,LinkOption.NOFOLLOW_LINKS))return 0;
            requireOrdinaryParents(folder);long total=0;
            try(DirectoryStream<Path> entries=Files.newDirectoryStream(folder)){
                for(Path entry:entries){BasicFileAttributes attrs=Files.readAttributes(entry,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
                    if(attrs.isRegularFile()&&!attrs.isSymbolicLink())try{total=Math.addExact(total,attrs.size());}catch(ArithmeticException overflow){throw new IOException("existing Army sidecar quota sum overflow",overflow);}}
            }
            return total;
        }
        @Override public StoredFile writeExclusive(Path target,long maximum,WriteBody body)throws IOException {
            absolute(target);Objects.requireNonNull(body);if(maximum<0||maximum>WriterContracts.MAX_PIN_BYTES)throw new IllegalArgumentException("finite complete create quote required");
            var missing=new ArrayList<Path>();Path cursor=target.getParent();
            while(!Files.exists(cursor,LinkOption.NOFOLLOW_LINKS)){if(missing.size()>=64)throw new IOException("Army sidecar directory depth exceeds finite plan");missing.add(cursor);cursor=cursor.getParent();if(cursor==null)throw new IOException("ordinary existing evidence ancestor required");}
            requireOrdinaryParents(cursor);var mutations=new ArrayList<StorageWriteGuard.Mutation>();
            for(int i=missing.size()-1;i>=0;i--)mutations.add(new StorageWriteGuard.DirectoryCreate(missing.get(i)));
            mutations.add(new StorageWriteGuard.FileCreate(target,maximum));
            return storage.write(new StorageWriteGuard.WritePlan(originalLock,mutations),()->{
                for(int i=missing.size()-1;i>=0;i--){requireOrdinaryParents(missing.get(i).getParent());Files.createDirectory(missing.get(i));}
                requireOrdinaryParents(target.getParent());Written expected;
                try(FileChannel channel=FileChannel.open(target,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
                    long[] physical={0};
                    expected=body.write((bytes,offset,length)->{
                        if(length<0||length>maximum-physical[0])throw new IOException("sidecar write exceeds its original finite create quote");
                        int count=channel.write(ByteBuffer.wrap(bytes,offset,length));physical[0]+=count;return count;
                    });
                    if(expected.bytes()>maximum)throw new IOException("sidecar exceeded its original finite create quote");channel.force(true);
                }
                Written actual=fileDigest(target);if(!actual.equals(expected))throw new IOException("actual durable Army sidecar bytes or digest changed");
                return new StoredFile(target,actual.bytes(),actual.sha256());
            });
        }
        public static Written fileDigest(Path target)throws IOException {
            MessageDigest digest=digest();long bytes=0;
            try(var stream=Files.newInputStream(target)){byte[] chunk=new byte[CHUNK];for(int n;(n=stream.read(chunk))!=-1;){digest.update(chunk,0,n);bytes=Math.addExact(bytes,n);}}
            return new Written(bytes,HexFormat.of().formatHex(digest.digest()));
        }
        private static void requireOrdinaryParents(Path path)throws IOException {
            for(Path cursor=path;cursor!=null;cursor=cursor.getParent()){var attrs=Files.readAttributes(cursor,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
                if(!attrs.isDirectory()||attrs.isSymbolicLink())throw new IOException("ordinary Army sidecar directory ancestry required");}
        }
    }
}

