package com.xenoamess.kaishek.ir;

import com.xenoamess.kaishek.profile.*;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Strict IR must preserve profile identity and expose unsupported semantics. */
class IrContractTest {
    private static final String HASH = "b".repeat(64);
    private static final BuildFingerprint FINGERPRINT =
            new BuildFingerprint("ck3", "1.19.0.6", HASH, List.of(), null, null);
    private static final OpcodeDescriptor DESCRIPTOR = new OpcodeDescriptor(
            "effect.test", "1.19.0.6", OpcodeKind.EFFECT, InputType.NONE,
            ScopeType.THIS, List.of(), RandomnessClass.DETERMINISTIC,
            true, true, false);

    @Test
    void uncertifiedDescriptorBecomesExplicitlyUnsupportedInstruction() {
        var instruction = IrInstruction.of(DESCRIPTOR, SourceSpan.unknown("fixture"), List.of());
        assertFalse(instruction.executable());
        assertEquals(RandomnessClass.UNSUPPORTED, instruction.randomness());
        assertEquals(UnsupportedReason.NOT_CERTIFIED, instruction.unsupportedReason());
        var program = new IrProgram("ck3-1.19.0.6", "1.19.0.6", FINGERPRINT,
                List.of(instruction), List.of());
        assertFalse(program.executable());
    }

    @Test
    void instructionRejectsInconsistentRandomnessAndUnsupportedReason() {
        assertThrows(IllegalArgumentException.class, () -> new IrInstruction(
                "effect.test", "1.19.0.6", OpcodeKind.EFFECT, InputType.NONE,
                ScopeType.THIS, List.of(), Map.of(), SourceSpan.unknown("fixture"),
                Set.of(), Set.of(), RandomnessClass.UNSUPPORTED, null));
        assertThrows(IllegalArgumentException.class, () -> new IrValue.LiteralValue(Double.NaN));
    }
}
