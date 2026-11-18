package org.xar.ck3.markets.oracle;

import java.util.Map;
import java.util.Objects;

/** Explicit asset routing does not invent an unknown source or retry through a weaker oracle. */
public final class CompositePriceOracle implements PriceOracle {
    private final Map<String, PriceOracle> routes;

    public CompositePriceOracle(Map<String, PriceOracle> routes) {
        Objects.requireNonNull(routes, "routes");
        routes.forEach((asset, source) -> {
            if (asset == null || asset.isBlank() || source == null) {
                throw new IllegalArgumentException("explicit nonblank asset and source required");
            }
        });
        this.routes = Map.copyOf(routes);
    }

    @Override
    public PriceQuote quote(String assetId, long day) {
        PriceOracle oracle = routes.get(Objects.requireNonNull(assetId, "assetId"));
        if (oracle == null) throw new IllegalArgumentException("no registered oracle source");
        PriceQuote result = oracle.quote(assetId, day);
        if (!assetId.equals(result.assetId()) || result.day() != day) {
            throw new IllegalStateException("oracle returned a different asset or publication day");
        }
        return result;
    }
}
