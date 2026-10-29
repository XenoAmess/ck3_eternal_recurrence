package org.xar.ck3.control.contracts;

/** The actual native Start/selected Stop action-id contract. This validates an identifier, never dispatch permission. */
public final class NativeSwayActionId {
    private NativeSwayActionId() { }
    public enum Kind { START, SELECTED_STOP }
    public static String require(String value, Kind kind) {
        java.util.Objects.requireNonNull(kind);
        StrictJson.require(value != null && value.length() <= 64 && value.startsWith(kind == Kind.START ? "sway-" : "stop-sway-")
                && value.matches("[A-Za-z0-9_-]+"), "bounded native Sway action ID");
        return value;
    }
}
