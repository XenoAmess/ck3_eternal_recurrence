package org.xar.ck3.control.nativebridge;

import java.time.Instant;
import org.xar.ck3.control.application.action.NativeActionPort.DispatchOutcome;

/** Fixed read-only native frontend bootstrap query; not a generic step or action authority. */
public interface NativeFrontendRoutePort {
    DispatchOutcome readFrontendRoute(Instant deadline) throws InterruptedException;
}

