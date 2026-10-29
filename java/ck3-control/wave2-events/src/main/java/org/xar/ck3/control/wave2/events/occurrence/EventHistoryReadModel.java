package org.xar.ck3.control.wave2.events.occurrence;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.List;
import org.xar.ck3.control.contracts.observation.ObservationReuse;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/**
 * Read-side attachment for a single complete shared RetainedJson parse. The complete document,
 * all opaque fields and original retained-value identities stay attached to the index.
 * This class never parses, reads a file, observes, creates a writer version, or submits an action.
 */
public final class EventHistoryReadModel<S extends Record, F extends Record> {
    private final ObservationReuse<S,F,?> owner;
    private final ObservationReuse.Token<S,F> token;
    private final RetainedJson.ObjectValue retainedDocument;
    private final EventOccurrence.PreparedHistory history;

    private EventHistoryReadModel(ObservationReuse<S,F,?> owner, ObservationReuse.Token<S,F> token,
            RetainedJson.ObjectValue retainedDocument, EventOccurrence.PreparedHistory history) {
        this.owner = owner; this.token = token; this.retainedDocument = retainedDocument; this.history = history;
    }

    public static <S extends Record,F extends Record> EventHistoryReadModel<S,F> bind(
            ObservationReuse<S,F,?> owner, ObservationReuse.Token<S,F> token, RetainedJson.ObjectValue completeRetainedDocument) {
        Objects.requireNonNull(owner); Objects.requireNonNull(token); Objects.requireNonNull(completeRetainedDocument);
        owner.requireCurrent(token);
        EventOccurrence.Request decodedRequest = EventOccurrenceCodec.decodeRetained(completeRetainedDocument);
        EventOccurrence.PreparedHistory prepared = EventOccurrence.prepare(decodedRequest.commands());
        owner.requireCurrent(token);
        return new EventHistoryReadModel<>(owner, token, completeRetainedDocument, prepared);
    }

    public EventOccurrence.Result count(String eventDefinitionKey, BigInteger actorCharacterId) {
        owner.requireCurrent(token);
        EventOccurrence.Result result = history.count(eventDefinitionKey, actorCharacterId);
        owner.requireCurrent(token);
        return result;
    }

    public RetainedJson.ObjectValue retainedDocument() {
        owner.requireCurrent(token); RetainedJson.ObjectValue result = retainedDocument; owner.requireCurrent(token); return result;
    }

    public Optional<List<EventOccurrence.HistoryItem>> retainedCommands() {
        owner.requireCurrent(token);
        Optional<List<EventOccurrence.HistoryItem>> result = history.retainedCommands();
        owner.requireCurrent(token);
        return result;
    }
}
