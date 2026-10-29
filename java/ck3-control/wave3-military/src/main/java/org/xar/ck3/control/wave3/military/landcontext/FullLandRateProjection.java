package org.xar.ck3.control.wave3.military.landcontext;

import java.util.List;
import org.xar.ck3.control.wave2.military.landstock.LandStockModel;

/** Conditional arithmetic, never an actual after stage or a monthly dispatch qualification. */
public record FullLandRateProjection(int selectedRefillUsageSoldiers, Long currentObservedTotalRateRaw,
                                      LandStockModel.RateResult numericResult, List<String> missingInputs) {
    public FullLandRateProjection { missingInputs = List.copyOf(missingInputs); }
    public boolean ready() { return numericResult instanceof LandStockModel.AvailableRate; }
}
