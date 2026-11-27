package org.xar.ck3.control.application.session;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.session.SessionPorts.JournalKind;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterContracts.HistoricalTransition;
import org.xar.ck3.control.contracts.StrictJson;

/** Empty ordinary batches in one captured Writer history. This is DATA for cold reopening only. */
final class CommittedImportedBatchTail {
    private CommittedImportedBatchTail() { }

    /** The caller supplies the verified original REBIND and its entire canonical tail from the held Writer. */
    static List<String> verify(ContinuityState current, HistoricalTransition attachment, HistoricalTransition rebind,
            List<HistoricalTransition> suffix) {
        var original = ContinuityJson.parseObject(rebind.details(), ContinuityJson.DOCUMENT_MAX_BYTES);
        var owner = OrdinaryCycleTransitions.sessionFromJson(original.get("session"));
        var restored = rebind.after().toJson();
        var cycle = restored.path(WriterContracts.ORDINARY_CYCLE_FIELD);
        require(SavedAttachmentAuthority.KIND.equals(attachment.kind()) && attachment.sequence() < rebind.sequence()
                && WriterContracts.ORDINARY_CYCLE_KIND.equals(rebind.kind())
                && "REBIND".equals(original.path("operation").asText())
                && WriterContracts.ORDINARY_IMPORTED_CYCLE_RESTORE_SOURCE.equals(original.path("source").asText())
                && attachment.eventIdentity().equals(original.path("attachment_identity").asText())
                && ContinuityJson.digest(attachment.after().toJson()).equals(original.path("attachment_head_digest").asText())
                && rebind.after().status() == ContinuityState.Status.RUNNING
                && ContinuityJson.same(owner.game().toJson(), restored.get("game_binding"))
                && owner.equals(OrdinaryCycleTransitions.sessionFromJson(cycle.get("session")))
                && cycle.path("head").isNull() && cycle.path("pending_receipt").isNull(),
                "empty batch tail requires the exact imported REBIND and its clean successor cycle");

        var departed = attachment.before().toJson().path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        require(JournalKind.BATCH_INTERRUPTED.name().equals(departed.path("boundary").asText()),
                "empty batch tail requires its actual departed interrupted batch");
        String previousBatch = StrictJson.text(departed.get("batch_id"));
        int separator = previousBatch.lastIndexOf('-');
        require(separator > 0 && previousBatch.substring(separator + 1).matches("0|[1-9][0-9]{0,4}"),
                "departed ordinary batch must carry its canonical sequence");
        String prefix = previousBatch.substring(0, separator);
        int next = Integer.parseInt(previousBatch.substring(separator + 1)) + 1;
        var batches = new ArrayList<String>();
        ContinuityState previous = rebind.after();
        for (int index = 0; index < suffix.size(); index += 2) {
            require(next < 65_536, "empty imported batch tail exceeds the Controller batch bound");
            String batch = prefix + "-" + next++;
            previous = verifyEdge(previous, suffix.get(index), owner, batch, JournalKind.BATCH_STARTED);
            require(index + 1 < suffix.size(), "empty imported batch tail still has an open BATCH_STARTED");
            var terminal = suffix.get(index + 1);
            var details = ContinuityJson.parseObject(terminal.details(), ContinuityJson.DOCUMENT_MAX_BYTES);
            var kind = JournalKind.valueOf(StrictJson.text(details.get("boundary")));
            require(kind == JournalKind.BATCH_FINISHED || kind == JournalKind.BATCH_DEFERRED,
                    "empty imported batch tail must close each batch with FINISHED or DEFERRED");
            previous = verifyEdge(previous, terminal, owner, batch, kind);
            batches.add(batch);
        }
        require(Arrays.equals(previous.canonicalBytes(), current.canonicalBytes()),
                "empty imported batch tail must reach the exact current Writer head");
        return List.copyOf(batches);
    }

    private static ContinuityState verifyEdge(ContinuityState previous, HistoricalTransition edge,
            SessionIdentity owner, String batch, JournalKind kind) {
        require(edge.sequence() == previous.sequence() + 1 && Arrays.equals(edge.before().canonicalBytes(), previous.canonicalBytes()),
                "empty imported batch tail is not contiguous with its original predecessor");
        var reduced = OrdinaryCycleTransitions.replayCommittedBatchMetadata(previous, owner, batch, kind, edge).toJson();
        reduced.put("sequence", edge.sequence()).put("last_event_identity", edge.eventIdentity());
        require(Arrays.equals(ContinuityJson.canonical(reduced), edge.after().canonicalBytes()),
                "empty imported batch tail changed data outside its ordinary boundary");
        return edge.after();
    }
}
