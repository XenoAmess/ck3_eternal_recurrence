package com.xenoamess.kaishek.zg361;

import com.xenoamess.kaishek.runtime.ExecutionContext;
import com.xenoamess.kaishek.runtime.RuntimeKernel;

import java.util.Map;
import java.util.Objects;

/**
 * Handlers for the synthetic 014 lifecycle.  They are deliberately separate
 * from the CK3 profile and mutate only namespaced fixture variables, making
 * the test useful without implying any native or product-live capability.
 */
public final class Synthetic361Runtime {
    public static final String STATE = "zg361.synthetic.014.state";
    public static final String CASE_ID = "zg361.synthetic.014.case_id";
    public static final String CHOICE = "zg361.synthetic.014.choice";

    private Synthetic361Runtime() { }

    /** Install exactly the three certified fixture handlers. */
    public static void install(RuntimeKernel kernel) {
        Objects.requireNonNull(kernel, "kernel");
        kernel.register(Synthetic361Profile.OPEN_CASE,
                invocation -> open(invocation.context(), invocation.parameters()));
        kernel.register(Synthetic361Profile.CHOOSE,
                invocation -> choose(invocation.context(), invocation.parameters()));
        kernel.register(Synthetic361Profile.CLOSE_CASE,
                invocation -> close(invocation.context(), invocation.parameters()));
    }

    private static String open(ExecutionContext context, Map<String, Object> parameters) {
        if (context.has(STATE)) throw new IllegalArgumentException("case is already open");
        String id = requiredString(parameters, "case_id");
        context.set(CASE_ID, id);
        context.set(STATE, "delivered");
        return "delivered";
    }

    private static String choose(ExecutionContext context, Map<String, Object> parameters) {
        String state = currentState(context);
        if (!"delivered".equals(state))
            throw new IllegalArgumentException("choice requires delivered state");
        String choice = requiredString(parameters, "choice");
        if (!choice.equals("a") && !choice.equals("b") && !choice.equals("c"))
            throw new IllegalArgumentException("choice must be a, b or c");
        context.set(CHOICE, choice);
        context.set(STATE, "appeal_open");
        return "appeal_open";
    }

    private static String close(ExecutionContext context, Map<String, Object> parameters) {
        String state = currentState(context);
        if (!"appeal_open".equals(state))
            throw new IllegalArgumentException("close requires appeal_open state");
        if (!parameters.isEmpty())
            throw new IllegalArgumentException("close does not accept parameters");
        context.set(STATE, "closed");
        return "closed";
    }

    private static String currentState(ExecutionContext context) {
        return context.get(STATE)
                .map(value -> {
                    if (value.value() instanceof String state) return state;
                    throw new IllegalArgumentException("state has wrong type");
                })
                .orElseThrow(() -> new IllegalArgumentException("case is not open"));
    }

    private static String requiredString(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        if (!(value instanceof String string) || string.isBlank())
            throw new IllegalArgumentException(name + " must be a non-blank string");
        return string;
    }
}
