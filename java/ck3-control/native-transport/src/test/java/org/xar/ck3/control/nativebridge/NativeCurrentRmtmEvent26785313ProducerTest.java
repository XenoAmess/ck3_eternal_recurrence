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
class NativeCurrentRmtmEvent26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256,boolean request) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("ack_chaos.request.json", 742, "592290098eed24aee189c23b9c088df85e841b9fa2c0e98d16553fa83ac7e309", true),
        new Artifact("ack_summary.request.json", 746, "420780dc11ebb075db5bcead0a2ba6d2eed059f5392f2bf939d223c09dc76a45", true),
        new Artifact("indeterminate.json", 1064, "f62e0ca40d6c9d713566aef93b2dfdac4b79f90e457c0a68c02e4b0f27e292a3", false),
        new Artifact("query-available.json", 1621, "60df1025f8b394842296b73a936dc66ba7ece2a135bfe7fcb8bafbe69a66ad68", false),
        new Artifact("query-fullsigned.json", 1623, "2c7e6c16243c993b39fb9e25d3946f6cf48fab6c033087c920cc0fd4b202acf5", false),
        new Artifact("query_chaos.request.json", 749, "659337993c968a7f67bbaaa24a8eef0d01f6d2d6b49ba6c9ce646c5df33668e2", true),
        new Artifact("query_summary.request.json", 753, "b6ea4f36316c50c19e25a787bad5d94deb797ab07379a8af291a55b253d54f48", true)
    );

    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static byte[] raw(String name)throws Exception{
        var a=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentRmtmEvent26785313ProducerTest.class.getResourceAsStream("/current267-rmtm-event-cpp-a01/"+name)){
            if(in==null)throw new IOException("Original RMTM C++ resource absent");
            var b=in.readAllBytes();assertEquals(a.bytes(),b.length,name);
            assertEquals(a.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),name);return b;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentRmtmEventResult frame(String name)throws Exception{return CurrentRmtmEventResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentRmtmEventResult data(ObjectNode n)throws IOException{return CurrentRmtmEventResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    private static ObjectNode facts(ObjectNode n){return (ObjectNode)n.get("facts_before");}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->data(n));}
    private static CoreFrame.Partial actual(ObjectNode c)throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentRmtmActorTransition.readCore(c.get("expected_core")));}

    @Test void originalPinsAndAllThreeTypedResponsesRoundTripWithoutRewritingTheSamples()throws Exception{
        int requests=0,responses=0;assertEquals(7,CPP.size());
        for(var a:CPP){var e=envelope(a.name());if(a.request()){requests++;assertEquals("execute_step",e.get("type").textValue());continue;}
            responses++;assertEquals("command_result",e.get("type").textValue());var r=frame(a.name());
            assertEquals(e.get("ok").booleanValue(),r.successful());assertEquals(r,CurrentRmtmEventResult.decode(r.encode()));assertEquals(24,NativeWire.parse(r.encode().bytes()).size());
            if(r.source().isPresent()){var s=r.source().orElseThrow();assertEquals(6,s.encode().size());assertEquals(s,CurrentRmtmEventSource.decode(s.encode()));}
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
            var e=StrictJson.object(envelope(a.name()),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","rmtm_event","core_control_deadline_unix_ms"));
            var c=StrictJson.object(e.get("rmtm_event"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence","instance_id"));
            var action=CurrentRmtmEvent.Action.parse(c.get("action").textValue());
            var request=CurrentRmtmEvent.request(actual(c),action,NativeWire.integer(c.get("provider_generation"),BigInteger.ZERO,MAX),NativeWire.integer(c.get("query_sequence"),BigInteger.ZERO,MAX),c.get("instance_id").isNull()?Optional.<Integer>empty():Optional.of(CurrentRmtmActorTransition.i32(c.get("instance_id"))));
            assertEquals(action.step(),request.step());assertEquals(e.get("step").textValue(),request.step());assertEquals(action.capability(),request.requiredCapability().orElseThrow());
            var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","rmtm_event"));
            var generated=NativeWire.object(fields.get("rmtm_event"));assertEquals(10,generated.size());assertEquals(0,fields.get("arguments").size());
            assertTrue(generated.get("provider_generation").isIntegralNumber());assertTrue(generated.get("query_sequence").isIntegralNumber());
            var compare=generated.deepCopy();assertEquals(c.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),compare.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
            compare.set("executable_sha256",c.get("executable_sha256"));assertEquals(c,compare); // Only the legal EXE-hash case is normalized.
            assertEquals(MAX,e.get("core_control_deadline_unix_ms").bigIntegerValue());fields.set("core_control_deadline_unix_ms",e.get("core_control_deadline_unix_ms"));
            byte[] packet=NativeWire.execute(e.get("request_id").textValue(),request.step(),e.get("expected_revision").bigIntegerValue(),StrictJson.canonical(fields));
            var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals(e.get("request_id").textValue(),decoded.requestId());assertEquals(action.step(),decoded.step());assertEquals(e.get("expected_revision").bigIntegerValue(),decoded.expectedRevision().orElseThrow());
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] body=Arrays.copyOfRange(packet,4,packet.length);
            var expected=e.deepCopy();((ObjectNode)expected.get("rmtm_event")).set("executable_sha256",generated.get("executable_sha256"));assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
            String directory=System.getProperty("xar.rmtm.java.requests.output.directory");
            if(directory!=null){assertFalse(directory.isBlank());var out=Path.of(directory).toAbsolutePath();Files.createDirectories(out);assertFalse(Files.isSymbolicLink(out));
                Files.write(out.resolve("java-event-"+action.wire()+".packet.bin"),packet,StandardOpenOption.CREATE_NEW);
                Files.write(out.resolve("java-event-"+action.wire()+".body.json"),body,StandardOpenOption.CREATE_NEW);}
        }
        assertEquals(4,count);
        // These are independently authored samples. No request/response ID pairing or live exchange is inferred.
    }

    private static ObjectNode row(ObjectNode n){return (ObjectNode)source(n).get("event_census").get("events").get(0);}
    private static ObjectNode option(ObjectNode n){return (ObjectNode)row(n).get("options").get(0);}

    @Test void fixedAuthoredZeroAndActualNativeCanAreRequiredButNeverInferred()throws Exception{
        var s=frame("query-available.json").source().orElseThrow();assertEquals(1,s.eventCensus().namedRootCount());assertEquals(1,s.eventCensus().events().size());
        var event=s.eventCensus().events().get(0);assertEquals("rmtm.1001",event.definitionKey());assertEquals(1,event.authoredOptionCount());assertEquals(0,event.options().get(0).authoredOptionIndex());assertTrue(s.ackAdmissible());
        assertTrue(event.options().get(0).permittedRole().isEmpty());assertTrue(event.options().get(0).sourceBoundOptionKey().isEmpty());
        var noCan=token("query-available.json");option(noCan).put("native_can_select",false);reject(noCan);source(noCan).put("ack_admissible",false);assertFalse(data(noCan).source().orElseThrow().ackAdmissible());
        var noCase=token("query-available.json");source(noCase).put("case_bound",false);reject(noCase);source(noCase).put("ack_admissible",false);assertTrue(data(noCase).successful());
        var noText=token("query-available.json");option(noText).put("text","");reject(noText);
        var wrongIndex=token("query-available.json");option(wrongIndex).put("authored_option_index",1);reject(wrongIndex);
        var other=token("query-available.json");row(other).put("definition_key","rmtm.other");reject(other);
    }

    @Test void completeCensusCannotHideDuplicatesOrReplaceActualRecipient()throws Exception{
        var dup=token("query-available.json");((ArrayNode)source(dup).get("event_census").get("events")).add(row(dup).deepCopy());reject(dup);
        var count=token("query-available.json");((ObjectNode)source(count).get("event_census")).put("named_root_count",2);reject(count);
        var recipient=token("query-available.json");row(recipient).put("recipient_character_id",-2);reject(recipient);
        var sampled=token("query-available.json");source(sampled).put("sampled_twice",false);reject(sampled);
        var absent=token("query-available.json");source(absent).putNull("fixed_instance_id");reject(absent);
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){var n=token("query-available.json");facts(n).put("played_character_id",actor);row(n).put("recipient_character_id",actor);assertEquals(actor,data(n).factsBefore().orElseThrow().playedCharacterId());}
    }

    @Test void readTextPreservesNulControlsRichtextAndFullUtf8ByteBoundary()throws Exception{
        String astral=new String(Character.toChars(0x1f600));
        for(String value:List.of("","literal\0value\n\t"+(char)0x15,"#P source DATA#!",astral.repeat(4096))){
            var n=token("query-available.json");row(n).put("description",value);assertEquals(value,data(n).source().orElseThrow().eventCensus().events().get(0).description());
        }
        var oversized=token("query-available.json");row(oversized).put("description",astral.repeat(4097));reject(oversized);
        var surrogate=token("query-available.json");row(surrogate).put("opening",String.valueOf((char)0xd800));
        assertThrows(IOException.class,()->CurrentRmtmEventSource.decode(source(surrogate))); // Direct Java DATA avoids UTF8 replacement before this decoder.
        var key=token("query-available.json");row(key).put("definition_key","bad key");reject(key);
        var date=token("query-available.json");facts(date).put("date_raw",Integer.MIN_VALUE);assertEquals(Integer.MIN_VALUE,data(date).factsBefore().orElseThrow().dateRaw());
    }

    @Test void voidSelectionNeverClaimsClosureDateOrSaveAndQueriesCannotCarryEffects()throws Exception{
        for(String flag:List.of("native_handled","event_closed","new_date_observed","physical_save_confirmed")){var n=token("query-available.json");n.put(flag,true);reject(n);}
        var q=frame("query-available.json");assertFalse(q.nativeHandled());assertFalse(q.eventClosed());assertFalse(q.newDateObserved());assertFalse(q.physicalSaveConfirmed());
        var forged=token("query-available.json");forged.put("action","ack_summary").put("status","selection_dispatched").put("instance_id",1).put("claim_sequence","3").put("effect_attempted",true).put("native_returned",true);
        forged.putNull("source");forged.put("source_available",false);reject(forged); // A dispatch cannot discard the immutable beforeSource.
        var c=NativeWire.object(envelope("query_summary.request.json").get("rmtm_event"));var core=actual(c);
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmEvent.request(core,CurrentRmtmEvent.Action.ACK_SUMMARY,BigInteger.ONE,BigInteger.ONE,Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmEvent.request(core,CurrentRmtmEvent.Action.QUERY_CHAOS,BigInteger.ZERO,BigInteger.ZERO,Optional.of(1)));
        assertThrows(IOException.class,()->CurrentRmtmEvent.Action.parse("select_any_event"));
    }

}
