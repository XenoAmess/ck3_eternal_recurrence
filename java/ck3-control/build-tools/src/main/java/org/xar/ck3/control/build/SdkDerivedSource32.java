package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.Actual;
import org.xar.ck3.control.build.SdkSourceAssembly.Digest;
import org.xar.ck3.control.build.SdkSourceAssembly.SourceRole;

/** A derived SDK inventory has its own schema and exact parent. The parent Git anchor never certifies new bytes. */
public final class SdkDerivedSource32 {
    public static final String SCHEMA = "xar.sdk-derived-source32/v2";
    public static final String VERIFIED_SCHEMA = "xar.sdk-derived-source32-verified/v2";
    private static final String PREFIX = "ck3_autonomous_player/src/";
    private static final String NATIVE_DRIVER = "xar_autoplayer/bridge/native_driver.py";
    private static final int MAX_METADATA = 2 << 20;
    private SdkDerivedSource32() { }
    public enum SourcePurpose { PARENT_NATIVE_UNCHANGED, FULL_SOFTWARE }
    public record NativeDriverIntent(Digest parentContent, Digest selectedContent) {
        public NativeDriverIntent { Objects.requireNonNull(parentContent); Objects.requireNonNull(selectedContent); }
    }
    public record Row(String relativePath, Digest content, String gitBlobSha1, String gitMode) {
        public Row {
            ExactSourcePatch.relative(relativePath); Objects.requireNonNull(content);
            if (gitBlobSha1 == null || !gitBlobSha1.matches("[0-9a-f]{40}") || !List.of("100644", "100755").contains(gitMode))
                throw new IllegalArgumentException("Exact ordinary source content and Git blob required");
        }
    }
    public record Delta(String relativePath, Digest before, Digest after) {
        public Delta { ExactSourcePatch.relative(relativePath); Objects.requireNonNull(after); if (after.equals(before)) throw new IllegalArgumentException("Actual source change required"); }
    }
    public record Lineage(String schema, String machineId, String observedAtUtc, FileRef parentFreezeRef,
                          FileRef parentAnchorRef, FileRef assemblyActualRef, String sdkRoot, SourcePurpose sourcePurpose, NativeDriverIntent nativeDriverIntent,
                          List<Row> currentInventory, List<Delta> deltas, boolean runtimeAdmitted) {
        public Lineage {
            if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}") || runtimeAdmitted)
                throw new IllegalArgumentException("Explicit derived source-only lineage required");
            Instant.parse(observedAtUtc); Objects.requireNonNull(parentFreezeRef); Objects.requireNonNull(parentAnchorRef);
            Objects.requireNonNull(assemblyActualRef); absolute(sdkRoot); Objects.requireNonNull(sourcePurpose); Objects.requireNonNull(nativeDriverIntent);
            if (sourcePurpose == SourcePurpose.PARENT_NATIVE_UNCHANGED && !nativeDriverIntent.parentContent().equals(nativeDriverIntent.selectedContent()))
                throw new IllegalArgumentException("Parent-native source branch requires exact unchanged native bytes");
            currentInventory = List.copyOf(currentInventory); deltas = List.copyOf(deltas);
            if (currentInventory.isEmpty() || currentInventory.size() > 4096 || deltas.isEmpty() || deltas.size() > 4096)
                throw new IllegalArgumentException("Complete bounded changed SDK inventory required");
            names(currentInventory.stream().map(Row::relativePath).toList()); names(deltas.stream().map(Delta::relativePath).toList());
        }
    }
    public record Verified(String schema, String machineId, String sdkRoot, FileRef lineageRef,
                           FileRef parentFreezeRef, FileRef parentAnchorRef, String parentBusinessSourceCommit,
                           FileRef assemblyActualRef, FileRef sdkNativeDriverRef, SourcePurpose sourcePurpose, NativeDriverIntent nativeDriverIntent, int currentSourceFiles,
                           int changedSourceFiles, boolean runtimeAdmitted, boolean nativeRestoreAdmitted) {
        public Verified {
            if (!VERIFIED_SCHEMA.equals(schema) || runtimeAdmitted || nativeRestoreAdmitted || parentBusinessSourceCommit == null || !parentBusinessSourceCommit.matches("[0-9a-f]{40}"))
                throw new IllegalArgumentException("Verified source lineage grants no runtime or Native restore authority");
            Objects.requireNonNull(sourcePurpose); Objects.requireNonNull(nativeDriverIntent);
            if (sourcePurpose == SourcePurpose.PARENT_NATIVE_UNCHANGED && !nativeDriverIntent.parentContent().equals(nativeDriverIntent.selectedContent()))
                throw new IllegalArgumentException("Unchanged-native source proof cannot certify changed bytes");
        }
    }
    private record Parent(JsonNode json, FileRef anchorRef, List<SdkSourceAssembly.FrozenSourceRow> rows) { }
    public static final String EMISSION_SCHEMA = "xar.sdk-derived-source32-java-verification/v2";
    public record VerifiedEmission(String schema, String machineId, String observedAtUtc, FileRef qualifiedToolsBuildRef,
                                   FileRef producerSourceRef, FileRef compiledProducerSourceRef,
                                   List<FileRef> producerRuntimeRefs, List<Row> currentInventory, Verified verified) {
        public VerifiedEmission {
            if (!EMISSION_SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}"))
                throw new IllegalArgumentException("Explicit source-bound Java verification receipt required");
            Instant.parse(observedAtUtc); Objects.requireNonNull(qualifiedToolsBuildRef); Objects.requireNonNull(producerSourceRef);
            Objects.requireNonNull(compiledProducerSourceRef); Objects.requireNonNull(verified); producerRuntimeRefs = List.copyOf(producerRuntimeRefs);
            currentInventory = List.copyOf(currentInventory); names(currentInventory.stream().map(Row::relativePath).toList());
            if (!machineId.equals(verified.machineId()) || producerRuntimeRefs.isEmpty() || producerRuntimeRefs.size() > 100
                    || currentInventory.size() != verified.currentSourceFiles() || currentInventory.isEmpty() || currentInventory.size() > 4096)
                throw new IllegalArgumentException("Same-machine complete Java producer closure required");
        }
    }
    private record ProducerProof(FileRef source, FileRef compiledSource, List<FileRef> runtime) { }

    /** Called by the existing post-reactor SDK configuration producer, before its child bootstrap is written. */
    public static FileRef emitVerified(FileRef lineageRef, FileRef qualifiedToolsBuildRef, Path freshOutput) throws IOException {
        ProducerProof proof = producerProof(qualifiedToolsBuildRef); Verified verified = verify(lineageRef);
        Path output = freshOutput.toAbsolutePath().normalize(); SharedSourceFiles.plainAncestors(output);
        if (!freshOutput.isAbsolute() || Files.exists(output) || !Files.isDirectory(output.getParent()))
            throw new IOException("New absolute immutable verification output with an existing admitted parent required");
        Lineage lineage = read(lineageRef); Actual actual = SdkSourceAssembly.readActual(lineage.assemblyActualRef());
        JsonNode parent = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(lineage.parentFreezeRef().path())));
        for (Path protectedRoot : List.of(absolute(verified.sdkRoot()), absolute(actual.graphRoot()), absolute(requiredText(parent, "source_root"))))
            if (output.startsWith(protectedRoot)) throw new IOException("Verification output must not mutate an SDK, assembly or original parent source tree");
        VerifiedEmission emission = new VerifiedEmission(EMISSION_SCHEMA, verified.machineId(), Instant.now().toString(),
                qualifiedToolsBuildRef, proof.source(), proof.compiledSource(), proof.runtime(), lineage.currentInventory(), verified);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(emission);
        if (raw.length > MAX_METADATA) throw new IOException("Bounded immutable verification receipt required");
        Files.write(output, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        FileRef result = FileRef.measure(output); readVerifiedEmission(result); return result;
    }

    /** No JSON flag grants qualification: the actual tools archive, both source inventories and SDK lineage are rechecked. */
    public static Verified readVerifiedEmission(FileRef emissionRef) throws IOException {
        if (emissionRef.bytes() < 1 || emissionRef.bytes() > MAX_METADATA) throw new IOException("Bounded Java verification receipt required");
        emissionRef.verify();
        VerifiedEmission emission = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(emissionRef.path())), VerifiedEmission.class);
        ProducerProof proof = producerProof(emission.qualifiedToolsBuildRef());
        if (!emission.producerSourceRef().equals(proof.source()) || !emission.compiledProducerSourceRef().equals(proof.compiledSource())
                || !emission.producerRuntimeRefs().equals(proof.runtime()) || !emission.verified().equals(verify(emission.verified().lineageRef()))
                || !emission.currentInventory().equals(read(emission.verified().lineageRef()).currentInventory()))
            throw new IOException("Java producer, source or complete current SDK verification differs");
        emissionRef.verify(); return emission.verified();
    }

    public static void main(String[] args) throws IOException {
        if (args.length != 7) throw new IllegalArgumentException("LINEAGE_PATH BYTES SHA256 TOOLS_BUILD_PATH BYTES SHA256 NEW_OUTPUT_FILE");
        FileRef result = emitVerified(new FileRef(args[0], Long.parseLong(args[1]), args[2]),
                new FileRef(args[3], Long.parseLong(args[4]), args[5]), Path.of(args[6]));
        System.out.println(ControlBuild.strictMapper().writeValueAsString(result));
    }

    private static ProducerProof producerProof(FileRef buildRef) throws IOException {
        var build = ControlBuild.verifiedCompletedReceipt(buildRef);
        if (build.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME) throw new IOException("Actual qualified tools runtime build required");
        try {
            Path ownArchive = Path.of(SdkDerivedSource32.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
            Path controlArchive = Path.of(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
            if (!Files.isRegularFile(ownArchive) || !ownArchive.equals(controlArchive))
                throw new IOException("Derived verifier and existing build producer must execute from the same actual qualified archive");
            List<FileRef> runtime = ControlBuild.producerClosure();
            if (!runtime.equals(build.completeDeployment()) || runtime.stream().noneMatch(ref -> absolute(ref.path()).equals(ownArchive)))
                throw new IOException("Executing Java producer closure differs from the entire qualified tools deployment");
            String suffix = "src/main/java/org/xar/ck3/control/build/SdkDerivedSource32.java";
            Path sourceRoot = absolute(build.sourceRoot()), compiledRoot = absolute(build.compiledSourceRoot());
            FileRef source = null, compiled = null;
            for (FileRef pin : build.sourcePins()) {
                Path path = absolute(pin.path()); if (!path.startsWith(sourceRoot)) continue;
                String relative = sourceRoot.relativize(path).toString().replace('\\', '/');
                if (!relative.equals(suffix) && !relative.equals("tools/" + suffix)) continue;
                if (source != null) throw new IOException("One actual verifier source required");
                source = pin; Path compiledPath = compiledRoot.resolve(relative).normalize();
                for (FileRef candidate : build.compiledSourcePins()) if (absolute(candidate.path()).equals(compiledPath)) {
                    if (compiled != null) throw new IOException("One actual compiled verifier source required"); compiled = candidate;
                }
            }
            if (source == null || compiled == null || source.bytes() != compiled.bytes() || !source.sha256().equals(compiled.sha256()))
                throw new IOException("Verifier must match both original and actually compiled complete source inventories");
            source.verify(); compiled.verify(); buildRef.verify(); return new ProducerProof(source, compiled, runtime);
        } catch (java.net.URISyntaxException error) { throw new IOException("Actual Java producer archive URI required", error); }
    }


    static Lineage derive(Actual actual, FileRef actualRef, FileRef parentRef) throws IOException {
        return derive(actual, actualRef, parentRef, SourcePurpose.PARENT_NATIVE_UNCHANGED, null);
    }
    static Lineage derive(Actual actual, FileRef actualRef, FileRef parentRef, SourcePurpose purpose, NativeDriverIntent intent) throws IOException {
        Objects.requireNonNull(purpose);
        Parent parent = parent(parentRef, actual.machineId()); actualRef.verify();
        if (!Path.of(actualRef.path()).toAbsolutePath().normalize().equals(absolute(actual.graphRoot()).resolve(".assembly/ACTUAL.json")))
            throw new IOException("Derived lineage must bind this exact persisted assembly");
        var old = new LinkedHashMap<String, SdkSourceAssembly.FrozenSourceRow>();
        for (var row : parent.rows()) old.put(row.relative(), row);
        var current = new LinkedHashMap<String, Row>();
        for (var source : actual.actualSourceClosure()) if (source.relativePath().startsWith(PREFIX)) {
            if (source.role() != SourceRole.SDK_SOURCE) throw new IOException("Derived production source cannot be relabeled as support or test");
            String relative = source.relativePath().substring(PREFIX.length());
            Path expected = absolute(actual.sdkRoot()).resolve(relative).normalize();
            if (!absolute(source.actual().path()).equals(expected)) throw new IOException("Derived source inventory escaped its SDK root");
            SharedSourceFiles.plainAncestors(expected); source.actual().verify();
            byte[] raw = Files.readAllBytes(expected); var prior = old.get(relative);
            Row row = new Row(relative, new Digest(source.actual().bytes(), source.actual().sha256()), blob(raw), prior == null ? "100644" : prior.gitMode());
            if (current.put(relative, row) != null) throw new IOException("Repeated SDK inventory leaf");
        }
        if (!current.keySet().containsAll(old.keySet())) throw new IOException("Derived consumer may not omit a parent SDK leaf");
        var rows = current.values().stream().sorted(java.util.Comparator.comparing(Row::relativePath)).toList();
        var deltas = new ArrayList<Delta>();
        for (Row row : rows) {
            var prior = old.get(row.relativePath()); Digest before = prior == null ? null : prior.content();
            if (!row.content().equals(before)) deltas.add(new Delta(row.relativePath(), before, row.content()));
        }
        Row nativeDriver = current.get(NATIVE_DRIVER); var originalNative = old.get(NATIVE_DRIVER);
        if (nativeDriver == null || originalNative == null) throw new IOException("Original and actual native driver source pins required");
        NativeDriverIntent measured = new NativeDriverIntent(originalNative.content(), nativeDriver.content());
        if (purpose == SourcePurpose.PARENT_NATIVE_UNCHANGED && !measured.parentContent().equals(measured.selectedContent()))
            throw new IOException("This source branch preserves the original native driver source; software-only deltas need their explicit purpose and exact intent");
        if ((purpose == SourcePurpose.FULL_SOFTWARE && intent == null) || (intent != null && !intent.equals(measured)))
            throw new IOException("Explicit software native before/selected digest differs from real parent or current inventory");
        return new Lineage(SCHEMA, actual.machineId(), Instant.now().toString(), parentRef, parent.anchorRef(), actualRef, actual.sdkRoot(), purpose, measured, rows, deltas, false);
    }

    static void verify(FileRef lineageRef, Actual actual, FileRef actualRef, FileRef parentRef) throws IOException {
        Lineage declared = read(lineageRef); Lineage measured = derive(actual, actualRef, parentRef, declared.sourcePurpose(), declared.nativeDriverIntent());
        if (!declared.machineId().equals(measured.machineId()) || !declared.parentFreezeRef().equals(measured.parentFreezeRef())
                || !declared.parentAnchorRef().equals(measured.parentAnchorRef()) || !declared.assemblyActualRef().equals(measured.assemblyActualRef())
                || !declared.sdkRoot().equals(measured.sdkRoot()) || declared.sourcePurpose() != measured.sourcePurpose() || !declared.nativeDriverIntent().equals(measured.nativeDriverIntent()) || !declared.currentInventory().equals(measured.currentInventory()) || !declared.deltas().equals(measured.deltas()))
            throw new IOException("Derived SDK parent, exact deltas or complete current inventory changed");
        lineageRef.verify(); actualRef.verify(); parentRef.verify();
    }
    public static Verified verify(FileRef lineageRef) throws IOException {
        Lineage declared = read(lineageRef); Actual actual = SdkSourceAssembly.readActual(declared.assemblyActualRef());
        verify(lineageRef, actual, declared.assemblyActualRef(), declared.parentFreezeRef());
        Parent parent = parent(declared.parentFreezeRef(), declared.machineId());
        FileRef nativeDriver = actual.actualSourceClosure().stream().filter(source -> source.relativePath().equals(PREFIX + NATIVE_DRIVER)).findFirst().orElseThrow().actual();
        return new Verified(VERIFIED_SCHEMA, declared.machineId(), declared.sdkRoot(), lineageRef, declared.parentFreezeRef(), declared.parentAnchorRef(),
                requiredText(parent.json(), "business_source_commit"), declared.assemblyActualRef(), nativeDriver, declared.sourcePurpose(), declared.nativeDriverIntent(), declared.currentInventory().size(), declared.deltas().size(), false, false);
    }
    public static Lineage read(FileRef ref) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX_METADATA) throw new IOException("Bounded derived SDK lineage required");
        ref.verify(); Lineage result = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), Lineage.class); ref.verify(); return result;
    }
    private static Parent parent(FileRef ref, String machine) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX_METADATA) throw new IOException("Bounded original Source32 inventory required");
        ref.verify(); JsonNode value = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(ref.path())));
        if (!"root.ck3.final-sdk-freeze/v1".equals(requiredText(value, "schema")) || !"FINAL_SOURCE_FROZEN".equals(requiredText(value, "status"))
                || !machine.equals(requiredText(value, "machine_id"))) throw new IOException("Real same-machine original Source32 parent required");
        FileRef anchorRef = ControlBuild.strictMapper().treeToValue(value.required("source32_canonical_anchor"), FileRef.class); anchorRef.verify();
        JsonNode anchor = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(anchorRef.path())));
        if (!"xar.source32.canonical-git-anchor/v1".equals(requiredText(anchor, "schema")) || !machine.equals(requiredText(anchor, "machine_id"))
                || !requiredText(value, "business_source_commit").equals(requiredText(anchor, "commit"))) throw new IOException("Original parent Source32 canonical anchor differs");
        List<SdkSourceAssembly.FrozenSourceRow> rows = SdkSourceAssembly.frozenRows(value); ref.verify(); anchorRef.verify(); return new Parent(value, anchorRef, rows);
    }
    private static String requiredText(JsonNode value, String field) throws IOException {
        JsonNode item = value.get(field); if (item == null || !item.isTextual() || item.textValue().isBlank()) throw new IOException("Required exact text: " + field); return item.textValue();
    }
    private static void names(List<String> names) {
        var unique = new java.util.HashSet<String>(); for (String name : names) if (!unique.add(name.toLowerCase(Locale.ROOT))) throw new IllegalArgumentException("Duplicate or case-alias derived source");
    }
    private static Path absolute(String path) { Path value = Path.of(path); if (!value.isAbsolute()) throw new IllegalArgumentException("Absolute exact SDK path required"); return value.toAbsolutePath().normalize(); }
    private static String blob(byte[] raw) {
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-1"); sha.update(("blob " + raw.length + "\0").getBytes(StandardCharsets.US_ASCII)); sha.update(raw); return HexFormat.of().formatHex(sha.digest());
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
