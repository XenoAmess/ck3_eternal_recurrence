package org.xar.ck3.control.wave3.military.landcontext;

import java.util.Objects;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterInput;

/** All three views are decoded from one row; no JSON enters the domain composition. */
public record FullLandStockInput(LandContextRow land, UpdaterInput updater,
                                  FleetSupplyModel.ArmyRow fleet, Long capturedStockRaw, Long capturedCapacityRaw) {
    public FullLandStockInput {
        Objects.requireNonNull(land); Objects.requireNonNull(updater); Objects.requireNonNull(fleet);
        if (!Objects.equals(land.armyId(), updater.armyId()) || !Objects.equals(land.armyId(), fleet.armyId())
                || !Objects.equals(land.nativeCarmyId(), updater.nativeCarmyId())
                || !Objects.equals(land.nativeCarmyId(), fleet.nativeCarmyId())
                || !Objects.equals(updater.sourceNextDate(), fleet.nextFrame())
                || !Objects.equals(capturedStockRaw, fleet.currentSupplyRaw())
                || land.available() != updater.rowAvailable() || land.available() != "available".equals(fleet.status())) {
            throw new IllegalArgumentException("LAND composition views belong to different same-query identities/status");
        }
    }
}
