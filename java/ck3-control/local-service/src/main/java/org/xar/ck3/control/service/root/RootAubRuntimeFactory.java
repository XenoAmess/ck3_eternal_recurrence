package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubBusinessStateRead;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One per-Game AUB registration and its sole-coordinator action bindings. No parallel claim journal. */
public final class RootAubRuntimeFactory {
    private RootAubRuntimeFactory() { }
    /** Original producer fault before any AUB read, once-claim or submission.
     * This immutable diagnostic grants no current-frame, Native, action or retry authority. */
    public static final class PreSubmissionRevisionMismatch extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final Mutation mutation;
        private final BigInteger expectedRevision;
        private final BigInteger actualRevision;
        private PreSubmissionRevisionMismatch(Mutation mutation,BigInteger expectedRevision,BigInteger actualRevision){
            super(mutation instanceof Select?"AUB select public revision changed":"AUB Confirm public revision changed");
            this.mutation=mutation;this.expectedRevision=expectedRevision;this.actualRevision=actualRevision;
        }
        public Mutation mutation(){return mutation;}
        public BigInteger expectedRevision(){return expectedRevision;}
        public BigInteger actualRevision(){return actualRevision;}
    }
    /** Pure original revision check, shared with the actual prepare branch. DATA alone grants no
     * scope or submission qualification; Runtime still validates its current Root/writer/frame first. */
    public static void requireExpectedPublicRevision(Mutation mutation,Optional<BigInteger> expectedRevision,BigInteger actualRevision){
        Objects.requireNonNull(mutation);Objects.requireNonNull(expectedRevision);Objects.requireNonNull(actualRevision);
        StrictJson.require(actualRevision.signum()>=0&&actualRevision.compareTo(NativeWire.UINT64_MAX)<=0,"actual AUB public revision is outside its existing uint64 contract");
        expectedRevision.ifPresent(revision->{
            StrictJson.require(revision.signum()>=0&&revision.compareTo(NativeWire.UINT64_MAX)<=0,"expected AUB public revision is outside its existing uint64 contract");
            if(!revision.equals(actualRevision))throw new PreSubmissionRevisionMismatch(mutation,revision,actualRevision);
        });
    }
    public record Sources(AubOperations.Sources nativeSources, ExactRef preparationAndReplay, List<ExactRef> producerClosure) {
        public Sources {
            Objects.requireNonNull(nativeSources);Objects.requireNonNull(preparationAndReplay);producerClosure=List.copyOf(producerClosure);
            StrictJson.require(preparationAndReplay.bytes()>0&&!producerClosure.isEmpty()&&producerClosure.size()<=32&&producerClosure.stream().allMatch(ref->ref.bytes()>0),"complete exact native AUB producer closure required");
        }
        List<ExactRef> refs(){var refs=new ArrayList<>(nativeSources.refs());refs.add(preparationAndReplay);refs.addAll(producerClosure);return List.copyOf(refs);}
    }
    public record Installed(Runtime runtime, RootDomainInstallation installation) {
        public Installed { Objects.requireNonNull(runtime);Objects.requireNonNull(installation); }
        public AubOperations.Registration registration(){return runtime.registration();}
    }
    public static final class Prepared {
        private final Sources sources;
        private RootApplicationAssembly.Core owner;
        private final IdentityHashMap<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        /** Before adoption: construct exact definitions only. No query, collector or current catalog is consulted. */
        public synchronized Installed install(RootRuntimeContext context)throws IOException {
            Objects.requireNonNull(context);if(owner==null)owner=context.core();StrictJson.require(owner==context.core(),"AUB Prepared belongs to one original Core");
            Installed old=installed.get(context);if(old!=null)return old;
            List<SharedSourceFiles.Witness> witnesses=witness(sources.refs());
            Runtime runtime=new Runtime(context,sources);Installed actual=new Installed(runtime,runtime.installation());
            for(var pin:witnesses)SharedSourceFiles.assertUnchanged(pin);installed.put(context,actual);return actual;
        }
    }
    private record CommandData(Mutation mutation, BigInteger generation, ExactRef optionsBefore, Optional<ExactRef> businessBefore) { }
    public static final class Runtime {
        private final RootRuntimeContext context;
        private final Sources sources;
        private final AubOperations.Registration registration;
        private final RootDomainInstallation installation;
        private Runtime(RootRuntimeContext context,Sources sources)throws IOException {
            this.context=context;this.sources=sources;
            registration=new AubOperations.Registration(context.transport(),context.archive(),sources.nativeSources());
            var select=action(AubOperations.SELECT);var confirm=action(AubOperations.CONFIRM);
            installation=new RootDomainInstallation("aub-original-exact-12003/v1",List.of(),List.of(
                    new RootReadContractCatalog.InstalledRead(registration.business().contract(),sources.nativeSources().decoder()),
                    new RootReadContractCatalog.InstalledRead(registration.options(),sources.nativeSources().decoder())),List.of(),List.of(select,confirm),List.of(),
                    List.of(recorded(AubOperations.SELECT),recorded(AubOperations.CONFIRM)),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public AubOperations.Registration registration(){return registration;}
        public RootDomainInstallation installation(){return installation;}
        public RootExecutableBindings.ActionBinding selectAction(){return installation.actions().get(0);}
        public RootExecutableBindings.ActionBinding confirmAction(){return installation.actions().get(1);}
        public void requireContext(RootRuntimeContext same){StrictJson.require(context==Objects.requireNonNull(same),"AUB control classification requires its identical per-Game context");}
        public void requireOwner(RootApplicationSession current){StrictJson.require(context.actions()==Objects.requireNonNull(current),"AUB wrapper must resolve the actual current per-Game runtime");}
        /** Called inside Root's actual currentOwned writer/frame scope; duplicate claims allocate no new command. */
        public ActionCommand prepare(ContinuityStorePort.Session same,Complete frame,Mutation mutation,Optional<BigInteger> expectedRevision,Instant deadline)throws IOException {
            context.requireCurrent(deadline);context.writer().requireSession(same);requireFrame(frame);Objects.requireNonNull(mutation);Objects.requireNonNull(expectedRevision);
            requireExpectedPublicRevision(mutation,expectedRevision,frame.identity().frame().revision());
            var archive=context.archive().withSession(same);String id=stableActionId(frame.identity(),mutation);
            Optional<ActionReceipt> original=ContinuityActionJournal.lookup(same.head().state(),id,archive);
            if(original.isPresent())throw new IOException("original AUB once-claim already exists ("+id+", "+original.orElseThrow().state().getClass().getSimpleName()+"); no mutation retry; reconcile original canonical action only");
            // Queries precede INTENT, as in the original producer. The coordinator durably records INTENT before its only write.
            PlanningReadResult.Known<Options> selected=known(read(same,registration.options(),frame,deadline));
            StrictJson.require(selected.value().policy().selected().equals(Optional.of(mutation.expected())),"actual AUB selected policy changed before mutation");
            // Validate the same exact public projection before any durable intent/write.
            AubOperations.publicOptions(selected.value());
            ExactRef selectedRef=archive.readReferenceOf(selected.receipt());Optional<ExactRef> disabledRef=Optional.empty();
            if(mutation instanceof Confirm) {
                PlanningReadResult.Known<AubBusinessStateRead.State> disabled=known(read(same,registration.business().contract(),frame,deadline));
                StrictJson.require(!disabled.value().flags().getFirst().present()&&disabled.value().detail().effectivelyVisible(),"AUB Confirm requires actual disabled visible detail");
                AubBusinessStateRead.normalizedForPublic(disabled.value());
                disabledRef=Optional.of(archive.readReferenceOf(disabled.receipt()));
            }
            ObjectNode args=StrictJson.object();args.put("schema","xar.java.aub-original-command/v1");args.put("expected_selected_key",mutation.expected().wire());
            if(mutation instanceof Select select)args.put("desired_key",select.desired().wire());
            args.put("connection_generation",frame.connectionGeneration().toString());args.set("options_before",selectedRef.toJson());
            if(disabledRef.isPresent())args.set("business_before",disabledRef.orElseThrow().toJson());
            var expected=new ExpectedPostcondition(1,frame.identity(),frame.source(),AubOperations.OBSERVER,AubOperations.expected(mutation));
            var claims=new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("aub-original:"+frame.identity().frame().episodeRunId()));
            return new ActionCommand(id,frame.identity(),frame.source(),frame.sessionId(),new OperationKey(mutation.step()),
                    OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"original AUB action arguments"),expected,claims,deadline);
        }
        private RootExecutableBindings.ActionBinding action(String step) {
            var effect=new NativeEffectRegistry.Binding(new OperationKey(step),sources.preparationAndReplay(),command->{
                try {
                    var same=context.borrowedSession();context.writer().requireSession(same);requireCommand(command);
                    CommandData data=data(command);before(command,data,context.archive().withSession(same),Optional.empty(),Optional.empty());
                    List<SharedSourceFiles.Witness> pins=witness(sources.refs());NativeRequest actual=registration.prepare(command,data.mutation(),data.generation());
                    for(var pin:pins)SharedSourceFiles.assertUnchanged(pin);return actual;
                } catch(IOException failure){throw new UncheckedIOException("actual AUB source/quote preparation unavailable",failure);}
            },this::observe);
            return new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(AubOperations.capability(step)),sources.nativeSources().decoder());
        }
        private NativeRecordedEvidenceVerifier.Binding recorded(String step) {
            return new NativeRecordedEvidenceVerifier.Binding(new OperationKey(step),sources.preparationAndReplay(),(head,receipt,archive)->{
                StrictJson.require(receipt.state() instanceof ActionState.Settled,"AUB original settlement required");var settled=(ActionState.Settled)receipt.state();
                StrictJson.require(settled.settlement() instanceof ActionState.ControlApplied,"AUB cannot claim ordinary gameplay, advance or SAVE settlement");
                var control=(ActionState.ControlApplied)settled.settlement();CommandData data=data(receipt.command());
                replay(receipt.command(),settled.attempt(),settled.dispatch(),control,data,archive);
            });
        }
        private NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
            if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return NativeEffectRegistry.Projected.pending("AUB original dispatch is not a successful ACK; UNKNOWN cannot be retried",List.of(attempt.guard().nativeEvidence()));
            try {
                requireCommand(command);CommandData data=data(command);validateAck(command,attempt,ack,data);
                return context.withSession(same->{
                    var identity=new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());
                    return context.collector().currentOwned(same,identity,ActionObservationWindow.deadline(command),lease->{
                        Complete fresh=lease.frame();requireFrame(fresh);samePausedFrame(command.before(),fresh.identity());
                        PlanningReadReceipt independent;
                        if(data.mutation() instanceof Select)independent=known(read(same,registration.options(),fresh,ActionObservationWindow.deadline(command))).receipt();
                        else independent=known(read(same,registration.business().contract(),fresh,ActionObservationWindow.deadline(command))).receipt();
                        var actual=actual(data.mutation(),independent);var control=new ActionState.ControlApplied(independent,AubOperations.OBSERVER,actual);
                        ActionEffects.validate(command,attempt,ack,control);replay(command,attempt,ack,control,data,context.archive().withSession(same));
                        return new NativeEffectRegistry.Projected(new ActionPorts.ControlObserved(control),Optional.of(compatible(command,attempt,ack,control,data)));
                    });
                });
            }catch(IOException|IllegalArgumentException|IllegalStateException failure){return NativeEffectRegistry.Projected.pending("AUB independent result unavailable; original once-claim remains consumed: "+failure.getMessage(),List.of(attempt.guard().nativeEvidence()));}
        }
        /** Original postcondition only. No new Native query, now(), writer or current Game is used in replay. */
        private void replay(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,ActionState.ControlApplied control,CommandData data,ActionPorts.OutcomeArchive archive) {
            try {
                StrictJson.require(dispatch instanceof NativeActionPort.AckReceived ack&&ack.nativeOk(),"AUB settlement needs its original successful ACK");var ack=(NativeActionPort.AckReceived)dispatch;
                validateAck(command,attempt,ack,data);before(command,data,archive,Optional.of(attempt),Optional.of(ack));
                NativeRecordedEvidenceVerifier.requireRead(control.read(),archive);NativeRequestChronology.requireSampledAfter(control.read(),attempt,ack);
                requireRead(command,control.read());StrictJson.require(control.supportingReads().isEmpty(),"AUB has one explicit independent later query");
                var values=actual(data.mutation(),control.read());StrictJson.require(control.observerSchema().equals(AubOperations.OBSERVER)&&control.actual().equals(values),"AUB archived independent policy/flags differ");
                StrictJson.require(command.actionId().equals(stableActionId(command.before(),data.mutation())),"AUB canonical once-claim identity changed");
                ActionEffects.validate(command,attempt,ack,control);
            }catch(IOException failure){throw new UncheckedIOException("actual archived AUB proof unavailable",failure);}
        }
        private void before(ActionCommand command,CommandData data,ActionPorts.OutcomeArchive archive,Optional<ActionState.Attempt> attempt,Optional<NativeActionPort.AckReceived> ack)throws IOException {
            PlanningReadReceipt selected=archive.loadRead(data.optionsBefore());StrictJson.require(archive.readReferenceOf(selected).equals(data.optionsBefore()),"AUB original quote archive changed");
            NativeRecordedEvidenceVerifier.requireRead(selected,archive);requireRead(command,selected);Options options=registration.decodeOptions(selected);
            StrictJson.require(options.policy().selected().equals(Optional.of(data.mutation().expected()))&&options.connectionGeneration().equals(data.generation()),"AUB original selected policy/generation differs from intent");
            if(attempt.isPresent())NativeRequestChronology.requireBeforeSubmission(selected,attempt.orElseThrow(),ack.orElseThrow());
            if(data.mutation() instanceof Confirm) {
                ExactRef ref=data.businessBefore().orElseThrow();PlanningReadReceipt disabled=archive.loadRead(ref);StrictJson.require(archive.readReferenceOf(disabled).equals(ref),"AUB original business quote archive changed");
                NativeRecordedEvidenceVerifier.requireRead(disabled,archive);requireRead(command,disabled);var state=registration.decodeBusiness(disabled);
                StrictJson.require(!state.flags().getFirst().present()&&state.detail().effectivelyVisible()&&state.connectionGeneration().equals(data.generation()),"AUB original Confirm was not disabled visible detail in the actual connection");
                if(attempt.isPresent())NativeRequestChronology.requireBeforeSubmission(disabled,attempt.orElseThrow(),ack.orElseThrow());
            }
        }
        private void validateAck(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,CommandData data)throws IOException {
            StrictJson.require(attempt.guard().connectionGeneration().equals(data.generation()),"AUB attempt changed actual quoted connection generation");
            ack.custody().orElseThrow(()->new IllegalArgumentException("AUB original dispatch custody absent")).verify(ack,attempt.guard());
            var frame=NativeWire.decode(ack.originalPacket());StrictJson.require(frame instanceof NativeWire.CommandResult,"AUB original ACK packet required");var result=(NativeWire.CommandResult)frame;
            RawJson token=ack.originalResultToken().orElseThrow();StrictJson.require(result.requestId().equals(attempt.requestId())&&result.nativeOk()&&java.util.Arrays.equals(result.payload().value(),ack.originalFrame().bytes())&&result.result().presence()==NativeWire.Presence.VALUE
                    &&java.util.Arrays.equals(result.result().token().orElseThrow().value(),token.bytes()),"AUB original ACK token/request differs");
            var outgoing=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
            StrictJson.require(outgoing.requestId().equals(attempt.requestId())&&outgoing.step().equals(data.mutation().step())&&outgoing.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision())),"AUB actual outgoing operation/revision differs");
            ObjectNode fields=NativeWire.object(NativeWire.parse(outgoing.normalizedAdditionalFields().value()));
            var wanted=StrictJson.object();wanted.put("expected_player_character_id",command.before().frame().identity().player());wanted.put("expected_game_pid",command.before().game().pid());wanted.put("expected_connection_generation",data.generation());wanted.put("expected_selected_key",data.mutation().expected().wire());
            if(data.mutation() instanceof Select select)wanted.put("desired_key",select.desired().wire());StrictJson.require(fields.equals(NativeWire.parse(StrictJson.canonical(wanted))),"AUB actual outgoing semantic request changed");
            NativeMutation decoded=AubOperations.nativeMutation(token,data.mutation(),command.before(),data.generation());
            // Original Confirm may report verification_pending while a later independent flag census proves its effect.
            // The select contract itself requires its exact same-call source transition; neither branch retries a write.
            StrictJson.require(!(data.mutation() instanceof Select)||decoded.nativeVerified(),"AUB source selection result unresolved; no success or retry");
        }
        private List<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue> actual(Mutation mutation,PlanningReadReceipt independent) {
            return mutation instanceof Select?AubOperations.actual(mutation,Optional.of(registration.decodeOptions(independent).policy()),Optional.empty()):AubOperations.actual(mutation,Optional.empty(),Optional.of(registration.decodeBusiness(independent)));
        }
        public RawJson result(ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws IOException {
            if(!(actual.state() instanceof ActionState.Settled settled)||!(settled.settlement() instanceof ActionState.ControlApplied control))throw new IOException("AUB original mutation unresolved; retain "+actual.command().actionId()+" and do not retry");
            CommandData data=data(actual.command());replay(actual.command(),settled.attempt(),settled.dispatch(),control,data,archive);
            return compatible(actual.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch(),control,data);
        }
        private RawJson compatible(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,ActionState.ControlApplied control,CommandData data)throws IOException {
            RawJson original=ack.originalResultToken().orElseThrow();
            if(data.mutation() instanceof Select select)return AubPublicCodec.select(select,original,command.before(),data.generation(),
                    registration.decodeOptions(control.read()),attempt.requestId(),command.actionId());
            return AubPublicCodec.confirm((Confirm)data.mutation(),original,command.before(),data.generation(),
                    registration.decodeBusiness(control.read()),attempt.requestId(),command.actionId());
        }
        private void requireCommand(ActionCommand command){StrictJson.require(command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId())&&command.before().game().equals(context.game().generation())&&command.before().machineId().equals(context.game().machineId())
                &&command.actionId().equals(stableActionId(command.before(),data(command).mutation())),"AUB action crossed actual per-Game source/session or bypassed its original semantic once-claim");}
        private void requireFrame(Complete frame){StrictJson.require(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())&&frame.identity().game().equals(context.game().generation())&&frame.identity().machineId().equals(context.game().machineId()),"AUB observation crossed actual per-Game source/session");}
        private <T> PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> contract,Complete frame,Instant deadline){return context.reads().read(same,contract,new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),deadline));}
    }
    public static String stableActionId(ObservationIdentity before,Mutation mutation) {
        ObjectNode identity=StrictJson.object();identity.put("game_pid",before.game().pid());identity.put("episode_run_id",before.frame().episodeRunId());identity.put("actor_id",before.frame().identity().player());
        if(mutation instanceof Select select){identity.put("expected_selected_key",select.expected().wire());identity.put("desired_key",select.desired().wire());}
        else identity.put("decision_key","enable_auto_build");
        return (mutation instanceof Select?"aub-select:":"aub-confirm:")+ActionCodec.sha256(StrictJson.canonical(identity));
    }
    private static CommandData data(ActionCommand command) {
        try {
            boolean select=command.operation().value().equals(AubOperations.SELECT);
            ObjectNode row=StrictJson.object(OpportunityJson.toNode(command.arguments()),select?Set.of("schema","expected_selected_key","desired_key","connection_generation","options_before"):Set.of("schema","expected_selected_key","connection_generation","options_before","business_before"));
            StrictJson.require(StrictJson.text(row.get("schema")).equals("xar.java.aub-original-command/v1"),"original AUB command schema required");
            PolicyKey expected=PolicyKey.parse(StrictJson.text(row.get("expected_selected_key")));Mutation mutation=select?new Select(expected,PolicyKey.parse(StrictJson.text(row.get("desired_key")))):new Confirm(expected);
            StrictJson.require(command.operation().value().equals(mutation.step()),"original fixed AUB mutation required");String raw=StrictJson.text(row.get("connection_generation"));
            StrictJson.require(raw.matches("[1-9][0-9]{0,19}"),"canonical decimal AUB generation required");BigInteger generation=new BigInteger(raw);StrictJson.require(generation.compareTo(NativeWire.UINT64_MAX)<=0,"AUB generation outside uint64");
            return new CommandData(mutation,generation,ExactRef.fromJson(row.get("options_before")),select?Optional.empty():Optional.of(ExactRef.fromJson(row.get("business_before"))));
        }catch(RuntimeException invalid){throw new IllegalArgumentException("malformed original AUB command",invalid);}
    }
    private static void requireRead(ActionCommand command,PlanningReadReceipt read) {
        StrictJson.require(read.request().source().equals(command.source())&&read.request().sessionId().equals(command.sessionId()),"AUB query changed original source/session");samePausedFrame(command.before(),read.request().before());samePausedFrame(command.before(),read.before().binding().observed());samePausedFrame(command.before(),read.after().binding().observed());
    }
    private static void samePausedFrame(ObservationIdentity before,ObservationIdentity actual) {
        StrictJson.require(before.machineId().equals(actual.machineId())&&before.game().equals(actual.game())&&before.frame().episodeRunId().equals(actual.frame().episodeRunId())&&before.frame().identity().player().equals(actual.frame().identity().player())
                &&before.frame().identity().dateRaw().equals(actual.frame().identity().dateRaw())&&before.frame().identity().nativeRevision().equals(actual.frame().identity().nativeRevision())&&before.frame().revision().equals(actual.frame().revision()),"AUB original same paused native/public frame drift");
    }
    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> read)throws IOException {if(read instanceof PlanningReadResult.Known<T> value)return value;throw new IOException("actual AUB independent query unavailable: "+read);}
    private static List<SharedSourceFiles.Witness> witness(List<ExactRef> refs)throws IOException {var pins=new ArrayList<SharedSourceFiles.Witness>();for(ExactRef ref:refs){var pin=SharedSourceFiles.observe(Path.of(ref.path()));StrictJson.require(pin.source().bytes()==ref.bytes()&&pin.source().sha256().equals(ref.sha256()),"AUB complete producer/consumer source closure changed");pins.add(pin);}return List.copyOf(pins);}
}
