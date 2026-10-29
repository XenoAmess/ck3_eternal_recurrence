package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Arrays;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;

/** Full service projection closure. Missing a Java stage is RED; an incomplete adapter cannot advertise the public Army route. */
public final class ArmyStrengthsPipeline {
    public enum Stage {
        SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_PENDING_UPDATE_V1(true), SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_CHARACTER_PREFIX_V1(true),
        SAME_INPUT_CONDITIONAL_POST_REFILL_LAND_SUPPLY_RATE_V1, SAME_INPUT_CONDITIONAL_SELECTED_REFILL_MONTHLY_ASSEMBLY_V1,
        SAME_INPUT_CONDITIONAL_POST_REFILL_BESIEGING_CURRENT_V1, SAME_INPUT_CONDITIONAL_FIXED_CHUNK0_PREPARATION_V1,
        SAME_INPUT_CONDITIONAL_SCOPED_ORDERED_REFILL_CURRENT_V1, NEXT_ROUTE_POSITION_SCOPED_ORDERED_REFILL_V1,
        SAME_INPUT_CONDITIONAL_ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_V1, SAME_INPUT_CONDITIONAL_ORDERED_REFILL_BESIEGING_ASSAULT_V1,
        SAME_INPUT_CURRENT_DAILY_ASSAULT_LOSS_V1, SAME_INPUT_CURRENT_DAILY_ASSAULT_QUEUE_APPEND_V1,
        SAME_INPUT_CURRENT_DAILY_ASSAULT_NORMAL_RETURN_RELEASE_V1, SAME_INPUT_CURRENT_ASSAULT_FIRST_REMOVAL_V1,
        CURRENT_FIRST_ROUTE_TARGET_SUPPLY_CONTRIBUTORS_V1, CURRENT_UNIT_NEW_DATE_ENTRY_NORMALIZATION_V1,
        CURRENT_UNIT_NEXT_MOVEMENT_PREFIX_V1, CURRENT_UNIT_NEXT_FIRST_EDGE_SELECTION_V1, CURRENT_UNIT_NEXT_ARRIVAL_TRANSITION_V1,
        CURRENT_UNIT_ARRIVAL_PRESTORE_DISEMBARK_WRITE_V1, SAME_INPUT_REPLENISHMENT_V1, LOSS_ALLOCATION_REQUESTS_V1,
        SAME_INPUT_CONDITIONAL_NEXT_ADMITTED_DAY_FLEET_RATE_V1, CURRENT_DAILY_ASSAULT_GROUP_INPUTS_V1,
        CURRENT_DAILY_ASSAULT_PLACEMENT_INPUTS_V1, SAME_INPUT_CURRENT_CANDIDATE_DETACHMENT_MAPPER_V1,
        SAME_INPUT_CURRENT_DETACHMENT_DATA_PREFIX_V1, SAME_INPUT_CONDITIONAL_FUTURE_DAILY_SUPPLY_SCHEDULE_V1,
        SOURCE_DERIVED_NEXT_UPDATER_WRITES_V1, SOURCE_DERIVED_NEXT_FLEET_SUPPLY_BUDGET_V1,
        SOURCE_DERIVED_NEXT_STOCK_SUPPLY_BUDGET_V1, SOURCE_DERIVED_NEXT_LAND_STOCK_SUPPLY_BUDGET_V1,
        CURRENT_CALLBACK_SUPPLY_RISK_V1, ACTUAL_SUPPLY_CALLBACK_OBSERVATION_SUMMARY_V1, CURRENT_CALLBACK_SOLDIER_EFFECTS_V1,
        CONDITIONAL_CURRENT_DETACHMENT_CALLBACK_V1, CURRENT_DETACHMENT_STORE_ADMISSION_V1, CURRENT_CHARACTER_DETACHMENT_SUFFIX_V1,
        CURRENT_ARMY_CONDITION30_INPUTS_V1, CURRENT_DISEMBARK_PENALTY_V1, CURRENT_ARMY_FLAG20_INPUTS_V1,
        CURRENT_ARMY_FLAG21_INPUTS_V1, CURRENT_SELECTED_TITLE_HOLDER_OWNER_RELATION_V1, CURRENT_ARMY_FLAG31_INPUTS_V1,
        CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1, CURRENT_POST_ADMISSION_REFRESH_INPUTS_V1,
        CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1, CURRENT_PRE_DATE_DATED_APPEND_INPUTS_V1,
        CURRENT_DAILY_ASSAULT_ROSTER_ADMISSION_INPUTS_V1, SAME_QUERY_CONDITIONAL_ASSAULT_GROUP_CONTRIBUTORS_12004,
        EXPLICIT_OBSERVED_ARMY_STAGE_PROJECTIONS_12004, ACTUAL_ARMY_LATE_EVENT_CONSUMPTION_12004,
        ACTUAL_ARMY_COMPILED_EFFECT_CONSUMPTION_12004, ACTUAL_ARMY_OBSERVED_PHASE_CONSUMPTION_12004;
        private final boolean perRow;
        Stage() { this(false); } Stage(boolean perRow) { this.perRow = perRow; }
        public String wire() { return name().toLowerCase(Locale.ROOT); } public boolean perRow() { return perRow; }
    }
    public record NativeSource(String version, String executableSha256) {
        public NativeSource { Objects.requireNonNull(version); ArmyTypes.require(executableSha256 != null && executableSha256.matches("[a-fA-F0-9]{64}"), "actual native source needs an exact executable digest"); }
    }
    public record Input(Snapshot snapshot, Read original, Query query, List<Row> selected, Optional<NativeWire.Hello> originalHello) {
        public Input { Objects.requireNonNull(snapshot); Objects.requireNonNull(original); Objects.requireNonNull(query); selected = List.copyOf(selected); Objects.requireNonNull(originalHello); }
        /** Controlled/history inputs without the original HELLO cannot claim an exact native source. */
        public Input(Snapshot snapshot, Read original, Query query, List<Row> selected) { this(snapshot, original, query, selected, Optional.empty()); }
        public boolean exactNativeBuild(String version, String sha256) {
            return actualNativeSource().map(source -> source.version().equals(version) && source.executableSha256().equalsIgnoreCase(sha256)).orElse(false);
        }
        public Optional<NativeSource> actualNativeSource() {
            if (originalHello.isEmpty()) return Optional.empty();
            byte[] packet = originalHello.orElseThrow().packet().value();
            var receipt = original.original();
            for (ExactRef evidence : List.of(receipt.before().binding().capabilityEvidence(), receipt.after().binding().capabilityEvidence()))
                ArmyTypes.require(evidence.bytes() == packet.length && evidence.sha256().equals(ActionCodec.sha256(packet)), "source HELLO differs from the actual original query guard evidence");
            try {
                if (!(NativeWire.decode(packet) instanceof NativeWire.Hello received)) throw new IOException("original source packet is not a HELLO");
                ArmyTypes.require(received.pid() == snapshot.binding().game().pid() && received.connectionGeneration().equals(snapshot.binding().connectionGeneration()), "source HELLO crossed query Game/session generation");
                if (!received.buildMatch() || !received.adapterStatus().equals("ready")) return Optional.empty();
                ObjectNode rawHello = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length)));
                var expectedVersion = rawHello.get("expected_ck3_version");
                if (expectedVersion == null || !expectedVersion.isTextual()) return Optional.empty();
                ObjectNode actualSnapshot = ArmyJson.parse(snapshot.original().bytes());
                var diagnostics = actualSnapshot.get("diagnostics");
                var projectedHello = diagnostics != null && diagnostics.isObject() ? diagnostics.get("hello") : null;
                ObjectNode hello = projectedHello != null && projectedHello.isObject() ? (ObjectNode) projectedHello : ArmyJson.empty();
                ObjectNode nativeResult = ArmyJson.parse(receipt.original().originalResultToken().orElseThrow().bytes());
                var sourceValue = nativeResult.get("source");
                ObjectNode source = sourceValue != null && sourceValue.isObject() ? (ObjectNode) sourceValue : ArmyJson.empty();
                var version = source.has("game_version") ? source.get("game_version") : hello.has("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version");
                var sha = source.has("executable_sha256") ? source.get("executable_sha256") : hello.has("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256");
                if (version == null || !version.isTextual() || sha == null || !sha.isTextual()
                        || !version.textValue().equals(expectedVersion.textValue()) || !sha.textValue().equalsIgnoreCase(received.gameSha256())) return Optional.empty();
                return Optional.of(new NativeSource(version.textValue(), sha.textValue()));
            } catch (IOException invalid) { throw new UncheckedIOException("actual native source cannot be decoded", invalid); }
        }
    }
    public record PerArmy<T>(ArmyTypes.PublicUnitId army, T projection) { public PerArmy { Objects.requireNonNull(army); Objects.requireNonNull(projection); } }
    public record Projection<T>(Stage stage, Class<T> type, T value, RawJson json, RawJson publicV2Json) {
        public Projection { Objects.requireNonNull(stage); Objects.requireNonNull(type); type.cast(Objects.requireNonNull(value)); Objects.requireNonNull(json); Objects.requireNonNull(publicV2Json); }
        public Projection(Stage stage, Class<T> type, T value, RawJson json) { this(stage, type, value, json, json); }
    }
    public record Results(List<Projection<?>> values) {
        public Results { values = List.copyOf(values); }
        public <T> T required(Stage key, Class<T> expectedType) {
            Projection<?> selected = values.stream().filter(value -> value.stage() == key).findFirst().orElseThrow(() -> new IllegalStateException("Army stage dependency is missing: " + key));
            ArmyTypes.require(selected.type().equals(expectedType), "Army stage dependency has a different exact typed contract"); return expectedType.cast(selected.value());
        }
        public ObjectNode topLevelJson() { ObjectNode fields = ArmyJson.empty(); values.stream().filter(value -> !value.stage().perRow()).forEach(value -> fields.set(value.stage().wire(), ArmyStrengthsCodec.parseValue(value.json()))); return fields; }
        public ObjectNode topLevelPublicV2Json() { ObjectNode fields = ArmyJson.empty(); values.stream().filter(value -> !value.stage().perRow()).forEach(value -> fields.set(value.stage().wire(), ArmyStrengthsCodec.parseValue(value.publicV2Json()))); return fields; }
        public ObjectNode rowJson(Row row) {
            return rowJson(row, false);
        }
        public ObjectNode rowPublicV2Json(Row row) { return rowJson(row, true); }
        private ObjectNode rowJson(Row row, boolean publicV2) {
            ObjectNode result = publicV2 ? ArmyStrengthsCodec.rowPublicV2Json(row) : ArmyStrengthsCodec.rowJson(row);
            for (Projection<?> stage : values) if (stage.stage().perRow()) {
                var list = ArmyStrengthsCodec.parseValue(publicV2 ? stage.publicV2Json() : stage.json()); ArmyTypes.require(list.isArray(), "per-row stage result must be an exact ordered army_id/projection array");
                var selected = new ArrayList<com.fasterxml.jackson.databind.JsonNode>();
                for (var item : list) { var entry = ArmyJson.closed(item, "army_id", "projection"); if (ArmyJson.unit(ArmyJson.get(entry, "army_id")).equals(row.core().army())) selected.add(ArmyJson.get(entry, "projection")); }
                ArmyTypes.require(selected.size() == 1, "per-row stage loses exact selected Army identity"); result.set(stage.stage().wire(), selected.getFirst());
            }
            return result;
        }
    }
    private interface Installed { Stage stage(); List<Stage> dependencies(); Projection<?> project(Input input, Results earlier); ExactRef source(); }
    private static final class Typed<T> implements Installed {
        private final Stage stage; private final Class<T> type; private final List<Stage> dependencies;
        private final BiFunction<Input,Results,T> producer; private final Function<T,RawJson> encoder; private final Function<T,RawJson> publicEncoder; private final ExactRef source;
        Typed(Stage stage, Class<T> type, List<Stage> dependencies, BiFunction<Input,Results,T> producer, Function<T,RawJson> encoder, Function<T,RawJson> publicEncoder, ExactRef source) {
            this.stage = stage; this.type = type; this.dependencies = List.copyOf(dependencies); this.producer = producer; this.encoder = encoder; this.publicEncoder = publicEncoder; this.source = source;
        }
        @Override public Stage stage() { return stage; } @Override public List<Stage> dependencies() { return dependencies; } @Override public ExactRef source() { return source; }
        @Override public Projection<T> project(Input input, Results earlier) { T value = type.cast(Objects.requireNonNull(producer.apply(input, earlier))); return new Projection<>(stage, type, value, Objects.requireNonNull(encoder.apply(value)), Objects.requireNonNull(publicEncoder.apply(value))); }
    }
    public record Coverage(List<Stage> installed, List<Stage> missing) { public Coverage { installed = List.copyOf(installed); missing = List.copyOf(missing); } public boolean complete() { return missing.isEmpty(); } }
    private final EnumMap<Stage,Installed> installed = new EnumMap<>(Stage.class);
    private boolean frozen;
    public synchronized <T> void register(Stage stage, Class<T> type, List<Stage> dependencies, BiFunction<Input,Results,T> producer, Function<T,RawJson> encoder, ExactRef source) {
        register(stage, type, dependencies, producer, encoder, value -> ArmyStrengthsBaselinePublicRules.encodeStage(stage, encoder.apply(value)), source);
    }
    public synchronized <T> void register(Stage stage, Class<T> type, List<Stage> dependencies, BiFunction<Input,Results,T> producer, Function<T,RawJson> encoder,
            Function<T,RawJson> publicV2Encoder, ExactRef source) {
        ArmyTypes.require(!frozen && !installed.containsKey(stage), "Army stage duplicate or already frozen"); Objects.requireNonNull(stage); Objects.requireNonNull(type); Objects.requireNonNull(producer); Objects.requireNonNull(encoder); Objects.requireNonNull(publicV2Encoder); Objects.requireNonNull(source);
        ArmyTypes.require(dependencies.stream().distinct().count() == dependencies.size() && dependencies.stream().allMatch(dependency -> dependency.ordinal() < stage.ordinal()), "Army projection dependencies must follow the source order without cycles");
        installed.put(stage, new Typed<>(stage, type, dependencies, producer, encoder, publicV2Encoder, source));
    }
    public synchronized void freeze() { ArmyTypes.require(!frozen, "Army pipeline already frozen"); frozen = true; }
    public synchronized Coverage coverage() { return new Coverage(new ArrayList<>(installed.keySet()), java.util.Arrays.stream(Stage.values()).filter(stage -> !installed.containsKey(stage)).toList()); }
    public synchronized void requireComplete() { ArmyTypes.require(frozen, "Army projection pipeline must be frozen"); Coverage coverage = coverage(); ArmyTypes.require(coverage.complete(), "Army full service projectors are not migrated: " + coverage.missing()); }
    public synchronized Results project(Input input) { requireComplete(); return projectAvailable(input); }
    /** Offline source-bound partial inspection only; the public route never uses this method. */
    public synchronized Results projectAvailable(Input input) {
        ArmyTypes.require(frozen, "Army pipeline must be frozen before projection"); List<Projection<?>> results = new ArrayList<>();
        for (Installed adapter : installed.values()) {
            ArmyTypes.require(adapter.dependencies().stream().allMatch(stage -> results.stream().anyMatch(result -> result.stage() == stage)), "actual earlier Army stage is missing");
            results.add(adapter.project(input, new Results(results)));
        }
        return new Results(results);
    }
}
