package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Packet;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;
import static org.xar.ck3.control.service.root.NaturalClockOriginals.ReadArtifact;

/** One terminal timeline read and one real Close primitive. Every business leaf uses the sole M3 original codec. */
public final class RootNaturalTimeline implements RootExecutableBindings.SuccessionUiOriginProof,ActionPorts.PostconditionPort {
    public static final String CONTRACT_ID="lifecycle/current-timeline-blocker12004/v1";
    public static final String OBSERVER="xar.java.native-death-modal-close/v1";
    private static final String ADMISSION="xar.java.native-death-modal-close-admission/v1";
    private static final String POST="xar.java.native-death-modal-close-original-postqueries/v1";
    private static final int MAX=65_536;
    private static final OperationKey QUERY=new OperationKey(NativeTimelineBlocker12004.QUERY_STEP);
    private static final OperationKey CLOSE=new OperationKey(NativeTimelineBlocker12004.CLOSE_STEP);
    private static final OpportunityJson.Obj EMPTY=new OpportunityJson.Obj(java.util.Map.of());
    private static final List<ExpectedValue> VALUES=List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),
            new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false),
            new ExpectedBoolean(new FieldKey("lifecycle.death_modal_cleared"),true));
    private final RootNaturalSuccessionOriginals root;
    private final ExactRef querySource,closeSource;
    private final NativePrivateActionPermission.QualificationVerifier qualifier;
    private final ReadContract<PlanningReadReceipt> contract;
    private final RootExecutableBindings.ActionBinding action;
    private final NativeRecordedEvidenceVerifier.Binding replay;
    private final NativePrivateActionPermission permission;
    RootNaturalTimeline(RootNaturalSuccessionOriginals root,ExactRef querySource,ExactRef closeSource,NativePrivateActionPermission.QualificationVerifier qualifier) {
        this(root,querySource,closeSource,qualifier,Optional.empty());
    }
    RootNaturalTimeline(RootNaturalSuccessionOriginals root,ExactRef querySource,ExactRef closeSource,NativePrivateActionPermission.QualificationVerifier qualifier,
            Optional<NativePrivateActionPermission> originalPermission) {
        this.root=Objects.requireNonNull(root);this.querySource=Objects.requireNonNull(querySource);this.closeSource=Objects.requireNonNull(closeSource);this.qualifier=Objects.requireNonNull(qualifier);
        require(querySource.bytes()>0&&closeSource.bytes()>0,"actual C++/Java native route sources required");
        contract=new ReadContract<>(CONTRACT_ID,QUERY,Optional.empty(),"allow_private_current_timeline_blocker_query",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,querySource,request->{
                    require(request.arguments().members().isEmpty(),"original private Timeline query has zero additional arguments");root.admitTerminal(request);
                    return new NativeRequest(QUERY.value(),Optional.empty(),new RawJson(new byte[]{'{','}'}));
                },receipt->{decode(receipt);return receipt;});
        action=createActionBinding();replay=createReplayBinding();permission=Objects.requireNonNull(originalPermission).orElseGet(this::createPrivatePermission);
        require(permission.operation().equals(CLOSE)&&permission.permissionKey().equals("allow_private_death_succession_modal_continue")
                &&permission.originalProducerSource().equals(closeSource),"Close must retain its original prelaunch permission source");
    }
    public ReadContract<PlanningReadReceipt> contract() { return contract; }
    public RootExecutableBindings.ActionBinding actionBinding() {return action;}
    private RootExecutableBindings.ActionBinding createActionBinding() {
        return new RootExecutableBindings.ActionBinding(NativeEffectRegistry.Binding.existing(CLOSE,closeSource,this,this),ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,Optional.empty(),closeSource,Optional.of(this));
    }
    public NativeRecordedEvidenceVerifier.Binding replayBinding() {return replay;}
    private NativeRecordedEvidenceVerifier.Binding createReplayBinding() {
        return new NativeRecordedEvidenceVerifier.Binding(CLOSE,closeSource,(head,receipt,archive)->{
            try {require(root.borrowed().head().digest().equals(head.digest()),"Close replay lost the actual writer head");if(receipt.command().origin() instanceof CommandOrigin.Gameplay)root.pendingRuntime().verifyCloseControl(receipt,archive);else verifyControl(receipt,archive);}
            catch(IOException failure){throw new UncheckedIOException("actual terminal Close replay unavailable",failure);}
        });
    }
    public NativePrivateActionPermission privatePermission() {return permission;}
    private NativePrivateActionPermission createPrivatePermission() {
        return new NativePrivateActionPermission(CLOSE,"allow_private_death_succession_modal_continue",closeSource,
                request->{try{wire(request);}catch(IllegalArgumentException failure){throw new IOException("strict native Close request changed",failure);}},qualifier);
    }
    private static void wire(NativeRequest request) {
        require(request.step().equals(CLOSE.value())&&request.requiredCapability().isEmpty(),"private Close operation/capability drift");
        var parsed=StrictJson.object(StrictJson.parse(request.additionalFields().bytes()),Set.of("expected_date_raw","expected_played_character_id"));
        StrictJson.integer(parsed.get("expected_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE);
        NativeCharacterId.fromJson(parsed.get("expected_played_character_id"));
    }
    public ReadArtifact read(ContinuityStorePort.Session same,RootLifecycleAuthority.Lease lease,Instant deadline)throws IOException {
        lease.assertCurrent(same);var actual=lease.identity();
        var known=root.read(same,contract,new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(actual),lease.snapshot().source(),actual.sessionId(),QUERY,EMPTY,deadline));
        require(known.value().equals(known.receipt()),"Timeline original receipt changed through installed codec");
        var result=artifact(known.receipt());require(result.semantic().equals(lease.originalSemantic()),"Timeline semantic is not the actual outer Root lease");lease.assertCurrent(same);return result;
    }
    public NativeTimelineBlocker12004.Query decode(ExactRef receipt)throws IOException { return decode(root.archive(root.borrowed()).loadRead(receipt)); }
    public NativeTimelineBlocker12004.Query decode(PlanningReadReceipt receipt) {
        try {
            require(receipt.contractId().equals(CONTRACT_ID)&&receipt.request().operation().equals(QUERY)&&receipt.request().arguments().members().isEmpty(),"not the installed terminal Timeline contract");
            var same=root.borrowed();var archive=root.archive(same);
            var before=RootLifecycleGuardEvidence.replay(receipt.before().binding(),archive,same,root.core().originals());
            var after=RootLifecycleGuardEvidence.replay(receipt.after().binding(),archive,same,root.core().originals());
            require(before.identity().equals(after.identity())&&before.semantic().equals(after.semantic())
                    &&receipt.request().origin().requireLifecycleTerminal().sameGuardFrame(before.identity())
                    &&receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                    &&receipt.before().binding().authorityId().equals(receipt.after().binding().authorityId()),"Timeline crossed its actual full terminal read frame");
            var frame=RootNaturalSuccessionOriginals.frame(before.identity(),before.semantic());
            ExactRef raw=root.originalFrame(receipt.original());
            require(receipt.original().originalResultToken().isPresent()
                    &&StrictJson.parse(receipt.original().originalFrame().bytes(),NativeTimelineBlocker12004.MAX_BYTES).get("result").equals(StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes(),NativeTimelineBlocker12004.MAX_BYTES)),"Timeline original frame/result token differ");
            return NativeTimelineBlocker12004.parseQuery(receipt.original().originalFrame().bytes(),raw,
                    new NativeTimelineBlocker12004.BoundFrame(root.currentSession(before.identity(),receipt.request().source()),frame,NativeTimelineBlocker12004.Scene.fromSnapshot(OpportunityJson.toNode(before.semantic()))),receipt.requestId());
        } catch(IOException failure) {throw new UncheckedIOException(failure);}
    }
    public ReadArtifact artifact(PlanningReadReceipt receipt)throws IOException {
        var same=root.borrowed();var archive=root.archive(same);var replay=RootLifecycleGuardEvidence.replay(receipt.after().binding(),archive,same,root.core().originals());decode(receipt);
        var basis=StrictJson.parse(archive.loadMaterial(receipt.after().binding().supportingEvidence().getFirst()).bytes(),MAX);
        ExactRef semantic=ExactRef.fromJson(basis.get("semantic"));require(Arrays.equals(root.readExact(semantic),org.xar.ck3.control.application.driver.DriverJson.encode(replay.semantic())),"actual archived semantic reference changed");
        return new ReadArtifact(archive.readReferenceOf(receipt),root.originalFrame(receipt.original()),receipt.requestId(),RootNaturalSuccessionOriginals.frame(replay.identity(),replay.semantic()),semantic);
    }
    public Packet packet(ReadArtifact read) {
        try {var receipt=root.archive(root.borrowed()).loadRead(read.receipt());var query=decode(receipt);require(read.equals(artifact(receipt)),"Timeline retained own-frame artifact differs");return new Packet(read.frame(),read.requestId(),read.actualFrame(),query.binding().scene());}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public ActionCommand closeCommand(String actionId,ExactRef initialReceipt,Instant deadline)throws IOException {
        var receipt=root.archive(root.borrowed()).loadRead(initialReceipt);var original=decode(receipt);require(original.context().supportedCloseObserved(),"actual timeline does not expose a legal supported Close");
        LifecycleIdentity identity=receipt.request().origin().requireLifecycleTerminal();
        var expected=new LifecycleExpectedPostcondition(identity,receipt.request().source(),OBSERVER,LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL,VALUES);
        ObjectNode args=StrictJson.object().put("expected_date_raw",identity.frame().dateRaw()).put("expected_played_character_id",((LifecycleIdentity.Character)identity.currentPlayer()).characterId());
        return new ActionCommand(actionId,new CommandOrigin.LifecycleTerminal(identity),receipt.request().source(),identity.sessionId(),CLOSE,
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"strict Close args"),new CommandExpectation.LifecycleTerminal(expected),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
    }
    /** RootLifecycleActionGuard installs this exact callback. It queries the legal native leaf under its current lease. */
    public ExactRef verifyClose(ContinuityStorePort.Session same,ActionCommand command,RootLifecycleAuthority.Lease lease,ActionPorts.OutcomeArchive archive)throws IOException {
        require(command.operation().equals(CLOSE)&&command.lifecycleBefore().sameGuardFrame(lease.identity())&&command.source().equals(lease.snapshot().source()),"Close changed the actual Root modal origin");
        validateCommand(command);var read=read(same,lease,command.deadline());var query=decode(read.receipt());require(query.context().supportedCloseObserved(),"actual Modal.canContinue/blocks/open predicates do not authorize Close");
        ObjectNode body=StrictJson.object().put("schema",ADMISSION).put("command_body_sha256",ActionCodec.bodySha256(command));body.set("capture_document",root.currentCaptureDocument().toJson());body.set("initial_read",read.receipt().toJson());body.set("raw_query_frame",read.frame().toJson());body.set("semantic",read.semantic().toJson());body.set("source_qualification",ExactRef.optionalToJson(lease.sourceQualification().proof()));
        RawJson raw=new RawJson(StrictJson.canonical(body,MAX));ExactRef ref=archive.preserveMaterial(raw);require(raw.equals(archive.loadMaterial(ref)),"actual modal admission archive drift");lease.assertCurrent(same);return ref;
    }
    @Override public ExactRef successionUiDefinitionSource(){return closeSource;}
    @Override public void requireSuccessionOrigin(ContinuityStorePort.Session same,ActionCommand exact)throws IOException {
        root.core().writer().requireSession(same);
        if(exact.origin() instanceof CommandOrigin.Gameplay){root.pendingRuntime().requireCloseOrigin(same,exact);return;}
        validateCommand(exact);
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        try{requireSuccessionOrigin(root.borrowed(),command);if(command.origin() instanceof CommandOrigin.Gameplay)return root.pendingRuntime().prepareClose(command);}
        catch(IOException failure){throw new UncheckedIOException(failure);}
        return terminalCloseWire(command); }
    private static void validateCommand(ActionCommand command) {
        require(command.operation().equals(CLOSE)&&command.lifecycleExpected().operation()==LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL&&command.lifecycleExpected().values().equals(VALUES),"Close is only a terminal modal-control command with explicit false day/SAVE/gameplay claims");
        var identity=command.lifecycleBefore();require(identity.frame().paused()&&identity.frame().mapReady()&&identity.terminalReason()==LifecycleIdentity.TerminalReason.CHANGED&&identity.currentPlayer() instanceof LifecycleIdentity.Character player&&player.alive(),"Close requires the actual paused different living player");
        ObjectNode args=StrictJson.object(OpportunityJson.toNode(command.arguments()),Set.of("expected_date_raw","expected_played_character_id"));
        require(StrictJson.integer(args.get("expected_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)==identity.frame().dateRaw().longValueExact()
                &&NativeCharacterId.fromJson(args.get("expected_played_character_id")).asBigInteger().equals(((LifecycleIdentity.Character)identity.currentPlayer()).characterId()),"Close wire fields differ from actual terminal frame");
    }
    static NativeRequest terminalCloseWire(ActionCommand command) {
        validateCommand(command);
        var identity=command.lifecycleBefore();
        var fields=StrictJson.object().put("expected_date_raw",identity.frame().dateRaw()).put("expected_played_character_id",((LifecycleIdentity.Character)identity.currentPlayer()).characterId());
        var result=new NativeRequest(CLOSE.value(),Optional.empty(),new RawJson(StrictJson.canonical(fields)));
        wire(result);
        return result;
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        try {
            if(command.origin() instanceof CommandOrigin.Gameplay)return root.pendingRuntime().observeClose(command,attempt,dispatch);
            validateCommand(command);var same=root.borrowed();var archive=root.archive(same);var initial=admission(command,attempt.guard(),archive);
            require(attempt.preparedRequest().equals(prepare(command)),"Close actual prepared native request differs");
            if(!(dispatch instanceof NativeActionPort.AckReceived ack))return new ActionPorts.Pending("Close original result unknown; no replay",List.of(archive.preserve(dispatch)));
            Packet close=closePacket(command,attempt,ack);var parsed=NativeTimelineBlocker12004.parseClose(root.readExact(close.original()),close.original(),new NativeTimelineBlocker12004.BoundFrame(root.currentSession(command.lifecycleBefore(),command.source()),close.actualFrame(),close.actualScene()),attempt.requestId());
            if(parsed.state()!=NativeTimelineBlocker12004.CloseState.SUBMITTED_PENDING)return new ActionPorts.Pending("Close returned RED or reclaim UNKNOWN; no replay",List.of(close.original()));
            var first=decode(initial);List<PlanningReadReceipt> reads=new ArrayList<>();var lastBinding=parsed.binding();var sequence=first.sequence();var observation=first.observationRevision();
            for(int count=0;count<8;count++) {
                var next=root.terminal().current(same,command.lifecycleBefore(),command.deadline(),lease->read(same,lease,command.deadline()));
                var receipt=archive.loadRead(next.receipt());var query=decode(receipt);reads.add(receipt);
                require(query.sequence().compareTo(sequence)>0&&query.observationRevision().compareTo(observation)>0&&NativeTimelineBlocker12004.sameContinuation(lastBinding,query.binding()),"actual post-Close query regressed or repeated");sequence=query.sequence();observation=query.observationRevision();lastBinding=query.binding();
                if(NativeTimelineBlocker12004.compareClearance(first,parsed,query).state()==NativeTimelineBlocker12004.ClearanceState.CLEARED_OBSERVED) {
                    ObjectNode material=StrictJson.object().put("schema",POST);material.set("initial_read",archive.readReferenceOf(initial).toJson());material.set("close_frame",close.original().toJson());var refs=material.putArray("subsequent_reads");reads.forEach(value->refs.add(archive.readReferenceOf(value).toJson()));
                    ExactRef basis=archive.preserveMaterial(new RawJson(StrictJson.canonical(material,MAX)));LifecycleIdentity after=receipt.request().origin().requireLifecycleTerminal();
                    var result=new LifecycleControlObservation(after,command.source(),command.sessionId(),OBSERVER,VALUES,initial,receipt,List.of(basis));result.validate(command,attempt);
                    return new ActionPorts.LifecycleControlObserved(result);
                }
            }
            return new ActionPorts.Pending("eight actual Timeline postqueries did not prove clearance; Close must not repeat",reads.stream().map(archive::readReferenceOf).toList());
        } catch(IOException|IllegalArgumentException|UncheckedIOException failure) {return new ActionPorts.Pending("actual native Close remains unresolved; no replay: "+failure.getMessage(),List.of(attempt.guard().nativeEvidence()));}
    }
    private PlanningReadReceipt admission(ActionCommand command,GuardEvidence guard,ActionPorts.OutcomeArchive archive)throws IOException {
        var replay=RootLifecycleGuardEvidence.replay(guard,archive,root.borrowed(),root.core().originals());ExactRef ref=replay.closeAdmission().orElseThrow(()->new IOException("actual Close legal-modal admission absent"));
        var body=StrictJson.object(StrictJson.parse(archive.loadMaterial(ref).bytes(),MAX),Set.of("schema","command_body_sha256","capture_document","initial_read","raw_query_frame","semantic"),Set.of("source_qualification"));
        require(ADMISSION.equals(StrictJson.text(body.get("schema")))&&ActionCodec.bodySha256(command).equals(StrictJson.text(body.get("command_body_sha256"))),"Close legal admission belongs to a different original command");
        var initial=archive.loadRead(ExactRef.fromJson(body.get("initial_read")));var artifact=artifact(initial);var query=decode(initial);
        require(query.context().supportedCloseObserved()&&command.lifecycleBefore().sameGuardFrame(initial.request().origin().requireLifecycleTerminal())&&artifact.frame().equals(ExactRef.fromJson(body.get("raw_query_frame")))&&artifact.semantic().equals(ExactRef.fromJson(body.get("semantic")))&&ExactRef.optionalFromJson(body.get("source_qualification")).equals(replay.identity().evidence().completeSourceQualification()),"Close lacks the actual same-frame typed Modal.canContinue source basis");return initial;
    }
    Packet closePacket(ActionReceipt receipt) {
        try {var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();var outcome=ActionTransitions.dispatch(receipt.state()).orElseThrow();require(outcome instanceof NativeActionPort.AckReceived,"Close has no exact native original ACK/RED frame");return closePacket(receipt.command(),attempt,(NativeActionPort.AckReceived)outcome);}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private Packet closePacket(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack)throws IOException {
        require(attempt.requestId().equals(ack.requestId()),"Close request/return changed");var same=root.borrowed();var replay=RootLifecycleGuardEvidence.replay(attempt.guard(),root.archive(same),same,root.core().originals());
        return new Packet(root.originalFrame(ack),ack.requestId(),RootNaturalSuccessionOriginals.frame(replay.identity(),replay.semantic()),NativeTimelineBlocker12004.Scene.fromSnapshot(OpportunityJson.toNode(replay.semantic())));
    }
    public List<ReadArtifact> postQueries(LifecycleControlObservation observation)throws IOException {
        require(observation.supportingEvidence().size()==1,"one complete original Close postquery basis required");var archive=root.archive(root.borrowed());var body=post(observation,archive);var refs=body.get("subsequent_reads");List<ReadArtifact> reads=new ArrayList<>();for(var ref:refs)reads.add(artifact(archive.loadRead(ExactRef.fromJson(ref))));return List.copyOf(reads);
    }
    private static ObjectNode post(LifecycleControlObservation observed,ActionPorts.OutcomeArchive archive) {
        require(observed.supportingEvidence().size()==1,"one exact Close original-postquery proof required");var body=StrictJson.object(StrictJson.parse(archive.loadMaterial(observed.supportingEvidence().getFirst()).bytes(),MAX),Set.of("schema","initial_read","close_frame","subsequent_reads"));
        require(POST.equals(StrictJson.text(body.get("schema")))&&ExactRef.fromJson(body.get("initial_read")).equals(archive.readReferenceOf(observed.beforeStatus()))&&body.get("subsequent_reads").isArray()&&body.get("subsequent_reads").size()>0&&body.get("subsequent_reads").size()<=8,"strict actual bounded Close queries required");return body;
    }
    /** Cold replay reads only the archive; no Close, Native query, observation or source-acquisition call occurs here. */
    public void verifyControl(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
        require(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.LifecycleControlApplied,"no actual terminal Close settlement");
        root.requireCanonicalAttempt(receipt);
        var attempt=((ActionState.Settled)receipt.state()).attempt();var guard=RootLifecycleGuardEvidence.replay(attempt.guard(),archive,root.borrowed(),root.core().originals());
        var admission=StrictJson.parse(archive.loadMaterial(guard.closeAdmission().orElseThrow()).bytes(),MAX);ExactRef capture=ExactRef.fromJson(admission.get("capture_document"));
        root.withRetainedCapture(capture,()->{verifyControlRetained(receipt,archive);return null;});
    }
    private void verifyControlRetained(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
        var settled=(ActionState.Settled)receipt.state();var observation=((ActionState.LifecycleControlApplied)settled.settlement()).observation();observation.validate(receipt.command(),settled.attempt());
        var initial=admission(receipt.command(),settled.attempt().guard(),archive);require(initial.equals(observation.beforeStatus()),"Close settlement changed original initial query");
        var packet=closePacket(receipt);var body=post(observation,archive);require(packet.original().equals(ExactRef.fromJson(body.get("close_frame"))),"Close native original frame changed");
        var submitted=NativeTimelineBlocker12004.parseClose(root.readExact(packet.original()),packet.original(),new NativeTimelineBlocker12004.BoundFrame(root.currentSession(receipt.command().lifecycleBefore(),receipt.command().source()),packet.actualFrame(),packet.actualScene()),packet.requestId());
        var first=decode(initial);var sequence=first.sequence();var revision=first.observationRevision();var binding=submitted.binding();NativeTimelineBlocker12004.Clearance last=null;PlanningReadReceipt finalRead=null;
        for(var ref:body.get("subsequent_reads")) {var next=archive.loadRead(ExactRef.fromJson(ref));var query=decode(next);require(query.sequence().compareTo(sequence)>0&&query.observationRevision().compareTo(revision)>0&&NativeTimelineBlocker12004.sameContinuation(binding,query.binding()),"archived actual Close postquery chain repeated/regressed");sequence=query.sequence();revision=query.observationRevision();binding=query.binding();last=NativeTimelineBlocker12004.compareClearance(first,submitted,query);finalRead=next;}
        require(last!=null&&last.state()==NativeTimelineBlocker12004.ClearanceState.CLEARED_OBSERVED&&Objects.equals(finalRead,observation.independentRead())&&observation.actual().equals(VALUES),"actual native Close modal/predicates were not independently observed clear");
    }
}
