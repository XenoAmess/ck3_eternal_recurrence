package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.time.Instant;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed receipt DATA. Decoding never constructs a creator, custody or private bootstrap capability. */
public final class ColdBootstrapJson {
    private ColdBootstrapJson() { }
    public static final int MAX_BYTES=65536;
    public record PhysicalData(String schema,String machineId,String requestId,String sessionId,
            WindowsJobProcess.ProcessIdentity game,String pipeName,String connectionGeneration,
            ExactRef nativeHello,ExactRef steamOffline,ExactRef launchEvidence,ExactRef save,
            FileStatIdentity saveStat,SharedSourceFiles.NativeFile saveNative,String observedAtUtc,String deadlineUtc) {
        public PhysicalData {
            if(!"xar.java-cold-physical-bootstrap/v1".equals(schema))throw new IllegalArgumentException("Cold physical receipt schema");
            for(String text:new String[]{machineId,requestId,sessionId,pipeName})StrictJson.text(text);
            Objects.requireNonNull(game);Objects.requireNonNull(nativeHello);Objects.requireNonNull(steamOffline);
            Objects.requireNonNull(launchEvidence);Objects.requireNonNull(save);Objects.requireNonNull(saveStat);Objects.requireNonNull(saveNative);
            positiveDecimal(connectionGeneration,64);
            Instant observed=Instant.parse(observedAtUtc),deadline=Instant.parse(deadlineUtc);
            if(!observed.isBefore(deadline)||!saveStat.bytes().equals(java.math.BigInteger.valueOf(save.bytes()))
                    ||saveNative.logicalBytes()!=save.bytes()||save.bytes()<=0)
                throw new IllegalArgumentException("Actual finite matching physical save facts required");
            for(long size:new long[]{save.bytes(),nativeHello.bytes(),steamOffline.bytes(),launchEvidence.bytes(),
                    saveNative.logicalBytes(),saveNative.allocatedBytes(),saveNative.linkCount()})StrictJson.safe(size,0);
        }
    }
    public record AdoptionData(String schema,String bootstrapId,ExactRef physical,String eventIdentity,
            long committedSequence,String committedHeadDigest,ExactRef fullDriver,String observedAtUtc) {
        public AdoptionData {
            if(!"xar.java-cold-canonical-bootstrap/v1".equals(schema))throw new IllegalArgumentException("Cold canonical receipt schema");
            StrictJson.text(bootstrapId);Objects.requireNonNull(physical);Objects.requireNonNull(fullDriver);
            StrictJson.safe(committedSequence,1);Instant.parse(observedAtUtc);
            if(eventIdentity==null||committedHeadDigest==null||!eventIdentity.matches("[0-9a-f]{64}")||!committedHeadDigest.matches("[0-9a-f]{64}"))
                throw new IllegalArgumentException("Exact canonical identity/digest required");
        }
    }
    public static byte[] encodePhysical(PhysicalData data)throws IOException{return bounded(ControlBuild.strictMapper().writeValueAsBytes(Objects.requireNonNull(data)));}
    public static byte[] encodeAdoption(AdoptionData data)throws IOException{return bounded(ControlBuild.strictMapper().writeValueAsBytes(Objects.requireNonNull(data)));}
    public static PhysicalData decodePhysical(byte[] bytes)throws IOException {
        JsonNode row=tree(bytes);keys(row,Set.of("schema","machine_id","request_id","session_id","game","pipe_name","connection_generation",
                "native_hello","steam_offline","launch_evidence","save","save_stat","save_native","observed_at_utc","deadline_utc"));
        texts(row,"schema","machine_id","request_id","session_id","pipe_name","connection_generation","observed_at_utc","deadline_utc");
        texts(row.path("game"),"creation_filetime_decimal","executable");
        integers(row.path("game"),"pid");
        texts(row.path("save_stat"),"file_id","mtime_ns");
        integers(row.path("save_stat"),"bytes");
        texts(row.path("save_native"),"volume_serial_decimal","file_id_decimal","legacy_volume_serial_decimal","legacy_file_id_hex",
                "creation_filetime_decimal","last_write_filetime_decimal","change_filetime_decimal");
        integers(row.path("save_native"),"logical_bytes","allocated_bytes","link_count");
        return ControlBuild.strictMapper().treeToValue(row,PhysicalData.class);
    }
    public static AdoptionData decodeAdoption(byte[] bytes)throws IOException {
        JsonNode row=tree(bytes);keys(row,Set.of("schema","bootstrap_id","physical","event_identity","committed_sequence","committed_head_digest","full_driver","observed_at_utc"));
        texts(row,"schema","bootstrap_id","event_identity","committed_head_digest","observed_at_utc");
        if(!row.path("committed_sequence").isIntegralNumber()||!row.path("committed_sequence").canConvertToLong())throw new IOException("Canonical sequence must be an integer");
        return ControlBuild.strictMapper().treeToValue(row,AdoptionData.class);
    }
    private static JsonNode tree(byte[] bytes)throws IOException{return ControlBuild.strictMapper().readTree(bounded(bytes));}
    private static byte[] bounded(byte[] bytes)throws IOException {
        if(bytes==null||bytes.length==0||bytes.length>MAX_BYTES)throw new IOException("Bounded complete cold receipt required");return bytes;
    }
    private static void keys(JsonNode node,Set<String> expected)throws IOException {
        if(node==null||!node.isObject())throw new IOException("Cold receipt object required");
        Set<String> actual=new HashSet<>();node.fieldNames().forEachRemaining(actual::add);
        if(!actual.equals(expected))throw new IOException("Cold receipt fields differ from the single closed contract");
    }
    private static void texts(JsonNode node,String... fields)throws IOException {
        for(String field:fields)if(!node.path(field).isTextual())throw new IOException("Cold receipt text field required: "+field);
    }
    private static void integers(JsonNode node,String... fields)throws IOException {
        for(String field:fields)if(!node.path(field).isIntegralNumber()||!node.path(field).canConvertToLong()
                ||node.path(field).longValue()<0||node.path(field).longValue()>StrictJson.MAX_SAFE_INTEGER)
            throw new IOException("Cold receipt safe integer field required: "+field);
    }
    private static void positiveDecimal(String value,int width) {
        if(value==null||!value.matches("[1-9][0-9]*")||value.length()>20||new java.math.BigInteger(value).bitLength()>width)
            throw new IllegalArgumentException("Canonical positive unsigned decimal required");
    }
}
