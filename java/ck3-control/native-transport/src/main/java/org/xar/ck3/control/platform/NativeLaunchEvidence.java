package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;

/** A real bridge build/registration reader must implement this port; no JSON status grants admission. */
public final class NativeLaunchEvidence {
    private NativeLaunchEvidence() { }
    public record Inputs(ControlBuild.FileRef environmentActual, ControlBuild.FileRef buildActual,
            ControlBuild.FileRef registrationActual) {
        public Inputs {
            Objects.requireNonNull(environmentActual); Objects.requireNonNull(buildActual); Objects.requireNonNull(registrationActual);
            if (new HashSet<>(List.of(environmentActual,buildActual,registrationActual)).size() != 3)
                throw new IllegalArgumentException("Three distinct actual native stages required");
        }
        public List<ControlBuild.FileRef> references() { return List.of(environmentActual, buildActual, registrationActual); }
    }
    public record Expected(String machineId, Path sourceRoot, List<ControlBuild.FileRef> completeSources,
            ControlBuild.FileRef bridgeDll, ControlBuild.FileRef injector, Inputs inputs) {
        public Expected {
            Objects.requireNonNull(machineId); Objects.requireNonNull(sourceRoot); Objects.requireNonNull(bridgeDll);
            Objects.requireNonNull(injector); Objects.requireNonNull(inputs); completeSources = List.copyOf(completeSources);
            if (machineId.isBlank() || machineId.equals("unknown") || !sourceRoot.isAbsolute() || completeSources.isEmpty())
                throw new IllegalArgumentException("Exact machine, complete native inputs and selected artifacts required");
        }
    }
    /** All source/tool/runtime/stage/output/registration originals verified by the fixed producer reader. */
    public record Proof(Expected expected, List<ControlBuild.FileRef> completeEvidenceClosure) {
        public Proof {
            Objects.requireNonNull(expected); completeEvidenceClosure = List.copyOf(completeEvidenceClosure);
            if (completeEvidenceClosure.isEmpty() || completeEvidenceClosure.size() > 16384
                    || new HashSet<>(completeEvidenceClosure).size() != completeEvidenceClosure.size()
                    || !completeEvidenceClosure.containsAll(expected.inputs().references())
                    || !completeEvidenceClosure.containsAll(expected.completeSources())
                    || !completeEvidenceClosure.contains(expected.bridgeDll()) || !completeEvidenceClosure.contains(expected.injector()))
                throw new IllegalArgumentException("Complete unique native stage evidence closure required");
        }
    }
    /**
     * This is a required production dependency, with no default or persisted permit loader.
     * Implementations must read actual command owner/exit/timeout/Job0, complete source/tool closure,
     * the exact bridge DLL/injector build outputs, and actual exclusion registration for that injector.
     * Research-only kinship/combat stages and generic Java build receipts cannot satisfy this contract.
     * Root must install the concrete source-reviewed reader; the lifecycle additionally binds its loaded class.
     */
    public interface Port { Proof verify(Expected expected) throws IOException; }
}
