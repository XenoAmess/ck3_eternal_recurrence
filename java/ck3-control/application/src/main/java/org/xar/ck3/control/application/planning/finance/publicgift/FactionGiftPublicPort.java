package org.xar.ck3.control.application.planning.finance.publicgift;

import java.io.IOException;
import java.time.Instant;
import org.xar.ck3.control.application.action.RawJson;

/** The identical per-Game Finance producer, installed once with its original writer/read/quote owners. */
@FunctionalInterface
public interface FactionGiftPublicPort {
    RawJson invoke(FactionGiftPublicContract.Request request, Instant deadline) throws IOException, InterruptedException;
}
