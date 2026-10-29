package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.wave2.finance.giftpending.*;

/** Original Python pending producer/classifier -> actual strict native packet consumer -> full persistent reducer roundtrip.
 * The native outer packet is assembled from the pinned .4 C++ serialization contract, not a live capture.
 * Root private restoration admission and canonical READ publication still require their real integration tests.
 */
final class GiftColdReadServiceTest {
    private static final ExactRef REF=new ExactRef("D:/fixture/gift-source.java",1,"a".repeat(64));
    private static final Instant DEADLINE=Instant.parse("2026-10-24T01:00:00Z");
    private static final GiftColdReadService OWNER=new GiftColdReadService(new FinanceReadContracts.Registration(REF,
            new FinanceReadContracts.Permission(Optional.empty(),GiftColdReadService.OPERATION.value(),
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    private static final String SCRIPT="""
        import copy,json,pathlib,runpy,sys,tempfile
        root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        ns=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_cold_recovery_contract_v1.py'))
        from xar_autoplayer.faction_gift_pending_v1 import read_faction_gift_ledger_v1
        with tempfile.TemporaryDirectory() as directory:
            state=pathlib.Path(directory)/'state';pending=ns['pending'](state);ledger=read_faction_gift_ledger_v1(state)
            applied=ns['recovery']();unchanged=copy.deepcopy(applied)
            unchanged['post_observation'].update(player_gold_raw=25000000,gift_opinion_present=False,gift_opinion_modifier_value=None,recipient_opinion_of_player=-40,source_faction_present=True,source_faction_targeting_player=True,source_faction_metrics_available=True,source_faction_power_raw=65000000,source_faction_discontent_raw=45000000,source_faction_member_character_ids=[33011])
            unchanged['save_is_pre_action_checkpoint']=True;unchanged['selected_save_sha256']='a'*64
            wrongsave=copy.deepcopy(unchanged);wrongsave['selected_save_sha256']='b'*64
            wallet=copy.deepcopy(applied);wallet['post_observation']['player_gold_raw']=25000000
            incomplete=copy.deepcopy(applied);incomplete['post_observation']['source_faction_requery_complete']=False;incomplete['independent_faction_storage_lookup_complete']=False
            cases=[{'recovery':r,'expected':ns['evaluate_faction_gift_cold_recovery_v1'](pending,r)} for r in [applied,unchanged,wrongsave,wallet,incomplete]]
            print(json.dumps({'ledger':ledger,'cases':cases},separators=(',',':')))
        """;
    private static JsonNode fixture()throws Exception {
        String configured=System.getProperty("xar.repository.root");
        assertNotNull(configured,"NOT EXECUTED: -Dxar.repository.root must point to actual original producers");
        Path root=Path.of(configured).toAbsolutePath().normalize();
        for(var pin:List.of(
                new String[]{"ck3_autonomous_player/tests/unit/test_faction_gift_cold_recovery_contract_v1.py","94bf100fa16659a4c3bb50b1f9dd9f6714a6e6a07a23a061bd9eefb0f036b938"},
                new String[]{"ck3_autonomous_player/src/xar_autoplayer/faction_gift_cold_recovery_contract_v1.py","72b408eaa65728470ee75a252af704c0586affb1e81e8094d6adcb8487a44429"},
                new String[]{"ck3_autonomous_player/native_bridge/include/xar_bridge/faction_gift_mitigation_action_v1.hpp","178eb31ef73196718c680c2689cab5dd9af8af9e614720278f900f82c2f4d9db"},
                new String[]{"ck3_autonomous_player/native_bridge/src/ck3_12004_faction_gift_router.cpp","6f442c40ebe17cdeb6436d8b280872fcdbd72eee56be288560c4d9e23056a7fe"}))
            assertEquals(pin[1],java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(root.resolve(pin[0])))));
        var builder=new ProcessBuilder(System.getProperty("xar.python","python"),"-c",SCRIPT,root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.redirectErrorStream(true);
        Process process=builder.start();
        if(!process.waitFor(45,TimeUnit.SECONDS)) { process.destroyForcibly();throw new AssertionError("actual original producer did not finish"); }
        byte[] raw=process.getInputStream().readNBytes(1048577);
        assertEquals(0,process.exitValue(),new String(raw,StandardCharsets.UTF_8));assertTrue(raw.length<=1048576);
        return StrictJson.parse(raw,1048576);
    }
    private static PlanningReadReceipt receipt(ObjectNode recovery) { return receipt(recovery,post->{ }); }
    private static PlanningReadReceipt receipt(ObjectNode recovery,java.util.function.Consumer<ObjectNode> nativeMutation) {
        var source=new G2Source("fixture-machine","2026-10-24T00:00:00Z","1.20.0.4",REF);
        var identity=new JointBudgetSelector.Frame(BigInteger.valueOf(32904),BigInteger.ONE,BigInteger.valueOf(53789952));
        var before=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(23456,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(identity,"native:1",BigInteger.valueOf(9),"native-32904-a"),1);
        Obj args=OrdinaryFinanceCollector.obj("source_faction_id",new IntegerValue(BigInteger.valueOf(771)),"recipient_character_id",new IntegerValue(BigInteger.valueOf(33011)));
        var request=new PlanningReadRequest(before,source,"fixture-cold-session",GiftColdReadService.OPERATION,args,DEADLINE);
        // The Python classifier projection deliberately omits unused native fields. Recreate the original C++ defaults
        // before overlaying those facts; mutations below target the resulting original wire observation.
        ObjectNode post=StrictJson.object().put("source_faction_target_character_id",0).put("source_faction_targeting_player",false)
                .put("source_faction_at_war",false).put("source_faction_power_raw",0).put("source_faction_discontent_raw",0)
                .put("recipient_is_ai",false).put("recipient_is_direct_landed_vassal",false);
        post.putNull("source_faction_leader_character_id");post.putArray("source_faction_member_character_ids");
        post.putObject("gift_preview").put("available",false).put("definition_key","").put("definition_stable_hash",0)
                .put("interaction_legal",false).put("auto_accept",false).put("gold_cost_raw",0).put("gold_scale",0).put("opinion_delta",0);
        post.setAll(((ObjectNode)recovery.get("post_observation")).deepCopy());
        post.put("available",true).put("paused",true).put("date_raw",53789952)
                .put("native_snapshot_revision",1).put("player_gold_scale",100000)
                .put("source_faction_metric_scale",post.path("source_faction_metrics_available").asBoolean()?100000:0);
        nativeMutation.accept(post);
        ObjectNode nativeResult=StrictJson.object().put("schema_version",1).put("private",true).put("game_version","1.20.0.4")
                .put("executable_sha256","98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518")
                .put("backend_id","ck3-1.20.0.4-private-faction-gift-mitigation-action-v1")
                .put("contract_stage","exact_build_private_action_source_static_ready_live_pending")
                .put("failure_flags",0).put("frame_failure_stage","none").put("direct_source_failure","none")
                .put("source_faction_id",771).put("recipient_character_id",33011).put("receipt_pending",false).put("executor_invocations",1);
        nativeResult.putNull("ack");nativeResult.putNull("preflight");
        nativeResult.putArray("typed_reds");nativeResult.set("observation",post);
        ObjectNode result=StrictJson.object().put("step",GiftColdReadService.OPERATION.value()).put("accepted",true)
                .put("private_build",true).put("advertised",false).put("status","independent_read_complete");
        result.set("native",nativeResult);result.putNull("receipt");
        ObjectNode frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","cold-source-read").put("ok",true);
        frame.set("result",result);RawJson full=new RawJson(StrictJson.canonical(frame));
        byte[] packet=ByteBuffer.allocate(full.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(full.bytes().length).put(full.bytes()).array();
        var nativeAck=new NativeActionPort.AckReceived("cold-source-read",true,Optional.of(new RawJson(StrictJson.canonical(result))),full,packet);
        var binding=new GuardEvidence(before,source,request.sessionId(),BigInteger.ONE,request.operation(),REF,REF,"fixture-source",DEADLINE.minusSeconds(30),DEADLINE);
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        return new PlanningReadReceipt(request,OWNER.contract().contractId(),nativeAck.requestId(),guard,guard,nativeAck);
    }
    @Test void originalProducerMaterialGoesThroughStrictPacketAndPersistentReducer()throws Exception {
        var original=fixture();var ledger=GiftPendingCodec.decodeLedger(StrictJson.canonical(original.get("ledger")));
        for(JsonNode row:original.get("cases")) {
            var recovery=((ObjectNode)row.get("recovery")).deepCopy();var receipt=receipt(recovery);var decoded=OWNER.contract().replay(receipt);
            recovery.set("post_observation",toNode(decoded.originalPost()));
            var resolution=GiftColdRecovery.resolve(ledger,ledger.pending().orElseThrow().requestId(),GiftColdRecoveryCodec.decodeRecovery(StrictJson.canonical(recovery)));
            JsonNode actual=StrictJson.parse(GiftColdRecoveryCodec.encodeResult(resolution.result()));
            assertEquals(row.get("expected").get("status"),actual.get("status"));
            assertEquals(row.get("expected").get("reason"),actual.get("reason"));
            assertEquals(resolution.ledger(),GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(resolution.ledger())));
            if(resolution.result() instanceof GiftColdRecovery.Unresolved)assertEquals(ledger,resolution.ledger());
            assertFalse(resolution.result().originalRequestReplayAllowed());
        }
    }
    @Test void originalPacketAndTypesCannotBeReplacedByAnAckOrRoundedIdentity()throws Exception {
        var recovery=(ObjectNode)fixture().get("cases").get(0).get("recovery");
        var receipt=receipt(recovery);assertTrue(OWNER.contract().hasPureReplay());
        Obj fields=object(parse(OWNER.contract().prepare(receipt.request(),"new-cold-read").additionalFields().bytes()),"cold fields");
        assertFalse(fields.members().containsKey("expected_revision"));
        assertEquals(new IntegerValue(BigInteger.valueOf(32904)),fields.get("expected_player_character_id"));
        byte[] bad=receipt.original().originalPacket();bad[0]^=1;
        var forged=new NativeActionPort.AckReceived(receipt.requestId(),true,receipt.original().originalResultToken(),receipt.original().originalFrame(),bad);
        assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(new PlanningReadReceipt(receipt.request(),receipt.contractId(),receipt.requestId(),receipt.before(),receipt.after(),forged)));
        for(String field:List.of("queried_source_faction_id","recipient_character_id","player_character_id","snapshot_revision")) {
            var wrong=recovery.deepCopy();((ObjectNode)wrong.get("post_observation")).put(field,true);
            assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(wrong)),field);
        }
    }
    @Test void actualOriginalBodyBoundaryPreservesBomFormattingLargeIntegersAndRejectsDuplicateFields() {
        byte[] raw=("{\"pending\":null,\"retained\":\""+ "x".repeat(200000)+"\",\"sequence\":18446744073709551615}").getBytes(StandardCharsets.UTF_8);
        byte[] bom=new byte[raw.length+3];bom[0]=(byte)0xef;bom[1]=(byte)0xbb;bom[2]=(byte)0xbf;System.arraycopy(raw,0,bom,3,raw.length);
        assertEquals(CanonicalFinanceStateSource.originalBody(raw,4194304),CanonicalFinanceStateSource.originalBody(bom,4194304));
        assertThrows(IllegalArgumentException.class,()->CanonicalFinanceStateSource.originalBody(raw,100));
        assertThrows(IllegalArgumentException.class,()->CanonicalFinanceStateSource.originalBody("{\"pending\":null,\"pending\":{}}".getBytes(StandardCharsets.UTF_8),4194304));
    }
    @Test void originalNativeWireCannotOmitAFieldOrSubstituteNullForADefiniteObservation()throws Exception {
        var recovery=(ObjectNode)fixture().get("cases").get(0).get("recovery");
        var decoded=OWNER.contract().replay(receipt(recovery));
        for(String field:decoded.originalPost().members().keySet()) {
            assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->post.remove(field))),"missing "+field);
            if(!List.of("gift_opinion_modifier_value","source_faction_leader_character_id").contains(field))
                assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->post.putNull(field))),"null "+field);
        }
        assertDoesNotThrow(()->OWNER.contract().replay(receipt(recovery,post->{post.putNull("gift_opinion_modifier_value");post.putNull("source_faction_leader_character_id");})));
    }
    @Test void exactNativeFixedWidthsAndMemberIdentityTypesAreValidatedBeforeTheClassifier()throws Exception {
        var recovery=(ObjectNode)fixture().get("cases").get(0).get("recovery");
        for(String field:List.of("source_faction_power_raw","source_faction_discontent_raw"))
            assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->post.put(field,BigInteger.ONE.shiftLeft(63)))),field);
        assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->post.put("gift_opinion_modifier_value",BigInteger.ONE.shiftLeft(31)))));
        assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->post.put("source_faction_leader_character_id",BigInteger.ONE.shiftLeft(32)))));
        for(var invalid:List.of(StrictJson.object().put("value",true).get("value"),StrictJson.object().put("value",33011.0).get("value"),
                StrictJson.object().put("value",BigInteger.ONE.shiftLeft(32)).get("value")))
            assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->post.putArray("source_faction_member_character_ids").add(invalid))));
        assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->((ObjectNode)post.get("gift_preview")).put("definition_stable_hash",BigInteger.ONE.shiftLeft(64)))));
        assertThrows(IllegalArgumentException.class,()->OWNER.contract().replay(receipt(recovery,post->((ObjectNode)post.get("gift_preview")).remove("available"))));
    }
    @Test void theActualSharedPriorityObserverNoLongerRejectsEverySupportedInputAtItsParserBoundary() {
        byte[] snapshot=org.xar.ck3.control.application.driver.DriverJson.encode(OrdinaryFinanceCollector.obj(
                "active_wars",new Arr(List.of()),"player_armies",new Arr(List.of()),"original_extension",new Text("x".repeat(200000))));
        var observed=org.xar.ck3.control.warbudget.OrdinaryWarPriority.observe(new org.xar.ck3.control.warbudget.OrdinaryWarPriority.Input(
                snapshot,"null".getBytes(StandardCharsets.UTF_8)));
        assertEquals(new Bool(true),object(parse(observed.toJson()),"actual priority output").get("read_only"));
        assertFalse(observed.actionAuthority());assertFalse(observed.deferredOptionalConstruction());
        assertFalse(CanonicalFinanceStateSource.sameOriginalBody("{\"pending\":null,\"retained\":1}".getBytes(StandardCharsets.UTF_8),
                "{\"pending\":null,\"retained\":1.0}".getBytes(StandardCharsets.UTF_8),4194304));
    }
}
