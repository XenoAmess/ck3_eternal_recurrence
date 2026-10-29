package org.xar.ck3.control.application.planning.finance;

import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import java.util.function.Supplier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** One host factory for the real ordinary finance producers and their original-evidence verifiers. */
public final class OrdinaryFinanceFactory {
    private OrdinaryFinanceFactory() { }
    public record Sources(ExactRef policy,ExactRef mercenaryMaterial,ExactRef giftMaterial,ExactRef quoteArchive) {
        public Sources { Objects.requireNonNull(policy);Objects.requireNonNull(mercenaryMaterial);Objects.requireNonNull(giftMaterial);Objects.requireNonNull(quoteArchive);
            StrictJson.require(policy.bytes()>0&&mercenaryMaterial.bytes()>0&&giftMaterial.bytes()>0&&quoteArchive.bytes()>0,"actual selected production sources required"); }
    }
    @FunctionalInterface public interface LockedCurrent {
        /** Bound by Root to the actual same-writer-lock current Driver collector, never the old planning DTO. */
        PlanningRequest current(Session borrowed,ActionCommand command);
    }
    public record Installed(FinanceReadContracts reads,FinanceStatePort state,OrdinaryFinanceCollector collector,
            OrdinaryFinancePolicies policies,List<OrdinaryPolicy> stages,List<ReadContract<?>> readContracts,
            List<NativeEffectRegistry.Binding> effectBindings,List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers,
            ActionPorts.IntentPreparationPort intentPreparation,FinanceEvidenceArchive quoteEvidence) {
        public Installed { Objects.requireNonNull(reads);Objects.requireNonNull(state);Objects.requireNonNull(collector);Objects.requireNonNull(policies);
            stages=List.copyOf(stages);readContracts=List.copyOf(readContracts);effectBindings=List.copyOf(effectBindings);archivedVerifiers=List.copyOf(archivedVerifiers);
            Objects.requireNonNull(intentPreparation);Objects.requireNonNull(quoteEvidence); }
    }
    public static Installed create(Sources sources,FinanceReadContracts.Registrations originalReadRegistrations,
            CanonicalFinanceStateSource originalWriter,org.xar.ck3.control.continuity.writer.ContinuityStorePort originalStore,
            PlanningReadPort originalReads,NativeEffectSnapshots snapshots,NativeEffectEvidence.FrameLoader archivedFrames,
            LockedCurrent current,List<OrdinaryFinancePolicies.PendingContributor> orderedPendingContributors,
            ActionPorts.OutcomeArchive archive,Supplier<Session> borrowed,OriginalEvidencePort originals,
            FinanceReadContracts.ExternalFeastInputs strictActivityInputs,FinanceReadContracts.ExternalFactionAlerts strictFactionAlerts,
            FinanceEvidenceArchive.HistoricalRootReplay historicalRoots) {
        Objects.requireNonNull(sources);Objects.requireNonNull(current);Objects.requireNonNull(archivedFrames);
        List<FinanceStatePort.ReaderBinding> owningBodyReaders=Objects.requireNonNull(originalWriter).owningReaders();
        var supplied=java.util.EnumSet.noneOf(FinanceStatePort.Domain.class);
        for(var binding:List.copyOf(owningBodyReaders))StrictJson.require(supplied.add(binding.domain()),"duplicate owning persistent-body decoder");
        StrictJson.require(supplied.contains(FinanceStatePort.Domain.MERCENARY),"actual mercenary persistent reducer must be installed");
        // Missing external domains remain missing in FinanceStatePort and defer optional spending; they never become fabricated CLEAR.
        FinanceReadContracts definitions=new FinanceReadContracts(originalReadRegistrations,Objects.requireNonNull(strictActivityInputs),Objects.requireNonNull(strictFactionAlerts));
        FinanceStatePort state=new FinanceStatePort(originalWriter,owningBodyReaders);
        OrdinaryFinanceCollector collector=new OrdinaryFinanceCollector(definitions,originalReads,state,borrowed);
        FinanceEvidenceArchive quotes=new FinanceEvidenceArchive(originalStore,archive,borrowed,originals,archivedFrames,definitions,owningBodyReaders,sources.quoteArchive(),historicalRoots);
        OrdinaryFinancePolicies policies=new OrdinaryFinancePolicies(sources.policy(),collector,NativeFinanceEffects::expected,orderedPendingContributors,quotes);
        NativeFinanceEffects effects=new NativeFinanceEffects(snapshots,originalReads,definitions,quotes,borrowed,archivedFrames);
        ActionPorts.PreparationPort preparation=new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) {
                throw new IllegalStateException("finance preparation requires the coordinator's actual request identity");
            }
            @Override public NativeRequest prepare(ActionCommand command,String requestId) {
                return NativeFinanceEffects.prepare(command,requestId);
            }
        };
        var effectBindings=List.of(new NativeEffectRegistry.Binding(OrdinaryFinancePolicies.MERCENARY,sources.mercenaryMaterial(),preparation,effects),
                new NativeEffectRegistry.Binding(OrdinaryFinancePolicies.GIFT,sources.giftMaterial(),preparation,effects));
        var archived=List.of(effects.archivedVerifier(OrdinaryFinancePolicies.MERCENARY,sources.mercenaryMaterial(),archivedFrames),
                effects.archivedVerifier(OrdinaryFinancePolicies.GIFT,sources.giftMaterial(),archivedFrames));
        ActionPorts.IntentPreparationPort intent=(session,command)-> {
            StrictJson.require(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)||command.operation().equals(OrdinaryFinancePolicies.GIFT),"unowned finance intent preparation");
            policies.revalidate(session,command,Objects.requireNonNull(current.current(session,command)));
        };
        return new Installed(definitions,state,collector,policies,policies.stages(),definitions.registeredContracts(),effectBindings,archived,intent,quotes);
    }
}

