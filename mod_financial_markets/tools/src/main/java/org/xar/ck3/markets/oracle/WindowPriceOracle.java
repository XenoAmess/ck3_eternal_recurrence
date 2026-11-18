package org.xar.ck3.markets.oracle;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Bounded, single-venue reference matching the native fixed-ring implementation. */
public final class WindowPriceOracle implements PriceOracle {
    public static final int WINDOW_DAYS = 14;
    public static final int MAX_SAMPLES_PER_DAY = 8;
    public static final int MAX_WEIGHT_LOTS = 1_000;
    public static final long MIN_SAMPLE_NOTIONAL_CENTS = 100;
    public static final long MIN_DAY_NOTIONAL_CENTS = 1_000;
    public static final String SOURCE_ID = "spot:xfm-central-exchange";
    private static final int MIN_DAY_SAMPLES = 4;
    private static final int MIN_DAYS = 7;
    private final Map<String, Asset> assets = new HashMap<>();
    private final int capacity;

    public WindowPriceOracle(int capacity) {
        if (capacity < 1 || capacity > 16_384) throw new IllegalArgumentException("invalid oracle capacity");
        this.capacity = capacity;
    }

    public synchronized void register(String assetId, long listedDay) {
        Objects.requireNonNull(assetId, "assetId");
        if (assetId.isBlank() || listedDay < 0) throw new IllegalArgumentException("invalid listing");
        if (assets.containsKey(assetId)) throw new IllegalArgumentException("asset already registered");
        if (assets.size() == capacity) throw new IllegalStateException("oracle capacity exhausted");
        assets.put(assetId, new Asset(listedDay));
    }

    /** Rejected samples may still be genuine spot trades and must not roll back spot execution. */
    public synchronized boolean record(QualifiedTrade trade) {
        Objects.requireNonNull(trade, "trade");
        Asset asset = require(trade.assetId());
        asset.roll(trade.day());
        if (trade.buyerBeneficiaryId().equals(trade.sellerBeneficiaryId()) || trade.controllerRelated()
                || asset.samples == MAX_SAMPLES_PER_DAY
                || asset.participants.contains(trade.buyerBeneficiaryId())
                || asset.participants.contains(trade.sellerBeneficiaryId())
                || Math.multiplyExact(trade.priceCents(), trade.lots()) < MIN_SAMPLE_NOTIONAL_CENTS) return false;
        long weightLots = Math.min(trade.lots(), MAX_WEIGHT_LOTS);
        long notional = Math.multiplyExact(trade.priceCents(), weightLots);
        long newNotional = Math.addExact(asset.notional, notional);
        long newLots = Math.addExact(asset.lots, weightLots);
        asset.notional = newNotional;
        asset.lots = newLots;
        asset.samples++;
        asset.participants.add(trade.buyerBeneficiaryId());
        asset.participants.add(trade.sellerBeneficiaryId());
        return true;
    }

    @Override
    public synchronized PriceQuote quote(String assetId, long day) {
        Asset asset = require(assetId);
        asset.roll(day);
        int validDays = 0;
        int participants = 0;
        long last = -1;
        long low = Long.MAX_VALUE;
        long high = 0;
        BigInteger total = BigInteger.ZERO;
        for (Candle candle : asset.candles) {
            if (candle == null || candle.day() < day - WINDOW_DAYS || candle.day() >= day) continue;
            validDays++;
            participants += candle.participants();
            last = Math.max(last, candle.day());
            low = Math.min(low, candle.vwap());
            high = Math.max(high, candle.vwap());
            total = total.add(BigInteger.valueOf(candle.vwap()));
        }
        String reason = validDays < MIN_DAYS ? "insufficient_completed_days"
                : day - last > 2 ? "stale_reference" : "single_venue_14_day_trimmed_vwap";
        if (validDays < MIN_DAYS || day - last > 2) {
            return new PriceQuote(assetId, day, asset.lastIndex, asset.lastIndex, 0,
                    Quality.PENDING, false, reason, last, SOURCE_ID);
        }
        long index = total.subtract(BigInteger.valueOf(low)).subtract(BigInteger.valueOf(high))
                .divide(BigInteger.valueOf(validDays - 2L)).longValueExact();
        asset.lastIndex = index;
        int maximum = validDays == WINDOW_DAYS && day - asset.listedDay >= 30 && participants >= 112 ? 10 : 3;
        return new PriceQuote(assetId, day, index, index, maximum, Quality.SINGLE_VENUE,
                true, reason, last, SOURCE_ID);
    }

    private Asset require(String assetId) {
        Asset asset = assets.get(Objects.requireNonNull(assetId, "assetId"));
        if (asset == null) throw new IllegalArgumentException("unknown oracle asset");
        return asset;
    }

    private record Candle(long day, long vwap, int participants) { }

    private static final class Asset {
        private final long listedDay;
        private final Candle[] candles = new Candle[WINDOW_DAYS];
        private final Set<String> participants = new HashSet<>(16);
        private long bucketDay = -1;
        private long notional;
        private long lots;
        private int samples;
        private long lastIndex;

        private Asset(long listedDay) { this.listedDay = listedDay; }

        private void roll(long day) {
            if (day < listedDay || day < bucketDay) throw new IllegalArgumentException("oracle clock regression");
            if (day == bucketDay) return;
            if (bucketDay >= 0) {
                int slot = (int) (bucketDay % WINDOW_DAYS);
                candles[slot] = samples >= MIN_DAY_SAMPLES && notional >= MIN_DAY_NOTIONAL_CENTS
                        ? new Candle(bucketDay, notional / lots, participants.size()) : null;
            }
            bucketDay = day;
            notional = 0;
            lots = 0;
            samples = 0;
            participants.clear();
        }
    }
}
