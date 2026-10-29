package org.xar.ck3.control.application.action;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;

/** Explicit registered frontend observer expectation; it is neither a proof nor a dispatch permit. */
public record FrontendExpectedPostcondition(FrontendIdentity before, G2Source source,
        String observerSchema, List<ExpectedValue> values) {
    public FrontendExpectedPostcondition {
        Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(observerSchema);
        StrictJson.require(before.machineId().equals(source.machineId()), "frontend expectation source machine drift");
        values = List.copyOf(values); StrictJson.require(!values.isEmpty(), "explicit frontend expected observations required");
        var fields = new HashSet<FieldKey>();
        for (ExpectedValue value : values) StrictJson.require(fields.add(value.field()), "duplicate frontend expected field");
    }
}
