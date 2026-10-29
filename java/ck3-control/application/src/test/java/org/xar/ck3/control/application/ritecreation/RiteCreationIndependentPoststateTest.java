package org.xar.ck3.control.application.ritecreation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.semantic.NativePlayerReligionContext;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationIndependentPoststate.*;

final class RiteCreationIndependentPoststateTest {
    record Case(String name,ObjectNode before,ObjectNode after,ObjectNode first,ObjectNode last,Outcome expected,JsonNode quote,boolean accepted,boolean originalAccepted) { }
    static ObjectNode snapshot(long wallet){
        var n=empty().put("snapshot_id","diagnostic-original").put("revision",17).put("native_revision",9).put("date_raw",12345)
            .put("paused",true).put("map_ready",true).put("episode_run_id","episode-fixture");
        n.putObject("played_character").put("character_id",34014).put("alive",true);
        n.putObject("played_character_piety").put("raw",wallet).put("scale",100000);
        n.putObject("diagnostics").put("connection_generation",1).putObject("hello").put("pid",123)
            .put("expected_ck3_version",VERSION).put("expected_ck3_sha256",SHA).put("ck3_build_match",true)
            .put("game_adapter_id","ck3-1.20.0.4-msvc-x64");return n;
    }
    static ObjectNode context(ObjectNode snapshot,long rite,long faith,long main){
        var n=empty().put("schema","ck3_12004_religion_context_v1").put("game_version",VERSION).put("executable_sha256",SHA)
            .put("available",true).putNull("unavailable_reason").put("capture_epoch",3)
            .put("rite_id",rite).put("faith_id",faith).put("religion_id",28).put("faith_main_rite_id",main)
            .put("faith_key","fixture").put("religion_key","fixture").putNull("faith_fervor_raw").put("spiritual_fulfillment_raw",0)
            .put("raw_scale",100000).put("read_only",true).put("domain_key","player_religion_context_v1")
            .put("backend_id","ck3-1.20.0.4-native-player-religion-context-v1");
        n.set("date_raw",snapshot.get("date_raw"));n.set("played_character_id",snapshot.get("played_character").get("character_id"));
        n.set("queried_revision",snapshot.get("revision"));n.set("snapshot_revision",snapshot.get("native_revision"));return n;
    }
    static Case base(String name,Outcome kind,long beforeWallet,long afterWallet,Long quote){
        var a=snapshot(beforeWallet);var b=snapshot(afterWallet);var c=context(a,26,27,26);var d=context(b,29,30,29);
        return new Case(name,a,b,c,d,kind,quote==null?empty().putNull("q").get("q"):empty().put("q",quote.longValue()).get("q"),true,true);
    }
    static Case bad(String name,java.util.function.Consumer<Case> change){
        var c=base(name,Outcome.CREATE_FAITH,100000,0,100000L);change.accept(c);
        return new Case(name,c.before,c.after,c.first,c.last,c.expected,c.quote,false,false);
    }
    static List<Case> cases(){
        var v=new ArrayList<Case>();
        v.add(base("new-faith-equal-quote",Outcome.CREATE_FAITH,100000,0,100000L));
        v.add(base("different-quote",Outcome.CREATE_FAITH,100000,0,99999L));
        v.add(base("full-signed65-delta",Outcome.CREATE_RITE,Long.MIN_VALUE,Long.MAX_VALUE,Long.MIN_VALUE));
        v.add(base("minimum-quote-negated-without-long-overflow",Outcome.CREATE_RITE,Long.MIN_VALUE,0,Long.MIN_VALUE));
        var rite=base("new-rite",Outcome.CREATE_RITE,100000,0,100000L);rite.last.put("faith_id",27);v.add(rite);
        var edit=base("edit-identical-full-four-ids",Outcome.EDIT_RITE,100000,0,null);edit.last.setAll(edit.first);v.add(edit);
        var zero=base("zero-reference-is-real",Outcome.CREATE_FAITH,0,0,0L);zero.first.put("rite_id",0);v.add(zero);
        var sentinel=base("native-null-sentinel-not-complete",Outcome.CREATE_FAITH,0,0,0L);sentinel.first.put("rite_id",4294967295L);v.add(sentinel);
        var absent=base("explicit-null-reference-not-complete",Outcome.CREATE_FAITH,0,0,null);absent.last.putNull("faith_id");v.add(absent);
        var unknown=base("missing-wallet-is-unknown",Outcome.CREATE_FAITH,0,0,0L);unknown.after.remove("played_character_piety");v.add(unknown);
        var nullWallet=base("null-wallet-is-unknown",Outcome.CREATE_FAITH,0,0,null);nullWallet.before.putNull("played_character_piety");v.add(nullWallet);
        var unavailable=base("unavailable-keeps-real-ids-resources-and-wide-frame",Outcome.CREATE_FAITH,0,0,null);
        unavailable.first.put("available",false).put("unavailable_reason","source-unavailable").put("date_raw",new BigInteger("-12345678901234567890"))
            .put("played_character_id",new BigInteger("12345678901234567890")).put("faith_fervor_raw",Long.MIN_VALUE);v.add(unavailable);
        var wide=base("available-unbounded-original-diagnostic-frame",Outcome.CREATE_FAITH,0,0,0L);
        for(var s:List.of(wide.before,wide.after)){s.put("date_raw",new BigInteger("-12345678901234567890"));object(s.get("played_character")).put("character_id",new BigInteger("12345678901234567890"));}
        for(var c:List.of(wide.first,wide.last)){c.set("date_raw",wide.before.get("date_raw"));c.set("played_character_id",wide.before.get("played_character").get("character_id"));}v.add(wide);
        var extra=base("original-projects-context-addons",Outcome.CREATE_FAITH,0,0,null);extra.first.putObject("future_addon").put("untouched",true);v.add(extra);
        v.add(bad("wrong-readonly-type",c->c.first.put("read_only",1)));
        v.add(bad("wrong-domain",c->c.first.put("domain_key","another")));
        v.add(bad("wrong-backend",c->c.first.put("backend_id","ck3-1.20.0.3-native-player-religion-context-v1")));
        v.add(bad("wrong-revision",c->c.first.put("queried_revision",18)));
        v.add(bad("wrong-native-revision",c->c.first.put("snapshot_revision",10)));
        v.add(bad("missing-required-null",c->c.first.remove("faith_fervor_raw")));
        v.add(bad("bool-reference",c->c.first.put("rite_id",true)));
        v.add(bad("float-reference",c->c.first.put("rite_id",26.0)));
        v.add(bad("out-of-u32-reference",c->c.first.put("rite_id",4294967296L)));
        v.add(bad("out-of-i64-resource",c->c.first.put("faith_fervor_raw",new BigInteger("9223372036854775808"))));
        v.add(bad("bool-epoch",c->c.first.put("capture_epoch",true)));
        v.add(bad("zero-epoch",c->c.first.put("capture_epoch",0)));
        v.add(bad("wrong-available-type",c->c.first.put("available",1)));
        v.add(bad("available-reason-must-be-null",c->c.first.put("unavailable_reason","stale")));
        v.add(bad("available-fulfillment-missing",c->c.first.putNull("spiritual_fulfillment_raw")));
        v.add(bad("wrong-player",c->c.first.put("played_character_id",34015)));
        v.add(bad("wrong-date",c->c.first.put("date_raw",12346)));
        v.add(bad("bool-wallet",c->object(c.before.get("played_character_piety")).put("raw",true)));
        v.add(bad("float-wallet",c->object(c.before.get("played_character_piety")).put("raw",100000.0)));
        v.add(bad("extra-wallet-key",c->object(c.before.get("played_character_piety")).put("extra",1)));
        v.add(bad("wrong-connection",c->object(c.after.get("diagnostics")).put("connection_generation",2)));
        v.add(bad("wrong-pid",c->object(object(c.after.get("diagnostics")).get("hello")).put("pid",124)));
        v.add(bad("wrong-episode",c->c.after.put("episode_run_id","another")));
        v.add(bad("not-paused",c->c.before.put("paused",false)));
        v.add(bad("bool-public-revision",c->c.before.put("revision",true)));
        for(JsonNode quote:List.of(empty().put("q",true).get("q"),empty().put("q",100000.0).get("q"),empty().put("q",new BigInteger("9223372036854775808")).get("q"))){
            var c=base("malformed-quote-"+quote.toString(),Outcome.CREATE_FAITH,0,0,null);
            v.add(new Case(c.name,c.before,c.after,c.first,c.last,c.expected,quote,false,false));
        }
        var strictScale=base("user-exact-integer-scale-strengthening",Outcome.CREATE_FAITH,0,0,null);object(strictScale.before.get("played_character_piety")).put("scale",100000.0);
        v.add(new Case(strictScale.name,strictScale.before,strictScale.after,strictScale.first,strictScale.last,strictScale.expected,strictScale.quote,false,true));
        return List.copyOf(v);
    }
    static RiteCreationIndependentPoststate.Result run(Case c){
        var scope=new EpisodeScope("episode-fixture");var before=replaySnapshot(raw(c.before),scope);var after=replaySnapshot(raw(c.after),scope);
        var first=observe(before,raw(c.first));var last=observe(after,raw(c.last));
        return evaluate(before,after,first,last,c.expected,c.quote.isNull()?OptionalLong.empty():OptionalLong.of(signed64(c.quote)));
    }
    @Test void everyDiagnosticBranchAndMalformedBoundaryIsRetainedAndRoundTrips(){
        int valid=0,bad=0;for(var c:cases()){
            if(c.accepted){var result=run(c);assertEquals(result,decode(encode(result)),c.name);assertFalse(result.businessOutcomeVerified());assertFalse(result.actionReady());valid++;}
            else{assertThrows(IllegalArgumentException.class,()->run(c),c.name);bad++;}
        }assertTrue(valid>=14&&bad>=25);
        var huge=run(cases().get(2));assertEquals(new BigInteger("18446744073709551615"),huge.delta().orElseThrow());
        assertEquals(QuoteComparison.EQUAL,run(cases().get(3)).comparison());
    }
    @Test void resultRejectsForgedReadyWrongNullableMissingUnknownAndComputedArithmetic(){
        var result=run(cases().get(0));
        for(String flag:List.of("edit_payload_changed_observed","other_resource_effects_verified","doctrine_parameters_verified","adoption_native_permission_verified","business_outcome_verified","action_ready")){
            var n=json(result);n.put(flag,true);assertThrows(IllegalArgumentException.class,()->decode(raw(n)),flag);
        }
        var missing=json(result);missing.remove("identity_pattern_matches");assertThrows(IllegalArgumentException.class,()->decode(raw(missing)));
        var boolInt=json(result);boolInt.put("piety_before_raw",true);assertThrows(IllegalArgumentException.class,()->decode(raw(boolInt)));
        var wrong=json(result);wrong.put("piety_delta_raw",-99999);assertThrows(IllegalArgumentException.class,()->decode(raw(wrong)));
        var extra=json(result);extra.put("unknown",1);assertThrows(IllegalArgumentException.class,()->decode(raw(extra)));
        var scope=new EpisodeScope("episode-fixture");var a=replaySnapshot(raw(snapshot(0)),scope);var b=replaySnapshot(raw(snapshot(0)),scope);
        var own=observe(a,raw(context(snapshot(0),26,27,26)));
        assertThrows(IllegalArgumentException.class,()->evaluate(b,b,own,own,Outcome.CREATE_RITE,OptionalLong.empty()));
    }
    @Test void soleLowerPreservesUnavailableWideValuesAndRequiredNulls(){
        var n=context(snapshot(0),26,27,26);var full=empty();for(String key:NativePlayerReligionContext.FIELDS)full.set(key,n.get(key));
        full.put("available",false).put("unavailable_reason","source-unavailable").put("date_raw",new BigInteger("-12345678901234567890")).put("played_character_id",new BigInteger("12345678901234567890"));
        var value=NativePlayerReligionContext.decode(full);assertEquals(value,NativePlayerReligionContext.decode(value.encode()));
        for(String key:NativePlayerReligionContext.FIELDS){var missing=full.deepCopy();missing.remove(key);assertThrows(IllegalArgumentException.class,()->NativePlayerReligionContext.decode(missing),key);}
        var wrong=full.deepCopy();wrong.put("raw_scale",100000.0);assertThrows(IllegalArgumentException.class,()->NativePlayerReligionContext.decode(wrong));
    }
}

