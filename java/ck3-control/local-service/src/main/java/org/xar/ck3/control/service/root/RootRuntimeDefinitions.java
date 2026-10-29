package org.xar.ck3.control.service.root;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.OriginalMcpCapture.OriginalMcpSourceSet;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.SingleWinnerSourceIndex;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.writer.RollbackPair;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpHost;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

/** One explicit configuration boundary; loading it never starts a Game or grants restoration authority. */
public final class RootRuntimeDefinitions {
    public static final int MAXIMUM_BYTES=StrictJson.EXPLICIT_MAX_BYTES;
    public static final int MAXIMUM_INDEX_BYTES=SingleWinnerSourceIndex.MAX_BYTES;
    private static final String EVENT_SCHEMA="xar.java-event-source-read-context/v1";
    private final Inputs inputs;
    private final RootRuntimeStartup startup;
    private final Clock actualClock;

    /** Pure, immutable inputs for the one named central constructor. No configured callback can mint authority. */
    public record Inputs(FileRef originalRef,Configuration configuration,RootApplicationConfiguration application,
            StorageLease storageLease,List<SelectedSource> sourceIndex,EventSourceReadContext eventSources,
            RootOriginalMcpCapture.Retained originalMcpCapture) {
        public Inputs {
            file(originalRef,MAXIMUM_BYTES);Objects.requireNonNull(configuration);Objects.requireNonNull(application);
            Objects.requireNonNull(storageLease);sourceIndex=List.copyOf(sourceIndex);Objects.requireNonNull(eventSources);
            Objects.requireNonNull(originalMcpCapture);
            StrictJson.require(same(configuration.data(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT),originalMcpCapture.original()),
                    "one actual captured MCP receipt across all runtime inputs required");
            StrictJson.require(configuration.machineId().equals(application.machineId())
                    &&configuration.machineId().equals(storageLease.machineId())
                    &&configuration.machineId().equals(eventSources.machineId()),"one actual machine across all runtime inputs required");
        }
        public ExactRef source(SourceRole role){return configuration.source(role);}
        public List<ExactRef> closure(ClosureRole role){return configuration.closure(role);}
        public FileRef data(DataRole role){return configuration.data(role);}
        /** Presence selects an exact original proof only; actual reducer and writer qualification is separate. */
        public Optional<FileRef> optionalData(DataRole role){return configuration.optionalData(role);}
        /** Recorded four-module metadata; selecting it grants no source, dispatch or Game qualification. */
        public OriginalMcpSourceSet originalMcpSources(Clock actualClock)throws IOException {
            originalMcpCapture.requireInputs(this,Objects.requireNonNull(actualClock));return originalMcpCapture.sourceSet();
        }
    }
    private RootRuntimeDefinitions(Inputs inputs,Clock clock)throws IOException {
        this.inputs=Objects.requireNonNull(inputs);actualClock=Objects.requireNonNull(clock);startup=new RootRuntimeStartup(inputs,actualClock);
    }
    /** Decode the necessary configuration DATA without granting source, runtime or Game qualification. */
    public static Inputs readInputs(FileRef ref,Clock clock)throws IOException {
        Objects.requireNonNull(clock);
        try {
            Configuration config=decodeConfiguration(read(ref,MAXIMUM_BYTES));
            RootApplicationConfiguration application=RootApplicationConfiguration.fromJson(StrictJson.parse(
                    read(config.applicationRef(),RootApplicationConfiguration.MAXIMUM_BYTES),RootApplicationConfiguration.MAXIMUM_BYTES));
            StrictJson.require(application.mode()==HostMode.COMPLETE_MIGRATION,"complete-migration application configuration required");
            StrictJson.require(same(config.nativeLaunchPlanRef(),RootApplicationConfiguration.file(application.nativeLaunchPlan())),
                    "native launch plan differs from selected application");
            StorageLease lease=decodeStorageLease(read(config.storageLeaseRef(),MAXIMUM_BYTES));
            List<SelectedSource> recorded=readSourceIndex(config.sourceIndex(),config.machineId(),clock);
            verifySources(config,recorded);
            EventSourceReadContext events=decodeEventSources(read(config.data(DataRole.TRUSTED_EVENT_SOURCE_CONTEXT),ProjectionEvidenceCodec.MAX_BYTES));
            RootOriginalMcpCapture.Retained captured=RootOriginalMcpCapture.readRetained(config.data(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT));
            return new Inputs(ref,config,application,lease,recorded,events,captured);
        }catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("invalid exact Root runtime definitions",invalid);}
    }
    public static RootRuntimeDefinitions readExact(FileRef ref,Clock clock)throws IOException {
        return new RootRuntimeDefinitions(readInputs(ref,clock),clock);
    }

    public Inputs inputs(){return inputs;}
    /** Pre-Core production from actual typed handlers; complete-migration/Game admission stays separate. */
    public RootBootstrapOutputContract.Output quotePublicAdmission(Path target)throws IOException {
        return startup.quotePublicAdmission(target);
    }
    public FileRef publishPublicAdmission(FileRef exactOutputBinding,Path target)throws IOException {
        try(var authority=RootBootstrapOutputGuard.readExact(exactOutputBinding,actualClock)){
            return startup.publishPublicAdmission(authority,target);
        }
    }
    public void requireApplication(FileRef actual)throws IOException {
        file(actual,MAXIMUM_BYTES);
        if(!same(inputs.configuration().applicationRef(),actual))throw new IOException("Root Main and runtime definitions selected different actual applications");
    }
    public void requireCompleteMigration()throws IOException {startup.requireCompleteMigration();}

    public RootRuntimeCatalogFactory catalogFactory(){return startup.catalogFactory();}
    /** The original public handler Context retained by this same Startup. */
    public RootPublicHandlerProductsFactory.Context publicHandlerContext()throws IOException{return startup.publicHandlerContext();}
    /** Retain the same original Prepared already owned by Startup/Core, never construct a fixture substitute. */
    public RootStartupNextResources.Prepared nextResources(RootApplicationAssembly.Core actual)throws IOException {
        return startup.nextResources(actual);
    }
    /** Return the one pre-Core Driver source factory retained by this same actual Startup. */
    public RootDriverProductSourcesFactory driverProductSources()throws IOException{return startup.driverProductSources();}
    public Optional<RollbackPair.Authority> rollbackAuthority(){return startup.rollbackAuthority();}
    public NativeLaunchPlan nativeLaunchPlan()throws IOException{return startup.nativeLaunchPlan();}
    /** Bind the actual CLI original through this same retained Startup; this issues no Core or output permission. */
    public void bindStartup(FileRef actualStartup)throws IOException {startup.bindStartup(actualStartup);}
    /** The retained Startup owns the guarded same-writer receipt path, including refusal before binding. */
    public void writeRuntimeReceipt(Path target,byte[] actual)throws IOException {startup.writeRuntimeReceipt(target,actual);}
    /** Return the retained pre-Writer authority; archive and writer must receive this identical object. */
    public StorageWriteGuard storageWriteGuard()throws IOException{return startup.storageWriteGuard();}
    /** Bind the actual installed catalog to the sole retained original-resume producer. */
    public void bindOriginalResume(RootApplicationAssembly.Core core,RootInstalledCatalog installed)throws IOException {
        startup.bindOriginalResume(core,installed);
    }
    /** Publish the retained actual directory before gameplay entry through the sole Startup producer. */
    public McpExecutableDirectory.Complete installFrontendPublic(RootApplicationAssembly.Core core,RootInstalledCatalog installed,
            PublicMcpHost host,Clock actualClock)throws IOException,InterruptedException {
        return startup.installFrontendPublic(core,installed,host,actualClock);
    }
    public JavaGameLifecycle gameLifecycle(RootApplicationAssembly.Core core)throws IOException{return startup.gameLifecycle(core);}
    public RootApplicationSession finishInitial(RootApplicationAssembly.Core core,RootInstalledCatalog installed,
            GameplayEntryService.Admitted admitted,JavaGameLifecycle lifecycle,RootStartupConfiguration start,Clock clock)throws IOException,InterruptedException {
        return startup.finishInitial(core,installed,admitted,lifecycle,start,clock);
    }
    /** Finish the actual Saved route through the same retained Startup and its sole original-resume producer. */
    public RootApplicationSession finishSaved(RootApplicationAssembly.Core core,RootInstalledCatalog installed,
            RootSavedNativeCoordinator coordinator,JavaGameLifecycle lifecycle,RootStartupConfiguration start,Clock clock)throws IOException,InterruptedException {
        return startup.finishSaved(core,installed,coordinator,lifecycle,start,clock);
    }
    public McpExecutableDirectory.Complete installPublic(RootApplicationAssembly.Core core,RootInstalledCatalog installed,
            PublicMcpHost host,Clock clock)throws IOException,InterruptedException{return startup.installPublic(core,installed,host,clock);}

    public static Configuration decodeConfiguration(byte[] bytes)throws IOException {
        StrictJson.parse(bytes,MAXIMUM_BYTES);
        return ControlBuild.strictMapper().readValue(bytes,Configuration.class);
    }
    public static byte[] encodeConfiguration(Configuration configuration)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(configuration)),MAXIMUM_BYTES);
    }
    /** Sole typed final-input producer. This copies configuration data and grants no source, runtime or Game qualification. */
    public static Configuration rebindInputs(Configuration actual,FileRef actualApplication,List<DataPin> exactOriginalData) {
        Objects.requireNonNull(actual);Objects.requireNonNull(actualApplication);Objects.requireNonNull(exactOriginalData);
        return new Configuration(actual.schema(),actual.machineId(),actual.observedAtUtc(),actual.reviewAtUtc(),
                actualApplication,actual.storageLeaseRef(),actual.nativeLaunchPlanRef(),actual.runtimePackageRequestRef(),
                actual.sourceIndex(),actual.sources(),actual.closures(),exactOriginalData,
                actual.governance(),actual.finance(),actual.army(),actual.prisoners(),actual.family(),actual.frontend(),
                actual.interactions(),actual.activity(),actual.crossRun(),actual.incidents(),actual.publicCatalog(),actual.startup());
    }
    public static StorageLease decodeStorageLease(byte[] bytes)throws IOException {
        StrictJson.parse(bytes,MAXIMUM_BYTES);
        return ControlBuild.strictMapper().readValue(bytes,StorageLease.class);
    }
    /** New strict wrapper around the existing evidence-grants codec, not a second grants parser. */
    public static EventSourceReadContext decodeEventSources(byte[] bytes) {
        var root=StrictJson.object(StrictJson.parse(bytes,ProjectionEvidenceCodec.MAX_BYTES),
                Set.of("schema","machine_id","state_root","stock_game_root","evidence_grants"));
        StrictJson.require(EVENT_SCHEMA.equals(StrictJson.text(root.get("schema"))),"exact fixed event-source schema required");
        String machine=StrictJson.text(root.get("machine_id")),state=StrictJson.text(root.get("state_root")),stock=StrictJson.text(root.get("stock_game_root"));
        machine(machine);absolute(state);absolute(stock);
        var grants=ProjectionEvidenceCodec.decode(StrictJson.canonical(root.get("evidence_grants"),ProjectionEvidenceCodec.MAX_BYTES));
        // A fresh configured state has no external review evidence yet. The sole offline
        // publisher initializes this same explicit empty collection, then appends real pins.
        return new EventSourceReadContext(machine,Path.of(state),Path.of(stock),grants);
    }
    /** Sole context encoder; explicit empty grants mean no external evidence, never a missing source. */
    public static byte[] encodeEventSources(EventSourceReadContext actual) {
        Objects.requireNonNull(actual);
        var grants=actual.evidenceGrants();
        var root=StrictJson.object().put("schema",EVENT_SCHEMA).put("machine_id",actual.machineId())
                .put("state_root",actual.stateRoot().toString()).put("stock_game_root",actual.stockGameRoot().toString());
        root.set("evidence_grants",StrictJson.parse(ProjectionEvidenceCodec.encode(grants),ProjectionEvidenceCodec.MAX_BYTES));
        byte[] encoded=StrictJson.canonical(root,ProjectionEvidenceCodec.MAX_BYTES);
        EventSourceReadContext decoded=decodeEventSources(encoded);
        StrictJson.require(decoded.machineId().equals(actual.machineId())&&decoded.stateRoot().equals(actual.stateRoot())
                &&decoded.stockGameRoot().equals(actual.stockGameRoot())&&decoded.evidenceGrants().equals(grants),
                "event source context codec roundtrip changed");
        return encoded;
    }
    private static SingleWinnerSourceIndex readSourceIndexDocument(SourceIndex source)throws IOException {
        byte[] compressed=read(source.compressedRef(),MAXIMUM_INDEX_BYTES),decoded;
        try(var gzip=new GZIPInputStream(new ByteArrayInputStream(compressed))){decoded=gzip.readNBytes(MAXIMUM_INDEX_BYTES+1);}
        if(decoded.length!=source.uncompressedBytes()||decoded.length>MAXIMUM_INDEX_BYTES||!hash(decoded).equalsIgnoreCase(source.uncompressedSha256()))
            throw new IOException("bounded decompressed source index bytes/SHA mismatch");
        // The unique shared source-index contract owns this independent bounded JSON domain.
        return requireIndexMachineDomain(SingleWinnerSourceIndex.decode(decoded));
    }
    /** Recorded ancestry reference only; it is not reopened as runtime qualification. */
    static FileRef sourceIndexOriginalInput(SourceIndex source)throws IOException {
        return readSourceIndexDocument(source).inputRef();
    }
    static List<SelectedSource> readSourceIndex(SourceIndex source,String current,Clock clock)throws IOException {
        Objects.requireNonNull(current);Objects.requireNonNull(clock);
        SingleWinnerSourceIndex index=readSourceIndexDocument(Objects.requireNonNull(source));
        return index.selectedFiles().stream().map(row->new SelectedSource(row.targetRelative(),new ExactRef(
                row.sourceRef().path(),row.sourceRef().bytes(),row.sourceRef().sha256()))).toList();
    }
    /** Preserve the existing configuration machine domain even at the pure ancestry boundary. */
    private static SingleWinnerSourceIndex requireIndexMachineDomain(SingleWinnerSourceIndex index)throws IOException {
        try{machine(index.machineId());return index;}
        catch(IllegalArgumentException invalid){throw new IOException("source index machine is outside the runtime configuration domain",invalid);}
    }
    /** Complete ordered producer inventory shared by exact resolution and later physical source custody. */
    static List<SelectedSource> configuredSources(Configuration config) {
        Objects.requireNonNull(config);
        var all=new ArrayList<SelectedSource>();
        for(SourcePin pin:config.sources())all.add(pin.selected());
        for(ProducerClosure closure:config.closures())all.addAll(closure.sources());
        for(FinanceRead source:config.finance().reads())all.add(source.definition());all.add(config.finance().giftColdDefinition());
        config.activity().reads().forEach(source->all.add(source.definition()));config.activity().mutations().forEach(source->all.add(source.definition()));
        return List.copyOf(all);
    }
    /** Recorded metadata consistency only; historical source files grant no runtime qualification. */
    static void verifySources(Configuration config,List<SelectedSource> index)throws IOException {
        Objects.requireNonNull(config);List.copyOf(Objects.requireNonNull(index));
        var selected=new HashMap<String,SelectedSource>();
        for(SelectedSource source:configuredSources(config)) {
            SelectedSource prior=selected.putIfAbsent(source.targetRelative().toLowerCase(Locale.ROOT),source);
            if(prior!=null&&!same(prior.sourceRef(),source.sourceRef()))
                throw new IOException("configuration assigns different bodies to one source target");
        }
    }
    static void verifyOriginalHistory(OriginalHistory original)throws IOException {
        Path path=Path.of(original.path());SharedSourceFiles.plainAncestors(path.getParent());
        if(original.originalRef()!=null)read(original.originalRef(),16<<20);
        else if(Files.exists(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("configured history absence conflicts with an existing original; explicit exact pin required");
    }
    static void verifyStorageLease(StorageLease lease,Configuration config,RootApplicationConfiguration app)throws IOException {
        for(var ref:List.of(lease.policyRef(),lease.capacityReleaseRef(),lease.runtimeBindingRef(),lease.wholeWorkpackageCensusRef()))read(ref,16<<20);
        for(RootBudget root:lease.roots())realDirectory(Path.of(root.path()));
        for(Path path:List.of(app.artifactRoot(),app.ledger().snapshot().getParent(),Path.of(config.incidents().incidentBase()),Path.of(config.incidents().scanBase()))) {
            if(lease.roots().stream().noneMatch(root->path.startsWith(Path.of(root.path()))))throw new IOException("runtime storage path lies outside actual lease: "+path);
        }
        for(VolumeThreshold volume:lease.volumes()) {
            Path root=Path.of(volume.root());realDirectory(root);long required;
            try{required=Math.addExact(volume.minimumUsableBytes(),volume.systemGrowthReserveBytes());}catch(ArithmeticException overflow){throw new IOException("runtime volume thresholds overflow",overflow);}
            if(Files.getFileStore(root).getUsableSpace()<required)throw new IOException("actual runtime volume is below the common policy threshold");
        }
        // Current scope, reserved native allocations and issuer/binding provenance are revalidated by the central runtime guard.
    }
    static void requireCurrent(String machine,String observed,String review,String current,Clock clock,String label)throws IOException {
        Instant now=clock.instant();if(!machine.equals(current)||instant(observed).isAfter(now)||!now.isBefore(instant(review)))
            throw new IOException("current machine and unexpired "+label+" required");
    }
    static byte[] read(FileRef ref,int maximum)throws IOException {
        file(ref,maximum);byte[] bytes;
        try(var input=Files.newInputStream(Path.of(ref.path()))){bytes=input.readNBytes(Math.addExact(maximum,1));}
        if(bytes.length!=ref.bytes()||bytes.length>maximum||!hash(bytes).equalsIgnoreCase(ref.sha256()))
            throw new IOException("exact runtime input changed while reading: "+ref.path());
        return bytes;
    }
    /** One bounded DATA boundary shared by configuration loading and actual consumers. */
    static byte[] readData(DataPin data)throws IOException {
        Objects.requireNonNull(data);return read(data.originalRef(),maximumDataBytes(data.role()));
    }
    private static void realDirectory(Path path)throws IOException {
        SharedSourceFiles.plainAncestors(path);if(!Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS)||!path.toRealPath().equals(path))throw new IOException("existing canonical runtime directory required: "+path);
    }
    private static String hash(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}}
    private static boolean same(FileRef a,FileRef b){return Path.of(a.path()).equals(Path.of(b.path()))&&a.bytes()==b.bytes()&&a.sha256().equalsIgnoreCase(b.sha256());}
    private static boolean same(ExactRef a,ExactRef b){return Path.of(a.path()).equals(Path.of(b.path()))&&a.bytes()==b.bytes()&&a.sha256().equalsIgnoreCase(b.sha256());}
}
