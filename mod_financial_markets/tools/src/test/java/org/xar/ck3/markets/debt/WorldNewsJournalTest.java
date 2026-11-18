package org.xar.ck3.markets.debt;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.debt.WorldNewsJournal.*;

final class WorldNewsJournalTest {
    @Test void remoteFactsReachEveryHumanIndependentlyAtMostThreePerDay() {
        var news = new WorldNewsJournal(); news.join("player-one"); news.join("player-two");
        for (int i = 1; i <= 20; i++) news.append(fact(i));
        assertEquals(3, news.deliver("player-one", 5).size());
        assertTrue(news.deliver("player-one", 5).isEmpty());
        assertEquals(3, news.deliver("player-two", 5).size());
        for (int day = 6; day <= 11; day++) news.deliver("player-one", day);
        assertTrue(news.deliver("player-one", 12).isEmpty());
        assertEquals(20, news.entries().size());
        assertEquals(4, news.deliver("player-two", 6).getFirst().sequence());
    }

    @Test void sameFactDoesNotDuplicateAndConflictCannotReplaceHistory() {
        var news = new WorldNewsJournal();
        assertEquals(news.append(fact(1)), news.append(fact(1)));
        assertThrows(IllegalArgumentException.class, () -> news.append(new Fact(fact(1).key(), "different", Kind.DEATH, 1, 5)));
        assertEquals(1, news.entries().size());
    }

    @Test void saveLoadPreservesDailyCapAndPendingNotifications() {
        var news = new WorldNewsJournal(); news.join("human");
        for (int i = 1; i <= 10; i++) news.append(fact(i));
        news.deliver("human", 5);
        var restored = WorldNewsJournal.restore(news.snapshot());
        assertTrue(restored.deliver("human", 5).isEmpty());
        assertEquals(4, restored.deliver("human", 6).getFirst().sequence());
        restored.join("new-human");
        assertTrue(restored.deliver("new-human", 6).isEmpty());
        assertEquals(10, restored.entries().size());
    }

    @Test void malformedJournalAndReverseDayAreRejected() {
        var news = new WorldNewsJournal(); news.join("human"); news.append(fact(1)); news.deliver("human", 5);
        assertThrows(IllegalArgumentException.class, () -> news.deliver("human", 4));
        assertThrows(IllegalArgumentException.class, () -> WorldNewsJournal.restore(new Snapshot(
                List.of(new Entry(2, fact(1))), List.of())));
        assertThrows(IllegalArgumentException.class, () -> new Fact(new FactKey("x", 1), "actor", Kind.DEATH, 21, 5));
    }

    @Test void deathsTakePriorityOverOrdinaryBacklogWithoutLosingOrRepeatingFacts() {
        var news = new WorldNewsJournal(); news.join("human");
        news.append(new Fact(new FactKey("listing-1", 1), "issuer", Kind.LISTING, 20, 5));
        news.append(new Fact(new FactKey("listing-2", 1), "issuer", Kind.LISTING, 20, 5));
        news.append(fact(1));
        news.append(new Fact(new FactKey("delisting-1", 1), "issuer", Kind.DELISTING, 20, 5));
        news.append(fact(2));
        news.append(new Fact(new FactKey("crisis-1", 1), "borrower", Kind.CRISIS, 20, 5));
        assertEquals(List.of(3L, 5L, 1L), news.deliver("human", 5).stream().map(Entry::sequence).toList());
        var restored = WorldNewsJournal.restore(news.snapshot());
        assertTrue(restored.deliver("human", 5).isEmpty());
        assertEquals(List.of(2L, 4L, 6L), restored.deliver("human", 6).stream().map(Entry::sequence).toList());
        assertTrue(restored.deliver("human", 7).isEmpty());
        assertEquals(6, restored.entries().size());
    }

    @Test void journalAndIndependentQueueCursorsSurviveJsonRoundTrip() throws Exception {
        var news = new WorldNewsJournal(); news.join("human");
        news.append(new Fact(new FactKey("listing", 1), "issuer", Kind.LISTING, 20, 5));
        news.append(fact(1));
        news.deliver("human", 5);
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        Snapshot snapshot = mapper.readValue(mapper.writeValueAsBytes(news.snapshot()), Snapshot.class);
        var restored = WorldNewsJournal.restore(snapshot);
        assertTrue(restored.deliver("human", 5).isEmpty());
        restored.append(fact(2));
        assertEquals(List.of(3L), restored.deliver("human", 6).stream().map(Entry::sequence).toList());
    }

    private Fact fact(int scene) { return new Fact(new FactKey("debt-" + scene, 1), "remote-ai-" + scene, Kind.DEATH, scene, 5); }
}
