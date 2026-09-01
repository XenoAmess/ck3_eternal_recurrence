package com.xenoamess.kaishek.ir;

import com.xenoamess.kaishek.profile.BuildFingerprint;
import com.xenoamess.kaishek.profile.GameProfile;
import com.xenoamess.kaishek.profile.InputType;
import com.xenoamess.kaishek.profile.OpcodeDescriptor;
import com.xenoamess.kaishek.profile.OpcodeKind;
import com.xenoamess.kaishek.profile.OpcodeRegistry;
import com.xenoamess.kaishek.profile.RandomnessClass;
import com.xenoamess.kaishek.profile.ScopeType;
import com.xenoamess.kaishek.syntax.Parser;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Contract tests for the deliberately small CST-to-IR lowering surface. */
class StrictIrCompilerTest {
    private static final String VERSION = "synthetic-compiler-1";
    private static final BuildFingerprint FINGERPRINT = new BuildFingerprint(
            "compiler-test", VERSION, "c".repeat(64), List.of(), null, null);
    private static final OpcodeDescriptor SET = new OpcodeDescriptor(
            "set_test", VERSION, OpcodeKind.EFFECT, InputType.BLOCK,
            ScopeType.CHARACTER, List.of("name"), RandomnessClass.DETERMINISTIC,
            true, true, true, 1, 1);
    private static final GameProfile PROFILE = new GameProfile(
            "compiler-test", VERSION, FINGERPRINT, new OpcodeRegistry(List.of(SET)),
            Set.of(SET.id()), Map.of(ScopeType.CHARACTER, Set.of(ScopeType.CHARACTER)));

    @Test
    void lowersRegisteredRhsBlockAndCalculatesSourcePosition() {
        byte[] source = "wrapper = {\n  set_test = { name = \"x\" }\n}\n"
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        IrProgram program = StrictIrCompiler.compile(Parser.parse(source), "fixture.txt", PROFILE);

        assertTrue(program.executable(), () -> program.diagnostics().toString());
        assertEquals(1, program.instructions().size());
        IrInstruction instruction = program.instructions().get(0);
        assertEquals("x", ((IrValue.LiteralValue) instruction.namedArguments().get("name")).value());
        assertEquals(2, instruction.sourceSpan().startLine());
        assertEquals(3, instruction.sourceSpan().startColumn());
        assertEquals("fixture.txt", instruction.sourceSpan().source());
    }

    @Test
    void unknownNestedOpcodeIsAnExplicitUnsupportedDiagnostic() {
        byte[] source = "wrapper = {\n  mystery = yes\n}\n"
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        IrProgram program = StrictIrCompiler.compile(Parser.parse(source), "fixture.txt", PROFILE);

        assertFalse(program.executable());
        assertTrue(program.diagnostics().stream().anyMatch(d ->
                d.code().equals("UNSUPPORTED_UNKNOWN_OPCODE")
                        && d.unsupportedReason()
                        == com.xenoamess.kaishek.profile.UnsupportedReason.UNKNOWN_OPCODE),
                () -> program.diagnostics().toString());
    }

    @Test
    void parserErrorBlocksAllInstructionEmission() {
        IrProgram program = StrictIrCompiler.compile(
                Parser.parse("wrapper = {\n  set_test = { name = \"unterminated\n}\n"),
                "fixture.txt", PROFILE);

        assertFalse(program.executable());
        assertTrue(program.instructions().isEmpty());
        assertTrue(program.diagnostics().stream().anyMatch(d ->
                d.code().equals("UNTERMINATED_STRING")),
                () -> program.diagnostics().toString());
    }

    @Test
    void bareListItemCannotBecomeSilentNoOp() {
        byte[] source = "wrapper = {\n  set_test = { bare_value }\n}\n"
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        IrProgram program = StrictIrCompiler.compile(Parser.parse(source), "fixture.txt", PROFILE);

        assertFalse(program.executable());
        assertTrue(program.diagnostics().stream().anyMatch(d ->
                        d.code().equals("UNSUPPORTED_LIST_ITEM")),
                () -> program.diagnostics().toString());
        assertTrue(program.instructions().isEmpty(),
                "invalid block must not emit a partially executable instruction");
    }

    @Test
    void repeatedNamedParameterIsExplicitlyRejectedByMapIrBoundary() {
        byte[] source = "wrapper = {\n  set_test = { name = first name = second }\n}\n"
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        IrProgram program = StrictIrCompiler.compile(Parser.parse(source), "fixture.txt", PROFILE);

        // Validator/CST retain ordered repeated fields.  The Phase 0 IR
        // contract still exposes named arguments as a Map, so lowering must
        // fail closed rather than overwrite either occurrence.
        assertFalse(program.executable());
        assertTrue(program.instructions().isEmpty(),
                "duplicate parameter must not emit a lossy instruction");
        assertTrue(program.diagnostics().stream().anyMatch(d ->
                        d.code().equals("DUPLICATE_PARAMETER")
                                && d.unsupportedReason()
                                == com.xenoamess.kaishek.profile.UnsupportedReason.INVALID_INPUT),
                () -> program.diagnostics().toString());
    }
}
