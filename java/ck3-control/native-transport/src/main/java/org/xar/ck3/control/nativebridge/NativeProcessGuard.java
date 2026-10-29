package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import org.xar.ck3.control.contracts.GameGeneration;

/** The lifecycle owner verifies the held original Game/process/EXE/DLL lease on every I/O boundary. */
@FunctionalInterface
public interface NativeProcessGuard {
    void verify(GameGeneration game) throws IOException;
}
