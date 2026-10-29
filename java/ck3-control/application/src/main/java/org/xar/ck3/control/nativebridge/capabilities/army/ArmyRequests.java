package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Public selections are values, never executable literal strings or caller-supplied JSON. */
public final class ArmyRequests {
    private ArmyRequests() { }
    public record Empty() { }
    public record War(FullId war) { public War { Objects.requireNonNull(war); } }
    public record Unit(PublicUnitId unit) { public Unit { Objects.requireNonNull(unit); } }
    public record Combat(FullId combat) { public Combat { Objects.requireNonNull(combat); } }
    public record Truce(PositiveId toward) { public Truce { Objects.requireNonNull(toward); } }
    public record Declaration(DeclarationId declaration) { public Declaration { Objects.requireNonNull(declaration); } }
    public record Move(PublicUnitId army, PositiveId target) { public Move { Objects.requireNonNull(army); Objects.requireNonNull(target); } }
    public record Siege(FullId siege) { public Siege { Objects.requireNonNull(siege); } }
    public record Hire(HireId reference) { public Hire { Objects.requireNonNull(reference); } }
    public record Commander(PublicUnitId army, Optional<PositiveId> target) { public Commander { Objects.requireNonNull(army); target = Objects.requireNonNull(target); } }
    public record AssignCommander(PublicUnitId army, PositiveId commander) { public AssignCommander { Objects.requireNonNull(army); Objects.requireNonNull(commander); } }
    public record Sampling(boolean enabled) { }
    public record CallAlly(FullId war, FullId recipient, List<Long> expectedSendCostRaw) {
        public CallAlly { Objects.requireNonNull(war); Objects.requireNonNull(recipient); expectedSendCostRaw = List.copyOf(expectedSendCostRaw); require(expectedSendCostRaw.size() == 10, "all ten current native cost slots required"); }
    }
    public record CreateMaa(int typeIndex, String actionId) {
        public CreateMaa { require(typeIndex >= 0, "observed registry index required"); require(actionId != null && !actionId.isEmpty() && actionId.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 63, "native action identity is at most 63 UTF-8 bytes"); }
    }
    public enum StrengthProfile { ORDINARY_CORE_V1, OBSERVED_HISTORY_FULL_V1 }
    public enum RefillEntryMode { OBSERVED_PREPARED, FIXED_CHUNK0_PREPARE }
    public record Strengths(List<PublicUnitId> armies, StrengthProfile profile, RefillEntryMode refill, RefillEntryMode besieging) {
        public Strengths { armies = distinct(armies, 1, 64, "selected armies"); Objects.requireNonNull(profile); Objects.requireNonNull(refill); Objects.requireNonNull(besieging); }
    }
    public record Terminal(Optional<FullId> priorCombat, Optional<PublicUnitId> subject, Optional<UInt64> afterSequence, List<FullId> characters) {
        public Terminal { priorCombat = Objects.requireNonNull(priorCombat); subject = Objects.requireNonNull(subject); afterSequence = Objects.requireNonNull(afterSequence); characters = distinct(characters, 0, 64, "terminal characters"); require(characters.stream().allMatch(character -> character.value() > 0), "requested terminal CharacterID must be positive"); require(priorCombat.isPresent() == subject.isPresent(), "terminal context pair required"); require(priorCombat.isPresent() || !characters.isEmpty() && afterSequence.isEmpty(), "character-only terminal read requires characters and no cursor"); afterSequence.ifPresent(value -> require(value.value().signum() > 0, "positive terminal cursor required")); }
    }
    public record CombatInputs(PositiveId target, Optional<PositiveId> attackerEntry, List<PublicUnitId> attackers, List<PublicUnitId> defenders, Optional<Integer> constructorAdjacencyKindRaw) {
        public CombatInputs { Objects.requireNonNull(target); attackerEntry = Objects.requireNonNull(attackerEntry); attackers = distinct(attackers, 1, 64, "attacker scope"); defenders = distinct(defenders, 1, 64, "defender scope"); constructorAdjacencyKindRaw = Objects.requireNonNull(constructorAdjacencyKindRaw); require(attackers.stream().noneMatch(defenders::contains), "combat sides cannot overlap"); require(attackerEntry.isPresent() || constructorAdjacencyKindRaw.equals(Optional.of(0)), "constructor-zero contact must be explicit"); require(attackerEntry.isEmpty() || constructorAdjacencyKindRaw.isEmpty(), "explicit entry cannot also claim constructor-zero"); }
    }
    public record WarEntry(List<PositiveId> targets) { public WarEntry { targets = distinct(targets, 1, 1, "production war-entry target"); } }
    public record Knight(PublicUnitId subject, PositiveId character, PositiveId regiment, PositiveId player, int war, PositiveId nativeArmy, PositiveId combat, PositiveId province, long dateRaw, UInt64 nativeRevision, String snapshotId) {
        public Knight { Objects.requireNonNull(subject); Objects.requireNonNull(character); Objects.requireNonNull(regiment); Objects.requireNonNull(player); Objects.requireNonNull(nativeArmy); Objects.requireNonNull(combat); Objects.requireNonNull(province); Objects.requireNonNull(nativeRevision); require(war >= 0 && dateRaw >= 0 && snapshotId != null && snapshotId.equals("native:" + nativeRevision.decimal()), "exact current-knight frame required"); }
    }
    public record RetreatOrder(PublicUnitId selected, FullId combat, Side side, Scope scope, PositiveId target, String candidateToken) {
        public RetreatOrder { Objects.requireNonNull(selected); Objects.requireNonNull(combat); Objects.requireNonNull(side); Objects.requireNonNull(scope); Objects.requireNonNull(target); require(candidateToken != null && candidateToken.matches("[A-Za-z0-9_-]{32,128}"), "original preview token required"); }
    }
}
