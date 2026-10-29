package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;

/** Exact checkpoint Driver lookup: private current staged owner or the strictly admitted public owner. No latest-Game selection. */
public final class RootCheckpointRuntimeAuthority implements RootM7CheckpointCapture.RuntimeAuthority {
    private final RootApplicationAssembly.Core core;
    private final RootRuntimeCatalogFactory catalogs;
    public RootCheckpointRuntimeAuthority(RootApplicationAssembly.Core actual,RootRuntimeCatalogFactory installed)throws IOException {
        core=Objects.requireNonNull(actual);catalogs=Objects.requireNonNull(installed);catalogs.requireBoundCore(core);
    }
    @Override public RootRuntimeContext require(SessionIdentity expected)throws IOException {
        core.writer().requireSession(core.writer().borrowedSession());catalogs.requireBoundCore(core);
        var staged=core.privateCheckpointRuntime(Objects.requireNonNull(expected));
        var context=staged.isPresent()?staged.orElseThrow():catalogs.requireCurrent(expected);
        var driverSession=context.adopted().session();
        if(context.core()!=core||context.writer()!=core.writer()||context.archive()!=core.archive()
                ||!context.game().machineId().equals(expected.machineId())||!context.game().generation().equals(expected.game())
                ||!context.game().sessionId().equals(expected.sessionId())||!driverSession.machineId().equals(expected.machineId())
                ||!driverSession.game().equals(expected.game())||!driverSession.sessionId().equals(expected.sessionId()))
            throw new IOException("checkpoint DATA resolver crossed its exact original Core/physical owner/Driver");
        context.game().verify();context.game().launchPlan().sources().requireLoadedClass(RootCheckpointRuntimeAuthority.class);
        return context;
    }
}
