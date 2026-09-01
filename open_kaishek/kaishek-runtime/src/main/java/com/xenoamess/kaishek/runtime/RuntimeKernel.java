package com.xenoamess.kaishek.runtime;

import com.xenoamess.kaishek.profile.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/** Strict opcode runtime. It executes only registered, certified handlers. */
public final class RuntimeKernel {
    @FunctionalInterface public interface OpcodeHandler { Object apply(Invocation invocation); }
    public record Invocation(String opcode, OpcodeDescriptor descriptor, ExecutionContext context, Map<String,Object> parameters) {
        public Invocation {
            Objects.requireNonNull(opcode);
            Objects.requireNonNull(descriptor);
            Objects.requireNonNull(context);
            // A strict IR literal may intentionally be `null` (`none`).
            // Preserve that value while still isolating the handler from
            // caller mutation; Map.copyOf would reject it before the runtime
            // had a chance to classify the operation.
            parameters = Collections.unmodifiableMap(new LinkedHashMap<>(
                    parameters == null ? Map.of() : parameters));
        }
    }
    private final OpcodeRegistry registry;
    private final Map<String, OpcodeHandler> handlers = new ConcurrentHashMap<>();
    private final HookDispatcher hooks;
    private final CaseRegistry cases;
    public RuntimeKernel(OpcodeRegistry registry) { this(registry, new HookDispatcher(), new CaseRegistry()); }
    public RuntimeKernel(OpcodeRegistry registry, HookDispatcher hooks, CaseRegistry cases) { this.registry = Objects.requireNonNull(registry); this.hooks = Objects.requireNonNull(hooks); this.cases = Objects.requireNonNull(cases); }
    public void register(String opcode, OpcodeHandler handler) {
        if (opcode == null || opcode.isBlank() || handler == null)
            throw new IllegalArgumentException("invalid opcode handler registration");
        if (!registry.contains(opcode)) throw new IllegalArgumentException("unregistered opcode: " + opcode);
        if (handlers.putIfAbsent(opcode, handler) != null)
            throw new IllegalArgumentException("duplicate handler: " + opcode);
    }
    public ExecutionResult<Object> execute(String opcode, ExecutionContext context, Map<String,Object> parameters) {
        if (opcode == null || !registry.contains(opcode)) return ExecutionResult.unsupported("unknown opcode: " + opcode, context == null ? new ExecutionTrace() : context.trace());
        if (context == null) return new ExecutionResult<>(ExecutionStatus.INVALID, null, "null context", new ExecutionTrace());
        OpcodeDescriptor descriptor = registry.require(opcode); OpcodeHandler handler = handlers.get(opcode);
        if (handler == null || !descriptor.certified()) return ExecutionResult.unsupported("opcode is not certified: " + opcode, context.trace());
        if (descriptor.requiredScope() != com.xenoamess.kaishek.profile.ScopeType.GLOBAL && !scopeMatches(descriptor.requiredScope(), context.scopes().current().type()))
            return new ExecutionResult<>(ExecutionStatus.INVALID, null, "required scope: " + descriptor.requiredScope(), context.trace());
        try {
            Object value = handler.apply(new Invocation(opcode, descriptor, context, parameters));
            context.trace().add(opcode, "execute", Map.of("status", "success"));
            return ExecutionResult.success(value, context.trace());
        } catch (DrawTapeExhaustedException e) { context.trace().add(opcode, "unsupported", Map.of("reason", e.getMessage())); return ExecutionResult.unsupported(e.getMessage(), context.trace()); }
          catch (UnsupportedOperationException e) { context.trace().add(opcode, "unsupported", Map.of("reason", e.getMessage())); return ExecutionResult.unsupported(e.getMessage(), context.trace()); }
          catch (IllegalArgumentException e) { return new ExecutionResult<>(ExecutionStatus.INVALID, null, e.getMessage(), context.trace()); }
    }
    private static boolean scopeMatches(com.xenoamess.kaishek.profile.ScopeType required, com.xenoamess.kaishek.profile.ScopeType actual) { return required == actual || (required == com.xenoamess.kaishek.profile.ScopeType.THIS && actual != null); }
    public List<ExecutionResult<?>> dispatchDueEvents(ExecutionContext context) {
        Objects.requireNonNull(context, "context");
        List<ExecutionResult<?>> results = new ArrayList<>(); for (EventEnvelope e : context.dueEvents()) {
            CaseBinding current = cases.get(e.binding().caseId()).orElse(null);
            if (!e.binding().equals(current)) { context.trace().add(e.hook(), "stale", Map.of("sequence", e.sequence())); results.add(new ExecutionResult<>(ExecutionStatus.STALE, null, "stale event ticket", context.trace())); continue; }
            results.add(hooks.dispatch(e.hook(), context.scopes(), e.payload(), context.trace()));
        } return results;
    }
    public HookDispatcher hooks() { return hooks; }
    public CaseRegistry cases() { return cases; }
}
