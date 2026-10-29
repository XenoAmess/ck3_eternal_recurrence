package org.xar.ck3.control.wave2.runtime.savedproof;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** The existing suspended-before-assignment managed Job is the only production launcher. */
public final class WindowsJobSdkMeasurementRunner implements ManagedSdkMeasurementRunner {
    private final Runnable capacityGuard;
    public WindowsJobSdkMeasurementRunner(Runnable capacityGuard) { this.capacityGuard = Objects.requireNonNull(capacityGuard); }
    @Override public Outcome run(SavedProofReadTicket ticket, Path request) throws IOException, InterruptedException {
        StrictJson.require(ticket.machineId().equals(WindowsJobProcess.currentMachineId()), "actual managed host machine");
        Path stdout = ticket.outputRoot().resolve("sdk-" + ticket.nonce() + ".stdout.json");
        Path stderr = ticket.outputRoot().resolve("sdk-" + ticket.nonce() + ".stderr.txt");
        StrictJson.require(!Files.exists(stdout) && !Files.exists(stderr), "create-only managed logs");
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv()); environment.put("PYTHONDONTWRITEBYTECODE", "1"); environment.put("PYTHONUTF8", "1");
        environment.put("TMP", ticket.outputRoot().toString()); environment.put("TEMP", ticket.outputRoot().toString());
        WindowsJobProcess.CommandSpec spec = new WindowsJobProcess.CommandSpec(ticket.pythonExecutable(),
            List.of("-I", "-B", "-X", "utf8", "-c", FixedSdkTransport.PROGRAM, request.toString()),
            ticket.outputRoot(), environment,
            stdout, stderr, ticket.jobMemoryBytes());
        capacityGuard.run();
        try (WindowsJobProcess process = WindowsJobProcess.start(spec)) {
            WindowsJobProcess.CommandResult result = process.await(Duration.ofSeconds(ticket.timeoutSeconds()), ticket.reviewAt(), () -> {
                capacityGuard.run();
                try {
                    StrictJson.require((!Files.exists(stdout) || Files.size(stdout) <= 65_536)
                        && (!Files.exists(stderr) || Files.size(stderr) <= 65_536), "bounded SDK managed logs");
                } catch (IOException error) { throw new IllegalStateException("measurement log guard", error); }
            });
            return new Outcome(result, stdout, stderr);
        }
    }
}
