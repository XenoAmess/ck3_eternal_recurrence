package com.xenoamess.kaishek.ir;

import com.xenoamess.kaishek.profile.*;
import java.util.*;

/** One instruction from the profile allow-list. Unknown instructions cannot be represented as executable IR. */
public record IrInstruction(
        String opcodeId,
        String profileVersion,
        OpcodeKind kind,
        InputType inputType,
        ScopeType requiredScope,
        List<IrValue> positionalArguments,
        Map<String, IrValue> namedArguments,
        SourceSpan sourceSpan,
        Set<String> readSet,
        Set<String> writeSet,
        RandomnessClass randomness,
        UnsupportedReason unsupportedReason) implements IrNode {
    /** Adapter for the lossless parser span type. */
    public IrInstruction(String opcodeId, String profileVersion, OpcodeKind kind, InputType inputType,
                         ScopeType requiredScope, List<IrValue> positionalArguments, Map<String, IrValue> namedArguments,
                         com.xenoamess.kaishek.syntax.SourceSpan sourceSpan, Set<String> readSet, Set<String> writeSet,
                         RandomnessClass randomness, UnsupportedReason unsupportedReason) {
        this(opcodeId, profileVersion, kind, inputType, requiredScope, positionalArguments, namedArguments,
                new SourceSpan("<input>", sourceSpan.start(), sourceSpan.end(), 1, 1, 1, 1), readSet, writeSet, randomness, unsupportedReason);
    }
    public IrInstruction {
        if (opcodeId == null || opcodeId.isBlank()) throw new IllegalArgumentException("opcodeId is blank");
        profileVersion = requireNonBlank(profileVersion, "profileVersion");
        kind = Objects.requireNonNull(kind, "kind"); inputType = Objects.requireNonNull(inputType, "inputType");
        requiredScope = Objects.requireNonNull(requiredScope, "requiredScope");
        positionalArguments = List.copyOf(Objects.requireNonNull(positionalArguments, "positionalArguments"));
        namedArguments = Collections.unmodifiableMap(new LinkedHashMap<>(Objects.requireNonNull(namedArguments, "namedArguments")));
        if (namedArguments.entrySet().stream().anyMatch(e -> e.getKey() == null || e.getKey().isBlank()))
            throw new IllegalArgumentException("blank parameter");
        if (namedArguments.values().stream().anyMatch(Objects::isNull))
            throw new IllegalArgumentException("namedArguments contains null value");
        sourceSpan = Objects.requireNonNull(sourceSpan, "sourceSpan");
        readSet = nonBlankSet(readSet, "readSet"); writeSet = nonBlankSet(writeSet, "writeSet");
        randomness = Objects.requireNonNull(randomness, "randomness");
        if ((unsupportedReason == null) != (randomness != RandomnessClass.UNSUPPORTED))
            throw new IllegalArgumentException(
                    "unsupported reason and randomness classification must agree");
    }
    public static IrInstruction of(OpcodeDescriptor d, SourceSpan span, List<IrValue> args) {
        return new IrInstruction(d.id(), d.profileVersion(), d.kind(), d.inputType(), d.requiredScope(), args,
                Map.of(), span, Set.of(), Set.of(), d.certified() ? d.randomness() : RandomnessClass.UNSUPPORTED,
                d.certified() ? null : UnsupportedReason.NOT_CERTIFIED);
    }
    public boolean executable() { return unsupportedReason == null; }

    private static String requireNonBlank(String value, String name) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is blank");
        return value;
    }

    private static Set<String> nonBlankSet(Set<String> values, String name) {
        Objects.requireNonNull(values, name);
        if (values.stream().anyMatch(v -> v == null || v.isBlank()))
            throw new IllegalArgumentException(name + " contains blank value");
        return Set.copyOf(values);
    }
}
