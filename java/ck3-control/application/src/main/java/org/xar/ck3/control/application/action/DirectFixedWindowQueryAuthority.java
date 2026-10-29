package org.xar.ck3.control.application.action;

import java.io.IOException;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.g2.common.G2Source;

/** Installed Root source reopens its private issued token and exact original query; DATA alone grants nothing. */
public interface DirectFixedWindowQueryAuthority {
    void requireOwner(GameGeneration game, String sessionId, G2Source source) throws IOException;
    ActionPorts.PostconditionResult observeOriginalQuery(Session same, ActionReceipt actualCanonicalPending,
            DirectFixedWindowQueryContinuation actual, ActionPorts.DirectWindowQueryWork observer)
            throws IOException, InterruptedException;
}
