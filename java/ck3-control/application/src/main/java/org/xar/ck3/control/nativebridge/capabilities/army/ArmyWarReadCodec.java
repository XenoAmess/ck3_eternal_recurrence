package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition;
import org.xar.ck3.control.wave2.military.coalition.CoalitionRiskJsonAdapter;
import org.xar.ck3.control.wave2.military.coalitionreceipt.CoalitionExecutionReceipt;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.warpolicy.NativeTerminationTerms;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual original read receipts -> full immutable war observations. Shared by service, effects and cold replay. */
public final class ArmyWarReadCodec {
    private ArmyWarReadCodec() { }
    public sealed interface Observation permits Declarations, Occupation, Options, Terms, WhitePeace, CoalitionV2, HolyContext, CoalitionV1 {
        PublicMethod method(); Obj normalizedResult();
    }
    public record Declarations(List<DeclarationContract.Choice> choices, UInt64 querySequence, Obj normalizedResult) implements Observation {
        public Declarations { choices = List.copyOf(choices); Objects.requireNonNull(querySequence); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_DECLARABLE_WARS; }
    }
    public record Occupation(ArmyWarOccupationCodec.Occupation value, Obj normalizedResult) implements Observation {
        public Occupation { Objects.requireNonNull(value); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1; }
    }
    public record Options(NativeTerminationOptions.NativePacket value, Obj normalizedResult) implements Observation {
        public Options { Objects.requireNonNull(value); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_WAR_TERMINATION_OPTIONS; }
    }
    public record Terms(Obj value, Obj normalizedResult) implements Observation {
        public Terms { Objects.requireNonNull(value); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_WAR_TERMINATION_TERMS; }
    }
    public record WhitePeace(int war, FullId actor, FullId recipient, boolean present, Optional<FullId> pendingInteraction, Obj normalizedResult) implements Observation {
        public WhitePeace { Objects.requireNonNull(actor); Objects.requireNonNull(recipient); Objects.requireNonNull(pendingInteraction); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS; }
    }
    public record CoalitionV2(PrewarCoalition.Observation value, CoalitionExecutionReceipt.Receipt execution,
            String nativeRequestId, Obj normalizedResult) implements Observation {
        public CoalitionV2 { Objects.requireNonNull(value); Objects.requireNonNull(execution); Objects.requireNonNull(nativeRequestId); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2; }
    }
    public record HolyContext(HolyCostObservation value, Optional<HolyWarDefenderJoinCodec.Observation> defenderJoin,
            Obj normalizedResult) implements Observation {
        public HolyContext { Objects.requireNonNull(value); Objects.requireNonNull(defenderJoin); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1; }
    }
    public record CoalitionV1(PrewarPartialCodec.Observation value, CoalitionExecutionReceipt.Receipt execution,
            PrewarPartialCodec.IndependentSource independentSource, String nativeRequestId, Obj normalizedResult) implements Observation {
        public CoalitionV1 { Objects.requireNonNull(value); Objects.requireNonNull(execution); Objects.requireNonNull(independentSource); Objects.requireNonNull(nativeRequestId); Objects.requireNonNull(normalizedResult); }
        public PublicMethod method() { return PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1; }
    }
    public record Scope(ArmyCalls.Call call, Context context, Obj currentSnapshot, Optional<DeclarationContract.Choice> declaration,
            Optional<PrewarPartialCodec.IndependentSource> independentSource) {
        public Scope { Objects.requireNonNull(call); Objects.requireNonNull(context); Objects.requireNonNull(currentSnapshot); Objects.requireNonNull(declaration); Objects.requireNonNull(independentSource); call.revision().requireCurrent(context.before().frame().revision()); }
        public Scope(ArmyCalls.Call call, Context context, Obj currentSnapshot, Optional<DeclarationContract.Choice> declaration) {
            this(call, context, currentSnapshot, declaration, Optional.empty());
        }
    }
    public static Observation decode(Scope scope, PlanningReadReceipt receipt) {
        Objects.requireNonNull(scope); Objects.requireNonNull(receipt);
        if (scope.call().method() == PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2) return coalition(scope, receipt);
        if (scope.call().method() == PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1) return partialCoalition(scope, receipt);
        ObjectNode n = ArmyNativeReadEvidence.result(scope.context(), receipt).deepCopy();
        yes(get(n, "accepted"));
        if (n.has("snapshot_revision")) equal(n.get("snapshot_revision"), scope.context().nativeRevision());
        return switch (scope.call().method()) {
            case QUERY_DECLARABLE_WARS -> {
                equal(get(n, "step"), "query-declarable-wars"); equal(get(n, "status"), "available");
                UInt64 sequence = positive(get(n, "query_sequence"));
                var choices = DeclarationContract.normalize(get(n, "declarable_wars")); n.set("declarable_wars", DeclarationContract.encode(choices));
                yield new Declarations(choices, sequence, immutable(n));
            }
            case QUERY_WAR_OCCUPATION_TARGETS_V1 -> {
                int war = war(scope.call()); Side side = side(scope.currentSnapshot(), war);
                var value = ArmyWarOccupationCodec.decode(bytes(n), scope.context(), war, side);
                n.set("war_occupation_targets_v1", ArmyWarOccupationCodec.normalizedNode(value));
                yield new Occupation(value, immutable(n));
            }
            case QUERY_WAR_TERMINATION_OPTIONS -> {
                int war = war(scope.call()); equal(get(n, "step"), "query-war-termination-options-" + war);
                var value = NativeTerminationOptions.normalizeNativePacket(get(n, "war_termination_options"), war);
                ObjectNode projected = WarTerminationReadProjection.options(scope.context(), scope.currentSnapshot(), value, positive(get(n, "query_sequence")), n);
                yield new Options(value, immutable(projected));
            }
            case QUERY_WAR_TERMINATION_TERMS -> {
                int war = war(scope.call()); equal(get(n, "step"), "query-war-termination-terms-v1-" + war);
                ObjectNode value = NativeTerminationTerms.normalize(get(n, "war_termination_terms"), war);
                ObjectNode projected = WarTerminationReadProjection.terms(scope.context(), scope.currentSnapshot(), value, positive(get(n, "query_sequence")), n);
                yield new Terms(immutable(value), immutable(projected));
            }
            case QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS -> white(scope, n);
            case QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1 -> holy(scope, n);
            default -> throw new IllegalArgumentException("war read has no complete production decoder");
        };
    }
    private static HolyContext holy(Scope scope, ObjectNode n) {
        equal(get(n, "step"), "query-player-ordinary-holy-war-declaration-context-v1");
        yes(get(n, "private_build")); yes(get(n, "read_only")); no(get(n, "advertised"));
        require(scope.call() instanceof ArmyCalls.Declaration, "holy context requires selected declaration");
        String id = ((ArmyCalls.Declaration) scope.call()).declarationId();
        var selected = scope.declaration().orElseThrow(() -> new IllegalArgumentException("actual current declaration lease required"));
        ObjectNode snapshot = object(OpportunityJson.toNode(scope.currentSnapshot()));
        var value = HolyCostJsonAdapter.normalize(get(n, "player_ordinary_holy_war_declaration_context"), snapshot, id, HolyCostJsonAdapter.selectedJson(selected));
        equal(get(n, "game_version"), value.build().gameVersion());
        require(text(get(n, "executable_sha256")).equalsIgnoreCase(value.build().executableSha256()), "holy context envelope exact build SHA differs");
        equal(get(n, "backend_id"), "ck3-" + value.build().gameVersion() + "-native-player-ordinary-holy-war-declaration-context-v1");
        equal(get(n, "domain_key"), HolyCostJsonAdapter.SCHEMA);
        equal(get(n, "snapshot_revision"), value.nativeRevision()); equal(get(n, "public_revision"), value.publicRevision());
        equal(get(n, "date_raw"), java.math.BigInteger.valueOf(value.dateRaw()));
        equal(get(n, "status"), value.available() ? "observed" : "unavailable");
        Optional<HolyWarDefenderJoinCodec.Observation> join = n.has(HolyWarDefenderJoinCodec.DOMAIN)
                ? Optional.of(HolyWarDefenderJoinCodec.normalize(n.get(HolyWarDefenderJoinCodec.DOMAIN), value, snapshot)) : Optional.empty();
        ObjectNode result = HolyCostJsonAdapter.encode(value);
        result.put("exact_ck3_build", value.build().gameVersion()).put("exe_sha256", value.build().executableSha256());
        result.set("queried_snapshot_id", get(snapshot, "snapshot_id")); result.set("queried_revision", get(snapshot, "revision"));
        result.set("queried_native_revision", get(snapshot, "native_revision"));
        result.set("snapshot_revision", n.get("snapshot_revision")); result.set("query_date_raw", n.get("date_raw"));
        result.set("backend_id", n.get("backend_id")); result.put("domain_key", HolyCostJsonAdapter.SCHEMA);
        result.set("query_status", n.get("status")); result.put("advertised", false);
        join.ifPresent(observed -> result.set(HolyWarDefenderJoinCodec.DOMAIN, HolyWarDefenderJoinCodec.encode(observed)));
        return new HolyContext(value, join, immutable(result));
    }
    private static WhitePeace white(Scope scope, ObjectNode n) {
        int war = war(scope.call()); equal(get(n, "step"), "query-outbound-war-white-peace-status-v1-" + war);
        ObjectNode v = closed(get(n, "outbound_war_white_peace_status"),
                "schema_version", "war_id", "actor_character_id", "recipient_character_id", "state", "present", "pending_interaction_id");
        require(i32(v.get("schema_version")) == 1 && id(v.get("war_id")).value() == war, "white-peace selected identity/version differs");
        FullId actor = full(v.get("actor_character_id")), recipient = full(v.get("recipient_character_id"));
        require(!actor.equals(recipient) && java.math.BigInteger.valueOf(actor.value()).equals(scope.context().playerId()), "white-peace sender/recipient differs");
        boolean present = bool(v.get("present")); equal(v.get("state"), present ? "exact_present" : "exact_absent");
        int pending = i32(v.get("pending_interaction_id")); require(present ? pending != -1 : pending == -1, "white-peace pending sentinel differs");
        return new WhitePeace(war, actor, recipient, present, present ? Optional.of(new FullId(pending)) : Optional.empty(), immutable(n));
    }
    private static CoalitionV1 partialCoalition(Scope scope, PlanningReadReceipt receipt) {
        ArmyNativeReadEvidence.verifyContext(scope.context(), receipt);
        require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "partial coalition lacks original native success token");
        ObjectNode top = parse(receipt.original().originalFrame().bytes());
        require(get(top, "result").equals(parse(receipt.original().originalResultToken().orElseThrow().bytes())), "partial token differs from complete original TOP");
        var command = PrewarPartialCodec.validateCommand(top, receipt.requestId());
        equal(command.unvalidatedResultCopy().get("step"), receipt.request().operation().value());
        var independent = scope.independentSource().orElseThrow(() -> new IllegalArgumentException("actual independent current war-entry source lease required"));
        var selected = scope.declaration().orElseThrow(() -> new IllegalArgumentException("actual current declaration lease required"));
        require(selected.targetCharacterId().equals(java.math.BigInteger.valueOf(independent.requestedTarget().value())), "partial independent source selected another requested target");
        ObjectNode snapshot = object(OpportunityJson.toNode(scope.currentSnapshot()));
        ObjectNode result = command.unvalidatedResultCopy();
        var value = PrewarPartialCodec.normalize(result.get(PrewarPartialCodec.DOMAIN), snapshot, selected, independent.effectiveTarget(), command.execution());
        result.set(PrewarPartialCodec.DOMAIN, PrewarPartialCodec.encode(value)); result.put("backend_id", "native-headless");
        result.set("execution_receipt", command.execution().toJson()); result.put("native_request_id", command.requestId());
        result.set("queried_snapshot_id", get(snapshot, "snapshot_id")); result.set("queried_revision", get(snapshot, "revision"));
        result.set("queried_native_revision", get(snapshot, "native_revision")); result.set("queried_date_raw", get(snapshot, "date_raw"));
        result.set("queried_actor_character_id", get(object(get(snapshot, "played_character")), "character_id"));
        result.set("queried_connection_generation", get(object(get(snapshot, "diagnostics")), "connection_generation"));
        result.set("queried_episode_run_id", snapshot.get("episode_run_id")); result.set("independent_effective_source", independent.toJson());
        return new CoalitionV1(value, command.execution(), independent, command.requestId(), immutable(result));
    }
    private static CoalitionV2 coalition(Scope scope, PlanningReadReceipt receipt) {
        ArmyNativeReadEvidence.verifyContext(scope.context(), receipt);
        require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "coalition read lacks original successful token");
        ObjectNode frame = parse(receipt.original().originalFrame().bytes());
        require(get(frame, "result").equals(parse(receipt.original().originalResultToken().orElseThrow().bytes())), "coalition token differs from actual full TOP");
        var command = CoalitionExecutionReceipt.validate(frame, receipt.requestId());
        equal(command.resultJson().get("step"), receipt.request().operation().value());
        var expected = DeclarationContract.encodeChoice(scope.declaration().orElseThrow(() -> new IllegalArgumentException("coalition requires actual current declaration source")));
        ObjectNode snapshot = object(OpportunityJson.toNode(scope.currentSnapshot()));
        var current = CoalitionExecutionReceipt.normalizeAgainstLease(command, snapshot, expected, null);
        ObjectNode result = command.resultJson(); result.set(CoalitionExecutionReceipt.DOMAIN_KEY, CoalitionRiskJsonAdapter.encodeObservation(current.observation()));
        result.set("execution_receipt", command.receipt().toJson()); result.put("native_request_id", command.requestId());
        return new CoalitionV2(current.observation(), command.receipt(), command.requestId(), immutable(result));
    }
    public static RawJson encode(Observation observation) { return new RawJson(OpportunityJson.encode(observation.normalizedResult())); }
    public static Side side(Obj snapshot, int war) {
        List<Obj> selected = OpportunityJson.array(snapshot.get("active_wars"), "active wars").stream().map(row -> OpportunityJson.object(row, "active war"))
                .filter(row -> row.get("war_id") instanceof OpportunityJson.IntegerValue id && id.value().equals(java.math.BigInteger.valueOf(war))).toList();
        require(selected.size() == 1, "read requires exactly one active selected war");
        return switch (OpportunityJson.text(selected.getFirst().get("player_side"), "player side")) { case "attacker" -> Side.ATTACKER; case "defender" -> Side.DEFENDER; default -> throw new IllegalArgumentException("unknown current war side"); };
    }
    private static int war(ArmyCalls.Call call) { require(call instanceof ArmyCalls.War, "war read argument shape differs"); return ((ArmyCalls.War) call).warId().intValueExact(); }
    private static Obj immutable(ObjectNode n) { return DriverJson.object(bytes(n), DriverJson.MAX_NATIVE_BYTES); }
}
