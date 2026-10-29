package org.xar.ck3.control.service.root;

import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;

/** Checks the original proposal clocks; it never changes an UNKNOWN command or extends a deadline. */
public final class OriginalCommandClocks {
    private OriginalCommandClocks() { }
    public static ActionCommand requireCurrentProposal(PlanningRequest request,ActionCommand command) {
        Objects.requireNonNull(request);Objects.requireNonNull(command);
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                &&command.before().equals(request.before())&&command.source().equals(request.source())
                &&command.sessionId().equals(request.sessionId())&&command.deadline().equals(request.deadline()),
                "war proposal crossed its original complete frame/source/session/deadline");
        StrictJson.require(command.expected().before().equals(request.before())
                &&command.expected().source().equals(request.source()),
                "war proposal expectation crossed its original frame/source");
        return command;
    }
    /** Rebinding a new proposal must retain its operation and original identity, never create a second intent. */
    public static ActionCommand requireRebound(PlanningRequest request,ActionCommand proposed,ActionCommand actual) {
        requireCurrentProposal(request,proposed);requireCurrentProposal(request,actual);
        StrictJson.require(actual.actionId().equals(proposed.actionId())&&actual.operation().equals(proposed.operation()),
                "actual owned war preparer changed the new proposal identity or operation");
        StrictJson.require(actual.claims().armyIds().containsAll(proposed.claims().armyIds())
                &&actual.claims().allyCharacterIds().containsAll(proposed.claims().allyCharacterIds())
                &&actual.claims().characterIds().containsAll(proposed.claims().characterIds())
                &&actual.claims().commitmentKeys().containsAll(proposed.claims().commitmentKeys()),
                "actual owned war preparer dropped an original resource claim");
        return actual;
    }
}

