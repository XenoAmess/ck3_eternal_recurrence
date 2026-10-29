package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.root.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Mandatory original Python Service/execute/normalizer differential, never a Game or runtime qualification. */
final class GrantTitlePublicProductionTest {
    @TempDir Path temporary;
    private static final ExactRef REF=new ExactRef("software/grant-source",1,"a".repeat(64));
    private static final long RECIPIENT=2147483650L;
    private static ObjectNode corpus;
    @Test void publicRuntimeBoundaryRoundTripsAndRejectsWrongMissingNullAndExtraFields() {
        var q=GrantTitlePublicCodec.query(args("{\"recipient_id\":2147483650,\"title_full_ids\":[0,4294967294],\"expected_revision\":\"18446744073709551615\"}"));
        assertEquals(q,GrantTitlePublicCodec.query(new PublicBindings.Value(GrantTitlePublicCodec.encodeRequest(q))));
        var s=GrantTitlePublicCodec.select(args("{\"recipient_id\":2147483650,\"title_full_id\":4294967294,\"desired_selected\":false,\"expected_selected_title_full_ids\":[0],\"expected_revision\":\"1\"}"));
        assertEquals(List.of(new FullId(0),new FullId(4294967294L)),s.nativeRequest().targets());assertFalse(s.desiredSelected());
        assertEquals(s,GrantTitlePublicCodec.select(new PublicBindings.Value(GrantTitlePublicCodec.encodeRequest(s))));
        for(String bad:List.of("true","1.0","null","-1","4294967295"))assertThrows(IllegalArgumentException.class,()->GrantTitlePublicCodec.query(args("{\"recipient_id\":"+bad+",\"title_full_ids\":[],\"expected_revision\":\"1\"}")));
        for(String bad:List.of("true","1.0","1","null","\"0\"","\"01\"","\"18446744073709551616\""))assertThrows(IllegalArgumentException.class,()->GrantTitlePublicCodec.query(args("{\"recipient_id\":1,\"title_full_ids\":[],\"expected_revision\":"+bad+"}")));
        for(String bad:List.of("{}","{\"recipient_id\":1,\"title_full_ids\":null,\"expected_revision\":\"1\"}","{\"recipient_id\":1,\"title_full_ids\":[1,1],\"expected_revision\":\"1\"}","{\"recipient_id\":1,\"title_full_ids\":[],\"expected_revision\":\"1\",\"extra\":false}"))assertThrows(IllegalArgumentException.class,()->GrantTitlePublicCodec.query(args(bad)));
        assertThrows(IllegalArgumentException.class,()->new GrantTitlePublicCodec.Send(new CharacterId(1),List.of(),BigInteger.ONE));
        var sixtyFour=java.util.stream.LongStream.range(0,64).mapToObj(FullId::new).toList();
        assertEquals(64,new GrantTitlePublicCodec.Query(new CharacterId(1),sixtyFour,BigInteger.ONE).titles().size());
        assertThrows(IllegalArgumentException.class,()->new GrantTitlePublicCodec.Select(new CharacterId(1),new FullId(99),true,sixtyFour,BigInteger.ONE));
    }
    @Test void originalFourServiceResultsMatchSoleNativeDecoderAndPublicProjection()throws Exception {
        for(JsonNode row:original().get("rows")) {
            Context current=current(row);GrantRequest request=request(row);RawJson raw=raw(row.get("native"));
            GrantResult result=GrantTitleCodec.decode(raw,current,request);assertEquals(request.operation(),result.operation());
            ObjectNode expected=object(row.get("public")).deepCopy();expected.remove("action_claim_path");
            assertEquals(expected,node(GrantTitlePublicCodec.observed(raw,current,request).original()));
            ObjectNode external=node(GrantTitlePublicCodec.encode(GrantTitlePublicCodec.observed(raw,current,request)));
            assertEquals("7",external.get("native_revision").textValue());assertEquals("2",external.get("connection_generation").textValue());assertEquals("1",external.get("queried_revision").textValue());
            assertFalse(external.get("business_full_credit").booleanValue());assertFalse(external.get("uses_mouse").booleanValue());
        }
        assertTrue(original().get("pending_changed_parameters_blocked").booleanValue());assertEquals(1,original().get("pending_dispatches").intValue());
    }
    @Test void actualFacadeQueryIsSamePreCoreContractAndPureMutationProducerCannotDispatch()throws Exception {
        JsonNode row=original().get("rows").get(0);Context current=current(row);var definitions=definitions();var captured=new ArrayList<ReadContract<?>>();int[] dispatches={0};
        PlanningReadPort reads=new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){captured.add(contract);var receipt=InteractionDirectPublicProductionTest.receipt(contract,request,raw(row.get("native")));return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);}};
        var facade=new InteractionCapabilities(definitions,reads,new ActionCoordinatorPort(){@Override public ActionReceipt execute(ActionCommand c){dispatches[0]++;throw new AssertionError("pure prepare must not execute");}@Override public ActionReceipt reconcile(String id){throw new AssertionError("UNKNOWN must not reconcile implicitly");}});
        var result=(GrantRead)facade.grantTitlePickerV1(current,request(row),Optional.empty());var known=(PlanningReadResult.Known<GrantResult>)result.result();
        assertSame(definitions.grantQuery(),captured.getFirst());assertTrue(definitions.contracts().stream().anyMatch(c->c==definitions.grantQuery()));assertEquals(known.value(),definitions.grantQuery().replay(known.receipt()));
        for(JsonNode mutation:original().get("rows"))if(!mutation.get("operation").textValue().equals("query")) {
            var command=facade.prepareGrantTitlePickerV1(action(current,"software-grant-"+mutation.get("operation").textValue()),request(mutation));
            assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));assertEquals(request(mutation),GrantPickerControlEffects.request(command));
            assertEquals(GrantTitleCodec.request(current,request(mutation)),new GrantPickerControlEffects(definitions.grantQuery(),(b,r)->{throw new AssertionError();},()->{throw new AssertionError();},(c,a,v)->{throw new AssertionError();}).prepare(command).additionalFields());
        }
        assertEquals(0,dispatches[0]);
    }
    @Test void originalWholeHolderAndSelectionProofsRejectBooleanIdsAndFalseTransfer()throws Exception {
        JsonNode send=original().get("rows").get(3);Context current=current(send);GrantRequest request=request(send);
        for(int mode=0;mode<6;mode++){ObjectNode n=object(send.get("native")).deepCopy();switch(mode){
            case 0->n.put("recipient_character_full_id",true);case 1->n.put("frame_verified",1);case 2->n.remove("transfer_verified");
            case 3->object(n.path("before").path("requested_title_holders").get(0)).put("holder_character_full_id",RECIPIENT);
            case 4->object(n.path("after").path("requested_title_holders").get(0)).put("available",false);
            case 5->object(n.get("before")).put("warning_confirmation_required",true);default->throw new AssertionError();}
            assertThrows(IllegalArgumentException.class,()->GrantTitleCodec.decode(raw(n),current,request));}
        GrantResult submitted=GrantTitleCodec.decode(raw(send.get("native")),current,request);
        ObjectNode q=object(send.get("native")).deepCopy();q.put("operation","query").put("status","observed").put("dispatch_invoked",false).put("native_call_completed",false).put("selection_verified",false).put("transfer_verified",false);
        GrantResult observed=GrantTitleCodec.decode(raw(q),current,GrantPickerControlEffects.queryRequest(request));
        assertTrue(GrantPickerControlEffects.proves(current,current,request,submitted,observed));
        var pending=new GrantResult(submitted.operation(),GrantStatus.PENDING,true,true,true,true,true,false,false,submitted.before(),submitted.after(),"");
        assertFalse(GrantPickerControlEffects.proves(current,current,request,pending,observed));
    }
    @Test void canonicalUnknownBlocksChangedParametersAndLegacyScopeCannotBeBypassed()throws Exception {
        JsonNode row=original().get("rows").get(3);Context current=current(row);GrantRequest request=request(row);var facade=new InteractionCapabilities(definitions(),new PlanningReadPort(){public <T>PlanningReadResult<T>read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError();}},new ActionCoordinatorPort(){public ActionReceipt execute(ActionCommand c){throw new AssertionError();}public ActionReceipt reconcile(String id){throw new AssertionError();}});
        var command=facade.prepareGrantTitlePickerV1(action(current,"software-unknown-grant"),request);
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual packet outcome unavailable",List.of(REF)));
        var changed=new GrantRequest(GrantOperation.SEND,request.recipient(),List.of(new FullId(999)),List.of(new FullId(999)),Optional.empty(),Optional.empty());
        assertEquals(Optional.of(receipt),RootGrantTitlePublicProducts.retained(List.of(receipt),current,changed));
        assertThrows(IllegalArgumentException.class,()->RootGrantTitlePublicProducts.retained(List.of(receipt,receipt),current,changed));
        Map<String,byte[]> pending=new TreeMap<>();original().get("pending_originals").properties().forEach(e->pending.put(e.getKey(),StrictJson.canonical(e.getValue())));
        assertEquals(1,RootGrantLegacyClaims.blockers(pending,current,changed).size());
        assertTrue(RootGrantLegacyClaims.blockers(Map.of(),current,changed).isEmpty()); // Pure DATA comparison is never a lease or runtime admission.
        var unrelated=new GrantRequest(GrantOperation.SEND,new CharacterId(RECIPIENT+1),changed.targets(),changed.expectedSelected(),Optional.empty(),Optional.empty());
        assertTrue(RootGrantLegacyClaims.blockers(pending,current,unrelated).isEmpty());
    }
    @Test void replacementJavaSessionRetainsCanonicalUnknownAndEveryLegacyPendingFile()throws Exception {
        JsonNode row=original().get("rows").get(3);Context current=current(row);GrantRequest requested=request(row);
        var facade=new InteractionCapabilities(definitions(),new PlanningReadPort(){public <T>PlanningReadResult<T>read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError("retaining UNKNOWN does not query");}},new ActionCoordinatorPort(){public ActionReceipt execute(ActionCommand c){throw new AssertionError("retaining UNKNOWN must not resend");}public ActionReceipt reconcile(String id){throw new AssertionError("retaining UNKNOWN must not reconcile implicitly");}});
        var command=facade.prepareGrantTitlePickerV1(action(current,"unknown-before-replacement"),requested);
        var unknown=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"original result remains unknown",List.of(REF)));
        var originalBefore=current.before();var replacementBefore=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(originalBefore.machineId(),new GameGeneration(originalBefore.game().pid()+1,new PythonOnlyUInt64(new BigInteger("18446744073709551610"))),originalBefore.frame(),originalBefore.observationVersion());
        var replacementSource=new org.xar.ck3.control.g2.common.G2Source(current.source().machineId(),"2026-10-24T09:00:00Z",current.source().exactBuild(),current.source().sourceRef());
        var replacement=new Context(replacementBefore,replacementSource,"replacement-session",current.connectionGeneration().add(BigInteger.ONE),current.build(),current.deadline(),current.controls());
        var changed=new GrantRequest(GrantOperation.SEND,requested.recipient(),List.of(new FullId(999)),List.of(new FullId(999)),Optional.empty(),Optional.empty());
        assertEquals(Optional.of(unknown),RootGrantTitlePublicProducts.retained(List.of(unknown),replacement,changed));
        assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        var pending=new TreeMap<String,byte[]>();original().get("pending_originals").properties().forEach(e->pending.put(e.getKey(),StrictJson.canonical(e.getValue())));
        var before=new TreeMap<String,String>();pending.forEach((name,bytes)->before.put(name,ActionCodec.sha256(bytes)));
        assertEquals(1,RootGrantLegacyClaims.blockersAcrossJavaReplacement(pending,replacement,changed).size());
        assertTrue(RootGrantLegacyClaims.blockers(pending,replacement,changed).isEmpty(),"the explicit legacy branch retains its original physical-PID scope");
        pending.forEach((name,bytes)->assertEquals(before.get(name),ActionCodec.sha256(bytes),"Java comparison preserves every original UNKNOWN byte"));
    }
    @Test void actualResolvedOriginalsRequireBothOriginalResultAndMatchingResolver()throws Exception {
        for(JsonNode row:original().get("rows"))if(!row.get("operation").textValue().equals("query")) {
            Context current=current(row);var requested=request(row);var files=new TreeMap<String,byte[]>();row.get("originals").properties().forEach(e->files.put(e.getKey(),StrictJson.canonical(e.getValue())));
            assertEquals(3,files.size(),"actual original execute writes claim/result/resolver for this terminal fixture");
            assertTrue(RootGrantLegacyClaims.blockersAcrossJavaReplacement(files,current,requested).isEmpty());
            for(String suffix:List.of(".result.json",".resolved.json")) {
                var missing=new TreeMap<>(files);assertTrue(missing.keySet().removeIf(name->name.endsWith(suffix)));
                assertEquals(1,RootGrantLegacyClaims.blockersAcrossJavaReplacement(missing,current,requested).size(),suffix+" alone cannot release UNKNOWN");
            }
            var altered=new TreeMap<>(files);String resolver=altered.keySet().stream().filter(name->name.endsWith(".resolved.json")).findFirst().orElseThrow();
            ObjectNode wrong=object(StrictJson.parse(altered.get(resolver),1<<20)).deepCopy();wrong.put("request_id","foreign-original");altered.put(resolver,StrictJson.canonical(wrong));
            assertEquals(1,RootGrantLegacyClaims.blockersAcrossJavaReplacement(altered,current,requested).size());
        }
    }
    @Test void coldVerifierRequiresOriginalLegacyPreparationAndNeverCallsLiveQuery()throws Exception {
        JsonNode row=original().get("rows").get(3);Context current=current(row);var definitions=definitions();int[] legacyChecks={0};
        var effects=new GrantPickerControlEffects(definitions.grantQuery(),(b,r)->{throw new AssertionError("cold replay cannot query a later live frame");},()->{throw new AssertionError("cold replay must use its passed original archive");},(c,a,archive)->{legacyChecks[0]++;throw new IllegalArgumentException("original legacy census absent");});
        var body=InteractionArguments.body(current).put("mutation_kind","GRANT");InteractionArguments.grant(body,request(row));
        var command=new ActionCommand("software-grant-cold",current.before(),current.source(),current.sessionId(),new OperationKey(GrantTitleCodec.step(GrantOperation.SEND)),InteractionArguments.app(body),action(current,"unused").expected(),action(current,"unused").claims(),current.deadline());
        var query=GrantPickerControlEffects.queryRequest(request(row));var queryBody=InteractionArguments.body(current);InteractionArguments.grant(queryBody,query);
        var readRequest=new PlanningReadRequest(current.before(),current.source(),current.sessionId(),definitions.grantQuery().operation(),InteractionArguments.app(queryBody),current.deadline());
        var originalRead=InteractionDirectPublicProductionTest.receipt(definitions.grantQuery(),readRequest,raw(row.get("native")));
        var ack=originalRead.original();var attempt=new ActionState.Attempt(ack.requestId(),java.time.Instant.parse("2026-10-24T00:00:00Z"),originalRead.before().binding(),effects.prepare(command));
        var control=new ActionState.ControlApplied(originalRead,GrantPickerControlEffects.OBSERVER,GrantPickerControlEffects.expectedValues());
        var settled=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,control));
        var verifier=effects.archived(GrantOperation.SEND,REF).verifier();assertThrows(IllegalArgumentException.class,()->verifier.verify(null,settled,null));assertEquals(1,legacyChecks[0]);
        var unknown=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"unknown",List.of(REF)));
        assertThrows(IllegalArgumentException.class,()->verifier.verify(null,unknown,null));assertEquals(1,legacyChecks[0]);
    }
    @Test void javaCensusColdConsumerUsesActualCoreHistoryWithoutAnyLiveManagedScope()throws Exception {
        JsonNode row=original().get("rows").get(3);Context old=current(row);var data=RootManagedSessionScopeTest.dataCore(temporary.resolve("actual-grant-cold-store"));
        var before=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(data.configuration().machineId(),old.before().game(),old.before().frame(),old.before().observationVersion());
        var source=new org.xar.ck3.control.g2.common.G2Source(data.configuration().machineId(),old.source().observedAtUtc(),old.source().exactBuild(),data.source());
        var current=new Context(before,source,old.sessionId(),old.connectionGeneration(),old.build(),old.deadline(),old.controls());
        var definitions=definitions();var requested=request(row);var body=InteractionArguments.body(current).put("mutation_kind","GRANT");InteractionArguments.grant(body,requested);
        var command=new ActionCommand("cold-java-grant-data",before,source,current.sessionId(),new OperationKey(GrantTitleCodec.step(GrantOperation.SEND)),InteractionArguments.app(body),action(current,"unused").expected(),action(current,"unused").claims(),current.deadline());
        var queryBody=InteractionArguments.body(current);InteractionArguments.grant(queryBody,GrantPickerControlEffects.queryRequest(requested));
        var readRequest=new PlanningReadRequest(before,source,current.sessionId(),definitions.grantQuery().operation(),InteractionArguments.app(queryBody),current.deadline());
        var receipt=InteractionDirectPublicProductionTest.receipt(definitions.grantQuery(),readRequest,raw(row.get("native")));
        var effects=new GrantPickerControlEffects(definitions.grantQuery(),(b,r)->{throw new AssertionError("cold verifier cannot query");},()->{throw new AssertionError("cold verifier uses the supplied original archive");},(c,a,archive)->{throw new AssertionError("explicit static historical DATA branch is exercised below");});
        data.core().writer().locked(same->{var head=same.head();var archive=data.core().archive().withSession(same);Path state=data.configuration().ledger().snapshot().getParent(),store=state.resolve("native-session").resolve("grant-title-picker-actions");
            var observed=new RootManagedSessionScope.Observation(current.before().machineId(),current.sessionId(),before,source,"software-no-live-launch",state,state,data.configuration().ledger().lock(),List.of(data.source()),head.state().sequence(),head.digest(),Optional.empty());
            byte[] bound=RootManagedSessionScope.bindCommand(RootManagedSessionScope.encode(observed),command,List.of(data.source()));ExactRef observedRef=archive.preserveMaterial(new RawJson(bound));
            var identity=org.xar.ck3.control.build.SharedSourceFiles.nativeDirectory(state);
            ObjectNode census=StrictJson.object().put("schema","xar.java.grant-once-census/v2").put("machine_id",current.before().machineId()).put("original_store",store.toString()).put("directory_present",false).put("parent_present",false).put("capture_head_sha256",head.digest());
            census.putNull("parent_identity");census.putNull("directory_identity");census.putArray("complete_parent_names");census.putArray("complete_names");census.putArray("files");census.putArray("blocking_original_claims");
            census.putObject("state_directory_identity").put("volume_serial_decimal",identity.volumeSerialDecimal()).put("file_id_decimal",identity.fileIdDecimal()).put("creation_filetime_decimal",identity.creationFiletimeDecimal());
            var names=census.putArray("complete_state_names");try(var entries=java.nio.file.Files.newDirectoryStream(state)){for(Path path:entries)names.add(path.getFileName().toString());}
            census.set("java_session_observation",observedRef.toJson());ExactRef censusRef=archive.preserveMaterial(raw(census));var base=effects.prepare(command);
            var nativeRequest=new NativeRequest(base.step(),base.requiredCapability(),base.additionalFields(),List.of(censusRef));
            var attempt=new ActionState.Attempt(receipt.original().requestId(),java.time.Instant.parse("2026-10-24T00:00:00Z"),receipt.before().binding(),nativeRequest);
            RootGrantLegacyClaims.verifyOriginals(data.core(),same,store,List.of(data.source()),command,attempt,archive);
            var changed=census.deepCopy();changed.put("capture_head_sha256","a".repeat(64));ExactRef wrong=archive.preserveMaterial(raw(changed));
            var wrongAttempt=new ActionState.Attempt(attempt.requestId(),attempt.submittedAt(),attempt.guard(),new NativeRequest(base.step(),base.requiredCapability(),base.additionalFields(),List.of(wrong)));
            assertThrows(IllegalArgumentException.class,()->RootGrantLegacyClaims.verifyOriginals(data.core(),same,store,List.of(data.source()),command,wrongAttempt,archive));
            assertThrows(IllegalArgumentException.class,()->RootGrantLegacyClaims.verifyOriginals(data.core(),same,store,List.of(REF),command,attempt,archive));
            assertEquals(head.digest(),same.head().digest(),"archive verification cannot write a claim, INTENT or new authority");return null;});
    }
    private static InteractionCapabilities.Installation definitions(){return new InteractionCapabilities.Installation(new InteractionCapabilities.Sources(REF,REF,REF,REF,REF,REF,REF,REF,REF,REF),new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),new InteractionCapabilities.RootHeirSource(){public PlanningReadResult<HeirSubject> read(Context c){throw new AssertionError();}public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session s,Context c){throw new AssertionError();}});}
    private static ActionContext action(Context c,String id){return new ActionContext(c,id,new ExpectedPostcondition(1,c.before(),c.source(),GrantPickerControlEffects.OBSERVER,GrantPickerControlEffects.expectedValues()),new Claims(Set.of(),Set.of(),Set.of(c.actor()),Set.of("foreground-window")));}
    private static Context current(JsonNode row){return InteractionDirectPublicProductionTest.project(InteractionDirectPublicProductionTest.frame(object(row.get("frame")),Build.CROZIER3),Build.CROZIER3);}
    private static GrantRequest request(JsonNode row){GrantOperation op=GrantOperation.valueOf(row.get("operation").textValue().toUpperCase(Locale.ROOT));return new GrantRequest(op,new CharacterId(RECIPIENT),List.of(new FullId(11),new FullId(22)),op==GrantOperation.SEND?List.of(new FullId(11),new FullId(22)):op==GrantOperation.SELECT?List.of(new FullId(11)):List.of(),op==GrantOperation.SELECT?Optional.of(new FullId(22)):Optional.empty(),op==GrantOperation.SELECT?Optional.of(true):Optional.empty());}
    private static PublicBindings.Value args(String n){return new PublicBindings.Value(new RawJson(n.getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode object(JsonNode n){assertInstanceOf(ObjectNode.class,n);return (ObjectNode)n;}
    private static ObjectNode node(RawJson n){return object(StrictJson.parse(n.bytes(),1<<20));}
    private static RawJson raw(JsonNode n){return new RawJson(StrictJson.canonical(n));}
    private static synchronized ObjectNode original()throws Exception {
        if(corpus!=null)return corpus;
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");assertNotNull(python,"required actual original-producer interpreter");assertNotNull(repository,"required original repository fixture");assertFalse(python.isBlank());assertFalse(repository.isBlank());repository=Path.of(repository).toRealPath().toString();
        String script="""
            import copy,json,os,pathlib,sys,tempfile
            root=pathlib.Path(os.environ['XAR_SOURCE_REPOSITORY']).resolve(strict=True)
            sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
            import test_ordinary_interaction as fixture
            from xar_autoplayer.bridge import grant_title_picker_v1 as grant
            from xar_autoplayer.bridge.ingame_decisions_open_contract import opening_binding
            from xar_autoplayer.bridge.service import GameplayBridgeService
            recipient=2147483650
            def window(selected,holder):
                return dict(available=True,window_visible=True,window_binding_verified=True,rows_complete=True,native_can_send=True,warning_confirmation_required=False,
                    rows=[dict(title_full_id=t,holder_character_full_id=holder,selected=t in selected,selectable=True) for t in [11,22]],selected_title_full_ids=selected,
                    requested_title_holders=[dict(title_full_id=t,available=True,holder_character_full_id=holder) for t in [11,22]])
            class Driver(fixture.MemoryDriver):
                grant_title_picker_v1=grant.execute
                def __init__(self,folder,pending=False):
                    super().__init__(folder);setattr(self,grant.PERMISSION,True);self.caps={'game.command.'+op+'-grant-title-picker-v1' for op in grant.OPERATIONS};self.calls=0;self.pending=pending
                def _execute_primitive_step(self,step,**kwargs):
                    self.calls+=1;op=step.split('-')[0];binding=opening_binding(self.take_snapshot());sel=[11,22] if op=='send' else [11] if op=='select' else []
                    after=[11,22] if op in ['send','select'] else []
                    self.native=dict(schema=grant.SCHEMA,operation=op,exact_build='1.20.0.3',executable_sha256=fixture.c.EXE_SHA256.upper(),recipient_character_full_id=recipient,
                        owner_thread_verified=True,frame_verified=True,source_abi_pins_verified=True,dispatch_invoked=op!='query',native_call_completed=op!='query',selection_verified=op=='select',
                        transfer_verified=op=='send' and not self.pending,business_full_credit=False,unavailable_reason='',
                        status='pending' if self.pending else {'query':'observed','prepare':'prepared','select':'selection_observed','send':'holder_transfer_observed'}[op],
                        before=window(sel,binding['played_character_id']),after=window(after,recipient if op=='send' else binding['played_character_id']),
                        **{k:binding[k] for k in ['native_revision','connection_generation','game_pid','played_character_id','date_raw']})
                    return copy.deepcopy(self.native)
            rows=[]
            for op in ['query','prepare','select','send']:
                with tempfile.TemporaryDirectory() as folder:
                    driver=Driver(pathlib.Path(folder));frame=driver.take_snapshot();service=GameplayBridgeService(driver)
                    selected=[11,22] if op=='send' else [11] if op=='select' else []
                    public=service.grant_title_picker_v1(op,recipient,expected_revision=1,requested_title_full_ids=[11,22],expected_selected_title_full_ids=selected,title_full_id=22 if op=='select' else None,desired_selected=True if op=='select' else None)
                    originals={} if op=='query' else {p.name:json.loads(p.read_text(encoding='utf-8')) for p in (pathlib.Path(folder)/'native-session'/'grant-title-picker-actions').iterdir()}
                    rows.append(dict(operation=op,frame=frame,native=driver.native,public=public,originals=originals))
            with tempfile.TemporaryDirectory() as folder:
                driver=Driver(pathlib.Path(folder),True);service=GameplayBridgeService(driver)
                service.grant_title_picker_v1('send',recipient,expected_revision=1,requested_title_full_ids=[11,22],expected_selected_title_full_ids=[11,22])
                blocked=False
                try:service.grant_title_picker_v1('send',recipient,expected_revision=1,requested_title_full_ids=[999],expected_selected_title_full_ids=[999])
                except ValueError:blocked=True
                originals={p.name:json.loads(p.read_text(encoding='utf-8')) for p in (pathlib.Path(folder)/'native-session'/'grant-title-picker-actions').iterdir()}
                json.dump(dict(rows=rows,pending_changed_parameters_blocked=blocked,pending_dispatches=driver.calls,pending_originals=originals),sys.stdout,separators=(',',':'),allow_nan=False)
            """;
        var builder=new ProcessBuilder(python,"-c",script).directory(Path.of(repository).toFile()).redirectErrorStream(true);builder.environment().put("XAR_SOURCE_REPOSITORY",repository);builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();var output=new java.util.concurrent.CompletableFuture<byte[]>();Thread reader=Thread.ofVirtual().start(()->{try{output.complete(process.getInputStream().readNBytes((1<<20)+1));}catch(java.io.IOException failure){output.completeExceptionally(failure);}});process.getOutputStream().close();
        try{assertTrue(process.waitFor(40,java.util.concurrent.TimeUnit.SECONDS),"original Grant Service timeout");byte[] bytes=output.get(5,java.util.concurrent.TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=(1<<20));corpus=node(new RawJson(bytes));return corpus;}
        finally{if(process.isAlive())process.destroyForcibly();reader.join(5000);}
    }
}
