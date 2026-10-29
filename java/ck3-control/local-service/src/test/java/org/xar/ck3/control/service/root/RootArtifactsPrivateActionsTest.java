package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** Real canonical writer/archive/central submission at a declared software packet edge; never Game qualification. */
final class RootArtifactsPrivateActionsTest {
    @TempDir Path temporary;
    @Test void actualCanonicalUnknownBlocksAllThreeAndSurvivesWriterReopenWithoutResubmit()throws Exception {
        for(Method method:RootArtifactsPrivateActions.supportedMethods()) {
            AtomicReference<ActionWriterIntegrationFixture> owned=new AtomicReference<>();
            var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(EXECUTABLE_SHA256,"software-artifact-private",ignored->List.of(),request->{throw new AssertionError("UNKNOWN test supplies no independent Native POST");},Optional.of(VERSION),Set.of());
            var scenarios=RootArtifactsPrivateActions.supportedMethods().stream().map(m->scenario(m,owned)).toList();
            try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve(method.name()),true,reads,scenarios)) {
                owned.set(fixture);ActionCommand first=command(fixture,method,"original-private-"+method.name());ActionReceipt unknown=execute(fixture,first);
                assertFalse(unknown.settled());assertEquals(1,fixture.nativeActionWrites());byte[] durable=fixture.ledgerBytes();
                if(method==Method.OPEN)fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
                    var attempt=ActionTransitions.attempt(unknown.state()).orElseThrow();var original=RootGuardEvidence.loadFrame(attempt.guard(),archive,fixture.frameLoader());
                    // Deliberately invalid before-as-after DATA cannot supply the missing original ACK.
                    var dispatch=ActionTransitions.dispatch(unknown.state()).orElseThrow();var publication=new ArtifactsService.PrivateActionPublication(original,original,unknown,archive.receiptReferenceOf(unknown),archive.referenceOf(dispatch),true);
                    Reply software=window(new RevisionRequest(Method.OPEN,BigInteger.valueOf(15)),BigInteger.valueOf(17),true,false,10);
                    assertThrows(IllegalArgumentException.class,()->ArtifactsService.publishPrivateAction(software,publication));return null;
                }));
                assertEquals(unknown,fixture.coordinator.execute(first));assertEquals(1,fixture.nativeActionWrites());assertArrayEquals(durable,fixture.ledgerBytes());
                assertEquals(unknown,fixture.reopenAndReturnExisting(first));assertArrayEquals(durable,fixture.ledgerBytes());assertEquals(1,fixture.nativeActionWrites());
                fixture.writer.locked(same->{var history=ContinuityActionJournal.receipts(same.head().state(),fixture.archive.withSession(same));
                    assertEquals(unknown,RootArtifactsPrivateActions.unresolvedOriginal(history,first.before().machineId(),first.before().frame().episodeRunId(),first.before().frame().identity().player()).orElseThrow());return null;});
                for(Method other:RootArtifactsPrivateActions.supportedMethods()) {
                    ActionCommand changed=changedCommand(first,other,"another-private-"+other.name());
                    assertThrows(RuntimeException.class,()->fixture.writer.locked(same->{fixture.writer.requireSession(same);RootArtifactsPrivateActions.requireNoUnresolved(ContinuityActionJournal.receipts(same.head().state(),fixture.archive.withSession(same)),changed.before().machineId(),changed.before().frame().episodeRunId(),changed.before().frame().identity().player());return null;}),"same actual writer preparation gate must retain the original pending owner");
                    assertEquals(1,fixture.nativeActionWrites());assertArrayEquals(durable,fixture.ledgerBytes());
                }
            }
        }
    }
    @Test void originalWindowAckAndIndependentPostMustKeepTheCompleteOriginalSequenceAndBaseline() {
        for(Method method:List.of(Method.OPEN,Method.CLOSE)) {
            Request action=new RevisionRequest(method,BigInteger.valueOf(15));Reply submitted=window(action,BigInteger.valueOf(17),true,false,10);
            Request post=RootArtifactsPrivateActions.postRequest(action,BigInteger.valueOf(15),BigInteger.valueOf(17));Reply observed=window(post,BigInteger.valueOf(17),true,true,10);
            assertDoesNotThrow(()->RootArtifactsPrivateActions.requireCorrelatedPost(action,submitted,observed));assertFalse(RootArtifactsPrivateActions.knownNoDispatch(submitted));
            Reply another=window(RootArtifactsPrivateActions.postRequest(action,BigInteger.valueOf(15),BigInteger.valueOf(18)),BigInteger.valueOf(18),true,true,10);
            assertThrows(IllegalArgumentException.class,()->RootArtifactsPrivateActions.requireCorrelatedPost(action,submitted,another));
            Reply changedBaseline=window(post,BigInteger.valueOf(17),true,true,9);
            assertThrows(IllegalArgumentException.class,()->RootArtifactsPrivateActions.requireCorrelatedPost(action,submitted,changedBaseline));
            Reply stillPending=window(post,BigInteger.valueOf(17),true,false,10);
            assertThrows(IllegalArgumentException.class,()->RootArtifactsPrivateActions.requireCorrelatedPost(action,submitted,stillPending));
            assertFalse(observed.payload().original().get("business_outcome_observed").booleanValue());
        }
    }
    @Test void noDispatchCannotClearTheNativeLedgerRejectionOrAConsumedUnknown() {
        for(Method method:List.of(Method.OPEN,Method.CLOSE)) {
            Request request=new RevisionRequest(method,BigInteger.valueOf(15));Reply noCall=window(request,BigInteger.ZERO,false,false,10);
            assertTrue(RootArtifactsPrivateActions.knownNoDispatch(noCall));
            ObjectNode packet=windowPacket(request,BigInteger.ZERO,false,false,10);ObjectNode body=(ObjectNode)packet.get("result").get(method.resultKey());
            body.put("status",method==Method.OPEN?"inventory_pending_or_once_ledger_rejected":"inventory_close_pending_or_once_intent_rejected");
            Reply rejected=ArtifactsCodec.normalize(request,frame(),new NativeEnvelope("authored-original-private",packet,frame()));assertFalse(RootArtifactsPrivateActions.knownNoDispatch(rejected));
            assertFalse(RootArtifactsPrivateActions.knownNoDispatch(window(request,BigInteger.valueOf(17),true,false,10)));
        }
    }
    @Test void unsignedOriginalIntentSurvivesPublicSerdeAndRejectsBooleanFloatOrTextAlias() {
        BigInteger max=new BigInteger("18446744073709551615");Request action=new RevisionRequest(Method.OPEN,BigInteger.valueOf(15));Request post=RootArtifactsPrivateActions.postRequest(action,BigInteger.valueOf(15),max);
        Reply submitted=window(action,max,true,false,10),observed=window(post,max,true,true,10);RootArtifactsPrivateActions.requireCorrelatedPost(action,submitted,observed);
        assertEquals(max,observed.facts().actualIntentSequence().orElseThrow());assertEquals(max.toString(),ArtifactsCodec.encode(post).get("expected_intent_sequence").textValue());
        ObjectNode nativeFields=ArtifactsCodec.nativeFields(post,frame(),Optional.of("a".repeat(64)));assertTrue(nativeFields.get("expected_intent_sequence").isIntegralNumber());assertEquals(max,nativeFields.get("expected_intent_sequence").bigIntegerValue());
        ObjectNode encoded=ArtifactsCodec.encode(post);encoded.put("expected_intent_sequence",true);assertThrows(RuntimeException.class,()->ArtifactsCodec.decode(post.method().originalName(),encoded));
        encoded.put("expected_intent_sequence",17.0);assertThrows(RuntimeException.class,()->ArtifactsCodec.decode(post.method().originalName(),encoded));
        encoded.put("expected_intent_sequence","017");assertThrows(RuntimeException.class,()->ArtifactsCodec.decode(post.method().originalName(),encoded));
    }
    @Test void personalIntentKeepsAllOriginalParametersAndRequiresPositivePolicyBeforeNativePreparation() {
        var empty=new PublicUnsigned64.Missing();var item=new PersonalSubmit(BigInteger.valueOf(15),73,true,2,empty,true);
        assertTrue(RootArtifactsPrivateActions.sameIntent(item,new PersonalSubmit(BigInteger.valueOf(16),73,true,2,empty,true)));
        for(Request changed:List.of(new PersonalSubmit(BigInteger.valueOf(15),74,true,2,empty,true),new PersonalSubmit(BigInteger.valueOf(15),73,false,2,empty,true),new PersonalSubmit(BigInteger.valueOf(15),73,true,3,empty,true),new PersonalSubmit(BigInteger.valueOf(15),73,true,2,new PublicUnsigned64.Value(BigInteger.valueOf(74)),true)))assertFalse(RootArtifactsPrivateActions.sameIntent(item,changed));
        var noPolicy=new PersonalSubmit(BigInteger.valueOf(15),73,true,2,empty,false);assertThrows(RuntimeException.class,()->ArtifactsCodec.nativeFields(noPolicy,frame(),Optional.empty()));
        PersonalPost post=(PersonalPost)RootArtifactsPrivateActions.postRequest(item,BigInteger.valueOf(16),BigInteger.valueOf(19));assertEquals(73,post.artifactId());assertEquals(BigInteger.valueOf(19),post.expectedIntentSequence());
    }
    @Test void windowCodecRefusesCrossProcessBirthGenerationAndPrivateActorZero() {
        Request action=new RevisionRequest(Method.OPEN,BigInteger.valueOf(15));ObjectNode packet=windowPacket(action,BigInteger.valueOf(17),true,false,10);NativeFrame before=frame();
        for(NativeFrame foreign:List.of(new NativeFrame(before.publicRevision(),before.nativeRevision(),before.dateRaw(),99,124,before.gameCreationFiletime(),before.connectionGeneration(),before.episodeRunId(),EXECUTABLE_SHA256,true,true,true),new NativeFrame(before.publicRevision(),before.nativeRevision(),before.dateRaw(),99,123,BigInteger.valueOf(3),before.connectionGeneration(),before.episodeRunId(),EXECUTABLE_SHA256,true,true,true),new NativeFrame(before.publicRevision(),before.nativeRevision(),before.dateRaw(),99,123,before.gameCreationFiletime(),BigInteger.valueOf(3),before.episodeRunId(),EXECUTABLE_SHA256,true,true,true)))assertThrows(RuntimeException.class,()->ArtifactsCodec.normalize(action,before,new NativeEnvelope("authored-original-private",packet,foreign)));
        assertThrows(RuntimeException.class,()->new NativeFrame(before.publicRevision(),before.nativeRevision(),before.dateRaw(),0,123,before.gameCreationFiletime(),before.connectionGeneration(),before.episodeRunId(),EXECUTABLE_SHA256,true,true,true));
    }
    @Test void actualReadSampledBeforeOriginalAckCannotReleaseAnIntent()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("no-dispatch-chronology"),false)) {
            ActionCommand seed=fixture.command("probe-before-action");
            var request=new PlanningReadRequest(seed.before(),seed.source(),seed.sessionId(),fixture.readContract.operation(),new OpportunityJson.Obj(Map.of()),seed.deadline());
            var observed=fixture.physicalInputs().transport().withMailbox(seed.deadline(),scope->fixture.reads.read(fixture.readContract,request));
            assertInstanceOf(PlanningReadResult.Known.class,observed);PlanningReadReceipt old=((PlanningReadResult.Known<?>)observed).receipt();
            ActionReceipt receipt=execute(fixture,fixture.command("actual-ack-after-probe"));var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();var ack=receipt.ack().orElseThrow();
            assertThrows(IllegalArgumentException.class,()->RootArtifactsPrivateActions.requireProbeAfter(old,attempt,ack));
            ActionCommand current=fixture.command("probe-after-action");var fresh=new PlanningReadRequest(current.before(),current.source(),current.sessionId(),fixture.readContract.operation(),new OpportunityJson.Obj(Map.of()),current.deadline());
            var later=fixture.physicalInputs().transport().withMailbox(current.deadline(),scope->fixture.reads.read(fixture.readContract,fresh));
            assertInstanceOf(PlanningReadResult.Known.class,later);assertDoesNotThrow(()->RootArtifactsPrivateActions.requireProbeAfter(((PlanningReadResult.Known<?>)later).receipt(),attempt,ack));
        }
    }
    @Test void actualPrivateAckProjectsCanonicalReferencesAndFullWidthCountersThroughTheNamedMcpRoute()throws Exception {
        AtomicReference<ActionWriterIntegrationFixture> owned=new AtomicReference<>();var nativeEnvelope=new AtomicReference<ObjectNode>();
        var baseScenario=scenario(Method.OPEN,owned);
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(baseScenario.operation(),baseScenario.requiredCapability(),baseScenario.postcondition(),baseScenario.originalDispatch(),Optional.of(()->new RawJson(StrictJson.canonical(nativeEnvelope.get()))),baseScenario.privatePermission(),baseScenario.initializeBaseline(),baseScenario.originalPreparation());
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(EXECUTABLE_SHA256,"software-private-publication",ignored->List.of(),request->{throw new AssertionError("no independent POST is supplied by this pending projection test");},Optional.of(VERSION),Set.of());
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-private-publication"),false,reads,List.of(scenario))) {
            owned.set(fixture);ActionCommand command=command(fixture,Method.OPEN,"private-original-publication");var hello=fixture.physicalInputs().transport().originalHello();
            ObjectNode envelope=(ObjectNode)windowPacket(new RevisionRequest(Method.OPEN,BigInteger.valueOf(15)),new BigInteger("18446744073709551615"),true,false,10).get("result");
            envelope.put("snapshot_revision",command.before().frame().identity().nativeRevision()).put("date_raw",command.before().frame().identity().dateRaw()).put("game_pid",command.before().game().pid()).put("connection_generation",hello.connectionGeneration());
            ObjectNode inner=(ObjectNode)envelope.get(Method.OPEN.resultKey());
            for(String role:List.of("current","before")){
                ObjectNode view=(ObjectNode)inner.get(role);view.put("native_revision",command.before().frame().identity().nativeRevision()).put("date_raw",command.before().frame().identity().dateRaw()).put("game_pid",command.before().game().pid()).put("connection_generation",hello.connectionGeneration()).put("played_character_id",command.before().frame().identity().player()).put("selected_character_id",command.before().frame().identity().player()).put("capture_epoch",new BigInteger("18446744073709551615"));
            }
            nativeEnvelope.set(envelope);ActionReceipt receipt=execute(fixture,command);assertFalse(receipt.settled());assertTrue(receipt.ack().isPresent());assertEquals(1,fixture.nativeActionWrites());
            ActionCommand probeBasis=fixture.command("actual-independent-publication-probe");
            var probeRequest=new PlanningReadRequest(probeBasis.before(),probeBasis.source(),probeBasis.sessionId(),fixture.readContract.operation(),new OpportunityJson.Obj(Map.of()),probeBasis.deadline());
            var probe=fixture.physicalInputs().transport().withMailbox(probeBasis.deadline(),scope->fixture.reads.read(fixture.readContract,probeRequest));assertInstanceOf(PlanningReadResult.Known.class,probe);PlanningReadReceipt actualAfterRead=((PlanningReadResult.Known<?>)probe).receipt();
            fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
                var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();var ack=receipt.ack().orElseThrow();Complete original=RootGuardEvidence.loadFrame(attempt.guard(),archive,fixture.frameLoader());var actual=ArtifactsService.actualFrame(original);
                RootArtifactsPrivateActions.requireProbeAfter(actualAfterRead,attempt,ack);Complete observedAfter=RootGuardEvidence.loadFrame(actualAfterRead.after().binding(),archive,fixture.frameLoader());
                Request request=ArtifactsCodec.decode(Method.OPEN.originalName(),assertInstanceOf(ObjectNode.class,OpportunityJson.toNode(command.arguments())).get("request"));
                // Actual guarded probe-after DATA is retained; public projection still grants no effect authority.
                Reply normalized=ArtifactsCodec.normalize(request,actual,new NativeEnvelope(ack.requestId(),StrictJson.parse(ack.originalFrame().bytes()),ArtifactsService.actualFrame(observedAfter)));
                var publication=new ArtifactsService.PrivateActionPublication(original,observedAfter,receipt,archive.receiptReferenceOf(receipt),archive.referenceOf(ack),true);Reply published=ArtifactsService.publishPrivateAction(normalized,publication);
                assertTrue(published.payload().original().get("intent_sequence").isIntegralNumber(),"raw NativePayload must remain the exact native original");
                ObjectNode publicBody=ArtifactsCodec.encode(published);
                assertEquals("18446744073709551615",publicBody.get("intent_sequence").textValue());
                assertEquals("18446744073709551615",publicBody.get("before").get("capture_epoch").textValue());
                assertTrue(published.payload().original().get("client_replay_blocked").booleanValue());assertFalse(published.payload().original().get("business_outcome_observed").booleanValue());
                assertEquals(publication.receiptReference(),ExactRef.fromJson(published.payload().original().get("java_canonical_action_receipt")));assertEquals(publication.acknowledgementReference(),ExactRef.fromJson(published.payload().original().get("java_original_native_ack")));
                assertEquals(observedAfter.identity().frame().snapshotId(),publicBody.get("post_snapshot_id").textValue());assertEquals("a".repeat(64),publicBody.get("client_source_inventory_sha256").textValue());
                assertFalse(published.payload().original().has("native_ui_raw_return_receipt"));
                assertThrows(IllegalArgumentException.class,()->ArtifactsService.publishPrivateAction(normalized,new ArtifactsService.PrivateActionPublication(original,observedAfter,receipt,publication.receiptReference(),publication.acknowledgementReference(),false)));
                Reply foreign=window(new RevisionRequest(Method.CLOSE,BigInteger.valueOf(15)),BigInteger.valueOf(17),true,false,10);assertThrows(IllegalArgumentException.class,()->ArtifactsService.publishPrivateAction(foreign,publication));
                var bindings=RootArtifactsPublicProducts.actionBindings(command.source().sourceRef(),Set.of(Method.OPEN),decoded->{assertTrue(RootArtifactsPrivateActions.sameIntent(request,decoded));return published;});
                try {
                    var result=invoke(bindings.getFirst(),new RawJson(StrictJson.canonical(ArtifactsCodec.encode(request))));ObjectNode structured=assertInstanceOf(ObjectNode.class,StrictJson.parse(result.bytes()).get("structuredContent"));
                    assertArrayEquals(StrictJson.canonical(publicBody),StrictJson.canonical(structured));assertTrue(structured.get("intent_sequence").isTextual());assertTrue(structured.get("current").get("capture_epoch").isTextual());
                }catch(Exception failure){throw new UncheckedIOException(new IOException("actual named private MCP serialization failed",failure));}
                return null;
            }));
            assertEquals(1,fixture.nativeActionWrites());assertFalse(receipt.settled());
        }
    }
    private static <Q,R>PublicMcpDirectory.CallResult invoke(McpExecutableDirectory.DirectBinding<Q,R> binding,RawJson input)throws Exception {
        var call=new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(input)),Optional.empty(),new McpCancellation());
        return binding.encoder().encode(binding.actual().invoke(binding.decoder().decode(call)));
    }
    private static ActionWriterIntegrationFixture.SoftwareActionScenario scenario(Method method,AtomicReference<ActionWriterIntegrationFixture> owned) {
        var operation=new OperationKey(method.step());
        return new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"software.original-artifact-private",(command,attempt,dispatch)->new ActionPorts.Pending("software Native ACK is missing; original UNKNOWN is retained",List.of(attempt.guard().nativeEvidence())),()->{},Optional.empty(),Optional.of(reviewed->{
            var producers=new EnumMap<Method,ExactRef>(Method.class);for(Method m:List.of(Method.OPEN,Method.CLOSE,Method.PERSONAL_SUBMIT,Method.OPEN_POST,Method.CLOSE_POST,Method.PERSONAL_POST))producers.put(m,reviewed);
            var source=new ArtifactsService.Sources(reviewed,reviewed,producers,List.of(reviewed),producers.keySet(),ArtifactsService::actualFrame,actual->reviewed.sha256(),(configuration,hello,guard,request)->{assertEquals(EXECUTABLE_SHA256,hello.gameSha256().toLowerCase(java.util.Locale.ROOT));assertEquals(method.step(),request.step());return reviewed;});
            return ArtifactsService.privatePermissions(source).stream().filter(permission->permission.operation().equals(operation)).findFirst().orElseThrow();
        }),false,Optional.of(new ActionPorts.PreparationPort(){
            public NativeRequest prepare(ActionCommand command){throw new AssertionError("real borrowed writer/request required");}
            public NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionCommand command,String requestId){
                try {var fixture=owned.get();fixture.writer.requireSession(same);var history=ContinuityActionJournal.receipts(same.head().state(),fixture.archive.withSession(same));
                    RootArtifactsPrivateActions.requireNoUnresolved(history,command.before().machineId(),command.before().frame().episodeRunId(),command.before().frame().identity().player());
                    ObjectNode args=assertInstanceOf(ObjectNode.class,OpportunityJson.toNode(command.arguments()));Request query=ArtifactsCodec.decode(args.get("method").textValue(),args.get("request"));
                    var captured=fixture.collector.currentOwned(same,new SessionIdentity(command.before().machineId(),command.before().game(),command.sessionId()),command.deadline(),lease->lease.frame());
                    Optional<String> inventory=query instanceof PersonalSubmit?Optional.empty():Optional.of(args.get("source_inventory_sha256").textValue());ObjectNode fields=ArtifactsCodec.nativeFields(query,ArtifactsService.actualFrame(captured),inventory);fields.put("expected_snapshot_revision",captured.identity().frame().identity().nativeRevision());return new NativeRequest(method.step(),Optional.empty(),new RawJson(StrictJson.canonical(fields)));
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            }
        }));
    }
    private static ActionCommand command(ActionWriterIntegrationFixture fixture,Method method,String actionId)throws Exception {
        ActionCommand base=fixture.command(actionId);Complete captured=fixture.physicalInputs().transport().withMailbox(base.deadline(),scope->fixture.writer.locked(same->fixture.collector.currentOwned(same,new SessionIdentity(base.before().machineId(),base.before().game(),base.sessionId()),base.deadline(),lease->lease.frame())));
        Request request=method==Method.PERSONAL_SUBMIT?new PersonalSubmit(captured.identity().frame().revision(),73,true,2,new PublicUnsigned64.Missing(),true):new RevisionRequest(method,captured.identity().frame().revision());
        var selected=new ArtifactsService.Selection(captured,ArtifactsService.actualFrame(captured),request,method==Method.PERSONAL_SUBMIT?Optional.empty():Optional.of("a".repeat(64)),base.deadline());
        var expected=new ExpectedPostcondition(1,captured.identity(),captured.source(),base.expected().observerSchema(),base.expected().values());
        return new ActionCommand(actionId,captured.identity(),captured.source(),captured.sessionId(),new OperationKey(method.step()),RootArtifactsPrivateActions.commandArguments(selected),expected,new Claims(Set.of(),Set.of(),Set.of(captured.identity().frame().identity().player()),Set.of()),base.deadline());
    }
    private static ActionCommand changedCommand(ActionCommand original,Method method,String actionId){
        ObjectNode args=assertInstanceOf(ObjectNode.class,OpportunityJson.toNode(original.arguments())).deepCopy();Request request=method==Method.PERSONAL_SUBMIT?new PersonalSubmit(original.before().frame().revision(),73,true,2,new PublicUnsigned64.Missing(),true):new RevisionRequest(method,original.before().frame().revision());
        args.put("method",method.originalName());args.set("request",ArtifactsCodec.encode(request));if(method==Method.PERSONAL_SUBMIT)args.putNull("source_inventory_sha256");else args.put("source_inventory_sha256","a".repeat(64));
        return new ActionCommand(actionId,original.before(),original.source(),original.sessionId(),new OperationKey(method.step()),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"changed private intent"),original.expected(),original.claims(),original.deadline());
    }
    private static ActionReceipt execute(ActionWriterIntegrationFixture fixture,ActionCommand command)throws Exception {
        var retained=new AtomicReference<ActionReceipt>();try{fixture.physicalInputs().transport().withMailbox(command.deadline(),scope->{retained.set(fixture.coordinator.execute(command));return null;});}catch(IOException poisoned){if(retained.get()==null)throw poisoned;assertFalse(retained.get().settled());}return retained.get();
    }
    static NativeFrame frame(){return new NativeFrame(BigInteger.valueOf(15),BigInteger.valueOf(20),BigInteger.valueOf(24),99,123,new BigInteger("18446744073709551615"),BigInteger.valueOf(2),"software-original-artifact",EXECUTABLE_SHA256,true,true,true);}
    private static Reply window(Request request,BigInteger sequence,boolean claimed,boolean resolved,int originalEpoch){return ArtifactsCodec.normalize(request,frame(),new NativeEnvelope("authored-original-private",windowPacket(request,sequence,claimed,resolved,originalEpoch),frame()));}
    /** Authored translation of the original Python window tests; no real Native receipt is claimed. */
    static ObjectNode windowPacket(Request request,BigInteger sequence,boolean claimed,boolean resolved,int originalEpoch) {
        Method method=request.method();boolean close=method==Method.CLOSE||method==Method.CLOSE_POST,post=method.readOnly();ObjectNode before=view(originalEpoch,close?false:true),after=view(12,close);
        ObjectNode current=post?after.deepCopy():view(originalEpoch,claimed?(!close):close);
        ObjectNode body=StrictJson.object().put("schema",close?"ck3_12004_player_inventory_window_close_v1":"ck3_12004_player_inventory_window_v1").put("game_version",VERSION).put("executable_sha256",EXECUTABLE_SHA256).put("operation",post?"post":close?"close":"open").put("read_only",post).put("available",true).putNull("unavailable_reason");
        body.put("loaded_code_pins_verified",true).put("loaded_gui_sources_verified",true).put("intent_sequence",claimed?sequence:BigInteger.ZERO).put("intent_found",claimed).put("once_intent_consumed",claimed).put("invoked",claimed).put("call_returned",claimed).put("needs_recovery",claimed&&!resolved).put("desired_window_observed",resolved);
        body.put("status",post?(resolved?(close?"inventory_window_closed_observed":"inventory_window_desired_observed"):"inventory_intent_pending_or_unknown"):claimed?(close?"inventory_close_invoked_post_pending":"inventory_original_open_invoked_post_pending"):(close?"inventory_already_hidden_no_call":"inventory_current_player_already_visible_no_call"));body.set("current",current);if(claimed)body.set("before",before);else body.set("before",current.deepCopy());if(post)body.set("after",after);else body.putNull("after");
        for(String key:List.of("artifact_equipped_observed","actor_aggregate_observed","personal_net_effect_attributed","business_outcome_observed","automatic_retry"))body.put(key,false);
        ObjectNode envelope=StrictJson.object().put("step",method.step()).put("accepted",true).put("private_build",true).put("read_only",post).put("advertised",false).put("game_version",VERSION).put("executable_sha256",EXECUTABLE_SHA256).put("backend_id",close?"ck3-1.20.0.4-native-player-inventory-window-close-v1-private":"ck3-1.20.0.4-native-player-inventory-window-v1-private").put("domain_key",method.domain()).put("snapshot_revision",20).put("date_raw",24).put("game_pid",123).put("connection_generation",2).put("status","observed");envelope.set(method.resultKey(),body);
        ObjectNode packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","authored-original-private").put("ok",true);packet.set("result",envelope);return packet;
    }
    private static ObjectNode view(int epoch,boolean hidden){return StrictJson.object().put("available",true).put("native_revision",20).put("capture_epoch",epoch).put("date_raw",24).put("game_pid",123).put("connection_generation",2).put("played_character_id",99).put("selected_character_id",99).put("window_present",true).put("root_present",true).put("native_visible",!hidden).put("effective_visible",!hidden).put("current_player_selected",true);}
}
