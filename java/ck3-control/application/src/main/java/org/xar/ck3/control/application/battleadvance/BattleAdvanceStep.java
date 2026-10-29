package org.xar.ck3.control.application.battleadvance;

import java.math.BigInteger;
import java.util.Optional;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact public spellings from war_contract.py, never a Native DLL command. */
public sealed interface BattleAdvanceStep permits BattleAdvanceStep.Battle, BattleAdvanceStep.Route, BattleAdvanceStep.Hold {
    String literal();
    int speed();
    Optional<BigInteger> requestedTarget();
    enum Scope { ACTIVE_BATTLE, COMMITTED_ROUTE, STATIONARY_OBJECTIVE_HOLD, ROUTE_CONTACT_WINDOW }
    Scope scope();
    Pattern DECISION = Pattern.compile("battle-decision-epoch-advance-to-([1-9][0-9]*)");
    Pattern ROUTE = Pattern.compile("committed-route-sentinel-advance-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)-until-([1-9][0-9]*)(?:-speed-([1245]))?");
    Pattern HOLD = Pattern.compile("war-objective-hold-sentinel-advance-war-([1-9][0-9]*)-army-(0|[1-9][0-9]*)-at-([1-9][0-9]*)-until-([1-9][0-9]*)(?:-speed-([1245]))?");

    record Battle(String literal, Optional<BigInteger> requestedTarget, boolean terminal) implements BattleAdvanceStep {
        public Battle {
            requestedTarget = java.util.Objects.requireNonNull(requestedTarget); requestedTarget.ifPresent(value -> date(value.toString()));
            String expected = terminal ? "battle-terminal-cruise" : requestedTarget.map(value -> "battle-decision-epoch-advance-to-" + value).orElse("battle-decision-epoch-advance");
            StrictJson.require((!terminal || requestedTarget.isEmpty()) && expected.equals(literal), "battle step literal/typed binding differs");
        }
        @Override public int speed() { return terminal ? 5 : 3; }
        @Override public Scope scope() { return Scope.ACTIVE_BATTLE; }
    }
    record Route(String literal, int armyId, int targetProvinceId, BigInteger targetDateRaw, int speed) implements BattleAdvanceStep {
        public Route {
            StrictJson.require(armyId >= 0 && targetProvinceId > 0 && speed >= 1 && speed <= 5, "route signed identity/speed required"); date(targetDateRaw.toString());
            StrictJson.require(literal.equals("committed-route-sentinel-advance-army-" + armyId + "-to-" + targetProvinceId + "-until-" + targetDateRaw + suffix(speed)), "route step literal/typed binding differs");
        }
        @Override public Optional<BigInteger> requestedTarget() { return Optional.of(targetDateRaw); }
        @Override public Scope scope() { return Scope.COMMITTED_ROUTE; }
    }
    record Hold(String literal, int warId, int armyId, int objectiveProvinceId, BigInteger targetDateRaw, int speed) implements BattleAdvanceStep {
        public Hold {
            StrictJson.require(warId > 0 && armyId >= 0 && objectiveProvinceId > 0 && speed >= 1 && speed <= 5, "hold signed identity/speed required"); date(targetDateRaw.toString());
            StrictJson.require(literal.equals("war-objective-hold-sentinel-advance-war-" + warId + "-army-" + armyId + "-at-" + objectiveProvinceId + "-until-" + targetDateRaw + suffix(speed)), "hold step literal/typed binding differs");
        }
        @Override public Optional<BigInteger> requestedTarget() { return Optional.of(targetDateRaw); }
        @Override public Scope scope() { return Scope.STATIONARY_OBJECTIVE_HOLD; }
    }
    static Optional<BattleAdvanceStep> parse(String literal) {
        if (literal == null) return Optional.empty();
        if (literal.equals("battle-decision-epoch-advance")) return Optional.of(new Battle(literal, Optional.empty(), false));
        if (literal.equals("battle-terminal-cruise")) return Optional.of(new Battle(literal, Optional.empty(), true));
        try {
            Matcher m = DECISION.matcher(literal);
            if (m.matches()) return Optional.of(new Battle(literal, Optional.of(date(m.group(1))), false));
            m = ROUTE.matcher(literal);
            if (m.matches()) return Optional.of(new Route(literal, id(m.group(1), true), id(m.group(2), false), date(m.group(3)), speed(m.group(4))));
            m = HOLD.matcher(literal);
            if (m.matches()) return Optional.of(new Hold(literal, id(m.group(1), false), id(m.group(2), true), id(m.group(3), false), date(m.group(4)), speed(m.group(5))));
            return Optional.empty();
        } catch (IllegalArgumentException error) { return Optional.empty(); }
    }
    private static int id(String token, boolean zero) {
        BigInteger value = new BigInteger(token);
        StrictJson.require(value.compareTo(BigInteger.valueOf(zero ? 0 : 1)) >= 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "signed int32 identity required");
        return value.intValueExact();
    }
    private static BigInteger date(String token) {
        BigInteger value = new BigInteger(token);
        StrictJson.require(value.signum() > 0 && value.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "positive signed int64 date required");
        return value;
    }
    private static int speed(String token) { return token == null ? 3 : Integer.parseInt(token); }
    private static String suffix(int speed) { return speed == 3 ? "" : "-speed-" + speed; }
}
