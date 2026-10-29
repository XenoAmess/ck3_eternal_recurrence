package org.xar.ck3.control.application.action;

import java.time.Instant;

/** Implemented by the same NativeGameTransport/endpoint as NativeActionPort. */
public interface NativePlanningReadPort {
    NativeActionPort.DispatchOutcome read(ReadPermit permit, NativeRequest request, Instant deadline) throws InterruptedException;
}
