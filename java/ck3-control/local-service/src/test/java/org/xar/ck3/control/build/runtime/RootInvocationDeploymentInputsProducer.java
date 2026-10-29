package org.xar.ck3.control.build.runtime;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Properties;
import java.util.jar.JarFile;
import org.xar.ck3.control.build.ControlCi;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.service.root.RootPackageNativeVerifier;

/** Test-only importer of existing genuine artifacts. Never builds a package or starts its command. */
public final class RootInvocationDeploymentInputsProducer implements RootInvocationDeploymentActualRegression.InputsProducer {
    public static final int MAXIMUM_PLAN_BYTES=65536;
    public static final String PROPERTY_PREFIX="xar.root.invocation.actual-inputs.";
    public RootInvocationDeploymentInputsProducer(){ }
    @Override public RootInvocationDeploymentActualRegression.Inputs produce()throws IOException {
        return readActual(configuredPlan(System.getProperties()));
    }
    /** Only the fixed plan source is configured; authority and production class names are never inputs. */
    static FileRef configuredPlan(Properties properties)throws IOException {
        Objects.requireNonNull(properties);
        String path=properties.getProperty(PROPERTY_PREFIX+"path");
        String size=properties.getProperty(PROPERTY_PREFIX+"bytes");
        String digest=properties.getProperty(PROPERTY_PREFIX+"sha256");
        if(path==null||path.isBlank()||size==null||!size.matches("[1-9][0-9]{0,5}")
                ||digest==null||!digest.matches("[0-9a-f]{64}"))
            throw new IOException("MISSING_ACTUAL_ROOT_INVOCATION_INPUT_PLAN: exact path/bytes/sha256 properties required");
        try {
            FileRef result=new FileRef(path,Long.parseLong(size),digest);positive(result,MAXIMUM_PLAN_BYTES);return result;
        } catch(IllegalArgumentException invalid){throw new IOException("strict actual invocation input properties differ",invalid);}
    }
    /** Fixed production authority; an input record cannot choose a substitute verifier or create an accepted package. */
    public static RootInvocationDeploymentActualRegression.Inputs readActual(FileRef exactPlan)throws IOException {
        var held=new ArrayList<SharedSourceFiles.Witness>();
        ControlCi.RootInvocationInputsPlan plan=ControlCi.decodeRootInvocationInputsPlan(read(exactPlan,MAXIMUM_PLAN_BYTES,held));
        Instant now=Instant.now();
        if(!WindowsJobProcess.currentMachineId().equals(plan.machineId())||now.isBefore(plan.observedAt())||!now.isBefore(plan.reviewAt()))
            throw new IOException("actual invocation input machine/review is not current");
        held.add(observe(plan.packageManifest()));
        var imported=JavaRuntimePackage.readAccepted(plan.packageManifest(),new RootPackageNativeVerifier());
        if(!(imported instanceof JavaRuntimePackage.PackageAvailable available)) {
            var failure=(JavaRuntimePackage.Unavailable)imported;
            throw new IOException("GENUINE_ROOT_PACKAGE_UNAVAILABLE: "+failure.stage()+": "+failure.reason());
        }
        var accepted=available.value();accepted.verifyCurrent();
        if(!accepted.manifest().request().machineId().equals(plan.machineId()))
            throw new IOException("input plan crossed the actual accepted package machine");
        long minimum=Math.addExact(accepted.manifest().request().launch().maximumHeapBytes(),128L<<20);
        if(plan.memoryLimitBytes()<minimum)throw new IOException("actual input memory is below the accepted JVM heap plus overhead");
        var invocation=RootStartupInvocation.decode(read(plan.invocation(),65536,held));
        for(FileRef ref:invocation.sources()){positive(ref,1024*1024);held.add(observe(ref));}
        for(var jar:plan.productionJars())held.add(requireProductionJar(accepted,jar));
        accepted.verifyCurrent();for(var witness:held)SharedSourceFiles.assertUnchanged(witness);
        return new RootInvocationDeploymentActualRegression.Inputs(accepted,plan.invocation(),plan.stdout(),plan.stderr(),plan.memoryLimitBytes());
    }
    private static SharedSourceFiles.Witness requireProductionJar(JavaRuntimePackage.VerifiedPackage accepted,ControlCi.RootInvocationProductionJar declared)throws IOException {
        Class<?> type=roleType(declared.role());
        if(type.getClassLoader()!=JavaRuntimeLaunch.class.getClassLoader()||type.getProtectionDomain()==null
                ||type.getProtectionDomain().getCodeSource()==null)
            throw new IOException("actual production classes require the same fixed source-JAR loader: "+type.getName());
        var location=type.getProtectionDomain().getCodeSource().getLocation();
        if(location==null||!"file".equals(location.getProtocol()))throw new IOException("actual production JAR CodeSource required");
        final Path current;
        try{current=Path.of(location.toURI()).toRealPath();}
        catch(java.net.URISyntaxException invalid){throw new IOException("actual production CodeSource URI differs",invalid);}
        var witness=SharedSourceFiles.observe(current);
        if(!witness.source().equals(declared.source()))throw new IOException("production JAR differs from its exact plan role: "+declared.role());
        var providers=accepted.manifest().layout().applicationClasses().stream().filter(row->row.binaryName().equals(type.getName())
                &&row.kind()==JavaRuntimePackageModel.ProviderKind.ORIGINAL).toList();
        if(providers.size()!=1)throw new IOException("accepted package lacks one original production provider: "+type.getName());
        String relative="quarkus-app/"+providers.getFirst().relativeJar();
        var outputs=accepted.manifest().outputFiles().stream().filter(row->row.relativePath().equals(relative)).toList();
        if(outputs.size()!=1)throw new IOException("actual production JAR is outside the accepted package layout");
        var output=outputs.getFirst();var actual=witness.source();
        boolean original=accepted.manifest().originalInputs().stream().anyMatch(row->row.source().equals(actual));
        boolean privateCopy=current.equals(Path.of(output.actual().source().path()).toRealPath())&&actual.equals(output.actual().source());
        if((!original&&!privateCopy)||actual.bytes()!=output.original().bytes()||!actual.sha256().equals(output.original().sha256()))
            throw new IOException("production source is neither the accepted original nor its exact private package JAR");
        output.original().verify();output.actual().source().verify();
        try(var jar=new JarFile(current.toFile(),false)) {
            if(jar.getJarEntry(type.getName().replace('.','/')+".class")==null)throw new IOException("actual JAR omits its loaded production class");
        }
        SharedSourceFiles.assertUnchanged(witness);return witness;
    }
    private static byte[] read(FileRef expected,int maximum,List<SharedSourceFiles.Witness> held)throws IOException {
        try{positive(expected,maximum);}catch(IllegalArgumentException invalid){throw new IOException("bounded exact input required",invalid);}
        var before=observe(expected);byte[] bytes;
        try(var input=Files.newInputStream(Path.of(expected.path()))){bytes=input.readNBytes(maximum+1);}
        if(bytes.length!=expected.bytes()||!sha256(bytes).equals(expected.sha256()))throw new IOException("actual complete input bytes differ");
        SharedSourceFiles.assertUnchanged(before);held.add(before);return bytes;
    }
    private static SharedSourceFiles.Witness observe(FileRef expected)throws IOException {
        var witness=SharedSourceFiles.observe(Path.of(expected.path()));
        if(!witness.source().equals(expected))throw new IOException("actual input content/path differs from its exact source");return witness;
    }
    private static Class<?> roleType(ControlCi.RootInvocationProductionRole role) {
        return switch(role) {
            case JAVA_RUNTIME_LAUNCH->JavaRuntimeLaunch.class;
            case ROOT_STARTUP_INVOCATION->RootStartupInvocation.class;
            case ROOT_NATIVE_AUTHORITY->RootPackageNativeVerifier.class;
        };
    }
    private static String sha256(byte[] bytes)throws IOException {
        try{return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));}
        catch(java.security.NoSuchAlgorithmException unavailable){throw new IOException("required SHA-256 unavailable",unavailable);}
    }
    private static void positive(FileRef ref,long maximum) {
        Objects.requireNonNull(ref);Path path=Path.of(ref.path());
        if(!path.isAbsolute()||!path.normalize().equals(path)||ref.bytes()<1||ref.bytes()>maximum)
            throw new IllegalArgumentException("bounded positive source with absolute normalized path required");
    }
}
