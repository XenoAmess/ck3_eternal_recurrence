package org.xar.ck3.control.nativebridge.capabilities.finance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanCodec;
import org.xar.ck3.control.wave2.finance.rawcash.ConstructionRefundSource;

/**
 * Controlled software response -> actual transport/read coordinator/Root guards/immutable archive ->
 * sole refund decoder and recorded assessment. No Game or native-business qualification.
 * The separate mandatory C++ thirteen-case golden route remains unchanged and is not synthesized here.
 */
final class NativeFinanceRefundArchiveTest {
    @TempDir Path root;
    private static final BigInteger EPOCH = new BigInteger("18446744073709551614");

    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<NativeFinanceReads> owner) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(HolyLoanCodec.SHA256.toLowerCase(java.util.Locale.ROOT),
                "controlled-refund-archive-12004", source -> {
                    var actual = new NativeFinanceReads(source);
                    assertTrue(owner.compareAndSet(null, actual));
                    return List.of(actual.cancelQuote());
                }, request -> {
                    ObjectNode parameters = StrictJson.object(StrictJson.parse(request.additionalFields().bytes()),
                            Set.of("province_id", "capture_epoch"));
                    ObjectNode copied = softwareNativeSource(StrictJson.text(parameters.get("capture_epoch")),
                            (int) StrictJson.integer(parameters.get("province_id"), 1, Integer.MAX_VALUE));
                    ObjectNode result = StrictJson.object().put("step", ConstructionRefundSource.OPERATION)
                            .put("accepted", true).put("status", "source_available").put("query_sequence", "1")
                            .put("snapshot_revision", "1").put("backend_id", NativeFinanceReads.BACKEND);
                    result.set("construction_refund_source_v1", copied);
                    return new RawJson(StrictJson.canonical(result));
                }, Optional.of(HolyLoanCodec.VERSION), Set.of());
    }

    private static PlanningReadResult.Known<ConstructionRefundSource.Result> read(
            ActionWriterIntegrationFixture fixture, NativeFinanceReads owner, BigInteger epoch) throws Exception {
        if (fixture.scenarioReadWrites() > 0) {
            // Consume the existing software packet producer again between independent reads; do not rewrite frame time.
            var transport = fixture.physicalInputs().transport();
            var previous = transport.latestObservedSnapshot().orElseThrow().observedAt();
            for (int attempt = 0; attempt < 2 && !transport.latestObservedSnapshot().orElseThrow().observedAt().isAfter(previous); attempt++)
                assertInstanceOf(org.xar.ck3.control.application.action.NativeSnapshotWaitPort.Received.class,
                        transport.waitForSnapshot(java.time.Instant.now().plusSeconds(5), java.time.Instant.now().plusSeconds(120)));
            assertTrue(transport.latestObservedSnapshot().orElseThrow().observedAt().isAfter(previous),
                    "the actual software receiver must accept a new packet occurrence");
        }
        // Real file-backed archive work on the data volume can exceed the fixture's generic 20-second helper.
        var before = assertInstanceOf(org.xar.ck3.control.application.session.SessionPorts.Ready.class,
                fixture.collector.observe(fixture.observationIdentity(), java.time.Instant.now().plusSeconds(120))).request();
        return fixture.writer.locked(same -> {
            var request = new PlanningReadRequest(before.before(), before.source(), before.sessionId(),
                    owner.cancelQuote().operation(), new NativeFinanceReads.CancelQuoteRequest(2, epoch).arguments(),
                    before.deadline());
            PlanningReadResult<ConstructionRefundSource.Result> result = fixture.reads.read(same, owner.cancelQuote(), request);
            if (result instanceof PlanningReadResult.Known<ConstructionRefundSource.Result> known) return known;
            fail("actual controlled central refund read unavailable: " + result);
            throw new AssertionError("unreachable");
        });
    }

    @Test void actualCentralReadOriginalArchiveAndAssessmentRoundTripWithoutFundingOrLedgerWrites() throws Exception {
        var owner = new AtomicReference<NativeFinanceReads>();
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("roundtrip"), false, scenario(owner), List.of(), java.time.Duration.ofSeconds(60))) {
            var known = read(fixture, owner.get(), EPOCH);
            byte[] ledger = fixture.ledgerBytes();
            int queries = fixture.scenarioReadWrites();
            fixture.writer.locked(same -> {
                var archived = fixture.archive.withSession(same);
                var bound = owner.get().bindCurrentRefund(archived, known);
                assertEquals(known.originalReceipt(), bound.originalRead());
                assertEquals(known.receipt(), archived.loadRead(bound.originalRead()));
                assertEquals(bound.originalRead(), archived.readReferenceOf(known.receipt()));
                var assessment = bound.refundAssessment();
                assertEquals(73, assessment.receiver().characterId());
                assertEquals(91, assessment.recordedBuilderCharacterId().orElseThrow());
                assertEquals(15000000, assessment.storedInputs().getFirst().storedRaw());
                assertTrue(assessment.refundQuoteRaw().isEmpty());
                assertFalse(assessment.completeNetRefundQuote());
                assertFalse(assessment.receivedFundsVerified());
                assertFalse(assessment.submissionQualified());
                assertEquals(0, assessment.fundingCreditRaw());
                ExactRef record = archived.preserveMaterial(new RawJson(bound.toJson()));
                byte[] original = archived.loadMaterial(record).bytes();
                assertArrayEquals(bound.toJson(), owner.get().decodeCurrentRefundRecord(original, archived, known).toJson());
                // Reopen the actual immutable store through a fresh archive object under this same writer.
                // The original current Known is still required; this does not grant cold/live read authority.
                try {
                    var reopened = new NativeOutcomeArchive(fixture.archive.artifactStore(), fixture.writer).withSession(same);
                    assertArrayEquals(bound.toJson(), owner.get().decodeCurrentRefundRecord(
                            reopened.loadMaterial(record).bytes(), reopened, known).toJson());
                } catch (java.io.IOException failure) {
                    throw new java.io.UncheckedIOException(failure);
                }
                return null;
            });
            assertEquals(queries, fixture.scenarioReadWrites());
            assertEquals(0, fixture.nativeActionWrites());
            assertArrayEquals(ledger, fixture.ledgerBytes());
        }
    }

    @Test void foreignLocatorsCrossedCurrentCopiesAndTamperedRecordsRefuseWithoutRepair() throws Exception {
        var owner = new AtomicReference<NativeFinanceReads>();
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("integrity"), false, scenario(owner), List.of(), java.time.Duration.ofSeconds(60))) {
            var first = read(fixture, owner.get(), EPOCH);
            var second = read(fixture, owner.get(), EPOCH.subtract(BigInteger.ONE));
            byte[] ledger = fixture.ledgerBytes();
            int queries = fixture.scenarioReadWrites();
            fixture.writer.locked(same -> {
                var archived = fixture.archive.withSession(same);
                var bound = owner.get().bindCurrentRefund(archived, first);
                var crossed = new PlanningReadResult.Known<>(second.value(), first.receipt(), first.originalReceipt());
                assertThrows(IllegalArgumentException.class, () -> owner.get().bindCurrentRefund(archived, crossed));
                try {
                    Path copy = fixture.root.resolve("foreign-read-metadata.json");
                    Files.copy(Path.of(first.originalReceipt().path()), copy);
                    var alias = new ExactRef(copy.toAbsolutePath().toString(),
                            first.originalReceipt().bytes(), first.originalReceipt().sha256());
                    var foreign = new PlanningReadResult.Known<>(first.value(), first.receipt(), alias);
                    assertThrows(RuntimeException.class, () -> owner.get().bindCurrentRefund(archived, foreign));
                    ObjectNode changedLocator = (ObjectNode) StrictJson.parse(bound.toJson());
                    changedLocator.set("original_read", alias.toJson());
                    assertThrows(IllegalArgumentException.class, () -> owner.get().decodeCurrentRefundRecord(
                            StrictJson.canonical(changedLocator), archived, first));
                    for (String field : Set.of("schema", "original_read", "refund_assessment")) {
                        ObjectNode missing = (ObjectNode) StrictJson.parse(bound.toJson()); missing.remove(field);
                        assertThrows(IllegalArgumentException.class, () -> owner.get().decodeCurrentRefundRecord(
                                StrictJson.canonical(missing), archived, first));
                    }
                    for (JsonNode wrongRef : List.of(StrictJson.object(), StrictJson.parse("true".getBytes(java.nio.charset.StandardCharsets.UTF_8)))) {
                        ObjectNode malformed = (ObjectNode) StrictJson.parse(bound.toJson()); malformed.set("original_read", wrongRef);
                        assertThrows(IllegalArgumentException.class, () -> owner.get().decodeCurrentRefundRecord(
                                StrictJson.canonical(malformed), archived, first));
                    }
                    ObjectNode funds = (ObjectNode) StrictJson.parse(bound.toJson());
                    ((ObjectNode) funds.get("refund_assessment")).put("received_funds_verified", true).put("funding_credit_raw", 15000000);
                    assertThrows(IllegalArgumentException.class, () -> owner.get().decodeCurrentRefundRecord(
                            StrictJson.canonical(funds), archived, first));
                    ObjectNode wrongBuilder = (ObjectNode) StrictJson.parse(bound.toJson());
                    ((ObjectNode) wrongBuilder.get("refund_assessment").get("copied_receiver")).put("character_id", 91);
                    assertThrows(IllegalArgumentException.class, () -> owner.get().decodeCurrentRefundRecord(
                            StrictJson.canonical(wrongBuilder), archived, first));
                    // Corrupt the exact published original read metadata; lookup must not republish/repair it.
                    byte[] damaged = "{}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
                    Files.write(Path.of(first.originalReceipt().path()), damaged);
                    assertThrows(RuntimeException.class, () -> owner.get().bindCurrentRefund(archived, first));
                    assertArrayEquals(damaged, Files.readAllBytes(Path.of(first.originalReceipt().path())));
                } catch (java.io.IOException failure) {
                    throw new java.io.UncheckedIOException(failure);
                }
                return null;
            });
            assertEquals(queries, fixture.scenarioReadWrites());
            assertEquals(0, fixture.nativeActionWrites());
            assertArrayEquals(ledger, fixture.ledgerBytes());
        }
    }

    /** Explicit software source matching the fixture's original raw snapshot actor73/shared initial date/revision1.
     * These values do not replace or alter any C++ golden, Game source or current observation. */
    private static ObjectNode softwareNativeSource(String epoch, int province) {
        ObjectNode node = StrictJson.object().put("schema", ConstructionRefundSource.NATIVE_SCHEMA)
                .put("game_version", HolyLoanCodec.VERSION).put("executable_sha256", HolyLoanCodec.SHA256)
                .put("read_only", true).put("scope", "copied_province_construction_source")
                .put("available", true).putNull("unavailable_reason").put("native_revision", "1")
                .put("capture_epoch", epoch).put("date_raw", ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("actor_character_id", 73)
                .put("province_id", province).put("copied_cancel_gate_allows", true);
        ObjectNode active = node.putObject("active_record");
        active.put("record_pointer", "9007199254750752").put("definition_pointer", "9007199254872064")
                .put("slot_index", 3).put("start_word", epoch).put("recorded_builder_character_id", 91);
        var vector = active.putArray("recorded_cost_raw_native"); vector.add(15000000);
        for (int index = 1; index < 9; ++index) vector.add(0);
        vector.add(Long.MIN_VALUE);
        node.putObject("receiver").put("character_id", 73).put("component_pointer", "9007199254806528")
                .put("current_gold_raw", 8300000);
        node.put("final_action_gate_observed", false).put("submission_qualified", false)
                .put("received_funds_verified", false).put("funding_credit_raw", 0);
        return node;
    }
}

