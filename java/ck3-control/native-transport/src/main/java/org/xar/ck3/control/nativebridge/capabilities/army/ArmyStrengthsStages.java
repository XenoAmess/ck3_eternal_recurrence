package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.replenishment.ReplenishmentCodec;
import org.xar.ck3.control.replenishment.ReplenishmentModel;
import org.xar.ck3.control.replenishment.ReplenishmentPolicy;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSoldierEffects;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSoldierEffectsCodec;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSupplyRisk;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSupplyRiskCodec;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyProjection;
import org.xar.ck3.control.wave2.military.stocksupply.NextFleetRate;
import org.xar.ck3.control.wave2.military.stocksupply.StockSupplyCodec;
import org.xar.ck3.control.wave2.military.stocksupply.StockSupplyProjection;
import org.xar.ck3.control.wave2.military.supplyschedule.NativeNextDailySupplySchedule;
import org.xar.ck3.control.wave2.military.supplyschedule.NativeNextDailySupplyScheduleCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterProjection;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteProjection;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Concrete existing Java stage producers; no caller can substitute a budget ACK for actual Army effects. */
public final class ArmyStrengthsStages {
    private ArmyStrengthsStages() { }
    public record ObservedReplenishment(ReplenishmentModel.Projection value) { public ObservedReplenishment { Objects.requireNonNull(value); } }
    public record CallbackRisks(List<PerArmy<CallbackSupplyRisk.Result>> values) { public CallbackRisks { values = List.copyOf(values); } }
    public record CallbackEffects(List<PerArmy<CallbackSoldierEffects.Result>> values) { public CallbackEffects { values = List.copyOf(values); } }
    public record FleetBudgets(List<PerArmy<FleetSupplyModel.FleetSupplyBudget>> values) { public FleetBudgets { values = List.copyOf(values); } }
    public record StockBudgets(List<PerArmy<StockSupplyProjection.Result>> values) { public StockBudgets { values = List.copyOf(values); } }
    public record FleetRates(List<PerArmy<NextFleetRate.Result>> values) { public FleetRates { values = List.copyOf(values); } }
    public record UpdaterWrites(List<PerArmy<UpdaterProjection>> values) { public UpdaterWrites { values = List.copyOf(values); } }
    public record SupplySchedules(List<PerArmy<Field<NativeNextDailySupplySchedule>>> values) { public SupplySchedules { values = List.copyOf(values); } }
    public static void install(ArmyStrengthsPipeline pipeline, ExactRef actualAdapterSource) {
        pipeline.register(Stage.SAME_INPUT_REPLENISHMENT_V1, ObservedReplenishment.class, List.of(), (input, earlier) -> observedReplenishment(input.selected()),
                value -> new RawJson(ReplenishmentCodec.encodeProjection(value.value())), actualAdapterSource);
        pipeline.register(Stage.SAME_INPUT_CONDITIONAL_NEXT_ADMITTED_DAY_FLEET_RATE_V1, FleetRates.class, List.of(), (input, earlier) -> new FleetRates(input.selected().stream().map(row ->
                new PerArmy<>(row.core().army(), NextFleetRate.project(StockSupplyCodec.decodeRateRow(earlier.rowJson(row))))).toList()), value -> perArmy(value.values(), StockSupplyCodec::encodeRate), actualAdapterSource);
        pipeline.register(Stage.SOURCE_DERIVED_NEXT_UPDATER_WRITES_V1, UpdaterWrites.class, List.of(), (input, earlier) -> new UpdaterWrites(input.selected().stream().map(row ->
                new PerArmy<>(row.core().army(), UpdaterWriteProjection.project(UpdaterWriteCodec.decode(earlier.rowJson(row))))).toList()), value -> perArmy(value.values(), UpdaterWriteCodec::encode), actualAdapterSource);
        pipeline.register(Stage.SOURCE_DERIVED_NEXT_FLEET_SUPPLY_BUDGET_V1, FleetBudgets.class, List.of(), (input, earlier) -> new FleetBudgets(input.selected().stream().map(row ->
                new PerArmy<>(row.core().army(), FleetSupplyProjection.project(FleetSupplyCodec.decodeRow(earlier.rowJson(row))))).toList()), value -> perArmy(value.values(), FleetSupplyCodec::encodeBudget), actualAdapterSource);
        pipeline.register(Stage.SOURCE_DERIVED_NEXT_STOCK_SUPPLY_BUDGET_V1, StockBudgets.class, List.of(), (input, earlier) -> new StockBudgets(input.selected().stream().map(row ->
                new PerArmy<>(row.core().army(), StockSupplyProjection.project(StockSupplyCodec.decodeRow(earlier.rowJson(row))))).toList()), value -> perArmy(value.values(), StockSupplyCodec::encode), actualAdapterSource);
        pipeline.register(Stage.CURRENT_CALLBACK_SUPPLY_RISK_V1, CallbackRisks.class, List.of(), (input, earlier) -> new CallbackRisks(input.selected().stream().map(row ->
                new PerArmy<>(row.core().army(), CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decodeRow(earlier.rowJson(row))))).toList()), value -> perArmy(value.values(), CallbackSupplyRiskCodec::encode), actualAdapterSource);
        pipeline.register(Stage.CURRENT_CALLBACK_SOLDIER_EFFECTS_V1, CallbackEffects.class, List.of(Stage.CURRENT_CALLBACK_SUPPLY_RISK_V1), (input, earlier) -> {
            CallbackRisks risks = earlier.required(Stage.CURRENT_CALLBACK_SUPPLY_RISK_V1, CallbackRisks.class); List<PerArmy<CallbackSoldierEffects.Result>> effects = new ArrayList<>();
            for (Row row : input.selected()) {
                var risk = risks.values().stream().filter(value -> value.army().equals(row.core().army())).findFirst().orElseThrow().projection();
                effects.add(new PerArmy<>(row.core().army(), CallbackSoldierEffects.project(CallbackSoldierEffectsCodec.decodeRow(earlier.rowJson(row), risk))));
            }
            return new CallbackEffects(effects);
        }, value -> perArmy(value.values(), CallbackSoldierEffectsCodec::encode), actualAdapterSource);
        pipeline.register(Stage.SAME_INPUT_CONDITIONAL_FUTURE_DAILY_SUPPLY_SCHEDULE_V1, SupplySchedules.class, List.of(), (input, earlier) -> new SupplySchedules(input.selected().stream().map(row -> {
            NativeNextDailySupplySchedule schedule = NativeNextDailySupplyScheduleCodec.fromSameQueryRow(earlier.rowJson(row));
            Field<NativeNextDailySupplySchedule> value = schedule == null ? new NullValue<>() : new Present<>(schedule); return new PerArmy<>(row.core().army(), value);
        }).toList()), value -> perArmy(value.values(), field -> NativeNextDailySupplyScheduleCodec.encode(field instanceof Present<NativeNextDailySupplySchedule> p ? p.value() : null)), actualAdapterSource);
    }
    /** Feed the existing pure producer from exact typed/full-family observations, avoiding its smaller external JSON envelope limit. */
    public static ObservedReplenishment observedReplenishment(List<Row> rows) {
        List<ReplenishmentModel.ArmyRow> input = new ArrayList<>();
        for (Row row : rows) {
            var family = row.families().stream().filter(value -> value.key() == ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT_RECORDS_V1).findFirst();
            ReplenishmentModel.Snapshots snapshots;
            if (family.isEmpty()) snapshots = new ReplenishmentModel.MissingSnapshots();
            else {
                JsonNode raw = ArmyStrengthsCodec.parseValue(family.orElseThrow().normalizedJson());
                if (raw.isNull()) snapshots = new ReplenishmentModel.NullSnapshots();
                else {
                    List<ReplenishmentModel.FullDataSnapshot> observed = new ArrayList<>();
                    for (JsonNode regiment : array(raw, value -> value)) {
                        var n = object(regiment); List<ReplenishmentModel.FullDataRecord> records = new ArrayList<>();
                        for (JsonNode data : array(get(n, "records"), value -> value)) {
                            var r = object(data);
                            records.add(new ReplenishmentModel.FullDataRecord(ArmyStrengthsCodec.enumText(get(r, "status"), ReplenishmentModel.RecordStatus.class), nullableString(get(r, "unavailable_reason")),
                                    i32(get(r, "record_index")), i32(get(r, "persistent_regiment_id")), i32(get(r, "chunk_index")), nullable32(get(r, "maximum_soldiers")), nullable32(get(r, "effective_current_soldiers")),
                                    nullable64(get(r, "persistent_prepared_replenishment_fraction_raw")), i32(get(r, "persistent_prepared_replenishment_fraction_scale")), nullableBool(get(r, "native_chunk_can_replenish"))));
                        }
                        observed.add(new ReplenishmentModel.FullDataSnapshot(i32(get(n, "army_regiment_id")), ArmyStrengthsCodec.enumText(get(n, "status"), ReplenishmentModel.CoverageStatus.class),
                                nullable32(get(n, "native_data_record_count")), nullableString(get(n, "unavailable_reason")), records));
                    }
                    snapshots = new ReplenishmentModel.PublishedSnapshots(observed);
                }
            }
            input.add(new ReplenishmentModel.ArmyRow(row.core().army().value(), snapshots));
        }
        return new ObservedReplenishment(ReplenishmentPolicy.projectObservedReplenishmentV1(input));
    }
    private static <T> RawJson perArmy(List<PerArmy<T>> values, Function<T,JsonNode> encoder) {
        var rows = empty().arrayNode(); for (PerArmy<T> value : values) rows.addObject().put("army_id", value.army().value()).set("projection", encoder.apply(value.projection())); return new RawJson(bytes(rows));
    }
    private static Integer nullable32(JsonNode value) { return value.isNull() ? null : i32(value); }
    private static Long nullable64(JsonNode value) { return value.isNull() ? null : i64(value); }
    private static Boolean nullableBool(JsonNode value) { return value.isNull() ? null : bool(value); }
    private static String nullableString(JsonNode value) { return value.isNull() ? null : nonempty(value); }
}
