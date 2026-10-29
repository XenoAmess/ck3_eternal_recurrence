package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** One actual Game's Army read/retreat graph. Concrete products survive menu -> same adopted Driver binding. */
public final class ArmyRuntimeInstaller implements AutoCloseable {
    /** The identical registration exists before Core opens. Only its concrete replay dependencies are bound later. */
    public static final class Prepared {
        private final Sources sources; private final Configuration configuration;
        private final List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> registrations;
        private ArmyRuntimeInstaller installer;
        public Prepared(Sources sources, Configuration configuration) {
            this.sources = Objects.requireNonNull(sources); this.configuration = Objects.requireNonNull(configuration);
            var replay = new org.xar.ck3.control.continuity.writer.DomainBodies.Verifier() {
                @Override public String verify(org.xar.ck3.control.continuity.ContinuityState detached, Optional<org.xar.ck3.control.continuity.writer.DomainBodies.BodyRef> previous,
                        org.xar.ck3.control.continuity.writer.DomainBodies.ImportRequest request, byte[] body) throws IOException {
                    throw new IOException("retreat import requires the actual original writer Head");
                }
                @Override public String verify(org.xar.ck3.control.continuity.writer.WriterContracts.Head head, Optional<org.xar.ck3.control.continuity.writer.DomainBodies.BodyRef> previous,
                        org.xar.ck3.control.continuity.writer.DomainBodies.ImportRequest request, byte[] body) throws IOException {
                    return actual().required().retreatDomain().registration(Prepared.this.sources.actualDomainProducerClosure()).verifier().verify(head, previous, request, body);
                }
            };
            registrations = List.of(new org.xar.ck3.control.continuity.writer.DomainBodies.Registration(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.ACTIVE_RETREAT,
                    org.xar.ck3.control.application.planning.military.ActiveRetreatState.SCHEMA, org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES,
                    sources.actualDomainProducerClosure(), replay));
        }
        public List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> domainRegistrations() { return registrations; }
        public Optional<RootArmyStockReadRuntime.Configuration> stockConfiguration(){return configuration.stock();}
        public Optional<ArmyWarSupplementalReads.StockSources> stockSources(){return sources.supplementalWar().stockSources();}
        public synchronized ArmyRuntimeInstaller install(RootRuntimeContext context) {
            if(installer != null) { if(installer.context == context) {StrictJson.require(!installer.closed,"retired Army installation cannot reopen live source custody");return installer;} StrictJson.require(installer.context.core() == context.core(),"one original Core owns the prepared Army registration across actual Game restoration");
                try{installer.close();}catch(IOException unavailable){throw new UncheckedIOException("original Army resources could not retire before replacement",unavailable);} }
            installer = new ArmyRuntimeInstaller(context, sources, configuration, registrations); installer.install(); return installer;
        }
        private synchronized ArmyRuntimeInstaller actual() { return Objects.requireNonNull(installer, "actual Army replay dependencies are not bound; no import is qualified"); }
    }
    public record ReadSources(ExactRef definition, ExactRef decoder) {
        public ReadSources { source(definition); source(decoder); }
    }
    public record ServiceSources(ExactRef closed, ExactRef battle, ExactRef preview, ExactRef order, ExactRef window) {
        public ServiceSources { source(closed); source(battle); source(preview); source(order); source(window); }
    }
    public record Sources(ReadSources closed, ReadSources battle, ReadSources route, ReadSources window, ReadSources reconciliation,
            ArmyWarExitTruceReads.Sources warExitTruce,ArmySpecialWarReads.Sources specialWar,
            ArmyWarSupplementalReads.Sources supplementalWar, RootArmyStockReadRuntime.Sources stockRead,ExactRef domain, ExactRef composite,
            ServiceSources services, List<ExactRef> actualDomainProducerClosure) {
        public Sources { Objects.requireNonNull(closed); Objects.requireNonNull(battle); Objects.requireNonNull(route); Objects.requireNonNull(window); Objects.requireNonNull(reconciliation); Objects.requireNonNull(warExitTruce);Objects.requireNonNull(specialWar);Objects.requireNonNull(supplementalWar);Objects.requireNonNull(stockRead); source(domain); source(composite); Objects.requireNonNull(services);
            actualDomainProducerClosure = List.copyOf(actualDomainProducerClosure); StrictJson.require(!actualDomainProducerClosure.isEmpty() && actualDomainProducerClosure.size() <= 64, "full original retreat producer source closure required"); actualDomainProducerClosure.forEach(ArmyRuntimeInstaller::source); }
    }
    public record Configuration(Duration commandReadTimeout, Duration reconciliationReadTimeout, ArmyRetreatOrderService.ActionIds actualRootActionIds,
            Optional<RootArmyStockReadRuntime.Configuration> stock) {
        public Configuration { finite(commandReadTimeout); finite(reconciliationReadTimeout); Objects.requireNonNull(actualRootActionIds);Objects.requireNonNull(stock); }
        public Configuration(Duration commandReadTimeout,Duration reconciliationReadTimeout,ArmyRetreatOrderService.ActionIds actualRootActionIds){this(commandReadTimeout,reconciliationReadTimeout,actualRootActionIds,Optional.empty());}
    }
    public record Installed(RootDomainInstallation installation, ArmyClosedReadService closedReads, ArmyBattleReadService battleReads,
            ArmyRetreatService retreatReads, ArmyRetreatOrderService retreatOrders, ArmyRetreatComposite retreatComposite,
            ArmyRetreatDomain retreatDomain, ArmyRetreatFrames frames, ArmyWindowReads windowContracts, ArmyWindowService windows, ArmyBattleReads battleContracts, ArmyRouteReads routeContracts, ArmyWindowAttempts.Source windowAttempts,
            ArmyClosedReadContracts closedContracts, ArmyBattleReconciliationReads reconciliationContracts, ArmyRetreatPostReadCollector reconciliationPost,
            ArmyWarExitTruceReads warExitTruceContracts,ArmySpecialWarReads specialWarReads,
            ArmyWarSupplementalReads supplementalWarReads,Optional<RootArmyStockReadRuntime> stockReads) {
        public Installed { Objects.requireNonNull(installation); Objects.requireNonNull(closedReads); Objects.requireNonNull(battleReads); Objects.requireNonNull(retreatReads); Objects.requireNonNull(retreatOrders); Objects.requireNonNull(retreatComposite); Objects.requireNonNull(retreatDomain); Objects.requireNonNull(frames); Objects.requireNonNull(windowContracts); Objects.requireNonNull(windows); Objects.requireNonNull(battleContracts); Objects.requireNonNull(routeContracts); Objects.requireNonNull(windowAttempts); Objects.requireNonNull(closedContracts); Objects.requireNonNull(reconciliationContracts); Objects.requireNonNull(reconciliationPost); Objects.requireNonNull(warExitTruceContracts);
            var actual = warExitTruceContracts.families();
            StrictJson.require(actual.size() == 1 && installation.readFamilies().stream().filter(f -> f.id().equals(ArmyWarExitTruceReads.FAMILY)).count() == 1
                    && installation.readFamilies().stream().anyMatch(f -> f == actual.getFirst())
                    && actual.getFirst().guardMode() == ReadContract.GuardMode.RECONCILIATION_OBSERVATION,
                    "the identical mandatory truce reconciliation family must occur once in the actual pre-freeze Army inventory");
            Objects.requireNonNull(specialWarReads);var special= specialWarReads.families();
            StrictJson.require(special.size()==ArmySpecialWarReads.Kind.values().length,"all mandatory special war READ families required");
            for(var family:special)StrictJson.require(family.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    &&installation.readFamilies().stream().filter(f->f.id().equals(family.id())).count()==1
                    &&installation.readFamilies().stream().anyMatch(f->f==family),"the same mandatory special war READ family must occur once before catalog freeze");
            Objects.requireNonNull(supplementalWarReads);Objects.requireNonNull(stockReads);
            StrictJson.require(stockReads.isPresent()==supplementalWarReads.sources().stockSources().isPresent(),"stock source facts and the identical actual runtime port must be installed together");
            var supplemental=supplementalWarReads.families();
            StrictJson.require(supplemental.size()==ArmyWarSupplementalReads.Kind.values().length,"both mandatory supplemental war READ families required");
            for(var family:supplemental)StrictJson.require(family.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    &&installation.readFamilies().stream().filter(f->f.id().equals(family.id())).count()==1
                    &&installation.readFamilies().stream().anyMatch(f->f==family),"the same mandatory supplemental war READ family must occur once before catalog freeze"); }
    }
    private final RootRuntimeContext context; private final Sources sources; private final Configuration configuration;
    private final List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> preparedRegistrations;
    private RootExecutableBindings.CompositeFamily<OperationKey> parentFamily;
    private Installed installed;
    private boolean closed;
    private boolean resourcesClosed;
    public ArmyRuntimeInstaller(RootRuntimeContext actualContext, Sources exactSources, Configuration actualConfiguration) {
        this(actualContext, exactSources, actualConfiguration, List.of());
    }
    private ArmyRuntimeInstaller(RootRuntimeContext actualContext, Sources exactSources, Configuration actualConfiguration,
            List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> originalRegistrations) {
        context = Objects.requireNonNull(actualContext); sources = Objects.requireNonNull(exactSources); configuration = Objects.requireNonNull(actualConfiguration);
        preparedRegistrations = List.copyOf(originalRegistrations);
        StrictJson.require(sources.supplementalWar().stockSources().isPresent()==configuration.stock().isPresent(),"stock facts must match the explicit configured branch");
        if(configuration.stock().isPresent()) {
            var actual=configuration.stock().orElseThrow();var refs=sources.supplementalWar().stockSources().orElseThrow();
            StrictJson.require(refs.decoder().equals(sources.stockRead().stockDecoder())&&refs.pair().equals(actual.pair())&&refs.pins().equals(actual.pins())
                    &&refs.nativeSourceCheckout().equals(actual.input().nativeSourceCheckout()),"stock catalog scope differs from its same configured originals");
        }
    }
    /** Before menu: installs callable finite families and a real composite; no adopted Driver is fabricated. */
    public synchronized Installed install() {
        StrictJson.require(!closed&&installed == null, "one Army installation per actual Root Game required");
        var frames = new ArmyRetreatFrames(() -> context.adopted().observations());
        var closedContracts = new ArmyClosedReadContracts(sources.closed().definition(), sources.closed().decoder());
        var battleContracts = new ArmyBattleReads(sources.battle().definition(), sources.battle().decoder(), context.reads());
        var routeContracts = new ArmyRouteReads(sources.route().definition(), sources.route().decoder(), context.reads());
        var windowContracts = new ArmyWindowReads(sources.window().definition(),sources.window().decoder(),context.reads(),context.archive());
        var reconciliationContracts=new ArmyBattleReconciliationReads(sources.reconciliation().definition(),sources.reconciliation().decoder(),context.reads());
        var warExitTruceContracts=new ArmyWarExitTruceReads(sources.warExitTruce(),context.reads());
        var specialWarReads=new ArmySpecialWarReads(sources.specialWar(),context.reads(),
                (selection,receipt)->RootArmyReadPacketVerifier.require(selection.context(),selection.operation(),ArmySpecialWarReads.nativeArguments(selection),receipt));
        Optional<RootArmyStockReadRuntime> stockReads;
        try{stockReads=configuration.stock().isPresent()?Optional.of(new RootArmyStockReadRuntime(context,sources.stockRead(),configuration.stock().orElseThrow())):Optional.empty();}
        catch(IOException unavailable){throw new UncheckedIOException("configured stock source runtime is unavailable",unavailable);}
        ArmyWarSupplementalReads.OriginalPacketVerifier supplementalPackets=(selection,receipt)->RootArmyReadPacketVerifier.require(selection.context(),selection.operation(),ArmyWarSupplementalReads.nativeArguments(),receipt);
        var supplementalWarReads=stockReads.isPresent()?new ArmyWarSupplementalReads(sources.supplementalWar(),context.reads(),
                ()->context.archive().withSession(borrowed()),context.frameLoader(),supplementalPackets,stockReads.orElseThrow())
                :new ArmyWarSupplementalReads(sources.supplementalWar(),context.reads(),()->context.archive().withSession(borrowed()),context.frameLoader(),supplementalPackets);
        var reconciliationPost=new ArmyRetreatReconciliationPost(reconciliationContracts,context::readCatalog,(command,attempt)->{
            try { var same=context.borrowedSession(); return context.reconciliation().currentForCommand(same,command,lease->{
                StrictJson.require(lease.attempt().equals(attempt),"retreat observer changed its actual retained primitive attempt");
                return new ArmyRetreatReconciliationPost.Scope(same,lease.identity(),lease.complete(),lease.validUntil());
            }); } catch(IOException failure) { throw new UncheckedIOException(failure); }
        });
        var windows = new ArmyWindowService(context.writer(),frames,windowContracts,context::readCatalog,this::commandDeadline);
        var domain = new ArmyRetreatDomain(context.archive().artifactStore(), context.archive(), context.frameLoader(), (head, start) ->
                new NativeRecordedEvidenceVerifier(context.archive(), this::borrowed, context.originals(), context.frameLoader(), context.bindings()).verify(head, start));
        var previews = new ArmyRetreatPreview(frames, battleContracts, routeContracts, context::readCatalog,context.archive(),context.frameLoader());
        var reads = new ArmyRetreatService(context.writer(), domain, frames, previews, battleContracts, context::readCatalog, this::commandDeadline, this::publishParent);
        StrictJson.require(context.core().journal() instanceof ContinuityActionJournal, "Army must borrow the original concrete continuity journal");
        var composite = new ArmyRetreatComposite(domain, frames, battleContracts, routeContracts, context::readCatalog, reads,
                (ContinuityActionJournal) context.core().journal(), context.archive(), context.frameLoader(), (original, retained) -> reconciliationDeadline());
        var compositeBinding = new RootExecutableBindings.CompositeBinding(composite, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.move-army-N-to-N"), sources.composite(), sources.composite());
        parentFamily = new RootExecutableBindings.CompositeFamily<>("army-retreat-original-order", OperationKey.class, compositeBinding, sources.composite(),
                operation -> new RawJson(StrictJson.canonical(StrictJson.object().put("operation", operation.value()))), operation -> operation,
                operation -> composite.archivedVerifier(operation, sources.composite()));
        var closed = new ArmyClosedReadService(() -> currentFrame(frames), context.reads(), context::readCatalog, closedContracts);
        var battle = new ArmyBattleReadService(context.writer(), battleContracts, context::readCatalog, () -> currentFrame(frames));
        var orders = new ArmyRetreatOrderService(context.writer(), domain, frames, composite, new ActionCoordinatorPort() {
            @Override public ActionReceipt execute(ActionCommand command) { publishParent(command.operation()); return context.actions().execute(command); }
            @Override public ActionReceipt execute(ContinuityStorePort.Session session, ActionCommand command) { publishParent(command.operation()); return context.actions().execute(session, command); }
            @Override public ActionReceipt reconcile(String id) { return context.actions().reconcile(id); }
            @Override public ActionReceipt reconcile(ContinuityStorePort.Session session, String id) { return context.actions().reconcile(session, id); }
        }, context.archive(), this::commandDeadline, configuration.actualRootActionIds());
        List<RootReadContractCatalog.Family<?,?>> families = new ArrayList<>(closedContracts.families()); families.addAll(battleContracts.families()); families.add(routeContracts.family()); families.addAll(windowContracts.families()); families.addAll(reconciliationContracts.families()); families.addAll(warExitTruceContracts.families());families.addAll(specialWarReads.families());families.addAll(supplementalWarReads.families());
        var pending = new RootDomainIntentPreparation.Binding("army-retreat-durable-exclusion", sources.composite(), command -> composite.supports(command.operation()), composite::prepareIntent);
        var registration = preparedRegistrations.isEmpty() ? List.of(domain.registration(sources.actualDomainProducerClosure())) : preparedRegistrations;
        var installation = new RootDomainInstallation("army-native-reads-retreat", registration, List.of(), families,
                List.of(), List.of(compositeBinding), List.of(), List.of(), List.of(parentFamily), List.of(), List.of(pending), Set.of(), List.of(), List.of(), List.of(), List.of(),
                List.of(new RootDomainInstallation.CompositeDomain(compositeBinding, Domain.war)));
        installed = new Installed(installation, closed, battle, reads, orders, composite, domain, frames, windowContracts, windows, battleContracts, routeContracts, windowContracts.attempts(),closedContracts,reconciliationContracts,reconciliationPost,warExitTruceContracts,specialWarReads,supplementalWarReads,stockReads); return installed;
    }
    /** Explicit private-minted fresh entry only. Restoration must import its complete original claims and pending. */
    public ArmyRetreatDomain.Known initialize(ContinuityStorePort.Session session, RootInitialEpisodeProof actualFirstEntry) throws IOException {
        var product = required(); Objects.requireNonNull(actualFirstEntry).requireCurrent(session);
        StrictJson.require(actualFirstEntry.source().equals(context.source()) && actualFirstEntry.adopted() == context.adopted(), "fresh retreat initialization belongs to another actual adopted Root Game");
        return product.retreatDomain().initializeNewEpisode(session, actualFirstEntry.frame());
    }
    public ArmyRetreatDomain.Known initialize(ContinuityStorePort.Session session,FreshCampaignContext actual)throws IOException {
        context.writer().requireSession(session);actual.requireCurrent(session);
        if(actual.adopted()!=context.adopted())throw new IOException("Fresh Army input belongs to another real Driver");
        return required().retreatDomain().initializeNewEpisode(session,actual.frame());
    }
    /** Restoration retains the latest canonical domain, including claims created after the SAVE. It never imports an empty state. */
    public ArmyRetreatDomain.Known adoptRestored(ContinuityStorePort.Session session,RootRestorationOriginalProof actualRestoration)throws IOException {
        context.writer().requireSession(session);Objects.requireNonNull(actualRestoration).requireCurrent(session);
        var before=session.head();var retained=required().retreatDomain().read(session);
        StrictJson.require(session.head().digest().equals(before.digest())&&session.head().state().sequence()==before.state().sequence(),"restoration Army domain read mutated its actual canonical Head");
        return retained;
    }
    /** Public MCP keeps these identical typed services. Registration describes only these ten actual source bodies. */
    public List<PublicBindings.BoundBinding> installPublic(PublicBindings bindings) {
        var product = required(); List<PublicBindings.BoundBinding> actual = new ArrayList<>(); actual.addAll(product.closedReads().install(bindings, sources.services().closed()));
        actual.addAll(product.battleReads().install(bindings, sources.services().battle())); actual.add(product.retreatReads().installPreview(bindings, sources.services().preview())); actual.add(product.retreatOrders().install(bindings, sources.services().order())); actual.addAll(product.windows().install(bindings,sources.services().window())); return List.copyOf(actual);
    }
    public ArmyRetreatDomain.Known currentRetreatDomain(ContinuityStorePort.Session session) throws IOException { return required().retreatDomain().read(session); }
    /** Reuses the identical retreat service and parent family for central Root dispatch. No read or submission occurs. */
    public ActionCommand prepareRetreatCommand(ContinuityStorePort.Session same,ArmyCalls.RetreatOrder input,
            ArmyRetreatFrames.Current before,String actualActionId)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(before);context.requireCurrent(before.deadline());
        context.collector().requireHeldFrame(same,before.actual());
        StrictJson.require(before.actual().identity().game().equals(context.game().generation())
                &&before.actual().identity().machineId().equals(context.game().machineId())
                &&before.actual().source().equals(context.source())
                &&before.actual().sessionId().equals(context.game().sessionId()),"retreat command preparation crossed its actual held Root Game/source/session");
        ActionCommand command=required().retreatOrders().prepareCommand(same,input,before,actualActionId);
        publishParent(command.operation());return command;
    }
    /** Pure candidate issuance for the Root's exact primitive-pending observation allowlist. No query or publication occurs here. */
    public List<RootReconciliationAuthority.AllowedRead> reconciliationReads(ActionReceipt original,ReconciliationIdentity identity,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual,Instant deadline) {
        String schema=original.command().expected().observerSchema();
        if(schema.equals(org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.SCHEMA))
            return warExitTruceReads(original,identity,actual,deadline);
        if(!schema.equals(ArmyRetreatComposite.MOVE_OBSERVER))return List.of();
        StrictJson.require(original.command().actionId().equals(identity.pending().actionId())&&original.bodySha256().equals(identity.pending().bodySha256())
                &&actual.identity().equals(identity.factual())&&actual.source().equals(identity.source())&&actual.sessionId().equals(identity.sessionId()),"retreat query candidates crossed the Root's actual original primitive/factual scope");
        return ArmyRetreatReconciliationPost.selections(original.command(),identity,deadline).stream().map(selection->{
            var issued=required().reconciliationContracts().issue(context.readCatalog(),selection);
            return new RootReconciliationAuthority.AllowedRead(issued.contract(),issued.request().arguments(),RootReconciliationAuthority.QueryKind.ARMY_M5);
        }).toList();
    }
    /** This supplies candidates only. Root independently reopens original/current frames and applies WAR_EXIT_TRUCE qualification. */
    private List<RootReconciliationAuthority.AllowedRead> warExitTruceReads(ActionReceipt original,ReconciliationIdentity identity,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual,Instant deadline) {
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
            var retained=archive.loadReceipt(identity.pending().originalReceipt());
            // This same pure supplier serves live admission and archived interpretation. The sole Root authority
            // checks current journal membership for live reads; history must retain its original unresolved receipt
            // even after the current journal later becomes Applied/Settled.
            StrictJson.require(retained.equals(original)&&!retained.settled()
                    &&retained.command().actionId().equals(identity.pending().actionId())
                    &&retained.bodySha256().equals(identity.pending().bodySha256())
                    &&retained.command().before().equals(identity.pending().originalBefore())
                    &&retained.bodySha256().equals(ActionCodec.bodySha256(retained.command()))
                    &&actual.identity().equals(identity.factual())&&actual.source().equals(identity.source())
                    &&actual.sessionId().equals(identity.sessionId()),"truce candidate crossed its canonical original receipt or actual factual frame");
            var attempt=ActionTransitions.attempt(retained.state()).orElseThrow(()->new IOException("truce candidate has no retained original Attempt"));
            RootGuardEvidence.requireHistory(attempt.guard(),archive,same);
            var before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
            if(NativeWarExitEffects.truceQuery(retained.command(),before,actual).isEmpty())return List.of();
            var selected=new ArmyWarExitTruceReads.Selection(identity,retained.command(),attempt,before,actual,deadline);
            var issued=required().warExitTruceContracts().issue(context.readCatalog(),selected);
            return List.of(new RootReconciliationAuthority.AllowedRead(issued.contract(),issued.request().arguments(),RootReconciliationAuthority.QueryKind.WAR_EXIT_TRUCE));
        } catch(IOException unavailable) { throw new UncheckedIOException("actual original-pending truce candidate unavailable",unavailable); }
    }
    public RootActionGuard.DerivedChildAdmission derivedChildAdmission() { return required().retreatComposite().derivedAdmission(); }
    public NativeRecordedEvidenceVerifier.DerivedGuardVerifier derivedGuardVerifier() { return required().retreatComposite().derivedGuardVerifier(); }
    public Installed products() { return required(); }
    /** Admission has permanently closed. This fact alone is not evidence that an OS close succeeded. */
    public synchronized boolean isClosed(){return closed;}
    /** Called by the actual Catalog after accepted calls drain, before the original writer closes. */
    @Override public synchronized void close()throws IOException {
        closed=true;if(resourcesClosed)return;if(installed!=null&&installed.stockReads().isPresent())installed.stockReads().orElseThrow().close();resourcesClosed=true;
    }
    public void publishCurrentToken(ContinuityStorePort.Session session) throws IOException {
        var known = currentRetreatDomain(session); ArmyRetreatTokens.capabilityToken(known.state()).ifPresent(token -> publishParent(new OperationKey(org.xar.ck3.control.planning.opportunity.OpportunityJson.text(token.get("order_step"), "actual order step"))));
    }
    private void publishParent(OperationKey operation) {
        StrictJson.require(ArmyRetreatComposite.handles(operation), "Army publisher may only issue its actual retreat composite"); context.bindings().issueComposite(Objects.requireNonNull(parentFamily), operation);
    }
    private ArmyTypes.Context current(ArmyRetreatFrames frames) {
        return currentFrame(frames).context();
    }
    private ArmyRetreatFrames.Current currentFrame(ArmyRetreatFrames frames) {
        try { return frames.current(commandDeadline()); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("actual Army frame observation interrupted", interrupted); }
    }
    private ContinuityStorePort.Session borrowed() { try { return context.borrowedSession(); } catch (IOException error) { throw new UncheckedIOException(error); } }
    private Instant commandDeadline() { return context.clock().instant().plus(configuration.commandReadTimeout()); }
    private Instant reconciliationDeadline() { var end = context.clock().instant().plus(configuration.reconciliationReadTimeout()); try { context.requireCurrent(end); return end; } catch (IOException error) { throw new UncheckedIOException(error); } }
    private synchronized Installed required() { return Objects.requireNonNull(installed, "actual Army installation is unavailable"); }
    private static void source(ExactRef ref) { Objects.requireNonNull(ref); StrictJson.require(ref.bytes() > 0, "actual immutable implementation source required"); }
    private static void finite(Duration value) { Objects.requireNonNull(value); StrictJson.require(!value.isZero() && !value.isNegative() && value.compareTo(Duration.ofMinutes(1)) <= 0, "positive finite Army read timeout required"); }
}
