package org.xar.ck3.control.wave2.events.interactionregistry;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import static org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry.*;

/** Read-only filesystem adapter. Every successful lookup hashes actual source/GUI/facts again. */
public final class InteractionRegistryReader {
    private static final int MAX_SOURCE_BYTES = 2 * 1024 * 1024;
    private static final int MAX_ENTRIES = 128;
    private static final int MAX_DIRECTORY_ENTRIES = 1024;
    private static final String REGISTRY = "evidence/interaction-source-registry";
    private static final String GUI_RELATIVE = "gui/interaction_notification_window.gui";
    private final String machineId;

    public InteractionRegistryReader(String machineId) { stable(machineId); this.machineId = machineId; }
    /** Portable callers without a bound machine stay explicitly unknown; this is never runtime admission. */
    public InteractionRegistryReader() { this("unknown"); }

    public Result load(Roots roots, Lookup lookup) {
        return load(roots, lookup, null);
    }
    public Result load(TrustedEventSourceContext trusted, Lookup lookup) {
        java.util.Objects.requireNonNull(trusted);
        if (!machineId.equals(trusted.machineId())) throw new IllegalArgumentException("interaction source reader must use the trusted host identity");
        return load(new Roots(trusted.stateDirectory(), trusted.stockGameDirectory()), lookup, trusted);
    }
    private Result load(Roots roots, Lookup lookup, TrustedEventSourceContext trusted) {
        java.util.Objects.requireNonNull(roots); java.util.Objects.requireNonNull(lookup);
        if (trusted == null) return loadOptional(roots, lookup, null);
        requireFallbackSource(trusted, lookup);
        Result result = loadOptional(roots, lookup, trusted);
        requireFallbackSource(trusted, lookup);
        return result;
    }
    private Result loadOptional(Roots roots, Lookup lookup, TrustedEventSourceContext trusted) {
        Path directory = roots.stateRoot().resolve(REGISTRY);
        if (!Files.exists(directory, LinkOption.NOFOLLOW_LINKS)) { return new Unknown(UnknownReason.NO_MATCH, List.of()); }
        Path stateReal;
        Path gameReal;
        Path directoryReal;
        try {
            stateReal = trusted == null ? roots.stateRoot().toRealPath() : trusted.stateDirectory();
            gameReal = trusted == null ? roots.gameRoot().toRealPath() : trusted.stockGameDirectory();
            directoryReal = directory.toRealPath();
            if (!directoryReal.startsWith(stateReal)) { return new Unknown(UnknownReason.REGISTRY_UNAVAILABLE, List.of()); }
        } catch (IOException | UncheckedIOException | SecurityException error) { return new Unknown(UnknownReason.REGISTRY_UNAVAILABLE, List.of()); }
        List<Path> entries;
        if (trusted != null) {
            try { entries = trusted.interactionRegistryEntries(); }
            catch (TrustedEventSourceContext.UnavailableException optionalRegistry) {
                if (optionalRegistry.failureKind() != TrustedEventSourceContext.FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE) throw optionalRegistry;
                requireFallbackSource(trusted, lookup);
                return new Unknown(UnknownReason.REGISTRY_UNAVAILABLE, List.of());
            }
        } else try (var paths = Files.list(directory)) {
            List<Path> scanned = paths.limit(MAX_DIRECTORY_ENTRIES + 1L).toList();
            if (scanned.size() > MAX_DIRECTORY_ENTRIES) { return new Unknown(UnknownReason.RESOURCE_LIMIT, List.of()); }
            entries = scanned.stream().filter(path -> path.getFileName().toString().matches("[0-9a-f]{64}\\.json"))
                    .sorted(Comparator.comparing(path -> path.getFileName().toString())).toList();
        } catch (IOException | UncheckedIOException | SecurityException error) { return new Unknown(UnknownReason.REGISTRY_UNAVAILABLE, List.of()); }
        if (entries.size() > MAX_ENTRIES) { return new Unknown(UnknownReason.RESOURCE_LIMIT, List.of()); }
        List<RejectedEntry> rejected = new ArrayList<>();
        for (Path path : entries) {
            try {
                RawFile entryFile = readAuthorized(path, stateReal, InteractionRegistryCodec.MAX_ENTRY_BYTES, trusted, ReadRole.ENTRY);
                Entry entry = InteractionRegistryCodec.parseEntry(entryFile.raw());
                if (!entry.binding().definition().canonicalKey().equals(lookup.definition().canonicalKey())) { continue; }
                if (!entry.binding().build().equals(lookup.build()) || !entry.binding().definition().equals(lookup.definition())
                        || !entry.binding().guiSha256().equals(lookup.guiSha256())) { throw rejected(Rejection.LOOKUP_BINDING_MISMATCH); }
                String name = path.getFileName().toString();
                String fingerprint = name.substring(0, name.length() - 5);
                if (!entry.fingerprint().equals(fingerprint) || !InteractionRegistryCodec.fingerprint(entry.binding()).equals(fingerprint)) {
                    throw rejected(Rejection.FINGERPRINT_MISMATCH);
                }
                RawFile factsFile = readAuthorized(absolute(entry.sourceFacts().path()), stateReal, InteractionRegistryCodec.MAX_FACTS_BYTES, trusted, ReadRole.FACTS);
                RawFile sourceFile = readAuthorized(absolute(entry.paths().sourcePath()), gameReal, MAX_SOURCE_BYTES, trusted, ReadRole.SOURCE);
                RawFile guiFile = readAuthorized(absolute(entry.paths().guiPath()), gameReal, MAX_SOURCE_BYTES, trusted, ReadRole.GUI);
                if (!entryFile.path().getParent().equals(directoryReal) || trusted == null && !factsFile.path().startsWith(directoryReal.resolve("facts"))
                        || !sourceFile.path().startsWith(gameReal.resolve("common/character_interactions")) || !guiFile.path().startsWith(gameReal.resolve("gui"))) {
                    throw rejected(Rejection.PATH_OUTSIDE_ROOT);
                }
                if (!InteractionRegistryCodec.digest(factsFile.raw()).equals(entry.sourceFacts().sha256())
                        || !InteractionRegistryCodec.digest(sourceFile.raw()).equals(entry.binding().sourceSha256())
                        || !InteractionRegistryCodec.digest(guiFile.raw()).equals(entry.binding().guiSha256())) { throw rejected(Rejection.SOURCE_MISMATCH); }
                Facts facts = InteractionRegistryCodec.parseFacts(factsFile.raw());
                if (!facts.fingerprint().equals(fingerprint) || !facts.binding().equals(entry.binding()) || !facts.paths().equals(entry.paths())) {
                    throw rejected(Rejection.SOURCE_MISMATCH);
                }
                Path relative = Path.of(facts.sourceRelative());
                if (relative.isAbsolute() || !roots.gameRoot().resolve(relative).normalize().toRealPath().equals(sourceFile.path())
                        || !roots.gameRoot().resolve(GUI_RELATIVE).toRealPath().equals(guiFile.path())) { throw rejected(Rejection.PATH_OUTSIDE_ROOT); }
                // The files must still have the measured identities after every source and facts read.
                recheck(entryFile); recheck(factsFile); recheck(sourceFile); recheck(guiFile);
                Audit audit = new Audit(machineId, Instant.now().toString(), fingerprint, path.toAbsolutePath().normalize().toString(), InteractionRegistryCodec.digest(entryFile.raw()),
                        entry.binding().sourceSha256(), entry.binding().guiSha256());
                return new Known(new VerifiedReview(entry, facts, audit));
            } catch (RegistryRejected error) { retain(rejected, path, error.reason); }
            catch (TrustedEventSourceContext.UnavailableException optionalEntry) {
                if (optionalEntry.failureKind() != TrustedEventSourceContext.FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE) throw optionalEntry;
                // Revalidation supplements typed provenance; it never softens an already observed root failure.
                requireFallbackSource(trusted, lookup);
                retain(rejected, path, Rejection.FILE_UNAVAILABLE);
            }
            catch (IllegalArgumentException error) { retain(rejected, path, Rejection.INVALID_CONTRACT); }
            catch (IOException | SecurityException error) { retain(rejected, path, Rejection.FILE_UNAVAILABLE); }
        }
        return new Unknown(rejected.isEmpty() ? UnknownReason.NO_MATCH : UnknownReason.REJECTED_ENTRY, rejected);
    }

    private static void requireFallbackSource(TrustedEventSourceContext trusted, Lookup lookup) {
        trusted.requireInteractionGui(lookup.guiSha256());
    }
    private static Path absolute(String value) throws RegistryRejected {
        Path path = Path.of(value); if (!path.isAbsolute()) { throw rejected(Rejection.PATH_OUTSIDE_ROOT); } return path;
    }
    private enum ReadRole { ENTRY, FACTS, SOURCE, GUI }
    private static RawFile readAuthorized(Path path, Path root, int maximum, TrustedEventSourceContext trusted, ReadRole role)
            throws IOException, RegistryRejected {
        if (trusted == null) return read(path, root, maximum);
        byte[] admitted = switch (role) {
            case ENTRY -> trusted.readInteractionEntry(path);
            case FACTS -> trusted.readInteractionFacts(path);
            case SOURCE -> trusted.readInteractionSource(path, maximum);
            case GUI -> trusted.readGuiSource(path, maximum);
        };
        // A historical facts path is admitted only by its exact server grant above, never by this root argument.
        RawFile result = read(path, role == ReadRole.FACTS ? path.getRoot() : root, maximum, true);
        if (!java.util.Arrays.equals(admitted, result.raw())) throw rejected(Rejection.FILE_CHANGED);
        return result;
    }
    private static RawFile read(Path requested, Path approvedRoot, int maximum) throws IOException, RegistryRejected {
        return read(requested, approvedRoot, maximum, false);
    }
    private static RawFile read(Path requested, Path approvedRoot, int maximum, boolean witnessedRoot) throws IOException, RegistryRejected {
        if (Files.isSymbolicLink(requested)) { throw rejected(Rejection.PATH_OUTSIDE_ROOT); }
        // Trusted roots retain the provider's typed witness checks; leaf verification cannot reclassify root I/O.
        Path actual = requested.toRealPath(); Path root = witnessedRoot ? approvedRoot : approvedRoot.toRealPath();
        if (!actual.startsWith(root)) { throw rejected(Rejection.PATH_OUTSIDE_ROOT); }
        Stamp before = stamp(actual); if (before.bytes() > maximum) { throw rejected(Rejection.INVALID_CONTRACT); }
        byte[] raw;
        try (var stream = Files.newInputStream(actual, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS)) { raw = stream.readNBytes(maximum + 1); }
        if (raw.length == 0 || raw.length > maximum || raw.length != before.bytes()) { throw rejected(Rejection.INVALID_CONTRACT); }
        RawFile result = new RawFile(requested.toAbsolutePath().normalize(), actual, before, raw); recheck(result); return result;
    }
    private static Stamp stamp(Path path) throws IOException, RegistryRejected {
        BasicFileAttributes value = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        if (!value.isRegularFile() || value.isSymbolicLink() || value.fileKey() == null) { throw rejected(Rejection.FILE_UNAVAILABLE); }
        // The platform key is opaque and never converted to a JS number or interpreted as a FileID.
        return new Stamp(value.fileKey().toString(), value.size(), value.lastModifiedTime());
    }
    private static void recheck(RawFile file) throws IOException, RegistryRejected {
        if (Files.isSymbolicLink(file.requested()) || !file.requested().toRealPath().equals(file.path()) || !file.stamp().equals(stamp(file.path()))) {
            throw rejected(Rejection.FILE_CHANGED);
        }
    }
    private static void retain(List<RejectedEntry> target, Path path, Rejection reason) {
        if (target.size() < 8) { target.add(new RejectedEntry(path.getFileName().toString(), reason)); }
    }
    private static RegistryRejected rejected(Rejection reason) { return new RegistryRejected(reason); }
    private record Stamp(String opaqueKey, long bytes, FileTime modified) { }
    private record RawFile(Path requested, Path path, Stamp stamp, byte[] raw) { }
    private static final class RegistryRejected extends Exception {
        private static final long serialVersionUID = 1L;
        private final Rejection reason;
        RegistryRejected(Rejection reason) { super(reason.name()); this.reason = reason; }
    }
}

