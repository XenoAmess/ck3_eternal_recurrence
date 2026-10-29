package org.xar.ck3.control.vanilla.schemesway;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Source;

/** Static exact-source lifecycle structure; displayed invalidation text is not a native terminal cause. */
public final class StockSwayLifecycleProfile {
    public static final long SOURCE_BYTES = 13634;
    public static final String SOURCE_SHA256 = "7d73696a96c28ff7daddc6b6fa08c3c4365d53a2b69a9aa70def0f00d18720b3";
    private StockSwayLifecycleProfile() { }
    public enum TriggerGroup { DEAD_ELSE_WAR, INDEPENDENT_DIPLOMATIC_RANGE }
    public enum Notification { TARGET_DEAD, OWNER_AT_WAR_WITH_TARGET, TARGET_OUTSIDE_DIPLOMATIC_RANGE }
    public record NotificationReference(TriggerGroup group, Notification notification, int firstLine, int lastLine) {
        public NotificationReference { Objects.requireNonNull(group); Objects.requireNonNull(notification); }
    }
    public record Profile(G2Source source, List<NotificationReference> invalidationNotifications) {
        public Profile { Objects.requireNonNull(source); invalidationNotifications = List.copyOf(invalidationNotifications); }
        public String phaseRollInput() { return "scope:scheme.scheme_success_chance"; }
        public List<String> phaseOutcomeActions() { return List.of("sway_success", "sway_failure"); }
        public String monthlyAction() { return "sway_ongoing"; }
        public int phaseFirstLine() { return 493; }
        public int phaseLastLine() { return 516; }
        public int monthlyFirstLine() { return 518; }
        public int monthlyLastLine() { return 525; }
        public boolean invalidationRangeBranchIsIndependent() { return true; }
        public boolean phaseSuccessIsFinalTerminal() { return false; }
        public boolean notificationProvesNativeEndCause() { return false; }
        public boolean evaluatesCurrentValidityOrRoll() { return false; }
    }
    public static Profile sourceBound(G2Source source) {
        Objects.requireNonNull(source);
        if (!source.exactBuild().equals("1.20.0.4") || source.sourceRef().bytes() != SOURCE_BYTES
                || !source.sourceRef().sha256().equals(SOURCE_SHA256)) {
            throw new IllegalArgumentException("exact .4 whole sway scheme source required");
        }
        return new Profile(source, List.of(
                new NotificationReference(TriggerGroup.DEAD_ELSE_WAR, Notification.TARGET_DEAD, 533, 544),
                new NotificationReference(TriggerGroup.DEAD_ELSE_WAR, Notification.OWNER_AT_WAR_WITH_TARGET, 545, 558),
                new NotificationReference(TriggerGroup.INDEPENDENT_DIPLOMATIC_RANGE, Notification.TARGET_OUTSIDE_DIPLOMATIC_RANGE, 560, 576)));
    }
}
