package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** A nonempty canonical software action chain, the real archive and actual reducer body.
 * The software packet edge supplies no Managed or Game qualification. */
final class NativeOutcomeArchiveNonemptyFailureTest {
    @TempDir Path root;
    private enum Damage { MISSING, CHANGED }
    private record Replay(ContinuityState predecessor, WriterContracts.Request request,
            ExactRef record, ExactRef receipt, byte[] ledger) {
        private Replay { ledger = ledger.clone(); }
        @Override public byte[] ledger() { return ledger.clone(); }
    }

    private static ActionCommand withArguments(ActionCommand original, OpportunityJson.Obj arguments) {
        return new ActionCommand(original.actionId(), original.origin(), original.source(), original.sessionId(),
                original.operation(), arguments, original.expectation(), original.claims(), original.deadline());
    }

    private static Replay recordedReplay(ActionWriterIntegrationFixture actual, ActionReceipt receipt) throws IOException {
        return actual.writer.locked(same -> {
            var head = same.head();
            assertTrue(head.state().sequence() > 0);
            assertFalse(ContinuityActionJournal.receipts(head.state(), actual.archive).isEmpty());
            ExactRef record = ContinuityActionJournal.recordHead(head.state()).orElseThrow();
            assertEquals(receipt, actual.archive.loadRecord(record).receipt());
            Path event = actual.root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")
                    .resolve(String.format(java.util.Locale.ROOT, "%08d.json", receipt.sequence()));
            byte[] eventBytes = Files.readAllBytes(event);
            JsonNode original = StrictJson.parse(eventBytes, ContinuityJson.DOCUMENT_MAX_BYTES);
            assertEquals(ContinuityActionJournal.KIND, StrictJson.text(original.get("kind")));
            assertEquals(receipt.sequence(), StrictJson.integer(original.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER));
            ContinuityState predecessor = same.requireHistoricalState(receipt.sequence() - 1,
                    StrictJson.text(original.get("previous_sha256")));
            // The exact durable details enter the production pure reducer. This request is
            // read-only replay input; it cannot supply a callback, authority or Native permit.
            var request = new WriterContracts.Request(ContinuityActionJournal.KIND,
                    ContinuityJson.canonical(original.get("details")), List.of(record));
            assertEquals(StrictJson.text(original.get("identity")), request.identity());
            return new Replay(predecessor, request, record, actual.archive.receiptReferenceOf(receipt), actual.ledgerBytes());
        });
    }

    private static ActionContinuityAuthority replayReducer(ActionPorts.OutcomeArchive bound) {
        return new ActionContinuityAuthority("read-only-original-reducer-test", bound,
                (head, command) -> { throw new AssertionError("pure reduction cannot issue a current guard"); },
                (head, receipt) -> { throw new AssertionError("pure reduction cannot issue recorded-evidence qualification"); },
                Clock.systemUTC());
    }

    private void nonemptyFailure(Damage damage) throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve(damage.name()), true)) {
            ActionCommand command = actual.command("retained-unknown-" + damage.name());
            ActionReceipt receipt = actual.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class, receipt.state());
            assertEquals(1, actual.nativeActionWrites());
            Replay replay = recordedReplay(actual, receipt);
            actual.writer.locked(same -> actual.archive.inSession(same, bound -> {
                ContinuityState reduced = replayReducer(bound).reduce(replay.predecessor(), replay.request());
                assertEquals(replay.record(), ContinuityActionJournal.recordHead(reduced).orElseThrow());
                assertEquals(replay.predecessor().sequence(), reduced.sequence(), "the sole writer assigns the event sequence");
                return null;
            }));

            var attempt = ActionTransitions.attempt(receipt.state()).orElseThrow();
            ExactRef dependency = attempt.guard().supportingEvidence().getFirst();
            Path body = Path.of(dependency.path());
            assertTrue(body.toRealPath().startsWith(actual.root.toRealPath()), "only this fixture's owned dependency may be damaged");
            assertTrue(Files.size(body) > 0);
            if (damage == Damage.MISSING) Files.delete(body);
            else Files.writeString(body, "{\"retained_original_changed\":true}", StandardCharsets.UTF_8);
            byte[] changed = damage == Damage.CHANGED ? Files.readAllBytes(body) : new byte[0];
            long filesAfterDamage = fileCount(actual.root);

            assertThrows(UncheckedIOException.class, () -> actual.archive.loadReceipt(replay.receipt()));
            assertThrows(UncheckedIOException.class, () -> actual.archive.loadRecord(replay.record()));
            assertThrows(UncheckedIOException.class, () -> actual.archive.receiptReferenceOf(receipt));
            AtomicBoolean reducerEntered = new AtomicBoolean();
            actual.writer.locked(same -> actual.archive.inSession(same, bound -> {
                reducerEntered.set(true);
                assertThrows(UncheckedIOException.class, () -> replayReducer(bound).reduce(replay.predecessor(), replay.request()));
                assertThrows(UncheckedIOException.class, () -> ContinuityActionJournal.receipts(sameHead(same), bound));
                return null;
            }));
            assertTrue(reducerEntered.get(), "failure must execute the actual reducer body, not just a shape check");
            assertThrows(Exception.class, () -> actual.writer.preview(replay.request()));
            assertThrows(Exception.class, () -> actual.reopenAndReturnExisting(command));
            assertEquals(1, actual.nativeActionWrites(), "UNKNOWN and archive failure cannot replay the Native action");
            assertEquals(filesAfterDamage, fileCount(actual.root), "a failed reader/reducer cannot repair or replace an original");
            assertArrayEquals(replay.ledger(), actual.ledgerBytes());
            if (damage == Damage.MISSING) assertFalse(Files.exists(body));
            else assertArrayEquals(changed, Files.readAllBytes(body));
        }
    }

    private static ContinuityState sameHead(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) {
        try { return same.head().state(); }
        catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    private static long fileCount(Path path) throws IOException {
        try (var entries = Files.walk(path)) { return entries.filter(Files::isRegularFile).count(); }
    }

    @Test void missingDependencyInNonemptyArchiveFailsRealReaderReducerPreviewAndColdContinuation() throws Exception {
        nonemptyFailure(Damage.MISSING);
    }
    @Test void changedDependencyInNonemptyArchiveFailsRealReaderReducerPreviewAndColdContinuation() throws Exception {
        nonemptyFailure(Damage.CHANGED);
    }
    @Test void jsonArrayDomainRetainsNestedSequenceNullEmptyAndMissingAcrossActualUnknownColdChain() throws Exception {
        // JSON arrays are the persistence domain of both Python list and tuple producers.
        // No in-memory tuple/list representation is compared to a persisted JSON object.
        byte[] json = "{\"result\":{\"sequence\":[1,[2,3],null,[],{}],\"empty\":[],\"null\":null}}"
                .getBytes(StandardCharsets.UTF_8);
        OpportunityJson.Obj expected = DriverJson.object(json, ActionCommand.MAX_ARGUMENT_BYTES);
        OpportunityJson.Obj persisted = DriverJson.object(PublicDataJson.encodeTyped(expected).bytes(), ActionCommand.MAX_ARGUMENT_BYTES);
        assertEquals(expected, persisted);
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("json-domain"), true)) {
            ActionCommand command = withArguments(actual.command("json-sequence-original"), expected);
            ActionReceipt original = actual.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class, original.state());
            ExactRef ref = actual.archive.receiptReferenceOf(original);
            ActionReceipt cold = actual.reopenAndReturnExisting(command);
            assertEquals(original, actual.archive.loadReceipt(ref));
            assertEquals(expected, cold.command().arguments());
            assertArrayEquals(PublicDataJson.encodeTyped(expected).bytes(), PublicDataJson.encodeTyped(cold.command().arguments()).bytes());
            assertEquals(1, actual.nativeActionWrites());
            OpportunityJson.Obj changed = DriverJson.object(
                    "{\"result\":{\"sequence\":[1,[2,3],null,[],{}],\"empty\":[],\"null\":null,\"missing\":null}}"
                            .getBytes(StandardCharsets.UTF_8), ActionCommand.MAX_ARGUMENT_BYTES);
            assertThrows(IllegalArgumentException.class, () -> actual.reopenAndReturnExisting(withArguments(command, changed)));
            assertEquals(1, actual.nativeActionWrites());
        }
    }
}
