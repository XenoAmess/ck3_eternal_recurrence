package org.xar.ck3.markets.core;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

public record AccountView(AccountId id, BeneficiaryId beneficiaryId, long availableCashCents,
                          long reservedCashCents, Map<CoinId, CoinBalance> holdings) {
    public AccountView {
        holdings = Collections.unmodifiableMap(new LinkedHashMap<>(holdings));
    }

    public CoinBalance balance(CoinId coinId) {
        return holdings.getOrDefault(coinId, new CoinBalance(0, 0));
    }

    public long totalCashCents() {
        return Math.addExact(availableCashCents, reservedCashCents);
    }
}
