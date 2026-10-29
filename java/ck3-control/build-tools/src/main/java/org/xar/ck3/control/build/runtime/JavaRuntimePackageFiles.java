package org.xar.ck3.control.build.runtime;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.ClassProvider;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Layout;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.ProviderKind;

/** Physical closure checks reuse the existing native file observer; no alternate FileID implementation. */
public final class JavaRuntimePackageFiles {
    private JavaRuntimePackageFiles() { }

    /** Exact complete tree, including resources. No symlink/reparse/extra-leaf exception. */
    public static List<FileRef> inventory(Path root, long maximumBytes) throws IOException {
        if (maximumBytes < 1 || maximumBytes > (4L << 30)) throw new IllegalArgumentException("finite runtime inventory byte envelope required");
        SharedSourceFiles.plainAncestors(root);
        if (!Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("actual complete runtime directory is missing: " + root);
        List<FileRef> files = new ArrayList<>(); long bytes = 0;
        try (var walk = Files.walk(root)) {
            var iterator = walk.iterator(); int entries = 0;
            while (iterator.hasNext()) {
                Path path = iterator.next();
                if (++entries > JavaRuntimePackageModel.MAX_FILES * 2) throw new IOException("runtime tree entry limit exceeded");
                SharedSourceFiles.plainAncestors(path);
                if (Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) continue;
                if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("plain runtime leaf required");
                FileRef file = FileRef.measure(path); bytes = Math.addExact(bytes, file.bytes()); files.add(file);
                if (bytes > maximumBytes || files.size() > JavaRuntimePackageModel.MAX_FILES) throw new IOException("runtime complete tree exceeds its byte/file envelope");
            }
        }
        files.sort(Comparator.comparing(FileRef::path)); return List.copyOf(files);
    }

    /** The producer and import reader both compare the whole tree, including non-JAR resources. */
    public static void verifyCompleteTree(Path root, List<FileRef> expected, long maximumBytes) throws IOException {
        relativeIndex(root, expected);
        if (!inventory(root, maximumBytes).equals(expected)) throw new IOException("complete runtime tree has missing, changed, reordered or additional leaves");
    }

    public static Layout inspectFastJar(Path root, List<FileRef> completeFiles, List<String> requiredClasses) throws IOException {
        Map<String, FileRef> files = relativeIndex(root, completeFiles);
        for (String required : List.of("quarkus-run.jar", "quarkus/quarkus-application.dat", "quarkus-app-dependencies.txt")) {
            FileRef file = files.get(required);
            if (file == null || file.bytes() == 0) throw new IOException("complete fast-jar leaf is missing: " + required);
        }
        List<String> jars = files.keySet().stream().filter(name -> name.endsWith(".jar")).sorted().toList();
        if (jars.stream().noneMatch(name -> name.startsWith("app/")) || jars.stream().noneMatch(name -> name.startsWith("lib/main/"))
                || jars.stream().noneMatch(name -> name.startsWith("lib/boot/"))) throw new IOException("application, main and boot dependency JAR closures are all required");
        for (String name : files.keySet()) {
            String lower = name.toLowerCase(Locale.ROOT);
            if (lower.endsWith(".py") || lower.endsWith(".pyc") || lower.endsWith(".exe") || lower.endsWith(".cmd")
                    || lower.endsWith(".bat") || lower.endsWith(".ps1")) throw new IOException("non-Java executable entry in fast-jar runtime payload");
        }
        List<ClassProvider> classes = new ArrayList<>(); List<String> boot = List.of(); int entries = 0;
        Set<String> originals = new HashSet<>(), generated = new HashSet<>(), transformed = new HashSet<>();
        for (String relative : jars) {
            FileRef file = files.get(relative); Witness before = SharedSourceFiles.observe(Path.of(file.path()));
            if (!before.source().equals(file)) throw new IOException("JAR source changed before closure inspection");
            ProviderKind kind = relative.equals("quarkus/transformed-bytecode.jar") ? ProviderKind.TRANSFORMED
                    : relative.equals("quarkus/generated-bytecode.jar") ? ProviderKind.GENERATED : ProviderKind.ORIGINAL;
            try (JarFile jar = new JarFile(file.path(), false)) {
                if (relative.equals("quarkus-run.jar")) {
                    var manifest = jar.getManifest();
                    if (manifest == null || !"io.quarkus.bootstrap.runner.QuarkusEntryPoint".equals(manifest.getMainAttributes().getValue(Attributes.Name.MAIN_CLASS)))
                        throw new IOException("actual Quarkus fast-jar Main-Class differs");
                    boot = bootClassPath(root, files, manifest.getMainAttributes().getValue(Attributes.Name.CLASS_PATH));
                }
                Set<String> jarNames = new HashSet<>(); Enumeration<JarEntry> enumeration = jar.entries();
                while (enumeration.hasMoreElements()) {
                    JarEntry entry = enumeration.nextElement(); String name = entry.getName();
                    if (++entries > 500_000 || name.length() > 4096 || !jarNames.add(name)) throw new IOException("bounded unique JAR entries required");
                    if (entry.isDirectory()) continue;
                    JavaRuntimePackageModel.relative(name);
                    if (!name.startsWith("org/xar/") || !name.endsWith(".class")) continue;
                    String type = name.substring(0, name.length() - 6).replace('/', '.');
                    Set<String> seen = kind == ProviderKind.ORIGINAL ? originals : kind == ProviderKind.GENERATED ? generated : transformed;
                    if (!seen.add(type)) throw new IOException("duplicate application class provider: " + type);
                    classes.add(new ClassProvider(type, relative, kind));
                }
            }
            SharedSourceFiles.assertUnchanged(before);
        }
        for (String type : generated) if (originals.contains(type) || transformed.contains(type)) throw new IOException("generated class aliases a production class: " + type);
        for (String type : transformed) if (!originals.contains(type)) throw new IOException("Quarkus transformation has no original application class: " + type);
        for (String type : requiredClasses) if (!originals.contains(type)) throw new IOException("required Java-only application class is absent: " + type);
        classes.sort(Comparator.comparing(ClassProvider::binaryName).thenComparing(ClassProvider::kind).thenComparing(ClassProvider::relativeJar));
        return new Layout(jars, boot, classes);
    }

    static Map<String, FileRef> relativeIndex(Path root, List<FileRef> files) throws IOException {
        Map<String, FileRef> result = new HashMap<>(); Set<String> folded = new HashSet<>();
        for (FileRef file : files) {
            Path path = Path.of(file.path());
            if (!path.startsWith(root) || path.equals(root)) throw new IOException("runtime reference escapes complete root");
            String relative = root.relativize(path).toString().replace('\\', '/');
            JavaRuntimePackageModel.relative(relative);
            if (!folded.add(relative.toLowerCase(Locale.ROOT)) || result.putIfAbsent(relative, file) != null) throw new IOException("duplicate/case-alias runtime path");
        }
        return Map.copyOf(result);
    }

    private static List<String> bootClassPath(Path root, Map<String, FileRef> files, String raw) throws IOException {
        if (raw == null || raw.isBlank()) throw new IOException("actual runner boot Class-Path is missing");
        List<String> result = new ArrayList<>(); Set<String> seen = new HashSet<>();
        for (String token : raw.trim().split(" +")) {
            final URI uri;
            try { uri = URI.create(token); } catch (IllegalArgumentException invalid) { throw new IOException("invalid boot Class-Path URI", invalid); }
            if (uri.isAbsolute() || uri.getAuthority() != null || uri.getQuery() != null || uri.getFragment() != null || uri.getPath() == null)
                throw new IOException("external boot Class-Path is forbidden");
            Path resolved = root.resolve(uri.getPath()).normalize();
            if (!resolved.startsWith(root) || resolved.equals(root)) throw new IOException("boot Class-Path escapes actual fast-jar");
            String relative = root.relativize(resolved).toString().replace('\\', '/');
            if (!relative.startsWith("lib/boot/") || !relative.endsWith(".jar") || !files.containsKey(relative) || !seen.add(relative))
                throw new IOException("runner boot dependency missing, repeated, or outside lib/boot");
            result.add(relative);
        }
        return List.copyOf(result);
    }

    static Witness copyNew(FileRef source, Path target) throws IOException {
        Witness before = SharedSourceFiles.observe(Path.of(source.path()));
        if (!before.source().equals(source)) throw new IOException("source differs before immutable package copy");
        SharedSourceFiles.plainAncestors(target); Files.createDirectories(target.getParent());
        long bytes = 0;
        try (InputStream input = Files.newInputStream(Path.of(source.path()));
                FileChannel output = FileChannel.open(target, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            byte[] buffer = new byte[65_536]; int count;
            while ((count = input.read(buffer)) != -1) {
                bytes = Math.addExact(bytes, count);
                if (bytes > source.bytes()) throw new IOException("immutable input grew while copying");
                ByteBuffer chunk = ByteBuffer.wrap(buffer, 0, count);
                while (chunk.hasRemaining()) output.write(chunk);
            }
            output.force(true);
        }
        if (bytes != source.bytes()) throw new IOException("immutable input shortened while copying");
        Witness copied = SharedSourceFiles.observe(target); SharedSourceFiles.assertUnchanged(before);
        if (copied.source().bytes() != source.bytes() || !copied.source().sha256().equals(source.sha256())
                || copied.nativeFile().identityKey().equals(before.nativeFile().identityKey())) throw new IOException("private copied bytes/identity differ");
        return copied;
    }
}
