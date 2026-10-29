package org.xar.ck3.control.application.lifecycle;

import java.util.Objects;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual result of the coordinator's existing borrowed writer Session, never an ACK or a caller flag. */
public record LifecycleCommit(WriterContracts.Prepared prepared, WriterContracts.Receipt receipt,
        java.util.List<WriterContracts.Pin> committedDocuments) {
    public LifecycleCommit {
        Objects.requireNonNull(prepared); Objects.requireNonNull(receipt); committedDocuments=java.util.List.copyOf(committedDocuments);
        var expected=prepared.reduced().toJson();expected.put("sequence",Math.addExact(prepared.predecessor().state().sequence(),1));
        expected.put("last_event_identity",prepared.request().identity());
        boolean exactEventHead=ContinuityJson.same(expected,receipt.head().toJson());
        boolean historical=false;
        if(receipt.disposition()==WriterContracts.Disposition.ALREADY_COMMITTED&&receipt.head().sequence()>=Math.addExact(prepared.predecessor().state().sequence(),1)) {
            var state=receipt.head().toJson();var registry=state.get(LifecycleContinuityAuthority.STATE_FIELD);
            var transitions=registry==null?null:registry.get("transitions");var actual=transitions==null?null:transitions.get(prepared.request().detailsObject().get("parent_action_id").textValue());
            historical=actual!=null&&ContinuityJson.same(actual,prepared.request().detailsObject());
        }
        String eventName=String.format(java.util.Locale.ROOT,"%08d.json",Math.addExact(prepared.predecessor().state().sequence(),1));
        StrictJson.require(prepared.request().identity().equals(receipt.eventIdentity())&&(exactEventHead||historical)
                &&receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE
                &&committedDocuments.stream().anyMatch(pin->java.nio.file.Path.of(pin.reference().path()).getFileName().toString().equals(eventName)),
                "actual original lifecycle commit and physical event documents required; historical receipts require sole-writer canonical verification");
    }
}
