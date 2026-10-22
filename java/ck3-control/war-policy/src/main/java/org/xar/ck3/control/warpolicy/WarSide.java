package org.xar.ck3.control.warpolicy;

import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.contracts.ContractViolationException;

public enum WarSide {
    ATTACKER("attacker"), DEFENDER("defender");
    private final String wire;
    WarSide(String wire) { this.wire = wire; }
    public String wire() { return wire; }
    public static WarSide fromJson(JsonNode value) {
        for (WarSide side : values()) {
            if (WarJson.textEquals(value, side.wire)) { return side; }
        }
        throw new ContractViolationException("player_side must be attacker or defender");
    }
}
