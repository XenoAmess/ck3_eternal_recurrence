package org.xar.ck3.control.application.action;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Qualification plus the separately committed original Entry. Construction never grants completion or adoption. */
public record FixtureBusinessObservation(FixtureBusinessEvidence evidence,ExactRef entryPrepared,ExactRef entryReceipt) {
    public static final String SCHEMA=FixturePlan.PARENT_SCHEMA;
    public FixtureBusinessObservation {
        Objects.requireNonNull(evidence);Objects.requireNonNull(entryPrepared);Objects.requireNonNull(entryReceipt);
        StrictJson.require(entryPrepared.bytes()>0&&entryReceipt.bytes()>0&&!entryPrepared.equals(entryReceipt),
                "fixture completion requires separate actual Entry Prepared and Receipt originals");
    }
    public void validateParent(ActionCommand parent){evidence.validateParent(parent);}
    public void validateChildren(CompositeExecution execution,List<ActionReceipt> canonical){evidence.validateChildren(execution,canonical);}
    public List<ExactRef> references(){var refs=new ArrayList<>(evidence.references());refs.add(entryPrepared);refs.add(entryReceipt);return refs.stream().distinct().toList();}
}
