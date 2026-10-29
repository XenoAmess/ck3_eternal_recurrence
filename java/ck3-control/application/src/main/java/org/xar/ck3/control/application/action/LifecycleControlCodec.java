package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

public final class LifecycleControlCodec {
    private LifecycleControlCodec() { }
    public static ObjectNode encode(LifecycleControlObservation value, Function<PlanningReadReceipt, ExactRef> readReference) {
        var row = StrictJson.object(); row.put("schema", "xar.lifecycle-modal-control/v1"); row.set("after", LifecycleIdentityCodec.encode(value.after()));
        row.set("source", ProposalLifecycleCodec.source(value.source())); row.put("session_id", value.sessionId()); row.put("observer_schema", value.observerSchema());
        row.set("actual", ProposalLifecycleCodec.encodeValues(value.actual()));
        row.set("before_status_ref", readReference.apply(value.beforeStatus()).toJson()); row.set("independent_read_ref", readReference.apply(value.independentRead()).toJson());
        var refs = row.putArray("supporting_evidence"); value.supportingEvidence().forEach(ref -> refs.add(ref.toJson())); return row;
    }
    public static LifecycleControlObservation decode(JsonNode raw, Function<ExactRef, PlanningReadReceipt> loadRead) {
        var row = StrictJson.object(raw, Set.of("schema", "after", "source", "session_id", "observer_schema", "actual", "before_status_ref", "independent_read_ref", "supporting_evidence"));
        StrictJson.require("xar.lifecycle-modal-control/v1".equals(StrictJson.text(row.get("schema"))) && row.get("supporting_evidence").isArray(), "exact modal-control schema and evidence array required");
        List<ExactRef> refs = new ArrayList<>(); row.get("supporting_evidence").forEach(ref -> refs.add(ExactRef.fromJson(ref)));
        return new LifecycleControlObservation(LifecycleIdentityCodec.decode(row.get("after")), G2Wire.source(row.get("source")), StrictJson.text(row.get("session_id")), StrictJson.text(row.get("observer_schema")),
                ProposalLifecycleCodec.values(row.get("actual")), loadRead.apply(ExactRef.fromJson(row.get("before_status_ref"))), loadRead.apply(ExactRef.fromJson(row.get("independent_read_ref"))), refs);
    }
}
