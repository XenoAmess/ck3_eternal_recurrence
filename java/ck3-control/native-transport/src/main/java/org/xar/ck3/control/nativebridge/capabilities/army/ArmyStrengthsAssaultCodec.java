package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.wave3.military.landcontext.FullDataModel;
import org.xar.ck3.control.wave3.military.landcontext.LandContextCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Complete .3 current-table and loss-family boundaries. Mutable JSON ends at this codec. */
public final class ArmyStrengthsAssaultCodec {
    private ArmyStrengthsAssaultCodec() { }
    public record State(ArmyStrengths.Status status,boolean ready,String unavailableReason) { public State { Objects.requireNonNull(status); } }
    public record Resolution(State state,Long requestedFullId,Boolean registryLoaded,Long registryCapacity,Long registryIndex,
            String indexedIdentity,Long indexedFullId,String selection,Boolean usedFallback,String objectIdentity,Long selectedFullId) { }
    public record Header(State state,String entriesIdentity,Boolean entriesPresent,Integer occupiedCount,Integer mask,Integer tailDistance,
            Long loadFactorBits,Integer endSlot,Integer endMarkerControl) { }
    public record Control(long slot,Integer control,String unavailableReason) { }
    public record AllocatorWitness(State state,boolean actualReadReady,String actualIdentity,String expectedIdentity,long expectedRva,Boolean matchesExpected) { }
    public record ReleaseHeader(State state,Boolean dataPresent,String dataIdentity,Integer count,Integer capacity) { }
    public sealed interface Occurrence permits ArmyOccurrence,ArRgOccurrence {
        State state();int nativeIndex();Long rawFullId();Resolution resolution();
    }
    public record ArmyOccurrence(State state,int nativeIndex,Long rawFullId,Resolution resolution) implements Occurrence { }
    public record ArRgOccurrence(State state,int nativeIndex,Long rawFullId,Resolution resolution,Long magic,Boolean identityValid,
            String definitionIdentity,Integer definitionType,Integer current,Boolean denominatorIncluded) implements Occurrence { }
    public record Vector<T extends Occurrence>(State state,boolean referencesReady,Integer count,String dataIdentity,Boolean dataPresent,
            List<T> occurrences,int observedCount,Field<AllocatorWitness> allocator,Field<ReleaseHeader> releaseHeader) {
        public Vector { occurrences=List.copyOf(occurrences);Objects.requireNonNull(allocator);Objects.requireNonNull(releaseHeader); }
    }
    public record Group(State state,int nativeIndex,long slot,Long hash,Integer control,Long siegeFullId,Resolution siege,
            Vector<ArmyOccurrence> armies,Vector<ArRgOccurrence> arrgs,boolean denominatorReady) { }
    public record Table(State state,Boolean managerLoaded,String managerIdentity,Header header,List<Control> controls,List<Group> groups,
            int observedOccupiedCount,boolean physicalScanReady,boolean rawGroupsReady) {
        public Table { controls=List.copyOf(controls);groups=List.copyOf(groups); }
        public boolean empty(){return Objects.equals(header.occupiedCount(),0)&&groups.isEmpty();}
        public boolean physicalGroupOrderReady(){return physicalScanReady||empty()&&rawGroupsReady;}
    }
    public record RegimentCount(int nativeIndex,Long rawFullId,Resolution resolution,Boolean identityValid,Integer current,Integer maximum) { }
    public record ArmyCount(State state,int nativeIndex,Long rawFullId,Resolution resolution,Integer wholeCurrent,List<RegimentCount> regiments) {
        public ArmyCount { regiments=List.copyOf(regiments); }
    }
    public record LossGroup(State state,int nativeIndex,long slot,Integer nativeExpectedLoss,Long provinceMagic,
            ArmyStrengthsRefill.Besieging besieging,List<ArmyCount> armies,Field<ArmyStrengthsRefill.OrderedBesieging> ordered) {
        public LossGroup { armies=List.copyOf(armies);Objects.requireNonNull(ordered); }
    }
    public record Target(State state,Resolution resolution,Boolean identityValid,Integer current,Integer maximum,Boolean writerSkipped,
            FullDataModel.Snapshot data) { }
    public record LossInputs(State state,List<LossGroup> groups,List<Target> targets) {
        public LossInputs { groups=List.copyOf(groups);targets=List.copyOf(targets); }
    }
    static ObjectNode closedWords(JsonNode n,String words){return closed(n,words.split(" "));}
    static ObjectNode extended(JsonNode n,String words,String... optional){
        ObjectNode o=object(n);Set<String> expected=new HashSet<>(List.of(words.split(" ")));for(String f:optional)if(o.has(f))expected.add(f);
        require(names(o).equals(expected),"wrong, missing or invented assault fields");return o;
    }
    static String textOrNull(ObjectNode o,String f,boolean emptyAllowed){JsonNode n=get(o,f);return n.isNull()?null:emptyAllowed?text(n):nonempty(n);}
    static Boolean boolOrNull(ObjectNode o,String f){JsonNode n=get(o,f);return n.isNull()?null:bool(n);}
    static Integer intOrNull(ObjectNode o,String f){JsonNode n=get(o,f);return n.isNull()?null:i32(n);}
    static Long longOrNull(ObjectNode o,String f){JsonNode n=get(o,f);return n.isNull()?null:i64(n);}
    static Long unsignedOrNull(ObjectNode o,String f){JsonNode n=get(o,f);return n.isNull()?null:range(n,BigInteger.ZERO,BigInteger.valueOf(0xffffffffL)).longValueExact();}
    static Integer byteOrNull(ObjectNode o,String f){JsonNode n=get(o,f);return n.isNull()?null:range(n,BigInteger.ZERO,BigInteger.valueOf(255)).intValueExact();}
    static State state(ObjectNode o){return state(o,true,false);}
    static State state(ObjectNode o,boolean coupled,boolean emptyAllowed){
        ArmyStrengths.Status status=switch(text(get(o,"status"))){case "available"->ArmyStrengths.Status.AVAILABLE;case "partial"->ArmyStrengths.Status.PARTIAL;case "unavailable"->ArmyStrengths.Status.UNAVAILABLE;default->throw new IllegalArgumentException("invalid assault status");};
        boolean ready=bool(get(o,"ready"));String reason=textOrNull(o,"unavailable_reason",emptyAllowed);
        if(coupled)require(ready==(status==ArmyStrengths.Status.AVAILABLE)&&ready==(reason==null),"assault state/readiness/reason disagree");return new State(status,ready,reason);
    }
    public static Resolution decodeResolution(JsonNode n,Long requested){
        ObjectNode o=closedWords(n,"status ready unavailable_reason requested_full_id_u32 registry_loaded registry_capacity_u32 registry_index_u32 indexed_identity indexed_full_id_u32 selection used_fallback object_identity selected_full_id_u32");
        Resolution r=new Resolution(state(o),unsignedOrNull(o,"requested_full_id_u32"),boolOrNull(o,"registry_loaded"),unsignedOrNull(o,"registry_capacity_u32"),unsignedOrNull(o,"registry_index_u32"),textOrNull(o,"indexed_identity",false),unsignedOrNull(o,"indexed_full_id_u32"),textOrNull(o,"selection",false),boolOrNull(o,"used_fallback"),textOrNull(o,"object_identity",false),unsignedOrNull(o,"selected_full_id_u32"));
        require(r.selection()==null||Set.of("registry_full_id","native_fallback").contains(r.selection()),"invalid assault resolver route");
        require(Objects.equals(r.requestedFullId(),requested),"assault raw requested FullID changed");
        if(r.state().ready()){
            require(r.objectIdentity()!=null&&r.selectedFullId()!=null&&r.selection()!=null&&Objects.equals(r.usedFallback(),r.selection().equals("native_fallback")),"assault selected operand/route missing");
            require(!r.selection().equals("registry_full_id")||Objects.equals(r.selectedFullId(),requested),"assault FullID generation mismatch");
        }return r;
    }
    private static Header header(JsonNode n){
        ObjectNode o=closedWords(n,"status ready unavailable_reason entries_identity entries_present occupied_count_raw_i32 mask_raw_i32 tail_distance_raw_u8 load_factor_f32_bits_u32 end_slot_raw_i32 end_marker_control_raw_u8");
        Header h=new Header(state(o),textOrNull(o,"entries_identity",false),boolOrNull(o,"entries_present"),intOrNull(o,"occupied_count_raw_i32"),intOrNull(o,"mask_raw_i32"),byteOrNull(o,"tail_distance_raw_u8"),unsignedOrNull(o,"load_factor_f32_bits_u32"),intOrNull(o,"end_slot_raw_i32"),byteOrNull(o,"end_marker_control_raw_u8"));
        if(h.mask()!=null&&h.tailDistance()!=null&&h.endSlot()!=null)require(h.endSlot()==h.mask()+h.tailDistance()+1,"assault end must retain signed wrap");return h;
    }
    private static AllocatorWitness allocator(JsonNode n,boolean arrg){
        ObjectNode o=closedWords(n,"status ready unavailable_reason actual_read_ready actual_identity expected_identity expected_rva_u32 matches_expected");State state=state(o,false,false);
        AllocatorWitness a=new AllocatorWitness(state,bool(get(o,"actual_read_ready")),textOrNull(o,"actual_identity",false),textOrNull(o,"expected_identity",false),range(get(o,"expected_rva_u32"),BigInteger.ZERO,BigInteger.valueOf(0xffffffffL)).longValueExact(),boolOrNull(o,"matches_expected"));
        require(a.expectedRva()==(arrg?0x54deb68L:0x54e0570L),"assault allocator source RVA changed");
        boolean ready=a.actualReadReady()&&a.expectedIdentity()!=null;
        require(a.actualReadReady()==(a.actualIdentity()!=null)&&state.ready()==ready&&(state.status()==ArmyStrengths.Status.AVAILABLE)==ready,"assault allocator readiness changed");
        require(Objects.equals(a.matchesExpected(),ready?Objects.equals(a.actualIdentity(),a.expectedIdentity()):null)&&(state.unavailableReason()==null)==ready,"assault allocator identity/diagnostic changed");return a;
    }
    public static AllocatorWitness decodeAllocatorWitness(JsonNode n,boolean arrg){return n==null||n.isNull()?null:allocator(n,arrg);}
    public static ReleaseHeader decodeReleaseHeader(JsonNode n){return n==null||n.isNull()?null:releaseHeader(n);}
    private static ReleaseHeader releaseHeader(JsonNode n){
        ObjectNode o=closedWords(n,"status ready unavailable_reason data_present data_identity count_raw_i32 capacity_raw_i32");
        return new ReleaseHeader(state(o,false,true),boolOrNull(o,"data_present"),textOrNull(o,"data_identity",true),intOrNull(o,"count_raw_i32"),intOrNull(o,"capacity_raw_i32"));
    }
    private static final String OCCURRENCE="native_index raw_full_id_u32 resolution status ready unavailable_reason";
    private static ArmyOccurrence army(JsonNode n){ObjectNode o=closedWords(n,OCCURRENCE);Long raw=unsignedOrNull(o,"raw_full_id_u32");ArmyOccurrence a=new ArmyOccurrence(state(o),nonnegative(get(o,"native_index")),raw,decodeResolution(get(o,"resolution"),raw));require(!a.state().ready()||a.resolution().state().ready(),"ready Army occurrence lacks resolver");return a;}
    private static ArRgOccurrence arrg(JsonNode n){
        ObjectNode o=closedWords(n,OCCURRENCE+" magic_raw_u32 identity_valid definition_identity definition_type_raw_i32 current_raw_i32 denominator_included");Long raw=unsignedOrNull(o,"raw_full_id_u32");
        ArRgOccurrence a=new ArRgOccurrence(state(o),nonnegative(get(o,"native_index")),raw,decodeResolution(get(o,"resolution"),raw),unsignedOrNull(o,"magic_raw_u32"),boolOrNull(o,"identity_valid"),textOrNull(o,"definition_identity",false),intOrNull(o,"definition_type_raw_i32"),intOrNull(o,"current_raw_i32"),boolOrNull(o,"denominator_included"));
        if(a.magic()!=null&&a.resolution().selectedFullId()!=null)require(Objects.equals(a.identityValid(),a.magic()==0x41725267L&&a.resolution().selectedFullId()!=0xffffffffL),"ArRg identity admission changed");
        Boolean included=Boolean.FALSE.equals(a.identityValid())?Boolean.FALSE:Boolean.TRUE.equals(a.identityValid())&&a.definitionType()!=null?Boolean.valueOf(a.definitionType()<=0):null;
        require(Objects.equals(a.denominatorIncluded(),included),"assault denominator admission changed");
        require(!a.state().ready()||a.resolution().state().ready()&&included!=null&&(!included||a.current()!=null),"ready ArRg lacks demanded current");return a;
    }
    private static <T extends Occurrence> Vector<T> vector(JsonNode n,boolean arrg,Function<JsonNode,T> decoder){
        ObjectNode o=extended(n,"status ready references_ready unavailable_reason count_raw_i32 data_identity data_present occurrences observed_occurrence_count","allocator_witness","release_header_v1");
        Vector<T> v=new Vector<>(state(o),bool(get(o,"references_ready")),intOrNull(o,"count_raw_i32"),textOrNull(o,"data_identity",false),boolOrNull(o,"data_present"),array(get(o,"occurrences"),decoder),nonnegative(get(o,"observed_occurrence_count")),field(o,"allocator_witness",x->allocator(x,arrg)),field(o,"release_header_v1",ArmyStrengthsAssaultCodec::releaseHeader));
        require(v.observedCount()==v.occurrences().size(),"assault vector count changed");int previous=-1;for(T row:v.occurrences()){require(row.nativeIndex()>previous&&(v.count()==null||row.nativeIndex()<v.count()),"assault occurrence order changed");previous=row.nativeIndex();}
        if(v.referencesReady()){
            require(v.count()!=null&&v.count()>=0&&v.count()==v.occurrences().size(),"assault complete vector lacks original count");for(int i=0;i<v.occurrences().size();i++)require(v.occurrences().get(i).nativeIndex()==i&&v.occurrences().get(i).rawFullId()!=null,"assault complete vector lacks ordered raw references");
        }require(!v.state().ready()||v.referencesReady()&&v.occurrences().stream().allMatch(x->x.state().ready()),"assault complete vector lacks demanded values");return v;
    }
    private static Group group(JsonNode n){
        ObjectNode o=closedWords(n,"native_index physical_slot_i64 status ready unavailable_reason hash_raw_u32 control_raw_u8 siege_full_id_u32 siege_resolution armies arrgs denominator_ready");Long raw=unsignedOrNull(o,"siege_full_id_u32");long slot=i64(get(o,"physical_slot_i64"));require(slot>=0,"negative physical group slot");
        Group g=new Group(state(o),nonnegative(get(o,"native_index")),slot,unsignedOrNull(o,"hash_raw_u32"),byteOrNull(o,"control_raw_u8"),raw,decodeResolution(get(o,"siege_resolution"),raw),vector(get(o,"armies"),false,ArmyStrengthsAssaultCodec::army),vector(get(o,"arrgs"),true,ArmyStrengthsAssaultCodec::arrg),bool(get(o,"denominator_ready")));
        require(!Objects.equals(g.control(),0),"assault group cannot occupy empty control");require(g.denominatorReady()==(g.arrgs().referencesReady()&&g.arrgs().occurrences().stream().allMatch(x->x.state().ready())),"assault denominator readiness changed");
        require(!g.state().ready()||raw!=null&&g.hash()!=null&&g.control()!=null&&g.siege().state().ready()&&g.armies().state().ready()&&g.arrgs().state().ready(),"assault ready group lacks actual inputs");return g;
    }
    public static Table decodeTable(JsonNode n){
        if(n==null||n.isNull())return null;
        ObjectNode o=closedWords(n,"schema_version source stage status ready unavailable_reason manager_loaded manager_identity header physical_controls groups observed_occupied_group_count physical_scan_ready raw_groups_ready");
        require(i32(get(o,"schema_version"))==1,"assault table schema changed");equal(get(o,"source"),"native_current_daily_assault_table");equal(get(o,"stage"),"observed_current_daily_assault_table");
        List<Control> controls=array(get(o,"physical_controls"),raw->{ObjectNode c=closedWords(raw,"physical_slot_i64 control_raw_u8 unavailable_reason");long slot=i64(get(c,"physical_slot_i64"));require(slot>=0,"negative assault control slot");return new Control(slot,byteOrNull(c,"control_raw_u8"),textOrNull(c,"unavailable_reason",false));});
        Table t=new Table(state(o),boolOrNull(o,"manager_loaded"),textOrNull(o,"manager_identity",false),header(get(o,"header")),controls,array(get(o,"groups"),ArmyStrengthsAssaultCodec::group),nonnegative(get(o,"observed_occupied_group_count")),bool(get(o,"physical_scan_ready")),bool(get(o,"raw_groups_ready")));
        long previous=-1;for(Control c:t.controls()){require(c.slot()>previous,"assault physical controls reordered");previous=c.slot();}
        previous=-1;int controlIndex=0;for(int i=0;i<t.groups().size();i++){
            Group g=t.groups().get(i);require(g.nativeIndex()==i&&g.slot()>previous&&(t.header().endSlot()==null||g.slot()<t.header().endSlot()),"assault physical groups reordered");previous=g.slot();
            while(controlIndex<t.controls().size()&&t.controls().get(controlIndex).slot()<g.slot())controlIndex++;
            if(controlIndex<t.controls().size()&&t.controls().get(controlIndex).slot()==g.slot())require(Objects.equals(t.controls().get(controlIndex).control(),g.control()),"assault occupied control changed");
        }
        require(t.groups().size()==t.observedOccupiedCount(),"assault group observed count changed");
        if(t.physicalScanReady()){
            require(t.header().endSlot()!=null&&t.header().endSlot()>=0&&t.controls().size()==t.header().endSlot(),"assault physical census incomplete");
            int groupIndex=0;for(int i=0;i<t.controls().size();i++){Control c=t.controls().get(i);require(c.slot()==i&&c.control()!=null,"assault physical control missing");if(c.control()!=0){require(groupIndex<t.groups().size()&&t.groups().get(groupIndex).slot()==c.slot(),"assault occupied group missing");groupIndex++;}}
            require(groupIndex==t.groups().size()&&t.header().endMarkerControl()!=null&&t.header().endMarkerControl()!=0,"assault end marker missing");
        }
        require(!t.rawGroupsReady()||t.empty()||t.physicalScanReady()&&t.groups().stream().allMatch(g->g.hash()!=null&&g.siegeFullId()!=null&&g.armies().referencesReady()&&g.arrgs().referencesReady()),"assault raw group claim lacks bytes");
        require(!t.state().ready()||Boolean.TRUE.equals(t.managerLoaded())&&t.rawGroupsReady()&&(t.empty()||t.groups().stream().allMatch(g->g.state().ready())),"assault table ready claim lacks actual inputs");return t;
    }
    public static LossInputs decodeLoss(JsonNode n){
        if(n==null||n.isNull())return null;ObjectNode o=closedWords(n,"status ready unavailable_reason schema_version source stage groups target_regiments");
        require(i32(get(o,"schema_version"))==1,"assault loss schema changed");equal(get(o,"source"),"native_current_daily_assault_loss_inputs");equal(get(o,"stage"),"observed_current_daily_assault_table");
        return new LossInputs(state(o),array(get(o,"groups"),ArmyStrengthsAssaultCodec::lossGroup),array(get(o,"target_regiments"),ArmyStrengthsAssaultCodec::target));
    }
    public static LossGroup lossGroup(JsonNode n){
        ObjectNode o=extended(n,"status ready unavailable_reason native_index physical_slot_i64 native_current_expected_loss province_magic_raw_u32 besieging_inputs_v1 army_counts","ordered_besieging_refill_inputs_v1");
        JsonNode b=get(o,"besieging_inputs_v1");ArmyStrengthsRefill.Besieging family=b.isNull()?null:ArmyStrengthsRefill.decodeBesieging(b);
        Field<ArmyStrengthsRefill.OrderedBesieging> ordered=field(o,"ordered_besieging_refill_inputs_v1",ArmyStrengthsRefill::decodeOrderedBesieging);
        if(ordered instanceof Present<ArmyStrengthsRefill.OrderedBesieging> p)require(family!=null&&family.provinceId()==p.value().provinceId(),"assault ordered Province scope changed");
        return new LossGroup(state(o),nonnegative(get(o,"native_index")),i64(get(o,"physical_slot_i64")),intOrNull(o,"native_current_expected_loss"),unsignedOrNull(o,"province_magic_raw_u32"),family,array(get(o,"army_counts"),ArmyStrengthsAssaultCodec::armyCount),ordered);
    }
    private static ArmyCount armyCount(JsonNode n){ObjectNode o=closedWords(n,"status ready unavailable_reason native_index raw_full_id_u32 resolution native_whole_current_soldiers regiments");Long raw=unsignedOrNull(o,"raw_full_id_u32");return new ArmyCount(state(o),nonnegative(get(o,"native_index")),raw,decodeResolution(get(o,"resolution"),raw),intOrNull(o,"native_whole_current_soldiers"),array(get(o,"regiments"),ArmyStrengthsAssaultCodec::regimentCount));}
    private static RegimentCount regimentCount(JsonNode n){ObjectNode o=closedWords(n,"native_index raw_full_id_u32 resolution identity_valid current_soldiers maximum_soldiers");Long raw=unsignedOrNull(o,"raw_full_id_u32");return new RegimentCount(nonnegative(get(o,"native_index")),raw,decodeResolution(get(o,"resolution"),raw),boolOrNull(o,"identity_valid"),intOrNull(o,"current_soldiers"),intOrNull(o,"maximum_soldiers"));}
    private static Target target(JsonNode n){ObjectNode o=closedWords(n,"status ready unavailable_reason resolution identity_valid current_soldiers maximum_soldiers native_loss_writer_skipped replenishment_records_v1");ObjectNode r=object(get(o,"resolution"));JsonNode d=get(o,"replenishment_records_v1");return new Target(state(o),decodeResolution(r,unsignedOrNull(r,"requested_full_id_u32")),boolOrNull(o,"identity_valid"),intOrNull(o,"current_soldiers"),intOrNull(o,"maximum_soldiers"),boolOrNull(o,"native_loss_writer_skipped"),d.isNull()?null:LandContextCodec.decodeData(d));}
    static ObjectNode emitState(State s){return empty().put("status",s.status().name().toLowerCase(java.util.Locale.ROOT)).put("ready",s.ready()).put("unavailable_reason",s.unavailableReason());}
    static void put(ObjectNode n,String key,Number v){if(v==null)n.putNull(key);else n.put(key,v.longValue());}
    static void put(ObjectNode n,String key,Boolean v){if(v==null)n.putNull(key);else n.put(key,v);}
    static <T> void emitField(ObjectNode n,String key,Field<T> f,Function<T,JsonNode> encoder){if(f instanceof Present<T> p)n.set(key,encoder.apply(p.value()));else if(f instanceof NullValue<T>)n.putNull(key);}
    public static ObjectNode encodeResolution(Resolution r){ObjectNode n=emitState(r.state());put(n,"requested_full_id_u32",r.requestedFullId());put(n,"registry_loaded",r.registryLoaded());put(n,"registry_capacity_u32",r.registryCapacity());put(n,"registry_index_u32",r.registryIndex());n.put("indexed_identity",r.indexedIdentity());put(n,"indexed_full_id_u32",r.indexedFullId());n.put("selection",r.selection());put(n,"used_fallback",r.usedFallback());n.put("object_identity",r.objectIdentity());put(n,"selected_full_id_u32",r.selectedFullId());return n;}
    public static ObjectNode encodeHeader(Header h){ObjectNode n=emitState(h.state()).put("entries_identity",h.entriesIdentity());put(n,"entries_present",h.entriesPresent());put(n,"occupied_count_raw_i32",h.occupiedCount());put(n,"mask_raw_i32",h.mask());put(n,"tail_distance_raw_u8",h.tailDistance());put(n,"load_factor_f32_bits_u32",h.loadFactorBits());put(n,"end_slot_raw_i32",h.endSlot());put(n,"end_marker_control_raw_u8",h.endMarkerControl());return n;}
    public static ObjectNode encodeAllocator(AllocatorWitness a){if(a==null)return null;ObjectNode n=emitState(a.state()).put("actual_read_ready",a.actualReadReady()).put("actual_identity",a.actualIdentity()).put("expected_identity",a.expectedIdentity()).put("expected_rva_u32",a.expectedRva());put(n,"matches_expected",a.matchesExpected());return n;}
    public static ObjectNode encodeReleaseHeader(ReleaseHeader h){if(h==null)return null;ObjectNode n=emitState(h.state()).put("data_identity",h.dataIdentity());put(n,"data_present",h.dataPresent());put(n,"count_raw_i32",h.count());put(n,"capacity_raw_i32",h.capacity());return n;}
    static ObjectNode encodeOccurrence(Occurrence o){ObjectNode n=emitState(o.state()).put("native_index",o.nativeIndex());put(n,"raw_full_id_u32",o.rawFullId());n.set("resolution",encodeResolution(o.resolution()));if(o instanceof ArRgOccurrence a){put(n,"magic_raw_u32",a.magic());put(n,"identity_valid",a.identityValid());n.put("definition_identity",a.definitionIdentity());put(n,"definition_type_raw_i32",a.definitionType());put(n,"current_raw_i32",a.current());put(n,"denominator_included",a.denominatorIncluded());}return n;}
    static ObjectNode encodeVector(Vector<?> v){ObjectNode n=emitState(v.state()).put("references_ready",v.referencesReady()).put("data_identity",v.dataIdentity()).put("observed_occurrence_count",v.observedCount());put(n,"count_raw_i32",v.count());put(n,"data_present",v.dataPresent());ArrayNode rows=n.putArray("occurrences");v.occurrences().forEach(o->rows.add(encodeOccurrence(o)));emitField(n,"allocator_witness",v.allocator(),ArmyStrengthsAssaultCodec::encodeAllocator);emitField(n,"release_header_v1",v.releaseHeader(),ArmyStrengthsAssaultCodec::encodeReleaseHeader);return n;}
    public static ObjectNode encodeGroup(Group g){ObjectNode n=emitState(g.state()).put("native_index",g.nativeIndex()).put("physical_slot_i64",g.slot()).put("denominator_ready",g.denominatorReady());put(n,"hash_raw_u32",g.hash());put(n,"control_raw_u8",g.control());put(n,"siege_full_id_u32",g.siegeFullId());n.set("siege_resolution",encodeResolution(g.siege()));n.set("armies",encodeVector(g.armies()));n.set("arrgs",encodeVector(g.arrgs()));return n;}
    public static ObjectNode encodeTable(Table t){if(t==null)return null;ObjectNode n=emitState(t.state()).put("schema_version",1).put("source","native_current_daily_assault_table").put("stage","observed_current_daily_assault_table").put("manager_identity",t.managerIdentity()).put("observed_occupied_group_count",t.observedOccupiedCount()).put("physical_scan_ready",t.physicalScanReady()).put("raw_groups_ready",t.rawGroupsReady());put(n,"manager_loaded",t.managerLoaded());n.set("header",encodeHeader(t.header()));ArrayNode controls=n.putArray("physical_controls");for(Control c:t.controls()){ObjectNode row=controls.addObject().put("physical_slot_i64",c.slot()).put("unavailable_reason",c.unavailableReason());put(row,"control_raw_u8",c.control());}ArrayNode groups=n.putArray("groups");t.groups().forEach(g->groups.add(encodeGroup(g)));return n;}
    static ObjectNode encodeRegimentCount(RegimentCount r){ObjectNode n=empty().put("native_index",r.nativeIndex());put(n,"raw_full_id_u32",r.rawFullId());n.set("resolution",encodeResolution(r.resolution()));put(n,"identity_valid",r.identityValid());put(n,"current_soldiers",r.current());put(n,"maximum_soldiers",r.maximum());return n;}
    static ObjectNode encodeArmyCount(ArmyCount a){ObjectNode n=emitState(a.state()).put("native_index",a.nativeIndex());put(n,"raw_full_id_u32",a.rawFullId());n.set("resolution",encodeResolution(a.resolution()));put(n,"native_whole_current_soldiers",a.wholeCurrent());ArrayNode regiments=n.putArray("regiments");a.regiments().forEach(r->regiments.add(encodeRegimentCount(r)));return n;}
    public static ObjectNode encodeLossGroup(LossGroup g){ObjectNode n=emitState(g.state()).put("native_index",g.nativeIndex()).put("physical_slot_i64",g.slot());put(n,"native_current_expected_loss",g.nativeExpectedLoss());put(n,"province_magic_raw_u32",g.provinceMagic());n.set("besieging_inputs_v1",g.besieging()==null?NullNode.getInstance():ArmyStrengthsRefill.encodeBesieging(g.besieging()));ArrayNode armies=n.putArray("army_counts");g.armies().forEach(a->armies.add(encodeArmyCount(a)));emitField(n,"ordered_besieging_refill_inputs_v1",g.ordered(),ArmyStrengthsRefill::encodeOrderedBesieging);return n;}
    static ObjectNode encodeTarget(Target t){ObjectNode n=emitState(t.state());n.set("resolution",encodeResolution(t.resolution()));put(n,"identity_valid",t.identityValid());put(n,"current_soldiers",t.current());put(n,"maximum_soldiers",t.maximum());put(n,"native_loss_writer_skipped",t.writerSkipped());n.set("replenishment_records_v1",t.data()==null?NullNode.getInstance():LandContextCodec.encodeData(t.data()));return n;}
    public static ObjectNode encodeLoss(LossInputs l){if(l==null)return null;ObjectNode n=emitState(l.state()).put("schema_version",1).put("source","native_current_daily_assault_loss_inputs").put("stage","observed_current_daily_assault_table");ArrayNode groups=n.putArray("groups");l.groups().forEach(g->groups.add(encodeLossGroup(g)));ArrayNode targets=n.putArray("target_regiments");l.targets().forEach(t->targets.add(encodeTarget(t)));return n;}
}
