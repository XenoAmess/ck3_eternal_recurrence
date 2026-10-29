package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;

/** Pure extra predicates installed as decorators by the real held-frame guard owner. No caller booleans grant admission. */
public final class GuiGuards {
    public enum Requirement { SOURCE_SESSION_CENSUS,PAUSED_MAP,PAUSED_MAP_NO_EVENT,PAUSED_MAP_NO_EVENT_OR_PENDING }
    private final GuiReads contracts;
    public GuiGuards(GuiReads contracts){this.contracts=Objects.requireNonNull(contracts);}
    public Requirement requirement(ReadContract<?> exact){
        if(exact==contracts.census)return Requirement.SOURCE_SESSION_CENSUS;
        if(exact==contracts.whiteBusiness||exact==contracts.whiteText)return Requirement.PAUSED_MAP_NO_EVENT;
        if(exact==contracts.aubPolicy||exact==contracts.aubState)return Requirement.PAUSED_MAP_NO_EVENT_OR_PENDING;
        if(exact==contracts.semantic||exact==contracts.decision)return Requirement.PAUSED_MAP;
        throw new IllegalArgumentException("GUI guard only admits exact root-installed contract instances");
    }
    public void validateRead(ReadContract<?> exact,RawJson actualHeldState){validate(requirement(exact),actualHeldState);}
    public void validateAction(ActionCommand actualCommand,RawJson actualHeldState){String op=actualCommand.operation().value();need(GuiActions.operations().contains(op),"unknown GUI mutation guard");
        Requirement requirement=op.startsWith("click-white-")?Requirement.PAUSED_MAP_NO_EVENT:
            op.contains("aub-policy")||op.equals("confirm-ingame-decision-outcome-v1")?Requirement.PAUSED_MAP_NO_EVENT_OR_PENDING:Requirement.PAUSED_MAP;
        validate(requirement,actualHeldState);
    }
    private static void validate(Requirement requirement,RawJson original){
        ObjectNode state=parse(original);if(requirement==Requirement.SOURCE_SESSION_CENSUS)return;
        yes(state,"paused","map_ready");ObjectNode player=obj(required(state,"played_character"));yes(player,"alive");
        need(integer(player,"character_id").signum()>0,"current actual living player required");
        if(requirement==Requirement.PAUSED_MAP_NO_EVENT||requirement==Requirement.PAUSED_MAP_NO_EVENT_OR_PENDING)
            need(required(state,"active_event").isNull(),"original GUI producer requires observed no-event state");
        if(requirement==Requirement.PAUSED_MAP_NO_EVENT_OR_PENDING)
            need(required(state,"pending_character_interaction").isNull(),"original GUI producer requires observed no-pending-interaction state");
    }
}
