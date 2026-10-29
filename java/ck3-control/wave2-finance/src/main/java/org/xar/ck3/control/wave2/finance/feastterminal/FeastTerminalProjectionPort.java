package org.xar.ck3.control.wave2.finance.feastterminal;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** The existing terminal interpreter exposed through the one projection host. */
public final class FeastTerminalProjectionPort
        implements ProjectionPort<FeastTerminalOutcome.Request, FeastTerminalOutcome.Outcome> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.FEAST_TERMINAL_NORMALIZE; }
    @Override public FeastTerminalOutcome.Request decode(byte[] payload) { return FeastTerminalCodec.decodeRequest(payload); }
    @Override public FeastTerminalOutcome.Outcome project(FeastTerminalOutcome.Request input) { return FeastTerminalPolicy.observe(input); }
    @Override public byte[] encode(FeastTerminalOutcome.Outcome output) { return FeastTerminalCodec.encodeOutcome(output); }
    @Override public int inputMaximumBytes() { return FeastTerminalCodec.MAX_INPUT_BYTES; }
    @Override public int outputMaximumBytes() { return FeastTerminalCodec.MAX_OUTPUT_BYTES; }
}
