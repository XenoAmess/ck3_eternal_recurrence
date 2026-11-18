package org.xar.ck3.markets.core;

public record BeneficiaryId(String value) {
    public BeneficiaryId {
        IdentifierRules.validate(value, "beneficiary ID");
    }
}
