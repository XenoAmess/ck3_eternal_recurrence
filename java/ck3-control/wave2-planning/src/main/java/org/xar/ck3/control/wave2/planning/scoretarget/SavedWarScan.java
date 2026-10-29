package org.xar.ck3.control.wave2.planning.scoretarget;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Fields from one actual SaveProjection; no source or native qualification is granted here. */
public record SavedWarScan(PlayerWarInput player, BigInteger unknownKeyFields,
        List<List<String>> warContainers, boolean warLayoutUnknown, String sourceRef) {
    public SavedWarScan {
        Objects.requireNonNull(player); Objects.requireNonNull(unknownKeyFields);
        StrictJson.require(unknownKeyFields.signum() >= 0, "nonnegative unknown field count required");
        warContainers = warContainers.stream().map(List::copyOf).toList();
        StrictJson.text(sourceRef);
    }
}
