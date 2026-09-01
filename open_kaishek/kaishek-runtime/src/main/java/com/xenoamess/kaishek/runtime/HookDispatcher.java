package com.xenoamess.kaishek.runtime;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.BiFunction;

/** Explicit hook allow-list. Missing hooks fail closed as UNSUPPORTED. */
public final class HookDispatcher {
    public record HookInvocation(String name, ScopeContext context, Map<String, Object> payload) {
        public HookInvocation { Objects.requireNonNull(name); Objects.requireNonNull(context); payload = Map.copyOf(payload == null ? Map.of() : payload); }
    }
    @FunctionalInterface public interface Hook extends BiFunction<HookInvocation, ExecutionTrace, ExecutionResult<?>> { }
    private final Map<String, Hook> hooks = new ConcurrentHashMap<>();
    public void register(String name, Hook hook) { if (name == null || name.isBlank() || hook == null) throw new IllegalArgumentException("invalid hook"); if (hooks.putIfAbsent(name, hook) != null) throw new IllegalArgumentException("duplicate hook: " + name); }
    public boolean contains(String name) { return name != null && hooks.containsKey(name); }
    public ExecutionResult<?> dispatch(String name, ScopeContext context, Map<String, Object> payload, ExecutionTrace trace) {
        ExecutionTrace out = trace == null ? new ExecutionTrace() : trace;
        if (context == null) return new ExecutionResult<>(ExecutionStatus.INVALID, null, "null scope context", out);
        // ConcurrentHashMap rejects null keys. Treat a missing/blank hook name as
        // an ordinary unsupported dispatch instead of leaking that implementation
        // detail as a NullPointerException.
        if (name == null || name.isBlank()) {
            out.add("<null>", "unsupported", Map.of("reason", "unregistered hook"));
            return ExecutionResult.unsupported("unregistered hook: " + name, out);
        }
        Hook hook = hooks.get(name);
        if (hook == null) { out.add(name == null ? "<null>" : name, "unsupported", Map.of("reason", "unregistered hook")); return ExecutionResult.unsupported("unregistered hook: " + name, out); }
        try { ExecutionResult<?> result = hook.apply(new HookInvocation(name, context, payload), out);
            if (result == null) { out.add(name, "unsupported", Map.of("reason", "hook returned null")); return ExecutionResult.unsupported("hook returned null", out); }
            return result; }
        catch (DrawTapeExhaustedException e) {
            out.add(name, "unsupported", Map.of("reason", e.getMessage()));
            return ExecutionResult.unsupported(e.getMessage(), out);
        }
        catch (UnsupportedOperationException e) {
            out.add(name, "unsupported", Map.of("reason", reason(e, "unsupported hook operation")));
            return ExecutionResult.unsupported(reason(e, "unsupported hook operation"), out);
        }
        catch (IllegalArgumentException e) {
            return new ExecutionResult<>(ExecutionStatus.INVALID, null,
                    reason(e, "invalid hook input"), out);
        }
    }

    private static String reason(RuntimeException exception, String fallback) {
        return exception.getMessage() == null || exception.getMessage().isBlank()
                ? fallback : exception.getMessage();
    }
}
