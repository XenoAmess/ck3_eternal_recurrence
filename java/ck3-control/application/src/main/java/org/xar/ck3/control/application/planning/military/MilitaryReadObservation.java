package org.xar.ck3.control.application.planning.military;

import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Original read result retained for the sole Driver history producer; it authorizes no world action. */
public record MilitaryReadObservation(Kind kind,Obj normalizedResult) {
    public enum Kind { ROUTE_PREVIEW,CONTACT_HORIZON }
    public MilitaryReadObservation {Objects.requireNonNull(kind);Objects.requireNonNull(normalizedResult);}
}
