package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.*;

/** Source-only producer/accepted-reader subroutines against real files; no service or full Views acceptance. */
final class SdkDerivedSource32Test {
    @TempDir Path temporary;
    private record Fixture(Actual actual, FileRef actualRef, FileRef parentRef, FileRef originalNative, FileRef parentAnchor) { }
    private Fixture fixture() throws IOException {
        Path parent = Files.createDirectory(temporary.resolve("parent"));
        Path parentNative = parent.resolve("xar_autoplayer/bridge/native_driver.py"); Files.createDirectories(parentNative.getParent()); Files.writeString(parentNative, "native source\n");
        Path parentPolicy = parent.resolve("xar_autoplayer/policy.py"); Files.writeString(parentPolicy, "original policy\n");
        var mapper = ControlBuild.strictMapper();
        Path anchorPath = temporary.resolve("anchor.json");
        var anchor = mapper.createObjectNode().put("schema", "xar.source32.canonical-git-anchor/v1").put("machine_id", "fixture-machine").put("commit", "a".repeat(40));
        Files.write(anchorPath, mapper.writeValueAsBytes(anchor)); FileRef anchorRef = FileRef.measure(anchorPath);
        var base = mapper.createObjectNode().put("schema", "root.ck3.final-sdk-freeze/v1").put("status", "FINAL_SOURCE_FROZEN").put("machine_id", "fixture-machine")
                .put("source_root", parent.toString()).put("business_source_commit", "a".repeat(40)).put("source_file_count", 2).put("source_bytes", Files.size(parentNative) + Files.size(parentPolicy));
        base.set("source32_canonical_anchor", mapper.valueToTree(anchorRef)); var rows = base.putArray("files");
        for (Path file : List.of(parentNative, parentPolicy)) {
            FileRef ref = FileRef.measure(file); rows.addObject().put("relative", parent.relativize(file).toString().replace('\\', '/')).put("bytes", ref.bytes()).put("sha256", ref.sha256()).put("git_blob_sha1", "b".repeat(40)).put("git_mode", "100644");
        }
        Path basePath = temporary.resolve("parent-freeze.json"); Files.write(basePath, mapper.writeValueAsBytes(base)); FileRef baseRef = FileRef.measure(basePath);
        Path graph = Files.createDirectory(temporary.resolve("consumer")), sdk = Files.createDirectories(graph.resolve("ck3_autonomous_player/src"));
        Path actualNative = sdk.resolve("xar_autoplayer/bridge/native_driver.py"); Files.createDirectories(actualNative.getParent()); Files.copy(parentNative, actualNative);
        Path actualPolicy = sdk.resolve("xar_autoplayer/policy.py"); Files.writeString(actualPolicy, "derived policy\n");
        var outputs = List.of(new OutputSource("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", SourceRole.SDK_SOURCE, FileRef.measure(actualNative)),
                new OutputSource("ck3_autonomous_player/src/xar_autoplayer/policy.py", SourceRole.SDK_SOURCE, FileRef.measure(actualPolicy)));
        FileRef proof = baseRef;
        var deployment = new DeploymentEvidence("source-fixture-only", proof, ControlBuild.TargetKind.SERVICE_FAST_JAR, graph.toString(), List.of(proof), List.of(proof), proof, false);
        String now = Instant.now().toString();
        Actual actual = new Actual(SdkSourceAssembly.ASSEMBLY_SCHEMA, "fixture-machine", now, now, AssemblyStatus.SOURCE_ASSEMBLED_NOT_IMPORTED, proof,
                graph.toString(), sdk.toString(), temporary.toString(), List.of(".", "ck3_autonomous_player/src"), outputs,
                List.of(new ImportSource(outputs.getFirst().relativePath(), ImportSourceLocation.FRESH_GRAPH, outputs.getFirst().actual())), List.of(), List.of(deployment), List.of(),
                new ProducerReuse("tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py", "tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", "compose_v1", "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", "validate_current_saved_cold_owner_v1"),
                List.of(NextStep.ACTUAL_IMPORT_CLOSURE), "c".repeat(64), proof, 4096, false, false, null);
        Path actualPath = Files.createDirectories(graph.resolve(".assembly")).resolve("ACTUAL.json"); Files.write(actualPath, mapper.writeValueAsBytes(actual));
        return new Fixture(actual, FileRef.measure(actualPath), baseRef, FileRef.measure(parentNative), anchorRef);
    }
    private FileRef lineage(Fixture fixture) throws IOException {
        var value = SdkDerivedSource32.derive(fixture.actual(), fixture.actualRef(), fixture.parentRef()); Path path = temporary.resolve("derived.json");
        Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value)); return FileRef.measure(path);
    }
    @Test void actualDerivedInventoryPreservesParentAndCarriesExactChangedBytes() throws Exception {
        Fixture f = fixture(); FileRef lineage = lineage(f); var value = SdkDerivedSource32.read(lineage);
        assertEquals(SdkDerivedSource32.SCHEMA, value.schema()); assertEquals(f.parentAnchor(), value.parentAnchorRef());
        assertEquals(2, value.currentInventory().size()); assertEquals(1, value.deltas().size());
        assertEquals("xar_autoplayer/policy.py", value.deltas().getFirst().relativePath()); assertNotEquals(value.deltas().getFirst().before(), value.deltas().getFirst().after());
        assertFalse(value.runtimeAdmitted()); SdkDerivedSource32.verify(lineage, f.actual(), f.actualRef(), f.parentRef());
        f.originalNative().verify(); assertEquals("native source\n", Files.readString(Path.of(f.originalNative().path())));
        var mapper = ControlBuild.strictMapper(); assertEquals(value, mapper.readValue(mapper.writeValueAsBytes(value), SdkDerivedSource32.Lineage.class));
    }
    @Test void derivedNativeDriverChangeOrRelabelledProductionLeafIsRejected() throws Exception {
        Fixture f = fixture(); Path nativePath = Path.of(f.actual().actualSourceClosure().getFirst().actual().path()); Files.writeString(nativePath, "changed native source\n");
        var mapper = ControlBuild.strictMapper(); var changed = mapper.valueToTree(f.actual());
        var first = (com.fasterxml.jackson.databind.node.ObjectNode) changed.get("actual_source_closure").get(0);
        first.set("actual", mapper.valueToTree(FileRef.measure(nativePath)));
        Actual changedActual = mapper.treeToValue(changed, Actual.class); Files.write(Path.of(f.actualRef().path()), mapper.writeValueAsBytes(changedActual));
        FileRef changedActualRef = FileRef.measure(Path.of(f.actualRef().path()));
        assertTrue(assertThrows(IOException.class, () -> SdkDerivedSource32.derive(changedActual, changedActualRef, f.parentRef())).getMessage().contains("native driver"));
        first.put("role", "SUPPORT_RESOURCE"); Actual mislabeled = mapper.treeToValue(changed, Actual.class);
        Files.write(Path.of(f.actualRef().path()), mapper.writeValueAsBytes(mislabeled)); FileRef mislabeledRef = FileRef.measure(Path.of(f.actualRef().path()));
        assertTrue(assertThrows(IOException.class, () -> SdkDerivedSource32.derive(mislabeled, mislabeledRef, f.parentRef())).getMessage().contains("relabeled"));
    }
    @Test void wrongDeltaOrMissingInventoryAndSourceTamperingCannotBeAccepted() throws Exception {
        Fixture f = fixture(); FileRef lineage = lineage(f); var mapper = ControlBuild.strictMapper(); var value = mapper.readTree(Files.readAllBytes(Path.of(lineage.path())));
        ((com.fasterxml.jackson.databind.node.ArrayNode) value.get("deltas")).removeAll(); Path bad = temporary.resolve("wrong-delta.json"); Files.write(bad, mapper.writeValueAsBytes(value));
        assertThrows(Exception.class, () -> SdkDerivedSource32.verify(FileRef.measure(bad), f.actual(), f.actualRef(), f.parentRef()));
        var missing = mapper.readTree(Files.readAllBytes(Path.of(lineage.path()))); ((com.fasterxml.jackson.databind.node.ArrayNode) missing.get("current_inventory")).remove(0);
        Path missingPath = temporary.resolve("missing-inventory.json"); Files.write(missingPath, mapper.writeValueAsBytes(missing));
        assertThrows(IOException.class, () -> SdkDerivedSource32.verify(FileRef.measure(missingPath), f.actual(), f.actualRef(), f.parentRef()));
        Files.writeString(Path.of(f.actual().actualSourceClosure().getLast().actual().path()), "tampered policy\n");
        assertThrows(IOException.class, () -> SdkDerivedSource32.verify(lineage, f.actual(), f.actualRef(), f.parentRef()));
    }
    @Test void strictLineageRejectsWrongSchemaNullUnknownAndPrimitiveCoercion() throws Exception {
        Fixture f = fixture(); FileRef lineage = lineage(f); var mapper = ControlBuild.strictMapper(); String raw = Files.readString(Path.of(lineage.path()));
        for (String invalid : List.of(raw.replace(SdkDerivedSource32.SCHEMA, "root.ck3.final-sdk-freeze/v1"), raw.replace("\"runtime_admitted\":false", "\"runtime_admitted\":true"),
                raw.replace("\"parent_anchor_ref\":", "\"unknown\":1,\"parent_anchor_ref\":"), raw.replace("\"bytes\":" + f.parentRef().bytes(), "\"bytes\":true"),
                raw.replace("\"machine_id\":\"fixture-machine\"", "\"machine_id\":null")))
            assertThrows(Exception.class, () -> mapper.readValue(invalid, SdkDerivedSource32.Lineage.class));
    }
    @Test void sourceBoundEmissionWireRejectsCoercionAndUnqualifiedIssuers() throws Exception {
        Fixture f = fixture(); FileRef lineage = lineage(f); var value = SdkDerivedSource32.read(lineage);
        FileRef actualNative = f.actual().actualSourceClosure().getFirst().actual();
        var verified = new SdkDerivedSource32.Verified(SdkDerivedSource32.VERIFIED_SCHEMA, value.machineId(), value.sdkRoot(), lineage,
                value.parentFreezeRef(), value.parentAnchorRef(), "a".repeat(40), value.assemblyActualRef(), actualNative, value.sourcePurpose(), value.nativeDriverIntent(), 2, 1, false, false);
        var emission = new SdkDerivedSource32.VerifiedEmission(SdkDerivedSource32.EMISSION_SCHEMA, value.machineId(), Instant.now().toString(),
                f.parentRef(), f.parentRef(), f.parentRef(), List.of(f.parentRef()), value.currentInventory(), verified);
        var mapper = ControlBuild.strictMapper(); String encoded = mapper.writeValueAsString(emission);
        assertEquals(emission, mapper.readValue(encoded, SdkDerivedSource32.VerifiedEmission.class));
        assertEquals(value.currentInventory(), mapper.readValue(encoded, SdkDerivedSource32.VerifiedEmission.class).currentInventory());
        assertThrows(IllegalArgumentException.class, () -> new SdkDerivedSource32.VerifiedEmission(SdkDerivedSource32.EMISSION_SCHEMA,
                value.machineId(), Instant.now().toString(), f.parentRef(), f.parentRef(), f.parentRef(), List.of(f.parentRef()), List.of(), verified));
        for (String invalid : List.of(encoded.replace("\"current_source_files\":2", "\"current_source_files\":true"),
                encoded.replace("\"producer_source_ref\":", "\"unknown\":1,\"producer_source_ref\":"),
                encoded.replace("\"runtime_admitted\":false", "\"runtime_admitted\":true")))
            assertThrows(Exception.class, () -> mapper.readValue(invalid, SdkDerivedSource32.VerifiedEmission.class));
        Path output = temporary.resolve("issuer-proof.json");
        assertThrows(Exception.class, () -> SdkDerivedSource32.emitVerified(lineage, f.parentRef(), output));
        assertFalse(Files.exists(output));
        Path forged = temporary.resolve("forged-proof.json"); Files.writeString(forged, encoded);
        assertThrows(Exception.class, () -> SdkDerivedSource32.readVerifiedEmission(FileRef.measure(forged)));
    }
    @Test void fullSoftwareNativeDeltaNeedsExactIntentAndCannotAdmitNativeRestore() throws Exception {
        Fixture f = fixture(); var mapper = ControlBuild.strictMapper();
        Path nativePath = Path.of(f.actual().actualSourceClosure().getFirst().actual().path());
        Files.writeString(nativePath, "pure Java delegation source\n"); FileRef selectedNative = FileRef.measure(nativePath);
        var changed = mapper.valueToTree(f.actual());
        ((com.fasterxml.jackson.databind.node.ObjectNode) changed.get("actual_source_closure").get(0)).set("actual", mapper.valueToTree(selectedNative));
        Actual current = mapper.treeToValue(changed, Actual.class); Files.write(Path.of(f.actualRef().path()), mapper.writeValueAsBytes(current));
        FileRef currentRef = FileRef.measure(Path.of(f.actualRef().path()));
        var intent = new SdkDerivedSource32.NativeDriverIntent(new Digest(f.originalNative().bytes(), f.originalNative().sha256()),
                new Digest(selectedNative.bytes(), selectedNative.sha256()));
        assertThrows(IOException.class, () -> SdkDerivedSource32.derive(current, currentRef, f.parentRef()));
        var value = SdkDerivedSource32.derive(current, currentRef, f.parentRef(), SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE, intent);
        assertEquals(intent, value.nativeDriverIntent()); assertEquals(SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE, value.sourcePurpose());
        Path path = temporary.resolve("software-lineage.json"); Files.write(path, mapper.writeValueAsBytes(value)); FileRef ref = FileRef.measure(path);
        SdkDerivedSource32.verify(ref, current, currentRef, f.parentRef());
        assertEquals(value, mapper.readValue(mapper.writeValueAsBytes(value), SdkDerivedSource32.Lineage.class));
        assertThrows(IOException.class, () -> SdkDerivedSource32.derive(current, currentRef, f.parentRef(), SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE, null));
        var wrong = new SdkDerivedSource32.NativeDriverIntent(intent.parentContent(), intent.parentContent());
        assertThrows(IOException.class, () -> SdkDerivedSource32.derive(current, currentRef, f.parentRef(), SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE, wrong));
        assertThrows(IllegalArgumentException.class, () -> new SdkDerivedSource32.Verified(SdkDerivedSource32.VERIFIED_SCHEMA, value.machineId(),
                value.sdkRoot(), ref, f.parentRef(), f.parentAnchor(), "a".repeat(40), currentRef, selectedNative, value.sourcePurpose(), intent, 2, 2, false, true));
        f.originalNative().verify();
    }
}
