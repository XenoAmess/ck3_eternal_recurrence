package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import org.junit.jupiter.api.Test;

/** Mandatory qualified native integration, deliberately outside default Surefire source patterns. */
public final class Person10NativeCorpusBuildActualRegression {
    /** Mandatory postqualification entry; runs the same persistent @Test bodies with the real JUnit engine. */
    public static void main(String[] args) {
        if(args.length!=0) throw new IllegalArgumentException("No alternate actual test selection allowed");
        var request=org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(Person10NativeCorpusBuildActualRegression.class))
                .configurationParameter("junit.jupiter.execution.parallel.enabled","false").build();
        var listener=new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        org.junit.platform.launcher.core.LauncherFactory.create().execute(request,listener);
        var summary=listener.getSummary();
        summary.printTo(new java.io.PrintWriter(System.out,true));
        summary.printFailuresTo(new java.io.PrintWriter(System.err,true));
        if(summary.getTestsFoundCount()!=1 || summary.getTestsStartedCount()!=1
                || summary.getTestsSucceededCount()!=1 || summary.getTestsFailedCount()!=0
                || summary.getTestsSkippedCount()!=0 || summary.getTestsAbortedCount()!=0
                || summary.getContainersFailedCount()!=0 || summary.getTotalFailureCount()!=0)
            throw new IllegalStateException("Mandatory actual integration requires exactly 1 successes without failures/skips/aborts");
        System.out.println("PASS_PERSON10_ACTUAL_JUNIT_1");
    }
    @Test void allTenNativeProducersReachTheSamePinnedCorpusConsumedByJavaPersonRegression() throws Exception {
        String root = System.getProperty("xar.person10.nativeCorpus"), manifestPath = System.getProperty("xar.person10.nativeCorpus.manifest"),
                sha = System.getProperty("xar.person10.nativeCorpus.manifest.sha256");
        assertNotNull(root, "NOT_EXECUTED: actual Person10 native corpus required");
        assertNotNull(manifestPath, "NOT_EXECUTED: actual original manifest required");
        assertNotNull(sha, "NOT_EXECUTED: pinned manifest digest required");
        var manifest = ControlBuild.FileRef.measure(Path.of(manifestPath)); assertEquals(sha, manifest.sha256());
        var parsed = Person10NativeCorpus.require(manifest, root);
        Path originalReceipt = Path.of(manifestPath).getParent().resolve(Person10NativeCorpusBuild.ACTUAL_NAME);
        assertTrue(Files.isRegularFile(originalReceipt), "NOT_EXECUTED: native producer actual receipt missing");
        var actual = Person10NativeCorpusBuild.readProduced(ControlBuild.FileRef.measure(originalReceipt));
        assertEquals(Person10NativeCorpusBuild.Status.PASS, actual.status()); assertEquals(manifest, actual.corpusManifest());
        assertEquals(Person10NativeCorpusBuild.SCOPE, actual.scope()); assertEquals(10, actual.produced().size());
        assertEquals(83, parsed.files().size()); assertEquals(12, actual.commands().size());
        assertEquals(new HashSet<>(parsed.files()), new HashSet<>(actual.produced().stream().flatMap(p -> p.packets().stream()).toList()));
        assertFalse(actual.sourceRefs().isEmpty()); assertFalse(actual.toolsAndRuntime().isEmpty());
    }
}

