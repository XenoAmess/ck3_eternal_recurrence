package org.xar.ck3.control.wave2.finance.feastcounters;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** Native four-field counter validation delegates to the existing strict codec. */
public final class OutcomeCounterNormalizeProjectionPort
        implements ProjectionPort<OutcomeCounterValues, OutcomeCounterValues> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.FEAST_COUNTER_NORMALIZE; }
    @Override public OutcomeCounterValues decode(byte[] payload) { return OutcomeCounterCodec.decodeCounters(payload); }
    @Override public OutcomeCounterValues project(OutcomeCounterValues input) { return input; }
    @Override public byte[] encode(OutcomeCounterValues output) { return OutcomeCounterCodec.encodeCounters(output); }
    @Override public int inputMaximumBytes() { return OutcomeCounterCodec.MAX_BYTES; }
    @Override public int outputMaximumBytes() { return OutcomeCounterCodec.MAX_BYTES; }
}
