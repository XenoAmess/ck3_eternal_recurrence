package com.xenoamess.kaishek.zg361;

import com.xenoamess.kaishek.ir.IrProgram;
import com.xenoamess.kaishek.ir.StrictIrCompiler;
import com.xenoamess.kaishek.runtime.ExecutionContext;
import com.xenoamess.kaishek.runtime.ExecutionResult;
import com.xenoamess.kaishek.runtime.ExecutionTrace;
import com.xenoamess.kaishek.runtime.IrExecutor;
import com.xenoamess.kaishek.runtime.RuntimeKernel;
import com.xenoamess.kaishek.runtime.ScopeContext;
import com.xenoamess.kaishek.runtime.ScopeRef;
import com.xenoamess.kaishek.syntax.ParseResult;
import com.xenoamess.kaishek.syntax.Parser;
import com.xenoamess.kaishek.validator.Diagnostic;
import com.xenoamess.kaishek.validator.Validator;

import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * End-to-end offline pipeline for the synthetic 014 slice:
 * generated `.txt` bytes → parser → schema validator → strict IR → finite VM.
 *
 * <p>The pipeline is intentionally tagged synthetic in its result and uses a
 * non-CK3 profile.  It is suitable for contract/property tests only; it does
 * not start CK3, call MCP, or certify native semantics.</p>
 */
public final class Synthetic361Pipeline {
    private Synthetic361Pipeline() { }

    public static Result runGenerated() {
        return run(Synthetic361Fixture.render());
    }

    public static Result run(byte[] source) {
        Objects.requireNonNull(source, "source");
        Synthetic361Profile profile = new Synthetic361Profile();
        ParseResult parsed = Parser.parse(source);
        List<Diagnostic> validation = Validator.validate(
                parsed, Synthetic361Fixture.SOURCE_PATH, profile);
        IrProgram program = StrictIrCompiler.compile(parsed,
                Synthetic361Fixture.SOURCE_PATH, profile.gameProfile());

        ExecutionResult<List<Object>> execution;
        boolean valid = validation.stream().noneMatch(d ->
                d.severity() == Diagnostic.Severity.ERROR);
        if (!valid || !program.executable()) {
            ExecutionTrace trace = new ExecutionTrace();
            String reason = !valid ? "validator rejected synthetic slice"
                    : "strict IR is not executable";
            trace.add("<pipeline>", "unsupported", Map.of("reason", reason));
            execution = ExecutionResult.unsupported(reason, trace);
        } else {
            ScopeRef character = new ScopeRef(
                    com.xenoamess.kaishek.profile.ScopeType.CHARACTER, "synthetic-character");
            ExecutionContext context = new ExecutionContext(
                    new ScopeContext(character, character, null), 0,
                    com.xenoamess.kaishek.runtime.DrawTape.of());
            RuntimeKernel kernel = new RuntimeKernel(profile.opcodeRegistry());
            Synthetic361Runtime.install(kernel);
            execution = IrExecutor.execute(program, kernel, context);
        }
        return new Result(source.clone(), parsed, List.copyOf(validation), program, execution);
    }

    public record Result(byte[] source, ParseResult parsed,
                         List<Diagnostic> validation,
                         IrProgram program,
                         ExecutionResult<List<Object>> execution) {
        public Result {
            source = source.clone();
            validation = List.copyOf(validation);
            Objects.requireNonNull(parsed, "parsed");
            Objects.requireNonNull(program, "program");
            Objects.requireNonNull(execution, "execution");
        }

        /** Keep the record's byte payload immutable at the API boundary. */
        @Override public byte[] source() { return source.clone(); }

        public boolean validationPassed() {
            return validation.stream().noneMatch(d ->
                    d.severity() == Diagnostic.Severity.ERROR);
        }

        public boolean syntheticFixture() { return true; }
    }
}
