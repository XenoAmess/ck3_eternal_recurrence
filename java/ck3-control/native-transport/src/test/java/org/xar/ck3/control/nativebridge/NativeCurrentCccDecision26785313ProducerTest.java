package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
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
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original C++ samples are exact software DATA; Java mutations do not become Native frames or live evidence. */
class NativeCurrentCccDecision26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256,boolean request) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("blocked-native-why-data.json", 1883, "a7a980eee2338c860ac1e6891f56a13955a2717212e6bf405d739d003fb46c94", false),
        new Artifact("confirm-dispatched.json", 1897, "205e03cf8815d6e08d2f22f8c6c00025d71412457e84f020f46cd09cffa1e1b2", false),
        new Artifact("confirm.request.json", 807, "afbb81ab090a81fbc68ce99e44d6d51fca1191cb24f798e0a8210908f105d44b", true),
        new Artifact("open-detail-dispatched.json", 1875, "c06cf375e3596eb7cb2e87a952f7f47dbe4f0115920273de4fc90af7986d802b", false),
        new Artifact("open-detail.request.json", 807, "7f73b4de8a5de678eff27ee04c098226e8a7ccb5126641c8294a4030b4a77624", true),
        new Artifact("open-list-dispatched.json", 1761, "adb1c94ddd2413fe0a5e35fbd92c910a4eeb4d52fb0be6f15584fcb578c37d66", false),
        new Artifact("open-list.request.json", 775, "7e15828712c4a3b68167a954d5d326e9918ac97f69dca5273220696aed09e779", true),
        new Artifact("query-confirm-source.json", 1860, "130815115fb5b6e7640416cec7eef3e2e699df98db60ebef6507c3d232b8eea1", false),
        new Artifact("query-open-detail-source.json", 1829, "6517972e54fca389c920407e778df0a04fc28fb0f584adf743d2f604f5d84f81", false),
        new Artifact("query-open-list-source.json", 1746, "ad101fe48f323868555886674d8be8b68387ec0cfbf655d19cc5f1f92d12746d", false),
        new Artifact("query.request.json", 772, "52a8e3f6a031e1882c6acadff49a03b620b4b5f5e9d61a97c99cce99528248fa", true)
    );
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static byte[] raw(String name)throws Exception{
        var a=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentCccDecision26785313ProducerTest.class.getResourceAsStream("/current267-ccc-decision-cpp-a1126/"+name)){
            if(in==null)throw new IOException("Original CCC decision C++ resource absent");var b=in.readAllBytes();assertEquals(a.bytes(),b.length,name);assertEquals(a.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),name);return b;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentCccDecisionResult frame(String name)throws Exception{return CurrentCccDecisionResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentCccDecisionResult data(ObjectNode n)throws IOException{return CurrentCccDecisionResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    private static ObjectNode row(ObjectNode n){return (ObjectNode)source(n).get("rows").get(0);}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->data(n));}

    @Test void elevenPinnedOriginalsAndSevenTypedResponsesKeepActualShapeAndStatus()throws Exception{
        assertEquals(11,CPP.size());int responses=0,requests=0;
        for(var a:CPP){var e=envelope(a.name());if(a.request()){requests++;assertEquals("execute_step",e.get("type").textValue());continue;}
            responses++;assertEquals("command_result",e.get("type").textValue());var r=frame(a.name());assertEquals(e.get("ok").booleanValue(),r.successful());assertEquals(r,CurrentCccDecisionResult.decode(r.encode()));
            assertEquals(24,NativeWire.parse(r.encode().bytes()).size());var s=r.source().orElseThrow();assertEquals(26,s.encode().size());assertEquals(s,CurrentCccDecisionSource.decode(s.encode()));
        }
        assertEquals(7,responses);assertEquals(4,requests);
    }

    @Test void fourOriginalFactoriesMatchNumericClaimsAndProduceActualNativeWirePackets()throws Exception{
        for(var a:CPP){if(!a.request())continue;
            var e=StrictJson.object(envelope(a.name()),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","ccc_decision","core_control_deadline_unix_ms"));
            var c=StrictJson.object(e.get("ccc_decision"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence","decision_key"));
            var action=CurrentCccDecision.Action.parse(c.get("action").textValue());var actual=new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentCccActorTransition.readCore(c.get("expected_core")));
            var request=CurrentCccDecision.request(actual,action,NativeWire.integer(c.get("provider_generation"),BigInteger.ZERO,MAX),NativeWire.integer(c.get("query_sequence"),BigInteger.ZERO,MAX),CurrentCccDecision.key(c.get("decision_key")));
            assertEquals(action.step(),request.step());assertEquals(e.get("step").textValue(),request.step());assertEquals(action.capability(),request.requiredCapability().orElseThrow());
            var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","ccc_decision"));var generated=NativeWire.object(fields.get("ccc_decision"));assertEquals(10,generated.size());
            assertTrue(generated.get("provider_generation").isIntegralNumber());assertTrue(generated.get("query_sequence").isIntegralNumber());
            var comparable=generated.deepCopy();assertEquals(c.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),comparable.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));comparable.set("executable_sha256",c.get("executable_sha256"));assertEquals(c,comparable);
            assertEquals(MAX,e.get("core_control_deadline_unix_ms").bigIntegerValue());fields.set("core_control_deadline_unix_ms",e.get("core_control_deadline_unix_ms"));
            byte[] packet=NativeWire.execute(e.get("request_id").textValue(),request.step(),BigInteger.ZERO,StrictJson.canonical(fields));var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals(e.get("request_id").textValue(),decoded.requestId());assertEquals(action.step(),decoded.step());assertEquals(BigInteger.ZERO,decoded.expectedRevision().orElseThrow());
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] body=Arrays.copyOfRange(packet,4,packet.length);var expected=e.deepCopy();((ObjectNode)expected.get("ccc_decision")).set("executable_sha256",generated.get("executable_sha256"));assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
            String directory=System.getProperty("xar.ccc.java.requests.output.directory");if(directory!=null){assertFalse(directory.isBlank());var out=Path.of(directory).toAbsolutePath();Files.createDirectories(out);assertFalse(Files.isSymbolicLink(out));
                Files.write(out.resolve("java-decision-"+action.wire()+".packet.bin"),packet,StandardOpenOption.CREATE_NEW);Files.write(out.resolve("java-decision-"+action.wire()+".body.json"),body,StandardOpenOption.CREATE_NEW);}
        }
    }

    @Test void toggleHandledIsBooleanDataWhileBothOtherCallbacksRemainVoidBeforeSource()throws Exception{
        var opened=frame("open-list-dispatched.json");assertEquals(CurrentCccDecisionResult.Status.NAVIGATION_DISPATCHED,opened.status());assertTrue(opened.nativeHandled());assertFalse(opened.source().orElseThrow().listVisible());
        assertEquals(frame("query-open-list-source.json").source(),opened.source());
        var falseReturn=token("open-list-dispatched.json");falseReturn.put("native_handled",false);assertTrue(data(falseReturn).successful());
        var detail=frame("open-detail-dispatched.json");assertEquals(CurrentCccDecisionResult.Status.SELECTION_DISPATCHED,detail.status());assertFalse(detail.nativeHandled());assertEquals(frame("query-open-detail-source.json").source(),detail.source());
        var confirmed=frame("confirm-dispatched.json");assertEquals(CurrentCccDecisionResult.Status.CONFIRMATION_DISPATCHED,confirmed.status());assertFalse(confirmed.nativeHandled());assertEquals(frame("query-confirm-source.json").source(),confirmed.source());
        for(String name:List.of("open-detail-dispatched.json","confirm-dispatched.json","query-confirm-source.json")){var n=token(name);n.put("native_handled",true);reject(n);}
        for(var a:CPP){if(a.request())continue;var r=frame(a.name());assertFalse(r.decisionApplied());assertFalse(r.newDateObserved());assertFalse(r.physicalSaveConfirmed());
            for(String flag:List.of("decision_applied","new_date_observed","physical_save_confirmed")){var n=token(a.name());n.put(flag,true);reject(n);}}
    }

    @Test void fourCorruptionFlagsAndVariableHalfPredicateRemainObservedCaseData()throws Exception{
        var s=frame("query-confirm-source.json").source().orElseThrow();assertEquals(List.of(false,false,false,true),s.corruptionTraits().orElseThrow());assertTrue(s.fixtureTaxVariablePresent().orElseThrow());assertTrue(s.fixtureTaxExactHalf().orElseThrow());
        var differentHalf=token("query-open-list-source.json");source(differentHalf).put("fixture_tax_exact_half",false);assertFalse(data(differentHalf).source().orElseThrow().fixtureTaxExactHalf().orElseThrow());
        var absent=token("query-confirm-source.json");source(absent).put("case_bound",false).put("confirm_admissible",false);source(absent).putNull("corruption_traits").putNull("fixture_tax_variable_present").putNull("fixture_tax_exact_half");assertTrue(data(absent).successful());
        var invented=token("query-confirm-source.json");source(invented).put("case_bound",false);reject(invented);
        var missing=token("query-confirm-source.json");source(missing).putNull("fixture_tax_exact_half");reject(missing);
        var falseParent=token("query-confirm-source.json");source(falseParent).put("fixture_tax_variable_present",false);reject(falseParent);
        var shortFlags=token("query-confirm-source.json");((com.fasterxml.jackson.databind.node.ArrayNode)source(shortFlags).get("corruption_traits")).remove(0);reject(shortFlags);
        var numeric=token("query-confirm-source.json");((com.fasterxml.jackson.databind.node.ArrayNode)source(numeric).get("corruption_traits")).set(0,StrictJson.object());reject(numeric);
    }

    @Test void tooltipContainsActualNulControlsAndFullUtf8ButNeverInventsExpiry()throws Exception{
        var original=frame("blocked-native-why-data.json").source().orElseThrow();assertFalse(original.nativeCanConfirm().orElseThrow());assertTrue(original.confirmTooltipObserved());assertTrue(original.confirmTooltip().orElseThrow().contains("\0"));assertTrue(original.confirmTooltip().orElseThrow().contains(String.valueOf((char)0x15)));
        String astral=new String(Character.toChars(0x1f600));
        for(String text:List.of("","a\0b\n\t"+(char)0x15,"x".repeat(16384),astral.repeat(4096),"3 years")){var n=token("blocked-native-why-data.json");source(n).put("confirm_tooltip",text);var s=data(n).source().orElseThrow();assertEquals(text,s.confirmTooltip().orElseThrow());assertTrue(s.cooldownExpiryDateRaw().isEmpty());assertFalse(s.cooldownReadbackComplete());}
        var tooLong=token("blocked-native-why-data.json");source(tooLong).put("confirm_tooltip",astral.repeat(4097));reject(tooLong);
        var fakeDate=token("blocked-native-why-data.json");source(fakeDate).put("cooldown_expiry_date_raw",0);reject(fakeDate);
        var fakeComplete=token("blocked-native-why-data.json");source(fakeComplete).put("cooldown_readback_complete",true);reject(fakeComplete);
        var notObserved=token("blocked-native-why-data.json");source(notObserved).put("confirm_tooltip_observed",false);reject(notObserved);
        var nullWhy=token("blocked-native-why-data.json");source(nullWhy).putNull("confirm_tooltip");reject(nullWhy);
    }

    @Test void actualListDetailModelAndNativeCanAreNecessaryOneWayConditions()throws Exception{
        var block=frame("blocked-native-why-data.json");assertTrue(block.successful());assertFalse(block.source().orElseThrow().confirmAdmissible());
        var noPermission=token("query-confirm-source.json");source(noPermission).put("confirm_admissible",false);assertTrue(data(noPermission).successful());
        var cannot=token("query-confirm-source.json");source(cannot).put("native_can_confirm",false);reject(cannot);
        var blocked=token("query-confirm-source.json");source(blocked).put("blocked_by_visible_modal",true);reject(blocked);
        var detail=token("query-open-detail-source.json");source(detail).put("list_enabled",false);reject(detail);
        var falseRow=token("query-open-detail-source.json");row(falseRow).put("is_selected",true);reject(falseRow);
        var open=token("query-open-list-source.json");source(open).put("list_visible",true);reject(open);
        var absent=token("query-open-detail-source.json");source(absent).put("list_found",false);reject(absent);
        var noSource=token("confirm-dispatched.json");noSource.putNull("source");noSource.put("source_available",false);reject(noSource);
        var noClaim=token("confirm-dispatched.json");noClaim.put("claim_sequence","0");reject(noClaim);
    }

    @Test void unknownPreservesDispatchAndSourcesCannotInjectOtherKeysOrPermissions()throws Exception{
        var n=token("confirm-dispatched.json");n.put("status","indeterminate").put("cleanup_known",false).put("unavailable_reason","java_DATA_after_dispatch_unknown");n.putNull("source");n.put("source_available",false);var r=data(n);assertTrue(r.effectAttempted());assertTrue(r.nativeReturned());assertFalse(r.cleanupKnown());assertTrue(r.source().isEmpty());assertEquals(r,CurrentCccDecisionResult.decode(r.encode()));
        n.put("status","unavailable");reject(n);
        var other=token("confirm-dispatched.json");other.put("decision_key","other_decision");reject(other);
        var caller=token("query-confirm-source.json");source(caller).put("caller_can_confirm",true);reject(caller);
        var extraRow=token("query-open-detail-source.json");row(extraRow).put("pointer","1");reject(extraRow);
        var nullOwner=token("query-confirm-source.json");nullOwner.putNull("owner");reject(nullOwner);
        var conflict=token("query-confirm-source.json");conflict.put("source_available",false);reject(conflict);
        assertThrows(IllegalArgumentException.class,()->new RawJson("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void unsignedWitnessesAndSignedCoreActorsKeepPrecisionAndJsonKinds()throws Exception{
        var max=token("query-confirm-source.json");max.put("provider_generation",MAX.toString()).put("query_sequence",MAX.toString());var owner=(ObjectNode)max.get("owner");for(String key:List.of("connection_generation","ticket_sequence","pump_epoch"))owner.put(key,MAX.toString());owner.put("thread_id",0xffff_ffffL);assertEquals(MAX,data(max).providerGeneration());assertEquals(MAX,data(max).owner().orElseThrow().connectionGeneration());
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){var n=token("query-confirm-source.json");((ObjectNode)n.get("facts_before")).put("played_character_id",actor);assertEquals(actor,data(n).factsBefore().orElseThrow().playedCharacterId());}
        var overflow=token("query-confirm-source.json");overflow.put("query_sequence","18446744073709551616");reject(overflow);
        var wrongType=token("query-confirm-source.json");wrongType.put("provider_generation",5);reject(wrongType);
        var local=token("query-confirm-source.json");((ObjectNode)local.get("facts_before")).put("local_player_id",-1);reject(local);
        var floatCount=token("query-confirm-source.json");source(floatCount).put("groups_count",1.0);reject(floatCount);
        var tooMany=token("query-confirm-source.json");source(tooMany).put("groups_count",65);reject(tooMany);
        var untyped=token("query-confirm-source.json");source(untyped).put("native_can_confirm","true");reject(untyped);
    }
}
