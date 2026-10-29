package org.xar.ck3.control.application.planning.family;

import java.util.EnumSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;

/** One host-owned family instance at both original call sites; never a second action or ledger authority. */
public final class FamilyOrdinaryFactory {
    private FamilyOrdinaryFactory() { }
    public record Inputs(ExactRef implementation, PlanningReadPort reader, Reads reads,
            CurrentSession sessions, FamilyDomainSource.CurrentBridge bridge, ImmutableArtifactStore artifacts,
            ActionPorts.OutcomeArchive outcomes, Commands sharedDateAdvance, Settings settings,
            FamilyNativePreparation.PlanningOriginalCapture planningOriginals) {
        public Inputs {
            Objects.requireNonNull(implementation); Objects.requireNonNull(reader); Objects.requireNonNull(reads);
            Objects.requireNonNull(sessions); Objects.requireNonNull(bridge);
            Objects.requireNonNull(artifacts); Objects.requireNonNull(outcomes);
            Objects.requireNonNull(sharedDateAdvance); Objects.requireNonNull(settings);
            Objects.requireNonNull(planningOriginals);
            if (implementation.bytes() <= 0) throw new IllegalArgumentException("actual family implementation source required");
        }
    }
    public record Binding(FamilyOrdinaryPolicy ordinary, FamilyMaterialStore materialResults) {
        public Binding { Objects.requireNonNull(ordinary); Objects.requireNonNull(materialResults); }
        public OrdinaryCorePolicy.CoreProducer rulerMarriage() { return ordinary::evaluateRulerMarriage; }
    }
    public record CompleteBinding(Binding strategies, FamilyPendingStore pending) {
        public CompleteBinding { Objects.requireNonNull(strategies); Objects.requireNonNull(pending); }
        public OrdinaryCorePolicy.CoreProducer rulerMarriage() { return strategies.rulerMarriage(); }
        public FamilyOrdinaryPolicy ordinary() { return strategies.ordinary(); }
        public org.xar.ck3.control.continuity.writer.DomainBodies.Registration registration(
                org.xar.ck3.control.continuity.writer.DomainBodies.Slot slot, java.util.List<ExactRef> actualProducerSources) {
            return pending.registration(slot, actualProducerSources, strategies.materialResults());
        }
    }
    public static CompleteBinding bind(Inputs input, FamilyPendingStore.Sources actualPendingSources) {
        Objects.requireNonNull(actualPendingSources);
        return new CompleteBinding(bind(input), new FamilyPendingStore(input.artifacts(), actualPendingSources));
    }
    public static Binding bind(Inputs input) {
        Objects.requireNonNull(input);
        for (Query query : requiredReads(input.settings())) if (!input.reads().available(query))
            throw new IllegalArgumentException("enabled family consumer lacks actual Root read contract: " + query.operation().value());
        FamilyMaterialStore materials = new FamilyMaterialStore(input.sessions(), input.artifacts(), input.outcomes(), input.bridge(), input.reads());
        FamilyOrdinaryPolicy policy = new FamilyOrdinaryPolicy(input.implementation(), input.reader(), input.reads(),
                new FamilyDomainSource(input.sessions(), input.bridge()), new FamilyCommands(input.sharedDateAdvance(),input.planningOriginals()), materials, input.settings());
        return new Binding(policy, materials);
    }
    public static Set<Query> requiredReads(Settings settings) {
        Objects.requireNonNull(settings); EnumSet<Query> required = EnumSet.of(Query.RULER_CHOICES);
        if (settings.familyEnabled()) required.addAll(EnumSet.of(Query.CURRENT_RELATION, Query.HEIR_LEGALITY,
                Query.HEIR_PROJECTION, Query.CHILD_HOUSE_PREVIEW, Query.FAMILY_RESULT, Query.FAMILY_ALLIANCE, Query.EDUCATION_CONTEXT));
        if (settings.familyEnabled() && settings.childFocusEnabled()) required.addAll(EnumSet.of(Query.CHILD_FOCUS, Query.CHILD_FOCUS_RECEIPT));
        if (settings.matrilinealPair().isPresent()) required.addAll(EnumSet.of(Query.CHILD_SUBJECT, Query.CHILD_VALUE,
                Query.MATRILINEAL_RESULT, Query.MATRILINEAL_ALLIANCE));
        if (settings.childDefaultEnabled()) required.addAll(EnumSet.of(Query.CHILD_SUBJECT, Query.CHILD_VALUE,
                Query.DEFAULT_RESULT, Query.DEFAULT_ALLIANCE, Query.CAMPAIGN_ROOT));
        return Set.copyOf(required);
    }
}
