package org.xar.ck3.control.application.advance;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

public final class PhysicalModalAvailability {
    private PhysicalModalAvailability() { }

    public static final String SCHEMA = "xar.java-physical-modal-availability/v1";

    public enum Kind {
        MISSING,
        EXPLICIT_NULL,
        OWNER_CACHE_UNAVAILABLE,
        OTHER_PRESENT
    }

    public static Kind classify(OpportunityJson.Obj semantic) {
        Objects.requireNonNull(semantic);
        if (!semantic.members().containsKey("top_exclusive_modal_choice_hint")) {
            return Kind.MISSING;
        }
        OpportunityJson.Value hint = semantic.get("top_exclusive_modal_choice_hint");
        if (hint == OpportunityJson.Nil.INSTANCE) {
            return Kind.EXPLICIT_NULL;
        }
        if (hint instanceof OpportunityJson.Obj obj && obj.members().size() == 5) {
            var members = obj.members();
            if (members.containsKey("status") && members.containsKey("source") && members.containsKey("owner_verified")
                    && members.containsKey("opaque_root_id") && members.containsKey("max_observation_age_ms")) {
                if (members.get("status") instanceof OpportunityJson.Text text && "unknown".equals(text.value())
                        && members.get("source") instanceof OpportunityJson.Text src && "owner_pump_cache_unavailable_or_expired".equals(src.value())
                        && members.get("owner_verified") instanceof OpportunityJson.Bool bool && !bool.value()
                        && members.get("opaque_root_id") == OpportunityJson.Nil.INSTANCE
                        && members.get("max_observation_age_ms") instanceof OpportunityJson.IntegerValue intVal
                        && BigInteger.valueOf(2000).equals(intVal.value())) {
                    return Kind.OWNER_CACHE_UNAVAILABLE;
                }
            }
        }
        return Kind.OTHER_PRESENT;
    }

    public static boolean unavailableProfileTransition(OpportunityJson.Obj before, OpportunityJson.Obj after) {
        Objects.requireNonNull(before);
        Objects.requireNonNull(after);
        Kind b = classify(before);
        Kind a = classify(after);
        if (!(b == Kind.MISSING && a == Kind.OWNER_CACHE_UNAVAILABLE) && !(b == Kind.OWNER_CACHE_UNAVAILABLE && a == Kind.MISSING)) {
            return false;
        }
        return Objects.equals(before.get("active_event"), after.get("active_event"))
                && Objects.equals(before.get("pending_character_interaction"), after.get("pending_character_interaction"))
                && Objects.equals(before.get("one_life_terminal_reason"), after.get("one_life_terminal_reason"));
    }
}