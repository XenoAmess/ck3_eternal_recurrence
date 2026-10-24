package org.xar.ck3.control.build;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;
import org.xar.ck3.control.build.CompleteSourceGraph.Plan;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Real Assembly -> Request -> Plan -> final Java winner-index producer. Source metadata only. */
public final class SourceGraphSdkIndexProducer {
    public static final String REQUEST_SCHEMA = "xar.source-graph.sdk-index-export-request/v1";
    public static final String RECEIPT_SCHEMA = "xar.source-graph.sdk-index-export-actual/v1";
    public static final String STATUS = "JAVA_SOURCE_WINNERS_ONLY_SOURCE_SELECTION_NOT_COMPILED";
    public static final String INDEX_NAME = "SINGLE-WINNER-SOURCE-INDEX01.json.gz";
    public static final String RECEIPT_NAME = "SOURCE-INDEX-EXPORT-ACTUAL01.json";
    private static final int RECEIPT_LIMIT = 1 << 20;

    /** This output is a fresh metadata directory under an already admitted parent, never a source tree. */
    public record Request(String schema, String machineId, FileRef inputRef, FileRef actualPlanRef,
            String outputRoot) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema))
                throw new IllegalArgumentException("Exact SDK-index export schema and machine required");
            SingleWinnerSourceIndex.requireMachineId(machineId);
            bounded(inputRef, SingleWinnerSourceIndex.MAX_BYTES);
            bounded(actualPlanRef, SingleWinnerSourceIndex.MAX_BYTES);
            if (outputRoot == null || !Path.of(outputRoot).isAbsolute()
                    || Path.of(outputRoot).toAbsolutePath().normalize().getParent() == null)
                throw new IllegalArgumentException("Absolute finite metadata output root required");
        }
    }

    /** Directly usable by the SDK's existing compressed-source-index field. */
    public record IndexArtifact(FileRef compressedRef, int uncompressedBytes, String uncompressedSha256) {
        public IndexArtifact {
            bounded(compressedRef, SingleWinnerSourceIndex.MAX_BYTES);
            if (uncompressedBytes <= 0 || uncompressedBytes > SingleWinnerSourceIndex.MAX_BYTES
                    || uncompressedSha256 == null || !uncompressedSha256.matches("[0-9a-f]{64}"))
                throw new IllegalArgumentException("Exact bounded uncompressed index identity required");
        }
    }

    /** Input/Plan custody is a sidecar; the SDK's closed eight-field v1 index wire is unchanged. */
    public record Receipt(String schema, String machineId, String owner, String observedAtUtc, String status,
            FileRef requestRef, FileRef inputRef, FileRef actualAssemblyRequestRef, FileRef actualPlanRef,
            IndexArtifact index, int finalFiles, int javaWinnerFiles, int excludedNonJavaFiles,
            int retiredTargets, String assemblyRequestComparison, String actualPlanComparison,
            String indexRoundtrip, String finalSourcePostcheck, String qualification) {
        public Receipt {
            if (!RECEIPT_SCHEMA.equals(schema) || !"/root/source_graph".equals(owner)
                    || !STATUS.equals(status))
                throw new IllegalArgumentException("Exact source-only export receipt identity required");
            SingleWinnerSourceIndex.requireMachineId(machineId);
            Instant.parse(observedAtUtc);
            bounded(requestRef, RECEIPT_LIMIT);
            bounded(inputRef, SingleWinnerSourceIndex.MAX_BYTES);
            bounded(actualAssemblyRequestRef, SingleWinnerSourceIndex.MAX_BYTES);
            bounded(actualPlanRef, SingleWinnerSourceIndex.MAX_BYTES);
            Objects.requireNonNull(index);
            if (javaWinnerFiles <= 0 || excludedNonJavaFiles < 0
                    || finalFiles != Math.addExact(javaWinnerFiles, excludedNonJavaFiles) || retiredTargets < 0
                    || !"MATCH".equals(assemblyRequestComparison) || !"MATCH".equals(actualPlanComparison)
                    || !"MATCH".equals(indexRoundtrip) || !"MATCH".equals(finalSourcePostcheck)
                    || !"SOURCE_SELECTION_ONLY_NO_NATIVE_COMPILED_RUNTIME_OR_GAME_AUTHORITY".equals(qualification))
                throw new IllegalArgumentException("Complete actual source-index export comparisons required");
        }
    }

    public record Exported(Receipt receipt, FileRef receiptRef) {
        public Exported { Objects.requireNonNull(receipt); bounded(receiptRef, RECEIPT_LIMIT); }
    }

    private record Prepared(SingleWinnerSourceIndex index, Plan plan, FileRef assemblyRef,
            CompleteSourceGraph.SelectionProof proof) { }
    private SourceGraphSdkIndexProducer() { }

    /**
     * Pure source custody operation, usable by SDK regression fixtures without a test-runner dependency.
     * Both inputs are real exact files from the shared generation pipeline, not a handwritten index.
     */
    public static SingleWinnerSourceIndex produce(FileRef inputRef, FileRef actualPlanRef, Clock clock)
            throws IOException {
        return prepare(inputRef, actualPlanRef, clock).index();
    }

    private static Prepared prepare(FileRef inputRef, FileRef actualPlanRef, Clock clock) throws IOException {
        Objects.requireNonNull(clock, "clock");
        Source08Assembly.Input input = ControlBuild.strictMapper().readValue(
                read(inputRef, SingleWinnerSourceIndex.MAX_BYTES), Source08Assembly.Input.class);
        Plan plan = ControlBuild.strictMapper().readValue(
                read(actualPlanRef, SingleWinnerSourceIndex.MAX_BYTES), Plan.class);
        if (!input.machineId().equals(plan.machineId())
                || Instant.parse(input.observedAtUtc()).isAfter(clock.instant())
                || Instant.parse(plan.observedAtUtc()).isAfter(clock.instant()))
            throw new IOException("Same-machine nonfuture actual Input and Plan required");
        if (plan.selections().isEmpty()) throw new IOException("Actual producer component selections required");
        FileRef assemblyRef = plan.selections().getFirst().selectionRef();
        for (var selection : plan.selections()) {
            if (!assemblyRef.equals(selection.selectionRef()))
                throw new IOException("Actual Plan must name the one shared assembly Request");
        }
        bounded(assemblyRef, SingleWinnerSourceIndex.MAX_BYTES);
        var actualRequest = SourceGraphPlanProducer.readRequest(assemblyRef);
        var reproducedRequest = Source08Assembly.prepare(input);
        if (!reproducedRequest.equals(actualRequest))
            throw new IOException("Actual assembly Request differs from exact Source08 Input producer");
        Plan reproducedPlan = SourceGraphPlanProducer.produce(assemblyRef);
        if (!reproducedPlan.equals(plan))
            throw new IOException("Actual typed Plan differs from exact shared Request producer");
        var proof = CompleteSourceGraph.resolve(plan);
        List<SelectedFile> java = proof.files().stream()
                .filter(file -> file.targetRelative().endsWith(".java"))
                .map(file -> new SelectedFile(file.targetRelative(), file.sourceRef())).toList();
        // Non-Java resources include legitimate empty fixtures. They remain in the real source graph,
        // while SDK runtime-role matching has always required only Java rows in this Java winner index.
        SingleWinnerSourceIndex index = new SingleWinnerSourceIndex(SingleWinnerSourceIndex.SCHEMA,
                input.machineId(), "/root/source_graph", clock.instant().toString(), STATUS, inputRef, false, java);
        index.validateFor(input.machineId(), clock);
        index.encode();
        inputRef.verify(); actualPlanRef.verify(); assemblyRef.verify();
        return new Prepared(index, plan, assemblyRef, proof);
    }

    /**
     * Exports a fresh gzip index and exact sidecar. The caller supplies its actual machine identity;
     * the CLI obtains it from the existing WindowsJobProcess provider. This grants no runtime admission.
     */
    public static Exported export(FileRef requestRef, String currentMachine, Clock clock) throws IOException {
        Request request = ControlBuild.strictMapper().readValue(read(requestRef, RECEIPT_LIMIT), Request.class);
        if (!request.machineId().equals(currentMachine))
            throw new IOException("Current exporter machine differs from exact request");
        Prepared prepared = prepare(request.inputRef(), request.actualPlanRef(), clock);
        prepared.index().validateFor(currentMachine, clock);
        Path root = Path.of(request.outputRoot()).toAbsolutePath().normalize();
        SharedSourceFiles.plainAncestors(root);
        if (!Files.isDirectory(root.getParent(), LinkOption.NOFOLLOW_LINKS)
                || Files.exists(root, LinkOption.NOFOLLOW_LINKS)
                || root.startsWith(Path.of(prepared.plan().baseline().root()).toAbsolutePath().normalize()))
            throw new IOException("Fresh admitted metadata output outside protected baseline required");
        for (var file : prepared.proof().files()) {
            if (Path.of(file.sourceRef().path()).toAbsolutePath().normalize().startsWith(root))
                throw new IOException("Metadata output overlaps an original selected source");
        }
        byte[] plain = prepared.index().encode();
        byte[] zipped;
        try (var bytes = new ByteArrayOutputStream(); var gzip = new GZIPOutputStream(bytes)) {
            gzip.write(plain); gzip.finish(); zipped = bytes.toByteArray();
        }
        if (zipped.length > SingleWinnerSourceIndex.MAX_BYTES)
            throw new IOException("Compressed source index exceeds finite bound");
        // All validation and the real generation chain complete before creating any output.
        Files.createDirectory(root);
        Path indexPath = root.resolve(INDEX_NAME);
        Files.write(indexPath, zipped, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        FileRef indexRef = FileRef.measure(indexPath);
        IndexArtifact artifact = new IndexArtifact(indexRef, plain.length, sha256(plain));
        SingleWinnerSourceIndex readBack = readIndex(artifact, currentMachine, clock);
        if (!prepared.index().equals(readBack))
            throw new IOException("Actual compressed source index differs on strict readback");
        for (var file : prepared.proof().files()) file.sourceRef().verify();
        request.inputRef().verify(); request.actualPlanRef().verify(); prepared.assemblyRef().verify();
        requestRef.verify(); indexRef.verify();
        Receipt receipt = new Receipt(RECEIPT_SCHEMA, currentMachine, "/root/source_graph",
                clock.instant().toString(), STATUS, requestRef, request.inputRef(), prepared.assemblyRef(),
                request.actualPlanRef(), artifact, prepared.proof().files().size(),
                readBack.selectedFiles().size(), prepared.proof().files().size() - readBack.selectedFiles().size(),
                prepared.plan().relocations().size(), "MATCH", "MATCH", "MATCH", "MATCH",
                "SOURCE_SELECTION_ONLY_NO_NATIVE_COMPILED_RUNTIME_OR_GAME_AUTHORITY");
        byte[] receiptBytes = ControlBuild.strictMapper().writeValueAsBytes(receipt);
        if (receiptBytes.length > RECEIPT_LIMIT
                || !receipt.equals(ControlBuild.strictMapper().readValue(receiptBytes, Receipt.class)))
            throw new IOException("Strict finite source-index export receipt roundtrip differs");
        Path receiptPath = root.resolve(RECEIPT_NAME);
        Files.write(receiptPath, receiptBytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        FileRef receiptRef = FileRef.measure(receiptPath);
        if (!receipt.equals(ControlBuild.strictMapper().readValue(read(receiptRef, RECEIPT_LIMIT), Receipt.class)))
            throw new IOException("Actual source-index export receipt differs on strict readback");
        return new Exported(receipt, receiptRef);
    }

    /** Shared exact gzip consumer for SDK boundary conversion and exporter readback regressions. */
    public static SingleWinnerSourceIndex readIndex(IndexArtifact artifact, String currentMachine, Clock clock)
            throws IOException {
        Objects.requireNonNull(artifact, "exact index artifact");
        byte[] plain;
        try (var gzip = new GZIPInputStream(new ByteArrayInputStream(
                read(artifact.compressedRef(), SingleWinnerSourceIndex.MAX_BYTES)))) {
            plain = gzip.readNBytes(SingleWinnerSourceIndex.MAX_BYTES + 1);
        }
        if (plain.length != artifact.uncompressedBytes() || plain.length > SingleWinnerSourceIndex.MAX_BYTES
                || !sha256(plain).equals(artifact.uncompressedSha256()))
            throw new IOException("Exact bounded decompressed index bytes/SHA differ");
        SingleWinnerSourceIndex index = SingleWinnerSourceIndex.decode(plain);
        index.validateFor(currentMachine, clock);
        index.inputRef().verify();
        artifact.compressedRef().verify();
        return index;
    }

    private static FileRef checked(FileRef ref, int maximum) throws IOException {
        bounded(ref, maximum); ref.verify(); return ref;
    }
    private static byte[] read(FileRef ref, int maximum) throws IOException {
        checked(ref, maximum);
        byte[] bytes;
        try (var input = Files.newInputStream(Path.of(ref.path()))) {
            bytes = input.readNBytes(maximum + 1);
        }
        if (bytes.length > maximum || bytes.length != ref.bytes())
            throw new IOException("Exact metadata exceeded the finite read bound or changed length");
        ref.verify(); return bytes;
    }
    private static void bounded(FileRef ref, int maximum) {
        Objects.requireNonNull(ref, "exact bounded metadata reference");
        if (ref.bytes() <= 0 || ref.bytes() > maximum)
            throw new IllegalArgumentException("Bounded nonempty metadata reference required");
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }

    /** Root invokes this source-only producer only with a fresh admitted metadata operation. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 3)
            throw new IllegalArgumentException("exact-export-request.json bytes sha256");
        FileRef requestRef = new FileRef(arguments[0], Long.parseLong(arguments[1]), arguments[2]);
        Exported result = export(requestRef, WindowsJobProcess.currentMachineId(), Clock.systemUTC());
        System.out.println(STATUS + " receipt=" + result.receiptRef().path()
                + " sha256=" + result.receiptRef().sha256());
    }
}
