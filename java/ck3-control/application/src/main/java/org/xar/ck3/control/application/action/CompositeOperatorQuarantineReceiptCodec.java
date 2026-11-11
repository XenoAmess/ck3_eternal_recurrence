package org.xar.ck3.control.application.action;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Explicit independent receipt format. Old action receipt encoders remain the old-schema route. */
public final class CompositeOperatorQuarantineReceiptCodec {
    public static final String SCHEMA="xar.java.composite-operator-quarantined-receipt/v1";
    private CompositeOperatorQuarantineReceiptCodec() { }
    public static byte[] encodeReceipt(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        require(receipt.state() instanceof ActionState.CompositeOperatorQuarantined,"only typed operator quarantine uses this receipt schema");
        var state=(ActionState.CompositeOperatorQuarantined)receipt.state();var proof=CompositeOperatorQuarantineObservation.load(receipt,archive);
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("version",receipt.version());row.put("sequence",receipt.sequence());row.put("body_sha256",receipt.bodySha256());
        row.set("original_receipt",proof.originalReceipt().toJson());row.set("observation_ref",state.observationRef().toJson());
        return ProposalLifecycleCodec.encodePayload(row,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
    }
    public static ActionReceipt decodeReceipt(JsonNode value,ActionPorts.OutcomeArchive archive) {
        var row=StrictJson.object(value,Set.of("schema","version","sequence","body_sha256","original_receipt","observation_ref"));
        require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact operator receipt schema required");
        var originalRef=ExactRef.fromJson(row.get("original_receipt"));var original=archive.loadReceipt(originalRef);
        require(original.state() instanceof ActionState.CompositeUnknown,"operator receipt must retain its original unknown receipt");
        var execution=((ActionState.CompositeUnknown)original.state()).execution();
        var receipt=new ActionReceipt(Math.toIntExact(StrictJson.integer(row.get("version"),1,1)),StrictJson.integer(row.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER),original.command(),StrictJson.text(row.get("body_sha256")),new ActionState.CompositeOperatorQuarantined(execution,ExactRef.fromJson(row.get("observation_ref"))));
        var proof=CompositeOperatorQuarantineObservation.load(receipt,archive);require(proof.originalReceipt().equals(originalRef),"operator receipt original reference differs");
        return receipt;
    }
}
