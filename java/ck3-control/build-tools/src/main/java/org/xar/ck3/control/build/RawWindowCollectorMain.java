package org.xar.ck3.control.build;

import java.nio.file.Path;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** One actual build-tools entry for M0..M7. Root supplies a new finite admission, never an old inline template. */
public final class RawWindowCollectorMain {
    private RawWindowCollectorMain() { }
    public static void main(String[] args) throws java.io.IOException {
        int exit; String machine = "unknown";
        byte[] output;
        try {
            machine = WindowsJobProcess.currentMachineId();
            if (args.length != 1) throw new IllegalArgumentException("one absolute fresh admission JSON path required");
            var original = RawWindowCaptureJson.readOriginal(Path.of(args[0]), 65_536);
            Admission admission = RawWindowCaptureJson.decode(original.bytes(), Admission.class, 65_536);
            CaptureOutcome result = RawWindowCollector.capture(admission, original.reference());
            output = RawWindowCaptureJson.encode(result);
            exit = result.status() == Status.COMPLETE && result.fallbackFinalDurable() && result.body().published() ? 0 : 1;
        } catch (java.io.IOException | RuntimeException failure) {
            output = RawWindowCaptureJson.encode(new RawWindowCaptureJson.CliFailure(CLI_FAILURE_SCHEMA, machine, java.time.Instant.now().toString(), "REJECTED_OR_UNAVAILABLE",
                    shortError(failure.toString()))); exit = 2;
        }
        System.out.write(output); System.out.write('\n'); System.out.flush();
        if (exit != 0) System.exit(exit);
    }
}
