package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** Single native child lifecycle for both closed finance and manifest-selected original captures. */
public final class CompiledCaptureProcess {
    /** Actual argv and identity of the same child handed to the native process owner. */
    public record InvocationEvidence(List<String> physicalArguments,
            WindowsJobProcess.ProcessIdentity actualProcess,
            SharedSourceFiles.Witness preparation,JavaUtf8NativeCustody.Evidence nativeSources) {
        public InvocationEvidence {
            physicalArguments = List.copyOf(physicalArguments);
            Objects.requireNonNull(actualProcess);
            if(preparation!=null){
                Objects.requireNonNull(preparation.source());Objects.requireNonNull(preparation.nativeFile());
                if(preparation.source().bytes()<1||preparation.source().bytes()>CiBootstrap.JavaUtf8Invocation.MAXIMUM_ENVELOPE_BYTES
                        ||preparation.source().bytes()!=preparation.nativeFile().logicalBytes()||preparation.nativeFile().linkCount()!=1)
                    throw new IllegalArgumentException("Exact finite actual preparation native witness required");
            }
            if (physicalArguments.isEmpty() || physicalArguments.size() > 80
                    || physicalArguments.stream().anyMatch(value -> value == null || value.indexOf('\0') >= 0)) {
                throw new IllegalArgumentException("Finite actual Java invocation required");
            }
        }
    }
    /** Explicit old metadata only. Never converted to current JDK metadata or actual native custody. */
    public record HistoricalPreparationPin(String path,long bytes,String sha256,String nativeKey) {
        public HistoricalPreparationPin {
            if(path==null||!Path.of(path).isAbsolute()||bytes<0||bytes>(2L<<30)
                    ||sha256==null||!sha256.matches("[0-9a-f]{64}")||nativeKey==null||nativeKey.indexOf('\0')>=0)
                throw new IllegalArgumentException("Exact historical opaque preparation metadata required");
        }
    }
    public record HistoricalInvocationV1(List<String> physicalArguments,WindowsJobProcess.ProcessIdentity actualProcess) {
        public HistoricalInvocationV1 { physicalArguments=historicalPhysical(physicalArguments);Objects.requireNonNull(actualProcess); }
    }
    public record HistoricalInvocationV2(List<String> physicalArguments,WindowsJobProcess.ProcessIdentity actualProcess,
            HistoricalPreparationPin preparation) {
        public HistoricalInvocationV2 { physicalArguments=historicalPhysical(physicalArguments);Objects.requireNonNull(actualProcess); }
    }
    public static byte[] encodeHistoricalInvocationV1(HistoricalInvocationV1 value)throws IOException {
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(Objects.requireNonNull(value));historyBound(bytes);return bytes;
    }
    public static HistoricalInvocationV1 decodeHistoricalInvocationV1(byte[] bytes)throws IOException {
        historyBound(bytes);return ControlBuild.strictMapper().readValue(bytes,HistoricalInvocationV1.class);
    }
    public static byte[] encodeHistoricalInvocationV2(HistoricalInvocationV2 value)throws IOException {
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(Objects.requireNonNull(value));historyBound(bytes);return bytes;
    }
    public static HistoricalInvocationV2 decodeHistoricalInvocationV2(byte[] bytes)throws IOException {
        historyBound(bytes);return ControlBuild.strictMapper().readValue(bytes,HistoricalInvocationV2.class);
    }
    private static List<String> historicalPhysical(List<String> arguments){
        var values=List.copyOf(arguments);
        if(values.isEmpty()||values.size()>80||values.stream().anyMatch(value->value.indexOf((char)0)>=0))
            throw new IllegalArgumentException("Finite retained historical physical argv required");
        return values;
    }
    private static void historyBound(byte[] bytes)throws IOException {
        if(bytes==null||bytes.length<1||bytes.length>(256<<10))throw new IOException("Finite explicit historical invocation required");
    }
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
        private InvocationEvidence actualEvidence;
        private CiBootstrap.JavaUtf8Invocation.Launch actualLaunch;
        private String preparationFailure;
        private String custodyFailure;
        private WindowsJobProcess.CommandResult actualTerminal;
        boolean started() { return started; }
        InvocationEvidence actualEvidence() { return actualEvidence; }
        CiBootstrap.JavaUtf8Invocation.Launch actualLaunch() { return actualLaunch; }
        String preparationFailure() { return preparationFailure; }
        String custodyFailure() { return custodyFailure; }
        WindowsJobProcess.CommandResult actualTerminal() { return actualTerminal; }
    }
    private CompiledCaptureProcess() { }
    private static String append(String previous,Throwable failure){return (previous==null?"":previous+"; ")+failure;}


    static WindowsJobProcess.CommandResult run(Plan plan, StartState state) throws IOException, InterruptedException {
        return runActual(plan, plan.command().subList(1, plan.command().size()), null, null, state);
    }

    /** Explicit Java boundary. Generic native commands retain their original direct path. */
    static WindowsJobProcess.CommandResult runJava(Plan plan,
            CiBootstrap.JavaUtf8Invocation.Launch actualLaunch,
            CiBootstrap.JavaUtf8Invocation.Carrier expectedCarrier, List<String> asciiVmOptions,
            long maximumInvocationEvidenceBytes,StartState state) throws IOException, InterruptedException {
        Objects.requireNonNull(actualLaunch);Objects.requireNonNull(state);
        if(state.started||state.actualEvidence!=null||state.actualTerminal!=null)throw new IOException("Single actual capture child required");
        if(maximumInvocationEvidenceBytes<1||maximumInvocationEvidenceBytes>JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES)
            throw new IOException("Finite actual receipt invocation allowance required");
        var inspected = CiBootstrap.JavaUtf8Invocation.inspect(actualLaunch.physicalArguments(), expectedCarrier, asciiVmOptions);
        if (!inspected.equals(actualLaunch.logicalRequest())
                || !CiBootstrap.JavaUtf8Invocation.read(actualLaunch.publication()).equals(inspected)
                || !CiBootstrap.JavaUtf8Invocation.launch(actualLaunch.publication(), expectedCarrier, asciiVmOptions)
                    .physicalArguments().equals(actualLaunch.physicalArguments())) {
            throw new IOException("Actual Java Launch differs from its retained envelope");
        }
        // Native source handles outlive the original child owner, including its final Job drain.
        try (var nativeInputs=JavaUtf8NativeCustody.acquire(actualLaunch,expectedCarrier)) {
            nativeInputs.requireCurrent();
            long quoted=maximumInvocationEvidenceBytes(nativeInputs,actualLaunch,Path.of(plan.command().getFirst()));
            if(quoted>maximumInvocationEvidenceBytes)throw new IOException("Actual invocation cannot fit original receipt allowance before native start");
            requireAdditionalBytes(Path.of(plan.outputRoot()),plan.treeMaximumBytes(),quoted);
            return runActual(plan,actualLaunch.physicalArguments(),actualLaunch,nativeInputs,state);
        } catch(IOException|RuntimeException failure) {
            if(state.actualTerminal==null)throw failure;
            state.custodyFailure=append(state.custodyFailure,failure);
            return state.actualTerminal;
        }
    }

    private static long maximumInvocationEvidenceBytes(JavaUtf8NativeCustody.Held held,
            CiBootstrap.JavaUtf8Invocation.Launch launch,Path actualExecutable)throws IOException {
        try{
            long nativeBytes=held.maximumEvidenceBytes(actualExecutable);
            long physicalBytes=ControlBuild.strictMapper().writeValueAsBytes(launch.physicalArguments()).length;
            long paths=Math.multiplyExact(2L,Math.addExact(actualExecutable.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length,
                    CiBootstrap.JavaUtf8Invocation.preparationPath(launch.logicalRequest()).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length));
            // Bounded numeric NativeFile/ProcessIdentity fields and JSON names; paths use explicit escaped UTF8 upper.
            return Math.addExact(Math.addExact(nativeBytes,physicalBytes),Math.addExact(paths,8192));
        }catch(ArithmeticException overflow){throw new IOException("Finite invocation evidence quote overflow",overflow);}
    }

    public static void requireJavaInvocation(InvocationEvidence evidence,
            CiBootstrap.JavaUtf8Invocation.Carrier expectedCarrier, List<String> asciiVmOptions,
            CiBootstrap.JavaUtf8Invocation.Request expectedRequest) throws IOException {
        Objects.requireNonNull(evidence); Objects.requireNonNull(expectedRequest);
        if (!CiBootstrap.JavaUtf8Invocation.inspect(evidence.physicalArguments(), expectedCarrier, asciiVmOptions)
                .equals(expectedRequest)) throw new IOException("Actual Java invocation differs from original logical request");
        if (evidence.preparation() == null) throw new IOException("Actual child preparation witness is unavailable");
        if(evidence.nativeSources()==null)throw new IOException("Actual continuously held native sources are unavailable");
        SharedSourceFiles.assertUnchanged(evidence.preparation());
        var preparationPin=CiBootstrap.JavaUtf8Invocation.captureFile(Path.of(evidence.preparation().source().path()));
        var prepared = CiBootstrap.JavaUtf8Invocation.readPreparation(preparationPin);
        var publication = new CiBootstrap.JavaUtf8Invocation.Publication(prepared.envelope());
        CiBootstrap.JavaUtf8Invocation.inspectPreparation(preparationPin, publication);
        if (!CiBootstrap.JavaUtf8Invocation.launch(publication, expectedCarrier, asciiVmOptions)
                .physicalArguments().equals(evidence.physicalArguments())) {
            throw new IOException("Actual child preparation belongs to another published invocation");
        }
        var actualLaunch=CiBootstrap.JavaUtf8Invocation.launch(publication,expectedCarrier,asciiVmOptions);
        JavaUtf8NativeCustody.requireCurrent(evidence.nativeSources(),actualLaunch,expectedCarrier);
        if(!evidence.nativeSources().identity().equals(evidence.actualProcess()))
            throw new IOException("Native sources belong to another actual child");
        SharedSourceFiles.assertUnchanged(evidence.preparation());
    }

    public static void requireProcess(InvocationEvidence evidence, WindowsJobProcess.CommandResult terminal)
            throws IOException {
        Objects.requireNonNull(evidence); Objects.requireNonNull(terminal);
        if (!evidence.actualProcess().equals(terminal.identity())) throw new IOException("Java invocation belongs to another actual child");
        if(evidence.nativeSources()!=null&&(!evidence.nativeSources().identity().equals(terminal.identity())
                ||!evidence.nativeSources().terminal().equals(terminal)))
            throw new IOException("Native custody belongs to another original terminal");
    }

    /** The actual loaded carrier must be one of the independently qualified caller runtime pins. */
    public static CiBootstrap.JavaUtf8Invocation.ClassCarrier callerCarrier(List<ControlBuild.FileRef> actualCallerRuntime)
            throws IOException {
        Path origin;
        try { origin = Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath(); }
        catch (java.net.URISyntaxException | RuntimeException error) { throw new IOException("Actual loaded carrier origin unavailable", error); }
        var pins = new java.util.ArrayList<CiBootstrap.JavaUtf8Invocation.ClasspathPin>();
        boolean includesOrigin = false;
        for (var ref : List.copyOf(actualCallerRuntime)) {
            ref.verify();
            Path path = Path.of(ref.path()).toRealPath();
            includesOrigin |= path.equals(origin);
            pins.add(CiBootstrap.JavaUtf8Invocation.captureClasspath(path));
            ref.verify();
        }
        if (!includesOrigin) throw new IOException("Actual loaded carrier absent from qualified caller runtime");
        return new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.copyOf(pins));
    }

    static void requireAdditionalBytes(Path root, long maximum, long pendingBytes) throws IOException {
        if (pendingBytes < 0 || maximum < 1) throw new IOException("Finite capture allocation required");
        long bytes = pendingBytes; int entries = 0;
        try (var files = Files.walk(root)) {
            var iterator = files.iterator();
            while (iterator.hasNext()) {
                Path file = iterator.next(); SharedSourceFiles.plainAncestors(file);
                if (++entries > 8192 || Files.isSymbolicLink(file)) throw new IOException("Finite ordinary output tree required");
                if (Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)) bytes = Math.addExact(bytes, Files.size(file));
                if (bytes > maximum) throw new IOException("Capture output tree exceeded declared bound");
            }
        } catch (ArithmeticException error) { throw new IOException("Capture allocation overflow", error); }
    }

    private static WindowsJobProcess.CommandResult runActual(Plan plan, List<String> actualArguments,
            CiBootstrap.JavaUtf8Invocation.Launch actualLaunch, JavaUtf8NativeCustody.Held nativeInputs,
            StartState state) throws IOException, InterruptedException {
        Objects.requireNonNull(state);
        if (state.started || state.actualEvidence != null) throw new IOException("Single actual capture child required");
        Path temporary = Path.of(plan.temporaryRoot()), root = Path.of(plan.outputRoot());
        Path stdout = Path.of(plan.stdoutPath()), stderr = Path.of(plan.stderrPath()), output = Path.of(plan.outputPath());
        Map<String,String> env = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); env.putAll(System.getenv());
        env.remove("JAVA_TOOL_OPTIONS"); env.remove("JDK_JAVA_OPTIONS"); env.remove("_JAVA_OPTIONS");
        for (String name : List.of("TEMP", "TMP", "TMPDIR")) env.put(name, temporary.toString());
        env.put("PYTHONDONTWRITEBYTECODE", "1"); env.put("PYTHONUTF8", "1");
        env.put("PYTHONIOENCODING", "utf-8"); env.put("OPENBLAS_NUM_THREADS", "1"); env.put("OMP_NUM_THREADS", "1");
        for (Environment item : plan.environment()) env.put(item.name(), item.value());
        Instant deadline = Instant.parse(plan.deadlineUtc());
        if (!Instant.now().isBefore(deadline)) throw new IOException("Capture deadline expired before native start");
        requireAdditionalBytes(root, plan.treeMaximumBytes(), 0);
        var spec = new WindowsJobProcess.CommandSpec(Path.of(plan.command().getFirst()),
                actualArguments, Path.of(plan.cwd()),
                Map.copyOf(env), stdout, stderr, plan.memoryBytes());
        try (var child = WindowsJobProcess.start(spec)) {
            state.started = true;
            if (actualLaunch != null) {
                state.actualLaunch = actualLaunch;
                state.actualEvidence = new InvocationEvidence(actualLaunch.physicalArguments(), child.identity(), null, null);
            }
            if(nativeInputs!=null)nativeInputs.attach(child);
            Runnable originalGuard=() -> {
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
                    requireAdditionalBytes(root, plan.treeMaximumBytes(), 0);
                } catch (IOException error) { throw new IllegalStateException("Capture storage monitor failed", error); }
            };
            var terminal=child.await(Duration.ofSeconds(plan.timeoutSeconds()),deadline,
                    nativeInputs==null?originalGuard:nativeInputs.guard(originalGuard));
            state.actualTerminal=terminal;
            JavaUtf8NativeCustody.Evidence nativeSources=null;
            if(nativeInputs!=null){
                try{nativeSources=nativeInputs.verifyTerminal(terminal).evidence();}
                catch(IOException|RuntimeException failure){state.custodyFailure=append(state.custodyFailure,failure);}
            }
            if (actualLaunch != null) {
                SharedSourceFiles.Witness actualPreparation=null;
                try {
                    var pin = CiBootstrap.JavaUtf8Invocation.captureFile(
                            CiBootstrap.JavaUtf8Invocation.preparationPath(actualLaunch.logicalRequest()));
                    CiBootstrap.JavaUtf8Invocation.inspectPreparation(pin, actualLaunch.publication());
                    actualPreparation=SharedSourceFiles.observe(Path.of(pin.path()));
                    if(actualPreparation.source().bytes()!=pin.bytes()||!actualPreparation.source().sha256().equals(pin.sha256()))
                        throw new IOException("Actual child preparation changed during native capture");
                    CiBootstrap.JavaUtf8Invocation.inspectPreparation(pin, actualLaunch.publication());
                    SharedSourceFiles.assertUnchanged(actualPreparation);
                } catch (IOException | RuntimeException failure) {
                    // Preserve the actual native terminal. The caller must reject qualification without its witness.
                    state.preparationFailure = failure.toString();
                }
                state.actualEvidence = new InvocationEvidence(actualLaunch.physicalArguments(), child.identity(),actualPreparation,nativeSources);
            }
            return terminal;
        }
    }
}
