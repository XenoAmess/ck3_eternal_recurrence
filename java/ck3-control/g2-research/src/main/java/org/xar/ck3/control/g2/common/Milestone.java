package org.xar.ck3.control.g2.common;

/** Fixed requirements identifiers; software evaluation never grants historical milestone credit. */
public enum Milestone {
    M0, M1, M2, M3, M4, M5, M6, M7;
    public String wire() { return "G2-" + name(); }
    public static Milestone fromWire(String value) {
        for (Milestone item : values()) if (item.wire().equals(value)) return item;
        throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST, "unknown G2 milestone");
    }
}
