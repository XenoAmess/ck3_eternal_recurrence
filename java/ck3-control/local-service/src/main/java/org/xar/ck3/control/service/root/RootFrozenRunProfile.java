package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FixtureStartupCase;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Actual run request plus the identical retained launch plan's environment. No DTO can issue a FrozenRunProfile. */
public final class RootFrozenRunProfile {
    public static final String SCHEMA="xar.java-original-driver-import-run-profile/v4";
    public static final int MAXIMUM_REQUEST_BYTES=65536;
    private static final Set<String> FIELDS=Set.of("schema","machine_id","observed_at_utc","review_at_utc","request_id",
            "session_id","environment_manifest","lifecycle","ordinary_campaign_no_pact","legacy_import");
    private RootFrozenRunProfile(){ }
    public enum LifecycleMode {
        ROGUE_ONE_LIFE("rogue_one_life"),ORDINARY_CAMPAIGN_SUCCESSION("ordinary_campaign_succession"),NATIVE_CAMPAIGN("native_campaign");
        private final String wire;LifecycleMode(String wire){this.wire=wire;}public String wire(){return wire;}
        static LifecycleMode decode(String wire){for(var value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("explicit production lifecycle required");}
    }
    public sealed interface ImportMode permits DisabledFreshRobert,DisabledFreshFixture,Enabled,EnabledNativeCampaign { }
    public record DisabledFreshRobert() implements ImportMode { }
    /** Explicit external fixture input. This data record cannot issue a prepared fixture or Game authority. */
    public record DisabledFreshFixture(ExactRef policySource,Optional<ExactRef> startupCaseSource) implements ImportMode {
        public DisabledFreshFixture(ExactRef policySource){this(policySource,Optional.empty());}
        public DisabledFreshFixture {Objects.requireNonNull(policySource);Objects.requireNonNull(startupCaseSource);absolute(Path.of(policySource.path()));
            require(policySource.bytes()>0&&policySource.bytes()<=1048576,"bounded exact fixture policy required");
            startupCaseSource.ifPresent(ref->{absolute(Path.of(ref.path()));require(ref.bytes()>0&&ref.bytes()<=1048576,"bounded exact external startup case contract required");});}
    }
    public record Enabled(Path stateDirectory) implements ImportMode {
        public Enabled {absolute(stateDirectory);}
    }
    /** Explicit Saved server projection; never an alias of a fresh fixture. */
    public record EnabledNativeCampaign(Path stateDirectory) implements ImportMode {
        public EnabledNativeCampaign {absolute(stateDirectory);}
    }
    /** This strict request is configuration data; readExact alone binds its original files and current plan. */
    public record Request(String machineId,Instant observedAt,Instant reviewAt,String requestId,String sessionId,
            ExactRef environmentManifest,LifecycleMode lifecycle,boolean ordinaryCampaignNoPact,ImportMode legacyImport) {
        public Request {
            Objects.requireNonNull(machineId);Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);
            Objects.requireNonNull(requestId);Objects.requireNonNull(sessionId);Objects.requireNonNull(environmentManifest);
            Objects.requireNonNull(lifecycle);Objects.requireNonNull(legacyImport);
            require((legacyImport instanceof DisabledFreshFixture||legacyImport instanceof EnabledNativeCampaign)==(lifecycle==LifecycleMode.NATIVE_CAMPAIGN),"only an explicit fresh fixture or Saved native mode selects native_campaign projection");
            if(lifecycle==LifecycleMode.NATIVE_CAMPAIGN)require(!ordinaryCampaignNoPact,"fixture projection cannot assert ordinary pact provenance");
            require(machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),"actual configured machine required");
            require(observedAt.isBefore(reviewAt)&&Duration.between(observedAt,reviewAt).compareTo(Duration.ofDays(7))<=0,"finite profile review required");
            require(requestId.matches("[A-Za-z0-9_-]{1,128}")&&sessionId.matches("[A-Za-z0-9_-]{1,128}"),"exact run request/session required");
            absolute(Path.of(environmentManifest.path()));require(environmentManifest.bytes()>0&&environmentManifest.bytes()<=1048576,"bounded actual environment manifest required");
        }
    }
    public static Request decode(byte[] raw) {
        ObjectValue value=object(OriginalDriverJournal.parse(raw,MAXIMUM_REQUEST_BYTES),"run profile request object required");exact(value,FIELDS);
        require(text(value.get("schema")).equals(SCHEMA),"run profile schema changed");
        Value noPact=value.get("ordinary_campaign_no_pact");require(noPact instanceof BooleanValue,"ordinary no-pact must be an explicit JSON boolean");
        ObjectValue input=object(value.get("legacy_import"),"explicit legacy import mode required");
        String kind=text(input.get("kind"));ImportMode mode;
        if(kind.equals("DISABLED_FRESH_ROBERT")){exact(input,Set.of("kind"));mode=new DisabledFreshRobert();}
        else if(kind.equals("DISABLED_FRESH_FIXTURE")){exact(input,Set.of("kind","policy_source","startup_case_source"));mode=new DisabledFreshFixture(reference(input.get("policy_source")),input.get("startup_case_source") instanceof NullValue?Optional.empty():Optional.of(reference(input.get("startup_case_source"))));}
        else if(kind.equals("ENABLED_NATIVE_CAMPAIGN")){exact(input,Set.of("kind","state_directory"));mode=new EnabledNativeCampaign(Path.of(text(input.get("state_directory"))));}
        else if(kind.equals("ENABLED")){exact(input,Set.of("kind","state_directory"));mode=new Enabled(Path.of(text(input.get("state_directory"))));}
        else throw new IllegalArgumentException("unknown legacy import mode");
        return new Request(text(value.get("machine_id")),instant(value.get("observed_at_utc")),instant(value.get("review_at_utc")),
                text(value.get("request_id")),text(value.get("session_id")),reference(value.get("environment_manifest")),
                LifecycleMode.decode(text(value.get("lifecycle"))),((BooleanValue)noPact).value(),mode);
    }
    public static byte[] encode(Request explicit) {
        Objects.requireNonNull(explicit);var value=new LinkedHashMap<String,Value>();
        value.put("schema",new StringValue(SCHEMA));value.put("machine_id",new StringValue(explicit.machineId()));
        value.put("observed_at_utc",new StringValue(explicit.observedAt().toString()));value.put("review_at_utc",new StringValue(explicit.reviewAt().toString()));
        value.put("request_id",new StringValue(explicit.requestId()));value.put("session_id",new StringValue(explicit.sessionId()));
        value.put("environment_manifest",reference(explicit.environmentManifest()));value.put("lifecycle",new StringValue(explicit.lifecycle().wire()));
        value.put("ordinary_campaign_no_pact",new BooleanValue(explicit.ordinaryCampaignNoPact()));
        var input=new LinkedHashMap<String,Value>();
        switch(explicit.legacyImport()) {
            case DisabledFreshRobert ignored->input.put("kind",new StringValue("DISABLED_FRESH_ROBERT"));
            case DisabledFreshFixture fixture->{input.put("kind",new StringValue("DISABLED_FRESH_FIXTURE"));input.put("policy_source",reference(fixture.policySource()));input.put("startup_case_source",fixture.startupCaseSource().<Value>map(RootFrozenRunProfile::reference).orElse(RetainedJson.NULL));}
            case EnabledNativeCampaign enabled->{input.put("kind",new StringValue("ENABLED_NATIVE_CAMPAIGN"));input.put("state_directory",new StringValue(enabled.stateDirectory().toString()));}
            case Enabled enabled->{input.put("kind",new StringValue("ENABLED"));input.put("state_directory",new StringValue(enabled.stateDirectory().toString()));}
        }
        value.put("legacy_import",new ObjectValue(input));return OriginalDriverJournal.canonical(new ObjectValue(value),MAXIMUM_REQUEST_BYTES).bytes();
    }
    public static final class FrozenRunProfile {
        private final NativeLaunchPlan plan;private final Request request;private final ExactRef requestRef;
        private final Optional<SuccessionLifecycleBinding> binding;private final InitialEpisodePolicy initialPolicy;private final List<SharedSourceFiles.Witness> originals;private final Optional<PreparedFixture> fixture;private final Optional<FixtureStartupCase> startupCase;
        private FrozenRunProfile(NativeLaunchPlan plan,Request request,ExactRef requestRef,Optional<SuccessionLifecycleBinding> binding,InitialEpisodePolicy initialPolicy,List<SharedSourceFiles.Witness> originals,Optional<PreparedFixture> fixture,Optional<FixtureStartupCase> startupCase) {
            this.plan=plan;this.request=request;this.requestRef=requestRef;this.binding=binding;this.initialPolicy=initialPolicy;this.originals=List.copyOf(originals);this.fixture=Objects.requireNonNull(fixture);this.startupCase=Objects.requireNonNull(startupCase);
        }
        public Request request(){return request;}
        public InitialEpisodePolicy initialPolicy(){return initialPolicy;}
        public ExactRef requestReference(){return requestRef;}
        public SuccessionLifecycleBinding binding(){return binding.orElseThrow(()->new IllegalStateException("native_campaign has null lifecycle provenance"));}
        public Optional<SuccessionLifecycleBinding> lifecycleBinding(){return binding;}
        /** Actual private projection, distinct from its nullable public provenance. */
        public void requireExplicitNativeCampaign()throws IOException {
            if(request.lifecycle()!=LifecycleMode.NATIVE_CAMPAIGN||binding.isPresent())throw new IOException("explicit native_campaign private projection required");
            if(request.legacyImport() instanceof DisabledFreshFixture)initialPolicy.requireFixtureProjection(fixture.orElseThrow());
            else if(request.legacyImport() instanceof EnabledNativeCampaign)initialPolicy.requireSavedProjection(plan);
            else throw new IOException("null lifecycle is not an explicit native_campaign projection");
        }
        public ImportMode importMode(){return request.legacyImport();}
        /** Same private prepared object produced once while this actual profile is read. */
        public Optional<PreparedFixture> fixture(){return fixture;}
        public Optional<FixtureStartupCase> startupCase(){return startupCase;}
        public List<ExactRef> originalReferences(){
            var refs=new ArrayList<ExactRef>(originals.stream().map(item->new ExactRef(item.source().path(),item.source().bytes(),item.source().sha256())).toList());
            fixture.ifPresent(actual->refs.addAll(actual.inputClosure()));startupCase.ifPresent(actual->refs.addAll(actual.sourceClosure()));return refs.stream().distinct().toList();
        }
        public void requireCurrent(NativeLaunchPlan identical,Clock actualClock)throws IOException {
            if(identical!=plan)throw new IOException("frozen run profile belongs to another retained launch plan instance");
            current(request,plan,actualClock);initialPolicy.verify();
            if(request.lifecycle()==LifecycleMode.NATIVE_CAMPAIGN)requireExplicitNativeCampaign();
            for(var original:originals)SharedSourceFiles.assertUnchanged(original);
            if(request.legacyImport() instanceof DisabledFreshFixture selected) {
                PreparedFixture actual=fixture.orElseThrow(()->new IOException("actual frozen fixture is missing its original prepared producer"));
                if(!actual.policySource().equals(selected.policySource())||!actual.stateDir().equals(plan.stateDirectory())
                        ||!actual.profileDirectory().equals(plan.profileDirectory()))throw new IOException("frozen fixture policy/state/profile differs from the identical plan");
                actual.verifySources();
                if(selected.startupCaseSource().isPresent()) {
                    var original=startupCase.orElseThrow(()->new IOException("explicit startup case lacks its original private prepared producer"));
                    if(!original.contractSource().equals(selected.startupCaseSource().orElseThrow()))throw new IOException("startup case contract differs from the explicit frozen request");original.verifySources();
                } else if(startupCase.isPresent())throw new IOException("unselected external startup case cannot be retained");
            } else if(fixture.isPresent()||startupCase.isPresent())throw new IOException("ordinary/imported profile cannot retain a fixture producer");
        }
    }
    /** The default physical reader prepares an explicit fixture once before reading its matching policy original. */
    public static FrozenRunProfile readExact(ExactRef actualRequest,NativeLaunchPlan identicalPlan,ExactRef actualPolicy,Clock actualClock)throws IOException {
        Objects.requireNonNull(actualRequest);Objects.requireNonNull(identicalPlan);Objects.requireNonNull(actualPolicy);Objects.requireNonNull(actualClock);
        var held=new ArrayList<SharedSourceFiles.Witness>();Request request=decode(read(actualRequest,MAXIMUM_REQUEST_BYTES,held));current(request,identicalPlan,actualClock);
        InitialEpisodePolicy policy;
        if(request.legacyImport() instanceof DisabledFreshFixture selected) {
            require(identicalPlan.preparedProfile().preparedInputs().stream().anyMatch(ref->same(ref,selected.policySource())),"fixture policy missing from actual prepared closure");
            PreparedFixture actual=PreparedFixture.prepare(selected.policySource(),identicalPlan.stateDirectory(),identicalPlan.profileDirectory(),"native_campaign");
            policy=InitialEpisodePolicy.readExactFixture(actualPolicy,identicalPlan.preparedProfile().environmentManifest(),actual);
        } else if(request.legacyImport() instanceof EnabledNativeCampaign)policy=InitialEpisodePolicy.readExactSaved(actualPolicy,identicalPlan);
        else policy=InitialEpisodePolicy.readExact(actualPolicy,identicalPlan.preparedProfile().environmentManifest());
        for(var original:held)SharedSourceFiles.assertUnchanged(original);
        return readExact(actualRequest,identicalPlan,policy,actualClock);
    }
    public static FrozenRunProfile readExact(ExactRef actualRequest,NativeLaunchPlan identicalPlan,InitialEpisodePolicy sameActualPolicy,Clock actualClock)throws IOException {
        Objects.requireNonNull(actualRequest);Objects.requireNonNull(identicalPlan);Objects.requireNonNull(sameActualPolicy);Objects.requireNonNull(actualClock);
        var originals=new ArrayList<SharedSourceFiles.Witness>();
        try {
            Request request=decode(read(actualRequest,MAXIMUM_REQUEST_BYTES,originals));current(request,identicalPlan,actualClock);
            FileRef environment=identicalPlan.preparedProfile().environmentManifest();
            require(same(environment,request.environmentManifest()),"explicit current environment differs from retained plan");
            // The run request is itself an exact prepared input. A nearby historical manifest is insufficient.
            require(identicalPlan.preparedProfile().preparedInputs().stream().anyMatch(ref->same(ref,actualRequest)),"run request missing from identical plan's prepared input closure");
            byte[] environmentBytes=read(request.environmentManifest(),1048576,originals);
            ObjectValue manifest=object(OriginalDriverJournal.parse(environmentBytes,1048576),"actual environment object required");
            var environmentTree=org.xar.ck3.control.build.ControlBuild.strictMapper().readTree(environmentBytes);
            org.xar.ck3.control.build.NativeRunProfileManifest.requireSupported(environmentTree);
            boolean currentEnvironment=org.xar.ck3.control.build.NativeRunProfileManifest.isCurrentVersion(environmentTree);
            require(currentEnvironment||(!(request.legacyImport() instanceof EnabledNativeCampaign)
                    &&!(request.legacyImport() instanceof DisabledFreshFixture)),
                    "historical ENV DATA cannot issue a current private native_campaign profile");
            if(currentEnvironment) {
                var typed=org.xar.ck3.control.build.NativeRunProfileManifest.readEnvironmentOriginal(environment);
                requireEnvironmentDomain(request.legacyImport(),typed);
                require(typed.game().executable().equals(identicalPlan.sources().review().gameExecutable().path())
                        &&typed.game().executableSha256().equals(identicalPlan.sources().review().gameExecutable().sha256()),
                        "current explicit environment belongs to another retained Game executable");
            }
            require(path(manifest.get("state_dir")).equals(identicalPlan.stateDirectory())&&path(manifest.get("profile_dir")).equals(identicalPlan.profileDirectory()),"current environment has another state/profile directory");
            require(text(manifest.get("machine_id")).equals(request.machineId()),"environment machine differs from actual request");
            sameActualPolicy.verify();
            require(sameActualPolicy.environment().equals(request.environmentManifest()),"existing InitialEpisodePolicy belongs to another exact current environment");
            Optional<SuccessionLifecycleBinding> normalized;
            if(request.legacyImport() instanceof EnabledNativeCampaign) {
                sameActualPolicy.requireSavedProjection(identicalPlan);normalized=Optional.empty();
            } else if(request.legacyImport() instanceof DisabledFreshFixture) {
                require(sameActualPolicy.kind()==InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_FIXTURE&&java.util.Arrays.equals(sameActualPolicy.lifecycle().bytes(),new byte[]{'n','u','l','l'}),"native_campaign must preserve null lifecycle provenance");
                normalized=Optional.empty();
            } else {
                SuccessionLifecycleBinding bound=SuccessionLifecycleCodec.decode(sameActualPolicy.lifecycle().bytes());
                require(bound.profile().lifecycle().equals(request.lifecycle().wire()),"explicit run lifecycle differs from the sole actual frozen policy producer");
                require(request.ordinaryCampaignNoPact()==bound.profile().ordinary(),"explicit fresh pact contradicts the sole frozen lifecycle profile");normalized=Optional.of(bound);
            }
            for(ExactRef original:sameActualPolicy.evidenceClosure())originals.add(retainOriginalEvidence(original));
            Optional<PreparedFixture> fixture=Optional.empty();Optional<FixtureStartupCase> startupCase=Optional.empty();
            if(request.legacyImport() instanceof DisabledFreshFixture selected) {
                require(identicalPlan.preparedProfile().preparedInputs().stream().anyMatch(ref->same(ref,selected.policySource())),
                        "explicit fixture policy must belong to the same prepared input closure");
                PreparedFixture actual=sameActualPolicy.explicitFixture().orElseThrow(()->new IOException("fixture initial policy has no original private preparation"));
                sameActualPolicy.requireFixtureProjection(actual);
                require(actual.policySource().equals(selected.policySource())&&actual.stateDir().equals(identicalPlan.stateDirectory())&&actual.profileDirectory().equals(identicalPlan.profileDirectory()),"fixture initial policy crossed the actual selected inputs");
                fixture=Optional.of(actual);
                if(selected.startupCaseSource().isPresent()) {
                    ExactRef contract=selected.startupCaseSource().orElseThrow();
                    require(identicalPlan.preparedProfile().preparedInputs().stream().anyMatch(ref->same(ref,contract)),"explicit startup case must belong to the same prepared input closure");
                    FixtureStartupCase prepared=FixtureStartupCase.prepare(contract,actual);
                    prepared.requireReviewedSources(identicalPlan.sources().review().completeRuntimeSources().stream().map(ref->new ExactRef(ref.path(),ref.bytes(),ref.sha256())).toList());
                    startupCase=Optional.of(prepared);
                }
            }
            FrozenRunProfile result=new FrozenRunProfile(identicalPlan,request,actualRequest,normalized,sameActualPolicy,originals,fixture,startupCase);
            result.requireCurrent(identicalPlan,actualClock);return result;
        }catch(IllegalArgumentException invalid){throw new IOException("actual frozen run profile is unavailable or incompatible",invalid);}
    }
    /** Closed configuration-domain check only; never issues a private FrozenRunProfile or Game qualification. */
    public static void requireEnvironmentDomain(ImportMode mode,org.xar.ck3.control.build.NativeRunProfileManifest.ProfileEnvironment actual) {
        Objects.requireNonNull(mode);Objects.requireNonNull(actual);
        switch(mode) {
            case EnabledNativeCampaign ignored->InitialEpisodePolicy.requireSavedProfileDomain(actual);
            case DisabledFreshFixture ignored->require(actual.kind()==org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.FRESH_FRONTEND_FIXTURE,
                    "fresh fixture import cannot consume an ordinary or Saved environment");
            case Enabled ignored->require(actual instanceof org.xar.ck3.control.build.NativeRunProfileManifest.Manifest,
                    "ordinary import requires the unchanged ordinary v2 environment");
            case DisabledFreshRobert ignored->require(actual instanceof org.xar.ck3.control.build.NativeRunProfileManifest.Manifest,
                    "ordinary fresh Robert requires the unchanged ordinary v2 environment");
        }
    }
    private static void current(Request request,NativeLaunchPlan plan,Clock clock)throws IOException {
        Instant now=Objects.requireNonNull(clock).instant();
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!request.machineId().equals(plan.sources().review().machineId())
                ||!request.requestId().equals(plan.requestId())||!request.sessionId().equals(plan.sessionId())
                ||now.isBefore(request.observedAt())||!now.isBefore(request.reviewAt()))throw new IOException("run profile is foreign, expired or belongs to another actual request/session");
        if(request.legacyImport() instanceof EnabledNativeCampaign enabled&&(!(plan.load() instanceof NativeLaunchPlan.SavedGame)||!enabled.stateDirectory().equals(plan.stateDirectory())))throw new IOException("explicit Saved native import requires the identical Saved plan/state directory");
        if(request.legacyImport() instanceof Enabled enabled&&!enabled.stateDirectory().equals(plan.stateDirectory()))throw new IOException("legacy import directory differs from the actual managed runtime directory");
        if(request.legacyImport() instanceof DisabledFreshFixture&&!(plan.load() instanceof NativeLaunchPlan.NewGame))throw new IOException("disabled fresh-fixture import cannot be used for a Saved launch");
        if(request.legacyImport() instanceof DisabledFreshRobert&&!(plan.load() instanceof NativeLaunchPlan.NewGame))throw new IOException("disabled fresh-Robert import cannot be used for a Saved launch");
    }
    /** Unparsed original evidence is streamed; JSON input bounds apply only to the actual decoders. */
    static SharedSourceFiles.Witness retainOriginalEvidence(ExactRef expected)throws IOException {
        try {
            absolute(Path.of(expected.path()));require(expected.bytes()>=0,"nonnegative exact evidence size required");
            var original=SharedSourceFiles.observe(Path.of(expected.path()));
            require(same(original.source(),expected),"original evidence differs from its configured exact reference");
            SharedSourceFiles.assertUnchanged(original);return original;
        } catch(IllegalArgumentException invalid) {throw new IOException("actual original evidence is unavailable or incompatible",invalid);}
    }
    private static byte[] read(ExactRef expected,int maximum,List<SharedSourceFiles.Witness> originals)throws IOException {
        absolute(Path.of(expected.path()));require(expected.bytes()>0&&expected.bytes()<=maximum,"bounded exact original required");
        var before=SharedSourceFiles.observe(Path.of(expected.path()));require(same(before.source(),expected),"original content/source differs from configured pin");
        byte[] bytes;try(var input=Files.newInputStream(Path.of(expected.path()))){bytes=input.readNBytes(maximum+1);}
        require(bytes.length==expected.bytes()&&OriginalDriverJournal.sha256(bytes).equals(expected.sha256()),"complete original read differs");
        SharedSourceFiles.assertUnchanged(before);originals.add(before);return bytes;
    }
    private static ExactRef reference(Value value){ObjectValue ref=object(value,"exact source reference required");exact(ref,Set.of("path","bytes","sha256"));return new ExactRef(text(ref.get("path")),OriginalDriverJournal.integer(ref.get("bytes"),"exact source size required").longValueExact(),text(ref.get("sha256")));}
    private static ObjectValue reference(ExactRef ref){return new ObjectValue(java.util.Map.of("path",new StringValue(ref.path()),"bytes",new IntegerValue(java.math.BigInteger.valueOf(ref.bytes())),"sha256",new StringValue(ref.sha256())));}
    private static Instant instant(Value value){String text=text(value);Instant result=Instant.parse(text);require(result.toString().equals(text),"canonical UTC instant required");return result;}
    private static ObjectValue object(Value value,String detail){if(value instanceof ObjectValue object)return object;throw new IllegalArgumentException(detail);}
    private static String text(Value value){if(value instanceof StringValue text&&!text.value().isEmpty())return text.value();throw new IllegalArgumentException("nonempty exact string required");}
    private static Path path(Value value){Path result=Path.of(text(value));absolute(result);return result;}
    private static void absolute(Path value){require(value!=null&&value.isAbsolute()&&value.normalize().equals(value),"absolute normalized original path required");}
    private static boolean same(FileRef left,ExactRef right){return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equals(right.sha256());}
    private static void exact(ObjectValue value,Set<String> fields){require(value.fields().keySet().equals(fields),"exact versioned fields required: "+fields);}
    private static void require(boolean condition,String detail){if(!condition)throw new IllegalArgumentException(detail);}
}
