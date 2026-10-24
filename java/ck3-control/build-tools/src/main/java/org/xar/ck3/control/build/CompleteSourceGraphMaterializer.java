package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.type.TypeReference;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** The sole native-copy producer for CompleteSourceGraph selections. No build or Game authority. */
public final class CompleteSourceGraphMaterializer {
    static final int JSON_LIMIT = 8 << 20;
    public enum Operation { MATERIALIZE, INDEPENDENT_AUDIT }
    public enum Qualification { SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME }
    public enum Check { MATCH }
    public record Card(String schema, String machineId, String owner, String observedAtUtc, String reviewAtUtc,
            Operation operation, FileRef planRef, FileRef qualifiedToolsRef, FileRef sourceStandingRef,
            FileRef rootAllocationRef, FileRef materializerSourceRef, FileRef graphContractSourceRef,
            FileRef producerActualRef, String sourceRoot, String metadataRoot, long maxSourceNativeBytes,
            long maxMetadataNativeBytes, String status) {
        public Card {
            if (!"xar.complete-source-graph-operation-card/v1".equals(schema)
                    || machineId == null || machineId.isBlank() || !"/root/source03_audit".equals(owner)
                    || !"FULL_GRAPH_SOURCE_OPERATION_ADMITTED".equals(status)) {
                throw new IllegalArgumentException("exact source-only operation card required");
            }
            Objects.requireNonNull(operation); Objects.requireNonNull(planRef); Objects.requireNonNull(qualifiedToolsRef);
            Objects.requireNonNull(sourceStandingRef); Objects.requireNonNull(rootAllocationRef);
            Objects.requireNonNull(materializerSourceRef); Objects.requireNonNull(graphContractSourceRef);
            if ((operation == Operation.INDEPENDENT_AUDIT) != (producerActualRef != null)
                    || (maxSourceNativeBytes != (36L << 20) && maxSourceNativeBytes != (44L << 20)
                            && maxSourceNativeBytes != (56L << 20) && maxSourceNativeBytes != (80L << 20))
                    || maxMetadataNativeBytes <= 0
                    || maxMetadataNativeBytes > (4L << 20)) {
                throw new IllegalArgumentException("finite G2 source/native metadata branch required");
            }
            Instant.parse(observedAtUtc); Instant.parse(reviewAtUtc); absolute(sourceRoot); absolute(metadataRoot);
        }
    }
    public record CopyRow(String targetRelative, Witness originalBefore, Witness originalAfter, Witness destination) {
        public CopyRow {
            Objects.requireNonNull(targetRelative); Objects.requireNonNull(originalBefore);
            Objects.requireNonNull(originalAfter); Objects.requireNonNull(destination);
        }
    }
    public record NativeProof(String schema, String machineId, String observedAtUtc,
            List<Witness> baselineBefore, List<Witness> baselineAfter, List<CopyRow> copies) {
        public NativeProof {
            if (!"xar.complete-source-native-copy-proof/v1".equals(schema) || machineId == null || machineId.isBlank()) {
                throw new IllegalArgumentException("complete native copy proof required");
            }
            Instant.parse(observedAtUtc); baselineBefore = List.copyOf(baselineBefore);
            baselineAfter = List.copyOf(baselineAfter); copies = List.copyOf(copies);
            if (baselineBefore.isEmpty() || copies.isEmpty() || !baselineBefore.equals(baselineAfter)) {
                throw new IllegalArgumentException("all baseline native fields before and after required");
            }
        }
    }
    public record NativeSize(int files, int directories, long logicalBytes, long allocatedFileBytes,
            long directoryGuardBytes, long nativeAccountedBytes) {
        public NativeSize {
            if (files <= 0 || directories <= 0 || logicalBytes < 0 || allocatedFileBytes < 0
                    || directoryGuardBytes != directories * 4096L
                    || nativeAccountedBytes != Math.addExact(allocatedFileBytes, directoryGuardBytes)) {
                throw new IllegalArgumentException("exact native files and directory accounting required");
            }
        }
    }
    public record Receipt(String schema, String machineId, String observedAtUtc, Qualification qualification,
            CompleteSourceGraph.Profile profile, String sourceRoot, int childModules, int reactorProjects,
            int baselineFiles, NativeSize size, FileRef planRef, FileRef cardRef, FileRef inventoryRef,
            FileRef copyProofRef, FileRef qualifiedToolsRef, FileRef materializerSourceRef,
            FileRef graphContractSourceRef, Check strictRoundtrip, Check originalNativePostcheck,
            Check canonicalSourcePostcheck) {
        public Receipt {
            if (!"xar.complete-source-materialization-actual/v1".equals(schema)
                    || machineId == null || machineId.isBlank() || qualification != Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME
                    || profile == null || !profile.completeG2()
                    || childModules != profile.childModules() || reactorProjects != profile.reactorProjects() || baselineFiles <= 0
                    || strictRoundtrip != Check.MATCH || originalNativePostcheck != Check.MATCH
                    || canonicalSourcePostcheck != Check.MATCH) {
                throw new IllegalArgumentException("complete source-only materialization required");
            }
            Instant.parse(observedAtUtc); absolute(sourceRoot); Objects.requireNonNull(size);
            requireSize(size, profile);
            for (FileRef ref : List.of(planRef, cardRef, inventoryRef, copyProofRef, qualifiedToolsRef,
                    materializerSourceRef, graphContractSourceRef)) Objects.requireNonNull(ref);
        }
    }
    private CompleteSourceGraphMaterializer() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("complete-plan.json fresh-materialization-card.json");
        FileRef planRef = FileRef.measure(Path.of(args[0]).toRealPath());
        FileRef cardRef = FileRef.measure(Path.of(args[1]).toRealPath());
        CompleteSourceGraph.Plan plan = CompleteSourceGraph.readPlan(planRef);
        Card card = read(cardRef, Card.class);
        Receipt result = materialize(plan, planRef, card, cardRef);
        System.out.println("COMPLETE_SOURCE_GRAPH_PASS files=" + result.size().files()
                + " logical=" + result.size().logicalBytes() + " native=" + result.size().nativeAccountedBytes());
    }

    public static Receipt materialize(CompleteSourceGraph.Plan plan, FileRef planRef, Card card, FileRef cardRef)
            throws IOException {
        admit(plan, planRef, card, cardRef, Operation.MATERIALIZE);
        CompleteSourceGraph.SelectionProof resolved = CompleteSourceGraph.resolve(plan);
        List<FileRef> baseline = CompleteSourceGraph.baselineFiles(plan);
        Path root = absolute(card.sourceRoot()), metadata = absolute(card.metadataRoot());
        independentRoots(plan, resolved, root, metadata);
        fresh(root); fresh(metadata);
        List<Witness> baselineBefore = observe(baseline);
        Map<Path, Witness> selectedBefore = new LinkedHashMap<>();
        for (CompleteSourceGraph.ResolvedFile row : resolved.files()) {
            Witness before = SharedSourceFiles.observe(absolute(row.sourceRef().path()));
            if (!sameRef(before.source(), row.sourceRef())) throw new IOException("selected input changed before batch");
            selectedBefore.putIfAbsent(absolute(row.sourceRef().path()), before);
        }
        // Bound ordinary-copy allocation and every prospective directory before creating the new root.
        Set<Path> directories = new HashSet<>(); directories.add(root);
        long predicted = 0;
        for (CompleteSourceGraph.ResolvedFile row : resolved.files()) {
            Path output = target(root, row.targetRelative());
            for (Path directory = output.getParent(); directory.startsWith(root); directory = directory.getParent()) {
                directories.add(directory);
                if (directory.equals(root)) break;
            }
            predicted = Math.addExact(predicted, Math.multiplyExact(Math.addExact(row.sourceRef().bytes(), 4095) / 4096, 4096));
        }
        if (Math.addExact(predicted, directories.size() * 4096L) > card.maxSourceNativeBytes()) {
            throw new IOException("ordinary copy native upper bound exceeds admitted source extent");
        }
        Files.createDirectory(root); Files.createDirectory(metadata);
        List<CopyRow> proof = new ArrayList<>(); long allocation = 0;
        Set<String> destinationIdentities = new HashSet<>();
        for (CompleteSourceGraph.ResolvedFile row : resolved.files()) {
            guard(card, planRef, cardRef);
            Witness original = selectedBefore.get(absolute(row.sourceRef().path()));
            SharedSourceFiles.assertUnchanged(original);
            Path output = target(root, row.targetRelative());
            Files.createDirectories(output.getParent());
            CopyRow copied = copy(row.targetRelative(), original, output);
            if (!destinationIdentities.add(copied.destination().nativeFile().identityKey())) {
                throw new IOException("two selected targets alias the same native file");
            }
            allocation = Math.addExact(allocation, copied.destination().nativeFile().allocatedBytes());
            if (allocation + directories.size() * 4096L > card.maxSourceNativeBytes()) {
                throw new IOException("actual source file allocation exceeded admitted source extent");
            }
            proof.add(copied);
        }
        List<Witness> baselineAfter = observe(baseline);
        if (!baselineBefore.equals(baselineAfter)) throw new IOException("full original baseline native postcheck differs");
        for (Witness original : selectedBefore.values()) SharedSourceFiles.assertUnchanged(original);
        List<FileRef> inventory = proof.stream().map(row -> row.destination().source())
                .sorted(Comparator.comparing(FileRef::path)).toList();
        NativeSize size = measure(root, inventory);
        requireSize(size, plan.profile());
        verifyCanonical(plan, root, inventory);
        NativeProof nativeProof = new NativeProof("xar.complete-source-native-copy-proof/v1", card.machineId(),
                Instant.now().toString(), baselineBefore, baselineAfter, proof);
        Path inventoryOutput = metadata.resolve("SOURCE-INVENTORY01.json.gz");
        Path proofOutput = metadata.resolve("COPY-PROOF01.json.gz");
        gzipBounded(inventoryOutput, inventory, metadata, card.maxMetadataNativeBytes());
        gzipBounded(proofOutput, nativeProof, metadata, card.maxMetadataNativeBytes(), plan.profile().copyProofMaxBytes());
        FileRef inventoryRef = FileRef.measure(inventoryOutput), proofRef = FileRef.measure(proofOutput);
        if (!inventory.equals(readGzip(inventoryRef, new TypeReference<List<FileRef>>() { }))
                || !nativeProof.equals(readGzip(proofRef, new TypeReference<NativeProof>() { }, plan.profile().copyProofMaxBytes()))) {
            throw new IOException("actual producer inventory/native copy proof strict roundtrip differs");
        }
        // Entire copy and evidence serialization stay inside the original observations.
        for (Witness original : baselineBefore) SharedSourceFiles.assertUnchanged(original);
        for (Witness original : selectedBefore.values()) SharedSourceFiles.assertUnchanged(original);
        for (CopyRow row : proof) SharedSourceFiles.assertUnchanged(row.destination());
        verifyCanonical(plan, root, inventory); guard(card, planRef, cardRef);
        Receipt receipt = new Receipt("xar.complete-source-materialization-actual/v1", card.machineId(),
                Instant.now().toString(), Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME,
                plan.profile(), root.toString(), plan.modules().size(), plan.modules().size() + 1, baseline.size(),
                size, planRef, cardRef, inventoryRef, proofRef, card.qualifiedToolsRef(), card.materializerSourceRef(),
                card.graphContractSourceRef(), Check.MATCH, Check.MATCH, Check.MATCH);
        Path actual = metadata.resolve("SOURCE-GRAPH-ACTUAL01.json");
        writeFreshBounded(actual, receipt, metadata, card.maxMetadataNativeBytes());
        if (!receipt.equals(read(FileRef.measure(actual), Receipt.class))) throw new IOException("written receipt differs");
        metadataBound(metadata, card.maxMetadataNativeBytes()); return receipt;
    }

    static CopyRow copy(String relative, Witness before, Path output) throws IOException {
        SharedSourceFiles.plainAncestors(output);
        SharedSourceFiles.assertUnchanged(before);
        try (var input = Files.newInputStream(absolute(before.source().path()));
             var destination = Files.newOutputStream(output, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            input.transferTo(destination);
        }
        Witness copied = SharedSourceFiles.observe(output);
        Witness after = SharedSourceFiles.observe(absolute(before.source().path()));
        CopyRow row = new CopyRow(relative, before, after, copied); relation(row);
        if (Files.isSameFile(absolute(before.source().path()), output)) throw new IOException("copy aliases original file");
        return row;
    }
    static void relation(CopyRow row) throws IOException {
        // Selected target canonicality is owned by CompleteSourceGraph, including the resource path domain.
        new CompleteSourceGraph.ResolvedFile(row.targetRelative(), row.originalBefore().source());
        if (!row.originalBefore().equals(row.originalAfter())
                || !sameContent(row.originalBefore().source(), row.destination().source())
                || row.originalBefore().nativeFile().identityKey().equals(row.destination().nativeFile().identityKey())
                || row.destination().nativeFile().linkCount() != 1) {
            throw new IOException("actual copy original-before/after, private identity or single-link invariant failed");
        }
    }
    static void admit(CompleteSourceGraph.Plan plan, FileRef planRef, Card card, FileRef cardRef, Operation operation)
            throws IOException {
        if (card.operation() != operation || !plan.profile().completeG2()
                || !plan.machineId().equals(card.machineId())
                || !card.machineId().equals(WindowsJobProcess.currentMachineId()) || !sameRef(planRef, card.planRef())) {
            throw new IOException("exact machine/operation/G2 profile/plan admission required");
        }
        requireProfileBudget(plan.profile(), card.maxSourceNativeBytes());
        ControlBuild.BuildReceipt tools = completedReceipt(card, planRef, cardRef);
        // Reject an incapable runtime before any source or metadata directory is created.
        try { ControlBuild.SourceLimitProfile.valueOf(plan.profile().sourceLimitProfile().name()); }
        catch (IllegalArgumentException error) { throw new IOException("qualified canonical ControlBuild " + plan.profile() + " provider unavailable", error); }
        List<FileRef> actual = ControlBuild.producerClosure();
        if (actual.size() != 6 || !ordered(actual).equals(ordered(tools.completeDeployment()))) {
            throw new IOException("complete exact qualified build-tools runtime required");
        }
    }
    static void requireProfileBudget(CompleteSourceGraph.Profile profile, long cardMaximum) throws IOException {
        if (profile == null || !profile.completeG2() || cardMaximum != profile.maxNativeBytes()) {
            throw new IOException("Operation card native source extent differs from its exact source profile");
        }
    }

    /** Historical software qualification and fresh operation authority are independent inputs. */
    static ControlBuild.BuildReceipt completedReceipt(Card card, FileRef planRef, FileRef cardRef) throws IOException {
        guard(card, planRef, cardRef);
        return ControlBuild.verifiedCompletedReceipt(card.qualifiedToolsRef());
    }

    static void guard(Card card, FileRef planRef, FileRef cardRef) throws IOException {
        Instant now = Instant.now(), observed = Instant.parse(card.observedAtUtc()), review = Instant.parse(card.reviewAtUtc());
        if (observed.isAfter(now.plusSeconds(5)) || !observed.isBefore(review) || !now.isBefore(review)) {
            throw new IOException("fresh finite operation card expired");
        }
        planRef.verify(); cardRef.verify();
        for (FileRef ref : List.of(card.planRef(), card.qualifiedToolsRef(), card.sourceStandingRef(), card.rootAllocationRef(),
                card.materializerSourceRef(), card.graphContractSourceRef())) ref.verify();
        if (card.producerActualRef() != null) card.producerActualRef().verify();
    }
    static void independentRoots(CompleteSourceGraph.Plan plan, CompleteSourceGraph.SelectionProof resolved,
            Path root, Path metadata) throws IOException {
        SharedSourceFiles.plainAncestors(root); SharedSourceFiles.plainAncestors(metadata);
        Path baseline = absolute(plan.baseline().root());
        if (overlap(root, baseline) || overlap(root, metadata) || overlap(metadata, baseline)) {
            throw new IOException("fresh source, baseline and metadata must be independent roots");
        }
        for (CompleteSourceGraph.ResolvedFile row : resolved.files()) {
            Path origin = absolute(row.sourceRef().path());
            if (origin.startsWith(root) || origin.startsWith(metadata)) throw new IOException("selected origin is inside new output");
        }
        if (!Files.isDirectory(root.getParent(), LinkOption.NOFOLLOW_LINKS)
                || !Files.isDirectory(metadata.getParent(), LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("approved existing ordinary output parents required");
        }
    }
    static void verifyCanonical(CompleteSourceGraph.Plan plan, Path root, List<FileRef> inventory) throws IOException {
        CompleteSourceGraph.requireRelocatedTargetsAbsent(plan, root);
        CompleteSourceGraph.MaterializedSources verified = CompleteSourceGraph.verifyMaterialized(plan, root);
        if (!verified.sourcePins().equals(inventory)) throw new IOException("canonical Maven producer differs from full copied inventory");
        Set<Path> expected = new HashSet<>();
        for (FileRef ref : inventory) expected.add(absolute(ref.path()));
        Set<Path> actual = new HashSet<>();
        try (var walk = Files.walk(root)) {
            for (Path path : walk.toList()) {
                SharedSourceFiles.plainAncestors(path);
                if (Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) continue;
                if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("nonordinary copied entry");
                actual.add(path.toAbsolutePath().normalize());
            }
        }
        if (!actual.equals(expected)) throw new IOException("ordinary copied tree differs from canonical selected set");
    }
    static NativeSize measure(Path root, List<FileRef> inventory) throws IOException {
        long logical = 0, allocation = 0; int directories;
        for (FileRef ref : inventory) {
            Witness observed = SharedSourceFiles.observe(absolute(ref.path()));
            if (!sameRef(observed.source(), ref)) throw new IOException("inventory source drift during native census");
            logical = Math.addExact(logical, ref.bytes()); allocation = Math.addExact(allocation, observed.nativeFile().allocatedBytes());
        }
        try (var walk = Files.walk(root)) {
            directories = Math.toIntExact(walk.filter(path -> Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)).count());
        }
        return new NativeSize(inventory.size(), directories, logical, allocation, directories * 4096L,
                Math.addExact(allocation, directories * 4096L));
    }
    static void requireSize(NativeSize size, CompleteSourceGraph.Profile profile) {
        if (size.files() > profile.maxFiles() || size.logicalBytes() > profile.maxLogicalBytes()
                || size.nativeAccountedBytes() > profile.maxNativeBytes()) {
            throw new IllegalArgumentException("original finite profile extent exceeded");
        }
    }
    static List<Witness> observe(List<FileRef> refs) throws IOException {
        List<Witness> result = new ArrayList<>();
        for (FileRef ref : refs) {
            Witness witness = SharedSourceFiles.observe(absolute(ref.path()));
            if (!sameRef(witness.source(), ref)) throw new IOException("exact native observation source differs");
            result.add(witness);
        }
        return List.copyOf(result);
    }
    static void metadataBound(Path root, long maximum) throws IOException {
        long allocation = 0;
        try (var walk = Files.walk(root)) {
            for (Path path : walk.toList()) {
                SharedSourceFiles.plainAncestors(path);
                allocation = Math.addExact(allocation, Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)
                        ? 4096 : SharedSourceFiles.nativeFile(path).allocatedBytes());
                if (allocation > maximum) throw new IOException("full graph metadata native envelope exceeded");
            }
        }
    }
    static void fresh(Path path) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        if (Files.exists(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("fresh non-replay output required: " + path);
    }
    static Path target(Path root, String relative) throws IOException {
        Path result = root.resolve(relative).normalize();
        if (!result.startsWith(root) || result.equals(root)) throw new IOException("target escapes assigned graph");
        return result;
    }
    static Path absolute(String value) {
        Path path = Path.of(value);
        if (!path.isAbsolute()) throw new IllegalArgumentException("absolute path required");
        return path.toAbsolutePath().normalize();
    }
    static boolean overlap(Path first, Path second) { return first.startsWith(second) || second.startsWith(first); }
    static boolean sameContent(FileRef first, FileRef second) {
        return first.bytes() == second.bytes() && first.sha256().equals(second.sha256());
    }
    static boolean sameRef(FileRef first, FileRef second) {
        return sameContent(first, second) && absolute(first.path()).equals(absolute(second.path()));
    }
    static List<FileRef> ordered(List<FileRef> refs) {
        return refs.stream().sorted(Comparator.comparing(FileRef::path)).toList();
    }
    static <T> T read(FileRef ref, Class<T> type) throws IOException {
        ref.verify(); if (ref.bytes() > JSON_LIMIT) throw new IOException("finite typed metadata bound exceeded");
        byte[] bytes = Files.readAllBytes(absolute(ref.path())); ref.verify();
        return ControlBuild.strictMapper().readValue(bytes, type);
    }
    static <T> T readGzip(FileRef ref, TypeReference<T> type) throws IOException {
        return readGzip(ref, type, JSON_LIMIT);
    }
    static <T> T readGzip(FileRef ref, TypeReference<T> type, int limit) throws IOException {
        requireProofLimit(limit);
        ref.verify(); byte[] bytes;
        try (var input = new GZIPInputStream(Files.newInputStream(absolute(ref.path())))) { bytes = input.readNBytes(limit + 1); }
        if (bytes.length > limit) throw new IOException("finite native proof transport exceeded");
        ref.verify(); return ControlBuild.strictMapper().readValue(bytes, type);
    }
    static void gzipBounded(Path path, Object value, Path root, long maximum) throws IOException {
        gzipBounded(path, value, root, maximum, JSON_LIMIT);
    }
    static void gzipBounded(Path path, Object value, Path root, long maximum, int limit) throws IOException {
        requireProofLimit(limit);
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(value);
        if (bytes.length > limit) throw new IOException("finite native proof serialization exceeded");
        var buffer = new java.io.ByteArrayOutputStream();
        try (var gzip = new GZIPOutputStream(buffer)) { gzip.write(bytes); }
        byte[] compressed = buffer.toByteArray();
        long reserved = Math.multiplyExact(Math.addExact(compressed.length, 4095) / 4096, 4096);
        metadataBound(root, Math.subtractExact(maximum, reserved));
        Files.write(path, compressed, StandardOpenOption.CREATE_NEW);
        metadataBound(root, maximum);
    }
    private static void requireProofLimit(int limit) throws IOException {
        if (limit != JSON_LIMIT && limit != (16 << 20)) throw new IOException("Explicit finite versioned native proof limit required");
    }
    static void writeFreshBounded(Path path, Object value, Path root, long maximum) throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(value);
        if (bytes.length > JSON_LIMIT) throw new IOException("finite typed metadata serialization exceeded");
        long reserved = Math.multiplyExact(Math.addExact(bytes.length, 4095) / 4096, 4096);
        metadataBound(root, Math.subtractExact(maximum, reserved));
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
        metadataBound(root, maximum);
    }
}


