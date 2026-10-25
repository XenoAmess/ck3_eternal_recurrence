package org.xar.ck3.rrf;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.rrf.Contracts.FileEntry;
import org.xar.ck3.rrf.Contracts.Manifest;
import org.xar.ck3.rrf.Contracts.Provenance;
import org.xar.ck3.rrf.Contracts.ProvenanceKind;
import org.xar.ck3.rrf.Contracts.ReleaseIdentity;

/** Explicit allowlist build. New outputs only; no recursive deletion, source-directory copy or private runtime runner. */
public final class ReleaseBuilder {
    public record BuildResult(String staging, String manifest, int files, String manifestSha256) { }
    public record Verification(int files, String version, String gitSha, String gitTag, String workshopItemId) { }
    public BuildResult build(Path source, Path output, ReleaseIdentity identity, Provenance provenance) throws IOException {
        ContentValidator.validate(source);
        ContentValidator.RuntimeProduct product = ContentValidator.product(source);
        Path input = source.toAbsolutePath().normalize(); Path staging = output.toAbsolutePath().normalize();
        if (input.startsWith(staging) || staging.startsWith(input)) throw new IllegalArgumentException("staging and source must be disjoint");
        Path manifestPath = staging.resolveSibling(staging.getFileName() + ".manifest.json");
        if (Files.exists(staging) || Files.exists(manifestPath)) throw new IllegalArgumentException("output exists; use a new attempt path");
        // Check all contract arguments before materializing staging.
        if (identity == null || provenance == null) throw new IllegalArgumentException("release identity/provenance required");
        if (provenance.kind() == ProvenanceKind.OBSERVED_MACHINE) {
            verifyGitTag(source, identity);
            if (!gitRevision(source, "HEAD").equals(identity.gitSha())) throw new IllegalArgumentException("release revision differs from source HEAD");
        }
        Files.createDirectories(staging.getParent()); Files.createDirectory(staging);
        List<FileEntry> entries = new ArrayList<>();
        for (String relative : product.files()) {
            byte[] bytes = Files.readAllBytes(source.resolve(relative)); Path target = staging.resolve(relative);
            Files.createDirectories(target.getParent()); Files.write(target, bytes, StandardOpenOption.CREATE_NEW);
            entries.add(new FileEntry(relative, bytes.length, sha256(bytes)));
        }
        Manifest manifest = new Manifest(2, identity.workshopItemId(), identity.gitTag(), identity.gitSha(), product.product().productId(), product.product().version(), provenance, entries);
        byte[] bytes = Json.write(manifest); Files.write(manifestPath, bytes, StandardOpenOption.CREATE_NEW);
        verify(source, staging, manifestPath);
        return new BuildResult(staging.toString(), manifestPath.toString(), entries.size(), sha256(bytes));
    }
    public Verification verify(Path source, Path staging, Path manifestPath) throws IOException {
        ContentValidator.RuntimeProduct product = ContentValidator.product(source);
        Manifest manifest = Json.read(Files.readAllBytes(manifestPath), Manifest.class);
        if (manifest.provenance().kind() == ProvenanceKind.OBSERVED_MACHINE) verifyGitTag(source, new ReleaseIdentity(manifest.workshopItemId(), manifest.gitTag(), manifest.gitSha()));
        if (!manifest.productId().equals(product.product().productId()) || !manifest.version().equals(product.product().version())) throw new IllegalArgumentException("manifest product/version mismatch");
        if (!manifest.files().stream().map(FileEntry::path).toList().equals(product.files())) throw new IllegalArgumentException("manifest differs from product allowlist");
        if (!ContentValidator.inventory(staging, true).keySet().equals(Set.copyOf(product.files()))) throw new IllegalArgumentException("extra/missing staging payload");
        for (FileEntry entry : manifest.files()) {
            byte[] bytes = Files.readAllBytes(staging.resolve(entry.path()));
            if (entry.size() != bytes.length || !entry.sha256().equals(sha256(bytes))) throw new IllegalArgumentException("staging content mismatch: " + entry.path());
            if (!MessageDigest.isEqual(bytes, Files.readAllBytes(source.resolve(entry.path())))) throw new IllegalArgumentException("staging differs from source: " + entry.path());
        }
        ContentValidator.validateTree(staging, product);
        return new Verification(manifest.files().size(), manifest.version(), manifest.gitSha(), manifest.gitTag(), manifest.workshopItemId());
    }
    private static void verifyGitTag(Path source, ReleaseIdentity identity) throws IOException {
        if (!gitRevision(source, "refs/tags/" + identity.gitTag() + "^{commit}").equals(identity.gitSha())) throw new IllegalArgumentException("release tag does not resolve to explicit revision");
    }
    private static String gitRevision(Path source, String reference) throws IOException {
        Process process = new ProcessBuilder("git", "-C", source.toString(), "rev-parse", "--verify", reference).redirectErrorStream(true).start();
        try {
            if (!process.waitFor(10, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("release Git identity lookup timed out"); }
            byte[] bytes = process.getInputStream().readNBytes(4097);
            String value = new String(bytes, StandardCharsets.UTF_8).strip();
            if (bytes.length > 4096 || process.exitValue() != 0 || !value.matches("[a-f0-9]{40}")) throw new IllegalArgumentException("release Git reference unavailable: " + reference);
            return value;
        } catch (InterruptedException error) {
            process.destroyForcibly(); Thread.currentThread().interrupt(); throw new IOException("release Git identity lookup interrupted", error);
        }
    }
    public static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }
}
