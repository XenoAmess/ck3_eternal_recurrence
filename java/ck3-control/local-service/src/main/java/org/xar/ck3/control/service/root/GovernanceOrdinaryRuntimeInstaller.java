package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Concrete ordinary governance assembly; all native producers and finance services are the central installed instances. */
public final class GovernanceOrdinaryRuntimeInstaller {
    private GovernanceOrdinaryRuntimeInstaller() { }
    public record Sources(ExactRef governancePolicy,ExactRef feastPolicy,ExactRef feastEffects,ExactRef activityActionDecoder,
            List<ExactRef> openingProducers,List<ExactRef> cadenceProducers,ExactRef openingTransitions,FeastDomainRuntime.Sources feastState) {
        public Sources {
            for(ExactRef ref:List.of(governancePolicy,feastPolicy,feastEffects,activityActionDecoder))StrictJson.require(ref.bytes()>0,"actual ordinary governance source required");
            Objects.requireNonNull(openingTransitions);Objects.requireNonNull(feastState);openingProducers=List.copyOf(openingProducers);cadenceProducers=List.copyOf(cadenceProducers);
            StrictJson.require(!openingProducers.isEmpty() && !cadenceProducers.isEmpty(),"complete opening/cadence producer closures required");
        }
    }
    /** These are concrete registered producers, not clear-state defaults or an alternate pending implementation. */
    public record StateDomains(GovernanceStateSupplier.BodyContract<DomainState> council,
            GovernanceStateSupplier.BodyContract<DomainState> crown,CrownRetryPublication retryPublication,
            Supplier<Optional<CrownRetryPublication.ImportProof>> retainedRetryProof,RootGovernanceDomains civicDomains,CrownRetryDue retryDue) {
        public StateDomains {
            Objects.requireNonNull(council);Objects.requireNonNull(crown);Objects.requireNonNull(retryPublication);
            Objects.requireNonNull(retainedRetryProof);Objects.requireNonNull(civicDomains);Objects.requireNonNull(retryDue);
            StrictJson.require(council.slot()==DomainBodies.Slot.COUNCIL && crown.slot()==DomainBodies.Slot.CROWN
                   ,"actual registered Council/Crown bodies and concrete domain intent publishers required");
        }
    }
    public static Prepared prepare(Path originalWriterLock,Sources sources,Clock clock) {return new Prepared(originalWriterLock,sources,clock);}
    public static final class Prepared {
        @FunctionalInterface private interface CurrentInitial {void requireCurrent(ContinuityStorePort.Session same)throws IOException;}
        private record InitialCadence(ExactRef basis,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity observation,
                String episodeId,List<ExactRef> evidence) {
            private InitialCadence {evidence=List.copyOf(evidence);}
        }
        private final Path lock;
        private final Sources sources;
        private final Clock clock;
        private final GovernanceOpeningRuntime opening;
        private final FeastDomainRuntime feast;
        private final GovernanceCadenceActions cadenceActions;
        private final GovernanceCadencePublication cadence;
        private final DomainBodies.Registration cadenceRegistration;
        private RootApplicationAssembly.Core core;
        private Installed current;
        private Prepared(Path lock,Sources sources,Clock clock) {
            this.lock=Objects.requireNonNull(lock).toAbsolutePath().normalize();this.sources=Objects.requireNonNull(sources);this.clock=Objects.requireNonNull(clock);
            opening=new GovernanceOpeningRuntime(new GovernanceOpeningRuntime.Sources(sources.openingProducers()));feast=new FeastDomainRuntime(this.lock,sources.feastState());cadenceActions=new GovernanceCadenceActions(sources.cadenceProducers());
            cadence=new GovernanceCadencePublication(this.lock,this::requireSession,sources.cadenceProducers(),
                    (head,previous,plan,refs)->active().replay.replay(head,previous,plan,refs),
                    (id,body)->core().archive().preserveArtifact(session(),body,1_048_576));
            cadenceRegistration=new DomainBodies.Registration(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,1_048_576,sources.cadenceProducers(),new DomainBodies.Verifier() {
                @Override public String verify(ContinuityState ignored,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException {
                    throw new IOException("cadence publication requires the actual locked writer Head");
                }
                @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException {
                    var raw=StrictJson.parse(request.producerInput());
                    if(GovernanceNextInitialization.SCHEMA.equals(StrictJson.text(raw.get("schema"))))return active().nextInitialization.verify(head,previous,request,original);
                    if(GovernanceCadenceActions.INPUT.equals(StrictJson.text(raw.get("schema"))))return cadenceActions.verify(head,previous,request,original);
                    if(!"xar.java-cadence-initial-entry/v1".equals(StrictJson.text(raw.get("schema"))))return cadence.verify(head,previous,request,original);
                    var input=StrictJson.object(raw,Set.of("schema","episode_run_id","observation","entry_evidence","initial_basis"));
                    var initial=initialCadence(session(),ExactRef.fromJson(input.get("initial_basis")),head);
                    byte[] expected=CadenceJson.writeState(CadenceModels.State.empty(initial.episodeId()));
                    var generated=initialCadenceRequest(initial,request.originalBody());
                    StrictJson.require(previous.isEmpty() && head.digest().equals(session().head().digest())
                            && request.slot()==generated.slot() && request.contractSchema().equals(generated.contractSchema())
                            && request.evidence().equals(generated.evidence()) && request.evidenceId().equals(generated.evidenceId())
                            && Arrays.equals(request.producerInput(),generated.producerInput()) && Arrays.equals(original,expected),
                            "cadence initialization requires the exact actual fresh-entry producer");
                    return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest()).put("body",ActionCodec.sha256(expected))));
                }
            });
        }
        public List<DomainBodies.Registration> domainRegistrations() {return List.of(opening.registration(),cadenceRegistration,feast.registration());}
        public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            Objects.requireNonNull(actual);StrictJson.require(core==null && actual.configuration().ledger().lock().toAbsolutePath().normalize().equals(lock),
                    "ordinary governance binds the original Core/writer once");core=actual;opening.bind(actual);feast.bindCore(actual);cadenceActions.bindCore(actual);feast.bindCadenceActions(cadenceActions::publish);
        }
        private synchronized RootApplicationAssembly.Core core()throws IOException {if(core==null)throw new IOException("ordinary governance has not bound the actual Core");return core;}
        private void requireSession(ContinuityStorePort.Session borrowed)throws IOException {core().writer().requireSession(borrowed);borrowed.requireWriter(lock);}
        private ContinuityStorePort.Session session()throws IOException {var result=core().writer().borrowedSession();requireSession(result);return result;}
        private ContinuityStorePort.Session suppliedSession() {try{return session();}catch(IOException failure){throw new UncheckedIOException(failure);}}
        private synchronized Installed active()throws IOException {if(current==null)throw new IOException("ordinary governance has no actual active Game installation");return current;}
        public synchronized Installed install(RootRuntimeContext context,GovernanceRuntimeInstaller.Installed nativeGovernance,
                GovernanceActivityRuntime activity,ActivityActionRoutes activityActions,StateDomains domains,RootCrownRetryRuntime.Installed retry)throws IOException {
            StrictJson.require(context.core()==core(),"ordinary governance cannot adopt another Core/writer");
            StrictJson.require(current==null || current.context!=context,"ordinary governance installs once per actual Game");
            context.requireCurrent(clock.instant().plusSeconds(1));opening.installContext(context);feast.installContext(context);cadenceActions.installContext(context);var installed=new Installed(this,context,nativeGovernance,activity,activityActions,domains,Objects.requireNonNull(retry));current=installed;return installed;
        }
        public synchronized Installed installUnavailable(RootRuntimeContext context,GovernanceRuntimeInstaller.Prepared nativePrepared,
                GovernanceActivityRuntime activity,ActivityActionRoutes actions,StateDomains domains)throws IOException {
            StrictJson.require(!Objects.requireNonNull(nativePrepared).nativeQualified(),"unavailable ordinary governance requires its recognized unqualified Native source");
            nativePrepared.requireHistoryContext(context);
            StrictJson.require(context.core()==core(),"ordinary governance cannot adopt another Core/writer");
            StrictJson.require(current==null||current.context!=context,"ordinary governance installs once per actual Game");
            context.requireCurrent(clock.instant().plusSeconds(1));opening.installContext(context);feast.installContext(context);cadenceActions.installContext(context);
            var installed=new Installed(this,context,Optional.empty(),activity,actions,domains,Optional.empty(),nativePrepared.openingReadOnly(),Optional.of(nativePrepared.configuredBuildData()));current=installed;return installed;
        }
        public List<WriterContracts.Receipt> afterInitialEntry(ContinuityStorePort.Session borrowed,RootInitialEpisodeProof actual)throws IOException {
            requireSession(borrowed);actual.requireCurrent(borrowed);
            var openingReceipt=opening.initialize(borrowed,actual);var feastReceipt=feast.initialize(borrowed,actual);
            return List.of(openingReceipt,feastReceipt,initializeCadence(borrowed,actual.preserveOriginal(borrowed),actual::requireCurrent));
        }
        public List<WriterContracts.Receipt> afterInitialEntry(ContinuityStorePort.Session borrowed,FreshCampaignContext actual)throws IOException {
            requireSession(borrowed);StrictJson.require(actual.context()==active().context,"fresh ordinary governance belongs to another installed Game");actual.requireCurrent(borrowed);
            var openingBody=borrowed.readDomain(DomainBodies.Slot.OPENING_GATE);
            var feastBody=borrowed.readDomain(DomainBodies.Slot.FEAST);
            var cadenceBody=borrowed.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE);
            boolean missingOpening=openingBody instanceof DomainBodies.Unavailable unavailable && unavailable.reason()==DomainBodies.Reason.UNIMPORTED;
            boolean missingFeast=feastBody instanceof DomainBodies.Unavailable unavailable && unavailable.reason()==DomainBodies.Reason.UNIMPORTED;
            boolean missingCadence=cadenceBody instanceof DomainBodies.Unavailable unavailable && unavailable.reason()==DomainBodies.Reason.UNIMPORTED;
            StrictJson.require(missingOpening || openingBody instanceof DomainBodies.Available,"fresh opening may initialize only an unimported slot");
            StrictJson.require(missingFeast || feastBody instanceof DomainBodies.Available,"fresh Feast may initialize only an unimported slot");
            StrictJson.require(missingCadence || cadenceBody instanceof DomainBodies.Available,"fresh cadence may initialize only an unimported slot");
            if(openingBody instanceof DomainBodies.Available available)GovernanceOpeningDocument.decode(available.canonicalBody());
            if(feastBody instanceof DomainBodies.Available available)FeastDomainRuntime.decode(available.canonicalBody());
            if(cadenceBody instanceof DomainBodies.Available available)CadenceJson.readState(available.canonicalBody(),actual.episodeId());
            var receipts=new ArrayList<WriterContracts.Receipt>();
            if(missingOpening)receipts.add(opening.initialize(borrowed,actual));
            if(missingFeast)receipts.add(feast.initialize(borrowed,actual));
            if(missingCadence)receipts.add(initializeCadence(borrowed,actual.preserveOriginal(borrowed),actual::requireCurrent));
            return List.copyOf(receipts);
        }
        private WriterContracts.Receipt initializeCadence(ContinuityStorePort.Session borrowed,ExactRef basis,CurrentInitial actual)throws IOException {
            requireSession(borrowed);actual.requireCurrent(borrowed);
            var old=borrowed.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE);
            if(!(old instanceof DomainBodies.Unavailable unavailable) || unavailable.reason()!=DomainBodies.Reason.UNIMPORTED)
                throw new IOException("actual fresh cadence slot is not unimported; pending/restored cadence must be preserved");
            var initial=initialCadence(borrowed,basis,borrowed.head());
            byte[] body=CadenceJson.writeState(CadenceModels.State.empty(initial.episodeId()));var ref=core().archive().preserveArtifact(borrowed,body,1_048_576);
            var prepared=borrowed.previewImport(initialCadenceRequest(initial,ref));actual.requireCurrent(borrowed);var receipt=borrowed.commitImport(prepared);
            var read=borrowed.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE);
            StrictJson.require(receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE && read instanceof DomainBodies.Available known
                    && known.reference().payload().equals(ref) && Arrays.equals(known.canonicalBody(),body),"actual cadence fresh import/readback required");return receipt;
        }
        public FeastDomainRuntime feastDomain() {return feast;}
        /** The owning catalog calls only during its actual private restoration DOMAIN_IMPORT suffix. */
        public RestoredFeastOriginal captureRestoredFeastOriginal(ContinuityStorePort.Session same,
                RootRestorationOriginalProof.Original original)throws IOException {
            requireSession(same);var installed=active();installed.requireNativeAvailable();
            return RestoredFeastOriginal.capture(installed.context,same,original,feast,installed.finalSettlement);
        }
        /** Called only by Core after actual FIRST BASELINE or its privately qualified cold restoration. */
        public List<DomainBodies.BodyRef> initializeNext(RootRuntimeContext context,ContinuityStorePort.Session same,
                RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
            requireSession(same);var installed=active();installed.requireNativeAvailable();StrictJson.require(installed.context==Objects.requireNonNull(context),"NEXT governance must use the actual same installed context");
            return installed.nextInitialization.initializeNext(same,Objects.requireNonNull(proof));
        }
        public GovernanceCadenceActions.Publisher actionCadencePublisher() {return cadenceActions::publish;}
        public OpeningTransitions openingTransitions() throws IOException {return opening.transitions();}
        private InitialCadence initialCadence(ContinuityStorePort.Session same,ExactRef basis,WriterContracts.Head head)throws IOException {
            var context=active().context;
            if(FreshCampaignContext.isOriginal(context,same,basis)) {
                var actual=FreshCampaignContext.replayOriginal(context,same,basis);actual.requireInitializationPredecessor(same,head);
                return new InitialCadence(actual.basis(),actual.observation(),actual.episodeId(),actual.evidence());
            }
            var actual=RootInitialEpisodeProof.replayOriginal(context,same,basis);actual.requireInitializationPredecessor(same,head);
            return new InitialCadence(actual.basis(),actual.observation(),actual.episodeId(),actual.evidence());
        }
        private DomainBodies.ImportRequest initialCadenceRequest(InitialCadence actual,ExactRef body) {
            var row=StrictJson.object().put("schema","xar.java-cadence-initial-entry/v1").put("episode_run_id",actual.episodeId());
            row.set("observation",org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(actual.observation()));row.set("initial_basis",actual.basis().toJson());
            var refs=row.putArray("entry_evidence");actual.evidence().forEach(ref->refs.add(ref.toJson()));byte[] input=StrictJson.canonical(row);
            return new DomainBodies.ImportRequest(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,body,input,actual.evidence(),"cadence-initial-"+ActionCodec.sha256(input));
        }
    }
    static List<OrdinaryPolicy> ordinaryPolicies(GovernanceObservationSupplier observed,ExactRef source,
            GovernancePolicies.Council actualCouncil,OrdinaryFeastPolicy actualFeast) {
        return List.of(new GovernancePolicies.Opening(observed,source),new GovernancePolicies.Lifestyle(observed,source),
                Objects.requireNonNull(actualCouncil),new GovernancePolicies.Crown(observed,source),Objects.requireNonNull(actualFeast));
    }
    /** Keep an unavailable optional observer distinct from a completed review or technical read failure. */
    static OrdinaryPolicy selectedOptionalSource(OrdinaryPolicy original,GovernanceObservationSupplier observed,
            boolean privateSourceInstalled,Optional<OpeningReadProfile.Bindings> readonlyDefinitions) {
        Objects.requireNonNull(original);Objects.requireNonNull(observed);Objects.requireNonNull(readonlyDefinitions);
        if(privateSourceInstalled||readonlyDefinitions.isEmpty()
                ||original.stage()!=PlanningStage.COUNCIL&&original.stage()!=PlanningStage.CROWN_AUTHORITY)return original;
        var definitions=readonlyDefinitions.orElseThrow();
        var profile=OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,
                definitions.current().sourceRef()).orElseThrow();
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage(){return original.stage();}
            @Override public ExactRef implementationSource(){return original.implementationSource();}
            @Override public Decision evaluate(PlanningRequest request,Draft previous) {
                if(previous.command().filter(command->command.operation().value().equals("life-advance")).isEmpty()
                        ||!request.observations().paused()||!request.observations().mapReady()||request.observations().foregroundPresent())
                    return original.evaluate(request,previous);
                var read=observed.durable(request);
                if(!(read instanceof Known<Durable> known))return original.evaluate(request,previous);
                var durable=known.value();durable.bind(request);
                var domain=stage()==PlanningStage.COUNCIL?durable.council():durable.crown();
                if(durable.cadence().isEmpty()||domain.isEmpty()||domain.orElseThrow().status()!=DomainStatus.KNOWN_CLEAR
                        ||domain.orElseThrow().latest().isPresent()||domain.orElseThrow().legacyPending().isPresent())
                    return original.evaluate(request,previous);
                var kind=stage()==PlanningStage.COUNCIL?CadenceModels.Domain.COUNCIL:CadenceModels.Domain.CROWN;
                var frame=request.before().frame();
                if(org.xar.ck3.control.planning.optionalcadence.OptionalCheckCadence.deferred(durable.cadence().orElseThrow(),kind,
                        new CadenceModels.Frame(frame.episodeRunId(),frame.identity().dateRaw(),frame.identity().nativeRevision())).isPresent()
                        ||!actualReadonlyZeroProgress(profile,request,previous))return original.evaluate(request,previous);
                var detail=previous.detail().with(stage()==PlanningStage.COUNCIL?"council_selected_private_source":"crown_selected_private_source",
                        new OpportunityJson.Obj(java.util.Map.of("status",new OpportunityJson.Text("unavailable"),
                                "private_source_installed",new OpportunityJson.Bool(false),"query_performed",new OpportunityJson.Bool(false),
                                "review_complete",new OpportunityJson.Bool(false),"cadence_published",new OpportunityJson.Bool(false),
                                "action_authority",new OpportunityJson.Bool(false))));
                return new Replace(new Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),
                        previous.purpose(),previous.domain(),detail),"selected optional Java private source unavailable; retain the original plan without a completed review");
            }
        };
    }
    private static boolean actualReadonlyZeroProgress(OpeningReadProfile profile,PlanningRequest request,OrdinaryPolicy.Draft previous) {
        if(!(previous.detail().get("lifestyle_readonly_progress") instanceof OpportunityJson.Obj query))return false;
        var row=org.xar.ck3.control.application.driver.DriverJson.toNode(query);
        if(!row.path("opening_read_profile").asText().equals(OpeningReadProfile.Kind.CURRENT.profile())
                ||!row.path("status").asText().equals("available")||!row.hasNonNull("opening_native_current"))return false;
        try {
            var current=request.before().frame();var identity=current.identity();
            var expected=new OpeningReadProfile.Frame(identity.nativeRevision(),identity.dateRaw(),identity.player());
            var data=profile.decodeData(OpeningReadProfile.Kind.CURRENT,new RawJson(StrictJson.canonical(row.get("opening_native_current"))),expected);
            OpeningTransitions.requireReadOnlyExistingData(data,expected);
            var progress=data.progress().orElseThrow();
            if(progress.unspentPerkPoints().orElseThrow().signum()!=0)return false;
            var source=row.path("source_frame");var snapshot=row.path("snapshot");
            if(!source.path("snapshot_id").asText().equals(current.snapshotId())||!observedNumber(source,"revision",current.revision())
                    ||!observedNumber(source,"native_revision",identity.nativeRevision())||!observedNumber(source,"date_raw",identity.dateRaw())
                    ||!snapshot.path("snapshot_id").asText().equals(current.snapshotId())||!snapshot.path("episode_run_id").asText().equals(current.episodeRunId())
                    ||!observedNumber(snapshot,"public_revision",current.revision())||!observedNumber(snapshot,"native_revision",identity.nativeRevision())
                    ||!observedNumber(snapshot,"date_raw",identity.dateRaw())||!observedNumber(snapshot,"player_character_id",identity.player()))return false;
            var focus=snapshot.path("current_focus");var projected=snapshot.path("current_lifestyle_progress");var readiness=snapshot.path("readiness");
            return focus.path("presence").asText().equals("present")&&projected.path("presence").asText().equals("present")
                    &&focus.path("key").asText().equals(progress.focusKey().orElseThrow())&&focus.path("lifestyle_key").asText().equals(progress.lifestyleKey().orElseThrow())
                    &&projected.path("lifestyle_key").asText().equals(progress.lifestyleKey().orElseThrow())
                    &&observedNumber(projected,"xp_total_raw",progress.xpTotalRaw().orElseThrow())
                    &&observedNumber(projected,"xp_within_level_raw",progress.xpWithinLevelRaw().orElseThrow())
                    &&observedNumber(projected,"xp_per_level",progress.xpPerLevel().orElseThrow())
                    &&observedNumber(projected,"unspent_perk_points",progress.unspentPerkPoints().orElseThrow())
                    &&observedNumber(projected,"used_perk_points",progress.usedPerkPoints().orElseThrow())
                    &&readiness.path("same_frame_ready").equals(com.fasterxml.jackson.databind.node.BooleanNode.TRUE)
                    &&readiness.path("current_focus_ready").equals(com.fasterxml.jackson.databind.node.BooleanNode.TRUE)
                    &&readiness.path("lifestyle_progress_ready").equals(com.fasterxml.jackson.databind.node.BooleanNode.TRUE);
        }catch(IllegalArgumentException|java.util.NoSuchElementException invalid){return false;}
    }
    private static boolean observedNumber(com.fasterxml.jackson.databind.JsonNode row,String key,java.math.BigInteger expected) {
        var value=row.get(key);return value!=null&&value.isIntegralNumber()&&value.bigIntegerValue().equals(expected);
    }
    static GovernanceCollector unavailableCollector(PlanningReadPort reads,ActionPorts.OutcomeArchive archive,
            GovernanceCollector.StateSupplier states,GovernanceBorrowedSession scope) {
        return new GovernanceCollector(reads,archive,states,new GovernanceCollector.Reads(Optional.empty(),Optional.empty(),Optional.empty(),
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty()),scope);
    }
    public static final class Installed {
        private final Prepared prepared;private final RootRuntimeContext context;
        private final GovernanceActivityRuntime activity;private final GovernanceCadenceReplay replay;
        private final GovernanceCollector collector;private final FeastObservationCollector feastCollector;
        private final GovernancePolicies.Council council;private final RootDomainInstallation installation;
        private NativeFeastEffects feastEffects;
        private final FeastFinalSettlement finalSettlement;
        private final GovernanceNextInitialization nextInitialization;
        private final boolean nativeQualified;
        private Installed(Prepared prepared,RootRuntimeContext context,GovernanceRuntimeInstaller.Installed nativeGovernance,
                GovernanceActivityRuntime activity,ActivityActionRoutes activityActions,StateDomains domains,RootCrownRetryRuntime.Installed retry) {
            this(prepared,context,Optional.of(nativeGovernance),activity,activityActions,domains,Optional.of(retry),Optional.empty(),Optional.empty());
        }
        private Installed(Prepared prepared,RootRuntimeContext context,Optional<GovernanceRuntimeInstaller.Installed> nativeProducts,
                GovernanceActivityRuntime activity,ActivityActionRoutes activityActions,StateDomains domains,Optional<RootCrownRetryRuntime.Installed> retryProducts,
                Optional<GovernanceRuntimeInstaller.Prepared.OpeningReadOnly> openingReadOnly,Optional<GovernanceRuntimeInstaller.Config> unavailableConfiguration) {
            nativeQualified=nativeProducts.isPresent();StrictJson.require(nativeQualified==retryProducts.isPresent(),"Native governance and retry products must be available together");
            this.prepared=prepared;this.context=Objects.requireNonNull(context);this.activity=Objects.requireNonNull(activity);
            nextInitialization=new GovernanceNextInitialization(context,activity,prepared.feast,
                    prepared.opening.registration(),prepared.feast.registration(),prepared.cadenceRegistration);
            prepared.opening.bindNextVerifier(nextInitialization);prepared.feast.bindNextVerifier(nextInitialization);
            if(nativeQualified)try {prepared.opening.transitions().bindNative(nativeProducts.orElseThrow());} catch(IOException failure){throw new UncheckedIOException(failure);}
            Objects.requireNonNull(activityActions);Objects.requireNonNull(domains);retryProducts.ifPresent(retry->retry.requireStateDomains(domains));prepared.cadenceActions.bindCivicDomains(domains.civicDomains());finalSettlement=new FeastFinalSettlement(context,activity);prepared.feast.bindFinalSettlement(finalSettlement);
            var finance=context.finance();var scope=new GovernanceBorrowedSession(prepared::suppliedSession,prepared.lock,prepared::requireSession);
            replay=new GovernanceCadenceReplay(prepared::suppliedSession,prepared::requireSession,
                    (same,ref)->context.archive().readArtifact(same,ref,1_048_576));
            var openingInputs=prepared.opening.inputs();
            var states=new GovernanceStateSupplier(scope,Optional.of(GovernanceStateSupplier.cadence(prepared.sources.cadenceProducers())),
                    Optional.of(openingInputs.stateContract(context)),Optional.of(domains.council()),Optional.of(domains.crown()),
                    GovernanceStateSupplier.verifiedCrownRetryFrames(scope,domains.retryPublication(),domains.retainedRetryProof(),domains.retryDue()));
            GovernanceObservationSupplier actualGovernance;
            GovernanceObservationSupplier observed;
            if(nativeQualified){
                var nativeGovernance=nativeProducts.orElseThrow();var retry=retryProducts.orElseThrow();
                var definitions=nativeGovernance.planningReads();
            var reads=new GovernanceCollector.Reads(Optional.empty(),Optional.of(definitions.formal()),Optional.empty(),Optional.empty(),
                    Optional.of(definitions.crown()),Optional.empty(),Optional.empty());
            collector=new GovernanceCollector(context.reads(),context.archive(),states,reads,scope,nativeGovernance.lifestyleReads(),request->{
                try {
                    var same=prepared.session();requireCurrent(request.deadline());
                    var result=finance.definitions().read(same,FinanceReadContracts.Query.ROOT,finance.readPort(),request);
                    if(result instanceof PlanningReadResult.Unavailable<FinanceReadContracts.Packet> unavailable)return new Unavailable<>(unavailable.reason());
                    var known=(PlanningReadResult.Known<FinanceReadContracts.Packet>)result;
                    return new Known<>(known.value().result(),List.of(known.originalReceipt()));
                } catch(IOException failure) {return new Unavailable<>("actual shared finance ROOT read unavailable: "+failure.getMessage());}
            },retry.clockReads());
                actualGovernance=new GovernanceCouncilSupplier(collector,nativeGovernance.councilReads());
                observed=replay.observe(retry.observe(actualGovernance));
            }else{
                if(openingReadOnly.isPresent()) {
                    var actual=openingReadOnly.orElseThrow();
                    try{prepared.opening.transitions().bindReadOnlyOpening(actual.definitions());}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
                    var readonly=GovernancePlanningReads.OpeningReadProfile.readPort(actual.definitions(),context.reads(),context.archive(),scope,prepared.clock,this::requireCurrent);
                    collector=new GovernanceCollector(context.reads(),context.archive(),states,new GovernanceCollector.Reads(Optional.empty(),Optional.empty(),Optional.empty(),
                            Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty()),scope,readonly);
                }else collector=unavailableCollector(context.reads(),context.archive(),states,scope);
                actualGovernance=collector;observed=replay.observe(actualGovernance);
            }
            FeastObservationCollector.ActivityReads activityReads=nativeQualified?activity:
                    (query,request,arguments)->new Unavailable<>(GovernanceRuntimeInstaller.UNAVAILABLE_1210);
            feastCollector=new FeastObservationCollector(finance.collector(),actualGovernance,context.archive(),activityReads,scope);
            var observedFeast=replay.observe(feastCollector);
            var feast=new OrdinaryFeastPolicy(prepared.sources.feastPolicy(),observedFeast,(operation,request,arguments)->effects().expected(operation,request,arguments));
            prepared.feast.bindPolicy(feast);
            council=new GovernancePolicies.Council(observed,prepared.sources.governancePolicy());
            var selectedPolicies=ordinaryPolicies(observed,prepared.sources.governancePolicy(),council,feast);
            // Actual absent private products are distinct from the two installed readonly definitions.
            var readonlyDefinitions=openingReadOnly.map(GovernanceRuntimeInstaller.Prepared.OpeningReadOnly::definitions);
            List<OrdinaryPolicy> policies=selectedPolicies.stream()
                    .map(policy->selectedOptionalSource(policy,observed,nativeProducts.isPresent()||retryProducts.isPresent(),readonlyDefinitions))
                    .map(policy->unavailableConfiguration.map(config->RootUnmigratedGovernancePolicies.select(policy,observed,observedFeast,config,nativeProducts.isPresent()||retryProducts.isPresent(),openingReadOnly.isPresent())).orElse(policy))
                    .map(replay::record).toList();
            OrdinaryPlanCompletion completion=new GovernancePlanCompletion(prepared::suppliedSession,prepared::requireSession,prepared.cadence,replay);
            if(nativeQualified)completion=retryProducts.orElseThrow().completion(completion);
            List<RootExecutableBindings.ActionBinding> actions=(nativeQualified?OrdinaryFeastPolicy.OWNED:Set.<OperationKey>of()).stream().sorted(java.util.Comparator.comparing(OperationKey::value)).map(operation->
                    new RootExecutableBindings.ActionBinding(new NativeEffectRegistry.Binding(operation,prepared.sources.feastEffects(),activityActions,
                            (command,attempt,dispatch)->effects().observe(command,attempt,dispatch)),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                            Optional.empty(),prepared.sources.activityActionDecoder())).toList();
            var archived=(nativeQualified?OrdinaryFeastPolicy.OWNED:Set.<OperationKey>of()).stream().sorted(java.util.Comparator.comparing(OperationKey::value)).map(operation->
                    NativeFeastEffects.archivedVerifier(operation,prepared.sources.feastEffects(),context.frameLoader(),activity)).toList();
            var required=new java.util.HashSet<OperationKey>();if(nativeQualified){required.addAll(OrdinaryFeastPolicy.OWNED);required.add(GovernancePolicies.FOCUS);}
            final OpeningTransitions openingTransitions;try{openingTransitions=prepared.opening.transitions();}catch(IOException failure){throw new UncheckedIOException(failure);}
            var openingReads=openingReadOnly.stream().flatMap(actual->actual.definitions().all().stream()
                    .map(contract->new RootReadContractCatalog.InstalledRead(contract,actual.decoder()))).toList();
            installation=new RootDomainInstallation("ordinary-governance",prepared.domainRegistrations(),openingReads,List.of(),actions,List.of(),archived,
                    List.of(),List.of(),List.of(),nativeQualified?List.of(prepared.feast.pendingBinding(),openingTransitions.pendingBinding(prepared.sources.openingTransitions())):List.of(),Set.copyOf(required),policies,List.of(openingTransitions,prepared.feast,prepared.cadenceActions.lifestyleCompletion(),completion),
                    actions.stream().map(binding->new RootDomainInstallation.FixedDomain(binding,Domain.diplomacy)).toList(),List.of(),List.of());
        }
        private void requireCurrent(java.time.Instant deadline)throws IOException {StrictJson.require(prepared.active()==this,"ordinary governance belongs to a retired Game");context.requireCurrent(deadline);}
        public boolean nativeQualified(){return nativeQualified;}
        private void requireNativeAvailable()throws IOException {if(!nativeQualified)throw new IOException(GovernanceRuntimeInstaller.UNAVAILABLE_1210);}
        private synchronized NativeFeastEffects effects() {
            try {requireNativeAvailable();requireCurrent(prepared.clock.instant().plusSeconds(1));}catch(IOException failure){throw new UncheckedIOException(failure);}
            if(feastEffects==null)feastEffects=new NativeFeastEffects(new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader()),activity);return feastEffects;
        }
        public RootDomainInstallation installation() {return installation;}
        public OrdinaryCorePolicy.CoreProducer coreCouncil() {return council::evaluateCoreCouncil;}
        public RootPlanningInputsFactory.OpeningInputs openingInputs() {return prepared.opening.inputs();}
        public GovernanceCollector collector() {return collector;}
        public FeastObservationCollector feastCollector() {return feastCollector;}
        public Optional<OpeningTransitions.CheckpointRequired> requiresOpeningCheckpoint(ContinuityStorePort.Session same)throws IOException {return prepared.opening.transitions().requiresCheckpoint(same);}
        public GovernanceCadenceReplay cadenceReplay() {return replay;}
    }
}
