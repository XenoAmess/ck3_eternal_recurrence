package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Single native child lifecycle for both closed finance and manifest-selected original captures. */
public final class CompiledCaptureProcess {
    public record Environment(String name, String value) {
        public Environment {
            if (name == null || value == null || !name.matches("(XAR_[A-Z0-9_]+|PYTHONOPTIMIZE)")
                    || name.length() > 128 || value.length() > 4096 || value.indexOf('\0') >= 0
                    || (name.equals("PYTHONOPTIMIZE") && !value.equals("0"))) {
                throw new IllegalArgumentException("Explicit finite original-fixture environment required");
            }
        }
    }
    record Plan(List<String> command, String cwd, String temporaryRoot, String outputRoot,
            String stdoutPath, String stderrPath, String outputPath, long outputMaximumBytes,
            long treeMaximumBytes, int timeoutSeconds, String deadlineUtc, long memoryBytes,
            List<Environment> environment) {
        Plan {
            command = List.copyOf(command); environment = List.copyOf(environment);
            if (command.isEmpty() || command.size() > 80 || outputMaximumBytes < 1
                    || treeMaximumBytes < outputMaximumBytes || treeMaximumBytes > (8L << 20)
                    || timeoutSeconds < 1 || timeoutSeconds > 120 || environment.size() > 32
                    || environment.stream().map(Environment::name).distinct().count() != environment.size()) {
                throw new IllegalArgumentException("Finite single owned capture plan required");
            }
            Instant.parse(deadlineUtc);
        }
    }
    static final class StartState {
        private boolean started;
        boolean started() { return started; }
    }
    private CompiledCaptureProcess() { }

    static WindowsJobProcess.CommandResult run(Plan plan, StartState state) throws IOException, InterruptedException {
        Path temporary = Path.of(plan.temporaryRoot()), root = Path.of(plan.outputRoot());
        Path stdout = Path.of(plan.stdoutPath()), stderr = Path.of(plan.stderrPath()), output = Path.of(plan.outputPath());
        Map<String,String> env = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); env.putAll(System.getenv());
        env.remove("JAVA_TOOL_OPTIONS"); env.remove("JDK_JAVA_OPTIONS"); env.remove("_JAVA_OPTIONS");
        for (String name : List.of("TEMP", "TMP", "TMPDIR")) env.put(name, temporary.toString());
        env.put("PYTHONDONTWRITEBYTECODE", "1"); env.put("PYTHONUTF8", "1");
        env.put("PYTHONIOENCODING", "utf-8"); env.put("OPENBLAS_NUM_THREADS", "1"); env.put("OMP_NUM_THREADS", "1");
        for (Environment item : plan.environment()) env.put(item.name(), item.value());
        Instant deadline = Instant.parse(plan.deadlineUtc());
        var spec = new WindowsJobProcess.CommandSpec(Path.of(plan.command().getFirst()),
                plan.command().subList(1, plan.command().size()), Path.of(plan.cwd()),
                Map.copyOf(env), stdout, stderr, plan.memoryBytes());
        try (var child = WindowsJobProcess.start(spec)) {
            state.started = true;
            return child.await(Duration.ofSeconds(plan.timeoutSeconds()), deadline, () -> {
                if (!Instant.now().isBefore(deadline)) throw new IllegalStateException("Capture deadline expired");
                try {
                    for (Path log : List.of(stdout, stderr)) if (Files.exists(log) && Files.size(log) > 65536) {
                        throw new IOException("Capture log exceeded64KiB");
                    }
                    long outputBytes = 0;
                    if (Files.isDirectory(output, LinkOption.NOFOLLOW_LINKS)) {
                        try (var paths = Files.walk(output)) {
                            var iterator = paths.iterator(); int count = 0;
                            while (iterator.hasNext()) {
                                Path path = iterator.next(); SharedSourceFiles.plainAncestors(path);
                                if (++count > 4097) throw new IOException("Finite output directory required");
                                if (Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) outputBytes = Math.addExact(outputBytes, Files.size(path));
                            }
                        }
                    } else if (Files.exists(output)) outputBytes = Files.size(output);
                    if (outputBytes > plan.outputMaximumBytes()) {
                        throw new IOException("Capture output exceeded its declared bound");
                    }
                    long bytes = 0; int entries = 0;
                    try (var files = Files.walk(root)) {
                        for (Path file : files.toList()) {
                            if (++entries > 8192 || Files.isSymbolicLink(file)) throw new IOException("Finite ordinary output tree required");
                            if (Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)) bytes = Math.addExact(bytes, Files.size(file));
                            if (bytes > plan.treeMaximumBytes()) throw new IOException("Capture output tree exceeded declared bound");
                        }
                    }
                } catch (IOException error) { throw new IllegalStateException("Capture storage monitor failed", error); }
            });
        }
    }
}
