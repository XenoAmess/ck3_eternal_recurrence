package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact original preparation/profile custody; neither a Start ACK nor a gameplay admission. */
public final class PreparedFixture {
    public enum EpisodeProjection { NATIVE_CAMPAIGN }
    /** Complete reviewed file DATA; it does not assert XAR absence or grant a one-life bypass. */
    public record MountedInventory(ExactRef policySource,List<ExactRef> immutableInputs,Set<String> mountedRelativePaths) {
        public MountedInventory {java.util.Objects.requireNonNull(policySource);immutableInputs=List.copyOf(immutableInputs);mountedRelativePaths=Set.copyOf(mountedRelativePaths);}
    }
    private final ExactRef policySource;
    private final FrontendFixturePolicy policy;
    private final Path stateDir,profileDirectory;
    private final RawJson originalPolicy;
    private final List<SharedSourceFiles.Witness> inputs;
    private final Set<String> mountedInputs;
    private PreparedFixture(ExactRef source,FrontendFixturePolicy policy,Path stateDir,Path profileDirectory,
            byte[] raw,List<SharedSourceFiles.Witness> inputs,Set<String> mounted) {
        policySource=source;this.policy=policy;this.stateDir=stateDir;this.profileDirectory=profileDirectory;
        originalPolicy=new RawJson(raw);this.inputs=List.copyOf(inputs);mountedInputs=Set.copyOf(mounted);
    }
    public ExactRef policySource() { return policySource; }
    public FrontendFixturePolicy policy() { return policy; }
    public FrontendFixturePolicy.Binding binding() { return policy.binding(policySource.sha256()); }
    public Path stateDir() { return stateDir; }
    public Path profileDirectory() { return profileDirectory; }
    public RawJson originalPolicy() { return originalPolicy; }
    public EpisodeProjection episodeProjection(){return EpisodeProjection.NATIVE_CAMPAIGN;}
    public MountedInventory mountedInventory(){return new MountedInventory(policySource,inputClosure(),mountedInputs);}
    public List<ExactRef> inputClosure() {
        return inputs.stream().map(w->new ExactRef(w.source().path(),w.source().bytes(),w.source().sha256())).toList();
    }
    /** Same private fixture and the sole explicit ENV producer must describe exactly the same originals. */
    public void requireEnvironment(org.xar.ck3.control.build.NativeRunProfileManifest.ProfileEnvironment original)throws IOException {
        verifySources();
        if(!(original instanceof org.xar.ck3.control.build.NativeRunProfileManifest.ExplicitManifest environment)
                ||environment.kind()!=org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.FRESH_FRONTEND_FIXTURE
                ||!(environment.profile() instanceof org.xar.ck3.control.build.NativeRunProfileManifest.FreshFixtureProfile profile))
            throw new IOException("Explicit fresh frontend fixture ENV required");
        var inventory=mountedInventory();
        var expected=inventory.immutableInputs().stream().map(PreparedFixture::file).toList();
        if(!profile.policySource().equals(file(inventory.policySource()))||!profile.immutableInputs().equals(expected)
                ||!new TreeSet<>(profile.mountedRelativePaths()).equals(new TreeSet<>(inventory.mountedRelativePaths()))
                ||!Path.of(environment.stateDir()).toRealPath().equals(stateDir)
                ||!Path.of(environment.profileDir()).toRealPath().equals(profileDirectory))
            throw new IOException("Actual explicit ENV differs from the same prepared fixture input closure");
        verifySources();
    }
    public static PreparedFixture prepare(ExactRef source,Path stateDir,Path profileDirectory,String episodeProjection)throws IOException {
        StrictJson.require("native_campaign".equals(episodeProjection),"fixture preparation requires explicit native_campaign");
        StrictJson.require(stateDir.isAbsolute()&&profileDirectory.isAbsolute()&&stateDir.normalize().equals(stateDir)
                &&profileDirectory.normalize().equals(profileDirectory),"exact absolute fixture paths required");
        ProjectStoragePolicy.requireBulkOutput(stateDir);ProjectStoragePolicy.requireBulkOutput(profileDirectory);
        Path state=stateDir.toRealPath(),profile=profileDirectory.toRealPath();
        StrictJson.require(profile.equals(state.resolve("profile").toRealPath()),"fixture profile must be actual bound stateDir/profile");
        StrictJson.require(source.bytes()>0&&source.bytes()<=1<<20,"bounded exact fixture policy required");file(source).verify();
        List<SharedSourceFiles.Witness> held=new ArrayList<>();
        var policyWitness=SharedSourceFiles.observe(Path.of(source.path()));held.add(policyWitness);
        byte[] raw=read(Path.of(source.path()),1<<20);
        StrictJson.require(raw.length==source.bytes()&&sha(raw).equals(source.sha256()),"fixture policy changed during exact read");
        byte[] json=raw.length>=3&&(raw[0]&255)==239&&(raw[1]&255)==187&&(raw[2]&255)==191?Arrays.copyOfRange(raw,3,raw.length):raw;
        var policy=FrontendFixturePolicy.fromJson(StrictJson.parse(json,1<<20));
        Path preparation=Path.of(policy.preparation().path());
        var preparationWitness=SharedSourceFiles.observe(preparation);held.add(preparationWitness);
        StrictJson.require(preparationWitness.source().sha256().equals(policy.preparation().sha256()),"original fixture preparation bytes changed");
        for(var entry:new java.util.TreeMap<>(policy.profileInputSha256()).entrySet()) {
            Path input=profile.resolve(entry.getKey()).toRealPath();
            StrictJson.require(input.startsWith(profile)&&Files.isRegularFile(input,LinkOption.NOFOLLOW_LINKS),"fixture input escapes actual profile");
            var witness=SharedSourceFiles.observe(input);
            StrictJson.require(witness.source().sha256().equals(entry.getValue()),"fixture profile input changed: "+entry.getKey());held.add(witness);
        }
        Set<String> mounted=mounted(profile);
        Set<String> declared=new TreeSet<>();
        for(String key:policy.profileInputSha256().keySet())if(key.startsWith("mod/")||key.startsWith("mod-content/"))declared.add(key);
        StrictJson.require(!mounted.isEmpty()&&mounted.equals(declared),"fixture mounted input inventory changed");
        byte[] dlcRaw=read(profile.resolve("dlc_load.json"),1<<20);
        if(dlcRaw.length>=3&&(dlcRaw[0]&255)==239&&(dlcRaw[1]&255)==187&&(dlcRaw[2]&255)==191)dlcRaw=Arrays.copyOfRange(dlcRaw,3,dlcRaw.length);
        var dlc=StrictJson.parse(dlcRaw,1<<20);var enabled=dlc.get("enabled_mods");
        StrictJson.require(enabled!=null&&enabled.isArray()&&!enabled.isEmpty(),"fixture enabled mod descriptors required");
        for(var mod:enabled)StrictJson.require(declared.contains(StrictJson.text(mod)),"enabled descriptor is not a bound mounted input");
        PreparedFixture result=new PreparedFixture(source,policy,state,profile,raw,held,mounted);
        result.verifyFreshPreparation();return result;
    }
    /** Revalidate immutable external inputs after Start without requiring logs to become empty again. */
    public void verifySources()throws IOException {
        ProjectStoragePolicy.requireBulkOutput(stateDir);ProjectStoragePolicy.requireBulkOutput(profileDirectory);
        for(var input:inputs)SharedSourceFiles.assertUnchanged(input);
        file(policySource).verify();
        StrictJson.require(mounted(profileDirectory).equals(mountedInputs),"actual mounted fixture inventory drifted");
    }
    /** Recheck the original preparation, never demand empty logs after the actual Game has reached its menu. */
    public void verifyBeforeClaim()throws IOException {
        verifySources();StrictJson.require(!Files.exists(stateDir.resolve("frontend-fixture-start-requests.jsonl")),"fixture Start was already exclusively claimed");
    }
    /** Fresh empty logs belong to the one pre-Game preparation, not a later Start or continuation. */
    private void verifyFreshPreparation()throws IOException {
        verifySources();Path logs=profileDirectory.resolve("logs");
        if(Files.exists(logs))try(var paths=Files.walk(logs)) {
            for(Path p:paths.filter(Files::isRegularFile).toList())StrictJson.require(Files.size(p)==0,"fixture startup requires fresh empty profile logs");
        }
    }
    private static Set<String> mounted(Path profile)throws IOException {
        Set<String> result=new LinkedHashSet<>();
        for(String top:List.of("mod","mod-content")) {
            Path dir=profile.resolve(top);if(!Files.exists(dir))continue;
            try(var paths=Files.walk(dir)) {
                for(Path p:paths.filter(Files::isRegularFile).toList()) {
                    Path real=p.toRealPath();StrictJson.require(real.startsWith(profile),"mounted fixture input escapes actual profile");
                    result.add(profile.relativize(p).toString().replace('\\','/'));
                }
            }
        }
        return Set.copyOf(result);
    }
    private static byte[] read(Path path,int maximum)throws IOException {
        try(var input=Files.newInputStream(path)){byte[] raw=input.readNBytes(maximum+1);StrictJson.require(raw.length<=maximum,"fixture input exceeds bounded JSON budget");return raw;}
    }
    private static ControlBuild.FileRef file(ExactRef ref) { return new ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256()); }
    static String sha(byte[] raw) { try{return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));}catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);} }
}

