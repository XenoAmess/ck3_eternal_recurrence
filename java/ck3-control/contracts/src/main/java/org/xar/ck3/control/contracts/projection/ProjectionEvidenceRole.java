package org.xar.ck3.control.contracts.projection;

import java.util.Locale;

/** Existing event-review evidence roles; a declaration does not grant native or action authority. */
public enum ProjectionEvidenceRole {
    EVENT_SOURCE_FACTS, UI_RECOVERY_LAUNCH, UI_RECOVERY_BEFORE, UI_RECOVERY_AFTER, UI_RECOVERY_LATER;
    public String wire() { return name().toLowerCase(Locale.ROOT).replace('_', '-'); }
    public static ProjectionEvidenceRole fromWire(String wire) {
        for (ProjectionEvidenceRole role : values()) { if (role.wire().equals(wire)) { return role; } }
        throw new IllegalArgumentException("unknown projection evidence role");
    }
}
