package org.xar.ck3.control.g2.m0;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Comparison;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Decision;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Immediate;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.ImmediateOption;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Input;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Outcome;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Power;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.PowerRelation;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Status;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.TailParameters;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Terminal;

/** Finite executable regression of original-v7 decision boundaries; original-producer differential is separate. */
public final class M0DomainVerification {
    private static int checks;
    private M0DomainVerification() { }

    public static void main(String[] arguments) {
        if (arguments.length != 0) { throw new IllegalArgumentException("M0 domain verification has no runtime arguments"); }
        M0Frame frame = frame(BigInteger.TWO, 33);
        Input baseline = input(frame, -1, 364, PowerRelation.ACTOR_STRONGER, 250_000, 100_000,
                -10, true, -20, true, 4);
        Decision ordinary = RaiktorThreeWayEvaluation.evaluate(baseline);
        equal(Outcome.CONTINUE, ordinary.comparison().recommendedOutcome().orElseThrow(), "ordinary continue winner");
        equal(BigInteger.valueOf(5), ordinary.comparison().winningMarginRaw().orElseThrow(), "top two margin");
        equal(List.of(Outcome.CONTINUE, Outcome.WHITE_PEACE, Outcome.SURRENDER), ordinary.comparison().eligibleOptions(),
                "original candidate insertion order");
        check(!ordinary.continueOption().campaignOutcomeForecastReady(), "power relation is not a forecast");
        check(!ordinary.continueOption().tailRiskPowerScaleApplied(), "actor stronger never long-war scales");

        Decision terminal = RaiktorThreeWayEvaluation.evaluate(input(frame, -100, 400,
                PowerRelation.ACTOR_STRONGER, 250_000, 100_000, 1_000_000, false, -20, true, 4));
        equal(List.of("opponent_has_enforceable_terminal_war_score"), terminal.continueOption().executionBlockers(),
                "native terminal score excludes continue");
        check(!terminal.continueOption().eligible(), "terminal continue is ineligible despite utility");
        equal(Outcome.SURRENDER, terminal.comparison().recommendedOutcome().orElseThrow(), "only legal budget-eligible terminal");
        equal(Optional.empty(), terminal.comparison().winningMarginRaw(), "sole candidate retains null margin");

        Decision unavailable = RaiktorThreeWayEvaluation.evaluate(input(frame, -100, 400,
                PowerRelation.ACTOR_STRONGER, 250_000, 100_000, 10, false, 20, false, 1));
        equal(Status.THREE_WAY_UNDERDETERMINED, unavailable.comparison().status(), "no eligible exit stays unknown");
        equal(Optional.empty(), unavailable.comparison().recommendedOutcome(), "unavailable routes cannot create an action");

        Decision tied = RaiktorThreeWayEvaluation.evaluate(input(frame, -100, 400,
                PowerRelation.EQUAL, 100_000, 100_000, -10, true, -10, true, 1));
        equal(Optional.empty(), tied.comparison().recommendedOutcome(), "insufficient margin remains underdetermined");
        equal(BigInteger.ZERO, tied.comparison().winningMarginRaw().orElseThrow(), "tie margin is exact zero");
        Decision zeroMargin = RaiktorThreeWayEvaluation.evaluate(input(frame, -100, 400,
                PowerRelation.EQUAL, 100_000, 100_000, -10, true, -10, true, 0));
        equal(Outcome.SURRENDER, zeroMargin.comparison().recommendedOutcome().orElseThrow(),
                "original lexical tie order remains surrender before white_peace at owner zero margin");

        Decision longLosing = RaiktorThreeWayEvaluation.evaluate(input(frame, -1, 365,
                PowerRelation.OPPONENT_STRONGER, 250_000, 100_000, -50, true, -75, true, 1));
        equal(BigInteger.valueOf(100), longLosing.continueOption().tailRiskPenaltyRaw(), "observed ratio scales long losing tail");
        equal(Outcome.WHITE_PEACE, longLosing.comparison().recommendedOutcome().orElseThrow(), "white peace comparison uses existing utility");
        Decision shortLosing = RaiktorThreeWayEvaluation.evaluate(input(frame, -1, 364,
                PowerRelation.OPPONENT_STRONGER, 250_000, 100_000, -50, true, -75, true, 1));
        equal(BigInteger.valueOf(40), shortLosing.continueOption().tailRiskPenaltyRaw(), "one day below horizon keeps base penalty");
        equal(Outcome.CONTINUE, shortLosing.comparison().recommendedOutcome().orElseThrow(), "short-horizon continuation stays original");
        Decision notLosing = RaiktorThreeWayEvaluation.evaluate(input(frame, 0, 365,
                PowerRelation.OPPONENT_STRONGER, 250_000, 100_000, -50, true, -75, true, 1));
        check(!notLosing.continueOption().tailRiskPowerScaleApplied(), "zero score cannot trigger losing-war scale");

        TailParameters fortyOne = new TailParameters(bi(365), bi(41), bi(10), bi(5));
        Decision floored = RaiktorThreeWayEvaluation.evaluate(new Input(longInput(frame).immediate(),
                new Power(frame, PowerRelation.OPPONENT_STRONGER, bi(250_001), bi(100_000), true),
                fortyOne, longInput(frame).terminal()));
        equal(bi(102), floored.continueOption().tailRiskPenaltyRaw(), "integer floor division matches Python nonnegative //");

        rejects(() -> new Power(frame, PowerRelation.EQUAL, bi(1), BigInteger.ZERO, true), "zero ratio scale rejected");
        rejects(() -> new TailParameters(bi(-1), bi(1), bi(1), bi(1)), "negative horizon rejected");
        rejects(() -> new Terminal(frame, bi(-100), bi(-100), bi(100), bi(1), false, true), "terminal classification must bind score");
        rejects(() -> new Terminal(frame, bi(-1), bi(-2), bi(2), bi(1), false, true), "absolute and player scores must agree");
        rejects(() -> RaiktorThreeWayEvaluation.evaluate(new Input(longInput(frame).immediate(),
                new Power(frame, PowerRelation.OPPONENT_STRONGER, bi(50_000), bi(100_000), true),
                model(), longInput(frame).terminal())), "opponent stronger cannot reduce penalty through ratio");
        rejects(() -> RaiktorThreeWayEvaluation.evaluate(new Input(longInput(frame).immediate(),
                new Power(frame, PowerRelation.OPPONENT_STRONGER, bi(200_000), bi(100_000), true),
                new TailParameters(bi(1), BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE), bi(1), bi(1)),
                longInput(frame).terminal())), "scaled penalty int64 overflow rejected");
        M0Frame changed = frame(BigInteger.valueOf(3), 33);
        rejects(() -> new Input(baseline.immediate(), new Power(changed, PowerRelation.EQUAL, bi(1), bi(1), true),
                model(), baseline.terminal()), "power frame drift rejected");
        rejects(() -> new Input(baseline.immediate(), baseline.power(), model(),
                new Terminal(changed, bi(-1), bi(-1), bi(1), bi(1), false, true)), "terminal frame drift rejected");

        equal(Integer.MIN_VALUE, frame(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE), Integer.MIN_VALUE).warId(),
                "negative signed full-generation ID retained");
        rejects(() -> frame(BigInteger.ONE.shiftLeft(64), 33), "uint64 overflow rejected");
        rejects(() -> frame(BigInteger.TWO, -1), "invalid full-generation sentinel rejected");

        Input synthetic = new Input(new Immediate(frame, baseline.immediate().whitePeace(), baseline.immediate().surrender(), bi(4), false),
                new Power(frame, baseline.power().relation(), baseline.power().actualPowerRatioRaw(), baseline.power().fixedPointScale(), false),
                model(), new Terminal(frame, bi(-1), bi(-1), bi(1), bi(364), false, false));
        equal(ordinary.comparison(), RaiktorThreeWayEvaluation.evaluate(synthetic).comparison(),
                "source eligibility does not rewrite static policy or grant submission authority");
        System.out.println("{\"schema\":\"xar.g2-m0-domain-verification/v1\",\"checks_passed\":" + checks
                + ",\"failed\":0,\"skipped\":0,\"game_calls\":0,\"scope\":\"pure_domain_boundaries_only\"}");
    }

    private static Input longInput(M0Frame frame) {
        return input(frame, -1, 400, PowerRelation.OPPONENT_STRONGER, 250_000, 100_000, -10, true, -20, true, 1);
    }
    private static Input input(M0Frame frame, int score, int days, PowerRelation relation, int ratio, int scale,
            int whiteUtility, boolean whiteEligible, int surrenderUtility, boolean surrenderEligible, int margin) {
        return new Input(new Immediate(frame, new ImmediateOption(bi(whiteUtility), whiteEligible, List.of()),
                new ImmediateOption(bi(surrenderUtility), surrenderEligible, List.of()), bi(margin), true),
                new Power(frame, relation, bi(ratio), bi(scale), true), model(),
                new Terminal(frame, bi(score), bi(score), bi(-score), bi(days), score <= -100, true));
    }
    private static TailParameters model() { return new TailParameters(bi(365), bi(40), bi(10), bi(5)); }
    private static M0Frame frame(BigInteger nativeRevision, int warId) {
        return new M0Frame("snapshot", BigInteger.ONE, nativeRevision, Integer.MIN_VALUE, "connection-generation:2", "episode", 77,
                true, warId, 17, "raiktor_claim_cb", 100, 200, 100);
    }
    private static BigInteger bi(long value) { return BigInteger.valueOf(value); }
    private static void equal(Object expected, Object actual, String description) {
        check(expected.equals(actual), description + " expected=" + expected + " actual=" + actual);
    }
    private static void check(boolean condition, String description) {
        if (!condition) { throw new AssertionError(description); } checks++;
    }
    private static void rejects(Runnable body, String description) {
        try { body.run(); } catch (IllegalArgumentException expected) { checks++; return; }
        throw new AssertionError(description);
    }
}
