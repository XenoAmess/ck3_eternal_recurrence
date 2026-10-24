package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

/** Metadata production only; actual request, native ownership and caller validators remain authoritative. */
public final class CaptureRequestPreparation {
    public record Prepared(Path recipePath, Path requestPath, Path resultPath, Instant reviewDeadline,
            ControlBuild.FileRef bindingRef, ControlBuild.FileRef standingRef,
            List<ControlBuild.FileRef> explicitInputs) {
        public Prepared {
            explicitInputs = List.copyOf(explicitInputs);
            if (!recipePath.getParent().equals(requestPath.getParent()) || !recipePath.getParent().equals(resultPath.getParent()))
                throw new IllegalArgumentException("One family parent required");
        }
    }
    private CaptureRequestPreparation() { }

    /**
     * One issuer-owned parent and one exact current binding produce all finite artifact paths,
     * the actual review deadline (never observed_at_utc), and outer inputs without its implicit executable.
     * No command starts and no runtime permission is granted.
     */
    public static Prepared prepare(Path ownedParent, String stem, ControlBuild.FileRef bindingRef,
            ControlBuild.FileRef executable, List<ControlBuild.FileRef> explicitInputs) throws IOException {
        Path parent = CompiledOriginalCaptureProfile.directory(ownedParent.toString());
        if (stem == null || !stem.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,59}")) throw new IOException("Finite artifact stem required");
        var binding = SharedOwnedCommandBinding.read(bindingRef);
        binding.standingRef().verify();
        if (binding.standingRef().bytes() > (64 << 10)) throw new IOException("Bounded standing metadata required");
        var standing = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(binding.standingRef().path())));
        SharedOwnedCommandBinding.verifyAuthority(standing, binding.standingExpectation(), binding.machineId());
        var deadlineField = standing.get("review_at_utc");
        if (deadlineField == null || !deadlineField.isTextual()) throw new IOException("Standing review deadline required");
        final Instant deadline;
        try { deadline = Instant.parse(deadlineField.textValue()); }
        catch (java.time.format.DateTimeParseException error) { throw new IOException("Canonical standing review deadline required", error); }
        if (!Instant.now().isBefore(deadline)) throw new IOException("Standing review deadline expired");
        binding.standingRef().verify(); bindingRef.verify();

        executable = CompiledOriginalCaptureProfile.ref(executable);
        if (explicitInputs == null || explicitInputs.size() > 512) throw new IOException("Finite explicit outer inputs required");
        Path executablePath = Path.of(executable.path());
        var seen = new HashSet<Path>(); var inputs = new ArrayList<ControlBuild.FileRef>();
        for (var input : explicitInputs) {
            CompiledOriginalCaptureProfile.ref(input);
            Path path = Path.of(input.path());
            if (path.equals(executablePath)) {
                if (input.bytes() != executable.bytes() || !input.sha256().equals(executable.sha256()))
                    throw new IOException("Implicit executable and explicit source identity conflict");
                continue;
            }
            if (!seen.add(path)) throw new IOException("Repeated explicit outer input path");
            inputs.add(input);
        }
        return new Prepared(parent.resolve(stem + "-SELECTION.json"), parent.resolve(stem + "-REQUEST.json"),
                parent.resolve(stem + "-RESULT.json"), deadline, bindingRef, binding.standingRef(), inputs);
    }
}

