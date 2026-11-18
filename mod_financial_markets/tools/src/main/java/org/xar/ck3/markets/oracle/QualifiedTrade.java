package org.xar.ck3.markets.oracle;

import java.util.Objects;

/** Beneficiary IDs are legal economic controllers, never the exchange's technical custodian. */
public record QualifiedTrade(String assetId, String buyerBeneficiaryId, String sellerBeneficiaryId,
                             long day, long priceCents, long lots, boolean controllerRelated) {
    public QualifiedTrade {
        Objects.requireNonNull(assetId, "assetId");
        Objects.requireNonNull(buyerBeneficiaryId, "buyerBeneficiaryId");
        Objects.requireNonNull(sellerBeneficiaryId, "sellerBeneficiaryId");
        if (assetId.isBlank() || buyerBeneficiaryId.isBlank() || sellerBeneficiaryId.isBlank()
                || day < 0 || priceCents <= 0 || lots <= 0) {
            throw new IllegalArgumentException("positive real trade and beneficiary identities required");
        }
        Math.multiplyExact(priceCents, lots);
    }
}
