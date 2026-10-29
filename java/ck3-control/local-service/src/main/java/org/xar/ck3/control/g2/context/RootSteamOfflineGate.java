package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.SteamOfflineObservation;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** Cold Root consumer of the same Java background producer as the ordinary lifecycle. */
public final class RootSteamOfflineGate {
    public static final String PLAN_SCHEMA = "xar.java-steam-offline-gate-plan/v1";
    private RootSteamOfflineGate() { }

    /** Data configuration only: exact installed Steam, explicit output and original bounded CEF timeout. */
    public record Plan(String machineId, ControlBuild.FileRef steamExecutable, Path evidenceRoot,
            Instant deadline, Duration observationTimeout, Duration cefTimeout) {
        public Plan {
            Objects.requireNonNull(machineId); Objects.requireNonNull(steamExecutable); Objects.requireNonNull(evidenceRoot);
            Objects.requireNonNull(deadline); bounded(observationTimeout); bounded(cefTimeout);
            if (machineId.isBlank() || machineId.equals("unknown") || !evidenceRoot.isAbsolute()
                    || !evidenceRoot.normalize().equals(evidenceRoot) || steamExecutable.bytes() < 1
                    || !Path.of(steamExecutable.path()).getFileName().toString().equalsIgnoreCase("steam.exe")) {
                throw new IllegalArgumentException("Finite exact Java Steam observation plan required");
            }
        }
        private static void bounded(Duration value) {
            Objects.requireNonNull(value);
            if (value.compareTo(Duration.ofMillis(100)) < 0 || value.compareTo(Duration.ofSeconds(10)) > 0
                    || !value.equals(Duration.ofMillis(value.toMillis()))) throw new IllegalArgumentException("Exact100..10000ms observation timeout required");
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static Plan fromJson(JsonNode node) {
            ObjectNode value = StrictJson.object(node, Set.of("schema", "machine_id", "steam_executable", "evidence_root",
                    "deadline", "observation_timeout_millis", "cef_timeout_millis"));
            StrictJson.require(StrictJson.text(value.get("schema")).equals(PLAN_SCHEMA), "Current Java Steam plan schema required");
            ExactRef steam = ExactRef.fromJson(value.get("steam_executable"));
            String rawDeadline = StrictJson.text(value.get("deadline")); Instant deadline = Instant.parse(rawDeadline);
            StrictJson.require(deadline.toString().equals(rawDeadline), "Canonical UTC Steam plan deadline required");
            return new Plan(StrictJson.text(value.get("machine_id")), new ControlBuild.FileRef(steam.path(), steam.bytes(), steam.sha256()),
                    Path.of(StrictJson.text(value.get("evidence_root"))), deadline,
                    Duration.ofMillis(StrictJson.integer(value.get("observation_timeout_millis"), 100, 10000)),
                    Duration.ofMillis(StrictJson.integer(value.get("cef_timeout_millis"), 100, 10000)));
        }
        @JsonValue public ObjectNode toJson() {
            ObjectNode node = StrictJson.object(); node.put("schema", PLAN_SCHEMA); node.put("machine_id", machineId);
            node.set("steam_executable", new ExactRef(steamExecutable.path(), steamExecutable.bytes(), steamExecutable.sha256()).toJson());
            node.put("evidence_root", evidenceRoot.toString()); node.put("deadline", deadline.toString());
            node.put("observation_timeout_millis", observationTimeout.toMillis()); node.put("cef_timeout_millis", cefTimeout.toMillis()); return node;
        }
    }
    /** Only observe constructs this wrapper around the actual private live Java token. */
    public static final class QualifiedOffline implements AutoCloseable {
        private final RootNativeRuntimeBinding runtime;
        private final Plan plan;
        private final SteamOfflineProbe.QualifiedOffline nativeToken;
        private boolean consumed, closed;
        private QualifiedOffline(RootNativeRuntimeBinding runtime, Plan plan, SteamOfflineProbe.QualifiedOffline nativeToken) {
            this.runtime = runtime; this.plan = plan; this.nativeToken = nativeToken;
        }
        public ControlBuild.FileRef receipt() { return nativeToken.evidence(); }
        public synchronized void consumeBeforeGameCreate(RootNativeRuntimeBinding expected) throws IOException {
            if (consumed || closed || runtime != expected) throw new IOException("Same original Root and unconsumed fresh Steam token required");
            consumed = true;
            try {
                verifySources(runtime, plan); nativeToken.evidence().verify(); nativeToken.consumeBeforeGameCreate();
            } catch (IOException | RuntimeException failure) {
                try { close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); } throw failure;
            }
            close();
        }
        @Override public synchronized void close() throws IOException {
            if (!closed) { closed = true; nativeToken.close(); }
        }
    }
    /** No interpreter, child process, cached receipt reader, screenshot, focus or Steam mode operation. */
    public static QualifiedOffline observe(RootNativeRuntimeBinding runtime, Plan plan) throws IOException {
        Objects.requireNonNull(runtime); Objects.requireNonNull(plan); verifySources(runtime, plan);
        ProjectStoragePolicy.requireBulkOutput(plan.evidenceRoot());
        SharedSourceFiles.plainAncestors(plan.evidenceRoot()); Files.createDirectory(plan.evidenceRoot());
        Instant observationDeadline = Instant.now().plus(plan.observationTimeout());
        if (observationDeadline.isAfter(plan.deadline())) observationDeadline = plan.deadline();
        var token = SteamOfflineProbe.observe(new SteamOfflineProbe.Plan(plan.machineId(), plan.steamExecutable(), observationDeadline),
                plan.evidenceRoot().resolve("offline.json"), plan.cefTimeout());
        try {
            SteamOfflineObservation.Offline observed = token.observation();
            if (!observed.common().machineId().equals(runtime.request().machineId())) throw new IOException("Actual Java Steam observation belongs to another machine");
            verifySources(runtime, plan); token.verify(); return new QualifiedOffline(runtime, plan, token);
        } catch (IOException | RuntimeException failure) {
            try { token.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); } throw failure;
        }
    }
    private static void verifySources(RootNativeRuntimeBinding runtime, Plan plan) throws IOException {
        runtime.verify(); plan.steamExecutable().verify();
        if (!plan.machineId().equals(runtime.request().machineId()) || !Instant.now().isBefore(plan.deadline())
                || plan.deadline().isAfter(runtime.request().reviewAt())) throw new IOException("Steam observation plan is expired or differs from Root binding");
        SteamOfflineProbe.requireReviewedSources(runtime.completeSources());
    }
}
