package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;

/** Existing explicit MCP reply callers use the same primitive and independent lifecycle verifier. */
public final class KnownPendingInteractionCommands {
    private KnownPendingInteractionCommands() { }
    private static Plan plan(Action action) {
        return new Plan(Classification.EXPLICIT_NATIVE_REPLY,"explicit-native-reply-v1",Optional.of(action),Optional.empty(),Optional.empty(),
                List.of(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),false);
    }
    public static ExpectedPostcondition expected(Context actualContext,Action explicitlyRequestedAction) {
        return KnownPendingInteractionPostcondition.expected(actualContext.before(),actualContext.source(),plan(explicitlyRequestedAction));
    }
    static ObjectNode arguments(ActionContext actual,Action action) {
        Context c=actual.frame();PendingSummary pending=c.controls().pending();
        need(pending!=null&&pending.autoAcceptNotification()==(action==Action.ACKNOWLEDGE),"explicit reply channel differs from actual pending");
        need(actual.expected().equals(expected(c,action)),"explicit reply caller must request the actual independent lifecycle contract");
        ObjectNode body=InteractionArguments.body(c).put("mutation_kind","PENDING_REPLY").put("pending_id",pending.instance().value())
                .put("accept",action==Action.ACCEPT).put("acknowledge",action==Action.ACKNOWLEDGE);
        ObjectNode artifact=body.putObject("known_pending_plan").put("explicit_native_reply",true).put("known_policy_handled",false)
                .put("semantic_decision_ready",false).put("native_ai_equivalent",false);
        artifact.set("java_policy_plan",KnownPendingInteractionPlanCodec.encode(plan(action)));
        ObjectNode summary=artifact.putObject("pending_character_interaction").put("instance_id",pending.instance().value())
                .put("sender_character_id",pending.sender().value()).put("auto_accept_notification",pending.autoAcceptNotification());
        summary.putObject("frame_binding").put("snapshot_id",c.before().frame().snapshotId()).put("public_revision",c.before().frame().revision())
                .put("native_revision",c.revision()).put("date_raw",c.date()).put("pending_interaction_id",pending.instance().value());
        return body;
    }
}
