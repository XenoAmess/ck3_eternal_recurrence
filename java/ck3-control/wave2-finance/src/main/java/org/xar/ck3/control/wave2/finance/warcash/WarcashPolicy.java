package org.xar.ck3.control.wave2.finance.warcash;

import static org.xar.ck3.control.wave2.finance.warcash.WarcashModel.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;

/** Read-only sourced cash aggregation. A complete result still grants no action qualification. */
public final class WarcashPolicy {
    private WarcashPolicy() { }
    private static void check(boolean condition, String reason) {
        if (!condition) { throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(reason); }
    }
    public static SingleReceipt observe(World world, Input input) {
        world.requireFrameReady();
        check(world.frame().equals(input.frame()) && world.warIds().stream().filter(input.warId()::equals).count() == 1,
            "one same-frame active WarID required");
        Map<String, String> missing = new LinkedHashMap<>();
        for (Amount amount : Amount.values()) {
            AmountFact fact = input.amounts().get(amount);
            if (fact instanceof MissingAmount) { missing.put(amount.wire(), amount.wire() + "_source_not_observed_same_frame"); }
            else if (fact instanceof Measured measured) {
                Observation observation = measured.observation();
                check(observation.frame().equals(world.frame()) && observation.warId().equals(input.warId()), "amount crossed same-frame WarID");
                observation.components().ifPresent(components -> {
                    world.requireActiveUniverse(); validateComponents(components, observation.raw(), world.frame(), input.warId(), world.warIds());
                });
            }
        }
        input.claims().ifPresent(claim -> check(claim.frame().equals(world.frame()) && claim.warId().equals(input.warId()), "claims crossed frame or war"));
        if (input.horizonDays().isEmpty()) { missing.put("horizon_days", "bounded_future_war_horizon_not_observed"); }
        if (input.assumptions().isEmpty()) { missing.put("future_bound_assumptions", "future_war_cost_bound_assumptions_not_observed"); }
        return new SingleReceipt(world.frame(), input.warId(), world.treasuryRaw(), input, missing);
    }
    public static SingleReceipt requireComplete(SingleReceipt receipt, Frame frame, BigInteger warId) {
        check(receipt.complete() && receipt.frame().equals(frame) && receipt.warId().equals(warId), "complete same-frame war cash required");
        for (Amount amount : Amount.values()) {
            check(receipt.input().amounts().get(amount) instanceof Measured, "missing amount is not measured zero");
        }
        return receipt;
    }
    public static AggregateReceipt aggregate(World world, List<SingleReceipt> supplied) {
        world.requireFrameReady(); world.requireActiveUniverse();
        List<BigInteger> warIds = world.warIds().stream().sorted().toList();
        Map<BigInteger, SingleReceipt> byWar = new LinkedHashMap<>();
        for (SingleReceipt receipt : supplied) {
            check(warIds.contains(receipt.warId()) && !byWar.containsKey(receipt.warId()), "duplicate or inactive receipt war");
            check(receipt.frame().equals(world.frame()) && receipt.treasuryRaw().equals(world.treasuryRaw()), "receipt crossed frame or treasury");
            byWar.put(receipt.warId(), receipt);
        }
        Map<String, String> missing = new LinkedHashMap<>();
        for (BigInteger warId : warIds) {
            SingleReceipt receipt = byWar.get(warId);
            if (receipt == null) { missing.put("war:" + warId + ":receipt", "active_war_receipt_not_observed"); }
            else { receipt.missing().forEach((key, value) -> missing.put("war:" + warId + ":" + key, value)); }
        }
        Map<Amount, Optional<BigInteger>> amounts = new EnumMap<>(Amount.class);
        Map<Amount, List<Component>> resources = new EnumMap<>(Amount.class);
        for (Amount amount : Amount.values()) {
            Map<ResourceKey, Component> unique = new TreeMap<>(); Map<ResourceKey, Set<BigInteger>> observedIn = new HashMap<>();
            boolean complete = byWar.size() == warIds.size();
            for (Map.Entry<BigInteger, SingleReceipt> entry : byWar.entrySet()) {
                AmountFact fact = entry.getValue().input().amounts().get(amount);
                if (!(fact instanceof Measured measured) || measured.observation().components().isEmpty()) {
                    missing.put("war:" + entry.getKey() + ":" + amount.wire() + ":resources", "explicit_cost_resource_attribution_not_observed");
                    complete = false; continue;
                }
                for (Component component : measured.observation().components().orElseThrow()) {
                    Component prior = unique.putIfAbsent(component.identity(), component);
                    check(prior == null || prior.equals(component), "shared war cash resource observations disagree");
                    observedIn.computeIfAbsent(component.identity(), key -> new HashSet<>()).add(entry.getKey());
                }
            }
            for (Map.Entry<ResourceKey, Component> entry : unique.entrySet()) {
                if (!observedIn.get(entry.getKey()).equals(new HashSet<>(entry.getValue().warIds()))) {
                    missing.put(amount.wire() + ":resource:" + entry.getKey().pythonTuple(), "cost_resource_missing_from_declared_war_receipt");
                    complete = false;
                }
            }
            List<Component> components = List.copyOf(unique.values()); resources.put(amount, components);
            amounts.put(amount, complete ? Optional.of(components.stream().map(Component::raw).reduce(BigInteger.ZERO, BigInteger::add)) : Optional.empty());
        }
        Set<Optional<BigInteger>> horizons = new HashSet<>(); byWar.values().forEach(row -> horizons.add(row.input().horizonDays()));
        Optional<BigInteger> horizon = horizons.size() == 1 && byWar.size() == warIds.size() ? horizons.iterator().next() : Optional.empty();
        if (horizon.isEmpty()) { missing.put("horizon_days", "common_bounded_future_war_horizon_not_observed"); }
        boolean claimsComplete = byWar.size() == warIds.size();
        Set<BigInteger> armies = new HashSet<>(), allies = new HashSet<>(), characters = new HashSet<>(); Set<String> commitments = new HashSet<>();
        for (Map.Entry<BigInteger, SingleReceipt> entry : byWar.entrySet()) {
            Optional<Claims> claim = entry.getValue().input().claims();
            if (claim.isEmpty()) { missing.put("war:" + entry.getKey() + ":resource_claims", "war_resource_occupation_not_observed"); claimsComplete = false; }
            else {
                armies.addAll(claim.orElseThrow().armyIds()); allies.addAll(claim.orElseThrow().allyCharacterIds());
                characters.addAll(claim.orElseThrow().characterIds()); commitments.addAll(claim.orElseThrow().commitmentKeys());
            }
        }
        Optional<ClaimUnion> occupied = claimsComplete ? Optional.of(new ClaimUnion(new ArrayList<>(armies), new ArrayList<>(allies),
            new ArrayList<>(characters), new ArrayList<>(commitments))) : Optional.empty();
        List<SingleReceipt> receipts = byWar.values().stream().sorted(java.util.Comparator.comparing(SingleReceipt::warId)).toList();
        return new AggregateReceipt(world.frame(), warIds, world.treasuryRaw(), amounts, resources, horizon, occupied, receipts, missing);
    }
    public static AggregateReceipt requireComplete(AggregateReceipt receipt, Frame frame, List<BigInteger> warIds) {
        check(receipt.complete() && receipt.frame().equals(frame) && receipt.warIds().equals(warIds.stream().sorted().toList()), "complete same-frame aggregate required");
        AggregateReceipt canonical = aggregate(new World(frame, true, true, receipt.treasuryRaw(), warIds), receipt.receipts());
        check(canonical.equals(receipt), "aggregate differs from its sourced original receipts");
        return receipt;
    }
    static void validateComponents(List<Component> components, BigInteger amount, Frame frame, BigInteger warId, List<BigInteger> active) {
        Set<ResourceKey> seen = new HashSet<>(); BigInteger sum = BigInteger.ZERO;
        for (Component component : components) {
            check(component.frame().equals(frame) && component.warIds().contains(warId) && active.containsAll(component.warIds()), "component frame or attribution differs");
            check(seen.add(component.identity()), "resource identity duplicated within amount"); sum = sum.add(component.raw());
        }
        check(sum.equals(amount), "amount differs from sourced component total");
    }
}
