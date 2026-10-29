package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeStorageGeometry;
import org.xar.ck3.control.build.FormalReleaseProducer;
import org.xar.ck3.control.build.FormalReleaseGit;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.service.root.RootProfileBootstrapInputs.Created;
import org.xar.ck3.control.service.root.RootProfileBootstrapInputs.Prepared;

/** Finite interactive Java entry: quote real bytes, receive an actual independent issuer binding, create and read back.
 * Each following quote uses only actual completed originals. This process never signs capacity or launches a Game. */
public final class RootProfileBootstrapCommand {
    private RootProfileBootstrapCommand(){ }
    public enum Mode { PROFILE,EXPLICIT_SAVED_PROFILE,EXPLICIT_FIXTURE_PROFILE,FORMAL_RELEASE,ORIGINAL_DRIVER_RUN_PROFILE,NORMAL_EXIT,INITIAL_POLICY,INITIAL_FIXTURE_POLICY,INITIAL_SAVED_NATIVE_POLICY,ISSUER_DECLARE,ISSUER_CENSUS,ISSUER_BINDING,ISSUER_FILE_REPLY,RUNTIME_CENSUS }
    /** Issuer metadata only. Limits are explicit Root choices; this request grants no capacity. */
    public record IssuerDeclarationRequest(String schema,String machineId,String reviewAtUtc,String windowId,
            FileRef actualPhaseQuote,String controlRoot,String target,long assetMaximumChargedBytes,
            long controlMaximumChargedBytes,long maximumSingleWriteBytes,int maximumEntries) {
        public IssuerDeclarationRequest {
            common(schema,"xar.java-root-bootstrap-issuer-declaration-request/v1",machineId,reviewAtUtc);
            Objects.requireNonNull(actualPhaseQuote);absolute(actualPhaseQuote.path());absolute(controlRoot);absolute(target);
            StrictJson.require(actualPhaseQuote.bytes()>0&&actualPhaseQuote.bytes()<=RootBootstrapProtocol.FRAME_BYTES,
                    "bounded actual producer phase quote required");
            StrictJson.text(windowId);
        }
    }
    public record IssuerCensusRequest(String schema,String machineId,String reviewAtUtc,FileRef declaration,String target) {
        public IssuerCensusRequest {
            common(schema,"xar.java-root-bootstrap-issuer-census-request/v1",machineId,reviewAtUtc);
            Objects.requireNonNull(declaration);absolute(declaration.path());absolute(target);
        }
    }
    /** Uses the existing runtime-storage declaration and usage model; grants no financial authority. */
    public record RuntimeCensusRequest(String schema,String machineId,String reviewAtUtc,FileRef declaration,
            RootRuntimeStorageContract.ExistingUsage existingWorkpackage,String target) {
        public RuntimeCensusRequest {
            common(schema,"xar.java-root-runtime-census-bootstrap/v1",machineId,reviewAtUtc);
            Objects.requireNonNull(declaration);Objects.requireNonNull(existingWorkpackage);
            absolute(declaration.path());absolute(target);
            StrictJson.require(declaration.bytes()>0&&declaration.bytes()<=RootRuntimeStorageContract.MAXIMUM_BYTES
                    &&existingWorkpackage.evidenceRef().bytes()>0
                    &&existingWorkpackage.evidenceRef().bytes()<=RootRuntimeStorageContract.MAXIMUM_BYTES,
                    "bounded exact runtime declaration and existing-usage evidence required");
        }
    }
    public record RuntimeCensusPublication(IssuerPublication publication,RootRuntimeStorageContract.WholeCensus census) {
        public RuntimeCensusPublication {Objects.requireNonNull(publication);Objects.requireNonNull(census);}
    }
    /** The independently issued exact CapacityRelease is an input, never constructed by this adapter. */
    public record IssuerBindingRequest(String schema,String machineId,String reviewAtUtc,FileRef capacityRelease,String target) {
        public IssuerBindingRequest {
            common(schema,"xar.java-root-bootstrap-issuer-binding-request/v1",machineId,reviewAtUtc);
            Objects.requireNonNull(capacityRelease);absolute(capacityRelease.path());absolute(target);
        }
    }
    /** Publishes only an envelope for a separately issued actual binding, priced by that same Guard. */
    public record IssuerFileReplyRequest(String schema,String machineId,String reviewAtUtc,FileRef channel,
            int phaseIndex,FileRef actualPhaseQuote,FileRef binding) {
        public IssuerFileReplyRequest {
            common(schema,"xar.java-root-bootstrap-issuer-file-reply-request/v1",machineId,reviewAtUtc);
            for(FileRef ref:List.of(channel,actualPhaseQuote,binding)){Objects.requireNonNull(ref);absolute(ref.path());}
            StrictJson.require(channel.bytes()>0&&channel.bytes()<=65536&&actualPhaseQuote.bytes()>0
                    &&actualPhaseQuote.bytes()<=RootBootstrapProtocol.FRAME_BYTES&&binding.bytes()>0
                    &&binding.bytes()<=RootBootstrapOutputContract.FORMAL_MAXIMUM_AUTHORITY_BYTES&&phaseIndex>=0&&phaseIndex<4,
                    "bounded exact file reply channel/phase/quote/binding required");
        }
    }
    public record IssuerPublication(FileRef original,SharedSourceFiles.NativeFile nativeFile) {
        public IssuerPublication {Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);}
    }
    public record IssuerDeclarationPublication(IssuerPublication declaration,NativeStorageGeometry.Volume assetGeometry,
            NativeStorageGeometry.Volume controlGeometry) {
        public IssuerDeclarationPublication {Objects.requireNonNull(declaration);Objects.requireNonNull(assetGeometry);Objects.requireNonNull(controlGeometry);}
    }
    public record IssuerBindingPublication(IssuerPublication binding,RootBootstrapOutputGuard.Accounting actualAccounting) {
        public IssuerBindingPublication {Objects.requireNonNull(binding);Objects.requireNonNull(actualAccounting);}
    }
    public record OriginalDriverRequest(String schema,String machineId,String reviewAtUtc,FileRef producerRequest,String target) {
        public OriginalDriverRequest {
            common(schema,"xar.java-root-original-driver-bootstrap/v1",machineId,reviewAtUtc);Objects.requireNonNull(producerRequest);absolute(target);
            StrictJson.require(producerRequest.bytes()>0&&producerRequest.bytes()<=RootOriginalDriverRunProfileProducer.MAXIMUM_REQUEST_BYTES,"bounded exact typed driver producer request required");
        }
    }
    public record FormalReleaseRequest(String schema,String machineId,String reviewAtUtc,FileRef producerRequest,FormalReleaseGit.Execution execution) {
        public FormalReleaseRequest {
            common(schema,"xar.java-root-formal-release-bootstrap/v1",machineId,reviewAtUtc);Objects.requireNonNull(producerRequest);Objects.requireNonNull(execution);
            absolute(producerRequest.path());StrictJson.require(producerRequest.bytes()>0&&producerRequest.bytes()<=65536,"bounded exact formal producer request required");
            StrictJson.require(machineId.equals(execution.machineId())&&!Instant.parse(reviewAtUtc).isAfter(Instant.parse(execution.reviewAtUtc())),
                    "formal bootstrap machine/review must fit its separate Git execution authority");
        }
    }
    public record ProfileRequest(String schema,String machineId,String reviewAtUtc,FileRef producerRequest,String productionInventoryTarget) {
        public ProfileRequest {common(schema,"xar.java-root-profile-bootstrap/v1",machineId,reviewAtUtc);Objects.requireNonNull(producerRequest);absolute(productionInventoryTarget);}
    }
    public record ExplicitProfileRequest(String schema,String machineId,String reviewAtUtc,FileRef producerRequest,String environmentTarget) {
        public ExplicitProfileRequest {
            common(schema,"xar.java-root-explicit-profile-bootstrap/v1",machineId,reviewAtUtc);
            Objects.requireNonNull(producerRequest);absolute(producerRequest.path());absolute(environmentTarget);
            StrictJson.require(producerRequest.bytes()>0&&producerRequest.bytes()<=NativeRunProfileManifest.MAXIMUM_BYTES,
                    "bounded exact explicit profile producer request required");
            StrictJson.require(Path.of(environmentTarget).getFileName().toString().equals(NativeRunProfileProducer.ENVIRONMENT_NAME),
                    "explicit ENV target requires the sole producer filename");
        }
    }
    public record NormalExitRequest(String schema,String machineId,String reviewAtUtc,ExactRef nativePlan,FileRef productionInventory,
            String guardTarget,String managedProfileTarget,String stockGameRoot) {
        public NormalExitRequest {common(schema,"xar.java-root-normal-exit-bootstrap/v1",machineId,reviewAtUtc);Objects.requireNonNull(nativePlan);
            Objects.requireNonNull(productionInventory);for(String path:List.of(guardTarget,managedProfileTarget,stockGameRoot))absolute(path);}
    }
    public record PolicyRequest(String schema,String machineId,String reviewAtUtc,FileRef actualEnvironment,
            InitialEpisodePolicy.Lifecycle lifecycle,InitialEpisodePolicy.FreshPact fresh,String target) {
        public PolicyRequest {common(schema,"xar.java-root-initial-policy-bootstrap/v1",machineId,reviewAtUtc);Objects.requireNonNull(actualEnvironment);
            Objects.requireNonNull(lifecycle);Objects.requireNonNull(fresh);absolute(target);}
    }
    public record FixturePolicyRequest(String schema,String machineId,String reviewAtUtc,FileRef actualEnvironment,
            ExactRef fixturePolicy,String stateDirectory,String profileDirectory,String target) {
        public FixturePolicyRequest {
            common(schema,"xar.java-root-initial-fixture-policy-bootstrap/v1",machineId,reviewAtUtc);
            Objects.requireNonNull(actualEnvironment);Objects.requireNonNull(fixturePolicy);
            for(String path:List.of(stateDirectory,profileDirectory,target))absolute(path);
            StrictJson.require(fixturePolicy.bytes()>0&&fixturePolicy.bytes()<=1<<20,"bounded actual fixture policy original required");
        }
    }
    public record SavedNativePolicyRequest(String schema,String machineId,String reviewAtUtc,FileRef actualEnvironment,
            FileRef actualSave,ExactRef nativeLaunchPlan,String target) {
        public SavedNativePolicyRequest {
            common(schema,"xar.java-root-initial-saved-native-policy-bootstrap/v1",machineId,reviewAtUtc);
            Objects.requireNonNull(actualEnvironment);Objects.requireNonNull(actualSave);Objects.requireNonNull(nativeLaunchPlan);
            absolute(actualEnvironment.path());absolute(actualSave.path());absolute(nativeLaunchPlan.path());absolute(target);
            StrictJson.require(actualSave.path().endsWith(".ck3")&&nativeLaunchPlan.bytes()>0&&nativeLaunchPlan.bytes()<=1<<20,
                    "exact Saved original and bounded actual Native plan required");
        }
    }
    public static void main(String[] args){
        try{
            if(args.length!=4&&args.length!=8)throw new IOException("MODE REQUEST_PATH BYTES SHA [FILE_REPLY CHANNEL_PATH BYTES SHA]");
            var mode=Mode.valueOf(args[0]);var original=new FileRef(Path.of(args[1]).toAbsolutePath().normalize().toString(),Long.parseLong(args[2]),args[3]);
            var requestOriginal=SharedSourceFiles.observe(Path.of(original.path()));
            if(!requestOriginal.source().equals(original))throw new IOException("bootstrap request original differs from its exact command-line source");
            Clock clock=Clock.systemUTC();
            RootBootstrapFileReply replies=null;
            if(args.length==8){
                if(!args[4].equals("FILE_REPLY"))throw new IOException("only the explicit FILE_REPLY transport suffix is accepted");
                long bytes=Long.parseLong(args[6]);
                if(!Long.toString(bytes).equals(args[6]))throw new IOException("canonical channel byte count required");
                var channel=new FileRef(args[5],bytes,args[7]);
                replies=RootBootstrapFileReply.open(channel,mode,requestOriginal,clock);
            }
            switch(mode){
                case ISSUER_DECLARE->{
                    var request=read(original,IssuerDeclarationRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var result=declareOutput(request,clock);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    emit("BOOTSTRAP_DECLARATION_CREATED_NO_CAPACITY_OR_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(result));
                }
                case ISSUER_CENSUS->{
                    var request=read(original,IssuerCensusRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var result=observeOutputCensus(request,clock);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    emit("BOOTSTRAP_CENSUS_CREATED_NO_CAPACITY_OR_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(result));
                }
                case RUNTIME_CENSUS->{
                    var request=read(original,RuntimeCensusRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var result=observeRuntimeCensus(request,clock);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var receipt=StrictJson.object().put("census_status",result.census().status());
                    receipt.set("publication",ControlBuild.strictMapper().valueToTree(result.publication()));
                    emit("RUNTIME_STORAGE_CENSUS_CREATED_NO_CAPACITY_OR_GAME_ADMISSION",receipt);
                }
                case ISSUER_BINDING->{
                    var request=read(original,IssuerBindingRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var result=bindIssuedCapacity(request,clock);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    emit("BOOTSTRAP_BINDING_CREATED_AND_READ_BACK_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(result));
                }
                case ISSUER_FILE_REPLY->{
                    var request=read(original,IssuerFileReplyRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var result=publishIssuedFileReply(request,clock);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    emit("BOOTSTRAP_FILE_REPLY_CREATED_AND_READ_BACK_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(result));
                }
                case ORIGINAL_DRIVER_RUN_PROFILE->{
                    var request=read(original,OriginalDriverRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var actual=RootOriginalDriverRunProfileProducer.prepare(request.producerRequest(),Path.of(request.target()),clock);
                    Created created=phase(replies,"ORIGINAL_DRIVER_RUN_PROFILE",RootProfileBootstrapInputs.originalDriverRunProfile(actual),
                            request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    actual.verifyCreated();
                    emit("ORIGINAL_DRIVER_RUN_PROFILE_CREATED_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(created));
                }
                case FORMAL_RELEASE->{
                    var request=read(original,FormalReleaseRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var producerOriginal=SharedSourceFiles.observe(Path.of(request.producerRequest().path()));
                    if(!producerOriginal.source().equals(request.producerRequest()))throw new IOException("formal producer request exact original changed");
                    var source=FormalReleaseProducer.readRequest(request.producerRequest());
                    if(!source.machineId().equals(request.machineId())||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(source.reviewAtUtc()))
                            ||!source.repository().equals(request.execution().repository()))
                        throw new IOException("formal bootstrap machine/review/repository differs from its sole producer/Git execution inputs");
                    try(var git=FormalReleaseGit.open(request.execution())){
                        var actual=FormalReleaseProducer.prepare(source,git,clock);SharedSourceFiles.assertUnchanged(producerOriginal);actual.verifyOriginals();
                        var created=phase(replies,"FORMAL_RELEASE_PAYLOAD_AND_MANIFEST",RootProfileBootstrapInputs.formalRelease(actual),
                                request.reviewAtUtc(),clock,requestOriginal,producerOriginal);
                        actual.verifyOriginals();SharedSourceFiles.assertUnchanged(producerOriginal);
                        emit("FORMAL_RELEASE_STAGING_CREATED_NO_UPLOAD_OR_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(created));
                    }
                }
                case PROFILE->{var request=read(original,ProfileRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var actual=NativeRunProfileProducer.prepare(NativeRunProfileProducer.readRequest(request.producerRequest()),clock);
                    Created inventory=phase(replies,"PROFILE_PRODUCTION_INVENTORY",RootProfileBootstrapInputs.productionInventory(actual,Path.of(request.productionInventoryTarget())),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    phase(replies,"PROFILE_ASSETS",RootProfileBootstrapInputs.assets(actual,inventory.original()),request.reviewAtUtc(),clock,requestOriginal);
                    var environment=phase(replies,"PROFILE_ENVIRONMENT",RootProfileBootstrapInputs.environment(actual,inventory.original(),clock),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    emit("PROFILE_INPUTS_CREATED_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(environment));}
                case EXPLICIT_SAVED_PROFILE,EXPLICIT_FIXTURE_PROFILE->{
                    var request=read(original,ExplicitProfileRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var producerOriginal=SharedSourceFiles.observe(Path.of(request.producerRequest().path()));
                    if(!producerOriginal.source().equals(request.producerRequest()))throw new IOException("explicit producer request exact original changed");
                    var source=NativeRunProfileProducer.readExplicitRequest(request.producerRequest());
                    if(!source.machineId().equals(request.machineId())||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(source.reviewAtUtc())))
                        throw new IOException("explicit bootstrap machine/review differs from its sole producer request");
                    requireExplicitMode(mode,source);
                    var actual=mode==Mode.EXPLICIT_SAVED_PROFILE?NativeRunProfileProducer.prepareSaved(source,clock)
                            :NativeRunProfileProducer.prepareFixture(source,clock);
                    SharedSourceFiles.assertUnchanged(producerOriginal);
                    Created environment=phase(replies,mode.name()+"_ENVIRONMENT",
                            RootProfileBootstrapInputs.explicitEnvironment(actual,request.producerRequest(),Path.of(request.environmentTarget()),clock),
                            request.reviewAtUtc(),clock,requestOriginal,producerOriginal).getFirst();
                    actual.verifyOriginals();var accepted=NativeRunProfileProducer.readEnvironmentVerified(environment.original());
                    if(!(accepted instanceof NativeRunProfileManifest.ExplicitManifest explicit)||!explicit.request().equals(source)
                            ||!explicit.profile().equals(actual.profile())||!explicit.profileAssets().equals(actual.profileAssets()))
                        throw new IOException("actual ENV readback differs from the identical explicit profile preparation");
                    SharedSourceFiles.assertUnchanged(producerOriginal);actual.verifyOriginals();
                    emit("EXPLICIT_PROFILE_ENV_CREATED_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(environment));
                }
                case NORMAL_EXIT->{var request=read(original,NormalExitRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    Created snapshot=phase(replies,"ORIGINAL_SETTINGS_SNAPSHOT",RootProfileBootstrapInputs.originalSettings(request.nativePlan()),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    var actual=RootProfileBootstrapInputs.normalExit(request.nativePlan(),snapshot.exact(),Path.of(request.guardTarget()));
                    Created guard=phase(replies,"NORMAL_EXIT_TARGET_BINDING",actual.targetBinding(),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    var outputs=phase(replies,"NORMAL_EXIT_INVENTORY_AND_PROJECTION",actual.inventory(guard,request.productionInventory(),Path.of(request.stockGameRoot())),request.reviewAtUtc(),clock,requestOriginal);
                    Created inventory=outputs.stream().filter(row->row.kind()==RootBootstrapOutputContract.Kind.NORMAL_EXIT_SOURCE_INVENTORY).findFirst().orElseThrow();
                    Created profile=phase(replies,"NORMAL_EXIT_MANAGED_PROFILE",actual.managedProfile(guard,inventory,Path.of(request.managedProfileTarget())),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    emit("NORMAL_EXIT_ORIGINALS_CREATED_NO_MANAGED_ADMISSION",ControlBuild.strictMapper().valueToTree(actual.input(inventory,profile)));}
                case INITIAL_POLICY->{var request=read(original,PolicyRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    Created policy=phase(replies,"INITIAL_POLICY",RootProfileBootstrapInputs.initialPolicy(request.actualEnvironment(),request.lifecycle(),request.fresh(),Path.of(request.target())),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    var accepted=InitialEpisodePolicy.readExact(policy.exact(),request.actualEnvironment());accepted.verify();
                    emit("INITIAL_POLICY_CREATED_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(policy));}
                case INITIAL_FIXTURE_POLICY->{var request=read(original,FixturePolicyRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var fixture=PreparedFixture.prepare(request.fixturePolicy(),Path.of(request.stateDirectory()),Path.of(request.profileDirectory()),"native_campaign");
                    Created policy=phase(replies,"INITIAL_FIXTURE_POLICY",RootProfileBootstrapInputs.initialFixturePolicy(request.actualEnvironment(),fixture,Path.of(request.target())),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    var accepted=InitialEpisodePolicy.readExactFixture(policy.exact(),request.actualEnvironment(),fixture);accepted.verify();
                    emit("INITIAL_FIXTURE_POLICY_CREATED_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(policy));}
                case INITIAL_SAVED_NATIVE_POLICY->{var request=read(original,SavedNativePolicyRequest.class);current(request.machineId(),request.reviewAtUtc(),clock,requestOriginal);
                    var plan=org.xar.ck3.control.platform.NativeLaunchPlan.readExact(request.nativeLaunchPlan(),new org.xar.ck3.control.platform.NativeBridgeLaunchEvidence());
                    if(!(plan.load() instanceof org.xar.ck3.control.platform.NativeLaunchPlan.SavedGame saved)
                            ||!saved.save().equals(request.actualSave())||!plan.preparedProfile().environmentManifest().equals(request.actualEnvironment())
                            ||!plan.sources().review().machineId().equals(request.machineId())||Instant.parse(request.reviewAtUtc()).isAfter(plan.deadline()))
                        throw new IOException("explicit Saved policy request differs from its actual Native plan, SAVE, environment or machine");
                    plan.sources().verify();plan.preparedProfile().verify(plan);
                    Created policy=phase(replies,"INITIAL_SAVED_NATIVE_POLICY",RootProfileBootstrapInputs.initialSavedNativePolicy(request.actualEnvironment(),request.actualSave(),request.nativeLaunchPlan(),Path.of(request.target())),request.reviewAtUtc(),clock,requestOriginal).getFirst();
                    var accepted=InitialEpisodePolicy.readExactSaved(policy.exact(),plan);accepted.requireSavedProjection(plan);accepted.verify();
                    plan.sources().verify();plan.preparedProfile().verify(plan);
                    emit("INITIAL_SAVED_NATIVE_POLICY_CREATED_NO_GAME_ADMISSION",ControlBuild.strictMapper().valueToTree(policy));}
            }
        }catch(Exception failure){System.err.println("BOOTSTRAP_UNAVAILABLE: "+failure.getClass().getSimpleName()+": "+failure.getMessage());System.exit(2);}
    }
    /** Reuses the original phase Quote contract and actual Native geometry; no generic schema aliases are accepted. */
    public static IssuerDeclarationPublication declareOutput(IssuerDeclarationRequest request,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);
        var quoteOriginal=SharedSourceFiles.observe(Path.of(request.actualPhaseQuote().path()));
        if(!quoteOriginal.source().equals(request.actualPhaseQuote()))throw new IOException("issuer phase quote original differs");
        byte[] wire=RootRuntimeDefinitions.read(request.actualPhaseQuote(),RootBootstrapProtocol.FRAME_BYTES);
        var quote=RootBootstrapProtocol.line(wire,RootBootstrapProtocol.Quote.class);
        if(!quote.machineId().equals(request.machineId())||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(quote.reviewAtUtc())))
            throw new IOException("issuer declaration cannot change the actual producer machine or extend its review");
        current(request.machineId(),request.reviewAtUtc(),clock,quoteOriginal);
        Path assets=Path.of(quote.assetRoot()),controls=Path.of(request.controlRoot());
        var assetDirectory=SharedSourceFiles.nativeDirectory(assets);var controlDirectory=SharedSourceFiles.nativeDirectory(controls);
        var assetGeometry=NativeStorageGeometry.read(assets);var controlGeometry=NativeStorageGeometry.read(controls);
        boolean formal=quote instanceof RootBootstrapProtocol.FormalQuote;
        var declaration=new RootBootstrapOutputContract.Declaration(
                formal?RootBootstrapOutputContract.FORMAL_DECLARATION:RootBootstrapOutputContract.DECLARATION,
                formal?RootBootstrapOutputContract.FORMAL_PURPOSE:RootBootstrapOutputContract.PURPOSE,
                request.machineId(),"/root",request.windowId(),clock.instant().toString(),request.reviewAtUtc(),
                assets.toString(),assetDirectory,controls.toString(),controlDirectory,request.assetMaximumChargedBytes(),
                request.controlMaximumChargedBytes(),request.maximumSingleWriteBytes(),request.maximumEntries(),
                quote.outputs(),quote.outputDirectories(),quote.retainedInputs());
        var created=writeIssuerMetadata(Path.of(request.target()),declaration,controls,controlDirectory,clock,quoteOriginal);
        if(!SharedSourceFiles.nativeDirectory(assets).equals(assetDirectory)||!NativeStorageGeometry.read(assets).equals(assetGeometry)
                ||!NativeStorageGeometry.read(controls).equals(controlGeometry))
            throw new IOException("issuer declaration Native directory or allocation geometry changed; retain the original write");
        current(request.machineId(),request.reviewAtUtc(),clock,quoteOriginal);
        return new IssuerDeclarationPublication(created,assetGeometry,controlGeometry);
    }
    /** Uses the sole production asset-root census, including its original bounded hierarchy and retained-input checks. */
    public static IssuerPublication observeOutputCensus(IssuerCensusRequest request,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);
        var original=SharedSourceFiles.observe(Path.of(request.declaration().path()));
        if(!original.source().equals(request.declaration()))throw new IOException("issuer declaration exact original differs");
        var declaration=readAuthority(request.declaration(),RootBootstrapOutputContract.Declaration.class);
        current(request.machineId(),request.reviewAtUtc(),clock,original);
        if(!declaration.machineId().equals(request.machineId())||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(declaration.reviewAtUtc())))
            throw new IOException("issuer census cannot change declaration machine or extend its review");
        var census=RootBootstrapOutputGuard.observeAssetRoot(request.declaration(),clock);
        var created=writeIssuerMetadata(Path.of(request.target()),census,Path.of(declaration.controlRoot()),declaration.controlDirectory(),clock,original);
        current(request.machineId(),request.reviewAtUtc(),clock,original);return created;
    }
    /** Calls the sole real runtime allocation observer. Missing/unstable roots remain its INCOMPLETE branch.
     * The control parent must exist outside every observed root, so publication cannot stale its own census.
     * Any failed CREATE_NEW/readback is retained; this method never overwrites or retries its target. */
    public static RuntimeCensusPublication observeRuntimeCensus(RuntimeCensusRequest request,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);
        var declarationOriginal=SharedSourceFiles.observe(Path.of(request.declaration().path()));
        var evidenceOriginal=SharedSourceFiles.observe(Path.of(request.existingWorkpackage().evidenceRef().path()));
        if(!declarationOriginal.source().equals(request.declaration())
                ||!evidenceOriginal.source().equals(request.existingWorkpackage().evidenceRef()))
            throw new IOException("runtime census declaration or existing-usage evidence differs from its exact original");
        var declaration=RootRuntimeStorageContract.decode(
                RootRuntimeDefinitions.read(request.declaration(),RootRuntimeStorageContract.MAXIMUM_BYTES),
                RootRuntimeStorageContract.Declaration.class);
        current(request.machineId(),request.reviewAtUtc(),clock,declarationOriginal,evidenceOriginal);
        if(!declaration.machineId().equals(request.machineId())
                ||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(declaration.reviewAtUtc())))
            throw new IOException("runtime census cannot change declaration machine or extend its review");
        Path target=Path.of(request.target()),controls=target.getParent();
        for(var root:declaration.roots())if(target.startsWith(Path.of(root.path())))
            throw new IOException("runtime census metadata target must be outside its observed allocation roots");
        var controlDirectory=SharedSourceFiles.nativeDirectory(controls);
        var census=RootRuntimeAllocationCensus.observe(request.declaration(),request.existingWorkpackage(),clock);
        current(request.machineId(),request.reviewAtUtc(),clock,declarationOriginal,evidenceOriginal);
        var published=writeIssuerMetadata(target,RootRuntimeStorageContract.encode(census),RootRuntimeStorageContract.MAXIMUM_BYTES,
                controls,controlDirectory,clock,declarationOriginal,evidenceOriginal);
        var readback=RootRuntimeStorageContract.decodeCensus(
                RootRuntimeDefinitions.read(published.original(),RootRuntimeStorageContract.MAXIMUM_BYTES));
        if(!census.equals(readback))throw new IOException("actual runtime census readback differs; retain original write without replay");
        current(request.machineId(),request.reviewAtUtc(),clock,declarationOriginal,evidenceOriginal);
        return new RuntimeCensusPublication(published,readback);
    }
    /** Only connects the sole financial issuer's existing release to its exact originals, then uses the original Guard reader. */
    public static IssuerBindingPublication bindIssuedCapacity(IssuerBindingRequest request,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);
        var original=SharedSourceFiles.observe(Path.of(request.capacityRelease().path()));
        if(!original.source().equals(request.capacityRelease()))throw new IOException("issuer capacity release exact original differs");
        var release=readAuthority(request.capacityRelease(),RootBootstrapOutputContract.CapacityRelease.class);
        var declarationOriginal=SharedSourceFiles.observe(Path.of(release.declarationRef().path()));
        var censusOriginal=SharedSourceFiles.observe(Path.of(release.censusRef().path()));
        if(!declarationOriginal.source().equals(release.declarationRef())||!censusOriginal.source().equals(release.censusRef()))
            throw new IOException("issuer capacity declaration or census original differs");
        var declaration=readAuthority(release.declarationRef(),RootBootstrapOutputContract.Declaration.class);
        current(request.machineId(),request.reviewAtUtc(),clock,original);
        if(!release.machineId().equals(request.machineId())||clock.instant().isBefore(Instant.parse(release.observedAtUtc()))
                ||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(release.reviewAtUtc())))
            throw new IOException("issuer binding cannot change release machine, predate release or extend its review");
        boolean formal=RootBootstrapOutputContract.FORMAL_CAPACITY.equals(release.schema());
        var binding=new RootBootstrapOutputContract.Binding(
                formal?RootBootstrapOutputContract.FORMAL_BINDING:RootBootstrapOutputContract.BINDING,
                release.purpose(),release.machineId(),release.ownerTask(),release.issuerTask(),release.windowId(),
                clock.instant().toString(),request.reviewAtUtc(),release.declarationRef(),release.censusRef(),request.capacityRelease());
        var created=writeIssuerMetadata(Path.of(request.target()),binding,Path.of(declaration.controlRoot()),declaration.controlDirectory(),
                clock,original,declarationOriginal,censusOriginal);
        // A refusal retains the actual binding file and never repeats CREATE_NEW or claims successful admission.
        try(var guard=RootBootstrapOutputGuard.readExact(created.original(),clock)) {
            var accounting=guard.accounting();current(request.machineId(),request.reviewAtUtc(),clock,original);
            SharedSourceFiles.assertUnchanged(declarationOriginal);SharedSourceFiles.assertUnchanged(censusOriginal);
            return new IssuerBindingPublication(created,accounting);
        }
    }
    /** Same admitted issuer metadata path, with final visibility strictly after the real Guard lock closes.
     * No authority is constructed, no failed publication is retried, and no temporary witness is relabeled. */
    public static IssuerPublication publishIssuedFileReply(IssuerFileReplyRequest request,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);
        var channelOriginal=RootBootstrapFileReply.observeExact(request.channel(),65536);
        var channel=RootBootstrapFileReply.decode(request.channel(),RootBootstrapProtocol.FileReplyChannel.class);
        var outerOriginal=RootBootstrapFileReply.observeExact(channel.bootstrapRequest(),65536);
        RootBootstrapFileReply.open(request.channel(),channel.mode(),outerOriginal,clock);
        if(!channel.machineId().equals(request.machineId())||!channel.deadline().equals(request.reviewAtUtc()))
            throw new IOException("issuer file reply cannot change the actual channel machine or finite deadline");
        var phases=RootBootstrapProtocol.commandPhases(channel.mode());
        if(request.phaseIndex()>=phases.size())throw new IOException("issuer file reply phase is outside its exact Command mode");
        Path quotePath=RootBootstrapFileReply.quotePath(channel,request.phaseIndex());
        if(!Path.of(request.actualPhaseQuote().path()).equals(quotePath))throw new IOException("issuer requires the fixed actual captured phase quote original");
        var quoteOriginal=RootBootstrapFileReply.observeExact(request.actualPhaseQuote(),RootBootstrapProtocol.FRAME_BYTES);
        byte[] wire=RootRuntimeDefinitions.read(request.actualPhaseQuote(),RootBootstrapProtocol.FRAME_BYTES);
        var quote=RootBootstrapProtocol.line(wire,RootBootstrapProtocol.Quote.class);
        if(!java.util.Arrays.equals(wire,RootBootstrapProtocol.quoteLine(quote))||!quote.phase().equals(phases.get(request.phaseIndex()))
                ||!quote.machineId().equals(request.machineId())||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(quote.reviewAtUtc()))
                ||(channel.mode()==Mode.FORMAL_RELEASE)!=(quote instanceof RootBootstrapProtocol.FormalQuote))
            throw new IOException("issuer requires the exact canonical LF phase quote, machine, branch and original window");
        Path target=RootBootstrapFileReply.replyPath(channel,request.phaseIndex());
        Path pending=target.resolveSibling("phase-"+request.phaseIndex()+"-reply.pending");
        Path assets=Path.of(quote.assetRoot()),controls=target.getParent();
        if(assets.startsWith(controls)||controls.startsWith(assets))throw new IOException("issuer file reply controls must be disjoint from actual assets");
        var bindingOriginal=RootBootstrapFileReply.observeExact(request.binding(),channel.mode()==Mode.FORMAL_RELEASE
                ?RootBootstrapOutputContract.FORMAL_MAXIMUM_AUTHORITY_BYTES:RootBootstrapOutputContract.MAXIMUM_BYTES);
        var reply=new RootBootstrapProtocol.FileReply("xar.java-root-bootstrap-file-reply/v1",request.channel(),channel.bootstrapRequest(),
                channel.mode(),quote.phase(),request.phaseIndex(),channel.deadline(),request.actualPhaseQuote(),quoteOriginal.nativeFile(),request.binding());
        org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness staged;
        try(var guard=RootBootstrapOutputGuard.readExact(request.binding(),clock)){
            guard.requirePlan(assets,quote.outputs(),quote.outputDirectories(),quote.retainedInputs());
            current(request.machineId(),request.reviewAtUtc(),clock,channelOriginal,outerOriginal);
            current(request.machineId(),request.reviewAtUtc(),clock,quoteOriginal,bindingOriginal);
            if(!SharedSourceFiles.nativeDirectory(controls).equals(channel.issuerReplyDirectory()))
                throw new IOException("issuer reply Native directory differs from the original channel");
            staged=guard.stageFileReply(pending,target,reply);
        }
        // NativeCheckpointFiles uses this same no-overwrite Windows publication primitive. ATOMIC_MOVE
        // without REPLACE_EXISTING can still replace on Windows, so it is deliberately not used here.
        var files=new NativeCheckpointFiles();files.verify(staged);
        current(request.machineId(),request.reviewAtUtc(),clock,channelOriginal,outerOriginal);
        current(request.machineId(),request.reviewAtUtc(),clock,quoteOriginal,bindingOriginal);
        if(!SharedSourceFiles.nativeDirectory(controls).equals(channel.issuerReplyDirectory()))throw new IOException("issuer reply directory changed before final publication");
        java.nio.file.Files.createLink(target,pending);
        var linked=SharedSourceFiles.observe(target);var stagedNative=SharedSourceFiles.nativeFile(pending);
        if(!linked.nativeFile().equals(stagedNative)||linked.source().bytes()!=staged.reference().bytes()
                ||!linked.source().sha256().equals(staged.reference().sha256())||linked.nativeFile().linkCount()!=2)
            throw new IOException("actual final file reply differs from the complete staged Native original; retain both names");
        java.nio.file.Files.delete(pending);
        var published=SharedSourceFiles.observe(target);
        if(published.nativeFile().linkCount()!=1||published.source().bytes()!=staged.reference().bytes()
                ||!published.source().sha256().equals(staged.reference().sha256())
                ||!java.util.Arrays.equals(RootBootstrapProtocol.encode(reply,65536),RootRuntimeDefinitions.read(published.source(),65536)))
            throw new IOException("actual final file reply readback differs; retain final and never republish");
        current(request.machineId(),request.reviewAtUtc(),clock,channelOriginal,outerOriginal);
        current(request.machineId(),request.reviewAtUtc(),clock,quoteOriginal,bindingOriginal);
        if(!SharedSourceFiles.nativeDirectory(controls).equals(channel.issuerReplyDirectory()))throw new IOException("issuer reply final directory identity changed");
        SharedSourceFiles.assertUnchanged(published);return new IssuerPublication(published.source(),published.nativeFile());
    }
    private static <T>T readAuthority(FileRef original,Class<T> type)throws IOException {
        var before=SharedSourceFiles.observe(Path.of(original.path()));
        if(!before.source().equals(original))throw new IOException("issuer authority differs from its exact original");
        T value=RootBootstrapOutputContract.decode(RootRuntimeDefinitions.read(original,RootBootstrapOutputContract.FORMAL_MAXIMUM_AUTHORITY_BYTES),type);
        SharedSourceFiles.assertUnchanged(before);return value;
    }
    private static IssuerPublication writeIssuerMetadata(Path target,RootBootstrapOutputContract.Authority authority,
            Path controls,SharedSourceFiles.DirectoryIdentity controlDirectory,Clock clock,SharedSourceFiles.Witness... originals)throws IOException {
        return writeIssuerMetadata(target,RootBootstrapOutputContract.encode(authority),
                RootBootstrapOutputContract.FORMAL_MAXIMUM_AUTHORITY_BYTES,controls,controlDirectory,clock,originals);
    }
    private static IssuerPublication writeIssuerMetadata(Path target,byte[] bytes,int maximumBytes,
            Path controls,SharedSourceFiles.DirectoryIdentity controlDirectory,Clock clock,SharedSourceFiles.Witness... originals)throws IOException {
        if(bytes.length==0||bytes.length>maximumBytes)throw new IOException("issuer metadata exceeds its existing typed contract bound");
        if(!target.isAbsolute()||!target.normalize().equals(target)||!target.getParent().equals(controls)
                ||!SharedSourceFiles.nativeDirectory(controls).equals(controlDirectory))
            throw new IOException("issuer metadata requires its declared exact plain control root");
        for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        var files=new NativeCheckpointFiles();
        var created=files.createNew(target,bytes);files.verify(created);
        if(!java.util.Arrays.equals(bytes,files.read(created,maximumBytes))
                ||!SharedSourceFiles.nativeDirectory(controls).equals(controlDirectory))
            throw new IOException("issuer metadata Native file or readback changed; retain original write without replay");
        for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        var physical=SharedSourceFiles.observe(target);
        if(!physical.source().path().equals(created.reference().path())||physical.source().bytes()!=bytes.length
                ||!physical.source().sha256().equals(created.reference().sha256()))
            throw new IOException("issuer metadata final Native observation differs from original CREATE_NEW");
        return new IssuerPublication(physical.source(),physical.nativeFile());
    }
    static void requireExplicitMode(Mode mode,NativeRunProfileManifest.ExplicitRequest request)throws IOException {
        Objects.requireNonNull(mode);Objects.requireNonNull(request);
        boolean saved=mode==Mode.EXPLICIT_SAVED_PROFILE&&request.source() instanceof NativeRunProfileManifest.SavedSource;
        boolean fixture=mode==Mode.EXPLICIT_FIXTURE_PROFILE&&request.source() instanceof NativeRunProfileManifest.FixtureSource;
        if(!saved&&!fixture)throw new IOException("explicit bootstrap mode must match the declared profile source domain");
    }
    static List<Created> phase(RootBootstrapFileReply replies,String name,Prepared prepared,String review,Clock clock,SharedSourceFiles.Witness request,
            SharedSourceFiles.Witness... held)throws Exception {
        current(WindowsJobProcess.currentMachineId(),review,clock,request);for(var input:held)current(WindowsJobProcess.currentMachineId(),review,clock,input);
        boolean formal=prepared.branch()==RootBootstrapOutputContract.Branch.FORMAL_RELEASE;
        RootBootstrapProtocol.Quote quote=formal?new RootBootstrapProtocol.FormalQuote(
                "xar.java-root-bootstrap-formal-release-phase-quote/v2",name,WindowsJobProcess.currentMachineId(),review,
                prepared.assetRoot().toString(),prepared.quote(),prepared.outputDirectories(),prepared.retainedInputs(),
                prepared.formalLayout().name(),RootBootstrapOutputContract.FORMAL_PURPOSE,prepared.formalAssetPeakUpperBytes(),
                RootBootstrapOutputContract.FORMAL_MAXIMUM_ASSET_BYTES,RootBootstrapOutputContract.MAXIMUM_CONTROL_BYTES,
                prepared.quote().stream().mapToLong(RootBootstrapOutputContract.Output::bytes).max().orElseThrow(),
                prepared.quote().size()+prepared.outputDirectories().size(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING")
                :new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1",name,WindowsJobProcess.currentMachineId(),review,
                prepared.assetRoot().toString(),prepared.quote(),prepared.outputDirectories(),prepared.retainedInputs(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
        RootBootstrapProtocol.emit(quote);
        RootBootstrapFileReply.BindingEvidence reply=null;FileRef binding;
        if(replies!=null){reply=replies.await(quote,review);binding=reply.binding();}
        else {
            // The original finite stdin route remains the OwnedStdio Session's binding transport.
            var input=new FutureTask<String>(RootProfileBootstrapCommand::readBindingLine);Thread.ofVirtual().start(input);
            String line;try{long remaining=java.time.Duration.between(clock.instant(),Instant.parse(review)).toMillis();
                if(remaining<=0)throw new IOException("bootstrap issuer-response window expired");line=input.get(remaining,TimeUnit.MILLISECONDS);
            }finally{input.cancel(true);}
            binding=ControlBuild.strictMapper().readValue(StrictJson.canonical(StrictJson.parse(line.getBytes(StandardCharsets.UTF_8),65536),65536),FileRef.class);
        }
        current(WindowsJobProcess.currentMachineId(),review,clock,request);for(var heldOriginal:held)current(WindowsJobProcess.currentMachineId(),review,clock,heldOriginal);
        if(reply!=null)reply.verify();
        try(var authority=RootBootstrapOutputGuard.readExact(binding,clock)){
            if(reply!=null)reply.verify();
            var actual=prepared.createNew(authority);current(WindowsJobProcess.currentMachineId(),review,clock,request);
            for(var heldOriginal:held)current(WindowsJobProcess.currentMachineId(),review,clock,heldOriginal);
            if(reply!=null)reply.verify();
            RootBootstrapProtocol.emit(new RootBootstrapProtocol.Emission<>("STAGE_CREATED_NO_GAME_ADMISSION",
                    WindowsJobProcess.currentMachineId(),clock.instant().toString(),new RootBootstrapProtocol.Stage(actual,authority.accounting())));
            return actual;
        }
    }
    private static String readBindingLine()throws IOException {
        var bytes=new java.io.ByteArrayOutputStream();while(true){int value=System.in.read();
            if(value<0)throw new IOException("actual issuer binding input ended before this phase");if(value=='\n')break;
            if(value!='\r'){if(bytes.size()>=65536)throw new IOException("issuer binding line exceeds finite input bound");bytes.write(value);}}
        try{return StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(bytes.toByteArray())).toString();}
        catch(java.nio.charset.CharacterCodingException invalid){throw new IOException("actual issuer binding must be strict UTF8",invalid);}
    }
    private static <T>T read(FileRef original,Class<T> type)throws IOException {
        var before=SharedSourceFiles.observe(Path.of(original.path()));byte[] bytes=RootRuntimeDefinitions.read(original,65536);
        if(!before.source().equals(original))throw new IOException("bootstrap request differs from its exact original");
        StrictJson.parse(bytes,65536);T actual=ControlBuild.strictMapper().readValue(bytes,type);SharedSourceFiles.assertUnchanged(before);return actual;
    }
    private static void emit(String status,com.fasterxml.jackson.databind.JsonNode value)throws IOException {
        var row=StrictJson.object();row.put("status",status);row.put("machine_id",WindowsJobProcess.currentMachineId());row.put("observed_at_utc",Instant.now().toString());row.set("originals",value);
        System.out.println(new String(StrictJson.canonical(row,1<<20),StandardCharsets.UTF_8));System.out.flush();
    }
    private static void current(String machine,String review,Clock clock,SharedSourceFiles.Witness first,
            SharedSourceFiles.Witness second)throws IOException {
        current(machine,review,clock,first);SharedSourceFiles.assertUnchanged(second);
    }
    private static void current(String machine,String review,Clock clock,SharedSourceFiles.Witness original)throws IOException {
        if(!machine.equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(Instant.parse(review))
                ||!SharedSourceFiles.nativeFile(Path.of(original.source().path())).equals(original.nativeFile()))throw new IOException("bootstrap request machine, review or source FileID drifted");
        SharedSourceFiles.assertUnchanged(original);
    }
    private static void common(String actual,String schema,String machine,String review){
        StrictJson.require(schema.equals(actual),"exact source bootstrap request schema required");StrictJson.text(machine);
        Instant until=Instant.parse(review);StrictJson.require(review.equals(until.toString()),"canonical bootstrap UTC review required");
        long remaining=java.time.Duration.between(Instant.now(),until).toMillis();StrictJson.require(remaining>0&&remaining<=1800000,"fresh finite bootstrap request window up to thirty minutes required");
    }
    private static void absolute(String value){StrictJson.text(value);Path path=Path.of(value);StrictJson.require(path.isAbsolute()&&path.normalize().equals(path),"actual normalized absolute bootstrap path required");}
}

