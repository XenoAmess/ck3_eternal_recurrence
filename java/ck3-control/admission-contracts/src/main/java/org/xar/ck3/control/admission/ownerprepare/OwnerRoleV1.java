package org.xar.ck3.control.admission.ownerprepare;

import org.xar.ck3.control.contracts.ContractViolationException;

/** The five production roles admitted by the v1 preparation input producer. */
public enum OwnerRoleV1 {
    SUPERVISOR("supervisor"),
    DISPLAY_OWNER("display_owner"),
    SDK_OWNER("sdk_owner"),
    FEEDER("feeder"),
    NATIVE_BUILD("native_build");

    private final String wireValue;

    OwnerRoleV1(String wireValue) {
        this.wireValue = wireValue;
    }

    public String wireValue() {
        return wireValue;
    }

    public static OwnerRoleV1 fromWire(String value) {
        for (OwnerRoleV1 role : values()) {
            if (role.wireValue.equals(value)) {
                return role;
            }
        }
        throw new ContractViolationException("exact admitted production role required");
    }
}
