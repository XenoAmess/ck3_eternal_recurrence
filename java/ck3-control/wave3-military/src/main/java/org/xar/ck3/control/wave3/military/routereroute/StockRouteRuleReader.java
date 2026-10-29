package org.xar.ck3.control.wave3.military.routereroute;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.regex.Pattern;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.FixedPoint;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.StockRules;

/** Reads the exact local vanilla defines source. It does not assert that an installed game's AI used these rules. */
public final class StockRouteRuleReader {
    private StockRouteRuleReader() { }
    public static StockRules read(Path path, String expectedSha256) throws IOException {
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(path)
                || Files.size(path) > 262_144) { throw new IOException("bounded exact vanilla source required"); }
        byte[] bytes = Files.readAllBytes(path);
        if (!sha256(bytes).equals(expectedSha256)) { throw new IOException("vanilla define source SHA drift"); }
        String source = new String(bytes, StandardCharsets.UTF_8);
        StockRules rules = new StockRules(integer(source, "MIN_PATH_COST_TO_CONSIDER_WATER_PATH"),
                integer(source, "MIN_PATH_COST_SAVINGS_TO_CONSIDER_WATER_PATH"),
                integer(source, "MIN_PATH_COST_TO_CONSIDER_WATER_PATH_FOR_GHW"),
                integer(source, "MIN_PATH_COST_SAVINGS_TO_CONSIDER_WATER_PATH_FOR_GHW"),
                integer(source, "MAX_PATH_COST_FACTOR"), fixed(source, "MAX_PATH_COST_FACTOR_TO_CONSIDER_WATER_PATH"),
                integer(source, "MIN_GOALS_PER_STACK"), fixed(source, "AVOID_BAD_ADJACENCY_MAX_PATHFIND_EXTRA_COST"),
                integer(source, "PLAYER_SUPPORT_IGNORE_BAD_SUPPLY_WITHIN_STEPS"), expectedSha256);
        if (!sha256(Files.readAllBytes(path)).equals(expectedSha256)) { throw new IOException("vanilla source changed while reading"); }
        return rules;
    }
    private static String token(String source, String key) {
        var matcher = Pattern.compile("(?m)^\\s*" + Pattern.quote(key) + "\\s*=\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(?:#.*)?$").matcher(source);
        if (!matcher.find()) { throw new IllegalArgumentException("required stock route define missing: " + key); }
        String value = matcher.group(1);
        if (matcher.find()) { throw new IllegalArgumentException("ambiguous stock route define: " + key); }
        return value;
    }
    private static int integer(String source, String key) { return new BigDecimal(token(source, key)).intValueExact(); }
    private static FixedPoint fixed(String source, String key) {
        return new FixedPoint(new BigDecimal(token(source, key)).multiply(BigDecimal.valueOf(FixedPoint.SCALE)).longValueExact());
    }
    public static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException(failure); }
    }
}
