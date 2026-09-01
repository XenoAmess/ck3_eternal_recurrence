package com.xenoamess.kaishek.ir;

import com.xenoamess.kaishek.profile.BuildFingerprint;
import java.util.*;

public record IrProgram(String profileId, String profileVersion, BuildFingerprint fingerprint,
                        List<IrInstruction> instructions, List<Diagnostic> diagnostics) {
    public IrProgram {
        if (profileId == null || profileId.isBlank()) throw new IllegalArgumentException("profileId is blank");
        profileVersion = requireNonBlank(profileVersion, "profileVersion"); fingerprint = Objects.requireNonNull(fingerprint, "fingerprint");
        instructions = List.copyOf(Objects.requireNonNull(instructions, "instructions"));
        diagnostics = List.copyOf(Objects.requireNonNull(diagnostics, "diagnostics"));
        final String version = profileVersion;
        if (instructions.stream().anyMatch(i -> !version.equals(i.profileVersion())))
            throw new IllegalArgumentException("instruction profile version mismatch");
    }
    public boolean executable() { return diagnostics.stream().noneMatch(d -> d.severity() == DiagnosticSeverity.ERROR)
            && instructions.stream().allMatch(IrInstruction::executable); }

    private static String requireNonBlank(String value, String name) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is blank");
        return value;
    }
}
