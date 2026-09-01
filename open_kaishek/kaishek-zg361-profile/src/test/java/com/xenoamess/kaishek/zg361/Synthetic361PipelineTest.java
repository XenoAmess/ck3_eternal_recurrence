package com.xenoamess.kaishek.zg361;

import com.xenoamess.kaishek.ir.StrictIrCompiler;
import com.xenoamess.kaishek.profile.Ck3Profile11906;
import com.xenoamess.kaishek.runtime.ExecutionContext;
import com.xenoamess.kaishek.runtime.ExecutionStatus;
import com.xenoamess.kaishek.runtime.IrExecutor;
import com.xenoamess.kaishek.runtime.RuntimeKernel;
import com.xenoamess.kaishek.runtime.ScopeContext;
import com.xenoamess.kaishek.runtime.ScopeRef;
import com.xenoamess.kaishek.runtime.DrawTape;
import com.xenoamess.kaishek.syntax.Parser;
import com.xenoamess.kaishek.validator.Diagnostic;
import com.xenoamess.kaishek.validator.Validator;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

/** Offline evidence for the generated 014 script → parser → VM pipeline. */
class Synthetic361PipelineTest {
    @Test
    void generatedTxtTraversesParserValidatorIrAndFiniteRuntime() {
        var result = Synthetic361Pipeline.runGenerated();

        assertTrue(result.parsed().diagnostics().isEmpty(),
                () -> result.parsed().diagnostics().toString());
        assertTrue(result.validationPassed(), () -> result.validation().toString());
        assertEquals(3, result.program().instructions().size());
        assertTrue(result.program().executable(),
                () -> result.program().diagnostics().toString());
        assertEquals(ExecutionStatus.SUCCESS, result.execution().status());
        assertEquals(java.util.List.of("delivered", "appeal_open", "closed"),
                result.execution().value());
        assertTrue(result.syntheticFixture());
    }

    @Test
    void generatedFileRetainsBomAndExactBytesAtFileBoundary() throws Exception {
        Path directory = Files.createTempDirectory("kaishek-zg361-");
        Path file = Synthetic361Fixture.writeTo(directory);
        byte[] expected = Synthetic361Fixture.render();
        assertArrayEquals(expected, Files.readAllBytes(file));
        assertTrue((expected[0] & 0xff) == 0xef && (expected[1] & 0xff) == 0xbb
                && (expected[2] & 0xff) == 0xbf);
        assertArrayEquals(expected, Parser.parse(Files.readAllBytes(file)).emit());
    }

    @Test
    void validatorRejectionPreventsUnknownOperationFromReachingVm() {
        String source = new String(Synthetic361Fixture.render(), StandardCharsets.UTF_8)
                .replace("zg361_014_choose =", "zg361_014_unknown =");
        var result = Synthetic361Pipeline.run(source.getBytes(StandardCharsets.UTF_8));

        assertTrue(result.validation().stream().anyMatch(d ->
                d.code().equals("UNKNOWN_OPCODE")));
        assertFalse(result.program().executable());
        assertEquals(ExecutionStatus.UNSUPPORTED, result.execution().status());
    }

    @Test
    void ck3ProfileRemainsUncertifiedAndCannotExecuteSyntheticScript() {
        var profile = new Ck3Profile11906();
        var parsed = Parser.parse(Synthetic361Fixture.render());
        var validation = Validator.validate(parsed, Synthetic361Fixture.SOURCE_PATH, profile);
        assertTrue(validation.stream().anyMatch(d -> d.code().equals("UNKNOWN_OPCODE")),
                () -> validation.toString());

        var program = StrictIrCompiler.compile(parsed, Synthetic361Fixture.SOURCE_PATH,
                profile.gameProfile());
        assertFalse(program.executable());
        var character = new ScopeRef(com.xenoamess.kaishek.profile.ScopeType.CHARACTER,
                "synthetic-character");
        var context = new ExecutionContext(new ScopeContext(character, character, null), 0,
                DrawTape.of());
        var execution = IrExecutor.execute(program, new RuntimeKernel(profile.opcodeRegistry()), context);
        assertEquals(ExecutionStatus.UNSUPPORTED, execution.status());
        assertTrue(context.variables().isEmpty());
    }
}
