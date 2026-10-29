package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Exact finite startup data. Neither this configuration nor its decoder can mint a Game or a resumed Driver. */
public record RootStartupConfiguration(String machineId,Instant reviewAt,ControlBuild.FileRef application,
        ControlBuild.FileRef runtimeDefinitions,String authorityId,G2Source source,FreshRobert entry,
        CheckpointPaths checkpoints,NativeReadiness.Policy ordinaryPolicy,Duration freshness,
        List<BatchLimits> batches,Path receiptDirectory) {
    public static final String SCHEMA="xar.java-root-startup/v1";
    public static final int MAXIMUM_BYTES=1<<20;
    public record FreshRobert(String actionId) {
        public FreshRobert { requireId(actionId); }
    }
    public record CheckpointPaths(Path driverCheckpoint,Path checkpointEvidence,Path attachmentEvidence,String lineageId,Path save) {
        public CheckpointPaths {
            for(Path path:List.of(driverCheckpoint,checkpointEvidence,attachmentEvidence,save))absolute(path);
            requireId(lineageId);StrictJson.require(save.getFileName().toString().endsWith(".ck3"),"actual CK3 save destination required");
            StrictJson.require(!driverCheckpoint.equals(save),"Driver checkpoint and physical CK3 save are distinct files");
        }
    }
    public RootStartupConfiguration {
        StrictJson.require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,63}")&&!machineId.equals("unknown"),"explicit startup machine required");
        Objects.requireNonNull(reviewAt);Objects.requireNonNull(application);Objects.requireNonNull(runtimeDefinitions);
        requireId(authorityId);Objects.requireNonNull(source);Objects.requireNonNull(entry);Objects.requireNonNull(checkpoints);
        Objects.requireNonNull(ordinaryPolicy);Objects.requireNonNull(freshness);absolute(receiptDirectory);batches=List.copyOf(batches);
        StrictJson.require(source.machineId().equals(machineId),"startup source belongs to another machine");
        for(var ref:List.of(application,runtimeDefinitions)) {
            absolute(Path.of(ref.path()));StrictJson.require(ref.bytes()>0&&ref.bytes()<=MAXIMUM_BYTES,"finite exact startup input required");
        }
        StrictJson.require(!application.path().equals(runtimeDefinitions.path()),"application and concrete runtime definitions require distinct exact inputs");
        StrictJson.require(!ordinaryPolicy.coldCheckpoint()&&!ordinaryPolicy.allowTerminal()&&ordinaryPolicy.expectedActor().isEmpty(),
                "ordinary owner follows the actual committed Driver; initial Robert and terminal admission have their separate real producers");
        StrictJson.require(ordinaryPolicy.stableFor().getNano()%1_000_000==0,"whole-millisecond readiness stability required");
        StrictJson.require(!freshness.isZero()&&!freshness.isNegative()&&freshness.compareTo(Duration.ofMinutes(1))<=0
                &&freshness.getNano()%1_000_000==0,"finite whole-millisecond source/readiness freshness required");
        StrictJson.require(!batches.isEmpty()&&batches.size()<=4096,"finite actual batch schedule required");
        Set<String> names=new HashSet<>();for(var batch:batches)StrictJson.require(names.add(batch.batchId()),"batch IDs cannot be replayed by a startup schedule");
    }
    public void requireCurrent(Clock clock)throws IOException {
        Objects.requireNonNull(clock);
        if(!machineId.equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(reviewAt))
            throw new IOException("actual startup machine and unexpired review required");
        application.verify();runtimeDefinitions.verify();RootApplicationConfiguration.file(source.sourceRef()).verify();
    }
    /** CLI identity includes bytes and SHA; measuring a caller-selected file is not an authorization substitute. */
    public static RootStartupConfiguration readExact(ControlBuild.FileRef exact)throws IOException {
        Objects.requireNonNull(exact);
        if(exact.bytes()<1||exact.bytes()>MAXIMUM_BYTES)throw new IOException("bounded exact Root startup input required");
        exact.verify();var witness=SharedSourceFiles.observe(Path.of(exact.path()));byte[] raw;
        try(var input=Files.newInputStream(Path.of(exact.path()))){raw=input.readNBytes(MAXIMUM_BYTES+1);}
        if(raw.length!=exact.bytes())throw new IOException("Root startup input changed while reading");
        try {
            var result=fromJson(StrictJson.parse(raw,MAXIMUM_BYTES));SharedSourceFiles.assertUnchanged(witness);exact.verify();return result;
        }catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("invalid exact Root startup configuration",invalid);}
    }
    public static RootStartupConfiguration fromJson(JsonNode value) {
        ObjectNode root=StrictJson.object(value,Set.of("schema","machine_id","review_at_utc","application","runtime_definitions",
                "authority_id","source","entry","checkpoints","ordinary_readiness","freshness_ms","batches","receipt_directory"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))),"exact Root startup schema required");
        var source=StrictJson.object(root.get("source"),Set.of("machine_id","observed_at_utc","exact_build","source_ref"));
        var entry=StrictJson.object(root.get("entry"),Set.of("kind","action_id"));
        StrictJson.require("FRESH_ROBERT_1066".equals(StrictJson.text(entry.get("kind"))),
                "cold JVM saved-driver adoption is unavailable; this startup requires the genuine initial Robert entry");
        var paths=StrictJson.object(root.get("checkpoints"),Set.of("driver_checkpoint","checkpoint_evidence","attachment_evidence","lineage_id","save"));
        var policy=StrictJson.object(root.get("ordinary_readiness"),Set.of("stable_for_ms","require_post_ready_pump"));
        JsonNode pump=policy.get("require_post_ready_pump");StrictJson.require(pump!=null&&pump.isBoolean(),"readiness pump policy must be a JSON boolean");
        JsonNode batchValues=root.get("batches");StrictJson.require(batchValues!=null&&batchValues.isArray()&&!batchValues.isEmpty()&&batchValues.size()<=4096,"finite batch schedule array required");
        List<BatchLimits> batches=new ArrayList<>();
        for(JsonNode item:batchValues) {
            var batch=StrictJson.object(item,Set.of("batch_id","maximum_turns","wall_time_ms","readiness_timeout_ms","poll_interval_ms","checkpoint_every_eligible_advances"));
            batches.add(new BatchLimits(StrictJson.text(batch.get("batch_id")),(int)StrictJson.integer(batch.get("maximum_turns"),1,100000),
                    Duration.ofMillis(StrictJson.integer(batch.get("wall_time_ms"),1,86400000)),
                    Duration.ofMillis(StrictJson.integer(batch.get("readiness_timeout_ms"),1,3600000)),
                    Duration.ofMillis(StrictJson.integer(batch.get("poll_interval_ms"),1,60000)),
                    (int)StrictJson.integer(batch.get("checkpoint_every_eligible_advances"),1,100000)));
        }
        return new RootStartupConfiguration(StrictJson.text(root.get("machine_id")),instant(root.get("review_at_utc")),
                file(root.get("application")),file(root.get("runtime_definitions")),StrictJson.text(root.get("authority_id")),
                new G2Source(StrictJson.text(source.get("machine_id")),StrictJson.text(source.get("observed_at_utc")),StrictJson.text(source.get("exact_build")),ExactRef.fromJson(source.get("source_ref"))),
                new FreshRobert(StrictJson.text(entry.get("action_id"))),
                new CheckpointPaths(path(paths.get("driver_checkpoint")),path(paths.get("checkpoint_evidence")),path(paths.get("attachment_evidence")),StrictJson.text(paths.get("lineage_id")),path(paths.get("save"))),
                new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ofMillis(StrictJson.integer(policy.get("stable_for_ms"),0,86400000)),pump.booleanValue()),
                Duration.ofMillis(StrictJson.integer(root.get("freshness_ms"),1,60000)),batches,path(root.get("receipt_directory")));
    }
    public ObjectNode toJson() {
        ObjectNode root=StrictJson.object();root.put("schema",SCHEMA);root.put("machine_id",machineId);root.put("review_at_utc",reviewAt.toString());
        root.set("application",new ExactRef(application.path(),application.bytes(),application.sha256()).toJson());
        root.set("runtime_definitions",new ExactRef(runtimeDefinitions.path(),runtimeDefinitions.bytes(),runtimeDefinitions.sha256()).toJson());root.put("authority_id",authorityId);
        var provenance=root.putObject("source");provenance.put("machine_id",source.machineId());provenance.put("observed_at_utc",source.observedAtUtc());
        provenance.put("exact_build",source.exactBuild());provenance.set("source_ref",source.sourceRef().toJson());
        var start=root.putObject("entry");start.put("kind","FRESH_ROBERT_1066");start.put("action_id",entry.actionId());
        var paths=root.putObject("checkpoints");paths.put("driver_checkpoint",checkpoints.driverCheckpoint().toString());paths.put("checkpoint_evidence",checkpoints.checkpointEvidence().toString());
        paths.put("attachment_evidence",checkpoints.attachmentEvidence().toString());paths.put("lineage_id",checkpoints.lineageId());paths.put("save",checkpoints.save().toString());
        var policy=root.putObject("ordinary_readiness");policy.put("stable_for_ms",ordinaryPolicy.stableFor().toMillis());policy.put("require_post_ready_pump",ordinaryPolicy.requirePostReadyPump());
        root.put("freshness_ms",freshness.toMillis());var scheduled=root.putArray("batches");
        for(var batch:batches){var item=scheduled.addObject();item.put("batch_id",batch.batchId());item.put("maximum_turns",batch.maximumTurns());item.put("wall_time_ms",batch.wallTime().toMillis());
            item.put("readiness_timeout_ms",batch.readinessTimeout().toMillis());item.put("poll_interval_ms",batch.pollInterval().toMillis());item.put("checkpoint_every_eligible_advances",batch.checkpointEveryEligibleAdvances());}
        root.put("receipt_directory",receiptDirectory.toString());return root;
    }
    private static ControlBuild.FileRef file(JsonNode value){return RootApplicationConfiguration.file(ExactRef.fromJson(value));}
    private static Path path(JsonNode value){Path path=Path.of(StrictJson.text(value));absolute(path);return path;}
    private static void absolute(Path value){StrictJson.require(value!=null&&value.isAbsolute()&&value.normalize().equals(value),"normalized absolute startup path required");}
    private static Instant instant(JsonNode value){String raw=StrictJson.text(value);Instant result=Instant.parse(raw);StrictJson.require(raw.equals(result.toString()),"canonical UTC startup review required");return result;}
    private static void requireId(String value){StrictJson.require(value!=null&&value.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"),"bounded exact startup identity required");}
}
