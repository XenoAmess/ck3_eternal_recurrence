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
class NativeCurrentRmtmObservation26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256,boolean request) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("cancel_budget.request.json", 785, "78f475f23b2e22e299f962d382f21b176970a7a7514bdd7dc9fa9676f954860e", true),
        new Artifact("cancel_offer.request.json", 791, "c2d6ff41d3cf1b04ce063c4a4980f8be68b2f0ba1c035d16a3a6d803f6838da4", true),
        new Artifact("indeterminate.json", 1036, "e74b39ecb659b9b0b55c0cbec7ff0e9ce04ae9b7f418609fb779e6ceab1e6d8d", false),
        new Artifact("open_budget.request.json", 781, "1fc26f485affe9fddea6e1dedea0397f87b72f84564da71b994c89822d2e1a96", true),
        new Artifact("open_offer.request.json", 787, "7c8d55cc08445c966b33011c3043c5e31fd3e621531aa1050cf81b8a8106756b", true),
        new Artifact("query-available.json", 2152, "9ccca379d48dab41877b9f2e9c1170a7ddd297c049e1a502bdf3ee15d5673ec2", false),
        new Artifact("query-fullsigned.json", 2154, "800b455c4303b8c04065eb11cdc0622e926732f05defe9a729a3242c363056d4", false),
        new Artifact("query_budget.request.json", 783, "0b50bd5ef0c576c0c2645eecee751c6aefc57819bed5ba40c4ba43e9de6552d2", true),
        new Artifact("query_council.request.json", 785, "2c620a3cbdd5eaf27fad46bac355b54a208ee60cf5855a801c543c0affa9af7c", true),
        new Artifact("query_offer.request.json", 789, "993bcda5298a439c0e9c93d6e5073c8b2fc98eaeda9dab862e116bc72523a577", true),
        new Artifact("query_title_phase.request.json", 793, "8ac5767c46550c5f23cec50d03327d935e88089b0b6e04bcb9c90b26b2a4bc35", true)
    );

    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static byte[] raw(String name)throws Exception{
        var a=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentRmtmObservation26785313ProducerTest.class.getResourceAsStream("/current267-rmtm-observation-cpp-a01/"+name)){
            if(in==null)throw new IOException("Original RMTM C++ resource absent");
            var b=in.readAllBytes();assertEquals(a.bytes(),b.length,name);
            assertEquals(a.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),name);return b;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentRmtmObservationResult frame(String name)throws Exception{return CurrentRmtmObservationResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentRmtmObservationResult data(ObjectNode n)throws IOException{return CurrentRmtmObservationResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    private static ObjectNode facts(ObjectNode n){return (ObjectNode)n.get("facts_before");}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->data(n));}
    private static CoreFrame.Partial actual(ObjectNode c)throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentRmtmActorTransition.readCore(c.get("expected_core")));}

    @Test void originalPinsAndAllThreeTypedResponsesRoundTripWithoutRewritingTheSamples()throws Exception{
        int requests=0,responses=0;assertEquals(11,CPP.size());
        for(var a:CPP){var e=envelope(a.name());if(a.request()){requests++;assertEquals("execute_step",e.get("type").textValue());continue;}
            responses++;assertEquals("command_result",e.get("type").textValue());var r=frame(a.name());
            assertEquals(e.get("ok").booleanValue(),r.successful());assertEquals(r,CurrentRmtmObservationResult.decode(r.encode()));assertEquals(22,NativeWire.parse(r.encode().bytes()).size());
            if(r.source().isPresent()){var s=r.source().orElseThrow();assertEquals(8,s.encode().size());assertEquals(s,CurrentRmtmObservationSource.decode(s.encode()));}
        }
        assertEquals(8,requests);assertEquals(3,responses);
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
            var e=StrictJson.object(envelope(a.name()),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","rmtm_observation","core_control_deadline_unix_ms"));
            var c=StrictJson.object(e.get("rmtm_observation"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence","phase","offer_target"));
            var action=CurrentRmtmObservation.Action.parse(c.get("action").textValue());
            var request=CurrentRmtmObservation.request(actual(c),action,NativeWire.integer(c.get("provider_generation"),BigInteger.ZERO,MAX),NativeWire.integer(c.get("query_sequence"),BigInteger.ZERO,MAX),c.get("phase").isNull()?Optional.<CurrentRmtmObservation.Phase>empty():Optional.of(CurrentRmtmObservation.Phase.parse(c.get("phase").textValue())),c.get("offer_target").isNull()?Optional.<CurrentRmtmObservation.OfferTarget>empty():Optional.of(CurrentRmtmObservation.OfferTarget.parse(c.get("offer_target").textValue())));
            assertEquals(action.step(),request.step());assertEquals(e.get("step").textValue(),request.step());assertEquals(action.capability(),request.requiredCapability().orElseThrow());
            var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","rmtm_observation"));
            var generated=NativeWire.object(fields.get("rmtm_observation"));assertEquals(11,generated.size());assertEquals(0,fields.get("arguments").size());
            assertTrue(generated.get("provider_generation").isIntegralNumber());assertTrue(generated.get("query_sequence").isIntegralNumber());
            var compare=generated.deepCopy();assertEquals(c.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),compare.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
            compare.set("executable_sha256",c.get("executable_sha256"));assertEquals(c,compare); // Only the legal EXE-hash case is normalized.
            assertEquals(MAX,e.get("core_control_deadline_unix_ms").bigIntegerValue());fields.set("core_control_deadline_unix_ms",e.get("core_control_deadline_unix_ms"));
            byte[] packet=NativeWire.execute(e.get("request_id").textValue(),request.step(),e.get("expected_revision").bigIntegerValue(),StrictJson.canonical(fields));
            var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals(e.get("request_id").textValue(),decoded.requestId());assertEquals(action.step(),decoded.step());assertEquals(e.get("expected_revision").bigIntegerValue(),decoded.expectedRevision().orElseThrow());
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] body=Arrays.copyOfRange(packet,4,packet.length);
            var expected=e.deepCopy();((ObjectNode)expected.get("rmtm_observation")).set("executable_sha256",generated.get("executable_sha256"));assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
            String directory=System.getProperty("xar.rmtm.java.requests.output.directory");
            if(directory!=null){assertFalse(directory.isBlank());var out=Path.of(directory).toAbsolutePath();Files.createDirectories(out);assertFalse(Files.isSymbolicLink(out));
                Files.write(out.resolve("java-observation-"+action.wire()+".packet.bin"),packet,StandardOpenOption.CREATE_NEW);
                Files.write(out.resolve("java-observation-"+action.wire()+".body.json"),body,StandardOpenOption.CREATE_NEW);}
        }
        assertEquals(8,count);
        // These are independently authored samples. No request/response ID pairing or live exchange is inferred.
    }

    private static ObjectNode council(ObjectNode n){return (ObjectNode)source(n).get("council");}
    private static ObjectNode firstSeat(ObjectNode n){return (ObjectNode)council(n).get("seats").get(0);}
    private static ObjectNode budgetData(boolean visible)throws Exception{
        // Explicit Java DATA union test, not a generated Native budget frame or actual UI state.
        var n=token("query-available.json");n.put("action","query_budget");var s=source(n);s.put("kind","budget").putNull("council");
        var b=s.putObject("budget").put("found",visible).put("visible",visible).put("enabled",visible).put("blocked_by_visible_modal",false)
                .put("open_admissible",!visible).put("cancel_admissible",visible).put("route","my_realm_player").put("sampled_twice",true);
        if(visible)b.put("owner_id",0).put("full_title_id",0).put("holder_id",0);else b.putNull("owner_id").putNull("full_title_id").putNull("holder_id");return n;
    }
    private static ObjectNode offerData()throws Exception{
        // Explicit Java DATA union test. Target key is fixed released_a, never an arbitrary caller ID.
        var n=token("query-available.json");n.put("action","query_offer");var s=source(n);s.put("kind","offer").putNull("council");
        s.putObject("offer").put("target","released_a").put("found",true).put("visible",true).put("enabled",true).put("blocked_by_visible_modal",false)
                .put("actor_id",0).put("recipient_id",-2).put("interaction_key","offer_vassalization_interaction").put("description","")
                .put("open_admissible",false).put("cancel_admissible",true).put("sampled_twice",true);return n;
    }

    @Test void councilKeepsAllNineActualFixedSeatsAndNullableIncumbents()throws Exception{
        var s=frame("query-available.json").source().orElseThrow().council().orElseThrow();assertEquals(9,s.nativeTaskCount());assertEquals(9,s.seats().size());assertTrue(s.completeModelCensus());assertTrue(s.sampledTwice());
        assertEquals(CurrentRmtmObservationSource.COUNCIL_KEYS,s.seats().stream().map(CurrentRmtmObservationSource.Seat::positionKey).toList());
        assertTrue(s.seats().stream().allMatch(v->v.incumbentId().isEmpty()&&v.incumbentAlive().isEmpty()));
        var missing=token("query-available.json");((ArrayNode)council(missing).get("seats")).remove(8);reject(missing);
        var duplicate=token("query-available.json");((ObjectNode)council(duplicate).get("seats").get(1)).put("full_task_id",0);reject(duplicate);
        var wrong=token("query-available.json");firstSeat(wrong).put("position_key","minister_arbitrary");reject(wrong);
        var pair=token("query-available.json");firstSeat(pair).put("incumbent_id",0);reject(pair);firstSeat(pair).put("incumbent_alive",false);assertEquals(Optional.of(false),data(pair).source().orElseThrow().council().orElseThrow().seats().get(0).incumbentAlive());
    }

    @Test void sourceUnionAndBudgetRouteNeverBorrowTheOfferOrTopLiegeContext()throws Exception{
        var absent=budgetData(false);var b=data(absent).source().orElseThrow().budget().orElseThrow();assertFalse(b.found());assertTrue(b.openAdmissible());assertTrue(b.fullTitleId().isEmpty());
        var visible=budgetData(true);assertTrue(data(visible).source().orElseThrow().budget().orElseThrow().cancelAdmissible());
        var wrongRoute=visible.deepCopy();((ObjectNode)source(wrongRoute).get("budget")).put("route","hud_top_liege");reject(wrongRoute);
        var wrongOwner=visible.deepCopy();((ObjectNode)source(wrongOwner).get("budget")).put("owner_id",-2);reject(wrongOwner);
        var noPair=visible.deepCopy();((ObjectNode)source(noPair).get("budget")).putNull("holder_id");reject(noPair);
        var two=visible.deepCopy();source(two).set("council",council(token("query-available.json")));reject(two);
        var noCase=visible.deepCopy();source(noCase).put("case_bound",false);reject(noCase);((ObjectNode)source(noCase).get("budget")).put("cancel_admissible",false);assertTrue(data(noCase).successful());
        var sampled=token("query-available.json");source(sampled).put("sampled_twice",false);reject(sampled);
    }

    @Test void offerKeepsActualSubjectAndFullDescriptionWithoutSendPermission()throws Exception{
        var original=offerData();var o=data(original).source().orElseThrow().offer().orElseThrow();assertEquals(CurrentRmtmObservation.OfferTarget.RELEASED_A,o.target());assertEquals(-2,o.recipientId());
        String astral=new String(Character.toChars(0x1f600));
        for(String text:List.of("","offer\0#P actual DATA#!\n\t"+(char)0x15,astral.repeat(4096))){var n=offerData();((ObjectNode)source(n).get("offer")).put("description",text);assertEquals(text,data(n).source().orElseThrow().offer().orElseThrow().description());}
        var tooLong=offerData();((ObjectNode)source(tooLong).get("offer")).put("description",astral.repeat(4097));reject(tooLong);
        var actor=offerData();((ObjectNode)source(actor).get("offer")).put("actor_id",-2);reject(actor);
        var key=offerData();((ObjectNode)source(key).get("offer")).put("interaction_key","arbitrary_interaction");reject(key);
        var caller=offerData();((ObjectNode)source(caller).get("offer")).put("target_actor_id",77);reject(caller);
        assertThrows(IOException.class,()->CurrentRmtmObservation.Action.parse("send_offer"));
        assertThrows(IOException.class,()->CurrentRmtmObservation.OfferTarget.parse("caller_id_77"));
    }

    @Test void actionPhaseAndTargetUnionAreExactAndObservedDatesRemainSignedData()throws Exception{
        var c=NativeWire.object(envelope("query_council.request.json").get("rmtm_observation"));var core=actual(c);
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmObservation.request(core,CurrentRmtmObservation.Action.QUERY_COUNCIL,BigInteger.ZERO,BigInteger.ZERO,Optional.of(CurrentRmtmObservation.Phase.D3),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmObservation.request(core,CurrentRmtmObservation.Action.QUERY_TITLE_PHASE,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmObservation.request(core,CurrentRmtmObservation.Action.QUERY_OFFER,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmObservation.request(core,CurrentRmtmObservation.Action.OPEN_BUDGET,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty()));
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){var n=token("query-available.json");facts(n).put("played_character_id",actor);council(n).put("owner_id",actor);assertEquals(actor,data(n).factsBefore().orElseThrow().playedCharacterId());}
        var date=token("query-available.json");facts(date).put("date_raw",Integer.MIN_VALUE);assertEquals(Integer.MIN_VALUE,data(date).factsBefore().orElseThrow().dateRaw());
        for(String flag:List.of("new_date_observed","physical_save_confirmed")){var n=token("query-available.json");n.put(flag,true);reject(n);}
        var noBefore=budgetData(false);noBefore.put("action","open_budget").put("status","navigation_dispatched").put("effect_attempted",true).put("native_returned",true).put("claim_sequence","3");noBefore.putNull("source");noBefore.put("source_available",false);reject(noBefore);
    }

}
