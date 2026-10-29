package org.xar.ck3.control.application.action;

import java.io.IOException;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** The one actual primitive preparation while its pre-INTENT domain producer owns the original writer. */
public final class ActionPreparationScope {
    private record Held(ContinuityStorePort.Session session, ActionCommand command, NativeRequest prepared) { }
    private static final ThreadLocal<Held> CURRENT = new ThreadLocal<>();
    private ActionPreparationScope() { }
    public static NativeRequest requirePrepared(ContinuityStorePort.Session same, ActionCommand command) throws IOException {
        Held held = CURRENT.get();
        StrictJson.require(held != null && held.session() == same && java.util.Arrays.equals(ActionCodec.encodeCommand(held.command()), ActionCodec.encodeCommand(command))
                && ActionCommandScope.current().filter(command::equals).isPresent(), "actual primitive preparation is unavailable or escaped its original writer/command scope");
        same.head(); return held.prepared();
    }
    static void within(ContinuityStorePort.Session same, ActionCommand command, NativeRequest prepared, Runnable work) {
        StrictJson.require(CURRENT.get() == null, "another primitive preparation scope is active");
        CURRENT.set(new Held(same, command, prepared)); try { work.run(); } finally { CURRENT.remove(); }
    }
}
