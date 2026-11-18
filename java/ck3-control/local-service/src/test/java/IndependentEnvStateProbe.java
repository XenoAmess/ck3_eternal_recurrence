import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration;

/**
 * Focused actual ENV06 -> prepared-profile -> real launch/config DTO checks.
 * Main args: nonexistent absolute scratch directory, migration evidence root.
 * Run only by the Java owner with the actual application/native-transport/Tools
 * runtime. No launch, full EXE/Save read, canonical writer or production output.
 * The policy created under scratch is ordinaryVanilla DATA solely for decoding.
 */
final class IndependentEnvStateProbe {
    private static final String PREFIX="agent-live01/independent-writer01/";
    public static void main(String[] args)throws Exception {
        check(args.length==2,"usage: <new owned absolute scratch> <migration evidence root>");
        Path scratch=Path.of(args[0]).toAbsolutePath().normalize(),root=Path.of(args[1]).toAbsolutePath().normalize();
        check(Path.of(args[0]).isAbsolute()&&Path.of(args[1]).isAbsolute(),"absolute paths required");
        check(!scratch.startsWith(root.resolve("agent-live01")),"scratch must be independent of actual runtime evidence");
        check(Files.notExists(scratch)&&Files.isDirectory(scratch.getParent()),"new scratch with existing parent required");
        Files.createDirectory(scratch);
        FileRef envRef=ref(root,PREFIX+"env/xar-autoplayer-environment.json",36869,
                "f17e510f6690ed283b68555b347688a550b9153885f01bfa28ff59ee8dc7361d");
        FileRef requestRef=ref(root,"java-tools-formal-env01/meta/independent-writer-inputs06/SAVED-VANILLA-PRODUCER-REQUEST-V2.json",1652,
                "f9dbe44b962d9cd356c6f0b954a9fa61213f06e4fd714677ad8e62af385d825d");
        var env=(NativeRunProfileManifest.ExplicitManifest)NativeRunProfileManifest.readEnvironmentOriginal(envRef);
        var request=NativeRunProfileProducer.readExplicitRequest(requestRef);
        Path nativeState=root.resolve(PREFIX).normalize(),profile=nativeState.resolve("profile");
        check(env.request().equals(request),"ENV06 embeds the exact public producer request");
        check(Path.of(env.stateDir()).equals(nativeState)&&request.stateDir().equals(env.stateDir()),"ENV06 Native state is W");
        check(Path.of(env.profileDir()).equals(profile)&&request.profile().equals(profile),"ENV06 profile is W/profile");
        check(!nativeState.equals(profile),"Native state is distinct from profile");
        check(env.game().rawVersion().equals("1.21.0")&&!env.game().debugMode(),"actual ENV06 Florin debug=false retained");
        check(env.profile().mountedMods().isEmpty(),"SavedVanilla composition retained");
        System.out.println("PASS actual ENV06 public producer request/native-state/profile documents");

        FileRef planRef=ref(root,"agent-live01/control/INDEPENDENT-ENV-ARMY17-PLAN01.json",3972,
                "30a18ee015790147462e4a92395740a115a5559f6cd0ece25c3b7c88f367615f");
        var plan=NativeLaunchPlanCodec.fromJson(StrictJson.parse(small(planRef,1<<20),1<<20));
        check(plan.stateDirectory().equals(nativeState)&&plan.profileDirectory().equals(profile),"actual plan preserves the Native directory roles");
        check(plan.preparedProfile().environmentManifest().equals(envRef),"actual plan retains original ENV06 ref");
        var projected=NativeLaunchPlan.PreparedProfile.fromExplicitEnvironment(envRef,List.of());
        check(projected.kind()==NativeRunProfileManifest.ProfileKind.SAVED_VANILLA,"public projection keeps Saved domain");
        check(projected.preparedInputs().containsAll(env.requiredPreparedFileRefs()),"public projection retains original prepared inputs");
        check(projected.preparedInputs().contains(request.vanillaRules())&&projected.preparedInputs().contains(request.launcherSettings()),
                "public projection retains actual rules/launcher inputs");
        check(plan.preparedProfile().preparedInputs().containsAll(projected.preparedInputs()),"actual plan consumes public projection inputs");
        check(plan.equals(NativeLaunchPlanCodec.fromJson(NativeLaunchPlanCodec.toJson(plan))),"actual launch DTO round trip retains state/profile");
        check(((NativeLaunchPlan.SavedGame)plan.load()).save().bytes()==87144632,"actual plan retains original source SAVE metadata, not a new pair");
        System.out.println("PASS actual launch DTO/public prepared-profile projection");

        FileRef fieldsRef=ref(root,"agent-live01/control/INDEPENDENT-WRITER-CODEX-STATIC-FIELDS02.json",4417,
                "1b4dab0c102b9839dc3fb0745f6fc5bb53da90d84f017bb343dc4ff5b4dd1ca0");
        var unsigned=StrictJson.parse(small(fieldsRef,65536),65536);
        Path businessState=Path.of(unsigned.path("candidate_runtime_fields").path("state_dir").textValue());
        check(businessState.equals(nativeState.resolve("business/state")),"actual unsigned worker fields use W/business/state");
        Path policy=scratch.resolve("ordinary-policy-DATA.json");
        var policyData=StrictJson.object();policyData.set("succession_lifecycle",NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson());
        Files.write(policy,StrictJson.canonical(policyData),StandardOpenOption.CREATE_NEW);
        var config=StrictJson.object().put("schema","xar.java-ordinary-runtime-configuration/v1")
                .put("machine_id",request.machineId()).put("state_dir",businessState.toString())
                .put("stock_game_root",scratch.resolve("unused-stock").toString())
                .put("native_implementation",plan.review().bridgeDll().path()).put("launch_plan_file",planRef.path())
                .put("initial_policy_file",policy.toString()).put("campaign_deadline_file",scratch.resolve("unused-campaign.json").toString())
                .put("formal_war_budget",scratch.resolve("unused-budget.json").toString())
                .put("formal_war_model",scratch.resolve("unused-model.json").toString()).put("authority_id","slot29-directory-DATA");
        config.set("configured_build",StrictJson.object().put("version",env.game().rawVersion()).put("exe_sha256",env.game().executableSha256()));
        Path configuration=scratch.resolve("ordinary-runtime-DATA.json");
        Files.write(configuration,StrictJson.canonical(config),StandardOpenOption.CREATE_NEW);
        var ordinary=RootOrdinaryRuntimeConfiguration.read(configuration);
        check(ordinary.stateDirectory().equals(businessState),"actual ordinary configuration producer keeps its own business state");
        check(ordinary.stateDirectory().getParent().equals(nativeState.resolve("business")),"Assembly writer root derives from business state parent");
        check(!ordinary.stateDirectory().equals(plan.stateDirectory()),"business state and Native state remain separate");
        check(ordinary.launchPlanFile().equals(Path.of(planRef.path())),"business configuration consumes the unchanged Native plan");
        check(env.equals(NativeRunProfileManifest.readEnvironmentOriginal(envRef)),"original ENV06 remains byte-pinned");
        check(Files.notExists(scratch.resolve("continuity")),"probe never prepares a canonical writer");
        System.out.println("PASS actual unsigned worker fields -> ordinary configuration producer directory separation");
        System.out.println("PASS 3 source/DTO checks; no canonical writer, policy authority, FrameSource, Game or SAVE qualification");
    }
    private static FileRef ref(Path root,String relative,long bytes,String sha){return new FileRef(root.resolve(relative).toString(),bytes,sha);}
    private static byte[] small(FileRef source,int maximum)throws IOException {
        if(source.bytes()>maximum)throw new IOException("bounded small original required");
        source.verify();byte[] raw;
        try(var input=Files.newInputStream(Path.of(source.path()))){raw=input.readNBytes(maximum+1);}
        if(raw.length!=source.bytes())throw new IOException("small original size drift");source.verify();return raw;
    }
    private static void check(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}
