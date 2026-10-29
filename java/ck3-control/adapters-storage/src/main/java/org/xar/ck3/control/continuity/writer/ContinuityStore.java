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
    ContinuityStore(Layout layout) { this.layout = layout; }
    Head head() throws IOException {
        var anchor = LedgerFiles.exact(layout.anchor(), ContinuityJson.LEDGER_MAX_BYTES);
        var snapshot = LedgerFiles.read(layout.snapshot(), ContinuityJson.LEDGER_MAX_BYTES);
        if (!Files.isDirectory(layout.events(), java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("existing original event directory required");
        List<Pin> pins = new ArrayList<>(List.of(anchor.pin(), snapshot.pin()));
        Set<String> committedSourceKeys = new java.util.HashSet<>();
        List<Path> absent = new ArrayList<>(); List<IndexRepair> repairs = new ArrayList<>();
        ContinuityState start = state(anchor.bytes()), stored = state(snapshot.bytes()), cursor = start;
        List<byte[]> documents = new ArrayList<>();
        for (int count = 0; count < ContinuityHistory.MAX_CONTINUITY_EVENTS; count++) {
            Path path = layout.event(Math.addExact(cursor.sequence(), 1));
            Optional<LedgerFiles.Document> document = LedgerFiles.optional(path, ContinuityJson.LEDGER_MAX_BYTES);
            if (document.isEmpty()) { LedgerFiles.requireAbsent(path); absent.add(path); break; }
            if (count == ContinuityHistory.MAX_CONTINUITY_EVENTS - 1) throw new IOException("finite continuity history exhausted");
            ContinuityEvent event = ContinuityEvent.fromJson(ContinuityJson.parseObject(document.orElseThrow().bytes(), ContinuityJson.LEDGER_MAX_BYTES), cursor);
            if(org.xar.ck3.control.continuity.EpisodeWindow.BASELINE_KIND.equals(event.kind())){
                var baseline=org.xar.ck3.control.continuity.EpisodeWindow.baseline(new Request(event.kind(),event.details(),List.of()));
                StrictJson.require(pins.contains(baseline.begin().eventPin()),
                        "BASELINE original BEGIN must retain its actual captured Win32 file identity, not only equal bytes");
            }
            StrictJson.require(committedSourceKeys.add(event.sourceKey()), "one durable event per continuity source identity");
            documents.add(document.orElseThrow().bytes()); pins.add(document.orElseThrow().pin()); cursor = event.after();
            Path indexPath = layout.sourceIndex(event.sourceKey());
            Optional<LedgerFiles.Document> index = LedgerFiles.optional(indexPath);
            if (index.isEmpty()) {
                LedgerFiles.requireAbsent(indexPath); absent.add(indexPath);
                repairs.add(new IndexRepair(indexPath, event.sequence(), event.identity()));
            } else {
                checkIndex(object(index.orElseThrow().bytes()), event.sequence(), event.identity()); pins.add(index.orElseThrow().pin());
            }
        }
        var projection = ContinuityHistory.preview(start, stored, documents);
        for (Path path : absent) LedgerFiles.requireAbsent(path);
        return new Head(projection.head(), pins, absent, repairs, projection.snapshotNeedsRecovery());
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
