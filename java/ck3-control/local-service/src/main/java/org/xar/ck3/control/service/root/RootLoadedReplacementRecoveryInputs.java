package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Fresh source DATA for the existing worker's already-created Saved Game route. No launch capability. */
public final class RootLoadedReplacementRecoveryInputs {
    public static final String SCHEMA="xar.java-existing-saved-replacement-recovery/v1";
    public static final String ORDINARY_SCHEMA="xar.java-existing-saved-replacement-recovery/v2";
    public enum Mode { NATIVE_CAMPAIGN,ORDINARY_PROFILE3 }
    private static final int LIMIT=65536;
    private RootLoadedReplacementRecoveryInputs(){ }
    public record Request(String machineId,Instant issuedAt,Instant deadline,ExactRef runtimeConfiguration,
            ExactRef ownerDescriptor,ExactRef parentControl,ExactRef generationClaim,ExactRef checkpointPair,
            ExactRef currentLoadedProfile,ExactRef savedPolicy,Path evidenceDirectory,String expectedHeadDigest,Mode mode) {
        public Request(String machineId,Instant issuedAt,Instant deadline,ExactRef runtimeConfiguration,
                ExactRef ownerDescriptor,ExactRef parentControl,ExactRef generationClaim,ExactRef checkpointPair,
                ExactRef currentLoadedProfile,ExactRef savedPolicy,Path evidenceDirectory,String expectedHeadDigest) {
            this(machineId,issuedAt,deadline,runtimeConfiguration,ownerDescriptor,parentControl,generationClaim,checkpointPair,
                    currentLoadedProfile,savedPolicy,evidenceDirectory,expectedHeadDigest,Mode.NATIVE_CAMPAIGN);
        }
        public Request {
            java.util.Objects.requireNonNull(mode);
            StrictJson.text(machineId);
            StrictJson.require(issuedAt.isBefore(deadline)&&Duration.between(issuedAt,deadline).compareTo(Duration.ofMinutes(45))<=0,
                    "fresh finite loaded recovery source must fit45 minutes");
            for(var ref:List.of(runtimeConfiguration,ownerDescriptor,parentControl,generationClaim,checkpointPair,currentLoadedProfile,savedPolicy))
                StrictJson.require(ref.bytes()>0&&ref.bytes()<=(1L<<20)&&Path.of(ref.path()).isAbsolute(),"bounded exact loaded source originals required");
            StrictJson.require(evidenceDirectory.isAbsolute()&&evidenceDirectory.normalize().equals(evidenceDirectory),
                    "exact fresh loaded evidence directory required");
            StrictJson.require(expectedHeadDigest!=null&&expectedHeadDigest.matches("[0-9a-f]{64}"),"original unchanged predecessor digest required");
        }
        public CheckpointPair pair()throws IOException {
            return CheckpointPairCodec.decode(read(checkpointPair,LIMIT));
        }
        public void requireCurrent(Clock clock)throws IOException {
            Instant now=clock.instant();
            if(now.isBefore(issuedAt)||!now.isBefore(deadline))throw new IOException("new loaded recovery source window expired");
            for(var ref:List.of(runtimeConfiguration,ownerDescriptor,parentControl,generationClaim,checkpointPair,currentLoadedProfile,savedPolicy))verify(ref);
        }
    }
    public static Request readExact(ExactRef original,Clock clock)throws IOException {
        var held=SharedSourceFiles.observe(Path.of(original.path()));
        if(!same(held.source(),original))throw new IOException("loaded recovery source identity differs");
        try {
            var result=decode(read(original,LIMIT));
            result.requireCurrent(clock);SharedSourceFiles.assertUnchanged(held);return result;
        } catch(IllegalArgumentException invalid){throw new IOException("invalid loaded recovery source",invalid);}
    }
    public static Request decode(byte[] bytes) {
        var version=StrictJson.parse(bytes,LIMIT).get("schema");
        if(version!=null&&version.isTextual()&&ORDINARY_SCHEMA.equals(version.textValue()))return decodeOrdinary(bytes);
            var row=StrictJson.object(StrictJson.parse(bytes,LIMIT),Set.of("schema","machine_id","issued_at_utc","deadline_utc",
                    "runtime_configuration","owner_descriptor","parent_control","generation_claim","checkpoint_pair","current_loaded_profile",
                    "saved_policy","evidence_directory","expected_head_digest"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact loaded recovery source version required");
            return new Request(StrictJson.text(row.get("machine_id")),Instant.parse(StrictJson.text(row.get("issued_at_utc"))),
                    Instant.parse(StrictJson.text(row.get("deadline_utc"))),ExactRef.fromJson(row.get("runtime_configuration")),
                    ExactRef.fromJson(row.get("owner_descriptor")),ExactRef.fromJson(row.get("parent_control")),
                    ExactRef.fromJson(row.get("generation_claim")),ExactRef.fromJson(row.get("checkpoint_pair")),
                    ExactRef.fromJson(row.get("current_loaded_profile")),ExactRef.fromJson(row.get("saved_policy")),
                    Path.of(StrictJson.text(row.get("evidence_directory"))),StrictJson.text(row.get("expected_head_digest")));
    }
    /** Metadata only. Eligibility comes from the later actual LoadedReplacement and complete Core proof. */
    public static byte[] encode(Request value) {
        if(value.mode()==Mode.ORDINARY_PROFILE3)return encodeOrdinary(value);
        var row=StrictJson.object().put("schema",SCHEMA).put("machine_id",value.machineId())
                .put("issued_at_utc",value.issuedAt().toString()).put("deadline_utc",value.deadline().toString())
                .put("evidence_directory",value.evidenceDirectory().toString()).put("expected_head_digest",value.expectedHeadDigest());
        row.set("runtime_configuration",value.runtimeConfiguration().toJson());row.set("owner_descriptor",value.ownerDescriptor().toJson());
        row.set("parent_control",value.parentControl().toJson());row.set("generation_claim",value.generationClaim().toJson());
        row.set("checkpoint_pair",value.checkpointPair().toJson());row.set("current_loaded_profile",value.currentLoadedProfile().toJson());
        row.set("saved_policy",value.savedPolicy().toJson());return StrictJson.canonical(row,LIMIT);
    }
    private static Request decodeOrdinary(byte[] bytes) {
        var row=StrictJson.object(StrictJson.parse(bytes,LIMIT),Set.of("schema","machine_id","issued_at_utc","deadline_utc",
                "runtime_configuration","owner_descriptor","parent_control","generation_claim","checkpoint_pair","current_loaded_profile",
                "saved_policy","evidence_directory","expected_head_digest","recovery_mode"));
        StrictJson.require(ORDINARY_SCHEMA.equals(StrictJson.text(row.get("schema")))
                &&"ordinary_profile3".equals(StrictJson.text(row.get("recovery_mode"))),"explicit ordinary recovery version/mode required");
        var shared=row.deepCopy();shared.remove("recovery_mode");shared.put("schema",SCHEMA);
        var value=decode(StrictJson.canonical(shared,LIMIT));
        return new Request(value.machineId(),value.issuedAt(),value.deadline(),value.runtimeConfiguration(),value.ownerDescriptor(),
                value.parentControl(),value.generationClaim(),value.checkpointPair(),value.currentLoadedProfile(),value.savedPolicy(),
                value.evidenceDirectory(),value.expectedHeadDigest(),Mode.ORDINARY_PROFILE3);
    }
    private static byte[] encodeOrdinary(Request value) {
        var legacy=new Request(value.machineId(),value.issuedAt(),value.deadline(),value.runtimeConfiguration(),value.ownerDescriptor(),
                value.parentControl(),value.generationClaim(),value.checkpointPair(),value.currentLoadedProfile(),value.savedPolicy(),
                value.evidenceDirectory(),value.expectedHeadDigest());
        var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(legacy),LIMIT);row.put("schema",ORDINARY_SCHEMA);
        row.put("recovery_mode","ordinary_profile3");return StrictJson.canonical(row,LIMIT);
    }
    public static final String IMPORTED_SCHEMA="xar.java-existing-imported-saved-replacement-recovery/v3";

    /** Fresh bounded READ request with the exact unchanged post-retirement predecessor. */
    public record ImportedRequest(String machineId,Instant issuedAt,Instant deadline,ExactRef originalRecoveryRequest,
            ExactRef ownerDescriptor,ExactRef parentControl,ExactRef generationClaim,Path evidenceDirectory,
            long expectedPredecessorSequence,String expectedHeadDigest) {
        public ImportedRequest {
            StrictJson.text(machineId);
            StrictJson.require(issuedAt.isBefore(deadline)&&Duration.between(issuedAt,deadline).compareTo(Duration.ofMinutes(45))<=0,
                    "Fresh finite imported loaded recovery must fit forty-five minutes");
            for(var ref:List.of(originalRecoveryRequest,ownerDescriptor,parentControl,generationClaim))
                StrictJson.require(ref.bytes()>0&&ref.bytes()<=(1L<<20)&&Path.of(ref.path()).isAbsolute(),"Bounded exact imported loaded original required");
            StrictJson.require(parentControl.bytes()<=LIMIT&&generationClaim.bytes()<=LIMIT&&originalRecoveryRequest.bytes()<=LIMIT,
                    "Imported replacement controls and historical request must fit 64 KiB");
            StrictJson.require(evidenceDirectory.isAbsolute()&&evidenceDirectory.normalize().equals(evidenceDirectory),
                    "Exact fresh imported loaded evidence directory required");
            StrictJson.require(expectedPredecessorSequence>0&&expectedHeadDigest!=null&&expectedHeadDigest.matches("[0-9a-f]{64}"),
                    "Exact imported post-retirement predecessor sequence and digest required");
        }
        public void requireCurrent(Clock clock)throws IOException {
            Instant now=clock.instant();
            if(now.isBefore(issuedAt)||!now.isBefore(deadline))throw new IOException("Imported loaded recovery READ window expired");
            for(var ref:List.of(originalRecoveryRequest,parentControl,generationClaim))readStable(ref,LIMIT);
            readStable(ownerDescriptor,1<<20);
        }
        /** Reads the selected exact3 without refreshing an old operation or re-labeling either saved source. */
        public OriginalImportedRequest original()throws IOException {
            try {
                var row=StrictJson.parse(readStable(originalRecoveryRequest,LIMIT),LIMIT);
                if(RootLoadedSavedResumeMain250.requestMode(row)!=3||!machineId.equals(StrictJson.text(row.get("machineId"))))
                    throw new IOException("Imported loaded recovery requires the same machine's exact original recovery request");
                return new OriginalImportedRequest(ExactRef.fromJson(row.get("sourceRuntimeConfiguration")),
                        ExactRef.fromJson(row.get("newRuntimeConfiguration")),ExactRef.fromJson(row.get("sourceConfirmation")),
                        ExactRef.fromJson(row.get("checkpointPair")),Path.of(StrictJson.text(row.get("ownerDirectory"))));
            } catch(IllegalArgumentException invalid) {
                throw new IOException("Invalid exact original recovery request",invalid);
            }
        }
    }
    public record OriginalImportedRequest(ExactRef sourceRuntimeConfiguration,ExactRef runtimeConfiguration,
            ExactRef sourceConfirmation,ExactRef checkpointPair,Path originalOwnerDirectory) {
        public OriginalImportedRequest {
            for(var ref:List.of(sourceRuntimeConfiguration,runtimeConfiguration,sourceConfirmation,checkpointPair))
                StrictJson.require(ref.bytes()>0&&Path.of(ref.path()).isAbsolute(),"Nonempty exact historical source reference required");
            StrictJson.require(originalOwnerDirectory.isAbsolute()&&originalOwnerDirectory.equals(originalOwnerDirectory.normalize()),
                    "Exact original owner directory required");
        }
        public CheckpointPair pair()throws IOException {return CheckpointPairCodec.decode(readStable(checkpointPair,LIMIT));}
    }

    public static ImportedRequest readImportedExact(ExactRef original,Clock clock)throws IOException {
        try {
            var result=decodeImported(readStable(original,LIMIT));
            result.requireCurrent(clock);return result;
        } catch(IllegalArgumentException|java.time.DateTimeException invalid) {
            throw new IOException("Invalid loaded imported recovery source",invalid);
        }
    }
    public static ImportedRequest decodeImported(byte[] bytes) {
        var row=StrictJson.object(StrictJson.parse(bytes,LIMIT),Set.of("schema","machine_id","issued_at_utc","deadline_utc",
                "original_recovery_request","owner_descriptor","parent_control","generation_claim","evidence_directory",
                "expected_predecessor_sequence","expected_head_digest"));
        StrictJson.require(IMPORTED_SCHEMA.equals(StrictJson.text(row.get("schema"))),"Exact imported loaded recovery source version required");
        return new ImportedRequest(StrictJson.text(row.get("machine_id")),Instant.parse(StrictJson.text(row.get("issued_at_utc"))),
                Instant.parse(StrictJson.text(row.get("deadline_utc"))),ExactRef.fromJson(row.get("original_recovery_request")),
                ExactRef.fromJson(row.get("owner_descriptor")),ExactRef.fromJson(row.get("parent_control")),ExactRef.fromJson(row.get("generation_claim")),
                Path.of(StrictJson.text(row.get("evidence_directory"))),StrictJson.integer(row.get("expected_predecessor_sequence"),1,Long.MAX_VALUE),
                StrictJson.text(row.get("expected_head_digest")));
    }
    public static byte[] encodeImported(ImportedRequest value) {
        var row=StrictJson.object().put("schema",IMPORTED_SCHEMA).put("machine_id",value.machineId())
                .put("issued_at_utc",value.issuedAt().toString()).put("deadline_utc",value.deadline().toString())
                .put("evidence_directory",value.evidenceDirectory().toString()).put("expected_head_digest",value.expectedHeadDigest())
                .put("expected_predecessor_sequence",value.expectedPredecessorSequence());
        row.set("original_recovery_request",value.originalRecoveryRequest().toJson());
        row.set("owner_descriptor",value.ownerDescriptor().toJson());row.set("parent_control",value.parentControl().toJson());
        row.set("generation_claim",value.generationClaim().toJson());return StrictJson.canonical(row,LIMIT);
    }
    private static byte[] readStable(ExactRef ref,int maximum)throws IOException {
        if(ref.bytes()<1||ref.bytes()>maximum)throw new IOException("Loaded original exceeds its finite role bound");
        Path path=Path.of(ref.path());
        var held=SharedSourceFiles.nativeFile(path);
        if(held.logicalBytes()!=ref.bytes())throw new IOException("Loaded original differs from its exact size");
        var bytes=read(ref,maximum);
        if(!held.equals(SharedSourceFiles.nativeFile(path)))throw new IOException("Loaded original native identity changed");
        return bytes;
    }

    static byte[] read(ExactRef ref,int maximum)throws IOException {
        if(ref.bytes()<1||ref.bytes()>maximum)throw new IOException("loaded source exceeds its finite role bound");
        byte[] bytes;try(var in=Files.newInputStream(Path.of(ref.path()))){bytes=in.readNBytes(maximum+1);}
        if(bytes.length!=ref.bytes()||!org.xar.ck3.control.application.action.ActionCodec.sha256(bytes).equals(ref.sha256()))
            throw new IOException("loaded source original bytes changed");
        return bytes;
    }
    static void verify(ExactRef ref)throws IOException {new ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256()).verify();}
    static boolean same(ControlBuild.FileRef ref,ExactRef expected) {
        return Path.of(ref.path()).equals(Path.of(expected.path()))&&ref.bytes()==expected.bytes()&&ref.sha256().equals(expected.sha256());
    }
}

