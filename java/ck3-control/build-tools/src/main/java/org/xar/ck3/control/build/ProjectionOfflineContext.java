package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;

/** Distinct typed fixed-root offline knowledge scope in the same source-qualified JVM; no Game or ledger authority. */
public final class ProjectionOfflineContext {
    public static final String PRODUCER = "java-quarkus-offline-event-analysis/v1";
    public static final String CONTRACT = "xar.offline-event-analysis/v1";
    private ProjectionOfflineContext() {}

    /** Explicit nonnull value enables UI offline review; paired roots additionally enable event batches. */
    public record Publishing(Path incidentRoot, Path knowledgeRoot) {
        public Publishing {
            if ((incidentRoot == null) != (knowledgeRoot == null)
                    || (incidentRoot != null && (!incidentRoot.isAbsolute() || !knowledgeRoot.isAbsolute()))) {
                throw new IllegalArgumentException("Optional paired explicit absolute offline event roots required");
            }
            if (incidentRoot != null) { incidentRoot = incidentRoot.normalize(); knowledgeRoot = knowledgeRoot.normalize(); }
        }
    }

    public record MandatoryReviews(String reviewRoot, String grantsManifest) {
        public MandatoryReviews { absolute(reviewRoot); absolute(grantsManifest); }
    }

    public record EventBatches(String incidentRoot, String knowledgeRoot, String grantsManifest) {
        public EventBatches { absolute(incidentRoot); absolute(knowledgeRoot); absolute(grantsManifest); }
    }

    public record Context(String schema, String machineId, String observedAtUtc,
            MandatoryReviews mandatoryReviews, EventBatches eventBatches) {
        public Context {
            if (!"xar.offline-event-analysis-context/v1".equals(schema) || machineId == null
                    || !machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown")) {
                throw new IllegalArgumentException("Actual machine-bound offline context required");
            }
            Instant.parse(observedAtUtc);
        }
    }

    public record Observed(Context context, ControlBuild.FileRef responseRef) {
        public Observed {
            Objects.requireNonNull(context); Objects.requireNonNull(responseRef);
            if (responseRef.bytes() < 1 || responseRef.bytes() > ProjectionDeploymentProof.MAX_OBSERVATION_BYTES) {
                throw new IllegalArgumentException("Bounded original offline context response required");
            }
        }
    }

    public static void requireExpected(MapAdmissionServiceOwner.Config config, String machine, Context context) throws IOException {
        Instant observed = Instant.parse(context.observedAtUtc()), now = Instant.now();
        if (config.offlinePublishing() == null || !machine.equals(context.machineId())
                || observed.isAfter(now.plusSeconds(5)) || observed.isBefore(now.minusSeconds(30))
                || context.mandatoryReviews() == null) {
            throw new IOException("Explicit current offline publishing scope and actual machine context required");
        }
        Path mandatoryRoot = config.eventStateRoot().resolve("evidence/unknown-mandatory-choice-reviews").normalize();
        if (!same(mandatoryRoot, context.mandatoryReviews().reviewRoot())
                || !same(config.evidenceGrantsManifest(), context.mandatoryReviews().grantsManifest())) {
            throw new IOException("Offline mandatory knowledge roots differ from explicit owner configuration");
        }
        Publishing expected = config.offlinePublishing();
        if (expected.incidentRoot() == null ? context.eventBatches() != null : context.eventBatches() == null
                || !same(expected.incidentRoot(), context.eventBatches().incidentRoot())
                || !same(expected.knowledgeRoot(), context.eventBatches().knowledgeRoot())
                || !same(config.evidenceGrantsManifest(), context.eventBatches().grantsManifest())) {
            throw new IOException("Offline event-batch roots differ from explicit owner configuration");
        }
    }

    private static boolean same(Path expected, String actual) { return expected.normalize().equals(Path.of(actual).normalize()); }
    private static void absolute(String value) {
        if (value == null || !Path.of(value).isAbsolute()) throw new IllegalArgumentException("Fixed absolute server offline root required");
    }
}
