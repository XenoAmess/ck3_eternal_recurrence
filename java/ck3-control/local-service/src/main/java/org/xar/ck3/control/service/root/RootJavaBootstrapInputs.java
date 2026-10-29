package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.family.FamilyInitialData;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole;

/** Actual bounded pre-Core command-line producer. No continuity writer, Game, HTTP server or original Python is started.
 * All input values must already be real source-bound originals. A quote is not a created file or a runtime admission.
 * Four MCP files use the sole public codec/writer. Final application/data references use the sole SDK producer.
 * Missing original capture/admission/settings fail before the first output; there is no template or empty provider. */
public final class RootJavaBootstrapInputs {
    public static final String SCHEMA="xar.java-root-bootstrap-input-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=65536;
    private static final int MAXIMUM_INPUT_BYTES=1<<20;
    private RootJavaBootstrapInputs(){ }
    public enum Mode { QUOTE,CREATE_NEW }
    public record Item(Kind kind,FileRef original,String target) {
        public Item {Objects.requireNonNull(kind);file(original);absolute(target);require(!Path.of(original.path()).equals(Path.of(target)),"input originals cannot be overwritten by bootstrap");}
    }
    /** bindingRef is explicitly null only for a read-only quote. Neither mode invents an authority or renews it. */
    public record Request(String schema,String machineId,String reviewAtUtc,Mode mode,FileRef bindingRef,List<Item> inputs) {
        public Request {
            require(SCHEMA.equals(schema),"exact bootstrap input request version required");machine(machineId);instant(reviewAtUtc);Objects.requireNonNull(mode);
            require((mode==Mode.QUOTE)==(bindingRef==null),"create-new requires an actual finite output binding; quote requires explicit null");
            if(bindingRef!=null)file(bindingRef);inputs=List.copyOf(inputs);
            require(!inputs.isEmpty()&&inputs.size()<=Kind.values().length,"bounded actual typed bootstrap inputs required");
            require(inputs.stream().map(Item::kind).distinct().count()==inputs.size()&&inputs.stream().map(Item::target).distinct().count()==inputs.size(),"unique bootstrap output roles/targets required");
            long publics=inputs.stream().filter(item->isPublic(item.kind())).count();require(publics==0||publics==4,"all four actual MCP originals must share one codec/producer invocation");
            long families=inputs.stream().filter(item->isFamily(item.kind())).count();require(families==0||families==3,"all three explicit initial family DATA originals must share their typed producer invocation");
        }
    }
    /** First selected registration is derived from actual source-bound plan/profile inputs, never a raw Configuration. */
    public static final String SELECTED_REGISTRATION_SCHEMA="xar.java-root-bootstrap-selected-registration-request/v1";
    public record SelectedRegistrationRequest(String schema,String machineId,String reviewAtUtc,Mode mode,FileRef bindingRef,
            String target,ExactRef configurationProducer,List<RootSelectedRegistrationConfiguration.SourceInput> sourceInputs,
            ExactRef nativeLaunchPlan,ExactRef initialPolicy) {
        public SelectedRegistrationRequest {
            require(SELECTED_REGISTRATION_SCHEMA.equals(schema),"exact first selected-registration request schema required");
            machine(machineId);instant(reviewAtUtc);Objects.requireNonNull(mode);absolute(target);
            require(Path.of(target).getParent()!=null&&Path.of(target).getFileName()!=null,"selected registration requires an exact file target under an actual directory");
            require((mode==Mode.QUOTE)==(bindingRef==null),"selected registration quote requires explicit null binding; creation requires actual binding");
            if(bindingRef!=null)file(bindingRef);
            Objects.requireNonNull(configurationProducer);Objects.requireNonNull(nativeLaunchPlan);Objects.requireNonNull(initialPolicy);
            sourceInputs=List.copyOf(sourceInputs);
            var roles=java.util.EnumSet.noneOf(RootSelectedRegistrationConfiguration.SourceRole.class);
            for(var source:sourceInputs)require(roles.add(source.role()),"one exact source for each selected-registration role required");
            require(roles.equals(java.util.EnumSet.allOf(RootSelectedRegistrationConfiguration.SourceRole.class)),"all nine actual selected-registration source roles required");
            for(ExactRef ref:List.of(configurationProducer,nativeLaunchPlan,initialPolicy)){
                absolute(ref.path());require(ref.bytes()>0&&ref.bytes()<=4L<<20,"bounded actual selected-registration source required");
                require(!Path.of(target).equals(Path.of(ref.path())),"selected registration cannot replace any actual source");
            }
            require(nativeLaunchPlan.bytes()<=1<<20&&initialPolicy.bytes()<=1<<20,"bounded actual Native plan and initial policy required");
            for(var source:sourceInputs)require(!Path.of(target).equals(Path.of(source.originalRef().path())),"selected registration cannot replace a source input");
        }
    }
    public static byte[] encodeSelectedRegistrationRequest(SelectedRegistrationRequest request)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(request)),MAXIMUM_REQUEST_BYTES);
    }
    public static SelectedRegistrationRequest decodeSelectedRegistrationRequest(byte[] bytes)throws IOException {
        try{StrictJson.parse(bytes,MAXIMUM_REQUEST_BYTES);return ControlBuild.strictMapper().readValue(bytes,SelectedRegistrationRequest.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict first selected-registration request",invalid);}
    }
    public static final class PreparedSelectedRegistration {
        private final SelectedRegistrationRequest request;
        private final org.xar.ck3.control.platform.NativeLaunchPlan plan;
        private final RootFrozenRunProfile.FrozenRunProfile profile;
        private final RootSelectedRegistrationConfiguration.Configuration configuration;
        private final List<SharedSourceFiles.Witness> originals;
        private final SharedSourceFiles.DirectoryIdentity parent;
        private final byte[] bytes;private boolean attempted;
        private PreparedSelectedRegistration(SelectedRegistrationRequest request,org.xar.ck3.control.platform.NativeLaunchPlan plan,
                RootFrozenRunProfile.FrozenRunProfile profile,RootSelectedRegistrationConfiguration.Configuration configuration,
                List<SharedSourceFiles.Witness> originals,SharedSourceFiles.DirectoryIdentity parent) {
            this.request=request;this.plan=plan;this.profile=profile;this.configuration=configuration;
            this.originals=List.copyOf(originals);this.parent=parent;bytes=RootSelectedRegistrationConfiguration.encode(configuration);
        }
        public RootSelectedRegistrationConfiguration.Configuration configuration(){return configuration;}
        public FileRef expected(){return new FileRef(Path.of(request.target()).toString(),bytes.length,DriverJson.sha256(bytes));}
        public List<Output> quote(){var ref=expected();return List.of(new Output(Kind.SELECTED_REGISTRATION,Path.of(request.target()).getFileName().toString(),ref.bytes(),ref.sha256()));}
        public void requireCurrent(Clock clock)throws IOException {
            if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(instant(request.reviewAtUtc()))
                    ||instant(request.reviewAtUtc()).isAfter(configuration.reviewAt()))
                throw new IOException("selected registration actual machine/source review expired or extended");
            for(var original:originals){
                if(!SharedSourceFiles.nativeFile(Path.of(original.source().path())).equals(original.nativeFile()))throw new IOException("selected registration source Native identity drifted");
                SharedSourceFiles.assertUnchanged(original);
            }
            if(!parent.equals(SharedSourceFiles.nativeDirectory(Path.of(request.target()).getParent())))throw new IOException("selected registration output directory identity drifted");
            org.xar.ck3.control.platform.NativePrelaunchInputs.requireCurrent(plan,clock);profile.requireCurrent(plan,clock);
            var actual=RootSelectedRegistrationConfiguration.produce(request.configurationProducer(),request.sourceInputs(),profile,plan,clock);
            if(!configuration.equals(actual)||!Arrays.equals(bytes,RootSelectedRegistrationConfiguration.encode(actual)))throw new IOException("actual selected-registration producer changed before publication");
        }
        public synchronized Created createNew(Clock clock)throws IOException {
            if(request.mode()!=Mode.CREATE_NEW)throw new IOException("selected registration quote cannot create an original");
            if(attempted)throw new IOException("selected registration creation already attempted; preserve unknown original without replay");
            requireCurrent(clock);Path target=Path.of(request.target());
            try(var guard=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)){
                guard.requirePlan(target.getParent(),quote(),List.of(),List.of());guard.requireTargets(List.of(target));requireCurrent(clock);
                var files=guard.files();attempted=true;var created=files.createNew(target,bytes);files.verify(created);
                byte[] actual=files.read(created,RootSelectedRegistrationConfiguration.MAXIMUM_BYTES);
                if(!Arrays.equals(bytes,actual)||!configuration.equals(RootSelectedRegistrationConfiguration.decode(actual)))throw new IOException("selected registration sole-codec Native readback differs");
                // This is the actual original capture consumer, not a second selected-configuration DTO.
                org.xar.ck3.control.build.OriginalMcpCapture.decodeSelectedConfiguration(actual,request.machineId(),new FileRef(request.configurationProducer().path(),request.configurationProducer().bytes(),request.configurationProducer().sha256()));
                var observed=SharedSourceFiles.observe(target);
                if(!expected().equals(observed.source()))throw new IOException("selected registration actual output reference differs");
                requireCurrent(clock);files.verify(created);guard.requireTargets(List.of(target));
                if(files!=guard.files()||guard.accounting().completedOutputs()!=1)throw new IOException("selected registration output inventory incomplete");
                return new Created(Kind.SELECTED_REGISTRATION,observed.source(),observed.nativeFile());
            }
        }
    }
    public static PreparedSelectedRegistration prepareSelectedRegistration(FileRef originalRequest,Clock clock)throws IOException {
        Objects.requireNonNull(clock);var originals=new ArrayList<SharedSourceFiles.Witness>();
        var request=decodeSelectedRegistrationRequest(read(originalRequest,MAXIMUM_REQUEST_BYTES,originals));
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(instant(request.reviewAtUtc())))throw new IOException("selected registration request is foreign or expired");
        Path target=Path.of(request.target());SharedSourceFiles.plainAncestors(target);
        if(Files.exists(target,java.nio.file.LinkOption.NOFOLLOW_LINKS))throw new IOException("selected registration target already exists; never overwrite or replay");
        for(ExactRef ref:List.of(request.configurationProducer(),request.nativeLaunchPlan(),request.initialPolicy()))
            RootSelectedRegistrationConfiguration.read(ref,4<<20,originals);
        for(var source:request.sourceInputs())RootSelectedRegistrationConfiguration.read(source.originalRef(),4<<20,originals);
        var plan=org.xar.ck3.control.platform.NativeLaunchPlan.readExact(request.nativeLaunchPlan(),new org.xar.ck3.control.platform.NativeBridgeLaunchEvidence());
        org.xar.ck3.control.platform.NativePrelaunchInputs.requireCurrent(plan,clock);
        var run=request.sourceInputs().stream().filter(row->row.role()==RootSelectedRegistrationConfiguration.SourceRole.RUN_PROFILE).findFirst().orElseThrow().originalRef();
        var profile=RootFrozenRunProfile.readExact(run,plan,request.initialPolicy(),clock);
        var actual=RootSelectedRegistrationConfiguration.produce(request.configurationProducer(),request.sourceInputs(),profile,plan,clock);
        if(!actual.machineId().equals(request.machineId()))throw new IOException("actual selected registration producer machine differs");
        var prepared=new PreparedSelectedRegistration(request,plan,profile,actual,originals,SharedSourceFiles.nativeDirectory(target.getParent()));
        prepared.requireCurrent(clock);return prepared;
    }
    /** First publication has explicit initial DATA values; it cannot recover or replace an existing original. */
    public static final String FAMILY_SCHEMA="xar.java-root-bootstrap-family-initial-request/v1";
    public record FamilyRequest(String schema,String machineId,String reviewAtUtc,Mode mode,FileRef bindingRef,
            String familyTarget,String childMatrilinealTarget,String defaultMarriageTarget,FamilyInitialData.Documents documents) {
        public FamilyRequest {
            require(FAMILY_SCHEMA.equals(schema),"exact initial family request version required");
            machine(machineId);instant(reviewAtUtc);Objects.requireNonNull(mode);Objects.requireNonNull(documents);
            require((mode==Mode.QUOTE)==(bindingRef==null),"initial create-new requires the original output binding; quote requires explicit null");
            if(bindingRef!=null)file(bindingRef);
            new RootFamilyInitialDataProducer.Targets(Path.of(familyTarget),Path.of(childMatrilinealTarget),Path.of(defaultMarriageTarget));
        }
        RootFamilyInitialDataProducer.Targets targets(){return new RootFamilyInitialDataProducer.Targets(
                Path.of(familyTarget),Path.of(childMatrilinealTarget),Path.of(defaultMarriageTarget));}
    }
    public static final class PreparedFamily {
        private final FamilyRequest request;
        private final RootFamilyInitialDataProducer.Prepared actual;
        private PreparedFamily(FamilyRequest request){this.request=request;actual=RootFamilyInitialDataProducer.prepare(request.targets(),request.documents());}
        public List<Output> quote(){return actual.outputs().stream().map(output->new Output(Kind.valueOf(output.role().name()),
                output.target().getFileName().toString(),output.bytes(),output.sha256())).toList();}
        public RootFamilyInitialDataProducer.Published createNew(Clock clock)throws IOException {
            if(request.mode()!=Mode.CREATE_NEW)throw new IOException("an initial family quote cannot create originals");
            currentFamily(request,clock);
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)){
                authority.requirePlan(request.targets().family().getParent(),quote(),List.of(),List.of());
                RootFamilyInitialDataProducer.Published published=actual.createNew(authority);
                if(authority.accounting().completedOutputs()!=3)throw new IOException("initial family output inventory is incomplete");
                currentFamily(request,clock);return published;
            }
        }
    }
    public static byte[] encodeFamilyRequest(FamilyRequest explicit)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(explicit)),MAXIMUM_REQUEST_BYTES);
    }
    public static FamilyRequest decodeFamilyRequest(byte[] bytes)throws IOException {
        try{StrictJson.parse(bytes,MAXIMUM_REQUEST_BYTES);return ControlBuild.strictMapper().readValue(bytes,FamilyRequest.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict initial family request",invalid);}
    }
    public static PreparedFamily prepareFamily(FamilyRequest request,Clock clock)throws IOException {
        currentFamily(Objects.requireNonNull(request),clock);return new PreparedFamily(request);
    }
    private static void currentFamily(FamilyRequest request,Clock clock)throws IOException {
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())
                ||!Objects.requireNonNull(clock).instant().isBefore(instant(request.reviewAtUtc())))
            throw new IOException("initial family request is foreign or expired");
    }
    public record PreparedFile(Kind kind,String target,byte[] bytes) {
        public PreparedFile {Objects.requireNonNull(kind);absolute(target);bytes=Objects.requireNonNull(bytes).clone();require(bytes.length>0&&bytes.length<=MAXIMUM_INPUT_BYTES,"finite actual bootstrap payload required");}
        @Override public byte[] bytes(){return bytes.clone();}
        public FileRef expected(){return new FileRef(target,bytes.length,DriverJson.sha256(bytes));}
        public Output output(){return new Output(kind,Path.of(target).getFileName().toString(),bytes.length,DriverJson.sha256(bytes));}
    }
    public record Created(Kind kind,FileRef original,SharedSourceFiles.NativeFile nativeFile) {
        public Created {Objects.requireNonNull(kind);Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);}
        /** The one actual profile file also carries its explicit no-pact choice. No second DATA file is minted. */
        public List<RootRuntimeDefinitionModel.DataPin> originalDriverRunProfileData(){
            require(kind==Kind.ORIGINAL_DRIVER_RUN_PROFILE,"actual original Driver run profile output required");
            return List.of(new RootRuntimeDefinitionModel.DataPin(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,original),
                    new RootRuntimeDefinitionModel.DataPin(DataRole.EXPLICIT_FRESH_PACT,original));
        }
    }
    public static final class Prepared {
        private final Request request;private final List<PreparedFile> files;private final List<SharedSourceFiles.Witness> witnesses;
        private final RootPublicCatalogCodec.PublicCatalog publicCatalog;
        private Prepared(Request request,List<PreparedFile> files,List<SharedSourceFiles.Witness> witnesses,RootPublicCatalogCodec.PublicCatalog publicCatalog){
            this.request=request;this.files=List.copyOf(files);this.witnesses=List.copyOf(witnesses);this.publicCatalog=publicCatalog;
        }
        public List<PreparedFile> files(){return files;}
        /** Uses actual encoded bytes before the financial issuer signs its exact plan; performs no filesystem write. */
        public List<Output> quote(){return files.stream().map(PreparedFile::output).toList();}
        public List<Created> createNew(Clock clock)throws IOException {
            if(request.mode()!=Mode.CREATE_NEW)throw new IOException("a read-only bootstrap quote cannot create inputs");
            current(request,clock);unchanged();
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)){
                List<Path> targets=files.stream().map(file->Path.of(file.target())).toList();authority.requireTargets(targets);
                // Validate the entire exact signed producer plan before the first immutable output is attempted.
                var binding=RootBootstrapOutputContract.decode(read(request.bindingRef(),MAXIMUM_BYTES,new ArrayList<>()),Binding.class);
                var declaration=RootBootstrapOutputContract.decode(read(binding.declarationRef(),MAXIMUM_BYTES,new ArrayList<>()),Declaration.class);
                if(!declaration.outputs().equals(quote())||files.stream().anyMatch(file->!Path.of(file.target()).getParent().equals(Path.of(declaration.assetRoot()))))
                    throw new IOException("bootstrap command's actual typed bytes/roles/targets differ from the complete issuer-priced output plan");
                var created=new ArrayList<Created>();CheckpointFiles same=authority.files();
                if(publicCatalog!=null){
                    var targets4=new RootPublicCatalogCodec.DocumentTargets(path(Kind.MCP_CATALOG),path(Kind.MCP_ADMISSION),path(Kind.MCP_TOOLS),path(Kind.MCP_RESOURCES));
                    var actual=RootPublicCatalogCodec.writeActualDocuments(authority,targets4,publicCatalog);
                    for(var kind:List.of(Kind.MCP_CATALOG,Kind.MCP_ADMISSION,Kind.MCP_TOOLS,Kind.MCP_RESOURCES))created.add(observe(kind,same));
                    actual.files().verify();
                }
                if(files.stream().anyMatch(file->isFamily(file.kind()))){
                    var targets3=new RootFamilyInitialDataProducer.Targets(path(Kind.FAMILY_DOMAIN),path(Kind.CHILD_MATRILINEAL_DOMAIN),path(Kind.DEFAULT_MARRIAGE_DOMAIN));
                    var initial=new FamilyInitialData.Documents(
                            FamilyInitialData.decode(Slot.FAMILY,prepared(Kind.FAMILY_DOMAIN).bytes()),
                            FamilyInitialData.decode(Slot.CHILD_MATRILINEAL,prepared(Kind.CHILD_MATRILINEAL_DOMAIN).bytes()),
                            FamilyInitialData.decode(Slot.DEFAULT_MARRIAGE,prepared(Kind.DEFAULT_MARRIAGE_DOMAIN).bytes()));
                    RootFamilyInitialDataProducer.prepare(targets3,initial).createNew(authority);
                    for(var kind:List.of(Kind.FAMILY_DOMAIN,Kind.CHILD_MATRILINEAL_DOMAIN,Kind.DEFAULT_MARRIAGE_DOMAIN))created.add(observe(kind,same));
                }
                for(var file:files)if(!isPublic(file.kind())&&!isFamily(file.kind())){
                    unchanged();current(request,clock);var actual=same.createNew(Path.of(file.target()),file.bytes());same.verify(actual);
                    if(!actual.reference().equals(exact(file.expected()))||!Arrays.equals(file.bytes(),same.read(actual,MAXIMUM_INPUT_BYTES)))
                        throw new IOException("bootstrap immutable output readback differs from its unique typed producer");
                    created.add(observe(file.kind(),same));
                }
                authority.requireTargets(targets);if(authority.files()!=same)throw new IOException("bootstrap file producer changed");
                unchanged();current(request,clock);if(authority.accounting().completedOutputs()!=files.size())throw new IOException("bootstrap output inventory is incomplete");
                return List.copyOf(created);
            }
        }
        private Created observe(Kind kind,CheckpointFiles same)throws IOException {
            var expected=files.stream().filter(file->file.kind()==kind).findFirst().orElseThrow();
            var actual=same.observe(Path.of(expected.target())).orElseThrow(()->new IOException("actual immutable bootstrap output is absent"));same.verify(actual);
            if(!actual.reference().equals(exact(expected.expected())))throw new IOException("actual bootstrap output reference changed");
            var nativeFile=SharedSourceFiles.nativeFile(Path.of(expected.target()));same.verify(actual);
            return new Created(kind,expected.expected(),nativeFile);
        }
        private PreparedFile prepared(Kind kind){return files.stream().filter(file->file.kind()==kind).findFirst().orElseThrow();}
        private Path path(Kind kind){return Path.of(prepared(kind).target());}
        private void unchanged()throws IOException {for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);}
    }
    public static Request decodeRequest(byte[] original)throws IOException {
        try{StrictJson.parse(original,MAXIMUM_REQUEST_BYTES);return ControlBuild.strictMapper().readValue(original,Request.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict bootstrap input request",invalid);}
    }
    public static byte[] encodeRequest(Request explicit)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(explicit)),MAXIMUM_REQUEST_BYTES);
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        Objects.requireNonNull(request);current(request,clock);var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        var originals=new EnumMap<Kind,byte[]>(Kind.class);var canonical=new EnumMap<Kind,PreparedFile>(Kind.class);
        for(var item:request.inputs())originals.put(item.kind(),read(item.original(),MAXIMUM_INPUT_BYTES,witnesses));
        RootPublicCatalogCodec.PublicCatalog actualPublic=null;
        if(originals.containsKey(Kind.MCP_CATALOG)){
            actualPublic=RootPublicCatalogCodec.decode(new RootPublicCatalogCodec.Documents(new RawJson(originals.get(Kind.MCP_CATALOG)),
                    new RawJson(originals.get(Kind.MCP_ADMISSION)),new RawJson(originals.get(Kind.MCP_TOOLS)),new RawJson(originals.get(Kind.MCP_RESOURCES))));
            var encoded=RootPublicCatalogCodec.encode(actualPublic);
            put(canonical,request,Kind.MCP_CATALOG,encoded.catalog().bytes());put(canonical,request,Kind.MCP_ADMISSION,encoded.admission().bytes());
            put(canonical,request,Kind.MCP_TOOLS,encoded.tools().bytes());put(canonical,request,Kind.MCP_RESOURCES,encoded.resources().bytes());
        }
        for(var item:request.inputs())if(!isPublic(item.kind()))put(canonical,request,item.kind(),canonical(item.kind(),item.original(),originals.get(item.kind())));
        // Pure immutable copies through the SDK's one data producer. Native plan/package/permissions/options stay selected.
        if(originals.containsKey(Kind.RUNTIME_DEFINITIONS)){
            var original=RootRuntimeDefinitions.decodeConfiguration(originals.get(Kind.RUNTIME_DEFINITIONS));var data=new ArrayList<RootRuntimeDefinitionModel.DataPin>();
            for(var pin:original.originalData()){
                Kind mapped=kind(pin.role());var replacement=mapped==null?null:canonical.get(mapped);
                if(replacement!=null&&List.of(DataRole.MCP_CATALOG,DataRole.MCP_TOOLS,DataRole.MCP_RESOURCES).contains(pin.role()))
                    throw new IOException("actual MCP capture originals must retain the identical five-document native custody; use the real capture returned refs, not bootstrap copies");
                data.add(replacement==null?pin:new RootRuntimeDefinitionModel.DataPin(pin.role(),replacement.expected()));
            }
            FileRef application=canonical.containsKey(Kind.APPLICATION)?canonical.get(Kind.APPLICATION).expected():original.applicationRef();
            var selected=RootRuntimeDefinitions.rebindInputs(original,application,data);
            put(canonical,request,Kind.RUNTIME_DEFINITIONS,RootRuntimeDefinitions.encodeConfiguration(selected));
        }
        if(originals.containsKey(Kind.STARTUP)){
            var original=RootStartupConfiguration.fromJson(StrictJson.parse(originals.get(Kind.STARTUP),RootStartupConfiguration.MAXIMUM_BYTES));
            FileRef application=canonical.containsKey(Kind.APPLICATION)?canonical.get(Kind.APPLICATION).expected():original.application();
            FileRef definitions=canonical.containsKey(Kind.RUNTIME_DEFINITIONS)?canonical.get(Kind.RUNTIME_DEFINITIONS).expected():original.runtimeDefinitions();
            var selected=new RootStartupConfiguration(original.machineId(),original.reviewAt(),application,definitions,original.authorityId(),original.source(),original.entry(),
                    original.checkpoints(),original.ordinaryPolicy(),original.freshness(),original.batches(),original.receiptDirectory());
            put(canonical,request,Kind.STARTUP,StrictJson.canonical(selected.toJson(),RootStartupConfiguration.MAXIMUM_BYTES));
        }
        for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);current(request,clock);
        List<PreparedFile> outputs=Arrays.stream(Kind.values()).filter(canonical::containsKey).map(canonical::get).toList();
        return new Prepared(request,outputs,witnesses,actualPublic);
    }
    private static byte[] canonical(Kind kind,FileRef original,byte[] raw)throws IOException {
        return switch(kind){
            case LIFE_SETTINGS->{var value=RootAdvanceRuntimeFacts.Settings.decode(exact(original),new RawJson(raw));yield RootAdvanceRuntimeFacts.Settings.encode(value.crownQueryEnabled(),value.crownPausedQueryEnabled(),value.warDailyWatchEnabled()).bytes();}
            case ADVANCE_TIMINGS->{var value=RootAdvanceInfrastructureFactory.Timings.decode(exact(original),new RawJson(raw));yield RootAdvanceInfrastructureFactory.Timings.encode(value.maximumFrames(),value.commandTimeout(),value.advanceTimeout()).bytes();}
            case CAMPAIGN_DEADLINE->CampaignDeadlineCodec.encodeConfiguration(CampaignDeadlineCodec.decodeConfiguration(raw,OrdinaryCampaignSchedule::calendar));
            case REMAINING_DOMAIN_SETTINGS->RootRuntimeDomainSettings.encode(RootRuntimeDomainSettings.decode(raw));
            case NATIVE_DOMAIN_ORIGINALS->RootRuntimeNativeOriginals.encode(RootRuntimeNativeOriginals.decode(raw));
            case FAMILY_DOMAIN->FamilyInitialData.encode(FamilyInitialData.decode(Slot.FAMILY,raw));
            case CHILD_MATRILINEAL_DOMAIN->FamilyInitialData.encode(FamilyInitialData.decode(Slot.CHILD_MATRILINEAL,raw));
            case DEFAULT_MARRIAGE_DOMAIN->FamilyInitialData.encode(FamilyInitialData.decode(Slot.DEFAULT_MARRIAGE,raw));
            case SWAY_CONFIGURATION->RootSwaySourcesFactory.encode(RootSwaySourcesFactory.decode(raw));
            case CAPABILITY_CONFIGURATION->RootCapabilityInputsProducer.encodeConfiguration(
                    org.xar.ck3.control.application.capabilities.DynamicCapabilities.decodeConfiguration(DriverJson.object(raw,MAXIMUM_INPUT_BYTES)));
            case CAPABILITY_SESSION_PRESENTATION->RootCapabilityInputsProducer.encodeSession(
                    org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.decode(DriverJson.object(raw,MAXIMUM_INPUT_BYTES)));
            case COA_READ_LIMITS->org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.encodeLimits(
                    org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.decodeLimits(new RawJson(raw))).bytes();
            case PROFILE_DLC_LOAD,PROFILE_SETTINGS,PROFILE_TUTORIAL,PROFILE_OUTER_DESCRIPTOR,PROFILE_PRESETS,PROFILE_ENVIRONMENT,
                    PROFILE_PRODUCTION_INVENTORY,INITIAL_POLICY,NORMAL_EXIT_TARGET_BINDING,NORMAL_EXIT_SOURCE_INVENTORY,
                    NORMAL_EXIT_MANAGED_PROFILE,NORMAL_EXIT_PROFILE_PROJECTION,ORIGINAL_SETTINGS_SNAPSHOT->
                    throw new IOException("profile and normal-exit outputs require the staged actual RootProfileBootstrapInputs producer");
            case ORIGINAL_DRIVER_RUN_PROFILE->RootFrozenRunProfile.encode(RootFrozenRunProfile.decode(raw));
            case ROOT_INTENT->RootSelectedRegistrationConfiguration.encodeIntent(RootSelectedRegistrationConfiguration.decodeIntent(raw));
            case SELECTED_REGISTRATION->RootSelectedRegistrationConfiguration.encode(RootSelectedRegistrationConfiguration.decode(raw));
            case APPLICATION->StrictJson.canonical(RootApplicationConfiguration.fromJson(StrictJson.parse(raw,RootApplicationConfiguration.MAXIMUM_BYTES)).toJson(),RootApplicationConfiguration.MAXIMUM_BYTES);
            case RUNTIME_DEFINITIONS->RootRuntimeDefinitions.encodeConfiguration(RootRuntimeDefinitions.decodeConfiguration(raw));
            case STARTUP->StrictJson.canonical(RootStartupConfiguration.fromJson(StrictJson.parse(raw,RootStartupConfiguration.MAXIMUM_BYTES)).toJson(),RootStartupConfiguration.MAXIMUM_BYTES);
            case FINITE_FIRST_LIVE_REQUEST->throw new IOException("first finite request requires the sole RootFiniteFirstLiveRequestProducer typed publisher");
            case TRUSTED_EVENT_SOURCE_CONTEXT->throw new IOException("first event context requires the sole RootEventSourceContextProducer typed publisher");
            case FORMAL_RELEASE_PAYLOAD,FORMAL_RELEASE_MANIFEST->throw new IOException("formal payloads require the sole pure release producer and explicit formal Guard branch");
            case NATIVE_LAUNCH_PLAN->throw new IOException("first native plans require the sole RootNativeLaunchPlanInputs actual constructor/codec publisher");
            case RUNTIME_DEFINITIONS_PUBLICATION_REQUEST->throw new IOException("first runtime publication requests require the sole RootRuntimeDefinitionsPublicationRequestProducer actual inputs/codec");
            case RUNTIME_DEFINITIONS_SOURCE_DECLARATION->throw new IOException("first source declarations require the sole RootRuntimeDefinitionsPublisher source-declaration producer");
            case ARMY_QUERY_HISTORY_CONFIGURATION->throw new IOException("actual query-history facts use the unique RootArmyQueryHistoryConfigurationProducer request/document publisher");
            case MCP_REGISTRATION_FACTS,MCP_INVENTORY_PROOF->throw new IOException("capture proof originals are produced only by the actual OriginalMcpCapture adapter, not by the generic configuration CLI");
            case MCP_CATALOG,MCP_ADMISSION,MCP_TOOLS,MCP_RESOURCES->throw new IOException("public originals require the sole four-document producer");
        };
    }
    private static Kind kind(DataRole role){return switch(role){
        case MCP_CATALOG->Kind.MCP_CATALOG;case MCP_ADMISSION->Kind.MCP_ADMISSION;case MCP_TOOLS->Kind.MCP_TOOLS;case MCP_RESOURCES->Kind.MCP_RESOURCES;
        case LIFE_SETTINGS->Kind.LIFE_SETTINGS;case ADVANCE_TIMINGS->Kind.ADVANCE_TIMINGS;case CAMPAIGN_DEADLINE->Kind.CAMPAIGN_DEADLINE;
        case REMAINING_DOMAIN_SETTINGS->Kind.REMAINING_DOMAIN_SETTINGS;case NATIVE_DOMAIN_ORIGINALS->Kind.NATIVE_DOMAIN_ORIGINALS;
        case FAMILY_DOMAIN->Kind.FAMILY_DOMAIN;case CHILD_MATRILINEAL_DOMAIN->Kind.CHILD_MATRILINEAL_DOMAIN;case DEFAULT_MARRIAGE_DOMAIN->Kind.DEFAULT_MARRIAGE_DOMAIN;
        case ORIGINAL_DRIVER_RUN_PROFILE,EXPLICIT_FRESH_PACT->Kind.ORIGINAL_DRIVER_RUN_PROFILE;case SWAY_CONFIGURATION->Kind.SWAY_CONFIGURATION;
        case CAPABILITY_CONFIGURATION->Kind.CAPABILITY_CONFIGURATION;case CAPABILITY_SESSION_PRESENTATION->Kind.CAPABILITY_SESSION_PRESENTATION;default->null;
    };}
    private static void put(EnumMap<Kind,PreparedFile> files,Request request,Kind kind,byte[] bytes){
        String target=request.inputs().stream().filter(item->item.kind()==kind).findFirst().orElseThrow().target();files.put(kind,new PreparedFile(kind,target,bytes));
    }
    private static byte[] read(FileRef exact,int maximum,List<SharedSourceFiles.Witness> witnesses)throws IOException {
        file(exact);if(exact.bytes()>maximum)throw new IOException("bootstrap original exceeds its bounded lane");
        var before=SharedSourceFiles.observe(Path.of(exact.path()));if(!before.source().equals(exact))throw new IOException("bootstrap input differs from its exact source");
        byte[] raw;try(var input=Files.newInputStream(Path.of(exact.path()))){raw=input.readNBytes(maximum+1);}
        if(raw.length!=exact.bytes()||!DriverJson.sha256(raw).equals(exact.sha256()))throw new IOException("bootstrap original changed during complete read");
        SharedSourceFiles.assertUnchanged(before);witnesses.add(before);return raw;
    }
    private static void current(Request request,Clock clock)throws IOException {
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!Objects.requireNonNull(clock).instant().isBefore(instant(request.reviewAtUtc())))
            throw new IOException("bootstrap request is foreign or expired");
    }
    private static boolean isPublic(Kind kind){return Set.of(Kind.MCP_CATALOG,Kind.MCP_ADMISSION,Kind.MCP_TOOLS,Kind.MCP_RESOURCES).contains(kind);}
    private static boolean isFamily(Kind kind){return Set.of(Kind.FAMILY_DOMAIN,Kind.CHILD_MATRILINEAL_DOMAIN,Kind.DEFAULT_MARRIAGE_DOMAIN).contains(kind);}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static void file(FileRef ref){Objects.requireNonNull(ref);absolute(ref.path());require(ref.bytes()>0&&ref.bytes()<=MAXIMUM_INPUT_BYTES&&ref.sha256().matches("[0-9a-f]{64}"),"bounded positive exact bootstrap original required");}
    private static void absolute(String value){Path path=Path.of(Objects.requireNonNull(value));require(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized bootstrap path required");}
    private static void machine(String value){require(value!=null&&value.matches("[a-z0-9][a-z0-9-]{0,127}")&&!value.equals("unknown"),"actual bootstrap machine required");}
    private static Instant instant(String raw){Instant value=Instant.parse(raw);require(value.toString().equals(raw),"canonical UTC review required");return value;}
    private static void require(boolean condition,String reason){if(!condition)throw new IllegalArgumentException(reason);}
    /** Invoke with exactly request absolute path, canonical positive byte count and lowercase SHA-256.
     * Stdout is a bounded receipt; Root owns its actual log/output budget and observes the process exit. */
    public static void main(String[] arguments)throws Exception {
        if(arguments.length!=3||!arguments[1].matches("[1-9][0-9]{0,6}")||!arguments[2].matches("[0-9a-f]{64}"))
            throw new IllegalArgumentException("RootJavaBootstrapInputs requires request-path exact-bytes exact-sha256");
        var original=new FileRef(Path.of(arguments[0]).toString(),Long.parseLong(arguments[1]),arguments[2]);var requestWitnesses=new ArrayList<SharedSourceFiles.Witness>();
        byte[] requestBytes=read(original,MAXIMUM_REQUEST_BYTES,requestWitnesses);
        JsonNode explicit=StrictJson.parse(requestBytes,MAXIMUM_REQUEST_BYTES);
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&SELECTED_REGISTRATION_SCHEMA.equals(explicit.get("schema").textValue())){
            var request=decodeSelectedRegistrationRequest(requestBytes);Clock clock=Clock.systemUTC();
            var prepared=prepareSelectedRegistration(original,clock);
            if(request.mode()==Mode.QUOTE){
                prepared.requireCurrent(clock);emitOrdinaryQuote("SELECTED_REGISTRATION",request.machineId(),request.reviewAtUtc(),
                        prepared.quote(),List.of(Path.of(request.target())),requestWitnesses);return;
            }
            var created=prepared.createNew(clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-selected-registration-result/v1")
                    .put("machine_id",request.machineId()).put("observed_at_utc",clock.instant().toString())
                    .put("scope","IMMUTABLE_SELECTED_REGISTRATION_ONLY_NO_CAPTURE_JAVA_OR_GAME_ADMISSION")
                    .put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
            receipt.set("request_ref",exact(original).toJson());receipt.set("original_ref",exact(created.original()).toJson());
            receipt.set("native_file",ControlBuild.strictMapper().valueToTree(created.nativeFile()));
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&FAMILY_SCHEMA.equals(explicit.get("schema").textValue())){
            FamilyRequest request=decodeFamilyRequest(requestBytes);Clock clock=Clock.systemUTC();PreparedFamily prepared=prepareFamily(request,clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-family-initial-result/v1")
                    .put("machine_id",request.machineId()).put("observed_at_utc",clock.instant().toString()).put("scope","IMMUTABLE_FAMILY_DATA_ONLY");
            receipt.set("request_ref",exact(original).toJson());
            if(request.mode()==Mode.QUOTE){
                emitOrdinaryQuote("FAMILY_INITIAL_DATA",request.machineId(),request.reviewAtUtc(),prepared.quote(),request.targets().paths(),requestWitnesses);return;
            }else{
                var published=prepared.createNew(clock);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
                receipt.set("definition_inputs",ControlBuild.strictMapper().valueToTree(published.definitionInputs()));
            }
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootFiniteFirstLiveRequestProducer.SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootFiniteFirstLiveRequestProducer.decode(requestBytes);Clock clock=Clock.systemUTC();
            var prepared=RootFiniteFirstLiveRequestProducer.prepare(request,clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-finite-first-live-result/v1")
                    .put("machine_id",request.finite().machineId()).put("observed_at_utc",clock.instant().toString())
                    .put("scope","IMMUTABLE_FINITE_REQUEST_ONLY");receipt.set("request_ref",exact(original).toJson());
            if(request.mode()==Mode.QUOTE){
                emitOrdinaryQuote("FINITE_FIRST_LIVE_REQUEST",request.finite().machineId(),request.finite().reviewAt().toString(),
                        prepared.quote(),List.of(request.target()),requestWitnesses);return;
            }else{
                var created=prepared.createNew(clock);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
                receipt.set("original_ref",exact(created.original()).toJson());
                receipt.set("native_file",ControlBuild.strictMapper().valueToTree(created.nativeFile()));
            }
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootEventSourceContextProducer.SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootEventSourceContextProducer.decode(requestBytes);Clock clock=Clock.systemUTC();
            var prepared=RootEventSourceContextProducer.prepare(request,clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-event-source-context-result/v1")
                    .put("machine_id",request.machineId()).put("observed_at_utc",clock.instant().toString())
                    .put("scope","IMMUTABLE_EVENT_SOURCE_CONFIGURATION_ONLY");receipt.set("request_ref",exact(original).toJson());
            if(request.mode()==Mode.QUOTE){
                prepared.requireCurrent(clock);
                emitOrdinaryQuote("TRUSTED_EVENT_SOURCE_CONTEXT",request.machineId(),request.reviewAtUtc(),prepared.quote(),
                        List.of(Path.of(request.target())),requestWitnesses);return;
            }else{
                var created=prepared.createNew(clock);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
                receipt.set("original_ref",exact(created.original()).toJson());
                receipt.set("native_file",ControlBuild.strictMapper().valueToTree(created.nativeFile()));
            }
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootCapabilityInputsProducer.SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootCapabilityInputsProducer.decodeRequest(requestBytes);Clock clock=Clock.systemUTC();
            var prepared=RootCapabilityInputsProducer.prepare(original,clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-capability-inputs-result/v1")
                    .put("machine_id",request.machineId()).put("observed_at_utc",clock.instant().toString())
                    .put("scope","IMMUTABLE_STARTUP_CAPABILITY_CONFIGURATION_ONLY");receipt.set("request_ref",exact(original).toJson());
            if(request.mode()==Mode.QUOTE){
                emitOrdinaryQuote("CAPABILITY_INITIAL_CONFIGURATION",request.machineId(),request.reviewAtUtc(),prepared.quote(),
                        prepared.files().stream().map(file->Path.of(file.target())).toList(),requestWitnesses);return;
            }else{
                var created=prepared.createNew(clock);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
                var rows=receipt.putArray("created_outputs");
                for(var value:created){var row=rows.addObject().put("kind",value.kind().name());row.set("original_ref",exact(value.original()).toJson());
                    row.set("native_file",ControlBuild.strictMapper().valueToTree(value.nativeFile()));}
            }
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootStartupConfigurationProducer.SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootStartupConfigurationProducer.decode(requestBytes);Clock clock=Clock.systemUTC();
            var prepared=RootStartupConfigurationProducer.prepare(request,clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-startup-result/v1")
                    .put("machine_id",request.startup().machineId()).put("observed_at_utc",clock.instant().toString())
                    .put("scope","IMMUTABLE_STARTUP_ORIGINAL_ONLY");receipt.set("request_ref",exact(original).toJson());
            if(request.mode()==Mode.QUOTE){
                emitOrdinaryQuote("STARTUP",request.startup().machineId(),request.startup().reviewAt().toString(),List.of(prepared.quote()),
                        List.of(request.target()),requestWitnesses);return;
            }else{
                var published=prepared.createNew();published.readExact(clock);
                receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
                receipt.set("original_ref",exact(published.original()).toJson());
                receipt.set("native_file",ControlBuild.strictMapper().valueToTree(published.nativeFile()));
            }
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootApplicationConfigurationProducer.REQUEST_SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootApplicationConfigurationProducer.decodeRequest(requestBytes);
            byte[] receipt=RootApplicationConfigurationProducer.execute(request,Clock.systemUTC());
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.write(receipt);System.out.write(10);System.out.flush();
            if(System.out.checkError())throw new IOException("application publication receipt output failed; preserve the original publication, never retry its write");
            return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootInitialPolicyBootstrap.SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootInitialPolicyBootstrap.decode(requestBytes);Clock clock=Clock.systemUTC();
            var prepared=RootInitialPolicyBootstrap.prepare(request,clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-initial-policy-result/v1")
                    .put("machine_id",request.machineId()).put("observed_at_utc",clock.instant().toString())
                    .put("scope","IMMUTABLE_INITIAL_POLICY_ONLY");receipt.set("request_ref",exact(original).toJson());
            if(request.mode()==Mode.QUOTE){
                emitOrdinaryQuote("INITIAL_POLICY",request.machineId(),request.reviewAtUtc(),prepared.quote(),
                        List.of(Path.of(request.target())),requestWitnesses);return;
            }else{
                var created=prepared.createNew(clock);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
                receipt.set("original_ref",created.exact().toJson());
                receipt.set("native_file",ControlBuild.strictMapper().valueToTree(created.nativeFile()));
            }
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootSwayConfigurationProducer.SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootSwayConfigurationProducer.decode(requestBytes);Clock clock=Clock.systemUTC();
            var prepared=RootSwayConfigurationProducer.prepare(request,clock);
            var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-sway-initial-result/v1")
                    .put("machine_id",request.machineId()).put("observed_at_utc",clock.instant().toString())
                    .put("scope","IMMUTABLE_SWAY_CONFIGURATION_ONLY");receipt.set("request_ref",exact(original).toJson());
            if(request.mode()==Mode.QUOTE){
                emitOrdinaryQuote("SWAY_CONFIGURATION",request.machineId(),request.reviewAtUtc(),prepared.quote(),
                        List.of(Path.of(request.target())),requestWitnesses);return;
            }else{
                var created=prepared.createNew(clock);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
                receipt.set("original_ref",exact(created.original()).toJson());receipt.set("native_file",ControlBuild.strictMapper().valueToTree(created.nativeFile()));
            }
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));return;
        }
        if(explicit.isObject()&&explicit.path("schema").isTextual()&&RootFreshContinuityInputs.SCHEMA.equals(explicit.get("schema").textValue())){
            var request=RootFreshContinuityInputs.decodeRequest(requestBytes);
            byte[] receipt=RootFreshContinuityInputs.execute(request,Clock.systemUTC());
            for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
            System.out.write(receipt);System.out.write(10);System.out.flush();
            if(System.out.checkError())throw new IOException("genesis initialization receipt output failed; query the original only, never replay its write");
            return;
        }
        Request request=decodeRequest(requestBytes);Clock clock=Clock.systemUTC();Prepared prepared=prepare(request,clock);
        var receipt=StrictJson.object().put("schema","xar.java-root-bootstrap-input-result/v1").put("machine_id",WindowsJobProcess.currentMachineId())
                .put("observed_at_utc",clock.instant().toString()).put("scope","IMMUTABLE_INPUT_FILES_ONLY");receipt.set("request_ref",exact(original).toJson());
        if(request.mode()==Mode.QUOTE){
            emitOrdinaryQuote("IMMUTABLE_INPUTS",request.machineId(),request.reviewAtUtc(),prepared.quote(),
                    prepared.files().stream().map(file->Path.of(file.target())).toList(),requestWitnesses);return;
        }else{var created=prepared.createNew(clock);receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");var rows=receipt.putArray("created_outputs");
            for(var value:created){var row=rows.addObject().put("kind",value.kind().name());row.set("original_ref",exact(value.original()).toJson());row.set("native_file",ControlBuild.strictMapper().valueToTree(value.nativeFile()));}}
        for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
        System.out.println(new String(StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES),java.nio.charset.StandardCharsets.UTF_8));
    }
    /** The actual issuer consumes only this existing typed phase protocol. Request custody stays in
     * the original exact CLI input/witnesses; CREATE_NEW retains its own actual publication receipt. */
    private static void emitOrdinaryQuote(String phase,String machine,String review,List<Output> outputs,List<Path> targets,
            List<SharedSourceFiles.Witness> requestWitnesses)throws IOException {
        outputs=List.copyOf(outputs);targets=List.copyOf(targets);
        if(outputs.isEmpty()||outputs.size()!=targets.size())throw new IOException("one exact target per actual quoted output required");
        Path assetRoot=targets.getFirst().getParent();
        if(assetRoot==null)throw new IOException("actual closed output root required before quote");
        for(int index=0;index<targets.size();index++){
            Path target=targets.get(index);
            if(!target.isAbsolute()||!target.normalize().equals(target)||!assetRoot.equals(target.getParent())
                    ||!target.getFileName().toString().equals(outputs.get(index).fileName()))
                throw new IOException("actual typed quote targets do not share their exact closed output plan");
        }
        for(var witness:requestWitnesses)SharedSourceFiles.assertUnchanged(witness);
        RootBootstrapProtocol.emit(new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1",phase,machine,review,
                assetRoot.toString(),outputs,List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING"));
    }
}

