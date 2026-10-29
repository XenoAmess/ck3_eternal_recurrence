package org.xar.ck3.control.service;

import jakarta.enterprise.context.ApplicationScoped;
import io.quarkus.runtime.Startup;
import jakarta.inject.Inject;
import java.util.ArrayList;
import java.util.List;
import java.util.ServiceLoader;
import java.nio.file.Path;
import java.net.URISyntaxException;
import java.util.Comparator;
import java.util.Optional;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.ProjectionArtifactAuthority;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputScope;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrants;
import org.xar.ck3.control.contracts.projection.ProjectionHostContext;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Single resident assembly root. Domain catalogs are supplied by the qualified application classpath. */
@ApplicationScoped
@Startup
public class ProjectionHost {
    private final ProjectionDispatcher dispatcher;
    private final List<CatalogOrigin> catalogs;
    private final ProjectionHostContext context;
    public record CatalogOrigin(String providerClass, String artifactPath,
            List<ProjectionDispatcher.OperationProfile> operations) {
        public CatalogOrigin { operations = List.copyOf(operations); }
    }
    @Inject public ProjectionHost(
            @ConfigProperty(name = "xar.projection.machine-id", defaultValue = "unknown") String expectedMachineId,
            @ConfigProperty(name = "xar.projection.event-source.state-root") Optional<String> stateRoot,
            @ConfigProperty(name = "xar.projection.event-source.stock-game-root") Optional<String> stockGameRoot,
            @ConfigProperty(name = "xar.projection.event-source.evidence-grants") Optional<String> evidenceManifest,
            @ConfigProperty(name = "xar.projection.artifact-input.scope-path") Optional<String> scopePath,
            @ConfigProperty(name = "xar.projection.artifact-input.scope-bytes") Optional<String> scopeBytes,
            @ConfigProperty(name = "xar.projection.artifact-input.scope-sha256") Optional<String> scopeSha256,
            @ConfigProperty(name = "xar.projection.capture-only", defaultValue = "false") boolean captureOnly) {
        this(loadContext(expectedMachineId, stateRoot, stockGameRoot, evidenceManifest, scopePath, scopeBytes, scopeSha256, captureOnly));
    }
    public ProjectionHost(String expectedMachineId, Optional<String> stateRoot, Optional<String> stockGameRoot, Optional<String> evidenceManifest) {
        this(expectedMachineId, stateRoot, stockGameRoot, evidenceManifest, Optional.empty(), Optional.empty(), Optional.empty(), false);
    }
    public ProjectionHost(ProjectionHostContext context) {
        this.context = java.util.Objects.requireNonNull(context);
        List<RegisteredProjection> ports = new ArrayList<>(); List<CatalogOrigin> origins = new ArrayList<>();
        ServiceLoader.load(ProjectionPortCatalog.class).forEach(catalog -> {
            List<RegisteredProjection> registered = List.copyOf(catalog.registrations(context)); ports.addAll(registered);
            List<ProjectionDispatcher.OperationProfile> profiles = registered.stream().map(port ->
                    new ProjectionDispatcher.OperationProfile(port.operation(), port.inputMaximumBytes(), port.outputMaximumBytes())).toList();
            origins.add(new CatalogOrigin(catalog.getClass().getName(), actualCodeSource(catalog.getClass()), profiles));
        });
        dispatcher = new ProjectionDispatcher(ports);
        catalogs = origins.stream().sorted(Comparator.comparing(CatalogOrigin::providerClass)).toList();
        context.artifactInputs().ifPresent(scope -> {
            if (scope instanceof ProjectionArtifactInputReader reader) reader.bindCatalogOwner(catalogs);
        });
    }
    public ProjectionHost(ProjectionDispatcher dispatcher) {
        this.dispatcher = java.util.Objects.requireNonNull(dispatcher); this.catalogs = List.of(); this.context = ProjectionHostContext.empty();
    }
    public ProjectionResult call(byte[] raw) { return dispatcher.dispatch(raw); }
    public List<ProjectionDispatcher.OperationProfile> profiles() { return dispatcher.profiles(); }
    public List<CatalogOrigin> catalogs() { return catalogs; }
    public ProjectionHostContext context() { return context; }
    public Optional<ProjectionArtifactAuthority.Active> artifactInputs() {
        if (context.artifactInputs().isEmpty()) return Optional.empty();
        if (context.artifactInputs().orElseThrow() instanceof ProjectionArtifactInputReader reader) return Optional.of(reader.current());
        throw new IllegalStateException("actual Root-configured artifact scope required for host proof");
    }
    private static ProjectionHostContext loadContext(String expectedMachineId, Optional<String> stateRoot,
            Optional<String> stockGameRoot, Optional<String> evidenceManifest, Optional<String> scopePath,
            Optional<String> scopeBytes, Optional<String> scopeSha256, boolean captureOnly) {
        Optional<ProjectionArtifactInputScope> artifacts = artifactScope(expectedMachineId, scopePath, scopeBytes, scopeSha256, captureOnly);
        if (stateRoot.isPresent() != stockGameRoot.isPresent()) {
            throw new IllegalArgumentException("event source state and stock game roots must be configured together");
        }
        if (stateRoot.isEmpty()) {
            if (evidenceManifest.isPresent()) { throw new IllegalArgumentException("evidence manifest requires fixed event source roots"); }
            return new ProjectionHostContext(Optional.empty(), artifacts);
        }
        String observedMachineId = WindowsJobProcess.currentMachineId();
        if (!observedMachineId.equals(expectedMachineId)) {
            throw new IllegalStateException("event source context actual machine differs from expected machine");
        }
        ProjectionEvidenceGrants grants = evidenceManifest.isPresent()
                ? new ProjectionEvidenceManifestReader(Path.of(evidenceManifest.orElseThrow()))
                : ProjectionEvidenceGrants.fixed(List.of());
        return new ProjectionHostContext(Optional.of(new EventSourceReadContext(observedMachineId,
                Path.of(stateRoot.orElseThrow()), Path.of(stockGameRoot.orElseThrow()), grants)), artifacts);
    }
    private static Optional<ProjectionArtifactInputScope> artifactScope(String machine, Optional<String> path,
            Optional<String> bytes, Optional<String> sha256, boolean captureOnly) {
        if (path.isEmpty() && bytes.isEmpty() && sha256.isEmpty()) return Optional.empty();
        if (captureOnly) throw new IllegalStateException("capture-only host cannot acquire the business artifact input scope");
        if (path.isEmpty() || bytes.isEmpty() || sha256.isEmpty() || !bytes.orElseThrow().matches("[1-9][0-9]{0,15}")) {
            throw new IllegalArgumentException("one exact Root scope reference is required");
        }
        var reference = new ExactRef(path.orElseThrow(), Long.parseLong(bytes.orElseThrow()), sha256.orElseThrow());
        return Optional.of(new ProjectionArtifactInputReader(reference, machine));
    }
    private static String actualCodeSource(Class<? extends ProjectionPortCatalog> provider) {
        var domain = provider.getProtectionDomain();
        if (domain == null || domain.getCodeSource() == null || domain.getCodeSource().getLocation() == null) {
            throw new IllegalStateException("projection catalog actual CodeSource unavailable: " + provider.getName());
        }
        try {
            var uri = domain.getCodeSource().getLocation().toURI();
            if (!"file".equalsIgnoreCase(uri.getScheme())) { throw new IllegalStateException("projection catalog CodeSource is not a file URI"); }
            return Path.of(uri).toAbsolutePath().normalize().toString();
        } catch (URISyntaxException error) { throw new IllegalStateException("invalid projection catalog CodeSource URI", error); }
    }
}
