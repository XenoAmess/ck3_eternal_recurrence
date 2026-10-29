package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;

/** Complete current Python normalizer, including the five independent additive native sub-observers.
 * Full immutable original JSON preserves absent/null and every source occurrence; projections never fabricate defaults.
 */
public final class PlayerHolyOrderContext {
    private static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private static final BigInteger U32_MAX = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    public record ArmyRole(int associationIndex, long armyRegimentId, boolean available,
            boolean armyResolved, boolean unitResolved, Optional<Long> nativeCarmyId,
            Optional<Long> publicArmyId, Optional<Long> unitCarmyBacklink, Optional<Long> ownerCharacterId) {
        public ArmyRole {
            need(associationIndex >= 0 && armyRegimentId >= 0 && armyRegimentId <= 0xffff_ffffL, "actual role ordinal/full raw reference");
            Objects.requireNonNull(nativeCarmyId); Objects.requireNonNull(publicArmyId);
            Objects.requireNonNull(unitCarmyBacklink); Objects.requireNonNull(ownerCharacterId);
            for (Optional<Long> id : List.of(nativeCarmyId, publicArmyId, unitCarmyBacklink, ownerCharacterId))
                need(id.isEmpty() || id.orElseThrow() >= 0 && id.orElseThrow() <= 0xffff_ffffL, "actual raw Army role uint32 reference required");
            need(!available || !armyResolved || nativeCarmyId.isPresent() && publicArmyId.isPresent(), "available resolved role lacks Army/Unit references");
            need(!unitResolved || armyResolved && ownerCharacterId.isPresent(), "resolved Unit requires actual Army and owner");
        }
    }
    public record ArmyRoles(boolean available, boolean appliesToPlayer, List<ArmyRole> occurrences) {
        public ArmyRoles { occurrences = List.copyOf(occurrences); need(appliesToPlayer || occurrences.isEmpty(), "inapplicable actual roles cannot contain occurrences"); }
    }
    public record MilitaryTerms(boolean available, Optional<Boolean> canHire, Optional<Boolean> canAfford,
            Optional<List<BigInteger>> resourceCostsRaw, Optional<ArmyRoles> currentArmyRoles) {
        public MilitaryTerms {
            Objects.requireNonNull(canHire); Objects.requireNonNull(canAfford);
            resourceCostsRaw = Objects.requireNonNull(resourceCostsRaw).map(List::copyOf);
            Objects.requireNonNull(currentArmyRoles);
            need(resourceCostsRaw.isEmpty() || resourceCostsRaw.orElseThrow().size() == 10, "complete ten-resource native costs required");
            resourceCostsRaw.ifPresent(costs -> costs.forEach(cost -> range(cost, I64_MIN, I64_MAX)));
            need(!available || canHire.isPresent() && canAfford.isPresent() && resourceCostsRaw.isPresent(), "available final terms cannot lose native predicates/quote");
        }
    }
    public record Order(long holyOrderId, long riteId, boolean military, Optional<Long> founderId,
            Optional<Long> patronId, Optional<Long> employerId, List<Long> leasedTitleIds,
            Optional<MilitaryTerms> terms) {
        public Order {
            need(holyOrderId >= 0 && holyOrderId < 0xffff_ffffL && riteId >= 0 && riteId < 0xffff_ffffL, "full holy-order/rite references excluding none");
            Objects.requireNonNull(founderId); Objects.requireNonNull(patronId); Objects.requireNonNull(employerId);
            leasedTitleIds = List.copyOf(leasedTitleIds); Objects.requireNonNull(terms);
            need(military == terms.isPresent(), "military/nonmilitary terms branch differs");
            for (Optional<Long> id : List.of(founderId, patronId, employerId))
                need(id.isEmpty() || id.orElseThrow() >= 0 && id.orElseThrow() < 0xffff_ffffL, "full nullable character reference excluding none required");
            leasedTitleIds.forEach(id -> need(id != null && id >= 0 && id < 0xffff_ffffL, "full leased-title reference including legal zero required"));
        }
    }
    private final PlayerReligionContext.Build build;
    private final long actor;
    private final int dateRaw;
    private final BigInteger captureEpoch;
    private final boolean available;
    private final List<Order> orders;
    private final RawJson original;
    private PlayerHolyOrderContext(PlayerReligionContext.Build build, long actor, int dateRaw, BigInteger captureEpoch,
            boolean available, List<Order> orders, RawJson original) {
        this.build = build; this.actor = actor; this.dateRaw = dateRaw; this.captureEpoch = captureEpoch;
        this.available = available; this.orders = List.copyOf(orders); this.original = original;
    }
    public PlayerReligionContext.Build build() { return build; }
    public long actorCharacterId() { return actor; }
    public int dateRaw() { return dateRaw; }
    public BigInteger captureEpoch() { return captureEpoch; }
    public boolean available() { return available; }
    public List<Order> orders() { return orders; }
    public RawJson original() { return original; }
    public ObjectNode encode() { return object(StrictJson.parse(original.bytes(), StrictJson.EXPLICIT_MAX_BYTES)); }
    public void requireFrame(PlayerReligionContext.Build actual, BigInteger player, BigInteger date) {
        need(build == actual && BigInteger.valueOf(actor).equals(player) && BigInteger.valueOf(dateRaw).equals(date), "holy-order context crossed current build/player/date");
    }
    public static PlayerHolyOrderContext decode(JsonNode value) {
        ObjectNode n = object(value);
        PlayerReligionContext.Build build = PlayerReligionContext.Build.exact(text(n, "game_version"), text(n, "executable_sha256"));
        need(build.version().equals("1.20.0.3") || build.version().equals("1.20.0.4"), "holy-order producer only qualifies exact .3/.4 builds");
        equal(n, "schema", "ck3_" + build.version().replace(".", "") + "_player_holy_order_context_v1");
        long actor = full(field(n, "played_character_id")); int date = integer(field(n, "date_raw"), I32_MIN, I32_MAX).intValueExact();
        equal(n, "raw_scale", BigInteger.valueOf(100000)); yes(n, "read_only");
        boolean available = availability(n); BigInteger epoch = integer(field(n, "capture_epoch"), BigInteger.ONE, U64);
        List<Order> orders = new ArrayList<>();
        for (JsonNode raw : rows(field(n, "rows"))) {
            ObjectNode row = object(raw); long id = full(field(row, "holy_order_id")), rite = full(field(row, "rite_id"));
            boolean military = bool(row, "is_military"); Optional<Long> founder = nullableFull(row.get("founder_id"));
            Optional<Long> patron = nullableFull(row.get("patron_id")), employer = nullableFull(row.get("employer_id"));
            List<Long> leases = rows(field(row, "leased_title_ids")).stream().map(PlayerHolyOrderContext::full).toList();
            Optional<MilitaryTerms> terms;
            if (!military) { need(nullish(row.get("military_terms")), "nonmilitary order has military terms"); terms = Optional.empty(); }
            else terms = Optional.of(terms(object(field(row, "military_terms")), employer, actor));
            orders.add(new Order(id, rite, military, founder, patron, employer, leases, terms));
        }
        return new PlayerHolyOrderContext(build, actor, date, epoch, available, orders, raw(n));
    }
    private static MilitaryTerms terms(ObjectNode n, Optional<Long> employer, long actor) {
        boolean available = availability(n); equal(n, "resource_scale", BigInteger.valueOf(100000));
        Optional<Boolean> hire = nullableBool(n.get("can_hire")), afford = nullableBool(n.get("can_afford"));
        Optional<List<BigInteger>> costs = Optional.empty();
        if (!nullish(n.get("resource_costs_raw"))) {
            List<BigInteger> values = rows(n.get("resource_costs_raw")).stream().map(v -> integer(v, I64_MIN, I64_MAX)).toList();
            need(values.size() == 10, "ten actual native resource costs required"); costs = Optional.of(values);
        }
        need(!available || hire.isPresent() && afford.isPresent() && costs.isPresent(), "available holy-order final terms incomplete");
        reasonLiteral(n, "can_hire"); reasonLiteral(n, "can_afford");
        if (n.has("troop_strength")) {
            ObjectNode strength = object(n.get("troop_strength")); boolean a = availability(strength);
            if (a) integer(field(strength, "current_soldiers"), BigInteger.ZERO, I32_MAX);
            else need(nullish(strength.get("current_soldiers")), "unavailable troop strength contains soldiers");
        }
        if (n.has("hire_cost_context")) costContext(object(n.get("hire_cost_context")));
        Optional<ArmyRoles> roles = Optional.empty();
        if (n.has("current_reinforcement_v1")) roles = Optional.of(reinforcement(object(n.get("current_reinforcement_v1")), employer, actor));
        if (n.has("current_war_eligibility")) {
            ObjectNode war = object(n.get("current_war_eligibility")); boolean a = availability(war);
            Optional<Boolean> qualifies = nullableBool(war.get("qualifies")); need(!a || qualifies.isPresent(), "available holy-order war subgate incomplete");
            reasonLiteral(war, ""); need(!a || bool(war, "reasons_available"), "available war subgate lacks native reason sampling");
        }
        if (n.has("service_lifecycle")) {
            ObjectNode service = object(n.get("service_lifecycle")); boolean a = availability(service);
            boolean applies = bool(service, "applies_to_player");
            need(applies == employer.equals(Optional.of(actor)), "service lifecycle employer scope drift");
            for (String key : List.of("release_eligible", "associated_regiment_in_combat", "release_check_queued")) {
                Optional<Boolean> v = nullableBool(service.get(key));
                need(!a || !applies || v.isPresent(), "available service lifecycle lacks player predicate");
                need(applies || v.isEmpty(), "inapplicable service sampled player predicate");
            }
        }
        if (n.has("troop_association")) {
            ObjectNode association = object(n.get("troop_association")); boolean a = availability(association), applies = bool(association, "applies_to_player");
            need(applies == employer.equals(Optional.of(actor)), "troop association employer scope drift");
            List<JsonNode> members = rows(field(association, "rows")); need(applies || members.isEmpty(), "inapplicable troop association contains members");
            for (JsonNode raw : members) {
                ObjectNode member = object(raw); full(field(member, "regiment_id")); boolean ma = availability(member);
                for (String key : List.of("regiment_resolved", "native_carmy_resolved", "combat_resolved")) bool(member, key);
                nullableFull(member.get("native_carmy_id")); nullableFull(member.get("combat_id"));
                need(ma || !a, "available troop association has an unavailable member");
            }
        }
        return new MilitaryTerms(available, hire, afford, costs, roles);
    }
    private static void costContext(ObjectNode n) {
        boolean a = availability(n); bool(n, "order_title_resolved"); equal(n, "resource_scale", BigInteger.valueOf(100000));
        Optional<Long> title = nullableRawU32(n.get("order_title_id")); nullableRawU32(n.get("order_title_holder_id"));
        Optional<Boolean> holder = nullableBool(n.get("title_holder_is_player")), patron = nullableBool(n.get("patron_is_player"));
        Optional<Boolean> other = nullableBool(n.get("employed_by_other"));
        Optional<BigInteger> multiplier = nullableInteger(n.get("selected_patron_multiplier_raw"), I64_MIN, I64_MAX);
        Optional<String> branch = nullableText(n.get("cost_branch"));
        need(branch.isEmpty() || SetHolder.BRANCHES.contains(branch.orElseThrow()), "unknown native hire cost branch");
        if (!a) return;
        need(title.isPresent() && holder.isPresent() && branch.isPresent(), "available cost context incomplete");
        switch (branch.orElseThrow()) {
            case "title_holder_zero" -> need(holder.orElseThrow() && patron.isEmpty() && other.isEmpty() && multiplier.isEmpty(), "holder exemption sampled later native branches");
            case "ordinary" -> need(!holder.orElseThrow() && patron.equals(Optional.of(false)) && other.isEmpty() && multiplier.isEmpty(), "ordinary branch contains patron inputs");
            case "patron_hire", "patron_recall" -> need(!holder.orElseThrow() && patron.equals(Optional.of(true)) && other.isPresent() &&
                    other.orElseThrow() == branch.orElseThrow().equals("patron_recall") && multiplier.isPresent(), "selected patron branch incomplete");
            default -> throw new IllegalArgumentException("native cost branch unavailable");
        }
    }
    private static ArmyRoles reinforcement(ObjectNode n, Optional<Long> employer, long actor) {
        equal(n, "fraction_scale", BigInteger.valueOf(100000)); boolean a = availability(n);
        Optional<BigInteger> count = nullableInteger(n.get("source_count"), I32_MIN, I32_MAX);
        List<JsonNode> regiments = rows(field(n, "rows"));
        need(!a || count.isPresent() && count.orElseThrow().equals(BigInteger.valueOf(regiments.size())), "native persistent roster source count differs");
        for (int index = 0; index < regiments.size(); index++) {
            ObjectNode row = object(regiments.get(index)); exactOrdinal(row, "source_index", index); rawU32(field(row, "persistent_regiment_id"));
            boolean resolved = bool(row, "resolved"), ra = availability(row);
            Optional<BigInteger> owner = nullableInteger(row.get("owner_character_id"), BigInteger.ZERO, U32_MAX);
            Optional<BigInteger> fraction = nullableInteger(row.get("monthly_replenishment_fraction_raw"), I64_MIN, I64_MAX);
            Optional<BigInteger> months = nullableInteger(row.get("native_months_to_full"), I32_MIN, I32_MAX);
            need(!ra || !resolved || owner.isPresent() && fraction.isPresent() && months.isPresent(), "resolved available persistent input absent");
            List<JsonNode> chunks = rows(field(row, "chunks"));
            need(!resolved || !ra || chunks.size() == 7, "actual resolved persistent chunk count must be seven");
            need(resolved || chunks.isEmpty() && owner.isEmpty() && fraction.isEmpty() && months.isEmpty(), "unresolved native regiment contains actual inputs");
            for (int ordinal = 0; ordinal < chunks.size(); ordinal++) {
                ObjectNode chunk = object(chunks.get(ordinal)); exactOrdinal(chunk, "chunk_index", ordinal); boolean ca = availability(chunk);
                for (String key : List.of("maximum_soldiers", "current_soldiers", "native_chunk_index", "state_raw"))
                    requiredIfAvailable(chunk.get(key), ca, I32_MIN, I32_MAX);
                for (String key : List.of("persistent_regiment_id", "army_regiment_id"))
                    requiredIfAvailable(chunk.get(key), ca, BigInteger.ZERO, U32_MAX);
                requiredIfAvailable(chunk.get("pending_raw"), ca, BigInteger.ZERO, BigInteger.valueOf(255));
                for (String key : List.of("native_can_replenish", "native_chunk_can_replenish")) {
                    Optional<Boolean> predicate = nullableBool(chunk.get(key));
                    need(!ca || predicate.isPresent(), "available independent replenish predicate absent");
                }
            }
        }
        ObjectNode roles = object(field(n, "army_roles")); boolean rolesAvailable = availability(roles), applies = bool(roles, "applies_to_player");
        need(applies == employer.equals(Optional.of(actor)), "current Army role employer scope drift");
        List<JsonNode> source = rows(field(roles, "rows")); need(applies || source.isEmpty(), "inapplicable current roles contain occurrences");
        List<ArmyRole> observed = new ArrayList<>();
        for (int index = 0; index < source.size(); index++) {
            ObjectNode role = object(source.get(index)); exactOrdinal(role, "association_index", index);
            long regiment = rawU32(field(role, "army_regiment_id")); boolean ra = availability(role);
            boolean armyResolved = bool(role, "army_resolved"), unitResolved = bool(role, "unit_resolved");
            Optional<Long> carmy = nullableRawU32(role.get("native_carmy_id")), commander = nullableRawU32(role.get("commander_character_id"));
            Optional<Long> unit = nullableRawU32(role.get("public_army_id")), backlink = nullableRawU32(role.get("unit_carmy_backlink"));
            Optional<Long> owner = nullableRawU32(role.get("owner_character_id"));
            need(!ra || !armyResolved || carmy.isPresent() && commander.isPresent() && unit.isPresent(), "available actual Army role fields incomplete");
            need(!unitResolved || armyResolved && owner.isPresent(), "actual resolved Unit owner incomplete");
            observed.add(new ArmyRole(index, regiment, ra, armyResolved, unitResolved, carmy, unit, backlink, owner));
        }
        return new ArmyRoles(rolesAvailable, applies, observed);
    }
    private static final class SetHolder {
        private static final java.util.Set<String> BRANCHES = java.util.Set.of("title_holder_zero", "ordinary", "patron_hire", "patron_recall");
    }
    private static RawJson raw(JsonNode value) { return new RawJson(StrictJson.canonical(value, StrictJson.EXPLICIT_MAX_BYTES)); }
    private static boolean nullish(JsonNode n) { return n == null || n.isNull(); }
    private static BigInteger integer(JsonNode n, BigInteger low, BigInteger high) {
        need(n != null && n.isIntegralNumber(), "actual integral JSON native token required");
        return range(n.bigIntegerValue(), low, high);
    }
    private static long full(JsonNode n) { return integer(n, BigInteger.ZERO, U32_MAX.subtract(BigInteger.ONE)).longValueExact(); }
    private static long rawU32(JsonNode n) { return integer(n, BigInteger.ZERO, U32_MAX).longValueExact(); }
    private static Optional<Long> nullableFull(JsonNode n) { return nullish(n) ? Optional.empty() : Optional.of(full(n)); }
    private static Optional<Long> nullableRawU32(JsonNode n) { return nullish(n) ? Optional.empty() : Optional.of(rawU32(n)); }
    private static Optional<BigInteger> nullableInteger(JsonNode n, BigInteger low, BigInteger high) { return nullish(n) ? Optional.empty() : Optional.of(integer(n, low, high)); }
    private static Optional<Boolean> nullableBool(JsonNode n) { if (nullish(n)) return Optional.empty(); need(n.isBoolean(), "actual nullable boolean required"); return Optional.of(n.booleanValue()); }
    private static Optional<String> nullableText(JsonNode n) { if (nullish(n)) return Optional.empty(); need(n.isTextual(), "actual nullable native text required"); return Optional.of(n.textValue()); }
    private static List<JsonNode> rows(JsonNode n) {
        need(n != null && n.isArray() && n.size() <= 8192, "bounded actual native occurrence array required");
        List<JsonNode> out = new ArrayList<>(); n.forEach(out::add); return List.copyOf(out);
    }
    private static boolean availability(ObjectNode n) {
        boolean a = bool(n, "available"); JsonNode reason = n.get("unavailable_reason");
        need(a ? nullish(reason) : reason != null && reason.isTextual() && !reason.textValue().isEmpty(), "native availability lost its actual reason branch");
        return a;
    }
    private static void reasonLiteral(ObjectNode n, String prefix) {
        String join = prefix.isEmpty() ? "" : prefix + "_";
        boolean sampled = bool(n, join + "reasons_available"); JsonNode literal = n.get(join + "reason_literal");
        need(sampled ? literal != null && literal.isTextual() : nullish(literal), "native sampled reason literal differs from availability");
    }
    private static void exactOrdinal(ObjectNode n, String key, int expected) {
        need(integer(field(n, key), BigInteger.ZERO, I32_MAX).equals(BigInteger.valueOf(expected)), "source occurrence order drift");
    }
    private static void requiredIfAvailable(JsonNode n, boolean available, BigInteger low, BigInteger high) {
        need(!available || !nullish(n), "available current native input absent"); if (!nullish(n)) integer(n, low, high);
    }
}
