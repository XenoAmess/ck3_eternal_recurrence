package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Offline publication after actual source review; not a read-only projection or a native action. */
public final class OfflineEventReviewGrantPublisher {
    private static final int LIMIT = 1_048_576;
    private OfflineEventReviewGrantPublisher() { }

    /** Constructed by the qualified offline dispatcher from fixed server configuration, never a caller payload. */
    public record Configuration(EventSourceReadContext sources, Path incidentRoot, Path reviewRoot, Path grantsManifest, Optional<Path> scanRoot) {
        public Configuration(EventSourceReadContext sources, Path incidentRoot, Path reviewRoot, Path grantsManifest) {
            this(sources, incidentRoot, reviewRoot, grantsManifest, Optional.empty());
        }
        public Configuration {
            Objects.requireNonNull(sources); incidentRoot = fixed(incidentRoot); reviewRoot = fixed(reviewRoot); grantsManifest = fixed(grantsManifest);
            scanRoot = Objects.requireNonNull(scanRoot).map(OfflineEventReviewGrantPublisher::fixed);
            new OfflineEventBatchAnalyzer.Configuration(sources, incidentRoot, reviewRoot, grantsManifest, scanRoot);
            require(!incidentRoot.startsWith(sources.stockGameRoot()) && !reviewRoot.startsWith(sources.stockGameRoot())
                    && !grantsManifest.startsWith(sources.stockGameRoot()), "offline evidence output cannot use installed stock roots");
        }
    }

    /** Revalidates new and already-known reviews, then adds exact facts grants under the shared writer lock. */
    public static EvidenceGrantManifestPublisher.Publication publish(Configuration configured, Path originalReport) throws IOException {
        Objects.requireNonNull(configured);
        TrustedEventSourceContext trusted = TrustedEventSourceContext.open(configured.sources());
        byte[] reportRaw = readWithin(configured.reviewRoot(), originalReport, LIMIT);
        ObjectValue report = RetainedJson.object(RetainedJson.parse(reportRaw));
        require(eq(report, "Game_MCP_OBS_calls", i(0)) && eq(report, "machine_id", s(trusted.machineId())), "original offline source report and machine required");
        ObjectValue manifestRef = o(report, "manifest");
        boolean observed = eq(report, "schema", s(OfflineBatchBinding.REPORT_V2));
        Path manifestRoot = observed ? configured.scanRoot().orElseThrow(() -> new IllegalArgumentException("Fixed actual scan root required")) : configured.incidentRoot();
        byte[] manifestRaw = referenced(manifestRoot, manifestRef, LIMIT);
        ExactRef manifestPin = new ExactRef(requiredText(manifestRef, "path"), manifestRaw.length, sha(manifestRaw));
        ObjectValue manifest = RetainedJson.object(RetainedJson.parse(manifestRaw));
        var binding = OfflineBatchBinding.manifest(StrictJson.parse(manifestRaw, LIMIT));
        OfflineBatchBinding.requireReport(StrictJson.parse(reportRaw, LIMIT), binding, manifestPin);
        List<ObjectValue> incidents = objects(manifest, "new_incidents"); require(incidents.size() <= 256, "bounded offline incident batch required");
        List<ExactRef> captures = new ArrayList<>();
        Map<String, ObjectValue> byIncident = new LinkedHashMap<>();
        for (ObjectValue incident : incidents) {
            String id = requiredText(incident, "incident_id"); require(byIncident.put(id, incident) == null, "duplicate incident identity");
            for (String stage : List.of("before", "after")) if (!(v(incident, stage) instanceof NullValue)) {
                byte[] original = readIncident(configured.incidentRoot(), incident, stage);
                captures.add(new ExactRef(requiredText(incident, stage), original.length, sha(original)));
            }
        }
        var originalScan = OfflineScanSource.load(configured.incidentRoot(), configured.scanRoot(), trusted.machineId(), manifestPin, captures);
        List<ObjectValue> reviews = new ArrayList<>(objects(report, "entries")); reviews.addAll(objects(report, "already_known"));
        require(reviews.size() <= 256, "bounded offline review report required");
        List<ProjectionEvidenceGrant> additions = new ArrayList<>();
        for (ObjectValue review : reviews) {
            String incidentId = requiredText(review, "incident_id"); ObjectValue incident = byIncident.get(incidentId);
            require(incident != null, "review lacks its original incident");
            ObjectValue before = RetainedJson.object(RetainedJson.parse(readIncident(configured.incidentRoot(), incident, "before")));
            boolean interaction = eq(incident, "kind", s("pending_character_interaction"));
            require(eq(before, "incident_id", s(incidentId)) && eq(before, "schema", s(interaction ? "xar.pending-interaction-left-reply/v1" : "xar.unhandled-event-first-rendered/v1")), "original before incident differs");
            if (!(v(incident, "after") instanceof NullValue)) {
                ObjectValue after = RetainedJson.object(RetainedJson.parse(readIncident(configured.incidentRoot(), incident, "after")));
                require(eq(after, "incident_id", s(incidentId)), "original after incident differs");
            }
            String fingerprint = requiredText(review, "fingerprint"); require(fingerprint.matches("[0-9a-f]{64}"), "canonical review fingerprint required");
            if (interaction) {
                var actual = OfflineInteractionSourceAnalyzer.analyze(before, trusted);
                var result = OfflineInteractionSourceAnalyzer.reviewed(before, trusted);
                require(result instanceof InteractionRegistry.Known, "Actual interaction source registry is unavailable");
                var verified = ((InteractionRegistry.Known)result).review();
                require(actual.facts().equals(verified.facts()) && fingerprint.equals(verified.entry().fingerprint()), "Interaction registry differs from its actual authored source");
                Path factsPath = fixed(Path.of(verified.entry().sourceFacts().path()));
                byte[] factsRaw = trusted.readState(factsPath, LIMIT);
                Path entryPath = trusted.stateDirectory().resolve("evidence/interaction-source-registry").resolve(fingerprint + ".json");
                byte[] entryRaw = trusted.readState(entryPath, 65_536);
                if (!(v(review, "published") instanceof NullValue)) requireReference(o(review, "published"), entryPath, entryRaw);
                if (!(v(review, "canonical_source_facts") instanceof NullValue)) requireReference(o(review, "canonical_source_facts"), factsPath, factsRaw);
                ProjectionEvidenceGrant grant = new ProjectionEvidenceGrant(factsPath, factsRaw.length, sha(factsRaw), configured.sources().machineId(), ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
                if (!additions.contains(grant)) additions.add(grant);
                continue;
            }
            Path registry = trusted.stateDirectory().resolve("evidence/event-source-registry");
            Path entryPath = registry.resolve(fingerprint + ".json"); Path factsPath = registry.resolve("facts").resolve(fingerprint + ".json");
            byte[] entryRaw = trusted.readState(entryPath, 65_536); ObjectValue entry = RetainedJson.object(RetainedJson.parse(entryRaw));
            ObjectValue factsRef = o(entry, "source_facts"); require(factsRef != null && fixed(Path.of(requiredText(factsRef, "path"))).equals(factsPath), "published entry must bind canonical producer facts");
            byte[] factsRaw = trusted.readState(factsPath, LIMIT); require(eq(factsRef, "sha256", s(sha(factsRaw))), "published facts original SHA differs");
            ObjectValue facts = RetainedJson.object(RetainedJson.parse(factsRaw));
            ObjectValue publishedBinding = o(entry, "binding"); require(publishedBinding != null, "published binding required");
            Path sourcePath = fixed(Path.of(requiredText(entry, "source_path")));
            byte[] sourceRaw = trusted.read(sourcePath, 2_097_152, TrustedEventSourceContext.FileRole.SOURCE);
            String relative = trusted.stockGameDirectory().relativize(sourcePath).toString().replace('\\', '/');
            require(SourceReviewedEventConsumer.reviewStatus(before, trusted) == SourceReviewedEventConsumer.KnowledgeStatus.SOURCE_REVIEWED,
                    "actual current capture does not validate against the published source knowledge");
            OfflineEventSourceAnalyzer.Analysis actual = OfflineEventSourceAnalyzer.analyzeReviewedBinding(publishedBinding, before, sourcePath, relative, sourceRaw);
            require(actual.fingerprint().equals(fingerprint) && actual.binding().equals(publishedBinding) && actual.facts().equals(facts)
                    && eq(entry, "schema", s(SourceReviewedEventConsumer.SCHEMA)) && eq(entry, "fingerprint", s(fingerprint))
                    && eq(entry, "classification", s("offline-source-reviewed-user-first-rendered-policy"))
                    && eq(entry, "material_effects_verified", b(false)) && eq(entry, "registry_contract_accepted", b(false)), "actual source review differs from immutable published knowledge");
            if (!(v(review, "published") instanceof NullValue)) requireReference(o(review, "published"), entryPath, entryRaw);
            if (!(v(review, "canonical_source_facts") instanceof NullValue)) requireReference(o(review, "canonical_source_facts"), factsPath, factsRaw);
            ProjectionEvidenceGrant grant = new ProjectionEvidenceGrant(factsPath, factsRaw.length, sha(factsRaw), configured.sources().machineId(), ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
            if (!additions.contains(grant)) additions.add(grant);
        }
        // Unresolved incidents are retained in the original report and receive no grant.
        objects(report, "unresolved"); trusted.verifyCurrentRoots();
        OfflineScanSource.recheck(configured.incidentRoot(), configured.scanRoot(), manifestPin, originalScan);
        require(java.util.Arrays.equals(reportRaw, readWithin(configured.reviewRoot(), originalReport, LIMIT)), "Actual report changed during grant publication");
        return EvidenceGrantManifestPublisher.publish(configured.grantsManifest(), additions);
    }

    private static void requireReference(ObjectValue reference, Path path, byte[] raw) {
        require(reference != null && fixed(Path.of(requiredText(reference, "path"))).equals(path)
                && eq(reference, "sha256", s(sha(raw))), "original publication reference differs");
    }
    private static byte[] readIncident(Path root, ObjectValue incident, String stage) throws IOException {
        byte[] raw = readWithin(root, Path.of(requiredText(incident, stage)), LIMIT);
        require(eq(incident, stage + "_sha256", s(sha(raw))), "original incident source SHA differs"); return raw;
    }
    private static byte[] referenced(Path root, ObjectValue reference, int maximum) throws IOException {
        require(reference != null, "original file reference required"); byte[] raw = readWithin(root, Path.of(requiredText(reference, "path")), maximum);
        require(eq(reference, "sha256", s(sha(raw))), "original file reference SHA differs"); return raw;
    }
    private static byte[] readWithin(Path root, Path supplied, int maximum) throws IOException {
        Path path = fixed(supplied); require(path.startsWith(root) && !path.equals(root), "offline input escapes its fixed producer root");
        return EvidenceGrantManifestPublisher.readStable(path, maximum);
    }
    private static Path fixed(Path path) { require(path != null && path.isAbsolute(), "absolute fixed offline producer path required"); return path.normalize(); }
    private static String requiredText(ObjectValue row, String field) { String value = text(row, field); require(value != null && !value.isBlank(), "required original text: " + field); return value; }
}
