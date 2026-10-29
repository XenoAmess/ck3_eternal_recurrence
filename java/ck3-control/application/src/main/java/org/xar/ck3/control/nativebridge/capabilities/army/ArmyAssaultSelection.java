package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One assault subject selection reducer, shared by preparation and independent effect replay. */
public final class ArmyAssaultSelection {
    public enum Source { OBJECTIVE, OCCUPATION }
    public record Siege(int id,boolean assaultObservable,boolean inProgress,boolean canStart,boolean canStop,boolean playerBesieging) {
        public Siege { StrictJson.require(id>=0,"complete nonnegative native SiegeID DATA required"); }
    }
    public record Holding(int warId,int provinceId,boolean siegeObservable,Optional<Siege> siege) {
        public Holding { StrictJson.require(warId>=0 && provinceId>=0,"complete nonnegative native war/province DATA required");Objects.requireNonNull(siege);StrictJson.require(siegeObservable || siege.isEmpty(),"unobservable holding cannot invent active siege"); }
    }
    public record Observation(int warId,int provinceId,Siege siege,Source source) {
        public Observation { StrictJson.require(warId>0 && provinceId>0,"positive complete assault location required");Objects.requireNonNull(siege);Objects.requireNonNull(source); }
    }
    private ArmyAssaultSelection() { }
    public static Optional<Observation> select(OpportunityJson.Obj actualFrame,List<Holding> sameFrameHoldings,int fullSiegeId) {
        StrictJson.require(fullSiegeId>0,"positive complete SiegeID required");Objects.requireNonNull(sameFrameHoldings);
        JsonNode frame=OpportunityJson.toNode(actualFrame);
        if(!flag(frame.get("paused")))return Optional.empty();
        JsonNode wars=frame.get("active_wars");StrictJson.require(wars!=null && wars.isArray(),"actual active war array required");
        List<Observation> matches=new ArrayList<>();
        for(JsonNode war:wars) {
            StrictJson.require(war.isObject(),"actual active war row required");Integer warId=positive(war.get("war_id"));
            if(warId==null)continue;
            Set<Integer> observedProvinces=new HashSet<>();JsonNode objectives=war.get("objective_province_states");
            if(objectives!=null && !objectives.isNull()) {
                StrictJson.require(objectives.isArray(),"actual objective province array required");
                for(JsonNode row:objectives) {
                    StrictJson.require(row.isObject(),"objective province row required");Integer province=positive(row.get("province_id"));
                    boolean observable=flag(row.get("siege_observable"));
                    if(observable && province!=null)observedProvinces.add(province);
                    if(!observable || province==null)continue;
                    Optional<Siege> siege=objectiveSiege(row.get("active_siege"));
                    if(siege.filter(value->value.id()==fullSiegeId && value.assaultObservable()).isPresent())
                        matches.add(new Observation(warId,province,siege.orElseThrow(),Source.OBJECTIVE));
                }
            }
            for(Holding holding:List.copyOf(sameFrameHoldings))
                if(holding.warId()==warId && holding.provinceId()>0 && !observedProvinces.contains(holding.provinceId()) && holding.siegeObservable()
                        && holding.siege().filter(value->value.id()==fullSiegeId && value.assaultObservable()).isPresent())
                    matches.add(new Observation(warId,holding.provinceId(),holding.siege().orElseThrow(),Source.OCCUPATION));
        }
        return matches.size()==1?Optional.of(matches.getFirst()):Optional.empty();
    }
    private static Optional<Siege> objectiveSiege(JsonNode value) {
        if(value==null || value.isNull())return Optional.empty();
        StrictJson.require(value.isObject(),"actual active siege object required");Integer id=positive(value.get("siege_id"));
        if(id==null || !flag(value.get("assault_observable")))return Optional.empty();
        return Optional.of(new Siege(id,true,bool(value.get("assault_in_progress")),bool(value.get("can_start_assault")),
                bool(value.get("can_stop_assault")),bool(value.get("player_army_besieging"))));
    }
    private static Integer positive(JsonNode value) {
        if(value==null || value.isNull())return null;
        int id=(int)StrictJson.integer(value,0,Integer.MAX_VALUE);return id>0?id:null;
    }
    private static boolean flag(JsonNode value) { if(value==null || value.isNull())return false;return bool(value); }
    private static boolean bool(JsonNode value) { StrictJson.require(value!=null && value.isBoolean(),"explicit actual siege Boolean required");return value.booleanValue(); }
}
