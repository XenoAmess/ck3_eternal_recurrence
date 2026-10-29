package org.xar.ck3.control.g2.m5;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m5.M5Research.ExistingWarPlan;
import org.xar.ck3.control.g2.m5.M5Research.MissingPlan;
import org.xar.ck3.control.g2.m5.M5Research.NullPlan;
import org.xar.ck3.control.g2.m5.M5Research.ObservedPlan;
import org.xar.ck3.control.g2.m5.M5Research.Result;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;
import org.xar.ck3.control.wave2.finance.warcash.WarcashCodec;
import org.xar.ck3.control.wave2.finance.warcash.WarcashModel;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreatsCodec;

/** Strict M5 composition boundary and durable JSON representation; no file or action port. */
public final class M5PayloadCodec {
    public static final int MAXIMUM_BYTES = ProjectionJson.MAX_BYTES;
    public static final String RESULT_SCHEMA = "xar.g2-m5-research-result/v1";
    public static final String OPERATION_SCHEMA = "xar.g2-m5-request/v1";
    private static final String PLAN = "existing_war_plan";
    private static final JsonFactory FACTORY = JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private static final Obj SCOPE = scope();

    private M5PayloadCodec() { }

    public sealed interface OperationRequest permits ContextRequest, LifecycleRequest { }
    public record ContextRequest(Request context) implements OperationRequest {
        public ContextRequest { Objects.requireNonNull(context, "M5 context request"); }
    }
    public record LifecycleRequest(ProjectionJson payload) implements OperationRequest {
        public LifecycleRequest { Objects.requireNonNull(payload, "M5 lifecycle request"); require(payload.isObject(), "M5 lifecycle object required"); }
    }

    public static OperationRequest decodeOperation(byte[] raw) {
        Obj operation = parseObject(raw, "M5 operation");
        require(operation.members().keySet().equals(Set.of("schema", "operation", "request")), "exact M5 operation fields required");
        require(new Text(OPERATION_SCHEMA).equals(operation.get("schema")), "M5 operation schema required");
        byte[] request = OpportunityJson.encode(object(operation.get("request"), "M5 operation request"));
        return switch (text(operation.get("operation"), "M5 operation")) {
            case "decision_context" -> new ContextRequest(decodeRequest(request));
            case "proposal_lifecycle" -> new LifecycleRequest(ProjectionJson.object(request, MAXIMUM_BYTES));
            default -> throw new IllegalArgumentException("unknown M5 operation");
        };
    }

    public static byte[] encodeContextOperation(Request context) {
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("schema", new Text(OPERATION_SCHEMA));
        fields.put("operation", new Text("decision_context"));
        fields.put("request", parseObject(encodeRequest(context), "M5 context request"));
        return checkedEncode(new Obj(fields));
    }

    public record Request(Obj intakeRequest, ExistingWarPlan existingWarPlan) {
        public Request {
            Objects.requireNonNull(intakeRequest, "original intake request");
            Objects.requireNonNull(existingWarPlan, "existing war plan presence");
            require(intakeRequest.members().keySet().equals(Set.of("schema", "snapshot", "sources")),
                    "exact original M5 intake request fields required");
            require(new Text(FormalProposalIntake.REQUEST_SCHEMA).equals(intakeRequest.get("schema")),
                    "original M5 intake request schema required");
            object(intakeRequest.get("snapshot"), "original intake snapshot");
            object(intakeRequest.get("sources"), "original intake sources");
        }
    }

    public static Request decodeRequest(byte[] raw) {
        Obj payload = parseObject(raw, "M5 payload");
        exactFields(payload, Set.of("intake_request"), "M5 payload");
        return new Request(object(payload.get("intake_request"), "original intake request"), plan(payload));
    }

    /** Original accepted collector outputs may exceed its smaller input boundary. */
    public static Obj decodeAnalysis(byte[] raw) {
        Obj analysis = parseObject(raw, "original intake analysis");
        validateAnalysis(analysis, false);
        return analysis;
    }

    public static byte[] encodeRequest(Request request) {
        Objects.requireNonNull(request, "M5 payload");
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("intake_request", request.intakeRequest());
        putPlan(fields, request.existingWarPlan());
        return checkedEncode(new Obj(fields));
    }

    /** The public domain entry actually reaches the sole participating-war summary consumer here. */
    public static byte[] encodeResult(Result result) {
        M5DecisionConsumer.Consumption consumption = M5DecisionConsumer.consume(result);
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("schema", new Text(RESULT_SCHEMA));
        fields.put("intake_analysis", result.intakeAnalysis());
        fields.put("participating_wars", participatingWars(result.participatingWars()));
        fields.put("scope", SCOPE);
        putPlan(fields, result.existingWarPlan());
        fields.put("decision_consumption", M5DecisionConsumer.toJson(consumption));
        return checkedEncode(new Obj(fields));
    }

    /** Recomputes the real consumer from retained evidence before accepting saved JSON. */
    public static Result decodeResult(byte[] raw) {
        Obj saved = parseObject(raw, "saved M5 result");
        exactFields(saved, Set.of("schema", "intake_analysis", "participating_wars", "scope",
                "decision_consumption"), "saved M5 result");
        require(new Text(RESULT_SCHEMA).equals(saved.get("schema")), "saved M5 result schema required");
        require(SCOPE.equals(saved.get("scope")), "saved M5 scope differs from its qualified fact boundary");
        Result result = new Result(object(saved.get("intake_analysis"), "original intake analysis"),
                ParticipatingWarThreatsCodec.decode(OpportunityJson.encode(saved.get("participating_wars"))), plan(saved));
        Obj actual = M5DecisionConsumer.toJson(M5DecisionConsumer.consume(result));
        require(actual.equals(saved.get("decision_consumption")),
                "saved M5 consumer differs from its retained original evidence");
        return result;
    }

    static Obj participatingWars(ParticipatingWarThreats.Observation observation) {
        return parseObject(ParticipatingWarThreatsCodec.encode(observation), "participating-war observation");
    }

    static void validateResult(Result result) {
        Objects.requireNonNull(result, "M5 result");
        Obj analysis = result.intakeAnalysis();
        validateAnalysis(analysis, true);
        Frame frame = frame(object(analysis.get("frame"), "original intake frame"));
        if (result.participatingWars() instanceof ParticipatingWarThreats.Observed observed) {
            require(frame.equals(observed.frame()), "participating wars crossed the original intake frame");
        } else if (result.participatingWars() instanceof ParticipatingWarThreats.Unavailable unavailable) {
            unavailable.sourceFrame().ifPresent(source -> require(frame.equals(source),
                    "unavailable participating-war diagnostic crossed the original intake frame"));
        }
        Obj selector = object(analysis.get("selector_request"), "original selector request");
        Obj snapshot = object(selector.get("snapshot"), "original selector snapshot");
        require(ParticipatingWarThreatsCodec.observeSnapshot(OpportunityJson.encode(snapshot)).equals(result.participatingWars()),
                "retained participating-war facts differ from their original snapshot");
    }

    private static void validateAnalysis(Obj analysis, boolean verifySelector) {
        Set<String> required = Set.of("schema", "projection_not_original_collection_receipt", "frame",
                "collected_domains", "collected_candidate_ids", "selector_request", "analysis",
                "resource_reservation_performed", "formal_action_ready", "selected_step");
        Set<String> optional = Set.of("war_cash_resource", "producer_family_status", "producer_faction_status", "incomplete_domains");
        require(analysis.members().keySet().containsAll(required)
                && analysis.members().keySet().stream().allMatch(key -> required.contains(key) || optional.contains(key)),
                "exact original intake analysis fields required");
        require(new Text(FormalProposalIntake.RESULT_SCHEMA).equals(analysis.get("schema")),
                "original intake analysis schema required");
        require(new Bool(true).equals(analysis.get("projection_not_original_collection_receipt")),
                "original intake projection marker required");
        require(new Bool(false).equals(analysis.get("resource_reservation_performed"))
                && new Bool(false).equals(analysis.get("formal_action_ready"))
                && analysis.get("selected_step") == Nil.INSTANCE,
                "M5 analytic result cannot acquire reservation or action authority");
        Obj selector = object(analysis.get("selector_request"), "original selector request");
        Obj intakeFrame = object(analysis.get("frame"), "original intake frame");
        require(intakeFrame.members().keySet().equals(Set.of("played_character_id", "native_revision", "date_raw",
                "snapshot_id", "revision", "episode_run_id")), "exact original intake frame fields required");
        Frame observed = frame(intakeFrame);
        require(observed.equals(frame(object(selector.get("snapshot"), "original selector snapshot"))),
                "original selector crossed the intake frame");
        List<Value> domains = new ArrayList<>(), identities = new ArrayList<>();
        for (Value value : array(selector.get("proposals"), "original collected proposals")) {
            Obj proposal = object(value, "original collected proposal");
            Text domain = new Text(text(proposal.get("domain"), "original candidate domain"));
            if (!domains.contains(domain)) domains.add(domain);
            identities.add(new Text(text(proposal.get("candidate_id"), "original candidate identity")));
        }
        require(new Arr(domains).equals(analysis.get("collected_domains"))
                && new Arr(identities).equals(analysis.get("collected_candidate_ids")),
                "original candidate identities or domain order differ from their proposals");
        object(analysis.get("analysis"), "retained original selector analysis");
        if (verifySelector) {
            Obj recomputed = parseObject(ObservedOpportunitySelector.select(OpportunityJson.encode(selector)), "original selector analysis");
            require(recomputed.equals(analysis.get("analysis")), "retained analysis differs from the original selector");
        }
        verifyRetainedWarBudget(analysis, selector, observed);
        for (String status : List.of("producer_family_status", "producer_faction_status"))
            if (analysis.members().containsKey(status)) text(analysis.get(status), status);
        if (analysis.members().containsKey("incomplete_domains")) array(analysis.get("incomplete_domains"), "original incomplete domains");
    }

    private static void verifyRetainedWarBudget(Obj analysis, Obj selector, Frame frame) {
        Obj snapshot = object(selector.get("snapshot"), "original selector snapshot");
        List<BigInteger> warIds = array(snapshot.get("active_wars"), "original active wars").stream()
                .map(value -> integer(object(value, "original active war").get("war_id"), "original WarID")).toList();
        if (warIds.isEmpty()) {
            require(!analysis.members().containsKey("war_cash_resource"), "peaceful original intake has no war budget result");
            return;
        }
        Obj raw = object(analysis.get("war_cash_resource"), "required original active-war cash budget");
        WarcashModel.Frame cashFrame = new WarcashModel.Frame(frame.playedCharacterId(), frame.nativeRevision(), frame.dateRaw(),
                frame.snapshotId(), frame.revision(), frame.episodeRunId());
        BigInteger treasury, pending, reserve;
        Obj commitments = object(selector.get("commitments"), "original commitments");
        if (warIds.size() != 1 || new Text(WarcashModel.AGGREGATE_SCHEMA).equals(raw.get("schema"))) {
            WarcashModel.AggregateReceipt receipt = WarcashCodec.verifyCompleteAggregate(OpportunityJson.toNode(raw), cashFrame, warIds);
            treasury = receipt.treasuryRaw(); pending = receipt.values().get(WarcashModel.Amount.PENDING).orElseThrow();
            reserve = receipt.jointReserve().orElseThrow(); WarcashModel.ClaimUnion occupied = receipt.occupied().orElseThrow();
            requireNumericClaims(commitments, "army_ids", occupied.armyIds());
            requireNumericClaims(commitments, "ally_character_ids", occupied.allyCharacterIds());
            requireNumericClaims(commitments, "character_ids", occupied.characterIds());
            require(array(commitments.get("commitment_keys"), "original commitment keys")
                    .containsAll(occupied.commitmentKeys().stream().map(Text::new).toList()), "saved budget omitted original occupied keys");
        } else {
            WarcashModel.SingleReceipt receipt = WarcashCodec.verifyCompleteSingle(OpportunityJson.toNode(raw), cashFrame, warIds.getFirst());
            treasury = receipt.treasuryRaw(); pending = receipt.value(WarcashModel.Amount.PENDING).orElseThrow();
            reserve = receipt.jointReserve().orElseThrow();
        }
        Obj gold = object(snapshot.get("played_character_gold"), "original treasury");
        require(new IntegerValue(BigInteger.valueOf(100000)).equals(gold.get("scale"))
                && treasury.equals(integer(gold.get("raw"), "original treasury raw")), "saved war budget treasury differs from its snapshot");
        require(integer(commitments.get("gold_raw"), "original committed gold").compareTo(pending) >= 0
                && integer(selector.get("gold_reserve_raw"), "original reserve").compareTo(reserve) >= 0,
                "saved active-war budget differs from original commitments or reserve");
    }

    private static void requireNumericClaims(Obj commitments, String field, List<BigInteger> expected) {
        require(array(commitments.get(field), field).containsAll(expected.stream().map(IntegerValue::new).toList()),
                "saved budget omitted original occupied " + field);
    }

    private static Frame frame(Obj source) {
        Value actor = source.get("played_character_id");
        if (actor == null || actor == Nil.INSTANCE)
            actor = object(source.get("played_character"), "original played character").get("character_id");
        return new Frame(integer(actor, "played character"),
                integer(source.get("native_revision"), "native revision"),
                integer(source.get("date_raw"), "date raw"), text(source.get("snapshot_id"), "snapshot id"),
                integer(source.get("revision"), "public revision"), text(source.get("episode_run_id"), "episode"));
    }

    private static ExistingWarPlan plan(Obj payload) {
        if (!payload.members().containsKey(PLAN)) return new MissingPlan();
        if (payload.get(PLAN) == Nil.INSTANCE) return new NullPlan();
        return new ObservedPlan(object(payload.get(PLAN), "existing ordinary war plan"));
    }

    static void putPlan(Map<String, Value> fields, ExistingWarPlan plan) {
        switch (plan) {
            case MissingPlan ignored -> { }
            case NullPlan ignored -> fields.put(PLAN, Nil.INSTANCE);
            case ObservedPlan observed -> fields.put(PLAN, observed.plan());
        }
    }

    private static void exactFields(Obj value, Set<String> required, String label) {
        Set<String> actual = value.members().keySet();
        require(actual.containsAll(required) && actual.stream().allMatch(key -> required.contains(key) || key.equals(PLAN)),
                "exact " + label + " fields required");
    }

    private static Obj scope() {
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("published_wars", new Text("player_participant_only"));
        fields.put("nonparticipant_liege_wars", new Text("unassessed"));
        fields.put("territorial_consequences_verified", new Bool(false));
        fields.put("candidate_policy", new Text("original_intake_and_selector"));
        fields.put("cash_priority_policy_recomputed", new Bool(false));
        fields.put("resource_reservation_performed", new Bool(false));
        fields.put("formal_action_ready", new Bool(false));
        fields.put("action_authorized", new Bool(false));
        return new Obj(fields);
    }

    static Obj parseObject(byte[] raw, String label) {
        byte[] checked = ProjectionJson.object(raw, MAXIMUM_BYTES).bytes();
        try (JsonParser parser = FACTORY.createParser(checked)) {
            require(parser.nextToken() != null, "M5 JSON value required");
            Obj result = object(fromParser(parser), label);
            require(parser.nextToken() == null, "one complete M5 JSON document required");
            return result;
        } catch (IOException error) {
            throw new IllegalArgumentException("invalid " + label, error);
        }
    }

    /** One narrow conversion into the existing immutable JSON type domain; no floating coercion. */
    private static Value fromParser(JsonParser parser) throws IOException {
        JsonToken token = parser.currentToken();
        require(token != null, "M5 JSON value required");
        return switch (token) {
            case START_OBJECT -> {
                Map<String, Value> fields = new LinkedHashMap<>();
                while (parser.nextToken() != JsonToken.END_OBJECT) {
                    require(parser.currentToken() == JsonToken.FIELD_NAME, "M5 JSON field required");
                    String field = parser.currentName();
                    require(parser.nextToken() != null, "M5 JSON field value required");
                    require(fields.put(field, fromParser(parser)) == null, "duplicate M5 JSON field");
                }
                yield new Obj(fields);
            }
            case START_ARRAY -> {
                List<Value> values = new ArrayList<>();
                while (parser.nextToken() != JsonToken.END_ARRAY) values.add(fromParser(parser));
                yield new Arr(values);
            }
            case VALUE_STRING -> new Text(parser.getText());
            case VALUE_NUMBER_INT -> new IntegerValue(parser.getBigIntegerValue());
            case VALUE_NUMBER_FLOAT -> new DecimalValue(parser.getText());
            case VALUE_TRUE -> new Bool(true);
            case VALUE_FALSE -> new Bool(false);
            case VALUE_NULL -> Nil.INSTANCE;
            default -> throw new IllegalArgumentException("unsupported M5 JSON token");
        };
    }

    private static byte[] checkedEncode(Obj value) {
        return ProjectionJson.object(OpportunityJson.encode(value), MAXIMUM_BYTES).bytes();
    }
}
