package org.xar.ck3.control.application.action;

import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

public final class ActionRecordCodec {
    private ActionRecordCodec() { }
    public static byte[] encode(ActionRecord record, ActionPorts.OutcomeArchive archive) {
        var row = StrictJson.object(); row.put("schema", "xar.java-action-record/v1");
        row.set("receipt_ref", archive.receiptReferenceOf(record.receipt()).toJson());
        if (record.previous().isPresent()) row.set("previous", record.previous().orElseThrow().toJson()); else row.putNull("previous");
        return StrictJson.canonical(row);
    }
    public static ActionRecord decode(byte[] raw, ActionPorts.OutcomeArchive archive) {
        var row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "receipt_ref", "previous"));
        StrictJson.require(StrictJson.text(row.get("schema")).equals("xar.java-action-record/v1"), "exact action record schema required");
        return new ActionRecord(archive.loadReceipt(ExactRef.fromJson(row.get("receipt_ref"))),
                row.get("previous").isNull() ? Optional.empty() : Optional.of(ExactRef.fromJson(row.get("previous"))));
    }
}
