package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;

/** The actual same-root scope of the outgoing authority's entire pure fresh-contract replay. */
public final class RootFamilyFreshRootAdmission implements RootFamilyMarriageSendAuthority.RootFreshAdmission {
    private final RootFamilyCampaignRead root;
    public RootFamilyFreshRootAdmission(RootFamilyCampaignRead sameRoot){root=Objects.requireNonNull(sameRoot);}
    @Override public void requireOriginal(Session same,PlanningReadReceipt original,ActionCommand command,Complete target,
            List<ExactRef> originals)throws IOException {
        root.requireFreshOriginal(same,original,command,target,originals);
    }
    @Override public <T> T withinFreshTarget(Session same,ActionCommand command,Complete target,List<ExactRef> originals,
            RootFamilyMarriageSendAuthority.FreshWork<T> work)throws IOException {
        var guard=root.freshTarget(same,command,target,originals);
        return root.withHistoricalTarget(same,guard,target,work::run);
    }
}
