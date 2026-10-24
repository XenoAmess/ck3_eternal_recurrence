package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;
import static org.xar.ck3.control.build.CompleteSourceGraphMaterializer.*;

/** Independent reread of every original, destination, ordinary source set and canonical Maven consumer. */
public final class CompleteSourceGraphAudit {
    public enum Verification { COMPLETE_PLAN_ORIGINS_AND_MATERIALIZED_TREE }
    public record NativeSnapshot(String schema, String machineId, String observedAtUtc,
            List<Witness> baseline, List<Witness> materialized) {
        public NativeSnapshot {
            if (!"xar.complete-source-independent-native-snapshot/v1".equals(schema)
                    || machineId == null || machineId.isBlank()) throw new IllegalArgumentException("native snapshot required");
            Instant.parse(observedAtUtc); baseline = List.copyOf(baseline); materialized = List.copyOf(materialized);
            if (baseline.isEmpty() || materialized.isEmpty()) throw new IllegalArgumentException("full source snapshots required");
        }
    }
    public record Manifest(String schema, String machineId, String observedAtUtc, Verification verification,
            Qualification qualification, CompleteSourceGraph.Profile profile, String sourceRoot,
            int baselineFiles, int childModules, int reactorProjects, NativeSize size,
            FileRef planRef, FileRef producerActualRef, FileRef producerCardRef, FileRef auditCardRef,
            FileRef inventoryRef, FileRef copyProofRef, FileRef independentNativeSnapshotRef,
            FileRef qualifiedToolsRef, FileRef materializerSourceRef, FileRef graphContractSourceRef,
            List<CompleteSourceGraph.ComponentSelection> selections, Check completeOrdinaryAndCanonicalSet,
            Check allOriginalNativePostcheck, Check allMaterializedNativePostcheck) {
        public Manifest {
            if (!"xar.complete-source-independent-manifest/v1".equals(schema)
                    || machineId == null || machineId.isBlank()
                    || verification != Verification.COMPLETE_PLAN_ORIGINS_AND_MATERIALIZED_TREE
                    || qualification != Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME
                    || profile == null || !profile.completeG2()
                    || baselineFiles <= 0 || childModules != profile.childModules() || reactorProjects != profile.reactorProjects()
                    || completeOrdinaryAndCanonicalSet != Check.MATCH || allOriginalNativePostcheck != Check.MATCH
                    || allMaterializedNativePostcheck != Check.MATCH) {
                throw new IllegalArgumentException("full independent source-only evidence required");
            }
            Instant.parse(observedAtUtc); absolute(sourceRoot); Objects.requireNonNull(size); requireSize(size, profile);
            for (FileRef ref : List.of(planRef, producerActualRef, producerCardRef, auditCardRef, inventoryRef, copyProofRef,
                    independentNativeSnapshotRef, qualifiedToolsRef, materializerSourceRef, graphContractSourceRef)) Objects.requireNonNull(ref);
            selections = List.copyOf(selections);
            Set<CompleteSourceGraph.Component> components = new HashSet<>();
            for (CompleteSourceGraph.ComponentSelection selection : selections) {
                if (!components.add(selection.component())) throw new IllegalArgumentException("duplicate component");
            }
            if (!components.equals(Set.of(CompleteSourceGraph.Component.values()))) throw new IllegalArgumentException("all final components required");
        }
    }
    public record AuditReceipt(String schema, String machineId, String observedAtUtc,
            Qualification qualification, FileRef producerActualRef, FileRef auditCardRef, FileRef manifestRef,
            int negativeCases, Check manifestRoundtrip, Check nativeSnapshotRoundtrip) {
        public AuditReceipt {
            if (!"xar.complete-source-independent-audit-actual/v1".equals(schema)
                    || machineId == null || machineId.isBlank() || negativeCases <= 0
                    || qualification != Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME
                    || manifestRoundtrip != Check.MATCH || nativeSnapshotRoundtrip != Check.MATCH) {
                throw new IllegalArgumentException("actual source audit result required");
            }
            Instant.parse(observedAtUtc);
            for (FileRef ref : List.of(producerActualRef, auditCardRef, manifestRef)) Objects.requireNonNull(ref);
        }
    }
    private CompleteSourceGraphAudit() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("fresh-independent-audit-card.json");
        FileRef cardRef = FileRef.measure(Path.of(args[0]).toRealPath());
        Card card = read(cardRef, Card.class);
        CompleteSourceGraph.Plan plan = CompleteSourceGraph.readPlan(card.planRef());
        AuditReceipt receipt = audit(plan, card, cardRef);
        System.out.println("COMPLETE_SOURCE_AUDIT_PASS negatives=" + receipt.negativeCases()
                + " manifest=" + receipt.manifestRef().path());
    }
    public static AuditReceipt audit(CompleteSourceGraph.Plan plan, Card card, FileRef cardRef) throws IOException {
        admit(plan, card.planRef(), card, cardRef, Operation.INDEPENDENT_AUDIT);
        FileRef actualRef = Objects.requireNonNull(card.producerActualRef());
        Receipt producer = read(actualRef, Receipt.class);
        if (!sameRef(producer.planRef(), card.planRef()) || !absolute(producer.sourceRoot()).equals(absolute(card.sourceRoot()))
                || !producer.machineId().equals(card.machineId()) || producer.profile() != plan.profile()) {
            throw new IOException("exact producer/plan/profile/source/machine required");
        }
        Card originalCard = read(producer.cardRef(), Card.class);
        if (originalCard.operation() != Operation.MATERIALIZE || !sameRef(originalCard.planRef(), card.planRef())
                || !absolute(originalCard.sourceRoot()).equals(absolute(card.sourceRoot()))) {
            throw new IOException("historical exact producer card provenance differs");
        }
        requireProfileBudget(plan.profile(), originalCard.maxSourceNativeBytes());
        // Original card is immutable provenance. Only the new independent card admits this run.
        for (FileRef ref : List.of(originalCard.sourceStandingRef(), originalCard.rootAllocationRef(),
                producer.materializerSourceRef(), producer.graphContractSourceRef(), producer.qualifiedToolsRef())) ref.verify();
        CompleteSourceGraph.SelectionProof selection = CompleteSourceGraph.resolve(plan);
        List<FileRef> baseline = CompleteSourceGraph.baselineFiles(plan);
        Path root = absolute(card.sourceRoot()), metadata = absolute(card.metadataRoot());
        independentRoots(plan, selection, root, metadata); fresh(metadata);
        if (overlap(metadata, absolute(originalCard.metadataRoot()))) throw new IOException("independent audit metadata must be separate");
        List<FileRef> inventory = readGzip(producer.inventoryRef(), new TypeReference<List<FileRef>>() { });
        NativeProof proof = readGzip(producer.copyProofRef(), new TypeReference<NativeProof>() { }, plan.profile().copyProofMaxBytes());
        if (!proof.machineId().equals(card.machineId()) || producer.baselineFiles() != baseline.size()
                || proof.baselineBefore().size() != baseline.size() || inventory.size() != selection.files().size()
                || proof.copies().size() != selection.files().size()) throw new IOException("all original and final proof rows required");
        List<Witness> oldCurrent = observe(baseline), current = observe(inventory);
        if (!oldCurrent.equals(proof.baselineBefore()) || !oldCurrent.equals(proof.baselineAfter())) {
            throw new IOException("historical/all current baseline native witnesses differ");
        }
        Map<String, CompleteSourceGraph.ResolvedFile> selected = new TreeMap<>();
        for (CompleteSourceGraph.ResolvedFile row : selection.files()) selected.put(row.targetRelative(), row);
        Map<Path, Witness> actual = new TreeMap<>(); Set<String> identities = new HashSet<>();
        for (Witness file : current) {
            if (!identities.add(file.nativeFile().identityKey()) || file.nativeFile().linkCount() != 1) {
                throw new IOException("materialized full set aliases or has a nonprivate link");
            }
            if (actual.putIfAbsent(absolute(file.source().path()), file) != null) throw new IOException("duplicate final inventory source");
        }
        Set<String> names = new HashSet<>();
        for (CopyRow row : proof.copies()) {
            relation(row);
            CompleteSourceGraph.ResolvedFile expected = selected.get(row.targetRelative());
            Witness destination = actual.get(target(root, row.targetRelative()));
            if (!names.add(row.targetRelative()) || expected == null || destination == null
                    || !sameRef(expected.sourceRef(), row.originalBefore().source())
                    || !row.destination().equals(destination)) throw new IOException("copy proof is not the exact resolved target/source relation");
            SharedSourceFiles.assertUnchanged(row.originalBefore()); SharedSourceFiles.assertUnchanged(row.originalAfter());
            if (identities.contains(row.originalBefore().nativeFile().identityKey())) throw new IOException("destination aliases a selected original");
        }
        if (!names.equals(selected.keySet())) throw new IOException("copy proof target set incomplete");
        NativeSize size = measure(root, inventory);
        if (!size.equals(producer.size()) || size.logicalBytes() != selection.logicalBytes()) throw new IOException("actual full native size differs");
        verifyCanonical(plan, root, inventory);
        for (Witness original : oldCurrent) {
            SharedSourceFiles.assertUnchanged(original);
            if (identities.contains(original.nativeFile().identityKey())) throw new IOException("destination aliases protected baseline");
        }
        for (Witness destination : current) SharedSourceFiles.assertUnchanged(destination);
        guard(card, card.planRef(), cardRef);
        java.nio.file.Files.createDirectory(metadata);
        NativeSnapshot snapshot = new NativeSnapshot("xar.complete-source-independent-native-snapshot/v1",
                card.machineId(), Instant.now().toString(), oldCurrent, current);
        Path snapshotPath = metadata.resolve("INDEPENDENT-NATIVE-SNAPSHOT01.json.gz");
        gzipBounded(snapshotPath, snapshot, metadata, card.maxMetadataNativeBytes());
        FileRef snapshotRef = FileRef.measure(snapshotPath);
        if (!snapshot.equals(readGzip(snapshotRef, new TypeReference<NativeSnapshot>() { }))) throw new IOException("independent native snapshot roundtrip differs");
        Manifest manifest = new Manifest("xar.complete-source-independent-manifest/v1", card.machineId(), Instant.now().toString(),
                Verification.COMPLETE_PLAN_ORIGINS_AND_MATERIALIZED_TREE, Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME,
                plan.profile(), root.toString(), baseline.size(), plan.modules().size(), plan.modules().size() + 1, size,
                card.planRef(), actualRef, producer.cardRef(), cardRef, producer.inventoryRef(), producer.copyProofRef(),
                snapshotRef, card.qualifiedToolsRef(), card.materializerSourceRef(), card.graphContractSourceRef(),
                selection.selections(), Check.MATCH, Check.MATCH, Check.MATCH);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(manifest);
        if (!manifest.equals(ControlBuild.strictMapper().readValue(raw, Manifest.class))) throw new IOException("independent manifest strict roundtrip differs");
        int negatives = negativeCases(raw, proof.copies().getFirst());
        // Revalidate all real sources after the independent serializer and rejection cases.
        for (Witness original : oldCurrent) SharedSourceFiles.assertUnchanged(original);
        for (CopyRow row : proof.copies()) SharedSourceFiles.assertUnchanged(row.originalBefore());
        for (Witness destination : current) SharedSourceFiles.assertUnchanged(destination);
        verifyCanonical(plan, root, inventory);
        producer.inventoryRef().verify(); producer.copyProofRef().verify(); producer.cardRef().verify(); actualRef.verify();
        guard(card, card.planRef(), cardRef);
        Path manifestPath = metadata.resolve("COMPLETE-SOURCE-TYPED-MANIFEST01.json");
        writeFreshBounded(manifestPath, manifest, metadata, card.maxMetadataNativeBytes());
        FileRef manifestRef = FileRef.measure(manifestPath);
        if (!manifest.equals(read(manifestRef, Manifest.class))) throw new IOException("written independent manifest differs");
        AuditReceipt receipt = new AuditReceipt("xar.complete-source-independent-audit-actual/v1", card.machineId(),
                Instant.now().toString(), Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME,
                actualRef, cardRef, manifestRef, negatives, Check.MATCH, Check.MATCH);
        Path receiptPath = metadata.resolve("COMPLETE-SOURCE-AUDIT-ACTUAL01.json");
        writeFreshBounded(receiptPath, receipt, metadata, card.maxMetadataNativeBytes());
        if (!receipt.equals(read(FileRef.measure(receiptPath), AuditReceipt.class))) throw new IOException("written audit actual differs");
        metadataBound(metadata, card.maxMetadataNativeBytes()); return receipt;
    }
    static int negativeCases(byte[] raw, CopyRow original) throws IOException {
        ObjectNode valid = (ObjectNode) ControlBuild.strictMapper().readTree(raw); int count = 0;
        CompleteSourceGraph.Profile profile = CompleteSourceGraph.Profile.valueOf(valid.get("profile").textValue());
        ObjectNode bad = valid.deepCopy(); bad.put("unexpected", true); reject(bad); count++;
        for (String key : List.of("profile", "plan_ref", "inventory_ref", "size", "selections", "qualification")) {
            bad = valid.deepCopy(); bad.remove(key); reject(bad); count++;
        }
        for (String key : List.of("baseline_files", "child_modules", "reactor_projects")) {
            bad = valid.deepCopy(); bad.put(key, true); reject(bad); count++;
            bad = valid.deepCopy(); bad.put(key, valid.get(key).longValue() + 0.0); reject(bad); count++;
        }
        bad = valid.deepCopy(); bad.put("child_modules", profile.childModules() - 1); reject(bad); count++;
        bad = valid.deepCopy(); bad.put("profile", "JAVA29_REPAIR_20261023"); reject(bad); count++;
        bad = valid.deepCopy(); bad.put("qualification", "SOURCE_AND_GAME"); reject(bad); count++;
        bad = valid.deepCopy(); ((ObjectNode) bad.get("size")).put("files", profile.maxFiles() + 1); reject(bad); count++;
        bad = valid.deepCopy(); ((ObjectNode) bad.get("size")).put("logical_bytes", profile.maxLogicalBytes() + 1); reject(bad); count++;
        bad = valid.deepCopy();
        ObjectNode oversized = (ObjectNode) bad.get("size");
        oversized.put("allocated_file_bytes", profile.maxNativeBytes());
        oversized.put("native_accounted_bytes", Math.addExact(profile.maxNativeBytes(), oversized.get("directory_guard_bytes").longValue()));
        reject(bad); count++;
        bad = valid.deepCopy(); ((ObjectNode) bad.get("inventory_ref")).put("bytes", 1.0); reject(bad); count++;
        String text = new String(raw, java.nio.charset.StandardCharsets.UTF_8);
        try { ControlBuild.strictMapper().readValue(text.substring(0, text.length() - 1) + ",\"child_modules\":" + profile.childModules() + "}", Manifest.class); }
        catch (IOException expected) { text = null; count++; }
        if (text != null) throw new IOException("duplicate independent manifest field accepted");
        try { relation(new CopyRow(original.targetRelative(), original.originalBefore(), original.originalAfter(), original.originalBefore())); }
        catch (IOException expected) { return count + 1; }
        throw new IOException("native alias relation accepted");
    }
    private static void reject(ObjectNode value) throws IOException {
        try { ControlBuild.strictMapper().treeToValue(value, Manifest.class); }
        catch (IOException expected) { return; }
        throw new IOException("invalid independent typed source manifest accepted");
    }
}

