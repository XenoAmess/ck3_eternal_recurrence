package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterTransactionCodec;

/** Requires the actual source-owned Root fixture producer; absent inputs fail explicitly and never count as success. */
public final class WriterTransactionFixtureActualTest {
    @Test void actualCommittedFixtureEntryUsesTheOneColdCodecAndRejectsChangedProjectionOrFields() throws Exception {
        var producers = ServiceLoader.load(FixtureCompositeActualTest.InputsProducer.class).stream().toList();
        if (producers.size() != 1) throw new IllegalStateException("MISSING_ACTUAL_ROOT_FIXTURE_COMPOSITE_INPUTS_NOT_RUN: WRITER_ENTRY_CODEC");
        var input = producers.getFirst().get().open(FixtureCompositeActualTest.Scenario.COMPLETE);
        var context = input.catalog().context();
        assertSame(context.writer(), input.menu().writer); assertSame(context.core().actions(), input.menu().coordinator);
        var terminal = input.menu().execute(input.parent());
        var observation = assertInstanceOf(ActionState.FixtureBusinessCompleted.class,
                assertInstanceOf(ActionState.CompositeSettled.class, terminal.state()).settlement()).observation();
        context.writer().locked(same -> {
            byte[] preparedBytes = context.archive().readArtifact(same, observation.entryPrepared(), WriterTransactionCodec.MAXIMUM_BYTES);
            byte[] receiptBytes = context.archive().readArtifact(same, observation.entryReceipt(), WriterTransactionCodec.MAXIMUM_BYTES);
            var prepared = WriterTransactionCodec.decodePrepared(preparedBytes, context.source().machineId());
            var receipt = WriterTransactionCodec.decodeReceipt(receiptBytes, context.source().machineId());
            same.requireCommitted(prepared, receipt);
            assertArrayEquals(preparedBytes, WriterTransactionCodec.encodePrepared(prepared));
            assertArrayEquals(receiptBytes, WriterTransactionCodec.encodeReceipt(receipt));
            assertEquals(WriterContracts.GAMEPLAY_ENTRY_KIND, prepared.request().kind());
            assertTrue(prepared.request().detailsObject().has("fixture"));
            WriterContracts.requireGameplayEntryReduction(prepared.predecessor().state(), prepared.reduced(), prepared.request(), false);
            ObjectNode changed = prepared.reduced().toJson(); changed.put("codec_unrelated_runtime_field", true);
            var changedState = ContinuityState.fromJson(changed, context.source().machineId());
            assertThrows(IllegalArgumentException.class, () -> WriterContracts.requireGameplayEntryReduction(
                    prepared.predecessor().state(), changedState, prepared.request(), false));
            ObjectNode malformed = prepared.request().detailsObject();
            ((ObjectNode)malformed.get("fixture")).put("caller_approved", true);
            var wrongFields = new WriterContracts.Request(prepared.request().kind(), ContinuityJson.canonical(malformed), prepared.request().evidence());
            assertThrows(IllegalArgumentException.class, () -> WriterContracts.gameplayEntryDetails(wrongFields));
            var wrongReceipt = new WriterContracts.Receipt(receipt.disposition(), receipt.head(), "b".repeat(64), receipt.writes(), receipt.recoveredCommittedReceipt());
            assertThrows(IllegalArgumentException.class, () -> same.requireCommitted(prepared, wrongReceipt));
            return null;
        });
        assertFalse(terminal.visibleGameplay()); assertFalse(terminal.eligibleAdvance());
    }
}
