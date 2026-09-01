package com.xenoamess.kaishek.runtime;

import com.xenoamess.kaishek.ir.IrInstruction;
import com.xenoamess.kaishek.ir.IrProgram;
import com.xenoamess.kaishek.ir.IrValue;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Small sequential executor for an already-lowered strict IR program.
 *
 * <p>The executor performs an executable preflight before invoking the
 * kernel.  Consequently an unknown, malformed, or uncertified instruction
 * cannot execute a prefix of the program and then silently disappear.  This
 * is intentionally a finite fixture runner, not a CK3 scheduler.</p>
 */
public final class IrExecutor {
    private IrExecutor() { }

    public static ExecutionResult<List<Object>> execute(IrProgram program,
                                                         RuntimeKernel kernel,
                                                         ExecutionContext context) {
        Objects.requireNonNull(program, "program");
        Objects.requireNonNull(kernel, "kernel");
        if (context == null) {
            return new ExecutionResult<>(ExecutionStatus.INVALID, null,
                    "null context", new ExecutionTrace());
        }
        if (!program.executable()) {
            String reason = program.diagnostics().stream()
                    .filter(d -> d.severity() == com.xenoamess.kaishek.ir.DiagnosticSeverity.ERROR)
                    .findFirst()
                    .map(d -> d.code() + ": " + d.message())
                    .orElse("IR program contains unsupported instructions");
            context.trace().add("<ir>", "unsupported", Map.of("reason", reason));
            return ExecutionResult.unsupported(reason, context.trace());
        }

        List<Object> values = new ArrayList<>(program.instructions().size());
        for (IrInstruction instruction : program.instructions()) {
            Map<String, Object> parameters;
            try {
                parameters = materializeParameters(instruction, context);
            } catch (UnsupportedOperationException e) {
                context.trace().add(instruction.opcodeId(), "unsupported",
                        Map.of("reason", e.getMessage() == null ? "unsupported value" : e.getMessage()));
                return ExecutionResult.unsupported(e.getMessage(), context.trace());
            } catch (IllegalArgumentException e) {
                return new ExecutionResult<>(ExecutionStatus.INVALID, null,
                        e.getMessage(), context.trace());
            }
            ExecutionResult<Object> result = kernel.execute(instruction.opcodeId(), context, parameters);
            if (!result.isSuccess()) {
                return new ExecutionResult<>(result.status(), null, result.reason(), result.trace());
            }
            values.add(result.value());
        }
        return ExecutionResult.success(Collections.unmodifiableList(new ArrayList<>(values)),
                context.trace());
    }

    private static Map<String, Object> materializeParameters(IrInstruction instruction,
                                                              ExecutionContext context) {
        Map<String, Object> parameters = new LinkedHashMap<>();
        for (Map.Entry<String, IrValue> entry : instruction.namedArguments().entrySet()) {
            parameters.put(entry.getKey(), materialize(entry.getValue(), context));
        }
        if (!instruction.positionalArguments().isEmpty()) {
            List<Object> positional = new ArrayList<>(instruction.positionalArguments().size());
            for (IrValue value : instruction.positionalArguments())
                positional.add(materialize(value, context));
            parameters.put("$positional", Collections.unmodifiableList(
                    new ArrayList<>(positional)));
        }
        return parameters;
    }

    private static Object materialize(IrValue value, ExecutionContext context) {
        return switch (value) {
            case IrValue.LiteralValue literal -> literal.value();
            case IrValue.ListValue list -> list.values().stream()
                    .map(item -> materialize(item, context)).toList();
            case IrValue.ScopeRef scope -> {
                ScopeRef resolved = context.scopes().resolve(scope.name());
                if (resolved == null)
                    throw new UnsupportedOperationException("unresolved scope reference: " + scope.name());
                yield resolved;
            }
            case IrValue.VariableRef variable -> context.get(variable.name())
                    .map(TypedValue::value)
                    .orElseThrow(() -> new UnsupportedOperationException(
                            "unresolved variable reference: " + variable.name()));
        };
    }
}
