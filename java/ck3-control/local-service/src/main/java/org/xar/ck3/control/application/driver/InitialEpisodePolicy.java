package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Set;
import java.math.BigInteger;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.continuity.ContinuityJson;

/** Explicit lifecycle business data; source-bound imports retain their actual original environment qualification. */
public final class InitialEpisodePolicy {
    public static final String SCHEMA = "xar.java.initial-episode-policy/v1";
    public enum Lifecycle { ROGUE_ONE_LIFE, ORDINARY_CAMPAIGN_SUCCESSION, NATIVE_CAMPAIGN_FIXTURE, NATIVE_CAMPAIGN_SAVED }
    public enum FreshPact { ROGUE_REQUIRED, ORDINARY_NO_PACT }
    public static final String FIXTURE_SCHEMA="xar.java.initial-episode-fixture-projection/v1";
    private final java.util.Optional<org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture> fixture;
    private final java.util.Optional<org.xar.ck3.control.platform.NativeLaunchPlan> savedPlan;
    private final java.util.Optional<ExactRef> source;
    private final java.util.Optional<ExactRef> environment;
    private final RawJson lifecycle;
    private final Lifecycle kind;
    private InitialEpisodePolicy(ExactRef source, ExactRef environment, RawJson lifecycle, Lifecycle kind) {
        this(source,environment,lifecycle,kind,java.util.Optional.empty());
    }
    private InitialEpisodePolicy(ExactRef source,ExactRef environment,RawJson lifecycle,Lifecycle kind,
            java.util.Optional<org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture> fixture) {
        this(source,environment,lifecycle,kind,fixture,java.util.Optional.empty());
    }
    private InitialEpisodePolicy(ExactRef source,ExactRef environment,RawJson lifecycle,Lifecycle kind,
            java.util.Optional<org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture> fixture,
            java.util.Optional<org.xar.ck3.control.platform.NativeLaunchPlan> savedPlan) {
        this(java.util.Optional.of(source),java.util.Optional.of(environment),lifecycle,kind,fixture,savedPlan);
    }
    private InitialEpisodePolicy(java.util.Optional<ExactRef> source,java.util.Optional<ExactRef> environment,RawJson lifecycle,Lifecycle kind,
            java.util.Optional<org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture> fixture,
            java.util.Optional<org.xar.ck3.control.platform.NativeLaunchPlan> savedPlan) {
        Objects.requireNonNull(source);Objects.requireNonNull(environment);Objects.requireNonNull(lifecycle);Objects.requireNonNull(kind);Objects.requireNonNull(fixture);Objects.requireNonNull(savedPlan);
        this.source=source;this.environment=environment;this.lifecycle=lifecycle;this.kind=kind;this.fixture=fixture;this.savedPlan=savedPlan;
    }
    public ExactRef source() { return source.orElseThrow(() -> new IllegalStateException("source provenance absent")); }
    public ExactRef environment() { return environment.orElseThrow(() -> new IllegalStateException("environment provenance absent")); }
    public java.util.Optional<ExactRef> optionalSource() { return source; }
    public java.util.Optional<ExactRef> optionalEnvironment() { return environment; }
    public RawJson lifecycle() { return lifecycle; }
    public Lifecycle kind() { return kind; }
    public java.util.Optional<org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture> explicitFixture(){return fixture;}
    /** Null lifecycle provenance is not inferred from the complete mod inventory. */
    public void requireFixtureProjection(org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture identical)throws IOException {
        StrictJson.require(kind==Lifecycle.NATIVE_CAMPAIGN_FIXTURE&&fixture.orElseThrow()==identical,"fixture projection crossed the actual prepared producer");verify();
    }
    public java.util.List<ExactRef> evidenceClosure()throws IOException {
        verify();
        ExactRef source=source();
        ExactRef environment=environment();
        var refs=new java.util.LinkedHashSet<ExactRef>();refs.add(source);refs.add(environment);
        if(fixture.isPresent()){refs.addAll(fixture.orElseThrow().inputClosure());return java.util.List.copyOf(refs);}
        if(savedPlan.isPresent()){var load=(org.xar.ck3.control.platform.NativeLaunchPlan.SavedGame)savedPlan.orElseThrow().load();refs.add(new ExactRef(load.save().path(),load.save().bytes(),load.save().sha256()));return java.util.List.copyOf(refs);}
        ObjectNode manifest=environment(environment);
        if(kind==Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION && lifecycleBinding().get("xar_enabled").isNull()) {
            ObjectNode evidence=object(manifest.get("verified_mod_absence"),"verified_mod_absence");
            refs.add(ExactRef.fromJson(evidence.get("profile_enabled_mods")));refs.add(ExactRef.fromJson(evidence.get("startup_log_snapshot")));
        }
        return java.util.List.copyOf(refs);
    }
    public void verify() throws IOException {
        if (source.isEmpty() || environment.isEmpty()) throw new java.io.IOException("source or environment provenance absent");
        ExactRef source=source();
        ExactRef environment=environment();
        file(source).verify(); file(environment).verify();
        ObjectNode actual=environment(environment);
        if(savedPlan.isPresent()) {
            var plan=savedPlan.orElseThrow();
            StrictJson.require(plan.load() instanceof org.xar.ck3.control.platform.NativeLaunchPlan.SavedGame,"saved projection lost its exact Saved plan");
            var saved=(org.xar.ck3.control.platform.NativeLaunchPlan.SavedGame)plan.load();
            StrictJson.require(java.util.Arrays.equals(savedProjection(file(environment),saved.save(),EnvironmentRead.RETAINED_ORIGINAL).bytes(),Files.readAllBytes(Path.of(source.path()))),"actual Saved projection original changed");return;
        }
        if(fixture.isPresent()) {
            byte[] expected=fixtureProjection(file(environment),fixture.orElseThrow(),EnvironmentRead.RETAINED_ORIGINAL).bytes();
            StrictJson.require(java.util.Arrays.equals(expected,Files.readAllBytes(Path.of(source.path()))),"actual fixture projection original changed");return;
        }
        StrictJson.require(java.util.Arrays.equals(lifecycle.bytes(),StrictJson.canonical(binding(actual,kind))),"actual frozen lifecycle inputs changed");
    }
    public void verifyGame(GameGeneration actualGame)throws IOException {
        verify();
        ExactRef environment=environment();
        ObjectNode actual=environment(environment);
        if(kind==Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION && actual.get("verified_mod_absence") instanceof ObjectNode absence
                && lifecycleBinding().get("xar_enabled").isNull()) {
            long pid=StrictJson.integer(absence.get("game_pid"),1,0xffff_ffffL);
            PythonOnlyUInt64 birth=gameCreationFiletime(absence.get("game_creation_filetime"));
            StrictJson.require(actualGame.equals(new GameGeneration(pid,birth)),"reviewed mod absence belongs to another actual Game birth");
        }
    }
    private ObjectNode lifecycleBinding() { return ContinuityJson.parseObject(lifecycle.bytes(),65536); }

    /** Factory for ordinary business lifecycle without source/environment provenance. */
    public static InitialEpisodePolicy ordinary(Lifecycle kind, RawJson lifecycle) {
        Objects.requireNonNull(kind);
        Objects.requireNonNull(lifecycle);
        if (kind != Lifecycle.ROGUE_ONE_LIFE && kind != Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION) {
            throw new IllegalArgumentException("ordinary factory only supports ROGUE_ONE_LIFE or ORDINARY_CAMPAIGN_SUCCESSION");
        }
        ObjectNode binding = StrictJson.object(ContinuityJson.parseObject(lifecycle.bytes(), 65536), Set.of("schema", "lifecycle", "xar_enabled", "pact_contract", "source", "environment_sha256"));
        StrictJson.require("xar.ck3.succession-lifecycle-binding/v1".equals(StrictJson.text(binding.get("schema"))), "exact succession lifecycle schema required");
        String lifecycleStr = StrictJson.text(binding.get("lifecycle"));
        String expectedLifecycle = kind == Lifecycle.ROGUE_ONE_LIFE ? "rogue_one_life" : "ordinary_campaign_succession";
        StrictJson.require(lifecycleStr.equals(expectedLifecycle), "lifecycle string must match kind");
        
        // Validate types only, no semantic checks on source/environment_sha256 values
        var xarEnabled = binding.get("xar_enabled");
        StrictJson.require(xarEnabled.isTextual() || xarEnabled.isNull(), "xar_enabled must be textual or null");
        StrictJson.require(binding.get("pact_contract").isTextual(), "pact_contract must be textual");
        StrictJson.require(binding.get("source").isTextual(), "source must be textual");
        var environmentSha256 = binding.get("environment_sha256");
        StrictJson.require(environmentSha256.isTextual() || environmentSha256.isNull(), "environment_sha256 must be textual or null");

        return new InitialEpisodePolicy(java.util.Optional.empty(), java.util.Optional.empty(), lifecycle, kind, java.util.Optional.empty(), java.util.Optional.empty());
    }
    /** Pure business bytes; only the admitted Bootstrap writer may create the policy original. */
    public static RawJson produce(ControlBuild.FileRef actualPreparedEnvironment,Lifecycle lifecycle,FreshPact fresh)throws IOException {
        Objects.requireNonNull(actualPreparedEnvironment);Objects.requireNonNull(lifecycle);Objects.requireNonNull(fresh);
        StrictJson.require((lifecycle==Lifecycle.ROGUE_ONE_LIFE && fresh==FreshPact.ROGUE_REQUIRED)
                || (lifecycle==Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION && fresh==FreshPact.ORDINARY_NO_PACT),"explicit matching fresh lifecycle contract required");
        actualPreparedEnvironment.verify();
        var held=SharedSourceFiles.observe(Path.of(actualPreparedEnvironment.path()));
        ExactRef environment=new ExactRef(actualPreparedEnvironment.path(),actualPreparedEnvironment.bytes(),actualPreparedEnvironment.sha256());
        ObjectNode actual=environment(environment);
        if(org.xar.ck3.control.build.NativeRunProfileManifest.isCurrentVersion(actual))
            org.xar.ck3.control.build.NativeRunProfileProducer.readVerified(actualPreparedEnvironment);
        ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);row.set("environment_manifest",environment.toJson());
        row.set("succession_lifecycle",binding(actual,lifecycle));
        RawJson value=new RawJson(StrictJson.canonical(row));
        SharedSourceFiles.assertUnchanged(held);actualPreparedEnvironment.verify();
        return value;
    }
    /** Uses the same sole producer and does not accept an output path or filesystem write authority. */
    public static byte[] encode(ControlBuild.FileRef actualPreparedEnvironment,Lifecycle lifecycle,FreshPact fresh)throws IOException {
        return produce(actualPreparedEnvironment,lifecycle,fresh).bytes();
    }
    public static InitialEpisodePolicy readExact(ExactRef source, ControlBuild.FileRef actualPreparedEnvironment) throws IOException {
        Objects.requireNonNull(source); Objects.requireNonNull(actualPreparedEnvironment);
        sourceBound(source);
        StrictJson.require(actualPreparedEnvironment.bytes()>0 && actualPreparedEnvironment.bytes()<=1<<20,"bounded actual prepared environment required");
        actualPreparedEnvironment.verify();
        var held=SharedSourceFiles.observe(Path.of(source.path()));
        byte[] bytes=Files.readAllBytes(Path.of(source.path()));
        StrictJson.require(bytes.length==source.bytes(), "actual initial episode policy size changed");
        ObjectNode root=StrictJson.object(ContinuityJson.parseObject(bytes, 1<<20),Set.of("schema","environment_manifest","succession_lifecycle"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))),"exact initial episode policy schema required");
        ExactRef environment=ExactRef.fromJson(root.get("environment_manifest"));
        StrictJson.require(file(environment).equals(actualPreparedEnvironment),"initial episode environment differs from actual managed profile");
        ObjectNode binding=StrictJson.object(root.get("succession_lifecycle"),Set.of("schema","lifecycle","xar_enabled","pact_contract","source","environment_sha256"));
        StrictJson.require("xar.ck3.succession-lifecycle-binding/v1".equals(StrictJson.text(binding.get("schema"))),"exact source lifecycle schema required");
        String lifecycle=StrictJson.text(binding.get("lifecycle"));
        Lifecycle kind=switch(lifecycle) {
            case "rogue_one_life" -> Lifecycle.ROGUE_ONE_LIFE;
            case "ordinary_campaign_succession" -> Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION;
            default -> throw new IllegalArgumentException("unclassified lifecycle cannot create a new playable episode");
        };
        String origin=StrictJson.text(binding.get("source"));
        String pact=StrictJson.text(binding.get("pact_contract"));
        boolean normal=kind==Lifecycle.ROGUE_ONE_LIFE
                ? binding.get("xar_enabled").isTextual() && "xar_on".equals(binding.get("xar_enabled").textValue()) && "terminal_settlement_required".equals(pact)
                : binding.get("xar_enabled").isTextual() && "xar_off".equals(binding.get("xar_enabled").textValue()) && "absent_by_fresh_campaign_xar_off_contract".equals(pact);
        boolean verifiedAbsence=kind==Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION && binding.get("xar_enabled").isNull()
                && "absent_by_verified_xar_mod_not_loaded".equals(pact) && origin.equals(pact);
        StrictJson.require(normal || verifiedAbsence,"frozen lifecycle support profile is inconsistent");
        ObjectNode actual=ContinuityJson.parseObject(Files.readAllBytes(Path.of(environment.path())),1<<20);
        var environmentDigest=binding.get("environment_sha256");
        StrictJson.require(environmentDigest!=null && environmentDigest.isTextual() && environmentDigest.textValue().matches("[0-9a-f]{64}")
                && environmentDigest.equals(actual.get("environment_sha256")),"new lifecycle must bind the actual prepared environment digest");
        StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(binding),StrictJson.canonical(binding(actual,kind))),
                "policy is not the exact actual frozen environment producer output");
        SharedSourceFiles.assertUnchanged(held); sourceBound(source); actualPreparedEnvironment.verify();
        return new InitialEpisodePolicy(source,environment,new RawJson(StrictJson.canonical(binding)),kind);
    }
    public static final String SAVED_SCHEMA="xar.java.initial-episode-saved-native-projection/v1";
    /** Explicit Saved projection is source data; the physical reader binds the original Saved plan. */
    public static RawJson produceSaved(ControlBuild.FileRef actualEnvironment,ControlBuild.FileRef actualSave)throws IOException {
        return savedProjection(actualEnvironment,actualSave,EnvironmentRead.PRELAUNCH_PHYSICAL);
    }
    private static RawJson savedProjection(ControlBuild.FileRef actualEnvironment,ControlBuild.FileRef actualSave,EnvironmentRead phase)throws IOException {
        Objects.requireNonNull(actualEnvironment);Objects.requireNonNull(actualSave);actualEnvironment.verify();actualSave.verify();
        StrictJson.require(Path.of(actualSave.path()).isAbsolute()&&actualSave.path().endsWith(".ck3"),"exact original Saved .ck3 required");
        var envHeld=SharedSourceFiles.observe(Path.of(actualEnvironment.path()));var saveHeld=SharedSourceFiles.observe(Path.of(actualSave.path()));
        var env=new ExactRef(actualEnvironment.path(),actualEnvironment.bytes(),actualEnvironment.sha256());
        ObjectNode manifest=environment(env);
        if(org.xar.ck3.control.build.NativeRunProfileManifest.isCurrentVersion(manifest))
            requireSavedProfileDomain(currentEnvironment(actualEnvironment,phase));
        Path state=Path.of(StrictJson.text(manifest.get("state_dir"))),profile=Path.of(StrictJson.text(manifest.get("profile_dir")));
        StrictJson.require(state.isAbsolute()&&profile.isAbsolute()&&Path.of(actualSave.path()).toRealPath().getParent().equals(profile.resolve("save games").toRealPath()),"Saved projection must name the exact prepared profile SAVE");
        ObjectNode row=StrictJson.object();row.put("schema",SAVED_SCHEMA);row.set("environment_manifest",env.toJson());
        row.put("episode_projection","native_campaign");row.putNull("succession_lifecycle");
        row.set("saved_game",new ExactRef(actualSave.path(),actualSave.bytes(),actualSave.sha256()).toJson());
        RawJson result=new RawJson(StrictJson.canonical(row,1<<20));
        SharedSourceFiles.assertUnchanged(envHeld);SharedSourceFiles.assertUnchanged(saveHeld);actualEnvironment.verify();actualSave.verify();return result;
    }
    public static InitialEpisodePolicy readExactSaved(ExactRef source,org.xar.ck3.control.platform.NativeLaunchPlan samePlan)throws IOException {
        Objects.requireNonNull(samePlan);sourceBound(source);
        StrictJson.require(samePlan.load() instanceof org.xar.ck3.control.platform.NativeLaunchPlan.SavedGame,"explicit Saved plan required for native_campaign");
        var saved=(org.xar.ck3.control.platform.NativeLaunchPlan.SavedGame)samePlan.load();var env=samePlan.preparedProfile().environmentManifest();
        var held=SharedSourceFiles.observe(Path.of(source.path()));byte[] bytes=Files.readAllBytes(Path.of(source.path()));
        ObjectNode row=StrictJson.object(ContinuityJson.parseObject(bytes,1<<20),Set.of("schema","environment_manifest","episode_projection","succession_lifecycle","saved_game"));
        StrictJson.require(SAVED_SCHEMA.equals(StrictJson.text(row.get("schema")))&&row.get("succession_lifecycle").isNull(),"strict Saved native projection/null provenance required");
        StrictJson.require(java.util.Arrays.equals(bytes,savedProjection(env,saved.save(),EnvironmentRead.RETAINED_ORIGINAL).bytes()),"Saved projection differs from its sole actual producer");
        SharedSourceFiles.assertUnchanged(held);sourceBound(source);
        var policy=new InitialEpisodePolicy(source,new ExactRef(env.path(),env.bytes(),env.sha256()),new RawJson(new byte[]{'n','u','l','l'}),Lifecycle.NATIVE_CAMPAIGN_SAVED,java.util.Optional.empty(),java.util.Optional.of(samePlan));
        policy.requireSavedProjection(samePlan);return policy;
    }
    public void requireSavedProjection(org.xar.ck3.control.platform.NativeLaunchPlan identical)throws IOException {
        StrictJson.require(kind==Lifecycle.NATIVE_CAMPAIGN_SAVED&&savedPlan.orElseThrow()==identical&&fixture.isEmpty(),"Saved native projection crossed the original plan");verify();
    }
    /** Explicit native_campaign preserves the original null lifecycle. This makes no XAR-rule or pact claim. */
    public static RawJson produceFixture(ControlBuild.FileRef actualEnvironment,
            org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture same)throws IOException {
        return fixtureProjection(actualEnvironment,same,EnvironmentRead.PRELAUNCH_PHYSICAL);
    }
    private static RawJson fixtureProjection(ControlBuild.FileRef actualEnvironment,
            org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture same,EnvironmentRead phase)throws IOException {
        Objects.requireNonNull(actualEnvironment);Objects.requireNonNull(same);actualEnvironment.verify();same.verifySources();
        var held=SharedSourceFiles.observe(Path.of(actualEnvironment.path()));
        ExactRef environment=new ExactRef(actualEnvironment.path(),actualEnvironment.bytes(),actualEnvironment.sha256());
        ObjectNode manifest=environment(environment);
        if(org.xar.ck3.control.build.NativeRunProfileManifest.isCurrentVersion(manifest))
            requireFixtureProfileDomain(currentEnvironment(actualEnvironment,phase),same);
        fixtureEnvironment(manifest,same);
        ObjectNode row=StrictJson.object();row.put("schema",FIXTURE_SCHEMA);row.set("environment_manifest",environment.toJson());
        row.put("episode_projection","native_campaign");row.putNull("succession_lifecycle");row.set("fixture_policy",same.policySource().toJson());
        var inputs=row.putArray("input_closure");for(ExactRef ref:same.inputClosure())inputs.add(ref.toJson());
        var mounted=row.putArray("mounted_relative_paths");for(String path:new java.util.TreeSet<>(same.mountedInventory().mountedRelativePaths()))mounted.add(path);
        RawJson original=new RawJson(StrictJson.canonical(row,1<<20));
        SharedSourceFiles.assertUnchanged(held);actualEnvironment.verify();same.verifySources();return original;
    }
    public static InitialEpisodePolicy readExactFixture(ExactRef source,ControlBuild.FileRef actualEnvironment,
            org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture same)throws IOException {
        Objects.requireNonNull(source);Objects.requireNonNull(actualEnvironment);Objects.requireNonNull(same);sourceBound(source);
        var held=SharedSourceFiles.observe(Path.of(source.path()));byte[] actual=Files.readAllBytes(Path.of(source.path()));
        ObjectNode value=StrictJson.object(ContinuityJson.parseObject(actual,1<<20),Set.of("schema","environment_manifest","episode_projection","succession_lifecycle","fixture_policy","input_closure","mounted_relative_paths"));
        StrictJson.require(FIXTURE_SCHEMA.equals(StrictJson.text(value.get("schema")))&&value.get("succession_lifecycle").isNull()
                &&"native_campaign".equals(StrictJson.text(value.get("episode_projection"))),"explicit fixture projection with null lifecycle provenance required");
        StrictJson.require(java.util.Arrays.equals(actual,fixtureProjection(actualEnvironment,same,EnvironmentRead.RETAINED_ORIGINAL).bytes()),"fixture projection is not the sole source-bound producer output");
        SharedSourceFiles.assertUnchanged(held);sourceBound(source);
        return new InitialEpisodePolicy(source,new ExactRef(actualEnvironment.path(),actualEnvironment.bytes(),actualEnvironment.sha256()),
                new RawJson(new byte[]{'n','u','l','l'}),Lifecycle.NATIVE_CAMPAIGN_FIXTURE,java.util.Optional.of(same));
    }
    private static void fixtureEnvironment(ObjectNode manifest,
            org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture same)throws IOException {
        StrictJson.require(same.episodeProjection()==org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture.EpisodeProjection.NATIVE_CAMPAIGN,
                "fixture projection must come from the actual preparation");
        StrictJson.require(Path.of(StrictJson.text(manifest.get("state_dir"))).toRealPath().equals(same.stateDir())
                &&Path.of(StrictJson.text(manifest.get("profile_dir"))).toRealPath().equals(same.profileDirectory()),"fixture projection crossed the actual profile/state");
        ObjectNode load;
        if(org.xar.ck3.control.build.NativeRunProfileManifest.isCurrentVersion(manifest)) {
            var typed=org.xar.ck3.control.build.NativeRunProfileManifest.decodeEnvironment(StrictJson.canonical(manifest,1<<20));
            requireFixtureProfileDomain(typed,same);
            var actual=(org.xar.ck3.control.build.NativeRunProfileManifest.FreshFixtureProfile)
                    ((org.xar.ck3.control.build.NativeRunProfileManifest.ExplicitManifest)typed).profile();
            load=StrictJson.object();var ordered=load.putArray("enabled_mods");actual.loadProfile().enabledMods().forEach(ordered::add);
            load.put("dlc_load_sha256",actual.loadProfile().dlcLoad().sha256());
        } else load=object(manifest.get("load_profile"),"load_profile");
        var enabled=load.get("enabled_mods");
        StrictJson.require(enabled!=null&&enabled.isArray()&&!enabled.isEmpty(),"actual nonempty fixture load profile required");
        ExactRef mods=null;
        Path expected=same.profileDirectory().resolve("dlc_load.json").toRealPath();
        for(ExactRef ref:same.inputClosure())if(Path.of(ref.path()).toRealPath().equals(expected))mods=ref;
        if(mods==null)throw new IOException("actual fixture mod list missing from retained inventory");
        StrictJson.require(mods.sha256().equals(StrictJson.text(load.get("dlc_load_sha256"))),"fixture environment differs from the retained mod list");
        byte[] raw=Files.readAllBytes(Path.of(mods.path()));if(raw.length>=3&&(raw[0]&255)==239&&(raw[1]&255)==187&&(raw[2]&255)==191)raw=java.util.Arrays.copyOfRange(raw,3,raw.length);
        StrictJson.require(enabled.equals(ContinuityJson.parseObject(raw,1<<20).get("enabled_mods")),"fixture environment changed actual enabled mod descriptors");
        for(var descriptor:enabled)StrictJson.require(same.mountedInventory().mountedRelativePaths().contains(StrictJson.text(descriptor)),"fixture environment names an unretained mounted descriptor");
        same.verifySources();
    }
    private enum EnvironmentRead { PRELAUNCH_PHYSICAL,RETAINED_ORIGINAL }
    private static org.xar.ck3.control.build.NativeRunProfileManifest.ProfileEnvironment currentEnvironment(
            ControlBuild.FileRef original,EnvironmentRead phase)throws IOException {
        return phase==EnvironmentRead.PRELAUNCH_PHYSICAL
                ?org.xar.ck3.control.build.NativeRunProfileProducer.readEnvironmentVerified(original)
                :org.xar.ck3.control.build.NativeRunProfileManifest.readEnvironmentOriginal(original);
    }
    /** Domain validation only. Decoded ENV data cannot issue a launch, policy, PreparedFixture or Game authority. */
    public static void requireSavedProfileDomain(org.xar.ck3.control.build.NativeRunProfileManifest.ProfileEnvironment actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(actual.kind()==org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.SAVED_VANILLA
                ||actual.kind()==org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.SAVED_PRODUCT_ONLY,
                "Saved native projection requires its explicit Saved environment domain");
    }
    /** Delegates exact fixture ENV binding to its sole private PreparedFixture producer. */
    public static void requireFixtureProfileDomain(org.xar.ck3.control.build.NativeRunProfileManifest.ProfileEnvironment actual,
            org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture same)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(same);same.requireEnvironment(actual);
    }
    private static void sourceBound(ExactRef source) throws IOException {
        StrictJson.require(source.bytes()>0 && source.bytes()<=1<<20,"bounded actual initial policy required"); file(source).verify();
    }
    private static ControlBuild.FileRef file(ExactRef ref) { return new ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256()); }
    private static ObjectNode environment(ExactRef source)throws IOException {
        sourceBound(source);var witness=SharedSourceFiles.observe(Path.of(source.path()));byte[] bytes;
        try(var input=Files.newInputStream(Path.of(source.path()))){bytes=input.readNBytes((1<<20)+1);}
        StrictJson.require(bytes.length==source.bytes()&&org.xar.ck3.control.build.NativeRunProfileRules.sha(bytes).equals(source.sha256()),
                "actual profile environment changed during bounded read");
        ObjectNode value=ContinuityJson.parseObject(bytes,1<<20);
        SharedSourceFiles.assertUnchanged(witness);
        org.xar.ck3.control.build.NativeRunProfileManifest.requireSupported(value);
        if(org.xar.ck3.control.build.NativeRunProfileManifest.isCurrentVersion(value))
            return org.xar.ck3.control.build.NativeRunProfileManifest.environmentJson(
                    org.xar.ck3.control.build.NativeRunProfileManifest.readEnvironmentOriginal(file(source)));
        return value;
    }
    private static ObjectNode binding(ObjectNode manifest,Lifecycle kind)throws IOException {
        String digest=StrictJson.text(manifest.get("environment_sha256"));
        StrictJson.require(digest.matches("[0-9a-f]{64}"),"actual frozen environment digest required");
        ObjectNode rules=object(manifest.get("rules"),"rules");var profile=rules.get("profile");
        StrictJson.require(profile!=null && profile.isArray(),"actual frozen game-rule profile required");
        java.util.List<String> settings=new java.util.ArrayList<>();
        for(var row:profile)if(row instanceof ObjectNode item && item.get("rule")!=null && item.get("rule").isTextual()
                && "xar_enabled".equals(item.get("rule").textValue()))settings.add(StrictJson.text(item.get("setting")));
        ObjectNode result=StrictJson.object();result.put("schema","xar.ck3.succession-lifecycle-binding/v1");
        result.put("lifecycle",kind==Lifecycle.ROGUE_ONE_LIFE?"rogue_one_life":"ordinary_campaign_succession");
        if(settings.isEmpty() && kind==Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION) {
            verifyAbsence(manifest);result.putNull("xar_enabled");result.put("pact_contract","absent_by_verified_xar_mod_not_loaded");
            result.put("source","absent_by_verified_xar_mod_not_loaded");
        } else {
            StrictJson.require(settings.size()==1 && (settings.getFirst().equals("xar_on") || settings.getFirst().equals("xar_off")),"one frozen xar_enabled rule required");
            String expected=kind==Lifecycle.ROGUE_ONE_LIFE?"xar_on":"xar_off";
            StrictJson.require(settings.getFirst().equals(expected),"actual frozen rule conflicts with selected lifecycle");
            result.put("xar_enabled",expected);result.put("pact_contract",kind==Lifecycle.ROGUE_ONE_LIFE?"terminal_settlement_required":"absent_by_fresh_campaign_xar_off_contract");
            result.put("source","prepared-environment-manifest");
        }
        result.put("environment_sha256",digest);return result;
    }
    /** FILETIME crosses JSON as one decimal string; legacy numeric originals must be regenerated. */
    private static PythonOnlyUInt64 gameCreationFiletime(com.fasterxml.jackson.databind.JsonNode value) {
        String raw=StrictJson.text(value);
        StrictJson.require(raw.matches("[1-9][0-9]{0,19}"),"canonical positive uint64 FILETIME decimal string required");
        return new PythonOnlyUInt64(new BigInteger(raw));
    }
    private static void verifyAbsence(ObjectNode manifest)throws IOException {
        ObjectNode load=object(manifest.get("load_profile"),"load_profile");ObjectNode evidence=object(manifest.get("verified_mod_absence"),"verified_mod_absence");
        StrictJson.require(empty(load.get("enabled_mods")) && empty(evidence.get("enabled_mods")) && empty(evidence.get("loaded_mods"))
                && "xar.verified-xar-mod-absence/v1".equals(StrictJson.text(evidence.get("schema")))
                && "ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED".equals(StrictJson.text(evidence.get("status")))
                && "/root".equals(StrictJson.text(evidence.get("reviewer")))
                && isTrue(evidence.get("enabled_mods_known")) && isTrue(evidence.get("loaded_mods_known")) && isTrue(evidence.get("startup_log_reviewed"))
                && manifest.get("environment_sha256").equals(evidence.get("environment_sha256")),"actual known-empty profile/startup review required");
        StrictJson.integer(evidence.get("game_pid"),1,0xffff_ffffL);gameCreationFiletime(evidence.get("game_creation_filetime"));
        Path profile=Path.of(StrictJson.text(manifest.get("profile_dir"))).toRealPath();
        StrictJson.require(profile.equals(Path.of(StrictJson.text(evidence.get("profile_dir"))).toRealPath()),"absence evidence crossed actual profile");
        ExactRef mods=ExactRef.fromJson(evidence.get("profile_enabled_mods"));StrictJson.require(mods.bytes()>0 && mods.bytes()<=65536,"bounded actual mod list required");file(mods).verify();
        StrictJson.require(Path.of(mods.path()).toRealPath().equals(profile.resolve("dlc_load.json").toRealPath())
                && mods.sha256().equals(StrictJson.text(load.get("dlc_load_sha256")))
                && empty(ContinuityJson.parseObject(Files.readAllBytes(Path.of(mods.path())),65536).get("enabled_mods")),"actual isolated profile mod list is not known empty");
        ExactRef log=ExactRef.fromJson(evidence.get("startup_log_snapshot"));StrictJson.require(log.bytes()>0 && log.bytes()<=262144,"bounded reviewed startup log required");file(log).verify();
        Path source=Path.of(StrictJson.text(evidence.get("startup_log_original_path"))).toAbsolutePath().normalize();
        StrictJson.require(source.startsWith(profile.resolve("logs")),"original reviewed startup log is outside actual profile");
        file(mods).verify();file(log).verify();
    }
    private static boolean empty(com.fasterxml.jackson.databind.JsonNode value) { return value!=null && value.isArray() && value.isEmpty(); }
    private static boolean isTrue(com.fasterxml.jackson.databind.JsonNode value) { return value!=null && value.isBoolean() && value.booleanValue(); }
    private static ObjectNode object(com.fasterxml.jackson.databind.JsonNode value,String field) {
        StrictJson.require(value instanceof ObjectNode,"actual object required: "+field);return (ObjectNode)value;
    }
}
