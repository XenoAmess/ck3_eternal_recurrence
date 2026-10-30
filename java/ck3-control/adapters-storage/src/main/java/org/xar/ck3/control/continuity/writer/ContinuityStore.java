package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityEvent;
import org.xar.ck3.control.continuity.ContinuityHistory;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Reads the existing finite anchor/event/snapshot chain. It never enumerates or rewrites history. */
final class ContinuityStore {
    private final Layout layout;
    private volatile Head retainedHead;
    ContinuityStore(Layout layout) { this.layout = layout; }
    Head head() throws IOException {
        Head fast = incrementalHead();
        if (fast != null) return fast;
        var anchor = LedgerFiles.exact(layout.anchor(), ContinuityJson.LEDGER_MAX_BYTES);
        var snapshot = LedgerFiles.read(layout.snapshot(), ContinuityJson.LEDGER_MAX_BYTES);
        if (!Files.isDirectory(layout.events(), java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("existing original event directory required");
        List<Pin> pins = new ArrayList<>(List.of(anchor.pin(), snapshot.pin()));
        List<Path> absent = new ArrayList<>(); List<IndexRepair> repairs = new ArrayList<>();
        ContinuityState start = state(anchor.bytes()), stored = state(snapshot.bytes());
        List<LedgerFiles.Document> captured = new ArrayList<>();
        Path nextAbsent = null;
        for (int count = 0; count < ContinuityHistory.maximumEvents(); count++) {
            Path path = layout.event(Math.addExact(start.sequence(), Math.addExact((long) count, 1)));
            Optional<LedgerFiles.Document> document = LedgerFiles.optional(path, ContinuityJson.LEDGER_MAX_BYTES);
            if (document.isEmpty()) { LedgerFiles.requireAbsent(path); nextAbsent = path; break; }
            if (count == ContinuityHistory.maximumEvents() - 1) throw new IOException("finite continuity history exhausted");
            captured.add(document.orElseThrow());
        }
        // The pure projector decodes and validates every original edge exactly once, including
        // its predecessor, full after state, unique source and exact earlier episode originals.
        var projection = ContinuityHistory.preview(start, stored, captured.stream().map(LedgerFiles.Document::bytes).toList());
        for (int index = 0; index < projection.events().size(); index++) {
            ContinuityEvent event = projection.events().get(index);
            if(org.xar.ck3.control.continuity.EpisodeWindow.BASELINE_KIND.equals(event.kind())){
                var baseline=org.xar.ck3.control.continuity.EpisodeWindow.baseline(new Request(event.kind(),event.details(),List.of()));
                StrictJson.require(pins.contains(baseline.begin().eventPin()),
                        "BASELINE original BEGIN must retain its actual captured Win32 file identity, not only equal bytes");
            }
            pins.add(captured.get(index).pin());
            Path indexPath = layout.sourceIndex(event.sourceKey());
            Optional<LedgerFiles.Document> sourceIndex = LedgerFiles.optional(indexPath);
            if (sourceIndex.isEmpty()) {
                LedgerFiles.requireAbsent(indexPath); absent.add(indexPath);
                repairs.add(new IndexRepair(indexPath, event.sequence(), event.identity()));
            } else {
                checkIndex(object(sourceIndex.orElseThrow().bytes()), event.sequence(), event.identity()); pins.add(sourceIndex.orElseThrow().pin());
            }
        }
        absent.add(java.util.Objects.requireNonNull(nextAbsent, "finite continuity next event absence required"));
        for (Path path : absent) LedgerFiles.requireAbsent(path);
        Head result = new Head(projection.head(), pins, absent, repairs, projection.snapshotNeedsRecovery());
        retainedHead = result;
        return result;
    }
    /** Read-only recapture after an actual historical-read failure; no repair is published. */
    Head refreshHead() throws IOException {
        retainedHead = null;
        return head();
    }
    /** Same writer lock: project only one next committed edge after a clean captured head. */
    private Head incrementalHead() throws IOException {
        Head previous = retainedHead;
        if (previous == null || previous.snapshotNeedsRecovery() || !previous.indexRepairs().isEmpty()) return null;
        var snapshot = LedgerFiles.read(layout.snapshot(), ContinuityJson.LEDGER_MAX_BYTES);
        Path next = layout.event(Math.addExact(previous.state().sequence(), 1));
        if (snapshot.pin().equals(previous.documents().get(1))) {
            if (Files.exists(next, java.nio.file.LinkOption.NOFOLLOW_LINKS)) return null;
            LedgerFiles.requireAbsent(next);
            return previous;
        }
        ContinuityState stored = state(snapshot.bytes());
        if (stored.sequence() != Math.addExact(previous.state().sequence(), 1)) return null;
        var document = LedgerFiles.optional(next, ContinuityJson.LEDGER_MAX_BYTES);
        if (document.isEmpty()) return null;
        ContinuityEvent event = ContinuityEvent.fromJson(
                ContinuityJson.parseObject(document.orElseThrow().bytes(), ContinuityJson.LEDGER_MAX_BYTES),
                previous.state());
        if (org.xar.ck3.control.continuity.EpisodeWindow.BEGIN_KIND.equals(event.kind())
                || org.xar.ck3.control.continuity.EpisodeWindow.BASELINE_KIND.equals(event.kind())) return null;
        StrictJson.require(ContinuityJson.same(stored.toJson(), event.after().toJson()),
                "retained canonical head differs from its next committed snapshot");
        Path indexPath = layout.sourceIndex(event.sourceKey());
        if (previous.documents().stream().anyMatch(pin ->
                java.nio.file.Path.of(pin.reference().path()).equals(indexPath))) return null;
        var sourceIndex = LedgerFiles.optional(indexPath);
        if (sourceIndex.isEmpty()) return null;
        checkIndex(object(sourceIndex.orElseThrow().bytes()), event.sequence(), event.identity());
        Path absent = layout.event(Math.addExact(event.sequence(), 1));
        if (Files.exists(absent, java.nio.file.LinkOption.NOFOLLOW_LINKS)) return null;
        LedgerFiles.requireAbsent(absent);
        List<Pin> pins = new ArrayList<>(previous.documents());
        pins.set(1, snapshot.pin());
        pins.add(document.orElseThrow().pin());
        pins.add(sourceIndex.orElseThrow().pin());
        Head result = new Head(stored, pins, List.of(absent), List.of(), false);
        retainedHead = result;
        return result;
    }
    Optional<ContinuityEvent> duplicate(Request request, Head head) throws IOException {
        Path indexPath = layout.sourceIndex(request.sourceKey());
        Optional<LedgerFiles.Document> index = LedgerFiles.optional(indexPath);
        Optional<IndexRepair> capturedMissing = head.indexRepairs().stream().filter(repair -> repair.path().equals(indexPath)).findFirst();
        if (index.isEmpty() && capturedMissing.isEmpty()) return Optional.empty();
        // A durable event is already committed even if the process died before its source index.
        // The captured exact source-key repair also prevents a changed ID payload from committing a second event.
        ObjectNode row = StrictJson.object(index.isPresent() ? object(index.orElseThrow().bytes())
                : capturedMissing.orElseThrow().toJson(), Set.of("sequence", "identity"));
        long sequence = StrictJson.integer(row.get("sequence"), 1, head.state().sequence());
        StrictJson.require(StrictJson.text(row.get("identity")).equals(request.identity()), "same evidence ID changed contents");
        var eventDocument = LedgerFiles.read(layout.event(sequence), ContinuityJson.LEDGER_MAX_BYTES);
        ObjectNode event = StrictJson.object(ContinuityJson.parseObject(eventDocument.bytes(), ContinuityJson.LEDGER_MAX_BYTES), Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        StrictJson.require(StrictJson.integer(event.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER) == sequence
                && StrictJson.text(event.get("kind")).equals(request.kind())
                && StrictJson.text(event.get("identity")).equals(request.identity())
                && ContinuityJson.same(event.get("details"), request.detailsObject()), "source index has no exact committed event");
        StrictJson.utc(StrictJson.text(event.get("at_utc")));
        ContinuityState after = ContinuityState.fromJson(event.get("after"), layout.machineId());
        // head() has already validated each exact origin-changing BEGIN/BASELINE edge.
        // An original event in an earlier episode keeps its own origin forever.
        StrictJson.require(after.sequence() == sequence
                && StrictJson.text(after.toJson().get("last_event_identity")).equals(request.identity()), "indexed event after binding");
        if (index.isPresent()) LedgerFiles.verify(index.orElseThrow().pin()); else LedgerFiles.requireAbsent(indexPath);
        LedgerFiles.verify(eventDocument.pin());
        return Optional.of(new ContinuityEvent(sequence, StrictJson.text(event.get("at_utc")), request.kind(), request.details(),
                request.identity(), StrictJson.text(event.get("previous_sha256")), after));
    }
    List<LedgerFiles.AtomicWrite> recoveryWrites(Head head)throws IOException {
        List<LedgerFiles.AtomicWrite> writes=new ArrayList<>();
        if(head.snapshotNeedsRecovery())writes.add(LedgerFiles.prepareAtomic(layout.snapshot(),head.state().canonicalBytes(),true,ContinuityJson.LEDGER_MAX_BYTES));
        for(IndexRepair repair:head.indexRepairs())
            writes.add(LedgerFiles.prepareAtomic(repair.path(),ContinuityJson.canonical(repair.toJson()),false));
        return List.copyOf(writes);
    }
    int recover(Head head,StorageWriteGuard storage)throws IOException {
        return recover(recoveryWrites(head),storage);
    }
    int recover(List<LedgerFiles.AtomicWrite> writes,StorageWriteGuard storage)throws IOException {
        if(writes.isEmpty())return 0;
        return storage.write(LedgerFiles.plan(layout.lock(),writes),()->{
            for(var write:writes)LedgerFiles.atomic(storage,layout.lock(),write);
            return writes.size();
        });
    }
    private ContinuityState state(byte[] raw) { return ContinuityState.fromJson(ContinuityJson.parseObject(raw, ContinuityJson.LEDGER_MAX_BYTES), layout.machineId()); }
    static void checkIndex(ObjectNode row, long sequence, String identity) {
        StrictJson.object(row, Set.of("sequence", "identity"));
        StrictJson.require(StrictJson.integer(row.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER) == sequence
                && StrictJson.text(row.get("identity")).equals(identity), "source index conflicts with committed event");
    }
}
