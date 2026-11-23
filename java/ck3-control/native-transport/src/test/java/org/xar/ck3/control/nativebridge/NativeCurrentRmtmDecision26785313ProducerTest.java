package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact original C++ software DATA. Java DATA mutations below are never Native frames or live exchanges. */
class NativeCurrentRmtmDecision26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256,boolean request) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("confirm.request.json", 782, "79df46885c702d9b2ff1a33d66a4dd2e67dacab39586f4da8bb9dec87dc91edd", true),
        new Artifact("indeterminate.json", 1067, "70882741ca72b75f4b7ae1d2a00f6bccf7091fa4ac5207775208a507e8b167f5", false),
        new Artifact("open_detail.request.json", 783, "b5880f2cf475c926d5a1888c876cb758ac810a37f94cf0b1288cdaf79182f388", true),
        new Artifact("open_list.request.json", 760, "face1d99a2bee56691a33d02d5cac714ee868160a5014827a2dc3c0acd4a4382", true),
        new Artifact("query-available.json", 1637, "5431106cd2b43e47c87ee8ddd9da22fef4240e089d51539f17cc7004d475bb66", false),
        new Artifact("query-fullsigned.json", 1638, "e6b5d95087bba28461611698892ccf5f8751d2ad0c9fe251df7fc95d9f1e740f", false),
        new Artifact("query.request.json", 756, "a7b816b7f295e5097dc8447bc956a0e6a6140edb6842a4c9460ea8315be8d46c", true)
    );

    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static byte[] raw(String name)throws Exception{
        var a=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentRmtmDecision26785313ProducerTest.class.getResourceAsStream("/current267-rmtm-decision-cpp-a01/"+name)){
            if(in==null)throw new IOException("Original RMTM C++ resource absent");
            var b=in.readAllBytes();assertEquals(a.bytes(),b.length,name);
            assertEquals(a.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),name);return b;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentRmtmDecisionResult frame(String name)throws Exception{return CurrentRmtmDecisionResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentRmtmDecisionResult data(ObjectNode n)throws IOException{return CurrentRmtmDecisionResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    private static ObjectNode facts(ObjectNode n){return (ObjectNode)n.get("facts_before");}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->data(n));}
    private static CoreFrame.Partial actual(ObjectNode c)throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentRmtmActorTransition.readCore(c.get("expected_core")));}

    @Test void originalPinsAndAllThreeTypedResponsesRoundTripWithoutRewritingTheSamples()throws Exception{
        int requests=0,responses=0;assertEquals(7,CPP.size());
        for(var a:CPP){var e=envelope(a.name());if(a.request()){requests++;assertEquals("execute_step",e.get("type").textValue());continue;}
            responses++;assertEquals("command_result",e.get("type").textValue());var r=frame(a.name());
            assertEquals(e.get("ok").booleanValue(),r.successful());assertEquals(r,CurrentRmtmDecisionResult.decode(r.encode()));assertEquals(24,NativeWire.parse(r.encode().bytes()).size());
            if(r.source().isPresent()){var s=r.source().orElseThrow();assertEquals(21,s.encode().size());assertEquals(s,CurrentRmtmDecisionSource.decode(s.encode()));}
        }
        assertEquals(4,requests);assertEquals(3,responses);
        assertEquals(0,frame("query-available.json").factsBefore().orElseThrow().playedCharacterId());
        assertEquals(-2,frame("query-fullsigned.json").factsBefore().orElseThrow().playedCharacterId());
    }

    @Test void actualUnknownRetainsItsOriginalInformationAndNeverBecomesACompleteSource()throws Exception{
        var u=frame("indeterminate.json");assertFalse(u.successful());assertFalse(u.cleanupKnown());assertTrue(u.source().isEmpty());
        assertEquals(BigInteger.ONE,u.providerGeneration());assertEquals(BigInteger.TWO,u.querySequence());assertEquals(BigInteger.ZERO,u.claimSequence());
        assertFalse(u.effectAttempted());assertFalse(u.nativeReturned());assertEquals("explicit_S0_self_owned_unknown",u.unavailableReason().orElseThrow());
        var wrong=token("indeterminate.json");wrong.put("status","available");reject(wrong);
        var missing=token("query-available.json");missing.putNull("source");reject(missing);
        var dirty=token("query-available.json");dirty.put("cleanup_known",false);reject(dirty);
        var owner=token("query-available.json");owner.putNull("facts_before");reject(owner);
    }

    @Test void uint64PrecisionAndExactShapeCannotCreateAuthority()throws Exception{
        var n=token("query-available.json");n.put("provider_generation",MAX.toString()).put("query_sequence",MAX.toString());
        assertEquals(MAX,data(n).providerGeneration());assertEquals(MAX,data(n).querySequence());
        for(String key:List.of("provider_generation","query_sequence","claim_sequence")){
            var over=token("query-available.json");over.put(key,"18446744073709551616");reject(over);
            var number=token("query-available.json");number.put(key,1);reject(number);
            var padded=token("query-available.json");padded.put(key,"01");reject(padded);
        }
        var caller=token("query-available.json");source(caller).put("caller_index",0);reject(caller);
        var extra=token("query-available.json");extra.put("caller_permission",true);reject(extra);
        var floatActor=token("query-available.json");facts(floatActor).put("played_character_id",0.0);reject(floatActor);
        var local=token("query-available.json");facts(local).put("local_player_id",-1);reject(local);
        var sentinel=token("query-available.json");facts(sentinel).put("played_character_id",-1);reject(sentinel);
        assertThrows(IllegalArgumentException.class,()->new RawJson("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->new RawJson("{} {}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void allOriginalRequestFactoriesKeepTheirOwnIdsMaxDeadlineAndActualWireEncoding()throws Exception{
        int count=0;
        for(var a:CPP){if(!a.request())continue;count++;
            var e=StrictJson.object(envelope(a.name()),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","rmtm_decision","core_control_deadline_unix_ms"));
            var c=StrictJson.object(e.get("rmtm_decision"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence","decision_key"));
            var action=CurrentRmtmDecision.Action.parse(c.get("action").textValue());
            var request=CurrentRmtmDecision.request(actual(c),action,NativeWire.integer(c.get("provider_generation"),BigInteger.ZERO,MAX),NativeWire.integer(c.get("query_sequence"),BigInteger.ZERO,MAX),c.get("decision_key").isNull()?Optional.<CurrentRmtmDecision.DecisionKey>empty():Optional.of(CurrentRmtmDecision.DecisionKey.parse(c.get("decision_key").textValue())));
            assertEquals(action.step(),request.step());assertEquals(e.get("step").textValue(),request.step());assertEquals(action.capability(),request.requiredCapability().orElseThrow());
            var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","rmtm_decision"));
            var generated=NativeWire.object(fields.get("rmtm_decision"));assertEquals(10,generated.size());assertEquals(0,fields.get("arguments").size());
            assertTrue(generated.get("provider_generation").isIntegralNumber());assertTrue(generated.get("query_sequence").isIntegralNumber());
            var compare=generated.deepCopy();assertEquals(c.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),compare.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
            compare.set("executable_sha256",c.get("executable_sha256"));assertEquals(c,compare); // Only the legal EXE-hash case is normalized.
            assertEquals(MAX,e.get("core_control_deadline_unix_ms").bigIntegerValue());fields.set("core_control_deadline_unix_ms",e.get("core_control_deadline_unix_ms"));
            byte[] packet=NativeWire.execute(e.get("request_id").textValue(),request.step(),e.get("expected_revision").bigIntegerValue(),StrictJson.canonical(fields));
            var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals(e.get("request_id").textValue(),decoded.requestId());assertEquals(action.step(),decoded.step());assertEquals(e.get("expected_revision").bigIntegerValue(),decoded.expectedRevision().orElseThrow());
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] body=Arrays.copyOfRange(packet,4,packet.length);
            var expected=e.deepCopy();((ObjectNode)expected.get("rmtm_decision")).set("executable_sha256",generated.get("executable_sha256"));assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
            String directory=System.getProperty("xar.rmtm.java.requests.output.directory");
            if(directory!=null){assertFalse(directory.isBlank());var out=Path.of(directory).toAbsolutePath();Files.createDirectories(out);assertFalse(Files.isSymbolicLink(out));
                Files.write(out.resolve("java-decision-"+action.wire()+".packet.bin"),packet,StandardOpenOption.CREATE_NEW);
                Files.write(out.resolve("java-decision-"+action.wire()+".body.json"),body,StandardOpenOption.CREATE_NEW);}
        }
        assertEquals(4,count);
        // These are independently authored samples. No request/response ID pairing or live exchange is inferred.
    }

    private static ObjectNode row(ObjectNode n){return (ObjectNode)source(n).get("rows").get(0);}
    private static ObjectNode selectedDetailData()throws Exception{
        var n=token("query-available.json");var s=source(n);
        s.put("detail_found",true).put("detail_visible",true).put("detail_enabled",true).put("widget_state",1)
                .put("selected_decision_key","rqa120_continue_decision").put("native_can_confirm",false)
                .put("confirm_tooltip_observed",true).put("confirm_tooltip","");
        row(n).put("is_selected",true).put("can_open_detail",false);return n;
    }

    @Test void fixedFiveKeysAndCompleteRowsDoNotBecomeArbitraryDecisionPermission()throws Exception{
        var s=frame("query-available.json").source().orElseThrow();assertEquals(1,s.rows().size());assertEquals(1,s.groupsCount().orElseThrow());assertEquals(1,s.totalModelRows().orElseThrow());
        assertEquals(CurrentRmtmDecision.DecisionKey.CONTINUE_CORE,s.rows().get(0).decisionKey());assertTrue(s.completeModelCensus());assertFalse(s.confirmAdmissible());
        assertEquals(List.of("rqa120_continue_decision","rqaui_prepare_fifty_decision","rqaui_prepare_fiftyone_decision","rmtm_claim_restoration_decision","rqaui_verify_actual_restoration_decision"),Arrays.stream(CurrentRmtmDecision.DecisionKey.values()).map(CurrentRmtmDecision.DecisionKey::wire).toList());
        var duplicate=token("query-available.json");((ArrayNode)source(duplicate).get("rows")).add(row(duplicate).deepCopy());reject(duplicate);
        var unknown=token("query-available.json");row(unknown).put("decision_key","arbitrary_decision");reject(unknown);
        var noCount=token("query-available.json");source(noCount).putNull("total_model_rows");reject(noCount);
        var noCase=token("query-available.json");source(noCase).put("case_bound",false);reject(noCase);row(noCase).put("can_open_detail",false);assertTrue(data(noCase).successful());
        assertThrows(IOException.class,()->CurrentRmtmDecision.DecisionKey.parse("rqaui_prepare_fifty_days"));
    }

    @Test void nativeCanFalseAndObservedTooltipAreDataNotReverseAdmissibility()throws Exception{
        var n=selectedDetailData();assertEquals(Optional.of(false),data(n).source().orElseThrow().nativeCanConfirm());assertFalse(data(n).source().orElseThrow().confirmAdmissible());
        var tooStrong=n.deepCopy();source(tooStrong).put("confirm_admissible",true);reject(tooStrong);
        source(n).put("native_can_confirm",true);assertFalse(data(n).source().orElseThrow().confirmAdmissible());
        var noObserved=n.deepCopy();source(noObserved).put("confirm_tooltip_observed",false).putNull("confirm_tooltip");reject(noObserved);
        var selectedMismatch=n.deepCopy();row(selectedMismatch).put("is_selected",false);reject(selectedMismatch);
        var another=n.deepCopy();source(another).put("other_decision_selected",true);reject(another);
    }

    @Test void completeTooltipPreservesNulRichtextAndUtf8PrecisionWithoutGuessingCosts()throws Exception{
        String astral=new String(Character.toChars(0x1f600));
        for(String text:List.of("","why\0#P literal#!\n\t"+(char)0x15,astral.repeat(4096))){var n=selectedDetailData();source(n).put("confirm_tooltip",text);assertEquals(text,data(n).source().orElseThrow().confirmTooltip().orElseThrow());}
        var tooLong=selectedDetailData();source(tooLong).put("confirm_tooltip",astral.repeat(4097));reject(tooLong);
        var unpaired=selectedDetailData();source(unpaired).put("confirm_tooltip",String.valueOf((char)0xd800));assertThrows(IOException.class,()->CurrentRmtmDecisionSource.decode(source(unpaired)));
        var date=token("query-available.json");facts(date).put("date_raw",Integer.MIN_VALUE);assertEquals(Integer.MIN_VALUE,data(date).factsBefore().orElseThrow().dateRaw());
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){var n=token("query-available.json");facts(n).put("played_character_id",actor);assertEquals(actor,data(n).factsBefore().orElseThrow().playedCharacterId());}
    }

    @Test void onlyTheToggleOpenListMayReturnHandledAndNoVoidDispatchIsBusinessProof()throws Exception{
        // Java DATA only. The genuine sample set contains no navigation dispatch frame.
        var n=token("query-available.json");n.put("action","open_list").put("status","navigation_dispatched").put("effect_attempted",true).put("native_returned",true).put("claim_sequence","3");
        source(n).put("list_visible",false).put("open_list_admissible",true);row(n).put("can_open_detail",false);
        for(boolean handled:new boolean[]{false,true}){n.put("native_handled",handled);assertEquals(handled,data(n).nativeHandled());assertFalse(data(n).decisionApplied());assertFalse(data(n).newDateObserved());assertFalse(data(n).physicalSaveConfirmed());}
        var noBefore=n.deepCopy();noBefore.putNull("source");noBefore.put("source_available",false);reject(noBefore);
        var foreign=n.deepCopy();foreign.put("action","confirm");reject(foreign);
        for(String flag:List.of("decision_applied","new_date_observed","physical_save_confirmed")){var wrong=token("query-available.json");wrong.put(flag,true);reject(wrong);}
        var c=NativeWire.object(envelope("query.request.json").get("rmtm_decision"));var core=actual(c);
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmDecision.request(core,CurrentRmtmDecision.Action.OPEN_LIST,BigInteger.ONE,BigInteger.ONE,Optional.of(CurrentRmtmDecision.DecisionKey.RESTORE)));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmDecision.request(core,CurrentRmtmDecision.Action.CONFIRM,BigInteger.ONE,BigInteger.ONE,Optional.empty()));
    }

}
