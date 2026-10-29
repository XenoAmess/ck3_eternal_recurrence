package org.xar.ck3.control.wave2.military.combatwire;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.xar.ck3.control.wave2.military.combatwire.CombatEncounterScope.Coalition;
import org.xar.ck3.control.wave2.military.combatwire.CombatEncounterScope.ScopeRole;

/**
 * Immutable normalized v2 observation. The detached canonical wire is retained solely
 * for lossless transport to the phase/forecast consumers; typed records are the domain seam.
 * Instances are created only after runtime validation of the entire observation.
 */
public final class CombatSimulationInputs {
    public enum Status { AVAILABLE, ABSENT, UNAVAILABLE }
    public enum EncounterRole { ATTACKER, DEFENDER }
    public enum RegimentKind { LEVY, MEN_AT_ARMS }
    public record Owner(Status status,Integer characterId,Long counterEfficiencyRaw,Long counterResistanceRaw,String unavailableReason) { }
    public record BattleContext(Status status,Integer sourceTargetProvinceId,Integer effectiveMinRoll,Integer effectiveMaxRoll,String unavailableReason) { }
    public record Commander(Status status,Integer characterId,Integer genericAdvantagePoints,BattleContext battleContext,String unavailableReason) { }
    public record EffectiveStats(Status status,Integer sourceTargetProvinceId,Integer maxSize,Long siegeValueRaw,Long damageRaw,Long toughnessRaw,Long pursuitRaw,Long screenRaw,String unavailableReason) { }
    public record MaaType(Status status,String key,String unavailableReason) { }
    public record Kind(Status status,RegimentKind value,String unavailableReason) { }
    public record CounterTarget(int classIndex,long effectivenessRaw) { }
    public record Counter(Status status,Integer classIndex,Long currentChunkRaw,List<CounterTarget> targets,String unavailableReason) {
        public Counter { targets=targets==null?null:List.copyOf(targets); }
    }
    public record Regiment(Status status,int regimentId,boolean identityValid,int currentSoldiers,int maximumSoldiers,MaaType maaType,
        Kind kind,Boolean fightsInMainPhase,EffectiveStats effectiveStats,Counter counter,String unavailableReason) { }
    public record Knight(int characterId,int sourceRegimentId,int armyId,int prowess,long effectivenessRaw,long damageRaw,long toughnessRaw) { }
    public record Knights(Status status,List<Knight> members,Integer loadedDamageMultiplier,Integer loadedToughnessMultiplier,boolean damageMultiplierPublished,boolean toughnessMultiplierPublished,String unavailableReason) {
        public Knights { members=members==null?null:List.copyOf(members); }
    }
    public record Army(Status status,int armyId,EncounterRole encounterRole,Integer nativeCarmyId,ScopeRole scopeRole,List<Integer> warIds,
        Integer currentProvinceId,Owner owner,Commander commander,List<Regiment> regiments,Knights knights,String unavailableReason) {
        public Army { warIds=List.copyOf(warIds);regiments=regiments==null?null:List.copyOf(regiments); }
    }
    public record Scenario(Integer attackerEntryProvinceId,List<Integer> attackerArmyIds,List<Integer> defenderArmyIds,Coalition attackerSide,Coalition defenderSide,boolean constructorZero) {
        public Scenario { attackerArmyIds=List.copyOf(attackerArmyIds);defenderArmyIds=List.copyOf(defenderArmyIds); }
    }
    public record Terrain(Status status,String key,Long combatWidthMultiplierRaw,String unavailableReason) { }
    public record Crossing(Status status,String kind,String unavailableReason) { }
    public record DefenderContext(Status status,Coalition defenderSide,Status holdingDefenderStatus,Boolean holdingDefender,String holdingUnavailableReason,String unavailableReason) { }
    public record Width(Status status,Integer base,Integer finalWidth,String unavailableReason) { }
    public record TargetProvince(Status status,int provinceId,Terrain terrain,Crossing crossing,DefenderContext defenderContext,Width precontactWidth,String unavailableReason) { }
    public record OngoingCombat(Status status,Integer combatId,Integer provinceId,Integer phase,Integer phaseDay,Integer baseWidth,Integer finalWidth,
        Integer side0Roll,Integer side1Roll,Long baseAdvantage,Long resolvedAdvantage,String orientation,String unavailableReason) { }
    public record CounterResolution(Status status,Coalition counteredSide,Coalition counteringSide,Integer counteredOwner,Integer counteringOwner,
        Long contextScaleRaw,int classCount,List<Long> retention,String unavailableReason) {
        public CounterResolution { retention=retention==null?null:List.copyOf(retention); }
    }
    public record Completeness(boolean inputObservationReady,boolean monteCarloReady,List<String> missingRequiredDomains) {
        public Completeness { missingRequiredDomains=List.copyOf(missingRequiredDomains); }
    }
    private final int targetProvinceId;
    private final Scenario scenario;
    private final List<Army> armies;
    private final TargetProvince targetProvince;
    private final List<OngoingCombat> ongoingCombats;
    private final List<CounterResolution> counterResolutions;
    private final Completeness completeness;
    private final ObjectNode wire;
    CombatSimulationInputs(int targetProvinceId,Scenario scenario,List<Army> armies,TargetProvince targetProvince,
            List<OngoingCombat> ongoingCombats,List<CounterResolution> counterResolutions,Completeness completeness,ObjectNode wire) {
        this.targetProvinceId=targetProvinceId;this.scenario=scenario;this.armies=List.copyOf(armies);this.targetProvince=targetProvince;
        this.ongoingCombats=List.copyOf(ongoingCombats);this.counterResolutions=List.copyOf(counterResolutions);this.completeness=completeness;this.wire=wire.deepCopy();
    }
    public int targetProvinceId(){return targetProvinceId;}
    public Scenario scenario(){return scenario;}
    public List<Army> armies(){return armies;}
    public TargetProvince targetProvince(){return targetProvince;}
    public List<OngoingCombat> ongoingCombats(){return ongoingCombats;}
    public List<CounterResolution> counterResolutions(){return counterResolutions;}
    public Completeness completeness(){return completeness;}
    public String status(){return completeness.inputObservationReady()?"available":"partial";}
    /** Java-internal original normalized JSON domain. External identity/sequence/time
     * fields require the shared decimal-string transport encoder before crossing JavaScript. */
    public ObjectNode toJson(){return wire.deepCopy();}
}

