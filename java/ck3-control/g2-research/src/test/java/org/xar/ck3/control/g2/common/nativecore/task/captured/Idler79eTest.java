package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;

/** Existing-module CI entry points for the ten bounded 79E source witnesses. */
public final class Idler79eTest {
    @Test
    public void scanAndClearSourceWitnesses() {
        Idler79eScanClearWitnesses.run();
    }

    @Test
    public void eventCompositionSourceWitnesses() {
        Idler79eCompositionWitnesses.run();
    }
}
