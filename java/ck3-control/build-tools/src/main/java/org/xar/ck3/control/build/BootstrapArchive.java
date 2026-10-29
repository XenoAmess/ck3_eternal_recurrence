package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import java.util.zip.ZipEntry;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.FileObject;
import javax.tools.ForwardingJavaFileManager;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.StandardLocation;
import javax.tools.ToolProvider;

/** Strict Java source bootstrap only. It neither runs Maven nor grants tools/Game qualification. */
public final class BootstrapArchive {
    public static final String REQUEST_SCHEMA = "xar.java-tools-bootstrap-archive-request/v1";
    public static final String ACTUAL_SCHEMA = "xar.java-tools-bootstrap-archive-actual/v1";
    public static final int METADATA_RESERVE_BYTES = 1 << 20;
    private BootstrapArchive() { }
    public enum Group { TOOLS, HOST }
    private enum LibraryRole { ANNOTATIONS, CORE, DATABIND, JNA, JNA_PLATFORM }
    public enum Status { STRICT_COMPILE_AND_ARCHIVE_READBACK_SOURCE_BOOTSTRAP_ONLY }
    public record Selected(Group group, String targetRelative, ControlBuild.FileRef sourceRef) {
        public Selected { Objects.requireNonNull(group); relative(targetRelative); Objects.requireNonNull(sourceRef); }
    }
    public record Request(String schema, String machineId, String taskOwner, String reviewAtUtc,
            ControlBuild.FileRef completeSelectionRef, ControlBuild.FileRef inputManifestRef,
            List<ControlBuild.FileRef> compileLibraries, String outputRoot, int expectedMainSources,
            long maximumSourceBytes, int maximumClasses, long maximumClassBytes,
            long maximumArchiveBytes, long maximumNewRootBytes) {
        public Request {
            compileLibraries = List.copyOf(compileLibraries);
            if (!REQUEST_SCHEMA.equals(schema) || !machineId.matches("[a-z0-9][a-z0-9-]{0,127}") || machineId.equals("unknown")
                    || !taskOwner.matches("/root(?:/[a-z0-9_]+)*") || compileLibraries.size() != 5
                    || expectedMainSources < 1 || expectedMainSources > 256
                    || maximumSourceBytes < 1 || maximumSourceBytes > (8L << 20)
                    || maximumClasses < expectedMainSources || maximumClasses > 4096
                    || maximumClassBytes < 1 || maximumClassBytes > (8L << 20)
                    || maximumArchiveBytes < 1 || maximumArchiveBytes > (8L << 20)
                    || maximumNewRootBytes < METADATA_RESERVE_BYTES || maximumNewRootBytes > (16L << 20))
                throw new IllegalArgumentException("Explicit finite source bootstrap contract required");
            if (!Instant.parse(reviewAtUtc).toString().equals(reviewAtUtc)) throw new IllegalArgumentException("Canonical UTC review required");
            absolute(outputRoot);
            Objects.requireNonNull(completeSelectionRef); Objects.requireNonNull(inputManifestRef);
        }
    }
    public record ArchiveEntry(String path, long bytes, String sha256) {
        public ArchiveEntry {
            relative(path);
            if (bytes < 0 || !sha256.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("Exact archive entry required");
        }
    }
    public record Actual(String schema, String machineId, String observedAtUtc, Status status,
            ControlBuild.FileRef requestRef, ControlBuild.FileRef selectionRef,
            List<ControlBuild.FileRef> compileLibraries, List<ControlBuild.FileRef> completeBootstrapRuntime,
            List<ArchiveEntry> completeArchiveEntries, List<String> compilerOptions,
            int mainSources, long sourceBytes, long classBytes, long plannedNewRootUpperBytes,
            List<SharedSourceFiles.Witness> createdRuntimeWitnesses,
            String Maven, String generalTools, String nativeOperations, String game) {
        public Actual {
            compileLibraries = List.copyOf(compileLibraries); completeBootstrapRuntime = List.copyOf(completeBootstrapRuntime);
            completeArchiveEntries = List.copyOf(completeArchiveEntries); compilerOptions = List.copyOf(compilerOptions);
            createdRuntimeWitnesses = List.copyOf(createdRuntimeWitnesses);
            if (!ACTUAL_SCHEMA.equals(schema) || status != Status.STRICT_COMPILE_AND_ARCHIVE_READBACK_SOURCE_BOOTSTRAP_ONLY
                    || !Instant.parse(observedAtUtc).toString().equals(observedAtUtc)
                    || compileLibraries.size() != 5 || completeBootstrapRuntime.size() != 6
                    || mainSources < 1 || sourceBytes < 1 || classBytes < 1 || plannedNewRootUpperBytes < 1
                    || completeArchiveEntries.isEmpty() || createdRuntimeWitnesses.size() != 6
                    || completeArchiveEntries.stream().map(ArchiveEntry::path).distinct().count() != completeArchiveEntries.size()
                    || !Maven.equals("NOT_RUN") || !generalTools.equals("NOT_QUALIFIED") || !nativeOperations.equals("NOT_RUN") || !game.equals("NOT_RUN"))
                throw new IllegalArgumentException("Closed source-bootstrap-only actual contract required");
        }
    }
    private record Unit(String path, ControlBuild.FileRef ref) { }
    private record Compilation(Map<String, byte[]> classes, List<String> options, long classBytes) { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("Request path, exact byte count and SHA256 required");
        var requestRef = new ControlBuild.FileRef(args[0], Long.parseLong(args[1]), args[2]);
        Request request = ControlBuild.strictMapper().readValue(exact(requestRef, 256 << 10), Request.class);
        create(request, requestRef);
    }
    public static Actual create(Request request, ControlBuild.FileRef requestRef) throws IOException {
        if (!ControlBuild.strictMapper().readValue(exact(requestRef, 256 << 10), Request.class).equals(request))
            throw new IOException("Typed bootstrap request differs from its exact original body");
        current(request);
        var guard = BoundedSourceInputGuard.open(request.inputManifestRef(), request.taskOwner());
        Actual result;
        try (Directories directories = new Directories()) {
        try (guard; Libraries custody = new Libraries()) {
            JsonNode selection = ControlBuild.strictMapper().readTree(exact(request.completeSelectionRef(), 1 << 20));
            if (!selection.path("schema").asText().equals("xar.java-source-effective-selection/v1")
                    || !selection.path("machine_id").asText().equals(request.machineId())
                    || !selection.path("owner").asText().equals(request.taskOwner())
                    || !selection.path("selected_files").isArray() || selection.path("selected_files").isEmpty()
                    || selection.path("selected_files").size() > 512)
                throw new IOException("Original complete typed source selection required");
            List<Unit> java = new ArrayList<>(), resources = new ArrayList<>();
            Set<String> targets = new HashSet<>();
            for (JsonNode row : selection.required("selected_files")) {
                Selected selected = ControlBuild.strictMapper().treeToValue(row, Selected.class);
                if (!targets.add(selected.group() + "/" + selected.targetRelative())) throw new IOException("Duplicate selected target");
                if (selected.group() == Group.TOOLS && selected.targetRelative().startsWith("build-tools/src/main/java/")) {
                    String path = selected.targetRelative().substring("build-tools/src/main/java/".length());
                    if (!path.endsWith(".java")) throw new IOException("Canonical Java source required");
                    java.add(new Unit(path, selected.sourceRef()));
                } else if (selected.group() == Group.TOOLS && selected.targetRelative().startsWith("build-tools/src/main/resources/")) {
                    String path = selected.targetRelative().substring("build-tools/src/main/resources/".length());
                    if (path.endsWith(".class") || path.equals("META-INF/MANIFEST.MF")) throw new IOException("Reserved archive resource");
                    resources.add(new Unit(path, selected.sourceRef()));
                }
            }
            if (java.size() != request.expectedMainSources()) throw new IOException("Complete main source count differs");
            List<ControlBuild.FileRef> expected = new ArrayList<>(); expected.add(request.completeSelectionRef());
            java.forEach(unit -> expected.add(unit.ref())); resources.forEach(unit -> expected.add(unit.ref()));
            expected.addAll(request.compileLibraries()); guard.requireExactInputs(expected);
            List<SharedSourceFiles.Witness> libraries = new ArrayList<>(); Set<LibraryRole> roles = new HashSet<>();
            for (var ref : request.compileLibraries()) {
                String name = Path.of(ref.path()).getFileName().toString();
                if (!name.matches("(jackson-[a-z-]+|jna|jna-platform)-[0-9][A-Za-z0-9.+-]*[.]jar") || !roles.add(role(name)))
                    throw new IOException("Exact five non-production library archives required");
                custody.retain(Path.of(ref.path()));
                var witness = SharedSourceFiles.observe(Path.of(ref.path()));
                if (!witness.source().equals(ref)) throw new IOException("Compile library actual pin differs");
                libraries.add(witness);
            }
            if (roles.size() != LibraryRole.values().length) throw new IOException("All five distinct library roles required");
            long sourceBytes = 0;
            for (Unit unit : java) sourceBytes = Math.addExact(sourceBytes, unit.ref().bytes());
            for (Unit unit : resources) sourceBytes = Math.addExact(sourceBytes, unit.ref().bytes());
            if (sourceBytes > request.maximumSourceBytes()) throw new IOException("Complete source extent exceeds release");
            Compilation compiled = compile(request, java);
            Map<String, byte[]> entries = new TreeMap<>(compiled.classes());
            for (Unit unit : resources) if (entries.putIfAbsent(unit.path(), exact(unit.ref(), request.maximumSourceBytes())) != null)
                throw new IOException("Class/resource archive collision");
            entries.put("META-INF/MANIFEST.MF", ("Manifest-Version: 1.0" + (char) 13 + (char) 10 + (char) 13 + (char) 10).getBytes(StandardCharsets.UTF_8));
            byte[] archive = archive(entries, request.maximumArchiveBytes());
            // Two separately allocated metadata files can cost one extra page beyond their combined logical ceiling.
            long planned = Math.addExact(round(archive.length), METADATA_RESERVE_BYTES + 12288L);
            for (var ref : request.compileLibraries()) planned = Math.addExact(planned, round(ref.bytes()));
            if (planned > request.maximumNewRootBytes()) throw new IOException("Bootstrap closed output peak exceeds release before CREATE_NEW");
            Path root = absolute(request.outputRoot()); SharedSourceFiles.plainAncestors(root);
            if (!Files.isDirectory(root.getParent(), LinkOption.NOFOLLOW_LINKS) || Files.exists(root, LinkOption.NOFOLLOW_LINKS))
                throw new IOException("Fresh bootstrap root under an existing plain parent required");
            directories.retainAncestors(root.getParent());
            SharedSourceFiles.plainAncestors(root); directories.requireCurrent();
            current(request); Files.createDirectory(root); directories.retain(root);
            Files.createDirectory(root.resolve("lib")); directories.retain(root.resolve("lib"));
            List<SharedSourceFiles.Witness> outputs = new ArrayList<>();
            Path jar = root.resolve("ck3-control-bootstrap-tools.jar");
            outputs.add(writeNew(jar, archive));
            for (var ref : request.compileLibraries()) {
                byte[] bytes = exact(ref, 8 << 20);
                outputs.add(writeNew(root.resolve("lib").resolve(Path.of(ref.path()).getFileName()), bytes));
            }
            List<ArchiveEntry> inventory = verifyArchive(jar, entries);
            custody.requireCurrent();
            for (var witness : outputs) SharedSourceFiles.assertUnchanged(witness);
            for (var witness : libraries) SharedSourceFiles.assertUnchanged(witness);
            List<ControlBuild.FileRef> runtime = outputs.stream().map(SharedSourceFiles.Witness::source)
                    .sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList();
            current(request);
            result = new Actual(ACTUAL_SCHEMA, request.machineId(), Instant.now().toString(),
                    Status.STRICT_COMPILE_AND_ARCHIVE_READBACK_SOURCE_BOOTSTRAP_ONLY, requestRef, request.completeSelectionRef(),
                    request.compileLibraries(), runtime, inventory, compiled.options(), java.size(), sourceBytes,
                    compiled.classBytes(), planned, outputs, "NOT_RUN", "NOT_QUALIFIED", "NOT_RUN", "NOT_RUN");
        }
        Path root = absolute(request.outputRoot());
        byte[] actual = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(result);
        byte[] sourceGuard = ControlBuild.strictMapper().writeValueAsBytes(guard.receipt());
        if (Math.addExact(actual.length, sourceGuard.length) > METADATA_RESERVE_BYTES)
            throw new IOException("Bootstrap metadata exceeds its reserved finite extent");
        writeNew(root.resolve("input-guard.actual.json"), sourceGuard);
        writeNew(root.resolve("actual.json"), actual);
        long finalCharge = finalCharge(root, request.compileLibraries().stream().map(ref -> Path.of(ref.path()).getFileName().toString())
                .collect(java.util.stream.Collectors.toUnmodifiableSet()));
        for (var witness : result.createdRuntimeWitnesses()) SharedSourceFiles.assertUnchanged(witness);
        directories.requireCurrent();
        if (finalCharge > request.maximumNewRootBytes()) throw new IOException("Actual bootstrap allocation exceeds release");
        System.out.println("SOURCE_BOOTSTRAP_ONLY main=" + result.mainSources() + ";entries="
                + result.completeArchiveEntries().size() + ";actual_allocated_with_directory_guard=" + finalCharge);
        return result;
        }
    }
    private static Compilation compile(Request request, List<Unit> units) throws IOException {
        var compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null || Runtime.version().feature() != 21) throw new IOException("Actual JDK21 compiler required");
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        Map<String, byte[]> classes = new TreeMap<>(); AtomicLong bytes = new AtomicLong();
        List<String> options = List.of("--release", "21", "-encoding", "UTF-8", "-Xlint:all", "-Werror", "-proc:none", "-implicit:none");
        try (StandardJavaFileManager standard = compiler.getStandardFileManager(diagnostics, null, StandardCharsets.UTF_8)) {
            standard.setLocationFromPaths(StandardLocation.CLASS_PATH, request.compileLibraries().stream().map(ref -> Path.of(ref.path())).toList());
            standard.setLocationFromPaths(StandardLocation.SOURCE_PATH, List.of());
            List<JavaFileObject> sources = new ArrayList<>();
            for (Unit unit : units) {
                byte[] input = exact(unit.ref(), request.maximumSourceBytes());
                String content = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(input)).toString();
                sources.add(new SimpleJavaFileObject(URI.create("memory:///" + unit.path()), JavaFileObject.Kind.SOURCE) {
                    @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return content; }
                });
            }
            var manager = new ForwardingJavaFileManager<StandardJavaFileManager>(standard) {
                @Override public JavaFileObject getJavaFileForOutput(Location location, String name,
                        JavaFileObject.Kind kind, FileObject sibling) throws IOException {
                    String path = name.replace('.', '/') + ".class"; relative(path);
                    if (location != StandardLocation.CLASS_OUTPUT || kind != JavaFileObject.Kind.CLASS
                            || classes.containsKey(path) || classes.size() >= request.maximumClasses())
                        throw new IOException("Closed bounded compiler class output required");
                    classes.put(path, new byte[0]);
                    return new SimpleJavaFileObject(URI.create("memory:///" + path), kind) {
                        @Override public OutputStream openOutputStream() {
                            return new LimitedOutput(request.maximumClassBytes(), bytes) {
                                @Override public void close() { classes.put(path, value()); }
                            };
                        }
                    };
                }
                @Override public FileObject getFileForOutput(Location location, String packageName,
                        String relativeName, FileObject sibling) throws IOException { throw new IOException("Unexpected compiler output"); }
            };
            if (!Boolean.TRUE.equals(compiler.getTask(null, manager, diagnostics, options, null, sources).call())) {
                String detail = diagnostics.getDiagnostics().stream().limit(8).map(item -> item.getKind() + ":" + item.getCode() + ":"
                                + (item.getSource() == null ? "compiler" : item.getSource().getName()) + ":" + item.getLineNumber()
                                + ":" + item.getMessage(java.util.Locale.ROOT).substring(0, Math.min(512, item.getMessage(java.util.Locale.ROOT).length())))
                        .reduce((left, right) -> left + ";" + right).orElse("compiler returned false");
                throw new IOException("Strict complete-main Java compilation failed: " + detail);
            }
            if (diagnostics.getDiagnostics().stream().anyMatch(item -> item.getKind() == Diagnostic.Kind.WARNING
                    || item.getKind() == Diagnostic.Kind.MANDATORY_WARNING || item.getKind() == Diagnostic.Kind.ERROR))
                throw new IOException("Strict compilation retained a warning/error");
        } catch (RuntimeException error) {
            throw new IOException("Strict compiler aborted before creating the bootstrap root", error);
        }
        for (Unit unit : units) {
            String path = unit.path().substring(0, unit.path().length() - 5) + ".class";
            if (!classes.containsKey(path)) throw new IOException("Main source missing its top-level class: " + path);
        }
        if (classes.isEmpty() || classes.values().stream().anyMatch(value -> value.length == 0)) throw new IOException("Complete class output required");
        return new Compilation(Map.copyOf(classes), options, bytes.get());
    }
    private static byte[] archive(Map<String, byte[]> entries, long maximum) throws IOException {
        var output = new LimitedOutput(maximum, new AtomicLong());
        try (var jar = new JarOutputStream(output)) {
            for (var item : entries.entrySet()) {
                ZipEntry entry = new ZipEntry(item.getKey()); entry.setTime(0); jar.putNextEntry(entry); jar.write(item.getValue()); jar.closeEntry();
            }
        }
        return output.value();
    }
    private static List<ArchiveEntry> verifyArchive(Path path, Map<String, byte[]> expected) throws IOException {
        var before = SharedSourceFiles.observe(path); Set<String> names = new HashSet<>(); List<ArchiveEntry> result = new ArrayList<>();
        try (JarFile jar = new JarFile(path.toFile(), true)) {
            var entries = jar.entries();
            while (entries.hasMoreElements()) {
                var entry = entries.nextElement(); byte[] wanted = expected.get(entry.getName());
                if (entry.isDirectory() || wanted == null || !names.add(entry.getName())) throw new IOException("Archive inventory differs");
                byte[] bytes;
                try (var input = jar.getInputStream(entry)) { bytes = input.readNBytes(Math.addExact(wanted.length, 1)); }
                if (!java.util.Arrays.equals(bytes, wanted)) throw new IOException("Archive entry body differs");
                result.add(new ArchiveEntry(entry.getName(), bytes.length, sha(bytes)));
            }
        }
        if (!names.equals(expected.keySet())) throw new IOException("Incomplete archive inventory");
        SharedSourceFiles.assertUnchanged(before); result.sort(Comparator.comparing(ArchiveEntry::path)); return List.copyOf(result);
    }
    private static SharedSourceFiles.Witness writeNew(Path path, byte[] bytes) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        try (FileChannel file = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(bytes); while (buffer.hasRemaining()) file.write(buffer); file.force(true);
        }
        var observed = SharedSourceFiles.observe(path);
        if (observed.source().bytes() != bytes.length || !observed.source().sha256().equals(sha(bytes)) || observed.nativeFile().linkCount() != 1)
            throw new IOException("Fresh bootstrap output body/native readback differs");
        return observed;
    }
    static byte[] exact(ControlBuild.FileRef ref, long maximum) throws IOException {
        if (maximum < 0 || maximum > Integer.MAX_VALUE || ref.bytes() < 0 || ref.bytes() >= Integer.MAX_VALUE || ref.bytes() > maximum) throw new IOException("Exact finite bootstrap input required");
        ref.verify(); byte[] bytes;
        try (var input = Files.newInputStream(Path.of(ref.path()))) { bytes = input.readNBytes(Math.toIntExact(ref.bytes() + 1)); }
        BoundedSourceInputGuard.verifyReadBytes(ref, bytes, Math.toIntExact(maximum)); return bytes;
    }
    private static void current(Request request) throws IOException {
        if (!WindowsJobProcess.currentMachineId().equals(request.machineId()) || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))
                || Thread.currentThread().isInterrupted()) throw new IOException("Bootstrap machine/deadline/interruption rejected");
    }
    private static Path absolute(String value) {
        Path path = Path.of(value); if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IllegalArgumentException("Canonical absolute output root required"); return path;
    }
    private static void relative(String value) {
        if (value == null || value.isEmpty() || value.startsWith("/") || value.indexOf((char) 92) >= 0
                || java.util.Arrays.stream(value.split("/", -1)).anyMatch(part -> !part.matches("[A-Za-z0-9_$.-]+") || part.equals(".") || part.equals("..")))
            throw new IllegalArgumentException("Canonical relative archive/source path required");
    }
    private static long round(long value) { return Math.multiplyExact(Math.floorDiv(Math.addExact(value, 4095), 4096), 4096); }
    private static LibraryRole role(String name) throws IOException {
        if (name.startsWith("jackson-annotations-")) return LibraryRole.ANNOTATIONS;
        if (name.startsWith("jackson-core-")) return LibraryRole.CORE;
        if (name.startsWith("jackson-databind-")) return LibraryRole.DATABIND;
        if (name.startsWith("jna-platform-")) return LibraryRole.JNA_PLATFORM;
        if (name.startsWith("jna-")) return LibraryRole.JNA;
        throw new IOException("Unknown bootstrap dependency role");
    }
    private static long finalCharge(Path root, Set<String> expectedLibraryNames) throws IOException {
        long result = directoryCharge(root);
        Set<String> rootNames = new HashSet<>(), libraryNames = new HashSet<>();
        try (var paths = Files.list(root)) {
            for (Path path : paths.toList()) {
                rootNames.add(path.getFileName().toString());
                if (path.getFileName().toString().equals("lib")) {
                    result = Math.addExact(result, directoryCharge(path));
                    try (var libraries = Files.list(path)) {
                        for (Path library : libraries.toList()) {
                            if (!libraryNames.add(library.getFileName().toString())) throw new IOException("Duplicate bootstrap library path");
                            result = Math.addExact(result, SharedSourceFiles.nativeFile(library).allocatedBytes());
                        }
                    }
                } else result = Math.addExact(result, SharedSourceFiles.nativeFile(path).allocatedBytes());
            }
        }
        if (!rootNames.equals(Set.of("ck3-control-bootstrap-tools.jar", "lib", "input-guard.actual.json", "actual.json"))
                || !libraryNames.equals(expectedLibraryNames)) throw new IOException("Final bootstrap closed root inventory differs");
        return result;
    }
    private static long directoryCharge(Path path) throws IOException {
        HANDLE handle = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path), 0x80, 1, null, 3, 0x02200000, null);
        if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("Bootstrap directory open Win32=" + Native.getLastError());
        try { return Math.max(4096L, SharedSourceFiles.nativeHeldDirectory(handle).allocatedBytes()); }
        finally { if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("Bootstrap directory close Win32=" + Native.getLastError()); }
    }
    /** No existing writer and no later writer/delete can change the five actual compiler library objects. */
    static final class Libraries implements AutoCloseable {
        private record Held(HANDLE handle, SharedSourceFiles.NativeFile original) { }
        private final List<Held> files = new ArrayList<>();
        void retain(Path path) throws IOException {
            SharedSourceFiles.plainAncestors(path);
            HANDLE handle = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path), 0x80000000, 1, null, 3, 0x00200000, null);
            if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("Immutable compiler library open Win32=" + Native.getLastError());
            try { files.add(new Held(handle, SharedSourceFiles.nativeHeldFile(handle))); }
            catch (IOException | RuntimeException error) { Kernel32.INSTANCE.CloseHandle(handle); throw error; }
        }
        void requireCurrent() throws IOException {
            for (Held held : files) if (!held.original().equals(SharedSourceFiles.nativeHeldFile(held.handle())))
                throw new IOException("Held compiler library native identity/content extent changed");
        }
        @Override public void close() throws IOException {
            IOException failure = null;
            for (int index = files.size() - 1; index >= 0; index--) {
                if (!Kernel32.INSTANCE.CloseHandle(files.get(index).handle())) {
                    IOException error = new IOException("Immutable library handle close Win32=" + Native.getLastError());
                    if (failure == null) failure = error; else failure.addSuppressed(error);
                }
            }
            if (failure != null) throw failure;
        }
    }
    static final class Directories implements AutoCloseable {
        private record Held(Path path, HANDLE handle, String identity) { }
        private final List<Held> directories = new ArrayList<>();
        void retainAncestors(Path path) throws IOException {
            int depth = 0;
            for (Path ancestor = path; ancestor != null; ancestor = ancestor.getParent()) {
                if (++depth > 64) throw new IOException("Bounded plain bootstrap ancestry required");
                retain(ancestor);
            }
            requireCurrent();
        }
        void retain(Path path) throws IOException {
            SharedSourceFiles.plainAncestors(path);
            // Attribute-only access does not participate in read/share custody; retain real directory read access.
            HANDLE handle = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path), 0x81, 1, null, 3, 0x02200000, null);
            if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("Bootstrap directory custody open Win32=" + Native.getLastError());
            try { directories.add(new Held(path, handle, SharedSourceFiles.nativeHeldDirectory(handle).identityKey())); }
            catch (IOException | RuntimeException error) { Kernel32.INSTANCE.CloseHandle(handle); throw error; }
        }
        void requireCurrent() throws IOException {
            for (Held held : directories) {
                if (!held.identity().equals(SharedSourceFiles.nativeHeldDirectory(held.handle()).identityKey()))
                    throw new IOException("Held bootstrap directory identity changed");
                SharedSourceFiles.plainAncestors(held.path());
                HANDLE current = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(held.path()), 0x80, 1, null, 3, 0x02200000, null);
                if (WinBase.INVALID_HANDLE_VALUE.equals(current)) throw new IOException("Bootstrap held directory path unavailable");
                try {
                    if (!held.identity().equals(SharedSourceFiles.nativeHeldDirectory(current).identityKey()))
                        throw new IOException("Bootstrap ancestor path no longer names its held original directory");
                } finally { if (!Kernel32.INSTANCE.CloseHandle(current)) throw new IOException("Bootstrap path observation close failed"); }
            }
        }
        @Override public void close() throws IOException {
            IOException failure = null;
            for (int index = directories.size() - 1; index >= 0; index--) {
                if (!Kernel32.INSTANCE.CloseHandle(directories.get(index).handle())) {
                    IOException error = new IOException("Bootstrap directory custody close Win32=" + Native.getLastError());
                    if (failure == null) failure = error; else failure.addSuppressed(error);
                }
            }
            if (failure != null) throw failure;
        }
    }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    private static class LimitedOutput extends OutputStream {
        private final long maximum; private final AtomicLong aggregate; private final ByteArrayOutputStream output = new ByteArrayOutputStream();
        LimitedOutput(long maximum, AtomicLong aggregate) { this.maximum = maximum; this.aggregate = aggregate; }
        @Override public void write(int value) throws IOException { byte[] one = { (byte) value }; write(one, 0, 1); }
        @Override public void write(byte[] value, int offset, int length) throws IOException {
            if (length < 0 || Math.addExact(aggregate.get(), length) > maximum) throw new IOException("Bounded compiler/archive output exceeded");
            aggregate.addAndGet(length); output.write(value, offset, length);
        }
        byte[] value() { return output.toByteArray(); }
    }
}
