package org.xar.ck3.control.application.action;

import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Stable, scoped decision identity. It neither reserves a sequence nor makes an existing action replayable. */
public final class ActionIds {
    private ActionIds() { }
    public static String forDecision(String sessionId, ObservationIdentity before, String decisionKey) {
        StrictJson.text(sessionId); StrictJson.text(decisionKey);
        var row = StrictJson.object(); row.put("session_id", sessionId); row.set("before", ProposalLifecycleCodec.observation(before)); row.put("decision_key", decisionKey);
        return "action-" + ActionCodec.sha256(ProposalLifecycleCodec.encodePayload(row));
    }
    public static String forDecision(String sessionId, LifecycleIdentity before, String decisionKey) {
        StrictJson.text(sessionId); StrictJson.text(decisionKey); java.util.Objects.requireNonNull(before);
        StrictJson.require(sessionId.equals(before.sessionId()), "lifecycle decision uses its actual held session");
        var row = StrictJson.object(); row.put("session_id", sessionId); row.set("before", LifecycleIdentityCodec.encode(before)); row.put("decision_key", decisionKey);
        return "action-" + ActionCodec.sha256(ProposalLifecycleCodec.encodePayload(row));
    }
    public static String child(String parentActionId, int ordinal) {
        StrictJson.text(parentActionId); StrictJson.require(ordinal >= 1 && ordinal <= 1024, "bounded composite child ordinal required");
        var row = StrictJson.object(); row.put("parent_action_id", parentActionId); row.put("ordinal", ordinal);
        return "child-" + ActionCodec.sha256(StrictJson.canonical(row));
    }
    /** Identifier formatting only. The actual root-installed operation family and native source permission still grant submission. */
    public static String child(String parentActionId, int ordinal, OperationKey operation) {
        java.util.Objects.requireNonNull(operation); String value = operation.value(); String prefix;
        String start = "submit-active-scheme-sway-v1-private-";
        if (value.startsWith(start)) {
            String target = value.substring(start.length());
            StrictJson.require(target.matches("[1-9][0-9]{0,9}") && new java.math.BigInteger(target).compareTo(new java.math.BigInteger("4294967295")) <= 0,
                    "canonical uint32 Sway target required for its reviewed native action identifier"); prefix = "sway-";
        } else if (value.equals("stop-active-scheme-sway-v1-private")) prefix = "stop-sway-";
        else return child(parentActionId, ordinal);
        StrictJson.text(parentActionId); StrictJson.require(ordinal >= 1 && ordinal <= 1024, "bounded composite child ordinal required");
        var row = StrictJson.object(); row.put("schema", "xar.sway-scoped-native-child-id/v1"); row.put("parent_action_id", parentActionId); row.put("ordinal", ordinal); row.put("operation", value);
        return prefix + ActionCodec.sha256(StrictJson.canonical(row)).substring(0, 64 - prefix.length());
    }
}
