package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.function.Supplier;
import org.xar.ck3.control.contracts.StrictJson;

/** Private dynamic custody after the registered source has approved this exact original Life child. */
final class CompositeContinuationNesting {
    private record Held(String parent, ActionCommand child) { }
    private static final ThreadLocal<Held> CURRENT = new ThreadLocal<>();
    private CompositeContinuationNesting() { }
    static <T> T within(ActionCommand parent, CompositeContinuationToken token, ActionCommand child, Supplier<T> work) {
        if (token.kind() != CompositeContinuationToken.Kind.SUCCESSOR_UI_DATE_ADVANCE) return work.get();
        StrictJson.require(CURRENT.get() == null && child.operation().value().equals("life-advance") && child.origin() instanceof CommandOrigin.Gameplay,
                "only the exact source-approved successor UI Life composite may nest");
        CURRENT.set(new Held(parent.actionId(), child)); try { return work.get(); } finally { CURRENT.remove(); }
    }
    static boolean authorizes(ActionCommand command, List<String> ancestors) {
        Held held = CURRENT.get();
        return held != null && ancestors.size() == 1 && ancestors.getFirst().equals(held.parent())
                && java.util.Arrays.equals(ActionCodec.encodeCommand(held.child()), ActionCodec.encodeCommand(command));
    }
    static boolean authorizesPlanning(ActionCommand command) {
        Held held = CURRENT.get(); return held != null && java.util.Arrays.equals(ActionCodec.encodeCommand(held.child()), ActionCodec.encodeCommand(command));
    }
}
