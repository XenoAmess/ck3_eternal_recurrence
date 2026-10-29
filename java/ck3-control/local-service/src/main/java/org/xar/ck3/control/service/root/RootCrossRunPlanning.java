package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain;
import org.xar.ck3.control.application.planning.campaign.CrossRunFirstCheckpointReader;
import org.xar.ck3.control.application.planning.campaign.CrossRunStrategySource;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain.*;

/** Core-owned actual cross-run producer. Initialization and scored-terminal publication use the original writer session. */
public final class RootCrossRunPlanning {
    private RootCrossRunPlanning() { }
    public enum ProducerRole {
        CORE_PRODUCER("RootCrossRunPlanning.java"), DOMAIN("CrossRunPlanningDomain.java"),
        STRATEGY_SOURCE("CrossRunStrategySource.java"), STRATEGY_REDUCER("CrossRunPlanning.java"),
        LIFECYCLE_REDUCER("LifecycleReducer.java"), TERMINAL_JOIN("TerminalLifecycleDecisionProducer.java");
        private final String fileName;
        ProducerRole(String fileName){this.fileName=fileName;}
        public String fileName(){return fileName;}
    }
    /** Configured original path and actual installed producer closure. This is data, never a restore or gameplay grant. */
    public record Sources(CheckpointFiles files,Path originalOneLifeHistory,Map<ProducerRole,ExactRef> roleProducers) {
        public Sources {
            Objects.requireNonNull(files);Objects.requireNonNull(originalOneLifeHistory);Objects.requireNonNull(roleProducers);
            StrictJson.require(originalOneLifeHistory.isAbsolute()&&originalOneLifeHistory.normalize().equals(originalOneLifeHistory),
                    "explicit absolute normalized original one-life history path required");
            StrictJson.require(originalOneLifeHistory.getFileName().toString().equals("one-life-history.json")
                    &&originalOneLifeHistory.getParent()!=null&&originalOneLifeHistory.getParent().getFileName().toString().equals("strategy"),
                    "original shared strategy/one-life-history.json path required");
            var roles=new EnumMap<ProducerRole,ExactRef>(ProducerRole.class);
            for(var entry:roleProducers.entrySet()){var role=entry.getKey();var ref=entry.getValue();
                Objects.requireNonNull(role);Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0,"actual installed cross-run source required");
                StrictJson.require(roles.put(role,ref)==null,"exact unique cross-run producer roles required");}
            StrictJson.require(roles.size()==ProducerRole.values().length,"complete cross-run producer closure required");
            roleProducers=Map.copyOf(roles);
        }
        public List<ExactRef> producers(){
            var seen=new java.util.HashSet<ExactRef>();var result=new ArrayList<ExactRef>();
            for(ProducerRole role:ProducerRole.values()){var ref=roleProducers.get(role);
                if(!seen.contains(ref)){seen.add(ref);result.add(ref);}}
            return List.copyOf(result);
        }
        public Sources(CheckpointFiles files,Path originalOneLifeHistory,List<ExactRef> producers){
            this(files,originalOneLifeHistory,legacyRoleMap(producers));
        }
        private static Map<ProducerRole,ExactRef> legacyRoleMap(List<ExactRef> producers){
            var roles=new EnumMap<ProducerRole,ExactRef>(ProducerRole.class);
            for(ExactRef ref:producers){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0,"actual installed cross-run source required");
                ProducerRole role=null;for(ProducerRole candidate:ProducerRole.values())if(Path.of(ref.path()).getFileName().toString().equals(candidate.fileName()))role=candidate;
                StrictJson.require(role!=null&&roles.put(role,ref)==null,"exact unique cross-run producer roles required");}
            StrictJson.require(roles.size()==ProducerRole.values().length,"complete cross-run producer closure required");
            return Map.copyOf(roles);
        }
    }
    /** Construct before Core.open; bind the actual Core once after its writer is created. No caller-supplied capture lambda. */
    public static final class Prepared {
        private final Sources sources;
        private final CrossRunPlanningDomain domain;
        private final List<DomainBodies.Registration> registrations;
        private final Map<SessionIdentity,RootRuntimeContext> contexts=new LinkedHashMap<>();
        private final Map<SessionIdentity,Installed> installed=new LinkedHashMap<>();
        private final Map<ExactRef,LiveInitialization> initializations=new LinkedHashMap<>();
        private RootApplicationAssembly.Core core;
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);domain=new CrossRunPlanningDomain(
                ()->requireCore().writer().borrowedSession(),this::capture);
            registrations=List.of(domain.registration(sources.producers()));}
        public CrossRunPlanningDomain domain(){return domain;}
        public List<DomainBodies.Registration> registrations(){return registrations;}
        public synchronized void bindCore(RootApplicationAssembly.Core actual){Objects.requireNonNull(actual);StrictJson.require(core==null||core==actual,"cross-run producer cannot move to another Core/writer");core=actual;}
        private synchronized RootApplicationAssembly.Core requireCore(){return Objects.requireNonNull(core,"cross-run producer must bind the actual Core");}
        /** Retains the same per-Game object for exact routing; every operation separately validates its actual authority. */
        public synchronized void attachContext(RootRuntimeContext context){Objects.requireNonNull(context);StrictJson.require(context.core()==requireCore(),"cross-run context belongs to another Core");SessionIdentity key=identity(context);RootRuntimeContext old=contexts.putIfAbsent(key,context);StrictJson.require(old==null||old==context,"duplicate physical Game context");}
        public synchronized Installed install(RootRuntimeContext context,RootLifecycleAuthority terminal,LifecycleComposites lifecycle,
                TerminalLifecycleDecisionProducer decisions){attachContext(context);Objects.requireNonNull(terminal);Objects.requireNonNull(lifecycle);Objects.requireNonNull(decisions);SessionIdentity key=identity(context);Installed old=installed.get(key);if(old!=null){StrictJson.require(old.terminal==terminal&&old.lifecycle==lifecycle&&old.decisions==decisions,"cross-run terminal producer cannot replace the original actual instances");return old;}var value=new Installed(this,context,terminal,lifecycle,decisions);installed.put(key,value);return value;}
        /** Consume only Core's sealed actual NEXT or restored-FIRST initialization branch. Saved originals are never current facts. */
        public CrossRunFirstCheckpointReader.Saved requireEpisodeFirst(RootRuntimeContext context,ContinuityStorePort.Session same,
                RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
            Objects.requireNonNull(proof);
            if(proof instanceof RootApplicationAssembly.NextEpisodeDomainProof next)return requireNextFirst(context,same,next);
            StrictJson.require(proof instanceof RootApplicationAssembly.RestoredFirstEpisodeDomainProof,
                    "actual private NEXT or restored-FIRST Core initialization proof required");
            attachContext(context);context.writer().requireSession(same);String head=same.head().digest();proof.requireCurrent(same,context);
            var material=proof.baselineMaterial();
            StrictJson.require(proof.kind()==RootApplicationAssembly.EpisodeDomainInitializationProof.Kind.RESTORED_FIRST
                    &&proof.lifecycleProof() instanceof org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.NextEpisode
                    &&material.sourceSemantic().equals(proof.savedSemantic())
                    &&java.util.Arrays.equals(material.savedDriver().encode(),proof.firstSavedDriver().encode())
                    &&material.session().game().equals(proof.savedSemantic().frame().game())
                    &&proof.afterSession().game().equals(proof.currentSemantic().frame().game())
                    &&!material.session().game().equals(proof.afterSession().game()),
                    "restored-FIRST CrossRun comparison crossed its historical saved material and actual replacement owner");
            context.semanticVerifier().verify(same,proof.afterSession(),proof.currentSemantic());
            StrictJson.require(java.util.Arrays.equals(proof.currentDriver().encode(),context.archive().readArtifact(same,
                    proof.currentSemantic().originalDriver(),org.xar.ck3.control.application.readiness.ReadinessArchive.Role.DRIVER.maximumBytes())),
                    "restored-FIRST current full Driver differs from its actual replacement SEM");
            var saved=CrossRunFirstCheckpointReader.compareRestored(same,material,proof.currentSemantic(),context.archive());
            CrossRunFirstCheckpointReader.requireNextPlan(proof.predecessorDriver(),proof.lifecycleProof().encodedResult(),saved.state());
            StrictJson.require(saved.body().equals(proof.oldDomain(DomainBodies.Slot.CROSS_RUN_PLANNING)),
                    "restored-FIRST CrossRun body is not its private original NEXT/BASELINE domain");
            requireSameCanonical(same,saved);proof.requireCurrent(same,context);
            StrictJson.require(head.equals(same.head().digest()),"restored-FIRST CrossRun initialization comparison changed canonical history");
            return saved;
        }
        /** Actual Core FIRST/M7 originals, after domain initialization and before any cycle rebind or Host publication. */
        public CrossRunFirstCheckpointReader.Saved requireNextFirst(RootRuntimeContext context,ContinuityStorePort.Session same,
                RootApplicationAssembly.NextEpisodeDomainProof proof)throws IOException {
            attachContext(context);context.writer().requireSession(same);Objects.requireNonNull(proof);String head=same.head().digest();
            proof.requireCurrent(same,context);var binding=proof.baseline();binding.requireCurrent(same);
            var material=proof.baselineMaterial();
            StrictJson.require(binding.beforeOwner().equals(proof.beforeSession())&&binding.afterOwner().equals(proof.afterSession())
                    &&material.session().equals(proof.afterSession())&&material.pair().equals(binding.firstCheckpoint().pair())
                    &&material.checkpointDigest().equals(binding.firstCheckpoint().digest())&&material.baseline().equals(binding.baseline())
                    &&material.sourceSemantic().equals(binding.semantic())&&material.sourceSemantic().equals(proof.savedSemantic())
                    &&java.util.Arrays.equals(material.savedDriver().encode(),binding.driver().encode())
                    &&java.util.Arrays.equals(material.savedDriver().encode(),proof.firstSavedDriver().encode()),
                    "CrossRun FIRST reader crossed the actual Core/M7 BASELINE, pair, saved Driver or SEM");
            var saved=CrossRunFirstCheckpointReader.read(same,material,context.archive());
            CrossRunFirstCheckpointReader.requireNextPlan(binding.predecessorDriver(),binding.proof().encodedResult(),saved.state());
            var result=org.xar.ck3.control.application.driver.DriverJson.object(binding.proof().encodedResult(),
                    org.xar.ck3.control.application.lifecycle.LifecycleProofCodec.MAX_RESULT_BYTES);
            StrictJson.require(new OpportunityJson.Text(material.savedDriver().session().episodeRunId()).equals(result.get("episode_run_id")),
                    "FIRST strategy plan belongs to another actual new episode");
            requireSameCanonical(same,saved);binding.requireCurrent(same);proof.requireCurrent(same,context);
            StrictJson.require(head.equals(same.head().digest()),"CrossRun FIRST/M7 comparison changed the canonical head");return saved;
        }
        /** The actual private restore original selects FIRST. Ordinary saved-cycle material stays in its existing branch. */
        public Optional<CrossRunFirstCheckpointReader.Saved> requireRestoredFirst(RootRuntimeContext context,
                ContinuityStorePort.Session same)throws IOException {
            attachContext(context);context.writer().requireSession(same);String head=same.head().digest();
            var actual=context.restorationOriginal(same);
            if(actual.material().kind()!=org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial.Kind.FIRST_BASELINE)
                return Optional.empty();
            StrictJson.require(actual.material() instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial,
                    "restored FIRST CrossRun comparison requires the actual private baselined material");
            var material=(SavedFirstCheckpointMaterialStore.BaselinedMaterial)actual.material();
            context.semanticVerifier().verify(same,identity(context),actual.semantic());
            var saved=CrossRunFirstCheckpointReader.compareRestored(same,material,actual.semantic(),context.archive());
            requireSameCanonical(same,saved);var retained=context.restorationOriginal(same);
            StrictJson.require(actual.basis().equals(retained.basis())&&material.witness().equals(retained.material().witness())
                    &&head.equals(same.head().digest()),"restored FIRST CrossRun original/ancestry changed during comparison");
            return Optional.of(saved);
        }
        private void requireSameCanonical(ContinuityStorePort.Session same,CrossRunFirstCheckpointReader.Saved saved)throws IOException {
            StateRead read=domain.read(same);
            StrictJson.require(read instanceof KnownState,"actual complete CrossRun domain is unavailable at FIRST comparison");
            KnownState actual=(KnownState)read;
            StrictJson.require(actual.body().equals(saved.body())&&actual.state().equals(saved.state()),
                    "current canonical CrossRun body differs from the exact original FIRST strategy; no reset/import is permitted");
        }
        /** Existing canonical state survives. Only a private actual initial entry can initialize an unimported slot. */
        public KnownState initializeFresh(RootRuntimeContext context,ContinuityStorePort.Session same,RootInitialEpisodeProof proof)throws IOException {
            attachContext(context);Objects.requireNonNull(proof);context.writer().requireSession(same);proof.requireCurrent(same);proof.requireInitializationPredecessor(same,same.head());
            StateRead existing=domain.read(same);if(existing instanceof KnownState known)return known;
            StrictJson.require(((MissingState)existing).original().reason()==DomainBodies.Reason.UNIMPORTED,
                    "unavailable/corrupt cross-run state is not an unimported initial slot");
            ExactRef basis=proof.preserveOriginal(same);var original=RootInitialEpisodeProof.replayOriginal(context,same,basis);original.requireInitializationPredecessor(same,same.head());
            Optional<FileWitness> file=sources.files().observe(sources.originalOneLifeHistory());CrossRunPlanning.State state=originalState(file);
            ExactRef previous=preserve(context,same,CrossRunPlanning.encodeState(state));Instant at=context.clock().instant();
            var origin=new EntryOrigin(original.observation(),original.source(),basis,sources.originalOneLifeHistory(),file);
            Input input=new Input("cross-run-initial:"+basis.sha256(),origin,previous,at);
            var live=new LegacyInitialization(context,proof);synchronized(this){StrictJson.require(initializations.putIfAbsent(basis,live)==null,"initial cross-run import is already in progress");}
            try{return publish(context,same,new Initialized(input,new StateDocument(previous,CrossRunPlanning.encodeState(state))));}
            finally{synchronized(this){StrictJson.require(initializations.remove(basis)==live,"initial cross-run proof scope changed");}}
        }
        /** Preserves the actual original strategy using fresh observed campaign DATA, without a legacy entry. */
        public KnownState initializeFresh(RootRuntimeContext context,ContinuityStorePort.Session same,FreshCampaignContext fresh)throws IOException {
            attachContext(context);Objects.requireNonNull(fresh);context.writer().requireSession(same);
            StrictJson.require(fresh.context()==context,"fresh campaign cross-run input crossed its actual context");
            fresh.requireCurrent(same);fresh.requireInitializationPredecessor(same,same.head());
            StateRead existing=domain.read(same);if(existing instanceof KnownState known)return known;
            StrictJson.require(((MissingState)existing).original().reason()==DomainBodies.Reason.UNIMPORTED,
                    "unavailable/corrupt cross-run state is not an unimported fresh campaign slot");
            ExactRef basis=fresh.preserveOriginal(same);var original=FreshCampaignContext.replayOriginal(context,same,basis);
            original.requireInitializationPredecessor(same,same.head());
            Optional<FileWitness> file=sources.files().observe(sources.originalOneLifeHistory());CrossRunPlanning.State state=originalState(file);
            ExactRef previous=preserve(context,same,CrossRunPlanning.encodeState(state));Instant at=context.clock().instant();
            var origin=new EntryOrigin(original.observation(),original.source(),basis,sources.originalOneLifeHistory(),file);
            Input input=new Input("cross-run-fresh-campaign:"+basis.sha256(),origin,previous,at);
            var live=new CampaignInitialization(context,fresh);synchronized(this){StrictJson.require(initializations.putIfAbsent(basis,live)==null,"fresh campaign cross-run import is already in progress");}
            try{return publish(context,same,new Initialized(input,new StateDocument(previous,CrossRunPlanning.encodeState(state))));}
            finally{synchronized(this){StrictJson.require(initializations.remove(basis)==live,"fresh campaign cross-run input scope changed");}}
        }
        private CrossRunPlanning.State originalState(Optional<FileWitness> expected)throws IOException {
            Optional<FileWitness> actual=sources.files().observe(sources.originalOneLifeHistory());
            StrictJson.require(actual.equals(expected),"original strategy path identity/absence changed");
            if(actual.isEmpty())return CrossRunPlanning.empty();
            FileWitness witness=actual.orElseThrow();byte[] bytes=sources.files().read(witness,CrossRunPlanning.MAX_BYTES);
            CrossRunPlanning.State state=CrossRunStrategySource.decode(bytes).state();sources.files().verify(witness);return state;
        }
        private Captured capture(ContinuityStorePort.Session same,WriterContracts.Head actualHead,Input input)throws IOException {
            requireCore().writer().requireSession(same);
            if(input.origin() instanceof EntryOrigin entry){LiveInitialization live;synchronized(this){live=initializations.get(entry.entryBasis());}
                if(live==null)throw new IOException("private actual initial-entry capture scope is unavailable");
                RootRuntimeContext context=live.context();live.requireCurrent(same,actualHead);live.verifyOriginal(same,actualHead,entry);
                StrictJson.require(entry.originalStrategy().equals(sources.originalOneLifeHistory()),"initial strategy source crossed the actual initial campaign/configuration");
                CrossRunPlanning.State state=originalState(entry.sourceFile());byte[] raw=context.archive().readArtifact(same,input.previousState(),CrossRunPlanning.MAX_BYTES);
                var previous=new StateDocument(input.previousState(),raw);StrictJson.require(previous.state().equals(state),"candidate prior state differs from actual original strategy source");
                return new Initialized(input,previous);
            }
            TerminalOrigin origin=(TerminalOrigin)input.origin();Installed owner=requireInstalled(origin.identity());
            return owner.capture(same,input);
        }
        private synchronized Installed requireInstalled(LifecycleIdentity identity)throws IOException {
            SessionIdentity key=new SessionIdentity(identity.machineId(),identity.game(),identity.sessionId());Installed value=installed.get(key);
            if(value==null)throw new IOException("actual per-Game cross-run terminal producer is not installed");
            StrictJson.require(requireCore().sessionAccess().current().identity().equals(key),"cross-run capture crossed the actual committed Root Game");return value;
        }
        private KnownState publish(RootRuntimeContext context,ContinuityStorePort.Session same,Captured capture)throws IOException {
            context.writer().requireSession(same);
            if(capture.input().origin() instanceof EntryOrigin entry){LiveInitialization live;synchronized(this){live=initializations.get(entry.entryBasis());}
                if(live==null)throw new IOException("actual initial Driver publication scope is unavailable");
                live.requireOutsideObservationScope(same);
            }else context.adopted().authority().requireOutsideObservationScope(same);
            CrossRunPlanning.State expected=CrossRunPlanningDomain.produce(capture);
            ExactRef candidate=preserve(context,same,CrossRunPlanning.encodeState(expected));Input input=capture.input();
            var request=new DomainBodies.ImportRequest(DomainBodies.Slot.CROSS_RUN_PLANNING,CrossRunPlanningDomain.CONTRACT_SCHEMA,candidate,
                    CrossRunPlanningDomain.encodeInput(input),input.evidence(),input.evidenceId());
            var prepared=same.previewImport(request);same.commitImport(prepared);
            StateRead after=domain.read(same);StrictJson.require(after instanceof KnownState,"actual cross-run import did not produce readable canonical state");
            KnownState known=(KnownState)after;StrictJson.require(known.state().equals(expected),"actual cross-run post-state differs from produced state");return known;
        }
        private static ExactRef preserve(RootRuntimeContext context,ContinuityStorePort.Session same,byte[] raw)throws IOException {
            return context.archive().preserveArtifact(same,raw,CrossRunPlanning.MAX_BYTES);
        }
    }
    private sealed interface LiveInitialization permits LegacyInitialization,CampaignInitialization {
        RootRuntimeContext context();
        void requireCurrent(ContinuityStorePort.Session same,WriterContracts.Head head)throws IOException;
        void verifyOriginal(ContinuityStorePort.Session same,WriterContracts.Head head,EntryOrigin entry)throws IOException;
        void requireOutsideObservationScope(ContinuityStorePort.Session same)throws IOException;
    }
    private record LegacyInitialization(RootRuntimeContext context,RootInitialEpisodeProof proof) implements LiveInitialization {
        @Override public void requireCurrent(ContinuityStorePort.Session same,WriterContracts.Head head)throws IOException {
            proof.requireCurrent(same);proof.requireInitializationPredecessor(same,head);
        }
        @Override public void verifyOriginal(ContinuityStorePort.Session same,WriterContracts.Head head,EntryOrigin entry)throws IOException {
            var original=RootInitialEpisodeProof.replayOriginal(context,same,entry.entryBasis());original.requireInitializationPredecessor(same,head);
            StrictJson.require(original.observation().equals(entry.frame())&&original.source().equals(entry.source()),"original cross-run entry input changed");
        }
        @Override public void requireOutsideObservationScope(ContinuityStorePort.Session same)throws IOException {
            proof.adopted().authority().requireOutsideObservationScope(same);
        }
    }
    private record CampaignInitialization(RootRuntimeContext context,FreshCampaignContext fresh) implements LiveInitialization {
        @Override public void requireCurrent(ContinuityStorePort.Session same,WriterContracts.Head head)throws IOException {
            fresh.requireCurrent(same);fresh.requireInitializationPredecessor(same,head);
        }
        @Override public void verifyOriginal(ContinuityStorePort.Session same,WriterContracts.Head head,EntryOrigin entry)throws IOException {
            var original=FreshCampaignContext.replayOriginal(context,same,entry.entryBasis());original.requireInitializationPredecessor(same,head);
            StrictJson.require(entry.entryBasis().equals(fresh.preserveOriginal(same))&&original.observation().equals(entry.frame())
                    &&original.source().equals(entry.source())&&original.observation().equals(fresh.currentObservation())
                    &&original.firstDriver().equals(fresh.adopted().seed().fullDriver()),"fresh campaign cross-run DATA owner changed");
        }
        @Override public void requireOutsideObservationScope(ContinuityStorePort.Session same)throws IOException {
            fresh.adopted().authority().requireOutsideObservationScope(same);
        }
    }
    /** The original actual lifecycle decision join owns terminal qualification. This service only publishes its already-produced strategy. */
    public static final class Installed {
        private final Prepared owner;private final RootRuntimeContext context;private final RootLifecycleAuthority terminal;
        private final LifecycleComposites lifecycle;private final TerminalLifecycleDecisionProducer decisions;
        private final Map<String,Instant> publicationDeadlines=new LinkedHashMap<>();
        private Installed(Prepared owner,RootRuntimeContext context,RootLifecycleAuthority terminal,LifecycleComposites lifecycle,TerminalLifecycleDecisionProducer decisions){this.owner=owner;this.context=context;this.terminal=terminal;this.lifecycle=lifecycle;this.decisions=decisions;}
        public StateRead read(ContinuityStorePort.Session same)throws IOException {context.writer().requireSession(same);return owner.domain.read(same);}
        /** Call after canonical DEATH settlement, before next episode. Missing/unavailable score is not an empty or completed life. */
        public KnownState recordScored(ContinuityStorePort.Session same,LifecycleIdentity expected,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.adopted().authority().requireOutsideObservationScope(same);
            context.requireCurrent(deadline);owner.requireInstalled(expected);
            KnownState before=known(same);Recorded captured=terminal.current(same,expected,deadline,lease->captureActual(same,lease,before,deadline,Optional.empty()));
            // The observation-only lifecycle lease has ended before the domain head changes.
            if(before.state().equals(CrossRunPlanningDomain.produce(captured)))return before;
            String id=captured.input().evidenceId();synchronized(this){StrictJson.require(publicationDeadlines.putIfAbsent(id,deadline)==null,"terminal cross-run publication is already in progress");}
            try{return owner.publish(context,same,captured);}
            finally{synchronized(this){StrictJson.require(publicationDeadlines.remove(id).equals(deadline),"terminal publication deadline scope changed");}}
        }
        private Recorded capture(ContinuityStorePort.Session same,Input input)throws IOException {
            TerminalOrigin origin=(TerminalOrigin)input.origin();KnownState before=known(same);
            StrictJson.require(before.body().payload().equals(input.previousState()),"terminal publication lost the actual canonical prior strategy");
            Instant deadline;synchronized(this){deadline=publicationDeadlines.get(input.evidenceId());}
            if(deadline==null)throw new IOException("actual canonical terminal publication scope is unavailable");context.requireCurrent(deadline);
            return terminal.current(same,origin.identity(),deadline,lease->captureActual(same,lease,before,deadline,Optional.of(input)));
        }
        private Recorded captureActual(ContinuityStorePort.Session same,RootLifecycleAuthority.Lease lease,KnownState previous,Instant deadline,Optional<Input> requested)throws IOException {
            lease.assertCurrent(same);var joined=decisions.canonicalTerminal(same,lease,deadline)
                    .orElseThrow(()->new IOException("actual canonical scored terminal is unavailable; cross-run state is unchanged"));
            ActionReceipt receipt=joined.actualReceipt();OpportunityJson.Obj result=joined.resultObj();
            StrictJson.require(receipt.command().origin() instanceof CommandOrigin.LifecycleTerminal origin&&origin.identity().sameSession(lease.identity()),
                    "actual terminal receipt crossed lifecycle subject/session");
            var driver=DriverStateSnapshot.decodeComplete(context.archive().readArtifact(same,joined.driverBeforeExactRef(),org.xar.ck3.control.application.readiness.ReadinessArchive.Role.DRIVER.maximumBytes()));
            StrictJson.require(driver.session().episodeRunId().equals(lease.identity().subject().episodeRunId())
                    &&driver.session().actorId().equals(lease.identity().subject().characterId()),"actual terminal original history belongs to another life");
            var history=new ArrayList<OpportunityJson.Obj>();for(var row:driver.commandHistory())history.add(
                    org.xar.ck3.control.application.driver.DriverJson.object(row.originalRow().json(),
                            org.xar.ck3.control.application.lifecycle.LifecycleProofCodec.MAX_RESULT_BYTES));
            Instant produced=Instant.parse(OpportunityJson.text(result.get("observed_at"),"actual terminal observed_at"));
            var actualStrategy=CrossRunStrategySource.decode(OpportunityJson.object(
                    lease.snapshot().facts().auxiliary().get("one_life_strategy"),"actual current Driver strategy"));
            StrictJson.require(actualStrategy.state().equals(CrossRunStrategySource.terminal(previous.state(),
                    lease.identity().subject().episodeRunId(),history,result,produced)),
                    "canonical terminal publication differs from the actual current Driver strategy/history");
            ExactRef receiptRef=context.archive().withSession(same).receiptReferenceOf(receipt);
            var refs=new TerminalReferences(receiptRef,joined.terminalRowExactRef(),joined.driverBeforeExactRef(),lease.identity().nativeEvidence(),lease.identity().evidence().originalDriver());
            Input actual=new Input("cross-run-terminal:"+receipt.command().actionId(),new TerminalOrigin(lease.identity(),context.source(),receipt.command().actionId(),refs),previous.body().payload(),produced);
            for(ExactRef ref:joined.evidenceList()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
            if(requested.isPresent()){Input input=requested.orElseThrow();TerminalOrigin source=(TerminalOrigin)input.origin();
                StrictJson.require(source.identity().sameGuardFrame(lease.identity())&&source.source().equals(context.source())
                        &&source.actionId().equals(receipt.command().actionId())&&source.references().equals(refs)&&input.producedAt().equals(produced),
                        "actual terminal input differs from canonical receipt/result/history/native originals");actual=input;}
            byte[] originalPrevious=context.archive().readArtifact(same,previous.body().payload(),CrossRunPlanning.MAX_BYTES);
            return new Recorded(actual,new StateDocument(previous.body().payload(),originalPrevious),List.copyOf(history),result);
        }
        private KnownState known(ContinuityStorePort.Session same)throws IOException {
            StateRead read=owner.domain.read(same);if(read instanceof KnownState known)return known;
            throw new IOException("cross-run state is unimported; absence cannot initialize a terminal or invent prior lives");
        }
    }
    private static SessionIdentity identity(RootRuntimeContext context){return new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());}
}
