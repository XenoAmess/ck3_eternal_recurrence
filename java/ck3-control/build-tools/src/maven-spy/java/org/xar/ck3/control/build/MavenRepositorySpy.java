package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.regex.Pattern;
import java.util.zip.ZipFile;
import org.apache.maven.eventspy.EventSpy;
import org.apache.maven.execution.ExecutionEvent;
import org.apache.maven.execution.MavenSession;

/** Compiled only against the observed default Maven lib; not a new application dependency. */
public final class MavenRepositorySpy implements EventSpy {
    private static final long MIB = 1L << 20;
    private static final long DIRECTORY_LIMIT = 32 * MIB;
    private static final Pattern ANSI = Pattern.compile("\u001b\\[[0-?]*[ -/]*[@-~]");
    private static final Pattern MANAGER = Pattern.compile("Using manager (.+?) for (.+)$");
    private static final Pattern INSTALL = Pattern.compile("Installing .+ to (.+ck3-save-core-0\\.1\\.0\\.(?:jar|pom))$");
    private static final Pattern LOAD = Pattern.compile("\\[class,load] ([A-Za-z0-9_.$]+) source: (.+)$");
    private static final Pattern LOAD_PID = Pattern.compile("^\\[[^\\]]+]\\[([1-9][0-9]{0,18})]\\[info]\\[class,load]");
    private static final Set<String> RESOLVERS = Set.of(
            "io.quarkus.bootstrap.resolver.maven.BootstrapMavenContext",
            "io.quarkus.bootstrap.resolver.maven.MavenArtifactResolver",
            "io.quarkus.maven.QuarkusBootstrapProvider",
            "io.quarkus.bootstrap.util.PropertyUtils",
            "io.quarkus.maven.components.QuarkusWorkspaceProvider",
            "org.eclipse.aether.internal.impl.DefaultLocalRepositoryProvider",
            "org.eclipse.aether.repository.LocalRepository");
    private int observations;

    public record SessionActual(String schema, String machineId, String sourceCommit, String observedAtUtc,
            String processIdDecimal, String event, String settingsLocalRepository, String sessionLocalRepository,
            String quarkusLocalRepoEnvironment, String mavenRepoLocalSystemProperty,
            CiBootstrap.FilePin userSettingsRef, CiBootstrap.FilePin globalSettingsRef, String unavailable) { }
    public record BindingActual(String schema, String machineId, String sourceCommit, String observedAtUtc,
            String repository, List<CiBootstrap.FilePin> originalLeafLogs, List<CiBootstrap.FilePin> installedLeaf,
            String evidenceScope) {
        public BindingActual { originalLeafLogs = List.copyOf(originalLeafLogs); installedLeaf = List.copyOf(installedLeaf); }
    }
    public record CommandActual(String schema, String startedAtUtc, String finishedAtUtc, String processIdDecimal,
            List<String> command, int originalExit, String stopReason, CiBootstrap.FilePin stdoutRef,
            CiBootstrap.FilePin stderrRef, CiBootstrap.FilePin commandFileRef, String scope) {
        public CommandActual { command = List.copyOf(command); }
    }
    public record Manager(String phase, String stream, boolean afterGenerateCodeTests, String manager, String repository) { }
    public record LoadedClass(String binaryName, String source, String processIdDecimal) { }
    public record ClassActual(String binaryName, String observedSource, String processIdDecimal, String evidenceScope,
            CiBootstrap.FilePin jarRef, String classEntry, long classBytes, String classSha256,
            CiBootstrap.FilePin javapRef, Integer javapOriginalExit, String unavailable) { }
    public record DiagnosticActual(String schema, String machineId, String sourceCommit, String observedAtUtc,
            List<CiBootstrap.FilePin> sessionObservations, List<Manager> managers, List<ClassActual> loadedClasses,
            CiBootstrap.FilePin originalMavenWaitRef, List<CiBootstrap.FilePin> selectedGavFiles,
            boolean diagnosticComplete, String unavailable, String scope) {
        public DiagnosticActual {
            sessionObservations = List.copyOf(sessionObservations); managers = List.copyOf(managers);
            loadedClasses = List.copyOf(loadedClasses); selectedGavFiles = List.copyOf(selectedGavFiles);
        }
    }
    record LogFacts(List<Manager> managers, List<LoadedClass> loadedClasses, Set<Path> installTargets) {
        LogFacts { managers = List.copyOf(managers); loadedClasses = List.copyOf(loadedClasses); installTargets = Set.copyOf(installTargets); }
    }

    @Override public void init(Context context) { }
    @Override public void close() { }

    @Override public void onEvent(Object event) {
        if (!(event instanceof ExecutionEvent execution)) return;
        boolean interesting = execution.getType() == ExecutionEvent.Type.SessionStarted
                || execution.getType() == ExecutionEvent.Type.SessionEnded
                || execution.getType() == ExecutionEvent.Type.MojoStarted && execution.getMojoExecution() != null
                && "quarkus-maven-plugin".equals(execution.getMojoExecution().getArtifactId())
                && "generate-code-tests".equals(execution.getMojoExecution().getGoal());
        if (!interesting || observations >= 8) return;
        try {
            Path root = plainDirectory(System.getProperty("xar.maven.repository.diagnostic.root"));
            Path owner = root.resolve("maven-jvm.pid"); String actualPid = Long.toString(ProcessHandle.current().pid());
            if (!Files.exists(owner, LinkOption.NOFOLLOW_LINKS) && execution.getType() == ExecutionEvent.Type.SessionStarted) {
                try { Files.writeString(owner, actualPid, StandardCharsets.US_ASCII, StandardOpenOption.CREATE_NEW); }
                catch (java.nio.file.FileAlreadyExistsException anotherJvm) { /* The original session is the sole observer owner. */ }
            }
            if (!Files.exists(owner, LinkOption.NOFOLLOW_LINKS)
                    || !actualPid.equals(Files.readString(owner, StandardCharsets.US_ASCII))) return;
            int ordinal = ++observations;
            SessionActual actual = sessionActual(execution.getSession(), execution.getType().name());
            CiBootstrap.publish(root.resolve("maven-session-" + ordinal + ".actual.json"), actual);
        } catch (IOException | RuntimeException failure) {
            // A diagnostic must not replace the original Maven business outcome.
            System.err.println("XAR_REPOSITORY_OBSERVER_UNAVAILABLE " + failure.getClass().getSimpleName());
        }
    }

    @SuppressWarnings("deprecation") // Maven 3's actual effective Settings are required, never reconstructed.
    private static SessionActual sessionActual(MavenSession session, String event) throws IOException {
        String settings = null, repository = null, unavailable = null;
        CiBootstrap.FilePin user = null, global = null;
        if (session == null) unavailable = "ExecutionEvent has no actual MavenSession";
        else {
            if (session.getSettings() != null) settings = session.getSettings().getLocalRepository();
            var resolver = session.getRepositorySession();
            if (resolver != null && resolver.getLocalRepositoryManager() != null)
                repository = resolver.getLocalRepositoryManager().getRepository().getBasedir().getAbsolutePath();
            if (session.getRequest() != null) {
                user = settingsPin(session.getRequest().getUserSettingsFile());
                global = settingsPin(session.getRequest().getGlobalSettingsFile());
            }
            if (settings == null || repository == null) unavailable = "Actual effective settings or session local repository unavailable";
        }
        return new SessionActual("xar.maven-repository-session/v1", property("xar.maven.repository.machine"),
                sourceCommit(), Instant.now().toString(), Long.toString(ProcessHandle.current().pid()), event,
                scalar(settings), scalar(repository), scalar(System.getenv("QUARKUS_LOCAL_REPO")),
                scalar(System.getProperty("maven.repo.local")), user, global, unavailable);
    }

    private static CiBootstrap.FilePin settingsPin(java.io.File file) throws IOException {
        if (file == null || !Files.exists(file.toPath(), LinkOption.NOFOLLOW_LINKS)) return null;
        // Only a digest of the original file is retained; credentials/XML are never copied or printed.
        return boundedPin(file.toPath(), 4 * MIB);
    }

    /** Called by the JDK-only bootstrap after its source/installation-bound extension build. */
    public static int execute(String mode, Path repository, Path root, String machine, Path extension,
            String[] mavenArguments) throws Exception {
        plainDirectory(root.toString()); plainDirectory(repository.toString());
        return switch (mode) {
            case "leaf" -> runMaven(repository, root, mavenArguments, true);
            case "prepare" -> { prepare(root, machine, extension); yield 0; }
            case "run" -> runMaven(repository, root, mavenArguments, false);
            case "collect" -> collect(root, machine);
            default -> throw new IllegalArgumentException("Known product Maven diagnostic mode required");
        };
    }

    private static void prepare(Path root, String machine, Path extension) throws IOException {
        List<CiBootstrap.FilePin> logs = new ArrayList<>();
        List<Manager> managers = new ArrayList<>(); Set<Path> targets = new LinkedHashSet<>();
        for (String stream : List.of("stdout", "stderr")) {
            Path log = root.resolve("leaf." + stream + ".log"); logs.add(boundedPin(log, 2 * MIB));
            LogFacts facts = logFacts(log, "leaf", stream); managers.addAll(facts.managers()); targets.addAll(facts.installTargets());
        }
        if (!Files.readString(root.resolve("leaf.exit.txt"), StandardCharsets.UTF_8).strip().equals("0"))
            throw new IOException("Actual successful original leaf exit required");
        Set<Path> repositories = new LinkedHashSet<>();
        for (Manager manager : managers) repositories.add(absolute(manager.repository()).toRealPath());
        if (repositories.size() != 1) throw new IOException("One observed leaf repository required; no guessed fallback");
        Path repository = repositories.iterator().next(), gav = gav(repository);
        Set<Path> expected = Set.of(gav.resolve("ck3-save-core-0.1.0.jar"), gav.resolve("ck3-save-core-0.1.0.pom"));
        if (!targets.equals(expected)) throw new IOException("Observed leaf install targets differ from its actual repository");
        List<CiBootstrap.FilePin> files = new ArrayList<>();
        for (Path path : expected.stream().sorted().toList()) files.add(boundedPin(path, MIB));
        CiBootstrap.publish(root.resolve("repository-binding.actual.json"), new BindingActual(
                "xar.maven-observed-leaf-binding/v2", machine, sourceCommit(), Instant.now().toString(),
                repository.toString(), logs, files, "Original leaf wait0, LRM and installed GAV; no product or pipeline qualification"));
        String inherited = System.getenv().getOrDefault("MAVEN_OPTS", "");
        if (inheritedProperty(inherited, "xar.maven.repository.diagnostic.root") != null)
            throw new IOException("A previous owned Maven repository observer is still bound");
        String priorExtensions = inheritedProperty(inherited, "maven.ext.class.path");
        String extensions = priorExtensions == null ? extension.toString() : priorExtensions + java.io.File.pathSeparator + extension;
        String options = inherited
                + " -verbose:class -Xlog:class+load=info:stdout:uptime,pid,level,tags " + jvmProperty("maven.ext.class.path", extensions)
                + " " + jvmProperty("xar.maven.repository.diagnostic.root", root.toString())
                + " " + jvmProperty("xar.maven.repository.machine", machine);
        Path environment = absolute(propertyEnvironment("GITHUB_ENV"));
        Files.writeString(environment, "QUARKUS_LOCAL_REPO=" + scalar(repository.toString())
                + "\nMAVEN_OPTS=" + scalar(options) + "\n", StandardCharsets.UTF_8, StandardOpenOption.APPEND);
        requireDirectoryBound(root);
    }

    static String inheritedProperty(String options, String name) throws IOException {
        String found = null; StringBuilder token = new StringBuilder(); boolean quoted = false;
        for (int index = 0; index <= options.length(); index++) {
            char character = index == options.length() ? ' ' : options.charAt(index);
            if (character == '"') { quoted = !quoted; continue; }
            if (Character.isWhitespace(character) && !quoted) {
                String item = token.toString(); token.setLength(0);
                if (item.startsWith("-D" + name + "=")) {
                    if (found != null) throw new IOException("Ambiguous inherited Maven extension property");
                    found = scalar(item.substring(name.length() + 3));
                }
            } else token.append(character);
        }
        if (quoted) throw new IOException("Unclosed inherited Maven JVM option quote");
        return found;
    }

    static String jvmProperty(String name, String value) throws IOException {
        if (!name.matches("[A-Za-z0-9.]+") || value == null || value.isBlank()
                || value.chars().anyMatch(c -> c == '"' || c == '\r' || c == '\n' || c == 0))
            throw new IOException("Exact scalar quoted JVM property required");
        return "\"-D" + name + "=" + value + "\"";
    }

    private static int runMaven(Path repository, Path root, String[] arguments, boolean leaf) throws Exception {
        if (arguments.length == 0 || !List.of(arguments).contains(leaf ? "install" : "verify"))
            throw new IllegalArgumentException("Original complete leaf install/product verify arguments required");
        String label = leaf ? "leaf" : "product";
        Path batch = root.resolve(label + "-maven.cmd");
        StringBuilder command = new StringBuilder("@echo off\r\ncall mvn");
        for (String argument : arguments) command.append(' ').append(cmdArgument(argument));
        command.append("\r\nexit /b %errorlevel%\r\n");
        Files.writeString(batch, command, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        Path system = absolute(propertyEnvironment("SystemRoot"));
        List<String> invocation = List.of(system.resolve("System32/cmd.exe").toString(), "/d", "/c", batch.toString());
        CommandActual result = capture(invocation, repository, root.resolve(label + ".stdout.log"),
                root.resolve(label + ".stderr.log"), (leaf ? 2 : 20) * MIB, 25 * 60_000L, root);
        CiBootstrap.publish(root.resolve(label + ".original-wait.actual.json"), result);
        if (leaf) Files.writeString(root.resolve("leaf.exit.txt"), Integer.toString(result.originalExit()), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        System.out.println("Original " + label + " Maven exit=" + result.originalExit() + ", stopReason=" + result.stopReason()
                + "; full original logs: " + root.resolve(label + ".stdout.log") + ", " + root.resolve(label + ".stderr.log"));
        return result.stopReason() == null ? result.originalExit() : 1;
    }

    static String cmdArgument(String value) throws IOException {
        if (value == null || value.isEmpty() || value.chars().anyMatch(c -> "\"\r\n\u0000&|<>^%!".indexOf(c) >= 0))
            throw new IOException("Plain exact original Maven argument required");
        return "\"" + value + "\"";
    }

    private static int collect(Path root, String machine) throws Exception {
        List<Manager> managers = new ArrayList<>(); List<LoadedClass> loaded = new ArrayList<>();
        List<CiBootstrap.FilePin> sessions = new ArrayList<>(), gavFiles = new ArrayList<>();
        List<ClassActual> classes = new ArrayList<>(); String unavailable = null;
        try {
            Path pidFile = root.resolve("maven-jvm.pid"); boundedPin(pidFile, 32);
            String originalJvmPid = Files.readString(pidFile, StandardCharsets.US_ASCII);
            if (!originalJvmPid.matches("[1-9][0-9]{0,18}")) throw new IOException("Original Maven JVM decimal PID required");
            for (String phase : List.of("leaf", "product")) for (String stream : List.of("stdout", "stderr")) {
                LogFacts facts = logFacts(root.resolve(phase + "." + stream + ".log"), phase, stream);
                managers.addAll(facts.managers());
                for (LoadedClass item : facts.loadedClasses())
                    if (isOriginalJvmClass(item, originalJvmPid) && !loaded.contains(item)) loaded.add(item);
            }
            try (var files = Files.list(root)) {
                for (Path file : files.filter(path -> path.getFileName().toString().matches("maven-session-[1-8]\\.actual\\.json")).sorted().toList())
                    { sessions.add(boundedPin(file, 64 * 1024)); if (!CiBootstrap.repositorySessionComplete(file, machine, originalJvmPid)) unavailable = "Actual Maven session fields unavailable"; }
            }
            for (LoadedClass item : loaded) classes.add(inspectClass(item, root, classes.size()));
            Set<Path> selected = new LinkedHashSet<>();
            for (Manager manager : managers) if (selected.size() < 8) selected.add(gav(absolute(manager.repository())));
            for (Path directory : selected) for (String extension : List.of("jar", "pom")) {
                Path path = directory.resolve("ck3-save-core-0.1.0." + extension);
                if (Files.exists(path, LinkOption.NOFOLLOW_LINKS)) gavFiles.add(boundedPin(path, MIB));
            }
            if (sessions.isEmpty()) unavailable = "No actual same-Maven-JVM EventSpy session observation";
            if (classes.stream().noneMatch(item -> item.binaryName().equals("io.quarkus.bootstrap.resolver.maven.BootstrapMavenContext") && item.unavailable() == null))
                unavailable = "No complete actual Quarkus BootstrapMavenContext load-origin/JAR/class/javap evidence";
        } catch (IOException | RuntimeException failure) { unavailable = failure.getClass().getSimpleName() + ": " + failure.getMessage(); }
        Path wait = root.resolve("product.original-wait.actual.json");
        CiBootstrap.FilePin waitRef = Files.exists(wait) ? boundedPin(wait, 64 * 1024) : null;
        if (waitRef == null) unavailable = "Original product Maven wait unavailable";
        CiBootstrap.publish(root.resolve("gav-readback.actual.json"), new DiagnosticActual(
                "xar.maven-repository-diagnostic/v2", machine, sourceCommit(), Instant.now().toString(),
                sessions, List.copyOf(managers), classes, waitRef, gavFiles, unavailable == null, unavailable,
                "Observation only. Session fields are actual Maven API values; class origins come only from this original Maven JVM verbose-class stdout. JAR/class bytes are measured after that process and unchanged through same-JAR javap; no in-memory-byte or defining-loader-instance claim. No Class.forName, candidate classpath or upstream-tag inference. Original Maven business exit is separate."));
        requireDirectoryBound(root);
        return unavailable == null ? 0 : 1;
    }

    static LogFacts logFacts(Path path, String phase, String stream) throws IOException {
        boundedPin(path, phase.equals("product") ? 24 * MIB : 2 * MIB);
        List<Manager> managers = new ArrayList<>(); List<LoadedClass> classes = new ArrayList<>();
        Set<Path> targets = new LinkedHashSet<>(); boolean afterTest = false;
        try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String raw;
            while ((raw = reader.readLine()) != null) {
                if (raw.length() > 64 * 1024) throw new IOException("Bounded original Maven log line required");
                String line = ANSI.matcher(raw).replaceAll("");
                if (line.contains("--- quarkus:") && line.contains(":generate-code-tests ")) afterTest = true;
                var manager = MANAGER.matcher(line);
                if (manager.find()) {
                    Manager observation = new Manager(phase, stream, afterTest, scalar(manager.group(1)), scalar(manager.group(2)));
                    if (!managers.contains(observation)) { if (managers.size() >= 24) throw new IOException("Too many original repository observations"); managers.add(observation); }
                }
                var install = INSTALL.matcher(line);
                if (install.find()) { if (targets.size() >= 8) throw new IOException("Too many original leaf targets"); targets.add(absolute(install.group(1))); }
                var origin = LOAD.matcher(line);
                if (phase.equals("product") && origin.find() && isObservedTarget(origin.group(1))) {
                    var pid = LOAD_PID.matcher(line);
                    LoadedClass observation = new LoadedClass(origin.group(1), scalar(origin.group(2)), pid.find() ? pid.group(1) : null);
                    if (!classes.contains(observation)) { if (classes.size() >= 12) throw new IOException("Too many actual resolver class origins"); classes.add(observation); }
                }
            }
        }
        return new LogFacts(managers, classes, targets);
    }

    static boolean isObservedTarget(String binaryName) {
        return RESOLVERS.contains(binaryName) || binaryName.startsWith("io.quarkus.maven.QuarkusBootstrapProvider$");
    }

    static boolean isOriginalJvmClass(LoadedClass loaded, String originalJvmPid) {
        return originalJvmPid.equals(loaded.processIdDecimal());
    }

    static ClassActual inspectClass(LoadedClass loaded, Path root, int ordinal) throws Exception {
        CiBootstrap.FilePin jarRef = null, javapRef = null; String entryName = loaded.binaryName().replace('.', '/') + ".class";
        long bytes = 0; String sha = null; Integer exit = null;
        try {
            if (!isObservedTarget(loaded.binaryName())) throw new IOException("Only originally observed resolver classes allowed");
            java.net.URI source = java.net.URI.create(loaded.source());
            if (!source.getScheme().equals("file")) throw new IOException("Actual local JAR class code-source required");
            Path jar = Path.of(source).toRealPath();
            if (!jar.getFileName().toString().endsWith(".jar")) throw new IOException("Actual loaded class did not originate in a JAR");
            jarRef = boundedPin(jar, 64 * MIB);
            try (ZipFile zip = new ZipFile(jar.toFile())) {
                var entries = zip.stream().filter(entry -> entry.getName().equals(entryName)).toList();
                if (entries.size() != 1 || entries.getFirst().isDirectory()) throw new IOException("One exact actual JAR class entry required");
                try (InputStream input = zip.getInputStream(entries.getFirst())) {
                    byte[] raw = input.readNBytes((int) MIB + 1); if (raw.length == 0 || raw.length > MIB) throw new IOException("Bounded loaded class required");
                    bytes = raw.length; sha = sha256(raw);
                }
            }
            Path javaHome = absolute(System.getProperty("java.home"));
            Path stdout = root.resolve("javap-" + ordinal + ".log"), stderr = root.resolve("javap-" + ordinal + ".stderr.log");
            CommandActual result = capture(List.of(javaHome.resolve("bin/javap.exe").toString(), "-c", "-p", "-classpath", jar.toString(), loaded.binaryName()),
                    root, stdout, stderr, 192 * 1024, 20_000, root);
            CiBootstrap.publish(root.resolve("javap-" + ordinal + ".original-wait.actual.json"), result);
            exit = result.originalExit(); javapRef = boundedPin(stdout, 192 * 1024);
            if (!jarRef.equals(boundedPin(jar, 64 * MIB))) throw new IOException("Actual loaded JAR changed during bytecode observation");
            if (exit != 0 || result.stopReason() != null) throw new IOException("Actual same-JAR javap did not complete");
            return new ClassActual(loaded.binaryName(), loaded.source(), loaded.processIdDecimal(), "ORIGINAL_MAVEN_JVM_VERBOSE_CLASS_LOAD", jarRef, entryName, bytes, sha, javapRef, exit, null);
        } catch (IOException | IllegalArgumentException failure) {
            return new ClassActual(loaded.binaryName(), loaded.source(), loaded.processIdDecimal(), "ORIGINAL_MAVEN_JVM_VERBOSE_CLASS_LOAD", jarRef, entryName, bytes, sha, javapRef, exit, failure.getClass().getSimpleName() + ": " + failure.getMessage());
        }
    }

    private static CommandActual capture(List<String> command, Path cwd, Path stdout, Path stderr,
            long maximum, long timeoutMillis, Path root) throws IOException, InterruptedException {
        String started = Instant.now().toString(); long deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(timeoutMillis);
        if (Files.exists(stdout) || Files.exists(stderr)) throw new IOException("New unique original command logs required");
        CiBootstrap.FilePin commandFile = command.size() == 4 && command.getLast().endsWith(".cmd")
                ? boundedPin(Path.of(command.getLast()), 64 * 1024) : null;
        Process child = new ProcessBuilder(command).directory(cwd.toFile()).start();
        child.getOutputStream().close();
        Quota quota = new Quota(maximum); AtomicReference<IOException> failure = new AtomicReference<>();
        Thread out = pump(child.getInputStream(), stdout, quota, failure), err = pump(child.getErrorStream(), stderr, quota, failure);
        String stopped = null;
        try {
            while (!child.waitFor(100, TimeUnit.MILLISECONDS)) {
                if (failure.get() != null || System.nanoTime() >= deadline) {
                    stopped = failure.get() == null ? "ORIGINAL_COMMAND_TIMEOUT" : "DIAGNOSTIC_OUTPUT_LIMIT_OR_IO"; break;
                }
                requireDirectoryBound(root);
            }
        } catch (IOException limit) { stopped = "DIAGNOSTIC_DIRECTORY_LIMIT_OR_IO"; }
        finally {
            if (child.isAlive()) {
                for (ProcessHandle descendant : child.descendants().toList().reversed()) if (descendant.isAlive()) descendant.destroyForcibly();
                child.destroyForcibly();
            }
            if (!child.waitFor(10, TimeUnit.SECONDS)) throw new IOException("Original command terminal unavailable");
            out.join(10_000); err.join(10_000);
            if (out.isAlive() || err.isAlive()) throw new IOException("Original stream terminal unavailable");
        }
        if (failure.get() != null && stopped == null) stopped = "DIAGNOSTIC_OUTPUT_LIMIT_OR_IO";
        if (commandFile != null && !commandFile.equals(boundedPin(Path.of(commandFile.path()), 64 * 1024)))
            throw new IOException("Original Maven command file changed during its process");
        return new CommandActual("xar.product-maven-original-command/v1", started, Instant.now().toString(),
                Long.toString(child.pid()), List.copyOf(command), child.exitValue(), stopped,
                boundedPin(stdout, maximum), boundedPin(stderr, maximum), commandFile, "Original process wait; diagnostic termination is distinct from ordinary Maven business failure");
    }

    private static Thread pump(InputStream input, Path destination, Quota quota, AtomicReference<IOException> failure) {
        return Thread.ofPlatform().start(() -> {
            try (input; OutputStream output = Files.newOutputStream(destination, StandardOpenOption.CREATE_NEW)) {
                byte[] buffer = new byte[8192]; int count;
                while ((count = input.read(buffer)) != -1) {
                    if (failure.get() != null) continue;
                    try { quota.reserve(count); output.write(buffer, 0, count); }
                    catch (IOException limit) { failure.compareAndSet(null, limit); }
                }
            } catch (IOException error) { failure.compareAndSet(null, error); }
        });
    }

    private static final class Quota {
        private final long maximum; private long used;
        Quota(long maximum) { this.maximum = maximum; }
        synchronized void reserve(int bytes) throws IOException {
            if (bytes < 0 || bytes > maximum - used) throw new IOException("Original stream evidence bound exceeded"); used += bytes;
        }
    }

    static CiBootstrap.FilePin boundedPin(Path path, long maximum) throws IOException {
        var attrs = Files.readAttributes(path, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (!attrs.isRegularFile() || attrs.isSymbolicLink() || attrs.isOther() || attrs.size() > maximum)
            throw new IOException("Bounded original plain file required: " + path);
        return CiBootstrap.measure(path);
    }
    static long requireDirectoryBound(Path root) throws IOException {
        long total = 0;
        try (var paths = Files.walk(root)) {
            var iterator = paths.iterator(); int entries = 0;
            while (iterator.hasNext()) {
                Path path = iterator.next(); if (++entries > 1024) throw new IOException("Diagnostic entry bound exceeded");
                var attributes = Files.readAttributes(path, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                if (attributes.isSymbolicLink() || attributes.isOther()) throw new IOException("Plain diagnostic tree required");
                if (attributes.isRegularFile()) { total = Math.addExact(total, attributes.size()); if (total > DIRECTORY_LIMIT) throw new IOException("Diagnostic 32MiB bound exceeded"); }
            }
        }
        return total;
    }
    private static Path gav(Path repository) { return repository.resolve("org/xar/ck3/ck3-save-core/0.1.0"); }
    private static Path absolute(String value) throws IOException {
        scalar(value); Path path = Path.of(value); if (!path.isAbsolute()) throw new IOException("Actual absolute path required"); return path.normalize();
    }
    private static Path plainDirectory(String value) throws IOException {
        Path path = absolute(value);
        if (!Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(path)) throw new IOException("Plain existing diagnostic directory required");
        return path.toRealPath();
    }
    private static String scalar(String value) throws IOException {
        if (value != null && (value.length() > 16 * 1024 || value.chars().anyMatch(c -> c == 0 || c == '\r' || c == '\n')))
            throw new IOException("Bounded safe scalar required"); return value;
    }
    private static String property(String name) throws IOException {
        String value = scalar(System.getProperty(name)); if (value == null || value.isBlank()) throw new IOException("Required diagnostic property unavailable: " + name); return value;
    }
    private static String propertyEnvironment(String name) throws IOException {
        String value = scalar(System.getenv(name)); if (value == null || value.isBlank()) throw new IOException("Required diagnostic environment unavailable: " + name); return value;
    }
    private static String sourceCommit() throws IOException {
        String value = propertyEnvironment("GITHUB_SHA"); if (!value.matches("[a-f0-9]{40}")) throw new IOException("Exact source commit required"); return value;
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
