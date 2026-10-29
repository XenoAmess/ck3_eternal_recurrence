package org.xar.ck3.control.wave2.planning.jointintake;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave2.planning.jointintake.IntakeWire.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.warcash.WarcashCodec;
import org.xar.ck3.control.wave2.finance.warcash.WarcashModel;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Budget;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Collection;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Domain;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Identity;

/** Actual collector's pre-dispatch closure. No reservation, native operation or material credit. */
public final class FormalProposalIntake {
    public static final String REQUEST_SCHEMA = "xar.java.m5-formal-intake-request.v2";
    public static final String HISTORICAL_REQUEST_SCHEMA = "xar.java.m5-formal-intake-request.v1";
    public static final String RESULT_SCHEMA = "xar.java.m5-formal-intake-analysis.v1";
    private FormalProposalIntake() { }

    public static byte[] collect(byte[] requestBody) {
        return collect(requestBody,false);
    }
    /** Explicit frozen input reader. The production entry never accepts or probes legacy expanded marriage sources. */
    public static byte[] collectHistoricalV1(byte[] requestBody) {
        return collect(requestBody,true);
    }
    private static byte[] collect(byte[] requestBody,boolean historical) {
        Obj request = object(OpportunityJson.parse(requestBody), "intake request");
        require(request.members().keySet().equals(Set.of("schema", "snapshot", "sources")), "exact intake request fields");
        equalsValue(request.get("schema"), new Text(historical?HISTORICAL_REQUEST_SCHEMA:REQUEST_SCHEMA), "exact declared intake request schema");
        Obj snapshot = object(request.get("snapshot"), "snapshot"), sources = object(request.get("sources"), "sources");
        require(bool(snapshot.get("paused"), "paused") && bool(snapshot.get("map_ready"), "map_ready"), "paused map required");
        Frame frame = frame(snapshot, false);
        equalsValue(sources.get("schema"), new Text("xar.ck3.m5-formal-proposal-sources.v1"), "source schema");
        equalsValue(sources.get("status"), new Text("available"), "source status"); equalsValue(sources.get("read_only"), new Bool(true), "read-only sources");
        equalsValue(sources.get("advertised"), new Bool(false), "unadvertised sources");
        require(frame.equals(frame(object(sources.get("frame"), "sources.frame"), true)), "sources crossed observed frame");
        Obj domains = object(sources.get("domains"), "source domains");
        Set<String> allowed = new HashSet<>(); for (Domain domain : Domain.values()) allowed.add(domain.name());
        require(allowed.containsAll(domains.members().keySet()), "unsupported domain source");
        List<Value> proposals = new ArrayList<>(); List<Identity> identities = new ArrayList<>();
        for (Domain domain : Domain.values()) {
            Value raw = domains.get(domain.name()); if (missingOrNull(raw)) continue;
            Obj source = object(raw, domain + " source");
            if(domain==Domain.marriage&&historical)require(source.members().keySet().equals(Set.of("plan"))
                    ||source.members().keySet().equals(Set.of("plan","plans")),"exact historical v1 marriage source fields");
            if (domain == Domain.marriage && !historical) {
                Set<String> marriageIds=new HashSet<>();
                for(Obj actualPlan:FamilyProposalPool.readSource(source).plans()) {
                    Obj proposal=FamilyProposalAdapter.adapt(frame,actualPlan);
                    require(marriageIds.add(text(proposal.get("candidate_id"),"candidate id")),"duplicate compact marriage candidate");
                    append(proposals,identities,domain,proposal);
                }
            } else if (domain == Domain.marriage && source.members().containsKey("plans")) {
                List<Value> plans = array(source.get("plans"), "marriage plans");
                require(plans.size() >= 1 && plans.size() <= 5 && plans.getFirst().equals(source.get("plan")), "selected five-row marriage source required");
                Set<String> marriageIds = new HashSet<>();
                for (Value value : plans) {
                    Obj proposal = FamilyProposalAdapter.adapt(frame, object(value, "marriage plan"));
                    require(marriageIds.add(text(proposal.get("candidate_id"), "candidate id")), "duplicate marriage candidate");
                    append(proposals, identities, domain, proposal);
                }
            } else {
                Obj proposal = switch (domain) {
                    case war -> WarProposalAdapter.adapt(frame, snapshot, source);
                    case council -> FormalDomainAdapters.council(frame, source);
                    case building -> FormalDomainAdapters.construction(frame, source);
                    case marriage -> FamilyProposalAdapter.adapt(frame, object(source.get("plan"), "marriage plan"));
                    case diplomacy -> FormalDomainAdapters.diplomacy(frame, source);
                    case lifestyle -> FormalDomainAdapters.lifestyle(frame, source);
                };
                append(proposals, identities, domain, proposal);
            }
        }
        Obj commitments = object(sources.get("existing_commitments"), "existing commitments");
        Budget budget = new Budget(nonnegative(sources.get("gold_reserve_raw"), "gold reserve"), nonnegative(sources.get("max_active_wars"), "war budget"));
        List<Value> activeWars = array(snapshot.get("active_wars"), "active wars");
        Value cashEvidence = activeWars.isEmpty() ? Nil.INSTANCE : verifyWarBudget(frame, snapshot, sources, commitments, budget, domains, activeWars);
        Obj selectorRequest = obj(f("snapshot", snapshot), f("proposals", new Arr(proposals)), f("commitments", commitments),
                f("gold_reserve_raw", number(budget.goldReserveRaw())), f("max_active_wars", number(budget.maxActiveWars())));
        // Reuse the existing selector, including all commitment/claim validation and stable ordering.
        // This is analytic execution only; the original dispatcher still owns its single reservation.
        Value analysis = OpportunityJson.parse(ObservedOpportunitySelector.select(OpportunityJson.encode(selectorRequest)));
        Collection collection = new Collection(frame, identities, budget);
        Obj result = obj(f("schema", new Text(RESULT_SCHEMA)), f("projection_not_original_collection_receipt", new Bool(true)), f("frame", frameNode(frame)),
                f("collected_domains", strings(collection.domains())), f("collected_candidate_ids", strings(collection.candidateIds())), f("selector_request", selectorRequest),
                f("analysis", analysis), f("resource_reservation_performed", new Bool(false)), f("formal_action_ready", new Bool(false)), f("selected_step", Nil.INSTANCE));
        if (!activeWars.isEmpty()) result = result.with("war_cash_resource", cashEvidence);
        if (sources.get("producer") instanceof Obj producer) {
            for (String domain : List.of("family", "faction")) if (producer.get(domain + "_status") instanceof Text status)
                result = result.with("producer_" + domain + "_status", status);
            if (producer.get("incomplete_domains") instanceof Arr incomplete) result = result.with("incomplete_domains", incomplete);
        }
        return OpportunityJson.encode(result);
    }
    /** Same actual formal adapter for one freshly revalidated owning plan, without rebuilding an expanded source wrapper. */
    public static String familyIdentity(Obj snapshot,Obj actualPlan) {
        require(bool(snapshot.get("paused"),"paused")&&bool(snapshot.get("map_ready"),"map_ready"),"paused map required");
        return text(FamilyProposalAdapter.adapt(frame(snapshot,false),actualPlan).get("candidate_id"),"family candidate identity");
    }
    private static void append(List<Value> proposals, List<Identity> identities, Domain domain, Obj proposal) {
        OpportunityJson.require(new Text(domain.name()).equals(proposal.get("domain")), "adapter domain mismatch");
        proposals.add(proposal); identities.add(new Identity(domain, text(proposal.get("candidate_id"), "candidate id")));
    }
    private static Obj verifyWarBudget(Frame frame, Obj snapshot, Obj sources, Obj commitments, Budget budget, Obj domains, List<Value> activeWars) {
        List<BigInteger> ids = new ArrayList<>();
        for (Value value : activeWars) ids.add(positive(object(value, "active war").get("war_id"), "active WarID"));
        require(new HashSet<>(ids).size() == ids.size(), "distinct active WarIDs required");
        Obj raw = object(sources.get("war_cash_resource"), "shared war cash");
        boolean aggregate = new Text(WarcashModel.AGGREGATE_SCHEMA).equals(raw.get("schema"));
        BigInteger treasury; BigInteger existing; BigInteger reserve;
        if (ids.size() != 1 || aggregate) {
            WarcashModel.AggregateReceipt receipt = WarcashCodec.verifyCompleteAggregate(OpportunityJson.toNode(raw), WarProposalAdapter.cashFrame(frame), ids);
            treasury = receipt.treasuryRaw(); existing = receipt.values().get(WarcashModel.Amount.PENDING).orElseThrow(); reserve = receipt.jointReserve().orElseThrow();
            WarcashModel.ClaimUnion occupied = receipt.occupied().orElseThrow();
            require(ids(commitments.get("army_ids"), "committed armies", true).containsAll(occupied.armyIds()), "missing active-war army occupation");
            require(ids(commitments.get("ally_character_ids"), "committed allies", false).containsAll(occupied.allyCharacterIds()), "missing active-war ally occupation");
            require(ids(commitments.get("character_ids"), "committed characters", false).containsAll(occupied.characterIds()), "missing active-war character occupation");
            List<Value> keys = array(commitments.get("commitment_keys"), "committed keys");
            require(keys.containsAll(occupied.commitmentKeys().stream().<Value>map(Text::new).toList()), "missing active-war key occupation");
        } else {
            WarcashModel.SingleReceipt receipt = WarcashCodec.verifyCompleteSingle(OpportunityJson.toNode(raw), WarProposalAdapter.cashFrame(frame), ids.getFirst());
            treasury = receipt.treasuryRaw(); existing = receipt.value(WarcashModel.Amount.PENDING).orElseThrow(); reserve = receipt.jointReserve().orElseThrow();
        }
        Obj current = object(snapshot.get("played_character_gold"), "treasury"); equalsValue(current.get("scale"), number(BigInteger.valueOf(100000)), "treasury scale");
        require(treasury.equals(integer(current.get("raw"), "treasury raw")), "shared war cash treasury differs from snapshot");
        require(integer(commitments.get("gold_raw"), "committed gold").compareTo(existing) >= 0 && budget.goldReserveRaw().compareTo(reserve) >= 0, "shared budget omits active-war cash");
        if (!missingOrNull(domains.get("war"))) {
            Obj observation = object(object(domains.get("war"), "war source").get("observation"), "war observation"); Value expected = raw;
            if (aggregate) {
                expected = null;
                for (Value value : array(raw.get("war_receipts"), "per-war receipts")) if (value instanceof Obj receipt && java.util.Objects.equals(receipt.get("war_id"), observation.get("war_id"))) { expected = receipt; break; }
            }
            require(expected != null && expected.equals(observation.get("war_cash_resource")), "war proposal cash differs from shared budget");
        }
        return raw;
    }

    // Local input aliases deliberately leave shared parser/encoder and internal result invariants unmarked.
    private static void require(boolean condition, String reason) { IntakeWire.domain(condition, reason); }
    private static Obj object(Value value, String name) { return IntakeWire.inputObject(value, name); }
    private static List<Value> array(Value value, String name) { return IntakeWire.inputArray(value, name); }
    private static String text(Value value, String name) { return IntakeWire.inputText(value, name); }
    private static BigInteger integer(Value value, String name) { return IntakeWire.inputInteger(value, name); }
    private static BigInteger nonnegative(Value value, String name) { return IntakeWire.inputNonnegative(value, name); }
    private static boolean bool(Value value, String name) { return IntakeWire.inputBool(value, name); }
}
