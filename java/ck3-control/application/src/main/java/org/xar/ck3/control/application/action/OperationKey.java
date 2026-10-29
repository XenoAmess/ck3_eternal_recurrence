package org.xar.ck3.control.application.action;

import org.xar.ck3.control.contracts.StrictJson;

/** Exact original operation name; registration, capability and legality are separate guards. */
public record OperationKey(String value) {
    public OperationKey {
        StrictJson.require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,16383}"), "bounded native operation key required");
    }
}
