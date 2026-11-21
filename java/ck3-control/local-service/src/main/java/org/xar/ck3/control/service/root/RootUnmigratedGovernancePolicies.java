package org.xar.ck3.control.service.root;

import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.governance.FeastObservationSupplier;
import org.xar.ck3.control.application.planning.governance.GovernanceCollector;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Current-build absent-source policy only. Durable originals, pending ownership and every actual action gate remain unchanged. */
final class RootUnmigratedGovernancePolicies {
    private static final Set<PlanningStage> STAGES=Set.of(PlanningStage.OPENING_LIFESTYLE_FOCUS,PlanningStage.LIFESTYLE,
            PlanningStage.COUNCIL,PlanningStage.CROWN_AUTHORITY,PlanningStage.FEAST);
    private RootUnmigratedGovernancePolicies() { }

    static OrdinaryPolicy select(OrdinaryPolicy original,GovernanceObservationSupplier observed,FeastObservationSupplier feast,
            GovernanceRuntimeInstaller.Config configured,boolean privateSourceInstalled,boolean readonlySourceInstalled) {
        Objects.requireNonNull(original);Objects.requireNonNull(observed);Objects.requireNonNull(feast);Objects.requireNonNull(configured);
        if(privateSourceInstalled||readonlySourceInstalled||configured.nativeQualified()||!STAGES.contains(original.stage())
                ||!ExactCk3Build.CK3_121003_STEAM_26785313.matches(configured.gameVersion(),configured.executableSha256()))return original;
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage(){return original.stage();}
            @Override public ExactRef implementationSource(){return original.implementationSource();}
            @Override public Decision evaluate(PlanningRequest request,Draft previous) {
                String exact=request.source().exactBuild();
                if(!exact.equalsIgnoreCase(configured.executableSha256())
                        &&!exact.equalsIgnoreCase(configured.gameVersion()+"@sha256:"+configured.executableSha256()))
                    return original.evaluate(request,previous);
                // Earlier work retains its original policy route, including original Wait/Reconcile behavior.
                if(previous.kind()!=Kind.ORDINARY||previous.command().filter(command->!command.operation().value().equals("life-advance")).isPresent()
                        ||previous.command().isEmpty()&&stage()!=PlanningStage.OPENING_LIFESTYLE_FOCUS)
                    return original.evaluate(request,previous);
                var read=observed.durable(request);
                if(!(read instanceof Known<Durable> known))return original.evaluate(request,previous);
                var durable=known.value();durable.bind(request);
                if(durable.cadence().isEmpty()||durable.opening().isEmpty()||durable.council().isEmpty()||durable.crown().isEmpty())
                    return original.evaluate(request,previous);
                var opening=durable.opening().orElseThrow();
                if(opening.stage()!=OpeningStage.AWAIT_SUBMIT||opening.action().isPresent()||opening.checkpoint().isPresent()
                        ||!opening.episodeRunId().equals(request.before().frame().episodeRunId())
                        ||!clear(durable.council().orElseThrow())||!clear(durable.crown().orElseThrow())
                        ||LifestyleHistory.select(GovernanceCollector.lifecycleHistory(request)).status()!=LifestyleHistory.Status.CLEAR)
                    return original.evaluate(request,previous);
                var feastRead=feast.state(request);
                if(!(feastRead instanceof Known<FeastObservationSupplier.State> knownFeast))return original.evaluate(request,previous);
                var state=knownFeast.value();state.bind(request);
                if(state.pending().isPresent()||state.actualReceipts().stream().anyMatch(receipt->!receipt.settled()))
                    return original.evaluate(request,previous);
                // Java canonical domains were really read above. query_performed refers to Native governance queries only.
                String reason="recognized current governance source unavailable; Native query_performed=false, review_complete=false, cadence_published=false, action_authority=false";
                var info=new OpportunityJson.Obj(Map.of(
                        "status",new OpportunityJson.Text("unavailable"),
                        "game_version",new OpportunityJson.Text(configured.gameVersion()),
                        "query_performed",new OpportunityJson.Bool(false),"review_complete",new OpportunityJson.Bool(false),
                        "cadence_published",new OpportunityJson.Bool(false),"action_authority",new OpportunityJson.Bool(false),
                        "private_source_installed",new OpportunityJson.Bool(false),"readonly_source_installed",new OpportunityJson.Bool(false)));
                return new Defer(reason,new OpportunityJson.Obj(Map.of("unmigrated_governance_"+stage().name().toLowerCase(Locale.ROOT),info)));
            }
        };
    }
    private static boolean clear(DomainState state) {
        return state.status()==DomainStatus.KNOWN_CLEAR&&state.latest().isEmpty()&&state.legacyPending().isEmpty();
    }
}
