package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.Kind;

/** First publication of DATA17..21 from actual typed requests. The five existing leaf codecs and
 * Root consumers remain authoritative. Configuration custody grants no Native plan or Game admission. */
public final class RootPlanningSettingsInputsProducer {
    public static final String SCHEMA="xar.java-root-planning-settings-request/v1";
    public static final String CORE_SCHEMA="xar.java-root-core-planning-settings-request/v1";
    public static final String COA_SCHEMA="xar.java-root-coa-read-limits-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=1<<20;
    private RootPlanningSettingsInputsProducer(){ }
    public enum Mode { QUOTE,CREATE_NEW,CORE_QUOTE,CORE_CREATE_NEW,COA_QUOTE,COA_CREATE_NEW }
    public sealed interface PublicationRequest permits Request,CoreRequest,CoaLimitsRequest {
        String machineId();String observedAtUtc();String reviewAtUtc();String outputRoot();
    }
    public record Life(boolean crownQueryEnabled,boolean crownPausedQueryEnabled,boolean warDailyWatchEnabled) { }
    public record Timings(int maximumFrames,long commandTimeoutMillis,long advanceTimeoutMillis) {
        public Timings {
            // The original leaf owns both the value bounds and exact millisecond semantics.
            RootAdvanceInfrastructureFactory.Timings.encode(maximumFrames,Duration.ofMillis(commandTimeoutMillis),Duration.ofMillis(advanceTimeoutMillis));
        }
    }
    /** Every value comes from the original request. No seed, policy, paths, Game dates or extra save are inferred. */
    public record Request(String schema,String machineId,String observedAtUtc,String reviewAtUtc,String outputRoot,
            Life life,Timings timings,CampaignDeadline.Founding campaignDeadline,
            RootRuntimeDomainSettings.Configuration remainingDomainSettings,
            RootRuntimeNativeOriginals.Configuration nativeDomainOriginals) implements PublicationRequest {
        public Request {
            require(SCHEMA.equals(schema),"exact planning-settings publication request version required");
            RootRuntimeDefinitionModel.machine(machineId);absolute(Path.of(outputRoot));
            Instant observed=instant(observedAtUtc),review=instant(reviewAtUtc);
            require(observed.isBefore(review)&&Duration.between(observed,review).compareTo(Duration.ofDays(7))<=0,
                    "finite reviewed planning-settings request required");
            Objects.requireNonNull(life);Objects.requireNonNull(timings);Objects.requireNonNull(campaignDeadline);
            Objects.requireNonNull(remainingDomainSettings);Objects.requireNonNull(nativeDomainOriginals);
            require(machineId.equals(remainingDomainSettings.machineId())&&machineId.equals(nativeDomainOriginals.machineId()),
                    "all planning-settings originals require the identical machine");
            require(!observed.isBefore(instant(remainingDomainSettings.observedAtUtc()))
                    &&!review.isAfter(instant(remainingDomainSettings.reviewAtUtc()))
                    &&!observed.isBefore(instant(nativeDomainOriginals.observedAtUtc()))
                    &&!review.isAfter(instant(nativeDomainOriginals.reviewAtUtc())),
                    "publication cannot predate or outlive its explicitly configured source period");
        }
    }
    /** Independent pure DATA17..19 publication. No unrelated native-cut or normal-exit prerequisite. */
    public record CoreRequest(String schema,String machineId,String observedAtUtc,String reviewAtUtc,String outputRoot,
            Life life,Timings timings,CampaignDeadline.Founding campaignDeadline) implements PublicationRequest {
        public CoreRequest {
            require(CORE_SCHEMA.equals(schema),"exact core planning-settings request version required");
            header(machineId,observedAtUtc,reviewAtUtc,outputRoot);
            Objects.requireNonNull(life);Objects.requireNonNull(timings);Objects.requireNonNull(campaignDeadline);
        }
    }
    /** First original for the existing mandatory domain-settings CoA limits source slot. */
    public record CoaLimitsRequest(String schema,String machineId,String observedAtUtc,String reviewAtUtc,String outputRoot,
            CoaVfs.Limits limits) implements PublicationRequest {
        public CoaLimitsRequest {
            require(COA_SCHEMA.equals(schema),"exact CoA limits publication request version required");
            header(machineId,observedAtUtc,reviewAtUtc,outputRoot);Objects.requireNonNull(limits);
        }
    }
    public static byte[] encodeCoreRequest(CoreRequest request)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(request)),MAXIMUM_REQUEST_BYTES);
    }
    public static CoreRequest decodeCoreRequest(byte[] original)throws IOException {
        try{StrictJson.parse(original,MAXIMUM_REQUEST_BYTES);return ControlBuild.strictMapper().readValue(original,CoreRequest.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict core planning-settings request",invalid);}
    }
    public static byte[] encodeCoaRequest(CoaLimitsRequest request)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(request)),MAXIMUM_REQUEST_BYTES);
    }
    public static CoaLimitsRequest decodeCoaRequest(byte[] original)throws IOException {
        try{StrictJson.parse(original,MAXIMUM_REQUEST_BYTES);return ControlBuild.strictMapper().readValue(original,CoaLimitsRequest.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict CoA limits publication request",invalid);}
    }
    public static byte[] encodeRequest(Request request)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(request)),MAXIMUM_REQUEST_BYTES);
    }
    public static Request decodeRequest(byte[] original)throws IOException {
        try {
            var wire=StrictJson.parse(original,MAXIMUM_REQUEST_BYTES);
            // Preserve the existing required-null Stock field through this new outer request boundary.
            var settings=wire.get("remaining_domain_settings");
            require(settings!=null&&settings.isObject()&&settings.has("stock_read"),"explicit nullable stock_read field required");
            return ControlBuild.strictMapper().readValue(original,Request.class);
        }catch(IllegalArgumentException invalid){throw new IOException("invalid strict planning-settings publication request",invalid);}
    }
    /** Pure output construction. This produces no FileRef claiming an existing file and performs no write. */
    public static List<RootJavaBootstrapInputs.PreparedFile> encodeFiles(Request request)throws IOException {
        Objects.requireNonNull(request);Path root=Path.of(request.outputRoot());
        var files=new ArrayList<>(encodeCoreFiles(new CoreRequest(CORE_SCHEMA,request.machineId(),request.observedAtUtc(),
                request.reviewAtUtc(),request.outputRoot(),request.life(),request.timings(),request.campaignDeadline())));
        files.add(output(root,Kind.REMAINING_DOMAIN_SETTINGS,"remaining-domain-settings.json",RootRuntimeDomainSettings.encode(request.remainingDomainSettings())));
        files.add(output(root,Kind.NATIVE_DOMAIN_ORIGINALS,"native-domain-originals.json",RootRuntimeNativeOriginals.encode(request.nativeDomainOriginals())));
        for(var file:files)validateLeaf(file);return List.copyOf(files);
    }
    public static List<RootJavaBootstrapInputs.PreparedFile> encodeCoreFiles(CoreRequest request)throws IOException {
        Objects.requireNonNull(request);Path root=Path.of(request.outputRoot());var life=request.life();var timings=request.timings();
        var deadline=CampaignDeadline.configure(request.campaignDeadline(),OrdinaryCampaignSchedule::calendar,Optional.empty());
        var files=List.of(
                output(root,Kind.LIFE_SETTINGS,"life-settings.json",RootAdvanceRuntimeFacts.Settings.encode(
                        life.crownQueryEnabled(),life.crownPausedQueryEnabled(),life.warDailyWatchEnabled()).bytes()),
                output(root,Kind.ADVANCE_TIMINGS,"advance-timings.json",RootAdvanceInfrastructureFactory.Timings.encode(
                        timings.maximumFrames(),Duration.ofMillis(timings.commandTimeoutMillis()),Duration.ofMillis(timings.advanceTimeoutMillis())).bytes()),
                output(root,Kind.CAMPAIGN_DEADLINE,"campaign-deadline.json",CampaignDeadlineCodec.encodeConfiguration(deadline)));
        for(var file:files)validateLeaf(file);
        return files;
    }
    public static Prepared prepare(FileRef actualRequest,Clock clock)throws IOException {
        Objects.requireNonNull(clock);var witnesses=new LinkedHashMap<Path,SharedSourceFiles.Witness>();
        Request request=decodeRequest(read(actualRequest,MAXIMUM_REQUEST_BYTES,witnesses));current(request,clock);
        var files=encodeFiles(request);
        // Read the actual configured originals before any output. No reference, empty history or guard is fabricated.
        for(var original:request.nativeDomainOriginals().originals())read(original.original(),RootRuntimeNativeOriginals.MAXIMUM_SOURCE_BYTES,witnesses);
        var settings=request.remainingDomainSettings();
        for(var ref:settings.formalWar().originals())read(ref,RootRuntimeDomainSettings.MAXIMUM_POLICY_BYTES,witnesses);
        for(var ref:settings.normalExit().originals())read(ref,RootRuntimeDomainSettings.MAXIMUM_POLICY_BYTES,witnesses);
        var limits=settings.coaReadLimits().original();
        org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.decodeLimits(
                new RawJson(read(limits,4096,witnesses)));
        if(settings.stockRead()!=null)for(var ref:settings.stockRead().originals())read(ref,RootRuntimeDomainSettings.MAXIMUM_POLICY_BYTES,witnesses);
        var query=OriginalDriverQueryHistorySettings.decode(read(file(settings.queryHistorySettings()),OriginalDriverQueryHistorySettings.MAX_BYTES,witnesses));
        var queryRequest=OriginalDriverQueryHistorySettings.decodeRequest(read(file(query.sourceRefs().configurationOriginal()),
                OriginalDriverQueryHistorySettings.MAX_BYTES,witnesses));
        if(!queryRequest.equals(query.request())||!request.machineId().equals(queryRequest.machineId())
                ||instant(settings.observedAtUtc()).isBefore(queryRequest.observedAt())
                ||instant(settings.reviewAtUtc()).isAfter(queryRequest.reviewAt()))
            throw new IOException("planning settings differ from or outlive their actual query-history request");
        read(file(query.sourceRefs().producerOriginal()),RootRuntimeDomainSettings.MAXIMUM_POLICY_BYTES,witnesses);
        if(queryRequest.configuration() instanceof OriginalDriverQueryHistorySettings.LegacyCaptured legacy){
            read(file(legacy.originalDriver()),RootRuntimeDomainSettings.MAXIMUM_POLICY_BYTES,witnesses);
            if(legacy.admissionGuard() instanceof OriginalDriverQueryHistorySettings.GuardValue guard)
                read(file(guard.original()),RootRuntimeDomainSettings.MAXIMUM_POLICY_BYTES,witnesses);
        }
        return prepared(request,files,witnesses,clock);
    }
    public static Prepared prepareCore(FileRef actualRequest,Clock clock)throws IOException {
        Objects.requireNonNull(clock);var witnesses=new LinkedHashMap<Path,SharedSourceFiles.Witness>();
        CoreRequest request=decodeCoreRequest(read(actualRequest,MAXIMUM_REQUEST_BYTES,witnesses));current(request,clock);
        return prepared(request,encodeCoreFiles(request),witnesses,clock);
    }
    public static Prepared prepareCoa(FileRef actualRequest,Clock clock)throws IOException {
        Objects.requireNonNull(clock);var witnesses=new LinkedHashMap<Path,SharedSourceFiles.Witness>();
        CoaLimitsRequest request=decodeCoaRequest(read(actualRequest,MAXIMUM_REQUEST_BYTES,witnesses));current(request,clock);
        var file=output(Path.of(request.outputRoot()),Kind.COA_READ_LIMITS,"coa-read-limits.json",CoaVfs.encodeLimits(request.limits()).bytes());
        validateLeaf(file);return prepared(request,List.of(file),witnesses,clock);
    }
    private static Prepared prepared(PublicationRequest request,List<RootJavaBootstrapInputs.PreparedFile> files,
            LinkedHashMap<Path,SharedSourceFiles.Witness> witnesses,Clock clock)throws IOException {
        for(Path original:witnesses.keySet())if(original.startsWith(Path.of(request.outputRoot())))
            throw new IOException("first settings outputs require an independent input root; retained inputs cannot be hidden inside the priced output root");
        var prepared=new Prepared(request,files,List.copyOf(witnesses.values()),clock);prepared.requireCurrent();return prepared;
    }
    public static final class Prepared {
        private final PublicationRequest request;private final List<RootJavaBootstrapInputs.PreparedFile> files;
        private final List<SharedSourceFiles.Witness> originals;private final Clock clock;private boolean attempted;
        private Prepared(PublicationRequest request,List<RootJavaBootstrapInputs.PreparedFile> files,List<SharedSourceFiles.Witness> originals,Clock clock){
            this.request=request;this.files=List.copyOf(files);this.originals=List.copyOf(originals);this.clock=clock;
        }
        public PublicationRequest request(){return request;}
        public List<RootJavaBootstrapInputs.PreparedFile> files(){return files;}
        public List<RootBootstrapOutputContract.Output> quote()throws IOException {
            requireCurrent();return files.stream().map(RootJavaBootstrapInputs.PreparedFile::output).toList();
        }
        /** The existing issuer consumes this exact shared protocol, with no custom receipt decoder. */
        public RootBootstrapProtocol.OrdinaryQuote quoteEnvelope()throws IOException {
            String phase=switch(request){case CoreRequest ignored->"CORE_SETTINGS";case CoaLimitsRequest ignored->"COA_READ_LIMITS";case Request ignored->"PLANNER_SETTINGS";};
            return new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1",phase,request.machineId(),request.reviewAtUtc(),
                    request.outputRoot(),quote(),List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
        }
        public void requireCurrent()throws IOException {
            current(request,clock);for(var original:originals)unchanged(original);
        }
        /** One original attempt only. Failure after a CREATE_NEW begins remains a real partial/unknown write. */
        public synchronized List<RootJavaBootstrapInputs.Created> createNew(RootBootstrapOutputGuard authority)throws IOException {
            if(attempted)throw new IOException("planning-settings publication already attempted; never replay a partial or unknown write");
            var outputs=quote();Objects.requireNonNull(authority).requirePlan(Path.of(request.outputRoot()),outputs,List.of(),List.of());
            var targets=files.stream().map(value->Path.of(value.target())).toList();authority.requireTargets(targets);
            attempted=true;var created=new ArrayList<RootJavaBootstrapInputs.Created>();var same=authority.files();
            for(var file:files){
                requireCurrent();var actual=same.createNew(Path.of(file.target()),file.bytes());same.verify(actual);
                if(!actual.reference().equals(exact(file.expected()))||!Arrays.equals(file.bytes(),same.read(actual,1<<20)))
                    throw new IOException("actual planning-settings output differs from its sole leaf codec");
                var nativeBefore=SharedSourceFiles.nativeFile(Path.of(file.target()));var witness=SharedSourceFiles.observe(Path.of(file.target()));
                if(!same(file.expected(),witness.source())||!nativeBefore.equals(witness.nativeFile()))
                    throw new IOException("actual planning-settings output native identity changed");
                validateLeaf(file);same.verify(actual);
                created.add(new RootJavaBootstrapInputs.Created(file.kind(),file.expected(),witness.nativeFile()));
            }
            // The actual Root consumers read the physical originals, including their transitive source custody.
            for(var original:created)switch(original.kind()){
                case REMAINING_DOMAIN_SETTINGS->RootRuntimeDomainSettings.readExact(original.original(),clock).requireCurrent(clock);
                case NATIVE_DOMAIN_ORIGINALS->RootRuntimeNativeOriginals.readExact(original.original(),clock).requireCurrent(clock);
                default->{ }
            }
            requireCurrent();authority.requireTargets(targets);
            if(authority.files()!=same||authority.accounting().completedOutputs()!=files.size())
                throw new IOException("planning-settings immutable inventory is incomplete or changed");
            return List.copyOf(created);
        }
    }
    private static RootJavaBootstrapInputs.PreparedFile output(Path root,Kind kind,String name,byte[] bytes){
        return new RootJavaBootstrapInputs.PreparedFile(kind,root.resolve(name).toString(),bytes);
    }
    private static void validateLeaf(RootJavaBootstrapInputs.PreparedFile file)throws IOException {
        byte[] raw=file.bytes();switch(file.kind()){
            case LIFE_SETTINGS->RootAdvanceRuntimeFacts.Settings.decode(exact(file.expected()),new RawJson(raw));
            case ADVANCE_TIMINGS->RootAdvanceInfrastructureFactory.Timings.decode(exact(file.expected()),new RawJson(raw));
            case CAMPAIGN_DEADLINE->CampaignDeadlineCodec.decodeConfiguration(raw,OrdinaryCampaignSchedule::calendar);
            case REMAINING_DOMAIN_SETTINGS->RootRuntimeDomainSettings.decode(raw);
            case NATIVE_DOMAIN_ORIGINALS->RootRuntimeNativeOriginals.decode(raw);
            case COA_READ_LIMITS->CoaVfs.decodeLimits(new RawJson(raw));
            default->throw new IOException("unsupported planning-settings output role");
        }
    }
    private static byte[] read(FileRef expected,int maximum,LinkedHashMap<Path,SharedSourceFiles.Witness> witnesses)throws IOException {
        Objects.requireNonNull(expected);Path path=Path.of(expected.path());absolute(path);
        if(expected.bytes()<0||expected.bytes()>maximum)throw new IOException("planning-settings source exceeds its bounded exact input lane");
        var previous=witnesses.get(path);
        if(previous!=null&&!same(expected,previous.source()))throw new IOException("one planning-settings source path has conflicting exact refs");
        var nativeBefore=SharedSourceFiles.nativeFile(path);var captured=SharedSourceFiles.observe(path);
        if(!same(expected,captured.source())||!nativeBefore.equals(captured.nativeFile()))
            throw new IOException("actual planning-settings source differs from its request pin");
        // The immutable original launch-settings snapshot may be empty; other typed originals retain their own positive bounds.
        byte[] bytes;try(var input=Files.newInputStream(path)){bytes=input.readNBytes(Math.addExact(maximum,1));}
        if(bytes.length!=expected.bytes()||bytes.length>maximum||!DriverJson.sha256(bytes).equals(expected.sha256()))
            throw new IOException("planning-settings actual complete source bytes differ from their exact pin");
        unchanged(captured);witnesses.putIfAbsent(path,captured);return bytes;
    }
    private static void unchanged(SharedSourceFiles.Witness witness)throws IOException {
        if(!SharedSourceFiles.nativeFile(Path.of(witness.source().path())).equals(witness.nativeFile()))
            throw new IOException("planning-settings original native identity changed");
        SharedSourceFiles.assertUnchanged(witness);
    }
    private static void current(PublicationRequest request,Clock clock)throws IOException {
        Instant now=clock.instant();if(!request.machineId().equals(WindowsJobProcess.currentMachineId())
                ||now.isBefore(instant(request.observedAtUtc()))||!now.isBefore(instant(request.reviewAtUtc())))
            throw new IOException("planning-settings publication request is foreign, future-dated or expired");
    }
    private static FileRef file(ExactRef exact){return new FileRef(exact.path(),exact.bytes(),exact.sha256());}
    private static ExactRef exact(FileRef file){return new ExactRef(file.path(),file.bytes(),file.sha256());}
    private static boolean same(FileRef left,FileRef right){return Path.of(left.path()).equals(Path.of(right.path()))
            &&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());}
    private static Instant instant(String text){Instant value=Instant.parse(text);require(value.toString().equals(text),"canonical UTC settings time required");return value;}
    private static void header(String machine,String observedAt,String reviewAt,String outputRoot){
        RootRuntimeDefinitionModel.machine(machine);absolute(Path.of(outputRoot));Instant observed=instant(observedAt),review=instant(reviewAt);
        require(observed.isBefore(review)&&Duration.between(observed,review).compareTo(Duration.ofDays(7))<=0,"finite reviewed settings request required");
    }
    private static void absolute(Path path){require(path.isAbsolute()&&path.normalize().equals(path),"normalized absolute settings path required");}
    private static void require(boolean value,String reason){if(!value)throw new IllegalArgumentException(reason);}
    /** Existing managed child entry: mode, actual request triplet, and only for CREATE_NEW actual binding triplet. */
    public static void main(String[] args)throws Exception {
        if(args.length!=4&&args.length!=7)throw new IllegalArgumentException("planning settings require mode request-ref [binding-ref]");
        Mode mode=Mode.valueOf(args[0]);boolean create=mode==Mode.CREATE_NEW||mode==Mode.CORE_CREATE_NEW||mode==Mode.COA_CREATE_NEW;
        if((!create&&args.length!=4)||(create&&args.length!=7))
            throw new IllegalArgumentException("planning-settings CREATE_NEW alone requires an actual independent output binding");
        FileRef request=argument(args,1);Clock clock=Clock.systemUTC();var prepared=switch(mode){
            case QUOTE,CREATE_NEW->prepare(request,clock);
            case CORE_QUOTE,CORE_CREATE_NEW->prepareCore(request,clock);
            case COA_QUOTE,COA_CREATE_NEW->prepareCoa(request,clock);
        };
        if(!create){RootBootstrapProtocol.emit(prepared.quoteEnvelope());return;}
        var receipt=StrictJson.object().put("schema","xar.java-root-planning-settings-publication/v1")
                .put("machine_id",WindowsJobProcess.currentMachineId()).put("observed_at_utc",clock.instant().toString())
                .put("scope","IMMUTABLE_CONFIGURATION_ONLY");receipt.set("request_ref",exact(request).toJson());
        try(var guard=RootBootstrapOutputGuard.readExact(argument(args,4),clock)){
            var created=prepared.createNew(guard);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
            receipt.set("outputs",ControlBuild.strictMapper().valueToTree(created));
        }
        prepared.requireCurrent();System.out.println(new String(StrictJson.canonical(receipt,65536),StandardCharsets.UTF_8));
    }
    private static FileRef argument(String[] args,int offset){
        require(args[offset+1].matches("[1-9][0-9]{0,7}")&&args[offset+2].matches("[0-9a-f]{64}"),"exact canonical request/binding byte count and SHA-256 required");
        return new FileRef(args[offset],Long.parseLong(args[offset+1]),args[offset+2]);
    }
}
