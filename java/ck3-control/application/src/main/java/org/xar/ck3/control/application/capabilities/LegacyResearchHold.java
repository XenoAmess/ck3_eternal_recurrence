package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.application.capabilities.CapabilityJson.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Set;

/** The original H3937 physical-hostile/formal-war-cash hold; identity drift cannot release it. */
public final class LegacyResearchHold {
    private LegacyResearchHold() { }
    public static boolean active(Obj snapshot) {
        if (snapshot == null || !named(snapshot,"episode_run_id","native-29829-2bc2d599f7f9")) return false;
        Obj lifecycle = obj(snapshot.get("succession_lifecycle")).orElse(null), goal = obj(snapshot.get("campaign_goal")).orElse(null), actor = obj(snapshot.get("played_character")).orElse(null);
        boolean ordinary = named(lifecycle,"lifecycle","ordinary_campaign_succession") && goal != null && actor != null
                && eq(goal,"format_version",new IntegerValue(BigInteger.ONE)) && named(goal,"goal_key","dynasty_continuity")
                && equalField(goal,"campaign_id",snapshot,"episode_run_id") && equalField(goal,"current_character_id",actor,"character_id");
        return !ordinary;
    }
    public static boolean dateControl(String step) {
        if (step == null) return false;
        return Set.of("life-advance","life-advance-one-day","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5",
                "battle-decision-epoch-advance","battle-terminal-cruise","committed-route-sentinel-advance","war-objective-hold-sentinel-advance").contains(step)
                || List.of("advance-route-contact-horizon-v1-","advance-route-contact-window-v1-","battle-decision-epoch-advance-",
                "battle-terminal-cruise-","committed-route-sentinel-advance-","war-objective-hold-sentinel-advance-").stream().anyMatch(step::startsWith);
    }
    public static boolean armyMoveControl(String step) {
        return step != null && (step.equals("move-army") || step.startsWith("move-army-") || step.equals("order-active-combat-retreat-v1") || step.startsWith("order-active-combat-retreat-v1-"));
    }
}
