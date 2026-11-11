package org.xar.ck3.control.application.action;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.util.List;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.application.planning.sway.OrdinarySwayPolicy;
import org.xar.ck3.control.application.planning.sway.SwayNativeWire;

/** Permanent retired identities and an explicit optional-Sway quarantine, not a no-effect conclusion. */
public final class CompositeOperatorQuarantinePolicy {
    private CompositeOperatorQuarantinePolicy() { }
    public static boolean quarantinedSway(List<ActionReceipt> canonical,GameGeneration game,String episode) {
        return canonical.stream().anyMatch(receipt->receipt.state() instanceof ActionState.CompositeOperatorQuarantined
                &&receipt.command().origin().game().equals(game)&&receipt.command().before().frame().episodeRunId().equals(episode)
                &&receipt.command().operation().equals(OrdinarySwayPolicy.OPERATION));
    }
    public static void requireNewActionAllowed(List<ActionReceipt> canonical,ActionCommand command) {
        for(var receipt:List.copyOf(canonical)) if(receipt.state() instanceof ActionState.CompositeOperatorQuarantined retired) {
            require(!receipt.command().actionId().equals(command.actionId())
                    &&retired.execution().children().stream().noneMatch(child->child.actionId().equals(command.actionId())),
                    "operator-retired parent/child action identity is permanently non-dispatchable");
        }
        String operation=command.operation().value();
        boolean sway=command.operation().equals(OrdinarySwayPolicy.OPERATION)||operation.startsWith(SwayNativeWire.START)||operation.equals(SwayNativeWire.STOP);
        require(!sway||!quarantinedSway(canonical,command.origin().game(),command.before().frame().episodeRunId()),
                "optional Sway ACTION is operator-quarantined for this original Game/episode with unknown effects");
    }
}
