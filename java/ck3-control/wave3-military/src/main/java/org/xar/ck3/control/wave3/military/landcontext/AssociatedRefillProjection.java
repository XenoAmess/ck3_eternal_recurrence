package org.xar.ck3.control.wave3.military.landcontext;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.replenishment.ReplenishmentModel;
import org.xar.ck3.control.replenishment.ReplenishmentPolicy;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorCodec;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel;

/** One explicit core call per observed persistent cache. DATA aliases share one ADD and remain repeated refresh contributions. */
public final class AssociatedRefillProjection {
    private AssociatedRefillProjection() {}
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public sealed interface Gap permits FieldGap,ChunkGap,RegimentGap {}
    public record FieldGap(String input) implements Gap {public FieldGap {Objects.requireNonNull(input);}}
    public record ChunkGap(int persistentRegimentId,int chunkIndex,List<String> inputs) implements Gap {public ChunkGap {inputs=List.copyOf(inputs);}}
    public record RegimentGap(int armyRegimentId,List<String> inputs) implements Gap {public RegimentGap {inputs=List.copyOf(inputs);}}
    public record Key(int persistentRegimentId,int chunkIndex) {}
    public record Occurrence(int armyRegimentId,int recordIndex) {}
    public record Input(boolean available,int armyId,List<FullDataModel.Snapshot> snapshots,List<LossSequenceModel.Regiment> strengths) {
        public Input {snapshots=snapshots==null?null:List.copyOf(snapshots);strengths=strengths==null?null:List.copyOf(strengths);}
    }
    public record Chunk(Key key,Status status,Integer currentBefore,Integer sameInputQ,Integer current,Integer maximum,
            Integer state,Integer associatedRegiment,Integer physicalAddCount,List<Occurrence> occurrences,List<String> missing) {
        public Chunk {Objects.requireNonNull(key);Objects.requireNonNull(status);occurrences=List.copyOf(occurrences);missing=List.copyOf(missing);}
    }
    public record Coverage(int persistentRegimentId,boolean allSevenRequestsObserved,Boolean nativeCoreAnyQualified,
            List<ReplenishmentModel.ChunkStatus> statusByChunk) {public Coverage {statusByChunk=List.copyOf(statusByChunk);}}
    public record Result(Status status,boolean chunksReady,boolean currentMaximumReady,boolean completePersistentRequestsReady,
            List<Chunk> chunks,List<RaisedRegimentRefresh.Result> refreshes,List<LossSequenceModel.FinalRegiment> strengths,
            List<Coverage> coverage,List<Gap> missing) {
        public Result {chunks=List.copyOf(chunks);refreshes=List.copyOf(refreshes);strengths=strengths==null?null:List.copyOf(strengths);coverage=List.copyOf(coverage);missing=List.copyOf(missing);}
    }
    private record Alias(FullDataModel.Snapshot snapshot,FullDataModel.DataRecord record) {}
    public static Input decode(JsonNode row) {
        StrictJson.require(row!=null&&row.isObject(),"associated refill row required");
        JsonNode raw=row.get("regiment_replenishment_records_v1");List<FullDataModel.Snapshot> snapshots=null;
        if(raw!=null&&!raw.isNull()) {StrictJson.require(raw.isArray(),"ordered associated DATA required");snapshots=new ArrayList<>();for(JsonNode value:raw)snapshots.add(LandContextCodec.decodeData(value));}
        var sequence=LossSequenceCodec.decodeArmyProjection(row);
        return new Input(new com.fasterxml.jackson.databind.node.TextNode("available").equals(row.get("status")),
                (int)StrictJson.integer(row.get("army_id"),Integer.MIN_VALUE,Integer.MAX_VALUE),snapshots,sequence.regiments());
    }
    public static Result project(JsonNode row) {return project(decode(row));}
    public static Result project(Input input) {
        if(!input.available()||input.snapshots()==null)return new Result(Status.UNAVAILABLE,false,false,false,List.of(),List.of(),null,List.of(),List.of(new FieldGap("available_associated_DATA_snapshot")));
        List<ReplenishmentModel.FullDataSnapshot> numeric=new ArrayList<>();
        for(var snapshot:input.snapshots()) {
            List<ReplenishmentModel.FullDataRecord> records=snapshot.records().stream().map(r->new ReplenishmentModel.FullDataRecord(
                ReplenishmentModel.RecordStatus.valueOf(r.status().name()),r.unavailableReason(),r.recordIndex(),r.persistentRegimentId(),r.chunkIndex(),
                r.maximumSoldiers(),r.effectiveCurrentSoldiers(),r.preparedFractionRaw(),r.preparedFractionScale(),r.nativeChunkCanReplenish())).toList();
            numeric.add(new ReplenishmentModel.FullDataSnapshot(snapshot.armyRegimentId(),ReplenishmentModel.CoverageStatus.valueOf(snapshot.status().name()),snapshot.nativeDataRecordCount(),snapshot.unavailableReason(),records));
        }
        var outputs=ReplenishmentPolicy.observedPersistentOutputs(List.of(new ReplenishmentModel.ArmyRow(input.armyId(),new ReplenishmentModel.PublishedSnapshots(numeric))));
        Map<Integer,ReplenishmentModel.PersistentOutput> byPersistent=new LinkedHashMap<>();List<Coverage> coverage=new ArrayList<>();
        for(var output:outputs) {
            boolean qualified=output.observationsByChunk().stream().flatMap(List::stream).anyMatch(o->o.calculation()!=null&&o.calculation().nativeCoreChunkQualifies());
            coverage.add(new Coverage(output.persistentRegimentId(),output.allSevenObserved(),qualified?Boolean.TRUE:output.allSevenObserved()?Boolean.FALSE:null,output.statusByChunk()));
            byPersistent.put(output.persistentRegimentId(),output);
        }
        Map<Key,List<Alias>> observations=new LinkedHashMap<>();
        for(var snapshot:input.snapshots())for(var record:snapshot.records())if(record.persistentRegimentId()!=-1&&record.chunkIndex()>=0&&record.chunkIndex()<7)
            observations.computeIfAbsent(new Key(record.persistentRegimentId(),record.chunkIndex()),ignored->new ArrayList<>()).add(new Alias(snapshot,record));
        List<Chunk> chunks=new ArrayList<>();List<Gap> missing=new ArrayList<>();
        for(var entry:observations.entrySet()) {
            Key key=entry.getKey();List<Alias> aliases=entry.getValue();var output=byPersistent.get(key.persistentRegimentId());List<String> reasons=new ArrayList<>();
            if(output==null||output.statusByChunk().get(key.chunkIndex())!=ReplenishmentModel.ChunkStatus.AVAILABLE)reasons.add("available_same_input_262c9d0_request");
            if(aliases.stream().anyMatch(a->a.record().status()!=FullDataModel.RecordStatus.AVAILABLE))reasons.add("available_physical_chunk_observation");
            if(aliases.stream().anyMatch(a->a.record().chunkArmyRegimentId()==null||a.record().chunkArmyRegimentId()==-1||a.record().chunkArmyRegimentId()!=a.snapshot().armyRegimentId()))reasons.add("observed_non_minus_one_chunk_association");
            var first=aliases.getFirst().record();
            if(aliases.stream().anyMatch(a->!Objects.equals(a.record().currentSoldiers(),first.currentSoldiers())||!Objects.equals(a.record().maximumSoldiers(),first.maximumSoldiers())||!Objects.equals(a.record().stateRaw(),first.stateRaw())||!Objects.equals(a.record().chunkArmyRegimentId(),first.chunkArmyRegimentId())))reasons.add("consistent_physical_alias_observations");
            List<Occurrence> positions=aliases.stream().map(a->new Occurrence(a.snapshot().armyRegimentId(),a.record().recordIndex())).toList();
            if(!reasons.isEmpty()) {chunks.add(new Chunk(key,Status.UNAVAILABLE,null,null,null,null,null,null,null,positions,reasons));missing.add(new ChunkGap(key.persistentRegimentId(),key.chunkIndex(),reasons));}
            else {
                int q=output.sameInputQByChunk().get(key.chunkIndex());Boolean admitted=coverage.stream().filter(c->c.persistentRegimentId()==key.persistentRegimentId()).findFirst().orElseThrow().nativeCoreAnyQualified();
                chunks.add(new Chunk(key,Status.AVAILABLE,first.currentSoldiers(),q,first.currentSoldiers()+q,first.maximumSoldiers(),first.stateRaw(),first.chunkArmyRegimentId(),admitted==null?null:admitted?1:0,positions,List.of()));
            }
        }
        List<RaisedRegimentRefresh.PhysicalChunk> physical=chunks.stream().filter(c->c.status()==Status.AVAILABLE).map(c->new RaisedRegimentRefresh.PhysicalChunk(c.key().persistentRegimentId(),c.key().chunkIndex(),c.current(),c.maximum())).toList();
        List<RaisedRegimentRefresh.Result> refreshes=input.snapshots().stream().map(snapshot->RaisedRegimentRefresh.project(LossSequenceCodec.decodeDataProjection(LandContextCodec.encodeData(snapshot)).snapshot(),physical)).toList();
        boolean roster=input.strengths()!=null&&input.strengths().stream().map(LossSequenceModel.Regiment::regimentId).toList().equals(input.snapshots().stream().map(FullDataModel.Snapshot::armyRegimentId).toList());
        if(!roster)missing.add(new FieldGap("complete_same_order_ArRg_DATA_roster"));
        for(var refresh:refreshes)if(!refresh.ready())missing.add(new RegimentGap(refresh.regimentId(),refresh.missingInputs()));
        boolean aggregate=roster&&refreshes.stream().allMatch(RaisedRegimentRefresh.Result::ready),chunksReady=physical.size()==chunks.size();
        Status status=chunksReady&&aggregate?Status.AVAILABLE:!physical.isEmpty()||refreshes.stream().anyMatch(RaisedRegimentRefresh.Result::ready)?Status.PARTIAL:Status.UNAVAILABLE;
        return new Result(status,chunksReady,aggregate,outputs.stream().allMatch(ReplenishmentModel.PersistentOutput::allSevenObserved),chunks,refreshes,
            aggregate?refreshes.stream().map(r->new LossSequenceModel.FinalRegiment(r.regimentId(),r.current(),r.maximum())).toList():null,coverage,missing);
    }
    public static ObjectNode encode(Result value) {
        ObjectNode out=StrictJson.object();out.put("projection_kind","conditional_associated_regular_refill_current_maximum");out.put("source_contract_game_version","1.20.0.3");
        out.put("input_basis","observed_prepared_cache_and_chunk_predicates; one_explicit_core_invocation_per_observed_persistent");
        out.put("status",value.status().name().toLowerCase(java.util.Locale.ROOT));out.put("associated_chunks_ready",value.chunksReady());out.put("associated_current_maximum_ready",value.currentMaximumReady());
        out.put("complete_persistent_requests_ready",value.completePersistentRequestsReady());out.put("actual_replenishment",false);out.putNull("actual_post_stage_current");out.put("full_regular_refill_ready",false);out.put("full_monthly_ready",false);
        ArrayNode excluded=out.putArray("excluded_stages");excluded.add("manager_roster_order_and_preparation").add("24e11b0_army_statistics").add("post_refill_supply_change_and_capacity");
        ArrayNode chunks=out.putArray("physical_chunks");for(var c:value.chunks())chunks.add(encodeChunk(c));
        ArrayNode refreshes=out.putArray("regiment_refreshes");for(var r:value.refreshes())refreshes.add(ArmySelectorCodec.refreshNode(r));
        out.putNull("conditional_regiment_strengths");if(value.strengths()!=null){ArrayNode a=out.putArray("conditional_regiment_strengths");for(var r:value.strengths()){ObjectNode n=a.addObject();n.put("army_regiment_id",r.regimentId());n.put("current_soldiers",r.current());n.put("maximum_soldiers",r.maximum());n.put("scale",1);}}
        ArrayNode coverage=out.putArray("persistent_core_coverage");for(var c:value.coverage()){ObjectNode n=coverage.addObject();n.put("persistent_regiment_id",c.persistentRegimentId());n.put("all_seven_requests_observed",c.allSevenRequestsObserved());if(c.nativeCoreAnyQualified()==null)n.putNull("native_core_any_qualified");else n.put("native_core_any_qualified",c.nativeCoreAnyQualified());ArrayNode states=n.putArray("status_by_chunk");c.statusByChunk().forEach(s->states.add(s.name().toLowerCase(java.util.Locale.ROOT)));}
        gaps(out.putArray("missing_inputs"),value.missing());return out;
    }
    public static ObjectNode encodeChunk(Chunk c){
        ObjectNode row=StrictJson.object();row.put("persistent_regiment_id",c.key().persistentRegimentId());row.put("chunk_index",c.key().chunkIndex());row.put("status",c.status().name().toLowerCase(java.util.Locale.ROOT));
        number(row,"current_soldiers_before",c.currentBefore());number(row,"same_input_q",c.sameInputQ());number(row,"current_soldiers",c.current());number(row,"maximum_soldiers",c.maximum());number(row,"state_raw",c.state());number(row,"chunk_army_regiment_id",c.associatedRegiment());number(row,"physical_add_count",c.physicalAddCount());
        if(c.status()==Status.AVAILABLE)row.put("pair_clear_reachable",false);else row.putNull("pair_clear_reachable");
        ArrayNode positions=row.putArray("data_occurrences");for(var p:c.occurrences()){ObjectNode n=positions.addObject();n.put("army_regiment_id",p.armyRegimentId());n.put("record_index",p.recordIndex());}
        strings(row,"missing_inputs",c.missing());return row;
    }
    public static void number(ObjectNode out,String key,Integer value){if(value==null)out.putNull(key);else out.put(key,value.intValue());}
    public static void strings(ObjectNode out,String key,List<String> values){ArrayNode a=out.putArray(key);values.forEach(a::add);}
    public static void gaps(ArrayNode out,List<Gap> gaps){for(var gap:gaps)switch(gap){case FieldGap g->out.add(g.input());case ChunkGap g->{ObjectNode n=out.addObject();n.put("persistent_regiment_id",g.persistentRegimentId());n.put("chunk_index",g.chunkIndex());strings(n,"inputs",g.inputs());}case RegimentGap g->{ObjectNode n=out.addObject();n.put("army_regiment_id",g.armyRegimentId());strings(n,"inputs",g.inputs());}}}
}
