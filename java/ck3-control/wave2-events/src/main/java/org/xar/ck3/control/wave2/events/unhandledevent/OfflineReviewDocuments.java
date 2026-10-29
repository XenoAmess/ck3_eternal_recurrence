package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Original immutable pretty-JSON representation and complete-inode publication, without a second writer owner. */
final class OfflineReviewDocuments {
    private OfflineReviewDocuments() { }
    static ExactRef write(Path root, Path target, Value value) throws IOException {
        byte[] raw = (pretty(value, 0) + "\n").getBytes(StandardCharsets.UTF_8);
        return writeRaw(root, target, raw);
    }
    private static ExactRef writeRaw(Path root, Path target, byte[] raw) throws IOException {
        require(target.isAbsolute() && target.normalize().startsWith(root) && !target.normalize().equals(root), "offline output escapes its fixed root");
        directory(root, target.getParent());
        require(raw.length <= 1_048_576, "immutable offline JSON exceeds its original input role");
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
            require(java.util.Arrays.equals(raw, EvidenceGrantManifestPublisher.readStable(target, 1_048_576)), "immutable offline source receipt already differs");
        } else if (OfflineAnalysisFiles.current().isPresent()) {
            ExactRef actual = OfflineAnalysisFiles.current().orElseThrow().createNew(target, raw);
            require(actual.equals(new ExactRef(target.toString(), raw.length, sha(raw))), "guarded immutable output differs");
        } else {
            Path temporary = target.resolveSibling(target.getFileName() + ".tmp-" + UUID.randomUUID());
            try {
                try (FileChannel file = FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS)) {
                    ByteBuffer bytes = ByteBuffer.wrap(raw); while (bytes.hasRemaining()) file.write(bytes); file.force(true);
                }
                directory(root, target.getParent());
                try { Files.createLink(target, temporary); }
                catch (FileAlreadyExistsException already) {
                    require(java.util.Arrays.equals(raw, EvidenceGrantManifestPublisher.readStable(target, 1_048_576)), "immutable offline source receipt already differs");
                }
            } finally { Files.deleteIfExists(temporary); }
        }
        require(java.util.Arrays.equals(raw, EvidenceGrantManifestPublisher.readStable(target, 1_048_576)), "immutable offline output readback differs");
        return new ExactRef(target.toString(), raw.length, sha(raw));
    }
    /** Local/canonical receipts share an immutable inode instead of duplicating the same source facts. */
    static ExactRef link(Path root, Path target, ExactRef original) throws IOException {
        require(target.isAbsolute() && target.normalize().startsWith(root) && !target.normalize().equals(root), "offline output escapes its fixed root");
        directory(root, target.getParent()); Path source = Path.of(original.path());
        byte[] raw = EvidenceGrantManifestPublisher.readStable(source, 1_048_576);
        require(raw.length == original.bytes() && sha(raw).equals(original.sha256()), "immutable source link original changed");
        if (!Files.getFileStore(source).equals(Files.getFileStore(target.getParent()))) return writeRaw(root, target, raw);
        if (!Files.exists(target, LinkOption.NOFOLLOW_LINKS) && OfflineAnalysisFiles.current().isPresent())
            OfflineAnalysisFiles.current().orElseThrow().beforeLink(target, original.bytes());
        try { Files.createLink(target, source); }
        catch (FileAlreadyExistsException existing) {
            require(java.util.Arrays.equals(raw, EvidenceGrantManifestPublisher.readStable(target, 1_048_576)), "immutable offline source receipt already differs");
        }
        require(java.util.Arrays.equals(raw, EvidenceGrantManifestPublisher.readStable(target, 1_048_576)), "immutable linked output readback differs");
        return new ExactRef(target.toString(), raw.length, original.sha256());
    }
    static void directory(Path root, Path target) throws IOException {
        require(root.isAbsolute() && target.normalize().startsWith(root), "fixed offline directory required");
        if (OfflineAnalysisFiles.current().isPresent()) {
            OfflineAnalysisFiles.current().orElseThrow().directories(target); checkedDirectory(root); checkedDirectory(target); return;
        }
        Path cursor = root; checkedDirectory(cursor);
        for (Path part : root.relativize(target)) {
            cursor = cursor.resolve(part);
            try { Files.createDirectory(cursor); } catch (FileAlreadyExistsException exists) { /* Recheck the actual existing directory below. */ }
            checkedDirectory(cursor);
        }
        checkedDirectory(root);
    }
    private static void checkedDirectory(Path path) throws IOException {
        var attributes = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        if (!attributes.isDirectory() || attributes.isSymbolicLink() || attributes.fileKey() == null || !path.toRealPath().equals(path)) throw new IOException("fixed offline directory identity unavailable");
    }
    static ObjectValue reference(ExactRef reference) { return obj(f("path", s(reference.path())), f("sha256", s(reference.sha256()))); }
    private static String pretty(Value value, int depth) {
        return switch (value) {
            case ObjectValue object -> {
                if (object.fields().isEmpty()) yield "{}";
                List<String> rows = new ArrayList<>();
                object.fields().keySet().stream().sorted(CODE_POINTS).forEach(key -> rows.add("  ".repeat(depth + 1)
                        + quote(key) + ": " + pretty(object.get(key), depth + 1)));
                yield "{\n" + String.join(",\n", rows) + "\n" + "  ".repeat(depth) + "}";
            }
            case ArrayValue array -> {
                if (array.values().isEmpty()) yield "[]";
                yield "[\n" + String.join(",\n", array.values().stream().map(item -> "  ".repeat(depth + 1) + pretty(item, depth + 1)).toList())
                        + "\n" + "  ".repeat(depth) + "]";
            }
            case FloatingValue ignored -> throw new IllegalArgumentException("offline facts/report cannot contain floating identities");
            case StringValue string -> quote(string.value());
            default -> new String(RetainedJson.encode(value), StandardCharsets.UTF_8);
        };
    }
    private static String quote(String value) {
        StringBuilder result = new StringBuilder("\""); String hex = "0123456789abcdef";
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            switch (current) {
                case '"' -> result.append("\\\""); case '\\' -> result.append("\\\\");
                case '\b' -> result.append("\\b"); case '\f' -> result.append("\\f"); case '\n' -> result.append("\\n");
                case '\r' -> result.append("\\r"); case '\t' -> result.append("\\t");
                default -> {
                    if (current < 0x20) result.append("\\u00").append(hex.charAt((current >>> 4) & 15)).append(hex.charAt(current & 15));
                    else result.append(current);
                }
            }
        }
        return result.append('"').toString();
    }
    private static final Comparator<String> CODE_POINTS = (left, right) -> {
        int a = 0, b = 0;
        while (a < left.length() && b < right.length()) {
            int x = left.codePointAt(a), y = right.codePointAt(b); if (x != y) return Integer.compare(x, y);
            a += Character.charCount(x); b += Character.charCount(y);
        }
        return Integer.compare(left.length() - a, right.length() - b);
    };
}
