package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave2.planning.jointintake.FamilyProposalPool;

/** Explicit in-memory migration/view of pinned historical test vectors. Never a production decoder or alias. */
final class M5CompactWireFixtures {
    private M5CompactWireFixtures() { }
    static ObjectNode currentAssembly(JsonNode historical) {
        Obj input = OpportunityJson.object(OpportunityJson.parse(SdkProjectionJson.encode(historical, 131_072)), "historical fixture");
        OpportunityJson.require(new Text(PeacetimeAssembly.HISTORICAL_REQUEST_SCHEMA).equals(input.get("schema")), "explicit v1 fixture required");
        Obj old = OpportunityJson.object(input.get("family"), "historical family stage");
        Value selected = old.get("plan");
        var family = new PeacetimeAssembly.Family(OpportunityJson.text(old.get("status"), "historical status"),
                selected == Nil.INSTANCE ? Optional.empty() : Optional.of(OpportunityJson.object(selected, "original selected plan")),
                OpportunityJson.array(old.get("plans"), "original explicit alternatives").stream()
                        .map(value -> OpportunityJson.object(value, "original alternative")).toList());
        Obj migrated = input.with("schema", new Text(PeacetimeAssembly.REQUEST_SCHEMA)).with("family", PeacetimeAssemblyCodec.familyStage(family));
        return (ObjectNode) OpportunityJson.toNode(migrated);
    }
    static JsonNode historicalSourceView(JsonNode current) {
        Obj source = OpportunityJson.object(OpportunityJson.parse(SdkProjectionJson.encode(current, 131_072)), "current source");
        Obj domains = OpportunityJson.object(source.get("domains"), "current domains");
        if (!domains.members().containsKey("marriage")) return current.deepCopy();
        var pool = FamilyProposalPool.fromJson(OpportunityJson.object(domains.get("marriage"), "current typed compact pool"));
        List<Value> expanded = pool.variants().stream().<Value>map(FamilyProposalPool.Variant::plan).toList();
        Obj historical = new Obj(java.util.Map.of("plan", pool.originalPlan(), "plans", new Arr(expanded)));
        return OpportunityJson.toNode(source.with("domains", domains.with("marriage", historical)));
    }
}
