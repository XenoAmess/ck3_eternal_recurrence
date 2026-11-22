package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original SHA-pinned C++ bytes only. Mutations below are Java contract DATA, never live/native exchange evidence. */
class NativeCurrentTedActorTransition26785313ProducerTest {
    private static final BigInteger U64=new BigInteger("18446744073709551615");
    private record Artifact(String name,int bytes,String sha256) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("advance-expired.json",1069,"2241c54059fa5213b0db1516f46b39195820e2a6bbf204a6384bcd8a5c71f689"),
        new Artifact("advance-indeterminate.json",1086,"61651746c59592c3231473873e4111c340609f3e9b7d485d9b696fa02d9d6a67"),
        new Artifact("advance-refused-spent-claim.json",1392,"506f050585fc692abc8bbdc100328a6649a5f4637799b22bcd23079dd55ae399"),
        new Artifact("advance-submitted.json",1740,"b7d7074aaa949cdf7ba16ff551572c6aedff8edd4cd3b13c687206b85d50fe5e"),
        new Artifact("advance_day.request.json",878,"dd11337b41f9ded2511a7cae30b3809ed5c5ced9cef0dd3d4918e09dcf0b4ff2"),
        new Artifact("confirm_epoch.request.json",880,"bf09fa6712ada59b9cb217e590056fa8b068dcaf614320e093bc646c00237ba3"),
        new Artifact("epoch-confirmed.json",1670,"5de9095f1c09b74629c00210a42f3c6f6d520c5e72351fd37262c1162ba7c695"),
        new Artifact("operation-running.json",1444,"9a13b7c7d207eba8c376000cf07b75003cf694670f9b2342a38cb0c392f6c855"),
        new Artifact("query_operation.request.json",880,"2766ff1d6f3023ba7f01d339686c73d5bda0e7d3336adb9323be4c954f94fbbf"),
        new Artifact("query_role.request.json",808,"775b381c5df45aaabe5d1f637770718881187ea302e2efe99a2eef4b4cf7b773"),
        new Artifact("recipient-epoch-query.json",1313,"92a24dc296df494f1d4f98b3a23c16113c1838845a609eb457cc6e0e26d9711f"),
        new Artifact("recipient-pending-query.json",1636,"2cd1440d655caed0f4fc401e0cda8351d94f958b70275fc44747ee25cdcb304a"),
        new Artifact("role-definition-missing.json",1308,"a1c8529ec42162d1888fa59240dc6086111a02cccec720dcb806f59cc9edb8a9"),
        new Artifact("role-shown-false.json",1308,"c87f9e48c116a82f1d49b53c079328494d0da49aa2ceee1a99ccc053959e8aa1"),
        new Artifact("second-advance-submitted.json",1738,"2ef6b04fd2ae849b55006f12fc66ec4f1fdcba5258a34f71a7850a96fdfcc349"),
        new Artifact("second-day-completed.json",1444,"cf420b48b70e24b87467310d7adecaf404a6f354dd883717eec63e00e21440a7"),
        new Artifact("song-query.json",1311,"5868082649455e248e3a9fb5c107546bfb624722273749182a5eec08af52406e"),
        new Artifact("transition-pending.json",1456,"a6802d71e8a2a9a96266cc4ccd79f411b54d083eb3069c32605875ce334db73b")
    );

    private static byte[] raw(String name)throws Exception {
        var expected=CPP.stream().filter(a->a.name().equals(name)).findFirst().orElseThrow(()->new IOException("Unknown original C++ resource: "+name));
        try(var in=NativeCurrentTedActorTransition26785313ProducerTest.class.getResourceAsStream("/current267-ted-cpp-a01/"+name)) {
            if(in==null)throw new IOException("Original TED C++ resource absent: "+name);
            byte[] bytes=in.readAllBytes();assertEquals(expected.bytes(),bytes.length,name);
            assertEquals(expected.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),name);
            return bytes;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static ObjectNode object(ObjectNode parent,String key){return (ObjectNode)parent.get(key);}
    private static CurrentTedActorTransitionResult changed(ObjectNode n)throws IOException {
        return CurrentTedActorTransitionResult.decode(new RawJson(StrictJson.canonical(n)));
    }
    private static CurrentTedActorTransitionResult frame(String name)throws Exception{return changed(token(name));}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
    private static CoreFrame.Partial core(ObjectNode prefix)throws IOException {
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentTedActorTransition.readCore(prefix));
    }

    @Test void fourteenOriginalResponsesRoundtripAndAllEighteenResourcesStayByteExact()throws Exception {
        int responses=0,requests=0;
        for(var a:CPP) {
            var original=envelope(a.name());
            if(original.get("type").textValue().equals("execute_step")){requests++;continue;}
            responses++;var f=changed(NativeWire.object(original.get("result")));
            assertEquals(original.get("ok").booleanValue(),f.ok(),a.name());
            assertEquals(f,CurrentTedActorTransitionResult.decode(f.encode()),a.name());
            assertEquals(26,NativeWire.parse(f.encode().bytes()).size());
            if(f.source().isPresent()) {
                var s=f.source().orElseThrow();assertEquals(12,s.encode().size());
                if(s.pending().isPresent())assertEquals(12,s.pending().orElseThrow().encode().size());
            }
            if(f.progress().isPresent())assertEquals(17,f.progress().orElseThrow().encode().size());
        }
        assertEquals(14,responses);assertEquals(4,requests);
    }

    @Test void fourOriginalRequestsMatchFactoryFieldsWithoutInventedNativeExchange()throws Exception {
        for(String name:List.of("query_role.request.json","advance_day.request.json","query_operation.request.json","confirm_epoch.request.json")) {
            var original=StrictJson.object(envelope(name),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","ted_actor_transition","core_control_deadline_unix_ms"));
            assertEquals("execute_step",original.get("type").textValue());assertEquals(1,original.get("protocol_version").intValue());
            assertEquals(0,original.get("expected_revision").intValue());assertEquals(1899999999999L,original.get("core_control_deadline_unix_ms").longValue());
            var claim=NativeWire.object(original.get("ted_actor_transition"));
            var action=CurrentTedActorTransition.Action.parse(claim.get("action").textValue());
            var prepared=CurrentTedActorTransition.request(core(object(claim,"expected_core")),action,claim.get("operation_id").textValue(),
                new BigInteger(claim.get("provider_generation").textValue()),new BigInteger(claim.get("query_sequence").textValue()),new BigInteger(claim.get("actor_epoch").textValue()));
            var fields=StrictJson.object(NativeWire.parse(prepared.additionalFields().bytes()),Set.of("arguments","ted_actor_transition"));
            assertEquals(0,fields.get("arguments").size());assertEquals(original.get("step").textValue(),prepared.step());
            assertEquals(action.capability(),prepared.requiredCapability().orElseThrow());
            var generated=object(fields,"ted_actor_transition");assertEquals(11,generated.size());
            assertEquals(claim.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),generated.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
            // Hash case is permitted by the actual Native identity parser. Preserve original bytes; compare other fields exactly.
            var comparable=generated.deepCopy();comparable.set("executable_sha256",claim.get("executable_sha256"));assertEquals(claim,comparable);
            for(String outer:List.of("request_id","step","type","protocol_version","core_control_deadline_unix_ms"))assertFalse(generated.has(outer));
        }
    }

    @Test void completeRoleQueryIsNotPermissionWhenDefinitionOrShownWitnessIsAbsent()throws Exception {
        var song=frame("song-query.json");var s=song.source().orElseThrow();
        assertEquals("",song.operationId());assertEquals(CurrentTedActorTransitionSource.Role.SONG,s.role());
        assertTrue(s.advanceAdmissible());assertFalse(s.confirmAdmissible());assertFalse(song.accepted());assertFalse(song.effectAttempted());
        var missing=frame("role-definition-missing.json").source().orElseThrow();
        assertFalse(missing.definitionFound());assertTrue(missing.nativeShown().isEmpty());assertFalse(missing.advanceAdmissible());
        var notShown=frame("role-shown-false.json").source().orElseThrow();
        assertTrue(notShown.definitionFound());assertEquals(Boolean.FALSE,notShown.nativeShown().orElseThrow());assertTrue(notShown.songActorId().isEmpty());
        var n=token("role-definition-missing.json");object(n,"source").put("advance_admissible",true);reject(n);
        n=token("role-shown-false.json");object(n,"source").put("advance_admissible",true);reject(n);
        n=token("song-query.json");object(n,"source").put("runtime_ready",false);reject(n);
        n=token("song-query.json");object(n,"source").put("predecessor_resolved",false);reject(n);
    }

    @Test void submittedAndStatusQueryRetainArmFactsWithoutAFabricatedAfterActorOrRoleLease()throws Exception {
        var submitted=frame("advance-submitted.json");var running=frame("operation-running.json");
        assertEquals(CurrentTedActorTransitionResult.Status.SUBMITTED,submitted.status());assertTrue(submitted.source().isPresent());
        assertEquals(-1,submitted.progress().orElseThrow().afterActorId());assertFalse(submitted.progress().orElseThrow().exactDayConfirmed());
        assertEquals(CurrentTedActorTransition.Action.QUERY_OPERATION,running.action());assertTrue(running.source().isEmpty());
        assertTrue(running.effectAttempted());assertTrue(running.nativeReturned());assertTrue(running.accepted());
        assertEquals(submitted.factsBefore(),running.factsBefore());assertEquals(submitted.progress(),running.progress());
        var n=token("operation-running.json");n.set("source",token("song-query.json").get("source"));n.put("source_available",true);reject(n);
        n=token("advance-submitted.json");n.putNull("source");n.put("source_available",false);reject(n);
    }

    @Test void pendingRequiresExactDailyTickDifferentObservedActorsAndOriginalDeadline()throws Exception {
        var f=frame("transition-pending.json");var p=f.progress().orElseThrow();
        assertEquals(24,p.targetDateRaw()-p.startingDateRaw());assertEquals(1,p.completedDailyTicks());
        assertTrue(p.exactDayConfirmed());assertTrue(p.transitionPending());assertNotEquals(p.beforeActorId(),p.afterActorId());
        assertEquals(BigInteger.ZERO,f.actorEpoch());assertTrue(f.source().isEmpty());
        var witness=frame("recipient-pending-query.json").source().orElseThrow();var pending=witness.pending().orElseThrow();
        assertEquals(f.operationId(),pending.operationId());assertEquals(f.deadlineUnixMs(),pending.originalDeadlineUnixMs());
        assertEquals(f.claimSequence(),pending.claimSequence());assertEquals(p.generation(),pending.generation());
        assertTrue(witness.confirmAdmissible());assertFalse(witness.advanceAdmissible());
        for(String key:List.of("before_actor_id","after_actor_id")) {
            var n=token("transition-pending.json");object(n,"progress").put(key,-1);reject(n);
        }
        var n=token("transition-pending.json");object(n,"progress").put("completed_daily_ticks",0);reject(n);
        n=token("transition-pending.json");object(n,"progress").put("target_date_raw",p.targetDateRaw()+1);reject(n);
        n=token("transition-pending.json");object(n,"progress").put("failure_flags",1);reject(n);
        n=token("transition-pending.json");object(n,"progress").put("generation","0");reject(n);
        n=token("recipient-pending-query.json");object(object(n,"source"),"pending").put("original_deadline_unix_ms",0);reject(n);
        n=token("recipient-pending-query.json");object(object(n,"source"),"pending").put("generation","0");reject(n);
        n=token("recipient-pending-query.json");object(object(n,"source"),"pending").put("claim_sequence","0");reject(n);
        n=token("recipient-pending-query.json");object(n,"source").put("recipient_actor_id",p.beforeActorId());reject(n);
    }

    @Test void epochConfirmationEchoesBeforeSourceZeroWhileTopEpochBecomesOneWithoutGameEffect()throws Exception {
        var f=frame("epoch-confirmed.json");var s=f.source().orElseThrow();
        assertEquals(BigInteger.ONE,f.actorEpoch());assertEquals(BigInteger.ZERO,s.actorEpoch());assertTrue(s.pending().isPresent());
        assertEquals(36423,f.factsBefore().orElseThrow().playedCharacterId());assertEquals(-16777215,s.songActorId().orElseThrow());
        assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertTrue(f.accepted());
        // DATA only: retaining original pending progress is legal; confirm's fresh recipient Core is not the old ARM Core.
        var n=token("epoch-confirmed.json");n.set("progress",token("transition-pending.json").get("progress"));
        assertEquals(36423,changed(n).factsBefore().orElseThrow().playedCharacterId());
        n=token("epoch-confirmed.json");n.putNull("source");n.put("source_available",false);reject(n);
        n=token("epoch-confirmed.json");n.put("effect_attempted",true);reject(n);
        n=token("recipient-pending-query.json");object(n,"source").put("predecessor_resolved",false);reject(n);
        n=token("recipient-pending-query.json");object(n,"source").put("runtime_ready",false);reject(n);
    }

    @Test void secondDayUsesConfirmedRecipientFrontierAndTerminatesAtEpochTwo()throws Exception {
        var role=frame("recipient-epoch-query.json").source().orElseThrow();
        assertEquals(BigInteger.ONE,role.actorEpoch());assertTrue(role.pending().isEmpty());assertTrue(role.advanceAdmissible());
        var submitted=frame("second-advance-submitted.json");assertEquals(BigInteger.ONE,submitted.actorEpoch());
        var done=frame("second-day-completed.json");var p=done.progress().orElseThrow();
        assertEquals(BigInteger.TWO,done.actorEpoch());assertEquals(p.beforeActorId(),p.afterActorId());
        assertEquals(24,p.lastObservedDateRaw()-p.startingDateRaw());assertFalse(p.transitionPending());assertTrue(done.source().isEmpty());
        var n=token("second-day-completed.json");object(n,"progress").put("after_actor_id",17);reject(n);
        n=token("second-day-completed.json");object(n,"progress").put("access_cleanup_unknown",true);reject(n);
        n=token("recipient-epoch-query.json");n.put("actor_epoch","2");object(n,"source").put("actor_epoch","2");reject(n);
    }

    @Test void signedPackedActorIsDistinctFromNonnegativeLocalPlayerAndUnsignedLeasePrecision()throws Exception {
        assertEquals(-16777215,frame("song-query.json").factsBefore().orElseThrow().playedCharacterId());
        assertEquals(U64,frame("song-query.json").providerGeneration());assertEquals(U64,frame("song-query.json").pumpEpoch());
        for(int actor:List.of(0,Integer.MIN_VALUE,-2)) {
            var n=token("song-query.json");object(n,"facts_before").put("played_character_id",actor);object(n,"source").put("song_actor_id",actor);
            assertEquals(actor,changed(n).factsBefore().orElseThrow().playedCharacterId());
        }
        var n=token("song-query.json");object(n,"facts_before").put("played_character_id",-1);object(n,"source").put("song_actor_id",-1);reject(n);
        n=token("song-query.json");object(n,"facts_before").put("local_player_id",-2);reject(n);
        for(String bad:List.of("01","-1","+1","1.0","18446744073709551616")) {
            n=token("song-query.json");n.put("provider_generation",bad);reject(n);
        }
        n=token("song-query.json");n.put("provider_generation",1);reject(n);
        n=token("song-query.json");n.put("actor_epoch","3");reject(n);
    }

    @Test void exactShapesAndUnknownScalarsCannotSupplyMissingSourcePendingOrProgressProof()throws Exception {
        var n=token("song-query.json");n.put("unknown_current_core",true);reject(n);
        n=token("song-query.json");object(n,"source").put("caller_actor",1);reject(n);
        n=token("song-query.json");object(n,"source").remove("native_shown");reject(n);
        n=token("song-query.json");object(n,"source").putNull("native_shown");reject(n);
        n=token("song-query.json");object(n,"source").put("role","caller");reject(n);
        n=token("song-query.json");n.put("status","done");reject(n);
        n=token("song-query.json");n.put("action","set_actor");reject(n);
        n=token("song-query.json");n.put("source_available",false);reject(n);
        n=token("song-query.json");n.set("core_after",StrictJson.object());reject(n);
        n=token("recipient-pending-query.json");object(object(n,"source"),"pending").put("replay",true);reject(n);
        n=token("operation-running.json");object(n,"progress").put("after_scope_verified",true);reject(n);
        n=token("song-query.json");n.put("unavailable_reason",7);reject(n);
    }

    @Test void spentExpiredAndCleanupUnknownRetainOriginalIdsWithoutReplayOrNoDispatchCredit()throws Exception {
        var spent=frame("advance-refused-spent-claim.json");var expired=frame("advance-expired.json");var unknown=frame("advance-indeterminate.json");
        assertEquals(CurrentTedActorTransitionResult.Status.STALE_SOURCE,spent.status());assertTrue(spent.claimSequence().signum()>0);assertFalse(spent.ok());assertFalse(spent.effectAttempted());
        assertEquals(CurrentTedActorTransitionResult.Status.EXPIRED,expired.status());assertTrue(expired.source().isEmpty());
        assertEquals(CurrentTedActorTransitionResult.Status.INDETERMINATE,unknown.status());assertFalse(unknown.cleanupKnown());assertTrue(unknown.source().isEmpty());
        assertEquals(spent.operationId(),unknown.operationId());assertEquals(spent.deadlineUnixMs(),unknown.deadlineUnixMs());
        assertEquals(spent.providerGeneration(),unknown.providerGeneration());
        var n=token("operation-running.json");n.put("status","unavailable");n.put("ok",false);n.put("unavailable_reason","status_read_unavailable");
        var retained=changed(n);assertTrue(retained.effectAttempted());assertTrue(retained.nativeReturned());assertTrue(retained.accepted());assertTrue(retained.source().isEmpty());
        n=token("advance-refused-spent-claim.json");n.put("effect_attempted",true);reject(n);
        n=token("advance-indeterminate.json");n.set("source",token("song-query.json").get("source"));n.put("source_available",true);reject(n);
    }

    @Test void absentOwnerFactsCannotAcquirePositiveOwnerScalarsAndObservedFactsRequireAllFour()throws Exception {
        var n=token("advance-expired.json");n.putNull("facts_before");
        for(String key:List.of("connection_generation","ticket_sequence","pump_epoch"))n.put(key,"0");n.put("thread_id",0);
        var noFacts=changed(n);assertTrue(noFacts.factsBefore().isEmpty());assertEquals(BigInteger.ZERO,noFacts.connectionGeneration());
        n.put("ticket_sequence","1");reject(n);
        for(String key:List.of("connection_generation","ticket_sequence","pump_epoch")) {
            n=token("song-query.json");n.put(key,"0");reject(n);
        }
        n=token("song-query.json");n.put("thread_id",0);reject(n);
        n=token("song-query.json");n.put("thread_id",4294967296L);reject(n);
    }

    @Test void requestFactoryRejectsCallerEpochLeaseAndPrefixShortcuts()throws Exception {
        var actual=core(object(token("song-query.json"),"facts_before"));
        assertThrows(IllegalArgumentException.class,()->CurrentTedActorTransition.request(actual,CurrentTedActorTransition.Action.QUERY_ROLE,"caller",BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->CurrentTedActorTransition.request(actual,CurrentTedActorTransition.Action.QUERY_ROLE,"",BigInteger.ONE,BigInteger.ZERO,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->CurrentTedActorTransition.request(actual,CurrentTedActorTransition.Action.ADVANCE_DAY,"date01",BigInteger.ZERO,BigInteger.ONE,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->CurrentTedActorTransition.request(actual,CurrentTedActorTransition.Action.ADVANCE_DAY,"date01",BigInteger.ONE,BigInteger.ONE,BigInteger.TWO));
        assertThrows(IllegalArgumentException.class,()->CurrentTedActorTransition.request(actual,CurrentTedActorTransition.Action.CONFIRM_EPOCH,"date01",BigInteger.ONE,BigInteger.ONE,BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->CurrentTedActorTransition.request(actual,CurrentTedActorTransition.Action.ADVANCE_DAY,"date01",U64.add(BigInteger.ONE),BigInteger.ONE,BigInteger.ZERO));
        assertThrows(IOException.class,()->CurrentTedActorTransition.Action.parse("resume_arbitrary"));
        var prefix=object(token("song-query.json"),"facts_before");prefix.put("paused",false);assertThrows(IllegalArgumentException.class,()->core(prefix));
    }
}
