package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Single producer/consumer contract for the actual move child; references identify original evidence, never authority. */
public record ArmyRetreatMoveRequest(ActiveRetreatProposal.Order order, ExactRef previewBody, List<ExactRef> preflightReads) {
    public static final String SCHEMA = "xar.army-active-retreat-move/v1";
    public ArmyRetreatMoveRequest { Objects.requireNonNull(order); Objects.requireNonNull(previewBody); preflightReads = List.copyOf(preflightReads); StrictJson.require(preflightReads.size() == 2 && !preflightReads.getFirst().equals(preflightReads.getLast()), "original control and route requery receipts required"); }
    public Obj encode() {
        var n = StrictJson.object().put("schema", SCHEMA); n.set("order", OpportunityJson.toNode(ActiveRetreatState.order(order))); n.set("preview_body", previewBody.toJson());
        var refs = n.putArray("preflight_reads"); preflightReads.forEach(ref -> refs.add(ref.toJson())); return DriverJson.object(StrictJson.canonical(n), org.xar.ck3.control.application.action.ActionCommand.MAX_ARGUMENT_BYTES);
    }
    public static ArmyRetreatMoveRequest decode(Obj value) {
        var n = StrictJson.object(OpportunityJson.toNode(value), Set.of("schema", "order", "preview_body", "preflight_reads")); StrictJson.require(StrictJson.text(n.get("schema")).equals(SCHEMA), "exact retreat move schema required");
        StrictJson.require(n.get("preflight_reads").isArray(), "original preflight receipt list required"); var reads = new java.util.ArrayList<ExactRef>(); n.get("preflight_reads").forEach(ref -> reads.add(ExactRef.fromJson(ref)));
        return new ArmyRetreatMoveRequest(ActiveRetreatState.order(OpportunityJson.object(value.get("order"), "retreat order")), ExactRef.fromJson(n.get("preview_body")), reads);
    }
}
