package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;

/** Shared strict original-body projection. Public input/output are DATA, never Native/source grants. */
public final class M7NativeProjection {
    public static final String GAME_VERSION = "1.20.0.4";
    public static final String EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final int MAX_BYTES = 1_048_576;
    private static final ObjectMapper JSON=new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
    private static final Set<String> LIFE = Set.of("schema","lifecycle","xar_enabled","pact_contract","source","environment_sha256");
    private M7NativeProjection() { }

    /** Expected facts supplied by the real Root owner; constructing this record grants nothing. */
    public record Binding(String machineId, String sourceEpoch, GameIdentity game, ExactRef executable,
            String episodeRunId, long actorCharacterId, String pipeName, String connectionGeneration,
            ProjectionJson lifecycle) {
        public Binding {
            StrictJson.text(machineId); StrictJson.text(sourceEpoch); Objects.requireNonNull(game); Objects.requireNonNull(executable);
            StrictJson.text(episodeRunId); StrictJson.text(pipeName); Objects.requireNonNull(lifecycle);
            StrictJson.require(executable.sha256().equalsIgnoreCase(EXE_SHA256), "independent exact .4 source binding required");
            NativeCharacterId.of(actorCharacterId);
            decimal(connectionGeneration);
            ObjectNode life=StrictJson.object(StrictJson.parse(lifecycle.bytes()),LIFE);
            StrictJson.require("xar.ck3.succession-lifecycle-binding/v1".equals(text(life,"schema"))
                    && "ordinary_campaign_succession".equals(text(life,"lifecycle")), "original ordinary lifecycle required");
        }
    }

    public static KernelCheckpointContinuity.Observation project(byte[] originalOwnerRow, Binding expected) throws IOException {
        Objects.requireNonNull(expected);
        // The complete body may contain unrelated decimal metrics. Validate its original JSON token
        // domain, then apply strict integer checks only to the fields consumed below.
        JsonNode row=JSON.readTree(ProjectionJson.object(originalOwnerRow,MAX_BYTES).bytes());
        JsonNode result=object(row.get("result"));
        StrictJson.require(result.get("is_error")!=null && result.get("is_error").isBoolean()
                && !result.get("is_error").booleanValue(), "original successful semantic completion required");
        JsonNode snapshot=object(result.get("structured_content"));
        StrictJson.require(bool(snapshot,"map_ready") && bool(snapshot,"paused"), "actual paused map required");
        long actor=NativeCharacterId.fromJson(object(snapshot.get("played_character")).get("character_id")).value();
        BigInteger revision=StrictJson.integer(snapshot.get("revision"),BigInteger.ZERO,StrictJson.UINT64_MAX);
        BigInteger nativeRevision=StrictJson.integer(snapshot.get("native_revision"),BigInteger.ONE,StrictJson.UINT64_MAX);
        String snapshotId=text(snapshot,"snapshot_id"), episode=text(snapshot,"episode_run_id");
        StrictJson.require(snapshotId.equals("native:"+nativeRevision) && actor==expected.actorCharacterId()
                && episode.equals(expected.episodeRunId()), "actual actor/episode/packet differs from original Root lineage");
        JsonNode diagnostics=object(snapshot.get("diagnostics")),hello=object(diagnostics.get("hello"));
        StrictJson.require(bool(diagnostics,"connected") && text(diagnostics,"pipe_name").equals(expected.pipeName())
                && integer(diagnostics,"bridge_pid",1,0xffff_ffffL)==expected.game().pid()
                && integer(hello,"pid",1,0xffff_ffffL)==expected.game().pid()
                && unsigned(diagnostics,"connection_generation").equals(expected.connectionGeneration())
                && unsigned(hello,"connection_generation").equals(expected.connectionGeneration())
                && bool(hello,"ck3_build_match") && text(hello,"expected_ck3_version").equals(GAME_VERSION)
                && text(hello,"expected_ck3_sha256").equalsIgnoreCase(expected.executable().sha256()),
                "actual Native diagnostics differ from the held .4 Game/connection");
        ObjectNode life=StrictJson.object(snapshot.get("succession_lifecycle"),LIFE);
        StrictJson.require(Arrays.equals(StrictJson.canonical(life),StrictJson.canonical(StrictJson.parse(expected.lifecycle().bytes()))),
                "complete actual lifecycle differs from the original Root lifecycle");
        var goal=GoalCodec.parseGoal(snapshot.get("campaign_goal"));
        return new KernelCheckpointContinuity.Observation(expected.machineId(),expected.sourceEpoch(),expected.game(),
                expected.executable(),snapshotId,revision,nativeRevision,episode,actor,
                integer(snapshot,"date_raw",0,StrictJson.MAX_SAFE_INTEGER),goal,null,null);
    }
    private static JsonNode object(JsonNode value) { StrictJson.require(value!=null && value.isObject(),"required Native object"); return value; }
    private static String text(JsonNode value,String field) { return StrictJson.text(value.get(field)); }
    private static boolean bool(JsonNode value,String field) {
        JsonNode v=value.get(field); StrictJson.require(v!=null && v.isBoolean(),"required exact Native boolean"); return v.booleanValue();
    }
    private static long integer(JsonNode value,String field,long minimum,long maximum) { return StrictJson.integer(value.get(field),minimum,maximum); }
    private static String unsigned(JsonNode value,String field) { return StrictJson.integer(value.get(field),BigInteger.ONE,StrictJson.UINT64_MAX).toString(); }
    private static void decimal(String value) {
        StrictJson.require(value!=null && value.matches("[1-9][0-9]{0,19}")
                && new BigInteger(value).compareTo(StrictJson.UINT64_MAX)<=0,"canonical positive uint64 identity required");
    }
}
