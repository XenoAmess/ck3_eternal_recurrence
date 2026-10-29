package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.NativePrelaunchInputs;
import org.xar.ck3.control.service.root.RootBootstrapOutputContract.Kind;
import org.xar.ck3.control.service.root.RootBootstrapOutputContract.Output;

/** First launch-plan original. Financial output admission remains the one concrete bootstrap guard.
 * Native source/profile acceptance is not Steam offline, a ManagedGameSession or Game readiness. */
public final class RootNativeLaunchPlanInputs {
    public static final String FILE_NAME = "native-launch-plan.json";
    public static final String INVOCATION_SCHEMA="xar.java-root-native-launch-plan-inputs/v1";
    /** The whole invocation, including nested configuration, shares one explicit JSON byte budget. */
    public static final int MAXIMUM_INVOCATION_BYTES=StrictJson.EXPLICIT_MAX_BYTES;
    private RootNativeLaunchPlanInputs() { }
    public enum Mode { QUOTE,CREATE_NEW }

    /** Explicit actual configuration and the original financial binding; a quote requires JSON null. */
    public record Invocation(Mode mode,Request request,Optional<FileRef> binding) {
        public Invocation {
            Objects.requireNonNull(mode);Objects.requireNonNull(request);binding=Objects.requireNonNull(binding);
            if((mode==Mode.CREATE_NEW)!=binding.isPresent())
                throw new IllegalArgumentException("create-new requires the actual output binding; quote requires explicit null");
            binding.ifPresent(ref->{
                Path path=Path.of(ref.path());
                if(!path.isAbsolute()||!path.normalize().equals(path)||ref.bytes()<1||ref.bytes()>RootBootstrapOutputContract.MAXIMUM_BYTES)
                    throw new IllegalArgumentException("bounded exact original output binding required");
            });
        }
    }

    /** The existing launch codec owns every configuration field, including both load/profile branches. */
    public static byte[] encodeInvocation(Invocation actual)throws IOException {
        Objects.requireNonNull(actual);var row=StrictJson.object().put("schema",INVOCATION_SCHEMA).put("mode",actual.mode().name());
        row.set("configuration",StrictJson.parse(encodeConfiguration(actual.request().configuration()),NativeLaunchPlanCodec.MAXIMUM_BYTES));
        row.put("target",actual.request().target().toString());row.put("review_at_utc",actual.request().reviewAt().toString());
        actual.binding().ifPresentOrElse(ref->row.set("binding_ref",new ExactRef(ref.path(),ref.bytes(),ref.sha256()).toJson()),()->row.putNull("binding_ref"));
        return StrictJson.canonical(row,MAXIMUM_INVOCATION_BYTES);
    }
    public static Invocation decodeInvocation(byte[] original)throws IOException {
        try {
            var row=StrictJson.object(StrictJson.parse(original,MAXIMUM_INVOCATION_BYTES),Set.of(
                    "schema","mode","configuration","target","review_at_utc","binding_ref"));
            StrictJson.require(INVOCATION_SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact Native plan input invocation schema required");
            String review=StrictJson.text(row.get("review_at_utc"));Instant until=Instant.parse(review);
            StrictJson.require(until.toString().equals(review),"canonical Native plan publication review required");
            var configuration=NativeLaunchPlanCodec.fromJson(row.get("configuration"));
            Optional<FileRef> binding;
            var field=row.get("binding_ref");
            StrictJson.require(field!=null,"explicit binding_ref or null required");
            if(field.isNull())binding=Optional.empty();
            else {var ref=ExactRef.fromJson(field);binding=Optional.of(new FileRef(ref.path(),ref.bytes(),ref.sha256()));}
            return new Invocation(Mode.valueOf(StrictJson.text(row.get("mode"))),new Request(configuration,Path.of(StrictJson.text(row.get("target"))),until),binding);
        }catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("invalid Native plan input invocation",invalid);}
    }
    public static Invocation readInvocation(FileRef original)throws IOException {
        return decodeInvocation(RootRuntimeDefinitions.read(Objects.requireNonNull(original),MAXIMUM_INVOCATION_BYTES));
    }

    /** Routes into the sole real producer and its existing Guard. No Native process or Game is started. */
    static byte[] execute(Invocation invocation,Clock clock)throws IOException {
        Objects.requireNonNull(invocation);Objects.requireNonNull(clock);
        Prepared prepared=prepare(invocation.request(),clock);
        if(invocation.mode()==Mode.QUOTE)return quoteFrame(invocation.request(),prepared.quote());
        var config = invocation.request().configuration();
        var effectiveMachine = config.review().machineId() != null ? config.review().machineId() : config.steam().machineId();
        var row=StrictJson.object().put("schema","xar.java-root-native-launch-plan-publication/v1")
                .put("machine_id",effectiveMachine)
                .put("observed_at_utc",clock.instant().toString())
                .put("scope","IMMUTABLE_NATIVE_PLAN_FILE_ONLY_NO_STEAM_GAME_OR_LEDGER_ADMISSION");
        row.set("output",ControlBuild.strictMapper().valueToTree(prepared.quote()));
        try(var authority=RootBootstrapOutputGuard.readExact(invocation.binding().orElseThrow(),clock)) {
            Published published=prepared.createNew(authority,clock);published.requireCurrent(clock);
            row.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
            row.set("original",published.original().toJson());row.set("native_file",ControlBuild.strictMapper().valueToTree(published.nativeFile()));
        }
        return StrictJson.canonical(row,65536);
    }
    /** The actual independent issuer consumes this sole phase-quote ABI. LF is emitted by main. */
    static byte[] quoteFrame(Request request,Output output)throws IOException {
        var config = request.configuration();
        var effectiveMachine = config.review().machineId() != null ? config.review().machineId() : config.steam().machineId();
        var quote=new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","NATIVE_LAUNCH_PLAN",
                effectiveMachine,request.reviewAt().toString(),request.target().getParent().toString(),
                List.of(output),List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
        return RootBootstrapProtocol.encode(quote,RootBootstrapProtocol.FRAME_BYTES-1);
    }
    /** One exact input request; no template plan, implicit native source, runtime launch or alternate writer. */
    public static void main(String[] args)throws IOException {
        if(args.length!=3||!args[1].matches("[1-9][0-9]{0,6}")||!args[2].matches("[0-9a-f]{64}"))
            throw new IllegalArgumentException("RootNativeLaunchPlanInputs requires invocation-path exact-bytes exact-sha256");
        var original=new FileRef(args[0],Long.parseLong(args[1]),args[2]);
        Invocation invocation=readInvocation(original);byte[] output=execute(invocation,Clock.systemUTC());original.verify();
        System.out.write(output);System.out.write(10);System.out.flush();
        if(System.out.checkError())throw new IOException("Native plan publication output failed; preserve the original publication and do not retry its write");
    }

    /** Explicit DATA from real inputs; no previous plan original or template is accepted. */
    public record Request(NativeLaunchPlanCodec.Configuration configuration, Path target, Instant reviewAt) {
        public Request {
            Objects.requireNonNull(configuration); Objects.requireNonNull(target); Objects.requireNonNull(reviewAt);
            if (!target.isAbsolute() || !target.normalize().equals(target)
                    || target.getFileName()==null || !FILE_NAME.equals(target.getFileName().toString()))
                throw new IllegalArgumentException("One normalized absolute first native-launch-plan.json target required");
            if (reviewAt.isAfter(configuration.deadline()))
                throw new IllegalArgumentException("Publication review must fit the actual plan deadline");
            var expires = configuration.review().expiresAt();
            if (!(configuration.preparedProfile().declaration() instanceof NativeLaunchPlan.PreparedProfile.NoMods)
                    && expires != null && reviewAt.isAfter(expires))
                throw new IllegalArgumentException("Publication review must fit the actual native review");
        }
    }

    /** Only prepare can construct this object, after the real Native proof and current profile are read. */
    public static final class Prepared {
        private final Request request;
        private final NativeLaunchPlan accepted;
        private final byte[] bytes;
        private final List<SharedSourceFiles.Witness> originals;
        private Prepared(Request request, NativeLaunchPlan accepted, byte[] bytes,
                List<SharedSourceFiles.Witness> originals) {
            this.request=request; this.accepted=accepted; this.bytes=bytes.clone();
            this.originals=List.copyOf(originals);
        }
        public Path target() { return request.target(); }
        /** Actual bytes are quoted before the independent issuer signs any output binding. */
        public Output quote() {
            return new Output(Kind.NATIVE_LAUNCH_PLAN, FILE_NAME, bytes.length, DriverJson.sha256(bytes));
        }
        public List<Output> outputs() { return List.of(quote()); }

        /** Uses the already admitted concrete pre-Core writer; it never creates or signs a card. */
        public Published createNew(RootBootstrapOutputGuard authority, Clock clock) throws IOException {
            Objects.requireNonNull(authority); current(clock);
            authority.requirePlan(request.target().getParent(), outputs(), List.of(), List.of());
            authority.requireTargets(List.of(request.target()));
            requireAbsent(request.target());
            var files=authority.files();
            var written=files.createNew(request.target(), bytes);
            files.verify(written);
            if (!Arrays.equals(bytes, files.read(written, NativeLaunchPlanCodec.MAXIMUM_BYTES)))
                throw new IOException("First native plan actual writer/readback differs");
            var witness=SharedSourceFiles.observe(request.target());
            var exact=written.reference();
            if (!witness.source().equals(new FileRef(exact.path(),exact.bytes(),exact.sha256())))
                throw new IOException("First native plan Native witness differs from original writer");
            NativeLaunchPlan reopened=NativeLaunchPlan.readExact(
                    new ExactRef(exact.path(),exact.bytes(),exact.sha256()),new NativeBridgeLaunchEvidence());
            if (!NativeLaunchPlanCodec.describe(reopened).equals(NativeLaunchPlanCodec.describe(accepted)))
                throw new IOException("First native plan sole strict consumer changed the typed configuration");
            SharedSourceFiles.assertUnchanged(witness);
            current(clock);
            authority.requireTargets(List.of(request.target()));
            if (authority.files()!=files)
                throw new IOException("First native plan writer identity changed");
            return new Published(request.reviewAt(),witness,reopened,originals);
        }
        private void current(Clock clock) throws IOException {
            requireCurrent(request,clock);
            for (var witness:originals) SharedSourceFiles.assertUnchanged(witness);
            requireSources(accepted,clock);
            for (var witness:originals) SharedSourceFiles.assertUnchanged(witness);
        }
    }

    /** Private mint from actual CREATE_NEW and the existing physical-plan reader, never a Ready flag. */
    public static final class Published {
        private final Instant reviewAt;
        private final SharedSourceFiles.Witness original;
        private final NativeLaunchPlan accepted;
        private final List<SharedSourceFiles.Witness> originals;
        private Published(Instant reviewAt,SharedSourceFiles.Witness original,NativeLaunchPlan accepted,
                List<SharedSourceFiles.Witness> originals) {
            this.reviewAt=reviewAt; this.original=original; this.accepted=accepted; this.originals=List.copyOf(originals);
        }
        public ExactRef original() {
            var source=original.source();
            return new ExactRef(source.path(),source.bytes(),source.sha256());
        }
        public SharedSourceFiles.NativeFile nativeFile() { return original.nativeFile(); }
        public NativeLaunchPlan requireCurrent(Clock clock) throws IOException {
            Objects.requireNonNull(clock);
            if (!clock.instant().isBefore(reviewAt))
                throw new IOException("First native plan publication review expired");
            SharedSourceFiles.assertUnchanged(original);
            for (var source:originals) SharedSourceFiles.assertUnchanged(source);
            requireSources(accepted,clock);
            for (var source:originals) SharedSourceFiles.assertUnchanged(source);
            SharedSourceFiles.assertUnchanged(original);
            return accepted;
        }
    }

    /** Reconstructs the exact PreparedProfile DATA from the sole current Java environment original. */
    public static NativeLaunchPlan.PreparedProfile preparedProfile(FileRef environmentOriginal) throws IOException {
        Objects.requireNonNull(environmentOriginal);
        var environment=NativeRunProfileProducer.readEnvironmentVerified(environmentOriginal);
        if(environment instanceof NativeRunProfileManifest.ExplicitManifest)
            return NativeLaunchPlan.PreparedProfile.fromExplicitEnvironment(environmentOriginal,List.of());
        var manifest=(NativeRunProfileManifest.Manifest)environment;
        var inputs=new ArrayList<FileRef>();
        for (var asset:manifest.profileAssets()) inputs.add(asset.original());
        inputs.add(measured(manifest.game().vanillaRules(),manifest.game().vanillaRulesSha256()));
        inputs.add(measured(manifest.game().launcherSettings(),manifest.game().launcherSettingsSha256()));
        inputs.add(measured(manifest.mod().productionManifest(),manifest.mod().productionManifestSha256()));
        return new NativeLaunchPlan.PreparedProfile(environmentOriginal,Path.of(manifest.mod().productionPath()),
                "mod/xar_autoplayer.mod",List.copyOf(inputs),manifest.mod().completeProductionFiles());
    }

    /** Explicit domains use the same physical producer; post-ENV request sources are independently retained. */
    public static NativeLaunchPlan.PreparedProfile preparedProfile(FileRef environmentOriginal,List<FileRef> additionalInputs)throws IOException {
        Objects.requireNonNull(environmentOriginal);Objects.requireNonNull(additionalInputs);
        var environment=NativeRunProfileProducer.readEnvironmentVerified(environmentOriginal);
        if(environment instanceof NativeRunProfileManifest.ExplicitManifest)
            return NativeLaunchPlan.PreparedProfile.fromExplicitEnvironment(environmentOriginal,additionalInputs);
        return ordinaryPreparedProfile(preparedProfile(environmentOriginal),additionalInputs);
    }
    /** Ordinary production keeps every original profile input and observes each independent later original. */
    static NativeLaunchPlan.PreparedProfile ordinaryPreparedProfile(NativeLaunchPlan.PreparedProfile ordinary,
            List<FileRef> additionalInputs)throws IOException {
        Objects.requireNonNull(ordinary);Objects.requireNonNull(additionalInputs);
        if(ordinary.ordinary().isEmpty()||additionalInputs.size()>8192)
            throw new IOException("finite ordinary prepared originals required");
        var inputs=new LinkedHashMap<Path,FileRef>();
        var ordered=new ArrayList<>(additionalInputs);
        ordered.sort(java.util.Comparator.comparing(ref->Path.of(ref.path()).toAbsolutePath().normalize().toString()));
        var all=new ArrayList<>(ordinary.preparedInputs());all.addAll(ordered);
        for(var ref:all){
            var held=SharedSourceFiles.observe(Path.of(ref.path()));
            if(!held.source().equals(ref))throw new IOException("ordinary prepared original differs from its exact reference");
            Path real=Path.of(ref.path()).toRealPath();var previous=inputs.putIfAbsent(real,ref);
            if(previous!=null&&!previous.equals(ref))throw new IOException("conflicting ordinary prepared input originals");
            SharedSourceFiles.assertUnchanged(held);
        }
        return new NativeLaunchPlan.PreparedProfile(ordinary.environmentManifest(),ordinary.productionRoot(),
                ordinary.enabledOuterDescriptorRef(),List.copyOf(inputs.values()),ordinary.completeProductionFiles());
    }

    public static Prepared prepare(Request request,Clock clock) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(clock);
        requireCurrent(request,clock); requireAbsent(request.target());
        var data=request.configuration();
        var profile = data.preparedProfile();
        if (profile.ordinary().isPresent() && data.debugMode())
            throw new IOException("Current Java production profile does not enable debug mode");
        byte[] bytes=encodeConfiguration(data);
        NativeLaunchPlan.PreparedProfile derived;
        if (profile.declaration() instanceof NativeLaunchPlan.PreparedProfile.NoMods) {
            derived = profile;
        } else {
            derived=preparedProfile(profile.environmentManifest(), profile.preparedInputs());
            if (!derived.equals(profile))
                throw new IOException("Explicit prepared profile differs from its actual current Java producer");
        }
        NativeLaunchPlan accepted;
        try { accepted=data.accept(new NativeBridgeLaunchEvidence()); }
        catch (IllegalArgumentException invalid) { throw new IOException("Invalid first native plan inputs",invalid); }
        var witnesses=profileWitnesses(derived);
        requireSources(accepted,clock);
        for (var witness:witnesses) SharedSourceFiles.assertUnchanged(witness);
        requireCurrent(request,clock); requireAbsent(request.target());
        return new Prepared(request,accepted,bytes,witnesses);
    }

    /** Sole codec DATA path, also exercised without minting source/financial admission. */
    static byte[] encodeConfiguration(NativeLaunchPlanCodec.Configuration data) throws IOException {
        Objects.requireNonNull(data);
        try {
            byte[] bytes=StrictJson.canonical(NativeLaunchPlanCodec.toJson(data),NativeLaunchPlanCodec.MAXIMUM_BYTES);
            var decoded=NativeLaunchPlanCodec.fromJson(StrictJson.parse(bytes,NativeLaunchPlanCodec.MAXIMUM_BYTES));
            if (!data.equals(decoded)) throw new IOException("Native plan configuration codec roundtrip differs");
            return bytes;
        } catch (IllegalArgumentException invalid) {
            throw new IOException("Invalid finite current Native plan DATA",invalid);
        }
    }
    private static List<SharedSourceFiles.Witness> profileWitnesses(NativeLaunchPlan.PreparedProfile prepared)
            throws IOException {
        if (prepared.declaration() instanceof NativeLaunchPlan.PreparedProfile.NoMods) return List.of();
        var refs=new ArrayList<FileRef>(); refs.add(prepared.environmentManifest());
        refs.addAll(prepared.preparedInputs());
        if(prepared.ordinary().isPresent())refs.addAll(prepared.completeProductionFiles());
        else {
            var original=NativeRunProfileProducer.readEnvironmentVerified(prepared.environmentManifest());
            if(!(original instanceof NativeRunProfileManifest.ExplicitManifest explicit))
                throw new IOException("Explicit prepared profile requires its actual physical ENV");
            for(var witness:explicit.profile().custody().productFiles())refs.add(witness.source());
        }
        Map<Path,FileRef> unique=new LinkedHashMap<>();
        for (var ref:refs) {
            ref.verify(); Path real=Path.of(ref.path()).toRealPath();
            FileRef prior=unique.putIfAbsent(real,ref);
            if (prior!=null && !prior.equals(ref)) throw new IOException("Conflicting actual profile source");
        }
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        for (var ref:unique.values()) {
            var witness=SharedSourceFiles.observe(Path.of(ref.path()));
            if (!witness.source().equals(ref)) throw new IOException("Profile source changed before first plan");
            witnesses.add(witness);
        }
        return List.copyOf(witnesses);
    }
    private static FileRef measured(String path,String expectedSha) throws IOException {
        var original=FileRef.measure(Path.of(path));
        if (!original.sha256().equals(expectedSha)) throw new IOException("Actual profile dependency digest differs");
        return original;
    }
    private static void requireSources(NativeLaunchPlan accepted,Clock clock) throws IOException {
        accepted.sources().requireLoadedClass(RootNativeLaunchPlanInputs.class);
        accepted.sources().requireLoadedClass(NativeLaunchPlanCodec.class);
        accepted.sources().requireLoadedClass(NativeBridgeLaunchEvidence.class);
        NativePrelaunchInputs.requireCurrent(accepted,clock);
    }
    private static void requireCurrent(Request request,Clock clock) throws IOException {
        if (!clock.instant().isBefore(request.reviewAt())
                || !clock.instant().isBefore(request.configuration().deadline()))
            throw new IOException("First native plan publication review/deadline expired");
    }
    private static void requireAbsent(Path target) throws IOException {
        SharedSourceFiles.plainAncestors(target.getParent());
        if (Files.exists(target,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("First native plan target already exists; original unknown writes are never replayed");
    }
}

