package org.xar.ck3.control.build.runtime;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;

/** Requires the real imported package and its actual source JAR class loader. Never starts its CommandSpec. */
public final class RootInvocationDeploymentActualRegression {
    /** Mandatory postqualification entry; runs the same persistent @Test bodies with the real JUnit engine. */
    public static void main(String[] args) {
        if(args.length!=0) throw new IllegalArgumentException("No alternate actual test selection allowed");
        String property="xar.root.invocation.actual-inputs-producer";
        String fixed=RootInvocationDeploymentInputsProducer.class.getName();
        if(System.getProperty(property)!=null&&!fixed.equals(System.getProperty(property)))
            throw new IllegalArgumentException("Only the fixed genuine package importer is permitted");
        System.setProperty(property,fixed);
        var request=org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(RootInvocationDeploymentActualRegression.class))
                .configurationParameter("junit.jupiter.execution.parallel.enabled","false").build();
        var listener=new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        org.junit.platform.launcher.core.LauncherFactory.create().execute(request,listener);
        var summary=listener.getSummary();
        summary.printTo(new java.io.PrintWriter(System.out,true));
        summary.printFailuresTo(new java.io.PrintWriter(System.err,true));
        if(summary.getTestsFoundCount()!=2 || summary.getTestsStartedCount()!=2
                || summary.getTestsSucceededCount()!=2 || summary.getTestsFailedCount()!=0
                || summary.getTestsSkippedCount()!=0 || summary.getTestsAbortedCount()!=0
                || summary.getContainersFailedCount()!=0 || summary.getTotalFailureCount()!=0)
            throw new IllegalStateException("Mandatory actual integration requires exactly 2 successes without failures/skips/aborts");
        System.out.println("PASS_ROOT_INVOCATION_ACTUAL_JUNIT_2");
    }
    public record Inputs(JavaRuntimePackage.VerifiedPackage accepted,ControlBuild.FileRef invocation,
            Path stdout,Path stderr,long memoryLimitBytes) { }
    public interface InputsProducer { Inputs produce()throws Exception; }
    @TempDir Path temporary;
    private Inputs actual()throws Exception {
        String provider=System.getProperty("xar.root.invocation.actual-inputs-producer");
        if(provider==null||provider.isBlank())throw new IOException("genuine imported Root package/source-JAR inputs are mandatory; no skipped or software substitute positive");
        var producer=Class.forName(provider).getDeclaredConstructor().newInstance();
        if(!(producer instanceof InputsProducer actual))throw new IOException("actual Root invocation input producer has the wrong typed contract");
        return actual.produce();
    }
    @Test void actualImportedOriginalOrPrivateJarAndExactInvocationReachTheSameCommandConsumer()throws Exception {
        var input=actual();input.accepted().verifyCurrent();input.invocation().verify();
        var invocation=RootStartupInvocation.decode(Files.readAllBytes(Path.of(input.invocation().path())));
        var launch=JavaRuntimeLaunch.prepareRoot(input.accepted(),input.invocation());var args=launch.arguments();
        assertEquals(invocation.arguments(),args.subList(args.indexOf("-jar")+2,args.size()));
        assertNotNull(launch.command(input.stdout(),input.stderr(),input.memoryLimitBytes()));launch.verifyCurrent();
        for(Class<?> type:JavaRuntimeLaunch.requiredInvocationSources())assertSame(JavaRuntimeLaunch.class.getClassLoader(),type.getClassLoader());
    }
    @Test void sameBytePhysicalInvocationReplacementCannotRenewAnActualPreparedCommand()throws Exception {
        var input=actual();Path copy=temporary.resolve("invocation.json");Files.copy(Path.of(input.invocation().path()),copy);
        var launch=JavaRuntimeLaunch.prepareRoot(input.accepted(),ControlBuild.FileRef.measure(copy));byte[] original=Files.readAllBytes(copy);
        Files.move(copy,temporary.resolve("retained-invocation.json"));Files.write(copy,original);
        assertThrows(IOException.class,launch::verifyCurrent);
        assertThrows(IOException.class,()->launch.command(input.stdout(),input.stderr(),input.memoryLimitBytes()));
    }
}

