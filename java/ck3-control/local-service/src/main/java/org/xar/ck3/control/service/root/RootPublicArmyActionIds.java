package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatOrderService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;

/** Existing shared action-ID formatter over the actual public caller's original writer/head and Army frame.
 * This object neither allocates another ledger sequence nor grants submission or an UNKNOWN retry.
 * Both real public services run their existing domain/source/ActionCoordinator guards after this formatting. */
public final class RootPublicArmyActionIds implements ArmyRetreatOrderService.ActionIds,ArmyOrdinaryActionService.ActionIds {
    private final RootCoreBoundPorts ports;private final String configuredPrefix;
    public RootPublicArmyActionIds(RootCoreBoundPorts actualPorts,String actualPrefix){
        ports=Objects.requireNonNull(actualPorts);configuredPrefix=Objects.requireNonNull(actualPrefix);
        if(!actualPrefix.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"))throw new IllegalArgumentException("explicit bounded public Army action prefix required");
    }
    @Override public String next(ContinuityStorePort.Session same,ArmyTypes.Context actualBefore)throws IOException {
        Objects.requireNonNull(actualBefore);ports.requireSession(same);String head=same.head().digest();
        var owner=new SessionIdentity(actualBefore.before().machineId(),actualBefore.before().game(),actualBefore.sessionId());
        RootRuntimeContext context=ports.requireCurrent(same,owner);context.requireCurrent(actualBefore.deadline());
        if(!context.source().equals(actualBefore.source())||!context.game().generation().equals(actualBefore.before().game())
                ||!context.game().sessionId().equals(actualBefore.sessionId()))throw new IOException("public Army ID formatting crossed its actual current Game/source/session");
        context.game().launchPlan().sources().requireLoadedClass(RootPublicArmyActionIds.class);
        String result=ActionIds.forDecision(actualBefore.sessionId(),actualBefore.before(),configuredPrefix+":public-army:"+head);
        ports.requireSession(same);if(!head.equals(same.head().digest()))throw new IOException("public Army ID formatting changed the original writer head");
        return result;
    }
}
