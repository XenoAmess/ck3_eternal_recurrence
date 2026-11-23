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

/** Exact owned C++ DATA; mutations below are Java DATA only, never emitted Native or live exchanges. */
class NativeCurrentCccEvent26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256,boolean request) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("cancel-dispatched.json", 2303, "666c4ab5bd250ce7b1412fd22fb73b01abd19ec5e1173c59096f3a58668fc696", false),
        new Artifact("query-cancel-source.json", 2284, "2c307fef2497390511a99c6b9b53bea8c11457832f39c2624fd54c48f11d73cd", false),
        new Artifact("query-original-source.json", 2432, "e4ac5155f86ba028ce942ec941c1ec9b6bc35b6c017f810875c5f82c22ccafec", false),
        new Artifact("query.request.json", 756, "a07740ab14016ccfb5ecee065484f0761af974d108cb3ed2c248f70c664c8838", true),
        new Artifact("select-temporary-cancel.request.json", 786, "26fcdd55eca5d18eb42faa2e8e892bbdd8be08d12a919ac1d7407efad8f252a4", true),
        new Artifact("select-tier-four.request.json", 772, "bb73482e539dd3976ffe51525c3464e0e79c3af1d6d4c8394275de3dcce317c1", true),
        new Artifact("tier-four-dispatched.json", 2454, "db1f2931a3c7511137ba058e35944d76043aa05a16296aff5483558e8cd2039e", false),
        new Artifact("unavailable.json", 820, "8c2d14a0f41adffdff85702a5d7edef315d2579249be05f5a7b878ac58c61940", false)
    );
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static byte[] raw(String name)throws Exception{
        var a=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentCccEvent26785313ProducerTest.class.getResourceAsStream("/current267-ccc-event-cpp-a1126/"+name)){
            if(in==null)throw new IOException("Original CCC event C++ resource absent");var b=in.readAllBytes();assertEquals(a.bytes(),b.length,name);assertEquals(a.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),name);return b;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentCccEventResult frame(String name)throws Exception{return CurrentCccEventResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentCccEventResult data(ObjectNode n)throws IOException{return CurrentCccEventResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    private static ObjectNode census(ObjectNode n){return (ObjectNode)source(n).get("event_census");}
    private static ObjectNode row(ObjectNode n){return (ObjectNode)census(n).get("events").get(0);}
    private static ArrayNode options(ObjectNode n){return (ArrayNode)row(n).get("options");}
    private static ObjectNode authored(ObjectNode n,int index){for(var o:options(n))if(o.get("authored_option_index").intValue()==index)return (ObjectNode)o;throw new IllegalArgumentException("Test requires actual authored identity");}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->data(n));}

    @Test void eightOriginalPinsAndFiveActualTypedResponsesPreserveFullCensus()throws Exception{
        assertEquals(8,CPP.size());int responses=0,requests=0;
        for(var a:CPP){var e=envelope(a.name());if(a.request()){requests++;assertEquals("execute_step",e.get("type").textValue());continue;}
            responses++;assertEquals("command_result",e.get("type").textValue());var actual=frame(a.name());assertEquals(e.get("ok").booleanValue(),actual.successful());
            assertEquals(actual,CurrentCccEventResult.decode(actual.encode()));assertEquals(24,NativeWire.parse(actual.encode().bytes()).size());
            if(actual.source().isPresent()){var s=actual.source().orElseThrow();assertEquals(7,s.encode().size());assertEquals(s,CurrentCccEventSource.decode(s.encode()));
                for(var event:s.encode().get("event_census").get("events")){assertEquals(10,event.size());for(var o:event.get("options"))assertEquals(6,o.size());}}
        }
        assertEquals(5,responses);assertEquals(3,requests);
    }

    @Test void threeOriginalFactoriesKeepNumericCustodyAndExportActualNativeWireBodies()throws Exception{
        for(var a:CPP){if(!a.request())continue;
            var e=StrictJson.object(envelope(a.name()),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","ccc_event","core_control_deadline_unix_ms"));
            var c=StrictJson.object(e.get("ccc_event"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence","instance_id"));
            var action=CurrentCccEvent.Action.parse(c.get("action").textValue());var core=new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentCccActorTransition.readCore(c.get("expected_core")));
            var instance=c.get("instance_id").isNull()?Optional.<Integer>empty():Optional.of(CurrentCccActorTransition.i32(c.get("instance_id")));
            var request=CurrentCccEvent.request(core,action,NativeWire.integer(c.get("provider_generation"),BigInteger.ZERO,MAX),NativeWire.integer(c.get("query_sequence"),BigInteger.ZERO,MAX),instance);
            assertEquals(action.step(),request.step());assertEquals(e.get("step").textValue(),request.step());assertEquals(action.capability(),request.requiredCapability().orElseThrow());
            var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","ccc_event"));var generated=NativeWire.object(fields.get("ccc_event"));assertEquals(10,generated.size());
            assertTrue(generated.get("provider_generation").isIntegralNumber());assertTrue(generated.get("query_sequence").isIntegralNumber());
            var comparable=generated.deepCopy();assertEquals(c.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),comparable.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));comparable.set("executable_sha256",c.get("executable_sha256"));assertEquals(c,comparable);
            assertEquals(MAX,e.get("core_control_deadline_unix_ms").bigIntegerValue());fields.set("core_control_deadline_unix_ms",e.get("core_control_deadline_unix_ms"));
            byte[] packet=NativeWire.execute(e.get("request_id").textValue(),request.step(),BigInteger.ZERO,StrictJson.canonical(fields));var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals(e.get("request_id").textValue(),decoded.requestId());assertEquals(action.step(),decoded.step());assertEquals(BigInteger.ZERO,decoded.expectedRevision().orElseThrow());
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] body=Arrays.copyOfRange(packet,4,packet.length);var expected=e.deepCopy();((ObjectNode)expected.get("ccc_event")).set("executable_sha256",generated.get("executable_sha256"));assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
            String directory=System.getProperty("xar.ccc.java.requests.output.directory");if(directory!=null){assertFalse(directory.isBlank());var out=Path.of(directory).toAbsolutePath();Files.createDirectories(out);assertFalse(Files.isSymbolicLink(out));
                Files.write(out.resolve("java-event-"+action.wire()+".packet.bin"),packet,StandardOpenOption.CREATE_NEW);Files.write(out.resolve("java-event-"+action.wire()+".body.json"),body,StandardOpenOption.CREATE_NEW);}
        }
    }

    @Test void actualAuthoredThreeAndFourAreNotMaterialArrayOrdinalsOrInventedLydRoles()throws Exception{
        var q=frame("query-original-source.json").source().orElseThrow();assertTrue(q.caseBound());assertEquals(4,q.eventCensus().events().get(0).options().get(0).authoredOptionIndex());
        assertEquals(6,q.eventCensus().events().get(0).authoredOptionCount());assertTrue(q.selectDAdmissible());assertTrue(q.selectFAdmissible());
        var cancel=frame("query-cancel-source.json").source().orElseThrow();assertEquals(5,cancel.eventCensus().events().get(0).options().size());assertFalse(cancel.selectDAdmissible());assertTrue(cancel.selectFAdmissible());
        assertFalse(cancel.eventCensus().events().get(0).options().stream().anyMatch(o->o.authoredOptionIndex()==3));
        assertTrue(cancel.eventCensus().events().get(0).options().stream().allMatch(o->o.permittedRole().isEmpty()&&o.sourceBoundOptionKey().isEmpty()));
        var falseD=token("query-original-source.json");authored(falseD,3).put("native_can_select",false);reject(falseD);source(falseD).put("select_d_admissible",false);assertTrue(data(falseD).successful());
        var falseF=token("query-cancel-source.json");authored(falseF,4).put("text","");reject(falseF);source(falseF).put("select_f_admissible",false);assertTrue(data(falseF).successful());
        var role=token("query-original-source.json");authored(role,3).put("permitted_role","tier_four");reject(role);
    }

    @Test void actualCaseProofAndFixedRecipientCannotBeInferredFromCanOrText()throws Exception{
        var noCase=token("query-original-source.json");source(noCase).put("case_bound",false);reject(noCase);
        source(noCase).put("select_d_admissible",false).put("select_f_admissible",false);assertTrue(data(noCase).successful());
        var noInstance=token("query-original-source.json");source(noInstance).putNull("fixed_instance_id");reject(noInstance);
        var wrong=token("query-original-source.json");row(wrong).put("recipient_character_id",0);reject(wrong);
        var foreign=token("query-original-source.json");row(foreign).put("definition_key","xccc.other");reject(foreign);
        var count=token("query-original-source.json");row(count).put("authored_option_count",5);reject(count);
        var duplicate=token("query-original-source.json");((ObjectNode)options(duplicate).get(1)).put("authored_option_index",4);reject(duplicate);
        var partial=token("query-original-source.json");source(partial).put("sampled_twice",false);reject(partial);
    }

    @Test void readUtf8PreservesControlsAndSixteenKiBBoundaryButRejectsNulInFourEventTexts()throws Exception{
        String astral=new String(Character.toChars(0x1f600));
        for(String value:List.of("","#P literal#!\n\t"+(char)0x15,"x".repeat(16384),astral.repeat(4096))){var n=token("query-original-source.json");row(n).put("description",value);assertEquals(value,data(n).source().orElseThrow().eventCensus().events().get(0).description());}
        for(String key:List.of("opening","description","text","disabled_reason")){var n=token("query-original-source.json");(key.equals("opening")||key.equals("description")?row(n):authored(n,3)).put(key,"a\0b");reject(n);}
        var tooLong=token("query-original-source.json");row(tooLong).put("description",astral.repeat(4097));reject(tooLong);
        var source=frame("query-original-source.json").source().orElseThrow();var e=source.eventCensus().events().get(0);
        var broken=new CurrentLydSource.EventRow(e.instanceId(),e.recipientCharacterId(),e.authoredOptionCount(),e.definitionKey(),String.valueOf((char)0xd800),e.description(),e.namedRootBound(),e.windowVisible(),e.windowEnabled(),e.options());
        assertThrows(IllegalArgumentException.class,()->new CurrentCccEventSource(new CurrentLydSource.Events(true,1,List.of(broken)),source.fixedInstanceId(),true,true,true,true));
    }

    @Test void bothVoidSelectionsKeepTheirOwnImmutableBeforeSourceAndNeverClaimClosure()throws Exception{
        var tier=frame("tier-four-dispatched.json");assertEquals(CurrentCccEvent.Action.SELECT_TIER_FOUR,tier.action());assertEquals(frame("query-original-source.json").source(),tier.source());
        var cancel=frame("cancel-dispatched.json");assertEquals(CurrentCccEvent.Action.SELECT_TEMPORARY_CANCEL,cancel.action());assertEquals(frame("query-cancel-source.json").source(),cancel.source());
        assertNotEquals(tier.instanceId(),cancel.instanceId());
        for(var a:CPP){if(a.request())continue;var r=frame(a.name());assertFalse(r.nativeHandled());assertFalse(r.eventClosed());assertFalse(r.newDateObserved());assertFalse(r.physicalSaveConfirmed());
            for(String flag:List.of("native_handled","event_closed","new_date_observed","physical_save_confirmed")){var n=token(a.name());n.put(flag,true);reject(n);}}
        var noBefore=token("tier-four-dispatched.json");noBefore.putNull("source");noBefore.put("source_available",false);reject(noBefore);
        var unspent=token("tier-four-dispatched.json");unspent.put("claim_sequence","0");reject(unspent);
        var alias=token("cancel-dispatched.json");alias.put("instance_id",31);reject(alias);
    }

    @Test void sourceNullUnknownPrecisionAndPackedActorDomainCannotBecomeNewPermission()throws Exception{
        var unavailable=frame("unavailable.json");assertFalse(unavailable.successful());assertTrue(unavailable.source().isEmpty());assertEquals(BigInteger.ZERO,unavailable.providerGeneration());
        var unknown=token("tier-four-dispatched.json");unknown.put("status","indeterminate").put("cleanup_known",false).put("unavailable_reason","owned_java_DATA_unknown");unknown.putNull("source");unknown.put("source_available",false);var u=data(unknown);assertTrue(u.effectAttempted());assertTrue(u.nativeReturned());assertFalse(u.cleanupKnown());assertTrue(u.source().isEmpty());
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){var n=token("query-original-source.json");((ObjectNode)n.get("facts_before")).put("played_character_id",actor);row(n).put("recipient_character_id",actor);assertEquals(actor,data(n).factsBefore().orElseThrow().playedCharacterId());}
        var max=token("query-original-source.json");max.put("provider_generation",MAX.toString()).put("query_sequence",MAX.toString());assertEquals(MAX,data(max).providerGeneration());
        var overflow=token("query-original-source.json");overflow.put("query_sequence","18446744073709551616");reject(overflow);
        var numeric=token("query-original-source.json");numeric.put("provider_generation",5);reject(numeric);
        var local=token("query-original-source.json");((ObjectNode)local.get("facts_before")).put("local_player_id",-1);reject(local);
        var extra=token("query-original-source.json");source(extra).put("caller_index",3);reject(extra);
        assertThrows(IllegalArgumentException.class,()->new RawJson("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8)));
    }
}
