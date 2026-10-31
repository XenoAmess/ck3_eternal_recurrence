package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** The actual operator source shares the original coordinator, writer, physical Game and sole Driver CAS. */
public final class RootOperatorCharacterAuthority {
    private static final String NO_CHANGE_SCHEMA="xar.java.operator-no-change-original/v1";
    private RootOperatorCharacterAuthority(){ }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {
        return new Prepared(inputs,selected);
    }
    public static Prepared prepareOrdinary(ExactRef actualNativeDefinition,RootAdditionalDomains.ImplementationMetadata metadata)throws IOException {
        return new Prepared(actualNativeDefinition,metadata);
    }
    public static final class Prepared implements RootSetPlayedCharacterRuntime.SourceFactory,
            WriterContracts.TransitionAuthority,OrdinaryCycleTransitions.OperatorAuthority {
        private final Optional<HistoricalSources> history;
        private final List<ExactRef> sources;
        private final ExactRef definition,decoder,implementation;
        private final IdentityHashMap<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        private final ThreadLocal<Execution> active=new ThreadLocal<>();
        private RootApplicationAssembly.Core core;
        private Prepared(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {
            this.history=Optional.of(new HistoricalSources(Objects.requireNonNull(inputs),Objects.requireNonNull(selected)));
            selected.requireInputs(inputs);
            var closure=new ArrayList<ExactRef>();
            implementation=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootOperatorCharacterAuthority.class);
            closure.add(implementation);
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootOperatorPhysicalEvidence.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootOperatorGuardEvidence.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootOperatorFreshReadEvidence.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPlayedCharacterPublicContract.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeFreshSnapshotPort.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeGameTransport.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeWire.class));
            for(Class<?> type:List.of(RootNativeSourceAuthority.class,RootRuntimeContext.class))
                closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,type));
            for(Class<?> type:List.of(DriverObservationAssembler.class,DriverObservationEvidenceReader.class,NativeDriverStamp.class,
                    DriverJson.class,RawJson.class,ActionCodec.class,ActionObservationWindow.class,LifecycleOriginFactory.class,NativeRequestChronology.class,RootExecutableBindings.class))
                closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,type));
            decoder=selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,OperatorPlayerSwitch.class);closure.add(decoder);
            for(Class<?> type:DriverOperatorRebindSource.implementationTypes())
                closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,type));
            closure.add(selected.javaSourceAt("continuity-core/src/main/java/org/xar/ck3/control/continuity/EpisodeWindow.java",EpisodeWindow.class));
            var original=RootRuntimeDefinitions.configuredSources(inputs.configuration());
            definition=nativeSource(original,"/src/set_played_character_v1_mailbox.cpp",RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP);closure.add(definition);
            closure.add(nativeSource(original,"/include/xar_bridge/set_played_character_v1_mailbox.hpp",RootRuntimeSelectedSources.OriginalKind.NATIVE_HEADER));
            closure.add(nativeSource(original,"/src/fresh_full_state_read_v1.cpp",RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP));
            closure.add(nativeSource(original,"/include/xar_bridge/fresh_full_state_read_v1.hpp",RootRuntimeSelectedSources.OriginalKind.NATIVE_HEADER));
            closure.add(nativeSource(original,"/src/ck3_11906_adapter.cpp",RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP));
            closure.add(nativeSource(original,"/src/game_adapter.cpp",RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP));
            closure.add(nativeSource(original,"/bridge.cpp",RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP));
            sources=closure.stream().distinct().sorted(Comparator.comparing(ExactRef::path)).toList();
            StrictJson.require(!sources.isEmpty()&&sources.size()<=128,"finite actual operator implementation/source closure required");
        }
        private Prepared(ExactRef actualNativeDefinition,RootAdditionalDomains.ImplementationMetadata metadata)throws IOException {
            this.history=Optional.empty();
            this.definition=Objects.requireNonNull(actualNativeDefinition);
            Objects.requireNonNull(metadata);
            this.decoder=metadata.implementation(OperatorPlayerSwitch.class);
            this.implementation=metadata.implementation(RootOperatorCharacterAuthority.class);
            var closure=new ArrayList<ExactRef>();
            closure.add(this.implementation);
            closure.add(this.decoder);
            closure.add(this.definition);
            for(Class<?> type:DriverOperatorRebindSource.implementationTypes())
                closure.add(metadata.implementation(type));
            this.sources=closure.stream().distinct().sorted(Comparator.comparing(ExactRef::path)).toList();
        }
        private ExactRef nativeSource(List<SelectedSource> originals,String suffix,RootRuntimeSelectedSources.OriginalKind kind)throws IOException {
            if(history.isEmpty())throw new IOException("INCOMPLETE_OPERATOR_SOURCE: native source lookup requires explicit legacy Inputs/Selected custody");
            var legacy=history.get();
            var matches=originals.stream().filter(row->("/"+row.targetRelative().replace('\\','/')).endsWith(suffix))
                    .map(SelectedSource::sourceRef).distinct().toList();
            if(matches.size()!=1)throw new IOException("INCOMPLETE_OPERATOR_SOURCE: exact configured native producer is absent or ambiguous: "+suffix);
            var ref=matches.getFirst();return legacy.selected.original(new FileRef(ref.path(),ref.bytes(),ref.sha256()),kind);
        }
        public void requireInputs(RootRuntimeDefinitions.Inputs identical,RootRuntimeSelectedSources same)throws IOException {
            if(history.isEmpty())throw new IOException("ordinary operator source has no historical Inputs/source custody");
            var legacy=history.get();
            if(legacy.inputs!=identical||legacy.selected!=same)throw new IOException("operator source belongs to another original Inputs/source custody");
            legacy.selected.requireInputs(legacy.inputs);
        }
        public List<ExactRef> sources(){return sources;}
        @Override public Class<?> implementationType(){return RootOperatorCharacterAuthority.class;}
        @Override public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        @Override public Collection<NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            Objects.requireNonNull(same);
            if(core!=null&&core!=same)throw new IOException("operator authority cannot replace its original Core");
            if(history.isPresent()){
                var legacy=history.get();
                legacy.selected.requireInputs(legacy.inputs);
                StrictJson.require(ContinuityJson.same(same.configuration().toJson(),legacy.inputs.application().toJson()),"operator authority requires the exact original application configuration bytes");
                StrictJson.require(same.configuration().writerSources().containsAll(sources),"INCOMPLETE_OPERATOR_SOURCE: original writer source roster omitted actual operator implementations");
            }
            if(core==null){same.bindOperatorAuthority(this);core=same;}
        }
        @Override public synchronized Installed install(RootRuntimeContext context)throws IOException {
            Objects.requireNonNull(context);if(core==null||context.core()!=core)throw new IOException("operator requires its privately bound actual Core");
            Installed retained=installed.get(context);if(retained!=null)return retained;
            if(installed.size()>=64)throw new IOException("operator actual physical-context bound exhausted");
            if(history.isPresent())history.get().selected.requireLoadedClasses(context.game().launchPlan());
            var actual=new Installed(this,context);
            installed.put(context,actual);return actual;
        }
        /** The sole catalog factory invokes this only after it froze and bound the actual combined inventory. */
        public synchronized void bindInventory(RootRuntimeContext context,RootExecutableBindings actual)throws IOException {
            if(context.core()!=core||context.bindings()!=Objects.requireNonNull(actual))throw new IOException("operator guard requires the identical installed combined inventory");
            Installed source=installed.get(context);if(source==null)throw new IOException("actual operator source must be installed before its guard inventory binding");
            requireInstalled(source);actual.bindOperatorAuthority(context.game().generation(),context.game().sessionId(),context.source(),source);
            source.inventoryBound=true;
        }
        synchronized void requireInstalled(Installed actual)throws IOException {
            if(actual==null||actual.prepared!=this||installed.get(actual.context)!=actual||actual.context.core()!=core)
                throw new IOException("operator source is not the identical installed private producer");
            if(history.isPresent()){
                var legacy=history.get();
                legacy.selected.requireInputs(legacy.inputs);legacy.selected.requireLoadedClasses(actual.context.game().launchPlan());
            }
        }
        private static final class HistoricalSources {
            private final RootRuntimeDefinitions.Inputs inputs;
            private final RootRuntimeSelectedSources selected;
            private HistoricalSources(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected){
                this.inputs=inputs;this.selected=selected;
            }
        }
        /** Historical no-rebind validation retrieves only the already installed private source; it never installs or issues. */
        public void requireOperatorWithoutRebind(RootRuntimeContext context,ContinuityStorePort.Session same,ActionReceipt receipt,
                ActionPorts.OutcomeArchive archive)throws IOException {
            installedForHistory(context).requireArchivedReceipt(same,receipt,archive,true);
        }
        /** Cold terminal replay authenticates original receipts through the existing source, without issuing a target family. */
        public void requireArchivedReceipt(RootRuntimeContext context,ContinuityStorePort.Session same,ActionReceipt receipt,
                ActionPorts.OutcomeArchive archive)throws IOException {
            installedForHistory(context).requireArchivedReceipt(same,receipt,archive,false);
        }
        private Installed installedForHistory(RootRuntimeContext context)throws IOException {
            Installed actual;
            synchronized(this){
                actual=installed.get(Objects.requireNonNull(context));
                if(actual==null||context.core()!=core||context.core().operatorAuthority()!=this)
                    throw new IOException("actual operator source was not installed for this identical Core/context");
            }
            return actual;
        }
        private Execution requireActive()throws IOException {
            Execution current=active.get();if(current==null)throw new IOException("operator source requires its privately entered original canonical execution");
            requireInstalled(current.owner);current.owner.context.writer().requireSession(current.same);return current;
        }
        @Override public String revalidate(ContinuityState before,WriterContracts.Request request)throws IOException {
            Execution actual=requireActive();StrictJson.require(actual.window!=null&&actual.window.request().identity().equals(request.identity())
                    &&ContinuityJson.same(actual.same.head().state().toJson(),before.toJson()),"operator transition escaped its private immediate predecessor");
            actual.owner.requireTransition(actual);return ContinuityJson.digest(before.toJson());
        }
        @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request)throws IOException {
            StrictJson.require(EpisodeWindow.OPERATOR_REBIND_KIND.equals(request.kind()),"operator authority cannot reduce BEGIN/BASELINE or another transition");
            return EpisodeWindow.reduce(before,request);
        }
        /** Only the installed observation/cycle consumers receive the genuine fresh post-CAS semantic original. */
        public SemanticEvidence requireOperatorRebound(SessionIdentity owner,ActionReceipt receipt,Instant deadline)throws IOException,InterruptedException {
            Installed actual;
            synchronized(this){actual=installed.values().stream().filter(value->value.matches(owner)).findFirst().orElseThrow(()->new IOException("actual operator owner is not installed"));}
            return actual.context.withSession(same->actual.requireCompleted(same,owner,receipt,deadline));
        }
        @Override public void requireCurrent(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt receipt,SemanticEvidence semantic)throws IOException {
            Installed actual;
            synchronized(this){actual=installed.values().stream().filter(value->value.matches(owner)).findFirst().orElseThrow(()->new IOException("actual operator cycle source is unavailable"));}
            SemanticEvidence qualified=actual.requireCompleted(same,owner,receipt,actual.context.clock().instant().plusSeconds(30));
            StrictJson.require(qualified.equals(semantic),"operator cycle rebind substituted its private actual rebound SEM");
        }
    }
    /** The constructor is private; a caller can neither install an equal-looking source nor mint an execution permit. */
    public static final class Installed implements RootSetPlayedCharacterRuntime.Source,ActionPorts.GuardPort,
            RootExecutableBindings.OperatorSourceOriginProof,DriverOperatorRebindSource {
        private final Prepared prepared;
        private final RootRuntimeContext context;
        private final RootDomainInstallation installation;
        private final LinkedHashMap<String,Execution> original=new LinkedHashMap<>();
        private Execution retained;
        private boolean driverBound,inventoryBound;
        private Installed(Prepared prepared,RootRuntimeContext context){
            this.prepared=prepared;this.context=context;
            var family=new RootExecutableBindings.Family<>("root-operator-player-switch",Long.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(OperatorPlayerSwitch.CAPABILITY),prepared.definition,prepared.decoder,prepared.implementation,
                    target->{var row=StrictJson.object();row.put("character_id",target);return new RawJson(StrictJson.canonical(row));},
                    target->new OperationKey("set-played-character-v1-"+target),this::issue,operation->decodeTarget(operation));
            installation=new RootDomainInstallation("root-operator-character",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                    List.of(family),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        private Optional<Long> decodeTarget(OperationKey operation){
            String prefix="set-played-character-v1-",value=operation.value();if(!value.startsWith(prefix))return Optional.empty();
            String target=value.substring(prefix.length());if(!target.matches("[1-9][0-9]{0,9}"))return Optional.empty();
            long parsed=Long.parseLong(target);return parsed<=Integer.MAX_VALUE?Optional.of(parsed):Optional.empty();
        }
        private RootExecutableBindings.IssuedAction issue(Long target){
            var operation=new OperationKey("set-played-character-v1-"+target);
            var effect=new NativeEffectRegistry.Binding(operation,prepared.definition,this,this::observe);
            var archived=new NativeRecordedEvidenceVerifier.Binding(operation,prepared.implementation,this::verifyArchived);
            return new RootExecutableBindings.IssuedAction(RootExecutableBindings.ActionBinding.operatorSource(effect,prepared.decoder,this),archived);
        }
        @Override public RootDomainInstallation installation(){return installation;}
        @Override public void requireOwner(RootRuntimeContext same)throws IOException {
            if(context!=same)throw new IOException("operator source belongs to another actual runtime context");prepared.requireInstalled(this);
        }
        boolean matches(SessionIdentity owner){return owner.machineId().equals(context.game().machineId())&&owner.game().equals(context.game().generation())&&owner.sessionId().equals(context.game().sessionId());}
        boolean hasOriginalPending(RootApplicationSession root){return retained!=null&&retained.root==root&&!retained.controllerAccepted&&!retained.closedWithoutRebind;}
        @Override public RootSetPlayedCharacterRuntime.Completed execute(RootApplicationSession root,OperatorPlayerSwitch.Request request,Instant deadline)throws IOException,InterruptedException {
            requireOwner(context);return root.executeOperatorCharacter(this,request,deadline);
        }
        /** Called by the sole Session while it retains its original calls lock and borrowed writer. */
        Result executeCurrent(RootApplicationSession root,OperatorPlayerSwitch.Request request,Instant deadline,ContinuityStorePort.Session same)throws IOException,InterruptedException {
            requireOwner(context);context.writer().requireSession(same);requireRoot(root);context.requireCurrent(deadline);
            if(!inventoryBound)throw new IOException("INCOMPLETE_OPERATOR_SOURCE: actual catalog did not bind its identical operator guard");
            if(prepared.active.get()!=null)throw new IOException("nested operator execution is unavailable");
            Execution execution=retained;
            if(execution!=null&&!execution.controllerAccepted&&!execution.closedWithoutRebind){
                if(!execution.request.equals(request)||execution.root!=root)throw new IOException("original operator attempt is unresolved; another target/revision cannot replace it");
                execution.same=same;execution.readDeadline=deadline;execution.currentPhysical=null;
                requireOnlyOriginal(same,execution.command.actionId());
            }else{
                requireOnlyOriginal(same,null);
                requireSupportedTransport(deadline);
                var before=RootOperatorPhysicalEvidence.captureBefore(context,root,same,deadline);
                supportedBefore(before,request);requirePlayerControl(before.full().semantic());
                if(context.remainingDomains().lifecycle().pending(same,root.identity()).isPresent())
                    throw new IOException("operator cannot clear a privately pending lifecycle/UI control obligation");
                preflight(root,same,before);
                if(original.size()>=256)throw new IOException("retained operator original bound exhausted before dispatch");
                execution=new Execution(this,root,same,request,deadline,before);
                execution.command=command(execution);retained=execution;
                original.put(execution.command.actionId(),execution);
            }
            if(!driverBound){context.adopted().authority().bindOperatorRebindSource(this);driverBound=true;}
            prepared.active.set(execution);
            try {
                boolean query=execution.canonicalEntered;execution.canonicalEntered=true;
                var receipt=root.operatorCanonical(this,same,execution.command,query);
                if(receipt.state() instanceof ActionState.RejectedBeforeDispatch){
                    verifyArchived(same.head(),receipt,context.archive().withSession(same));
                    execution.closedWithoutRebind=true;
                    throw failure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"original operator was rejected before native submission",Optional.of(context.archive().withSession(same).receiptReferenceOf(receipt)));
                }
                if(receipt.state() instanceof ActionState.Settled rejected&&rejected.settlement() instanceof ActionState.Rejected
                        &&rejected.dispatch() instanceof NativeActionPort.AckReceived ack){
                    var reason=OperatorPlayerSwitch.knownRejection(ack);
                    if(reason.isPresent()){
                        verifyArchived(same.head(),receipt,context.archive().withSession(same));execution.closedWithoutRebind=true;
                        throw failure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,"native gameplay step failed: "+reason.get().wire(),
                                Optional.of(context.archive().withSession(same).receiptReferenceOf(receipt)));
                    }
                }
                if(!(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.OperatorRebound rebound)){
                    String reason="operator result remains UNKNOWN; preserve the original attempt and query it read-only";
                    var dispatch=ActionTransitions.dispatch(receipt.state());
                    if(dispatch.orElse(null) instanceof NativeActionPort.AckReceived ack&&!ack.nativeOk()){
                        var fields=DriverJson.object(ack.originalFrame().bytes(),DriverJson.MAX_NATIVE_BYTES);
                        if(fields.get("error") instanceof OpportunityJson.Text error&&!(fields.get("typed_query_failure_v1") instanceof OpportunityJson.Obj))
                            reason="native played-character rebind returned an unknown rejection code: "+error.value();
                    }
                    throw failure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,reason,Optional.of(context.archive().withSession(same).receiptReferenceOf(receipt)));
                }
                execution.completion=rebound.observation();execution.finalReceipt=receipt;
                verifyArchived(same.head(),receipt,context.archive().withSession(same));
                requireCompleted(same,root.identity(),receipt,deadline);
                return new Result(receipt,new RootSetPlayedCharacterRuntime.Completed(execution.completion,execution.fromActor));
            }finally{prepared.active.remove();}
        }
        void accepted(Result actual)throws IOException {
            if(retained==null||retained.finalReceipt!=actual.receipt()||!retained.completion.equals(actual.completed().completion()))
                throw new IOException("Controller acceptance must consume the identical private original operator result");retained.controllerAccepted=true;
        }
        void requireCanonicalScope(RootApplicationSession root,ContinuityStorePort.Session same,ActionCommand command)throws IOException {
            Execution actual=prepared.requireActive();StrictJson.require(actual.owner==this&&actual.root==root&&actual.same==same&&actual.command.equals(command),
                    "operator canonical caller has no identical private source execution");requireRoot(root);requireOnlyOriginal(same,command.actionId());
        }
        private void requireRoot(RootApplicationSession root)throws IOException {
            if(context.actions()!=root||context.adopted()!=root.driver()||!root.ownedBy(context.core())||root.isRetired())
                throw new IOException("operator cannot transfer the actual Root, Driver or physical owner");
        }
        private void requireOnlyOriginal(ContinuityStorePort.Session same,String permitted)throws IOException {
            context.writer().requireSession(same);
            boolean blocked=context.core().actions().withFrozen(same,lease->lease.snapshot().actions().stream()
                    .anyMatch(value->!value.settled()&&!value.command().actionId().equals(permitted)));
            if(blocked)throw new IOException("operator cannot clear another unresolved canonical action or pending continuation");
        }
        private void supportedBefore(RootOperatorPhysicalEvidence.Captured before,OperatorPlayerSwitch.Request request)throws IOException {
            var packet=NativeWire.decode(context.archive().withSession(context.borrowedSession()).readOriginalPacket(before.hello()));
            if(!(packet instanceof NativeWire.Hello hello))throw new IOException("actual operator HELLO is unavailable");
            RootPlayedCharacterPublicContract.requireCapability(Set.copyOf(hello.capabilities()));
            RootPlayedCharacterPublicContract.requireBefore(request,before.full().semantic());
            if(!"ck3-1.19.0.6-msvc-x64".equals(hello.adapterId())||!hello.gameSha256().equalsIgnoreCase(OperatorPlayerSwitch.EXECUTABLE_SHA256))
                throw failure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"native played-character rebind requires the frozen exact build",Optional.of(before.hello()));
            RootOperatorGuardEvidence.requireSupported(hello);
            StrictJson.require(before.full().facts().publicRevision().equals(request.expectedRevision()),"operator actual public facts differ from its source-bound semantic revision");
            if(!hello.capabilities().contains(NativeFreshSnapshotPort.CAPABILITY))
                throw failure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"independent operator full-state READ producer is unavailable",Optional.of(before.hello()));
        }
        private void requireSupportedTransport(Instant deadline)throws IOException,InterruptedException {
            var transport=context.transport();transport.awaitHello(deadline);transport.verifyHeld(deadline);
            var hello=transport.diagnostics().originalHello().orElseThrow(()->new IOException("actual operator HELLO is unavailable")).original();
            RootPlayedCharacterPublicContract.requireCapability(Set.copyOf(hello.capabilities()));
        }
        private void preflight(RootApplicationSession root,ContinuityStorePort.Session same,RootOperatorPhysicalEvidence.Captured before)throws IOException {
            root.cycles().requireOperatorBefore(same,root.identity(),before.known().driver(),
                    OpportunityJson.integer(before.full().semantic().get("date_raw"),"date_raw"));
            var state=same.head().state();var window=EpisodeWindow.state(state);
            var whole=state.toJson();String status=StrictJson.text(whole.get("status"));
            StrictJson.require(Set.of("running","complete").contains(status),"operator cannot erase a repair-required/interrupted original continuity window");
            for(String key:List.of("pending_cycle","pending_checkpoint"))StrictJson.require(!whole.has(key)||whole.get(key).isNull(),"operator cannot replace an original pending cycle or SAVE");
            if(window.isPresent()){
                EpisodeWindow.requireActive(state);
                StrictJson.require(org.xar.ck3.control.contracts.GameGeneration.fromJson(state.toJson().get("game_binding")).equals(before.known().stamp().game()),
                        "operator cannot enter another active Window Game");
            }else{
                var entry=state.toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD);
                StrictJson.require(entry!=null&&entry.isObject(),"operator original Root requires its genuinely committed gameplay entry");
                var baseline=state.toJson().get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD);
                StrictJson.require(baseline!=null&&!baseline.isNull(),"operator original Root lacks its genuine Driver history baseline");
                // This is only the original canonical opening. Actual full Game/source/Driver qualification is the private physical capture.
                StrictJson.require(before.full().actual().session().game().equals(context.game().generation())
                        &&before.known().stamp().game().equals(context.game().generation()),"operator initial entry is not the same actual full Game");
            }
            var lineage=EpisodeWindow.operatorLineage(state);
            if(!lineage.isEmpty())StrictJson.require(lineage.getLast().after().actorId()==before.known().driver().session().actorId().longValueExact()
                    &&lineage.getLast().afterDriverVersion()<=before.known().stamp().driverVersion(),"operator predecessor differs from actual canonical actor lineage");
        }
        private ActionCommand command(Execution execution){
            var before=execution.before;var full=before.full();CommandOrigin origin;
            var projected=context.core().observationAssembler().assemble(full.actual(),full.facts(),full.originalEvidence());
            var player=full.semantic().get("played_character");
            boolean living=player instanceof OpportunityJson.Obj character&&character.get("alive") instanceof OpportunityJson.Bool alive&&alive.value();
            if(living&&projected instanceof DriverObservationAssembler.Complete complete)origin=new CommandOrigin.Gameplay(complete.identity());
            else{
                var terminal=LifecycleOriginFactory.projectOperatorBefore(full,before.hello(),before.driver(),before.source().proof(),execution.request);
                StrictJson.require(terminal instanceof LifecycleOriginFactory.Projected,"operator actual old-subject origin is unavailable");
                origin=new CommandOrigin.LifecycleTerminal(((LifecycleOriginFactory.Projected)terminal).identity());
            }
            var expected=new OperatorRebindExpectation(origin,context.source(),execution.request,before.known().stamp().episodeRunId(),before.known().stamp().episodeEpoch(),before.driver());
            return new ActionCommand("operator-"+UUID.randomUUID(),origin,context.source(),execution.root.identity().sessionId(),new OperationKey(execution.request.step()),
                    new OpportunityJson.Obj(Map.of()),new CommandExpectation.OperatorRebind(expected),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),execution.readDeadline);
        }
        private void requirePlayerControl(OpportunityJson.Obj semantic)throws IOException {
            var value=semantic.get("_player_control_authorization_blocked_v1");
            if(value!=null&&value!=OpportunityJson.Nil.INSTANCE&&(!(value instanceof OpportunityJson.Bool blocked)||blocked.value()))
                throw new IOException("operator cannot bypass actual player-control authorization isolation");
        }
        @Override public ExactRef operatorDefinitionSource(){return prepared.definition;}
        @Override public void requireOperatorOrigin(ContinuityStorePort.Session same,ActionCommand command)throws IOException {
            Execution actual=prepared.requireActive();requireCanonicalScope(actual.root,same,command);actual.before.requireRetained(same);
            supportedBefore(actual.before,actual.request);requirePlayerControl(actual.before.full().semantic());
        }
        @Override public NativeRequest prepare(ActionCommand command){throw new IllegalStateException("operator preparation requires the actual borrowed writer and private source");}
        @Override public NativeRequest prepare(ContinuityStorePort.Session same,ActionCommand command,String requestId){
            try{requireOperatorOrigin(same,command);return new NativeRequest(command.operation().value(),Optional.of(OperatorPlayerSwitch.CAPABILITY),new RawJson(StrictJson.canonical(StrictJson.object())),prepared.sources);}
            catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        @Override public ActionPorts.PostconditionResult observeOperatorReconciliation(ContinuityStorePort.Session same,
                ActionReceipt canonical,Instant deadline,ActionPorts.OperatorReconciliationWork observer)throws IOException,InterruptedException {
            Execution actual=prepared.requireActive();requireCanonicalScope(actual.root,same,canonical.command());
            StrictJson.require(canonical.command().expectation() instanceof CommandExpectation.OperatorRebind&&!canonical.settled()
                    &&canonical.equals(canonical(same,canonical.command().actionId())),"operator read-only continuation changed its canonical original");
            var attempt=ActionTransitions.attempt(canonical.state()).orElseThrow(()->new IOException("original operator has no durable attempt"));
            var dispatch=ActionTransitions.dispatch(canonical.state()).orElseThrow(()->new IOException("original operator has no definitive dispatch"));
            if(!(dispatch instanceof NativeActionPort.AckReceived ack))
                return new ActionPorts.Pending("original operator still has no actual ACK; no replay",List.of(attempt.guard().nativeEvidence()));
            if(!ack.nativeOk()&&OperatorPlayerSwitch.knownRejection(ack).isEmpty())
                return new ActionPorts.Pending("original operator rejection is not an exact known native code; no replay",List.of(attempt.guard().nativeEvidence()));
            ack.custody().orElseThrow(()->new IOException("original operator ACK custody is absent")).verify(ack,attempt.guard());
            RootOperatorGuardEvidence.requireHistorical(same,canonical.command(),attempt.guard(),context.archive().withSession(same));
            context.requireCurrent(deadline);Instant previous=actual.readDeadline;
            if(deadline.isBefore(actual.readDeadline))actual.readDeadline=deadline;
            try{return Objects.requireNonNull(observer.apply());}finally{actual.readDeadline=previous;}
        }
        @Override public GuardEvidence verify(WriterContracts.Head head,ActionCommand command){
            try{
                Execution actual=prepared.requireActive();requireCanonicalScope(actual.root,actual.same,command);actual.before.requireRetained(actual.same);
                StrictJson.require(head.digest().equals(actual.same.head().digest()),"operator guard crossed the actual canonical head");
                ExactRef proof=RootOperatorGuardEvidence.preserve(actual.before,command,context.core().authorityId(),context.archive().withSession(actual.same),head,actual.same);
                return new GuardEvidence(command.origin(),context.source(),command.sessionId(),actual.before.full().actual().session().connectionGeneration(),command.operation(),
                        actual.before.full().originalEvidence(),actual.before.hello(),context.core().authorityId(),actual.before.full().actual().observedAt(),actual.readDeadline,List.of(proof));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
            try{
                Execution actual=prepared.requireActive();requireCanonicalScope(actual.root,actual.same,command);
                if(!(dispatch instanceof NativeActionPort.AckReceived ack))
                    return NativeEffectRegistry.Projected.pending("original operator dispatch has no actual ACK; no replay",List.of(attempt.guard().nativeEvidence()));
                ack.custody().orElseThrow(()->new IOException("actual operator ACK receive custody is absent")).verify(ack,attempt.guard());
                var archive=context.archive().withSession(actual.same);
                RootOperatorGuardEvidence.requireHistorical(actual.same,command,attempt.guard(),archive);
                if(!ack.nativeOk()){
                    var reason=OperatorPlayerSwitch.knownRejection(ack);
                    if(reason.isEmpty())return NativeEffectRegistry.Projected.pending("original operator rejection is not an exact known native code; no replay",List.of(attempt.guard().nativeEvidence()));
                    archive.preserve(ack);
                    return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(new ActionState.Rejected(ack.requestId(),reason.get().wire(),archive.referenceOf(ack))),Optional.empty());
                }
                var token=DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
                var status=OperatorPlayerSwitch.NativeStatus.parse(OpportunityJson.text(token.get("status"),"operator native status"));
                if(actual.ack!=null)StrictJson.require(actual.ack.equals(ack)&&actual.attempt.equals(attempt),"operator cannot change its original ACK or attempt");
                actual.ack=ack;actual.attempt=attempt;
                archive.preserve(ack);ExactRef ackRef=archive.referenceOf(ack);
                if(actual.currentPhysical==null){
                    actual.currentPhysical=actual.after==null
                            ?RootOperatorPhysicalEvidence.capture(context,actual.root,actual.same,readDeadline(actual))
                            :RootOperatorPhysicalEvidence.captureBefore(context,actual.root,actual.same,readDeadline(actual));
                    if(actual.after!=null)StrictJson.require(Arrays.equals(actual.currentPhysical.full().actual().originalPacket(),actual.after.full().actual().originalPacket())
                            &&actual.currentPhysical.full().actual().observedAt().equals(actual.after.full().actual().observedAt()),
                            "operator original AFTER occurrence is no longer the held current original; keep UNKNOWN without another mutation");
                    StrictJson.require(!actual.currentPhysical.full().actual().observedAt().isBefore(ack.custody().orElseThrow().responseReceived().observedAt()),
                            "operator after was not independently received after its original ACK");
                    OperatorPlayerSwitch.requireAfter(actual.request,node(actual.currentPhysical.full().semantic()));
                    requireSamePhysical(actual.before,actual.currentPhysical);requirePlayerControl(actual.currentPhysical.full().semantic());
                    if(actual.after==null)actual.after=actual.currentPhysical;
                }
                var beforeDriver=actual.before.known().driver();boolean changed=beforeDriver.session().actorId().longValueExact()!=actual.request.characterId();
                if(actual.freshReadProof==null)actual.freshReadProof=RootOperatorFreshReadEvidence.preserve(command,ack,actual.before,actual.after,archive);
                ExactRef afterDriver=actual.before.driver(),afterAux=actual.before.auxiliary(),commit,proof;
                if(changed){
                    if(actual.window==null){
                        var known=actual.currentPhysical.known();var proposed=DriverOperatorRebindProjection.propose(known,actual.request);
                        afterDriver=archive.preserveMaterial(RawJson.fullMaterial(proposed.driver().encode()));
                        afterAux=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(proposed.auxiliary())));
                        var prior=EpisodeWindow.operatorLineage(actual.same.head().state());
                        var previous=prior.isEmpty()?Optional.<String>empty():Optional.of(prior.getLast().digest());
                        var originals=new EpisodeWindow.OperatorOriginals(actual.before.hello(),actual.before.full().originalEvidence(),ackRef,
                                actual.after.full().originalEvidence(),actual.before.driver(),afterDriver,actual.before.auxiliary(),afterAux);
                        actual.window=new EpisodeWindow.OperatorRebind(command.actionId(),identity(actual.before.full(),known,beforeDriver.session().actorId().longValueExact()),
                                identity(actual.after.full(),known,actual.request.characterId()),known.stamp().driverVersion(),Math.addExact(known.stamp().driverVersion(),1),
                                command.actionId(),ActionCodec.bodySha256(command),attempt.requestId(),context.source().sourceRef(),originals,previous);
                        var base=actual.window.request();var refs=new ArrayList<>(base.evidence());refs.add(actual.freshReadProof);
                        actual.windowRequest=new WriterContracts.Request(base.kind(),base.details(),refs.stream().distinct().toList());
                        actual.windowPrepared=actual.same.preview(actual.windowRequest);
                    }
                    if(actual.windowReceipt==null){
                        if(actual.commitAttempted){
                            actual.windowReceipt=actual.same.queryCommitted(actual.windowPrepared).orElseThrow(()->new IOException("original operator Window commit is unresolved; do not re-commit"));
                        }else{
                            actual.commitAttempted=true;actual.windowReceipt=actual.same.commit(actual.windowPrepared);
                        }
                    }
                    actual.same.requireCommitted(actual.windowPrepared,actual.windowReceipt);
                    if(actual.published==null){
                        actual.casKnown=actual.currentPhysical.known();
                        actual.published=context.adopted().authority().publishOperatorRebind(actual.same);
                    }
                    afterDriver=actual.window.originals().afterDriver();afterAux=actual.window.originals().afterAuxiliary();
                    commit=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(actual.windowReceipt.head().toJson())));
                    proof=actual.published.originalSource();
                }else{
                    var canonical=canonical(actual.same,command.actionId());
                    StrictJson.require(!canonical.settled()&&ActionTransitions.dispatch(canonical.state()).filter(ack::equals).isPresent(),"unchanged operator lacks its canonical original ACK point");
                    commit=archive.receiptReferenceOf(canonical);
                    proof=preserveNoChange(actual,commit,ackRef);
                }
                if(actual.rebound==null)actual.rebound=rebound(actual);
                OperatorPlayerSwitch.requireAfter(actual.request,node(actual.rebound.full().semantic()));
                OperatorPlayerSwitch.requireRebound(actual.request,beforeDriver.session().episodeRunId(),node(actual.rebound.full().semantic()));
                StrictJson.require(actual.rebound.known().driver().session().actorId().longValueExact()==actual.request.characterId(),"actual post-publication Driver did not rebind its actor");
                ExactRef rebound=actual.semantic.semantic();var facts=actual.rebound.full().facts();
                var refs=new OperatorPlayerSwitch.Artifacts(actual.before.hello(),actual.before.full().originalEvidence(),ackRef,actual.after.full().originalEvidence(),
                        actual.before.driver(),afterDriver,actual.before.auxiliary(),afterAux,commit,proof,rebound);
                var completion=new OperatorPlayerSwitch.Completion(actual.request,command.actionId(),ActionCodec.bodySha256(command),attempt.requestId(),context.source(),
                        actual.rebound.full().actual().session(),beforeDriver.session().episodeRunId(),facts.episodeEpoch(),beforeDriver.session().actorId().longValueExact(),
                        actual.before.known().stamp().driverVersion(),actual.rebound.known().stamp().driverVersion(),status,facts.publicRevision(),facts.nativeRevision(),
                        OpportunityJson.integer(actual.rebound.full().semantic().get("date_raw"),"date_raw").longValueExact(),refs);
                completion.validate(command,attempt,ack);actual.completion=completion;
                return new NativeEffectRegistry.Projected(new ActionPorts.OperatorRebindObserved(completion),Optional.empty());
            }catch(InterruptedException interrupted){Thread.currentThread().interrupt();return NativeEffectRegistry.Projected.pending("operator independent observation interrupted; preserve original attempt",List.of(attempt.guard().nativeEvidence()));}
            catch(IOException|RuntimeException failure){return NativeEffectRegistry.Projected.pending("operator original poststate/source is unavailable: "+failure.getClass().getName()+"; no replay",List.of(attempt.guard().nativeEvidence()));}
        }
        private Instant readDeadline(Execution actual){
            Instant central=ActionObservationWindow.deadline(actual.command);return central.isBefore(actual.readDeadline)?central:actual.readDeadline;
        }
        private void requireTransition(Execution actual)throws IOException {
            requireCanonicalScope(actual.root,actual.same,actual.command);
            StrictJson.require(actual.ack!=null&&actual.after!=null&&actual.window!=null,"actual operator transition requires original ACK and independent after");
            var canonical=canonical(actual.same,actual.command.actionId());
            StrictJson.require(!canonical.settled()&&ActionTransitions.attempt(canonical.state()).filter(actual.attempt::equals).isPresent()
                    &&ActionTransitions.dispatch(canonical.state()).filter(actual.ack::equals).isPresent(),"operator canonical attempt or ACK changed before its Window transition");
            Objects.requireNonNull(actual.currentPhysical).requireRetained(actual.same);
            RootOperatorGuardEvidence.requireHistorical(actual.same,actual.command,actual.attempt.guard(),context.archive().withSession(actual.same));
            var proposed=DriverOperatorRebindProjection.propose(actual.currentPhysical.known(),actual.request);
            var archive=context.archive().withSession(actual.same);
            StrictJson.require(Arrays.equals(archive.loadFullMaterial(actual.window.originals().afterDriver()).bytes(),proposed.driver().encode())
                    &&Arrays.equals(archive.loadFullMaterial(actual.window.originals().afterAuxiliary()).bytes(),DriverJson.encode(proposed.auxiliary())),
                    "operator Window did not preserve the sole complete Driver/auxiliary proposal");
        }
        @Override public List<ExactRef> sources(){return prepared.sources;}
        @Override public DriverOperatorRebindSource.Capture current(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException {
            Execution actual=prepared.requireActive();requireCurrent(same,expected,actual);return actual;
        }
        @Override public void requireCurrent(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverOperatorRebindSource.Capture capture)throws IOException {
            Execution actual=prepared.requireActive();
            StrictJson.require(capture==actual&&actual.owner==this&&actual.same==same&&expected==context.adopted().authority()
                    &&actual.windowPrepared!=null&&actual.windowReceipt!=null,"operator CAS source is not the identical private actual capture");
            context.writer().requireSession(same);requireInstalledCurrent(actual);
            same.requireCommitted(actual.windowPrepared,actual.windowReceipt);
            StrictJson.require(same.head().digest().equals(ContinuityJson.digest(actual.windowReceipt.head().toJson())),"operator CAS must consume its immediate original Window head");
            Objects.requireNonNull(actual.currentPhysical).requireRetained(same);requireOnlyOriginal(same,actual.command.actionId());
        }
        @Override public void requirePublished(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverOperatorRebindSource.Capture capture,
                DriverSnapshotFacts.Known published)throws IOException {
            if(!(capture instanceof Execution actual)||actual.owner!=this||original.get(actual.command.actionId())!=actual||expected!=context.adopted().authority())
                throw new IOException("operator publication belongs to another private issuer");
            context.writer().requireSession(same);requireInstalledCurrent(actual);
            same.requireCommitted(actual.windowPrepared,actual.windowReceipt);
            var proposed=DriverOperatorRebindProjection.propose(actual.actualKnown(),actual.request);
            StrictJson.require(published.stamp().game().equals(actual.after.known().stamp().game())&&published.stamp().episodeEpoch()==actual.after.known().stamp().episodeEpoch()
                    &&published.stamp().driverVersion()==actual.window.afterDriverVersion()&&Arrays.equals(published.driver().encode(),proposed.driver().encode())
                    &&published.auxiliary().equals(proposed.auxiliary())&&published.originalHistoryBasis().equals(actual.after.known().originalHistoryBasis()),
                    "operator published Driver/auxiliary/history/epoch differs from its private actual source");
        }
        private void requireInstalledCurrent(Execution actual)throws IOException {
            prepared.requireInstalled(this);requireRoot(actual.root);context.game().verify();
            StrictJson.require(actual.command.source().equals(context.source())&&actual.command.sessionId().equals(context.game().sessionId()),"operator private original source/session changed");
        }
        private ActionReceipt canonical(ContinuityStorePort.Session same,String id){
            return context.core().actions().withFrozen(same,lease->lease.find(id).orElseThrow(()->new IllegalArgumentException("original canonical operator action is absent")));
        }
        /** Reprojects the genuinely ACK-after raw occurrence against the newly published Driver; this is not another native observation. */
        private Rebound rebound(Execution actual)throws IOException {
            var packet=Objects.requireNonNull(actual.after).full();
            return context.adopted().authority().withFrozenRawObservation(packet.actual(),actual.same,frozen->{
                var known=frozen.state();
                var full=context.core().observationAssembler().projectFull(packet.actual(),frozen.facts(),packet.originalEvidence());
                var assembled=context.core().observationAssembler().assemble(full.actual(),full.facts(),full.originalEvidence());
            StrictJson.require(assembled instanceof DriverObservationAssembler.Complete,"actual rebound raw packet and newly published Driver did not join");
            var complete=(DriverObservationAssembler.Complete)assembled;var archive=context.archive().withSession(actual.same);
            ExactRef sem=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(full.semantic())));
            ExactRef stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(complete,known)));
            var facts=archive.loadFullMaterial(full.facts().semanticFactsEvidence());
            ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(full.facts().semanticFactsEvidence(),facts);
            var result=new SemanticEvidence(complete.identity(),sem,full.originalEvidence(),stamp,driver,full.actual().observedAt());
            context.semanticVerifier().verify(actual.same,actual.root.identity(),result);actual.semantic=result;
            return new Rebound(full,known);
            });
        }
        private ExactRef preserveNoChange(Execution actual,ExactRef commit,ExactRef ack){
            var row=StrictJson.object();row.put("schema",NO_CHANGE_SCHEMA).put("action_id",actual.command.actionId()).put("body_sha256",ActionCodec.bodySha256(actual.command));
            row.set("before_driver",actual.before.driver().toJson());row.set("before_auxiliary",actual.before.auxiliary().toJson());row.set("ack",ack.toJson());
            row.set("before_native",actual.before.full().originalEvidence().toJson());row.set("after_native",actual.after.full().originalEvidence().toJson());row.set("canonical_ack",commit.toJson());
            row.set("source",context.source().sourceRef().toJson());row.set("fresh_read_proof",Objects.requireNonNull(actual.freshReadProof).toJson());
            return context.archive().withSession(actual.same).preserveMaterial(new RawJson(StrictJson.canonical(row)));
        }
        private void verifyArchived(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
            try{
                var same=context.borrowedSession();context.writer().requireSession(same);
                StrictJson.require(head.digest().equals(same.head().digest()),"operator archive verifier must retain the original actual writer view");
                if(receipt.state() instanceof ActionState.RejectedBeforeDispatch zero){
                    RootOperatorGuardEvidence.requireHistorical(same,receipt.command(),zero.attempt().guard(),archive);
                    StrictJson.require(zero.attempt().requestId().equals(zero.dispatch().requestId())
                            &&zero.dispatch().proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                            &&zero.dispatch().proof().requestBytesWritten()==0
                            &&archive.load(archive.referenceOf(zero.dispatch())).equals(zero.dispatch()),
                            "operator zero-dispatch completion lacks its actual original no-write outcome");
                    return;
                }
                var settled=(ActionState.Settled)receipt.state();
                var guard=RootOperatorGuardEvidence.requireHistorical(same,receipt.command(),settled.attempt().guard(),archive);
                if(settled.settlement() instanceof ActionState.Rejected rejection){
                    StrictJson.require(settled.dispatch() instanceof NativeActionPort.AckReceived,"operator rejection requires its actual original ACK");
                    var ack=(NativeActionPort.AckReceived)settled.dispatch();
                    var reason=OperatorPlayerSwitch.knownRejection(ack).orElseThrow(()->new IOException("unknown operator native code cannot become a terminal rejection"));
                    ack.custody().orElseThrow(()->new IOException("original rejected operator ACK custody absent")).verify(ack,settled.attempt().guard());
                    StrictJson.require(archive.load(archive.referenceOf(ack)).equals(ack)&&rejection.requestId().equals(ack.requestId())
                            &&rejection.reason().equals(reason.wire())&&rejection.originalEvidence().equals(archive.referenceOf(ack)),
                            "operator rejection changed its actual ACK, exact native code or original metadata");
                    return;
                }
                StrictJson.require(settled.settlement() instanceof ActionState.OperatorRebound,"actual typed operator settlement required");
                var completion=((ActionState.OperatorRebound)settled.settlement()).observation();completion.validate(receipt.command(),settled.attempt(),settled.dispatch());
                ((CommandExpectation.OperatorRebind)receipt.command().expectation()).expected().validateCompletion(completion);
                guard.gameExecutable().ifPresent(executable->StrictJson.require(executable.sha256().equalsIgnoreCase(OperatorPlayerSwitch.EXECUTABLE_SHA256),"operator archived executable differs"));
                StrictJson.require(completion.source().equals(receipt.command().source())&&completion.transport().game().equals(receipt.command().origin().game())
                        &&completion.transport().sessionId().equals(receipt.command().sessionId()),"operator archived source/Game differs from its actual original command");
                DriverOperatorRebindOriginals.requireCanonical(same,receipt,archive);
                if(completion.rebindPerformed()){
                    var publication=DriverOperatorRebindOriginals.decodePublication(archive.loadMaterial(completion.originals().privateProof()));
                    var reads=RootOperatorFreshReadEvidence.require(publication.freshReadProof(),receipt,archive);
                    for(ExactRef ref:reads.references()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
                }
                if(!completion.rebindPerformed()){
                    var refs=completion.originals();var proof=StrictJson.object(StrictJson.parse(archive.loadMaterial(refs.privateProof()).bytes()),
                            Set.of("schema","action_id","body_sha256","before_driver","before_auxiliary","ack","before_native","after_native","canonical_ack","source","fresh_read_proof"));
                    StrictJson.require(NO_CHANGE_SCHEMA.equals(StrictJson.text(proof.get("schema")))&&receipt.command().actionId().equals(StrictJson.text(proof.get("action_id")))
                            &&receipt.bodySha256().equals(StrictJson.text(proof.get("body_sha256")))&&refs.beforeDriver().equals(ExactRef.fromJson(proof.get("before_driver")))
                            &&refs.beforeAuxiliary().equals(ExactRef.fromJson(proof.get("before_auxiliary")))&&refs.ack().equals(ExactRef.fromJson(proof.get("ack")))
                            &&refs.beforeNative().equals(ExactRef.fromJson(proof.get("before_native")))&&refs.afterNative().equals(ExactRef.fromJson(proof.get("after_native")))
                            &&refs.canonicalCommit().equals(ExactRef.fromJson(proof.get("canonical_ack")))&&receipt.command().source().sourceRef().equals(ExactRef.fromJson(proof.get("source"))),
                            "unchanged operator private original proof changed its exact original roles");
                    RootOperatorFreshReadEvidence.require(ExactRef.fromJson(proof.get("fresh_read_proof")),receipt,archive);
                }
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private void requireArchivedReceipt(ContinuityStorePort.Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive originals,boolean failureWithoutRebind)throws IOException {
            Objects.requireNonNull(receipt);Objects.requireNonNull(originals);context.writer().requireSession(same);prepared.requireInstalled(this);
            StrictJson.require(inventoryBound&&same==context.borrowedSession(),
                    "operator non-rebind history requires its installed source and identical borrowed writer session");
            StrictJson.require(originals instanceof NativeOutcomeArchive,"operator non-rebind history requires its actual physical archive");
            var nativeArchive=(NativeOutcomeArchive)originals;
            StrictJson.require(nativeArchive.writer()==context.writer()&&nativeArchive.artifactStore()==context.archive().artifactStore(),
                    "operator non-rebind history crossed its original writer or physical archive");
            StrictJson.require(receipt.command().source().equals(context.source())&&receipt.command().sessionId().equals(context.game().sessionId())
                    &&receipt.command().origin().game().equals(context.game().generation())&&decodeTarget(receipt.command().operation()).isPresent(),
                    "operator non-rebind history crossed its actual source/Game/session/target");
            boolean eligible=receipt.state() instanceof ActionState.RejectedBeforeDispatch;
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Rejected
                    &&settled.dispatch() instanceof NativeActionPort.AckReceived ack)
                eligible=OperatorPlayerSwitch.knownRejection(ack).isPresent();
            if(!failureWithoutRebind&&receipt.state() instanceof ActionState.Settled settled
                    &&settled.settlement() instanceof ActionState.OperatorRebound)eligible=true;
            StrictJson.require(eligible,"only source-verified operator terminal receipts may use this historical path");
            var archive=nativeArchive.withSession(same);var head=same.head();
            ContinuityActionJournal.requireHistoricalReceipt(head.state(),receipt,archive);
            verifyArchived(head,receipt,archive);
            context.writer().requireSession(same);
            StrictJson.require(same.head().equals(head),"operator non-rebind history changed its actual writer head");
        }
        SemanticEvidence requireCompleted(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt receipt,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.requireCurrent(deadline);requireOwner(context);requireOnlyOriginal(same,null);
            Execution actual=original.get(receipt.command().actionId());
            if(actual==null||actual.completion==null||actual.semantic==null||!matches(owner)||actual.root!=context.actions())
                throw new IOException("operator current admission requires the actual private completed source, not a caller DTO");
            var canonical=canonical(same,receipt.command().actionId());
            StrictJson.require(canonical.equals(receipt)&&receipt.settled()&&receipt.command().source().equals(context.source()),"operator admission is not its canonical actual completion");
            verifyArchived(same.head(),receipt,context.archive().withSession(same));
            if(actual.published!=null)actual.published.requireCurrent(same);
            else context.adopted().authority().withFrozenFacts(same,frozen->{
                StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"unchanged operator current Driver is incomplete");
                var known=(DriverSnapshotFacts.Known)frozen.state();StrictJson.require(Arrays.equals(known.driver().encode(),actual.before.known().driver().encode())
                        &&known.stamp().equals(actual.before.known().stamp())&&known.auxiliary().equals(actual.before.known().auxiliary()),"unchanged operator rewrote its Driver/auxiliary/version");return null;});
            context.semanticVerifier().verify(same,owner,actual.semantic);return actual.semantic;
        }
        private static void requireSamePhysical(RootOperatorPhysicalEvidence.Captured before,RootOperatorPhysicalEvidence.Captured after){
            StrictJson.require(before.full().actual().session().equals(after.full().actual().session())&&before.full().facts().source().equals(after.full().facts().source())
                    &&!after.full().actual().observedAt().isBefore(before.full().actual().observedAt()),
                    "operator independent observations crossed actual connection/source or chronology");
            if(before.metadata().isPresent()&&after.metadata().isPresent()){
                StrictJson.require(before.metadata().get().ownerSourceEpoch().equals(after.metadata().get().ownerSourceEpoch())
                        &&before.metadata().get().epochManifest().equals(after.metadata().get().epochManifest())
                        &&before.metadata().get().gameExecutable().equals(after.metadata().get().gameExecutable()),
                        "operator independent observations crossed actual source epoch/EXE");
            }
        }
        private static EpisodeWindow.Identity identity(DriverObservationAssembler.FullSnapshot frame,DriverSnapshotFacts.Known known,long actor){
            var transport=frame.actual().session();return new EpisodeWindow.Identity(transport.machineId(),transport.game(),transport.sessionId(),known.stamp().episodeRunId(),
                    known.stamp().episodeEpoch(),actor,OpportunityJson.integer(frame.semantic().get("date_raw"),"date_raw").longValueExact());
        }
    }
    /** Retained only by this actual installed issuer. Public inputs cannot construct or replace these fields. */
    private static final class Execution implements DriverOperatorRebindSource.Capture {
        private final Installed owner;private final RootApplicationSession root;private ContinuityStorePort.Session same;
        private final OperatorPlayerSwitch.Request request;private Instant readDeadline;private final RootOperatorPhysicalEvidence.Captured before;
        private final Long fromActor;
        private RootOperatorPhysicalEvidence.Captured after,currentPhysical;
        private Rebound rebound;
        private ActionCommand command;private ActionState.Attempt attempt;private NativeActionPort.AckReceived ack;
        private EpisodeWindow.OperatorRebind window;private WriterContracts.Request windowRequest;private WriterContracts.Prepared windowPrepared;private WriterContracts.Receipt windowReceipt;
        private ExactRef freshReadProof;
        private DriverStateAssembler.PublishedOperatorRebind published;
        private DriverSnapshotFacts.Known casKnown;
        private OperatorPlayerSwitch.Completion completion;private SemanticEvidence semantic;private ActionReceipt finalReceipt;
        private boolean canonicalEntered,commitAttempted,controllerAccepted,closedWithoutRebind;
        private Execution(Installed owner,RootApplicationSession root,ContinuityStorePort.Session same,OperatorPlayerSwitch.Request request,Instant deadline,
                RootOperatorPhysicalEvidence.Captured before){
            this.owner=owner;this.root=root;this.same=same;this.request=request;readDeadline=deadline;this.before=before;
            var player=before.full().semantic().get("played_character");
            fromActor=player instanceof OpportunityJson.Obj object?OpportunityJson.integer(object.get("character_id"),"character_id").longValueExact():null;
        }
        @Override public DriverSnapshotFacts.Known actualKnown(){return Objects.requireNonNull(casKnown);}
        @Override public OperatorPlayerSwitch.Request request(){return request;}
        @Override public ActionCommand originalCommand(){return command;}
        @Override public DriverObservationAssembler.FullSnapshot actualBefore(){return before.full();}
        @Override public DriverObservationAssembler.FullSnapshot actualAfter(){return Objects.requireNonNull(after).full();}
        @Override public WriterContracts.Prepared originalPrepared(){return Objects.requireNonNull(windowPrepared);}
        @Override public WriterContracts.Receipt actualReceipt(){return Objects.requireNonNull(windowReceipt);}
        @Override public ExactRef originalFreshReadProof(){return Objects.requireNonNull(freshReadProof);}
    }
    private record Rebound(DriverObservationAssembler.FullSnapshot full,DriverSnapshotFacts.Known known){ }
    record Result(ActionReceipt receipt,RootSetPlayedCharacterRuntime.Completed completed){Result{Objects.requireNonNull(receipt);Objects.requireNonNull(completed);}}
    private static com.fasterxml.jackson.databind.JsonNode node(OpportunityJson.Obj value){return FullJsonTree.parse(DriverJson.encode(value),DriverJson.MAX_NATIVE_BYTES);}
    private static PublicServiceFailure failure(PublicServiceFailure.Kind kind,String reason,Optional<ExactRef> original){return new PublicServiceFailure(kind,reason,original);}
}
