package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual same-episode terminal row archived before the canonical lifecycle child commits. */
public record LifecycleHistoryBinding(String actionId,String parentBodySha256,long historyIndex,ExactRef originalRow) {
    public static final String SCHEMA="xar.java-lifecycle-history-binding/v1";
    public LifecycleHistoryBinding {
        StrictJson.text(actionId);org.xar.ck3.control.continuity.writer.WriterContracts.requireDigest(parentBodySha256);
        StrictJson.safe(historyIndex,1);java.util.Objects.requireNonNull(originalRow);StrictJson.require(originalRow.bytes()>0,"actual archived lifecycle row required");
    }
    public static LifecycleHistoryBinding produced(ActionCommand parent,DriverStateSnapshot.Complete actualAfter,ExactRef rowRef) {
        StrictJson.require(parent.operation().value().equals("death-terminal")&&!actualAfter.commandHistory().isEmpty(),"only an actual same-episode terminal produces current history coverage");
        var row=actualAfter.commandHistory().getLast();
        StrictJson.require(rowRef.bytes()==row.originalRow().json().length&&rowRef.sha256().equals(LifecycleJson.sha(row.originalRow().json())),"full original lifecycle row bytes differ");
        return new LifecycleHistoryBinding(parent.actionId(),ActionCodec.bodySha256(parent),row.index(),rowRef);
    }
    public ObjectNode toJson() {
        var row=LifecycleJson.row();row.put("schema",SCHEMA);row.put("action_id",actionId);row.put("parent_body_sha256",parentBodySha256);
        row.put("history_index",historyIndex);row.set("original_row",originalRow.toJson());return row;
    }
    public static LifecycleHistoryBinding fromJson(JsonNode value) {
        var row=StrictJson.object(value,Set.of("schema","action_id","parent_body_sha256","history_index","original_row"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"actual lifecycle history binding schema");
        return new LifecycleHistoryBinding(StrictJson.text(row.get("action_id")),StrictJson.text(row.get("parent_body_sha256")),
                StrictJson.integer(row.get("history_index"),1,StrictJson.MAX_SAFE_INTEGER),ExactRef.fromJson(row.get("original_row")));
    }
}
