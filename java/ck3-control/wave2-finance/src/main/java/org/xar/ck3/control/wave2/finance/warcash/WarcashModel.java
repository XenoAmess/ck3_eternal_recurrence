package org.xar.ck3.control.wave2.finance.warcash;

import java.math.BigInteger;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Immutable measured facts. No JSON tree, native access, ledger, or estimate lives in this model. */
public final class WarcashModel {
    public static final int GOLD_SCALE = 100_000;
    public static final String SINGLE_SCHEMA = "xar.ck3.m5-active-war-cash-resource.v1";
    public static final String AGGREGATE_SCHEMA = "xar.ck3.m5-aggregate-active-war-cash-resource.v1";
    private WarcashModel() { }

    public enum Amount {
        PENDING("pending_war_cash_raw"), IMMEDIATE("immediate_war_action_cost_raw"),
        FUTURE("future_war_cost_upper_raw"), RISK("future_risk_budget_raw"), POLICY("policy_minimum_gold_reserve_raw");
        private final String wire;
        Amount(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Frame(BigInteger playedCharacterId, BigInteger nativeRevision, BigInteger dateRaw,
            String snapshotId, BigInteger revision, String episodeRunId) {
        public Frame {
            positive(playedCharacterId); positive(nativeRevision); nonnegative(dateRaw); positive(revision);
            text(snapshotId); text(episodeRunId);
        }
    }
    public record World(Frame frame, boolean paused, boolean mapReady, BigInteger treasuryRaw, List<BigInteger> warIds) {
        public World {
            Objects.requireNonNull(frame); Objects.requireNonNull(treasuryRaw);
            warIds = List.copyOf(warIds); warIds.forEach(WarcashModel::positive);
        }
        public void requireActiveUniverse() {
            if (warIds.isEmpty() || new HashSet<>(warIds).size() != warIds.size()) { throw new ProjectionDomainRejection("exact distinct active WarIDs required"); }
        }
        public void requireFrameReady() { if (!paused || !mapReady) { throw new ProjectionDomainRejection("paused map frame required"); } }
    }
    public record ResourceKey(String kind, String id, BigInteger ownerCharacterId) implements Comparable<ResourceKey> {
        public ResourceKey { text(kind); text(id); positive(ownerCharacterId); }
        @Override public int compareTo(ResourceKey other) {
            int order = compareText(kind, other.kind);
            if (order == 0) { order = compareText(id, other.id); }
            return order == 0 ? ownerCharacterId.compareTo(other.ownerCharacterId) : order;
        }
        public String pythonTuple() { return "(" + pythonRepr(kind) + ", " + pythonRepr(id) + ", " + ownerCharacterId + ")"; }
    }
    public record Component(ResourceKey identity, BigInteger raw, String source, Frame frame, List<BigInteger> warIds) {
        public Component {
            Objects.requireNonNull(identity); nonnegative(raw); text(source); Objects.requireNonNull(frame);
            warIds = List.copyOf(warIds); warIds.forEach(WarcashModel::positive);
            check(new HashSet<>(warIds).size() == warIds.size(), "component war attribution duplicated");
            warIds = warIds.stream().sorted().toList();
        }
    }
    public record Observation(BigInteger raw, String source, Frame frame, BigInteger warId,
            Optional<List<Component>> components) {
        public Observation {
            nonnegative(raw); text(source); Objects.requireNonNull(frame); positive(warId); Objects.requireNonNull(components);
            components = components.map(List::copyOf);
            if (components.isPresent()) {
                BigInteger sum = BigInteger.ZERO; HashSet<ResourceKey> identities = new HashSet<>();
                for (Component component : components.orElseThrow()) {
                    check(component.frame().equals(frame) && component.warIds().contains(warId), "component crossed frame or war");
                    check(identities.add(component.identity()), "component identity duplicated"); sum = sum.add(component.raw());
                }
                check(sum.equals(raw), "amount differs from component total");
            }
        }
    }
    public sealed interface AmountFact permits MissingAmount, Measured {
        Optional<BigInteger> raw();
    }
    public record MissingAmount() implements AmountFact {
        @Override public Optional<BigInteger> raw() { return Optional.empty(); }
    }
    public record Measured(Observation observation) implements AmountFact {
        public Measured { Objects.requireNonNull(observation); }
        @Override public Optional<BigInteger> raw() { return Optional.of(observation.raw()); }
    }
    public record Claims(String source, Frame frame, BigInteger warId, List<BigInteger> armyIds,
            List<BigInteger> allyCharacterIds, List<BigInteger> characterIds, List<String> commitmentKeys) {
        public Claims {
            text(source); Objects.requireNonNull(frame); positive(warId);
            armyIds = distinctNumbers(armyIds, false); allyCharacterIds = distinctNumbers(allyCharacterIds, true);
            characterIds = distinctNumbers(characterIds, true); commitmentKeys = distinctText(commitmentKeys);
        }
    }
    public record ClaimUnion(List<BigInteger> armyIds, List<BigInteger> allyCharacterIds,
            List<BigInteger> characterIds, List<String> commitmentKeys) {
        public ClaimUnion {
            armyIds = distinctNumbers(armyIds, false); allyCharacterIds = distinctNumbers(allyCharacterIds, true);
            characterIds = distinctNumbers(characterIds, true); commitmentKeys = distinctText(commitmentKeys);
        }
    }
    public record Input(Frame frame, BigInteger warId, Map<Amount, AmountFact> amounts,
            Optional<BigInteger> horizonDays, Optional<List<String>> assumptions, Optional<Claims> claims) {
        public Input {
            Objects.requireNonNull(frame); positive(warId); amounts = completeAmounts(amounts);
            Objects.requireNonNull(horizonDays); horizonDays.ifPresent(WarcashModel::positive);
            Objects.requireNonNull(assumptions); assumptions = assumptions.map(items -> {
                check(!items.isEmpty(), "known assumptions cannot be empty"); items.forEach(WarcashModel::text); return List.copyOf(items);
            });
            Objects.requireNonNull(claims);
            for (AmountFact fact : amounts.values()) {
                if (fact instanceof Measured measured) {
                    check(measured.observation().frame().equals(frame) && measured.observation().warId().equals(warId), "amount crossed input frame or war");
                }
            }
            claims.ifPresent(claim -> check(claim.frame().equals(frame) && claim.warId().equals(warId), "claims crossed input frame or war"));
        }
    }
    public record SingleReceipt(Frame frame, BigInteger warId, BigInteger treasuryRaw, Input input,
            Map<String, String> missing) {
        public SingleReceipt {
            Objects.requireNonNull(frame); positive(warId); Objects.requireNonNull(treasuryRaw); Objects.requireNonNull(input);
            missing = Map.copyOf(missing);
            check(frame.equals(input.frame()) && warId.equals(input.warId()), "single receipt input identity differs");
            if (missing.isEmpty()) {
                check(input.amounts().values().stream().allMatch(fact -> fact instanceof Measured)
                    && input.horizonDays().isPresent() && input.assumptions().isPresent(), "complete receipt cannot contain unknown facts");
            }
        }
        public boolean complete() { return missing.isEmpty(); }
        public Optional<BigInteger> value(Amount amount) { return input.amounts().get(amount).raw(); }
        public Optional<BigInteger> future() {
            return input.horizonDays().isPresent() && input.assumptions().isPresent() ? sum(value(Amount.FUTURE), value(Amount.RISK)) : Optional.empty();
        }
        public Optional<BigInteger> jointReserve() { return sum(future(), value(Amount.POLICY)); }
    }
    public record AggregateReceipt(Frame frame, List<BigInteger> warIds, BigInteger treasuryRaw,
            Map<Amount, Optional<BigInteger>> values, Map<Amount, List<Component>> resources,
            Optional<BigInteger> horizonDays, Optional<ClaimUnion> occupied,
            List<SingleReceipt> receipts, Map<String, String> missing) {
        public AggregateReceipt {
            Objects.requireNonNull(frame); warIds = distinctNumbers(warIds, true); Objects.requireNonNull(treasuryRaw);
            EnumMap<Amount, Optional<BigInteger>> numbers = new EnumMap<>(Amount.class);
            EnumMap<Amount, List<Component>> components = new EnumMap<>(Amount.class);
            for (Amount amount : Amount.values()) {
                Optional<BigInteger> value = Objects.requireNonNull(values.get(amount)); value.ifPresent(WarcashModel::nonnegative);
                numbers.put(amount, value); components.put(amount, List.copyOf(resources.get(amount)));
            }
            values = Map.copyOf(numbers); resources = Map.copyOf(components);
            Objects.requireNonNull(horizonDays); Objects.requireNonNull(occupied); receipts = List.copyOf(receipts); missing = Map.copyOf(missing);
            horizonDays.ifPresent(WarcashModel::positive);
            for (Amount amount : Amount.values()) {
                if (values.get(amount).isPresent()) {
                    check(values.get(amount).orElseThrow().equals(resources.get(amount).stream().map(Component::raw).reduce(BigInteger.ZERO, BigInteger::add)), "aggregate amount differs from resources");
                }
            }
            if (missing.isEmpty()) {
                check(values.values().stream().allMatch(Optional::isPresent) && horizonDays.isPresent() && occupied.isPresent()
                    && receipts.size() == warIds.size() && receipts.stream().allMatch(SingleReceipt::complete), "complete aggregate contains unknown facts");
            }
        }
        public boolean complete() { return missing.isEmpty(); }
        public Optional<BigInteger> future() {
            return horizonDays.isPresent() && receipts.stream().allMatch(row -> row.input().assumptions().isPresent())
                ? sum(values.get(Amount.FUTURE), values.get(Amount.RISK)) : Optional.empty();
        }
        public Optional<BigInteger> jointReserve() { return sum(future(), values.get(Amount.POLICY)); }
    }
    static Map<Amount, AmountFact> completeAmounts(Map<Amount, AmountFact> source) {
        check(source.size() == Amount.values().length, "all amount fact branches required");
        EnumMap<Amount, AmountFact> result = new EnumMap<>(Amount.class);
        for (Amount key : Amount.values()) { result.put(key, Objects.requireNonNull(source.get(key))); }
        return Map.copyOf(result);
    }
    static Optional<BigInteger> sum(Optional<BigInteger> first, Optional<BigInteger> second) {
        return first.isPresent() && second.isPresent() ? Optional.of(first.orElseThrow().add(second.orElseThrow())) : Optional.empty();
    }
    static List<BigInteger> distinctNumbers(List<BigInteger> source, boolean requirePositive) {
        List<BigInteger> result = List.copyOf(source);
        result.forEach(requirePositive ? WarcashModel::positive : WarcashModel::nonnegative);
        check(new HashSet<>(result).size() == result.size(), "identity claims duplicated"); return result.stream().sorted().toList();
    }
    static List<String> distinctText(List<String> source) {
        List<String> result = List.copyOf(source); result.forEach(WarcashModel::text);
        check(new HashSet<>(result).size() == result.size(), "text claims duplicated"); return result.stream().sorted(WarcashModel::compareText).toList();
    }
    static int compareText(String first, String second) {
        int a = 0, b = 0;
        while (a < first.length() && b < second.length()) {
            int x = first.codePointAt(a), y = second.codePointAt(b); if (x != y) { return Integer.compare(x, y); }
            a += Character.charCount(x); b += Character.charCount(y);
        }
        return Integer.compare(first.length() - a, second.length() - b);
    }
    static String pythonRepr(String text) {
        char quote = text.indexOf('\'') >= 0 && text.indexOf('"') < 0 ? '"' : '\'';
        StringBuilder out = new StringBuilder().append(quote);
        text.codePoints().forEach(code -> {
            if (code == quote || code == '\\') { out.append('\\').appendCodePoint(code); }
            else if (code == '\n') { out.append("\\n"); } else if (code == '\r') { out.append("\\r"); }
            else if (code == '\t') { out.append("\\t"); }
            else {
                int type = Character.getType(code);
                boolean printable = code == 32 || !(Character.isISOControl(code) || type == Character.FORMAT
                    || type == Character.LINE_SEPARATOR || type == Character.PARAGRAPH_SEPARATOR || type == Character.SPACE_SEPARATOR
                    || type == Character.UNASSIGNED || type == Character.PRIVATE_USE || type == Character.SURROGATE);
                if (printable) { out.appendCodePoint(code); }
                else if (code <= 255) { out.append(String.format(java.util.Locale.ROOT, "\\x%02x", code)); }
                else if (code <= 65535) { out.append(String.format(java.util.Locale.ROOT, "\\u%04x", code)); }
                else { out.append(String.format(java.util.Locale.ROOT, "\\U%08x", code)); }
            }
        });
        return out.append(quote).toString();
    }
    static void text(String value) {
        check(value != null && !value.isEmpty() && value.codePointCount(0, value.length()) <= 32768, "nonempty bounded sourced text required");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (Character.isHighSurrogate(c)) { check(i + 1 < value.length() && Character.isLowSurrogate(value.charAt(i + 1)), "unpaired surrogate"); i++; }
            else { check(!Character.isLowSurrogate(c), "unpaired surrogate"); }
        }
    }
    static void positive(BigInteger value) { check(value != null && value.signum() > 0, "positive exact identity required"); }
    static void nonnegative(BigInteger value) { check(value != null && value.signum() >= 0, "nonnegative raw amount or identity required"); }
    static void check(boolean condition, String reason) { if (!condition) { throw new IllegalArgumentException(reason); } }
}
