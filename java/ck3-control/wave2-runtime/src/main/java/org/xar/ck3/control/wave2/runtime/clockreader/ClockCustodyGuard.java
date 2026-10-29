package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.AttemptFingerprint;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.ContentEvidenceRef;
import org.xar.ck3.control.reconciliation.LateOutcome.Scope;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockPinnedFiles.Pin;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.KernelProcessProbe;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ProcessObservation;

/** Source and live-process consistency adapter. Existing original Queue/native qualification stays authoritative. */
public final class ClockCustodyGuard {
    @FunctionalInterface public interface MachineIdentityReader { String currentMachineId() throws IOException; }
    public enum Role { MACHINE_RECEIPT, CLOSURE, JAVA_BUILD, PROVIDER, QUALIFICATION, ORIGINAL_FAILURE,
        EXPECTED_HEAD, GAME_EXECUTABLE, QUEUE_EXECUTABLE, APPLICATION_EXECUTABLE, QUEUE_SOURCE }
    public record Source(Role role, Pin pin) { public Source { Objects.requireNonNull(role); Objects.requireNonNull(pin); } }
    public record Observation(Scope scope, ProcessObservation game, ProcessObservation queue, ProcessObservation application) {
        public Observation { Objects.requireNonNull(scope); Objects.requireNonNull(game); Objects.requireNonNull(queue); Objects.requireNonNull(application); }
    }
    private final Attempt admitted;
    private final Map<Role, Pin> pins;
    private final KernelProcessProbe probe;
    private final MachineIdentityReader machine;
    private final java.util.EnumSet<Role> verifiedBinaries = java.util.EnumSet.noneOf(Role.class);
    public ClockCustodyGuard(Attempt admitted, List<Source> sources, KernelProcessProbe probe) {
        this(admitted, sources, probe, org.xar.ck3.control.build.WindowsJobProcess::currentMachineId);
    }
    public ClockCustodyGuard(Attempt admitted, List<Source> sources, KernelProcessProbe probe, MachineIdentityReader machine) {
        this.admitted = Objects.requireNonNull(admitted); this.probe = Objects.requireNonNull(probe);
        this.machine = Objects.requireNonNull(machine);
        EnumMap<Role, Pin> collected = new EnumMap<>(Role.class);
        for (Source source : List.copyOf(sources)) { StrictJson.require(collected.put(source.role(), source.pin()) == null, "unique source role"); }
        StrictJson.require(collected.keySet().equals(Set.of(Role.values())), "all actual source and custody pins required");
        this.pins = Map.copyOf(collected);
        var s = admitted.scope().source();
        same(Role.CLOSURE, s.closureSha256()); same(Role.JAVA_BUILD, s.javaBuildSha256()); same(Role.PROVIDER, s.providerSha256());
        same(Role.QUALIFICATION, s.qualificationReceiptSha256()); same(Role.GAME_EXECUTABLE, s.executableSha256());
        evidence(Role.ORIGINAL_FAILURE, admitted.original().receipt()); evidence(Role.EXPECTED_HEAD, admitted.expectedHead());
    }
    public synchronized Observation verify(Attempt expected) throws IOException {
        ClockPinnedFiles.require(AttemptFingerprint.sha256(admitted).equals(AttemptFingerprint.sha256(expected)), "different admitted attempt");
        ClockPinnedFiles.require(expected.scope().machineId().equals(machine.currentMachineId()), "actual host machine differs from admitted attempt");
        // These are actual bounded reads and kernel measurements, not success flags supplied by a caller.
        for (Map.Entry<Role, Pin> entry : pins.entrySet()) {
            if (binary(entry.getKey())) {
                if (!verifiedBinaries.contains(entry.getKey())) { ClockPinnedFiles.verifyStreaming(entry.getValue(), 1024L * 1024 * 1024); }
                else { ClockPinnedFiles.verifyContentStamp(entry.getValue()); }
                continue;
            }
            byte[] raw = ClockPinnedFiles.read(entry.getValue(), maximum(entry.getKey()));
            if (entry.getKey() == Role.MACHINE_RECEIPT) {
                JsonNode machine = StrictJson.parse(raw);
                ClockPinnedFiles.require(machine.isObject() && expected.scope().machineId().equals(StrictJson.text(machine.get("machine_id"))), "machine receipt differs");
            }
        }
        ProcessObservation game = probe.observe(expected.scope().game().pid());
        ProcessObservation queue = probe.observe(expected.scope().queue().pid());
        ProcessObservation application = probe.observe(expected.scope().application().pid());
        ClockPinnedFiles.require(game.identity().equals(expected.scope().game()) && queue.identity().equals(expected.scope().queue())
                && application.identity().equals(expected.scope().application()), "kernel PID/birth identity changed");
        executable(game, Role.GAME_EXECUTABLE); executable(queue, Role.QUEUE_EXECUTABLE); executable(application, Role.APPLICATION_EXECUTABLE);
        verifiedBinaries.addAll(java.util.EnumSet.of(Role.PROVIDER, Role.GAME_EXECUTABLE, Role.QUEUE_EXECUTABLE, Role.APPLICATION_EXECUTABLE));
        return new Observation(expected.scope(), game, queue, application);
    }
    private void same(Role role, String sha) { StrictJson.require(pins.get(role).sha256().equals(sha), "source role digest mismatch: " + role); }
    private void evidence(Role role, ContentEvidenceRef reference) {
        same(role, reference.sha256());
        StrictJson.require(pins.get(role).bytes() == reference.bytes(), "source role length mismatch: " + role);
    }
    private void executable(ProcessObservation measured, Role role) throws IOException {
        Path actual = measured.executable().toRealPath();
        ClockPinnedFiles.require(actual.equals(pins.get(role).contentStamp().realPath()), "actual process executable differs from admitted pin");
    }
    private static int maximum(Role role) {
        return switch (role) {
            case MACHINE_RECEIPT, ORIGINAL_FAILURE, EXPECTED_HEAD -> 65_536;
            case CLOSURE, JAVA_BUILD, QUALIFICATION, QUEUE_SOURCE -> 2 * 1024 * 1024;
            case PROVIDER, GAME_EXECUTABLE, QUEUE_EXECUTABLE, APPLICATION_EXECUTABLE -> throw new IllegalStateException("source binary uses streaming budget");
        };
    }
    private static boolean binary(Role role) {
        return role == Role.PROVIDER || role == Role.GAME_EXECUTABLE || role == Role.QUEUE_EXECUTABLE || role == Role.APPLICATION_EXECUTABLE;
    }
}
