package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ControlCi;
import org.xar.ck3.control.build.NativeStorageGeometry;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.ContractPin;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.JavaHome;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.LaunchSettings;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeInputs;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Quote;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;
import org.xar.ck3.control.build.runtime.RootStartupInvocation;
import org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.FiniteFirstLiveInvocation;

/** The actual Root package parameter graph. DATA production never starts Game or grants storage authority. */
public final class RootRuntimePackageInputsProducer {
    public static final String PARAMETERS_SCHEMA="xar.root-runtime-package-input-parameters/v1";
    public static final String REVIEW_SCHEMA="xar.root-runtime-package-input-review/v1";
    public static final String CAPTURE_REVIEW_SCHEMA="xar.root-runtime-capture-input-review/v1";
    private static final int SMALL_BYTES=65536;
    public static final List<String> REQUIRED_ROOT_CLASSES=List.of(RootQuarkusEntrypoint.class.getName(),RootApplicationMain.class.getName(),RootPackageNativeVerifier.class.getName(),RootRuntimePackageInputsProducer.class.getName());
    private RootRuntimePackageInputsProducer(){ }

    /** All FileRefs name existing producer outputs. Future outputs are paths only. */
    public record Parameters(String schema,String machineId,String generation,String reviewAtUtc,
            Path artifactsRoot,Path packageRoot,Path metadataRoot,FileRef serviceBuildActual,
            JavaHome javaHome,NativeInputs nativeInputs,List<ContractPin> contracts,FileRef hostConfiguration,
            LaunchSettings launch,List<String> additionalRequiredClasses,FileRef storageEvidence,long maximumOutputBytes,long perDirectoryGuardBytes,long commandMemoryLimitBytes) {
        public Parameters {
            if(!PARAMETERS_SCHEMA.equals(schema)||machineId==null||generation==null||!generation.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
                    ||reviewAtUtc==null||serviceBuildActual==null||javaHome==null||nativeInputs==null
                    ||hostConfiguration==null||launch==null||storageEvidence==null)
                throw new IllegalArgumentException("Complete actual Root input parameters required");
            Instant.parse(reviewAtUtc);absolute(artifactsRoot);absolute(packageRoot);absolute(metadataRoot);
            if(!packageRoot.startsWith(artifactsRoot)||packageRoot.equals(artifactsRoot)
                    ||!metadataRoot.startsWith(artifactsRoot)||metadataRoot.equals(artifactsRoot)
                    ||!packageRoot.equals(artifactsRoot.resolve("runtime-package").resolve(generation))
                    ||!metadataRoot.equals(artifactsRoot.resolve("runtime-inputs").resolve(generation))
                    ||maximumOutputBytes<1||maximumOutputBytes>JavaRuntimePackageModel.MAX_PACKAGE_BYTES
                    ||perDirectoryGuardBytes<4096)
                throw new IllegalArgumentException("Separate finite package/metadata roots under issued artifacts root required");
            contracts=List.copyOf(contracts);additionalRequiredClasses=List.copyOf(additionalRequiredClasses);
            if(!additionalRequiredClasses.containsAll(REQUIRED_ROOT_CLASSES))throw new IllegalArgumentException("Actual Root entry/verifier/input-producer classes must be required in the accepted service");
            if(launch.mode()!=HostMode.COMPLETE_MIGRATION)throw new IllegalArgumentException("Only the actual full Root startup mode is supported");
            requireCommandMemory(launch,commandMemoryLimitBytes);
        }
    }
    /** The quote is DATA from genuine review. Capacity issues a separate real permit after seeing it. */
    public record Review(String schema,FileRef parametersRef,FileRef requestRef,Quote quote,
            long allocationUnitBytes,long perDirectoryGuardBytes,long allocationUpperBytes) {
        public Review {
            if(!REVIEW_SCHEMA.equals(schema)||parametersRef==null||requestRef==null||quote==null
                    ||allocationUnitBytes<1||allocationUnitBytes>(1L<<20)||perDirectoryGuardBytes<4096
                    ||allocationUpperBytes<1||allocationUpperBytes>JavaRuntimePackageModel.MAX_PACKAGE_BYTES)
                throw new IllegalArgumentException("Exact actual request/quote and native geometry required");
        }
    }
    /** Source-reviewed candidate DATA only; ordinary permit/package consumers do not accept this schema. */
    public record CapturedReview(String schema,FileRef parametersRef,FileRef requestRef,FileRef captureBuildActual,
            ControlBuild.CaptureQualification qualification,ControlBuild.CaptureTestState tests,Quote quote,
            long allocationUnitBytes,long perDirectoryGuardBytes,long allocationUpperBytes) {
        public CapturedReview {
            if(!CAPTURE_REVIEW_SCHEMA.equals(schema)||parametersRef==null||requestRef==null||captureBuildActual==null
                    ||qualification!=ControlBuild.CaptureQualification.TEST_COMPILED_CAPTURE_ONLY
                    ||tests!=ControlBuild.CaptureTestState.NOT_RUN||quote==null
                    ||allocationUnitBytes<1||allocationUnitBytes>(1L<<20)||perDirectoryGuardBytes<4096
                    ||allocationUpperBytes<1||allocationUpperBytes>JavaRuntimePackageModel.MAX_PACKAGE_BYTES)
                throw new IllegalArgumentException("actual capture-only request/quote and explicit TEST_NOT_RUN required");
        }
    }
    public static void requireCommandMemory(LaunchSettings launch,long memory) {
        Objects.requireNonNull(launch);
        if(memory<Math.addExact(launch.maximumHeapBytes(),128L<<20)||memory>(32L<<30))
            throw new IllegalArgumentException("Actual command memory must cover selected heap plus128MiB");
    }
    private static void absolute(Path value) {
        if(value==null||!value.isAbsolute()||!value.normalize().equals(value))
            throw new IllegalArgumentException("Normalized absolute output path required");
    }
    private static Request request(Parameters p,String createdAtUtc) {
        return new Request(JavaRuntimePackageModel.REQUEST_SCHEMA,p.machineId(),p.generation(),createdAtUtc,
                p.reviewAtUtc(),p.packageRoot().toString(),p.serviceBuildActual(),p.javaHome(),p.nativeInputs(),
                p.contracts(),p.hostConfiguration(),p.launch(),p.additionalRequiredClasses(),p.maximumOutputBytes());
    }
    private static void current(Parameters p)throws IOException {
        if(!WindowsJobProcess.currentMachineId().equals(p.machineId())||!Instant.now().isBefore(Instant.parse(p.reviewAtUtc())))
            throw new IOException("Actual machine/review window unavailable");
        ProjectStoragePolicy.requireBulkOutput(p.packageRoot());ProjectStoragePolicy.requireBulkOutput(p.metadataRoot());
        p.storageEvidence().verify();
    }
    private static JavaRuntimePackage.ReviewAvailable review(Request actual)throws IOException {
        var build=ControlBuild.verifiedCompletedReceipt(actual.serviceBuildActual());
        requireOriginalProducerDeployment(build.completeDeployment());
        var result=JavaRuntimePackage.review(actual,new RootPackageNativeVerifier());
        if(!(result instanceof JavaRuntimePackage.ReviewAvailable value))
            throw new IOException("Actual Root package review unavailable: "+result);
        return value;
    }
    private static JavaRuntimePackage.CapturedReviewAvailable reviewCaptured(Request actual)throws IOException {
        var build=ControlBuild.verifiedCompletedCaptureReceipt(actual.serviceBuildActual());
        requireOriginalProducerDeployment(build.completeDeployment());
        var result=JavaRuntimePackage.reviewCapturedService(actual,new RootPackageNativeVerifier());
        if(!(result instanceof JavaRuntimePackage.CapturedReviewAvailable value))
            throw new IOException("Actual capture-only Root service review unavailable: "+result);
        value.verifyCurrent();return value;
    }
    private static void requireOriginalProducerDeployment(List<FileRef> completeDeployment)throws IOException {
        for(Class<?> type:List.of(RootRuntimePackageInputsProducer.class,RootPackageNativeVerifier.class,JavaRuntimePackage.class)) {
            if(type.getClassLoader()!=RootRuntimePackageInputsProducer.class.getClassLoader()
                    ||type.getProtectionDomain().getCodeSource()==null)
                throw new IOException("Actual package input producer requires one original production JAR loader");
            final Path jar;
            try{jar=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();}
            catch(java.net.URISyntaxException invalid){throw new IOException("Original production CodeSource URI differs",invalid);}
            var witness=SharedSourceFiles.observe(jar);
            if(!completeDeployment.contains(witness.source()))
                throw new IOException("Input producer/verifier/package code is not from the accepted original deployment: "+type.getName());
            try(var opened=new java.util.jar.JarFile(jar.toFile(),false)) {
                if(opened.getJarEntry(type.getName().replace('.','/')+".class")==null)
                    throw new IOException("Original production JAR omits its actual loaded class");
            }
            SharedSourceFiles.assertUnchanged(witness);
        }
    }
    /** Writes only small input metadata after actual Host/Native/source review. No package or future FileRef is created. */
    public static FileRef prepare(FileRef originalParameters)throws IOException {
        Parameters p=read(originalParameters,Parameters.class,JavaRuntimePackageModel.MAX_METADATA_BYTES);current(p);
        Request request=request(p,Instant.now().toString());
        var actual=review(request);
        long unit=NativeStorageGeometry.read(p.artifactsRoot()).clusterBytes();
        long upper=JavaRuntimePackage.allocationUpperBytes(actual,unit,p.perDirectoryGuardBytes());
        if(upper>p.maximumOutputBytes())throw new IOException("Actual package quote exceeds the requested bounded maximum");
        byte[] encodedRequest=JavaRuntimePackageCodec.encodeRequest(request);
        if(Files.exists(p.metadataRoot())||Files.exists(p.packageRoot()))
            throw new IOException("Immutable input generation/package root already exists; preserve its outcome");
        originalParameters.verify();current(p);
        SharedSourceFiles.plainAncestors(p.metadataRoot());
        Files.createDirectories(p.packageRoot().getParent());
        Files.createDirectories(p.metadataRoot().getParent());Files.createDirectory(p.metadataRoot());
        FileRef requestRef=write(p.metadataRoot().resolve("request.json"),encodedRequest,JavaRuntimePackageModel.MAX_METADATA_BYTES);
        if(!JavaRuntimePackageCodec.readRequest(requestRef).equals(request))
            throw new IOException("Actual request cold readback changed");
        var result=new Review(REVIEW_SCHEMA,originalParameters,requestRef,actual.quote(),unit,p.perDirectoryGuardBytes(),upper);
        FileRef publication=write(p.metadataRoot().resolve("review.json"),ControlBuild.strictMapper().writeValueAsBytes(result),SMALL_BYTES);
        if(!read(publication,Review.class,SMALL_BYTES).equals(result))throw new IOException("Actual review DATA roundtrip changed");
        originalParameters.verify();current(p);return publication;
    }
    /** Reviews real capture layout and publishes small candidate request DATA; never copies a package or issues a permit. */
    public static FileRef prepareCapturedService(FileRef originalParameters)throws IOException {
        Parameters p=read(originalParameters,Parameters.class,JavaRuntimePackageModel.MAX_METADATA_BYTES);current(p);
        Request request=request(p,Instant.now().toString());var actual=reviewCaptured(request);
        long unit=NativeStorageGeometry.read(p.artifactsRoot()).clusterBytes();
        long upper=JavaRuntimePackage.allocationUpperBytes(actual,unit,p.perDirectoryGuardBytes());
        if(upper>p.maximumOutputBytes())throw new IOException("actual candidate quote exceeds its bounded maximum");
        if(Files.exists(p.metadataRoot())||Files.exists(p.packageRoot()))
            throw new IOException("candidate metadata/package generation already exists; preserve its outcome");
        originalParameters.verify();current(p);actual.verifyCurrent();SharedSourceFiles.plainAncestors(p.metadataRoot());
        Files.createDirectories(p.metadataRoot().getParent());Files.createDirectory(p.metadataRoot());
        FileRef requestRef=write(p.metadataRoot().resolve("capture-request.json"),JavaRuntimePackageCodec.encodeRequest(request),
                JavaRuntimePackageModel.MAX_METADATA_BYTES);
        if(!JavaRuntimePackageCodec.readRequest(requestRef).equals(request))throw new IOException("actual capture request readback changed");
        var result=new CapturedReview(CAPTURE_REVIEW_SCHEMA,originalParameters,requestRef,p.serviceBuildActual(),
                actual.qualification(),actual.tests(),actual.quote(),unit,p.perDirectoryGuardBytes(),upper);
        FileRef publication=write(p.metadataRoot().resolve("capture-review.json"),ControlBuild.strictMapper().writeValueAsBytes(result),SMALL_BYTES);
        if(!read(publication,CapturedReview.class,SMALL_BYTES).equals(result))throw new IOException("actual capture review readback changed");
        originalParameters.verify();current(p);actual.verifyCurrent();return publication;
    }
    /** Adopts a separately issued permit; returns the existing actual CI consumer type, never a second authority. */
    public static FileRef bindPermit(FileRef originalReview,FileRef issuedPermit,FileRef actualStartup,List<FileRef> savedRequest,Path destination)throws IOException {
        return bindPermitActual(originalReview,issuedPermit,actualStartup,savedRequest,Optional.empty(),destination);
    }
    /** Same package/write authority, carrying the distinct finite invocation to the existing launch consumer. */
    public static FileRef bindFinitePermit(FileRef originalReview,FileRef issuedPermit,FileRef actualFiniteRequest,Path destination)throws IOException {
        var finite=RootFiniteFirstLiveRequest.readExact(actualFiniteRequest);finite.requireCurrent(java.time.Clock.systemUTC());
        var result=bindPermitActual(originalReview,issuedPermit,finite.startup().startup(),List.of(),Optional.of(actualFiniteRequest),destination);
        actualFiniteRequest.verify();return result;
    }
    private static FileRef bindPermitActual(FileRef originalReview,FileRef issuedPermit,FileRef actualStartup,List<FileRef> savedRequest,
            Optional<FileRef> actualFiniteRequest,Path destination)throws IOException {
        absolute(destination);
        var held=read(originalReview,Review.class,SMALL_BYTES);
        var p=read(held.parametersRef(),Parameters.class,JavaRuntimePackageModel.MAX_METADATA_BYTES);current(p);
        if(!Path.of(originalReview.path()).equals(p.metadataRoot().resolve("review.json"))
                ||!destination.startsWith(p.metadataRoot())||destination.equals(p.metadataRoot()))
            throw new IOException("Permit binding must retain the original input generation");
        var request=JavaRuntimePackageCodec.readRequest(held.requestRef());
        if(!request.equals(request(p,request.createdAtUtc())))throw new IOException("Actual request differs from its original parameters");
        savedRequest=List.copyOf(savedRequest);
        if(savedRequest.size()>1)throw new IOException("At most one explicit actual Saved input required");
        actualStartup.verify();for(var saved:savedRequest)saved.verify();
        var startup=RootStartupConfiguration.readExact(actualStartup);
        startup.requireCurrent(java.time.Clock.systemUTC());
        if(!startup.machineId().equals(p.machineId())||!startup.application().equals(p.hostConfiguration())
                ||Instant.parse(p.reviewAtUtc()).isAfter(startup.reviewAt()))
            throw new IOException("Actual Root startup differs from the same package Host configuration/machine/window");
        byte[] invocation;
        if(actualFiniteRequest.isPresent()){
            var finite=RootFiniteFirstLiveRequest.readExact(actualFiniteRequest.orElseThrow());finite.requireCurrent(java.time.Clock.systemUTC());
            if(!savedRequest.isEmpty()||!finite.startup().startup().equals(actualStartup)
                    ||!finite.machineId().equals(p.machineId())||Instant.parse(p.reviewAtUtc()).isAfter(finite.reviewAt()))
                throw new IOException("finite request differs from this actual package startup/machine/window");
            invocation=new FiniteFirstLiveInvocation(actualFiniteRequest.orElseThrow()).encode();
        }else invocation=new RootStartupInvocation(actualStartup,savedRequest.isEmpty()?Optional.empty():Optional.of(savedRequest.getFirst())).encode();
        var actual=review(request);
        long unit=NativeStorageGeometry.read(p.artifactsRoot()).clusterBytes();
        long upper=JavaRuntimePackage.allocationUpperBytes(actual,unit,p.perDirectoryGuardBytes());
        if(!actual.quote().equals(held.quote())||unit!=held.allocationUnitBytes()
                ||upper!=held.allocationUpperBytes()||p.perDirectoryGuardBytes()!=held.perDirectoryGuardBytes())
            throw new IOException("Actual reviewed package quote or geometry changed before permit adoption");
        var permit=read(issuedPermit,JavaRuntimePackage.WritePermit.class,SMALL_BYTES);
        if(!permit.machineId().equals(p.machineId())||!permit.exactOutputRoot().equals(p.packageRoot().toString())
                ||!permit.actualStorageEvidence().equals(p.storageEvidence())||permit.allocationUnitBytes()!=unit
                ||permit.perDirectoryGuardBytes()!=p.perDirectoryGuardBytes()||permit.allocationUpperBytes()<upper
                ||permit.allocationUpperBytes()>request.maximumOutputBytes()
                ||!Instant.now().isBefore(Instant.parse(permit.expiresAtUtc()))
                ||Instant.parse(permit.expiresAtUtc()).isAfter(Instant.parse(p.reviewAtUtc())))
            throw new IOException("Issued permit differs from actual machine/root/release/geometry/quote/window");
        permit.actualStorageEvidence().verify();issuedPermit.verify();held.parametersRef().verify();originalReview.verify();
        Path invocationPath=p.metadataRoot().resolve("invocation.json");
        if(Files.exists(destination)||Files.exists(invocationPath))
            throw new IOException("Retained invocation/binding generation cannot be overwritten or silently retried");
        FileRef invocationRef=write(invocationPath,invocation,SMALL_BYTES);
        byte[] readback=readBytes(invocationRef,SMALL_BYTES);
        if(!java.util.Arrays.equals(readback,invocation))throw new IOException("Actual invocation cold readback changed");
        if(actualFiniteRequest.isPresent()){
            if(!FiniteFirstLiveInvocation.decode(readback).finiteRequest().equals(actualFiniteRequest.orElseThrow()))
                throw new IOException("finite invocation reader changed its exact original request");
            actualFiniteRequest.orElseThrow().verify();
        }else RootStartupInvocation.decode(readback);
        var input=new ControlCi.RootPackageProductionInput(held.requestRef(),invocationRef,permit,p.commandMemoryLimitBytes());
        FileRef result=write(destination,ControlBuild.strictMapper().writeValueAsBytes(input),SMALL_BYTES);
        if(!read(result,ControlCi.RootPackageProductionInput.class,SMALL_BYTES).equals(input))
            throw new IOException("Actual CI input binding cold readback changed");
        issuedPermit.verify();originalReview.verify();current(p);return result;
    }
    private static byte[] readBytes(FileRef ref,int maximum)throws IOException {
        if(ref.bytes()<1||ref.bytes()>maximum)throw new IOException("Bounded existing exact input required");
        var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        if(!witness.source().equals(ref))throw new IOException("Exact original input differs");
        byte[] raw=Files.readAllBytes(Path.of(ref.path()));SharedSourceFiles.assertUnchanged(witness);
        if(raw.length!=ref.bytes())throw new IOException("Complete input read changed");return raw;
    }
    private static <T> T read(FileRef ref,Class<T> type,int maximum)throws IOException {
        return ControlBuild.strictMapper().readValue(readBytes(ref,maximum),type);
    }
    private static FileRef write(Path path,byte[] raw,int maximum)throws IOException {
        if(raw.length<1||raw.length>maximum)throw new IOException("Finite metadata output exceeded");
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        FileRef result=FileRef.measure(path);
        if(!java.util.Arrays.equals(raw,readBytes(result,maximum)))throw new IOException("Metadata create/readback changed");return result;
    }
    private static FileRef argument(String[] args,int offset) {
        if(!args[offset+1].matches("[1-9][0-9]{0,7}"))throw new IllegalArgumentException("Canonical positive exact input bytes required");
        return new FileRef(args[offset],Long.parseLong(args[offset+1]),args[offset+2]);
    }
    public static void main(String[] args)throws IOException {
        final FileRef output;
        if(args.length==4&&args[0].equals("--prepare"))output=prepare(argument(args,1));
        else if(args.length==4&&args[0].equals("--prepare-captured-service"))output=prepareCapturedService(argument(args,1));
        else if(args.length==14&&args[0].equals("--bind-finite-permit")&&args[4].equals("--permit")
                &&args[8].equals("--finite-request")&&args[12].equals("--output"))
            output=bindFinitePermit(argument(args,1),argument(args,5),argument(args,9),Path.of(args[13]));
        else if((args.length==14||args.length==18)&&args[0].equals("--bind-permit")&&args[4].equals("--permit")&&args[8].equals("--startup")
                &&args[args.length-2].equals("--output")&&(args.length==14||args[12].equals("--saved")))
            output=bindPermit(argument(args,1),argument(args,5),argument(args,9),
                    args.length==14?List.of():List.of(argument(args,13)),Path.of(args[args.length-1]));
        else throw new IllegalArgumentException("Use --prepare PARAMS exact3, --prepare-captured-service PARAMS exact3, --bind-permit REVIEW exact3 --permit PERMIT exact3 --startup START exact3 [--saved SAVED exact3] --output NEW_PATH, or --bind-finite-permit REVIEW exact3 --permit PERMIT exact3 --finite-request REQUEST exact3 --output NEW_PATH");
        System.out.println(ControlBuild.strictMapper().writeValueAsString(output));
    }
}

