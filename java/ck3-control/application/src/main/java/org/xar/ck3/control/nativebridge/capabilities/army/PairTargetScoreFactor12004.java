package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Exact 1A09040 stage, reached at three original pair-score callsites. No candidate/action or win odds. */
public final class PairTargetScoreFactor12004 {
    public static final long SCALE = 100_000;
    private PairTargetScoreFactor12004() { }
    public enum CallSite {
        FIRST(0x1A0874B), SECOND(0x1A0881F), THIRD(0x1A088C4);
        private final int rva;
        CallSite(int rva) { this.rva = rva; }
        public int rva() { return rva; }
        public static CallSite fromRva(int rva) {
            return switch (rva) { case 0x1A0874B -> FIRST; case 0x1A0881F -> SECOND; case 0x1A088C4 -> THIRD;
                default -> throw new IllegalArgumentException("unregistered pair-score factor caller"); };
        }
    }
    public record Parameters(long idealEnemyPowerRaw, int definitionScoreRaw) { }
    public record Inputs(Scope scope, CallSite callSite, long amountARaw,
                         OptionalLong amountBRaw, Optional<Parameters> parameters) {
        public Inputs {
            Objects.requireNonNull(scope); Objects.requireNonNull(callSite); Objects.requireNonNull(amountBRaw); Objects.requireNonNull(parameters);
            if (amountARaw <= 0) {
                if (amountBRaw.isPresent() || parameters.isPresent()) throw new IllegalArgumentException("first zero branch must not invent unobserved inputs");
            } else {
                if (amountBRaw.isEmpty()) throw new IllegalArgumentException("positive first amount demands second input");
                if ((amountBRaw.getAsLong() > 0) != parameters.isPresent()) throw new IllegalArgumentException("native positive branch parameter demands differ");
            }
        }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); CallSite callSite(); }
    public record Available(Inputs inputs) implements Observation {
        public Available { Objects.requireNonNull(inputs); }
        @Override public Scope scope() { return inputs.scope(); }
        @Override public CallSite callSite() { return inputs.callSite(); }
    }
    public record Incomplete(Scope scope, CallSite callSite, String reason) implements Observation {
        public Incomplete {
            Objects.requireNonNull(scope); Objects.requireNonNull(callSite); Objects.requireNonNull(reason);
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic required");
        }
    }
    public enum Branch { FIRST_NONPOSITIVE, SECOND_NONPOSITIVE, LOWER_BLEND, UPPER_GAP }
    public sealed interface Result permits WeightedFactor, NotReady { }
    public record WeightedFactor(long amountRaw, Branch branch) implements Result {
        public WeightedFactor { Objects.requireNonNull(branch); }
    }
    public record NotReady(String reason) implements Result { public NotReady { Objects.requireNonNull(reason); } }

    /** Existing shared HIGH-operand native arithmetic; this leaf does not introduce a second fixed-point library. */
    public static Result consume(Scope actualUpdate, CallSite actualCaller, Observation originalRead) {
        Objects.requireNonNull(actualUpdate); Objects.requireNonNull(actualCaller); Objects.requireNonNull(originalRead);
        if (!actualUpdate.equals(originalRead.scope()) || actualCaller != originalRead.callSite())
            return new NotReady("coordinator_update_caller_or_source_changed");
        if (originalRead instanceof Incomplete missing) return new NotReady(missing.reason());
        Inputs i = ((Available) originalRead).inputs();
        if (i.amountARaw() <= 0) return new WeightedFactor(0, Branch.FIRST_NONPOSITIVE);
        long b = i.amountBRaw().orElseThrow();
        if (b <= 0) return new WeightedFactor(0, Branch.SECOND_NONPOSITIVE);
        Parameters p = i.parameters().orElseThrow();
        long ideal = LandStockPolicy.nativeFixedMultiply(i.amountARaw(), p.idealEnemyPowerRaw());
        final long factor; final Branch branch;
        if (b <= ideal) {
            long ratio = LandStockPolicy.nativeFixedDivide(b, ideal).value().longValueExact();
            factor = LandStockPolicy.nativeFixedMultiply(ratio, 50_000) + 50_000;
            branch = Branch.LOWER_BLEND;
        } else {
            // Preserve original A - B, not ideal - B. The original zero-divisor result is positive uint32 max.
            factor = LandStockPolicy.nativeFixedDivide(i.amountARaw() - b, ideal).value().longValueExact();
            branch = Branch.UPPER_GAP;
        }
        long clamped = Math.min(SCALE, Math.max(0, factor));
        return new WeightedFactor(LandStockPolicy.nativeFixedMultiply((long) p.definitionScoreRaw() * SCALE, clamped), branch);
    }

    public static Observation decode(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "scope", "caller_rva", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 1) throw new IllegalArgumentException("pair factor schema version");
        Scope scope = LocalTargetScore12004.scope(n.get("scope")); CallSite site = CallSite.fromRva(i32(n.get("caller_rva")));
        String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be explicit null");
            return new Incomplete(scope, site, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("pair factor discriminant");
        ObjectNode f = closed(n.get("facts"), "amount_a_raw", "amount_b_raw", "parameters");
        long a = signed64(text(f.get("amount_a_raw")));
        OptionalLong b = f.get("amount_b_raw").isNull() ? OptionalLong.empty() : OptionalLong.of(signed64(text(f.get("amount_b_raw"))));
        Optional<Parameters> parameters;
        if (f.get("parameters").isNull()) parameters = Optional.empty();
        else {
            ObjectNode p = closed(f.get("parameters"), "ideal_enemy_power_raw", "definition_score_raw");
            parameters = Optional.of(new Parameters(signed64(text(p.get("ideal_enemy_power_raw"))), i32(p.get("definition_score_raw"))));
        }
        return new Available(new Inputs(scope, site, a, b, parameters));
    }
    public static byte[] encode(Observation observation) {
        ObjectNode n = empty(); n.put("schema_version", 1); n.set("scope", LocalTargetScore12004.encodeScope(observation.scope())); n.put("caller_rva", observation.callSite().rva());
        if (observation instanceof Incomplete missing) { n.put("status", "incomplete"); n.put("reason", missing.reason()); n.putNull("facts"); return bytes(n); }
        Inputs i = ((Available) observation).inputs(); n.put("status", "available"); n.putNull("reason"); ObjectNode f = n.putObject("facts");
        f.put("amount_a_raw", Long.toString(i.amountARaw()));
        if (i.amountBRaw().isEmpty()) f.putNull("amount_b_raw"); else f.put("amount_b_raw", Long.toString(i.amountBRaw().getAsLong()));
        if (i.parameters().isEmpty()) f.putNull("parameters");
        else { Parameters p = i.parameters().orElseThrow(); ObjectNode row = f.putObject("parameters"); row.put("ideal_enemy_power_raw", Long.toString(p.idealEnemyPowerRaw())); row.put("definition_score_raw", p.definitionScoreRaw()); }
        return bytes(n);
    }
    static long signed64(String value) {
        if (!value.matches("0|-?[1-9][0-9]{0,18}")) throw new IllegalArgumentException("canonical signed64 decimal string required");
        try { return Long.parseLong(value); } catch (NumberFormatException error) { throw new IllegalArgumentException("signed64 outside native width", error); }
    }
}
