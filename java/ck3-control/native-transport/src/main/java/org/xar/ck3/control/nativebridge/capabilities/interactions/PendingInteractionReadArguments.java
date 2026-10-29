package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Root's collector delegates to the original single interaction argument codec. */
public final class PendingInteractionReadArguments {
    private PendingInteractionReadArguments() { }
    public static OpportunityJson.Obj current(InteractionModels.Context actual) {
        Objects.requireNonNull(actual);
        InteractionModels.PendingSummary pending=actual.controls().pending();
        InteractionJson.need(pending!=null,"actual current pending instance required");
        return InteractionArguments.app(InteractionArguments.body(actual).put("pending_id",pending.instance().value()));
    }
}
