package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete physical-order inventory DATA. Fixed references do not confer ownership or action authority. */
public record CurrentLivingInventoryQuerySource(long actorFullId, List<Artifact> artifacts,
        List<Slot> slots, Optional<Integer> weaponSlot, List<Reference> fixedReferences,
        boolean completeInventory, boolean sampledTwice) {
    public static final long NUMERIC_DENOMINATOR = 100_000L;
    public static final List<String> NUMERIC_KEYS = List.of("xalw_level", "xalw_xp_in_level",
            "xalw_pending_xp", "xalw_growth_sequence");

    public enum NumericState {
        ABSENT("absent"), PRESENT_EMPTY("present_empty"), OTHER_KIND("other_kind"), NUMERIC("numeric");
        private final String wire;
        NumericState(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static NumericState parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown Living numeric state");
        }
    }
    public enum ReferenceRole {
        FIXTURE_TARGET("fixture_target"), FIXTURE_MATERIAL_COMMON("fixture_material_common"),
        FIXTURE_MATERIAL_MASTERWORK("fixture_material_masterwork"), FIXTURE_MATERIAL_FAMED("fixture_material_famed"),
        FIXTURE_MATERIAL_ILLUSTRIOUS("fixture_material_illustrious"), SELECTED_ARTIFACT("selected_artifact");
        private final String wire;
        ReferenceRole(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static ReferenceRole parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown fixed Living reference role");
        }
    }
    public enum ReferenceState {
        ABSENT("absent"), PRESENT_EMPTY("present_empty"), WRONG_KIND("wrong_kind"), ARTIFACT("artifact");
        private final String wire;
        ReferenceState(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static ReferenceState parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown fixed Living reference state");
        }
    }
    public record Numeric(NumericState state, int scopeKind, Optional<Long> raw) {
        public Numeric {
            Objects.requireNonNull(state); Objects.requireNonNull(raw); requireKind(scopeKind);
            switch (state) {
                case ABSENT, PRESENT_EMPTY -> StrictJson.require(scopeKind == 0 && raw.isEmpty(), "Empty numeric reference shape differs");
                case OTHER_KIND -> StrictJson.require(scopeKind != 0 && scopeKind != 1 && raw.isEmpty(), "Non-numeric reference shape differs");
                case NUMERIC -> StrictJson.require(scopeKind == 1 && raw.isPresent(), "Actual numeric signed64 value required");
            }
        }
    }
    public record Artifact(long fullId, long ownerFullId, String typeKey, int rarityRaw,
            boolean equipped, List<Numeric> numeric) {
        public Artifact {
            CurrentLivingInventoryQuery.requireFullId(fullId); CurrentLivingInventoryQuery.requireFullId(ownerFullId);
            CurrentLivingInventoryQuery.requireActualText(typeKey); numeric = List.copyOf(Objects.requireNonNull(numeric));
            StrictJson.require(numeric.size() == 4, "Four physical-order Living numeric fields required");
        }
    }
    public record Slot(String key, Optional<Long> artifactFullId) {
        public Slot {
            CurrentLivingInventoryQuery.requireActualText(key); Objects.requireNonNull(artifactFullId);
            artifactFullId.ifPresent(CurrentLivingInventoryQuery::requireFullId);
        }
    }
    public record Reference(ReferenceRole role, ReferenceState state, int scopeKind,
            Optional<Long> artifactFullId) {
        public Reference {
            Objects.requireNonNull(role); Objects.requireNonNull(state); Objects.requireNonNull(artifactFullId); requireKind(scopeKind);
            artifactFullId.ifPresent(CurrentLivingInventoryQuery::requireFullId);
            switch (state) {
                case ABSENT, PRESENT_EMPTY -> StrictJson.require(scopeKind == 0 && artifactFullId.isEmpty(), "Empty fixed reference shape differs");
                case WRONG_KIND -> StrictJson.require(scopeKind != 0 && scopeKind != 36 && artifactFullId.isEmpty(), "Wrong-kind fixed reference shape differs");
                case ARTIFACT -> StrictJson.require(scopeKind == 36 && artifactFullId.isPresent(), "Actual artifact ScopeRef required");
            }
        }
    }
    public CurrentLivingInventoryQuerySource {
        CurrentLivingInventoryQuery.requireFullId(actorFullId);
        artifacts = List.copyOf(Objects.requireNonNull(artifacts)); slots = List.copyOf(Objects.requireNonNull(slots));
        fixedReferences = List.copyOf(Objects.requireNonNull(fixedReferences)); Objects.requireNonNull(weaponSlot);
        StrictJson.require(completeInventory && sampledTwice && artifacts.size() <= 128 && slots.size() <= 32,
                "Complete double-sampled bounded physical inventory required");
        StrictJson.require(fixedReferences.size() == ReferenceRole.values().length, "Exactly six unfiltered fixed references required");
        for (int i = 0; i < fixedReferences.size(); i++)
            StrictJson.require(fixedReferences.get(i).role() == ReferenceRole.values()[i], "Fixed reference role order differs");
        var ids = new HashSet<Long>();
        for (var artifact : artifacts)
            StrictJson.require(artifact.ownerFullId() == actorFullId && ids.add(artifact.fullId()), "Artifact ownership/full-ID uniqueness differs");
        var keys = new HashSet<String>(); Optional<Integer> actualWeapon = Optional.empty();
        for (int i = 0; i < slots.size(); i++) {
            var slot = slots.get(i); StrictJson.require(keys.add(slot.key()), "Duplicate physical slot key");
            if (slot.key().equals("weapon")) actualWeapon = Optional.of(i);
            if (slot.artifactFullId().isPresent()) StrictJson.require(ids.contains(slot.artifactFullId().orElseThrow()), "Equipped slot lacks complete owned artifact");
        }
        StrictJson.require(weaponSlot.equals(actualWeapon), "Observed weapon slot differs from complete physical slots");
        for (var artifact : artifacts) {
            boolean inSlot = slots.stream().anyMatch(slot -> slot.artifactFullId().equals(Optional.of(artifact.fullId())));
            StrictJson.require(inSlot == artifact.equipped(), "Artifact equipped DATA differs from physical slots");
        }
        // A consumed material's fixed ScopeRef may survive outside this inventory. No membership or action grant is inferred.
    }
    public long numericDenominator() { return NUMERIC_DENOMINATOR; }
    private static void requireKind(int kind) { StrictJson.require(kind >= 0 && kind <= 0xffff, "Actual uint16 ScopeKind required"); }
    private static int kind(JsonNode value) throws IOException {
        return NativeWire.integer(value, BigInteger.ZERO, BigInteger.valueOf(0xffff)).intValueExact();
    }
    private static Optional<Long> optionalId(JsonNode value) throws IOException {
        return value.isNull() ? Optional.empty() : Optional.of(CurrentLivingInventoryQuery.fullId(value));
    }
    private static long signed64(JsonNode value) throws IOException {
        String text = CurrentLivingInventoryQuery.actualText(value);
        if (!text.matches("0|-?[1-9][0-9]{0,18}")) throw new IOException("Canonical signed64 decimal string required");
        try { return Long.parseLong(text); }
        catch (NumberFormatException invalid) { throw new IOException("Signed64 overflow", invalid); }
    }
    private static JsonNode array(JsonNode value, int maximum) throws IOException {
        if (value == null || !value.isArray() || value.size() > maximum) throw new IOException("Complete bounded array required");
        return value;
    }
    public static CurrentLivingInventoryQuerySource decode(JsonNode value) throws IOException {
        try {
            var source = StrictJson.object(value, Set.of("schema", "actor_full_id", "numeric_denominator", "artifacts", "slots",
                    "weapon_slot", "fixed_references", "complete_inventory", "sampled_twice"));
            CurrentLivingInventoryQuery.identity(source, "schema", CurrentLivingInventoryQuery.SOURCE_SCHEMA);
            NativeWire.integer(source.get("numeric_denominator"), BigInteger.valueOf(NUMERIC_DENOMINATOR), BigInteger.valueOf(NUMERIC_DENOMINATOR));
            var artifacts = new ArrayList<Artifact>();
            for (var row : array(source.get("artifacts"), 128)) {
                var a = StrictJson.object(row, Set.of("full_id", "owner_full_id", "type_key", "rarity_raw", "equipped", "numeric"));
                var numeric = new ArrayList<Numeric>();
                for (var n : array(a.get("numeric"), 4)) {
                    var scalar = StrictJson.object(n, Set.of("state", "scope_kind", "raw"));
                    numeric.add(new Numeric(NumericState.parse(NativeWire.text(scalar.get("state"))), kind(scalar.get("scope_kind")),
                            scalar.get("raw").isNull() ? Optional.empty() : Optional.of(signed64(scalar.get("raw")))));
                }
                artifacts.add(new Artifact(CurrentLivingInventoryQuery.fullId(a.get("full_id")), CurrentLivingInventoryQuery.fullId(a.get("owner_full_id")),
                        CurrentLivingInventoryQuery.actualText(a.get("type_key")), CurrentLivingInventoryQuery.i32(a.get("rarity_raw")),
                        CurrentLivingInventoryQuery.bool(a, "equipped"), numeric));
            }
            var slots = new ArrayList<Slot>();
            for (var row : array(source.get("slots"), 32)) {
                var slot = StrictJson.object(row, Set.of("key", "artifact_full_id"));
                slots.add(new Slot(CurrentLivingInventoryQuery.actualText(slot.get("key")), optionalId(slot.get("artifact_full_id"))));
            }
            var refs = new ArrayList<Reference>();
            for (var row : array(source.get("fixed_references"), 6)) {
                var ref = StrictJson.object(row, Set.of("role", "state", "scope_kind", "artifact_full_id"));
                refs.add(new Reference(ReferenceRole.parse(NativeWire.text(ref.get("role"))), ReferenceState.parse(NativeWire.text(ref.get("state"))),
                        kind(ref.get("scope_kind")), optionalId(ref.get("artifact_full_id"))));
            }
            Optional<Integer> weapon = source.get("weapon_slot").isNull() ? Optional.empty()
                    : Optional.of(NativeWire.integer(source.get("weapon_slot"), BigInteger.ZERO, BigInteger.valueOf(31)).intValueExact());
            return new CurrentLivingInventoryQuerySource(CurrentLivingInventoryQuery.fullId(source.get("actor_full_id")), artifacts, slots, weapon, refs,
                    CurrentLivingInventoryQuery.bool(source, "complete_inventory"), CurrentLivingInventoryQuery.bool(source, "sampled_twice"));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact current Living inventory Source DATA", invalid);
        }
    }
    public ObjectNode encode() {
        var result = StrictJson.object().put("schema", CurrentLivingInventoryQuery.SOURCE_SCHEMA).put("actor_full_id", actorFullId)
                .put("numeric_denominator", NUMERIC_DENOMINATOR);
        var allArtifacts = result.putArray("artifacts");
        for (var artifact : artifacts) {
            var row = allArtifacts.addObject().put("full_id", artifact.fullId()).put("owner_full_id", artifact.ownerFullId())
                    .put("type_key", artifact.typeKey()).put("rarity_raw", artifact.rarityRaw()).put("equipped", artifact.equipped());
            var fields = row.putArray("numeric");
            for (var numeric : artifact.numeric()) {
                var field = fields.addObject().put("state", numeric.state().wire()).put("scope_kind", numeric.scopeKind());
                if (numeric.raw().isPresent()) field.put("raw", Long.toString(numeric.raw().orElseThrow())); else field.putNull("raw");
            }
        }
        var allSlots = result.putArray("slots");
        for (var slot : slots) {
            var row = allSlots.addObject().put("key", slot.key());
            if (slot.artifactFullId().isPresent()) row.put("artifact_full_id", slot.artifactFullId().orElseThrow()); else row.putNull("artifact_full_id");
        }
        if (weaponSlot.isPresent()) result.put("weapon_slot", weaponSlot.orElseThrow()); else result.putNull("weapon_slot");
        var allRefs = result.putArray("fixed_references");
        for (var reference : fixedReferences) {
            var row = allRefs.addObject().put("role", reference.role().wire()).put("state", reference.state().wire()).put("scope_kind", reference.scopeKind());
            if (reference.artifactFullId().isPresent()) row.put("artifact_full_id", reference.artifactFullId().orElseThrow()); else row.putNull("artifact_full_id");
        }
        return result.put("complete_inventory", completeInventory).put("sampled_twice", sampledTwice);
    }
}
