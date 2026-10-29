package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.InitialDriverBootstrap;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;

/** Real fixture requests installed in the same Root action registry. Start ACK never supplies map proof. */
public final class FixtureFrontendEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA="xar.java.fixture-frontend-independent-effect/v1";
    public static final String BASIS="xar.java.fixture-frontend-original-basis/v1";
    private final PreparedFixture fixture;
    private final FrontendRulesDefinitions definitions;
    private final PlanningReadPort reads;
    private final NativeOutcomeArchive nativeArchive;
    private final ContinuityWriter writer;
    private final InitialDriverBootstrap bootstrap;
    private final NativeSemanticEvidenceVerifier semantics;
    private final FixtureModelContract models;
    private final java.time.Clock clock;
    public FixtureFrontendEffects(PreparedFixture fixture,FrontendRulesDefinitions sameDefinitions,PlanningReadPort soleReads,
            NativeOutcomeArchive sameArchive,ContinuityWriter sameWriter,InitialDriverBootstrap sameBootstrap,NativeSemanticEvidenceVerifier sameSemantics,java.time.Clock sameClock) {
        this.fixture=Objects.requireNonNull(fixture);definitions=Objects.requireNonNull(sameDefinitions);reads=Objects.requireNonNull(soleReads);
        nativeArchive=Objects.requireNonNull(sameArchive);writer=Objects.requireNonNull(sameWriter);
        bootstrap=Objects.requireNonNull(sameBootstrap);semantics=Objects.requireNonNull(sameSemantics);
        models=new FixtureModelContract(fixture,definitions);
        clock=Objects.requireNonNull(sameClock);
        StrictJson.require(nativeArchive.writer()==writer,"fixture effects require same Root writer/archive");
    }
    public PreparedFixture fixture() { return fixture; }
    public FixtureModelContract models(){return models;}
    public List<Primitive> writes() {
        return fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?
                List.of(Primitive.SCENARIO_BOOKMARK,Primitive.SCENARIO_CHARACTER,Primitive.SCENARIO_START):List.of(Primitive.SELECT_1066,Primitive.START_BOOKMARK);
    }
    public List<RootExecutableBindings.ActionBinding> actions(ExactRef implementation,ExactRef decoder) {
        return writes().stream().map(step->new RootExecutableBindings.ActionBinding(
                new NativeEffectRegistry.Binding(step.operation(),implementation,this::prepare,this),ReadContract.GuardMode.FRONTEND_SESSION,Optional.of(step.capability()),decoder)).toList();
    }
    public List<FrontendRouteAdmission> routeAdmissions(ExactRef implementation) {
        return writes().stream().map(step->new FrontendRouteAdmission(step.operation(),Set.of(FrontendRulesData.Route.BOOKMARKS),FrontendRouteAdmission.FrameMode.MENU,implementation)).toList();
    }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(ExactRef implementation) {
        return writes().stream().map(step->new NativeRecordedEvidenceVerifier.Binding(step.operation(),implementation,(head,receipt,archive)->{
            if(start(step))verifyArchivedStart(receipt,archive);else replay(receipt,archive);
        })).toList();
    }
    public OpportunityJson.Obj arguments(FixtureFrontendProducer.Mutation mutation,FixturePlan identicalParentPlan) {
        ObjectNode n=StrictJson.object();n.set("policy_source",fixture.policySource().toJson());n.set("claim",mutation.claim().toJson());
        StrictJson.require(identicalParentPlan.policySource().equals(fixture.policySource())&&identicalParentPlan.claim().equals(mutation.claim()),"fixture child changed original parent plan");
        n.set("fixture_plan",identicalParentPlan.encode());
        n.set("before_route",mutation.route().toJson());n.set("model",mutation.model().toJson());return DriverJson.object(StrictJson.canonical(n),65536);
    }
    public FrontendExpectedPostcondition expected(FrontendIdentity actual,org.xar.ck3.control.g2.common.G2Source source,Primitive step) {
        requireStep(step);return new FrontendExpectedPostcondition(actual,source,start(step)?FixtureStartObservation.SCHEMA:SCHEMA,values(step));
    }
    private List<ExpectedValue> values(Primitive step) {
        if(start(step))return List.of(new ExpectedText(new FieldKey("status"),"independent_first_map_observed"),new ExpectedBoolean(new FieldKey("postcondition_verified"),true));
        return List.of(new ExpectedText(new FieldKey("bookmark_key"),fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?FrontendFixturePolicy.SCENARIO_TARGET.bookmarkKey():"bm_1066_rags_to_riches"),
                new ExpectedBoolean(new FieldKey("selected_character_proven"),step==Primitive.SCENARIO_CHARACTER||step==Primitive.SELECT_1066));
    }
    public NativeRequest prepare(ActionCommand command) {
        try {
            fixture.verifySources();Primitive step=step(command.operation());ActionPorts.OutcomeArchive archive=archive();
            String parentId=inputs(command,step,archive);var same=writer.borrowedSession();
            var parent=ActionChildPlanningScope.reservedParent(same,same.head(),command).orElseThrow(()->new IOException("fixture primitive has no actual canonical upfront parent reservation"));
            StrictJson.require(parent.actionId().equals(parentId),"fixture child changed its exclusive original claim parent");
            StrictJson.require(command.expectation().requireFrontend().equals(expected(command.origin().requireFrontend(),command.source(),step)),"fixture immutable expected result drifted");
            return step.emptyRequest();
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private String inputs(ActionCommand command,Primitive step,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(command.origin() instanceof CommandOrigin.Frontend&&command.origin().requireFrontend().frame() instanceof FrontendFrame.Menu,"fixture mutation requires actual frontend Menu origin");
        ObjectNode args=StrictJson.object(StrictJson.parse(OpportunityJson.encode(command.arguments())),Set.of("policy_source","claim","before_route","model","fixture_plan"));
        StrictJson.require(ExactRef.fromJson(args.get("policy_source")).equals(fixture.policySource()),"fixture command changed exact prepared policy");
        ExactRef claim=ExactRef.fromJson(args.get("claim"));RawJson claimRaw=archive.loadMaterial(claim);
        var plan=FixturePlan.decode(args.get("fixture_plan"));StrictJson.require(plan.claim().equals(claim)&&plan.policySource().equals(fixture.policySource())
                &&plan.kind().name().equals(fixture.policy().kind().name()),"fixture primitive changed its exact source-bound parent plan");
        StrictJson.require(claimRaw.bytes().length==claim.bytes()&&DriverJson.sha256(claimRaw.bytes()).equals(claim.sha256()),"fixture original exclusive claim changed");
        ObjectNode c=StrictJson.object(StrictJson.parse(claimRaw.bytes()),Set.of("phase","action_id","binding","policy_binding","policy_source"));
        StrictJson.require(StrictJson.text(c.get("phase")).equals("claimed-before-any-mutation")&&ExactRef.fromJson(c.get("policy_source")).equals(fixture.policySource())
                &&FrontendFixturePolicy.Binding.fromJson(c.get("policy_binding")).equals(fixture.binding()),"fixture claim is not its original prepared producer");
        ObjectNode binding=StrictJson.object(c.get("binding"),Set.of("bridge_pid","connection_generation"));
        var origin=command.origin().requireFrontend();
        StrictJson.require(StrictJson.integer(binding.get("bridge_pid"),1,0xffff_ffffL)==origin.bridgePid()
                &&StrictJson.integer(binding.get("connection_generation"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(origin.connectionGeneration())
                ,"fixture action crossed its exclusive original process/claim identity");
        var route=load(command,ExactRef.fromJson(args.get("before_route")),definitions.route(),archive);
        StrictJson.require(route.value().route()==FrontendRulesData.Route.BOOKMARKS,"fixture mutation lacks original Bookmarks route");
        var model=load(command,ExactRef.fromJson(args.get("model")),models.model(),archive);
        StrictJson.require(model.value().source().equals(route.value().source()),"fixture route/model crossed exact native source");
        var build=model.value().source().build();build.requireRules();
        if(fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO)StrictJson.require(build==FrontendRulesData.Build.CK3_12004,"scenario alias requires actual .4");
        if(step==Primitive.SELECT_1066)model.value().probeTarget(character(),false);
        else if(step!=Primitive.SCENARIO_BOOKMARK)model.value().selected(character(),fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO,start(step));
        return StrictJson.text(c.get("action_id"));
    }
    private String character() { return fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?FrontendFixturePolicy.SCENARIO_TARGET.characterNameKey():FrontendFixturePolicy.ROBERT_KEY; }
    private <T> PlanningReadResult.Known<T> load(ActionCommand command,ExactRef ref,ReadContract<T> contract,ActionPorts.OutcomeArchive archive) {
        var read=archive.loadRead(ref);NativeRecordedEvidenceVerifier.requireRead(read,archive);
        StrictJson.require(archive.readReferenceOf(read).equals(ref)&&read.contractId().equals(contract.contractId())&&read.request().operation().equals(contract.operation())
                &&read.request().source().equals(command.source())&&read.request().sessionId().equals(command.sessionId())
                &&read.request().origin() instanceof CommandOrigin.Frontend&&command.origin().requireFrontend().sameSession(read.request().origin().requireFrontend())
                &&read.after().binding().origin() instanceof CommandOrigin.Frontend&&command.origin().requireFrontend().sameSession(read.after().binding().origin().requireFrontend())
                &&read.after().binding().origin().requireFrontend().frame().querySequence().compareTo(command.origin().requireFrontend().frame().querySequence())<=0,
                "fixture source/model receipt crossed actual session/contract or came from a future query");
        return new PlanningReadResult.Known<>(contract.decode(read),read,ref);
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        Primitive step=step(command.operation());
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return NativeEffectRegistry.Projected.pending("fixture native result unknown; original request cannot be replayed",List.of(attempt.guard().nativeEvidence()));
        if(start(step))return observeStart(command,attempt,ack);
        java.time.Instant until=clock.instant().plusSeconds(10);if(until.isAfter(ActionObservationWindow.deadline(command)))until=ActionObservationWindow.deadline(command);
        while(true) {
            try{return observeSelection(command,attempt,ack);}
            catch(IllegalArgumentException unavailable) {
                if(!clock.instant().isBefore(until))return NativeEffectRegistry.Projected.pending("original fixture selection never published an independent selected model; no setter retry",List.of(attempt.guard().nativeEvidence()));
                try{Thread.sleep(Math.min(100,Math.max(1,java.time.Duration.between(clock.instant(),until).toMillis())));}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();return NativeEffectRegistry.Projected.pending("original fixture selected-model read interrupted; no setter retry",List.of(attempt.guard().nativeEvidence()));}
            }
        }
    }
    private NativeEffectRegistry.Projected observeSelection(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack) {
        var request=new PlanningReadRequest(attempt.guard().origin(),command.source(),command.sessionId(),models.model().operation(),new OpportunityJson.Obj(java.util.Map.of()),ActionObservationWindow.deadline(command));
        var read=reads.read(models.model(),request);
        if(!(read instanceof PlanningReadResult.Known<?> known))return NativeEffectRegistry.Projected.pending("independent fixture selected-model read unavailable; no setter retry",List.of(attempt.guard().nativeEvidence()));
        var archive=archiveUnchecked();var first=project(command,attempt,ack,known.receipt(),archive,List.of());
        ExactRef compatible=archive.preserveMaterial(first.compatibleResult().orElseThrow());
        ObjectNode basis=StrictJson.object();basis.put("schema",BASIS);basis.put("command_body_sha256",ActionCodec.bodySha256(command));basis.put("request_id",attempt.requestId());
        basis.set("after_read",archive.preserveRead(known.receipt()).toJson());basis.set("compatible_material",compatible.toJson());
        ExactRef retained=archive.preserveMaterial(new RawJson(StrictJson.canonical(basis)));
        return project(command,attempt,ack,known.receipt(),archive,List.of(retained));
    }
    private NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,PlanningReadReceipt read,ActionPorts.OutcomeArchive archive,List<ExactRef> support) {
        Primitive step=step(command.operation());StrictJson.require(!start(step),"Start ACK has no frontend/map settlement");inputs(command,step,archive);
        NativeRecordedEvidenceVerifier.requireRead(read,archive);
        StrictJson.require(read.request().operation().equals(models.model().operation())&&read.request().source().equals(command.source())
                &&read.request().sessionId().equals(command.sessionId())&&read.request().origin() instanceof CommandOrigin.Frontend
                &&command.origin().requireFrontend().sameSession(read.request().origin().requireFrontend())
                &&command.origin().requireFrontend().sameSession(read.after().binding().origin().requireFrontend())
                &&!read.requestId().equals(attempt.requestId())&&!read.after().binding().observedAt().isBefore(attempt.submittedAt())
                &&read.after().binding().origin().requireFrontend().frame().querySequence().compareTo(attempt.guard().origin().requireFrontend().frame().querySequence())>0,"fixture effect needs a distinct later actual read");
        FixtureStartSubmission.requireAck(ack.originalResultToken().orElseThrow(),step);
        models.model().decode(read).selected(character(),fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO,step==Primitive.SCENARIO_CHARACTER||step==Primitive.SELECT_1066);
        var identity=read.after().binding().origin().requireFrontend();
        var observation=new FrontendEffectObservation(identity,command.source(),command.sessionId(),SCHEMA,values(step),read.requestId(),read.after().binding().observedAt(),identity.nativeEvidence(),support);
        if(!support.isEmpty())ActionEffects.validate(command,attempt,new ActionState.FrontendApplied(observation));
        ObjectNode result=StrictJson.object();result.put("schema",SCHEMA);result.put("status","observed");result.put("postcondition_verified",true);
        result.put("operation",step.operation().value());result.put("action_request_id",attempt.requestId());result.put("independent_read_request_id",read.requestId());
        result.put("uses_ocr",false);result.put("uses_keyboard",false);result.put("uses_mouse",false);
        return new NativeEffectRegistry.Projected(new ActionPorts.FrontendObserved(observation),Optional.of(new RawJson(StrictJson.canonical(result))));
    }
    private NativeEffectRegistry.Projected observeStart(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack) {
        try {
            var archive=archive();inputs(command,step(command.operation()),archive);FixtureStartSubmission.requireAck(ack.originalResultToken().orElseThrow(),step(command.operation()));
            FixturePlan plan=FixturePlan.decode(DriverJson.toNode(command.arguments()).get("fixture_plan"));
            var staged=bootstrap.stageFixture(command,attempt,ack);staged.awaitIndependentPausedPump(64);
            var read=staged.independentRead();
            archive.preserve(read.acknowledgement());
            var observation=FixtureStartObservation.from(plan,command.origin().requireFrontend(),staged.firstMapFrame(),staged.firstMapSemantic(),
                    staged.originalHello(),staged.firstHeartbeat(),staged.lastHeartbeat(),staged.firstMapSourceQualification(),read.acknowledgement(),read.snapshotReceived());
            verifyStart(command,attempt,ack,observation,archive);
            return new NativeEffectRegistry.Projected(new ActionPorts.FixtureStartObserved(observation),Optional.of(ack.originalResultToken().orElseThrow()));
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();return NativeEffectRegistry.Projected.pending("fixture original Start first-map read interrupted; never resubmit",List.of(attempt.guard().nativeEvidence()));}
        catch(IOException|IllegalArgumentException unavailable){return NativeEffectRegistry.Projected.pending("fixture actual first-map proof unavailable: "+unavailable.getMessage(),List.of(attempt.guard().nativeEvidence()));}
    }
    public void verifyArchivedStart(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.FixtureStarted,
                "fixture archived Start needs the original physically settled first-map result");
        var settled=(ActionState.Settled)receipt.state();StrictJson.require(settled.dispatch() instanceof NativeActionPort.AckReceived,"actual original Start ACK required");
        try{verifyStart(receipt.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch(),((ActionState.FixtureStarted)settled.settlement()).observation(),archive);}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private void verifyStart(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,
            FixtureStartObservation observation,ActionPorts.OutcomeArchive archive)throws IOException {
        inputs(command,step(command.operation()),archive);observation.validate(command,attempt,ack);
        StrictJson.require(observation.fixture().policySource().equals(fixture.policySource()),"fixture first-map proof changed its exact policy");
        var same=writer.borrowedSession();writer.requireSession(same);semantics.verify(same,observation.gameplaySession(),observation.firstMap());
        byte[] nativePacket=nativeArchive.readArtifact(same,observation.firstMap().originalNativePacket(),ReadinessArchive.Role.NATIVE_PACKET.maximumBytes());
        var decoded=NativeWire.decode(nativePacket);StrictJson.require(decoded instanceof NativeWire.Snapshot,"fixture first map lacks its actual original native packet");
        var nativeFrame=(NativeWire.Snapshot)decoded;
        var actual=new NativeObservationPort.ObservedFrame(observation.independentRead().custody().orElseThrow().session(),nativeFrame.snapshotId(),nativeFrame.revision(),
                new RawJson(nativeFrame.state().value()),nativePacket,observation.firstMap().observedAt());
        NativeFreshSnapshotPort.verifyAfterOriginal(ack,observation.independentRead(),actual,observation.snapshotReceived());
        var semantic=DriverJson.object(nativeArchive.readArtifact(same,observation.firstMap().semantic(),ReadinessArchive.Role.SEMANTIC.maximumBytes()),ReadinessArchive.Role.SEMANTIC.maximumBytes());
        StrictJson.require(org.xar.ck3.control.application.driver.DriverObservationAssembler.bindingSha256(semantic).equals(observation.fullBindingSha256())
                &&new OpportunityJson.Bool(true).equals(semantic.get("map_ready"))&&new OpportunityJson.Bool(true).equals(semantic.get("paused")),"fixture first-map full Native/Driver binding or paused map differs");
        if(observation.sourceQualification().isPresent()) {
        var proof=NativeSourceProofCodec.decode(nativeArchive.readArtifact(same,observation.sourceQualification().orElseThrow(),ReadinessArchive.Role.SOURCE_PROOF.maximumBytes()));
        StrictJson.require(proof.machineId().equals(command.source().machineId())&&proof.sessionId().equals(command.sessionId())&&proof.source().equals(command.source().sourceRef()),"fixture first-map source proof crossed actual source/session");
        for(ExactRef ref:proof.completeEvidenceClosure())new org.xar.ck3.control.build.ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256()).verify();
        }
        var hello=packet(nativeArchive.readArtifact(same,observation.originalHello(),ReadinessArchive.Role.HELLO.maximumBytes()));
        StrictJson.require(new OpportunityJson.Text("hello").equals(hello.get("type"))&&new OpportunityJson.Bool(true).equals(hello.get("ck3_build_match"))
                &&OpportunityJson.integer(hello.get("pid"),"pid").equals(BigInteger.valueOf(command.origin().game().pid()))
                &&OpportunityJson.integer(hello.get("connection_generation"),"connection_generation").equals(observation.connectionGeneration()),"fixture first map HELLO crossed actual owner");
        var first=packet(nativeArchive.readArtifact(same,observation.firstHeartbeat(),ReadinessArchive.Role.HEARTBEAT.maximumBytes()));
        var last=packet(nativeArchive.readArtifact(same,observation.lastHeartbeat(),ReadinessArchive.Role.HEARTBEAT.maximumBytes()));
        verifyPump(first,last,observation.firstMap().frame().frame().identity().dateRaw());
    }
    private static OpportunityJson.Obj packet(byte[] framed) {
        StrictJson.require(framed.length>=5&&java.nio.ByteBuffer.wrap(framed,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt()==framed.length-4,"exact original LE native packet required");
        return DriverJson.object(java.util.Arrays.copyOfRange(framed,4,framed.length),DriverJson.MAX_NATIVE_BYTES);
    }
    private static void verifyPump(OpportunityJson.Obj first,OpportunityJson.Obj last,BigInteger date) {
        StrictJson.require(new OpportunityJson.Text("heartbeat").equals(first.get("type"))&&new OpportunityJson.Text("heartbeat").equals(last.get("type"))
                &&OpportunityJson.integer(last.get("sequence"),"sequence").compareTo(OpportunityJson.integer(first.get("sequence"),"sequence"))>0,"fixture requires independent later original owner heartbeat");
        var a=OpportunityJson.object(first.get("main_thread_query_mailbox_v1"),"mailbox");var b=OpportunityJson.object(last.get("main_thread_query_mailbox_v1"),"mailbox");
        for(var mailbox:List.of(a,b)) {
            for(String field:List.of("installed","ready","executor_submission_enabled","paused","stamp_read_success"))StrictJson.require(new OpportunityJson.Bool(true).equals(mailbox.get(field)),"actual fixture owner mailbox incomplete: "+field);
            StrictJson.require(new OpportunityJson.Bool(false).equals(mailbox.get("stop"))&&OpportunityJson.integer(mailbox.get("failure"),"failure").signum()==0
                    &&OpportunityJson.integer(mailbox.get("date_raw"),"date_raw").equals(date)&&OpportunityJson.integer(mailbox.get("owner_tid"),"owner_tid").signum()>0
                    &&OpportunityJson.integer(mailbox.get("owner_tid"),"owner_tid").equals(OpportunityJson.integer(mailbox.get("current_tid"),"current_tid"))
                    &&OpportunityJson.integer(mailbox.get("pump_epochs"),"pump_epochs").equals(OpportunityJson.integer(mailbox.get("owner_verified_pump_epochs"),"owner_verified_pump_epochs")),"fixture owner stamp/TID/date changed");
        }
        StrictJson.require(OpportunityJson.integer(b.get("pump_epochs"),"pump_epochs").compareTo(OpportunityJson.integer(a.get("pump_epochs"),"pump_epochs"))>0,"fixture paused owner pump did not advance");
    }
    private void replay(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(receipt.state() instanceof ActionState.Settled&&((ActionState.Settled)receipt.state()).settlement() instanceof ActionState.FrontendApplied,"fixture selection replay requires actual settled original");
        var settled=(ActionState.Settled)receipt.state();var original=((ActionState.FrontendApplied)settled.settlement()).observation();
        StrictJson.require(original.supportingEvidence().size()==1&&settled.dispatch() instanceof NativeActionPort.AckReceived,"fixture selection has no unique original ACK/read basis");
        RawJson raw=archive.loadMaterial(original.supportingEvidence().getFirst());ObjectNode b=StrictJson.object(StrictJson.parse(raw.bytes()),Set.of("schema","command_body_sha256","request_id","after_read","compatible_material"));
        StrictJson.require(StrictJson.text(b.get("schema")).equals(BASIS)&&StrictJson.text(b.get("command_body_sha256")).equals(receipt.bodySha256())
                &&StrictJson.text(b.get("request_id")).equals(settled.attempt().requestId()),"fixture archived request/body mismatch");
        var result=project(receipt.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch(),archive.loadRead(ExactRef.fromJson(b.get("after_read"))),archive,original.supportingEvidence());
        StrictJson.require(result.result() instanceof ActionPorts.FrontendObserved&&((ActionPorts.FrontendObserved)result.result()).observation().equals(original)
                &&result.compatibleResult().orElseThrow().equals(archive.loadMaterial(ExactRef.fromJson(b.get("compatible_material")))),"fixture original replay differs");
    }
    private ActionPorts.OutcomeArchive archive()throws IOException {var borrowed=writer.borrowedSession();writer.requireSession(borrowed);return nativeArchive.withSession(borrowed);}
    private ActionPorts.OutcomeArchive archiveUnchecked() {try{return archive();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    private Primitive step(OperationKey op) {return writes().stream().filter(p->p.operation().equals(op)).findFirst().orElseThrow(()->new IllegalArgumentException("fixture operation outside explicit policy"));}
    private void requireStep(Primitive step) {StrictJson.require(writes().contains(step),"fixture primitive outside explicit policy");}
    public static boolean start(Primitive p) {return p==Primitive.START_BOOKMARK||p==Primitive.SCENARIO_START;}
}
