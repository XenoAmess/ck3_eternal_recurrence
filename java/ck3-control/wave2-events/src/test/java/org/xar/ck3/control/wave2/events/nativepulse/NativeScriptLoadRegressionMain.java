package org.xar.ck3.control.wave2.events.nativepulse;

import java.io.PrintWriter;
import java.util.Objects;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;
import org.junit.platform.launcher.listeners.SummaryGeneratingListener;
import org.junit.platform.launcher.listeners.TestExecutionSummary;

/** Runs the retained shared Load regression bodies without a second Maven writer. */
public final class NativeScriptLoadRegressionMain {
    private static final long EXPECTED_METHODS = 17;

    private NativeScriptLoadRegressionMain() { }

    public static void main(String[] arguments) {
        Objects.requireNonNull(arguments);
        if (arguments.length != 0) {
            throw new IllegalArgumentException("test selection is fixed; no arguments accepted");
        }
        String nativeSource = System.getProperty("xar.g2.m2.native03.path");
        if (nativeSource == null || nativeSource.isBlank()) {
            throw new IllegalArgumentException("mandatory retained native03 source property is absent");
        }

        var request = LauncherDiscoveryRequestBuilder.request()
                .selectors(DiscoverySelectors.selectClass(NativeScriptMathProgramTest.class),
                        DiscoverySelectors.selectClass(NativeNamedScriptValueProgramTest.class))
                .build();
        SummaryGeneratingListener listener = new SummaryGeneratingListener();
        Launcher launcher = LauncherFactory.create();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        TestExecutionSummary summary = listener.getSummary();
        PrintWriter output = new PrintWriter(System.out, true);
        summary.printTo(output);
        if (summary.getTestsFoundCount() != EXPECTED_METHODS
                || summary.getTestsStartedCount() != EXPECTED_METHODS
                || summary.getTestsSucceededCount() != EXPECTED_METHODS
                || summary.getTestsFailedCount() != 0
                || summary.getTestsSkippedCount() != 0
                || summary.getTestsAbortedCount() != 0
                || summary.getContainersFailedCount() != 0
                || summary.getContainersAbortedCount() != 0
                || summary.getTotalFailureCount() != 0) {
            summary.printFailuresTo(new PrintWriter(System.err, true));
            throw new IllegalStateException("retained shared Load regression requires all 17 methods to pass");
        }
        output.println("M2_LOAD17_PASS_SOFTWARE_ONLY_NO_GAME_OR_LOADED_SOURCE_QUALIFICATION");
    }
}
