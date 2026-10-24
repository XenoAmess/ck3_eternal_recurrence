package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Synthetic content/provenance negatives only; no capture, Python or process is started. */
final class FinanceOriginalGoldenEvidenceTest {
    @TempDir Path directory;

    @Test void readerContentRejectsBooleanZeroAndChangedActualLedgerHash() throws IOException {
        ObjectNode sample = reader();
        assertEquals(1, FinanceOriginalGoldenEvidence.validateSamples(sample,
                FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS));
        sample.put("new_proposal_source_reads", false);
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.validateSamples(sample,
                FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS));
        sample.put("new_proposal_source_reads", 0);
        sample.put("ledger_sha256_after", "b".repeat(64));
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.validateSamples(sample,
                FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS));
    }

    @Test void pendingRouteRequiresEveryOriginalCaseInDisplayCaptureOrder() throws IOException {
        List<String> names = List.of("receipt_applied", "receipt_wrong_gold", "receipt_timeout",
                "receipt_wrong_process", "receipt_revision_changed", "cold_applied",
                "cold_unchanged", "cold_unknown", "cold_timeout", "cold_same_process", "cold_invalid_birth");
        ObjectNode sample = ControlBuild.strictMapper().createObjectNode();
        ArrayNode cases = sample.putArray("cases");
        for (String name : names) cases.addObject().put("name", name);
        assertEquals(11, FinanceOriginalGoldenEvidence.validateSamples(sample,
                FinanceOriginalGoldenEvidence.Leaf.PENDING_ROUTE));
        ((ObjectNode) cases.get(10)).put("name", "cold_unknown");
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.validateSamples(sample,
                FinanceOriginalGoldenEvidence.Leaf.PENDING_ROUTE));
        cases.remove(10);
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.validateSamples(sample,
                FinanceOriginalGoldenEvidence.Leaf.PENDING_ROUTE));
    }

    @Test void emittedOriginalSourcesMustMatchRealPinnedBytesAndExactIntegerLengths() throws IOException {
        Fixture fixture = sources();
        assertEquals(8, FinanceOriginalGoldenEvidence.sources(fixture.golden(), fixture.boundary(),
                FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS, fixture.refs()).size());
        ((ObjectNode) fixture.golden().path("source_refs").get(0)).put("bytes", false);
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.sources(fixture.golden(),
                fixture.boundary(), FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS, fixture.refs()));
        ((ObjectNode) fixture.golden().path("source_refs").get(0)).put("bytes", fixture.refs().getFirst().bytes());
        Files.writeString(Path.of(fixture.refs().getFirst().path()), "changed real source");
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.sources(fixture.golden(),
                fixture.boundary(), FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS, fixture.refs()));
    }

    @Test void emittedSourceCannotEscapeDuplicateOrOmitTheActualRequestBoundary() throws IOException {
        Fixture fixture = sources();
        ObjectNode first = (ObjectNode) fixture.golden().path("source_refs").get(0);
        first.put("path", "../outside.py");
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.sources(fixture.golden(),
                fixture.boundary(), FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS, fixture.refs()));
        first.put("path", "source0.py");
        ((ObjectNode) fixture.golden().path("source_refs").get(1)).put("path", "source0.py");
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.sources(fixture.golden(),
                fixture.boundary(), FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS, fixture.refs()));
        ((ObjectNode) fixture.golden().path("source_refs").get(1)).put("path", "source1.py");
        assertThrows(IOException.class, () -> FinanceOriginalGoldenEvidence.sources(fixture.golden(),
                fixture.boundary(), FinanceOriginalGoldenEvidence.Leaf.PENDING_READERS,
                fixture.refs().subList(1, fixture.refs().size())));
    }

    @Test void preparationCannotRelabelDuplicatedOrMiscountedOriginalSourcesAsAccepted() throws IOException {
        Fixture fixture = sources();
        var source = fixture.boundary();
        var duplicated = new ArrayList<>(fixture.refs());
        duplicated.set(1, duplicated.getFirst());
        assertThrows(IllegalArgumentException.class, () -> boundary(duplicated));
        assertThrows(IllegalArgumentException.class, () -> new FinanceOriginalGoldenEvidence.Boundary(
                source.schema(), source.machineId(), source.observedAtUtc(), "PASS",
                source.originalRepository(), source.frozenJavaSourceModule(), source.originalSourceRefs(),
                source.frozenJavaSourceRefs(), source.interpreterRef(), source.scope(),
                source.originalRefCount(), source.sourceBytes(), source.execution()));
    }

    private ObjectNode reader() {
        ObjectNode result = ControlBuild.strictMapper().createObjectNode();
        result.put("new_proposal_source_reads", 0);
        result.put("ledger_sha256_before", "a".repeat(64));
        result.put("ledger_sha256_after", "a".repeat(64));
        result.putObject("ledger").putObject("pending").put("request_id", "synthetic-content-only");
        result.putObject("feast_budget").put("reason", "faction_gift_pending");
        result.putObject("formal_collector").putObject("plan")
                .put("selected_step", "private-query-faction-gift-receipt-v1");
        return result;
    }

    private Fixture sources() throws IOException {
        List<ControlBuild.FileRef> refs = new ArrayList<>();
        ObjectNode golden = ControlBuild.strictMapper().createObjectNode();
        ArrayNode emitted = golden.putArray("source_refs");
        for (int index = 0; index < 8; index++) {
            Path source = directory.resolve("source" + index + ".py");
            Files.writeString(source, "synthetic_source_" + index);
            ControlBuild.FileRef ref = ControlBuild.FileRef.measure(source.toRealPath());
            refs.add(ref);
            emitted.addObject().put("path", source.getFileName().toString())
                    .put("bytes", ref.bytes()).put("sha256", ref.sha256());
        }
        return new Fixture(List.copyOf(refs), boundary(refs), golden);
    }

    private FinanceOriginalGoldenEvidence.Boundary boundary(List<ControlBuild.FileRef> refs) throws IOException {
        return new FinanceOriginalGoldenEvidence.Boundary("xar.finance-original-source-boundary/v1",
                "synthetic-machine-content-unit-only", Instant.now().toString(), "SOURCE_ONLY_NOT_EXECUTABLE",
                directory.toRealPath().toString(), directory.toRealPath().toString(), refs,
                refs.subList(0, 5), refs.getFirst(), "Synthetic pure content boundary; no capture qualification",
                refs.size(), refs.stream().mapToLong(ControlBuild.FileRef::bytes).sum(), "NOT_RUN");
    }

    private record Fixture(List<ControlBuild.FileRef> refs,
            FinanceOriginalGoldenEvidence.Boundary boundary, ObjectNode golden) { }
}
