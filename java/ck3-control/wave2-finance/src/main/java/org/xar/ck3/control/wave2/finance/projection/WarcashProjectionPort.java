package org.xar.ck3.control.wave2.finance.projection;

import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.finance.warcash.WarcashCodec;

/** Same domain decoder and receipt policy as the original byte entrance. */
public final class WarcashProjectionPort implements ProjectionPort<WarcashCodec.Request, JsonNode> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.WARCASH_EVALUATE; }
    @Override public WarcashCodec.Request decode(byte[] rawPayload) { return WarcashCodec.parse(rawPayload); }
    @Override public JsonNode project(WarcashCodec.Request input) { return WarcashCodec.evaluate(input); }
    @Override public byte[] encode(JsonNode result) { return StrictJson.canonical(result, outputMaximumBytes()); }
    @Override public int inputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
    @Override public int outputMaximumBytes() { return WarcashCodec.OUTPUT_MAX_BYTES; }
}
