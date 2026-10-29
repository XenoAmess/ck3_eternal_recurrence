package org.xar.ck3.control.service.root;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.zip.CRC32;
import org.apache.commons.compress.archivers.zip.UnsupportedZipFeatureException;
import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;
import org.apache.commons.compress.archivers.zip.ZipFile;
import org.tukaani.xz.LZMAInputStream;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.SharedSourceFiles.DirectoryIdentity;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.TextRules;

/** Sole Java migration of ck3_save_artifacts.py. Read-only format inspection is never a SAVE/restore permit. */
public final class RootSaveArtifactInspector {
    public static final String SCHEMA = "xar.ck3.save-artifacts/v1";
    public static final int MAX_SAVE_ARTIFACTS = 512;
    public static final int MAX_REPORTED_ZIP_MEMBERS = 128;
    public record FileFacts(String name, String relativePath, long bytes, String sha256) {
        public FileFacts {
            Objects.requireNonNull(name); Objects.requireNonNull(relativePath); StrictJson.safe(bytes, 0);
            StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "full original save digest required");
        }
    }
    public sealed interface Artifact permits ZipArtifact, OtherArtifact { FileFacts file(); }
    public record Member(String name, long bytes, long compressedBytes, String crc32, int compression, int flags) {
        public Member {
            Objects.requireNonNull(name); StrictJson.safe(bytes, 0); StrictJson.safe(compressedBytes, 0);
            StrictJson.require(crc32 != null && crc32.matches("[0-9a-f]{8}") && compression >= 0 && compression <= 65535
                    && flags >= 0 && flags <= 65535, "exact ZIP central member facts required");
        }
    }
    public record ZipArtifact(FileFacts file, boolean zipValid, String badMember, boolean hasGamestate,
            int memberCount, List<Member> members) implements Artifact {
        public ZipArtifact {
            Objects.requireNonNull(file); members = List.copyOf(members);
            StrictJson.require(memberCount >= 0 && members.size() == Math.min(memberCount, MAX_REPORTED_ZIP_MEMBERS)
                    && zipValid == (badMember == null), "complete ZIP integrity and bounded original report required");
        }
        public boolean integrityOk() { return zipValid && hasGamestate; }
        public boolean membersTruncated() { return memberCount > members.size(); }
    }
    public enum RawHeader { TEXT, BINARY }
    public record OtherArtifact(FileFacts file, RawHeader rawHeader, String formatProbeError) implements Artifact {
        public OtherArtifact { Objects.requireNonNull(file); Objects.requireNonNull(formatProbeError); }
    }
    public record Response(Path profileDirectory, Path saveRoot, List<Artifact> artifacts) {
        public Response {
            Objects.requireNonNull(profileDirectory); Objects.requireNonNull(saveRoot); artifacts = List.copyOf(artifacts);
            StrictJson.require(profileDirectory.isAbsolute() && profileDirectory.normalize().equals(profileDirectory)
                    && saveRoot.equals(profileDirectory.resolve("save games")) && artifacts.size() <= MAX_SAVE_ARTIFACTS,
                    "one exact configured profile and bounded save inventory required");
        }
    }
    private final Path profile;
    private final DirectoryIdentity profileIdentity;
    private final TextRules textRules;

    /** Package-only filesystem leaf. Production obtains this path solely from the retained actual plan Prepared. */
    RootSaveArtifactInspector(Path actualProfile, TextRules actualOriginalTextRules) throws IOException {
        profile = Objects.requireNonNull(actualProfile).toAbsolutePath().normalize();
        textRules = Objects.requireNonNull(actualOriginalTextRules);
        SharedSourceFiles.plainAncestors(profile); profileIdentity = SharedSourceFiles.nativeDirectory(profile);
    }
    void requireCurrent() throws IOException {
        SharedSourceFiles.plainAncestors(profile);
        if (!profileIdentity.equals(SharedSourceFiles.nativeDirectory(profile)))
            throw new IOException("configured SAVE profile native identity changed");
    }
    Response inspect() throws IOException {
        requireCurrent(); Path saveRoot = profile.resolve("save games");
        DirectoryIdentity saveIdentity = Files.isDirectory(saveRoot)
                ? SharedSourceFiles.nativeDirectory(saveRoot) : null;
        List<Path> candidates = candidates(saveRoot); var artifacts = new ArrayList<Artifact>();
        var originals = new ArrayList<Witness>();
        for (Path candidate : candidates) {
            Witness witness = SharedSourceFiles.observe(candidate);
            artifacts.add(inspectSelected(candidate, witness)); originals.add(witness);
        }
        requireCurrent();
        if (!candidates.equals(candidates(saveRoot))) throw new IOException("SAVE inventory changed during inspection");
        if (saveIdentity == null ? Files.isDirectory(saveRoot)
                : !saveIdentity.equals(SharedSourceFiles.nativeDirectory(saveRoot)))
            throw new IOException("SAVE directory native identity changed during inspection");
        for (Witness original : originals) SharedSourceFiles.assertUnchanged(original);
        return new Response(profile, saveRoot, artifacts);
    }
    private List<Path> candidates(Path saveRoot) throws IOException {
        var candidates = new ArrayList<Path>(); Path last = profile.resolve("last_save.ck3");
        if (Files.isRegularFile(last) || Files.isSymbolicLink(last)) candidates.add(last);
        if (Files.isDirectory(saveRoot)) {
            SharedSourceFiles.nativeDirectory(saveRoot);
            try (var paths = Files.newDirectoryStream(saveRoot)) {
                for (Path path : paths) {
                    String name = path.getFileName().toString();
                    if (name.length() >= 4 && name.regionMatches(true, name.length() - 4, ".ck3", 0, 4)) {
                        candidates.add(path);
                        if (candidates.size() > MAX_SAVE_ARTIFACTS) throw new IOException("configured profile contains more than512 CK3 saves");
                    }
                }
            }
            int first = !candidates.isEmpty() && candidates.getFirst().equals(last) ? 1 : 0;
            candidates.subList(first, candidates.size()).sort(Comparator.comparing(
                    path -> textRules.fold(path.getFileName().toString()), RootSaveArtifactInspector::codePointCompare));
        }
        if (candidates.size() > MAX_SAVE_ARTIFACTS) throw new IOException("configured profile contains more than512 CK3 saves");
        return List.copyOf(candidates);
    }
    private static int codePointCompare(String left, String right) {
        int a = 0, b = 0;
        while (a < left.length() && b < right.length()) {
            int x = left.codePointAt(a), y = right.codePointAt(b);
            if (x != y) return Integer.compare(x, y); a += Character.charCount(x); b += Character.charCount(y);
        }
        return Integer.compare(left.length() - a, right.length() - b);
    }
    Artifact inspectSelected(Path candidate, Witness witness) throws IOException {
        requireCurrent();
        Path normalized = candidate.toAbsolutePath().normalize();
        if (!normalized.startsWith(profile) || !normalized.getParent().equals(profile)
                && !normalized.getParent().equals(profile.resolve("save games")))
            throw new IOException("SAVE artifact escapes the actual configured profile");
        if (!normalized.equals(Path.of(witness.source().path()).toAbsolutePath().normalize()))
            throw new IOException("selected SAVE and exact original witness path differ");
        var source = witness.source(); FileFacts file = new FileFacts(candidate.getFileName().toString(),
                profile.relativize(candidate).toString().replace('\\', '/'), source.bytes(), source.sha256());
        ZipFile archive;
        try { archive = ZipFile.builder().setPath(candidate).setCharset(java.nio.charset.Charset.forName("CP437"))
                .setUseUnicodeExtraFields(false).get(); }
        catch (IOException invalidZip) {
            byte[] header;
            try (InputStream input = Files.newInputStream(candidate)) { header = input.readNBytes(96); }
            OtherArtifact result = new OtherArtifact(file, rawHeader(header),
                    invalidZip instanceof java.nio.file.AccessDeniedException ? "PermissionError" : "BadZipFile");
            SharedSourceFiles.assertUnchanged(witness); return result;
        }
        try (archive) {
            var ordered = new ArrayList<ZipArchiveEntry>(); var reported = new ArrayList<Member>();
            var lastNamed = new LinkedHashMap<String, ZipArchiveEntry>(); boolean gamestate = false;
            var entries = archive.getEntries();
            while (entries.hasMoreElements()) {
                ZipArchiveEntry entry = entries.nextElement(); ordered.add(entry); lastNamed.put(entry.getName(), entry);
                gamestate |= entry.getName().equals("gamestate");
                if (reported.size() < MAX_REPORTED_ZIP_MEMBERS) reported.add(new Member(entry.getName(), entry.getSize(),
                        entry.getCompressedSize(), "%08x".formatted(entry.getCrc()), entry.getMethod(), entry.getRawFlag()));
            }
            String bad = null; byte[] buffer = new byte[1 << 20];
            for (ZipArchiveEntry declaration : ordered) {
                // Original Python testzip opens each declared NAME; duplicate names therefore read their final member.
                ZipArchiveEntry entry = lastNamed.get(declaration.getName());
                if (entry.getGeneralPurposeBit().usesEncryption()) throw new IOException("encrypted SAVE ZIP requires an unavailable original password");
                CRC32 crc = new CRC32(); long count = 0;
                try (InputStream input = memberStream(archive, entry)) {
                    for (int size; (size = input.read(buffer)) != -1;) {
                        if (Thread.currentThread().isInterrupted()) throw new java.io.InterruptedIOException("SAVE inspection interrupted");
                        crc.update(buffer, 0, size); count = Math.addExact(count, size);
                        if (count > entry.getSize()) break;
                    }
                } catch (UnsupportedZipFeatureException unsupported) { throw new IOException("original SAVE compression unavailable", unsupported); }
                catch (java.io.InterruptedIOException cancelled) { throw cancelled; }
                catch (IOException damaged) { bad = declaration.getName(); break; }
                if (crc.getValue() != entry.getCrc() || count != entry.getSize()) { bad = declaration.getName(); break; }
            }
            SharedSourceFiles.assertUnchanged(witness);
            return new ZipArtifact(file, bad == null, bad, gamestate, ordered.size(), reported);
        }
    }
    private static InputStream memberStream(ZipFile archive, ZipArchiveEntry entry) throws IOException {
        if (entry.getMethod() != 14) return archive.getInputStream(entry);
        InputStream raw = new BufferedInputStream(archive.getRawInputStream(entry));
        try {
            byte[] prefix = raw.readNBytes(4);
            if (prefix.length != 4 || (Byte.toUnsignedInt(prefix[2]) | Byte.toUnsignedInt(prefix[3]) << 8) != 5)
                throw new IOException("invalid original ZIP LZMA property header");
            byte[] properties = raw.readNBytes(5); if (properties.length != 5) throw new IOException("truncated ZIP LZMA properties");
            long dictionary = Integer.toUnsignedLong(java.nio.ByteBuffer.wrap(properties, 1, 4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt());
            if (dictionary > LZMAInputStream.DICT_SIZE_MAX) throw new IOException("ZIP LZMA dictionary exceeds real Java codec capacity");
            return new LZMAInputStream(raw, (entry.getRawFlag() & 2) != 0 ? -1 : entry.getSize(), properties[0], (int) dictionary);
        } catch (IOException | RuntimeException failed) { raw.close(); throw failed; }
    }
    private static RawHeader rawHeader(byte[] header) {
        int index = 0; if (header.length < 4 || header[index++] != 'S' || header[index++] != 'A' || header[index++] != 'V') return null;
        int digits = index;
        while (index < header.length && (header[index] >= '0' && header[index] <= '9' || header[index] >= 'A' && header[index] <= 'F'
                || header[index] >= 'a' && header[index] <= 'f')) index++;
        if (index == digits) return null; if (index < header.length && header[index] == '\r') index++;
        if (index >= header.length || header[index++] != '\n') return null;
        if (prefix(header, index, "meta_data={".getBytes(java.nio.charset.StandardCharsets.US_ASCII))) return RawHeader.TEXT;
        return prefix(header, index, new byte[] {'U', '1', 1, 0, 3, 0}) ? RawHeader.BINARY : null;
    }
    private static boolean prefix(byte[] actual, int offset, byte[] expected) {
        if (actual.length - offset < expected.length) return false;
        for (int i = 0; i < expected.length; i++) if (actual[offset + i] != expected[i]) return false; return true;
    }
    /** The original seed predicate only; this is never physical SAVE, canonical ledger or recovery admission. */
    public static void requireSeedable(Artifact artifact) throws IOException {
        Objects.requireNonNull(artifact);
        if (artifact instanceof ZipArtifact zip && zip.zipValid() && zip.hasGamestate()
                || artifact instanceof OtherArtifact other && other.rawHeader() != null) return;
        throw new IOException("SAVE seed must be CRC-valid ZIP containing gamestate or a recognized native raw SAV header");
    }
}
