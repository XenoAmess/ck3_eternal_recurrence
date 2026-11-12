package org.xar.ck3.control.warbudget;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/** Public raw-byte producer parity and ownership. Pure DATA; no private AST, IO, issuer or timing oracle. */
final class OrdinaryWarPriorityOwnedInput60Test {
    private static final BigInteger HUGE=new BigInteger("123456789012345678901234567890");
    private static final BigInteger HIGH_UNIT=new BigInteger("4294967294");
    private static final BigInteger WAR=BigInteger.valueOf(11);
    private static byte[] raw(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static byte[] snapshot(){return raw("""
        {
          "source":"injected-dll-named-pipe","snapshot_id":"native:22","native_revision":22,"revision":17,
          "date_raw":53144328,"episode_run_id":"owned-轮回😀","paused":true,"map_ready":true,
          "played_character":{"source":"native","character_id":7,"alive":true},
          "played_character_gold":{"raw":-5,"scale":100000},
          "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
          "diagnostics":{"connected":true,"bridge_pid":100,"connection_generation":3},
          "player_armies":[
            {"army_id":0,"soldiers":2,"retreating":true,"unknown_army":"雪😀"},
            {"army_id":4294967294,"soldiers":3,"retreating":true}
          ],
          "active_wars":[{
            "source":"native","war_id":11,"player_is_primary_war_leader":true,"player_side":"defender",
            "player_relative_war_score":-80,"primary_opponent_character_id":9,"targeted_title_ids":[101,102],
            "objective_province_states":[{"province_id":31,"occupation_observable":true,"is_occupied":true,"occupying_character_id":9}],
            "enemy_armies":[
              {"source":"native","army_id":9,"owner_character_id":9,"soldiers":20,"army_state":"sieging","siege_province_in_player_subrealm":true},
              {"source":"native","army_id":10,"owner_character_id":9,"soldiers":5,"army_state":"idle"}
            ]
          }],
          "army_strengths_status":"available","army_strengths_queried_snapshot_id":"native:22","army_strengths_queried_revision":17,
          "army_strengths":[
            {"status":"available","scope_role":"player","army_id":0,"war_ids":[11],"current_soldiers":2,"maximum_soldiers":10,"ai_base_power_raw":20},
            {"status":"available","scope_role":"player","army_id":4294967294,"war_ids":[11],"current_soldiers":3,"maximum_soldiers":10,"ai_base_power_raw":30},
            {"status":"available","scope_role":"active_war_enemy","army_id":9,"war_ids":[11],"current_soldiers":123456789012345678901234567890,"maximum_soldiers":246913578024691357802469135780,"ai_base_power_raw":123456789012345678901234567890},
            {"status":"available","scope_role":"active_war_enemy","army_id":10,"war_ids":[11],"current_soldiers":5,"maximum_soldiers":10,"ai_base_power_raw":7}
          ],
          "unknown_complete_material":{"huge":123456789012345678901234567890,"decimal":1.2300e+40,"unicode":"轮回😀雪","missing_stays_missing":{},"null_stays_null":null}
        }
        """);}
    private static byte[] root(){return raw("""
        {"status":"available","player_character_id":7,"snapshot_revision":22,"date_raw":53144328,
         "primary_title":{"title_id":101},
         "held_title_partition":[{"title":{"title_id":101,"tier_raw":4}},{"title":{"title_id":102,"tier_raw":2}}],
         "player_monthly_gold_income":{"raw":-10,"scale":100000},
         "player_max_monthly_gold_maintenance_v1":{"status":"available","value":{"raw":2,"scale":100000}},
         "unknown_root":{"huge":123456789012345678901234567890,"label":"王国😀"}}
        """);}

    @Test void bothPublicEntriesPreserveCompleteNonemptyWarOutputAndAllPublicObservationQueries() {
        for(byte[] currentRoot:List.of(root(),raw("null"))) {
            byte[] original=snapshot();var input=new OrdinaryWarPriority.Input(original,currentRoot);
            var legacy=OrdinaryWarPriority.observe(input);
            var owned=OrdinaryWarPriority.observe(original,currentRoot);
            sameObservation(legacy,owned);
            assertTrue(owned.deferredOptionalConstruction());assertFalse(owned.actionAuthority());
            var priority=StrictJson.parse(owned.toJson());
            assertEquals(1,priority.path("wars").size());
            assertEquals(11,priority.path("cash_protection_priority_war_ids").get(0).intValue());
            assertEquals(Optional.of(BigInteger.valueOf(5)),owned.countCurrentFullMembers(List.of(BigInteger.ZERO,HIGH_UNIT),Optional.empty()));
            assertEquals(Optional.of(HUGE.add(BigInteger.valueOf(5))),owned.countCurrentFullMembers(List.of(BigInteger.valueOf(9),BigInteger.TEN),Optional.of(WAR)));
            var material=FullJsonTree.parse(owned.sourceSnapshot(),FullJsonTree.MAXIMUM_BYTES);
            assertEquals(HUGE,material.path("unknown_complete_material").path("huge").bigIntegerValue());
            assertEquals("轮回😀雪",material.path("unknown_complete_material").path("unicode").textValue());
            String originalText=new String(owned.sourceSnapshot(),StandardCharsets.UTF_8);
            assertTrue(originalText.contains("1.2300e+40"),"complete material keeps the decimal token, not a coerced receipt number");
            assertTrue(material.path("unknown_complete_material").path("missing_stays_missing").isObject());
            assertFalse(material.path("unknown_complete_material").path("missing_stays_missing").has("invented"));
            assertTrue(material.path("unknown_complete_material").path("null_stays_null").isNull());
        }
    }
    @Test void callerAndGetterArrayMutationCannotAlterEitherObservationOrTheLegacyInputFinancePath() {
        byte[] original=snapshot(),currentRoot=root(),savedSnapshot=original.clone(),savedRoot=currentRoot.clone();
        var input=new OrdinaryWarPriority.Input(original,currentRoot);
        var legacy=OrdinaryWarPriority.observe(input);var owned=OrdinaryWarPriority.observe(original,currentRoot);
        sameObservation(legacy,owned);
        var request=new OrdinaryWarPriority.FinanceRequest(input,Optional.of(BigInteger.valueOf(3)),Optional.of(BigInteger.valueOf(18)),BigInteger.ZERO,6,BigInteger.ONE);
        byte[] finance=OrdinaryWarPriority.finance(request),output=owned.toJson(),material=owned.sourceSnapshot();
        Arrays.fill(original,(byte)'!');Arrays.fill(currentRoot,(byte)'[');
        byte[] snapshotGetter=input.snapshot(),rootGetter=input.nullableCampaignRoot();
        Arrays.fill(snapshotGetter,(byte)'?');Arrays.fill(rootGetter,(byte)'?');
        assertArrayEquals(savedSnapshot,input.snapshot());assertArrayEquals(savedRoot,input.nullableCampaignRoot());
        assertNotSame(snapshotGetter,input.snapshot());assertNotSame(rootGetter,input.nullableCampaignRoot());
        byte[] exposedOutput=owned.toJson(),exposedSource=owned.sourceSnapshot();
        Arrays.fill(exposedOutput,(byte)'!');Arrays.fill(exposedSource,(byte)'!');
        assertArrayEquals(output,owned.toJson());assertArrayEquals(material,owned.sourceSnapshot());
        sameObservation(legacy,owned);sameObservation(OrdinaryWarPriority.observe(input),owned);
        assertArrayEquals(finance,OrdinaryWarPriority.finance(request));
        assertThrows(ContractViolationException.class,()->OrdinaryWarPriority.observe(original,currentRoot),
                "a subsequent invalid caller input is parsed again, never served from an earlier observation");
    }
    @Test void nullAndDoubleInvalidInputsKeepCloneBeforeParsingAndSnapshotBeforeRootFailureOrder() {
        assertEquals(NullPointerException.class,sameFailure("both null",null,null).type());
        assertEquals(NullPointerException.class,sameFailure("snapshot null before bad root",null,raw("[")).type());
        assertEquals(NullPointerException.class,sameFailure("root null before malformed snapshot",raw("{"),null).type());
        assertEquals(NullPointerException.class,sameFailure("root null before malformed UTF8",new byte[]{(byte)0xc3,(byte)0x28},null).type());
        var shape=sameFailure("snapshot object check before root parse",raw("[]"),raw("{"));
        assertEquals(ContractViolationException.class,shape.type());assertEquals("budget JSON object required",shape.message());
        var snapshotFailure=legacyFailure(raw("{"),raw("null"));
        var rootFailure=legacyFailure(snapshot(),raw("false"));
        assertNotEquals(snapshotFailure,rootFailure,"the two independent invalid inputs must have distinguishable failures");
        assertEquals(snapshotFailure,sameFailure("snapshot parse precedes root shape",raw("{"),raw("false")));
        assertEquals(snapshotFailure,sameFailure("snapshot parse precedes root parse",raw("{"),raw("[")));
        assertThrows(NullPointerException.class,()->OrdinaryWarPriority.observe((OrdinaryWarPriority.Input)null),
                "legacy one-argument API remains available and does not manufacture Input");
    }

    private record Invalid(String label,byte[] snapshot,byte[] root) { }
    @Test void malformedUtf8JsonAndSnapshotOrNullableRootShapesRetainExactFailureClassAndMessage() {
        byte[] invalidUtf8={(byte)0xc3,(byte)0x28};
        List<Invalid> invalid=List.of(
                new Invalid("snapshot malformed UTF8",invalidUtf8,root()),
                new Invalid("snapshot malformed JSON",raw("{"),root()),
                new Invalid("snapshot array",raw("[]"),root()),
                new Invalid("snapshot null token",raw("null"),root()),
                new Invalid("snapshot boolean",raw("true"),root()),
                new Invalid("snapshot integer",raw("1"),root()),
                new Invalid("root malformed UTF8",snapshot(),invalidUtf8),
                new Invalid("root malformed JSON",snapshot(),raw("{")),
                new Invalid("root array",snapshot(),raw("[]")),
                new Invalid("root boolean",snapshot(),raw("false")),
                new Invalid("root integer",snapshot(),raw("1")),
                new Invalid("root decimal",snapshot(),raw("1.25")),
                new Invalid("root string",snapshot(),raw("\"root\"")));
        for(var value:invalid) {
            Failure old=sameFailure(value.label(),value.snapshot(),value.root());
            assertNotEquals(NullPointerException.class,old.type(),value.label()+" is malformed DATA, not a Java null reference");
        }
    }
    private static void sameObservation(OrdinaryWarPriority.Observation old,OrdinaryWarPriority.Observation next) {
        assertArrayEquals(old.toJson(),next.toJson(),"complete original priority bytes");
        assertArrayEquals(old.sourceSnapshot(),next.sourceSnapshot(),"complete original source snapshot bytes");
        assertEquals(old.deferredOptionalConstruction(),next.deferredOptionalConstruction());
        assertEquals(old.actionAuthority(),next.actionAuthority());
        assertEquals(old.countCurrentMembers(List.of(0),Optional.empty()),next.countCurrentMembers(List.of(0),Optional.empty()));
        assertEquals(old.countCurrentMembers(List.of(9,10),Optional.of(WAR)),next.countCurrentMembers(List.of(9,10),Optional.of(WAR)));
        List<List<BigInteger>> queries=List.of(List.<BigInteger>of(),List.of(BigInteger.ZERO,HIGH_UNIT),
                List.of(BigInteger.valueOf(9),BigInteger.TEN),List.of(BigInteger.valueOf(9),BigInteger.valueOf(9)),List.of(BigInteger.valueOf(999)));
        List<Optional<BigInteger>> wars=List.of(Optional.<BigInteger>empty(),Optional.of(WAR),Optional.of(BigInteger.valueOf(999)));
        for(var ids:queries)for(var war:wars)
            assertEquals(old.countCurrentFullMembers(ids,war),next.countCurrentFullMembers(ids,war),"public full-unit query "+ids+" / "+war);
        assertEquals(Optional.empty(),next.countCurrentFullMembers(List.of(BigInteger.ZERO,BigInteger.ZERO),Optional.empty()));
        assertEquals(Optional.empty(),next.countCurrentFullMembers(List.of(BigInteger.valueOf(999)),Optional.empty()));
    }
    private record Failure(Class<?> type,String message) { }
    private static Failure failure(Runnable call) {
        try {call.run();}
        catch(RuntimeException rejected) {return new Failure(rejected.getClass(),rejected.getMessage());}
        throw new AssertionError("invalid input unexpectedly succeeded");
    }
    private static Failure legacyFailure(byte[] snapshot,byte[] root) {
        return failure(()->OrdinaryWarPriority.observe(new OrdinaryWarPriority.Input(snapshot,root)));
    }
    private static Failure sameFailure(String label,byte[] snapshot,byte[] root) {
        Failure old=legacyFailure(snapshot,root);
        assertEquals(old,failure(()->OrdinaryWarPriority.observe(snapshot,root)),label);
        return old;
    }
}
