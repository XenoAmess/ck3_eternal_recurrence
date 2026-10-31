package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import java.time.Instant;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.advance.LifeAdvanceCommands;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.advance.LifeAdvanceRootReplay;
import org.xar.ck3.control.application.advance.ProductionAdvanceReadiness;
import org.xar.ck3.control.application.advance.PendingUiLifeAdvance;
import org.xar.ck3.control.application.advance.AdvanceReadiness;
import org.xar.ck3.control.application.history.DriverHistoryAccess;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Concrete Life assembly over the original Root and the one battle-owned clock infrastructure.
 * Installation is pure construction before adoption; actual Driver/collector objects resolve only when called.
 */
public final class RootLifeRuntimeFactory {
    private RootLifeRuntimeFactory() { }

    public record Sources(ExactRef compositeImplementation,ExactRef commandProducer,
            ExactRef resultDecoder,ExactRef archivedVerifier) {
        public Sources {
            for(ExactRef ref:List.of(compositeImplementation,commandProducer,resultDecoder,archivedVerifier))
                require(ref.bytes()>0,"actual complete Life implementation/command/result/replay source required");
        }
    }

    /** One Prepared binds the same actual infrastructure and settings for every physical Root context. */
    public static final class Prepared {
        private final Sources sources;
        private final RootAdvanceRuntimeFacts.Settings settings;
        private final RootAdvanceInfrastructureFactory.Prepared infrastructure;
        private final Map<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        private final Set<RootRuntimeContext> entered=Collections.newSetFromMap(new IdentityHashMap<>());

        public Prepared(Sources actualSources,RootAdvanceRuntimeFacts.Settings actualSettings,
                RootAdvanceInfrastructureFactory.Prepared sameInfrastructure) {
            sources=Objects.requireNonNull(actualSources);settings=Objects.requireNonNull(actualSettings);
            infrastructure=Objects.requireNonNull(sameInfrastructure);
        }

        public List<ExactRef> requiredSources() {
            var refs=new java.util.LinkedHashSet<ExactRef>();
            refs.addAll(List.of(sources.compositeImplementation(),sources.commandProducer(),sources.resultDecoder(),sources.archivedVerifier(),settings.original()));
            refs.addAll(infrastructure.requiredSources());return List.copyOf(refs);
        }

        public synchronized Installed install(RootRuntimeContext context,RootCrownRetryRuntime.Prepared sameRetry)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(sameRetry);
            require(context.core()==sameRetry.core(),"Life and Crown retry must retain the identical original Core");
            Installed existing=installed.get(context);
            if(existing!=null) {
                require(existing.retry==sameRetry,"same physical Life context cannot replace its Crown producer");
                return existing;
            }
            require(installed.size()<64 && !entered.contains(context),
                    "physical Life installation exceeded its bound or an earlier partial construction remains unresolved");
            entered.add(context);
            var candidate=new Installed(context,sameRetry,sources,settings,infrastructure);
            installed.put(context,candidate);return candidate;
        }
    }

    public static final class Installed {
        private final RootRuntimeContext context;
        private final RootCrownRetryRuntime.Prepared retry;
        private final DriverHistoryAccess history;
        private final RootAdvanceRuntimeFacts runtimeFacts;
        private final ProductionAdvanceReadiness readiness;
        private final PendingUiLifeAdvance.Scope pendingUiScope;
        private final AdvanceReadiness.Port scopedReadiness;
        private final RootAdvanceInfrastructureFactory.Installed infrastructure;
        private final LifeAdvanceRootReplay replay;
        private final LifeAdvanceComposite composite;
        private final LifeAdvanceCommands commands;
        private final RootDomainInstallation installation;

        private Installed(RootRuntimeContext context,RootCrownRetryRuntime.Prepared retry,Sources sources,
                RootAdvanceRuntimeFacts.Settings settings,RootAdvanceInfrastructureFactory.Prepared clockInfrastructure)throws IOException {
            this.context=context;this.retry=retry;
            // Resolve the actual later-adopted authority on every invocation. No dummy
            // Driver, synthetic Known or replacement repository can enter this graph.
            history=new DriverHistoryAccess(()->context.adopted().authority(),context.archive());
            runtimeFacts=new RootAdvanceRuntimeFacts(context,retry.due(),retry.retainedProof(),settings);
            readiness=new ProductionAdvanceReadiness(history,runtimeFacts,retry.due(),this::borrowedSession,runtimeFacts);
            pendingUiScope=new PendingUiLifeAdvance.Scope(context::borrowedSession);
            scopedReadiness=pendingUiScope.readiness(readiness);
            infrastructure=clockInfrastructure.install(context,scopedReadiness,pendingUiScope);
            replay=new LifeAdvanceRootReplay(context.frameLoader());
            composite=new LifeAdvanceComposite(infrastructure.observations(),scopedReadiness,infrastructure.timeline(),
                    infrastructure.statuses(),context.core().actions(),context.archive(),context.clock(),replay,this::readCancellationStatus);
            commands=new LifeAdvanceCommands(composite,pendingUiScope);
            var binding=new RootExecutableBindings.CompositeBinding(composite,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.empty(),sources.compositeImplementation(),sources.resultDecoder());
            var archived=List.of(replay.binding(new OperationKey("life-advance"),sources.archivedVerifier()),
                    replay.binding(new OperationKey("life-advance-one-day"),sources.archivedVerifier()));
            installation=new RootDomainInstallation("shared-actual-life-advance",List.of(),List.of(),List.of(),List.of(),
                    List.of(binding),archived,List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        /** One genuine fixed physical Status read; its scope never grants ordinary Driver readiness or submission. */
        private LifeAdvanceComposite.CancellationRead readCancellationStatus(ActionCommand parent, CompositeExecution execution,
                List<ActionReceipt> proposedChildren, Instant deadline) {
            try {
                return context.withSession(same -> {
                    var originalArchive = context.archive().withSession(same);
                    var heldHead = same.head();
                    var actual = ContinuityActionJournal.lookup(heldHead.state(), parent.actionId(), originalArchive).orElseThrow();
                    require(actual.command().equals(parent) && actual.state() instanceof ActionState.CompositeUnknown unknown
                            && unknown.execution().equals(execution), "Life physical Status changed its canonical unresolved parent");
                    var children = execution.children().stream().map(bound -> {
                        var child = ContinuityActionJournal.lookup(heldHead.state(), bound.actionId(), originalArchive).orElseThrow();
                        require(child.bodySha256().equals(bound.bodySha256()), "Life physical Status child body differs from canonical history");
                        return child;
                    }).toList();
                    require(children.equals(proposedChildren), "Life physical Status borrowed another child prefix");
                    if (children.getLast().command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX))
                        LifeAdvanceComposite.requireCancelledInitializationPrefix(parent, execution, children);
                    else LifeAdvanceComposite.requireArmedInitializationPrefix(parent, execution, children);
                    var profile = infrastructure.physicalStatuses();
                    RootUnknownSentinelReadProfile.requireInstalled(profile, infrastructure.statuses());
                    PhysicalStatusIdentity.requireProfile(profile);
                    PlanningReadResult.Known<Status> status = context.physicalStatusReads().withObserved(same, deadline, lease -> {
                        var request = PlanningReadRequest.newStatusOnly(lease.identity(), profile.operation(),
                                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()), deadline);
                        var result = context.reads().read(same, profile, request);
                        if (!(result instanceof PlanningReadResult.Known<Status> known))
                            throw new IOException("Life physical Status unavailable: " + ((PlanningReadResult.Unavailable<Status>) result).reason());
                        require(known.receipt().request().equals(request) && known.receipt().contractId().equals(profile.contractId())
                                && known.value().equals(ClockStatusRead.decode(known.receipt().original())),
                                "Life physical Status returned another request or decoded value");
                        return known;
                    });
                    // Exit physical-only custody, then use the existing genuine fresh full-state READ producer.
                    context.adopted().authority().requireOutsideObservationScope(same);
                    NativeFreshSnapshotPort.Result fresh;
                    try { fresh = context.transport().readFreshFullState(deadline); }
                    catch (InterruptedException interrupted) {
                        Thread.currentThread().interrupt();
                        var failure = new java.io.InterruptedIOException("Life cancellation fresh after-Status read interrupted; no replay");
                        failure.initCause(interrupted); throw failure;
                    }
                    if (fresh instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                        String reason = unavailable.reason();
                        throw new IOException("Life cancellation fresh after-Status read unavailable: " + reason.substring(0, Math.min(512, reason.length())));
                    }
                    var received = (NativeFreshSnapshotPort.Received) fresh;
                    NativeFreshSnapshotPort.verifyAfter(status.receipt().original(), received);
                    var ending = LifeAdvanceRootReplay.push(context.adopted().observations().project(received.originalFrame(), deadline));
                    var custody = status.receipt().original().custody().orElseThrow(); custody.verify(status.receipt());
                    require(!ending.observedAt().isBefore(custody.responseReceived().observedAt()),
                            "Life cancellation has no fresh complete semantic frame after its actual physical Status");
                    return new LifeAdvanceComposite.CancellationRead(status, ending);
                });
            } catch (IOException failure) { throw new UncheckedIOException("actual source-owned Life physical Status unavailable", failure); }
        }
        private ContinuityStorePort.Session borrowedSession() {
            try {return context.borrowedSession();}
            catch(IOException failure) {throw new UncheckedIOException("Life requires the actual borrowed Root writer",failure);}
        }
        /** Installer ownership only; this guard grants no observation, dispatch or Ready qualification. */
        public void requireContext(RootRuntimeContext actual)throws IOException {
            require(actual==context && actual.core()==retry.core(),"Life product belongs to another actual Root context or Core");
            require(infrastructure!=null && composite!=null && commands!=null && replay!=null && pendingUiScope!=null && scopedReadiness!=null
                    && installation.composites().size()==1 && installation.composites().getFirst().handler()==composite,
                    "Life product lost its privately constructed shared infrastructure/composite custody");
        }
        public DriverHistoryAccess history(){return history;}
        public RootAdvanceRuntimeFacts runtimeFacts(){return runtimeFacts;}
        public ProductionAdvanceReadiness readiness(){return readiness;}
        /** The same privately constructed scope consumed by infrastructure, Life and Commands. */
        public PendingUiLifeAdvance.Scope pendingUiScope(){return pendingUiScope;}
        public RootAdvanceInfrastructureFactory.Installed infrastructure(){return infrastructure;}
        public LifeAdvanceRootReplay replay(){return replay;}
        public LifeAdvanceComposite composite(){return composite;}
        public LifeAdvanceCommands commands(){return commands;}
        /** Life-only bindings; the unique Root aggregator also consumes infrastructure().installation() once. */
        public RootDomainInstallation installation(){return installation;}
        public List<RootDomainInstallation> installations(){return List.of(infrastructure.installation(),installation);}
    }
}
