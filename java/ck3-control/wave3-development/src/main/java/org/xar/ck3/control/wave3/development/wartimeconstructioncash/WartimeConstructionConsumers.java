package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import java.util.Objects;
import java.math.BigInteger;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import static org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.*;

/** Narrow consumer guards for prequote, quoted outlay and the original writer's final check. */
public final class WartimeConstructionConsumers {
    private WartimeConstructionConsumers() { }
    @FunctionalInterface public interface CurrentInputs {
        /** Read the original local current snapshot/root/spending/market/ledger context, with no new native query. */
        Input readCurrent();
    }
    public static Decision observeBeforeOptionalQuery(CurrentInputs inputs) {
        Input observed = Objects.requireNonNull(inputs.readCurrent());
        Input zeroSpend = new Input(observed.kindWire(), Read.of(BigInteger.ZERO), observed.context(), observed.quotes(),
                observed.marketShape(), observed.procurement(), observed.focusRequest());
        return WartimeConstructionCash.observe(zeroSpend);
    }
    public static Decision observeQuotedOutlay(CurrentInputs inputs) {
        return WartimeConstructionCash.observe(Objects.requireNonNull(inputs.readCurrent()));
    }
    /** Call inside the original submission authority before creating intent; an old decision is not accepted. */
    public static Decision requireCurrentBeforeIntent(CurrentInputs inputs) {
        Decision decision = WartimeConstructionCash.observe(Objects.requireNonNull(inputs.readCurrent()));
        if (!decision.newSpendAllowed()) throw new DeferredConstructionException(decision);
        return decision;
    }
    public static final class DeferredConstructionException extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        // Business DTOs use WartimeConstructionCodec, not Java exception serialization.
        private final transient Decision decision;
        public DeferredConstructionException(Decision decision) {
            super("wartime optional construction deferred before intent/send: " + decision.reason().orElseThrow().wire());
            this.decision = decision;
        }
        public Decision decision() {
            if (decision == null) throw new IllegalStateException("local decision payload unavailable after exception deserialization; use WartimeConstructionCodec");
            return decision;
        }
    }
}
