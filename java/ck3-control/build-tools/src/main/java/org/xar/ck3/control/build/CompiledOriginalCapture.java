package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Shared manifest-selected original capture adapter; actual native lifecycle lives in CompiledCaptureProcess. */
public final class CompiledOriginalCapture {
    public static final String REQUEST_SCHEMA = "xar.compiled-original-capture-request/v3";
    public static final String RECEIPT_SCHEMA = "xar.compiled-original-capture-actual/v3";
    public enum Mode { QUALIFY_ONLY, EXECUTE }
    public enum Status { PASS, RED, UNKNOWN }
    public enum Scope { MANIFEST_CLASS_CLOSURE_ONLY, ORIGINAL_SOURCE_EXPORT_ONLY, ORIGINAL_MAIN_OUTPUT_NOT_RESOURCE_ACCEPTANCE }
    public enum OutputKind { FILE, DIRECTORY }

    public record Request(String schema, String id, String machineId, String cwd,
            CompiledOriginalCaptureProfile.Profile profile,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> inputRefs,
            String outputPath, OutputKind outputKind, long maxOutputBytes, long maxTreeBytes,
            List<CompiledCaptureProcess.Environment> environment) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema) || id == null || !id.matches("[a-z0-9][a-z0-9-]{0,59}")
                    || machineId == null || machineId.isBlank()) throw new IllegalArgumentException("Versioned original capture identity required");
            cwd = CompiledOriginalCaptureProfile.canonical(cwd).toString();
            outputPath = CompiledOriginalCaptureProfile.canonical(outputPath).toString();
            Objects.requireNonNull(profile); sourceRefs = CompiledOriginalCaptureProfile.refs(sourceRefs, 1, 8192);
            inputRefs = CompiledOriginalCaptureProfile.refs(inputRefs, 1, 8192); environment = List.copyOf(environment);
            Objects.requireNonNull(outputKind);
            if (profile.invocation() == CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT && outputKind != OutputKind.FILE)
                throw new IllegalArgumentException("Source export produces one exact file");
            if (maxOutputBytes < 1 || maxOutputBytes > (outputKind == OutputKind.FILE ? 2L << 20 : 4L << 20) || maxTreeBytes < maxOutputBytes
                    || maxTreeBytes > (8L << 20) || environment.size() > 32) throw new IllegalArgumentException("Finite original output/environment limits required");
        }
    }
    public record RunSpec(ControlBuild.FileRef requestRef, String receiptPath,
            CompiledGoldenCapture.Limits limits, Mode mode) {
        public RunSpec {
            requestRef = CompiledOriginalCaptureProfile.ref(requestRef);
            if (requestRef.bytes() < 1 || requestRef.bytes() > (2 << 20)) throw new IllegalArgumentException("Finite request pin required");
            receiptPath = CompiledOriginalCaptureProfile.canonical(receiptPath).toString();
            Objects.requireNonNull(limits); Objects.requireNonNull(mode);
        }
    }
    public record Receipt(String schema, String machineId, String observedAtUtc, Mode mode,
            Status status, Scope scope, ControlBuild.FileRef requestRef, CompiledGoldenCapture.Limits limits,
            boolean childStarted, WindowsJobProcess.CommandResult commandResult,
            ControlBuild.FileRef proofRef, boolean postcheckSame,
            ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef,
            ControlBuild.FileRef outputRef, ControlBuild.FileRef outputDirectoryManifestRef,
            List<ControlBuild.FileRef> initialOwnedDirectoryManifestRefs,
            List<ControlBuild.FileRef> ownedDirectoryManifestRefs, String error) {
        public Receipt {
            if (!RECEIPT_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()) throw new IllegalArgumentException("Typed actual capture receipt required");
            Instant.parse(observedAtUtc); Objects.requireNonNull(mode); Objects.requireNonNull(status); Objects.requireNonNull(scope);
            requestRef = CompiledOriginalCaptureProfile.ref(requestRef); Objects.requireNonNull(limits);
            ownedDirectoryManifestRefs = List.copyOf(ownedDirectoryManifestRefs);
            initialOwnedDirectoryManifestRefs = List.copyOf(initialOwnedDirectoryManifestRefs);
            if (status == Status.PASS) {
                if (error != null || proofRef == null || !postcheckSame) throw new IllegalArgumentException("Actual equal pre/post provenance required");
                if (mode == Mode.QUALIFY_ONLY) {
                    if (childStarted || commandResult != null || outputRef != null || outputDirectoryManifestRef != null
                            || !ownedDirectoryManifestRefs.isEmpty() || stdoutRef != null || stderrRef != null
                            || scope != Scope.MANIFEST_CLASS_CLOSURE_ONLY) throw new IllegalArgumentException("Qualification starts no child and claims no artifact");
                } else if (!childStarted || commandResult == null || !commandResult.passed()
                        || (outputRef == null) == (outputDirectoryManifestRef == null)
                        || stdoutRef == null || stderrRef == null || scope == Scope.MANIFEST_CLASS_CLOSURE_ONLY) {
                    throw new IllegalArgumentException("Actual successful native terminal/Job0/output required");
                }
            } else if (error == null || error.isBlank()) throw new IllegalArgumentException("Actual failure reason required");
            if (status == Status.UNKNOWN && (!childStarted || commandResult != null)) throw new IllegalArgumentException("Unknown requires started child without trusted terminal");
        }
    }
    private CompiledOriginalCapture() { }
    public static Request parseRequest(byte[] bytes) throws IOException {
        require(bytes != null && bytes.length > 0 && bytes.length <= (2 << 20), "Finite original request required");
        return ControlBuild.strictMapper().readValue(bytes, Request.class);
    }
    /** Create-only typed request producer; writing a request grants no capture qualification. */
    public static ControlBuild.FileRef writeRequest(Request request, Path ownedRoot, Path destination) throws IOException {
        Objects.requireNonNull(request);
        Path root = CompiledOriginalCaptureProfile.directory(ownedRoot.toString());
        Path output = CompiledOriginalCaptureProfile.canonical(destination.toString()); inside(root, output);
        var reference = CompiledOriginalCaptureProfile.requireReferenceBinding(request);
        if (request.profile().interpreterRef() != null) {
            var repository = CompiledOriginalCaptureProfile.directory(reference == null ? request.cwd() : reference.canonicalRepository());
            CompiledOriginalCaptureProfile.requireInterpreter(repository, request.profile().interpreterRef());
        }
        if (reference != null) require(request.inputRefs().containsAll(reference.inputRefs()), "Reference metadata and source inputs required");
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(request);
        require(request.equals(parseRequest(bytes)), "Typed request serialization changed");
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        var result = ControlBuild.FileRef.measure(output);
        require(request.equals(parseRequest(CompiledGoldenCapture.readPinned(result, 2 << 20))), "Written request differs");
        if (reference != null) require(reference.equals(CompiledOriginalCaptureProfile.requireReferenceBinding(request)),
                "Reference inputs changed during typed request production");
        return result;
    }
    public static Receipt execute(RunSpec spec) throws IOException, InterruptedException {
        Request request = parseRequest(CompiledGoldenCapture.readPinned(spec.requestRef(), 2 << 20));
        String machine = WindowsJobProcess.currentMachineId();
        require(machine.equals(request.machineId()), "Request machine differs from actual current machine");
        Path root = CompiledOriginalCaptureProfile.directory(spec.limits().outputRoot());
        Path temporary = CompiledOriginalCaptureProfile.directory(spec.limits().temporaryRoot());
        Path receiptPath = CompiledOriginalCaptureProfile.canonical(spec.receiptPath());
        Path output = Path.of(request.outputPath()), stdout = root.resolve("original.stdout.log"), stderr = root.resolve("original.stderr.log");
        Path proofPath = root.resolve("original-proof.json"), reserved = root.resolve("original-reserved.json");
        for (Path path : List.of(receiptPath, output, stdout, stderr, proofPath, reserved)) {
            inside(root, path); require(!Files.exists(path, LinkOption.NOFOLLOW_LINKS), "Create-only capture paths already exist");
        }
        require(List.of(receiptPath, output, stdout, stderr, proofPath, reserved).stream().distinct().count() == 6, "Distinct capture artifact paths required");
        var paths = new ArrayList<Path>(List.of(receiptPath, output, stdout, stderr, proofPath, reserved));
        paths.add(root.resolve("original-output-directory.json")); int directoryIndex = 0;
        for (var directory : request.profile().directories()) if (directory.kind() == CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY) {
            paths.add(root.resolve("original-initial-owned-" + directoryIndex + ".json"));
            paths.add(root.resolve("original-owned-directory-" + directoryIndex++ + ".json"));
        }
        require(paths.stream().distinct().count() == paths.size(), "Output collides with exact manifest artifact paths");
        for (Path path : paths) require(!Files.exists(path, LinkOption.NOFOLLOW_LINKS), "Create-only manifest artifact already exists");
        for (var arg : request.profile().arguments()) if (arg.kind() == CompiledOriginalCaptureProfile.ArgumentKind.SCRATCH) {
            Path scratch = CompiledOriginalCaptureProfile.canonical(arg.value()); inside(root, scratch);
            require(!Files.exists(scratch, LinkOption.NOFOLLOW_LINKS) && !output.startsWith(scratch), "New separate original scratch required");
        }
        guard(spec.limits()); Files.write(reserved, ControlBuild.strictMapper().writeValueAsBytes(spec), StandardOpenOption.CREATE_NEW);
        var start = new CompiledCaptureProcess.StartState();
        CompiledOriginalCaptureProfile.Proof before = null; ControlBuild.FileRef proofRef = null;
        WindowsJobProcess.CommandResult result = null; String failure = null; boolean same = false;
        ControlBuild.FileRef directoryOutput = null; List<ControlBuild.FileRef> ownedOutputs = new ArrayList<>();
        List<ControlBuild.FileRef> initialOwned = new ArrayList<>();
        try {
            prepareDirectories(request, root, initialOwned);
            before = CompiledOriginalCaptureProfile.validate(request, CompiledOriginalCaptureProfile.Context.CALLER);
            byte[] proofBytes = ControlBuild.strictMapper().writeValueAsBytes(before);
            require(proofBytes.length <= (4 << 20), "Finite actual compiler proof required");
            Files.write(proofPath, proofBytes, StandardOpenOption.CREATE_NEW); proofRef = ControlBuild.FileRef.measure(proofPath);
            if (spec.mode() == Mode.EXECUTE) {
                var command = new ArrayList<String>();
                command.add(before.javaExecutableRef().path()); command.add("-Xms16m"); command.add("-Xmx96m");
                command.addAll(childTemporaryArguments(temporary));
                command.add("-cp"); command.add(String.join(java.io.File.pathSeparator, before.childClasspath()));
                command.add(OriginalCaptureInvoker.class.getName());
                for (var pin : List.of(spec.requestRef(), proofRef)) {
                    command.add(pin.path()); command.add(Long.toString(pin.bytes())); command.add(pin.sha256());
                }
                var plan = new CompiledCaptureProcess.Plan(command, request.cwd(), temporary.toString(), root.toString(),
                        stdout.toString(), stderr.toString(), output.toString(), request.maxOutputBytes(), request.maxTreeBytes(),
                        spec.limits().timeoutSeconds(), spec.limits().deadlineUtc(), spec.limits().childMemoryBytes(), request.environment());
                result = CompiledCaptureProcess.run(plan, start);
                require(result.passed(), "Original child failed, timed out or retained native Job members");
                if (request.outputKind() == OutputKind.FILE) {
                    require(Files.isRegularFile(output, LinkOption.NOFOLLOW_LINKS) && Files.size(output) > 0
                            && Files.size(output) <= request.maxOutputBytes(), "Bounded original output required");
                } else directoryOutput = writeDirectoryManifest(root.resolve("original-output-directory.json"), output, request.maxOutputBytes());
                int index = 0;
                for (var arg : request.profile().directories()) if (arg.kind() == CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY)
                    ownedOutputs.add(writeDirectoryManifest(root.resolve("original-owned-directory-" + index++ + ".json"), Path.of(arg.path()), request.maxTreeBytes()));
            }
            guard(spec.limits()); spec.requestRef().verify(); proofRef.verify();
            for (var initial : initialOwned) readDirectoryManifest(initial).verifyRetained();
            var after = CompiledOriginalCaptureProfile.validate(request, CompiledOriginalCaptureProfile.Context.CALLER);
            same = before.equals(after); require(same, "Original capture closure changed during operation");
        } catch (IOException | RuntimeException error) { failure = error.toString(); }
        finally {
            try {
                spec.requestRef().verify();
                if (before != null) {
                    same = before.equals(CompiledOriginalCaptureProfile.validate(request, CompiledOriginalCaptureProfile.Context.CALLER));
                    require(same, "Terminal original capture closure changed"); if (proofRef != null) proofRef.verify();
                }
            } catch (IOException | RuntimeException error) { same = false; failure = (failure == null ? "" : failure + "; ") + "postcheck: " + error; }
        }
        Status status = failure == null ? Status.PASS : (start.started() && result == null ? Status.UNKNOWN : Status.RED);
        Scope scope = spec.mode() == Mode.QUALIFY_ONLY ? Scope.MANIFEST_CLASS_CLOSURE_ONLY
                : request.profile().invocation() == CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT
                    ? Scope.ORIGINAL_SOURCE_EXPORT_ONLY : Scope.ORIGINAL_MAIN_OUTPUT_NOT_RESOURCE_ACCEPTANCE;
        Receipt receipt = new Receipt(RECEIPT_SCHEMA, machine, Instant.now().toString(), spec.mode(), status, scope,
                spec.requestRef(), spec.limits(), start.started(), result, proofRef, same,
                spec.mode() == Mode.EXECUTE ? measured(stdout, 65536) : null,
                spec.mode() == Mode.EXECUTE ? measured(stderr, 65536) : null,
                spec.mode() == Mode.EXECUTE && request.outputKind() == OutputKind.FILE ? measured(output, request.maxOutputBytes()) : null,
                directoryOutput, initialOwned, ownedOutputs, failure);
        Files.write(receiptPath, ControlBuild.strictMapper().writeValueAsBytes(receipt), StandardOpenOption.CREATE_NEW);
        return receipt;
    }

    public static Receipt acceptedReceipt(ControlBuild.FileRef ref, Mode mode) throws IOException {
        require(ref.bytes() > 0 && ref.bytes() <= (256 << 10), "Finite actual receipt pin required");
        Receipt receipt = ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(ref, 256 << 10), Receipt.class);
        require(receipt.status() == Status.PASS && receipt.mode() == mode
                && receipt.machineId().equals(WindowsJobProcess.currentMachineId()), "Actual successful current-machine receipt required");
        Request request = parseRequest(CompiledGoldenCapture.readPinned(receipt.requestRef(), 2 << 20));
        var recorded = ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(receipt.proofRef(), 4 << 20),
                CompiledOriginalCaptureProfile.Proof.class);
        var actual = CompiledOriginalCaptureProfile.validate(request, CompiledOriginalCaptureProfile.Context.CALLER);
        require(actual.equals(recorded) && receipt.postcheckSame(), "Actual complete compiler/caller proof no longer matches");
        var owned = request.profile().directories().stream().filter(item -> item.kind() == CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY).toList();
        require(receipt.initialOwnedDirectoryManifestRefs().size() == owned.size(), "Actual initial owned directory inventories required");
        for (int index = 0; index < owned.size(); index++) {
            var initial = readDirectoryManifest(receipt.initialOwnedDirectoryManifestRefs().get(index));
            require(initial.root().equals(owned.get(index).path()), "Initial owned directory differs"); initial.verifyRetained();
        }
        if (mode == Mode.EXECUTE) {
            require(receipt.commandResult().accounting().memoryLimitBytes() == receipt.limits().childMemoryBytes(), "Actual terminal memory binding differs");
            requireOutput(request, receipt.outputRef(), receipt.outputDirectoryManifestRef());
            receipt.stdoutRef().verify(); receipt.stderrRef().verify();
            require(receipt.ownedDirectoryManifestRefs().size() == owned.size(), "Every actual owned directory output required");
            for (int index = 0; index < owned.size(); index++) {
                var manifest = readDirectoryManifest(receipt.ownedDirectoryManifestRefs().get(index));
                require(manifest.root().equals(owned.get(index).path()), "Owned output directory differs"); manifest.verify();
            }
        }
        ref.verify(); return receipt;
    }

    static List<String> childTemporaryArguments(Path temporary) throws IOException {
        Path owned = CompiledOriginalCaptureProfile.directory(temporary.toString());
        return List.of("-Djava.io.tmpdir=" + owned, "-Djna.tmpdir=" + owned);
    }
    static void prepareDirectories(Request request, Path root, List<ControlBuild.FileRef> initialOwned) throws IOException {
        int index = 0;
        for (var argument : request.profile().directories()) {
            Path path = Path.of(argument.path());
            if (argument.kind() == CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY) {
                inside(root, path);
                if (argument.preparation() == CompiledOriginalCaptureProfile.DirectoryPreparation.CREATE_EMPTY) Files.createDirectory(path);
                initialOwned.add(writeDirectoryManifest(root.resolve("original-initial-owned-" + index++ + ".json"), path, request.maxTreeBytes()));
            } else if (argument.kind() == CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY) {
                require(!path.startsWith(Path.of(request.outputPath())) && !Path.of(request.outputPath()).startsWith(path), "Immutable input directory overlaps mutable output");
                argument.inputManifest().verify();
            } else CompiledOriginalCaptureProfile.directory(argument.path());
        }
    }
    static ControlBuild.FileRef writeDirectoryManifest(Path destination, Path directory, long maximum) throws IOException {
        var manifest = CompiledOriginalCaptureProfile.DirectoryManifest.measure(directory, maximum);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(manifest);
        require(raw.length <= (2 << 20), "Bounded exact directory manifest required");
        Files.write(destination, raw, StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(destination);
    }
    static CompiledOriginalCaptureProfile.DirectoryManifest readDirectoryManifest(ControlBuild.FileRef reference) throws IOException {
        return ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(reference, 2 << 20), CompiledOriginalCaptureProfile.DirectoryManifest.class);
    }
    static void requireOutput(Request request, ControlBuild.FileRef file, ControlBuild.FileRef directory) throws IOException {
        if (request.outputKind() == OutputKind.FILE) {
            require(directory == null && file != null && file.path().equals(request.outputPath())
                    && file.bytes() > 0 && file.bytes() <= request.maxOutputBytes(), "Actual file output differs"); file.verify();
        } else {
            require(file == null && directory != null, "Actual directory manifest required"); var manifest = readDirectoryManifest(directory);
            require(manifest.root().equals(request.outputPath()) && !manifest.files().isEmpty(), "Actual nonempty output directory differs");
            require(manifest.sameInventory(CompiledOriginalCaptureProfile.DirectoryManifest.measure(Path.of(request.outputPath()), request.maxOutputBytes())), "Output directory inventory changed");
        }
    }

    static void inside(Path root, Path path) throws IOException {
        require(path.startsWith(root) && !path.equals(root), "Capture output escapes admitted root");
        Path parent = path.getParent();
        while (parent != null && !Files.exists(parent, LinkOption.NOFOLLOW_LINKS)) parent = parent.getParent();
        require(parent != null && parent.startsWith(root) && parent.toRealPath().equals(parent), "Canonical output ancestry required");
    }
    private static void guard(CompiledGoldenCapture.Limits limits) throws IOException {
        require(Instant.now().isBefore(Instant.parse(limits.deadlineUtc())), "Capture deadline expired");
    }
    private static ControlBuild.FileRef measured(Path path, long maximum) throws IOException {
        return Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && Files.size(path) <= maximum ? ControlBuild.FileRef.measure(path) : null;
    }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }

    public static void main(String[] args) throws Exception {
        if (args.length == 5 && args[0].equals("directory-manifest")) {
            Path root = CompiledOriginalCaptureProfile.directory(args[4]);
            Path destination = CompiledOriginalCaptureProfile.canonical(args[2]); inside(root, destination);
            if (!args[3].matches("[1-9][0-9]{0,7}")) throw new IllegalArgumentException("Positive bounded directory bytes required");
            long maximum = Long.parseLong(args[3]); require(maximum <= (64L << 20), "Finite directory input extent required");
            var reference = writeDirectoryManifest(destination, CompiledOriginalCaptureProfile.canonical(args[1]), maximum);
            System.out.println(ControlBuild.strictMapper().writeValueAsString(reference));
        } else if (args.length == 4 && args[0].equals("run")) {
            var pin = new ControlBuild.FileRef(args[1], Long.parseLong(args[2]), args[3]);
            require(pin.bytes() > 0 && pin.bytes() <= 65536, "Finite run specification pin required");
            var spec = ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(pin, 65536), RunSpec.class);
            Receipt receipt = execute(spec); System.out.println(ControlBuild.strictMapper().writeValueAsString(receipt));
            if (receipt.status() != Status.PASS) System.exit(receipt.status() == Status.UNKNOWN ? 2 : 1);
        } else if (args.length == 5 && args[0].equals("accept")) {
            var pin = new ControlBuild.FileRef(args[1], Long.parseLong(args[2]), args[3]);
            System.out.println(ControlBuild.strictMapper().writeValueAsString(acceptedReceipt(pin, Mode.valueOf(args[4]))));
        } else throw new IllegalArgumentException("run spec bytes sha256 | accept receipt bytes sha256 expectedMode | directory-manifest directory newFile maxBytes ownedRoot");
    }
}
