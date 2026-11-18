package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Read-only source/actual-load mapping. Neither an original pair replacement nor Game/adoption authority. */
public final class NativeSavedGameClone {
    public static final String SCHEMA="xar.java-saved-source-clone/v1";
    private NativeSavedGameClone(){ }

    /** Acquire actual file/directory handles before the first policy quote; close before Game CREATE. */
    public static QualifiedCloneCustody qualify(NativeLaunchPlan identicalPlan,FileWitness originalSave)throws IOException {
        Objects.requireNonNull(identicalPlan);
        return qualify(identicalPlan,originalSave,QualifiedCloneCustody.DEFAULT_MAXIMUM_FILE_BYTES,
                identicalPlan.deadline(),java.time.Clock.systemUTC());
    }
    public static QualifiedCloneCustody qualify(NativeLaunchPlan identicalPlan,FileWitness originalSave,
            int maximumFileBytes,java.time.Instant until,java.time.Clock clock)throws IOException {
        return QualifiedCloneCustody.retain(identicalPlan,originalSave,maximumFileBytes,until,clock);
    }

    /** Lexical target only; no file, process or launch authority is implied. */
    public static Path actualPath(NativeLaunchPlan plan)throws IOException {
        Objects.requireNonNull(plan);
        if(!(plan.load() instanceof NativeLaunchPlan.SavedGame saved))throw new IOException("exact Saved plan required");
        Path profile=plan.profileDirectory();
        if(!profile.isAbsolute()||!profile.equals(profile.normalize()))throw new IOException("exact absolute profile required");
        return profile.resolve("save games").resolve(saved.basename()+".ck3");
    }

    /** Observes an already materialized target. This method never copies or rewrites either file. */
    public static Observation observe(NativeLaunchPlan identicalPlan,FileWitness originalSave)throws IOException {
        Objects.requireNonNull(originalSave);
        Path actual=actualPath(identicalPlan);
        var saved=(NativeLaunchPlan.SavedGame)identicalPlan.load();
        if(!new ExactRef(saved.save().path(),saved.save().bytes(),saved.save().sha256()).equals(originalSave.reference()))
            throw new IOException("Saved plan differs from the exact original pair source");
        Path profile=identicalPlan.profileDirectory(),saves=actual.getParent();
        SharedSourceFiles.plainAncestors(profile);SharedSourceFiles.plainAncestors(saves);
        var profileIdentity=SharedSourceFiles.nativeDirectory(profile);
        var savesIdentity=SharedSourceFiles.nativeDirectory(saves);
        var files=new NativeCheckpointFiles();files.verify(originalSave);
        var source=SharedSourceFiles.observe(Path.of(originalSave.reference().path()));
        var target=SharedSourceFiles.observe(actual);
        var actualSave=files.observe(actual).orElseThrow(()->new IOException("materialized SAVE target is missing"));
        if(actualSave.reference().bytes()!=originalSave.reference().bytes()
                ||!actualSave.reference().sha256().equals(originalSave.reference().sha256()))
            throw new IOException("actual load target differs from the original SAVE contents");
        boolean inPlace=Path.of(originalSave.reference().path()).equals(actual);
        if(!inPlace&&source.nativeFile().identityKey().equals(target.nativeFile().identityKey()))
            throw new IOException("external original and actual load target must not be hard-link aliases");
        if(inPlace&&!originalSave.equals(actualSave))throw new IOException("in-place original witness changed");
        Observation result=new Observation(identicalPlan,profile,profileIdentity,savesIdentity,originalSave,actualSave,source,target,inPlace);
        result.requireCurrent(identicalPlan,originalSave);return result;
    }

    /** Opaque physical-file observation only. JSON DATA cannot construct this object. */
    public static final class Observation {
        private final NativeLaunchPlan plan;
        private final Path profile;
        private final SharedSourceFiles.DirectoryIdentity profileIdentity,savesIdentity;
        private final FileWitness originalSave,actualSave;
        private final SharedSourceFiles.Witness source,target;
        private final boolean inPlace;
        private Observation(NativeLaunchPlan plan,Path profile,SharedSourceFiles.DirectoryIdentity profileIdentity,
                SharedSourceFiles.DirectoryIdentity savesIdentity,FileWitness originalSave,FileWitness actualSave,
                SharedSourceFiles.Witness source,SharedSourceFiles.Witness target,boolean inPlace) {
            this.plan=plan;this.profile=profile;this.profileIdentity=profileIdentity;this.savesIdentity=savesIdentity;
            this.originalSave=originalSave;this.actualSave=actualSave;this.source=source;this.target=target;this.inPlace=inPlace;
        }
        public Path profileDirectory(){return profile;}
        public FileWitness originalSave(){return originalSave;}
        public FileWitness actualSave(){return actualSave;}
        public boolean inPlace(){return inPlace;}
        public void requireCurrent(NativeLaunchPlan identicalPlan,FileWitness sameOriginal)throws IOException {
            if(identicalPlan!=plan||!originalSave.equals(sameOriginal))throw new IOException("source-clone observation crossed its original plan or pair witness");
            Path actual=actualPath(plan);
            if(!profileIdentity.equals(SharedSourceFiles.nativeDirectory(profile))
                    ||!savesIdentity.equals(SharedSourceFiles.nativeDirectory(actual.getParent())))
                throw new IOException("actual load profile directory identity changed");
            SharedSourceFiles.assertUnchanged(source);SharedSourceFiles.assertUnchanged(target);
            var files=new NativeCheckpointFiles();files.verify(originalSave);files.verify(actualSave);
            if(!actualSave.reference().path().equals(actual.toString()))throw new IOException("actual load target path changed");
        }
        /** Historical DATA, including both volume/FileID identities. It grants no current file or process permit. */
        public ObjectNode toJson() {
            var row=StrictJson.object();row.put("schema",SCHEMA);row.put("request_id",plan.requestId());row.put("session_id",plan.sessionId());
            row.put("profile_directory",profile.toString());row.set("profile_identity",directory(profileIdentity));
            row.set("save_directory_identity",directory(savesIdentity));
            row.set("original_save",CheckpointPairCodec.fileWitnessToJson(originalSave));
            row.set("actual_save",CheckpointPairCodec.fileWitnessToJson(actualSave));
            row.set("original_native_identity",nativeIdentity(source));row.set("actual_native_identity",nativeIdentity(target));
            row.put("in_place",inPlace);return row;
        }
    }
    private static ObjectNode directory(SharedSourceFiles.DirectoryIdentity identity) {
        var row=StrictJson.object();row.put("volume_serial_decimal",identity.volumeSerialDecimal());
        row.put("file_id_decimal",identity.fileIdDecimal());row.put("creation_filetime_decimal",identity.creationFiletimeDecimal());return row;
    }
    private static ObjectNode nativeIdentity(SharedSourceFiles.Witness witness) {
        var nativeFile=witness.nativeFile();var row=StrictJson.object();
        row.put("volume_serial_decimal",nativeFile.volumeSerialDecimal());row.put("file_id_decimal",nativeFile.fileIdDecimal());
        row.put("creation_filetime_decimal",nativeFile.creationFiletimeDecimal());return row;
    }
}
