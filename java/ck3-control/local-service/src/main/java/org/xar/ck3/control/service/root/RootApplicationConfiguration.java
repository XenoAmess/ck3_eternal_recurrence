package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact data inputs. Loading this file never creates a Game, ledger, session, authority or readiness proof. */
public record RootApplicationConfiguration(String machineId, HostMode mode, Instant reviewAt,
        ExactRef nativeLaunchPlan, WriterContracts.Layout ledger, List<ExactRef> writerSources,
        Path artifactRoot, long maximumArtifactBytes) {
    public static final String SCHEMA = "xar.java-root-application/v1";
    public static final int MAXIMUM_BYTES = 1 << 20;
    public RootApplicationConfiguration {
        StrictJson.require(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,63}") && !machineId.equals("unknown"),
                "explicit Root machine ID required");
        Objects.requireNonNull(mode); Objects.requireNonNull(reviewAt); Objects.requireNonNull(nativeLaunchPlan);
        Objects.requireNonNull(ledger); writerSources = List.copyOf(writerSources); Objects.requireNonNull(artifactRoot);
        StrictJson.require(ledger.machineId().equals(machineId), "Root ledger belongs to another machine");
        requireAbsolute(artifactRoot);
        StrictJson.require(!artifactRoot.equals(ledger.snapshot().getParent()) && !ledger.snapshot().startsWith(artifactRoot),
                "immutable artifact store cannot contain the canonical mutable ledger");
        StrictJson.safe(maximumArtifactBytes, 1);
        StrictJson.require(maximumArtifactBytes <= (1L << 40), "finite configured immutable archive budget required");
        StrictJson.require(nativeLaunchPlan.bytes() > 0 && nativeLaunchPlan.bytes() <= MAXIMUM_BYTES,
                "bounded exact native launch plan required");
        StrictJson.require(!writerSources.isEmpty() && writerSources.size() <= WriterContracts.MAXIMUM_CONFIGURED_SOURCES, "complete finite writer source closure required");
        Set<Path> names = new HashSet<>();
        for (ExactRef source : writerSources) {
            StrictJson.require(source.bytes() > 0 && names.add(Path.of(source.path()).normalize()), "unique nonempty writer source required");
            requireAbsolute(Path.of(source.path()));
        }
    }

    /** Compatibility DATA method; historical review/source references grant no runtime permission. */
    public void requireCurrent(Clock clock) throws IOException {Objects.requireNonNull(clock);}

    public static RootApplicationConfiguration readExact(ControlBuild.FileRef exact) throws IOException {
        Objects.requireNonNull(exact);
        if(exact.bytes()<1||exact.bytes()>MAXIMUM_BYTES)throw new IOException("Bounded exact Root configuration required");
        byte[] raw;
        try(var input=Files.newInputStream(Path.of(exact.path()))){raw=input.readNBytes(MAXIMUM_BYTES+1);}
        if(raw.length!=exact.bytes()||raw.length>MAXIMUM_BYTES
                ||!org.xar.ck3.control.application.driver.DriverJson.sha256(raw).equalsIgnoreCase(exact.sha256()))
            throw new IOException("Root configuration DATA bytes/SHA mismatch");
        try{return fromJson(StrictJson.parse(raw,MAXIMUM_BYTES));}
        catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("Invalid exact Root application configuration",invalid);}
    }

    public static RootApplicationConfiguration fromJson(JsonNode value) {
        ObjectNode root = StrictJson.object(value, Set.of("schema", "machine_id", "mode", "review_at_utc", "native_launch_plan",
                "ledger", "writer_sources", "artifact_root", "maximum_artifact_bytes"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "exact Root application schema required");
        String machine = StrictJson.text(root.get("machine_id"));
        String rawInstant = StrictJson.text(root.get("review_at_utc")); Instant review = Instant.parse(rawInstant);
        StrictJson.require(rawInstant.equals(review.toString()), "canonical UTC review time required");
        ObjectNode ledger = StrictJson.object(root.get("ledger"), Set.of("snapshot", "anchor"));
        JsonNode sources = root.get("writer_sources");
        StrictJson.require(sources != null && sources.isArray() && !sources.isEmpty() && sources.size() <= WriterContracts.MAXIMUM_CONFIGURED_SOURCES,
                "actual writer source list required");
        List<ExactRef> refs = new ArrayList<>(); for (JsonNode source : sources) refs.add(ExactRef.fromJson(source));
        return new RootApplicationConfiguration(machine, HostMode.valueOf(StrictJson.text(root.get("mode"))), review,
                ExactRef.fromJson(root.get("native_launch_plan")),
                new WriterContracts.Layout(absolute(StrictJson.text(ledger.get("snapshot"))), ExactRef.fromJson(ledger.get("anchor")), machine),
                refs, absolute(StrictJson.text(root.get("artifact_root"))),
                StrictJson.integer(root.get("maximum_artifact_bytes"), 1, 1L << 40));
    }

    public ObjectNode toJson() {
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA); root.put("machine_id", machineId);
        root.put("mode", mode.name()); root.put("review_at_utc", reviewAt.toString()); root.set("native_launch_plan", nativeLaunchPlan.toJson());
        ObjectNode layout = root.putObject("ledger"); layout.put("snapshot", ledger.snapshot().toString()); layout.set("anchor", ledger.anchor().toJson());
        var sources = root.putArray("writer_sources"); writerSources.forEach(source -> sources.add(source.toJson()));
        root.put("artifact_root", artifactRoot.toString()); root.put("maximum_artifact_bytes", maximumArtifactBytes); return root;
    }

    public static ControlBuild.FileRef file(ExactRef ref) { return new ControlBuild.FileRef(ref.path(), ref.bytes(), ref.sha256()); }
    private static Path absolute(String raw) { Path result = Path.of(raw); requireAbsolute(result); return result; }
    private static void requireAbsolute(Path path) {
        StrictJson.require(path.isAbsolute() && path.normalize().equals(path), "normalized absolute Root input path required");
    }
}
