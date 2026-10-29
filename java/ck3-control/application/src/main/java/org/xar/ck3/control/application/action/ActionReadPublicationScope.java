package org.xar.ck3.control.application.action;

import java.util.function.Supplier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Pre-INTENT producers call this actual Root barrier before irreversible claims or pending imports. No publication is performed here. */
public final class ActionReadPublicationScope {
    private record Held(ActionJournal.LockedJournal journal, ActionCommand command, ActionPorts.IntentBarrierPort barrier) { }
    private static final ThreadLocal<Held> CURRENT = new ThreadLocal<>();
    private ActionReadPublicationScope() { }
    public static void requireClearBeforeIntent(ContinuityStorePort.Session same, ActionCommand command) throws java.io.IOException {
        Held held = CURRENT.get();
        StrictJson.require(held != null && held.journal().writerSession() == same
                && java.util.Arrays.equals(ActionCodec.encodeCommand(held.command()), ActionCodec.encodeCommand(command))
                && ActionCommandScope.current().filter(command::equals).isPresent() && held.journal().find(command.actionId()).isEmpty(),
                "READ preparation barrier escaped its original pre-INTENT writer/command scope");
        same.head(); // The actual writer rejects an escaped or foreign-thread Session before a claim can be consumed.
        held.barrier().check(same, command);
    }
    static <T> T within(ActionJournal.LockedJournal journal, ActionCommand command, ActionPorts.IntentBarrierPort barrier, Supplier<T> work) {
        Held previous = CURRENT.get(); CURRENT.set(new Held(journal, command, barrier));
        try { return work.get(); } finally { if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
