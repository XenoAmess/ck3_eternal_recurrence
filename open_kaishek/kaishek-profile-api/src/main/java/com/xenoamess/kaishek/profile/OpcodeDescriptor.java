package com.xenoamess.kaishek.profile;

import java.util.List;
import java.util.Objects;

public record OpcodeDescriptor(
        String id,
        String profileVersion,
        OpcodeKind kind,
        InputType inputType,
        ScopeType requiredScope,
        List<String> parameterNames,
        RandomnessClass randomness,
        boolean writesState,
        boolean readsState,
        boolean certified,
        int minParameters,
        int maxParameters) {
    /**
     * Backwards-compatible constructor for descriptors that have no optional
     * parameters.  The explicit arity constructor below is used when a CK3
     * opcode accepts a documented optional argument (for example
     * {@code trigger_event.days}).
     */
    public OpcodeDescriptor(String id, String profileVersion, OpcodeKind kind,
                            InputType inputType, ScopeType requiredScope,
                            List<String> parameterNames, RandomnessClass randomness,
                            boolean writesState, boolean readsState, boolean certified) {
        this(id, profileVersion, kind, inputType, requiredScope, parameterNames,
                randomness, writesState, readsState, certified,
                parameterNames == null ? 0 : parameterNames.size(),
                parameterNames == null ? 0 : parameterNames.size());
    }

    public OpcodeDescriptor {
        if (id == null || id.isBlank() || !id.matches("[A-Za-z0-9_.:-]+"))
            throw new IllegalArgumentException("invalid opcode id");
        profileVersion = requireNonBlank(profileVersion, "profileVersion");
        kind = Objects.requireNonNull(kind, "kind");
        inputType = Objects.requireNonNull(inputType, "inputType");
        requiredScope = Objects.requireNonNull(requiredScope, "requiredScope");
        parameterNames = List.copyOf(Objects.requireNonNull(parameterNames, "parameterNames"));
        if (parameterNames.stream().anyMatch(p -> p == null || p.isBlank()))
            throw new IllegalArgumentException("parameterNames contains blank value");
        if (minParameters < 0 || maxParameters < minParameters)
            throw new IllegalArgumentException("invalid parameter arity");
        randomness = Objects.requireNonNull(randomness, "randomness");
        if (certified && randomness == RandomnessClass.UNSUPPORTED)
            throw new IllegalArgumentException("unsupported opcode cannot be certified");
    }

    private static String requireNonBlank(String value, String name) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is blank");
        return value;
    }
}
