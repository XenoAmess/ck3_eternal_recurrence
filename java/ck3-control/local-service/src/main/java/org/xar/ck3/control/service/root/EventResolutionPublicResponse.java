package org.xar.ck3.control.service.root;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.PublicEventResolution;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Adds the original resolver's selection metadata to the existing canonical public event result.
 * Metadata never changes ACK, UNKNOWN, native material or the independent window-advancement verdict. */
public final class EventResolutionPublicResponse {
    private EventResolutionPublicResponse() { }
    public static final class Payload {
        private final RawJson original;
        private Payload(RawJson original) { this.original=Objects.requireNonNull(original); }
        public RawJson original() { return original; }
    }
    /** In the same original writer/archive result callback, after the single Root execution. */
    public static Payload capture(ActionReceipt actual,ActionPorts.OutcomeArchive sameArchive,Optional<RawJson> installedVerifiedMaterial) {
        Objects.requireNonNull(actual);
        var sameSelection=EventOptionPublicResponse.capture(actual,sameArchive,installedVerifiedMaterial);
        var row=PublicEventResolution.ordinaryEvent(actual.command().arguments());
        return append(sameSelection,row);
    }
    /** Shared metadata producer and the original public-result parser remain the only field contracts. */
    static Payload append(EventOptionPublicResponse.Payload sameSelection,OpportunityJson.Obj ordinaryEvent) {
        Objects.requireNonNull(sameSelection);Objects.requireNonNull(ordinaryEvent);
        var root=object(sameSelection.original());
        StrictJson.require(!root.members().containsKey("ordinary_events"),"original event result already declares resolver metadata");
        int instance=integer(root,"event_instance_id"),option=integer(root,"option_number");
        var exact=PublicEventResolution.validateOrdinaryEvent(ordinaryEvent,instance,option);
        return parse(new RawJson(DriverJson.encode(root.with("ordinary_events",new OpportunityJson.Arr(List.of(exact))))));
    }
    /** A wire round trip verifies shape and correspondence; it grants no archive, Game or replay authority. */
    public static Payload parse(RawJson original) {
        Objects.requireNonNull(original);var root=object(original);
        StrictJson.require(root.get("ordinary_events") instanceof OpportunityJson.Arr,"one original resolver event metadata row required");
        var rows=((OpportunityJson.Arr)root.get("ordinary_events")).items();
        StrictJson.require(rows.size()==1&&rows.getFirst() instanceof OpportunityJson.Obj,"exactly one original resolver event metadata row required");
        var fields=new LinkedHashMap<>(root.members());fields.remove("ordinary_events");
        var base=new RawJson(DriverJson.encode(new OpportunityJson.Obj(fields)));
        EventOptionPublicResponse.parse(base);
        PublicEventResolution.validateOrdinaryEvent((OpportunityJson.Obj)rows.getFirst(),integer(root,"event_instance_id"),integer(root,"option_number"));
        return new Payload(original);
    }
    private static OpportunityJson.Obj object(RawJson original) {
        StrictJson.require(original.bytes().length<=EventOptionPublicResponse.MAXIMUM_RESPONSE_BYTES,"bounded complete resolver response required");
        return DriverJson.object(original.bytes(),EventOptionPublicResponse.MAXIMUM_RESPONSE_BYTES);
    }
    private static int integer(OpportunityJson.Obj value,String field) { return OpportunityJson.integer(value.get(field),"actual resolver "+field).intValueExact(); }
}
