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
class NativeCurrentRmtmActorTransition26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256,boolean request) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("advance_day.request.json", 826, "72040b87ec5ddcb7b64891186a3241a9f26729c5da09b3f2a1e1b5b659d9e31e", true),
        new Artifact("confirm_epoch.request.json", 832, "36fadd9b57e74ce4df9af8dc69881773801991864a722dd99374fe504b4e37e0", true),
        new Artifact("indeterminate.json", 969, "c55303e83b641a17a6586643c08d4f688befc0a397da5b4c091c1025a24b7b45", false),
        new Artifact("query-available.json", 1369, "8fc7b475cb7e1968ed5c5d34366303f18c6c5db9fc886334d889b5d5ceaf05aa", false),
        new Artifact("query-fullsigned.json", 1371, "c796dfe1ea73086c38d49a199c58a6995ea9c8dd95d0ce71c73a4af8e3a16b66", false),
        new Artifact("query_operation.request.json", 828, "ad9276cd366b776cdde67643972321128f7173256a1d3321b16fe9f77d875efc", true),
        new Artifact("query_role.request.json", 801, "599bc7c23be5a56a30b8459ce594dcd1f07a8bbb4c2c56f0ed13b16eb25738f8", true)
    );

    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static byte[] raw(String name)throws Exception{
        var a=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentRmtmActorTransition26785313ProducerTest.class.getResourceAsStream("/current267-rmtm-transition-cpp-a01/"+name)){
            if(in==null)throw new IOException("Original RMTM C++ resource absent");
            var b=in.readAllBytes();assertEquals(a.bytes(),b.length,name);
            assertEquals(a.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),name);return b;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentRmtmActorTransitionResult frame(String name)throws Exception{return CurrentRmtmActorTransitionResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentRmtmActorTransitionResult data(ObjectNode n)throws IOException{return CurrentRmtmActorTransitionResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    private static ObjectNode facts(ObjectNode n){return (ObjectNode)n.get("facts_before");}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->data(n));}
    private static CoreFrame.Partial actual(ObjectNode c)throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentRmtmActorTransition.readCore(c.get("expected_core")));}

    @Test void originalPinsAndAllThreeTypedResponsesRoundTripWithoutRewritingTheSamples()throws Exception{
        int requests=0,responses=0;assertEquals(7,CPP.size());
        for(var a:CPP){var e=envelope(a.name());if(a.request()){requests++;assertEquals("execute_step",e.get("type").textValue());continue;}
            responses++;assertEquals("command_result",e.get("type").textValue());var r=frame(a.name());
            assertEquals(e.get("ok").booleanValue(),r.successful());assertEquals(r,CurrentRmtmActorTransitionResult.decode(r.encode()));assertEquals(27,NativeWire.parse(r.encode().bytes()).size());
            if(r.source().isPresent()){var s=r.source().orElseThrow();assertEquals(17,s.encode().size());assertEquals(s,CurrentRmtmActorTransitionSource.decode(s.encode()));}
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
            var e=StrictJson.object(envelope(a.name()),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","rmtm_actor_transition","core_control_deadline_unix_ms"));
            var c=StrictJson.object(e.get("rmtm_actor_transition"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence","operation_id","actor_epoch"));
            var action=CurrentRmtmActorTransition.Action.parse(c.get("action").textValue());
            var request=CurrentRmtmActorTransition.request(actual(c),action,c.get("operation_id").textValue(),CurrentRmtmActorTransition.decimal(c,"provider_generation"),CurrentRmtmActorTransition.decimal(c,"query_sequence"),CurrentRmtmActorTransition.decimal(c,"actor_epoch"));
            assertEquals(action.step(),request.step());assertEquals(e.get("step").textValue(),request.step());assertEquals(action.capability(),request.requiredCapability().orElseThrow());
            var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","rmtm_actor_transition"));
            var generated=NativeWire.object(fields.get("rmtm_actor_transition"));assertEquals(11,generated.size());assertEquals(0,fields.get("arguments").size());
            for(String key:List.of("provider_generation","query_sequence","actor_epoch"))assertTrue(generated.get(key).isTextual(),key);
            var compare=generated.deepCopy();assertEquals(c.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),compare.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
            compare.set("executable_sha256",c.get("executable_sha256"));assertEquals(c,compare); // Only the legal EXE-hash case is normalized.
            assertEquals(MAX,e.get("core_control_deadline_unix_ms").bigIntegerValue());fields.set("core_control_deadline_unix_ms",e.get("core_control_deadline_unix_ms"));
            byte[] packet=NativeWire.execute(e.get("request_id").textValue(),request.step(),e.get("expected_revision").bigIntegerValue(),StrictJson.canonical(fields));
            var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals(e.get("request_id").textValue(),decoded.requestId());assertEquals(action.step(),decoded.step());assertEquals(e.get("expected_revision").bigIntegerValue(),decoded.expectedRevision().orElseThrow());
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] body=Arrays.copyOfRange(packet,4,packet.length);
            var expected=e.deepCopy();((ObjectNode)expected.get("rmtm_actor_transition")).set("executable_sha256",generated.get("executable_sha256"));assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
            String directory=System.getProperty("xar.rmtm.java.requests.output.directory");
            if(directory!=null){assertFalse(directory.isBlank());var out=Path.of(directory).toAbsolutePath();Files.createDirectories(out);assertFalse(Files.isSymbolicLink(out));
                Files.write(out.resolve("java-transition-"+action.wire()+".packet.bin"),packet,StandardOpenOption.CREATE_NEW);
                Files.write(out.resolve("java-transition-"+action.wire()+".body.json"),body,StandardOpenOption.CREATE_NEW);}
        }
        assertEquals(4,count);
        // These are independently authored samples. No request/response ID pairing or live exchange is inferred.
    }

    @Test void originalRoleWitnessDoesNotTurnAvailableDataIntoAdvancePermission()throws Exception{
        var r=frame("query-available.json");var s=r.source().orElseThrow();
        assertFalse(r.accepted());assertTrue(r.progress().isEmpty());assertEquals(BigInteger.ZERO,r.actorEpoch());
        assertEquals(CurrentRmtmActorTransitionSource.Role.SONG,s.role());assertTrue(s.nativeShown().orElseThrow());
        assertFalse(s.runtimeReady());assertFalse(s.predecessorResolved());assertFalse(s.advanceAdmissible());assertFalse(s.confirmAdmissible());
        assertTrue(s.executeTimeIdentityConfirmed().isEmpty());assertEquals(14,s.maximumNaturalDays());
        var forged=token("query-available.json");source(forged).put("advance_admissible",true);reject(forged);
        var falseShown=token("query-available.json");source(falseShown).put("native_shown",false);assertFalse(data(falseShown).source().orElseThrow().nativeShown().orElseThrow());
        var noDefinition=token("query-available.json");source(noDefinition).put("definition_found",false);reject(noDefinition);
        source(noDefinition).putNull("native_shown");assertTrue(data(noDefinition).successful());
        var executeProof=token("query-available.json");source(executeProof).put("execute_time_identity_confirmed",false);
        assertEquals(Optional.of(false),data(executeProof).source().orElseThrow().executeTimeIdentityConfirmed());
    }

    @Test void fourteenNaturalDaysAndTwoFrontiersRemainSeparateExactDomains()throws Exception{
        assertEquals(14,CurrentRmtmActorTransition.MAXIMUM_NATURAL_DAYS);
        for(int day:new int[]{0,1,13,14}){var n=token("query-available.json");n.put("completed_natural_days",day);source(n).put("completed_natural_days",day);assertEquals(day,data(n).completedNaturalDays());}
        for(int day:new int[]{-1,15}){var n=token("query-available.json");n.put("completed_natural_days",day);reject(n);n=token("query-available.json");source(n).put("completed_natural_days",day);reject(n);}
        var epoch=token("query-available.json");epoch.put("actor_epoch","2");reject(epoch);
        var sourceEpoch=token("query-available.json");source(sourceEpoch).put("actor_epoch","2");reject(sourceEpoch);
        var maximum=token("query-available.json");source(maximum).put("maximum_natural_days",13);reject(maximum);
        var capture=token("query-available.json");source(capture).put("case_start_captured",false).put("case_start_date_raw",Integer.MIN_VALUE);
        assertFalse(data(capture).source().orElseThrow().caseStartCaptured());
        var date=token("query-available.json");facts(date).put("date_raw",Integer.MIN_VALUE);source(date).put("case_start_date_raw",Integer.MIN_VALUE);
        assertEquals(Integer.MIN_VALUE,data(date).factsBefore().orElseThrow().dateRaw());
    }

    @Test void retainedUnknownCannotBeWashedIntoKnownNoArmOrFreshRoleSource()throws Exception{
        // Java DATA only: this is not a new Native pending/ARM frame or a real exchange.
        var n=token("indeterminate.json");n.put("action","query_operation").put("operation_id","original-arm-data");
        n.put("accepted",true).put("claim_sequence","9").put("effect_attempted",true).put("native_returned",true);
        var retained=data(n);assertTrue(retained.accepted());assertTrue(retained.effectAttempted());assertTrue(retained.nativeReturned());assertTrue(retained.source().isEmpty());
        assertEquals(retained,CurrentRmtmActorTransitionResult.decode(retained.encode()));
        for(String known:List.of("unavailable","expired","stale_source")){var wrong=n.deepCopy();wrong.put("status",known);reject(wrong);}
        var inject=n.deepCopy();inject.set("source",source(token("query-available.json")));inject.put("source_available",true);reject(inject);
        var fakeAfter=token("query-available.json");fakeAfter.set("core_after",facts(fakeAfter).deepCopy());reject(fakeAfter);
        var role=token("query-available.json");role.put("accepted",true);reject(role);
        var reason=token("query-available.json");reason.putNull("unavailable_reason");reject(reason);
    }

    @Test void requestConstructionRejectsCallerFrontiersAndRetainsPackedSignedActors()throws Exception{
        var c=NativeWire.object(envelope("query_role.request.json").get("rmtm_actor_transition"));var core=actual(c);
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmActorTransition.request(core,CurrentRmtmActorTransition.Action.QUERY_ROLE,"",BigInteger.ONE,BigInteger.ZERO,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmActorTransition.request(core,CurrentRmtmActorTransition.Action.CONFIRM_EPOCH,"original",BigInteger.ONE,BigInteger.ONE,BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmActorTransition.request(core,CurrentRmtmActorTransition.Action.ADVANCE_DAY,"original",MAX.add(BigInteger.ONE),BigInteger.ONE,BigInteger.ZERO));
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){
            var n=token("query-available.json");facts(n).put("played_character_id",actor);source(n).put("song_actor_id",actor);
            assertEquals(actor,data(n).source().orElseThrow().songActorId().orElseThrow());
        }
        assertEquals(MAX,frame("query-available.json").deadlineUnixMs());
    }

}
