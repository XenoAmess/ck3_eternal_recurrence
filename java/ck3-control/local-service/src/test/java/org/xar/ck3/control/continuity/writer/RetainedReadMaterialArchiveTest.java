package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual software ACK/guards and physical CAS; no Family eligibility or live Native qualification is constructed. */
final class RetainedReadMaterialArchiveTest {
    @TempDir Path temporary;

    @Test void retainedV4MaterialSurvivesANewWriterScopeAndColdDecodeWithoutItsExportPath() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("roundtrip"), false)) {
            fixture.command("retained-material-query");
            var ordinary = fixture.lastNestedRead.get();
            assertEquals(PlanningReadReceipt.ArchiveVersion.CURRENT_V2, ordinary.archiveVersion());
            assertTrue(ordinary.retainedMaterial().isEmpty());
            Path export = temporary.resolve("current-export.json");
            byte[] original = " {\"schema\":\"software-family-relation-export/v1\",\"rows\":[{\"id\":18446744073709551615}],\"optional\":null} \n".getBytes(StandardCharsets.UTF_8);
            Files.write(export, original);
            var material = fixture.archive.preserveMaterial(new RawJson(Files.readAllBytes(export)));
            var attached = attach(ordinary, material);
            var first = new AtomicReference<ContinuityStorePort.Session>();
            ExactRef readRef = fixture.writer.locked(same -> {
                first.set(same);
                return fixture.archive.withSession(same).preserveRead(attached);
            });
            Files.delete(export);
            int nativeReads = fixture.nativeReadWrites();
            byte[] ledger = fixture.ledgerBytes();
            fixture.writer.locked(same -> {
                assertNotSame(first.get(), same);
                var loaded = fixture.archive.withSession(same).loadRead(readRef);
                assertEquals(attached, loaded);
                assertEquals(readRef, fixture.archive.withSession(same).readReferenceOf(loaded));
                assertArrayEquals(original, fixture.archive.withSession(same).loadMaterial(loaded.retainedMaterial().orElseThrow().original()).bytes());
                return null;
            });
            var cold = NativeArchiveDataCodec.retainedFiles().readData(readRef).receipt();
            assertEquals(attached, cold);
            assertEquals(ordinary.request(), cold.request());
            assertEquals(ordinary.original(), cold.original());
            assertEquals(ordinary.before(), cold.before());
            assertEquals(ordinary.after(), cold.after());
            assertTrue(cold.adoption().isEmpty());
            assertEquals(material, cold.retainedMaterial().orElseThrow().original());
            assertArrayEquals(ordinary.original().originalPacket(), cold.original().originalPacket());
            assertEquals(nativeReads, fixture.nativeReadWrites());
            assertEquals(0, fixture.nativeActionWrites());
            assertArrayEquals(ledger, fixture.ledgerBytes());
            var metadata = metadata(readRef);
            assertEquals("xar.planning-read-archive/v4", metadata.path("schema").textValue());
            assertEquals("FAMILY_RELATION_EXPORT", metadata.path("retained_material").path("kind").textValue());
            String output = System.getProperty("xar.material.roundtrip.bundle");
            if (output != null) {
                Path directory = Path.of(output); Files.createDirectories(directory);
                Files.write(directory.resolve("read-ref.json"), StrictJson.canonical(readRef.toJson()));
            }
        }
    }

    @Test void missingRetainedMaterialFailsBothArchiveAndColdReadWithoutAnotherRequest() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("missing"), false)) {
            fixture.command("missing-material-query");
            var material = fixture.archive.preserveMaterial(raw("{\"retained\":true}"));
            var receipt = attach(fixture.lastNestedRead.get(), material);
            var readRef = fixture.archive.preserveRead(receipt);
            int reads = fixture.nativeReadWrites();
            Files.delete(Path.of(material.path()));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadRead(readRef));
            assertThrows(IOException.class, () -> NativeArchiveDataCodec.retainedFiles().readData(readRef));
            assertEquals(reads, fixture.nativeReadWrites());
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void malformedV4AttachmentIsRejectedAndOrdinaryV2KeepsItsClosedShape() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("shape"), false)) {
            fixture.command("shape-material-query");
            var ordinary = fixture.lastNestedRead.get();
            var oldConstructor = new PlanningReadReceipt(ordinary.request(), ordinary.contractId(), ordinary.requestId(),
                    ordinary.before(), ordinary.after(), ordinary.original(), ordinary.adoption(), ordinary.archiveVersion());
            assertEquals(ordinary, oldConstructor);
            var oldRef = fixture.archive.preserveRead(ordinary);
            var v2 = metadata(oldRef);
            assertEquals("xar.planning-read-archive/v2", v2.path("schema").textValue());
            assertFalse(v2.has("retained_material"));
            assertEquals(ordinary, fixture.archive.loadRead(oldRef));
            assertEquals(ordinary, NativeArchiveDataCodec.retainedFiles().readData(oldRef).receipt());
            var material = fixture.archive.preserveMaterial(raw("{\"retained\":true}"));
            var v4 = metadata(fixture.archive.preserveRead(attach(ordinary, material)));
            var wrongKindType = v4.deepCopy(); ((ObjectNode) wrongKindType.get("retained_material")).put("kind", true);
            reject(fixture, wrongKindType);
            var wrongKind = v4.deepCopy(); ((ObjectNode) wrongKind.get("retained_material")).put("kind", "OTHER");
            reject(fixture, wrongKind);
            var wrongRefType = v4.deepCopy(); ((ObjectNode) wrongRefType.get("retained_material")).put("original", false);
            reject(fixture, wrongRefType);
            var missing = v4.deepCopy(); missing.remove("retained_material");
            reject(fixture, missing);
            var extra = v2.deepCopy(); extra.set("retained_material", v4.get("retained_material"));
            reject(fixture, extra);
            assertThrows(IllegalArgumentException.class, () -> new PlanningReadReceipt(ordinary.request(), ordinary.contractId(), ordinary.requestId(),
                    ordinary.before(), ordinary.after(), ordinary.original(), Optional.empty(), PlanningReadReceipt.ArchiveVersion.CURRENT_V2,
                    Optional.of(new PlanningReadReceipt.RetainedMaterial(PlanningReadReceipt.RetainedMaterial.Kind.FAMILY_RELATION_EXPORT, material))));
        }
    }

    private static PlanningReadReceipt attach(PlanningReadReceipt original, ExactRef material) {
        return new PlanningReadReceipt(original.request(), original.contractId(), original.requestId(), original.before(), original.after(),
                original.original(), Optional.empty(), PlanningReadReceipt.ArchiveVersion.RETAINED_MATERIAL_V4,
                Optional.of(new PlanningReadReceipt.RetainedMaterial(PlanningReadReceipt.RetainedMaterial.Kind.FAMILY_RELATION_EXPORT, material)));
    }

    private static ObjectNode metadata(ExactRef original) throws IOException {
        return ObjectNode.class.cast(StrictJson.parse(Files.readAllBytes(Path.of(original.path())), StrictJson.EXPLICIT_MAX_BYTES));
    }

    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }

    private static void reject(ActionWriterIntegrationFixture fixture, ObjectNode changed) {
        var ref = fixture.archive.preserveMaterial(new RawJson(StrictJson.canonical(changed, StrictJson.EXPLICIT_MAX_BYTES)));
        assertThrows(IllegalArgumentException.class, () -> fixture.archive.loadRead(ref));
        assertThrows(IllegalArgumentException.class, () -> NativeArchiveDataCodec.retainedFiles().readData(ref));
    }
}
