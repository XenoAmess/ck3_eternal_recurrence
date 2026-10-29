package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly.*;

import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScopeCodec;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionReleaseCodec;

/** Exact assembly request, with declared projections for original SDK domain and ledger extensions. */
public final class PeacetimeAssemblyCodec {
    private PeacetimeAssemblyCodec() { }
    public static Inputs decode(byte[] raw) {
        return decode(raw,false);
    }
    /** Explicit frozen v1 reader. Production decode never probes or falls back to this shape. */
    public static Inputs decodeHistoricalV1(byte[] raw) {
        return decode(raw,true);
    }
    private static Inputs decode(byte[] raw,boolean historical) {
        Obj request = object(OpportunityJson.parse(raw), "assembly request");
        require(request.members().keySet().equals(Set.of("schema", "before", "expected_revision", "reader", "baseline_plan", "ledgers_before", "ledgers_after", "construction_process", "construction", "faction", "family")), "exact assembly request fields");
        require(new Text(historical?HISTORICAL_REQUEST_SCHEMA:REQUEST_SCHEMA).equals(request.get("schema")), "exact declared assembly schema required");
        Obj scopeRequest = obj("schema", new Text(PeacetimeScopeCodec.SCHEMA), "before", request.get("before"), "expected_revision", request.get("expected_revision"), "reader", request.get("reader"));
        PeacetimeScopeCodec.Request scope = PeacetimeScopeCodec.decode(OpportunityJson.encode(scopeRequest));
        Ledgers beforeLedgers = ledgers(request.get("ledgers_before"));
        Ledgers afterLedgers = ledgers(request.get("ledgers_after"));
        Obj scopeNode = object(OpportunityJson.parse(PeacetimeScopeCodec.encode(PeacetimeScope.requirePeacefulFrame(scope.before(), scope.expectedRevision()))), "scope observation");
        ConstructionReleaseCodec.Request release = ConstructionReleaseCodec.decode(OpportunityJson.encode(obj("schema", new Text(ConstructionReleaseCodec.SCHEMA),
                "frame", scopeNode.get("frame"), "applied", beforeLedgers.construction().get("applied"), "process_observation", request.get("construction_process"))));
        Obj construction = object(request.get("construction"), "construction result"), faction = object(request.get("faction"), "faction result");
        ConstructionStatus buildingStatus = switch (text(construction.get("status"), "construction status")) {
            case "selected" -> ConstructionStatus.SELECTED;
            case "no_legal_budgeted_building" -> ConstructionStatus.NO_LEGAL_BUDGETED_BUILDING;
            case "prior_receipt_not_released" -> ConstructionStatus.PRIOR_RECEIPT_NOT_RELEASED;
            default -> throw new IllegalArgumentException("M5 peacetime construction source is incomplete");
        };
        FactionStatus factionStatus = switch (text(faction.get("status"), "faction status")) {
            case "selected" -> FactionStatus.SELECTED; case "no_legal_candidate" -> FactionStatus.NO_LEGAL_CANDIDATE;
            case "consumer_disabled" -> FactionStatus.CONSUMER_DISABLED; case "known_empty" -> FactionStatus.KNOWN_EMPTY;
            case "same_frame_root_unavailable" -> FactionStatus.SAME_FRAME_ROOT_UNAVAILABLE;
            default -> throw new IllegalArgumentException("M5 peacetime faction source is incomplete");
        };
        Obj family = object(request.get("family"), "family stage");
        Family actual;
        if(historical) {
            require(family.members().keySet().equals(Set.of("status", "plan", "plans")), "exact historical v1 family stage fields");
            Value plan = family.get("plan"); Optional<Obj> selected = plan == Nil.INSTANCE ? Optional.empty() : Optional.of(object(plan, "selected family plan"));
            List<Obj> plans = array(family.get("plans"), "valued family plans").stream().map(value -> object(value, "family plan")).toList();
            actual=new Family(text(family.get("status"), "family status"),selected,plans);
        } else {
            require(family.members().keySet().equals(Set.of("status", "pool")), "exact compact v2 family stage fields");
            String status=text(family.get("status"),"family status");
            actual=family.get("pool")==Nil.INSTANCE?new Family(status,Optional.empty(),List.of()):M5FamilyCandidatePool.fromJson(object(family.get("pool"),"actual compact family pool")).family();
            require(actual.status().equals(status),"compact family status differs from actual pool");
        }
        return new Inputs(scope, object(request.get("before"), "before"), object(request.get("baseline_plan"), "baseline plan"),
                beforeLedgers, afterLedgers, release, new Construction(buildingStatus, construction),
                new Faction(factionStatus, faction), actual);
    }
    public static Obj familyStage(Family family) {
        return obj("status",new Text(family.status()),"pool",family.selectedPlan().isPresent()?PeacetimeAssembly.familySource(family):Nil.INSTANCE);
    }
    private static Ledgers ledgers(Value value) {
        Obj rows = object(value, "ledger readbacks");
        require(rows.members().keySet().equals(Set.of("construction", "faction", "family", "child_default")), "four actual ledger readback documents required");
        return new Ledgers(object(rows.get("construction"), "construction ledger"), object(rows.get("faction"), "faction ledger"),
                object(rows.get("family"), "family ledger"), object(rows.get("child_default"), "child default ledger"));
    }
}
