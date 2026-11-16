package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.RootProcessAttach;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Explicit retained ordinary profile DATA. Only readExact binds an actual private loaded/material pair. */
public final class RootLoadedOrdinaryProfile {
    public static final String SCHEMA="xar.java-current-loaded-ordinary-run-profile/v6";
    public static final String REQUEST_SCHEMA="xar.java-original-driver-run-profile-producer-request/v3";
    private static final int LIMIT=65536,MATERIAL_LIMIT=1<<20;
    private static final Set<String> FIELDS=Set.of("profile","owner_descriptor","parent_control","generation_claim",
            "checkpoint_pair","saved_material","original_policy","policy_target");
    private RootLoadedOrdinaryProfile(){ }
    public record Request(RootFrozenRunProfile.Request profile,ExactRef ownerDescriptor,ExactRef parentControl,
            ExactRef generationClaim,ExactRef checkpointPair,CheckpointPair.FileWitness savedMaterial,
            ExactRef originalPolicy,Path policyTarget) {
        public Request {
            Objects.requireNonNull(profile);Objects.requireNonNull(savedMaterial);Objects.requireNonNull(policyTarget);
            require(profile.lifecycle()==RootFrozenRunProfile.LifecycleMode.ORDINARY_CAMPAIGN_SUCCESSION
                    &&profile.ordinaryCampaignNoPact()&&profile.legacyImport() instanceof RootFrozenRunProfile.Enabled,
                    "explicit ordinary succession loaded profile required");
            require(Duration.between(profile.observedAt(),profile.reviewAt()).compareTo(Duration.ofMinutes(45))<=0,
                    "ordinary loaded profile must fit the fresh source window");
            for(var ref:List.of(ownerDescriptor,parentControl,generationClaim,checkpointPair,originalPolicy,savedMaterial.reference()))
                require(ref.bytes()>0&&ref.bytes()<=MATERIAL_LIMIT&&Path.of(ref.path()).isAbsolute(),"bounded original ordinary source required");
            require(policyTarget.isAbsolute()&&policyTarget.normalize().equals(policyTarget)
                    &&!policyTarget.equals(Path.of(originalPolicy.path())),"new distinct ordinary policy target required");
        }
    }
    public record PolicyCopy(Path target,byte[] bytes) {
        public PolicyCopy {Objects.requireNonNull(target);bytes=bytes.clone();}
        @Override public byte[] bytes(){return bytes.clone();}
    }
    public static byte[] encodeRequest(Request value) {
        var row=fields(value);row.put("schema",REQUEST_SCHEMA);return StrictJson.canonical(row,LIMIT);
    }
    public static Request decodeRequest(byte[] raw) {
        var keys=new java.util.HashSet<>(FIELDS);keys.add("schema");
        var row=StrictJson.object(StrictJson.parse(raw,LIMIT),keys);
        require(REQUEST_SCHEMA.equals(StrictJson.text(row.get("schema"))),"ordinary loaded producer version required");return request(row);
    }
    private static ObjectNode fields(Request value) {
        var row=StrictJson.object();row.set("profile",StrictJson.parse(RootFrozenRunProfile.encode(value.profile()),LIMIT));
        row.set("owner_descriptor",value.ownerDescriptor().toJson());row.set("parent_control",value.parentControl().toJson());
        row.set("generation_claim",value.generationClaim().toJson());row.set("checkpoint_pair",value.checkpointPair().toJson());
        row.set("saved_material",CheckpointPairCodec.fileWitnessToJson(value.savedMaterial()));
        row.set("original_policy",value.originalPolicy().toJson());row.put("policy_target",value.policyTarget().toString());return row;
    }
    private static Request request(ObjectNode row) {
        return new Request(RootFrozenRunProfile.decode(StrictJson.canonical(row.get("profile"),LIMIT)),
                ExactRef.fromJson(row.get("owner_descriptor")),ExactRef.fromJson(row.get("parent_control")),
                ExactRef.fromJson(row.get("generation_claim")),ExactRef.fromJson(row.get("checkpoint_pair")),
                CheckpointPairCodec.fileWitnessFromJson(row.get("saved_material")),ExactRef.fromJson(row.get("original_policy")),
                Path.of(StrictJson.text(row.get("policy_target"))));
    }
    public static final class Prepared {
        private final Request request;private final byte[] bytes,policy;private final List<SharedSourceFiles.Witness> originals;private final Clock clock;
        private Prepared(Request request,byte[] bytes,byte[] policy,List<SharedSourceFiles.Witness> originals,Clock clock){
            this.request=request;this.bytes=bytes.clone();this.policy=policy.clone();this.originals=List.copyOf(originals);this.clock=clock;
        }
        public Request request(){return request;}
        public byte[] bytes(){return bytes.clone();}
        public PolicyCopy policyCopy(){return new PolicyCopy(request.policyTarget(),policy);}
        public void verifyOriginals()throws IOException {
            current(request.profile(),clock);for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        }
        public void verifyCreated(Path target)throws IOException {
            verifyOriginals();require(Arrays.equals(read(exact(target,bytes),LIMIT),bytes),"ordinary profile differs from its original producer");
            require(Arrays.equals(read(exact(request.policyTarget(),policy),MATERIAL_LIMIT),policy),"ordinary policy copy differs from its source");verifyOriginals();
        }
    }
    /** Metadata and original policy bytes only; the existing Body writer owns both CREATE_NEW outputs. */
    public static Prepared prepare(Request request,Path target,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);current(request.profile(),clock);
        require(target.isAbsolute()&&target.normalize().equals(target)&&target.getParent().equals(request.policyTarget().getParent())
                &&!target.equals(request.policyTarget()),"ordinary policy and profile require distinct sibling outputs");
        var held=new ArrayList<SharedSourceFiles.Witness>();
        for(var ref:List.of(request.profile().environmentManifest(),request.ownerDescriptor(),request.parentControl(),
                request.generationClaim(),request.checkpointPair(),request.originalPolicy(),request.savedMaterial().reference()))retain(ref,held);
        byte[] policy=read(request.originalPolicy(),MATERIAL_LIMIT);RawJson lifecycle=policyLifecycle(policy);
        var files=new NativeCheckpointFiles();files.verify(request.savedMaterial());
        var material=StrictJson.object(StrictJson.parse(files.read(request.savedMaterial(),MATERIAL_LIMIT),MATERIAL_LIMIT),
                Set.of("schema","pair","session","proof","original_writer_head","original_writer_head_sha256","checkpoint_binding_sha256","cycle_authority_sha256"));
        var pair=CheckpointPairCodec.decode(read(request.checkpointPair(),LIMIT));
        require(SavedAttachmentSourceStore.MATERIAL_SCHEMA.equals(StrictJson.text(material.get("schema")))
                &&pair.equals(CheckpointPairCodec.decode(StrictJson.canonical(material.get("pair"),MATERIAL_LIMIT))),"ordinary policy source changed its actual pair");
        require(StrictJson.integer(material.get("proof").get("semantic").get("frame").get("observation_version"),3,3)==3,
                "ordinary retained policy requires its original profile-three SEM");
        retain(pair.driver().reference(),held);files.verify(pair.driver());
        var saved=DriverStateSnapshot.decodeComplete(files.read(pair.driver(),DriverCheckpointStore.MAX_DRIVER_BYTES));
        requireLifecycle(saved,lifecycle);files.verify(request.savedMaterial());
        var row=fields(request);row.put("schema",SCHEMA);row.set("ordinary_policy",exact(request.policyTarget(),policy).toJson());
        var result=new Prepared(request,StrictJson.canonical(row,LIMIT),policy,held,clock);result.verifyOriginals();return result;
    }
    /** DATA check only. A caller cannot obtain a LoadedReplacement or SavedMaterial through this method. */
    public static RawJson requireMaterial(Session same,SavedCheckpointMaterial material,byte[] policy)throws IOException {
        require(material instanceof SavedAttachmentSourceStore.SavedMaterial,"ordinary loaded policy requires its private ordinary material");
        require(material.sourceSemantic().frame().observationVersion()==3,"ordinary loaded source must retain its actual profile-three SEM");
        var original=(SavedAttachmentSourceStore.SavedMaterial)material;
        original.requireSemanticDriver(same,original.savedDriver());
        RawJson lifecycle=policyLifecycle(policy);requireLifecycle(original.savedDriver(),lifecycle);return lifecycle;
    }
    public static final class Qualified {
        private final Request request;private final NativeLaunchPlan plan;private final RootProcessAttach.LoadedReplacement role;
        private final SavedCheckpointMaterial material;private final List<SharedSourceFiles.Witness> originals;private final Clock clock;
        private Qualified(Request request,NativeLaunchPlan plan,RootProcessAttach.LoadedReplacement role,
                SavedCheckpointMaterial material,List<SharedSourceFiles.Witness> originals,Clock clock) {
            this.request=request;this.plan=plan;this.role=role;this.material=material;this.originals=List.copyOf(originals);this.clock=clock;
        }
        public void requireCurrent()throws IOException {
            current(request.profile(),clock);requireRole(request,plan,role);
            for(var original:originals)SharedSourceFiles.assertUnchanged(original);
            require(material.witness().equals(request.savedMaterial())&&material.pair().equals(role.pair()),"ordinary loaded material identity changed");
        }
    }
    /** Only this actual same-plan LoadedReplacement and private SavedMaterial can select the ordinary consumer route. */
    public static Qualified readExact(ExactRef source,ExactRef policy,ExactRef runtimeConfiguration,NativeLaunchPlan plan,
            RootProcessAttach.LoadedReplacement role,Session same,SavedCheckpointMaterial material,
            InitialEpisodePolicy configuredPolicy,Clock clock)throws IOException {
        Objects.requireNonNull(role);Objects.requireNonNull(plan);Objects.requireNonNull(same);Objects.requireNonNull(material);
        var held=new ArrayList<SharedSourceFiles.Witness>();retain(source,held);retain(policy,held);retain(runtimeConfiguration,held);
        var keys=new java.util.HashSet<>(FIELDS);keys.add("schema");keys.add("ordinary_policy");
        var row=StrictJson.object(StrictJson.parse(read(source,LIMIT),LIMIT),keys);
        require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"explicit ordinary loaded profile version required");
        Request request=request(row);current(request.profile(),clock);requireRole(request,plan,role);
        require(sameRef(ExactRef.fromJson(row.get("ordinary_policy")),policy)
                &&Path.of(policy.path()).equals(request.policyTarget()),"ordinary policy differs from its current profile output");
        require(material instanceof SavedAttachmentSourceStore.SavedMaterial&&material.witness().equals(request.savedMaterial())
                &&material.pair().equals(role.pair())&&material.session().machineId().equals(request.profile().machineId()),
                "ordinary loaded profile lacks its exact private saved material");
        var configuration=StrictJson.parse(read(runtimeConfiguration,MATERIAL_LIMIT),MATERIAL_LIMIT);
        require(configuration.isObject(),"actual runtime configuration object required");
        Path initial=Path.of(StrictJson.text(configuration.get("initial_policy_file")));
        if(!initial.isAbsolute())initial=Path.of(runtimeConfiguration.path()).getParent().resolve(initial).normalize();
        require(initial.equals(Path.of(request.originalPolicy().path())),"ordinary policy source differs from the actual configuration");
        for(var ref:List.of(request.originalPolicy(),request.checkpointPair(),request.savedMaterial().reference(),request.profile().environmentManifest()))retain(ref,held);
        byte[] copied=read(policy,MATERIAL_LIMIT),original=read(request.originalPolicy(),MATERIAL_LIMIT);
        require(Arrays.equals(copied,original),"ordinary loaded policy is not the exact original policy copy");
        RawJson lifecycle=requireMaterial(same,material,copied);
        require(configuredPolicy.kind()==InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION
                &&Arrays.equals(SuccessionLifecycleCodec.normalize(configuredPolicy.lifecycle().bytes()),lifecycle.bytes()),
                "configured ordinary lifecycle differs from the genuine saved Driver");
        var environment=plan.preparedProfile().environmentManifest();
        require(RootLoadedReplacementRecoveryInputs.same(environment,request.profile().environmentManifest()),"ordinary profile environment differs from its actual plan");
        InitialEpisodePolicy.requireSavedProfileDomain(org.xar.ck3.control.build.NativeRunProfileManifest.readEnvironmentOriginal(environment));
        var result=new Qualified(request,plan,role,material,held,clock);result.requireCurrent();return result;
    }
    private static void requireRole(Request request,NativeLaunchPlan plan,RootProcessAttach.LoadedReplacement role)throws IOException {
        var profile=request.profile();role.requireCurrent(profile.reviewAt());role.sourceWindow().requireOwner(role,profile.reviewAt());
        require(role.attached().launchPlan()==plan&&profile.requestId().equals(plan.requestId())&&profile.sessionId().equals(plan.sessionId())
                &&profile.machineId().equals(plan.sources().review().machineId()),"ordinary loaded profile crossed its identical actual plan");
        require(profile.legacyImport() instanceof RootFrozenRunProfile.Enabled enabled&&enabled.stateDirectory().equals(plan.stateDirectory())
                &&plan.load() instanceof NativeLaunchPlan.SavedGame,"ordinary loaded profile requires its actual Saved plan/state");
        require(request.ownerDescriptor().equals(role.ownerDescriptor())&&request.parentControl().equals(role.parentControl())
                &&request.generationClaim().equals(role.generationClaim())
                &&CheckpointPairCodec.decode(read(request.checkpointPair(),LIMIT)).equals(role.pair()),"ordinary loaded original owner/pair differs");
        require(!profile.reviewAt().isAfter(role.sourceWindow().deadline()),"ordinary profile exceeds its actual finite source");
    }
    private static RawJson policyLifecycle(byte[] policy) {
        var row=StrictJson.object(StrictJson.parse(policy,MATERIAL_LIMIT),Set.of("schema","succession_lifecycle"));
        require("xar.java.initial-episode-policy/v1".equals(StrictJson.text(row.get("schema"))),"original ordinary policy schema required");
        byte[] lifecycle=StrictJson.canonical(row.get("succession_lifecycle"),MATERIAL_LIMIT);
        var binding=SuccessionLifecycleCodec.decode(lifecycle);require(binding.profile().ordinary(),"retained lifecycle is not ordinary succession");
        return new RawJson(SuccessionLifecycleCodec.encode(binding));
    }
    private static void requireLifecycle(DriverStateSnapshot.Complete saved,RawJson lifecycle) {
        require(saved.successionLifecycle() instanceof DriverStateSnapshot.Value,"ordinary saved Driver must retain its explicit lifecycle");
        var value=(DriverStateSnapshot.Value)saved.successionLifecycle();
        require(Arrays.equals(SuccessionLifecycleCodec.normalize(value.json()),lifecycle.bytes()),"ordinary policy changed the full saved lifecycle binding");
    }
    private static void current(RootFrozenRunProfile.Request request,Clock clock)throws IOException {
        RootRuntimeDefinitions.requireCurrent(request.machineId(),request.observedAt().toString(),request.reviewAt().toString(),
                WindowsJobProcess.currentMachineId(),clock,"explicit loaded ordinary source");
    }
    private static byte[] read(ExactRef ref,int maximum)throws IOException {return RootLoadedReplacementRecoveryInputs.read(ref,maximum);}
    private static void retain(ExactRef ref,List<SharedSourceFiles.Witness> held)throws IOException {
        var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        require(RootLoadedReplacementRecoveryInputs.same(witness.source(),ref),"ordinary original source changed");held.add(witness);
    }
    private static ExactRef exact(Path path,byte[] bytes){return new ExactRef(path.toString(),bytes.length,org.xar.ck3.control.application.action.ActionCodec.sha256(bytes));}
    private static boolean sameRef(ExactRef a,ExactRef b){return Path.of(a.path()).equals(Path.of(b.path()))&&a.bytes()==b.bytes()&&a.sha256().equals(b.sha256());}
}
