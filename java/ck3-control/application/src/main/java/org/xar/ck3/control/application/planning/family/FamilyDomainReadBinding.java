package org.xar.ck3.control.application.planning.family;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** A full original domain body at one real canonical-history position. Construction grants no read qualification. */
public record FamilyDomainReadBinding(Slot slot,ExactRef body,long sequence,String headDigest) {
    public enum Selection { PENDING("pending"), RESOLVED("resolved");
        private final String field;Selection(String field){this.field=field;}public String field(){return field;}
    }
    public FamilyDomainReadBinding {
        Objects.requireNonNull(slot);Objects.requireNonNull(body);StrictJson.safe(sequence,0);
        StrictJson.require(Set.of(Slot.FAMILY,Slot.CHILD_MATRILINEAL,Slot.DEFAULT_MARRIAGE).contains(slot)
                && body.bytes()>0 && headDigest!=null && headDigest.matches("[0-9a-f]{64}"),"exact original family body/history binding");
    }
    public Obj toJson() {
        return new Obj(Map.of("slot",new Text(slot.name()),"body",OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(body.toJson())),"body"),
                "sequence",new IntegerValue(BigInteger.valueOf(sequence)),"head_digest",new Text(headDigest)));
    }
    public static FamilyDomainReadBinding fromJson(Obj value) {
        StrictJson.require(value.members().keySet().equals(Set.of("slot","body","sequence","head_digest")),"closed original_domain fields");
        return new FamilyDomainReadBinding(Slot.valueOf(OpportunityJson.text(value.get("slot"),"slot")),
                ExactRef.fromJson(OpportunityJson.toNode(value.get("body"))),OpportunityJson.integer(value.get("sequence"),"sequence").longValueExact(),
                OpportunityJson.text(value.get("head_digest"),"head_digest"));
    }
    /** Root owns the concrete original writer, registered full bodies and historical-state verifier. */
    public interface Authority {
        FamilyDomainReadBinding current(Session same,Slot slot,Selection selection,Obj selected)throws IOException;
        Obj verifyCurrent(PlanningReadRequest request,FamilyDomainReadBinding binding,Selection selection,Obj selected)throws IOException;
        Obj verifyOriginal(PlanningReadReceipt receipt,FamilyDomainReadBinding binding,Selection selection,Obj selected)throws IOException;
    }
}
