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

/** Test-scope only: the same-source build bootstrap's exact four accounting and issuer persistent software suites. */
public final class BuildCriticalSoftwareRegressionMain {
    private static final Set<String> CLASSES=Set.of(
        ControlBuildAccountingTest.class.getName(),ManualAttemptCapacityReleaseProducerTest.class.getName(),ManualBuildCapacityReleaseProducerTest.class.getName(),ManualPreparationExceptionSerializationTest.class.getName());
    private BuildCriticalSoftwareRegressionMain() { }
    public record Failure(String uniqueId,String exceptionType,String message) { }
    public enum Scope { CRITICAL_ACCOUNTING_AND_MANUAL_ISSUER_SOFTWARE_ONLY }
    public record Result(String schema,Scope scope,String machineId,String observedAtUtc,String status,List<String> discoveredMethods,
                         long found,long started,long succeeded,long failed,long skipped,long aborted,
                         long containersFailed,long containersSkipped,long containersAborted,List<Failure> failures) { }
    public static void main(String[] args)throws IOException {
        if(args.length!=0)throw new IllegalArgumentException("no arguments; exact frozen four-suite scope");
        var config=LauncherConfig.builder().enableTestEngineAutoRegistration(false)
            .enableLauncherSessionListenerAutoRegistration(false).enableLauncherDiscoveryListenerAutoRegistration(false)
            .enableTestExecutionListenerAutoRegistration(false).enablePostDiscoveryFilterAutoRegistration(false)
            .addTestEngines(new JupiterTestEngine()).build();
        var request=LauncherDiscoveryRequestBuilder.request().selectors(
            DiscoverySelectors.selectClass(ControlBuildAccountingTest.class),
            DiscoverySelectors.selectClass(ManualAttemptCapacityReleaseProducerTest.class),
            DiscoverySelectors.selectClass(ManualBuildCapacityReleaseProducerTest.class),
            DiscoverySelectors.selectClass(ManualPreparationExceptionSerializationTest.class))
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
        if(methods.size()!=21||methods.stream().filter(v->v.startsWith(ControlBuildAccountingTest.class.getName()+"#")).count()!=7
            ||methods.stream().filter(v->v.startsWith(ManualAttemptCapacityReleaseProducerTest.class.getName()+"#")).count()!=7
            ||methods.stream().filter(v->v.startsWith(ManualBuildCapacityReleaseProducerTest.class.getName()+"#")).count()!=6
            ||methods.stream().filter(v->v.startsWith(ManualPreparationExceptionSerializationTest.class.getName()+"#")).count()!=1)
            throw new IllegalStateException("MISSING exact 7+7+6+1 persistent critical software tests");
        var listener=new SummaryGeneratingListener();launcher.execute(plan,listener);var summary=listener.getSummary();
        var failures=new ArrayList<Failure>();
        for(var failure:summary.getFailures()) {
            Throwable error=failure.getException();String message=String.valueOf(error.getMessage());
            failures.add(new Failure(failure.getTestIdentifier().getUniqueId(),error.getClass().getName(),
                message.length()<=1024?message:message.substring(0,1024)));
        }
        boolean pass=summary.getTestsFoundCount()==21&&summary.getTestsStartedCount()==21&&summary.getTestsSucceededCount()==21
            &&summary.getTestsFailedCount()==0&&summary.getTestsSkippedCount()==0&&summary.getTestsAbortedCount()==0
            &&summary.getContainersFailedCount()==0&&summary.getContainersSkippedCount()==0&&summary.getContainersAbortedCount()==0
            &&summary.getTotalFailureCount()==0;
        var result=new Result("xar.build-critical-software-regressions/v1",Scope.CRITICAL_ACCOUNTING_AND_MANUAL_ISSUER_SOFTWARE_ONLY,WindowsJobProcess.currentMachineId(),Instant.now().toString(),pass?"PASS":"FAIL",
            List.copyOf(methods),summary.getTestsFoundCount(),summary.getTestsStartedCount(),summary.getTestsSucceededCount(),
            summary.getTestsFailedCount(),summary.getTestsSkippedCount(),summary.getTestsAbortedCount(),
            summary.getContainersFailedCount(),summary.getContainersSkippedCount(),summary.getContainersAbortedCount(),List.copyOf(failures));
        byte[] output=ControlBuild.strictMapper().writeValueAsBytes(result);
        if(!ControlBuild.strictMapper().readValue(output,Result.class).equals(result))
            throw new IOException("Exact typed software result roundtrip differs");
        if(output.length>65536)throw new IOException("bounded complete software result exceeded");
        System.out.write(output);System.out.write('\n');System.out.flush();if(!pass)System.exit(2);
    }
}


