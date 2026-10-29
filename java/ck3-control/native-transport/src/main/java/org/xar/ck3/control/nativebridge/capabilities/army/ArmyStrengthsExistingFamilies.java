package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Objects;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputsCodec;
import org.xar.ck3.control.wave2.military.callbackrisk.CurrentSupplyDispatch;
import org.xar.ck3.control.wave2.military.callbackrisk.CurrentSupplyDispatchCodec;
import org.xar.ck3.control.wave2.military.combatroles.CombatRoles;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesCodec;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryInputs;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplySchedule;
import org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrame;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key;

/** Reuse each established full Java family normalizer; no second partial validator is introduced. */
public final class ArmyStrengthsExistingFamilies {
    private ArmyStrengthsExistingFamilies() { }
    public record Sources(ExactRef monthlyLoss, ExactRef dailyQueue, ExactRef countyEntry, ExactRef sourceNextFrame,
            ExactRef fleetTick, ExactRef supplyDispatch, ExactRef futureSupply, ExactRef combatRoles) {
        public Sources { for (ExactRef source : java.util.List.of(monthlyLoss, dailyQueue, countyEntry, sourceNextFrame, fleetTick, supplyDispatch, futureSupply, combatRoles)) Objects.requireNonNull(source); }
    }
    public static void install(ArmyStrengthsFamilies.Registry registry, Sources sources) {
        add(registry, Key.MONTHLY_LOSS_BUDGET_INPUTS_V1, MonthlyLossModel.BudgetInputs.class,
                (node, row) -> MonthlyLossCodec.decodeFamilyNullable(node), MonthlyLossCodec::encodeFamilyNullable, sources.monthlyLoss());
        add(registry, Key.MONTHLY_DAILY_QUEUE_INPUTS_V1, ArmyDailyQueueInputs.class,
                (node, row) -> ArmyDailyQueueInputsCodec.decodeNullable(node), ArmyDailyQueueInputsCodec::encodeNullable, sources.dailyQueue());
        add(registry, Key.COUNTY_ENTRY_INPUTS_V1, CountyEntryInputs.class,
                (node, row) -> CountyEntryCodec.decode(node, ArmyStrengthsCodec.present(row.currentSoldiers())), CountyEntryCodec::inputsNode, sources.countyEntry());
        add(registry, Key.SOURCE_DERIVED_NEXT_DAILY_SUPPLY_FRAME_INPUTS_V1, SourceNextFrame.class,
                (node, row) -> SourceNextFrameCodec.decode(node, row.army().value(), nativeId(row)), SourceNextFrameCodec::encode, sources.sourceNextFrame());
        add(registry, Key.CURRENT_FLEET_SUPPLY_TICK_INPUTS_V1, FleetSupplyModel.FleetTick.class,
                (node, row) -> FleetSupplyCodec.decodeTick(node), value -> value == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : FleetSupplyCodec.encodeTick(value), sources.fleetTick());
        add(registry, Key.CURRENT_DAILY_SUPPLY_DISPATCH_INPUTS_V1, CurrentSupplyDispatch.class,
                (node, row) -> CurrentSupplyDispatchCodec.decode(node, row.army().value(), nativeId(row)), CurrentSupplyDispatchCodec::encode, sources.supplyDispatch());
        add(registry, Key.FUTURE_DAILY_SUPPLY_SCHEDULE_INPUTS_V1, FutureDailySupplySchedule.class,
                (node, row) -> FutureDailySupplyScheduleCodec.decode(node, row.army().value(), nativeId(row)), FutureDailySupplyScheduleCodec::encode, sources.futureSupply());
        add(registry, Key.CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1, CombatRoles.Inputs.class,
                (node, row) -> CombatRolesCodec.decode(node), CombatRolesCodec::encode, sources.combatRoles());
    }
    private static Integer nativeId(ArmyStrengths.Core row) { return row.nativeArmy() instanceof Present<FullId> p ? p.value().value() : null; }
    private static <T> void add(ArmyStrengthsFamilies.Registry registry, Key key, Class<T> type,
            BiFunction<JsonNode,ArmyStrengths.Core,T> decoder, Function<T,JsonNode> encoder, ExactRef source) {
        registry.register(key, type, (input, row) -> {
            JsonNode node = input instanceof Present<RawJson> p ? ArmyStrengthsCodec.parseValue(p.value()) : com.fasterxml.jackson.databind.node.NullNode.getInstance();
            T value = decoder.apply(node, row.core()); return value == null ? new NullValue<>() : new Present<>(value);
        }, field -> new RawJson(ArmyJson.bytes(encoder.apply(field instanceof Present<T> p ? p.value() : null))), source);
    }
}
