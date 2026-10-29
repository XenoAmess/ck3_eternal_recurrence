package org.xar.ck3.control.wave2.finance.projection;

import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;

/** Existing optional financing observation; JSON null remains a valid, explicit result. */
public final class HolyLoanProjectionPort
        implements ProjectionPort<LoanFinancingCodec.Request, LoanFinancingCodec.LoanInput> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.HOLY_LOAN_PROJECT; }
    @Override public LoanFinancingCodec.Request decode(byte[] rawPayload) { return LoanFinancingCodec.parse(rawPayload); }
    @Override public LoanFinancingCodec.LoanInput project(LoanFinancingCodec.Request input) { return LoanFinancingCodec.project(input); }
    @Override public byte[] encode(LoanFinancingCodec.LoanInput result) { return LoanFinancingCodec.encode(result); }
    @Override public int inputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
    @Override public int outputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
}
