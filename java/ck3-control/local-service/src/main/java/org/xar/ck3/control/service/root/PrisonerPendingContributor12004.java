package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Comparator;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinancePolicies;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Concrete sole pending-barrier contributor. Every continuation retains the original action and Native request identity. */
public final class PrisonerPendingContributor12004 implements OrdinaryFinancePolicies.PendingContributor {
    private final RootRuntimeContext context;
    private final PrisonerLegacyBinding12004 originals;
    private final PrisonersRuntimeDefinitions definitions;
    public PrisonerPendingContributor12004(RootRuntimeContext context,PrisonerLegacyBinding12004 originals,PrisonersRuntimeDefinitions definitions) {
        this.context=Objects.requireNonNull(context);this.originals=Objects.requireNonNull(originals);this.definitions=Objects.requireNonNull(definitions);
    }
    @Override public Optional<OrdinaryPolicy.Decision> pending(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        try {
            var borrowed=context.borrowedSession();context.writer().requireSession(borrowed);
            Optional<ActionReceipt> unresolved=context.core().actions().withFrozen(borrowed,lease->{
                var result=lease.snapshot().actions().stream().filter(receipt->!receipt.settled() && owned(receipt.command().operation()))
                        .min(Comparator.comparingLong(ActionReceipt::sequence));lease.assertCurrent();return result;
            });
            if(unresolved.isPresent()) return Optional.of(continuation(request,previous,unresolved.orElseThrow()));
            for(var family:PrisonerPlanningPorts.Family.values()) {
                var bound=originals.read(borrowed,request,family);
                if(bound instanceof PrisonerLegacyBinding12004.Unavailable unavailable)
                    return Optional.of(new OrdinaryPolicy.Defer("actual prisoner original binding unavailable; retain UNKNOWN without replay",
                            previous.detail().with("prisoner_pending_reason",new OpportunityJson.Text(unavailable.reason()))));
                if(bound instanceof PrisonerLegacyBinding12004.Bound original) {
                    if(!original.receipt().settled())return Optional.of(continuation(request,previous,original.receipt()));
                    definitions.resolve(borrowed,original);
                    return Optional.of(new OrdinaryPolicy.Refresh("actual canonical prisoner terminal replayed and reduced by the sole writer; refresh current inputs"));
                }
            }
            return Optional.empty();
        } catch(IOException | IllegalArgumentException failure) {
            String reason=failure.getMessage()==null?"actual prisoner pending source unavailable":failure.getMessage();
            return Optional.of(new OrdinaryPolicy.Defer("original prisoner state cannot be inferred clear",
                    previous.detail().with("prisoner_pending_reason",new OpportunityJson.Text(reason.substring(0,Math.min(1024,reason.length()))))));
        }
    }
    private static OrdinaryPolicy.Decision continuation(PlanningRequest request,OrdinaryPolicy.Draft previous,ActionReceipt original) {
        var command=original.command();
        boolean same=command.origin() instanceof CommandOrigin.Gameplay && command.before().game().equals(request.before().game())
                && command.before().machineId().equals(request.before().machineId()) && command.source().equals(request.source())
                && command.sessionId().equals(request.sessionId()) && command.before().frame().episodeRunId().equals(request.before().frame().episodeRunId())
                && command.before().frame().identity().player().equals(request.before().frame().identity().player());
        var facts=request.observations().actionFacts().stream().filter(fact->fact.actionId().equals(command.actionId())).toList();
        var detail=previous.detail().with("prisoner_material_result",new OpportunityJson.Bool(false))
                .with("prisoner_original_action_id",new OpportunityJson.Text(command.actionId()));
        if(!same || facts.size()!=1 || !facts.getFirst().bodySha256().equals(original.bodySha256()))
            return new OrdinaryPolicy.Defer("original prisoner action lacks its exact authoritative current fact; UNKNOWN retained",detail);
        return new OrdinaryPolicy.ReconcileExisting(command.actionId(),detail,"read only the original prisoner request outcome; UNKNOWN never creates another submission");
    }
    private static boolean owned(OperationKey operation) {
        return operation.equals(PrisonerOrdinaryPolicy12004.RELEASE)||operation.equals(PrisonerOrdinaryPolicy12004.RANSOM);
    }
}

