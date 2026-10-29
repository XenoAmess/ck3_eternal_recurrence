package org.xar.ck3.control.score.projection;

import java.util.List;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.score.CampaignArithmeticCodec;

/** Arithmetic-only registration in the existing projection host. */
public final class CampaignArithmeticProjectionCatalog implements ProjectionPortCatalog {
    public CampaignArithmeticProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new ProjectionPort<CampaignArithmeticCodec.Request, CampaignArithmeticCodec.Result>() {
            @Override public ProjectionOperation operation() { return ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE; }
            @Override public int inputMaximumBytes() { return 65536; }
            @Override public int outputMaximumBytes() { return 65536; }
            @Override public CampaignArithmeticCodec.Request decode(byte[] raw) { return CampaignArithmeticCodec.decode(raw); }
            @Override public CampaignArithmeticCodec.Result project(CampaignArithmeticCodec.Request request) {
                try { return CampaignArithmeticCodec.evaluate(request); }
                catch (ContractViolationException invalidInput) {
                    throw new ProjectionDomainRejection(invalidInput.getMessage());
                }
            }
            @Override public byte[] encode(CampaignArithmeticCodec.Result result) { return CampaignArithmeticCodec.encode(result); }
        }));
    }
}
