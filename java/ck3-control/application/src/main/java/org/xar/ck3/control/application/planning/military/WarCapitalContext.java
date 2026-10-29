package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.LateWarCoreInputs.is;
import static org.xar.ck3.control.application.planning.military.CapitalRegroupEligibility.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.military.LateWarCoreInputs.Context;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.warexit.WarExitLateBridge;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Current campaign-root and defender admission, strategy707..795,882..934,16718..16888. */
public final class WarCapitalContext {
    private WarCapitalContext() {}
    private static final List<String> ROOT_PARTS=List.of("player_identity_ready","player_monthly_gold_income_ready",
            "player_health_ready","player_domain_ready","player_targeting_factions_ready","primary_title_ready",
            "primary_title_succession_ready","held_title_partition_ready","capital_ready","lieges_ready",
            "direct_landed_vassals_ready","adjacent_external_province_holders_ready","related_character_contexts_ready",
            "government_ready","same_frame_ready");
    public static Optional<Obj> sameFrameRoot(PlanningRequest request) {
        Obj snapshot=request.observations().snapshot();Obj player=object(snapshot.get("played_character"));
        if(!(player.get("character_id") instanceof IntegerValue&&snapshot.get("native_revision") instanceof IntegerValue
                &&snapshot.get("date_raw") instanceof IntegerValue))return Optional.empty();
        List<Obj> candidates=new ArrayList<>();List<Obj> history=request.observations().history();
        for(int i=history.size()-1;i>=0;i--) {
            Obj row=history.get(i);Obj result=result(row);
            if("query-campaign-root-context-v1".equals(command(row))&&yes(row.get("ok"))&&result!=null
                    &&result.get("campaign_root_context") instanceof Obj root)candidates.add(root);
        }
        if(snapshot.get("campaign_root_context") instanceof Obj root)candidates.add(root);
        for(Obj root:candidates) {
            Obj readiness=object(root.get("readiness"));
            if(is(root,"status","available")&&Objects.equals(root.get("snapshot_revision"),snapshot.get("native_revision"))
                    &&Objects.equals(root.get("date_raw"),snapshot.get("date_raw"))
                    &&Objects.equals(root.get("player_character_id"),player.get("character_id"))
                    &&(yes(readiness.get("ready"))||no(readiness.get("ready"))&&no(readiness.get("selected_game_rule_tokens_ready"))
                        &&ROOT_PARTS.stream().allMatch(key->yes(readiness.get(key)))))return Optional.of(root);
        }
        return Optional.empty();
    }
    private record County(int title,int province) {}
    public static Optional<List<Integer>> directlyHeldCountyCapitals(Obj root) {
        Obj ready=object(root.get("readiness"));
        if(!yes(ready.get("held_title_partition_ready"))||!(root.get("held_title_partition") instanceof Arr partition))return Optional.empty();
        List<County> counties=new ArrayList<>();
        for(Value raw:partition.items()) {
            if(!(raw instanceof Obj row))return Optional.empty();
            if(row.members().containsKey("capital_province_kind")||row.members().containsKey("title_key")) {
                if(landlessFamily(row))continue;
                return Optional.empty();
            }
            if(!(row.get("title") instanceof Obj title))return Optional.empty();
            Integer titleId=optionalInt(title.get("title_id")),tier=optionalInt(title.get("tier_raw"));
            if(titleId==null||tier==null)return Optional.empty();
            if(tier!=2)continue;
            Integer province=optionalInt(row.get("capital_province_id"));if(province==null||province<=0)return Optional.empty();
            counties.add(new County(titleId,province));
        }
        if(counties.isEmpty())return Optional.empty();
        List<Integer> ids=counties.stream().sorted(Comparator.comparingInt(County::title)).map(County::province).toList();
        return new HashSet<>(ids).size()==ids.size()?Optional.of(ids):Optional.empty();
    }
    private static boolean landlessFamily(Obj row) {
        Obj title=object(row.get("title"));Integer tier=optionalInt(title.get("tier_raw"));
        String key=optionalText(row.get("title_key"));Integer titleId=optionalInt(title.get("title_id"));
        Integer heir=optionalInt(row.get("first_heir_character_id"));
        return row.members().keySet().equals(Set.of("title","first_heir_character_id","capital_province_id","primary","capital_province_kind","title_key"))
                &&title.members().keySet().equals(Set.of("title_id","tier_raw","tier_key"))
                &&titleId!=null&&titleId>0&&tier!=null&&tier==2&&is(title,"tier_key","county")&&row.get("primary") instanceof Bool
                &&row.get("capital_province_id")==Nil.INSTANCE&&is(row,"capital_province_kind","landless_noble_family_no_province")
                &&key!=null&&key.length()>=3&&key.length()<=1024&&key.matches("c_[A-Za-z0-9][A-Za-z0-9_]*")
                &&(row.get("first_heir_character_id")==Nil.INSTANCE||heir!=null&&heir>0);
    }
    public static Optional<Obj> primaryDefenderHold(Context c,boolean observableEnemyRoutes,boolean defeatScoreContact) {
        var p=c.published();Obj war=c.war();Army army=c.subject();Integer score=optionalInt(war.get("player_relative_war_score"));
        if(!(quiet(c)&&is(war,"player_side","defender")&&yes(war.get("player_is_primary_war_leader"))&&score!=null
                &&(score>-100&&score<100||score==-100&&observableEnemyRoutes&&defeatScoreContact)
                &&p.rankedExactObjectives().isEmpty()&&c.controlled().size()==1&&p.unsafeArmyIds().isEmpty()
                &&p.activeAssaults().isEmpty()&&army.moveTargetPresent()&&idle(army,true)))return Optional.empty();
        if(c.enemies().isEmpty()||c.enemies().size()>64)return Optional.empty();
        for(Army enemy:c.enemies()) {
            if(enemy.current()==null||!Boolean.FALSE.equals(enemy.inCombat())||!Boolean.FALSE.equals(enemy.retreating())
                    ||!enemy.moveTargetPresent()||enemy.route().isEmpty())return Optional.empty();
            List<Integer> route=enemy.route().orElseThrow();
            if(observableEnemyRoutes) {
                if(!List.of("gathering","regular","moving","sieging","embarked").contains(enemy.tacticalState()==null?"":enemy.tacticalState())
                        ||!(enemy.target()==null&&route.isEmpty()||enemy.target()!=null&&!route.isEmpty()&&route.getLast().equals(enemy.target())))return Optional.empty();
            } else if(!"gathering".equals(enemy.tacticalState())||enemy.target()!=null||!route.isEmpty())return Optional.empty();
        }
        Obj summary=p.warSummaries().stream().filter(r->Objects.equals(optionalInt(r.get("war_id")),p.tacticalWarId())).findFirst().orElse(null);
        if(summary==null)return Optional.empty();
        Obj reuse=object(summary.get("war_termination_negative_reuse")),options=c.termination();Obj evidence;
        if(is(reuse,"status","negative_assessment_reused"))evidence=obj(f("status",text("negative_assessment_reused")),
                f("queried_date_raw",nullable(reuse.get("queried_date_raw"))),f("expires_date_raw",nullable(reuse.get("expires_date_raw"))));
        else if(sameFrameTermination(c,options)&&is(options,"player_side","defender")&&yes(options.get("player_is_primary_war_leader"))
                &&Objects.equals(options.get("player_relative_war_score"),war.get("player_relative_war_score"))
                &&!WarExitLateBridge.authorizedExitCandidate(c.request(),p.tacticalWarId()))
            evidence=obj(f("status",text("same_frame_no_authorized_exit")),f("queried_snapshot_id",nullable(options.get("queried_snapshot_id"))),
                    f("queried_revision",nullable(options.get("queried_revision"))));
        else return Optional.empty();
        return Optional.of(obj(f("status",text("ready")),f("war_id",number(p.tacticalWarId())),f("army_id",number(army.id())),
                f("current_province_id",number(c.current())),f("termination_evidence",evidence),f("enemy_army_ids",numbers(c.hostileIds()))));
    }
    private static boolean sameFrameTermination(Context c,Obj row) {
        Obj s=c.snapshot(),d=object(s.get("diagnostics"));
        return Objects.equals(optionalInt(row.get("war_id")),c.published().tacticalWarId())
                &&Objects.equals(row.get("queried_snapshot_id"),s.get("snapshot_id"))&&Objects.equals(row.get("queried_revision"),s.get("revision"))
                &&Objects.equals(row.get("queried_native_revision"),s.get("native_revision"))
                &&Objects.equals(row.get("queried_connection_generation"),d.get("connection_generation"))
                &&Objects.equals(row.get("episode_run_id"),s.get("episode_run_id"));
    }
}
