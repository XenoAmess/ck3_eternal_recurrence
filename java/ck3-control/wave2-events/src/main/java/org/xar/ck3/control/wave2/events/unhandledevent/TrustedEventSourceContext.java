package org.xar.ck3.control.wave2.events.unhandledevent;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;

/** Server-injected roots for read-only source review; no request field can enlarge these roots. */
public final class TrustedEventSourceContext {
    public enum FileRole { REGISTRY_ENTRY, FACTS, SOURCE, GUI, INTERACTION_SOURCE }
    public enum FailureKind { REQUIRED_SOURCE_UNAVAILABLE, OPTIONAL_EVIDENCE_UNAVAILABLE }
    public static final class UnavailableException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final FailureKind failureKind;
        // Existing and unclassified failures remain hard failures.
        UnavailableException(String message, Throwable cause) { this(FailureKind.REQUIRED_SOURCE_UNAVAILABLE, message, cause); }
        private UnavailableException(FailureKind failureKind, String message, Throwable cause) {
            super(message, cause); this.failureKind = Objects.requireNonNull(failureKind);
        }
        public FailureKind failureKind() { return failureKind; }
    }
    private record DirectoryWitness(Path path, BasicFileAttributes identity) { }
    private final String machineId;
    private final DirectoryWitness state;
    private final DirectoryWitness stock;
    private final List<ProjectionEvidenceGrant> grants;

    private TrustedEventSourceContext(String machineId, DirectoryWitness state, DirectoryWitness stock,
            List<ProjectionEvidenceGrant> grants) {
        this.machineId = machineId; this.state = state; this.stock = stock; this.grants = List.copyOf(grants);
    }

    /** The host supplies its independently observed stable machine identity, never a payload assertion. */
    public static TrustedEventSourceContext open(String machineId, Path stateRoot, Path stockGameRoot) {
        return open(new EventSourceReadContext(machineId, stateRoot, stockGameRoot));
    }

    /** Takes one immutable server grant snapshot for this projection; never consults caller JSON. */
    public static TrustedEventSourceContext openEvidence(EventSourceReadContext configured) {
        try {
            Objects.requireNonNull(configured, "configured read context");
            List<ProjectionEvidenceGrant> snapshot = List.copyOf(configured.evidenceGrants());
            return new TrustedEventSourceContext(configured.machineId(), root(configured.stateRoot()), root(configured.stockGameRoot()), snapshot);
        } catch (IOException | IllegalArgumentException error) {
            throw new UnavailableException("configured event source roots are unavailable", error);
        }
    }

    /** Full event review additionally binds the five already reviewed stock source/GUI inputs. */
    public static TrustedEventSourceContext open(EventSourceReadContext configured) {
        TrustedEventSourceContext context = openEvidence(configured);
        context.verifyCurrentRoots();
        return context;
    }
    public String machineId() { return machineId; }
    public Path stateDirectory() { return state.path(); }
    public Path stockGameDirectory() { return stock.path(); }
    /** The exact immutable snapshot already taken by open; does not refresh server permissions mid-projection. */
    public List<ProjectionEvidenceGrant> evidenceGrantsSnapshot() { return grants; }

    public byte[] readInteractionSource(Path path, int maximum) { return readRole(path, maximum, FileRole.INTERACTION_SOURCE); }
    public byte[] readGuiSource(Path path, int maximum) { return readRole(path, maximum, FileRole.GUI); }
    /** All optional registry results still require this exact GUI and the original root witnesses. */
    public void requireInteractionGui(String expectedSha256) {
        if (expectedSha256 == null || !expectedSha256.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("exact interaction GUI SHA required");
        byte[] gui = readGuiSource(stock.path().resolve("gui/interaction_notification_window.gui"), 2_097_152);
        if (!SourceReviewJson.sha(gui).equals(expectedSha256)) throw new UnavailableException("required interaction GUI source changed", null);
    }
    public byte[] readInteractionEntry(Path supplied) {
        Path path = absolute(supplied); Path canonical = state.path().resolve("evidence/interaction-source-registry");
        if (!canonical.equals(path.getParent()) || !path.getFileName().toString().matches("[0-9a-f]{64}\\.json")) {
            throw new UnavailableException(FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE, "canonical interaction entry required", null);
        }
        return readState(path, 65_536);
    }
    public byte[] readInteractionFacts(Path supplied) {
        Path path = absolute(supplied); Path canonical = state.path().resolve("evidence/interaction-source-registry/facts");
        if (canonical.equals(path.getParent()) && path.getFileName().toString().matches("[0-9a-f]{64}\\.json")) return readState(path, 1_048_576);
        return readDeclared(path, 1_048_576, ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
    }
    public List<Path> interactionRegistryEntries() {
        try { return registryEntries("evidence/interaction-source-registry"); }
        catch (IOException error) { throw new UnavailableException(FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE, "configured interaction registry unavailable", error); }
    }
    private byte[] readRole(Path path, int maximum, FileRole role) {
        try { return read(path, maximum, role); }
        catch (IOException | IllegalArgumentException error) {
            FailureKind kind = role == FileRole.INTERACTION_SOURCE ? FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE : FailureKind.REQUIRED_SOURCE_UNAVAILABLE;
            throw new UnavailableException(kind, "configured source evidence unavailable", error);
        }
    }

    /** Reads only beneath the fixed state root; does not imply any native or current-machine qualification. */
    public byte[] readState(Path supplied, int maximum) {
        try {
            Path path = absolute(supplied);
            if (!path.startsWith(state.path()) || path.equals(state.path())) throw new IOException("read escapes the fixed state root");
            return stableRead(path, maximum, state.path());
        } catch (IOException | IllegalArgumentException error) {
            throw new UnavailableException(FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE, "configured state evidence unavailable", error);
        }
    }

    /** A grant is an exact server declaration, not a broad root nor a current-machine assertion. */
    public ProjectionEvidenceGrant declaredGrant(Path supplied, ProjectionEvidenceRole role) {
        Path path = absolute(supplied);
        return grants.stream().filter(grant -> grant.path().equals(path) && grant.role() == role).findFirst()
                .orElseThrow(() -> new UnavailableException(FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE, "required exact evidence grant unavailable", null));
    }

    /** Rechecks the exact server pin on every read; callers still validate their receipt's own declarations. */
    public byte[] readDeclared(Path supplied, int maximum, ProjectionEvidenceRole role) {
        ProjectionEvidenceGrant grant = declaredGrant(supplied, Objects.requireNonNull(role, "evidence role"));
        try {
            if (maximum < 1 || grant.bytes() > maximum) throw new IOException("declared evidence exceeds its role bound");
            byte[] raw = stableRead(grant.path(), maximum, grant.path().getRoot());
            if (raw.length != grant.bytes() || !SourceReviewJson.sha(raw).equals(grant.sha256())) {
                throw new IOException("actual evidence differs from its exact server pin");
            }
            return raw;
        } catch (IOException | IllegalArgumentException error) {
            throw new UnavailableException(FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE, "declared evidence changed or unavailable", error);
        }
    }

    private static void verifyRequired(DirectoryWitness witness) {
        try { verify(witness); }
        catch (IOException | IllegalArgumentException failure) {
            throw new UnavailableException("configured source root identity changed or unavailable", failure);
        }
    }
    private void verifyParent(DirectoryWitness witness) throws IOException {
        if (witness.path().equals(state.path())) verifyRequired(state);
        else if (witness.path().equals(stock.path())) verifyRequired(stock);
        else verify(witness);
    }
    private List<DirectoryWitness> sourceParents(Path root, Path parent) throws IOException {
        List<DirectoryWitness> result = new ArrayList<>(); Path cursor = root;
        result.add(sourceDirectory(cursor));
        for (Path part : root.relativize(parent)) { cursor = cursor.resolve(part); result.add(sourceDirectory(cursor)); }
        return List.copyOf(result);
    }
    private DirectoryWitness sourceDirectory(Path path) throws IOException {
        if (path.equals(state.path())) { verifyRequired(state); return state; }
        if (path.equals(stock.path())) { verifyRequired(stock); return stock; }
        return directory(path);
    }
    private static Path absolute(Path supplied) {
        if (supplied == null || !supplied.isAbsolute()) throw new UnavailableException("absolute evidence path required", null);
        return supplied.normalize();
    }

    private byte[] stableRead(Path path, int maximum, Path permittedRoot) throws IOException {
        verifyRequired(state); verifyRequired(stock);
        List<DirectoryWitness> witnesses = sourceParents(permittedRoot, path.getParent());
        byte[] raw = SourceReviewedEventConsumer.read(path, maximum);
        for (DirectoryWitness witness : witnesses) verifyParent(witness);
        verifyRequired(state); verifyRequired(stock);
        if (!path.toRealPath().equals(path)) throw new IOException("evidence resolves through a path alias");
        return raw;
    }

    public void verifyCurrentRoots() {
        try {
            verifyRequired(state); verifyRequired(stock);
            for (Map.Entry<String, String> pin : ReviewedLetterSourceRebind.installedSourceHashes().entrySet()) {
                FileRole role = pin.getKey().startsWith("gui/") ? FileRole.GUI : FileRole.SOURCE;
                byte[] raw = read(stock.path().resolve(pin.getKey()), 2_097_152, role);
                if (!SourceReviewJson.sha(raw).equals(pin.getValue())) {
                    throw new IOException("configured stock source/GUI differs from the existing .4 review");
                }
            }
        } catch (IOException | IllegalArgumentException error) {
            throw new UnavailableException("trusted event source context changed or is unavailable", error);
        }
    }

    void requireBuild(String build) {
        if (!"1.20.0.4".equals(build)) throw new IllegalArgumentException("configured event source context only binds reviewed .4 source inputs");
    }

    byte[] read(Path supplied, int maximum, FileRole role) throws IOException {
        Objects.requireNonNull(role, "file role");
        Path path = Objects.requireNonNull(supplied, "source path").toAbsolutePath().normalize();
        Path permitted = switch (role) {
            case REGISTRY_ENTRY -> state.path().resolve("evidence/event-source-registry");
            case FACTS -> state.path().resolve("evidence/event-source-registry/facts");
            case SOURCE -> stock.path().resolve("events");
            case GUI -> stock.path().resolve("gui");
            case INTERACTION_SOURCE -> stock.path().resolve("common/character_interactions");
        };
        if (role == FileRole.FACTS && !path.startsWith(permitted)) {
            return readDeclared(path, maximum, ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        }
        if (!path.startsWith(permitted) || path.equals(permitted)) throw new IOException("event source read escapes its configured role root");
        if ((role == FileRole.REGISTRY_ENTRY || role == FileRole.FACTS)
                && (!path.getParent().equals(permitted) || !path.getFileName().toString().matches("[0-9a-f]{64}\\.json"))) {
            throw new IOException("event registry/facts path is outside the canonical entry layout");
        }
        if ((role == FileRole.SOURCE || role == FileRole.INTERACTION_SOURCE) && !path.getFileName().toString().endsWith(".txt")) throw new IOException("source text path required");
        if (role == FileRole.GUI && !path.getFileName().toString().endsWith(".gui")) throw new IOException("event GUI source path required");
        Path configured = role == FileRole.REGISTRY_ENTRY || role == FileRole.FACTS ? state.path() : stock.path();
        verifyRequired(state); verifyRequired(stock);
        List<DirectoryWitness> parents = sourceParents(configured, path.getParent());
        byte[] bytes = SourceReviewedEventConsumer.read(path, maximum);
        for (DirectoryWitness parent : parents) verifyParent(parent);
        verifyRequired(state); verifyRequired(stock);
        if (!path.toRealPath().equals(path)) throw new IOException("event source file resolves through a path alias");
        return bytes;
    }

    List<Path> registryEntries() throws IOException {
        return registryEntries("evidence/event-source-registry");
    }
    private List<Path> registryEntries(String fixedRelative) throws IOException {
        verifyRequired(state); verifyRequired(stock);
        Path directory = state.path().resolve(fixedRelative);
        Path cursor = state.path();
        List<DirectoryWitness> witnesses = new ArrayList<>(); witnesses.add(state);
        for (Path part : state.path().relativize(directory)) {
            cursor = cursor.resolve(part);
            if (!Files.exists(cursor, LinkOption.NOFOLLOW_LINKS)) return List.of();
            witnesses.add(directory(cursor));
        }
        List<Path> result = SourceReviewedEventConsumer.registryEntries(directory);
        for (DirectoryWitness witness : witnesses) verifyParent(witness);
        return result;
    }

    private static DirectoryWitness root(Path supplied) throws IOException {
        if (supplied == null || !supplied.isAbsolute()) throw new IOException("absolute configured event source root required");
        Path path = supplied.toAbsolutePath().normalize();
        List<DirectoryWitness> ancestors = parents(path.getRoot(), path);
        for (DirectoryWitness ancestor : ancestors) verify(ancestor);
        return directory(path);
    }
    private static List<DirectoryWitness> parents(Path root, Path parent) throws IOException {
        List<DirectoryWitness> result = new ArrayList<>(); Path cursor = root;
        result.add(directory(cursor));
        for (Path part : root.relativize(parent)) { cursor = cursor.resolve(part); result.add(directory(cursor)); }
        return List.copyOf(result);
    }
    private static DirectoryWitness directory(Path path) throws IOException {
        BasicFileAttributes identity = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        if (!identity.isDirectory() || identity.isSymbolicLink() || identity.fileKey() == null || !path.toRealPath().equals(path)) {
            throw new IOException("identity-bearing directory without symlink/junction aliases required: " + path
                + "; directory=" + identity.isDirectory() + "; symbolicLink=" + identity.isSymbolicLink()
                + "; fileKey=" + identity.fileKey() + "; realPath=" + path.toRealPath());
        }
        return new DirectoryWitness(path, identity);
    }
    private static void verify(DirectoryWitness witness) throws IOException {
        DirectoryWitness current = directory(witness.path());
        if (!Objects.equals(witness.identity().fileKey(), current.identity().fileKey())) {
            throw new IOException("configured event source directory identity changed");
        }
    }
}

