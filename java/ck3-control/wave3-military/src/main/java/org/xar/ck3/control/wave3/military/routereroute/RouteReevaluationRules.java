package org.xar.ck3.control.wave3.military.routereroute;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.FixedPoint;

/** Additional exact vanilla source declarations. Native AI scheduling and full caller order remain unqualified. */
public record RouteReevaluationRules(FixedPoint badAdjacencyPredictionRatio, FixedPoint maximumExtraPathCost,
                                     int resupplyInterruptedCooldownDays, List<Integer> goalsPerTier, String sourceSha256) {
    public RouteReevaluationRules {
        Objects.requireNonNull(badAdjacencyPredictionRatio); Objects.requireNonNull(maximumExtraPathCost);
        StrictJson.require(badAdjacencyPredictionRatio.raw() >= 0 && maximumExtraPathCost.raw() >= 0
                && resupplyInterruptedCooldownDays >= 0, "nonnegative source declarations required");
        goalsPerTier = List.copyOf(goalsPerTier); StrictJson.require(!goalsPerTier.isEmpty(), "source tier array required");
        goalsPerTier.forEach(value -> StrictJson.require(value >= 0, "nonnegative source goal count required"));
        StrictJson.require(sourceSha256 != null && sourceSha256.matches("[0-9a-f]{64}"), "source SHA required");
    }
    public enum Hint { NATIVE_PREDICTION_REQUIRED, ALTERNATIVE_COST_REQUIRED, ALTERNATIVE_CANDIDATE, NO_ALTERNATIVE_HINT }
    /** A source-declared search hint cannot veto any ranked ordinary objective or grant a route/contact permit. */
    public Hint badAdjacencyHint(Optional<FixedPoint> nativePrediction, Optional<FixedPoint> alternativeExtraPathCost) {
        Objects.requireNonNull(nativePrediction); Objects.requireNonNull(alternativeExtraPathCost);
        nativePrediction.ifPresent(value -> StrictJson.require(value.raw() >= 0, "nonnegative observed native prediction required"));
        alternativeExtraPathCost.ifPresent(value -> StrictJson.require(value.raw() >= 0, "nonnegative observed alternative extra cost required"));
        if (nativePrediction.isEmpty()) { return Hint.NATIVE_PREDICTION_REQUIRED; }
        if (nativePrediction.orElseThrow().raw() >= badAdjacencyPredictionRatio.raw()) { return Hint.NO_ALTERNATIVE_HINT; }
        if (alternativeExtraPathCost.isEmpty()) { return Hint.ALTERNATIVE_COST_REQUIRED; }
        return alternativeExtraPathCost.orElseThrow().raw() <= maximumExtraPathCost.raw() ? Hint.ALTERNATIVE_CANDIDATE : Hint.NO_ALTERNATIVE_HINT;
    }
    public static RouteReevaluationRules read(Path sourcePath, String expectedSha256) throws IOException {
        if (!Files.isRegularFile(sourcePath, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(sourcePath)
                || Files.size(sourcePath) > 262_144) { throw new IOException("bounded exact source required"); }
        byte[] bytes = Files.readAllBytes(sourcePath);
        if (!StockRouteRuleReader.sha256(bytes).equals(expectedSha256)) { throw new IOException("reevaluation defines source drift"); }
        String source = new String(bytes, StandardCharsets.UTF_8);
        var tiers = Pattern.compile("(?ms)^\\s*GOALS_PER_TYPE\\s*=\\s*\\{([^}]*)}").matcher(source);
        StrictJson.require(tiers.find(), "source goal tier array missing"); String tierBody = tiers.group(1);
        StrictJson.require(!tiers.find(), "ambiguous source tier array"); List<Integer> values = new ArrayList<>();
        for (String line : tierBody.split("\\R")) {
            String token = line.split("#", 2)[0].trim(); if (!token.isEmpty()) { values.add(new BigDecimal(token).intValueExact()); }
        }
        RouteReevaluationRules rules = new RouteReevaluationRules(fixed(source, "AVOID_BAD_ADJACENCY_COMBAT_PREDICTION_RATIO"),
                fixed(source, "AVOID_BAD_ADJACENCY_MAX_PATHFIND_EXTRA_COST"),
                new BigDecimal(token(source, "RESUPPLY_COOLDOWN_DAYS")).intValueExact(), values, expectedSha256);
        if (!StockRouteRuleReader.sha256(Files.readAllBytes(sourcePath)).equals(expectedSha256)) { throw new IOException("source changed during read"); }
        return rules;
    }
    private static FixedPoint fixed(String source, String key) {
        return new FixedPoint(new BigDecimal(token(source, key)).multiply(BigDecimal.valueOf(FixedPoint.SCALE)).longValueExact());
    }
    private static String token(String source, String key) {
        var matcher = Pattern.compile("(?m)^\\s*" + Pattern.quote(key) + "\\s*=\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(?:#.*)?$").matcher(source);
        StrictJson.require(matcher.find(), "required source define missing: " + key); String value = matcher.group(1);
        StrictJson.require(!matcher.find(), "ambiguous source define: " + key); return value;
    }
}
