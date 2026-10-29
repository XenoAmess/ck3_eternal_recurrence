package org.xar.ck3.control.nativebridge;

import java.time.Instant;
import org.xar.ck3.control.application.action.NativeActionPort;

/** Fixed original standalone query, independently readable before a full gameplay Snapshot. */
@FunctionalInterface
public interface NativeCoreFramePort {
    NativeActionPort.DispatchOutcome readCoreFrame(Instant deadline) throws InterruptedException;
}
