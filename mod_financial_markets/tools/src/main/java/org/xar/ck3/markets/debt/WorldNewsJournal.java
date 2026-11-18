package org.xar.ck3.markets.debt;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Public facts only. Delivery cursors never erase facts, including remote characters' deaths. */
public final class WorldNewsJournal {
    public enum Kind { DEFAULT, AID, RESTRUCTURING, CRISIS, DEATH, RECOVERY, LISTING, DELISTING, DISCLOSURE, FINANCING_FAILED }
    public record FactKey(String sourceId, long revision) {
        public FactKey {
            if (sourceId == null || sourceId.isBlank() || revision < 1) throw new IllegalArgumentException("invalid fact identity");
        }
    }
    public record Fact(FactKey key, String actorId, Kind kind, int scene, long day) {
        public Fact {
            Objects.requireNonNull(key); Objects.requireNonNull(kind);
            if (actorId == null || actorId.isBlank() || day < 0 || scene < 1 || scene > 20)
                throw new IllegalArgumentException("invalid public fact");
        }
    }
    public record Entry(long sequence, Fact fact) {
        public Entry { if (sequence < 1) throw new IllegalArgumentException("invalid sequence"); Objects.requireNonNull(fact); }
    }
    public record Cursor(String playerId, int regularDelivered, int deathsDelivered, long lastDay, int deliveredToday) {
        public Cursor {
            if (playerId == null || playerId.isBlank() || regularDelivered < 0 || deathsDelivered < 0
                    || lastDay < -1 || deliveredToday < 0 || deliveredToday > 3)
                throw new IllegalArgumentException("invalid recipient cursor");
        }
    }
    public record Snapshot(List<Entry> entries, List<Cursor> cursors) {
        public Snapshot { entries = List.copyOf(entries); cursors = List.copyOf(cursors); }
    }
    private final List<Entry> entries = new ArrayList<>();
    private final List<Entry> regularQueue = new ArrayList<>();
    private final List<Entry> deathQueue = new ArrayList<>();
    private final Map<FactKey, Entry> facts = new LinkedHashMap<>();
    private final Map<String, Cursor> recipients = new LinkedHashMap<>();

    public synchronized Entry append(Fact fact) {
        Entry existing = facts.get(fact.key());
        if (existing != null) {
            if (!existing.fact().equals(fact)) throw new IllegalArgumentException("fact identity conflict");
            return existing;
        }
        Entry entry = new Entry(Math.addExact(entries.size(), 1), fact);
        entries.add(entry); facts.put(fact.key(), entry);
        if (fact.kind() == Kind.DEATH) deathQueue.add(entry); else regularQueue.add(entry);
        return entry;
    }

    /** New players can open the full journal; old facts are not replayed as a burst of toasts. */
    public synchronized void join(String playerId) {
        Cursor cursor = new Cursor(playerId, regularQueue.size(), deathQueue.size(), -1, 0);
        recipients.putIfAbsent(playerId, cursor);
    }

    public synchronized List<Entry> deliver(String playerId, long day) {
        if (day < 0) throw new IllegalArgumentException("invalid day");
        Cursor cursor = recipients.get(playerId);
        if (cursor == null) throw new IllegalArgumentException("unknown human player");
        if (day < cursor.lastDay()) throw new IllegalArgumentException("day reversal requires restoring the same snapshot");
        int already = day == cursor.lastDay() ? cursor.deliveredToday() : 0;
        List<Entry> result = new ArrayList<>(3);
        int deaths = cursor.deathsDelivered();
        int regular = cursor.regularDelivered();
        while (deaths < deathQueue.size() && result.size() < 3 - already) result.add(deathQueue.get(deaths++));
        while (regular < regularQueue.size() && result.size() < 3 - already) result.add(regularQueue.get(regular++));
        recipients.put(playerId, new Cursor(playerId, regular, deaths, day, already + result.size()));
        return List.copyOf(result);
    }

    public synchronized List<Entry> entries() { return List.copyOf(entries); }
    public synchronized Snapshot snapshot() { return new Snapshot(entries, new ArrayList<>(recipients.values())); }

    public static WorldNewsJournal restore(Snapshot snapshot) {
        WorldNewsJournal journal = new WorldNewsJournal();
        for (Entry entry : snapshot.entries()) {
            if (entry.sequence() != journal.entries.size() + 1 || journal.facts.containsKey(entry.fact().key()))
                throw new IllegalArgumentException("noncontiguous or duplicate journal fact");
            journal.append(entry.fact());
        }
        for (Cursor cursor : snapshot.cursors()) {
            if (cursor.regularDelivered() > journal.regularQueue.size() || cursor.deathsDelivered() > journal.deathQueue.size()
                    || journal.recipients.putIfAbsent(cursor.playerId(), cursor) != null)
                throw new IllegalArgumentException("invalid or duplicate recipient");
        }
        return journal;
    }
}
