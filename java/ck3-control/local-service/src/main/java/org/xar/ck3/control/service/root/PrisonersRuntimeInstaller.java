package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** One concrete ordinary prisoner graph per actual physical Game. Constructors and inventory membership grant no dispatch qualification. */
public final class PrisonersRuntimeInstaller {
    private static final String WAR_CAPABILITY="game.command.query-war-prisoner-release-pairs-v1-N";
    public record Sources(ExactRef collectionProducer,ExactRef collectionDecoder,ExactRef warProducer,ExactRef warDecoder,
            ExactRef actionProducer,ExactRef actionPreparation,ExactRef actionObserver,ExactRef actionDecoder,ExactRef recordedVerifier,
            ExactRef ordinaryPolicies,ExactRef successionPolicies,ExactRef stockInteractions,ExactRef ledgerProducer,ExactRef episodeLedger) {
        public Sources {
            for(ExactRef ref:List.of(collectionProducer,collectionDecoder,warProducer,warDecoder,actionProducer,actionPreparation,
                    actionObserver,actionDecoder,recordedVerifier,ordinaryPolicies,successionPolicies,stockInteractions,ledgerProducer,episodeLedger))
                StrictJson.require(ref.bytes()>0,"complete actual prisoner implementation sources required");
        }
        public List<ExactRef> domainClosure() {
            return List.of(collectionProducer,collectionDecoder,warProducer,warDecoder,actionProducer,actionPreparation,
                    actionObserver,actionDecoder,recordedVerifier,ordinaryPolicies,stockInteractions,ledgerProducer,episodeLedger);
        }
    }
    public record Configuration(PrisonersRuntimeDefinitions definitions) {
        public Configuration { Objects.requireNonNull(definitions); }
    }
    public record WarId(long value) { public WarId { StrictJson.require(value>0 && value<0xffff_ffffL,"valid full native war ID required"); } }
    private final RootRuntimeContext context;
    private final Sources sources;
    private final Configuration configuration;
    private final PrisonerNativeQueries nativeQueries;
    private final RootReadContractCatalog.Family<WarId,RawJson> warFamily;
    private final PrisonerPlanningPorts.Queries queries;
    private final PrisonerActionBinding12004 preparation;
    private final PrisonerPlanningPorts.Bindings ordinary;
    private final PrisonerPendingContributor12004 pending;
    private final RootDomainInstallation installation;
    private NativePrisonerEffects12004 effects;
    private KnownInteractionsRuntimeInstaller boundKnown;
    // Bounded actual source originals only. No borrowed writer Session is retained.
    private PlanningReadResult.Known<RawJson> publicCollection;
    private ActionCommand publicCommand;
    private RawJson publicInput;
    private long publicTarget;
    public PrisonersRuntimeInstaller(RootRuntimeContext context,Sources sources,Configuration configuration)throws IOException {
        this.context=Objects.requireNonNull(context);this.sources=Objects.requireNonNull(sources);this.configuration=Objects.requireNonNull(configuration);
        nativeQueries=new PrisonerNativeQueries(sources.collectionProducer(),(ordinal,request,arguments)->admit(request));
        warFamily=new RootReadContractCatalog.Family<>("prisoners/war-retention12004",WarId.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of(WAR_CAPABILITY),sources.warProducer(),sources.warDecoder(),id->new RawJson(StrictJson.canonical(StrictJson.object().put("war_id",id.value()))),
                id->new OperationKey(PrisonerPlanningPorts.warStep(id.value())),this::warContract);
        queries=new PrisonerPlanningPorts.Queries(nativeQueries.contracts(),id->context.readCatalog().issue(warFamily,new WarId(id)));
        preparation=new PrisonerActionBinding12004(context.archive(),queries);
        configuration.definitions().attachCurrent(context,preparation,nativeQueries.contract(0));
        var ledgers=new PrisonerDomainBodyReader12004(slot -> context.borrowedSession().readDomain(slot),context.game().machineId());
        ordinary=new PrisonerPlanningPorts.Bindings(context.reads(),queries,Optional.of(catalog()),ledgers,preparation,
                (request,value)->new PrisonerPlanningPorts.RecordUnavailable("actual native succession producer/record port must be supplied by the sole M3 owner"));
        var originals=new PrisonerLegacyBinding12004(context.writer(),context.archive(),context.core().actions(),preparation);
        pending=new PrisonerPendingContributor12004(context,originals,configuration.definitions());
        List<RootReadContractCatalog.InstalledRead> reads=nativeQueries.contracts().stream()
                .map(read->new RootReadContractCatalog.InstalledRead(read,sources.collectionDecoder())).toList();
        var actions=new ArrayList<RootExecutableBindings.ActionBinding>();
        var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
        for(OperationKey operation:List.of(PrisonerOrdinaryPolicy12004.RELEASE,PrisonerOrdinaryPolicy12004.RANSOM)) {
            var binding=new NativeEffectRegistry.Binding(operation,sources.actionObserver(),preparation,
                    (command,attempt,dispatch)->observer().observe(command,attempt,dispatch));
            actions.add(new RootExecutableBindings.ActionBinding(binding,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.actionDecoder()));
            archived.add(NativePrisonerEffects12004.archivedVerifier(operation,sources.recordedVerifier(),context.frameLoader(),nativeQueries.contract(0),preparation));
        }
        var policySources=new OrdinaryPrisonerPolicies12004.Sources(sources.ordinaryPolicies(),sources.successionPolicies());
        var intent=new RootDomainIntentPreparation.Binding("prisoner-original-pending12004",sources.ledgerProducer(),
                command->command.operation().equals(PrisonerOrdinaryPolicy12004.RELEASE)||command.operation().equals(PrisonerOrdinaryPolicy12004.RANSOM),
                configuration.definitions()::prepare);
        installation=new RootDomainInstallation("prisoners12004",configuration.definitions().registrations(),reads,List.of(warFamily),actions,
                List.of(),archived,List.of(),List.of(),List.of(),List.of(intent),
                Set.of(PrisonerOrdinaryPolicy12004.RELEASE,PrisonerOrdinaryPolicy12004.RANSOM),
                OrdinaryPrisonerPolicies12004.prisoners(policySources,ordinary),List.of(),
                actions.stream().map(binding->new RootDomainInstallation.FixedDomain(binding,Domain.diplomacy)).toList(),List.of(),List.of());
    }
    public synchronized void bindKnown(KnownInteractionsRuntimeInstaller actualKnown)throws IOException {
        Objects.requireNonNull(actualKnown);StrictJson.require(boundKnown==null,"the actual Known products bind exactly once");
        actualKnown.requireContext(context);queries.bindTurnBundle(actualKnown.turnBundleFor(context));boundKnown=actualKnown;
    }
    public void requireContext(RootRuntimeContext actual){StrictJson.require(context==Objects.requireNonNull(actual),"prisoner products belong to another actual runtime context");}
    public synchronized void requireKnown(KnownInteractionsRuntimeInstaller actual) {
        StrictJson.require(boundKnown==Objects.requireNonNull(actual),"actual Known products are not the once-bound prisoner peer");queries.requireTurnBundleBound();
    }
    public RootDomainInstallation install() { queries.requireTurnBundleBound();return installation; }
    public PrisonerNativeQueries nativeQueries() { return nativeQueries; }
    /** The notification owner consumes this identical contract; it must not construct another ordinal-zero codec/catalog. */
    public ReadContract<RawJson> collectionContract() { return nativeQueries.contract(0); }
    public synchronized void retainPublicCollection(ReadContract<RawJson> contract,PlanningReadResult.Known<RawJson> actual) {
        Objects.requireNonNull(actual);StrictJson.require(nativeQueries.contracts().stream().anyMatch(value->value==contract)
                &&contract.hasPureReplay()&&contract.replay(actual.receipt()).equals(actual.value())
                &&actual.receipt().request().source().equals(context.source())
                &&actual.receipt().request().sessionId().equals(context.game().sessionId())
                &&actual.receipt().request().before().game().equals(context.game().generation()),"public collection must be the actual same-runtime query original");
        publicCollection=actual;
    }
    public synchronized RootApplicationSession.PublicActionDecision<RawJson> publicDecision(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,RawJson incoming,long target,
            OperationKey operation,java.time.Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);queries.requireTurnBundleBound();
        StrictJson.require(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())
                &&frame.identity().game().equals(context.game().generation()),"public prisoner action lost its actual current Root frame");
        var archive=context.archive().withSession(same);
        if(publicCommand==null)retainCanonicalPending(same,archive,frame,incoming,target,operation);
        if(publicCommand!=null){
            var prior=ContinuityActionJournal.lookup(same.head().state(),publicCommand.actionId(),archive);
            boolean sameInput=publicTarget==target&&publicCommand.operation().equals(operation)
                    &&StrictJson.parse(publicInput.bytes()).equals(StrictJson.parse(incoming.bytes()));
            if(prior.isPresent()){
                var original=prior.orElseThrow();StrictJson.require(original.command().equals(publicCommand),"public original command/body identity changed");
                if(original.state() instanceof ActionState.RejectedBeforeDispatch)configuration.definitions().resolveZeroBeforeDispatch(same,original);
                if(sameInput){
                    if(original.state() instanceof ActionState.RejectedBeforeDispatch)throw publicFailure("original prisoner request was rejected before dispatch; retain its zero-write proof and obtain a current collection");
                    if(original.state() instanceof ActionState.Settled)return new RootApplicationSession.RetainPublicResult<>(presentPublic(original,archive,same));
                    return new RootApplicationSession.ReconcilePublicAction<>(original.command().actionId(),archive.receiptReferenceOf(original));
                }
                if(!(original.state() instanceof ActionState.Settled)&&!(original.state() instanceof ActionState.RejectedBeforeDispatch))throw publicFailure("original prisoner submission is unresolved; do not resend");
            }
        }
        if(publicCollection==null)throw publicFailure("public submission lacks a complete current paused collection");
        var retained=publicCollection;NativeRecordedEvidenceVerifier.requireRead(retained.receipt(),archive);
        StrictJson.require(archive.loadRead(retained.originalReceipt()).equals(retained.receipt()),"public query original changed in the canonical archive");
        for(var guard:List.of(retained.receipt().before(),retained.receipt().after()))
            StrictJson.require(context.clock().instant().isBefore(guard.binding().validUntil()),"public prisoner collection lease expired");
        String actionId=ActionIds.forDecision(frame.sessionId(),frame.identity(),"public-prisoner:"+operation.value()+":"+target+":"+retained.originalReceipt().sha256()+":"+same.head().digest());
        var command=preparation.withArchive(archive).bindPublic(actionId,frame.identity(),frame.source(),frame.sessionId(),deadline,
                frame.semantic(),retained,incoming,target,operation);
        publicCommand=command;publicInput=incoming;publicTarget=target;
        return new RootApplicationSession.SubmitPublicAction<>(command);
    }
    /** Cold same-physical continuation reads the real domain and canonical journal; incoming JSON never mints an action identity. */
    private void retainCanonicalPending(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive archive,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,RawJson incoming,long target,OperationKey operation)throws IOException {
        var family=operation.equals(PrisonerOrdinaryPolicy12004.RELEASE)?PrisonerPlanningPorts.Family.RELEASE:PrisonerPlanningPorts.Family.RANSOM;
        var read=same.readDomain(PrisonerLegacyBinding12004.slot(family));
        if(!(read instanceof DomainBodies.Available actual))throw publicFailure("actual prisoner domain is unavailable; original pending cannot be replaced");
        var body=StrictJson.parse(actual.canonicalBody(),1_048_576);PrisonerLedgerReducer12004.validate(family,body);
        PrisonerEpisodeLedger12004.decode(family,new RawJson(actual.canonicalBody())).epoch().owner().require(frame.identity(),frame.source(),frame.sessionId());
        if(body.get("pending").isNull())return;
        var pending=PrisonerPendingIdentity12004.decode(family,new RawJson(StrictJson.canonical(body.get("pending"))));
        var matches=ContinuityActionJournal.receipts(same.head().state(),archive).stream().filter(receipt->pending.matches(receipt)
                &&PrisonerActionBinding12004.isPublic(receipt.command())&&receipt.command().operation().equals(operation)
                &&receipt.command().source().equals(context.source())&&receipt.command().sessionId().equals(context.game().sessionId())
                &&receipt.command().before().game().equals(context.game().generation())).toList();
        if(matches.size()!=1)throw publicFailure("original prisoner pending has no unique canonical public action; UNKNOWN retained");
        var original=matches.getFirst();PrisonerLegacyBinding12004.originalLineage(same.head(),archive,original);
        var selected=preparation.withArchive(archive).selected(original.command());
        if(pending.target()!=target||!StrictJson.parse(selected.normalized().bytes()).equals(StrictJson.parse(incoming.bytes())))
            throw publicFailure("original prisoner pending differs from this input; reconcile its original action without resending");
        publicCommand=original.command();publicInput=selected.normalized();publicTarget=target;
    }
    /** Presents only the exact canonical native queue ACK. Independent material settlement never changes this original public wire. */
    public RawJson presentPublic(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,ContinuityStorePort.Session same)throws IOException {
        context.writer().requireSession(same);var command=receipt.command();
        StrictJson.require(PrisonerActionBinding12004.isPublic(command)&&archive.loadReceipt(archive.receiptReferenceOf(receipt)).equals(receipt),"actual original public receipt required");
        var dispatch=ActionTransitions.dispatch(receipt.state());
        var failure=PrisonerPublicFailure12004.canonical(receipt,archive);
        if(failure.isPresent())throw failure.orElseThrow();
        var ack=(NativeActionPort.AckReceived)dispatch.orElseThrow();
        StrictJson.require(archive.load(archive.referenceOf(ack)).equals(ack),"actual public ACK original changed");
        var expected=StrictJson.object().put("step",command.operation().value()).put("accepted",true).put("status","submitted_verification_pending");
        if(ack.originalResultToken().isEmpty()||!StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()).equals(expected))throw PrisonerPublicFailure12004.malformedAcknowledgement(receipt,archive);
        var selected=preparation.withArchive(archive).selected(command);
        NativeRequestChronology.requireBeforeSubmission(selected.receipt(),ActionTransitions.attempt(receipt.state()).orElseThrow(),ack);
        return PrisonerPublicPendingCodec12004.fromAcknowledgement(command,ack,selected);
    }
    private static PublicServiceFailure publicFailure(String message){return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,message,Optional.empty());}
    public PrisonerPendingContributor12004 pendingContributor() { return pending; }
    public PrisonersRuntimeDefinitions definitions() { return configuration.definitions(); }
    public List<DomainBodies.BodyRef> initializeNext(ContinuityStorePort.Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        return configuration.definitions().initializeNext(same,proof);
    }
    /** Retained read-only release priority using the identical installed ordinary bindings; no succession record port is fabricated. */
    public boolean retainedReleaseReady(PlanningRequest request) {
        return new PrisonerCollector12004(ordinary).retainedReleaseReady(Objects.requireNonNull(request));
    }
    public PrisonerPlanningPorts.Bindings bindingsForSuccession(PrisonerPlanningPorts.SuccessionRecordPort actualM3Producer) {
        return new PrisonerPlanningPorts.Bindings(ordinary.reads(),ordinary.queries(),ordinary.catalog(),ordinary.ledgers(),ordinary.commands(),Objects.requireNonNull(actualM3Producer));
    }
    private synchronized NativePrisonerEffects12004 observer() {
        if(effects==null) {
            var snapshots=new NativeEffectSnapshots(context.adopted().observations(),context.archive(),context.frameLoader());
            effects=new NativePrisonerEffects12004(snapshots,context.reads(),nativeQueries.contract(0),preparation,context.archive());
        }
        return effects;
    }
    private void admit(PlanningReadRequest request) {
        try {
            context.requireCurrent(request.deadline());
            StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay && request.before().game().equals(context.game().generation())
                    && request.source().equals(context.source()) && request.sessionId().equals(context.game().sessionId())
                    && request.before().machineId().equals(context.game().machineId())
                    && request.source().exactBuild().equals("1.20.0.4@sha256:"+PrisonerVanillaResearch.EXE_SHA256),
                    "prisoner request must retain the actual source-qualified .4 Game/session");
            var borrowed=context.borrowedSession();context.writer().requireSession(borrowed);
        } catch(IOException failure) { throw new UncheckedIOException("actual original prisoner read scope unavailable",failure); }
    }
    private ReadContract<RawJson> warContract(WarId id) {
        OperationKey operation=new OperationKey(PrisonerPlanningPorts.warStep(id.value()));
        return new ReadContract<>("prisoners/war-retention12004/"+id.value(),operation,Optional.of(WAR_CAPABILITY),WAR_CAPABILITY,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,sources.warProducer(),
                request->{admit(request);StrictJson.require(request.arguments().members().isEmpty(),"fixed war route arguments required");
                    return new NativeRequest(operation.value(),Optional.of(WAR_CAPABILITY),new RawJson(StrictJson.canonical(StrictJson.object())));},
                receipt->{
                    StrictJson.require(receipt.original().nativeOk() && receipt.before().binding().observed().equals(receipt.request().before())
                            && receipt.after().binding().observed().equals(receipt.request().before())
                            && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"actual stable war proof read required");
                    RawJson original=receipt.original().originalResultToken().orElseThrow();var before=receipt.request().before();
                    PrisonerRansomFormalPolicy12004.readWar(original.bytes(),new PrisonerRansomFormalPolicy12004.Frame(before.frame().revision(),
                            before.frame().identity().nativeRevision(),before.frame().identity().dateRaw().intValueExact(),
                            before.frame().identity().player().longValueExact(),List.of(id.value())),id.value());
                    return original;
                });
    }
    private PrisonerVanillaResearch.Catalog catalog()throws IOException {
        var ref=sources.stockInteractions();var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        StrictJson.require(witness.source().bytes()==ref.bytes() && witness.source().sha256().equals(ref.sha256())
                && ref.bytes()==PrisonerVanillaResearch.STOCK_BYTES && ref.sha256().equals(PrisonerVanillaResearch.STOCK_SHA256),"actual pinned stock prison interaction source required");
        byte[] bytes=Files.readAllBytes(Path.of(ref.path()));SharedSourceFiles.assertUnchanged(witness);
        var source=new PrisonerVanillaResearch.Source(new G2Source(context.game().machineId(),context.clock().instant().toString(),"1.20.0.4",ref),PrisonerVanillaResearch.EXE_SHA256);
        return PrisonerVanillaResearch.inspect(bytes,source);
    }
    /** Supply these actual permissions to the managed transport before creating this per-Game installer. */
    public static List<NativePrivateActionPermission> privatePermissions(Sources sources,NativePrivateActionPermission.QualificationVerifier actualQualification) {
        Objects.requireNonNull(sources);Objects.requireNonNull(actualQualification);
        return List.of(new NativePrivateActionPermission(PrisonerOrdinaryPolicy12004.RELEASE,"allow_private_prisoner_ransom_action",sources.actionProducer(),
                request->validatePrimitive(request,true),actualQualification),
                new NativePrivateActionPermission(PrisonerOrdinaryPolicy12004.RANSOM,"allow_private_prisoner_ransom_action",sources.actionProducer(),
                        request->validatePrimitive(request,false),actualQualification));
    }
    private static void validatePrimitive(NativeRequest request,boolean release) {
        StrictJson.require(request.requiredCapability().isEmpty(),"private prisoner primitive cannot borrow an advertised capability");
        Set<String> keys=release?Set.of("prisoner_character_id","release_query_sequence","release_option_mask_bits")
                :Set.of("prisoner_character_id","payer_character_id","quote_query_sequence","quoted_gold_raw");
        JsonNode row=StrictJson.object(StrictJson.parse(request.additionalFields().bytes()),keys);
        StrictJson.integer(row.get("prisoner_character_id"),1,0xffff_fffeL);
        if(release) {
            StrictJson.integer(row.get("release_query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX);
            StrictJson.integer(row.get("release_option_mask_bits"),0,8191);
        } else {
            StrictJson.integer(row.get("payer_character_id"),1,0xffff_fffeL);
            StrictJson.integer(row.get("quote_query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX);
            StrictJson.integer(row.get("quoted_gold_raw"),1,Long.MAX_VALUE);
        }
    }
}

