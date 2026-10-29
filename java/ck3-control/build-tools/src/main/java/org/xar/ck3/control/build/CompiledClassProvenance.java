package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import com.sun.source.util.JavacTask;
import java.nio.charset.StandardCharsets;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaFileObject;
import javax.tools.ToolProvider;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;

/** Class-file provenance only. The build producer owns successful Maven/Job and complete manifest admission. */
public final class CompiledClassProvenance {
    public static final int MAX_CLASS_BYTES = 16 << 20;
    public enum SourceSet { MAIN, TEST }

    public record Origin(String binaryName, String sourceFile, ControlBuild.FileRef classRef,
            ControlBuild.FileRef sourceRef, String runtimeOrigin) {
        public Origin {
            Objects.requireNonNull(binaryName); Objects.requireNonNull(sourceFile);
            Objects.requireNonNull(classRef); Objects.requireNonNull(sourceRef); Objects.requireNonNull(runtimeOrigin);
            if (binaryName.isBlank() || sourceFile.isBlank() || !Path.of(runtimeOrigin).isAbsolute()) {
                throw new IllegalArgumentException("Actual binary, source and absolute runtime origin required");
            }
        }
    }

    private record Parsed(String internalName, String sourceFile) {}
    private CompiledClassProvenance() {}

    /** No class is loaded or initialized; all identity fields are read from the pinned actual class file. */
    public static Origin attest(Path classOutputRoot, ControlBuild.FileRef classRef, Path compiledModuleRoot,
            SourceSet sourceSet, List<ControlBuild.FileRef> compiledSourceRefs) throws IOException {
        Objects.requireNonNull(classOutputRoot); Objects.requireNonNull(classRef); Objects.requireNonNull(compiledModuleRoot);
        Objects.requireNonNull(sourceSet); compiledSourceRefs = List.copyOf(compiledSourceRefs);
        if (compiledSourceRefs.size() > 32768 || classRef.bytes() < 1 || classRef.bytes() > MAX_CLASS_BYTES) {
            throw new IOException("Finite actual class and compiled-source inventory required");
        }
        Path output = classOutputRoot.toAbsolutePath().normalize(), module = compiledModuleRoot.toAbsolutePath().normalize();
        Path actual = Path.of(classRef.path()).toAbsolutePath().normalize();
        if (!Files.isDirectory(output) || !Files.isDirectory(module) || !actual.startsWith(output)) {
            throw new IOException("Actual class output and compiled module roots required");
        }
        classRef.verify(); byte[] raw;
        try (InputStream input = Files.newInputStream(actual)) { raw = input.readNBytes(MAX_CLASS_BYTES + 1); }
        if (raw.length != classRef.bytes() || !digest(raw).equals(classRef.sha256())) {
            throw new IOException("Read class bytes differ from actual class reference");
        }
        Parsed parsed = parse(raw);
        Path expectedClass = output.resolve(parsed.internalName() + ".class").normalize();
        if (!expectedClass.startsWith(output) || !actual.equals(expectedClass)
                || !actual.toRealPath().equals(output.toRealPath().resolve(parsed.internalName() + ".class").normalize())) {
            throw new IOException("Class output path differs from its internal binary name or actual runtime origin");
        }
        int slash = parsed.internalName().lastIndexOf('/');
        String packagePath = slash < 0 ? "" : parsed.internalName().substring(0, slash + 1);
        Path sourceBase = module.resolve(sourceSet == SourceSet.MAIN ? "src/main/java" : "src/test/java");
        Path expectedSource = sourceBase.resolve(packagePath + parsed.sourceFile()).normalize();
        if (!expectedSource.startsWith(sourceBase)) throw new IOException("Class source escaped its source set");
        ControlBuild.FileRef source = resolveSource(sourceBase, parsed.sourceFile(),
                packagePath.isEmpty() ? "" : packagePath.substring(0, packagePath.length() - 1).replace('/', '.'), compiledSourceRefs);
        source.verify();
        if (!Path.of(source.path()).toRealPath().startsWith(sourceBase.toRealPath())) throw new IOException("Source escaped actual compiled source set");
        classRef.verify(); source.verify();
        return new Origin(parsed.internalName().replace('/', '.'), parsed.sourceFile(), classRef, source, output.toRealPath().toString());
    }

    /** javac SourceFile binds a filename and declared package, not a mandatory physical package directory. */
    private static ControlBuild.FileRef resolveSource(Path sourceBase, String filename,
            String packageName, List<ControlBuild.FileRef> compiledSources) throws IOException {
        var candidates = new java.util.ArrayList<ControlBuild.FileRef>();
        for (var candidate : compiledSources) {
            Path path = Path.of(candidate.path()).toAbsolutePath().normalize();
            if (path.startsWith(sourceBase) && path.getFileName().toString().equals(filename)) candidates.add(candidate);
        }
        ControlBuild.FileRef selected = null;
        for (var candidate : candidates) {
            candidate.verify();
            if (!Path.of(candidate.path()).toRealPath().startsWith(sourceBase.toRealPath()))
                throw new IOException("Source escaped actual compiled source set");
            if (!declaredPackage(candidate).equals(packageName)) continue;
            if (selected != null) throw new IOException("Multiple compiled-source references match actual SourceFile and declared package");
            selected = candidate;
        }
        if (selected == null) throw new IOException("Actual SourceFile absent from this compiled module/source-set inventory");
        return selected;
    }

    /** Parse only: no source compilation, annotation processing, class loading or output is performed. */
    private static String declaredPackage(ControlBuild.FileRef source) throws IOException {
        var compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new IOException("Actual JDK source parser required for noncanonical SourceFile paths");
        var diagnostics = new DiagnosticCollector<JavaFileObject>();
        try (var files = compiler.getStandardFileManager(diagnostics, java.util.Locale.ROOT, StandardCharsets.UTF_8)) {
            var work = compiler.getTask(null, files, diagnostics, List.of("-proc:none"), null,
                    files.getJavaFileObjectsFromPaths(List.of(Path.of(source.path()))));
            if (!(work instanceof JavacTask task)) throw new IOException("Actual JDK syntax parser required");
            var units = task.parse().iterator();
            if (!units.hasNext()) throw new IOException("One actual Java source declaration required");
            var unit = units.next();
            if (units.hasNext() || diagnostics.getDiagnostics().stream().anyMatch(row -> row.getKind() == Diagnostic.Kind.ERROR))
                throw new IOException("Actual Java source declaration is malformed");
            source.verify();
            return unit.getPackageName() == null ? "" : unit.getPackageName().toString();
        } catch (RuntimeException invalid) { throw new IOException("Actual Java source declaration is unavailable", invalid); }
    }

    private static Parsed parse(byte[] raw) throws IOException {
        Cursor input = new Cursor(raw);
        if (input.u4() != 0xcafebabeL) throw new IOException("Class-file magic required");
        input.u2(); int major = input.u2();
        if (major < 45) throw new IOException("Unsupported class-file version");
        int count = input.u2();
        if (count < 2) throw new IOException("Actual constant pool required");
        int[] tags = new int[count], first = new int[count], second = new int[count]; String[] text = new String[count];
        for (int index = 1; index < count; index++) {
            int tag = input.u1(); tags[index] = tag;
            switch (tag) {
                case 1 -> text[index] = input.modifiedUtf();
                case 3, 4 -> input.skip(4);
                case 5, 6 -> {
                    input.skip(8);
                    if (++index >= count) throw new IOException("Long/double constant requires its second pool slot");
                }
                case 7, 8, 16, 19, 20 -> first[index] = input.u2();
                case 9, 10, 11, 12, 17, 18 -> { first[index] = input.u2(); second[index] = input.u2(); }
                case 15 -> { first[index] = input.u1(); second[index] = input.u2(); }
                default -> throw new IOException("Unknown class-file constant-pool tag: " + tag);
            }
        }
        for (int index = 1; index < count; index++) {
            switch (tags[index]) {
                case 7, 8, 16, 19, 20 -> utf(first[index], tags, text);
                case 9, 10, 11 -> { requireTag(first[index], 7, tags); requireTag(second[index], 12, tags); }
                case 12 -> { utf(first[index], tags, text); utf(second[index], tags, text); }
                case 17, 18 -> requireTag(second[index], 12, tags);
                case 15 -> {
                    int kind = first[index], reference = second[index];
                    if (kind < 1 || kind > 9) throw new IOException("Invalid method-handle reference kind");
                    if (kind <= 4) requireTag(reference, 9, tags);
                    else if (kind == 9) requireTag(reference, 11, tags);
                    else if ((kind == 6 || kind == 7) && major >= 52 && reference > 0 && reference < count
                            && tags[reference] == 11) { /* Valid interface static/special handle. */ }
                    else requireTag(reference, 10, tags);
                }
                default -> { /* Numeric constants and reserved long/double slots contain no references. */ }
            }
        }
        input.u2(); int self = input.u2(); requireTag(self, 7, tags);
        String internalName = utf(first[self], tags, text); requireInternalName(internalName);
        int parent = input.u2(); if (parent != 0) requireTag(parent, 7, tags);
        int interfaces = input.u2(); for (int index = 0; index < interfaces; index++) requireTag(input.u2(), 7, tags);
        skipMembers(input, tags, text); skipMembers(input, tags, text);
        String sourceFile = null; int attributes = input.u2();
        for (int index = 0; index < attributes; index++) {
            String name = utf(input.u2(), tags, text); long length = input.u4();
            int end = input.end(length);
            if (name.equals("SourceFile")) {
                if (sourceFile != null || length != 2) throw new IOException("Exactly one two-byte SourceFile attribute required");
                sourceFile = utf(input.u2(), tags, text); requireSourceFile(sourceFile);
            } else if (name.equals("InnerClasses")) {
                int entries = input.u2();
                if (length != 2L + 8L * entries) throw new IOException("Invalid InnerClasses attribute size");
                for (int entry = 0; entry < entries; entry++) {
                    requireTag(input.u2(), 7, tags); int outer = input.u2(), innerName = input.u2();
                    if (outer != 0) requireTag(outer, 7, tags); if (innerName != 0) utf(innerName, tags, text); input.u2();
                }
            } else input.skip(length);
            if (input.position != end) throw new IOException("Class attribute exceeds its declared byte boundary");
        }
        if (sourceFile == null || input.position != raw.length) throw new IOException("One actual SourceFile and exact complete class bytes required");
        return new Parsed(internalName, sourceFile);
    }

    private static void skipMembers(Cursor input, int[] tags, String[] text) throws IOException {
        int members = input.u2();
        for (int index = 0; index < members; index++) {
            input.u2(); utf(input.u2(), tags, text); utf(input.u2(), tags, text); int attributes = input.u2();
            for (int attribute = 0; attribute < attributes; attribute++) { utf(input.u2(), tags, text); input.skip(input.u4()); }
        }
    }

    private static String utf(int index, int[] tags, String[] text) throws IOException {
        requireTag(index, 1, tags); return text[index];
    }
    private static void requireTag(int index, int tag, int[] tags) throws IOException {
        if (index < 1 || index >= tags.length || tags[index] != tag) throw new IOException("Invalid constant-pool reference");
    }
    private static void requireInternalName(String name) throws IOException {
        String[] parts = name.split("/", -1);
        for (int part = 0; part < parts.length; part++) {
            String item = parts[part];
            if (part == parts.length - 1 && (item.equals("module-info") || item.equals("package-info"))) continue;
            if (item.isEmpty() || !Character.isJavaIdentifierStart(item.codePointAt(0))) throw new IOException("Canonical internal binary name required");
            for (int offset = Character.charCount(item.codePointAt(0)); offset < item.length();) {
                int point = item.codePointAt(offset);
                if (!Character.isJavaIdentifierPart(point) || Character.isIdentifierIgnorable(point)) throw new IOException("Invalid internal binary name character");
                offset += Character.charCount(point);
            }
        }
    }
    private static void requireSourceFile(String name) throws IOException {
        if (!name.endsWith(".java") || name.length() <= 5 || name.indexOf('/') >= 0 || name.indexOf('\\') >= 0
                || name.indexOf(':') >= 0 || name.codePoints().anyMatch(point -> point < 32 || point == 127)) {
            throw new IOException("Plain actual Java SourceFile basename required");
        }
        try {
            if (!Path.of(name).getFileName().toString().equals(name)) throw new IOException("Plain actual Java SourceFile basename required");
        } catch (java.nio.file.InvalidPathException error) { throw new IOException("Invalid actual Java SourceFile basename", error); }
    }
    private static String digest(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    /** Strict modified UTF-8 (UTF-16 code units), not ordinary UTF-8 and not a replacement decoder. */
    private static final class Cursor {
        private final byte[] bytes; private int position;
        Cursor(byte[] bytes) { this.bytes = bytes; }
        int end(long length) throws IOException {
            if (length < 0 || length > bytes.length - position) throw new IOException("Truncated class-file byte boundary");
            return position + (int) length;
        }
        int u1() throws IOException { end(1); return bytes[position++] & 255; }
        int u2() throws IOException { return (u1() << 8) | u1(); }
        long u4() throws IOException { return ((long) u2() << 16) | u2(); }
        void skip(long length) throws IOException { position = end(length); }
        String modifiedUtf() throws IOException {
            int limit = end(u2()); StringBuilder result = new StringBuilder();
            while (position < limit) {
                int one = u1(), value;
                if (one >= 1 && one <= 127) value = one;
                else if ((one & 224) == 192) {
                    if (position >= limit) throw new IOException("Truncated modified UTF-8 pair");
                    int two = u1(); if ((two & 192) != 128) throw new IOException("Invalid modified UTF-8 continuation");
                    value = ((one & 31) << 6) | (two & 63);
                    if (value < 128 && !(one == 192 && two == 128)) throw new IOException("Noncanonical modified UTF-8 pair");
                } else if ((one & 240) == 224) {
                    if (limit - position < 2) throw new IOException("Truncated modified UTF-8 triple");
                    int two = u1(), three = u1();
                    if ((two & 192) != 128 || (three & 192) != 128) throw new IOException("Invalid modified UTF-8 continuation");
                    value = ((one & 15) << 12) | ((two & 63) << 6) | (three & 63);
                    if (value < 2048) throw new IOException("Noncanonical modified UTF-8 triple");
                } else throw new IOException("Invalid modified UTF-8 lead byte");
                result.append((char) value);
            }
            return result.toString();
        }
    }
}
