package org.xar.ck3.control.wave2.military.combatwire.phaseevent;

import static org.xar.ck3.control.wave2.military.combatwire.phaseevent.PhaseJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

/** Exact 1.19.0.6 source identity. Never grants qualification to another build or loaded playset. */
public final class StockPhaseManifest {
    public static final String SHA256="91EDCEEDC634C5ACDCFAC8B02F53FE74C4E7A2E1768AAFC12CD0D976E874F2AC";
    public static final String RESOURCE="/org/xar/ck3/control/wave2/military/combatwire/phaseevent/ck3_1_19_0_6_stock_combat_phase_events.json";
    public record Source(String relativePath,String sha256,int loadOrder) { }
    static final class Row {
        final int index,typeIndex; final String key,type; final long baseWeight; final ObjectNode validity,chance,effect; final Set<String> dependencies,tags;
        Row(ObjectNode row){index=(int)signed(row.get("global_load_index"),"row index");typeIndex=(int)signed(row.get("type_load_index"),"type index");key=text(row.get("key"),"key");type=text(row.get("type"),"type");baseWeight=signed(row.get("base_weight"),"base weight");validity=object(row.get("validity_ast"),"validity").deepCopy();chance=object(row.get("chance_ast"),"chance").deepCopy();effect=object(row.get("effect_ast"),"effect").deepCopy();dependencies=strings(row.get("state_dependencies"),"dependencies");tags=strings(row.get("transition_tags"),"transition tags");}
    }
    private final List<Source> sources;
    final List<Row> rows;
    private final Set<String> dependencies;
    private final ObjectNode payload;
    private StockPhaseManifest(byte[] bytes){
        JsonNode parsed;try{parsed=JSON.readTree(bytes);}catch(IOException e){throw new IllegalArgumentException("phase manifest is invalid JSON",e);}
        ObjectNode root=object(parsed,"manifest");
        List<String> order=new ArrayList<>();root.fieldNames().forEachRemaining(order::add);
        require(order.equals(List.of("schema_version","game_version","executable_sha256","rules_source","files","event_rows","supported_transition_opcodes","completeness","canonical_manifest_sha256")),"manifest top-level schema/order drifted");
        require(text(root.get("canonical_manifest_sha256"),"manifest sha").equals(SHA256),"manifest claimed SHA drifted");ObjectNode unhashed=root.deepCopy();unhashed.remove("canonical_manifest_sha256");require(digest(unhashed).equals(SHA256),"manifest canonical SHA drifted");
        require(signed(root.get("schema_version"),"schema_version")==1,"manifest version drifted");require(text(root.get("game_version"),"game_version").equals("1.19.0.6"),"manifest game drifted");require(text(root.get("executable_sha256"),"executable SHA").equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"manifest executable drifted");require(text(root.get("rules_source"),"rules_source").equals("stock-installation-static-manifest"),"manifest source drifted");
        List<Source> pins=new ArrayList<>();for(JsonNode raw:array(root.get("files"),"files")){keys(raw,"relative_path sha256 load_order","source");String sha=text(raw.get("sha256"),"source SHA");require(sha.matches("[0-9A-F]{64}"),"malformed source SHA");int index=pins.size();require(signed(raw.get("load_order"),"load_order")==index,"source load order drifted");pins.add(new Source(text(raw.get("relative_path"),"relative_path"),sha,index));}sources=List.copyOf(pins);
        require(root.get("supported_transition_opcodes").equals(PhaseConstants.TRANSITIONS),"transition order drifted");
        ArrayNode rawRows=array(root.get("event_rows"),"event_rows");require(rawRows.size()==13,"phase manifest must contain 13 rows");List<Row> selected=new ArrayList<>();Set<String> all=new HashSet<>(),seen=new HashSet<>();int commander=0,knight=0;
        for(JsonNode raw:rawRows){keys(raw,"global_load_index type_load_index key type base_weight validity_ast chance_ast effect_ast transition_tags state_dependencies","event row");Row row=new Row(object(raw,"event row"));require(row.index==selected.size(),"global event order drifted");require(row.type.equals("commander")||row.type.equals("knight"),"unknown event family");int wanted=row.type.equals("commander")?commander++:knight++;require(row.typeIndex==wanted,"per-type event order drifted");require(seen.add(row.key),"duplicate phase key");strings(raw.get("transition_tags"),"transition tags");selected.add(row);all.addAll(row.dependencies);}
        require(commander==4&&knight==9,"event type counts drifted");rows=List.copyOf(selected);dependencies=Set.copyOf(all);
        JsonNode completeness=root.get("completeness");keys(completeness,"loaded_playset_verified ast_evaluator_ready original_trace_ready unsupported_opcodes","completeness");for(String key:List.of("loaded_playset_verified","ast_evaluator_ready","original_trace_ready"))bool(completeness.get(key),key);strings(completeness.get("unsupported_opcodes"),"unsupported_opcodes");payload=root.deepCopy();
    }
    public static StockPhaseManifest load(){try(InputStream stream=StockPhaseManifest.class.getResourceAsStream(RESOURCE)){if(stream==null)throw new IllegalArgumentException("pinned phase manifest resource missing: "+RESOURCE);return new StockPhaseManifest(stream.readAllBytes());}catch(IOException e){throw new IllegalArgumentException("cannot read phase manifest",e);}}
    public static StockPhaseManifest load(Path path){try{return new StockPhaseManifest(Files.readAllBytes(path));}catch(IOException e){throw new IllegalArgumentException("cannot read manifest "+path,e);}}
    public String canonicalSha256(){return SHA256;}
    public List<Source> sources(){return sources;}
    public Set<String> requiredStateRefs(){return dependencies;}
    public ObjectNode toJson(){return payload.deepCopy();}
    public boolean fidelityGate(){JsonNode c=payload.get("completeness");return bool(c.get("loaded_playset_verified"),"playset")&&bool(c.get("ast_evaluator_ready"),"evaluator")&&bool(c.get("original_trace_ready"),"trace");}
    public void requireEvaluatorReady(){if(!fidelityGate())throw new IllegalStateException("stock AST loaded-playset/evaluator/original-trace gates are not all ready");}
}
