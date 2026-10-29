package org.xar.ck3.control.wave2.finance.holyloan;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

/** Complete pure _loan_financing_input consumer. Same-frame copied observations never become spendable funds. */
public final class LoanFinancingCodec {
    private LoanFinancingCodec() { }
    public sealed interface LoanInput permits NotProvided, Refused, Projected { }
    public record NotProvided() implements LoanInput { }
    public record Refused(Reason reason) implements LoanInput { }
    public enum Reason {
        FRAME_UNQUALIFIED("loan_complete_planning_source_frame_unqualified"), CASH_UNQUALIFIED("loan_cash_input_unqualified");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record PlanningFrame(String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
            BigInteger actorCharacterId, String episodeRunId, BigInteger bridgePid, BigInteger connectionGeneration) { }
    /** Exact existing three-field wire wrapper; JSON nodes are copied at this SDK boundary. */
    public record Request(JsonNode snapshot, JsonNode cashResources, JsonNode cashSourceFrame) {
        public Request {
            StrictJson.require(snapshot != null && snapshot.isObject(), "financing snapshot object required");
            snapshot = snapshot.deepCopy();
            cashResources = Objects.requireNonNull(cashResources, "cashResources").deepCopy();
            cashSourceFrame = Objects.requireNonNull(cashSourceFrame, "cashSourceFrame").deepCopy();
        }
        @Override public JsonNode snapshot() { return snapshot.deepCopy(); }
        @Override public JsonNode cashResources() { return cashResources.deepCopy(); }
        @Override public JsonNode cashSourceFrame() { return cashSourceFrame.deepCopy(); }
    }
    /** Private construction binds the typed loan to the exact full planning frame checked by this consumer. */
    public static final class Projected implements LoanInput {
        private final PlanningFrame planningFrame;
        private final RawCashCodec.LoanObservation observation;
        private final byte[] wire;
        private Projected(PlanningFrame planningFrame, RawCashCodec.LoanObservation observation, byte[] wire) {
            this.planningFrame = planningFrame; this.observation = observation; this.wire = wire.clone();
        }
        public PlanningFrame planningFrame() { return planningFrame; }
        public RawCashCodec.LoanObservation observation() { return observation; }
        public byte[] toJson() { return wire.clone(); }
    }

    /** Exact new wrapper; its existing snapshot/cash SDK containers retain their own extension semantics. */
    public static Request parse(byte[] bytes) {
        JsonNode input = StrictJson.object(StrictJson.parse(bytes), Set.of("snapshot", "cash_resources", "cash_source_frame"));
        return new Request(input.get("snapshot"), input.get("cash_resources"), input.get("cash_source_frame"));
    }
    public static LoanInput decodeAndProject(byte[] bytes) { return project(parse(bytes)); }

    public static LoanInput project(Request request) {
        Objects.requireNonNull(request, "request");
        JsonNode snapshot = request.snapshot, cash = request.cashResources, source = request.cashSourceFrame;
        if (cash.isNull() && source.isNull()) { return new NotProvided(); }
        JsonNode diagnostics = snapshot.get("diagnostics"), played = snapshot.get("played_character");
        ObjectNode expected = StrictJson.object(); expected.put("schema", "xar.ck3.planning-source-frame/v1"); expected.put("status", "complete");
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")) {
            expected.set(key, snapshot.has(key) ? snapshot.get(key) : StrictJson.object().nullNode());
        }
        expected.set("actor_character_id", part(played, "character_id")); expected.set("bridge_pid", part(diagnostics, "bridge_pid"));
        expected.set("connection_generation", part(diagnostics, "connection_generation"));
        boolean qualified = flag(snapshot, "paused") && flag(snapshot, "map_ready") && cash.isObject() && source.isObject()
                && textValue(expected.get("snapshot_id")) && textValue(expected.get("episode_run_id")) && expected.equals(source);
        for (String key : List.of("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation")) {
            int minimum = key.equals("native_revision") || key.equals("actor_character_id") || key.equals("bridge_pid") ? 1 : 0;
            JsonNode value = expected.get(key); qualified &= value.isIntegralNumber() && value.bigIntegerValue().compareTo(BigInteger.valueOf(minimum)) >= 0;
        }
        for (String key : List.of("snapshot_id", "revision", "native_revision")) {
            JsonNode queried = cash.isObject() ? cash.get("queried_" + key) : null, value = expected.get(key);
            qualified &= queried != null && queried.getNodeType() == value.getNodeType() && queried.equals(value);
        }
        if (!qualified) { return new Refused(Reason.FRAME_UNQUALIFIED); }
        RawCashCodec.NormalizedCurrentCash normalized;
        try { normalized = RawCashCodec.normalize(serialize(cash), serialize(snapshot)); }
        catch (ContractViolationException error) { return new Refused(Reason.CASH_UNQUALIFIED); }
        if (!normalized.loanObservation().known()) { return new NotProvided(); }
        JsonNode loan = StrictJson.parse(normalized.toJson()).get(RawCashCodec.LOAN_KEY); ObjectNode output = ((ObjectNode) loan).deepCopy();
        output.set("planning_source_frame", expected);
        PlanningFrame frame = new PlanningFrame(expected.get("snapshot_id").textValue(), expected.get("revision").bigIntegerValue(),
                expected.get("native_revision").bigIntegerValue(), expected.get("date_raw").bigIntegerValue(),
                expected.get("actor_character_id").bigIntegerValue(), expected.get("episode_run_id").textValue(),
                expected.get("bridge_pid").bigIntegerValue(), expected.get("connection_generation").bigIntegerValue());
        return new Projected(frame, normalized.loanObservation().value(), serialize(output));
    }
    public static byte[] encode(LoanInput input) {
        if (input instanceof NotProvided) { return new byte[] {'n', 'u', 'l', 'l'}; }
        if (input instanceof Refused refused) { return RawCashCodec.unavailableLoanObservation(refused.reason().wire()); }
        return ((Projected) input).toJson();
    }
    private static JsonNode part(JsonNode node, String key) {
        return node != null && node.isObject() && node.has(key) ? node.get(key) : StrictJson.object().nullNode();
    }
    private static boolean flag(JsonNode node, String key) { return node.has(key) && node.get(key).isBoolean() && node.get(key).booleanValue(); }
    private static boolean textValue(JsonNode node) { return node.isTextual() && !node.textValue().isEmpty(); }
    private static byte[] serialize(JsonNode node) {
        return SdkProjectionJson.encode(node);
    }
}
