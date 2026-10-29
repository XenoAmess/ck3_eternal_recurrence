package org.xar.ck3.control.wave2.runtime.savedproof;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Execution boundary; test doubles must not issue production measurement tokens. */
@FunctionalInterface
public interface ManagedSdkMeasurementRunner {
    Outcome run(SavedProofReadTicket ticket, Path request) throws IOException, InterruptedException;
    record Outcome(WindowsJobProcess.CommandResult command, Path stdout, Path stderr) {
        public Outcome { Objects.requireNonNull(command); Objects.requireNonNull(stdout); Objects.requireNonNull(stderr); }
    }
}
