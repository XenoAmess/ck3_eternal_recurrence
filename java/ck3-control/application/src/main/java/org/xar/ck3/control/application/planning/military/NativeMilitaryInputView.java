package org.xar.ck3.control.application.planning.military;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/**
 * Necessary operand equality for military read reuse. This is data comparison, not freshness or readiness.
 * The sole publisher must additionally prove the exact original contract/decoder, current raw native
 * bytes, source, Game/session/connection, full factual identity, arguments and active capabilities.
 */
public final class NativeMilitaryInputView {
    private NativeMilitaryInputView() {}
    public enum Field {
        SNAPSHOT_ID("snapshot_id"), REVISION("revision"), NATIVE_REVISION("native_revision"), DATE("date_raw"),
        EPISODE("episode_run_id"), PAUSED("paused"), MAP_READY("map_ready"), SPEED("speed"),
        PLAYER("played_character"), ARMIES("player_armies"), WARS("active_wars"), DECLARABLE_WARS("declarable_wars"),
        EVENT("active_event"), INTERACTION("pending_character_interaction"), TERMINAL("one_life_terminal_reason");
        private final String wire;
        Field(String wire){this.wire=wire;}
        public String wire(){return wire;}
    }
    public record Projection(ActiveRetreatProposal.SourceFrame frame,Obj taggedOperands,Obj taggedTransport) {
        public Projection {
            Objects.requireNonNull(frame);Objects.requireNonNull(taggedOperands);Objects.requireNonNull(taggedTransport);
            OpportunityJson.require(taggedOperands.members().keySet().equals(java.util.Arrays.stream(Field.values()).map(Field::wire).collect(java.util.stream.Collectors.toSet()))
                    &&taggedTransport.members().keySet().equals(java.util.Set.of("connection_generation","bridge_pid")),"fixed native military operand fields required");
            taggedOperands.members().values().forEach(NativeMilitaryInputView::tagged);
            taggedTransport.members().values().forEach(NativeMilitaryInputView::tagged);
        }
    }
    /** Complete native military arrays are retained; no empty army/war value is inferred from a missing field. */
    public static Projection capture(Obj originalSnapshot) {
        Objects.requireNonNull(originalSnapshot);var frame=ActiveRetreatProposal.SourceFrame.read(originalSnapshot);
        OpportunityJson.object(originalSnapshot.get("played_character"),"actual military player");
        OpportunityJson.array(originalSnapshot.get("player_armies"),"actual native player armies");
        OpportunityJson.array(originalSnapshot.get("active_wars"),"actual native active wars");
        Obj diagnostics=OpportunityJson.object(originalSnapshot.get("diagnostics"),"actual native transport diagnostics");
        var fields=new LinkedHashMap<String,Value>();for(Field field:Field.values())fields.put(field.wire(),tag(originalSnapshot,field.wire()));
        return new Projection(frame,new Obj(fields),new Obj(Map.of("connection_generation",tag(diagnostics,"connection_generation"),"bridge_pid",tag(diagnostics,"bridge_pid"))));
    }
    public static boolean sameNativeOperands(Obj originalSnapshot,Obj currentSnapshot) {
        try{return capture(originalSnapshot).equals(capture(currentSnapshot));}
        catch(IllegalArgumentException invalid){return false;}
    }
    private static Arr tag(Obj object,String key) {
        return object.members().containsKey(key)?new Arr(List.of(new Bool(true),object.get(key))):new Arr(List.of(new Bool(false)));
    }
    private static void tagged(Value raw) {
        var items=OpportunityJson.array(raw,"presence-tagged native operand");
        OpportunityJson.require(items.size()==1&&new Bool(false).equals(items.getFirst())
                ||items.size()==2&&new Bool(true).equals(items.getFirst()),"native operand must preserve missing/null presence");
    }
}
