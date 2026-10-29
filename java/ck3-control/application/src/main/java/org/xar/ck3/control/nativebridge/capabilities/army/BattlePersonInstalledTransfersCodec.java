package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.military.combatwire.KnightTransferLineageCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Same-batch retained transfer DATA. No retained record grants a new preparation, Entry or mutation. */
public final class BattlePersonInstalledTransfersCodec {
    public static final String SCHEMA="xar.ck3.person-installed-transfer-capture-12004-v1";
    public static final String EXE_SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Set<String> FIELDS=Set.of("schema","build_version","executable_sha256","historical_capture","configured","installed","install_failure_flags","request_filtered",
            "snapshot_revision","observed_date_raw","requested_receiver_count","unresolved_receiver_count","latest_record_sequence","overwritten_records","records");
    private static final List<String> SNAP_PTRS=List.of("model_a_owner_identity","model_b_owner_identity","observed_owner_identity","carrier_identity","installed_model_identity","installed_model_owner_identity","matching_installed_inline_context_identity");
    private static final Set<String> PHYSICAL_PTRS=Set.of("clock_identity","model_identity","original_return_rva","data_identity","storage_identity","block_identity","allocator_receiver_identity","allocator_identity","allocator_dispatch_vtable_identity");
    private BattlePersonInstalledTransfersCodec() { }
    public record Receiver(BigInteger identity,long characterId) {
        public Receiver { Objects.requireNonNull(identity);require(identity.signum()>0 && identity.bitLength()<=64,"receiver","nonzero uint64 pointer required");require(characterId>=0 && characterId<=0xffff_ffffL,"receiver","full uint32 character required"); }
    }
    public static final class TransferRecord {
        private final BigInteger sequence;
        private final boolean offlineFixture;
        private final Receiver beforeOwner;
        private final byte[] normalized;
        private TransferRecord(ObjectNode value,ObjectNode nativeWire,Receiver owner) {
            sequence=integer(value,"record_sequence");offlineFixture=value.get("offline_fixture").booleanValue();beforeOwner=owner;
            // The shared leaf's internal numeric pointer projection is not the native JSON wire.
            // Preserve the completely validated original JSON domain for persistence round trips.
            normalized=ArmyJson.bytes(nativeWire);
        }
        public BigInteger recordSequence() { return sequence; }
        public boolean offlineFixture() { return offlineFixture; }
        public Receiver beforeOwner() { return beforeOwner; }
        public ObjectNode toJson() { return ArmyJson.parse(normalized); }
    }
    public static final class Query {
        private final boolean configured,installed;
        private final long installFailureFlags;
        private final BigInteger revision,latest,overwritten;
        private final int dateRaw,requested,unresolved;
        private final List<TransferRecord> records;
        private final byte[] normalized;
        private Query(ObjectNode value,List<TransferRecord> records) {
            configured=value.get("configured").booleanValue();installed=value.get("installed").booleanValue();installFailureFlags=integer(value,"install_failure_flags").longValueExact();
            revision=integer(value,"snapshot_revision");dateRaw=integer(value,"observed_date_raw").intValueExact();requested=integer(value,"requested_receiver_count").intValueExact();unresolved=integer(value,"unresolved_receiver_count").intValueExact();
            latest=integer(value,"latest_record_sequence");overwritten=integer(value,"overwritten_records");this.records=List.copyOf(records);normalized=ArmyJson.bytes(value);
        }
        public boolean configured() { return configured; }
        public boolean installed() { return installed; }
        public long installFailureFlags() { return installFailureFlags; }
        public BigInteger nativeRevision() { return revision; }
        public int observedDateRaw() { return dateRaw; }
        public int requestedReceiverCount() { return requested; }
        public int unresolvedReceiverCount() { return unresolved; }
        public BigInteger latestRecordSequence() { return latest; }
        public BigInteger overwrittenRecords() { return overwritten; }
        public List<TransferRecord> records() { return records; }
        public List<TransferRecord> forReceiver(Receiver owner) { return records.stream().filter(record->record.beforeOwner().equals(Objects.requireNonNull(owner))).toList(); }
        public ObjectNode toJson() { return ArmyJson.parse(normalized); }
        public boolean grantsEntryOrMutationAuthority() { return false; }
    }
    public static ObjectNode normalize(JsonNode value,String field,BattlePersonSixStageCaptureCodec.NormalizedQuery owners,BigInteger expectedRevision,int expectedDateRaw) {
        return decode(value,field,owners,expectedRevision,expectedDateRaw).toJson();
    }
    public static Query decode(JsonNode value,String field,BattlePersonSixStageCaptureCodec.NormalizedQuery owners,BigInteger expectedRevision,int expectedDateRaw) {
        Objects.requireNonNull(owners);Objects.requireNonNull(expectedRevision);
        require(expectedRevision.signum()>=0 && expectedRevision.bitLength()<=64 && expectedRevision.equals(owners.nativeRevision()) && expectedDateRaw==owners.observedDateRaw(),field,"outer and actual same-batch capture frame differ");
        ObjectNode raw=exact(value,field,FIELDS),out=object();
        for(String key:List.of("schema","build_version","executable_sha256"))out.set(key,text(raw.get(key),field+"."+key,false,true));
        require(SCHEMA.equals(string(out.get("schema"))) && "1.20.0.4".equals(string(out.get("build_version"))) && EXE_SHA.equalsIgnoreCase(string(out.get("executable_sha256"))),field,"exact installed transfer source/build required");
        for(String key:List.of("historical_capture","configured","installed","request_filtered"))out.set(key,bool(raw.get(key),field+"."+key,false));
        require(trueValue(out,"historical_capture") && trueValue(out,"request_filtered"),field,"outer sidecar must retain historical same-request filtering");
        out.set("install_failure_flags",number(raw.get("install_failure_flags"),field+".install_failure_flags",32,true,false));
        for(String key:List.of("snapshot_revision","requested_receiver_count","unresolved_receiver_count","latest_record_sequence","overwritten_records"))out.set(key,number(raw.get(key),field+"."+key,64,true,false));
        out.set("observed_date_raw",number(raw.get("observed_date_raw"),field+".observed_date_raw",64,false,false));
        require(expectedRevision.equals(integer(out,"snapshot_revision")) && BigInteger.valueOf(expectedDateRaw).equals(integer(out,"observed_date_raw")),field,"installed transfer sidecar crossed native revision/date");
        List<BattlePersonSixStageCaptureCodec.CaptureOwner> batch=owners.owners();Set<Receiver> resolved=new HashSet<>();int unresolved=0;
        for(var owner:batch) {
            Long id=owner.characterId();BigInteger pointer=pointer(owner.characterIdentity(),field+".owners.character_identity",true);
            if(pointer==null || pointer.signum()==0 || id==null)unresolved++;
            else resolved.add(new Receiver(pointer,id));
        }
        require(BigInteger.valueOf(batch.size()).equals(integer(out,"requested_receiver_count")) && BigInteger.valueOf(unresolved).equals(integer(out,"unresolved_receiver_count")),field,"receiver counts differ from actual six-stage batch; ID zero is engaged");
        BigInteger latest=integer(out,"latest_record_sequence"),overwritten=integer(out,"overwritten_records"),capacity=BigInteger.valueOf(128);
        require(overwritten.equals(latest.subtract(capacity).max(BigInteger.ZERO)),field,"native retained ring overwrite count differs");
        JsonNode wireRecords=raw.get("records");require(wireRecords!=null && wireRecords.isArray() && wireRecords.size()<=128,field+".records","native retained capacity exceeded or array missing");
        var normalizedRecords=list();List<TransferRecord> records=new ArrayList<>();BigInteger prior=BigInteger.ZERO,lower=latest.subtract(capacity).max(BigInteger.ZERO);
        for(int index=0;index<wireRecords.size();index++) {
            String name=field+".records["+index+"]";ObjectNode wire=exact(wireRecords.get(index),name,Set.of("record_sequence","offline_fixture","stage","physical_postimage"));
            BigInteger sequence=integer(number(wire.get("record_sequence"),name+".record_sequence",64,true,false));
            require(sequence.compareTo(prior)>0 && sequence.compareTo(lower)>0 && sequence.compareTo(latest)<=0,name,"record order is outside actual retained native ring");prior=sequence;
            nativeTokens(wire,name);
            ObjectNode normalized=KnightTransferLineageCodec.normalizeRecord(wire);
            physicalWireTokens(wire.get("physical_postimage"),name+".physical_postimage");
            ObjectNode stage=(ObjectNode)normalized.get("stage");require(trueValue(stage,"observed") && trueValue(stage,"original_returned"),name,"production retention requires observed original return");
            ObjectNode before=(ObjectNode)stage.get("before");BigInteger pointer=integer(before,"observed_owner_identity"),id=integer(before,"observed_owner_character_id");
            require(pointer!=null && pointer.signum()!=0 && id!=null,name,"filtered record lacks immutable before receiver");
            Receiver receiver=new Receiver(pointer,id.longValueExact());require(resolved.contains(receiver),name,"record belongs to a different pointer or full generation ID");
            normalizedRecords.add(wire.deepCopy());records.add(new TransferRecord(normalized,wire,receiver));
        }
        out.set("records",normalizedRecords);return new Query(out,records);
    }
    private static void nativeTokens(ObjectNode record,String field) {
        ObjectNode stage=exact(record.get("stage"),field+".stage",Set.of("observation_stage","observed","original_called","original_returned","reason","model_a_identity","model_b_identity","original_return_rva",
                "before_event","completed_event","preparation","before","after","preparation_model_is_b","preparation_owner_matches_before","preparation_owner_matches_after","before_after_owner_generation_equal","event_clock_and_thread_match","completion_ordered_after_begin","generic_postimages_complete","transfer_to_entry_association_proven","observer_model_write_performed","full_person_ready","entry_ready"));
        for(String key:List.of("model_a_identity","model_b_identity","original_return_rva"))pointerNode(stage.get(key),field+".stage."+key,false);
        for(String key:List.of("before_event","completed_event")) {
            ObjectNode event=exact(stage.get(key),field+"."+key,Set.of("clock_identity","sequence","thread_id"));pointerNode(event.get("clock_identity"),field+"."+key+".clock_identity",false);
            number(event.get("sequence"),field+"."+key+".sequence",64,true,false);
        }
        require(stage.get("preparation") instanceof ObjectNode,field,"preparation object required");ObjectNode prep=(ObjectNode)stage.get("preparation");number(prep.get("preparation_capture_sequence"),field+".preparation_capture_sequence",64,true,false);
        for(String key:List.of("preparation_character_identity","preparation_model_identity","preparation_context_identity","preparation_owner_character_identity"))pointerNode(prep.get(key),field+"."+key,true);
        for(String key:List.of("before","after")) {
            require(stage.get(key) instanceof ObjectNode,field+"."+key,"snapshot object required");ObjectNode snapshot=(ObjectNode)stage.get(key);
            for(String pointer:SNAP_PTRS)pointerNode(snapshot.get(pointer),field+"."+key+"."+pointer,true);
        }
    }
    private static void pointerNode(JsonNode value,String field,boolean nullable) {
        if(nullable && nil(value))return;require(value!=null && value.isTextual(),field,"native pointer must retain its hexadecimal string token");pointer(value.textValue(),field,false);
    }
    /** Wire token checks only; the single shared physical codec validates the complete schema and relationships. */
    private static void physicalWireTokens(JsonNode value,String field) {
        if(nil(value))return;
        if(value.isArray()) { for(int index=0;index<value.size();index++)physicalWireTokens(value.get(index),field+"["+index+"]");return; }
        if(!value.isObject())return;
        value.properties().forEach(entry->{
            String key=entry.getKey(),name=field+"."+key;JsonNode item=entry.getValue();
            if(PHYSICAL_PTRS.contains(key))pointerNode(item,name,true);
            else if(Set.of("sequence","maximum_payload_bytes","row_copy_budget").contains(key))number(item,name,64,true,false);
            else if(key.equals("values_q64"))numbers(item,name,64,false,true,false);
            else if(key.equals("values_q64_raw_bits") || key.equals("ordered_payload_raw64")) {
                if(!nil(item)) {
                    require(item.isArray(),name,"native raw bit array required");
                    for(JsonNode bits:item)require(bits.isTextual() && bits.textValue().matches("0x[0-9a-fA-F]{16}"),name,"native raw bits retain sixteen hexadecimal digits");
                }
            } else physicalWireTokens(item,name);
        });
    }
    private static BigInteger pointer(String value,String field,boolean nullable) {
        if(value==null && nullable)return null;require(value!=null && value.matches("0x[0-9a-fA-F]+"),field,"native hexadecimal pointer required");
        BigInteger result=new BigInteger(value.substring(2),16);require(result.bitLength()<=64,field,"native pointer outside uint64");return result;
    }
}
