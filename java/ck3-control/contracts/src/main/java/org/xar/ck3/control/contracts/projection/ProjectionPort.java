package org.xar.ck3.control.contracts.projection;

import org.xar.ck3.control.contracts.StrictJson;

/** Domain-owned typed codec and pure application. No file, action, writer or native transport is supplied. */
public interface ProjectionPort<I, O> {
    ProjectionOperation operation();
    I decode(byte[] rawPayload);
    O project(I input);
    byte[] encode(O result);
    default int inputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
    default int outputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
}
