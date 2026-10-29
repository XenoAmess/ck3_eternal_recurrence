package org.xar.ck3.control.build;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.junit.jupiter.engine.JupiterTestEngine;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.engine.support.descriptor.MethodSource;
import org.junit.platform.launcher.core.LauncherConfig;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;
import org.junit.platform.launcher.listeners.SummaryGeneratingListener;

/** Test-scope only: the frozen collector's exact three persistent software suites. */
public final class RawWindowSoftwareRegressionMain {
    private static final Set<String> CLASSES=Set.of(
        RawWindowCollectorTest.class.getName(),RawWindowLocatorTest.class.getName(),RawWindowImageProofTest.class.getName());
    private RawWindowSoftwareRegressionMain() { }
    public record Failure(String uniqueId,String exceptionType,String message) { }
    public record Result(String machineId,String observedAtUtc,String status,List<String> discoveredMethods,
                         long found,long started,long succeeded,long failed,long skipped,long aborted,
                         long containersFailed,long containersSkipped,long containersAborted,List<Failure> failures) { }
    public static void main(String[] args)throws IOException {
        if(args.length!=0)throw new IllegalArgumentException("no arguments; exact frozen three-suite scope");
        var config=LauncherConfig.builder().enableTestEngineAutoRegistration(false)
            .enableLauncherSessionListenerAutoRegistration(false).enableLauncherDiscoveryListenerAutoRegistration(false)
            .enableTestExecutionListenerAutoRegistration(false).enablePostDiscoveryFilterAutoRegistration(false)
            .addTestEngines(new JupiterTestEngine()).build();
        var request=LauncherDiscoveryRequestBuilder.request().selectors(
            DiscoverySelectors.selectClass(RawWindowCollectorTest.class),
            DiscoverySelectors.selectClass(RawWindowLocatorTest.class),
            DiscoverySelectors.selectClass(RawWindowImageProofTest.class))
            .configurationParameter("junit.jupiter.execution.parallel.enabled","false")
            .configurationParameter("junit.jupiter.extensions.autodetection.enabled","false").build();
        var launcher=LauncherFactory.create(config);var plan=launcher.discover(request);var methods=new TreeSet<String>();
        for(var root:plan.getRoots())for(var test:plan.getDescendants(root))if(test.isTest()) {
            var source=test.getSource().orElseThrow(()->new IllegalStateException("MISSING test method source"));
            if(!(source instanceof MethodSource method)||!CLASSES.contains(method.getClassName()))
                throw new IllegalStateException("foreign or non-method test in exact software scope");
            if(!methods.add(method.getClassName()+"#"+method.getMethodName()))
                throw new IllegalStateException("duplicate exact software test");
        }
        if(methods.size()!=26||methods.stream().filter(v->v.startsWith(RawWindowCollectorTest.class.getName()+"#")).count()!=13
            ||methods.stream().filter(v->v.startsWith(RawWindowLocatorTest.class.getName()+"#")).count()!=9
            ||methods.stream().filter(v->v.startsWith(RawWindowImageProofTest.class.getName()+"#")).count()!=4)
            throw new IllegalStateException("MISSING exact 13+9+4 persistent software tests");
        var listener=new SummaryGeneratingListener();launcher.execute(plan,listener);var summary=listener.getSummary();
        var failures=new ArrayList<Failure>();
        for(var failure:summary.getFailures()) {
            Throwable error=failure.getException();String message=String.valueOf(error.getMessage());
            failures.add(new Failure(failure.getTestIdentifier().getUniqueId(),error.getClass().getName(),
                message.length()<=1024?message:message.substring(0,1024)));
        }
        boolean pass=summary.getTestsFoundCount()==26&&summary.getTestsStartedCount()==26&&summary.getTestsSucceededCount()==26
            &&summary.getTestsFailedCount()==0&&summary.getTestsSkippedCount()==0&&summary.getTestsAbortedCount()==0
            &&summary.getContainersFailedCount()==0&&summary.getContainersSkippedCount()==0&&summary.getContainersAbortedCount()==0
            &&summary.getTotalFailureCount()==0;
        var result=new Result(WindowsJobProcess.currentMachineId(),Instant.now().toString(),pass?"PASS":"FAIL",
            List.copyOf(methods),summary.getTestsFoundCount(),summary.getTestsStartedCount(),summary.getTestsSucceededCount(),
            summary.getTestsFailedCount(),summary.getTestsSkippedCount(),summary.getTestsAbortedCount(),
            summary.getContainersFailedCount(),summary.getContainersSkippedCount(),summary.getContainersAbortedCount(),List.copyOf(failures));
        byte[] output=ControlBuild.strictMapper().writeValueAsBytes(result);
        if(output.length>65536)throw new IOException("bounded complete software result exceeded");
        System.out.write(output);System.out.write('\n');System.out.flush();if(!pass)System.exit(2);
    }
}


