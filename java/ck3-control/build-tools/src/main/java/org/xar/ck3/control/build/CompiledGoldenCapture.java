package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Shared V14 compiled-golden CLI. The shared owned-command launcher supplies the
 * fresh finite execution slot; this boundary admits compiled inputs, owns the
 * inner native Job and records its actual terminal. No source-launch fallback.
 */
public final class CompiledGoldenCapture {
    public static final String BATCH_SCHEMA = "xar.shared-compiled-golden-capture-batch/v1";
    public static final String HISTORICAL_RECEIPT_SCHEMA = "xar.shared-compiled-golden-capture-actual/v1";
    public static final String UNPREPARED_RECEIPT_SCHEMA = "xar.shared-compiled-golden-capture-actual/v2";
    public static final String JDK_ONLY_RECEIPT_SCHEMA = "xar.shared-compiled-golden-capture-actual/v3";
    public static final String RECEIPT_SCHEMA = "xar.shared-compiled-golden-capture-actual/v4";
    public enum Mode { QUALIFY_ONLY, CAPTURE }
    public enum Status { PASS, RED }

    /** The seven capture-row fields remain unchanged; profiles are per request. */
    public record Request(String id, List<String> command, String cwd,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> inputRefs,
            String outputPath, long maxOutputBytes) {
        public Request {
            if (id == null || !id.matches("[a-z0-9][a-z0-9-]{0,59}") || command == null
                    || command.size() < 10 || command.size() > 11 || maxOutputBytes < 1
                    || maxOutputBytes > (2L << 20)) throw new IllegalArgumentException("Finite seven-field capture row required");
            command = List.copyOf(command);
            for (String item : command) if (item == null || item.isEmpty()
                    || item.codePoints().anyMatch(point -> point < 32 || point == 127)) {
                throw new IllegalArgumentException("Plain finite command arguments required");
            }
            cwd = canonicalPath(cwd).toString(); outputPath = canonicalPath(outputPath).toString();
            sourceRefs = refs(sourceRefs, 1, 64); inputRefs = refs(inputRefs, 6, 64);
            for (ControlBuild.FileRef ref : sourceRefs) {
                String name = ref.path().toLowerCase(java.util.Locale.ROOT);
                if (name.endsWith(".class") || name.endsWith(".jar") || name.endsWith(".exe") || name.endsWith(".dll")) {
                    throw new IllegalArgumentException("Compiled artifacts must not be source_refs");
                }
            }
        }
    }

    public record ProfileBinding(String requestId, CompiledCaptureInputProfile.Profile inputProfile) {
        public ProfileBinding { Objects.requireNonNull(requestId); Objects.requireNonNull(inputProfile); }
    }

    public record Batch(String schema, String machineId, List<Request> captures,
            List<ProfileBinding> compiledInputProfiles) {
        public Batch {
            if (!BATCH_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || captures == null || captures.isEmpty() || captures.size() > 4
                    || compiledInputProfiles == null || captures.size() != compiledInputProfiles.size()) {
                throw new IllegalArgumentException("Explicit finite compiled capture batch required");
            }
            captures = List.copyOf(captures); compiledInputProfiles = List.copyOf(compiledInputProfiles);
            Set<String> ids = new HashSet<>();
            for (Request request : captures) if (!ids.add(request.id())) throw new IllegalArgumentException("Duplicate capture id");
            Set<String> bound = new HashSet<>();
            for (ProfileBinding binding : compiledInputProfiles) {
                if (!ids.contains(binding.requestId()) || !bound.add(binding.requestId())) {
                    throw new IllegalArgumentException("Unused, duplicate or conflicting compiled input profile");
                }
                Request request = captures.stream().filter(row -> row.id().equals(binding.requestId())).findFirst().orElseThrow();
                Set<ControlBuild.FileRef> classes = new HashSet<>();
                for (ControlBuild.FileRef ref : request.inputRefs()) if (ref.path().endsWith(".class")) classes.add(ref);
                if (!classes.equals(Set.copyOf(binding.inputProfile().runtimeClassRefs()))) {
                    throw new IllegalArgumentException("Only this request's exact six classes may be admitted");
                }
            }
        }

        public CompiledCaptureInputProfile.Profile profileFor(String id) {
            return compiledInputProfiles.stream().filter(row -> row.requestId().equals(id))
                    .findFirst().orElseThrow(() -> new IllegalArgumentException("Missing compiled profile")).inputProfile();
        }
    }

    /** Limits are explicit arguments from the admitted shared launcher, not an independent lease. */
    public record Limits(String outputRoot, String temporaryRoot, String deadlineUtc,
            int timeoutSeconds, long childMemoryBytes) {
        public Limits {
            outputRoot = canonicalPath(outputRoot).toString(); temporaryRoot = canonicalPath(temporaryRoot).toString();
            Objects.requireNonNull(deadlineUtc); Instant.parse(deadlineUtc);
            if (timeoutSeconds < 1 || timeoutSeconds > 120 || childMemoryBytes < (128L << 20)
                    || childMemoryBytes > (512L << 20)) throw new IllegalArgumentException("Finite shared-slot limits required");
        }
    }

    public record Observation(String requestId, CompiledCaptureInputProfile.Proof before,
            CompiledCaptureInputProfile.Proof after, WindowsJobProcess.CommandResult result,
            ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef,
            ControlBuild.FileRef outputRef, String error,
            CompiledCaptureProcess.InvocationEvidence invocationEvidence,
            CompiledCaptureProcess.HistoricalInvocationV2 historicalInvocationEvidence) {
        public Observation {
            Objects.requireNonNull(requestId);
            if (invocationEvidence != null && historicalInvocationEvidence != null) {
                throw new IllegalArgumentException("Current and historical invocation evidence are distinct type domains");
            }
        }
        /** Historical/direct-qualification shape; cannot grant current CAPTURE acceptance. */
        public Observation(String requestId, CompiledCaptureInputProfile.Proof before,
                CompiledCaptureInputProfile.Proof after, WindowsJobProcess.CommandResult result,
                ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef,
                ControlBuild.FileRef outputRef, String error) {
            this(requestId, before, after, result, stdoutRef, stderrRef, outputRef, error, null, null);
        }
    }

    public record Receipt(String schema, String machineId, String observedAtUtc, Mode mode, Status status,
            ControlBuild.FileRef batchRef, Batch batch, Limits limits, int childrenStarted,
            List<Observation> observations, String error) {
        public Receipt {
            if ((!RECEIPT_SCHEMA.equals(schema) && !HISTORICAL_RECEIPT_SCHEMA.equals(schema)
                    && !UNPREPARED_RECEIPT_SCHEMA.equals(schema) && !JDK_ONLY_RECEIPT_SCHEMA.equals(schema))
                    || machineId == null || machineId.isBlank()) {
                throw new IllegalArgumentException("Typed compiled capture receipt required");
            }
            Instant.parse(observedAtUtc); Objects.requireNonNull(mode); Objects.requireNonNull(status);
            batchRef = canonicalRef(batchRef); Objects.requireNonNull(batch); Objects.requireNonNull(limits);
            observations = List.copyOf(observations);
            if (HISTORICAL_RECEIPT_SCHEMA.equals(schema) && observations.stream().anyMatch(item -> item.invocationEvidence() != null
                    || item.historicalInvocationEvidence() != null)) {
                throw new IllegalArgumentException("Historical schema cannot claim retained Java invocation evidence");
            }
            if (!RECEIPT_SCHEMA.equals(schema) && observations.stream().anyMatch(item -> item.invocationEvidence() != null)) {
                throw new IllegalArgumentException("Historical invocation data cannot be represented as current native custody");
            }
            if (RECEIPT_SCHEMA.equals(schema) && observations.stream().anyMatch(item -> item.historicalInvocationEvidence() != null)) {
                throw new IllegalArgumentException("Current receipt cannot use the historical invocation memory domain");
            }
            if (UNPREPARED_RECEIPT_SCHEMA.equals(schema) && observations.stream().anyMatch(item -> item.historicalInvocationEvidence() != null
                    && item.historicalInvocationEvidence().preparation() != null)) {
                throw new IllegalArgumentException("Historical v2 cannot claim actual preparation custody");
            }
            if (childrenStarted < 0 || childrenStarted > 1 || observations.size() > 4) {
                throw new IllegalArgumentException("A capture slot starts at most one child");
            }
            if (status == Status.PASS) {
                if (error != null || observations.size() != batch.captures().size()) throw new IllegalArgumentException("Complete successful observations required");
                for (int index = 0; index < observations.size(); index++) {
                    Observation observation = observations.get(index);
                    if (!observation.requestId().equals(batch.captures().get(index).id()) || observation.error() != null
                            || observation.before() == null || !observation.before().equals(observation.after())) {
                        throw new IllegalArgumentException("Exact per-request immutable pre/post proofs required");
                    }
                    if (mode == Mode.QUALIFY_ONLY) {
                        if (childrenStarted != 0 || observation.result() != null || observation.stdoutRef() != null
                                || observation.stderrRef() != null || observation.outputRef() != null || observation.invocationEvidence() != null
                                || observation.historicalInvocationEvidence() != null) {
                            throw new IllegalArgumentException("Qualification must start zero children and claim no output");
                        }
                    } else if (childrenStarted != 1 || observations.size() != 1 || observation.result() == null
                            || !observation.result().passed() || observation.stdoutRef() == null
                            || observation.stderrRef() == null || observation.outputRef() == null) {
                        throw new IllegalArgumentException("Actual successful child terminal/Job0 and artifacts required");
                    } else if (RECEIPT_SCHEMA.equals(schema) && (observation.invocationEvidence() == null
                            || observation.invocationEvidence().preparation() == null
                            || observation.invocationEvidence().nativeSources() == null
                            || !observation.invocationEvidence().actualProcess().equals(observation.result().identity()))) {
                        throw new IllegalArgumentException("Current capture requires the same child, actual preparation and held native source custody");
                    } else if (JDK_ONLY_RECEIPT_SCHEMA.equals(schema) && (observation.historicalInvocationEvidence() == null
                            || observation.historicalInvocationEvidence().preparation() == null
                            || !observation.historicalInvocationEvidence().actualProcess().equals(observation.result().identity()))) {
                        throw new IllegalArgumentException("Historical v3 must preserve its original child, argv and preparation metadata");
                    }
                }
            } else if (error == null || error.isBlank()) throw new IllegalArgumentException("RED preserves actual failure");
        }
    }

    private CompiledGoldenCapture() { }

    public static Batch parseBatch(byte[] json) throws IOException {
        require(json != null && json.length > 0 && json.length <= (256 << 10), "Finite compiled batch JSON required");
        return ControlBuild.strictMapper().readValue(json, Batch.class);
    }

    /** Actual production admission. This is also the no-child qualification route. */
    public static CompiledCaptureInputProfile.Proof qualify(Request request, CompiledCaptureInputProfile.Profile profile) throws IOException {
        return CompiledCaptureInputProfile.validate(profile, request.cwd(), request.command(), request.outputPath(),
                request.sourceRefs(), request.inputRefs());
    }

    /** Produces a create-only receipt for both success and real runtime failure. */
    public static Receipt execute(ControlBuild.FileRef batchRef, Path receiptPath, Limits limits, Mode mode)
            throws IOException, InterruptedException {
        Objects.requireNonNull(mode); batchRef = canonicalRef(batchRef);
        Batch batch = parseBatch(readPinned(batchRef, 256 << 10));
        String machine = WindowsJobProcess.currentMachineId();
        require(machine.equals(batch.machineId()), "Actual current machine differs from compiled batch");
        Path root = existingDirectory(limits.outputRoot()), temporary = existingDirectory(limits.temporaryRoot());
        Path receipt = canonicalPath(receiptPath.toString()); requireInside(root, receipt);
        require(!Files.exists(receipt, LinkOption.NOFOLLOW_LINKS), "Never overwrite a capture receipt");
        require(mode == Mode.QUALIFY_ONLY || batch.captures().size() == 1, "One actual capture per admitted slot");
        Instant deadline = Instant.parse(limits.deadlineUtc()); guard(deadline);
        List<Observation> observations = new ArrayList<>(); int started = 0; String failure = null;
        for (Request request : batch.captures()) {
            CompiledCaptureInputProfile.Proof before = null, after = null;
            WindowsJobProcess.CommandResult result = null;
            CompiledCaptureProcess.InvocationEvidence invocationEvidence = null;
            Path stdout = root.resolve("capture-" + request.id() + ".stdout.log");
            Path stderr = root.resolve("capture-" + request.id() + ".stderr.log");
            Path output = Path.of(request.outputPath());
            try {
                guard(deadline); batchRef.verify(); requireInside(root, output);
                require(!Set.of(stdout, stderr, receipt).contains(output), "Golden output must differ from logs and receipt");
                require(!Files.exists(stdout, LinkOption.NOFOLLOW_LINKS) && !Files.exists(stderr, LinkOption.NOFOLLOW_LINKS)
                        && !Files.exists(output, LinkOption.NOFOLLOW_LINKS), "Create-only capture evidence already exists");
                if (batch.profileFor(request.id()).launcher().argumentCount() == 4) {
                    Path scratch = canonicalPath(request.command().get(9)); requireInside(root, scratch);
                    require(!scratch.equals(output) && !output.startsWith(scratch) && !Files.exists(scratch, LinkOption.NOFOLLOW_LINKS),
                            "Pending capture scratch must be absent and separate from golden output");
                }
                before = qualify(request, batch.profileFor(request.id()));
                if (mode == Mode.CAPTURE) {
                    var plan = new CompiledCaptureProcess.Plan(request.command(), request.cwd(), temporary.toString(), root.toString(),
                            stdout.toString(), stderr.toString(), output.toString(), request.maxOutputBytes(), 8L << 20,
                            limits.timeoutSeconds(), limits.deadlineUtc(), limits.childMemoryBytes(), List.of());
                    var state = new CompiledCaptureProcess.StartState();
                    var carrier = CompiledCaptureProcess.callerCarrier(before.callerRuntimeClosure());
                    var logical = invocationRequest(request, before, limits);
                    requireOutputDisjoint(output, logical);
                    var publication = CiBootstrap.JavaUtf8Invocation.publish(logical,
                            CiBootstrap.JavaUtf8Invocation.captureOutputRoot(root), "capture-" + request.id() + "-java-invocation.bin",
                            pending -> CompiledCaptureProcess.requireAdditionalBytes(root, 8L << 20, pending));
                    var launch = CiBootstrap.JavaUtf8Invocation.launch(publication, carrier, asciiVmOptions(request));
                    guard(deadline); batchRef.verify();
                    long invocationAllowance = invocationEvidenceAllowance(batchRef, batch, limits, machine, request, before, stdout, stderr, output);
                    try { result = CompiledCaptureProcess.runJava(plan, launch, carrier, asciiVmOptions(request), invocationAllowance, state); }
                    finally {
                        if (state.started()) started++;
                        invocationEvidence = state.actualEvidence();
                        if (result == null) result = state.actualTerminal();
                    }
                    require(state.custodyFailure() == null, "Actual native source custody failed: " + state.custodyFailure());
                    require(state.preparationFailure() == null, "Actual child preparation evidence failed: " + state.preparationFailure());
                    requireCurrentInvocation(request, before, limits, invocationEvidence, result);
                    require(result.passed(), "Actual capture child failed, timed out or retained Job members");
                    require(Files.isRegularFile(output, LinkOption.NOFOLLOW_LINKS) && Files.size(output) > 0
                            && Files.size(output) <= request.maxOutputBytes(), "Actual finite golden output required");
                }
                after = qualify(request, batch.profileFor(request.id()));
                require(before.equals(after), "Compiled capture input proof changed during operation");
                batchRef.verify(); guard(deadline);
            } catch (IOException | RuntimeException error) {
                failure = error.toString();
            } finally {
                try {
                    batchRef.verify();
                    if (before != null) {
                        after = qualify(request, batch.profileFor(request.id()));
                        require(before.equals(after), "Terminal compiled capture proof changed");
                    }
                } catch (IOException | RuntimeException error) {
                    failure = (failure == null ? "" : failure + "; ") + "terminal_postcheck: " + error;
                }
            }
            observations.add(new Observation(request.id(), before, after, result,
                    mode == Mode.CAPTURE ? measuredOrNull(stdout, 65536) : null,
                    mode == Mode.CAPTURE ? measuredOrNull(stderr, 65536) : null,
                    mode == Mode.CAPTURE ? measuredOrNull(output, request.maxOutputBytes()) : null, failure, invocationEvidence, null));
            if (failure != null) break;
        }
        Receipt result = new Receipt(RECEIPT_SCHEMA, machine, Instant.now().toString(), mode,
                failure == null ? Status.PASS : Status.RED, batchRef, batch, limits, started, observations, failure);
        byte[] receiptBytes = encodeReceipt(result);
        require(receiptBytes.length <= (1 << 20), "Actual capture receipt exceeds its original 1MiB reader bound");
        CompiledCaptureProcess.requireAdditionalBytes(root, 8L << 20, receiptBytes.length);
        Files.write(receipt, receiptBytes, StandardOpenOption.CREATE_NEW);
        return result;
    }

    /** Consumer revalidates genuine producer inputs; JSON shape or a recorded PASS is insufficient. */
    public static Receipt acceptedReceipt(ControlBuild.FileRef receiptRef, Mode expectedMode) throws IOException {
        Receipt receipt = parseReceipt(readPinned(canonicalRef(receiptRef), 1 << 20));
        require(RECEIPT_SCHEMA.equals(receipt.schema()), "Historical capture lacks current invocation/loading evidence; use explicit historical metadata reader");
        require(receipt.status() == Status.PASS && receipt.mode() == expectedMode
                && receipt.machineId().equals(WindowsJobProcess.currentMachineId()), "Successful actual current-machine receipt of expected mode required");
        Batch actualBatch = parseBatch(readPinned(receipt.batchRef(), 256 << 10));
        require(actualBatch.equals(receipt.batch()), "Receipt batch differs from actual pinned request bytes");
        for (int index = 0; index < actualBatch.captures().size(); index++) {
            Request request = actualBatch.captures().get(index); Observation observation = receipt.observations().get(index);
            CompiledCaptureInputProfile.Proof actual = qualify(request, actualBatch.profileFor(request.id()));
            require(actual.equals(observation.before()) && actual.equals(observation.after()), "Accepted producer/proof no longer matches actual complete inputs");
            if (expectedMode == Mode.CAPTURE) {
                requireCurrentInvocation(request, actual, receipt.limits(), observation.invocationEvidence(), observation.result());
                require(Path.of(observation.outputRef().path()).equals(Path.of(request.outputPath()))
                        && observation.outputRef().bytes() > 0 && observation.outputRef().bytes() <= request.maxOutputBytes(), "Output artifact must match the exact capture row");
                observation.stdoutRef().verify(); observation.stderrRef().verify(); observation.outputRef().verify();
                require(observation.result().accounting().memoryLimitBytes() == receipt.limits().childMemoryBytes(), "Actual child Job memory differs from explicit consumed limits");
            }
        }
        receiptRef.verify(); return receipt;
    }

    /** Reads v1/v2/v3 metadata without granting current capture, Unicode, producer or native custody. */
    public static Receipt historicalReceiptMetadata(ControlBuild.FileRef receiptRef) throws IOException {
        Receipt receipt = parseReceipt(readPinned(canonicalRef(receiptRef), 1 << 20));
        require(HISTORICAL_RECEIPT_SCHEMA.equals(receipt.schema()) || UNPREPARED_RECEIPT_SCHEMA.equals(receipt.schema())
                        || JDK_ONLY_RECEIPT_SCHEMA.equals(receipt.schema()), "Explicit v1/v2/v3 historical receipt required");
        receiptRef.verify(); return receipt;
    }

    /** One versioned receipt serializer preserves each historical schema's actual missing fields. */
    public static byte[] encodeReceipt(Receipt receipt) throws IOException {
        Objects.requireNonNull(receipt);
        var mapper = ControlBuild.strictMapper();
        com.fasterxml.jackson.databind.node.ObjectNode document = mapper.valueToTree(receipt);
        for (int index = 0; index < receipt.observations().size(); index++) {
            var item = (com.fasterxml.jackson.databind.node.ObjectNode) document.path("observations").get(index);
            item.remove("historical_invocation_evidence");
            var historical = receipt.observations().get(index).historicalInvocationEvidence();
            if (HISTORICAL_RECEIPT_SCHEMA.equals(receipt.schema())) item.remove("invocation_evidence");
            else if (UNPREPARED_RECEIPT_SCHEMA.equals(receipt.schema())) {
                if (historical == null) item.putNull("invocation_evidence");
                else item.set("invocation_evidence", mapper.readTree(CompiledCaptureProcess.encodeHistoricalInvocationV1(
                        new CompiledCaptureProcess.HistoricalInvocationV1(historical.physicalArguments(), historical.actualProcess()))));
            } else if (JDK_ONLY_RECEIPT_SCHEMA.equals(receipt.schema())) {
                if (historical == null) item.putNull("invocation_evidence");
                else item.set("invocation_evidence", mapper.readTree(CompiledCaptureProcess.encodeHistoricalInvocationV2(historical)));
            }
        }
        return RECEIPT_SCHEMA.equals(receipt.schema()) ? mapper.writeValueAsBytes(document)
                : mapper.writerWithDefaultPrettyPrinter().writeValueAsBytes(document);
    }

    static Receipt parseReceipt(byte[] raw) throws IOException {
        var mapper = ControlBuild.strictMapper();
        var document = mapper.readTree(raw);
        require(document != null && document.isObject(), "Typed compiled capture receipt object required");
        String schema = document.path("schema").asText();
        require(RECEIPT_SCHEMA.equals(schema) || HISTORICAL_RECEIPT_SCHEMA.equals(schema)
                || UNPREPARED_RECEIPT_SCHEMA.equals(schema) || JDK_ONLY_RECEIPT_SCHEMA.equals(schema), "Known exact capture receipt version required");
        if (document.path("observations").isArray()) for (var item : document.path("observations")) {
            require(item.isObject() && !item.has("historical_invocation_evidence"), "Historical invocation memory slot is never an input wire field");
            var row = (com.fasterxml.jackson.databind.node.ObjectNode) item;
            CompiledCaptureProcess.HistoricalInvocationV2 historical = null;
            if (HISTORICAL_RECEIPT_SCHEMA.equals(schema)) {
                require(!row.has("invocation_evidence"), "v1 invocation evidence is absent, never retroactively supplied");
                row.putNull("invocation_evidence");
            } else if (!RECEIPT_SCHEMA.equals(schema)) {
                require(row.has("invocation_evidence"), "Recorded historical invocation field must preserve presence");
                var evidence = row.get("invocation_evidence");
                if (!evidence.isNull()) {
                    byte[] original = mapper.writeValueAsBytes(evidence);
                    if (UNPREPARED_RECEIPT_SCHEMA.equals(schema)) {
                        var v1 = CompiledCaptureProcess.decodeHistoricalInvocationV1(original);
                        historical = new CompiledCaptureProcess.HistoricalInvocationV2(v1.physicalArguments(), v1.actualProcess(), null);
                    } else historical = CompiledCaptureProcess.decodeHistoricalInvocationV2(original);
                }
                row.putNull("invocation_evidence");
            }
            row.set("historical_invocation_evidence", mapper.valueToTree(historical));
        }
        return mapper.treeToValue(document, Receipt.class);
    }

    /** Logical data from an already genuine whole-input proof; this does not start a child. */
    public static CiBootstrap.JavaUtf8Invocation.Request invocationRequest(Request request,
            CompiledCaptureInputProfile.Proof actualProof, Limits limits) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(actualProof); Objects.requireNonNull(limits);
        var profile = actualProof.profile();
        require(request.command().size() == 7 + profile.launcher().argumentCount()
                && request.command().get(3).equals("-Dxar.capture.classRoot=" + profile.classRoot())
                && request.command().get(4).equals("-cp") && request.command().get(5).equals(profile.classRoot())
                && request.command().get(6).equals(profile.launcher().binaryName()), "Logical invocation must preserve the qualified exact command");
        var classes = CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(profile.classRoot()));
        return new CiBootstrap.JavaUtf8Invocation.Request(
                new CiBootstrap.JavaUtf8Invocation.ClassTarget(profile.launcher().binaryName(), classes, List.of(classes)),
                List.of(new CiBootstrap.JavaUtf8Invocation.Property("xar.capture.classRoot", profile.classRoot())),
                request.command().subList(7, request.command().size()),
                CiBootstrap.JavaUtf8Invocation.captureOutputRoot(Path.of(limits.outputRoot())));
    }

    static List<String> asciiVmOptions(Request request) {
        return List.copyOf(request.command().subList(1, 3));
    }

    static void requireOutputDisjoint(Path originalOutput, CiBootstrap.JavaUtf8Invocation.Request logical) throws IOException {
        Path preparation = CiBootstrap.JavaUtf8Invocation.preparationPath(logical);
        require(!originalOutput.startsWith(preparation) && !preparation.startsWith(originalOutput),
                "Original golden output must be disjoint from the invocation preparation output");
    }

    /** Pure byte quotation only: these placeholder digests are never published or accepted as observed files. */
    private static long invocationEvidenceAllowance(ControlBuild.FileRef batchRef, Batch batch, Limits limits, String machine,
            Request request, CompiledCaptureInputProfile.Proof before, Path stdout, Path stderr, Path output) throws IOException {
        String digestWidth = "0".repeat(64);
        var metadata = new Observation(request.id(), before, before, null,
                new ControlBuild.FileRef(stdout.toString(), 65536, digestWidth),
                new ControlBuild.FileRef(stderr.toString(), 65536, digestWidth),
                new ControlBuild.FileRef(output.toString(), request.maxOutputBytes(), digestWidth),
                "byte-quotation-only", null, null);
        var quote = new Receipt(RECEIPT_SCHEMA, machine, Instant.now().toString(), Mode.CAPTURE, Status.RED,
                batchRef, batch, limits, 1, List.of(metadata), "byte-quotation-only");
        long remaining = (1L << 20) - encodeReceipt(quote).length;
        // The outer result repeats the same terminal already carried inside nativeSources.
        // Reserve two complete invocation bounds; no second terminal field table or fixed headroom.
        require(remaining >= 2, "Original receipt metadata leaves no room for actual native invocation evidence");
        return remaining / 2;
    }

    /** Same child identity and sole engine inspector are mandatory for every current capture consumer. */
    public static void requireCurrentInvocation(Request request, CompiledCaptureInputProfile.Proof actualProof,
            Limits limits, CompiledCaptureProcess.InvocationEvidence actualEvidence,
            WindowsJobProcess.CommandResult actualTerminal) throws IOException {
        require(actualEvidence != null && actualTerminal != null, "Retained actual Java invocation and terminal required");
        CompiledCaptureProcess.requireProcess(actualEvidence, actualTerminal);
        require(Path.of(actualTerminal.identity().executable()).equals(Path.of(request.command().getFirst())),
                "Actual invocation must use the originally pinned Java executable");
        var logical = invocationRequest(request, actualProof, limits);
        requireOutputDisjoint(Path.of(request.outputPath()), logical);
        CompiledCaptureProcess.requireJavaInvocation(actualEvidence,
                CompiledCaptureProcess.callerCarrier(actualProof.callerRuntimeClosure()), asciiVmOptions(request),
                logical);
    }

    private static void guard(Instant deadline) { if (!Instant.now().isBefore(deadline)) throw new IllegalStateException("Shared capture deadline expired"); }
    private static ControlBuild.FileRef measuredOrNull(Path path, long maximum) throws IOException {
        return Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && Files.size(path) <= maximum ? ControlBuild.FileRef.measure(path) : null;
    }
    static byte[] readPinned(ControlBuild.FileRef ref, int maximum) throws IOException {
        ref.verify(); require(ref.bytes() > 0 && ref.bytes() <= maximum, "Finite exact pinned JSON required");
        byte[] raw;
        try (var input = Files.newInputStream(Path.of(ref.path()))) { raw = input.readNBytes(maximum + 1); }
        require(raw.length == ref.bytes() && raw.length <= maximum, "Pinned JSON size changed during read");
        try {
            String hash = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));
            require(hash.equals(ref.sha256()), "Actually parsed JSON bytes differ from pinned SHA256");
        } catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        ref.verify(); return raw;
    }
    private static Path existingDirectory(String value) throws IOException {
        Path path = canonicalPath(value); require(Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)
                && path.toRealPath().equals(path), "Existing actual canonical directory required"); return path;
    }
    private static void requireInside(Path root, Path output) throws IOException {
        require(output.startsWith(root) && !output.equals(root), "Output must stay inside the admitted root");
        Path parent = output.getParent();
        while (parent != null && !Files.exists(parent, LinkOption.NOFOLLOW_LINKS)) parent = parent.getParent();
        require(parent != null && parent.startsWith(root) && parent.toRealPath().equals(parent), "Output ancestor alias/reparse escape rejected");
    }
    private static Path canonicalPath(String value) {
        Objects.requireNonNull(value); Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.toAbsolutePath().normalize())) throw new IllegalArgumentException("Absolute canonical path required");
        return path;
    }
    private static ControlBuild.FileRef canonicalRef(ControlBuild.FileRef ref) {
        Objects.requireNonNull(ref); return new ControlBuild.FileRef(canonicalPath(ref.path()).toString(), ref.bytes(), ref.sha256());
    }
    private static List<ControlBuild.FileRef> refs(List<ControlBuild.FileRef> values, int minimum, int maximum) {
        if (values == null || values.size() < minimum || values.size() > maximum) throw new IllegalArgumentException("Finite exact reference list required");
        List<ControlBuild.FileRef> result = values.stream().map(CompiledGoldenCapture::canonicalRef).toList();
        if (result.stream().map(ControlBuild.FileRef::path).distinct().count() != result.size()) throw new IllegalArgumentException("Duplicate/conflicting reference paths rejected");
        if (result.stream().anyMatch(ref -> ref.bytes() > (8L << 20))) throw new IllegalArgumentException("Finite source/input reference byte ceilings required");
        return result;
    }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }

    /** Invoke this packaged class on the complete accepted build-tools classpath. */
    public static void main(String[] arguments) throws Exception {
        if (arguments.length == 4 && arguments[0].equals("--accept-receipt") && arguments[2].equals("--expected-mode")) {
            Receipt receipt = acceptedReceipt(ControlBuild.FileRef.measure(canonicalPath(arguments[1])), Mode.valueOf(arguments[3]));
            System.out.println(new String(encodeReceipt(receipt), java.nio.charset.StandardCharsets.UTF_8)); return;
        }
        Map<String, String> options = new HashMap<>();
        require(arguments.length % 2 == 0, "Explicit option/value pairs required");
        Set<String> known = Set.of("--batch", "--receipt", "--output-root", "--temporary-root", "--deadline-utc", "--timeout-seconds", "--child-memory-bytes", "--mode");
        for (int index = 0; index < arguments.length; index += 2) {
            require(known.contains(arguments[index]) && options.putIfAbsent(arguments[index], arguments[index + 1]) == null, "Unknown or repeated CLI option");
        }
        require(options.keySet().equals(known), "All explicit shared capture CLI options required");
        var limits = new Limits(options.get("--output-root"), options.get("--temporary-root"), options.get("--deadline-utc"),
                Integer.parseInt(options.get("--timeout-seconds")), Long.parseLong(options.get("--child-memory-bytes")));
        Receipt receipt = execute(ControlBuild.FileRef.measure(canonicalPath(options.get("--batch"))),
                canonicalPath(options.get("--receipt")), limits, Mode.valueOf(options.get("--mode")));
        System.out.println(new String(encodeReceipt(receipt), java.nio.charset.StandardCharsets.UTF_8));
        if (receipt.status() != Status.PASS) System.exit(1);
    }
}
