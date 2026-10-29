package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Closed Army extension inventory. A registered typed Java normalizer is mandatory; source declarations grant no implementation. */
public final class ArmyStrengthsFamilies {
    private ArmyStrengthsFamilies() { }
    public enum Key {
        REGIMENT_REPLENISHMENT, REGIMENT_STRENGTHS, REGIMENT_REPLENISHMENT_RECORDS_V1,
        FIXED_CHUNK0_PREPARATION_INPUTS_V1, CURRENT_MOVEMENT_PROGRESS, ARMY_UPDATE_CLOCK_V1,
        NATIVE_OWNER_RECALL_INPUTS_V1, NATIVE_MAA_RECRUITMENT_INPUTS_V1, OWNED_REGIMENTS_V1,
        LOSS_APPLICATION_INPUTS_V1, MONTHLY_LOSS_BUDGET_INPUTS_V1, MONTHLY_CALLER_EFFECT_INPUTS_V1,
        MONTHLY_DAILY_QUEUE_INPUTS_V1, MONTHLY_FIRST_REMOVAL_CLEANUP_INPUTS_V1,
        MONTHLY_CURRENT_HELPER_DOMAIN_INPUTS_V1, MONTHLY_CURRENT_HELPER_POINT_STORE_INPUTS_V1,
        CURRENT_PROVINCE_SUPPLY_CONTRIBUTORS_V1, CURRENT_PROVINCE_BESIEGING_CONTRIBUTORS_V1,
        CURRENT_LAND_RESUPPLY_V1, CURRENT_LAND_SUPPLY_RATE_INPUTS_V1, SCOPED_ORDERED_REFILL_INPUTS_V1,
        CURRENT_DAILY_ASSAULT_TABLE_V1, CURRENT_DAILY_ASSAULT_ROSTER_ADMISSION_V1, COUNTY_ENTRY_INPUTS_V1,
        NATIVE_ARMY_RESOLUTION_V1, ORDERED_BESIEGING_REFILL_INPUTS_V1, CURRENT_DAILY_ASSAULT_LOSS_INPUTS_V1,
        ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_INPUTS_V1, CURRENT_FIRST_ROUTE_TARGET_SUPPLY_CONTRIBUTORS_V1,
        NEXT_ROUTE_REPLENISHMENT_POSITION_INPUTS_V1, CURRENT_ASSAULT_REMOVAL_REFERENCE_INPUTS_V1,
        CURRENT_PRE_DATE_PENDING_UPDATE_INPUTS_V1, CURRENT_PRE_DATE_DATED_APPEND_INPUTS_V1,
        CURRENT_POST_ADMISSION_REFRESH_INPUTS_V1, CURRENT_CANDIDATE_DETACHMENT_MAPPER_INPUTS_V1,
        CURRENT_DETACHMENT_DATA_INPUTS_V1, FUTURE_DAILY_SUPPLY_SCHEDULE_INPUTS_V1,
        CURRENT_DETACHMENT_CALLBACK_INPUTS_V1, CURRENT_DETACHMENT_STORE_INPUTS_V1,
        CURRENT_CHARACTER_DETACHMENT_INPUTS_V1, CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1,
        CURRENT_ARMY_CONDITION30_INPUTS_V1, SOURCE_DERIVED_NEXT_DAILY_SUPPLY_FRAME_INPUTS_V1,
        CURRENT_UNIT_NEW_DATE_SCHEDULE_INPUTS_V1, CURRENT_UNIT_NEW_DATE_CALLBACK_ENTRY_INPUTS_V1,
        CURRENT_ARMY_FLAG20_INPUTS_V1, CURRENT_DISEMBARK_PENALTY_V1, CURRENT_ARMY_FLAG21_INPUTS_V1,
        CURRENT_SELECTED_TITLE_HOLDER_OWNER_RELATION_V1, CURRENT_ARMY_FLAG31_INPUTS_V1,
        CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1, CURRENT_FLEET_SUPPLY_TICK_INPUTS_V1,
        CURRENT_DAILY_SUPPLY_DISPATCH_INPUTS_V1, CURRENT_MONTH_FIRST_REFILL_CALL_INPUTS_V1,
        ACTUAL_LOSS_WRITER_OBSERVATIONS_V1, ACTUAL_SUPPLY_CALLBACK_OBSERVATIONS_V1,
        BATTLE_CASUALTY_OBSERVATIONS_V1, ACTUAL_ARMY_LATE_EVENT_OBSERVATIONS_V1,
        ACTUAL_COMPILED_EFFECT_OBSERVATIONS_V1, ARMY_NATURAL_PHASE_OBSERVATIONS_V1,
        ACTUAL_ARMY_REGULAR_CORE_OBSERVATIONS_V1, ACTUAL_ARMY_DAILY_ASSAULT_PREPARATION_OBSERVATIONS_V1,
        ACTUAL_ARMY_ASSAULT_PLACEMENT_OBSERVATIONS_V1, ARMY_ACTUAL_ASSAULT_CONSUMER_OBSERVATIONS_V1,
        ACTUAL_ARMY_ASSAULT_GROUP_RELEASE_OBSERVATIONS_V1, NATIVE_GATHERING_DUE_NATURAL_STAGE_12004,
        ACTUAL_ARMY_CLEANUP_OBSERVATIONS_V1, ACTUAL_ARMY_PRE_DATE_PREFIX_OBSERVATIONS_V1;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
        public boolean retainedPhase() { return ordinal() >= ARMY_NATURAL_PHASE_OBSERVATIONS_V1.ordinal(); }
        public boolean defaultNullWhenMissing() { return this == FIXED_CHUNK0_PREPARATION_INPUTS_V1 || this == NEXT_ROUTE_REPLENISHMENT_POSITION_INPUTS_V1 || this == ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_INPUTS_V1 || this == BATTLE_CASUALTY_OBSERVATIONS_V1; }
    }
    @FunctionalInterface public interface Normalizer<T> { Field<T> normalize(Field<RawJson> actual, ArmyStrengths.RowContext row); }
    private interface Installed { ArmyStrengths.FamilyValue<?> normalize(Field<RawJson> actual, ArmyStrengths.RowContext row); ExactRef source(); }
    private static final class Typed<T> implements Installed {
        private final Key key; private final Class<T> type; private final Normalizer<T> decoder;
        private final Function<Field<T>,RawJson> encoder; private final Function<Field<T>,RawJson> publicEncoder; private final ExactRef source;
        Typed(Key key, Class<T> type, Normalizer<T> decoder, Function<Field<T>,RawJson> encoder, Function<Field<T>,RawJson> publicEncoder, ExactRef source) {
            this.key = key; this.type = type; this.decoder = decoder; this.encoder = encoder; this.publicEncoder = publicEncoder; this.source = source;
        }
        @Override public ExactRef source() { return source; }
        @Override public ArmyStrengths.FamilyValue<T> normalize(Field<RawJson> actual, ArmyStrengths.RowContext row) {
            Field<T> value = Objects.requireNonNull(decoder.normalize(actual, row));
            if (value instanceof Present<T> present) type.cast(present.value());
            return new ArmyStrengths.FamilyValue<>(key, type, value, Objects.requireNonNull(encoder.apply(value)), Objects.requireNonNull(publicEncoder.apply(value)));
        }
    }
    public static final class MissingMigration extends IllegalStateException {
        private static final long serialVersionUID = 1L; private final Key[] missing;
        MissingMigration(List<Key> missing) { super("Army rich normalization is incomplete: " + missing); this.missing = List.copyOf(missing).toArray(Key[]::new); }
        public List<Key> missing() { return List.of(missing); }
    }
    public record Coverage(List<Key> installed, List<Key> missing) {
        public Coverage { installed = List.copyOf(installed); missing = List.copyOf(missing); }
        public boolean complete() { return missing.isEmpty(); }
    }
    public static final class Registry {
        // Heterogeneous adapters are restricted to this validated Class<T>/Normalizer<T>/Encoder<T> boundary.
        private final EnumMap<Key,Installed> installed = new EnumMap<>(Key.class);
        private boolean frozen;
        public synchronized <T> void register(Key key, Class<T> type, Normalizer<T> decoder, Function<Field<T>,RawJson> encoder, ExactRef source) {
            register(key, type, decoder, encoder, value -> ArmyStrengthsBaselinePublicRules.encodeFamily(key, encoder.apply(value)), source);
        }
        public synchronized <T> void register(Key key, Class<T> type, Normalizer<T> decoder, Function<Field<T>,RawJson> encoder,
                Function<Field<T>,RawJson> publicV2Encoder, ExactRef source) {
            require(!frozen, "Army family registry frozen"); Objects.requireNonNull(key); Objects.requireNonNull(type);
            Objects.requireNonNull(decoder); Objects.requireNonNull(encoder); Objects.requireNonNull(publicV2Encoder); Objects.requireNonNull(source);
            require(key != Key.REGIMENT_STRENGTHS && source.bytes() > 0 && !type.isPrimitive(), "regiment composition has its single built-in typed normalizer");
            require(!installed.containsKey(key), "duplicate Army family normalizer");
            installed.put(key, new Typed<>(key, type, decoder, encoder, publicV2Encoder, source));
        }
        public synchronized void freeze() { require(!frozen, "Army family registry already frozen"); frozen = true; }
        public synchronized Coverage coverage() {
            List<Key> actual = new ArrayList<>(installed.keySet()); actual.add(Key.REGIMENT_STRENGTHS);
            return new Coverage(actual, List.of(Key.values()).stream().filter(key -> !actual.contains(key)).toList());
        }
        public synchronized void requireCompleteRich() {
            require(frozen, "Army family registry must be frozen before production reads"); Coverage coverage = coverage();
            if (!coverage.complete()) throw new MissingMigration(coverage.missing());
        }
        public synchronized ArmyStrengths.FamilyValue<?> normalize(Key key, Field<RawJson> actual, ArmyStrengths.RowContext row) {
            require(frozen, "Army family normalizer cannot run before Root freeze");
            Installed selected = installed.get(Objects.requireNonNull(key));
            if (selected == null) throw new MissingMigration(List.of(key));
            return selected.normalize(actual, row);
        }
        public synchronized List<ExactRef> sourceRefs() { return installed.values().stream().map(Installed::source).toList(); }
    }
    public static Set<String> allowedFieldNames() { return java.util.Arrays.stream(Key.values()).map(Key::wire).collect(java.util.stream.Collectors.toUnmodifiableSet()); }
}
