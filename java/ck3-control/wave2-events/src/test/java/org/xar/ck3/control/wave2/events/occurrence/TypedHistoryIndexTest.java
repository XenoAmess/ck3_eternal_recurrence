package org.xar.ck3.control.wave2.events.occurrence;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.observation.ObservationReuse;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Tests the actual shared index and owner, including unrelated history rows. */
final class TypedHistoryIndexTest {
    private record Source(String key) { }
    private record Frame(int revision) { }
    private record Payload(int value) { }

    @Test void allOriginalProducerCasesReachTheSharedPreparedIndexAndSerialization() throws IOException {
        JsonNode golden;
        try (InputStream stream = getClass().getResourceAsStream("/occurrence/event-occurrence-golden-v1.json")) {
            if (stream == null) { throw new IOException("actual event producer corpus required; never skip"); }
            golden = StrictJson.parse(stream.readAllBytes(), 1_048_576);
        }
        int cases = 0;
        for (JsonNode row : golden.path("cases")) {
            byte[] wire = new ObjectMapper().writeValueAsBytes(row.get("request"));
            EventOccurrence.Request request = EventOccurrenceCodec.decode(wire);
            EventOccurrence.PreparedHistory prepared = EventOccurrence.prepare(request.commands());
            assertEquals(request.commands(), prepared.retainedCommands());
            assertEquals(row.get("expected"), StrictJson.parse(EventOccurrenceCodec.encode(
                    prepared.count(request.eventDefinitionKey(), request.playedCharacterId())), 1_048_576));
            assertEquals(request, EventOccurrenceCodec.decodeRetained(RetainedJson.object(RetainedJson.parse(wire))));
            cases++;
        }
        assertEquals(28, cases);
        List<EventOccurrence.HistoryItem> rows = new ArrayList<>(Collections.nCopies(300_000, new EventOccurrence.IgnoredItem()));
        rows.add(new EventOccurrence.CommandRow("select-event-option-1", false, null));
        EventOccurrence.PreparedHistory invalid = EventOccurrence.prepare(Optional.of(rows));
        assertEquals(300_001, invalid.retainedCommands().orElseThrow().size());
        assertEquals(EventOccurrence.Reason.UNVERIFIED_HISTORICAL_EVENT_SELECTION,
                invalid.count("unrelated.event", BigInteger.ONE).reason());
    }

    @Test void foreignOwnerAndUnknownOutcomeCannotReuseTheRetainedDocument() throws IOException {
        JsonNode golden;
        try (InputStream stream = getClass().getResourceAsStream("/occurrence/event-occurrence-golden-v1.json")) {
            if (stream == null) { throw new IOException("actual event producer corpus required; never skip"); }
            golden = StrictJson.parse(stream.readAllBytes(), 1_048_576);
        }
        RetainedJson.ObjectValue document = RetainedJson.object(RetainedJson.parse(new ObjectMapper()
                .writeValueAsBytes(golden.path("cases").get(3).get("request"))));
        ObservationReuse<Source, Frame, Payload> owner = new ObservationReuse<>("typed-index-test", 2);
        ObservationReuse.WriterVersion version = new ObservationReuse.WriterVersion("typed-index-test", BigInteger.ONE);
        ObservationReuse.Scope<Source, Frame> scope = new ObservationReuse.Scope<>(new Source("actual-corpus"), new Frame(1), version);
        ObservationReuse.Token<Source, Frame> token = owner.bindFresh(scope);
        EventHistoryReadModel<Source, Frame> index = EventHistoryReadModel.bind(owner, token, document);
        assertSame(document, index.retainedDocument());
        ObservationReuse<Source, Frame, Payload> foreign = new ObservationReuse<>("typed-index-test", 2);
        assertThrows(IllegalStateException.class, () -> EventHistoryReadModel.bind(owner, foreign.bindFresh(scope), document));
        owner.unknownOutcome(version);
        assertThrows(IllegalStateException.class, index::retainedDocument);
        assertThrows(IllegalStateException.class, index::retainedCommands);
        assertThrows(IllegalStateException.class, () -> index.count("unrelated.event", BigInteger.ONE));
    }
}
