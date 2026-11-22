package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
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

/** Only the nineteen SHA-pinned resources are genuine C++ bytes. Mutations are Java contract DATA, never Native observations. */
class NativeCurrentLyd26785313ProducerTest {
    private record Artifact(String name,int bytes,String sha256) { }
    private static final List<Artifact> CPP=List.of(
        new Artifact("add-modal-confirm.json",2564,"4b5281b16c739855d8b6f86e8e3e149343cab907386076dea0cecc1086828fd7"),
        new Artifact("add-modal-query.json",2554,"b2e398d8451e4c5720fa5673af05c990a0cffd03958374c0bb82ae2a15fcf955"),
        new Artifact("decision-confirm.json",2309,"2dc89d2f7886ceb560f8c79483a689b7be820d9944770424dbcb52cddd0cb487"),
        new Artifact("decision-detail.json",2291,"322026dc15f5156a8d1721c016cdb92763d0186933be479d9a44467b029d6d2c"),
        new Artifact("decisions-hidden.json",1820,"42c9817c72f55b87aae96b57ef77adcf6064df96481053015b507bb9a7fd570e"),
        new Artifact("decisions-open-list.json",1824,"fce50fb2c5f9582f5f2ad6f7ea6e6e8a9dadc13facddb198d0248c50323dcb4f"),
        new Artifact("decisions-query.json",2270,"613e185251ea78aef328417bb8e9246310daaad753670511daebcab7e893154f"),
        new Artifact("event-choose-pay.json",2085,"bc0d495877a977de2285f01d7433dae6ae70bc6945ddeab656af6748609f834b"),
        new Artifact("events-empty.json",1443,"a8eb3f073137b256ad4a0286f4c918b73f9e2f166f7c328537da7b0ee6c78d78"),
        new Artifact("events-query.json",2049,"6d97fe06d27958021c04f42002cd7c17da6dea401179a48283534a7b2812c374"),
        new Artifact("personal-can-false.json",2528,"144f6445475e368eee4339d2e10907c87f636aaa4d2eaa97437b7ac71dbfd47a"),
        new Artifact("personal-query.json",2526,"391fa25bd1c743bef3c9cf3cf00eba1f458689461c3233cf032435f586851bf9"),
        new Artifact("personal-select.json",2546,"8bc47b469b7064640dcf7d5a16bafa4b6dc18f2c3561eef4d90c484f0b33fa56"),
        new Artifact("query.request.json",847,"c0a0cbfa9dff8f918b34b6ec35b8b90a2094665c9bcadb9617777240523d1386"),
        new Artifact("readback-resources.json",1664,"a4e4902537f1f1ba446156b97917f3b48b8059b47568b52b00075002d513043b"),
        new Artifact("select-expired.json",1337,"c74ca33a5e82cc8a18bc5ab4afcb83d313b47673a386967727f51c0e4ff041e8"),
        new Artifact("select-indeterminate.json",1351,"13892aed118e5c800c4e0d5d210037690e722077d11e05c3dbcb0dd35bed4314"),
        new Artifact("select-refused-spent-claim.json",2566,"7901744b01d0929c2fbaba4c85a732e54e8d514b9223156835c3cf4f28d988bd"),
        new Artifact("select.request.json",923,"0a6ba569ec8add113e4108d141874b10a6fab3bef5729abadd6180b61bd87540")
    );
    private static byte[] raw(String name)throws Exception {
        var expected=CPP.stream().filter(a->a.name().equals(name)).findFirst().orElseThrow(()->new IOException("Unknown original C++ resource: "+name));
        try(var in=NativeCurrentLyd26785313ProducerTest.class.getResourceAsStream("/current267-lyd-cpp-a749/"+name)) {
            if(in==null)throw new IOException("Original C++ LYD resource absent: "+name);
            byte[] bytes=in.readAllBytes();assertEquals(expected.bytes(),bytes.length,name);
            assertEquals(expected.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),name);
            return bytes;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentLydResult changed(ObjectNode n)throws IOException{return CurrentLydResult.decode(new RawJson(StrictJson.canonical(n)));}
    private static CurrentLydResult frame(String name)throws Exception{return changed(token(name));}
    private static ObjectNode branch(ObjectNode n,String key){return (ObjectNode)n.get("source").get(key);}
    private static ObjectNode row(ObjectNode n,int index){return (ObjectNode)branch(n,"personal").get("rows").get(index);}
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
    private static CoreFrame.Partial actualCore()throws Exception{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("personal-query.json").factsBefore().orElseThrow());}

    @Test void seventeenOriginalCppResponsesRoundtripTypedAndTwoOriginalRequestsRemainExact()throws Exception {
        int responses=0,requests=0,negative=0;
        for(var artifact:CPP) {
            var original=envelope(artifact.name());
            if(original.get("type").textValue().equals("execute_step")){requests++;continue;}
            responses++;var result=changed(NativeWire.object(original.get("result")));
            assertEquals(result,CurrentLydResult.decode(result.encode()),artifact.name());
            assertEquals(original.get("ok").booleanValue(),result.successful(),artifact.name());
            assertEquals(31,NativeWire.parse(result.encode().bytes()).size());
            if(!result.successful())negative++;
        }
        assertEquals(19,CPP.size());assertEquals(17,responses);assertEquals(2,requests);assertEquals(3,negative);
    }

    @Test void bothOriginalCppRequestClaimsMatchTheJavaTypedFactoryWithoutOuterDuplication()throws Exception {
        for(String name:List.of("query.request.json","select.request.json")) {
            var original=StrictJson.object(envelope(name),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","lyd","core_control_deadline_unix_ms"));
            assertEquals("execute_step",original.get("type").textValue());assertEquals(1,original.get("protocol_version").intValue());assertEquals(0,original.get("expected_revision").intValue());
            assertEquals(1899999999999L,original.get("core_control_deadline_unix_ms").longValue());
            var claim=NativeWire.object(original.get("lyd"));var action=CurrentLyd.Action.parse(claim.get("action").textValue());
            var target=new CurrentLyd.Target(CurrentLydSource.decision(claim.get("decision_key")),CurrentLydSource.personalKey(claim.get("personal_key")),
                    CurrentLydSource.role(claim.get("event_role")),CurrentLyd.integer(claim.get("instance_id")),claim.get("choice_token").textValue());
            var core=new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,CurrentLyd.readCore(claim.get("expected_core")));
            var prepared=CurrentLyd.request(core,action,new BigInteger(claim.get("provider_generation").textValue()),new BigInteger(claim.get("query_sequence").textValue()),target);
            var fields=StrictJson.object(NativeWire.parse(prepared.additionalFields().bytes()),Set.of("arguments","lyd"));assertEquals(0,fields.get("arguments").size());
            var generated=NativeWire.object(fields.get("lyd"));assertEquals(14,generated.size());assertEquals(original.get("step").textValue(),prepared.step());assertEquals(action.capability(),prepared.requiredCapability().orElseThrow());
            // Native's exact hash identity reader permits case; original CPP request bytes themselves remain SHA-pinned above.
            assertEquals(claim.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),generated.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
            var comparable=generated.deepCopy();comparable.set("executable_sha256",claim.get("executable_sha256"));assertEquals(claim,comparable);
            for(String outer:List.of("request_id","step","type","protocol_version","core_control_deadline_unix_ms"))assertFalse(generated.has(outer));
        }
    }

    @Test void requestTargetsRejectBeginConfirmationPracticeRolesAndUnissuedTokens()throws Exception {
        var core=actualCore();
        assertThrows(IllegalArgumentException.class,()->CurrentLyd.request(core,CurrentLyd.Action.CONFIRM_DECISION,BigInteger.ONE,BigInteger.ONE,CurrentLyd.Target.decision(CurrentLyd.DecisionKey.BEGIN_READONLY)));
        assertThrows(IOException.class,()->CurrentLyd.EventRole.parse("knowing_acting_practice"));
        assertThrows(IOException.class,()->CurrentLyd.Action.parse("execute_script"));
        assertThrows(IllegalArgumentException.class,()->CurrentLyd.Target.event(CurrentLyd.EventRole.RITUAL_MUSIC_PAY,0));
        assertThrows(IllegalArgumentException.class,()->CurrentLyd.request(core,CurrentLyd.Action.SELECT_PERSONAL_CANDIDATE,BigInteger.ONE,BigInteger.ONE,CurrentLyd.Target.personal(CurrentLyd.PersonalKey.REVERENT_HEAVEN)));
        assertThrows(IllegalArgumentException.class,()->CurrentLyd.request(core,CurrentLyd.Action.QUERY_ADD_CONFIRMATION,BigInteger.ONE,BigInteger.ONE,CurrentLyd.Target.personal(CurrentLyd.PersonalKey.REVERENT_HEAVEN)));
        var inspect=CurrentLyd.request(core,CurrentLyd.Action.OPEN_DETAIL,BigInteger.ONE,BigInteger.ONE,CurrentLyd.Target.decision(CurrentLyd.DecisionKey.BEGIN_READONLY));
        assertEquals(CurrentLyd.Action.OPEN_DETAIL.step(),inspect.step());
    }

    @Test void actualEventCensusAndRichtextCannotBeCollapsedOrReboundToPractice()throws Exception {
        var actual=frame("events-query.json").source().orElseThrow().events().orElseThrow();assertEquals(1,actual.namedRootCount());assertEquals(7,actual.events().get(0).instanceId());
        assertEquals("\u0015Y原样文本\u0015!",actual.events().get(0).description());
        var n=token("events-query.json");var events=branch(n,"events");((ArrayNode)events.get("events")).add(events.get("events").get(0).deepCopy());events.put("named_root_count",2);reject(n);
        n=token("events-empty.json");assertTrue(changed(n).source().orElseThrow().events().orElseThrow().events().isEmpty());branch(n,"events").put("named_root_count",1);reject(n);
        n=token("events-query.json");var event=(ObjectNode)branch(n,"events").get("events").get(0);
        event.put("definition_key","lyd.1032").put("authored_option_count",3);
        var first=(ObjectNode)event.get("options").get(0);first.put("authored_option_index",1).put("permitted_role","knowing_acting_inquiry").put("source_bound_option_key","lyd_play_knowing_acting_support_option_0");
        ((ObjectNode)event.get("options").get(1)).put("authored_option_index",2).put("permitted_role","knowing_acting_cancel");
        reject(n); // Known inquiry identity cannot authorize the reserved authored practice slot1.
        n=token("event-choose-pay.json");n.put("instance_id",8);reject(n);
    }

    @Test void unionUnknownMissingAndNullableRolesFailWithoutNormalization()throws Exception {
        var n=token("personal-query.json");n.put("caller_actor",17);reject(n);
        n=token("personal-query.json");((ObjectNode)n.get("source")).set("readback",branch(token("readback-resources.json"),"readback"));reject(n);
        n=token("personal-query.json");((ObjectNode)n.get("source")).put("kind","events");reject(n);
        n=token("personal-query.json");row(n,0).put("ordinal",0);reject(n);
        n=token("decisions-query.json");branch(n,"decisions").remove("conditions_text");reject(n);
        n=token("personal-query.json");n.putNull("owner");reject(n);
        n=token("personal-query.json");n.put("cleanup_known",false);reject(n);
        n=token("personal-query.json");n.put("source_available",false);reject(n);
        for(String key:List.of("schema","game_version","executable_sha256","backend","adapter_id")){n=token("personal-query.json");n.put(key,"wrong");reject(n);}
    }

    @Test void unqualifiedFieldsAndCurrencyQuoteCannotBecomeZeroOrInventedCost()throws Exception {
        for(String key:List.of("legitimacy_raw","diplomacy_xp_raw","learning_xp_raw","capital_control_raw")) {
            var n=token("readback-resources.json");branch(n,"readback").put(key,"0");reject(n);
            n=token("readback-resources.json");branch(n,"readback").remove(key);reject(n);
        }
        var n=token("readback-resources.json");branch(n,"readback").put("original_case_readback_complete",true);reject(n);
        n=token("personal-query.json");branch(n,"personal").set("quoted_currency_costs",branch(token("readback-resources.json"),"readback").get("resources"));reject(n);
        n=token("personal-query.json");branch(n,"personal").put("spiritual_fulfillment_raw","12345");
        var p=changed(n).source().orElseThrow().personal().orElseThrow();assertEquals(12345L,p.spiritualFulfillmentRaw().orElseThrow().longValue());assertTrue(p.quotedCurrencyCosts().isEmpty());
    }

    @Test void unrelatedRowsAndNegativeNativeCanCannotMintSelection()throws Exception {
        var n=token("personal-query.json");row(n,0).put("definition_key","unreviewed_tenet").put("choice_token","").put("select_admissible",false).put("native_can_pick",false);reject(n);
        row(n,0).putNull("native_can_pick");assertTrue(changed(n).successful());
        var negative=frame("personal-can-false.json");assertTrue(negative.successful());assertFalse(negative.source().orElseThrow().personal().orElseThrow().rows().get(0).nativeCanPick().orElseThrow());
        n=token("personal-can-false.json");n.put("action","select_personal_candidate").put("status","selection_dispatched").put("claim_sequence","1").put("effect_attempted",true).put("native_returned",true);reject(n);
        n=token("personal-query.json");branch(n,"personal").put("model_materialized",false);reject(n);
        n=token("personal-query.json");((ArrayNode)branch(n,"personal").get("rows")).add(row(n,0).deepCopy());reject(n);
    }

    @Test void modalTargetAndFreshCanAreNecessaryButDispatchIsNotMembership()throws Exception {
        var selected=frame("personal-select.json");assertEquals(CurrentLydResult.Status.SELECTION_DISPATCHED,selected.status());assertFalse(selected.source().orElseThrow().personal().orElseThrow().addModal().found());
        var confirmed=frame("add-modal-confirm.json");assertEquals(CurrentLydResult.Status.CONFIRMATION_DISPATCHED,confirmed.status());assertTrue(confirmed.source().orElseThrow().personal().orElseThrow().actualPersonalKeys().isEmpty());
        var n=token("add-modal-confirm.json");n.put("personal_key",CurrentLyd.PersonalKey.KNOWING_ACTING_SUPPORT.wire());reject(n);
        n=token("add-modal-query.json");((ObjectNode)branch(n,"personal").get("add_modal")).put("native_can_accept",false);reject(n);
        n=token("add-modal-query.json");((ObjectNode)branch(n,"personal").get("add_modal")).put("closed",true);reject(n);
    }

    @Test void toggleBoolIsDataAndEveryAppliedPaidDateSaveFlagStaysFalse()throws Exception {
        for(boolean handled:new boolean[]{false,true}){var n=token("decisions-open-list.json");n.put("native_handled",handled);var value=changed(n);assertEquals(handled,value.nativeHandled());assertTrue(value.successful());assertFalse(NativeWire.parse(value.encode().bytes()).get("personal_applied").booleanValue());}
        var n=token("decision-confirm.json");n.put("native_handled",true);reject(n);
        for(String key:List.of("event_closed","personal_applied","gold_paid","piety_paid","modifiers_applied","new_date_observed","physical_save_confirmed")){n=token("add-modal-confirm.json");n.put(key,true);reject(n);}
    }

    @Test void fullSignedActorAndRawResourcePrecisionArePreservedWithoutPositivityOrFloatingPoint()throws Exception {
        assertEquals(-16777215,actualCore().prefix().playedCharacterId());
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE}){var n=token("personal-query.json");((ObjectNode)n.get("facts_before")).put("played_character_id",actor);assertEquals(actor,changed(n).factsBefore().orElseThrow().playedCharacterId());}
        var n=token("personal-query.json");((ObjectNode)n.get("facts_before")).put("played_character_id",-1);reject(n);
        n=token("personal-query.json");((ObjectNode)n.get("facts_before")).put("local_player_id",-2);reject(n);
        var resources=frame("readback-resources.json").source().orElseThrow().readback().orElseThrow().resources().orElseThrow();
        assertEquals(-9223372036854775807L,resources.personalGoldRaw());assertEquals(Long.MAX_VALUE,resources.prestigeRaw());assertEquals(-20000000L,resources.pietyRaw());assertEquals(12,resources.stressPoints());
        n=token("readback-resources.json");((ObjectNode)branch(n,"readback").get("resources")).put("personal_gold_raw",Long.toString(Long.MIN_VALUE));assertEquals(Long.MIN_VALUE,changed(n).source().orElseThrow().readback().orElseThrow().resources().orElseThrow().personalGoldRaw());
        for(String bad:List.of("-0","01","+1","1.0","1e3","9223372036854775808","-9223372036854775809")){n=token("readback-resources.json");((ObjectNode)branch(n,"readback").get("resources")).put("piety_raw",bad);reject(n);}
        n=token("readback-resources.json");((ObjectNode)branch(n,"readback").get("resources")).put("piety_raw",0);reject(n);
        assertEquals(new BigInteger("18446744073709551615"),frame("personal-query.json").providerGeneration());
        n=token("personal-query.json");n.put("provider_generation","18446744073709551616");reject(n);
    }

    @Test void knownSpentRefusalAndUnknownRetainTheirOriginalFactsWithoutReplayCredit()throws Exception {
        var refused=frame("select-refused-spent-claim.json");assertFalse(refused.successful());assertTrue(refused.claimSequence().signum()>0);assertFalse(refused.effectAttempted());assertFalse(refused.nativeReturned());assertTrue(refused.source().isPresent());
        var expired=frame("select-expired.json");assertEquals(CurrentLydResult.Status.EXPIRED,expired.status());assertEquals(refused.personalKey(),expired.personalKey());assertTrue(expired.source().isEmpty());
        var unknown=frame("select-indeterminate.json");assertEquals(CurrentLydResult.Status.INDETERMINATE,unknown.status());assertFalse(unknown.cleanupKnown());assertTrue(unknown.source().isEmpty());
        var n=token("select-refused-spent-claim.json");n.put("effect_attempted",true);reject(n);
        n=token("personal-query.json");n.put("provider_generation","01");reject(n);
    }

    @Test void sourceEncodingCannotExposeOrMutateItsRetainedTypedBeforeSnapshot()throws Exception {
        var f=frame("personal-query.json");var s=f.source().orElseThrow();var exported=s.encode();exported.put("kind","events");
        assertEquals(CurrentLyd.Kind.PERSONAL,s.kind());assertEquals("personal",s.encode().get("kind").textValue());assertEquals(f,CurrentLydResult.decode(f.encode()));
    }
}
