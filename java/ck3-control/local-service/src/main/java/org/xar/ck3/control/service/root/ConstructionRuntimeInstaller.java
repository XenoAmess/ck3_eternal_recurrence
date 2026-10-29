package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Concrete per-Game construction graph. All reads share finance's actual Root contract objects. */
public final class ConstructionRuntimeInstaller {
    public record Sources(ExactRef policySource, ExactRef collectorSource, ExactRef nativeActionSource,
            ExactRef observerSource, ExactRef archiveVerifierSource, ExactRef lifecycleSource, ExactRef snapshotVerifierSource,
            ExactRef originalsSource, ConstructionDomainLifecycle.Prepared domain) {
        public Sources {
            Objects.requireNonNull(domain);
            for (ExactRef source : List.of(policySource, collectorSource, nativeActionSource, observerSource, archiveVerifierSource, lifecycleSource, snapshotVerifierSource, originalsSource)) {
                Objects.requireNonNull(source); StrictJson.require(source.bytes() > 0, "actual complete construction producer source required");
                StrictJson.require(domain.registration().producerSources().contains(source), "construction owning registry omitted a real installed producer source");
            }
        }
        public org.xar.ck3.control.continuity.writer.DomainBodies.Registration registration() { return domain.registration(); }
    }
    private final RootRuntimeContext context;
    private final Sources sources;
    private final LinkedHashMap<String, RetainedPlan> plans = new LinkedHashMap<>();
    private RootDomainInstallation installed;
    private OrdinaryConstructionPolicy policy;
    private OrdinaryConstructionMaterialFollowup completion;
    private RootConstructionDomainOriginals originals;
    private ConstructionPeacetimeSources peacetimeSources;
    public ConstructionRuntimeInstaller(RootRuntimeContext context, Sources sources) {
        this.context = Objects.requireNonNull(context); this.sources = Objects.requireNonNull(sources);
    }
    public synchronized RootDomainInstallation install() {
        if (installed != null) return installed;
        FinanceRuntimeServices finance = context.finance();
        try {
            context.game().launchPlan().sources().requireLoadedClass(ConstructionFundingEvidence.class);
            context.game().launchPlan().sources().requireLoadedClass(ConstructionMaterialSource.class);
        }
        catch (IOException failure) { throw new UncheckedIOException("actual construction funding/material bridge is outside the selected loaded source graph", failure); }
        sources.domain().bindCore(context.writer(), context.archive(), context.frameLoader(), finance.definitions());
        var existingOriginals = sources.domain().originals();
        if (existingOriginals.isEmpty()) originals = new RootConstructionDomainOriginals(context.core(), sources.domain(), sources.originalsSource());
        else {
            if (!(existingOriginals.orElseThrow() instanceof RootConstructionDomainOriginals actual))
                throw new IllegalArgumentException("construction original-proof owner is not the selected actual Root producer");
            originals = actual; originals.requireCore(context.core(), sources.originalsSource());
        }
        OrdinaryConstructionCollector collector = new OrdinaryConstructionCollector(finance.collector(), ending(), financing());
        peacetimeSources = new ConstructionPeacetimeSources(sources.domain(), collector);
        completion = new OrdinaryConstructionMaterialFollowup(sources.domain(), (borrowed, original) ->
                context.collector().currentPlanning(borrowed, original, original.deadline(), (exactOriginal, current) -> {
                    var read = collector.material(borrowed, exactOriginal);
                    if (!(read instanceof OrdinaryConstructionCollector.MaterialAvailable known)) return read;
                    // These are the genuine captured current Native/Driver originals used by all three read guards.
                    // Keep their actual manifest identity; do not copy an old facts reference into the new observation.
                    Obj input = known.queryInput().with("starting_snapshot", current.frame().semantic()).with("ending_snapshot", current.frame().semantic());
                    return new OrdinaryConstructionCollector.MaterialAvailable(input, known.root(), known.cash(), known.originalReads());
                }), context::borrowedSession);
        policy = new OrdinaryConstructionPolicy(sources.policySource(), collector,
                (request, arguments) -> Optional.of(NativeConstructionEffects.expected(request.before(), request.source(), arguments)), completion);
        OrdinaryPolicy actualPolicy = trackedPolicy(policy);
        NativeEffectRegistry.Observer observer = (command, attempt, dispatch) -> {
            try {
                context.requireCurrent(command.deadline()); var borrowed = context.borrowedSession();
                context.writer().requireSession(borrowed);
                var archive = context.archive().withSession(borrowed);
                NativeConstructionEffects actual = new NativeConstructionEffects(
                        new NativeEffectSnapshots(context.adopted().observations(), archive, context.frameLoader()), context.reads(),
                        context.finance().definitions().contract(FinanceReadContracts.Query.CONSTRUCTION));
                return actual.observe(command, attempt, dispatch);
            } catch (IOException failure) { throw new UncheckedIOException("actual construction material source unavailable", failure); }
        };
        ActionPorts.PreparationPort primitive = command -> {
            requireConstruction(command);
            // The retained native command accepts only its step and expected native revision.
            // Candidate tuple/cost are independently checked before INTENT and after dispatch.
            return new NativeRequest(OrdinaryConstructionPolicy.OPERATION.value(), Optional.empty(), new RawJson(new byte[]{'{','}'}));
        };
        var effect = new NativeEffectRegistry.Binding(OrdinaryConstructionPolicy.OPERATION, sources.nativeActionSource(), primitive, observer);
        var action = new RootExecutableBindings.ActionBinding(effect, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), sources.observerSource());
        var archived = NativeConstructionEffects.archivedVerifier(OrdinaryConstructionPolicy.OPERATION, sources.archiveVerifierSource(),
                context.frameLoader(), finance.definitions().contract(FinanceReadContracts.Query.CONSTRUCTION));
        var pending = new RootDomainIntentPreparation.Binding("construction.original-pending.v1", sources.lifecycleSource(),
                command -> command.operation().equals(OrdinaryConstructionPolicy.OPERATION), this::beforeIntent);
        OrdinaryPlanCompletion actualCompletion = new OrdinaryPlanCompletion() {
            @Override public PlanningDisposition afterPlanning(PlanningRequest original, PlanningResult planned) {
                return completion.afterPlanning(original, planned);
            }
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
                ExecutionDisposition result = completion.afterExecution(actual);
                if (actual.command().operation().equals(OrdinaryConstructionPolicy.OPERATION)) synchronized (plans) { plans.remove(actual.command().actionId()); }
                return result;
            }
        };
        installed = new RootDomainInstallation("ordinary-construction-java-v1", List.of(sources.registration()),
                List.of(), List.of(), List.of(action), List.of(), List.of(archived), List.of(), List.of(), List.of(),
                List.of(pending), Set.of(OrdinaryConstructionPolicy.OPERATION), List.of(actualPolicy), List.of(actualCompletion),
                List.of(new RootDomainInstallation.FixedDomain(action, Domain.building)), List.of(), List.of());
        return installed;
    }
    public Optional<ConstructionDomainLifecycle.Publication> initializeFresh(ContinuityStorePort.Session same, RootInitialEpisodeProof actual) throws IOException {
        StrictJson.require(installed != null && originals != null, "actual construction installer is not installed");
        return originals.initializeFresh(context, same, actual);
    }
    public Optional<ConstructionDomainLifecycle.Publication> initializeFresh(ContinuityStorePort.Session same,FreshCampaignContext actual)throws IOException {
        StrictJson.require(installed!=null&&originals!=null,"actual construction installer is not installed");
        return originals.initializeFresh(context,same,actual);
    }
    public Optional<ConstructionDomainLifecycle.Publication> restore(ContinuityStorePort.Session same, RootRestorationOriginalProof actual) throws IOException {
        StrictJson.require(installed != null && originals != null, "actual construction installer is not installed");
        return originals.restore(context, same, actual);
    }
    public ConstructionNextEpisodeReducer.Initialization initializeNext(ContinuityStorePort.Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof proof) throws IOException {
        StrictJson.require(installed != null && originals != null, "actual construction installer is not installed");
        proof.requireCurrent(same, context);
        var initialized = originals.initializeNext(context, same, proof);
        proof.requireCurrent(same, context);
        return initialized;
    }
    public ConstructionPeacetimeSources.Prior m5Prior(ContinuityStorePort.Session same, PlanningRequest original) throws IOException {
        StrictJson.require(installed != null && peacetimeSources != null, "actual construction source is not installed");
        return context.collector().currentPlanning(same, original, original.deadline(), (exactOriginal, current) -> peacetimeSources.prior(same, exactOriginal));
    }
    public ConstructionPeacetimeSources.Capture m5Capture(ContinuityStorePort.Session same, PlanningRequest original,
            ConstructionPeacetimeSources.Prior prior) throws IOException {
        StrictJson.require(installed != null && peacetimeSources != null, "actual construction source is not installed");
        return context.collector().currentPlanning(same, original, original.deadline(), (exactOriginal, current) -> peacetimeSources.capture(same, exactOriginal, prior));
    }
    private OrdinaryPolicy trackedPolicy(OrdinaryConstructionPolicy actual) {
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage() { return actual.stage(); }
            @Override public ExactRef implementationSource() { return sources.policySource(); }
            @Override public Decision evaluate(PlanningRequest request, Draft previous) {
                Decision selected = actual.evaluate(request, previous);
                if (selected instanceof Replace replace && replace.draft().command().isPresent()) {
                    ActionCommand command = replace.draft().command().orElseThrow();
                    if (command.operation().equals(OrdinaryConstructionPolicy.OPERATION)) synchronized (plans) {
                        RetainedPlan old = plans.get(command.actionId());
                        StrictJson.require(old == null || old.command().equals(command), "construction action identity changed its actual planned body");
                        plans.put(command.actionId(), new RetainedPlan(command, request));
                        while (plans.size() > 128) plans.remove(plans.keySet().iterator().next());
                    }
                }
                return selected;
            }
        };
    }
    private void beforeIntent(ContinuityStorePort.Session session, ActionCommand command) {
        requireConstruction(command);
        try {
            context.writer().requireSession(session); context.requireCurrent(command.deadline());
            RetainedPlan actual;
            synchronized (plans) { actual = plans.get(command.actionId()); }
            StrictJson.require(actual != null && actual.command().equals(command), "construction final gate lacks its actual ordinary producer request");
            PlanningRequest original = actual.request();
            context.collector().currentPlanning(session, original, command, command.deadline(), (exactOriginal, current) -> {
                StrictJson.require(current.frame().identity().equals(command.before()) && current.frame().source().equals(command.source())
                        && current.frame().sessionId().equals(command.sessionId()),
                        "construction final gate source or complete original frame changed; replan");
                StrictJson.require(exactOriginal == original, "construction final gate replaced its actual original planning request");
                policy.revalidateConstruction(session, command, exactOriginal); return Boolean.TRUE;
            });
            sources.domain().prepareIntent(session, command);
        } catch (IOException failure) { throw new UncheckedIOException("construction actual same-writer intent preparation failed", failure); }
    }
    private OrdinaryConstructionCollector.EndingSnapshot ending() {
        return new OrdinaryConstructionCollector.EndingSnapshot() {
            @Override public Obj readCurrent(PlanningRequest request) {
                try { return readCurrent(context.borrowedSession(), request); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public Obj readCurrent(ContinuityStorePort.Session session, PlanningRequest request) {
                try {
                    return context.readiness().current(session, request.before(), request.deadline(), current -> {
                        StrictJson.require(current.frame().identity().equals(request.before()) && current.frame().source().equals(request.source())
                                && current.frame().sessionId().equals(request.sessionId()), "construction read ended on another actual frame/source/session");
                        return current.frame().semantic();
                    });
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
        };
    }
    private OrdinaryConstructionCollector.FinancingPending financing() {
        return new OrdinaryConstructionCollector.FinancingPending() {
            @Override public CanonicalFundingPending.Result readUnderOriginalWriterLock(PlanningRequest request) {
                try { return readUnderOriginalWriterLock(context.borrowedSession(), request); }
                catch (IOException failure) { return new CanonicalFundingPending.Unavailable("actual owned-submission writer unavailable: " + failure.getMessage()); }
            }
            @Override public CanonicalFundingPending.Result readUnderOriginalWriterLock(ContinuityStorePort.Session session, PlanningRequest request) {
                try {
                    context.writer().requireSession(session);
                    return context.finance().fundingPending().read(session, request);
                } catch (IOException failure) { return new CanonicalFundingPending.Unavailable("actual owned-submission original unavailable: " + failure.getMessage()); }
            }
        };
    }
    private static void requireConstruction(ActionCommand command) {
        StrictJson.require(command.operation().equals(OrdinaryConstructionPolicy.OPERATION)
                && command.arguments().members().keySet().equals(Set.of("candidate", "pre_proof_epoch", "ordinary_cash_request", "ordinary_cash_result", ConstructionFundingEvidence.FIELD)),
                "exact original construction command payload required");
        NativeConstructionEffects.Candidate.decode(command.arguments());
        ConstructionFundingEvidence.command(command);
        StrictJson.require(NativeConstructionEffects.expected(command.before(), command.source(), command.arguments()).equals(command.expected()), "construction exact material expectation drift");
    }
    private record RetainedPlan(ActionCommand command, PlanningRequest request) {
        private RetainedPlan { Objects.requireNonNull(command); Objects.requireNonNull(request); }
    }
}
