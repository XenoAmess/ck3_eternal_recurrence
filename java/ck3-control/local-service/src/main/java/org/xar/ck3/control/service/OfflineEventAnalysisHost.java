package org.xar.ck3.control.service;

import io.quarkus.runtime.Startup;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Instance;
import org.xar.ck3.control.contracts.offline.BatchReviewCompletionPort;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding;
import jakarta.inject.Inject;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.OfflineMandatoryChoiceReviewProducer;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventBatchAnalyzer;
import static org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.*;

/** Assembly only. Existing domain producers own analysis, custody, idempotence and the single publication lock. */
@ApplicationScoped
@Startup
public class OfflineEventAnalysisHost {
    private static final Logger LOG = Logger.getLogger(OfflineEventAnalysisHost.class);
    private static final String LAUNCH = "ROOT-ACTUAL-GAME-LAUNCH.json";
    public record MandatoryScope(Path reviewRoot, Path grantsManifest) { }
    public record BatchScope(Path incidentRoot, Path knowledgeRoot, Path grantsManifest, Optional<Path> scanRoot) { }
    public record Settings(boolean enabled, boolean captureOnly, Optional<Path> grantsManifest, Optional<Path> incidentRoot, Optional<Path> knowledgeRoot, Optional<Path> scanRoot) {
        public Settings(boolean enabled, boolean captureOnly, Optional<Path> grantsManifest, Optional<Path> incidentRoot, Optional<Path> knowledgeRoot) {
            this(enabled, captureOnly, grantsManifest, incidentRoot, knowledgeRoot, Optional.empty());
        }
        public Settings(boolean enabled, Optional<Path> grantsManifest, Optional<Path> incidentRoot, Optional<Path> knowledgeRoot) {
            this(enabled, false, grantsManifest, incidentRoot, knowledgeRoot, Optional.empty());
        }
        public Settings {
            Objects.requireNonNull(grantsManifest); Objects.requireNonNull(incidentRoot); Objects.requireNonNull(knowledgeRoot); Objects.requireNonNull(scanRoot);
            grantsManifest.ifPresent(OfflineEventAnalysisHost::fixed); incidentRoot.ifPresent(OfflineEventAnalysisHost::fixed); knowledgeRoot.ifPresent(OfflineEventAnalysisHost::fixed);
            scanRoot.ifPresent(OfflineEventAnalysisHost::fixed);
            if (scanRoot.isPresent() && incidentRoot.isEmpty()) throw new IllegalArgumentException("fixed scan root requires the paired incident/knowledge roots");
            if (incidentRoot.isPresent() != knowledgeRoot.isPresent()) throw new IllegalArgumentException("offline incident and knowledge roots must be paired");
        }
    }
    private final Optional<EventSourceReadContext> sources;
    private final Optional<MandatoryScope> mandatory;
    private final Optional<BatchScope> batches;
    private final Optional<EvidenceGrantManifestPublisher.Publication> initialization;
    private final Optional<BatchReviewCompletionPort> completion;

    @Inject public OfflineEventAnalysisHost(ProjectionHost projections,
            @ConfigProperty(name = "xar.projection.offline.enabled", defaultValue = "false") boolean enabled,
            @ConfigProperty(name = "xar.projection.capture-only", defaultValue = "false") boolean captureOnly,
            @ConfigProperty(name = "xar.projection.event-source.evidence-grants") Optional<String> manifest,
            @ConfigProperty(name = "xar.projection.offline.incident-root") Optional<String> incidents,
            @ConfigProperty(name = "xar.projection.offline.knowledge-root") Optional<String> knowledge,
            @ConfigProperty(name = "xar.projection.offline.scan-root") Optional<String> scans,
            Instance<BatchReviewCompletionPort> completions) {
        this(projections.context().eventSources(), new Settings(enabled, captureOnly, manifest.map(Path::of), incidents.map(Path::of), knowledge.map(Path::of), scans.map(Path::of)),
                completions.isResolvable() ? Optional.of(completions.get()) : Optional.empty());
    }
    public OfflineEventAnalysisHost(Optional<EventSourceReadContext> configuredSources, Settings settings) {
        this(configuredSources, settings, Optional.empty());
    }
    public OfflineEventAnalysisHost(Optional<EventSourceReadContext> configuredSources, Settings settings, Optional<BatchReviewCompletionPort> completion) {
        Objects.requireNonNull(configuredSources); Objects.requireNonNull(settings); this.completion = Objects.requireNonNull(completion);
        if (settings.captureOnly() && settings.enabled()) throw new IllegalStateException("capture-only host cannot enable offline knowledge publication");
        if (!settings.enabled()) {
            sources = Optional.empty(); mandatory = Optional.empty(); batches = Optional.empty(); initialization = Optional.empty(); return;
        }
        EventSourceReadContext trusted = configuredSources.orElseThrow(() -> new IllegalStateException("offline analysis requires actual-machine-bound event source roots"));
        Path manifest = fixed(settings.grantsManifest().orElseThrow(() -> new IllegalStateException("offline analysis requires a fixed grants manifest")));
        MandatoryScope ui = new MandatoryScope(trusted.stateRoot().resolve("evidence/unknown-mandatory-choice-reviews"), manifest);
        // These original constructors validate fixed output scope before any initialization write.
        new OfflineMandatoryChoiceReviewProducer.Configuration(trusted, ui.reviewRoot(), manifest);
        Optional<BatchScope> batch = settings.incidentRoot().map(incident -> new BatchScope(fixed(incident), fixed(settings.knowledgeRoot().orElseThrow()), manifest, settings.scanRoot().map(OfflineEventAnalysisHost::fixed)));
        batch.ifPresent(scope -> new OfflineEventBatchAnalyzer.Configuration(trusted, scope.incidentRoot(), scope.knowledgeRoot(), manifest, scope.scanRoot()));
        try {
            // Explicit offline-enabled initialization uses the original single writer. Existing or malformed content is never replaced with empty.
            var published = EvidenceGrantManifestPublisher.publish(manifest, List.of());
            initialization = Optional.of(published);
            LOG.infof("offline_knowledge_init machine_id=%s observed_at_utc=%s path=%s bytes=%d sha256=%s grants=%d added=%d",
                    trusted.machineId(), Instant.now(), published.path(), published.bytes(), published.sha256(), published.grants(), published.added());
        } catch (IOException | RuntimeException failure) { throw new IllegalStateException("offline knowledge manifest initialization failed", failure); }
        sources = Optional.of(trusted); mandatory = Optional.of(ui); batches = batch;
    }
    public Optional<MandatoryScope> mandatoryScope() { return mandatory; }
    public Optional<BatchScope> batchScope() { return batches; }
    public Optional<EvidenceGrantManifestPublisher.Publication> initialization() { return initialization; }

    public CaptureResult capture(CaptureRequest request) throws IOException {
        var configured = uiConfiguration(request.launchRef());
        var captured = OfflineMandatoryChoiceReviewProducer.captureInputs(configured, pin(request.launchRef()));
        try {
            return new CaptureResult(request.batchId(), captured.sources().stream().map(OfflineEventAnalysisHost::reference).toList());
        } catch (IllegalArgumentException failure) { throw new IllegalStateException("invalid original offline capture output", failure); }
    }
    public ReviewResult review(ReviewRequest request) throws IOException {
        ExactRef launch = request.sourceRefs().stream().filter(ref -> LAUNCH.equals(Path.of(ref.path()).getFileName().toString()))
                .reduce((first, second) -> { throw new IllegalArgumentException("one captured original UI launch is required"); })
                .orElseThrow(() -> new IllegalArgumentException("captured UI source inventory lacks its original launch"));
        var configured = uiConfiguration(launch);
        var captured = new OfflineMandatoryChoiceReviewProducer.CapturedInputs(configured.incidentAttempt(), request.sourceRefs().stream().map(OfflineEventAnalysisHost::pin).toList());
        var result = OfflineMandatoryChoiceReviewProducer.reviewCaptured(configured, captured);
        try {
            if (!result.sources().equals(captured.sources())) throw new IllegalStateException("original offline review returned another captured inventory");
            List<Review> reviews = result.reviews().stream().map(row -> new Review(row.incidentId(), ReviewStatus.fromWire(row.status()),
                    new ExactRef(row.review().toString(), row.bytes(), row.sha256()))).toList();
            var published = result.grants();
            if (!published.path().equals(configured.grantsManifest())) throw new IllegalStateException("original offline publication escaped its fixed manifest");
            return new ReviewResult(request.batchId(), reviews, new Publication(new ExactRef(published.path().toString(), published.bytes(), published.sha256()), published.grants(), published.added()), request.sourceRefs());
        } catch (IllegalArgumentException failure) { throw new IllegalStateException("invalid original offline review output", failure); }
    }
    public byte[] batch(BatchRequest request) throws IOException {
        BatchScope scope = batches.orElseThrow(OfflineEventAnalysisHost::unavailable);
        EventSourceReadContext trusted = snapshot();
        var configured = new OfflineEventBatchAnalyzer.Configuration(trusted, scope.incidentRoot(), scope.knowledgeRoot(), scope.grantsManifest(), scope.scanRoot());
        var original = new OfflineEventBatchAnalyzer.Request(request.batchId(), request.manifestRef(), request.capturedRefs());
        var binding = OfflineEventBatchAnalyzer.validateInputs(configured, original);
        if (binding instanceof OfflineBatchBinding.ObservedScan && completion.isEmpty()) throw unavailable();
        var result = OfflineEventBatchAnalyzer.run(configured, original);
        try {
            if (!trusted.machineId().equals(result.machineId()) || !scope.grantsManifest().equals(result.grants().path())) {
                throw new IllegalStateException("original offline batch returned another fixed source context");
            }
            byte[] encoded = OfflineEventAnalysisWire.validateBatchResult(OfflineEventBatchAnalyzer.encode(result), request.batchId());
            if (binding instanceof OfflineBatchBinding.ObservedScan) completion.orElseThrow().complete(request, result.report());
            return encoded;
        }
        catch (IllegalArgumentException failure) { throw new IllegalStateException("invalid original offline batch output", failure); }
    }
    private OfflineMandatoryChoiceReviewProducer.Configuration uiConfiguration(ExactRef anchor) {
        MandatoryScope scope = mandatory.orElseThrow(OfflineEventAnalysisHost::unavailable);
        EventSourceReadContext trusted = snapshot(); Path launch = Path.of(anchor.path()).normalize();
        if (!LAUNCH.equals(launch.getFileName().toString()) || launch.getParent() == null) throw new IllegalArgumentException("original offline launch role required");
        Path attempt = launch.getParent(); Path current = trusted.stateRoot().getParent();
        boolean declared = trusted.evidenceGrants().stream().anyMatch(grant -> grant.role() == ProjectionEvidenceRole.UI_RECOVERY_LAUNCH
                && grant.path().equals(launch) && grant.bytes() == anchor.bytes() && grant.sha256().equals(anchor.sha256()));
        if (!attempt.equals(current) && !declared) throw unavailable();
        return new OfflineMandatoryChoiceReviewProducer.Configuration(trusted, scope.reviewRoot(), scope.grantsManifest(), attempt);
    }
    private EventSourceReadContext snapshot() {
        var trusted = sources.orElseThrow(OfflineEventAnalysisHost::unavailable);
        // Preserve original configured grants and take a fresh snapshot of the same fixed server publication.
        // Local registry discovery is already dynamic; this also preserves the actual origin machine when a
        // later/idempotent analysis republishes previously created facts rather than guessing "unknown".
        Path manifest = mandatory.orElseThrow(OfflineEventAnalysisHost::unavailable).grantsManifest();
        return new EventSourceReadContext(trusted.machineId(), trusted.stateRoot(), trusted.stockGameRoot(), () -> {
            var merged = new ArrayList<ProjectionEvidenceGrant>(trusted.evidenceGrants());
            try {
                for (var actual : ProjectionEvidenceCodec.decode(EvidenceGrantManifestPublisher.readStable(manifest, ProjectionEvidenceCodec.MAX_BYTES))) {
                    var old = merged.stream().filter(row -> row.path().equals(actual.path()) && row.role() == actual.role()).findFirst();
                    if (old.isPresent() && !old.orElseThrow().equals(actual)) throw new IOException("configured grant conflicts with actual fixed knowledge publication");
                    if (old.isEmpty()) merged.add(actual);
                }
                return ProjectionEvidenceCodec.validated(merged);
            } catch (IOException failure) { throw new UncheckedIOException("actual fixed offline knowledge publication unavailable", failure); }
        });
    }
    private static OfflineMandatoryChoiceReviewProducer.SourcePin pin(ExactRef ref) {
        return new OfflineMandatoryChoiceReviewProducer.SourcePin(Path.of(ref.path()), ref.bytes(), ref.sha256());
    }
    private static ExactRef reference(OfflineMandatoryChoiceReviewProducer.SourcePin ref) {
        return new ExactRef(ref.path().toString(), ref.bytes(), ref.sha256());
    }
    private static Path fixed(Path path) {
        if (!path.isAbsolute()) throw new IllegalArgumentException("absolute fixed offline path required");
        return path.normalize();
    }
    private static ProjectionProtocolException unavailable() {
        return new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "fixed offline producer scope or exact historical launch unavailable");
    }
}
