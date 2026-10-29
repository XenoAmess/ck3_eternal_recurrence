package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Mandatory installed public-pause producer -> actual archive/readers/reducer.
 * A missing actual provider is NOT_RUN_REQUIRED, never a skipped or fabricated success. */
final class NativeOutcomeArchivePublicPauseFailureTest {
    @Test void actualInstalledKnownPauseFailureReopensNonemptyMaterialsAndActualPureReducer() throws Exception {
        var providers = ServiceLoader.load(RootPublicPauseRuntimeTest.InputsProducer.class).stream().toList();
        if (providers.size() != 1)
            throw new IllegalStateException("MISSING_ACTUAL_ROOT_PUBLIC_PAUSE_INPUTS_NOT_RUN: archive-nonempty-failure");
        var input = java.util.Objects.requireNonNull(providers.getFirst().get().open(
                RootPublicPauseRuntimeTest.Scenario.KNOWN_RECOVERY_FAILURE));
        var catalog = input.catalog();
        var context = catalog.context();
        var root = assertInstanceOf(RootApplicationSession.class, context.actions());
        long nativeBefore = input.actualNativePausePacketsWritten().getAsLong();
        var failure = assertThrows(PublicServiceFailure.class, () ->
                RootPublicStepExecution.execute(root, catalog, input.caller(), input.deadline()));
        assertEquals(PublicServiceFailure.Kind.STEP_POSTCONDITION_ERROR, failure.kind());
        ExactRef actualReport = failure.originalCandidate().orElseThrow();
        root.withPublicStandaloneRead(input.deadline(), same -> {
            context.core().requireCurrentForAccess(same, root);
            ActionReceipt original = context.core().actions().withFrozen(same,
                    lease -> lease.find(input.parentActionId()).orElseThrow());
            var settled = assertInstanceOf(ActionState.CompositeSettled.class, original.state());
            var rejected = assertInstanceOf(ActionState.CompositeRejected.class, settled.settlement());
            assertEquals(List.of(actualReport), rejected.evidence());
            var archive = context.archive().withSession(same);
            var report = archive.loadMaterial(actualReport);
            assertEquals(actualReport.bytes(), report.bytes().length);
            assertEquals(actualReport.sha256(), ActionCodec.sha256(report.bytes()));
            ExactRef receipt = archive.receiptReferenceOf(original);
            assertEquals(original, archive.loadReceipt(receipt));
            byte[] encoded = ActionReceiptCodec.encodeReceipt(original, archive);
            assertEquals(ActionReceiptCodec.COMPOSITE_FAILURE_EVIDENCE_SCHEMA,
                    StrictJson.text(StrictJson.parse(encoded).get("schema")));
            assertEquals(original, ActionReceiptCodec.decodeReceipt(encoded, archive));
            context.bindings().actualArchivedVerifier(original.command().operation()).orElseThrow()
                    .verifier().verify(same.head(), original, archive);
            RootPublicPausePlanningAssertions.requireZeroBusiness(catalog.planningDomainCatalog(), same, archive, original);
            // The event and historical predecessor come from this exact writer, not a
            // detached receipt or reconstructed success. No new preview/commit is issued.
            Path snapshot = Path.of(same.persistedHead().path());
            Path event = snapshot.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS")
                    .resolve(String.format(java.util.Locale.ROOT, "%08d.json", original.sequence()));
            if (Files.size(event) > ContinuityJson.DOCUMENT_MAX_BYTES)
                throw new IOException("actual public-pause event exceeds its original canonical bound");
            var eventRow = StrictJson.parse(Files.readAllBytes(event), ContinuityJson.DOCUMENT_MAX_BYTES);
            var previous = same.requireHistoricalState(original.sequence() - 1, StrictJson.text(eventRow.get("previous_sha256")));
            ExactRef record = ExactRef.fromJson(eventRow.get("details").get("receipt_ref"));
            var request = new WriterContracts.Request(ContinuityActionJournal.KIND,
                    ContinuityJson.canonical(eventRow.get("details")), List.of(record));
            assertEquals(StrictJson.text(eventRow.get("identity")), request.identity());
            var reducer = new ActionContinuityAuthority("archived-actual-pause-pure-reducer-test", archive,
                    (head, command) -> { throw new AssertionError("pure reduction cannot acquire a live guard"); },
                    (head, receiptValue) -> { throw new AssertionError("pure reduction cannot issue a new qualification"); }, Clock.systemUTC());
            assertEquals(record, ContinuityActionJournal.recordHead(reducer.reduce(previous, request)).orElseThrow());
            assertFalse(original.visibleGameplay()); assertFalse(original.eligibleAdvance());
            return null;
        });
        long afterFirst = input.actualNativePausePacketsWritten().getAsLong();
        assertTrue(afterFirst - nativeBefore <= 2);
        assertThrows(PublicServiceFailure.class, () ->
                RootPublicStepExecution.execute(root, catalog, input.caller(), input.deadline()));
        assertEquals(afterFirst, input.actualNativePausePacketsWritten().getAsLong(), "retained failure cannot replay a primitive");
    }
}
