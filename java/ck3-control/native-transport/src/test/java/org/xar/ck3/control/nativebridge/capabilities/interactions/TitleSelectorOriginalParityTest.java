package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionTitleSelectorReads.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Software packets through actual preinstalled arbitrary families and original unchanged Python normalizers. */
final class TitleSelectorOriginalParityTest {
    private static final ExactRef SOURCE=new ExactRef("software-title-source",1,"a".repeat(64));
    private static final java.time.Instant NOW=java.time.Instant.parse("2026-10-24T00:00:00Z");
    private static final Context CONTEXT=context();
    private static Context context(){
        var source=new org.xar.ck3.control.g2.common.G2Source("software-title-machine",NOW.toString(),"1.20.0.4@sha256:"+Build.CROZIER4.sha256(),SOURCE);
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(707),BigInteger.valueOf(41),BigInteger.valueOf(24000)),"software-title-snapshot",BigInteger.valueOf(7),"episode-1");
        var before=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),frame,1);
        return new Context(before,source,"software-title-session",BigInteger.ONE,Build.CROZIER4,NOW.plusSeconds(60),new ControlFrame(true,true,true,1,707L,707,"episode-1",false,null,null,List.of()));
    }
    @TempDir Path temp;
    @Test void actualFamiliesIssueArbitrarySelectorsRetainIdentityAndSerializeStrictly() {
        var reads=new InteractionTitleSelectorReads(SOURCE,SOURCE);var catalog=new RootReadContractCatalog(List.of(),reads.families());reads.attach(catalog);
        for(var selector:selectors()) {
            assertEquals(selector,decodeSelector(encodeSelector(selector)));var actual=reads.issue(selector);assertSame(actual,reads.issue(decodeSelector(encodeSelector(selector))));
            var request=request(actual,selector);assertEquals(operation(selector),actual.operation());assertTrue(actual.hasPureReplay());
            var prepared=actual.prepare(request,"software-title");assertEquals(NativeStepDiscriminator.identity(operation(selector)).nativeStep(),prepared.step());assertEquals(Optional.of(selector.kind().capability()),prepared.requiredCapability());
            var nativeFields=StrictJson.parse(prepared.additionalFields().bytes());assertFalse(nativeFields.has("group_context"));assertFalse(nativeFields.has("expected_revision"));
            assertEquals(selector instanceof AppointmentSelector?7:0,nativeFields.size());
        }
        assertThrows(IllegalArgumentException.class,()->reads.attach(new RootReadContractCatalog(List.of(),new InteractionTitleSelectorReads(SOURCE,SOURCE).families())));
        assertNotSame(reads.issue(new LawSelector(new FullId(1))),reads.issue(new LawSelector(new FullId(2))));
        var multi = new ClaimsSelector(List.of(new Int32Id(2), new Int32Id(1)));
        var multiDecoded = InteractionTitleSelectorReads.decodeSelector(InteractionTitleSelectorReads.encodeSelector(multi));
        assertEquals(multi, multiDecoded);
        assertEquals(List.of(new Int32Id(2), new Int32Id(1)), ((ClaimsSelector)multiDecoded).titles());
        var multiReq = new TitleClaimsPublicCodec.Request(java.math.BigInteger.ZERO, multi);
        assertEquals(multiReq, TitleClaimsPublicCodec.decode(multi.kind(), TitleClaimsPublicCodec.encode(multiReq)));
    }
    @Test void originalPythonNormalizersAgreeWithActualTypedDecoderReplayAndPublication()throws Exception {
        var reads=new InteractionTitleSelectorReads(SOURCE,SOURCE);reads.attach(new RootReadContractCatalog(List.of(),reads.families()));
        for(var selector:selectors()) {
            var actual=reads.issue(selector);var nativeResult=wire(selector);var receipt=receipt(request(actual,selector),actual.contractId(),nativeResult);
            var decoded=actual.decode(receipt);assertEquals(decoded,actual.replay(receipt));assertArrayEquals(raw(nativeResult).bytes(),decoded.original().bytes());
            assertEquals(StrictJson.parse(raw(nativeResult).bytes()),oracle(selector,nativeResult));
            var publicOriginal=TitleClaimsPublicCodec.publication(new PlanningReadResult.Known<>(decoded,receipt,SOURCE),selector);var publication=StrictJson.parse(publicOriginal.bytes());if(selector instanceof AppointmentSelector)assertTrue(new String(publicOriginal.bytes(),StandardCharsets.UTF_8).contains("\"x\":-0.0"));
            assertEquals(CONTEXT.before().frame().revision().toString(),publication.get("queried_revision").textValue());assertEquals("18446744073709551615",publication.get(selector instanceof AppointmentSelector?"pump_epoch":"query_sequence").textValue());
            assertEquals(StrictJson.parse(raw(nativeResult).bytes()),StrictJson.parse(decoded.original().bytes()));
            if(selector instanceof AppointmentSelector){assertEquals("episode-1",publication.get("episode_run_id").textValue());assertEquals("1",publication.get("queried_connection_generation").textValue());assertTrue(publication.get("title_appointment").get("candidates").get(0).get("score_raw").isTextual());}
            else assertTrue(publication.get("read_only").booleanValue());
        }
    }
    @Test void publicRequestsPreserveDefaultsNullableIdsAndExactUint64Boundaries() {
        for(var selector:selectors()){var request=new TitleClaimsPublicCodec.Request(StrictJson.UINT64_MAX,selector);assertEquals(request,TitleClaimsPublicCodec.decode(selector.kind(),TitleClaimsPublicCodec.encode(request)));}
        var defaults=TitleClaimsPublicCodec.decode(Kind.APPOINTMENT,raw("{\"expected_revision\":0}"));assertEquals(new AppointmentSelector(new AppointmentRequest(Optional.empty(),0,32,Optional.empty(),Optional.empty())),defaults.selector());
        for(String value:List.of("true","0.0","null","9007199254740992","\"00\"","\"18446744073709551616\""))assertThrows(IllegalArgumentException.class,()->TitleClaimsPublicCodec.decode(Kind.APPOINTMENT,raw("{\"expected_revision\":"+value+"}")));
        for(String value:List.of("{\"expected_revision\":0,\"candidate_offset\":null}","{\"expected_revision\":0,\"candidate_limit\":0}","{\"expected_revision\":0,\"requested_title_id\":0}","{\"expected_revision\":0,\"actor_id\":707}"))assertThrows(IllegalArgumentException.class,()->TitleClaimsPublicCodec.decode(Kind.APPOINTMENT,raw(value)));
        assertThrows(IllegalArgumentException.class,()->TitleClaimsPublicCodec.decode(Kind.CLAIMS,raw("{\"expected_revision\":0,\"title_ids\":[2,2]}")));
        assertThrows(IllegalArgumentException.class,()->TitleClaimsPublicCodec.decode(Kind.HOLDER,raw("{\"expected_revision\":0,\"title_id\":2147483648}")));
    }
    @Test void wrongNativeFrameTypesOrderAndOriginalCommandAreRejectedBeforePublication()throws Exception {
        for(var selector:selectors()) {
            var contract=contract(SOURCE,selector);var result=wire(selector);
            if(selector instanceof AppointmentSelector)result.put("native_revision",CONTEXT.revision().add(BigInteger.ONE));
            else ((ObjectNode)result.get(selector instanceof LawSelector?"title_own_laws":selector instanceof ClaimsSelector?"player_claims":"title_holder")).put("actor_character_id",1);
            assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(request(contract,selector),contract.contractId(),result)));
        }
        var selector=new LawSelector(new FullId(4294967294L));var contract=contract(SOURCE,selector);var malformed=wire(selector);((ObjectNode)malformed.get("title_own_laws")).put("native_law_count",true);
        assertThrows(IllegalArgumentException.class,()->contract.replay(receipt(request(contract,selector),contract.contractId(),malformed)));
        var foreign=new LawSelector(new FullId(4));assertThrows(IllegalArgumentException.class,()->contract.prepare(request(contract,foreign),"software-title"));
    }
    @Test void nativeEmptyUnavailableAndPresentRowsRetainTheirDifferentOriginalMeanings()throws Exception {
        for(var selector:selectors())if(!(selector instanceof AppointmentSelector)){
            var actual=contract(SOURCE,selector);var original=wire(selector);String field=selector instanceof LawSelector?"title_own_laws":selector instanceof ClaimsSelector?"player_claims":"title_holder";
            var value=(ObjectNode)original.get(field);value.put("status","unavailable").put("available",false).put("unavailable_reason","software_native_unavailable");original.put("status","unavailable");
            if(selector instanceof LawSelector){value.putNull("native_law_count").putNull("laws").putNull("single_heir_member");}
            else if(selector instanceof ClaimsSelector)value.putNull("claims");
            else {for(String name:List.of("title_tier_raw","title_tier_key","holder_character_id","holder_immediate_liege_character_id","holder_top_liege_character_id","holder_is_player","holder_in_player_realm"))value.putNull(name);value.put("title_key_available",false).put("title_key_status","unavailable").putNull("title_key").put("title_key_unavailable_reason","software_native_unavailable");}
            assertEquals(StrictJson.parse(raw(original).bytes()),oracle(selector,original));var receipt=receipt(request(actual,selector),actual.contractId(),original);var decoded=actual.decode(receipt);assertEquals(decoded,actual.replay(receipt));var published=StrictJson.parse(TitleClaimsPublicCodec.publication(new PlanningReadResult.Known<>(decoded,receipt,SOURCE),selector).bytes());assertFalse(published.get(field).get("available").booleanValue());assertEquals("software_native_unavailable",published.get(field).get("unavailable_reason").textValue());
        }
        var selector=new LawSelector(new FullId(4294967294L));var packet=wire(selector);var value=(ObjectNode)packet.get("title_own_laws");value.put("native_law_count",1).put("single_heir_member",true);value.putArray("laws").addObject().put("native_definition_id",4294967295L).put("key","single_heir_succession_law");var actual=contract(SOURCE,selector);assertEquals(StrictJson.parse(raw(packet).bytes()),oracle(selector,packet));assertEquals(actual.decode(receipt(request(actual,selector),actual.contractId(),packet)),actual.replay(receipt(request(actual,selector),actual.contractId(),packet)));
    }
    @Test void sharedHolderDecoderRequiresCompleteCurrent4KeysForFixedAndArbitraryContracts()throws Exception {
        var selector=new HolderSelector(new Int32Id(0));
        var arbitraryReads=new InteractionTitleSelectorReads(SOURCE,SOURCE);arbitraryReads.attach(new RootReadContractCatalog(List.of(),arbitraryReads.families()));
        var arbitrary=arbitraryReads.issue(selector);
        var installed=new InteractionCapabilities.Installation(new InteractionCapabilities.Sources(SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE),
                new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of(selector.title())),new InteractionCapabilities.RootHeirSource(){
                    public PlanningReadResult<HeirSubject> read(Context c){throw new AssertionError("holder read must not query an heir");}
                    public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context c){throw new AssertionError("holder read must not query an heir");}
                });
        var fixed=installed.holders().getFirst().contract();
        var fixedRequest=new PlanningReadRequest(CONTEXT.before(),CONTEXT.source(),CONTEXT.sessionId(),fixed.operation(),InteractionArguments.app(InteractionArguments.body(CONTEXT)),CONTEXT.deadline());
        var arbitraryRequest=request(arbitrary,selector);
        var keyFields=List.of("title_key_available","title_key_status","title_key","title_key_unavailable_reason");
        for(boolean available:List.of(true,false)) {
            ObjectNode complete=wire(selector);var holder=(ObjectNode)complete.get("title_holder");
            if(!available) {
                complete.put("status","unavailable");holder.put("status","unavailable").put("available",false).put("unavailable_reason","software_native_unavailable");
                for(String field:List.of("title_tier_raw","title_tier_key","holder_character_id","holder_immediate_liege_character_id","holder_top_liege_character_id","holder_is_player","holder_in_player_realm"))holder.putNull(field);
                holder.put("title_key_available",false).put("title_key_status","unavailable").putNull("title_key").put("title_key_unavailable_reason","software_native_unavailable");
            }
            var fixedReceipt=receipt(fixedRequest,fixed.contractId(),complete);var arbitraryReceipt=receipt(arbitraryRequest,arbitrary.contractId(),complete);
            var value=fixed.decode(fixedReceipt);assertEquals(value,fixed.replay(fixedReceipt));
            assertEquals(value,((HolderValue)arbitrary.decode(arbitraryReceipt)).value());assertEquals(arbitrary.decode(arbitraryReceipt),arbitrary.replay(arbitraryReceipt));
            for(int missing=-1;missing<keyFields.size();missing++) {
                ObjectNode malformed=complete.deepCopy();var fields=(ObjectNode)malformed.get("title_holder");
                if(missing<0)fields.remove(keyFields);else fields.remove(keyFields.get(missing));
                assertHolderRejected(fixed,fixedRequest,arbitrary,arbitraryRequest,malformed);
            }
            for(String field:keyFields) {
                ObjectNode malformed=complete.deepCopy();((ObjectNode)malformed.get("title_holder")).put(field,1);
                assertHolderRejected(fixed,fixedRequest,arbitrary,arbitraryRequest,malformed);
            }
        }
        var oldSource=new org.xar.ck3.control.g2.common.G2Source(CONTEXT.source().machineId(),NOW.toString(),"1.20.0.3@sha256:"+Build.CROZIER3.sha256(),SOURCE);
        var oldContext=new Context(CONTEXT.before(),oldSource,CONTEXT.sessionId(),CONTEXT.connectionGeneration(),Build.CROZIER3,CONTEXT.deadline(),CONTEXT.controls());
        ObjectNode historical=wire(selector);var holder=(ObjectNode)historical.get("title_holder");holder.put("game_version",Build.CROZIER3.version()).put("executable_sha256",Build.CROZIER3.sha256());holder.remove(keyFields);
        var oldFixedRequest=new PlanningReadRequest(oldContext.before(),oldContext.source(),oldContext.sessionId(),fixed.operation(),InteractionArguments.app(InteractionArguments.body(oldContext)),oldContext.deadline());
        var oldArbitraryRequest=new PlanningReadRequest(oldContext.before(),oldContext.source(),oldContext.sessionId(),arbitrary.operation(),arguments(oldContext,selector),oldContext.deadline());
        assertEquals(StrictJson.parse(raw(historical).bytes()),oracle(selector,historical));
        var fixedReceipt=receipt(oldFixedRequest,fixed.contractId(),historical);var arbitraryReceipt=receipt(oldArbitraryRequest,arbitrary.contractId(),historical);
        var oldValue=fixed.decode(fixedReceipt);assertEquals(oldValue,fixed.replay(fixedReceipt));assertTrue(oldValue.titleKey().isEmpty());assertTrue(oldValue.titleKeyUnavailableReason().isEmpty());
        assertEquals(oldValue,((HolderValue)arbitrary.decode(arbitraryReceipt)).value());assertEquals(arbitrary.decode(arbitraryReceipt),arbitrary.replay(arbitraryReceipt));
        holder.put("title_key_available",true);assertHolderRejected(fixed,oldFixedRequest,arbitrary,oldArbitraryRequest,historical);
    }
    private static void assertHolderRejected(ReadContract<TitleHolder> fixed,PlanningReadRequest fixedRequest,ReadContract<Decoded> arbitrary,PlanningReadRequest arbitraryRequest,ObjectNode packet)throws Exception {
        var fixedReceipt=receipt(fixedRequest,fixed.contractId(),packet);var arbitraryReceipt=receipt(arbitraryRequest,arbitrary.contractId(),packet);
        assertThrows(IllegalArgumentException.class,()->fixed.decode(fixedReceipt));assertThrows(IllegalArgumentException.class,()->fixed.replay(fixedReceipt));
        assertThrows(IllegalArgumentException.class,()->arbitrary.decode(arbitraryReceipt));assertThrows(IllegalArgumentException.class,()->arbitrary.replay(arbitraryReceipt));
    }
    private static List<Selector> selectors(){return List.of(new LawSelector(new FullId(4294967294L)),new ClaimsSelector(List.of(new Int32Id(2),new Int32Id(1))),new HolderSelector(new Int32Id(0)),new AppointmentSelector(new AppointmentRequest(Optional.of(new CharacterId(301989889)),0,1,Optional.of(new CharacterId(2013265924L)),Optional.empty())));}
    private static PlanningReadRequest request(ReadContract<Decoded> contract,Selector selector){return new PlanningReadRequest(CONTEXT.before(),CONTEXT.source(),CONTEXT.sessionId(),contract.operation(),arguments(CONTEXT,selector),CONTEXT.deadline());}
    private static ObjectNode wire(Selector selector)throws Exception {
        var n=StrictJson.object().put("step",NativeStepDiscriminator.identity(operation(selector)).nativeStep()).put("accepted",true).put("status","available").put("read_only",true).put("backend_id","native-headless").put("snapshot_revision",CONTEXT.revision()).put("date_raw",CONTEXT.date()).put("query_sequence",StrictJson.UINT64_MAX);
        if(selector instanceof AppointmentSelector){
            n.remove(java.util.List.of("step","query_sequence","snapshot_revision","backend_id","read_only"));
            n.put("schema","ck3-ingame-ui-window-v1").put("available",true).put("status","observed").put("window_kind","title_appointment").put("window_name","title_appointment").put("window_exists",true).put("effective_visible",true).put("enabled",true).put("dispatch_invoked",false).put("verification_pending",false).put("paused",true).put("native_revision",CONTEXT.revision()).put("played_character_id",CONTEXT.actor()).put("application_owner_thread_verified",true).put("gui_owner_binding_verified",true).put("game_version",Build.CROZIER4.version()).put("executable_sha256",Build.CROZIER4.sha256()).put("pump_epoch",StrictJson.UINT64_MAX).put("thread_id",1).put("subject_id_available",true).put("current_subject_id",872415234).put("owner_character_id_available",true).put("owner_character_id",1442840579);
            byte[] original=Files.readAllBytes(Path.of(required("xar.repository.root"),"ck3_autonomous_player/tests/fixtures/appointment_window_snapshot_v1_synthetic.json"));assertEquals(1281,original.length);assertEquals("076edf98308712cf318f89df0c6ac9b9f23444b60f78ed8df616b1af0ca15670",ActionCodec.sha256(original));n.set("title_appointment",StrictJson.parse(original));n.putObject("combat_geometry").putObject("proposed_translation").put("x",-0.0).put("y",0.0);return n;
        }
        String field=selector instanceof LawSelector?"title_own_laws":selector instanceof ClaimsSelector?"player_claims":"title_holder";
        var v=n.putObject(field).put("schema","xar.ck3."+(selector instanceof LawSelector?"title-own-laws":selector instanceof ClaimsSelector?"player-claims":"title-holder")+".v1").put("schema_version",1).put("game_version",Build.CROZIER4.version()).put("executable_sha256",Build.CROZIER4.sha256()).put("status","available").put("available",true).putNull("unavailable_reason").put("snapshot_revision",CONTEXT.revision()).put("date_raw",CONTEXT.date()).put("actor_character_id",CONTEXT.actor());
        switch(selector){
            case LawSelector law->{v.put("title_id",law.title().value()).put("native_law_count",0).put("single_heir_member",false);v.putArray("laws");}
            case ClaimsSelector claims->{var ids=v.putArray("title_ids");var rows=v.putArray("claims");for(var title:claims.titles()){ids.add(title.value());rows.addObject().put("title_id",title.value()).put("present",false).put("state","absent").putNull("strong").putNull("implicit");}}
            case HolderSelector holder->v.put("title_id",holder.title().value()).put("title_tier_raw",1).put("title_tier_key","barony").putNull("holder_character_id").putNull("holder_immediate_liege_character_id").putNull("holder_top_liege_character_id").put("holder_is_player",false).put("holder_in_player_realm",false).put("title_key_available",true).put("title_key_status","available").put("title_key","b_software_fixture").putNull("title_key_unavailable_reason");
            case AppointmentSelector ignored->throw new AssertionError();
        }return n;
    }
    private static PlanningReadReceipt receipt(PlanningReadRequest request,String id,ObjectNode result)throws Exception {
        var packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","software-title").put("ok",true);packet.set("result",result);var original=raw(packet);
        var ack=new NativeActionPort.AckReceived("software-title",true,Optional.of(raw(result)),original,NativeWire.packet(original.bytes()));
        var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),SOURCE,SOURCE,"software-title-authority",NOW,CONTEXT.deadline());
        var guard=new PlanningReadGuard(evidence,true,true,true,"1".repeat(64));return new PlanningReadReceipt(request,id,"software-title",guard,guard,ack);
    }
    private JsonNode oracle(Selector selector,ObjectNode packet)throws Exception {
        String script="""
            import hashlib,importlib.util,json,pathlib,sys,base64
            root=pathlib.Path(sys.argv[1]);p=json.loads(base64.b64decode(sys.argv[2]).decode('utf-8'));kind=p['kind'];n=p['packet'];r=p['request']
            pins={'LAWS':('title_own_laws_contract.py','f91c9a9cfbd1141b037c6bb4e1324a4e53ba81172c634fa66d7a7540bb5bf68b'),'CLAIMS':('player_claims_contract.py','08fc5c228f16491d9faf3b065d5599662d73bbf854e380c5258e7f759ad863fc'),'HOLDER':('title_holder_contract.py','cbd762eb4944837baa7a4caf5500c4e088e72759bc9eb1f7506b0972b4466f81'),'APPOINTMENT':('appointment_window_contract.py','5b7d3003f01f1a097316df75e07e4b6526129d80669698dd0a55cb18f72361db')}
            name,sha=pins[kind];path=root/'ck3_autonomous_player/src/xar_autoplayer/bridge'/name
            assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
            spec=importlib.util.spec_from_file_location('original_title_oracle',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            kwargs=dict(expected_actor_character_id=p['actor'],expected_snapshot_revision=p['native'],expected_date_raw=p['date'])
            if kind=='LAWS':n['title_own_laws']=m.normalize_title_own_laws_v1(n['title_own_laws'],expected_title_id=r['title_id'],**kwargs)
            elif kind=='CLAIMS':n['player_claims']=m.normalize_player_claims_v1(n['player_claims'],expected_title_ids=r['title_ids'],**kwargs)
            elif kind=='HOLDER':n['title_holder']=m.normalize_title_holder_v1(n['title_holder'],expected_title_id=r['title_id'],**kwargs)
            else:
                fields=m.validate_request(int(r['expected_revision']),r['requested_title_id'],r['candidate_offset'],r['candidate_limit'],r['breakdown_character_id'],r['diagnostic_character_id'])
                n=m.normalize_result(n,fields=fields,native_revision=p['native'],date_raw=p['date'],actor_id=p['actor'])
            print(json.dumps(n,separators=(',',':'),sort_keys=True))
            """;
        var input=StrictJson.object().put("kind",selector.kind().name()).put("actor",CONTEXT.actor()).put("native",CONTEXT.revision()).put("date",CONTEXT.date());input.set("packet",packet);input.set("request",StrictJson.parse(TitleClaimsPublicCodec.encode(new TitleClaimsPublicCodec.Request(BigInteger.ZERO,selector)).bytes()));
        Path output=temp.resolve(selector.kind().name()+"-original.log");var process=new ProcessBuilder(required("xar.python"),"-B","-c",script,required("xar.repository.root"),java.util.Base64.getEncoder().encodeToString(input.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))).redirectErrorStream(true).redirectOutput(output.toFile()).start();
        if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new AssertionError("bounded original title normalizer timeout");}assertTrue(Files.size(output)<=65536);assertEquals(0,process.exitValue(),Files.readString(output));return StrictJson.parse(Files.readAllBytes(output));
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"required CI input "+key);assertFalse(value.isBlank());return value;}
    private static RawJson raw(JsonNode value){return raw(value.toString());}
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    @Test void appointmentAndGenericGuiHaveDistinctLogicalReadsWithTheOriginalNativeWire() {
        var gui=new org.xar.ck3.control.nativebridge.capabilities.gui.GuiReads(
                new org.xar.ck3.control.nativebridge.capabilities.gui.GuiReads.Sources(SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE));
        var installed=new InteractionCapabilities.Installation(new InteractionCapabilities.Sources(SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE),
                new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),new InteractionCapabilities.RootHeirSource(){
                    public PlanningReadResult<HeirSubject> read(Context c){throw new AssertionError("not an heir read");}
                    public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context c){throw new AssertionError("not an heir read");}
                });
        var fixed=installed.contracts().stream().filter(read->read.contractId().equals("interactions:current-appointment")).findFirst().orElseThrow();
        var selector=new AppointmentSelector(new AppointmentRequest(Optional.empty(),0,32,Optional.empty(),Optional.empty()));
        var dynamic=contract(SOURCE,selector);
        var selected=NativeStepDiscriminator.IngameWindow.TITLE_APPOINTMENT;
        assertEquals(selected.operationKey(),fixed.operation());assertEquals(selected.operationKey(),dynamic.operation());
        assertNotEquals(gui.semantic.operation(),fixed.operation());
        var bindings=new java.util.ArrayList<ReadContract<?>>(installed.contracts());bindings.add(gui.semantic);
        var otherMetadata=new ExactRef("software-dynamic-source",1,"b".repeat(64));
        var families=new InteractionTitleSelectorReads(otherMetadata,otherMetadata);
        var readCatalog=new RootReadContractCatalog(bindings.stream().map(read->new RootReadContractCatalog.InstalledRead(read,SOURCE)).toList(),families.families());
        families.attach(readCatalog);
        var root=RootExecutableBindings.freeze(List.of(),readCatalog,List.of(),16);
        int initialViews=root.installed().size();
        dynamic=families.issue(selector);
        assertEquals(initialViews,root.installed().size());
        assertTrue(readCatalog.containsIdentity(fixed));assertTrue(readCatalog.containsIdentity(dynamic));
        assertEquals(1,root.installed().stream().filter(step->step.operation().equals(selected.operationKey())).count());
        assertEquals(ExecutableStepBindings.Kind.READ,root.resolve(gui.semantic.operation(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).orElseThrow().kind());
        assertEquals(ExecutableStepBindings.Kind.READ,root.resolve(selected.operationKey(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).orElseThrow().kind());
        var fields=InteractionArguments.body(CONTEXT);InteractionArguments.appointment(fields,selector.request());
        var fixedRequest=new PlanningReadRequest(CONTEXT.before(),CONTEXT.source(),CONTEXT.sessionId(),fixed.operation(),InteractionArguments.app(fields),CONTEXT.deadline());
        var fixedWire=fixed.prepare(fixedRequest,"fixed-appointment");var dynamicWire=dynamic.prepare(request(dynamic,selector),"dynamic-appointment");
        for(var original:List.of(fixedWire,dynamicWire)){
            assertEquals("query-ingame-ui-window-v1",original.step());
            assertEquals("title_appointment",StrictJson.parse(original.additionalFields().bytes()).get("window_kind").textValue());
            NativeStepDiscriminator.requireRequest(selected.operationKey(),ExecutableStepBindings.Kind.READ,original);
            assertFalse(NativeStepDiscriminator.matchesRequest(selected.operationKey(),ExecutableStepBindings.Kind.ACTION,original));
            assertFalse(NativeStepDiscriminator.matchesRequest(selected.operationKey(),ExecutableStepBindings.Kind.READ,
                    new NativeRequest(selected.nativeStep(),Optional.of(selected.capability()),raw("{\"window_kind\":\"army\"}"))));
        }
        var identity=NativeStepDiscriminator.identity(selected.operationKey());
        assertEquals(identity,NativeStepDiscriminator.fromJson(NativeStepDiscriminator.toJson(identity)));
        var historical=NativeStepDiscriminator.toJson(identity);historical.put("schema",NativeStepDiscriminator.LEGACY_SCHEMA);
        assertThrows(IllegalArgumentException.class,()->NativeStepDiscriminator.fromJson(historical));
    }

}
