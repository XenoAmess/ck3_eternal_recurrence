package org.xar.ck3.control.wave3.runtime.childexports;

import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Creation roles from the retained canonical chain, with the original export order. */
public enum ChildRole {
    OWNER("owner"), QUEUE("Queue"), MCP_APP("MCPApp");

    private final String wire;

    ChildRole(String wire) { this.wire = wire; }

    public String wire() { return wire; }

    public List<ChildRole> exportedRoles() {
        return switch (this) {
            case OWNER -> List.of(QUEUE, MCP_APP);
            case QUEUE -> List.of(MCP_APP);
            case MCP_APP -> List.of();
        };
    }

    public static ChildRole parse(String value) {
        StrictJson.text(value);
        for (ChildRole role : values()) {
            if (role.wire.equals(value)) { return role; }
        }
        throw new org.xar.ck3.control.contracts.ContractViolationException("exact canonical child role required");
    }
}
