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
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original C++ software samples remain separate; Java DATA mutations below are not Native frames or exchanges. */
class NativeCurrentCccActorTransition26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256,boolean request) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("advance.request.json", 845, "0116e4afd67cdbb936f946448f0e3f485ca736ff1f25e95c36ac147d598bb2df", true),
        new Artifact("confirm.request.json", 851, "198d77370feafc7279c32abc763799f408d7b5f950bb5c30553e5d89c0febe89", true),
        new Artifact("epoch-confirmed.json", 1665, "25a7f63d85ef03ab39523612537439e948f55fa3a3ce595b661a2ec94fa07313", false),
        new Artifact("query-epoch-one-source.json", 1315, "75c4de89ce7d6250e7caa765f0d9f507041d544d6ddd85411f6038756c0ce588", false),
        new Artifact("query-pending-official-source.json", 1641, "b3192251f34a9064a2f83db1e461570c6f28bdceab3f2b8317dc9a550a7fb8b7", false),
        new Artifact("query-song-source.json", 1310, "c25dfba60b583e93b2f66787596ad95608ed616aaf1ede9a89bf2f8429d0fd95", false),
        new Artifact("query-thirteenth-day-source.json", 1318, "91ce69fa69f96780c29d40f012ba7fa79118ebcc13d752452ba7b00c503e8c8e", false),
        new Artifact("query.request.json", 819, "a06d855dd2b9b9247025fcd3364107491594afef5a00c48a4f5a09b124e6bf0e", true),
        new Artifact("running-unobserved.json", 1345, "572e5d038708c1ae783f44f684db1b19a600acf13c97e0582af52ad630a6045f", false),
        new Artifact("status.request.json", 846, "3a3fed76f7e3f6e7659881e7b38a80852fd5334952c12cf8d496e163d39e8689", true),
        new Artifact("submitted.json", 1721, "e0fa8c1f747826893ed9eeee5ddef160ee3091b0c65115fca54b79c7541ac806", false),
        new Artifact("transition-pending.json", 1356, "f425c16270ebf14e940bcacb9a56a86112f5c2677316596e5c1fd9378fae464c", false)
    );
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static byte[] raw(String name)throws Exception{
        var a=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentCccActorTransition26785313ProducerTest.class.getResourceAsStream("/current267-ccc-transition-cpp-a1126/"+name)){
            if(in==null)throw new IOException("Original C++ CCC transition resource absent");var b=in.readAllBytes();assertEquals(a.bytes(),b.length,name);
            assertEquals(a.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),name);return b;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentCccActorTransitionResult frame(String name)throws Exception{return CurrentCccActorTransitionResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentCccActorTransitionResult data(ObjectNode n)throws IOException{return CurrentCccActorTransitionResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    private static ObjectNode facts(ObjectNode n){return (ObjectNode)n.get("facts_before");}
    private static ObjectNode progress(ObjectNode n){return (ObjectNode)n.get("progress");}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->data(n));}

    @Test void twelveOriginalPinsAndEightTypedResultsPreserveActualEnvelopeStates()throws Exception{
        assertEquals(12,CPP.size());int responses=0,requests=0;
        for(var a:CPP){var e=envelope(a.name());
            if(a.request()){requests++;assertEquals("execute_step",e.get("type").textValue());continue;}
            responses++;assertEquals("command_result",e.get("type").textValue());var r=frame(a.name());
            assertEquals(e.get("request_id").textValue(),r.requestId());assertEquals(e.get("ok").booleanValue(),r.ok());assertEquals(r,CurrentCccActorTransitionResult.decode(r.encode()));
            assertEquals(27,NativeWire.parse(r.encode().bytes()).size());assertNull(NativeWire.parse(r.encode().bytes()).get("core_after").textValue());
            if(r.source().isPresent()){var s=r.source().orElseThrow();assertEquals(15,s.encode().size());assertEquals(s,CurrentCccActorTransitionSource.decode(s.encode()));
                if(s.pending().isPresent())assertEquals(12,s.pending().orElseThrow().encode().size());}
            if(r.progress().isPresent())assertEquals(17,NativeWire.parse(r.encode().bytes()).get("progress").size());
        }
        assertEquals(8,responses);assertEquals(4,requests);
    }

    @Test void fourOriginalRequestFactoriesKeepTheirOwnIdsDeadlinesAndStringCustodyEncoding()throws Exception{
        for(var a:CPP){if(!a.request())continue;
            var e=StrictJson.object(envelope(a.name()),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","ccc_actor_transition","core_control_deadline_unix_ms"));
            var c=StrictJson.object(e.get("ccc_actor_transition"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence","operation_id","actor_epoch"));
            var action=CurrentCccActorTransition.Action.parse(c.get("action").textValue());
            var actual=new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentCccActorTransition.readCore(c.get("expected_core")));
            var request=CurrentCccActorTransition.request(actual,action,c.get("operation_id").textValue(),CurrentCccActorTransition.decimal(c,"provider_generation"),CurrentCccActorTransition.decimal(c,"query_sequence"),CurrentCccActorTransition.decimal(c,"actor_epoch"));
            assertEquals(action.step(),request.step());assertEquals(e.get("step").textValue(),request.step());assertEquals(action.capability(),request.requiredCapability().orElseThrow());
            var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","ccc_actor_transition"));var generated=NativeWire.object(fields.get("ccc_actor_transition"));assertEquals(11,generated.size());
            for(String key:List.of("provider_generation","query_sequence","actor_epoch"))assertTrue(generated.get(key).isTextual(),key);
            var comparison=generated.deepCopy();assertEquals(c.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),comparison.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));comparison.set("executable_sha256",c.get("executable_sha256"));assertEquals(c,comparison);
            assertEquals(0,fields.get("arguments").size());assertEquals(MAX,e.get("core_control_deadline_unix_ms").bigIntegerValue());
            fields.set("core_control_deadline_unix_ms",e.get("core_control_deadline_unix_ms"));byte[] packet=NativeWire.execute(e.get("request_id").textValue(),request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
            var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals(e.get("request_id").textValue(),decoded.requestId());assertEquals(request.step(),decoded.step());assertEquals(BigInteger.ZERO,decoded.expectedRevision().orElseThrow());
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] body=Arrays.copyOfRange(packet,4,packet.length);
            var expected=e.deepCopy();((ObjectNode)expected.get("ccc_actor_transition")).set("executable_sha256",generated.get("executable_sha256"));assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
            String directory=System.getProperty("xar.ccc.java.requests.output.directory");if(directory!=null){assertFalse(directory.isBlank());var out=Path.of(directory).toAbsolutePath();Files.createDirectories(out);assertFalse(Files.isSymbolicLink(out));
                Files.write(out.resolve("java-transition-"+action.wire()+".packet.bin"),packet,StandardOpenOption.CREATE_NEW);Files.write(out.resolve("java-transition-"+action.wire()+".body.json"),body,StandardOpenOption.CREATE_NEW);}
        }
        // Original response IDs deliberately differ from request fixture IDs. Do not fabricate a paired exchange.
        assertNotEquals(envelope("advance.request.json").get("request_id"),envelope("submitted.json").get("request_id"));
    }

    @Test void immutableBeforeSourceAndOriginalPendingStatusDoNotBecomeFreshActorPermission()throws Exception{
        var sent=frame("submitted.json");assertEquals(CurrentCccActorTransitionResult.Status.SUBMITTED,sent.status());assertTrue(sent.effectAttempted());assertTrue(sent.nativeReturned());
        assertEquals(frame("query-song-source.json").source(),sent.source());
        var running=frame("running-unobserved.json");assertEquals(CurrentCccActorTransition.Action.QUERY_OPERATION,running.action());assertTrue(running.source().isEmpty());
        assertTrue(running.accepted());assertTrue(running.effectAttempted());assertEquals(-1,running.progress().orElseThrow().afterActorId());assertEquals(-1,running.progress().orElseThrow().overshootDays());
        var pending=frame("transition-pending.json");assertTrue(pending.source().isEmpty());assertEquals(BigInteger.ZERO,pending.actorEpoch());assertEquals(1,pending.completedNaturalDays());assertTrue(pending.progress().orElseThrow().transitionPending());
        var confirmed=frame("epoch-confirmed.json");assertEquals(BigInteger.ONE,confirmed.actorEpoch());assertEquals(BigInteger.ZERO,confirmed.source().orElseThrow().actorEpoch());assertTrue(confirmed.accepted());assertFalse(confirmed.effectAttempted());assertFalse(confirmed.nativeReturned());
        assertEquals(frame("query-pending-official-source.json").source(),confirmed.source());assertEquals(MAX,confirmed.source().orElseThrow().pending().orElseThrow().originalDeadlineUnixMs());
        var noBefore=token("submitted.json");noBefore.putNull("source");noBefore.put("source_available",false);reject(noBefore);
        var injected=token("transition-pending.json");injected.set("source",source(token("query-pending-official-source.json")));injected.put("source_available",true);reject(injected);
        var wrongEpoch=token("epoch-confirmed.json");wrongEpoch.put("actor_epoch","0");reject(wrongEpoch);
    }

    @Test void naturalDayCountHasThirteenDayBudgetIndependentOfTwoActorFrontiers()throws Exception{
        var day13=frame("query-thirteenth-day-source.json");assertEquals(13,day13.completedNaturalDays());assertEquals(BigInteger.ONE,day13.actorEpoch());
        var s=day13.source().orElseThrow();assertEquals(13,s.maximumNaturalDays());assertEquals(13,s.completedNaturalDays());assertFalse(s.advanceAdmissible());
        var over=token("query-thirteenth-day-source.json");over.put("completed_natural_days",14);reject(over);
        var sourceOver=token("query-thirteenth-day-source.json");source(sourceOver).put("completed_natural_days",14);reject(sourceOver);
        var more=token("query-thirteenth-day-source.json");source(more).put("advance_admissible",true);reject(more);
        var epoch2=token("query-epoch-one-source.json");epoch2.put("actor_epoch","2");reject(epoch2);
        var sourceEpoch2=token("query-epoch-one-source.json");source(sourceEpoch2).put("actor_epoch","2");reject(sourceEpoch2);
        var maxChanged=token("query-song-source.json");source(maxChanged).put("maximum_natural_days",14);reject(maxChanged);
    }

    @Test void pendingAndProgressRequireActualOneTickButAllowUnobservedAfterSentinelWhileRunning()throws Exception{
        for(String field:List.of("arm_attempted","resume_attempted","resume_submitted","exact_day_confirmed","shutdown_safe")){
            var n=token("transition-pending.json");progress(n).put(field,false);reject(n);
        }
        for(String field:List.of("armed","access_cleanup_unknown")){var n=token("transition-pending.json");progress(n).put(field,true);reject(n);}
        var ticks=token("transition-pending.json");progress(ticks).put("completed_daily_ticks",2);reject(ticks);
        var failed=token("transition-pending.json");progress(failed).put("failure_flags",1);reject(failed);
        var overshoot=token("transition-pending.json");progress(overshoot).put("overshoot_days",1);reject(overshoot);
        var same=token("transition-pending.json");progress(same).set("after_actor_id",progress(same).get("before_actor_id"));reject(same);
        var unobserved=token("running-unobserved.json");progress(unobserved).put("after_actor_id",0);reject(unobserved);
        var originalDrift=token("running-unobserved.json");facts(originalDrift).put("played_character_id",0);reject(originalDrift);
    }

    @Test void deferredUnknownRetainsOriginalArmFlagsAndCannotWashIntoKnownMissingClaim()throws Exception{
        // Java DATA mutation, not a new C++ response or a live UNKNOWN receipt.
        var n=token("running-unobserved.json");n.put("status","indeterminate").put("ok",false).put("cleanup_known",false).put("unavailable_reason","deferred_original_owner_unknown");
        var unknown=data(n);assertFalse(unknown.ok());assertFalse(unknown.cleanupKnown());assertTrue(unknown.accepted());assertTrue(unknown.effectAttempted());assertTrue(unknown.nativeReturned());assertTrue(unknown.source().isEmpty());
        assertEquals(frame("running-unobserved.json").progress(),unknown.progress());assertEquals(unknown,CurrentCccActorTransitionResult.decode(unknown.encode()));
        n.put("status","unavailable");reject(n);n.put("status","expired");reject(n);
        var forgedSource=token("running-unobserved.json");forgedSource.set("source",source(token("query-song-source.json")));forgedSource.put("source_available",true);reject(forgedSource);
        var fakeAfter=token("transition-pending.json");fakeAfter.set("core_after",facts(fakeAfter).deepCopy());reject(fakeAfter);
    }

    @Test void fullUint64AndSignedActorsAreExactDataWithoutLocalPlayerRelaxation()throws Exception{
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){
            var n=token("query-song-source.json");facts(n).put("played_character_id",actor);source(n).put("song_actor_id",actor);assertEquals(actor,data(n).factsBefore().orElseThrow().playedCharacterId());
        }
        var max=token("query-song-source.json");for(String key:List.of("provider_generation","query_sequence","connection_generation","ticket_sequence","pump_epoch"))max.put(key,MAX.toString());
        max.put("deadline_unix_ms",MAX).put("thread_id",0xffff_ffffL);assertEquals(MAX,data(max).deadlineUnixMs());assertEquals(MAX,data(max).providerGeneration());
        for(String key:List.of("provider_generation","query_sequence","claim_sequence","actor_epoch","connection_generation")){
            var n=token("query-song-source.json");n.put(key,"18446744073709551616");reject(n);n=token("query-song-source.json");n.put(key,1);reject(n);
        }
        var nullOwner=token("query-song-source.json");nullOwner.putNull("facts_before");reject(nullOwner);
        var local=token("query-song-source.json");facts(local).put("local_player_id",-1);reject(local);
        var sentinel=token("query-song-source.json");source(sentinel).put("song_actor_id",-1);reject(sentinel);
        var floatDay=token("query-song-source.json");floatDay.put("completed_natural_days",0.0);reject(floatDay);
    }

    @Test void roleCaseWitnessAndCanonicalShapeAreOnlyOneWayPrerequisites()throws Exception{
        var n=token("query-song-source.json");source(n).put("advance_admissible",false);assertTrue(data(n).ok());
        var notReady=token("query-song-source.json");source(notReady).put("runtime_ready",false);reject(notReady);
        var pending=token("query-pending-official-source.json");source(pending).put("predecessor_resolved",false);reject(pending);
        var missing=token("query-song-source.json");source(missing).remove("case_start_date_raw");reject(missing);
        var caller=token("query-song-source.json");source(caller).put("caller_actor",44739);reject(caller);
        var reasonType=token("query-song-source.json");reasonType.putNull("unavailable_reason");reject(reasonType);
        var duplicate="{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8);assertThrows(IllegalArgumentException.class,()->new RawJson(duplicate));
        assertThrows(IllegalArgumentException.class,()->new RawJson("{} {}".getBytes(StandardCharsets.UTF_8)));
    }
}
