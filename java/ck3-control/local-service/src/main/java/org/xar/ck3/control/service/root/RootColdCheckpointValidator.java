package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Canonical physical counterpart of cold_checkpoint_validator.py. Reads and validates; never publishes or writes. */
public final class RootColdCheckpointValidator {
    public static final String CHECKPOINT_FILENAME="xar_checkpoint.ck3";
    public static final String LOAD_SAVE_NAME="xar_checkpoint";
    public static final int MAXIMUM_DRIVER_BYTES=DriverCheckpointStore.MAX_DRIVER_BYTES;
    private final ContinuityWriter writer;
    private final WindowsSavedProofIdentityReader identities;
    private final java.util.IdentityHashMap<Expected,LegacyResumeNormalizer.LifecycleProjection> originalLegacyProjections=new java.util.IdentityHashMap<>();

    /** No configured callback or caller-supplied verifier can mint a Verified ticket. */
    public RootColdCheckpointValidator(ContinuityWriter actualWriter) {
        writer=Objects.requireNonNull(actualWriter);identities=new WindowsSavedProofIdentityReader();
    }
    public record Expected(ExactRef driverRef,FileStatIdentity driverIdentity,ExactRef saveRef,FileStatIdentity saveIdentity,
            String pipeName,Path profileDir,Obj expectedRawCheckpoint,Obj expectedNormalizedAnchor,long expectedHistoryRows) {
        public Expected {
            Objects.requireNonNull(driverRef);Objects.requireNonNull(driverIdentity);Objects.requireNonNull(saveRef);Objects.requireNonNull(saveIdentity);
            Objects.requireNonNull(profileDir);Objects.requireNonNull(expectedRawCheckpoint);Objects.requireNonNull(expectedNormalizedAnchor);
            nonempty(pipeName,"cold checkpoint pipe name must be nonempty");absolute(profileDir);absolute(Path.of(driverRef.path()));absolute(Path.of(saveRef.path()));
            StrictJson.require(driverRef.bytes()>0&&driverRef.bytes()<=MAXIMUM_DRIVER_BYTES&&saveRef.bytes()>0&&expectedHistoryRows>=1,
                    "complete bounded original Driver and nonempty actual SAVE/history required");
            StrictJson.require(driverIdentity.bytes().equals(BigInteger.valueOf(driverRef.bytes()))&&saveIdentity.bytes().equals(BigInteger.valueOf(saveRef.bytes())),
                    "original OS stat identities and exact content sizes differ");
            StrictJson.require(!Path.of(driverRef.path()).equals(Path.of(saveRef.path())),"independent original Driver and SAVE files required");
        }
    }
    /** Private minting binds full immutable data to this concrete owner, exact borrowed scope and original head. */
    public static final class Verified {
        private final RootColdCheckpointValidator issuer;
        private final Session scope;
        private final String headDigest;
        private final Expected expected;
        private final FileWitness driverWitness,saveWitness;
        private final byte[] driverBytes;
        private final Obj driverPayload,normalizedAnchor;
        private LegacyResumeNormalizer.LifecycleProjection legacyProjection=LegacyResumeNormalizer.LifecycleProjection.BOUND_OR_LEGACY;
        private Verified(RootColdCheckpointValidator issuer,Session scope,String headDigest,Expected expected,
                FileWitness driverWitness,FileWitness saveWitness,byte[] driverBytes,Obj driverPayload,Obj normalizedAnchor) {
            this.issuer=issuer;this.scope=scope;this.headDigest=headDigest;this.expected=expected;this.driverWitness=driverWitness;
            this.saveWitness=saveWitness;this.driverBytes=driverBytes;this.driverPayload=driverPayload;this.normalizedAnchor=normalizedAnchor;
        }
        public Obj normalizedAnchor(){return normalizedAnchor;}
        public Obj driverPayload(){return driverPayload;}
        public byte[] driverBytes(){return driverBytes.clone();}
        public FileWitness driverWitness(){return driverWitness;}
        public FileWitness saveWitness(){return saveWitness;}
        public Expected expected(){return expected;}
    }
    private record Loaded(FileWitness witness,byte[] retainedBytes) { }
    /** Builds review DATA from the actual private original and complete physical witnesses.
     * JSON type-domain equivalence permits original whitespace/key order; physical bytes keep their own exact SHA/Win32 identity.
     * A base file that omits replayed WAL facts is rejected. This method grants no Verified ticket or reducer admission. */
    public Expected expectedLegacy(Session same,RootOriginalDriverJournal.OriginalJournalLoad actualOriginal,
            FileWitness completeDriver,FileWitness actualSave,Path actualProfile)throws IOException {
        Objects.requireNonNull(actualOriginal);Objects.requireNonNull(completeDriver);Objects.requireNonNull(actualSave);
        writer.requireSession(same);String head=same.head().digest();
        actualOriginal.requireRetained(same);actualOriginal.requireActualProfile(same,actualProfile);
        try {
            requireProfileSave(actualProfile,actualSave.reference());
            Loaded physical=readPhysical(completeDriver.reference(),completeDriver.identity(),true);
            readPhysical(actualSave.reference(),actualSave.identity(),false);
            Obj physicalPayload=DriverJson.object(physical.retainedBytes(),MAXIMUM_DRIVER_BYTES);
            Obj originalPayload=DriverJson.object(actualOriginal.fullBytes(),MAXIMUM_DRIVER_BYTES);
            StrictJson.require(DriverJson.toNode(physicalPayload).equals(DriverJson.toNode(originalPayload)),
                    "complete physical Driver differs from the actual replayed original; an unconsolidated base is not a full-state barrier");
            var projection=actualOriginal.frozenLifecycleProjection() instanceof org.xar.ck3.control.application.history.LegacyResumeMigration.ExplicitNativeCampaign
                    ?LegacyResumeNormalizer.LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN:LegacyResumeNormalizer.LifecycleProjection.BOUND_OR_LEGACY;
            Obj anchor=normalizeLegacyPayload(physicalPayload,actualOriginal.pipeName(),actualProfile,actualSave,projection);
            Expected result=new Expected(completeDriver.reference(),completeDriver.identity(),actualSave.reference(),actualSave.identity(),
                    actualOriginal.pipeName(),actualProfile,object(physicalPayload.get("last_checkpoint"),"actual raw checkpoint"),anchor,
                    array(physicalPayload.get("command_history"),"actual complete command history").items().size());
            requireIdentity(completeDriver.reference(),completeDriver.identity());requireIdentity(actualSave.reference(),actualSave.identity());
            actualOriginal.requireActualProfile(same,actualProfile);actualOriginal.requireRetained(same);requireHead(same,head);
            if(originalLegacyProjections.size()>=4096)throw new IOException("Original cold projection retention is full");
            originalLegacyProjections.put(result,projection);
            return result;
        }catch(IllegalArgumentException malformed){throw new IOException("actual legacy cold review input is invalid",malformed);}
    }
    /** Explicit original-Python/P37 branch. Java material issuers use verify(), never a manufactured legacy journal. */
    public Verified verifyLegacy(Session same,Expected expected)throws IOException {
        Verified ticket=verify(same,expected);
        var projection=originalLegacyProjections.getOrDefault(expected,LegacyResumeNormalizer.LifecycleProjection.BOUND_OR_LEGACY);
        normalizeLegacyPayload(ticket.driverPayload,expected.pipeName(),expected.profileDir(),ticket.saveWitness,projection);
        ticket.legacyProjection=projection;
        requireCurrent(same,ticket);return ticket;
    }
    public void requireCurrentLegacy(Session same,Verified ticket)throws IOException {
        requireCurrent(same,ticket);
        normalizeLegacyPayload(ticket.driverPayload,ticket.expected.pipeName(),ticket.expected.profileDir(),ticket.saveWitness,ticket.legacyProjection);
        requireCurrent(same,ticket);
    }

    public Verified verify(Session same,Expected expected)throws IOException {
        Objects.requireNonNull(expected);writer.requireSession(same);String head=same.head().digest();
        try {
            requireProfileSave(expected.profileDir(),expected.saveRef());
            Loaded driver=readPhysical(expected.driverRef(),expected.driverIdentity(),true);
            Loaded save=readPhysical(expected.saveRef(),expected.saveIdentity(),false);
            Obj payload=DriverJson.object(driver.retainedBytes(),MAXIMUM_DRIVER_BYTES);
            Obj anchor=normalizePayload(payload,expected.pipeName(),expected.profileDir(),save.witness());
            StrictJson.require(object(payload.get("last_checkpoint"),"complete raw last_checkpoint").equals(expected.expectedRawCheckpoint()),"physical Driver raw checkpoint differs from canonical review");
            StrictJson.require(anchor.equals(expected.expectedNormalizedAnchor()),"physical normalized checkpoint differs from canonical review");
            StrictJson.require(array(payload.get("command_history"),"complete Driver command history").items().size()==expected.expectedHistoryRows(),"physical complete Driver history count differs from canonical review");
            requireHead(same,head);
            // Recheck both OS identities after the other file was read. The digest was computed from the complete physical read.
            requireIdentity(expected.driverRef(),driver.witness().identity());requireIdentity(expected.saveRef(),save.witness().identity());
            return new Verified(this,same,head,expected,driver.witness(),save.witness(),driver.retainedBytes(),payload,anchor);
        }catch(IllegalArgumentException malformed){throw new IOException("actual cold checkpoint validation failed",malformed);}
    }
    public void requireCurrent(Session same,Verified ticket)throws IOException {
        Objects.requireNonNull(ticket);writer.requireSession(same);
        if(ticket.issuer!=this||ticket.scope!=same)throw new IOException("cold checkpoint ticket belongs to another concrete owner or borrowed writer scope");
        requireHead(same,ticket.headDigest);requireProfileSave(ticket.expected.profileDir(),ticket.expected.saveRef());
        readPhysical(ticket.driverWitness.reference(),ticket.driverWitness.identity(),false);
        readPhysical(ticket.saveWitness.reference(),ticket.saveWitness.identity(),false);requireHead(same,ticket.headDigest);
    }
    private void requireHead(Session same,String digest)throws IOException {
        writer.requireSession(same);if(!same.head().digest().equals(digest))throw new IOException("original writer head changed during cold checkpoint validation");
    }
    private Loaded readPhysical(ExactRef expected,FileStatIdentity identity,boolean retain)throws IOException {
        Path path=Path.of(expected.path());SharedSourceFiles.plainAncestors(path);requireIdentity(expected,identity);
        byte[] complete=retain?new byte[Math.toIntExact(expected.bytes())]:null;
        byte[] block=retain?null:new byte[65536];long consumed=0;MessageDigest digest=sha256();
        try(InputStream input=Files.newInputStream(path)) {
            while(consumed<expected.bytes()) {
                if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("cold checkpoint physical read interrupted");
                int count=retain?input.read(complete,Math.toIntExact(consumed),(int)Math.min(65536,expected.bytes()-consumed))
                        :input.read(block,0,(int)Math.min(block.length,expected.bytes()-consumed));
                if(count<0)throw new IOException("actual cold checkpoint source shortened while reading");if(count==0)continue;
                digest.update(retain?complete:block,retain?Math.toIntExact(consumed):0,count);consumed+=count;
            }
            if(input.read()!=-1)throw new IOException("actual cold checkpoint source grew while reading");
        }
        requireIdentity(expected,identity);
        if(!HexFormat.of().formatHex(digest.digest()).equals(expected.sha256()))throw new IOException("actual cold checkpoint bytes/SHA differ from canonical source");
        return new Loaded(new FileWitness(expected,identity),complete);
    }
    private void requireIdentity(ExactRef ref,FileStatIdentity expected)throws IOException {
        FileStatIdentity actual=identities.stat(Path.of(ref.path()));
        if(!actual.equals(expected)||!actual.bytes().equals(BigInteger.valueOf(ref.bytes())))throw new IOException("actual cold checkpoint OS inode/ns identity changed");
    }
    private static void requireProfileSave(Path profile,ExactRef save)throws IOException {
        absolute(profile);SharedSourceFiles.plainAncestors(profile);
        if(!profile.toRealPath().equals(profile))throw new IOException("actual original profile must be canonical");
        Path expected=profile.resolve("save games").resolve(CHECKPOINT_FILENAME);SharedSourceFiles.plainAncestors(expected);
        if(!expected.toRealPath().equals(Path.of(save.path())))throw new IOException("actual SAVE is not the canonical profile cold checkpoint");
    }
    /** Complete original legacy DATA normalization before its separate physical checkpoint projection. */
    static Obj normalizeLegacyPayload(Obj document,String pipe,Path profile,FileWitness actualSave) {
        return normalizeLegacyPayload(document,pipe,profile,actualSave,LegacyResumeNormalizer.LifecycleProjection.BOUND_OR_LEGACY);
    }
    /** DATA normalization only. Production selects explicit null solely from the retained private original profile. */
    static Obj normalizeLegacyPayload(Obj document,String pipe,Path profile,FileWitness actualSave,
            LegacyResumeNormalizer.LifecycleProjection projection) {
        var canonical=LegacyResumeNormalizer.normalize(document,pipe,LegacyResumeNormalizer.HistoryMaterialization.OMIT,Objects.requireNonNull(projection));
        StrictJson.require(canonical instanceof LegacyResumeNormalizer.Loaded,"legacy cold Driver failed the complete canonical resume consumer: "+
                (canonical instanceof LegacyResumeNormalizer.Rejected rejected?rejected.driverError():canonical));
        return normalizePayload(document,pipe,profile,actualSave);
    }
    /** Pure raw Driver -> normalized anchor; this result has no physical or writer qualification. */
    static Obj normalizePayload(Obj document,String pipe,Path profile,FileWitness actualSave) {
        Objects.requireNonNull(document);nonempty(pipe,"cold checkpoint pipe name must be nonempty");absolute(profile);Objects.requireNonNull(actualSave);
        Obj checkpoint=object(document.get("last_checkpoint"),"v2 checkpoint required");
        StrictJson.require(sameInteger(document.get("format_version"),BigInteger.TWO)&&text(document.get("pipe_name"),pipe)
                &&text(checkpoint.get("name"),CHECKPOINT_FILENAME),"cold checkpoint start requires a v2 driver state for this pipe");
        BigInteger size=integer(checkpoint.get("size"),"checkpoint size"),date=integer(checkpoint.get("date_raw"),"saved date"),historyIndex=integer(checkpoint.get("history_index"),"checkpoint history index");
        BigInteger character=integer(document.get("episode_character_id"),"episode character");String run=word(document.get("episode_run_id"),"episode run ID");
        String digest=word(checkpoint.get("sha256"),"checkpoint SHA");Arr history=array(document.get("command_history"),"complete command history");
        StrictJson.require(size.signum()>0&&digest.matches("[0-9a-f]{64}")&&historyIndex.signum()>0&&historyIndex.compareTo(BigInteger.valueOf(history.items().size()))<=0
                &&sameInteger(checkpoint.get("episode_character_id"),character)&&text(checkpoint.get("episode_run_id"),run),"cold checkpoint state has an incomplete checkpoint anchor");
        Obj row=object(history.items().get(historyIndex.intValueExact()-1),"checkpoint history row"),result=object(row.get("result"),"checkpoint result"),saved=object(result.get("checkpoint"),"checkpoint save result");
        StrictJson.require(sameInteger(row.get("index"),historyIndex)&&text(row.get("command"),"save-checkpoint")&&row.get("ok") instanceof Bool ok&&ok.value()
                &&sameInteger(saved.get("size"),size)&&text(saved.get("sha256"),digest)&&sameInteger(saved.get("date_raw"),date),"cold checkpoint history anchor does not match the save");
        Value normalized=Nil.INSTANCE;Value a=document.get("succession_lifecycle"),b=checkpoint.get("succession_lifecycle"),c=saved.get("succession_lifecycle");
        boolean documentHas=document.members().containsKey("succession_lifecycle"),checkpointHas=checkpoint.members().containsKey("succession_lifecycle"),savedHas=saved.members().containsKey("succession_lifecycle");
        if(documentHas||checkpointHas||savedHas) {
            StrictJson.require(documentHas&&checkpointHas&&savedHas,"cold checkpoint lifecycle source fields must all be present together");
            if(a==Nil.INSTANCE||b==Nil.INSTANCE||c==Nil.INSTANCE) {
                StrictJson.require(a==Nil.INSTANCE&&b==Nil.INSTANCE&&c==Nil.INSTANCE,"cold checkpoint explicit null/object lifecycle sources differ");
            }else {
                Obj first=lifecycle(a),second=lifecycle(b),third=lifecycle(c);
                StrictJson.require(first.equals(second)&&first.equals(third),"cold checkpoint succession lifecycle sources differ");normalized=first;
            }
        }
        Path expected=profile.resolve("save games").resolve(CHECKPOINT_FILENAME);
        StrictJson.require(Path.of(actualSave.reference().path()).equals(expected)&&BigInteger.valueOf(actualSave.reference().bytes()).equals(size)&&actualSave.reference().sha256().equals(digest),"cold checkpoint bytes differ from the v2 driver state");
        var anchor=new LinkedHashMap<String,Value>();anchor.put("name",new Text(CHECKPOINT_FILENAME));anchor.put("load_save_name",new Text(LOAD_SAVE_NAME));
        anchor.put("path",new Text(expected.toString()));anchor.put("size",new IntegerValue(size));anchor.put("sha256",new Text(digest));
        anchor.put("saved_date_raw",new IntegerValue(date));anchor.put("history_index",new IntegerValue(historyIndex));anchor.put("succession_lifecycle",normalized);
        return new Obj(anchor);
    }
    private static Obj lifecycle(Value value) {
        Obj row=object(value,"complete succession lifecycle binding");byte[] normalized=SuccessionLifecycleCodec.normalize(DriverJson.encode(row));
        return DriverJson.object(normalized,SuccessionLifecycleCodec.MAX_BYTES);
    }
    private static boolean present(Value value){return value!=null&&value!=Nil.INSTANCE;}
    private static Obj object(Value value,String field){if(value instanceof Obj row)return row;throw new IllegalArgumentException(field);}
    private static Arr array(Value value,String field){if(value instanceof Arr rows)return rows;throw new IllegalArgumentException(field);}
    private static BigInteger integer(Value value,String field){if(value instanceof IntegerValue number)return number.value();throw new IllegalArgumentException("exact integer required: "+field);}
    private static boolean sameInteger(Value value,BigInteger expected){return value instanceof IntegerValue number&&number.value().equals(expected);}
    private static boolean text(Value value,String expected){return value instanceof Text word&&word.value().equals(expected);}
    private static String word(Value value,String field){if(value instanceof Text word){nonempty(word.value(),field);return word.value();}throw new IllegalArgumentException(field);}
    private static void nonempty(String value,String field){StrictJson.require(value!=null&&!value.isEmpty(),field);}
    private static void absolute(Path path){StrictJson.require(path.isAbsolute()&&path.normalize().equals(path),"explicit canonical absolute original path required");}
    private static MessageDigest sha256(){try{return MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}}
}
