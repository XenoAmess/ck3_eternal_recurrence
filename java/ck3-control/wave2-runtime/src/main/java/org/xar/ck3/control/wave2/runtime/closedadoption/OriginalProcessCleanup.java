package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.io.IOException;

/** Preserve the original failure while independently closing input and consuming the owned child. */
final class OriginalProcessCleanup {
    private OriginalProcessCleanup() { }

    static void suppressing(OriginalWriterTransaction.ManagedProcess process, Throwable primary) {
        if (primary instanceof InterruptedException) { Thread.currentThread().interrupt(); }
        try { process.closeOwnedInput(); }
        catch (IOException | RuntimeException | Error cleanup) { suppress(primary,cleanup); }
        try { process.awaitActualExit(); }
        catch (InterruptedException cleanup) { Thread.currentThread().interrupt(); suppress(primary,cleanup); }
        catch (IOException | RuntimeException | Error cleanup) { suppress(primary,cleanup); }
    }

    private static void suppress(Throwable primary, Throwable cleanup) {
        if (cleanup != primary) { primary.addSuppressed(cleanup); }
    }
}
