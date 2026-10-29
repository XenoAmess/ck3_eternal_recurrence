package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** One exact Root-registered bootstrap read. It cannot authorize a gameplay action or another query. */
public final class GameplayEntryReadGuard implements PlanningReadCoordinator.ReadGuardPort {
    private final ReadContract<?> campaignRoot;
    private final RootPlanningReadGuard actual;
    public GameplayEntryReadGuard(InitialDriverBootstrap firstDriver, ReadContract<?> actualCampaignRoot,
            ContinuityWriter writer, NativeOutcomeArchive archive, OriginalEvidencePort originals,
            RootReadContractCatalog sameCatalog,G2Source source,Clock clock,String authorityId) {
        campaignRoot=Objects.requireNonNull(actualCampaignRoot);
        StrictJson.require(campaignRoot.operation().equals(GameplayEntryRoot.OPERATION)
                && campaignRoot.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP && sameCatalog.containsIdentity(campaignRoot),
                "exact installed actual campaign-root read required");
        actual=new RootPlanningReadGuard(Objects.requireNonNull(firstDriver),() -> {
            try { return writer.borrowedSession(); }
            catch(IOException failure) { throw new UncheckedIOException(failure); }
        },archive,source,clock,authorityId,originals,sameCatalog);
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
        StrictJson.require(contract==campaignRoot && request.operation().equals(GameplayEntryRoot.OPERATION),"first-entry read scope permits only its identical campaign-root contract");
        return actual.verify(head,request,contract);
    }
}
