package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Document;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Request;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.SourceRefs;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Actual request -> source document. Legacy absence never becomes a default Java option.
 * Publication uses the existing finite bootstrap authority and grants no Game permit. */
public final class RootArmyQueryHistoryConfigurationProducer {
    private RootArmyQueryHistoryConfigurationProducer(){ }
    public static final class Prepared {
        private final Document document;private final byte[] bytes;private final NativeLaunchPlan plan;
        private final List<SharedSourceFiles.Witness> originals;private final Clock clock;private boolean attempted;
        private Prepared(Document document,NativeLaunchPlan plan,List<SharedSourceFiles.Witness> originals,Clock clock){
            this.document=document;this.plan=plan;this.originals=List.copyOf(originals);this.clock=clock;
            bytes=OriginalDriverQueryHistorySettings.encode(document);
        }
        public Document document(){return document;}
        public byte[] bytes(){return bytes.clone();}
        public RootBootstrapOutputContract.Output quote(Path target)throws IOException {
            absolute(target);requireCurrent();return new RootBootstrapOutputContract.Output(
                    RootBootstrapOutputContract.Kind.ARMY_QUERY_HISTORY_CONFIGURATION,target.getFileName().toString(),bytes.length,DriverJson.sha256(bytes));
        }
        public void requireCurrent()throws IOException {
            current(document.request(),clock);for(var original:originals)unchanged(original);
            requireProducer(plan,document.sourceRefs().producerOriginal());
            var actual=readRequest(document.sourceRefs().configurationOriginal());
            if(!actual.equals(document.request()))throw new IOException("query-history request no longer matches its producer document");
            if(!Arrays.equals(bytes,OriginalDriverQueryHistorySettings.encode(document)))throw new IOException("query-history encoding changed");
        }
        public synchronized Published createNew(Path target,RootBootstrapOutputGuard authority)throws IOException {
            if(attempted)throw new IOException("query-history publication already attempted; never replay an unknown write");
            var output=quote(target);Objects.requireNonNull(authority).requirePlan(target.getParent(),List.of(output),List.of(),List.of());
            authority.requireTargets(List.of(target));attempted=true;
            var files=authority.files();var actual=files.createNew(target,bytes);files.verify(actual);
            if(!Arrays.equals(bytes,files.read(actual,OriginalDriverQueryHistorySettings.MAX_BYTES)))
                throw new IOException("actual query-history readback differs from its typed producer");
            var original=new ExactRef(actual.reference().path(),actual.reference().bytes(),actual.reference().sha256());
            var nativeBefore=SharedSourceFiles.nativeFile(target);var witness=SharedSourceFiles.observe(target);
            if(!same(original,witness.source())||!nativeBefore.equals(witness.nativeFile()))
                throw new IOException("query-history publication changed native identity");
            requireCurrent();files.verify(actual);authority.requireTargets(List.of(target));
            return new Published(original,witness,document.sourceRefs());
        }
    }
    public static final class Published {
        private final ExactRef original;private final SharedSourceFiles.Witness witness;private final SourceRefs sources;
        private Published(ExactRef original,SharedSourceFiles.Witness witness,SourceRefs sources){this.original=original;this.witness=witness;this.sources=sources;}
        public ExactRef original(){return original;}
        public SharedSourceFiles.NativeFile nativeFile(){return witness.nativeFile();}
        public OriginalDriverQueryHistorySettings.Bound readExact(NativeLaunchPlan samePlan,Clock clock)throws IOException {
            unchanged(witness);var bound=OriginalDriverQueryHistorySettings.readExact(original,sources.configurationOriginal(),sources.producerOriginal(),samePlan,clock);
            unchanged(witness);return bound;
        }
    }
    public static Prepared prepare(ExactRef actualRequest,ExactRef actualProducer,NativeLaunchPlan samePlan,Clock clock)throws IOException {
        Objects.requireNonNull(clock);Objects.requireNonNull(samePlan);requireProducer(samePlan,actualProducer);
        var originals=new ArrayList<SharedSourceFiles.Witness>();var request=decodeRequest(read(actualRequest,OriginalDriverQueryHistorySettings.MAX_BYTES,originals));
        current(request,clock);read(actualProducer,16<<20,originals);
        if(request.configuration() instanceof OriginalDriverQueryHistorySettings.LegacyCaptured legacy){
            read(legacy.originalDriver(),16<<20,originals);
            if(legacy.admissionGuard() instanceof OriginalDriverQueryHistorySettings.GuardValue callable)read(callable.original(),16<<20,originals);
        }
        var result=new Prepared(new Document(new SourceRefs(actualRequest,actualProducer),request),samePlan,originals,clock);result.requireCurrent();return result;
    }
    /** The total supplier calls this with the same settings, selector, plan and storage before creating the NT factory. */
    public static OriginalDriverQueryHistorySettings.Bound readBound(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeDomainSettings.Bound settings,NativeLaunchPlan plan,
            RootRuntimeStorageGuard storage,Clock clock)throws IOException {
        Objects.requireNonNull(inputs);selected.requireInputs(inputs);settings.requireCurrent(clock);
        if(!settings.original().equals(inputs.data(RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS)))
            throw new IOException("query-history settings are not the actual Inputs selected settings original");
        var producer=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootArmyQueryHistoryConfigurationProducer.class);
        selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,OriginalDriverQueryHistorySettings.class);
        var original=settings.configuration().queryHistorySettings();Document document=readDocument(original);
        if(!document.sourceRefs().producerOriginal().equals(producer))throw new IOException("query-history document has another actual selected producer");
        var bound=OriginalDriverQueryHistorySettings.readExact(original,document.sourceRefs().configurationOriginal(),producer,plan,clock);
        if(bound.effective() instanceof OriginalDriverQueryHistorySettings.WithStateDirectory actual)
            storage.requireDeclaredPaths(List.of(actual.stateDirectory().resolve("native-session/army-query-history-results")));
        settings.requireCurrent(clock);selected.requireCurrent();return bound;
    }
    private static Request decodeRequest(byte[] bytes)throws IOException {
        try{return OriginalDriverQueryHistorySettings.decodeRequest(bytes);}
        catch(RuntimeException invalid){throw new IOException("invalid actual query-history request",invalid);}
    }
    private static Request readRequest(ExactRef original)throws IOException {
        return decodeRequest(read(original,OriginalDriverQueryHistorySettings.MAX_BYTES,new ArrayList<>()));
    }
    private static Document readDocument(ExactRef original)throws IOException {
        try{return OriginalDriverQueryHistorySettings.decode(read(original,OriginalDriverQueryHistorySettings.MAX_BYTES,new ArrayList<>()));}
        catch(RuntimeException invalid){throw new IOException("invalid actual query-history source document",invalid);}
    }
    private static void requireProducer(NativeLaunchPlan plan,ExactRef original)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(original);
        if(!Path.of(original.path()).getFileName().toString().equals(OriginalDriverQueryHistorySettings.PRODUCER_FILE))
            throw new IOException("query-history source role requires its one actual Java producer");
        plan.sources().verify();plan.sources().requireLoadedClass(RootArmyQueryHistoryConfigurationProducer.class);
        plan.sources().requireLoadedClass(OriginalDriverQueryHistorySettings.class);
        if(plan.sources().review().completeRuntimeSources().stream().noneMatch(ref->same(original,ref)))
            throw new IOException("actual query-history producer is outside the identical complete runtime source cut");
    }
    private static void current(Request request,Clock clock)throws IOException {
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||clock.instant().isBefore(request.observedAt())
                ||!clock.instant().isBefore(request.reviewAt()))throw new IOException("query-history source request is foreign, future-dated or expired");
    }
    private static byte[] read(ExactRef expected,int maximum,List<SharedSourceFiles.Witness> witnesses)throws IOException {
        Objects.requireNonNull(expected);Path path=Path.of(expected.path());absolute(path);
        if(expected.bytes()<1||expected.bytes()>maximum)throw new IOException("query-history original exceeds its exact source lane");
        var before=SharedSourceFiles.nativeFile(path);var actual=SharedSourceFiles.observe(path);
        if(!same(expected,actual.source())||!before.equals(actual.nativeFile()))throw new IOException("query-history source changed during actual capture");
        byte[] bytes=RootRuntimeDefinitions.read(actual.source(),maximum);unchanged(actual);witnesses.add(actual);return bytes;
    }
    private static boolean same(ExactRef expected,FileRef actual){return Path.of(expected.path()).equals(Path.of(actual.path()))
            &&expected.bytes()==actual.bytes()&&expected.sha256().equalsIgnoreCase(actual.sha256());}
    private static void unchanged(SharedSourceFiles.Witness original)throws IOException {
        if(!SharedSourceFiles.nativeFile(Path.of(original.source().path())).equals(original.nativeFile()))throw new IOException("query-history original NativeFile identity changed");
        SharedSourceFiles.assertUnchanged(original);
    }
    private static void absolute(Path path)throws IOException {
        if(path==null||!path.isAbsolute()||!path.normalize().equals(path)||path.getParent()==null)
            throw new IOException("query-history source/output must have an absolute normalized file path");
    }
    public enum Mode { QUOTE, CREATE_NEW }
    /** Quote reads actual inputs. CREATE_NEW additionally consumes one independently issued bootstrap binding.
     * Arguments: mode, request triplet, producer triplet, NativePlan triplet, target, optional binding triplet. */
    public static void main(String[] args)throws Exception {
        if(args.length!=11&&args.length!=14)throw new IllegalArgumentException("query-history requires mode request-ref producer-ref NativePlan-ref target [binding-ref]");
        Mode mode=Mode.valueOf(args[0]);
        if((mode==Mode.QUOTE&&args.length!=11)||(mode==Mode.CREATE_NEW&&args.length!=14))
            throw new IllegalArgumentException("binding is mandatory only for CREATE_NEW");
        ExactRef request=argumentRef(args,1),producer=argumentRef(args,4),planOriginal=argumentRef(args,7);
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();read(planOriginal,16<<20,witnesses);
        var plan=NativeLaunchPlan.readExact(planOriginal,new NativeBridgeLaunchEvidence());
        Clock clock=Clock.systemUTC();var prepared=prepare(request,producer,plan,clock);Path target=Path.of(args[10]);
        var receipt=org.xar.ck3.control.contracts.StrictJson.object().put("schema","xar.java-army-query-history-publication/v1")
                .put("machine_id",WindowsJobProcess.currentMachineId()).put("observed_at_utc",clock.instant().toString())
                .put("configuration_origin",prepared.document().request().configuration().origin().name())
                .put("scope","IMMUTABLE_CONFIGURATION_ONLY");
        receipt.set("request",request.toJson());receipt.set("producer",producer.toJson());receipt.set("native_plan",planOriginal.toJson());
        if(mode==Mode.QUOTE){
            var quote=prepared.quote(target);receipt.put("status","QUOTED_NOT_WRITTEN");
            receipt.set("output",ControlBuild.strictMapper().valueToTree(quote));
        }else{
            ExactRef binding=argumentRef(args,11);
            try(var guard=RootBootstrapOutputGuard.readExact(new FileRef(binding.path(),binding.bytes(),binding.sha256()),clock)){
                var published=prepared.createNew(target,guard);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_GAME_ADMISSION");
                receipt.set("original",published.original().toJson());
                receipt.set("native_file",ControlBuild.strictMapper().valueToTree(published.nativeFile()));
            }
        }
        for(var original:witnesses)unchanged(original);prepared.requireCurrent();
        System.out.println(new String(org.xar.ck3.control.contracts.StrictJson.canonical(receipt,65536),java.nio.charset.StandardCharsets.UTF_8));
    }
    private static ExactRef argumentRef(String[] arguments,int offset){
        if(!arguments[offset+1].matches("[1-9][0-9]{0,7}")||!arguments[offset+2].matches("[0-9a-f]{64}"))
            throw new IllegalArgumentException("actual original requires canonical positive bytes and lowercase SHA-256");
        return new ExactRef(arguments[offset],Long.parseLong(arguments[offset+1]),arguments[offset+2]);
    }
}
