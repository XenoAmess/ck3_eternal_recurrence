package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.RootSavedLoadReadiness;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Original A14 same-Game Root mod-absence proof, with immutable sidecars and canonical string identities. */
final class ColdModAbsenceProof {
    private static final int LIMIT=262_144;
    private record Pin(ExactRef reference,FileStatIdentity identity) { }
    static final class Prepared {
        private final RootColdResumeSession session;
        private final ExactRef launch,manifest,mods,snapshot,readiness;
        private final List<Pin> inputs;
        private Prepared(RootColdResumeSession session,ExactRef launch,ExactRef manifest,ExactRef mods,
                ExactRef snapshot,ExactRef readiness,List<Pin> inputs) {
            this.session=session;this.launch=launch;this.manifest=manifest;this.mods=mods;
            this.snapshot=snapshot;this.readiness=readiness;this.inputs=List.copyOf(inputs);
        }
        List<ExactRef> sourcePins() { return inputs.stream().map(Pin::reference).toList(); }
        void requireCurrent() throws IOException { session.requireCurrent();requirePins(inputs); }
        Verified publish(RootColdStageReview.Reviewed reviewed) throws IOException {
            requireCurrent();
            StrictJson.require(reviewed.stage()==RootColdStageReview.Stage.MOD_ABSENCE_ROOT_REVIEW && reviewed.consumed(),
                    "actual original writer consumed independent same-Game Root mod review");
            reviewed.requireCurrent();
            ObjectNode launchBody=object(read(launch,LIMIT)),manifestBody=object(read(manifest,LIMIT));
            ObjectNode proof=build(launchBody,manifestBody,object(read(mods,65_536)),launch,manifest,mods,snapshot,
                    session.actualSavedLoad().log().path(),reviewed.reviewedAt().toString(),reviewed.approvalRef());
            Path directory=Path.of(launch.path()).getParent();
            ExactRef proofRef=write(directory.resolve("STAGED-MOD-ABSENCE-PROOF.json"),StrictJson.canonical(proof));
            ObjectNode sidecar=StrictJson.object(); sidecar.put("schema","xar.root-saved-cold-actual-bindings/v1");
            sidecar.put("machine_id",StrictJson.text(launchBody.get("machine_id")));
            sidecar.put("session_nonce",session.scopeNonce()); sidecar.set("basis_ref",session.restoreInputs().basis().reference().toJson());
            sidecar.set("qualification_ref",session.restoreInputs().qualificationRef().toJson());
            sidecar.set("plan_ref",session.restoreInputs().plan().toJson()); sidecar.set("quote_ref",session.restoreInputs().quote().toJson());
            sidecar.set("preflight_ref",session.restoreInputs().preflight().toJson()); sidecar.put("pipe_name",session.restoreInputs().pipeName());
            sidecar.set("actual_game",launch.toJson()); sidecar.set("mod_absence",proofRef.toJson());
            sidecar.set("environment_manifest",manifest.toJson()); sidecar.set("root_review_ref",reviewed.approvalRef().toJson());
            sidecar.set("expected_lifecycle",StrictJson.parse(session.restoreInputs().basis().bytes()).get("checkpoint").get("succession_lifecycle"));
            ExactRef sidecarRef=write(directory.resolve("STAGED-COLD-ACTUAL-BINDINGS.json"),StrictJson.canonical(sidecar));
            var pins=new ArrayList<>(inputs);pins.add(pin(reviewed.approvalRef()));pins.add(pin(proofRef));pins.add(pin(sidecarRef));
            Verified result=new Verified(sidecarRef,proofRef,launch,List.copyOf(pins));result.requireSourcesUnchanged();return result;
        }
    }
    static final class Verified {
        private final ExactRef sidecar,proof,launch;
        private final List<Pin> pins;
        private Verified(ExactRef sidecar,ExactRef proof,ExactRef launch,List<Pin> pins) {
            this.sidecar=sidecar;this.proof=proof;this.launch=launch;this.pins=pins;
        }
        ExactRef sidecarRef() { return sidecar; }
        ExactRef proofRef() { return proof; }
        ExactRef launchRef() { return launch; }
        List<ExactRef> sourcePins() { return pins.stream().map(Pin::reference).toList(); }
        void requireSourcesUnchanged() throws IOException { requirePins(pins); }
    }
    private ColdModAbsenceProof() { }
    static Prepared prepare(RootColdResumeSession session) throws IOException {
        session.requireCurrent(); var held=session.heldGame();held.verify();var ready=session.actualSavedLoad();
        var paths=session.statePaths(); var sources=session.approvedProgramSources();
        ExactRef manifest=find(sources,paths.environmentManifest()),mods=find(sources,paths.profileRoot().resolve("dlc_load.json"));
        Path root=session.ownedDirectory().resolve("mod-evidence-"+java.util.UUID.randomUUID().toString().replace("-",""));
        Files.createDirectory(root);var launch=StrictJson.object(); launch.put("schema","xar.root-held-saved-game-launch/v1");
        launch.put("machine_id",held.runtime().request().machineId()); launch.put("pid",held.identity().pid());
        launch.put("creation_filetime_decimal",held.identity().creationFiletimeDecimal());launch.put("executable",held.identity().executable());
        launch.set("executable_ref",exact(held.runtime().request().gameExecutable()).toJson());launch.put("session_nonce",session.scopeNonce());
        launch.put("observed_at_utc",java.time.Instant.now().toString());
        ExactRef launchRef=write(root.resolve("STAGED-ACTUAL-GAME-LAUNCH.json"),StrictJson.canonical(launch));
        ExactRef snapshot=snapshot(ready,root.resolve("STAGED-STARTUP-SNAPSHOT.log"));
        ObjectNode evidence=StrictJson.object();evidence.put("schema","xar.root-saved-cold-startup-snapshot/v1");
        evidence.put("machine_id",held.runtime().request().machineId());evidence.set("actual_game",launchRef.toJson());
        evidence.set("source_log",exact(ready.log()).toJson());evidence.put("source_native_identity",ready.nativeFile().identityKey());
        evidence.put("epoch_utc",ready.epoch().toString());evidence.put("readiness_observed_at_utc",ready.observedAt().toString());
        evidence.set("snapshot",snapshot.toJson());evidence.put("snapshot_scope","EXACT_COMPLETE_LINE_PREFIX_OF_RECORDED_CURRENT_EPOCH_LOG");
        evidence.put("start_byte",0);evidence.put("end_byte_exclusive",snapshot.bytes());
        evidence.putObject("setup").put("line",ready.setup().line()).put("text",ready.setup().text());
        evidence.putObject("in_game").put("line",ready.inGame().line()).put("text",ready.inGame().text());
        ExactRef readiness=write(root.resolve("STAGED-STARTUP-SNAPSHOT-SOURCE.json"),StrictJson.canonical(evidence));
        List<Pin> pins=new ArrayList<>();for(ExactRef ref:List.of(launchRef,manifest,mods,snapshot,readiness)){pins.add(pin(ref));}
        Prepared result=new Prepared(session,launchRef,manifest,mods,snapshot,readiness,pins);requirePins(pins);return result;
    }
    /** Original producer checks, with explicit decimal FILETIME storage for the new cross-language contract. */
    static ObjectNode build(ObjectNode launch,ObjectNode manifest,ObjectNode mods,ExactRef launchRef,ExactRef manifestRef,
            ExactRef modsRef,ExactRef snapshotRef,String originalLog,String reviewedAt,ExactRef reviewRef) {
        StrictJson.integer(launch.get("pid"),1,0xffff_ffffL);String birth=StrictJson.text(launch.get("creation_filetime_decimal"));
        StrictJson.require(birth.matches("[1-9][0-9]{0,19}") && new java.math.BigInteger(birth).compareTo(StrictJson.UINT64_MAX)<=0,
                "actual same-Game canonical uint64 FILETIME");
        String machine=StrictJson.text(launch.get("machine_id"));
        StrictJson.require(machine.equals(StrictJson.text(manifest.get("machine_id"))),"actual same-machine profile and held Game");
        Path profile=Path.of(StrictJson.text(manifest.get("profile_dir"))),log=Path.of(originalLog);
        String environment=StrictJson.text(manifest.get("environment_sha256"));
        StrictJson.require(profile.isAbsolute() && log.isAbsolute() && log.normalize().equals(log) && log.startsWith(profile.resolve("logs"))
                && environment.matches("[0-9a-f]{64}") && Path.of(modsRef.path()).equals(profile.resolve("dlc_load.json"))
                && modsRef.bytes()>0 && modsRef.bytes()<=65_536 && snapshotRef.bytes()>0 && snapshotRef.bytes()<=LIMIT,
                "actual isolated finite profile/startup snapshot sources");
        ObjectNode load=object(manifest.get("load_profile"));
        StrictJson.require(load.path("enabled_mods").isArray() && load.path("enabled_mods").isEmpty()
                && mods.path("enabled_mods").isArray() && mods.path("enabled_mods").isEmpty()
                && StrictJson.text(load.get("dlc_load_sha256")).equals(modsRef.sha256()),"actual known-empty enabled-mod profile bytes");
        StrictJson.utc(reviewedAt);
        ObjectNode proof=StrictJson.object();proof.put("schema","xar.verified-xar-mod-absence/v2");
        proof.put("game_pid",launch.get("pid").longValue());proof.put("game_creation_filetime_decimal",birth);proof.put("machine_id",machine);
        proof.put("status","ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED");proof.put("reviewer","/root");proof.put("at_utc",reviewedAt);
        proof.put("startup_log_reviewed",true);proof.put("enabled_mods_known",true);proof.put("loaded_mods_known",true);
        proof.putArray("enabled_mods");proof.putArray("loaded_mods");proof.put("environment_sha256",environment);proof.put("profile_dir",profile.toString());
        proof.set("profile_enabled_mods",modsRef.toJson());proof.set("startup_log_snapshot",snapshotRef.toJson());
        proof.put("startup_log_original_path",log.toString());proof.put("startup_log_snapshot_scope","EXACT_COMPLETE_LINE_PREFIX_OF_RECORDED_CURRENT_EPOCH_LOG");
        proof.set("actual_game",launchRef.toJson());proof.set("environment_manifest",manifestRef.toJson());proof.set("root_stage_review",reviewRef.toJson());return proof;
    }
    /** Recorded-prefix copier only. A public Ready data record does not mint Prepared/Verified proof custody. */
    static ExactRef snapshot(RootSavedLoadReadiness.Ready ready,Path destination) throws IOException {
        Path path=Path.of(ready.log().path());var before=SharedSourceFiles.nativeFile(path);
        StrictJson.require(before.identityKey().equals(ready.nativeFile().identityKey()) && before.logicalBytes()>=ready.log().bytes()
                && ready.log().bytes()>0 && ready.log().bytes()<=RootSavedLoadReadiness.MAX_LOG_BYTES,"same actual current-epoch log, bounded recorded prefix");
        MessageDigest digest;try{digest=MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
        ByteArrayOutputStream prefix=new ByteArrayOutputStream();long remaining=ready.log().bytes();
        try(var input=Files.newInputStream(path)) {
            byte[] buffer=new byte[16<<10];
            while(remaining>0) {
                int count=input.read(buffer,0,(int)Math.min(buffer.length,remaining));if(count<0){throw new IOException("recorded startup log ended early");}
                digest.update(buffer,0,count);int take=Math.min(count,LIMIT-prefix.size());if(take>0){prefix.write(buffer,0,take);}remaining-=count;
            }
        }
        StrictJson.require(HexFormat.of().formatHex(digest.digest()).equals(ready.log().sha256())
                && SharedSourceFiles.nativeFile(path).identityKey().equals(before.identityKey()),"exact recorded startup log window and original native file identity");
        byte[] bytes=prefix.toByteArray();int end=bytes.length;
        while(end>0 && bytes[end-1]!='\n'){end--;}
        StrictJson.require(end>0,"nonempty complete startup log lines required; no partial-line truncation");
        return write(destination,Arrays.copyOf(bytes,end));
    }
    private static ExactRef find(List<ControlBuild.FileRef> sources,Path path) {
        var found=sources.stream().filter(ref->Path.of(ref.path()).equals(path)).toList();
        StrictJson.require(found.size()==1,"one actual privately verified profile source");return exact(found.getFirst());
    }
    private static Pin pin(ExactRef ref) throws IOException { read(ref,LIMIT);return new Pin(ref,new WindowsSavedProofIdentityReader().stat(Path.of(ref.path()))); }
    private static void requirePins(List<Pin> pins) throws IOException {
        var identities=new WindowsSavedProofIdentityReader();for(Pin pin:pins){read(pin.reference(),LIMIT);StrictJson.require(pin.identity().equals(identities.stat(Path.of(pin.reference().path()))),"original Root proof/source native identity unchanged");}
    }
    private static byte[] read(ExactRef ref,int bound) throws IOException {
        StrictJson.require(ref.bytes()>0 && ref.bytes()<=bound,"bounded complete Root profile/evidence bytes");
        var identities=new WindowsSavedProofIdentityReader();Path path=Path.of(ref.path());var before=identities.stat(path);byte[] raw;
        try(var input=Files.newInputStream(path)){raw=input.readNBytes(bound+1);}
        StrictJson.require(raw.length==ref.bytes() && before.equals(identities.stat(path)) && RecoveryEvidence.sha256(raw).equals(ref.sha256()),"exact Root source bytes and native identity");return raw;
    }
    private static ExactRef write(Path path,byte[] bytes) throws IOException {
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);return new ExactRef(path.toString(),bytes.length,RecoveryEvidence.sha256(bytes));
    }
    private static ExactRef exact(ControlBuild.FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static ObjectNode object(byte[] raw){return object(StrictJson.parse(raw,LIMIT));}
    private static ObjectNode object(com.fasterxml.jackson.databind.JsonNode value){StrictJson.require(value instanceof ObjectNode,"actual original JSON object");return (ObjectNode)value;}
}
