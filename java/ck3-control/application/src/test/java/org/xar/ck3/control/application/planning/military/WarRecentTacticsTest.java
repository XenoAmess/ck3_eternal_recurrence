package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.List;
import java.util.OptionalInt;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

class WarRecentTacticsTest {
    @Test void actualOriginalLongContactProducesBoundedCollisionHintAndJsonRoundtrip() throws Exception {
        Obj player=army(11,41,"regular",false), enemy=army(21,41,"regular",false);
        var history=List.of(advance(1,summary(24000,player,List.of(enemy),24),summary(24432,player,List.of(enemy),24),true));
        Obj actual=compare(history,24432,11);
        assertEquals(numbers(List.of(21)),actual.get("blocked_enemy_ids")); assertEquals(numbers(List.of(41)),actual.get("blocked_province_ids"));
        assertEquals(new Bool(true),actual.get("contact_stale"));
        assertEquals(actual,OpportunityJson.parse(OpportunityJson.encode(actual)));
    }
    @Test void twoRealProbesAndTheExactNinetyDayExpiryPreservePublicUnitZero() throws Exception {
        Obj player=army(0,41,"regular",false), enemy=army(21,41,"regular",false);
        var history=List.of(advance(1,summary(24000,player,List.of(enemy),24),summary(24024,player,List.of(enemy),24),true),
                advance(2,summary(24024,player,List.of(enemy),24),summary(24048,player,List.of(enemy),24),true));
        assertEquals(numbers(List.of(21)),compare(history,24048+2160-1,0).get("blocked_enemy_ids"));
        assertEquals(new Arr(List.of()),compare(history,24048+2160,0).get("blocked_enemy_ids"));
    }
    @Test void actualOriginalScoreDropRequiresAnObservedLocalNonretreatingEnemy() throws Exception {
        Obj player=army(11,2635,"regular",false), enemy=army(21,2635,"regular",false);
        for (List<Obj> enemies:List.of(List.<Obj>of(),List.of(enemy),List.of(enemy.with("retreating",new Bool(true))))) {
            var history=List.of(advance(1,summary(53263584,player,enemies,50),summary(53263632,player,enemies,16),true));
            Obj actual=compare(history,53263632,11);
            assertEquals(!enemies.isEmpty()&&!yes(enemies.getFirst().get("retreating")),!OpportunityJson.array(actual.get("blocked_enemy_ids"),"blocked").isEmpty());
        }
    }
    @Test void scoreImprovementAndRealEnemyDisappearanceClearPriorCollisionBlocks() throws Exception {
        Obj player=army(11,41,"regular",false), enemy=army(21,41,"regular",false);
        Obj first=advance(1,summary(24000,player,List.of(enemy),24),summary(24432,player,List.of(enemy),24),true);
        for (Obj second:List.of(advance(2,summary(24432,player,List.of(enemy),24),summary(24456,player,List.of(enemy),25),true),
                advance(2,summary(24432,player,List.of(enemy),24),summary(24456,player,List.of(),24),true))) {
            Obj actual=compare(List.of(first,second),24456,11);
            assertEquals(new Bool(false),actual.get("contact_stale"));
        }
    }
    @Test void retreatDaysUseSuccessfulActualSlicesAndResetAtTheLatestRestore() throws Exception {
        Obj player=army(11,41,"embarked",true);
        Obj first=advance(1,summary(24000,player,List.of(),24),summary(24024,player,List.of(),24),true);
        Obj failed=advance(2,summary(24024,player,List.of(),24),summary(24264,player,List.of(),24),false);
        Obj second=advance(3,summary(24024,player,List.of(),24),summary(24072,player,List.of(),24),true);
        assertEquals(number(3),compare(List.of(first,failed,second),24072,11).get("retreat_days"));
        Obj restore=obj(f("index",number(4)),f("command",text("restore-checkpoint")),f("ok",new Bool(true)));
        Obj next=advance(5,summary(24072,player,List.of(),24),summary(24096,player,List.of(),24),true);
        assertEquals(number(1),compare(List.of(first,failed,second,restore,next),24096,11).get("retreat_days"));
    }
    @Test void completedObjectiveUsesTheSourceFallbackAndObservedScoreProgress() throws Exception {
        Obj before=army(11,41,"sieging",false), after=army(11,41,"regular",false);
        Obj old=summary(24000,before,List.of(),24), newer=summary(24024,after,List.of(),25);
        Obj war=OpportunityJson.object(OpportunityJson.array(old.get("wars"),"wars").getFirst(),"war")
                .with("war_objective_province_ids",new Arr(List.of())).with("enemy_primary_default_raise_province_id",number(41));
        old=old.with("wars",new Arr(List.of(war)));
        assertEquals(numbers(List.of(41)),compare(List.of(advance(1,old,newer,true)),24024,11).get("completed_objective_province_ids"));
    }
    @Test void nestedSelectedPlanNeverSubstitutesForFactualRootProgress() throws Exception {
        Obj player=army(11,41,"regular",false), enemy=army(21,41,"regular",false);
        Obj progress=result(summary(24000,player,List.of(enemy),24),summary(24432,player,List.of(enemy),24));
        Obj nested=obj(f("index",number(1)),f("command",text("auto-turn")),f("ok",new Bool(true)),
                f("result",obj(f("auto_turn",obj(f("selected_step",text("life-advance")),f("result",progress))))));
        assertEquals(new Bool(false),compare(List.of(nested),24432,11).get("contact_stale"));
        Obj actual=nested.with("result",progress.with("auto_turn",obj(f("selected_step",text("life-advance")),f("result",obj()))));
        assertEquals(new Bool(true),compare(List.of(actual),24432,11).get("contact_stale"));
    }
    @Test void unknownLocationsAndWrongIntegerTypesCannotInventLocalContact() {
        Obj player=army(0,41,"regular",false), enemy=army(21,41,"regular",false);
        Obj bad=enemy.with("army_id",new Bool(false));
        var actual=WarRecentTactics.evaluate(List.of(advance(1,summary(24000,player,List.of(bad),50),summary(24432,player,List.of(bad),10),true)),
                obj(f("date_raw",number(24432))),OptionalInt.of(0),OptionalInt.of(88));
        assertTrue(actual.blockedEnemyIds().isEmpty());
        Obj missing=without(army(0,41,"regular",false),"current_province_id");
        Obj missingEnemy=without(enemy,"current_province_id");
        actual=WarRecentTactics.evaluate(List.of(advance(1,summary(24000,missing,List.of(missingEnemy),50),summary(24432,missing,List.of(missingEnemy),10),true)),
                obj(f("date_raw",number(24432))),OptionalInt.of(0),OptionalInt.of(88));
        assertTrue(actual.blockedEnemyIds().isEmpty()); assertTrue(actual.blockedProvinceIds().isEmpty());
    }
    @Test void missingTacticalIdsPreserveTheOriginalOmittedContactField() throws Exception {
        Obj snapshot=obj(f("date_raw",number(24)));
        Obj actual=WarRecentTactics.evaluate(List.of(),snapshot,OptionalInt.empty(),OptionalInt.of(88)).toJson();
        assertFalse(actual.members().containsKey("contact_stale"));
        assertEquals(actual,OriginalWarTacticsOracle.call(obj(f("operation",text("recent")),f("history",new Arr(List.of())),
                f("snapshot",snapshot),f("army_id",Nil.INSTANCE),f("war_id",number(88)))));
    }
    private static Obj compare(List<Obj> history,int date,int army) throws Exception {
        Obj snapshot=obj(f("date_raw",number(date)));
        Obj actual=WarRecentTactics.evaluate(history,snapshot,OptionalInt.of(army),OptionalInt.of(88)).toJson();
        assertEquals(actual,OriginalWarTacticsOracle.call(obj(f("operation",text("recent")),f("history",new Arr(List.copyOf(history))),
                f("snapshot",snapshot),f("army_id",number(army)),f("war_id",number(88)))));
        return actual;
    }
    private static Obj army(int id,int province,String state,boolean retreating) {
        return obj(f("army_id",number(id)),f("current_province_id",number(province)),f("army_state",text(state)),
                f("retreating",new Bool(retreating)),f("in_combat",new Bool(false)));
    }
    private static Obj summary(int date,Obj player,List<Obj> enemies,int score) {
        Obj war=obj(f("war_id",number(88)),f("player_relative_war_score",number(score)),f("player_armies",new Arr(List.of(player))),
                f("enemy_armies",new Arr(List.copyOf(enemies))),f("war_objective_province_ids",numbers(List.of(41))));
        return obj(f("date_raw",number(date)),f("wars",new Arr(List.of(war))));
    }
    private static Obj result(Obj before,Obj after) { return obj(f("war_progress_before",before),f("war_progress_after",after)); }
    private static Obj without(Obj source,String field) {
        var values=new java.util.LinkedHashMap<>(source.members()); values.remove(field); return new Obj(values);
    }
    private static Obj advance(int index,Obj before,Obj after,boolean ok) {
        return obj(f("index",number(index)),f("command",text("life-advance")),f("ok",new Bool(ok)),f("result",result(before,after)));
    }
}
