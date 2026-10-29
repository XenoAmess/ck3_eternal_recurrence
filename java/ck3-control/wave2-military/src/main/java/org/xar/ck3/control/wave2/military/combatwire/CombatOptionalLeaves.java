package org.xar.ck3.control.wave2.military.combatwire;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputs.Army;

/** Narrow boundary for the independently migrated additive exact-build leaves. */
public interface CombatOptionalLeaves {
    enum Leaf {
        PHASE_RITE_PARAMETERS("phase_rite_parameters_v1"),
        PHASE_WARMONGER_CORE("phase_warmonger_core_v1"),
        PHASE_BERSERKER_VALIDITY("phase_berserker_validity_inputs_v1"),
        PHASE_BERSERKER_CHANCE("phase_berserker_chance_inputs_v1"),
        PHASE_EVENT_CALENDAR("phase_event_calendar_observation_v1"),
        PHASE_EVENT_ROLE_COMPATIBILITY("phase_event_role_compatibility_v1"),
        PHASE_EVENT_COMMANDER_SIDE_IDENTITY("phase_event_commander_side_identity_v1"),
        PHASE_EVENT_COMMANDER_TRIGGER("phase_event_commander_trigger_conditions_v1"),
        PHASE_EVENT_COMMANDER_CHANCE("phase_event_commander_chance_weights_v1"),
        KNIGHT_STAT_CONSUMPTION("knight_stat_consumption_v1"),
        KNIGHT_CURRENT_MODEL_ASSOCIATION("current_model_association_v1"),
        ORDINARY_STAT_INPUTS("ordinary_stat_inputs_v1"),
        MAA_STAT_INPUTS("maa_stat_inputs_v1");
        private final String wireName;
        Leaf(String name){wireName=name;}
        public String wireName(){return wireName;}
    }
    record Context(String path,Integer expectedCharacterId,List<Army> armies,ObjectNode normalizedRoot) {
        public Context { armies=List.copyOf(armies);normalizedRoot=normalizedRoot==null?null:normalizedRoot.deepCopy(); }
        @Override public ObjectNode normalizedRoot(){return normalizedRoot==null?null:normalizedRoot.deepCopy();}
    }
    /** Implementations validate before constructing their typed leaf and return its canonical JSON. */
    JsonNode normalize(Leaf leaf,JsonNode value,Context context);

    /** All thirteen published leaves are actual strict normalizers in this installation. */
    static CombatOptionalLeaves complete(){
        return compose(new CombatPhaseOptionalLeaves(),new CombatPhysicalStatLeaves());
    }

    /** Explicit complete installation: each leaf has exactly one owning normalizer. */
    static CombatOptionalLeaves compose(CombatOptionalLeaves phase,CombatOptionalLeaves physical){
        java.util.Objects.requireNonNull(phase);java.util.Objects.requireNonNull(physical);
        return (leaf,value,context)->switch(leaf){
            case KNIGHT_STAT_CONSUMPTION,KNIGHT_CURRENT_MODEL_ASSOCIATION,ORDINARY_STAT_INPUTS,MAA_STAT_INPUTS -> physical.normalize(leaf,value,context);
            case PHASE_RITE_PARAMETERS,PHASE_WARMONGER_CORE,PHASE_BERSERKER_VALIDITY,PHASE_BERSERKER_CHANCE,
                 PHASE_EVENT_CALENDAR,PHASE_EVENT_ROLE_COMPATIBILITY,PHASE_EVENT_COMMANDER_SIDE_IDENTITY,
                 PHASE_EVENT_COMMANDER_TRIGGER,PHASE_EVENT_COMMANDER_CHANCE -> phase.normalize(leaf,value,context);
        };
    }

    /** No unpublished leaf acquires invented observations; present unsupported leaves fail closed. */
    static CombatOptionalLeaves unpublishedOnly(){
        return (leaf,value,context)->{
            if(CombatWire.nil(value))return NullNode.instance;
            throw new IllegalArgumentException("combat optional leaf codec not installed: "+leaf.wireName());
        };
    }
}

