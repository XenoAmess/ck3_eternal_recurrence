package org.xar.ck3.control.wave2.military.callbackrisk;

import java.util.Objects;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel;
import org.xar.ck3.control.wave2.military.losssequence.LossSequencePolicy;

/** Uses the one already computed same-query supply budget in the shared four-pass loss core. */
public final class CallbackSoldierEffects {
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum MissingReason { CONDITIONAL_CURRENT_CALLBACK_SUPPLY_BUDGET, LOSS_APPLICATION_INPUTS_V1 }
    public record SupplyBudget(boolean ready, Integer soldiers, boolean postStockReady, Long postStockRaw) {
        public static SupplyBudget from(CallbackSupplyRisk.Result risk) {
            Objects.requireNonNull(risk);
            var entry = risk.supplyEntry();
            return new SupplyBudget(entry.component().ready(), entry.component().soldiers(), entry.postStockReady(), entry.postStockRaw());
        }
    }
    public record Input(SupplyBudget budget, Integer observedCurrentSoldiers,
                        boolean lossInputsPresent, Integer observedSupplyBudget,
                        Integer observedSiegeBudget, Integer observedRaidBudget,
                        LossSequenceModel.Input sequenceInput) {
        public Input { Objects.requireNonNull(budget); }
    }
    public record Result(Input input, Status status, boolean ready, MissingReason missingReason,
                         LossSequenceModel.Result sequence) {
        public Result { Objects.requireNonNull(input); Objects.requireNonNull(status); }
    }
    private CallbackSoldierEffects() {}

    public static Result project(Input input) {
        Objects.requireNonNull(input);
        if (!input.budget().ready() || input.budget().soldiers() == null) {
            return new Result(input, Status.UNAVAILABLE, false, MissingReason.CONDITIONAL_CURRENT_CALLBACK_SUPPLY_BUDGET, null);
        }
        if (!input.lossInputsPresent()) return new Result(input, Status.PARTIAL, false, MissingReason.LOSS_APPLICATION_INPUTS_V1, null);
        Objects.requireNonNull(input.sequenceInput(), "ready budget and present loss inputs require the actual shared sequence input");
        var sequence = LossSequencePolicy.project(input.sequenceInput());
        return new Result(input, sequence.ready() ? Status.AVAILABLE : Status.PARTIAL, sequence.ready(), null, sequence);
    }
}
