package org.xar.ck3.control.wave2.military.monthlyloss;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.StockBasis;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyProjection;
import org.xar.ck3.control.wave2.military.losssequence.AssociatedChunkWriter;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec;
import org.xar.ck3.control.wave2.military.losssequence.LossSequencePolicy;
import org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleCodec;
import org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleProjection;
import org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleProjectionCodec;
import org.xar.ck3.control.wave2.military.supplyschedule.NativeNextDailySupplyScheduleCodec;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockCodec;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockProjection;

/** One in-process adapter for existing consumers; contains no arithmetic, IO, service or fallback. */
public final class SupplyConsumerBindings {
    public static final String SCHEMA = "xar.military-supply-consumer-request/v1";
    public static final int MAX_BYTES = 131_072;
    public enum Operation {
        MONTHLY_BUDGETS, LOSS_SEQUENCE, ASSOCIATED_WRITER, SUPPLY_COMPONENT,
        FLEET_BUDGET, FLEET_AT_STOCK, NORMALIZE_SCHEDULE, PROJECT_SCHEDULE,
        NATIVE_NEXT_SCHEDULE, ZERO_CALLBACK, SUCCESSFUL_OCCURRENCES
    }
    public record Request(Operation operation, ObjectNode arguments) {
        public Request {
            java.util.Objects.requireNonNull(operation);
            java.util.Objects.requireNonNull(arguments);
            Set<String> expected = switch (operation) {
                case MONTHLY_BUDGETS, LOSS_SEQUENCE, FLEET_BUDGET, NATIVE_NEXT_SCHEDULE, ZERO_CALLBACK -> Set.of("row");
                case ASSOCIATED_WRITER -> Set.of("row", "writer_request");
                case SUPPLY_COMPONENT -> Set.of("result", "inputs", "losses");
                case FLEET_AT_STOCK -> Set.of("row", "stock", "stock_basis", "post_updater_stock_used", "stock_input_name");
                case NORMALIZE_SCHEDULE -> Set.of("family", "expected_army_id", "expected_carmy_id");
                case PROJECT_SCHEDULE -> Set.of("row_or_family", "prospective_frames");
                case SUCCESSFUL_OCCURRENCES -> Set.of("stock", "capacity", "monthly");
            };
            StrictJson.object(arguments, expected);
            arguments = arguments.deepCopy();
        }
        @Override public ObjectNode arguments() { return arguments.deepCopy(); }
    }
    private SupplyConsumerBindings() { }

    /** JSON is a narrow transport boundary; every declared operand reaches its existing typed codec. */
    public static byte[] exchange(byte[] rawRequest) {
        return exchange(decodeRequest(rawRequest));
    }

    public static Request decodeRequest(byte[] rawRequest) {
        ObjectNode request = StrictJson.object(StrictJson.parse(rawRequest, MAX_BYTES),
                Set.of("schema", "operation", "arguments"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(request.get("schema"))), "supply request schema differs");
        Operation operation;
        try { operation = Operation.valueOf(StrictJson.text(request.get("operation"))); }
        catch (IllegalArgumentException error) { throw new IllegalArgumentException("unknown supply consumer operation", error); }
        StrictJson.require(request.get("arguments").isObject(), "supply arguments must be an object");
        return new Request(operation, (ObjectNode) request.get("arguments"));
    }

    public static byte[] exchange(Request request) {
        java.util.Objects.requireNonNull(request);
        Operation operation = request.operation();
        ObjectNode arguments = request.arguments();
        JsonNode result = switch (operation) {
            case MONTHLY_BUDGETS -> LossSequenceCodec.monthlyBudgetsNodeForHost(row(arguments));
            case LOSS_SEQUENCE -> LossSequenceCodec.sequenceNode(LossSequencePolicy.project(
                    input(() -> LossSequenceCodec.decodeArmyProjection(row(arguments)))));
            case ASSOCIATED_WRITER -> {
                ObjectNode value = arguments;
                yield LossSequenceCodec.writerNode(AssociatedChunkWriter.project(
                        input(() -> LossSequenceCodec.decodeArmyProjection(value.get("row"))),
                        input(() -> LossSequenceCodec.decodeWriterRequest(value.get("writer_request")))));
            }
            case FLEET_BUDGET -> FleetSupplyCodec.encodeBudget(FleetSupplyProjection.project(input(() -> FleetSupplyCodec.decodeRow(row(arguments)))));
            case FLEET_AT_STOCK -> {
                ObjectNode value = arguments;
                StockBasis basis = input(() -> stockBasis(value));
                yield FleetSupplyCodec.encodeBudget(FleetSupplyProjection.projectAtStock(
                        input(() -> FleetSupplyCodec.decodeRow(value.get("row"))), input(() -> nullable64(value.get("stock"))), basis));
            }
            case SUPPLY_COMPONENT -> component(arguments);
            case NORMALIZE_SCHEDULE -> {
                ObjectNode value = arguments;
                yield FutureDailySupplyScheduleCodec.encode(input(() -> FutureDailySupplyScheduleCodec.decode(value.get("family"),
                        nullable32(value.get("expected_army_id")), nullable32(value.get("expected_carmy_id")))));
            }
            case PROJECT_SCHEDULE -> {
                ObjectNode value = arguments;
                var family = input(() -> FutureDailySupplyScheduleProjectionCodec.decodeRowOrFamily(value.get("row_or_family")));
                var frames = input(() -> FutureDailySupplyScheduleProjectionCodec.decodeFrames(value.get("prospective_frames")));
                yield FutureDailySupplyScheduleProjectionCodec.encode(FutureDailySupplyScheduleProjection.project(family, frames));
            }
            case NATIVE_NEXT_SCHEDULE -> NativeNextDailySupplyScheduleCodec.encode(
                    NativeNextDailySupplyScheduleCodec.fromSameQueryRowForHost(row(arguments)));
            case ZERO_CALLBACK -> ZeroStockCodec.encode(ZeroStockProjection.projectNextCallbackCandidate(ZeroStockCodec.decodeForHost(row(arguments))));
            case SUCCESSFUL_OCCURRENCES -> {
                ObjectNode value = arguments;
                yield ZeroStockCodec.encodeOpportunities(ZeroStockProjection.successfulOccurrencesToZero(
                        opportunityInteger(value.get("stock")), opportunityInteger(value.get("capacity")), opportunityInteger(value.get("monthly"))));
            }
        };
        return StrictJson.canonical(result, MAX_BYTES);
    }

    /** Preserve the old helper's mutation and reached-only field presence at this JSON boundary. */

    private static <T> T input(java.util.function.Supplier<T> validator) {
        try { return validator.get(); }
        catch (IllegalArgumentException rejected) {
            if (rejected instanceof org.xar.ck3.control.contracts.projection.ProjectionDomainRejection) throw rejected;
            throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(rejected.getMessage());
        }
    }
    private static StockBasis stockBasis(ObjectNode value) {
        StockBasis basis = switch (StrictJson.text(value.get("stock_basis"))) {
            case "captured_current_stock_unchanged" -> StockBasis.CAPTURED_CURRENT_STOCK_UNCHANGED;
            case "conditional_post_updater_stock" -> StockBasis.CONDITIONAL_POST_UPDATER_STOCK;
            default -> throw new IllegalArgumentException("unsupported stock basis");
        };
        StrictJson.require(value.get("post_updater_stock_used").isBoolean()
                && value.get("post_updater_stock_used").booleanValue() == basis.postUpdaterStockUsed()
                && basis.stockInputName().equals(StrictJson.text(value.get("stock_input_name"))), "stock provenance differs");
        return basis;
    }
    private record ComponentInputs(ObjectNode result, long stock, MonthlyLossModel.SupplyInputs supply,
                                   MonthlyLossModel.LossInputs losses) { }
    private static ComponentInputs componentInputs(ObjectNode value) {
        StrictJson.require(value.get("result").isObject(), "supply result must be object");
        StrictJson.require(value.get("inputs").isObject() && value.get("losses").isObject(), "supply helper operands must be objects");
        ObjectNode result = value.get("result").deepCopy(); JsonNode missing = result.get("missing_inputs");
        StrictJson.require(missing != null && missing.isArray(), "ordered existing missing inputs required");
        for (JsonNode item : missing) StrictJson.text(item);
        long stock = StrictJson.integer(result.get("conditional_post_supply_raw"), Long.MIN_VALUE, Long.MAX_VALUE);
        return new ComponentInputs(result, stock, MonthlyLossCodec.decodeSupplyProjection(value.get("inputs")),
                MonthlyLossCodec.decodeLossProjection(value.get("losses")));
    }

    private static ObjectNode component(ObjectNode arguments) {
        ComponentInputs decoded = input(() -> componentInputs(arguments));
        ObjectNode result = decoded.result(); JsonNode oldMissing = result.get("missing_inputs");
        var component = MonthlyLossPolicy.deriveSupplyComponent(decoded.stock(), decoded.supply(), decoded.losses());
        if (component.stateIndex() != null) result.put("supply_state_index", component.stateIndex().intValue());
        if (component.baseFractionRaw() != null) result.put("supply_base_fraction_raw", component.baseFractionRaw().longValue());
        if (component.effectiveFractionRaw() != null) result.put("supply_effective_fraction_raw", component.effectiveFractionRaw().longValue());
        if (component.ready()) { result.put("supply_budget_ready", true); result.put("supply_budget_soldiers", component.soldiers().intValue()); }
        ArrayNode missing = (ArrayNode) oldMissing;
        component.missingInputs().forEach(missing::add);
        return result;
    }
    private static JsonNode row(ObjectNode arguments) { return arguments.get("row"); }
    private static Long opportunityInteger(JsonNode value) {
        return value.isIntegralNumber() && value.canConvertToLong() ? value.longValue() : null;
    }
    private static Long nullable64(JsonNode value) { return value.isNull() ? null : StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static Integer nullable32(JsonNode value) { return value.isNull() ? null : (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
}
