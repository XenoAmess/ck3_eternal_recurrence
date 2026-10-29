package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** Existing host operation; no transport, process, file reader or native submitter is started here. */
public final class PeacetimeAssemblyProjectionPort
        implements ProjectionPort<PeacetimeAssembly.Inputs, PeacetimeAssemblyApplication.Result> {
    public PeacetimeAssemblyProjectionPort() { }
    @Override public ProjectionOperation operation() { return ProjectionOperation.PEACETIME_ASSEMBLY_COLLECT; }
    @Override public int inputMaximumBytes() { return PeacetimeAssemblyApplication.MAXIMUM_BYTES; }
    @Override public int outputMaximumBytes() { return PeacetimeAssemblyApplication.MAXIMUM_BYTES; }
    @Override public PeacetimeAssembly.Inputs decode(byte[] rawPayload) { return PeacetimeAssemblyCodec.decode(rawPayload); }
    @Override public PeacetimeAssemblyApplication.Result project(PeacetimeAssembly.Inputs input) {
        try { return PeacetimeAssemblyApplication.project(input); }
        catch (org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Unavailable refused) {
            throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(refused.getMessage());
        }
    }
    @Override public byte[] encode(PeacetimeAssemblyApplication.Result result) { return PeacetimeAssemblyApplication.encode(result); }
}
