package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.landstock.LandStockModel;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Source-bound current assault calculations. No native stage is executed by this bundle. */
public final class ArmyStrengthsAssault {
    private static final long Q=100000L;
    private ArmyStrengthsAssault() { }
    public static void install(ArmyStrengthsFamilies.Registry registry,ArmyStrengthsPipeline pipeline,org.xar.ck3.control.contracts.ExactRef actualJavaBundleSource){ArmyStrengthsAssaultInstaller.install(registry,pipeline,actualJavaBundleSource);}
    /** Full original current-table guard, including optional allocator/release witnesses. */
    public static ObjectNode normalizeTable(JsonNode value){return ArmyStrengthsAssaultCodec.encodeTable(ArmyStrengthsAssaultCodec.decodeTable(value));}
    /** Boundary presentation paired with the actual immutable calculation, never an uncomputed JSON wrapper. */
    public static final class EligibleContributors {
        private final ArmyStrengthsAssaultEligible.Result value;private final RawJson encoded;
        private EligibleContributors(ArmyStrengthsAssaultEligible.Result value,ObjectNode encoded){this.value=value;this.encoded=new RawJson(ArmyJson.bytes(encoded));}
        public ArmyStrengthsAssaultEligible.Result value(){return value;}
        public boolean ready(){return value.ready();}
        public boolean conditionalBesiegingStrengthReady(){return value.bReady();}
        public Integer conditionalBesiegingStrength(){return value.b();}
        public boolean expectedLossReady(){return value.expectedReady();}
        public Integer expectedLoss(){return value.expected();}
        public ObjectNode besiegingInputs(){JsonNode node=toJson().get("besieging_inputs_v1");return node.isNull()?null:ArmyJson.object(node);}
        public ObjectNode toJson(){return ArmyJson.object(ArmyStrengthsCodec.parseValue(encoded));}
    }
    public static final class LossProjection {
        private final ArmyStrengthsAssaultLoss.Result value;
        private LossProjection(ArmyStrengthsAssaultLoss.Result value){this.value=value;}
        public ArmyStrengthsAssaultLoss.Result value(){return value;}
        public boolean sequentialNumericReady(){return value.sequentialReady();}
        public boolean queueRequestsReady(){return value.queueRequestsReady();}
        public int completedGroupCount(){return value.completed();}
        public ObjectNode toJson(){return ArmyStrengthsAssaultLoss.encode(value);}
    }
    public static LossProjection loss(ObjectNode normalizedArmy){
        int army=ArmyJson.i32(ArmyJson.get(normalizedArmy,"army_id"));
        return new LossProjection(ArmyStrengthsAssaultLoss.project(army,ArmyStrengthsAssaultCodec.decodeTable(normalizedArmy.get("current_daily_assault_table_v1")),ArmyStrengthsAssaultCodec.decodeLoss(normalizedArmy.get("current_daily_assault_loss_inputs_v1"))));
    }
    public static ObjectNode queue(ObjectNode army,ObjectNode numeric){return ArmyStrengthsAssaultCurrent.encodeQueue(ArmyStrengthsAssaultCurrent.queuePrefix(ArmyJson.i32(ArmyJson.get(army,"army_id")),ArmyStrengthsAssaultBoundary.pending(army),ArmyStrengthsAssaultBoundary.numeric(numeric)));}
    public static ObjectNode normalRelease(ObjectNode army,ObjectNode queue){return ArmyStrengthsAssaultCurrent.encodeRelease(ArmyStrengthsAssaultCurrent.release(ArmyJson.i32(ArmyJson.get(army,"army_id")),ArmyStrengthsAssaultCodec.decodeTable(army.get("current_daily_assault_table_v1")),ArmyStrengthsAssaultBoundary.queue(queue)));}
    /** Original consumer codec entrance. Extra physical provenance is retained only in the encoded presentation. */
    public static EligibleContributors eligible(JsonNode group,JsonNode physical,JsonNode refresh){
        var input=ArmyStrengthsAssaultCodec.lossGroup(group);List<ArmyStrengthsAssaultEligible.FinalPhysical> finalPhysical=null;
        if(physical!=null&&!physical.isNull())finalPhysical=ArmyJson.array(physical,node->{ObjectNode row=ArmyJson.object(node);int id=ArmyJson.i32(ArmyJson.get(row,"persistent_regiment_id")),index=ArmyJson.i32(ArmyJson.get(row,"chunk_index"));boolean available=row.has("status")&&row.get("status").isTextual()&&row.get("status").textValue().equals("available");Integer current=available?ArmyJson.i32(ArmyJson.get(row,"current_soldiers")):null,maximum=available?ArmyJson.i32(ArmyJson.get(row,"maximum_soldiers")):null;Field<Integer> state=!available?new NullValue<>():ArmyJson.field(row,"state_raw",ArmyJson::i32);return new ArmyStrengthsAssaultEligible.FinalPhysical(id,index,available,current,maximum,state);});
        var selection=refresh==null||refresh.isNull()?null:ArmyStrengthsRefill.decodeOrderedBesieging(refresh);var result=ArmyStrengthsAssaultEligible.project(input,finalPhysical,selection);ObjectNode encoded=ArmyStrengthsAssaultEligible.encode(result);
        // The Python physical overlay copies provenance fields without interpreting them. Keep that behavior at the codec edge.
        if(physical!=null&&physical.isArray()&&!result.physical().isEmpty()){
            Map<ArmyStrengthsAssaultLoss.PhysicalKey,ObjectNode> supplied=new LinkedHashMap<>();Map<ArmyStrengthsAssaultLoss.PhysicalKey,ObjectNode> computed=new LinkedHashMap<>();
            for(JsonNode row:encoded.get("conditional_physical_chunks")){var key=new ArmyStrengthsAssaultLoss.PhysicalKey(row.get("persistent_regiment_id").intValue(),row.get("chunk_index").intValue());computed.put(key,ArmyJson.object(row));}
            for(JsonNode raw:physical){ObjectNode copy=ArmyJson.object(raw).deepCopy();var key=new ArmyStrengthsAssaultLoss.PhysicalKey(copy.get("persistent_regiment_id").intValue(),copy.get("chunk_index").intValue());ObjectNode scalar=computed.get(key);if(scalar==null)continue;for(String field:List.of("status","current_soldiers","maximum_soldiers"))copy.set(field,scalar.get(field));if(scalar.has("state_raw"))copy.set("state_raw",scalar.get("state_raw"));require(!supplied.containsKey(key)||supplied.get(key).equals(copy),"conflicting duplicate final physical provenance");supplied.put(key,copy);}
            ArrayNode rows=encoded.putArray("conditional_physical_chunks");for(var entry:computed.entrySet())rows.add(supplied.getOrDefault(entry.getKey(),entry.getValue()));
        }
        return new EligibleContributors(result,encoded);
    }
    public static List<ArmyStrengthsPublicNumbers.Rule> expectedLossPublicNumberRules(String prefix){
        Objects.requireNonNull(prefix);if(!prefix.isEmpty()&&!prefix.startsWith("/"))throw new IllegalArgumentException("canonical JSON path prefix required");
        return List.of("casualty_percentage_index","casualty_percentage_raw","wrapped_product_raw","percentage_divisor_raw","divided_raw").stream()
            .map(field->new ArmyStrengthsPublicNumbers.Rule(prefix+"/"+field,ArmyStrengthsPublicNumbers.Domain.SIGNED_64)).toList();
    }
    /** Prefix is the family object itself, not a native/public per-Army wrapper. */
    public static List<ArmyStrengthsPublicNumbers.Rule> familyPublicNumberRules(ArmyStrengthsFamilies.Key key,String prefix){return ArmyStrengthsAssaultInstaller.familyRules(key).stream().map(rule->rule.prefixed(prefix)).toList();}
    /** Prefix is the single projection object; array/per-Army wrapper paths are removed exactly. */
    public static List<ArmyStrengthsPublicNumbers.Rule> projectionPublicNumberRules(ArmyStrengthsPipeline.Stage stage,String prefix){
        String base=stage==ArmyStrengthsPipeline.Stage.CURRENT_DAILY_ASSAULT_GROUP_INPUTS_V1||stage==ArmyStrengthsPipeline.Stage.CURRENT_DAILY_ASSAULT_PLACEMENT_INPUTS_V1?"/*":"/*/projection";
        return ArmyStrengthsAssaultInstaller.stageRules(stage).stream().map(rule->{require(rule.exactPath().startsWith(base+"/"),"foreign stage path");return new ArmyStrengthsPublicNumbers.Rule(rule.exactPath().substring(base.length()),rule.domain(),rule.traversal()).prefixed(prefix);}).toList();
    }
    public static List<ArmyStrengthsPublicNumbers.Rule> eligiblePublicNumberRules(String prefix){
        String base="/*/projection/group_budget_outputs/*";return ArmyStrengthsAssaultInstaller.stageRules(ArmyStrengthsPipeline.Stage.SAME_QUERY_CONDITIONAL_ASSAULT_GROUP_CONTRIBUTORS_12004).stream().filter(rule->rule.exactPath().startsWith(base+"/")).map(rule->new ArmyStrengthsPublicNumbers.Rule(rule.exactPath().substring(base.length()),rule.domain(),rule.traversal()).prefixed(prefix)).toList();
    }

    /** Only the exact scalar facts demanded by held25205C0, after full family validation. */
    public record ExpectedLossInput(int provinceId,ArmyStrengths.Status status,Boolean hasActiveSiege,
            Integer breachLevelRaw,Integer casualtyPercentageCount,Long casualtyPercentageRaw,Integer conditionalBesiegingStrength) {
        public ExpectedLossInput { Objects.requireNonNull(status); }
    }
    public record ExpectedLoss(boolean ready,Integer conditionalExpectedLoss,String zeroBasis,Long casualtyPercentageIndex,
            Long casualtyPercentageRaw,Long wrappedProductRaw,Long dividedRaw,LandStockModel.DivisionPath divisionPath,
            List<String> missingInputs) {
        public ExpectedLoss { missingInputs=List.copyOf(missingInputs); }
        public ObjectNode toJson(){return encodeExpectedLoss(this);}
    }
    public static ExpectedLoss expectedLoss(ExpectedLossInput input) {
        Objects.requireNonNull(input);
        if(input.provinceId()==-1&&input.status()!=ArmyStrengths.Status.UNAVAILABLE)return zeroLoss("no_valid_Province",null);
        Integer b=input.conditionalBesiegingStrength();
        if(b!=null&&b<=0)return zeroLoss("nonpositive_conditional_B",null);
        if(Boolean.FALSE.equals(input.hasActiveSiege()))return zeroLoss("no_active_Siege",null);
        Long index=null;List<String> missing=new ArrayList<>();
        if(input.breachLevelRaw()!=null&&input.casualtyPercentageCount()!=null){index=(long)input.breachLevelRaw()-1;if(index<0||index>=input.casualtyPercentageCount())return zeroLoss("breach_index_outside_loaded_table",index);}
        else missing.add("captured_breach_and_casualty_table_count");
        if(!Boolean.TRUE.equals(input.hasActiveSiege()))missing.add("captured_active_Siege");
        if(b==null)missing.add("conditional_besieging_strength");
        if(input.casualtyPercentageRaw()==null)missing.add("captured_indexed_casualty_percentage_raw");
        if(!missing.isEmpty())return new ExpectedLoss(false,null,null,index,null,null,null,null,missing);
        long product=(long)b*input.casualtyPercentageRaw();
        LandStockModel.DivisionResult divided=LandStockPolicy.nativeFixedDivide(product,100*Q);
        long raw=divided.value().longValueExact();
        return new ExpectedLoss(true,(int)(raw/Q),null,index,input.casualtyPercentageRaw(),product,raw,divided.path(),List.of());
    }
    private static ExpectedLoss zeroLoss(String basis,Long index){return new ExpectedLoss(true,0,basis,index,null,null,null,null,List.of());}
    /** Explicit JSON representation; raw signed64 fields are converted only by the public protocol encoder. */
    public static ObjectNode encodeExpectedLoss(ExpectedLoss value) {
        ObjectNode n=ArmyJson.empty();n.put("ready",value.ready());put(n,"conditional_expected_loss",value.conditionalExpectedLoss());n.put("zero_basis",value.zeroBasis());put(n,"casualty_percentage_index",value.casualtyPercentageIndex());put(n,"casualty_percentage_raw",value.casualtyPercentageRaw());put(n,"wrapped_product_raw",value.wrappedProductRaw());n.put("percentage_divisor_raw",100*Q);put(n,"divided_raw",value.dividedRaw());n.put("division_path",value.divisionPath()==null?null:value.divisionPath().name().toLowerCase(Locale.ROOT));var missing=n.putArray("missing_inputs");value.missingInputs().forEach(missing::add);return n;
    }
    private static void put(ObjectNode n,String key,Number value){if(value==null)n.putNull(key);else n.put(key,value.longValue());}
}
