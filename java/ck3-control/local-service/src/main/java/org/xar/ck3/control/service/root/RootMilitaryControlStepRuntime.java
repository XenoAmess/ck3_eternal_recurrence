package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.nativebridge.publicmethods.gui.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Three original fixed native PIPE controls. Canonical Action rows are their sole durable once claims. */
public final class RootMilitaryControlStepRuntime {
    private RootMilitaryControlStepRuntime() { }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs actual)throws IOException{return new Prepared(actual);}
    public record Sources(ExactRef producer,ExactRef decoder,List<ExactRef> producers) {
        public Sources {
            Objects.requireNonNull(producer);Objects.requireNonNull(decoder);producers=List.copyOf(producers);
            require(!producers.isEmpty()&&producers.size()<=64&&producers.containsAll(List.of(producer,decoder))
                    &&producers.stream().allMatch(source->source.bytes()>0),"complete military control producer identities required");
        }
    }
    /** Ordinary composition keeps the actual callable producers without a historical Definitions selection. */
    public static Prepared prepare(Sources sources){return new Prepared(Objects.requireNonNull(sources));}
    public static final class Prepared {
        private final Optional<RootRuntimeSelectedSources> selected;
        private final ExactRef producer,decoder;
        private final List<ExactRef> originals;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        private Prepared(RootRuntimeDefinitions.Inputs inputs)throws IOException {
            var actualSelection=new RootRuntimeSelectedSources(Objects.requireNonNull(inputs));selected=Optional.of(actualSelection);
            producer=actualSelection.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,MilitaryControlActions.class);
            decoder=actualSelection.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,MilitaryControlContract.class);
            actualSelection.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,MilitaryReceiverProof.class);
            actualSelection.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootMilitaryControlStepRuntime.class);
            actualSelection.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootMilitaryControlPublicStepProducts.class);
            ExactRef driver=inputs.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER);
            Path path=Path.of(driver.path()).toAbsolutePath().normalize();
            require(path.getFileName().toString().equals("native_driver.py")&&path.getParent().getFileName().toString().equals("bridge"),"actual configured original native driver required");
            var refs=new ArrayList<ExactRef>();refs.add(driver);Path bridge=path.getParent();
            for(String name:List.of("service.py","gui_window_tree_contract.py","frontend_gui_route_contract.py","gui_callback_binding_12004_contract.py","gui_refill_receiver_candidates_12004_contract.py","military_reinforcement_12004.py","military_reinforcement_12004_contract.py","ingame_military_open_12004.py","timeline_control_ack_v1.py"))refs.add(source(bridge.resolve(name)));
            originals=List.copyOf(refs);for(ExactRef original:originals)requireSame(original);
        }
        private Prepared(Sources sources) {
            selected=Optional.empty();producer=sources.producer();decoder=sources.decoder();originals=sources.producers();
        }
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            Objects.requireNonNull(same);if(core!=null&&core!=same)throw new IOException("military controls cannot change their original Core");core=same;
        }
        public synchronized Installed install(RootRuntimeContext context,RootGuiPublicProducts.Installed sameGui,RootLifeRuntimeFactory.Installed sameLife)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(sameGui);Objects.requireNonNull(sameLife);
            if(core==null||core!=context.core())throw new IOException("fixed military controls require their bound actual Core");
            Attempt prior=attempts.get(context);if(prior!=null){if(prior.installed!=null){require(prior.installed.gui==sameGui&&prior.installed.life==sameLife,"actual military dependencies changed");return prior.installed;}throw new IOException("partial military control construction is not replayable",prior.failure);}
            if(attempts.size()>=64)throw new IOException("finite actual military context bound exhausted");
            Attempt attempt=new Attempt();attempts.put(context,attempt);
            try {
                if(selected.isPresent()){
                    selected.orElseThrow().requireLoadedClasses(context.game().launchPlan());
                    for(ExactRef ref:originals)requireSame(ref);requireSame(producer);requireSame(decoder);
                }
                sameGui.requireContext(context);sameLife.requireContext(context);attempt.installed=new Installed(context,sameGui,sameLife,producer,decoder);return attempt.installed;
            } catch(IOException|RuntimeException failure){attempt.failure=failure;throw failure;}
        }
        private static final class Attempt {Installed installed;Throwable failure;}
    }
    public static final class Installed {
        private final RootRuntimeContext context;
        private final RootGuiPublicProducts.Installed gui;
        private final RootLifeRuntimeFactory.Installed life;
        private final MilitaryControlActions actions;
        private final ExactRef producer;
        private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext context,RootGuiPublicProducts.Installed gui,RootLifeRuntimeFactory.Installed life,ExactRef producer,ExactRef decoder) {
            this.context=context;this.gui=gui;this.life=life;this.producer=producer;
            // No Driver, session or Native read during pre-adoption inventory construction.
            actions=new MilitaryControlActions(gui.contracts(),context.reads(),()->context.archive().withSession(context.borrowedSession()),context.frameLoader(),context.clock());
            var registered=new ArrayList<RootExecutableBindings.ActionBinding>();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
            for(Control control:Control.values()) {
                var effect=NativeEffectRegistry.Binding.existing(control.operation(),producer,actions,actions);
                registered.add(new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(control.capability()),decoder));
                archived.add(new NativeRecordedEvidenceVerifier.Binding(control.operation(),producer,(head,receipt,archive)->{try{replay(receipt,archive);}catch(IOException failure){throw new java.io.UncheckedIOException("actual military archived authority unavailable",failure);}}));
            }
            installation=new RootDomainInstallation("original-fixed-military-control",List.of(),List.of(),List.of(),registered,List.of(),archived,
                    List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public RootDomainInstallation installation(){return installation;}
        public List<RootExecutableBindings.ActionBinding> actionBindings(){return installation.actions();}
        public List<NativeRecordedEvidenceVerifier.Binding> archivedBindings(){return installation.archived();}
        /** Pure installed ownership predicate, never authority to execute or turn UNKNOWN into success. */
        public boolean matchesControl(ActionCommand command) {
            if(command==null||!(command.origin() instanceof CommandOrigin.Gameplay)||!command.source().equals(context.source())
                    ||!command.sessionId().equals(context.game().sessionId())||!command.before().game().equals(context.game().generation()))return false;
            if(Control.parse(command.operation()).isEmpty())return false;
            try {
                MilitaryControlActions.binding(command);
                var installed=context.bindings().actualActionBinding(command.operation());
                return installed.isPresent()&&installed.orElseThrow().preparation()==actions&&installed.orElseThrow().producerSource().equals(producer)
                        &&installation.archived().stream().anyMatch(binding->binding.operation().equals(command.operation())&&binding.definitionSource().equals(producer));
            } catch(IllegalArgumentException invalid){return false;}
        }
        /** Same closed producer can retain an unresolved outcome; classification must keep that state blocked. */
        public boolean matchesPending(ActionCommand command){return matchesControl(command);}
        /** Installer custody only: no unbound Driver/session is consulted here. */
        public void requireContext(RootRuntimeContext same)throws IOException {
            require(context==same&&context.core()==same.core(),"fixed military product crossed actual Root/Core");gui.requireContext(same);life.requireContext(same);
            require(installation.actions().size()==3&&installation.actions().stream().allMatch(binding->binding.effect().preparation()==actions),"fixed military callable custody changed");
        }
        public ActionCommand prepare(Control control,PlanningRequest original,Complete frame,Known known,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
            requireContext(context);context.writer().requireSession(same);context.requireCurrent(original.deadline());caller.requireCurrent(original);
            require(caller.step().equals(control.operation())&&frame.identity().equals(original.before())&&frame.source().equals(original.source())
                    &&frame.sessionId().equals(original.sessionId())&&frame.semantic().equals(original.observations().snapshot()),"fixed military EXECUTE lost its original public planning frame");
            require(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())&&frame.identity().game().equals(context.game().generation())
                    &&known.stamp().game().equals(frame.identity().game())&&known.stamp().episodeRunId().equals(frame.identity().frame().episodeRunId()),"fixed military actual Driver owner differs");
            require(flag(frame,"paused")&&flag(frame,"map_ready"),"fixed military controls require the actual paused map");
            require(original.observations().actionSteps().contains(control.operation())&&original.observations().bridgeCapabilities().contains(control.capability()),"original advertised military native capability unavailable");
            var installed=context.bindings().actualActionBinding(control.operation()).orElseThrow();require(installed.preparation()==actions&&installed.producerSource().equals(producer),"another military native producer is installed");
            var hello=context.transport().originalHello();require(hello.buildMatch()&&hello.gameSha256().equals(GuiModels.Build.CROZIER4.sha256())&&hello.pid()==frame.identity().game().pid()
                    &&hello.connectionGeneration().equals(frame.connectionGeneration()),"military fixed original exact-.4 HELLO differs");
            Binding binding=new Binding(new GuiModels.Context(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),GuiModels.Build.CROZIER4,original.deadline()));
            require(binding.publicRevision().signum()>0,"actual military public revision must be positive");
            requireUnclaimed(context,same,control,binding);
            var command=actions.prepareCommand(control,binding,RootPublicStepExecution.actionId(original,caller));
            if(control!=Control.OPEN){var archive=context.archive().withSession(same);var read=archive.loadRead(ExactRef.fromJson(OpportunityJson.toNode(command.arguments()).get("_military_before_read")));
                require(read.before().originalBindingSha256().equals(frame.fullBindingSha256())&&read.after().originalBindingSha256().equals(frame.fullBindingSha256()),"military before READ crossed held full public planning originals");}
            return command;
        }
        private void replay(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            var attempt=ActionTransitions.attempt(receipt.state());
            if(attempt.isPresent()) {
                RootGuardEvidence.requireHistory(attempt.orElseThrow().guard(),archive,context.borrowedSession());
                var before=RootGuardEvidence.loadFrame(attempt.orElseThrow().guard(),archive,context.frameLoader());
                require(before.identity().equals(receipt.command().before()),"military archived canonical guard frame differs");
                receipt.ack().ifPresent(ack->{ack.custody().orElseThrow().verify(ack,attempt.orElseThrow().guard());require(archive.load(archive.referenceOf(ack)).equals(ack),"military original ACK custody changed");});
            }
            actions.replay(context.borrowedSession().head(),receipt,archive);
        }
        /** Actual canonical public control recording; primitive children of Life/Clock never enter this owner. */
        public RawJson recordedResult(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            requireContext(context);require(matchesControl(receipt.command()),"recording crossed the actual installed fixed military producer");
            replay(receipt,archive);return format(receipt,archive,actions,false);
        }
        public RawJson present(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
            requireContext(context);context.writer().requireSession(same);require(receipt.command().operation().equals(caller.step()),"military public original step changed");
            replay(receipt,archive);return result(receipt,archive,actions);
        }
    }
    private static void requireUnclaimed(RootRuntimeContext context,Session same,Control selected,Binding binding) {
        context.core().actions().withFrozen(same,lease->{
            for(ActionReceipt prior:lease.snapshot().actions()) {
                var control=Control.parse(prior.command().operation());if(control.isEmpty()||(selected==Control.OPEN)!=(control.orElseThrow()==Control.OPEN))continue;
                var command=prior.command();if(!command.source().equals(binding.context().source())||!command.sessionId().equals(binding.context().sessionId())
                        ||!command.before().game().equals(binding.context().before().game())||!command.before().frame().episodeRunId().equals(binding.context().before().frame().episodeRunId())
                        ||!command.before().frame().identity().player().equals(binding.context().before().frame().identity().player()))continue;
                boolean verified=prior.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied;
                require(verified,"an unresolved original military once claim blocks both toggle directions; UNKNOWN is never resent");
                require(!command.operation().equals(selected.operation())||!command.before().frame().revision().equals(binding.publicRevision()),"this fixed military action already has its original same-frame once claim");
            }
            lease.assertCurrent();return null;
        });
    }
    /** Full original Driver result, keeping native ACK distinct from its independently verified UI state. */
    static RawJson result(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,MilitaryControlActions producer) {
        return format(receipt,archive,producer,true);
    }
    private static RawJson format(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,MilitaryControlActions producer,boolean publicWire) {
        Binding binding=MilitaryControlActions.binding(receipt.command());Control control=Control.parse(receipt.command().operation()).orElseThrow();
        var ack=receipt.ack().orElseThrow(()->failure(receipt,archive,"military action has no original ACK; UNKNOWN is never resent"));
        if(!ack.nativeOk())throw failure(receipt,archive,"original military native rejection");
        ObjectNode nativeAck=node(ack.originalResultToken().orElseThrow());ObjectNode out=nativeAck.deepCopy();
        boolean verified=receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied;
        if(control==Control.OPEN&&!verified)throw failure(receipt,archive,"military native ACK lacks an independently visible root");
        PlanningReadReceipt after=null;
        if(verified)after=((ActionState.ControlApplied)((ActionState.Settled)receipt.state()).settlement()).read();
        else if(receipt.state() instanceof ActionState.Unknown unknown) {
            if(!unknown.reason().equals("acknowledged_verification_pending"))throw failure(receipt,archive,unknown.reason());
            for(ExactRef ref:unknown.evidence()) {after=archive.loadRead(ref);producer.normalized(after,binding);}
        }
        out.put("status",control==Control.OPEN?"verified_visible":verified?("noaction_already_desired".equals(nativeAck.path("status").asText())?"verified_already_desired":"verified_desired"):"acknowledged_verification_pending");
        out.put("postcondition_verified",verified).put("verification_pending",!verified);
        out.set("native_ack",nativeAck);out.put("action_request_id",ack.requestId()).put("action_claim_path",archive.receiptReferenceOf(receipt).path())
                .put("episode_run_id",binding.context().before().frame().episodeRunId()).put("queried_revision",binding.publicRevision())
                .put("mouse_used",false).put("keyboard_used",false).put("ocr_used",false);
        if(control!=Control.OPEN) {
            var original=OpportunityJson.toNode(receipt.command().arguments()).get("_military_before_read");var before=archive.loadRead(ExactRef.fromJson(original));
            out.set("before_observation",node(MilitaryReceiverProof.observeFixedReinforcement(producer.normalized(before,binding),binding).encode()));
            if(after==null)out.putNull("later_observation");else out.set("later_observation",node(MilitaryReceiverProof.observeFixedReinforcement(producer.normalized(after,binding),binding).encode()));
        } else out.set("later_military_tree",node(producer.normalized(after,binding)));
        if(publicWire)decimalCounters(out);return raw(out);
    }
    private static PublicServiceFailure failure(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,String reason){return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,reason,Optional.of(archive.receiptReferenceOf(receipt)));}
    private static final Set<String> DECIMAL_COUNTERS=Set.of("revision","native_revision","connection_generation","pump_epoch","ticket_sequence","queried_revision","queried_native_revision");
    static void decimalCounters(JsonNode value){
        if(value instanceof ObjectNode row){var fields=new ArrayList<String>();row.fieldNames().forEachRemaining(fields::add);for(String field:fields){JsonNode child=row.get(field);if(DECIMAL_COUNTERS.contains(field)&&child.isIntegralNumber()){require(child.bigIntegerValue().signum()>=0,"public native counter cannot be negative");row.put(field,child.bigIntegerValue().toString());}else decimalCounters(child);}}
        else if(value.isArray())value.forEach(RootMilitaryControlStepRuntime::decimalCounters);
    }
    private static boolean flag(Complete frame,String name){return frame.semantic().get(name) instanceof OpportunityJson.Bool value&&value.value();}
    private static ExactRef source(Path path)throws IOException{var actual=SharedSourceFiles.observe(path);SharedSourceFiles.assertUnchanged(actual);return new ExactRef(actual.source().path(),actual.source().bytes(),actual.source().sha256());}
    private static void requireSame(ExactRef expected)throws IOException{require(source(Path.of(expected.path())).equals(expected),"configured military source changed");}
}
