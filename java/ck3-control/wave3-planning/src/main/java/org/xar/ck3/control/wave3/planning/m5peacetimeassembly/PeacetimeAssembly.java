package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScopeCodec;
import org.xar.ck3.control.wave3.planning.pendingfamilyclaims.PendingFamilyClaims;
import org.xar.ck3.control.wave3.planning.pendingfamilyclaims.PendingFamilyClaimsCodec;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionReleaseCodec;

/** Complete final pure assembly of the original peaceful query. No I/O, reservation or action authority. */
public final class PeacetimeAssembly {
    public static final String REQUEST_SCHEMA = "xar.java.m5-peacetime-assembly.v2";
    public static final String HISTORICAL_REQUEST_SCHEMA = "xar.java.m5-peacetime-assembly.v1";
    public static final String SOURCE_SCHEMA = "xar.ck3.m5-formal-proposal-sources.v1";
    private static final BigInteger BUILDING_RESERVE = BigInteger.valueOf(20_000_000);
    private static final BigInteger GIFT_RESERVE = BigInteger.valueOf(10_000_000);
    private PeacetimeAssembly() { }

    public enum ConstructionStatus { SELECTED, NO_LEGAL_BUDGETED_BUILDING, PRIOR_RECEIPT_NOT_RELEASED }
    public enum FactionStatus { SELECTED, NO_LEGAL_CANDIDATE, CONSUMER_DISABLED, SAME_FRAME_ROOT_UNAVAILABLE, KNOWN_EMPTY }
    public record Construction(ConstructionStatus status, Obj originalQuery) {
        public Construction { Objects.requireNonNull(status); Objects.requireNonNull(originalQuery);
            require(PeacetimeAssembly.status(status).equals(originalQuery.get("status")), "construction status projection differs"); }
    }
    public record Faction(FactionStatus status, Obj originalCandidate) {
        public Faction { Objects.requireNonNull(status); Objects.requireNonNull(originalCandidate);
            require(PeacetimeAssembly.status(status).equals(originalCandidate.get("status")), "faction status projection differs"); }
    }
    public record Family(String status, Optional<Obj> selectedPlan, List<Obj> plans) {
        public Family {
            require(status != null && !status.isEmpty(), "family status required"); Objects.requireNonNull(selectedPlan); plans = List.copyOf(plans);
            if (selectedPlan.isPresent()) require(status.equals("selected") && !plans.isEmpty() && plans.size() <= 5
                    && plans.getFirst().equals(selectedPlan.orElseThrow()), "selected family proof must retain its first plan");
            else require(plans.isEmpty() && !status.equals("selected"), "unselected family cannot contain proposals");
        }
    }
    /** Original normalized ledger documents, including extensions and missing-vs-null semantics. */
    public record Ledgers(Obj construction, Obj faction, Obj family, Obj childDefault) {
        public Ledgers {
            normalizedConstruction(construction);
            normalizedFaction(faction);
            normalizedRelationship(family, "xar.ck3.first-heir-marriage-formal.v1");
            normalizedRelationship(childDefault, "xar.ck3.player-child-default-formal.v1");
        }
    }
    public record Inputs(PeacetimeScopeCodec.Request scope, Obj initialSnapshot, Obj baselinePlan,
                         Ledgers before, Ledgers after, ConstructionReleaseCodec.Request constructionRelease,
                         Construction construction, Faction faction, Family family) {
        public Inputs {
            Objects.requireNonNull(scope); Objects.requireNonNull(initialSnapshot); Objects.requireNonNull(baselinePlan);
            Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(constructionRelease);
            Objects.requireNonNull(construction); Objects.requireNonNull(faction); Objects.requireNonNull(family);
        }
    }
    public record Result(PeacetimeScope.StableObservation scope, PendingFamilyClaims.Claims occupied,
                         boolean familyPendingPresent, boolean childPendingPresent,
                         Construction construction, Faction faction, Family family) {
        public Result { Objects.requireNonNull(scope); Objects.requireNonNull(occupied); Objects.requireNonNull(construction); Objects.requireNonNull(faction); Objects.requireNonNull(family); }
        public boolean formalActionReady() { return false; }
    }

    public static Result compose(Inputs input) {
        PeacetimeScope.StableObservation scope = PeacetimeScope.verify(input.scope.before(), input.scope.expectedRevision(), input.scope.readback());
        require(new Text("one-life-turn-v1").equals(input.baselinePlan.get("policy"))
                && new Text("life-advance").equals(input.baselinePlan.get("selected_step")), "M5 peacetime source requires the ordinary life-advance baseline");
        checkLedgers(input.before, input.after);
        require(input.before.construction.get("pending") == Nil.INSTANCE, "M5 peacetime source has an unresolved construction action");
        require(input.before.faction.get("pending") == Nil.INSTANCE, "M5 peacetime source has an unresolved faction gift action");
        require(input.constructionRelease.frame().equals(scope.frame()), "construction release crossed assembly frame");
        ConstructionRelease.Decision release = ConstructionRelease.assess(input.constructionRelease.frame(), input.constructionRelease.applied(), input.constructionRelease.processObservation());
        require(release.blocksCandidate() == (input.construction.status == ConstructionStatus.PRIOR_RECEIPT_NOT_RELEASED), "construction source differs from actual prior receipt release");
        require(input.before.family.members().containsKey("pending") && input.before.childDefault.members().containsKey("pending"), "original normalized family/child ledger pending fields required");
        Value familyPending = input.before.family.get("pending"), childPending = input.before.childDefault.get("pending");
        PendingFamilyClaims.ActorEpisode current = new PendingFamilyClaims.ActorEpisode(scope.frame().player(), scope.frame().episodeRunId());
        PendingFamilyClaims.Claims family = PendingFamilyClaims.family(current, PendingFamilyClaimsCodec.decodeFamilyPending(OpportunityJson.encode(familyPending)));
        PendingFamilyClaims.Claims child = PendingFamilyClaims.childDefault(current, PendingFamilyClaimsCodec.decodeChildPending(OpportunityJson.encode(childPending)));
        PendingFamilyClaims.Claims occupied = new PendingFamilyClaims.Claims(union(family.allyCharacterIds(), child.allyCharacterIds()),
                union(family.characterIds(), child.characterIds()), union(family.commitmentKeys(), child.commitmentKeys()));
        if (input.construction.status != ConstructionStatus.PRIOR_RECEIPT_NOT_RELEASED) {
            Obj world = object(input.construction.originalQuery.get("world"), "construction world");
            require(integer(world.get("player_gold_raw"), "construction gold").equals(scope.observedGoldRaw()), "M5 peacetime construction gold crossed the planning frame");
        }
        if (input.faction.status == FactionStatus.SELECTED || input.faction.status == FactionStatus.NO_LEGAL_CANDIDATE) {
            Obj observation = object(input.faction.originalCandidate.get("observation"), "faction observation");
            require(integer(observation.get("player_gold_raw"), "faction gold").equals(scope.observedGoldRaw()), "M5 peacetime faction gold crossed the planning frame");
        }
        return new Result(scope, occupied, familyPending != Nil.INSTANCE, childPending != Nil.INSTANCE, input.construction, input.faction, input.family);
    }

    private static void checkLedgers(Ledgers before, Ledgers after) {
        require(before.construction.equals(after.construction), "M5 peacetime construction ledger changed during readback");
        require(before.faction.equals(after.faction), "M5 peacetime faction ledger changed during readback");
        require(before.family.equals(after.family), "M5 peacetime family ledger changed during readback");
        require(before.childDefault.equals(after.childDefault), "M5 peacetime child-default ledger changed during readback");
    }
    private static <T extends Comparable<? super T>> List<T> union(List<T> first, List<T> second) {
        TreeSet<T> items = new TreeSet<>(first); items.addAll(second); return List.copyOf(items);
    }
    private static void normalizedConstruction(Obj ledger) {
        ledgerSchema(ledger, "xar.ck3.construction_formal_pending_v1");
        nullableObject(ledger, "pending"); nullableObject(ledger, "applied");
        List<Value> receipts = new ArrayList<>(array(ledger.get("applied_prior"), "normalized applied_prior"));
        for (Value value : receipts) object(value, "prior construction receipt");
        if (ledger.get("applied") instanceof Obj applied) receipts.add(applied);
        if (receipts.size() > 1) {
            Set<String> requestIds = new HashSet<>();
            for (Value value : receipts) {
                String requestId = text(object(value, "construction receipt").get("action_request_id"), "construction action_request_id");
                require(requestIds.add(requestId), "construction applied receipt identity is unknown");
            }
        }
    }
    private static void normalizedFaction(Obj ledger) {
        ledgerSchema(ledger, "xar.ck3.faction_gift_pending_v1");
        require(ledger.members().keySet().equals(Set.of("schema", "format_version", "pending", "resolved_request_outcomes")), "exact normalized faction ledger fields required");
        require(BigInteger.ONE.equals(integer(ledger.get("format_version"), "faction ledger format_version")), "faction ledger format_version must be one");
        nullableObject(ledger, "pending");
        Obj resolved = object(ledger.get("resolved_request_outcomes"), "faction resolved_request_outcomes");
        resolved.members().forEach((requestId, value) -> {
            require(!requestId.isEmpty(), "resolved faction request identity required");
            require(new Text("applied").equals(value) || new Text("unchanged").equals(value), "faction resolved request outcomes are unknown");
        });
    }
    private static void normalizedRelationship(Obj ledger, String schema) {
        ledgerSchema(ledger, schema); nullableObject(ledger, "pending"); nullableObject(ledger, "resolved");
    }
    private static void ledgerSchema(Obj ledger, String schema) {
        Objects.requireNonNull(ledger);
        require(new Text(schema).equals(ledger.get("schema")), "normalized ledger schema required: " + schema);
    }
    private static void nullableObject(Obj ledger, String key) {
        Value value = ledger.get(key);
        require(value == Nil.INSTANCE || value instanceof Obj, "normalized ledger " + key + " must be present and object or null");
    }

    public static Obj source(Result result) {
        Obj verified = object(OpportunityJson.parse(PeacetimeScopeCodec.encode(result.scope)), "verified observation");
        Obj frame = object(verified.get("frame"), "verified frame");
        Obj claims = PendingFamilyClaimsCodec.toJson(result.occupied);
        Obj commitments = obj("frame", frame, "gold_raw", number(0), "pending_war_slots", number(0), "army_ids", new Arr(List.of()),
                "ally_character_ids", claims.get("ally_character_ids"), "character_ids", claims.get("character_ids"), "commitment_keys", claims.get("commitment_keys"));
        Map<String, Value> domains = new LinkedHashMap<>();
        if (result.construction.status == ConstructionStatus.SELECTED) domains.put("building", obj("query", result.construction.originalQuery));
        if (result.faction.status == FactionStatus.SELECTED) domains.put("diplomacy", obj("candidate", result.faction.originalCandidate));
        result.family.selectedPlan.ifPresent(plan -> domains.put("marriage", familySource(result.family)));
        Obj producer = obj("policy", new Text("g2-m5-peacetime-building-faction-family-source-v1"), "scope", new Text("peacetime_building_faction_and_opted_family"),
                "observed_player_gold_raw", new IntegerValue(result.scope.observedGoldRaw()), "domain_minimum_gold_reserves_raw", obj("building", new IntegerValue(BUILDING_RESERVE), "diplomacy", new IntegerValue(GIFT_RESERVE)),
                "observed_active_war_count", number(0), "observed_player_army_count", number(0), "construction_status", status(result.construction.status), "faction_status", status(result.faction.status),
                "incomplete_domains", new Arr(result.faction.status == FactionStatus.SAME_FRAME_ROOT_UNAVAILABLE ? List.of(new Text("diplomacy")) : List.of()),
                "family_status", new Text(result.family.status), "pending_family_commitment_source", result.familyPendingPresent ? new Text("formal_pending_ledger") : Nil.INSTANCE,
                "pending_child_default_commitment_source", result.childPendingPresent ? new Text("formal_pending_ledger") : Nil.INSTANCE,
                "pending_formal_ledgers_empty", new Bool(!result.familyPendingPresent && !result.childPendingPresent), "formal_action_ready", new Bool(false));
        return obj("schema", new Text(SOURCE_SCHEMA), "status", new Text("available"), "read_only", new Bool(true), "advertised", new Bool(false),
                "frame", frame, "existing_commitments", commitments, "gold_reserve_raw", number(0), "max_active_wars", number(0), "domains", new Obj(domains), "producer", producer);
    }
    public static byte[] assemble(byte[] request) { return OpportunityJson.encode(source(compose(PeacetimeAssemblyCodec.decode(request)))); }
    /** The domain container retains its existing outer contract; this nested message has its own strict v2 schema. */
    public static Obj familySource(Family family) {
        require(family.selectedPlan().isPresent(), "a compact family source requires the actual owning selected plan");
        var pool=M5FamilyCandidatePool.collect(family.selectedPlan().orElseThrow());
        require(pool.variants().stream().map(M5FamilyCandidatePool.Variant::plan).toList().equals(family.plans()),
                "family assembly alternatives differ from its complete actual owning pool");
        return M5FamilyCandidatePool.toJson(pool);
    }
    /** The real migrated collector consumes every included domain; malformed selected payloads remain RED. */
    public static byte[] assembleAndCollect(byte[] request) {
        Inputs input = PeacetimeAssemblyCodec.decode(request); Obj source = source(compose(input));
        return FormalProposalIntake.collect(OpportunityJson.encode(obj("schema", new Text(FormalProposalIntake.REQUEST_SCHEMA), "snapshot", input.initialSnapshot, "sources", source)));
    }
    private static Text status(Enum<?> value) { return new Text(value.name().toLowerCase(java.util.Locale.ROOT)); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    /** This narrow builder accepts only the sealed immutable JSON value domain, never arbitrary objects. */
    static Obj obj(Object... fields) {
        OpportunityJson.require(fields.length % 2 == 0, "paired fields required"); Map<String, Value> values = new LinkedHashMap<>();
        for (int index = 0; index < fields.length; index += 2) {
            OpportunityJson.require(fields[index] instanceof String && fields[index + 1] instanceof Value, "typed JSON fields required");
            String key = (String) fields[index]; OpportunityJson.require(values.put(key, (Value) fields[index + 1]) == null, "duplicate emitted field");
        }
        return new Obj(values);
    }

    /** Deliberate caller-controlled assembly predicates only; emitted-object invariants stay ordinary failures. */
    private static void require(boolean condition, String reason) {
        if (!condition) throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(reason);
    }
}
