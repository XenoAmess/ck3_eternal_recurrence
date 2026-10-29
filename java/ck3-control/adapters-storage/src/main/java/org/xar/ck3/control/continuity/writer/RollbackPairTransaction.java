package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityEvent;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Private transaction machinery of ContinuityWriter, always inside its original lock. */
final class RollbackPairTransaction {
    enum Kind { EVENT, SNAPSHOT, INDEX }
    record Operation(Kind kind, Path path, byte[] payload, boolean replace) { }
    private RollbackPairTransaction() { }
    static RollbackPair.Commit commit(Layout layout, ContinuityStore store, RollbackPair.Plan submitted,
                                       RollbackPair.Authority authority, String nowUtc, WriterFaultProbe faults, StorageWriteGuard storageGuard) throws IOException {
        WindowsLedgerLock.requireHeld(layout.lock()); StrictJson.utc(nowUtc); RollbackPair.validate(submitted);
        Head actual = store.head();
        // Snapshot may advance only through the exact planned pair. All other captured files retain identity.
        for (Pin pin : submitted.originalHead().documents()) {
            if (!Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(layout.snapshot())) LedgerFiles.verify(pin);
        }
        for (Pin pin : submitted.evidence().qualificationSources()) LedgerFiles.verify(pin);
        LedgerFiles.exact(submitted.evidence().proof(), ContinuityJson.DOCUMENT_MAX_BYTES);
        RollbackPair.Evidence evidence = authority.revalidate(submitted.originalHead(), submitted.evidence().proof());
        RollbackPair.Plan checked = RollbackPair.plan(submitted.originalHead(), evidence);
        StrictJson.require(ContinuityJson.same(submitted.toJson(), checked.toJson()), "stale/forged rollback plan or actual source prerequisite drift");
        List<ContinuityState> states = List.of(checked.originalHead().state(), checked.first().committed(), checked.second().committed());
        int stage = stage(actual.state(), states); StrictJson.require(stage >= 0, "rollback actual head sequence/digest CAS drift");
        var snapshotDocument = LedgerFiles.read(layout.snapshot(), ContinuityJson.LEDGER_MAX_BYTES);
        ContinuityState snapshot = ContinuityState.fromJson(ContinuityJson.parseObject(snapshotDocument.bytes(), ContinuityJson.LEDGER_MAX_BYTES), layout.machineId());
        int snapshotStage = stage(snapshot, states); StrictJson.require(snapshotStage >= 0 && snapshotStage <= stage, "snapshot outside exact pair lineage");
        if (snapshotStage == 0) {
            Pin originalSnapshot = submitted.originalHead().documents().stream()
                    .filter(pin -> Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(layout.snapshot())).findFirst()
                    .orElseThrow(() -> new IOException("original rollback view has no captured canonical snapshot identity"));
            StrictJson.require(originalSnapshot.equals(snapshotDocument.pin()), "uncommitted original snapshot identity drift");
        }
        long beforeSequence = states.get(0).sequence(); List<Operation> operations = new ArrayList<>();
        int currentSnapshotStage = snapshotStage, offset = 0;
        for (RollbackPair.EventPlan planned : List.of(checked.first(), checked.second())) {
            offset++; long sequence = beforeSequence + offset; Request request = planned.request();
            ContinuityEvent event = new ContinuityEvent(sequence, nowUtc, request.kind(), request.details(), request.identity(),
                    ContinuityJson.digest(states.get(offset - 1).toJson()), planned.committed());
            byte[] bytes = ContinuityJson.canonical(ContinuityEvent.fromJson(event.toJson(), states.get(offset - 1)).toJson());
            capped(bytes); capped(planned.committed().canonicalBytes());
            Path eventPath = layout.event(sequence); Optional<LedgerFiles.Document> existing = LedgerFiles.optional(eventPath, ContinuityJson.LEDGER_MAX_BYTES);
            StrictJson.require(existing.isPresent() == (offset <= stage), "head/event existence mismatch");
            if (existing.isPresent()) checkExisting(ContinuityJson.parseObject(existing.orElseThrow().bytes(), ContinuityJson.LEDGER_MAX_BYTES), event.toJson());
            Path indexPath = layout.sourceIndex(request.sourceKey());
            Optional<LedgerFiles.Document> index = LedgerFiles.optional(indexPath);
            if (index.isPresent()) {
                StrictJson.require(existing.isPresent(), "orphan rollback source index");
                ContinuityStore.checkIndex(object(index.orElseThrow().bytes()), sequence, request.identity());
            }
            if (existing.isEmpty()) operations.add(new Operation(Kind.EVENT, eventPath, bytes, false));
            if (currentSnapshotStage < offset) {
                operations.add(new Operation(Kind.SNAPSHOT, layout.snapshot(), planned.committed().canonicalBytes(), true)); currentSnapshotStage = offset;
            }
            if (index.isEmpty()) operations.add(new Operation(Kind.INDEX, indexPath,
                    ContinuityJson.canonical(new IndexRepair(indexPath, sequence, request.identity()).toJson()), false));
        }
        // All validation and all operations are frozen before the first write, exactly as the original transaction.
        for (Pin pin : checked.evidence().qualificationSources()) LedgerFiles.verify(pin);
        ContinuityWriter.requireSameHead(actual, store.head());
        List<LedgerFiles.AtomicWrite> physical=new ArrayList<>();
        for(Operation operation:operations) {
            int max = operation.kind() == Kind.INDEX ? ContinuityJson.DOCUMENT_MAX_BYTES : ContinuityJson.LEDGER_MAX_BYTES;
            physical.add(LedgerFiles.prepareAtomic(operation.path(),operation.payload(),operation.replace(),max));
        }
        try {
            if(physical.isEmpty())return new RollbackPair.Commit(checked.transactionId(),beforeSequence,beforeSequence+2,
                    ContinuityJson.digest(states.get(2).toJson()),stage>0,0,0);
            return storageGuard.write(LedgerFiles.plan(layout.lock(),physical),()->{
                int events=0;
                for(int index=0;index<operations.size();index++){
                    Operation operation=operations.get(index);
                    LedgerFiles.atomic(storageGuard,layout.lock(),physical.get(index));
                    if(operation.kind()==Kind.EVENT)events++;
                    WriterFaultProbe.Boundary boundary=switch(operation.kind()){
                        case EVENT->WriterFaultProbe.Boundary.EVENT_PUBLISHED;
                        case SNAPSHOT->WriterFaultProbe.Boundary.SNAPSHOT_PUBLISHED;
                        case INDEX->WriterFaultProbe.Boundary.SOURCE_INDEX_PUBLISHED;
                    };
                    faults.reached(boundary,StrictJson.integer(ContinuityJson.parseObject(operation.payload(),
                            operation.kind()==Kind.INDEX?ContinuityJson.DOCUMENT_MAX_BYTES:ContinuityJson.LEDGER_MAX_BYTES).get("sequence"),1,StrictJson.MAX_SAFE_INTEGER));
                }
                Head after=store.head();
                StrictJson.require(ContinuityJson.same(after.state().toJson(),states.get(2).toJson())
                        &&!after.snapshotNeedsRecovery()&&after.indexRepairs().isEmpty(),"rollback actual persisted readback");
                return new RollbackPair.Commit(checked.transactionId(),beforeSequence,beforeSequence+2,
                        ContinuityJson.digest(states.get(2).toJson()),stage>0,operations.size(),events);
            });
        }catch(IOException|RuntimeException error){
            throw new CommitUncertainException(checked.transactionId(),beforeSequence+2,error);
        }
    }
    private static void capped(byte[] bytes) throws IOException {
        if (bytes.length + 1 > ContinuityJson.LEDGER_MAX_BYTES) throw new IOException("rollback receipt exceeds ledger output cap");
    }
    private static int stage(ContinuityState actual, List<ContinuityState> states) {
        for (int i = 0; i < states.size(); i++) if (ContinuityJson.same(actual.toJson(), states.get(i).toJson())) return i;
        return -1;
    }
    private static void checkExisting(ObjectNode actual, ObjectNode expected) {
        StrictJson.object(actual, Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        StrictJson.utc(StrictJson.text(actual.get("at_utc")));
        for (String field : Set.of("sequence", "kind", "details", "identity", "previous_sha256", "after"))
            StrictJson.require(ContinuityJson.same(actual.get(field), expected.get(field)), "rollback committed event conflict " + field);
    }
}
