package org.xar.ck3.control.wave3.runtime.childexports;

import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportCallbackAdapter.Request;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportCallbackAdapter.Result;

/** Registered in the existing host; base64 wrapper is distinct from the unchanged 16 KiB private wire. */
public final class ChildExportProjectionPort implements ProjectionPort<Request, Result> {
    public static final int CALLBACK_INPUT_MAX_BYTES = 32_768;
    public static final int CALLBACK_OUTPUT_MAX_BYTES = 32_768;

    @Override public ProjectionOperation operation() { return ProjectionOperation.CHILD_EXPORT_PROJECT; }
    @Override public Request decode(byte[] rawPayload) {
        return ChildExportCallbackAdapter.decodeRequest(StrictJson.parse(rawPayload, CALLBACK_INPUT_MAX_BYTES));
    }
    @Override public Result project(Request input) { return ChildExportCallbackAdapter.evaluate(input); }
    @Override public byte[] encode(Result result) {
        return StrictJson.canonical(ChildExportCallbackAdapter.encodeResult(result), CALLBACK_OUTPUT_MAX_BYTES);
    }
    @Override public int inputMaximumBytes() { return CALLBACK_INPUT_MAX_BYTES; }
    @Override public int outputMaximumBytes() { return CALLBACK_OUTPUT_MAX_BYTES; }
}
