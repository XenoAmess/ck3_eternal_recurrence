package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual same-Core structural family installation. Only the original coordinator may submit. */
public final class RootArmyStructuralStepRuntime {
    public record Sources(ExactRef actions,ExactRef codec,ExactRef effects,ExactRef runtime) {
        public Sources {for(ExactRef ref:List.of(actions,codec,effects,runtime))StrictJson.require(ref.bytes()>0,"actual structural source closure required");
            }
        public List<ExactRef> all(){return List.of(actions,codec,effects,runtime);}
    }
    public static final class Prepared {
        private final Sources sources;private final Duration timeout;private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private static final class Attempt {RootArmyStructuralStepRuntime installed;IOException failure;}
        public Prepared(Sources sources,Duration commandTimeout) {
            this.sources=Objects.requireNonNull(sources);timeout=Objects.requireNonNull(commandTimeout);
            StrictJson.require(!timeout.isNegative()&&!timeout.isZero()&&timeout.compareTo(Duration.ofHours(1))<=0,"actual finite Army input timeout required");
        }
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindCore(RootApplicationAssembly.Core same) {
            Objects.requireNonNull(same);StrictJson.require(core==null||core==same,"structural Prepared crossed Core");core=same;
        }
        public synchronized RootArmyStructuralStepRuntime install(RootRuntimeContext context)throws IOException {
            if(core==null||context.core()!=core)throw new IOException("structural install requires its completely bound actual Core");
            Attempt old=attempts.get(context);
            if(old!=null){if(old.installed!=null)return old.installed;throw new IOException("partial structural install cannot be retried",old.failure);}
            if(attempts.size()>=64)throw new IOException("finite actual structural context limit reached");
            Attempt attempt=new Attempt();attempts.put(context,attempt);
            try{attempt.installed=new RootArmyStructuralStepRuntime(context,sources,timeout);return attempt.installed;}
            catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("structural installation failed",failure);throw attempt.failure;}
        }
    }
    private record Qualified(ArmyStructuralActions.Call call,G2Source source,String sessionId) { }
    private final RootRuntimeContext context;private final Sources sources;private final Duration timeout;
    private final ArmyStructuralEffects effects;private final Preparation preparation=new Preparation();
    private final java.util.EnumMap<ArmyStructuralActions.Kind,RootExecutableBindings.Family<Qualified>> families=
            new java.util.EnumMap<>(ArmyStructuralActions.Kind.class);
    private final RootDomainInstallation installation;
    private RootArmyStructuralStepRuntime(RootRuntimeContext context,Sources sources,Duration timeout)throws IOException {
        this.context=Objects.requireNonNull(context);this.sources=Objects.requireNonNull(sources);this.timeout=timeout;
        for(Class<?> type:List.of(RootArmyStructuralStepRuntime.class,ArmyStructuralActions.class,ArmyStructuralActionCodec.class,ArmyStructuralEffects.class))
            context.game().launchPlan().sources().requireLoadedClass(type);
        effects=new ArmyStructuralEffects(()->context.adopted().observations(),context.archive(),context.frameLoader(),context.clock(),timeout);
        for(ArmyStructuralActions.Kind kind:ArmyStructuralActions.Kind.values()) {
            String capability=capability(kind);
            var family=new RootExecutableBindings.Family<>("army-structural-"+kind.name().toLowerCase(java.util.Locale.ROOT),Qualified.class,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,java.util.Optional.of(capability),sources.runtime(),sources.codec(),sources.effects(),
                    q->{StrictJson.require(q.call().kind()==kind,"structural family kind drift");return ArmyStructuralActionCodec.encode(q.call());},
                    q->q.call().operation(),q->{
                        StrictJson.require(q.call().kind()==kind&&q.source().equals(context.source())&&q.sessionId().equals(context.game().sessionId()),
                                "structural family crossed its actual source/session");
                        var live=new NativeEffectRegistry.Binding(q.call().operation(),sources.runtime(),preparation,effects);
                        return new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(live,
                                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,java.util.Optional.of(capability),sources.codec()),
                                effects.archivedVerifier(q.call().operation(),sources.effects()));
                    },operation->ArmyStructuralActions.parse(operation).filter(call->call.kind()==kind)
                            .map(call->new Qualified(call,context.source(),context.game().sessionId())));
            families.put(kind,family);
        }
        List<RootExecutableBindings.Family<?>> actual=families.values().stream().<RootExecutableBindings.Family<?>>map(value->value).toList();
        installation=new RootDomainInstallation("army-structural-original",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                actual,List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),
                actual.stream().map(family->new RootDomainInstallation.FamilyDomain(family,Domain.war)).toList(),List.of());
    }
    public static boolean accepts(OperationKey operation){return ArmyStructuralActions.parse(operation).isPresent();}
    public List<ExactRef> sources(){return sources.all();}
    public RootDomainInstallation installation(){return installation;}
    public void requireContext(RootRuntimeContext same)throws IOException {
        if(same!=context)throw new IOException("structural runtime crossed its actual installed context");
        context.requireCurrent(context.clock().instant().plus(timeout));
        for(Class<?> type:List.of(RootArmyStructuralStepRuntime.class,ArmyStructuralActions.class,ArmyStructuralActionCodec.class,ArmyStructuralEffects.class))
            context.game().launchPlan().sources().requireLoadedClass(type);
    }
    public ActionCommand prepare(PlanningRequest original,Complete frame,Known known,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Objects.requireNonNull(known);caller.requireCurrent(original);requireContext(context);context.writer().requireSession(same);
        var call=ArmyStructuralActions.parse(caller.step()).orElseThrow(()->new IllegalArgumentException("unrelated structural selector"));
        StrictJson.require(frame.identity().equals(original.before())&&frame.source().equals(original.source())
                &&frame.sessionId().equals(original.sessionId()),"structural preparation crossed actual held planning frame");
        current(same,frame.identity(),frame.source(),frame.sessionId(),original.deadline());
        try{ArmyStructuralActions.preflight(call,frame.semantic());}
        catch(ArmyStructuralActions.DriverUnavailable rejected) {
            var failure=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,rejected.getMessage(),java.util.Optional.empty());
            throw RootPublicStepFailureOriginals.recordDriverFailure(original,frame,known,same,caller,failure,java.util.Optional.empty(),java.util.Optional.empty());
        }
        if(!original.observations().actionSteps().contains(caller.step())) {
            var failure=new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                    "native DLL does not implement gameplay step "+caller.step().value(),java.util.Optional.empty());
            throw RootPublicStepFailureOriginals.recordDriverFailure(original,frame,known,same,caller,failure,java.util.Optional.empty(),java.util.Optional.empty());
        }
        String id=RootPublicStepExecution.actionId(original,caller);
        var previous=ContinuityActionJournal.lookup(same.head().state(),id,context.archive().withSession(same));
        if(previous.isPresent()) {
            ActionCommand old=previous.orElseThrow().command();
            StrictJson.require(old.operation().equals(caller.step())&&old.source().equals(original.source())&&old.sessionId().equals(original.sessionId()),
                    "original structural action identity changed");
            context.bindings().issue(families.get(call.kind()),new Qualified(call,old.source(),old.sessionId()));
            return old; // coordinator consumes the canonical original; never another native attempt
        }
        context.bindings().issue(families.get(call.kind()),new Qualified(call,frame.source(),frame.sessionId()));
        return new ActionCommand(id,frame.identity(),frame.source(),frame.sessionId(),call.operation(),DriverJson.object(ArmyStructuralActionCodec.encode(call).bytes(),DriverJson.MAX_NATIVE_BYTES),
                ArmyStructuralEffects.expected(frame.identity(),frame.source(),call),claims(call,frame.identity()),original.deadline());
    }
    private Complete current(Session same,ObservationIdentity before,G2Source source,String session,Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);
        try {
            Complete frame=context.adopted().observations().observe(deadline);
            StrictJson.require(frame.identity().equals(before)&&frame.source().equals(source)&&frame.sessionId().equals(session)
                    &&new Bool(true).equals(frame.semantic().get("paused"))&&new Bool(true).equals(frame.semantic().get("map_ready")),
                    "structural actual frame is stale or not a paused ready map");
            return frame;
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("structural preparation interrupted; no dispatch",interrupted);}
    }
    private final class Preparation implements ActionPorts.PreparationPort {
        @Override public NativeRequest prepare(ActionCommand command){throw new IllegalStateException("structural preparation requires original writer Session");}
        @Override public NativeRequest prepare(ActionCommand command,String requestId){throw new IllegalStateException("structural preparation requires original writer Session");}
        @Override public NativeRequest prepare(Session same,ActionCommand command,String requestId) {
            try {
                StrictJson.text(requestId);context.writer().requireSession(same);
                var call=ArmyStructuralActionCodec.decode(new RawJson(DriverJson.encode(command.arguments())));
                Complete actual=current(same,command.before(),command.source(),command.sessionId(),command.deadline());
                ArmyStructuralActions.preflight(call,actual.semantic());
                StrictJson.require(command.operation().equals(call.operation())&&command.claims().equals(claims(call,command.before()))
                        &&command.expected().equals(ArmyStructuralEffects.expected(command.before(),command.source(),call)),
                        "structural typed command/claims/postcondition drift");
                return ArmyStructuralActionCodec.request(call);
            }catch(IOException unavailable){throw new java.io.UncheckedIOException("actual structural preparation unavailable",unavailable);}
        }
    }
    public RawJson present(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        requireContext(context);context.writer().requireSession(same);
        StrictJson.require(receipt.command().operation().equals(caller.step())
                &&ContinuityActionJournal.lookup(same.head().state(),receipt.command().actionId(),archive).filter(receipt::equals).isPresent(),
                "structural original result lacks its canonical same-writer receipt");
        var call=ArmyStructuralActionCodec.decode(new RawJson(DriverJson.encode(receipt.command().arguments())));
        var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->bridge("structural action has no original native attempt"));
        var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow(()->bridge("structural outcome unknown; never retry"));
        if(!(dispatch instanceof NativeActionPort.AckReceived ack))throw bridge("structural native result unknown; no replay");
        Obj request=ArmyStructuralActionCodec.outbound(receipt.command(),attempt,ack,archive);
        Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
        ArmyStructuralEffects.requireBefore(receipt.command(),before);RawJson result;
        try {
        if(!ack.nativeOk()) {
            Obj response=org.xar.ck3.control.application.driver.DriverJson.object(ack.originalFrame().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            String nativeError=response.get("error") instanceof Text text?text.value():"unknown error";
            if(!(call instanceof ArmyStructuralActions.Halt halt)||!nativeError.equals("CK3 halt-army command validation failed")
                    ||!ArmyStructuralActions.matchesHaltRefusal(halt,before.semantic(),request,response,attempt.requestId())) {
                var failure=new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,
                        "native gameplay step failed: "+nativeError,java.util.Optional.of(archive.referenceOf(ack)));
                throw RootPublicStepFailureOriginals.recordActionDriverFailure(receipt,archive,same,caller,failure,java.util.Optional.empty(),java.util.Optional.empty());
            }
            Complete after;
            try{after=context.adopted().observations().observe(ActionObservationWindow.deadline(receipt.command()));}
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("halt rejection route observation interrupted",interrupted);}
            ArmyStructuralEffects.requireScope(before,after);
            StrictJson.require(!after.observedAt().isBefore(attempt.submittedAt()),"halt rejection has no fresh original route observation");
            result=ArmyStructuralActions.haltDeferred(halt,before.semantic(),after.semantic(),request,response,attempt.requestId());
        } else {
            if(ack.originalResultToken().isEmpty())throw bridge("original structural native result payload unavailable");
            if(call instanceof ArmyStructuralActions.Halt)
                result=ArmyStructuralActions.format(call,before.semantic(),before.semantic(),ack.originalResultToken().orElseThrow());
            else {
                var applied=NativeEffectEvidence.loadIfPresent(receipt,archive,context.frameLoader());
                if(applied.isPresent())result=ArmyStructuralActions.format(call,applied.orElseThrow().frames().before().semantic(),
                        applied.orElseThrow().frames().after().semantic(),ack.originalResultToken().orElseThrow());
                else result=ArmyStructuralEffects.pendingMaterial(receipt,archive,context.frameLoader())
                        .orElseThrow(()->bridge("original structural submitted observation unavailable; never replay"));
            }
        }
        } catch(ArmyStructuralActions.DriverUnavailable rejected) {
            // Preserve original date-format and exact stock-refusal route-readback faults.
            // Preserve the canonical receipt and failure; this grants no retry or Applied.
            var failure=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,rejected.getMessage(),java.util.Optional.empty());
            throw RootPublicStepFailureOriginals.recordActionDriverFailure(receipt,archive,same,caller,failure,java.util.Optional.empty(),java.util.Optional.empty());
        }
        return ArmyPublicWire.encodeExactSourceBound(org.xar.ck3.control.application.driver.DriverJson.object(result.bytes(),
                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES),
                new ArmyTypes.Context(receipt.command().before(),receipt.command().source(),receipt.command().sessionId(),receipt.command().deadline()));
    }
    private static Claims claims(ArmyStructuralActions.Call call,ObservationIdentity before) {
        var armies=new java.util.HashSet<BigInteger>();armies.add(BigInteger.valueOf(call.source().value()));
        if(call instanceof ArmyStructuralActions.Merge merge)armies.add(BigInteger.valueOf(merge.destination().value()));
        var scope=StrictJson.object().put("player",before.frame().identity().player()).put("episode_run_id",before.frame().episodeRunId());
        String commitment="army-scope:"+org.xar.ck3.control.application.driver.DriverJson.sha256(StrictJson.canonical(scope))+":army:"+call.source().value();
        return new Claims(Set.copyOf(armies),Set.of(),Set.of(),Set.of(commitment));
    }
    private static String capability(ArmyStructuralActions.Kind kind) {
        return switch(kind){case HALT->"game.command.halt-army-N";case SPLIT_HALF->"game.command.split-army-half-N";case MERGE->"game.command.merge-armies-N-with-N";};
    }
    private static PublicServiceFailure bridge(String message){return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,message,java.util.Optional.empty());}
}

