package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.service.root.RootMenuSession;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.require;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.*;

/** Real Start submission, independent first SEM/root/pump projection, and identical archived replay. */
public final class GameplayStartEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA=FrontendGameplayExpectedPostcondition.SCHEMA;
    public static final String BASIS="xar.java.frontend-start-original-basis/v1";
    public record Arguments(ExactRef beforeRoute,ExactRef selectedModel,String characterNameKey) {
        public Arguments { Objects.requireNonNull(beforeRoute);Objects.requireNonNull(selectedModel);StrictJson.text(characterNameKey); }
        public Obj encode() {
            ObjectNode row=StrictJson.object();row.set("before_route",beforeRoute.toJson());row.set("selected_model",selectedModel.toJson());row.put("character_name_key",characterNameKey);
            return DriverJson.object(ContinuityJson.canonical(row),65536);
        }
        public static Arguments decode(Obj value) {
            ObjectNode row=StrictJson.object(ContinuityJson.parseObject(OpportunityJson.encode(value),65536),Set.of("before_route","selected_model","character_name_key"));
            return new Arguments(ExactRef.fromJson(row.get("before_route")),ExactRef.fromJson(row.get("selected_model")),StrictJson.text(row.get("character_name_key")));
        }
    }
    private record Selection(ObservedRoute route,Candidate candidate) { }
    private final FrontendRulesDefinitions definitions;
    private final ReadContract<?> campaignRoot;
    private final InitialDriverBootstrap bootstrap;
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive nativeArchive;
    private final NativeSemanticEvidenceVerifier semantics;
    private RootMenuSession menu;
    private FrontendStartRootQueries rootQueries;
    public GameplayStartEffects(FrontendRulesDefinitions definitions,ReadContract<?> actualCampaignRoot,
            InitialDriverBootstrap bootstrap,ContinuityWriter writer,NativeOutcomeArchive archive,NativeSemanticEvidenceVerifier semantics) {
        this.definitions=Objects.requireNonNull(definitions);campaignRoot=Objects.requireNonNull(actualCampaignRoot);
        this.bootstrap=Objects.requireNonNull(bootstrap);this.writer=Objects.requireNonNull(writer);nativeArchive=Objects.requireNonNull(archive);this.semantics=Objects.requireNonNull(semantics);
        require(archive.writer()==writer && campaignRoot.operation().equals(GameplayEntryRoot.OPERATION)
                && campaignRoot.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,"same writer/archive and real root contract required");
    }
    public synchronized void bindMenu(RootMenuSession actual) {
        require(menu==null,"Start already belongs to its actual Root menu");menu=Objects.requireNonNull(actual);
    }
    public synchronized void bindRootQueries(FrontendStartRootQueries actual)throws IOException {
        Objects.requireNonNull(actual);actual.requireOwner(writer,nativeArchive,campaignRoot);
        if(rootQueries!=null)throw new IOException("same actual Start producer cannot replace its sole campaign-root query custody");rootQueries=actual;
    }
    public synchronized FrontendStartRootQueries rootQueries()throws IOException {
        if(rootQueries==null)throw new IOException("actual Start campaign-root query custody is not installed");return rootQueries;
    }
    public List<NativeEffectRegistry.Binding> bindings(ExactRef actualImplementation) {
        return List.of(new NativeEffectRegistry.Binding(Primitive.START_BOOKMARK.operation(),actualImplementation,this::prepare,this));
    }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(ExactRef actualImplementation) {
        return List.of(new NativeRecordedEvidenceVerifier.Binding(Primitive.START_BOOKMARK.operation(),actualImplementation,(head,receipt,archive)->verifyArchived(receipt,archive)));
    }
    public static List<ExpectedValue> values(Candidate candidate) {
        return List.of(new ExpectedText(new FieldKey("selected_bookmark_key"),candidate.bookmarkKey()),
                new ExpectedText(new FieldKey("selected_character_name_key"),candidate.characterNameKey()),
                new ExpectedInteger(new FieldKey("date_raw"),BigInteger.valueOf(candidate.dateRaw())),
                new ExpectedBoolean(new FieldKey("map_ready"),true),new ExpectedBoolean(new FieldKey("paused"),true),
                new ExpectedText(new FieldKey("government_key"),"feudal_government"));
    }
    public FrontendGameplayExpectedPostcondition expected(FrontendIdentity origin,org.xar.ck3.control.g2.common.G2Source source,Candidate candidate) {
        return new FrontendGameplayExpectedPostcondition(origin,source,SCHEMA,candidate.bookmarkKey(),candidate.characterNameKey(),candidate.dateRaw(),values(candidate));
    }
    public NativeRequest prepare(ActionCommand command) {
        require(command.operation().equals(Primitive.START_BOOKMARK.operation()) && command.origin() instanceof CommandOrigin.Frontend
                && command.origin().requireFrontend().frame() instanceof FrontendFrame.Menu,"Start requires its exact original menu operation");
        Selection selected=selection(command,nativeArchive.withSession(borrowed()));
        var expected=expected(command.origin().requireFrontend(),command.source(),selected.candidate());
        require(expected.equals(command.expectation().requireGameplayEntry()),"Start expected identity differs from actual native bookmark model");
        return Primitive.START_BOOKMARK.emptyRequest();
    }
    private Selection selection(ActionCommand command,ActionPorts.OutcomeArchive archive) {
        Arguments input=Arguments.decode(command.arguments());
        PlanningReadReceipt route=load(command,input.beforeRoute(),definitions.route(),archive);
        PlanningReadReceipt model=load(command,input.selectedModel(),definitions.bookmark(),archive);
        ObservedRoute observed=definitions.route().decode(route);
        Candidate selected=definitions.bookmark().decode(model).selected(input.characterNameKey(),false,true);
        require(observed.route()==Route.BOOKMARKS && observed.source().equals(selected.source()),"Start lacks actual selected ordinary bookmarks route/model");
        return new Selection(observed,selected);
    }
    private <T> PlanningReadReceipt load(ActionCommand command,ExactRef ref,ReadContract<T> contract,ActionPorts.OutcomeArchive archive) {
        PlanningReadReceipt read=archive.loadRead(ref);require(archive.readReferenceOf(read).equals(ref),"Start original read reference changed");
        NativeRecordedEvidenceVerifier.requireRead(read,archive);
        require(read.contractId().equals(contract.contractId()) && read.request().operation().equals(contract.operation())
                && read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId())
                && read.request().origin() instanceof CommandOrigin.Frontend
                && command.origin().requireFrontend().sameSession(read.request().origin().requireFrontend())
                && read.after().binding().origin() instanceof CommandOrigin.Frontend
                && command.origin().requireFrontend().sameSession(read.after().binding().origin().requireFrontend())
                && read.after().binding().origin().requireFrontend().frame().querySequence().compareTo(command.origin().requireFrontend().frame().querySequence())<=0,
                "Start selected read crossed actual source/session or cites future frontend sequence");
        return read;
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        if(!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk())
            return NativeEffectRegistry.Projected.pending("Start dispatch unresolved; the original native action is never replayed",List.of(attempt.guard().nativeEvidence()));
        try {
            RootMenuSession actualMenu;
            synchronized(this) { actualMenu=menu; }
            if(actualMenu==null)throw new IOException("actual Root frontend graph not installed");
            var borrowed=writer.borrowedSession();writer.requireSession(borrowed);
            var archive=nativeArchive.withSession(borrowed);
            Selection selected=selection(command,archive);
            var staged=bootstrap.stage(command,attempt);
            PlanningReadRequest request=new PlanningReadRequest(new CommandOrigin.Gameplay(staged.frame().identity()),command.source(),
                    staged.frame().sessionId(),campaignRoot.operation(),org.xar.ck3.control.application.planning.finance.FinanceReadContracts.rootArguments(
                            org.xar.ck3.control.application.planning.finance.FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),command.deadline());
            FrontendStartRootQueries queryCustody=rootQueries();
            PlanningReadResult<?> result=staged.scopedRead(()->actualMenu.readEntry(borrowed,campaignRoot,request,queryCustody));
            if(!(result instanceof PlanningReadResult.Known<?> known))throw new IOException("independent actual campaign-root read unavailable; original Start remains pending");
            staged.retainRoot(known);queryCustody.frameVerified(borrowed,campaignRoot,known);staged.awaitIndependentPausedPump(32);
            ObjectNode basis=StrictJson.object();basis.put("schema",BASIS);basis.put("command_body_sha256",ActionCodec.bodySha256(command));basis.put("request_id",attempt.requestId());
            basis.set("first_heartbeat",staged.firstHeartbeat().toJson());basis.set("last_heartbeat",staged.lastHeartbeat().toJson());
            basis.set("source_qualification",ExactRef.optionalToJson(staged.sourceQualification()));basis.set("original_hello",staged.originalHello().toJson());
            basis.set("policy_source",staged.policy().source().toJson());basis.set("environment",staged.policy().environment().toJson());
            basis.set("independent_root_read",archive.preserveRead(known.receipt()).toJson());
            basis.set("compatible_material",archive.preserveMaterial(compatible(command,attempt,known.receipt())).toJson());
            ExactRef retained=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(basis)));
            FrontendGameplayObservation observation=observation(command,attempt,ack,selected,staged.semantic(),known.receipt(),List.of(retained),archive);
            ActionEffects.validate(command,attempt,new ActionState.GameplayEntered(observation));
            return projected(command,attempt,known.receipt(),observation);
        } catch(InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return NativeEffectRegistry.Projected.pending("Start first-map collection interrupted; original submit must not be repeated",List.of(attempt.guard().nativeEvidence()));
        } catch(IOException | IllegalArgumentException | IllegalStateException failure) {
            return NativeEffectRegistry.Projected.pending("Start actual first Driver/SEM/root/pump incomplete: "+String.valueOf(failure.getMessage()),List.of(attempt.guard().nativeEvidence()));
        }
    }
    private FrontendGameplayObservation observation(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,
            Selection selected,org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence semantic,PlanningReadReceipt root,
            List<ExactRef> supporting,ActionPorts.OutcomeArchive archive)throws IOException {
        var borrowed=writer.borrowedSession();writer.requireSession(borrowed);
        semantics.verify(borrowed,new SessionIdentity(command.source().machineId(),command.origin().game(),command.sessionId()),semantic);
        NativeRecordedEvidenceVerifier.requireRead(root,archive);
        GameplayEntryRoot independent=GameplayEntryRoot.decode(root);
        Obj snapshot=DriverJson.object(nativeArchive.readArtifact(borrowed,semantic.semantic(),ReadinessArchive.Role.SEMANTIC.maximumBytes()),ReadinessArchive.Role.SEMANTIC.maximumBytes());
        var id=semantic.frame().frame();
        require(root.request().before().equals(semantic.frame()) && independent.player().equals(id.identity().player())
                && independent.dateRaw()==selected.candidate().dateRaw(),"Start independent root differs from first SEM");
        FrontendRulesPostconditions.started(selected.route(),selected.candidate(),
                FrontendRulesCodec.nativeAck(ack.originalResultToken().orElseThrow(),Primitive.START_BOOKMARK.operation().value()),
                new FrontendRulesPostconditions.MapPost(id.snapshotId(),id.identity().nativeRevision(),id.identity().dateRaw().intValueExact(),id.identity().player(),
                        bool(snapshot.get("paused"),"paused"),bool(snapshot.get("map_ready"),"map_ready")),
                new FrontendRulesPostconditions.CampaignRootPost(true,id.identity().nativeRevision(),independent.dateRaw(),independent.player(),independent.governmentKey()));
        return new FrontendGameplayObservation(command.origin().requireFrontend(),command.source(),
                new SessionIdentity(command.source().machineId(),command.origin().game(),command.sessionId()),attempt.guard().connectionGeneration(),SCHEMA,
                values(selected.candidate()),semantic,root,supporting);
    }
    private static NativeEffectRegistry.Projected projected(ActionCommand command,ActionState.Attempt attempt,PlanningReadReceipt root,FrontendGameplayObservation observation) {
        return new NativeEffectRegistry.Projected(new ActionPorts.GameplayEntryObserved(observation),Optional.of(compatible(command,attempt,root)));
    }
    private static RawJson compatible(ActionCommand command,ActionState.Attempt attempt,PlanningReadReceipt root) {
        ObjectNode result=StrictJson.object();result.put("schema",SCHEMA);result.put("status","observed");result.put("postcondition_verified",true);
        result.put("operation",command.operation().value());result.put("action_request_id",attempt.requestId());result.put("independent_root_request_id",root.requestId());
        result.put("uses_ocr",false);result.put("uses_keyboard",false);result.put("uses_mouse",false);
        return new RawJson(ContinuityJson.canonical(result));
    }
    public void verifyArchived(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        try {
            require(receipt.state() instanceof ActionState.Settled && ((ActionState.Settled)receipt.state()).settlement() instanceof ActionState.GameplayEntered,
                    "Start archived replay requires actual GameplayEntered settlement");
            var settled=(ActionState.Settled)receipt.state();var observation=((ActionState.GameplayEntered)settled.settlement()).observation();
            require(settled.dispatch() instanceof NativeActionPort.AckReceived && observation.supportingEvidence().size()==1,"Start lacks original ACK or unique independent basis");
            ExactRef ref=observation.supportingEvidence().getFirst();RawJson raw=archive.loadMaterial(ref);
            require(raw.bytes().length==ref.bytes() && DriverJson.sha256(raw.bytes()).equals(ref.sha256()),"Start basis physical bytes differ");
            ObjectNode row=StrictJson.object(ContinuityJson.parseObject(raw.bytes(),65536),Set.of("schema","command_body_sha256","request_id","first_heartbeat","last_heartbeat","policy_source","environment","independent_root_read","original_hello","compatible_material"),Set.of("source_qualification"));
            require(BASIS.equals(StrictJson.text(row.get("schema"))) && receipt.bodySha256().equals(StrictJson.text(row.get("command_body_sha256")))
                    && settled.attempt().requestId().equals(StrictJson.text(row.get("request_id"))),"Start basis crossed exact command or native request");
            var borrowed=writer.borrowedSession();writer.requireSession(borrowed);
            for(String field:List.of("policy_source","environment")) {
                var exact=ExactRef.fromJson(row.get(field));var pin=borrowed.capturePin(exact,1<<20);borrowed.verifyPin(pin);
            }
            PlanningReadReceipt root=archive.loadRead(ExactRef.fromJson(row.get("independent_root_read")));
            require(root.equals(observation.campaignRootRead()),"Start archived root read changed");
            require(compatible(receipt.command(),settled.attempt(),root).equals(archive.loadMaterial(ExactRef.fromJson(row.get("compatible_material")))),
                    "Start original compatible result differs from the actual consumer projection");
            verifyHello(nativeArchive.readArtifact(borrowed,ExactRef.fromJson(row.get("original_hello")),ReadinessArchive.Role.HELLO.maximumBytes()),observation);
            verifyPump(nativeArchive.readArtifact(borrowed,ExactRef.fromJson(row.get("first_heartbeat")),ReadinessArchive.Role.HEARTBEAT.maximumBytes()),
                    nativeArchive.readArtifact(borrowed,ExactRef.fromJson(row.get("last_heartbeat")),ReadinessArchive.Role.HEARTBEAT.maximumBytes()),observation.after().frame().identity().dateRaw());
            var replayed=observation(receipt.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch(),selection(receipt.command(),archive),
                    observation.semanticEvidence(),root,observation.supportingEvidence(),archive);
            require(replayed.equals(observation),"actual archived Start map/root/SEM replay differs");
            observation.validate(receipt.command(),settled.attempt());
        } catch(IOException failure) { throw new UncheckedIOException("Start original-evidence replay unavailable",failure); }
    }
    static void verifyPump(byte[] before,byte[] after,BigInteger date) {
        Obj first=packet(before);Obj last=packet(after);
        require(new Text("heartbeat").equals(first.get("type")) && new Text("heartbeat").equals(last.get("type"))
                && BigInteger.ONE.equals(integer(first.get("protocol_version"),"protocol_version"))
                && BigInteger.ONE.equals(integer(last.get("protocol_version"),"protocol_version"))
                && integer(last.get("sequence"),"sequence").compareTo(integer(first.get("sequence"),"sequence"))>0,"independent later actual heartbeat required");
        Obj a=object(first.get("main_thread_query_mailbox_v1"),"mailbox");Obj b=object(last.get("main_thread_query_mailbox_v1"),"mailbox");
        for(Obj mailbox:List.of(a,b))require(bool(mailbox.get("installed"),"installed") && bool(mailbox.get("ready"),"ready")
                && !bool(mailbox.get("stop"),"stop") && bool(mailbox.get("executor_submission_enabled"),"executor_submission_enabled")
                && integer(mailbox.get("failure"),"failure").signum()==0 && bool(mailbox.get("paused"),"paused")
                && integer(mailbox.get("date_raw"),"date_raw").equals(date),"actual paused mailbox source/pump differs");
        require(integer(b.get("pump_epochs"),"pump_epochs").compareTo(integer(a.get("pump_epochs"),"pump_epochs"))>0,"application-main pump did not advance after first readiness");
    }
    private static void verifyHello(byte[] helloBytes,FrontendGameplayObservation observation)throws IOException {
        Obj hello=packet(helloBytes);
        require(new Text("hello").equals(hello.get("type")) && bool(hello.get("ck3_build_match"),"ck3_build_match")
                && BigInteger.ONE.equals(integer(hello.get("protocol_version"),"protocol_version"))
                && new Text("ready").equals(hello.get("game_adapter_status"))
                && integer(hello.get("pid"),"pid").equals(BigInteger.valueOf(observation.after().game().pid()))
                && integer(hello.get("connection_generation"),"connection_generation").equals(observation.connectionGeneration()),"Start hello lost the actual held Game/connection");
    }
    /** The shared v3 decoder is the sole source-proof wire boundary for both actual Start paths. */
    static NativeSourceProofDocument sourceProof(byte[] original,String machineId,String sessionId,ExactRef source)throws IOException {
        NativeSourceProofDocument proof=NativeSourceProofCodec.decode(original);
        require(proof.machineId().equals(Objects.requireNonNull(machineId))
                &&proof.sessionId().equals(Objects.requireNonNull(sessionId)),"Start original full source qualification differs");
        require(proof.source().equals(Objects.requireNonNull(source)),"Start qualified native source differs from original command source");
        return proof;
    }
    private static Obj packet(byte[] raw) {
        require(raw.length>=5 && ByteBuffer.wrap(raw,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==raw.length-4,"exact original heartbeat LE frame required");
        return DriverJson.object(Arrays.copyOfRange(raw,4,raw.length),ReadinessArchive.Role.HEARTBEAT.maximumBytes());
    }
    private ContinuityStorePort.Session borrowed() {
        try { return writer.borrowedSession(); } catch(IOException failure) { throw new UncheckedIOException(failure); }
    }
}
