package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnostics;
import org.xar.ck3.control.service.mcp.RootMcpBridgeDiagnostics;

/** Joins installed Driver-private producers; missing original Start custody supplies no Start query claim. */
public final class RootPublicDiagnosticSupplements implements RootMcpBridgeDiagnostics.SupplementResolver {
    private final RootRuntimeCatalogFactory catalogs;
    private final ExactRef source;
    public RootPublicDiagnosticSupplements(RootRuntimeCatalogFactory catalogs,ExactRef actualThisSource) {
        this.catalogs=Objects.requireNonNull(catalogs);source=Objects.requireNonNull(actualThisSource);
        StrictJson.require(source.bytes()>0,"actual selected diagnostic supplement implementation required");
    }
    @Override public ExactRef implementationSource(){return source;}
    @Override public Set<BridgeDiagnostics.RequiredInput> inputs(){return BridgeDiagnostics.supplementInputs();}
    @Override public BridgeDiagnostics.Supplement capture(RootRuntimeContext current,ContinuityStorePort.Session same,
            DriverSnapshotFacts.Known actualDriver,BridgeDiagnostics.Received actualReceived)throws IOException {
        Objects.requireNonNull(current);Objects.requireNonNull(same);Objects.requireNonNull(actualDriver);Objects.requireNonNull(actualReceived);
        var catalog=catalogs.requireCurrentCatalog(current.core().sessionAccess().current());
        StrictJson.require(catalog.context()==current,"diagnostic supplement crossed the actual current installed context");
        var start=catalog.frontend().optionalFrontendStartDiagnostics();
        return new BridgeDiagnostics.Supplement(catalog.declarationDiagnostics().capture(current,same,actualDriver,actualReceived),
                start.isPresent()?start.orElseThrow().capture(current,same,actualDriver,actualReceived):Optional.empty());
    }
}
