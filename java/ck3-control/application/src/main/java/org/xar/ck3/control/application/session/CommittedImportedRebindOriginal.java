package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterContracts.HistoricalTransition;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Read-only original for a stopped worker whose imported successor is already rebound and has taken no ordinary action. */
final class CommittedImportedRebindOriginal {
    private CommittedImportedRebindOriginal() { }

    record Data(HistoricalTransition attachment, HistoricalTransition rebind, SavedAttachmentSourceStore.ImportedOrigin importedOrigin,
            SavedAttachmentSourceStore.ImportedRecoveryBasis recoveryBasis, CheckpointPair pair,
            SemanticEvidence archivedSemantic, Pin tombstone, List<Pin> semanticPins, List<String> consumedSuccessorBatches) {
        Data { semanticPins = List.copyOf(semanticPins); consumedSuccessorBatches = List.copyOf(consumedSuccessorBatches); }
    }

    /** Historical archive and its exact current Writer suffix. The suffix still requires its own business replay. */
    record Historical(Data original, ContinuityState current, List<HistoricalTransition> suffix) {
        Historical { suffix=List.copyOf(suffix); }
    }

    static Data read(Session same, Pin actualAttachment) throws IOException {
        var history = readRetained(same,actualAttachment,false);
        var original = history.original();
        final List<String> consumed;
        try {
            consumed=CommittedImportedBatchTail.verify(history.current(),original.attachment(),original.rebind(),history.suffix());
        } catch(IllegalArgumentException invalid) {
            throw new IOException("Invalid committed imported REBIND batch suffix",invalid);
        }
        return new Data(original.attachment(),original.rebind(),original.importedOrigin(),original.recoveryBasis(),original.pair(),
                original.archivedSemantic(),original.tombstone(),original.semanticPins(),consumed);
    }

    static Historical readHistorical(Session same, Pin actualAttachment)throws IOException {
        return readRetained(same,actualAttachment,true);
    }

    private static Historical readRetained(Session same, Pin actualAttachment, boolean locateHistoricRebind) throws IOException {
        var head = same.head();
        if (head.snapshotNeedsRecovery() || !head.indexRepairs().isEmpty())
            throw new IOException("Committed imported REBIND readback requires a clean canonical head");
        long sequence = head.state().sequence();
        try {
            var eventDirectory = Path.of(same.persistedHead().path()).toAbsolutePath().normalize()
                    .resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
            var state = head.state().toJson();
            var batchOwner = state.path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("session");
            boolean successorBatch = batchOwner.hasNonNull("game") && ContinuityJson.same(batchOwner.get("game"), state.get("game_binding"));
            var suffix = locateHistoricRebind || successorBatch
                    ? Optional.of(findIndexedRebind(same, head, actualAttachment, eventDirectory)) : Optional.<IndexedRebind>empty();
            var originals = new ArrayList<Pin>();
            originals.add(actualAttachment);
            if (suffix.isPresent()) originals.addAll(suffix.orElseThrow().events());
            else originals.add(document(head,eventDirectory.resolve(String.format(Locale.ROOT, "%08d.json", sequence))));
            var edges = same.withHistoricalTransitions(originals, retained -> {
                try { return List.copyOf(retained); }
                catch (UncheckedIOException failure) { throw failure.getCause(); }
            });
            var attachment = edges.getFirst();
            if (!attachment.kind().equals(SavedAttachmentAuthority.KIND) || sequence <= attachment.sequence())
                throw new IOException("Committed imported REBIND readback requires an earlier exact imported attachment");
            var rebind = edges.get(1);
            var source = ContinuityJson.parseObject(rebind.details(), ContinuityJson.DOCUMENT_MAX_BYTES);
            String attachmentDigest = ContinuityJson.digest(attachment.after().toJson());
            boolean exactRebind = suffix.map(found->rebind.sequence()==found.rebindSequence()&&rebind.eventIdentity().equals(found.rebindIdentity()))
                    .orElseGet(()->head.digest().equals(ContinuityJson.digest(rebind.after().toJson())));
            if (!WriterContracts.ORDINARY_CYCLE_KIND.equals(rebind.kind()) || !"REBIND".equals(source.path("operation").asText())
                    || !WriterContracts.ORDINARY_IMPORTED_CYCLE_RESTORE_SOURCE.equals(source.path("source").asText())
                    || !attachment.eventIdentity().equals(StrictJson.text(source.get("attachment_identity")))
                    || !attachmentDigest.equals(StrictJson.text(source.get("attachment_head_digest")))
                    || !("restore-cycle:" + attachment.eventIdentity()).equals(StrictJson.text(source.get("evidence_id")))
                    || !exactRebind)
                throw new IOException("Current head is not the exact committed imported REBIND");

            var original = ContinuityJson.parseObject(attachment.details(), ContinuityJson.DOCUMENT_MAX_BYTES);
            var basis = SavedAttachmentSourceStore.importedRecoveryBasis(original)
                    .orElseThrow(() -> new IOException("Committed imported REBIND needs its exact recovery basis"));
            var sources = SavedAttachmentSourceStore.Sources.decode(original.get(SavedAttachmentSourceStore.SOURCES_DETAIL));
            var imported = sources.importedOrigin()
                    .orElseThrow(() -> new IOException("Committed imported REBIND needs its independent Saved origin"));
            var pair = CheckpointPairCodec.decode(ContinuityJson.canonical(original.get(SavedAttachmentAuthority.PAIR_DETAIL)));
            var semantic = OrdinaryCycleTransitions.semanticFromJson(source.get("semantic"));
            var opening = ContinuityJson.object(attachment.after().toJson().get("latest_binding"));
            var oldActionHead = ContinuityActionJournal.recordHead(attachment.after());
            if (!basis.departed().equals(imported.owner()) || !basis.successor().equals(OrdinaryCycleTransitions.sessionFromJson(source.get("session")))
                    || basis.predecessorSequence() != attachment.before().sequence()
                    || !basis.predecessorDigest().equals(ContinuityJson.digest(attachment.before().toJson()))
                    || !basis.requestId().equals(StrictJson.text(original.get("evidence_id")))
                    || !basis.secondNative().reference().equals(sources.restoredNative())
                    || !sources.restoredNative().equals(ExactRef.fromJson(opening.get("original_native_packet")))
                    || !pair.equals(CheckpointPairCodec.decode(ContinuityJson.canonical(source.get("restore_pair"))))
                    || sources.physicalSaveWitness().filter(pair.save()::equals).isEmpty()
                    || oldActionHead.isEmpty() || !oldActionHead.equals(ContinuityActionJournal.recordHead(attachment.before()))
                    || !oldActionHead.equals(ContinuityActionJournal.recordHead(rebind.after()))
                    || semantic.originalNativePacket().equals(basis.secondNative().reference())
                    || semantic.frame().frame().snapshotId().equals(StrictJson.text(opening.get("snapshot_id")))
                    || semantic.frame().frame().identity().nativeRevision().compareTo(new BigInteger(StrictJson.text(opening.get("native_revision")))) <= 0)
                throw new IOException("Committed imported REBIND changed its exact successor, physical SAVE or historical action/observation roles");

            var before = rebind.before();
            same.requireDomainImportContinuation(attachment.sequence(), attachmentDigest, before.sequence(),
                    ContinuityJson.digest(before.toJson()));

            var tombstone = same.capturePin(ExactRef.fromJson(source.get("previous_state_ref")), ContinuityJson.DOCUMENT_MAX_BYTES);
            var reduced = OrdinaryCycleTransitions.replayImportedRebind(before, source,
                    same.readPinned(tombstone, ContinuityJson.DOCUMENT_MAX_BYTES)).toJson();
            reduced.put("sequence", rebind.sequence()).put("last_event_identity", rebind.eventIdentity());
            if (!ContinuityJson.same(reduced, rebind.after().toJson()))
                throw new IOException("Committed imported REBIND differs from the exact zero-credit ordinary reducer");

            var semanticPins = new ArrayList<Pin>();
            for (var ref : semantic.references()) semanticPins.add(same.capturePin(ref, WriterContracts.MAX_PIN_BYTES));
            for (var pin : basis.pins()) same.verifyPin(pin);
            same.verifyPin(imported.targetEntry());
            same.verifyPin(imported.physicalConfirmation());
            if(suffix.isPresent())same.verifyPin(suffix.orElseThrow().index());
            if (!head.digest().equals(same.head().digest()))
                throw new IOException("Canonical head changed during committed imported REBIND readback");
            return new Historical(new Data(attachment,rebind,imported,basis,pair,semantic,tombstone,semanticPins,List.of()),
                    head.state(),edges.subList(2,edges.size()));
        } catch (IllegalArgumentException | java.time.DateTimeException invalid) {
            throw new IOException("Invalid committed imported REBIND original", invalid);
        }
    }

    private record IndexedRebind(Pin index,long rebindSequence,String rebindIdentity,List<Pin> events) { }

    private static IndexedRebind findIndexedRebind(Session same, WriterContracts.Head head, Pin attachment, Path events)throws IOException {
        var attached=ContinuityJson.parseObject(same.readPinned(attachment,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
        String identity=StrictJson.text(attached.get("identity"));
        var key=StrictJson.object().put("kind",WriterContracts.ORDINARY_CYCLE_KIND).put("evidence_id","restore-cycle:"+identity);
        var index=document(head,events.resolve("source-"+ContinuityJson.digest(key)+".json"));
        var entry=StrictJson.object(ContinuityJson.parseObject(same.readPinned(index,ContinuityJson.DOCUMENT_MAX_BYTES),ContinuityJson.DOCUMENT_MAX_BYTES),
                Set.of("identity","sequence"));
        long start=StrictJson.integer(entry.get("sequence"),1,head.state().sequence());
        var numbered=ContinuityBatchJournal.canonicalEventPins(same,head).subMap(start,true,head.state().sequence(),true);
        if(numbered.size()!=Math.addExact(Math.subtractExact(head.state().sequence(),start),1))
            throw new IOException("Committed imported REBIND batch suffix is missing an original numbered event");
        return new IndexedRebind(index,start,StrictJson.text(entry.get("identity")),List.copyOf(numbered.values()));
    }

    private static Pin document(WriterContracts.Head head, Path path)throws IOException {
        return head.documents().stream().filter(pin->path.equals(Path.of(pin.reference().path()).toAbsolutePath().normalize()))
                .findFirst().orElseThrow(()->new IOException("Committed imported REBIND lacks its captured canonical document"));
    }
}
