package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.coalitionreceipt.CoalitionExecutionReceipt;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Complete original V1 partial coalition contract. Independent request and effective defender are supplied by the actual outer consumer. */
public final class PrewarPartialCodec {
    public static final String STEP = "query-prewar-force-coalition-coverage-v1";
    public static final String DOMAIN = "prewar_force_coalition_coverage";
    private static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Set<String> FIELDS = Set.of("schema_version", "status", "read_only", "game_version", "executable_sha256", "capture_epoch",
            "native_revision", "public_revision", "date_raw", "actor_character_id", "declaration_id", "selected_declaration", "effective_target_character_id",
            "ticket", "query_sequence", "current_allies", "owner_forces", "actor_ready_unraised_lower_soldiers", "enemy_upper_soldiers",
            "enemy_force_coverage_complete", "complete_initial_participants_ready", "automatic_declaration_enabled");
    private static final Set<String> ALLIES = Set.of("owner_character_id", "available", "unavailable_reason", "collection_complete", "ally_character_ids",
            "unresolved_source_character_ids", "dead_source_character_ids");
    private static final Set<String> FORCES = Set.of("owner_character_id", "raised_available", "raised_unavailable_reason", "raised_armies",
            "raised_current_soldiers", "raised_maximum_soldiers", "unraised_available", "unraised_unavailable_reason", "unraised_soldiers", "native_raise_legal");
    private static final Set<String> SELECTED = Set.of("target_character_id", "casus_belli_index", "casus_belli_key", "configuration_index", "claimant_character_id", "target_title_ids");
    private PrewarPartialCodec() { }
    /** Current-source values only. The native owner mints its private lease from the actual archived independent read. */
    public record IndependentSource(UInt64 declarationQuerySequence, UInt64 assessmentQuerySequence, PositiveId requestedTarget, PositiveId effectiveTarget) {
        public IndependentSource {
            Objects.requireNonNull(declarationQuerySequence); Objects.requireNonNull(assessmentQuerySequence); Objects.requireNonNull(requestedTarget); Objects.requireNonNull(effectiveTarget);
            require(declarationQuerySequence.value().signum() > 0 && assessmentQuerySequence.value().signum() > 0, "independent source requires positive completed query sequences");
        }
        public ObjectNode toJson() {
            return empty().put("declaration_query_sequence", declarationQuerySequence.value()).put("assessment_query_sequence", assessmentQuerySequence.value())
                    .put("requested_target_character_id", requestedTarget.value()).put("effective_target_character_id", effectiveTarget.value())
                    .put("effective_source", "same_frame_native_war_entry_assessment_generic_target").put("assessment_game_version", "1.20.0.4").put("assessment_executable_sha256", EXE);
        }
    }
    /** Only the strict full TOP validator creates this independent execution binding. It does not validate the domain. */
    public static final class Command {
        private final String requestId;
        private final CoalitionExecutionReceipt.Receipt execution;
        private final OpportunityJson.Obj unvalidatedResult;
        private Command(String requestId, CoalitionExecutionReceipt.Receipt execution, ObjectNode result) {
            this.requestId = requestId; this.execution = execution; unvalidatedResult = DriverJson.object(bytes(result), DriverJson.MAX_NATIVE_BYTES);
        }
        public String requestId() { return requestId; }
        public CoalitionExecutionReceipt.Receipt execution() { return execution; }
        public ObjectNode unvalidatedResultCopy() { return object(OpportunityJson.toNode(unvalidatedResult)).deepCopy(); }
    }
    public static Command validateCommand(JsonNode originalTop, String expectedRequestId) {
        require(expectedRequestId != null && !expectedRequestId.isEmpty(), "fresh actual request ID required");
        ObjectNode top = closed(originalTop, "type", "protocol_version", "request_id", "ok", "execution_receipt", "result");
        equal(top.get("type"), "command_result"); equal(top.get("protocol_version"), BigInteger.ONE); equal(top.get("request_id"), expectedRequestId); yes(top.get("ok"));
        ObjectNode execution = closed(top.get("execution_receipt"), "ticket", "query_sequence", "capture_epoch");
        var binding = new CoalitionExecutionReceipt.Receipt(positive(execution.get("ticket")).value(), positive(execution.get("query_sequence")).value(), positive(execution.get("capture_epoch")).value());
        ObjectNode result = closed(top.get("result"), "step", "accepted", "status", "private_build", "read_only", "advertised", "domain_key", DOMAIN);
        equal(result.get("step"), STEP); yes(result.get("accepted")); equal(result.get("status"), "available_partial"); yes(result.get("private_build"));
        yes(result.get("read_only")); no(result.get("advertised")); equal(result.get("domain_key"), DOMAIN);
        return new Command(expectedRequestId, binding, result);
    }
    public record Allies(FullId owner, boolean available, Optional<String> unavailableReason, boolean collectionComplete,
            Optional<List<FullId>> allyIds, Optional<List<FullId>> unresolvedIds, Optional<List<FullId>> deadIds) {
        public Allies { Objects.requireNonNull(owner); Objects.requireNonNull(unavailableReason); allyIds = copied(allyIds); unresolvedIds = copied(unresolvedIds); deadIds = copied(deadIds); }
    }
    public record RaisedArmy(PublicUnitId army, Optional<Integer> currentSoldiers, Optional<Integer> maximumSoldiers) {
        public RaisedArmy { Objects.requireNonNull(army); Objects.requireNonNull(currentSoldiers); Objects.requireNonNull(maximumSoldiers); }
    }
    public record Force(FullId owner, boolean raisedAvailable, Optional<String> raisedUnavailableReason, Optional<List<RaisedArmy>> raisedArmies,
            Optional<Long> raisedCurrent, Optional<Long> raisedMaximum, boolean unraisedAvailable, Optional<String> unraisedUnavailableReason,
            Optional<Integer> unraisedSoldiers, Optional<Boolean> nativeRaiseLegal) {
        public Force { Objects.requireNonNull(owner); Objects.requireNonNull(raisedUnavailableReason); raisedArmies = copied(raisedArmies);
            Objects.requireNonNull(raisedCurrent); Objects.requireNonNull(raisedMaximum); Objects.requireNonNull(unraisedUnavailableReason);
            Objects.requireNonNull(unraisedSoldiers); Objects.requireNonNull(nativeRaiseLegal); }
    }
    public record Observation(UInt64 captureEpoch, UInt64 nativeRevision, UInt64 publicRevision, int dateRaw, PositiveId actor,
            DeclarationContract.Choice declaration, PositiveId effectiveTarget, CoalitionExecutionReceipt.Receipt actualExecution,
            List<Allies> allies, List<Force> forces, Optional<Long> actorReadyUnraisedLowerSoldiers, OpportunityJson.Obj normalized) {
        public Observation { Objects.requireNonNull(captureEpoch); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(publicRevision);
            Objects.requireNonNull(actor); Objects.requireNonNull(declaration); Objects.requireNonNull(effectiveTarget); Objects.requireNonNull(actualExecution);
            allies = List.copyOf(allies); forces = List.copyOf(forces); Objects.requireNonNull(actorReadyUnraisedLowerSoldiers); Objects.requireNonNull(normalized); }
        public boolean automaticDeclarationEnabled() { return false; }
        public boolean completeInitialParticipantsReady() { return false; }
    }
    /** This is a pure value boundary. Neither caller-authored expected IDs nor this result qualify current history or dispatch. */
    public static Observation normalize(JsonNode raw, JsonNode actualSnapshot, DeclarationContract.Choice currentDeclaration,
            PositiveId independentlyObservedEffectiveTarget, CoalitionExecutionReceipt.Receipt actualExecution) {
        Objects.requireNonNull(currentDeclaration); Objects.requireNonNull(independentlyObservedEffectiveTarget); Objects.requireNonNull(actualExecution);
        ObjectNode n = StrictJson.object(raw, FIELDS), snapshot = object(actualSnapshot);
        equal(n.get("schema_version"), BigInteger.ONE); equal(n.get("status"), "available_partial"); yes(n.get("read_only"));
        yes(get(snapshot, "paused")); yes(get(snapshot, "map_ready"));
        equal(n.get("game_version"), "1.20.0.4"); require(text(n.get("executable_sha256")).equalsIgnoreCase(EXE), "partial coalition belongs to another exact build");
        ObjectNode hello = object(get(object(get(snapshot, "diagnostics")), "hello")); equal(get(hello, "expected_ck3_version"), "1.20.0.4");
        require(text(get(hello, "expected_ck3_sha256")).equalsIgnoreCase(EXE), "partial coalition snapshot belongs to another exact build");
        UInt64 epoch = positive(n.get("capture_epoch")), nativeRevision = positive(n.get("native_revision")), publicRevision = positive(n.get("public_revision"));
        require(epoch.value().equals(actualExecution.captureEpoch()) && positive(n.get("ticket")).value().equals(actualExecution.ticket())
                && positive(n.get("query_sequence")).value().equals(actualExecution.querySequence()), "partial domain cannot prove its own execution binding");
        if (snapshot.has("capture_epoch")) require(epoch.equals(positive(snapshot.get("capture_epoch"))), "partial capture epoch differs from current source");
        require(nativeRevision.equals(positive(get(snapshot, "native_revision"))) && publicRevision.equals(positive(get(snapshot, "revision"))), "partial coalition frame revision differs");
        int date = i32(n.get("date_raw")); require(date == i32(get(snapshot, "date_raw")), "partial coalition date differs");
        ObjectNode player = object(get(snapshot, "played_character")); yes(get(player, "alive")); PositiveId actor = id(n.get("actor_character_id"));
        require(actor.equals(id(get(player, "character_id"))), "partial actor differs from living played character");
        String declarationId = currentDeclaration.declarationId();
        require(declarationId.matches("[1-9][0-9]*-(?:0|[1-9][0-9]*)-(?:-1|0|[1-9][0-9]*)"), "partial selected declaration ID is not canonical");
        equal(n.get("declaration_id"), declarationId); ObjectNode expectedSelected = selected(currentDeclaration);
        require(selectedNode(n.get("selected_declaration")).equals(expectedSelected), "partial selected tuple differs from actual current declaration");
        var matching = DeclarationContract.normalize(get(snapshot, "declarable_wars")).stream().filter(choice -> choice.declarationId().equals(declarationId)).toList();
        require(matching.size() == 1 && selected(matching.getFirst()).equals(expectedSelected), "partial selected declaration is absent, ambiguous or stale");
        PositiveId effective = id(n.get("effective_target_character_id"));
        require(effective.equals(independentlyObservedEffectiveTarget) && !effective.equals(actor), "partial effective defender differs from independent assessment or collapses to actor");
        List<JsonNode> allyRows = array(n.get("current_allies"), value -> value); require(allyRows.size() == 2, "both primary ally-owner rows required");
        List<Allies> allies = new ArrayList<>(); Set<FullId> owners = new HashSet<>(List.of(new FullId(actor.value()), new FullId(effective.value())));
        List<FullId> primaries = List.of(new FullId(actor.value()), new FullId(effective.value()));
        for (int i = 0; i < allyRows.size(); i++) {
            ObjectNode a = StrictJson.object(allyRows.get(i), ALLIES); FullId owner = full(a.get("owner_character_id")); require(owner.equals(primaries.get(i)), "ally primary owner/order differs");
            boolean ready = bool(a.get("available")), complete = bool(a.get("collection_complete")); Optional<String> why = reason(a.get("unavailable_reason"), ready);
            Optional<List<FullId>> observed = characters(a.get("ally_character_ids")), unresolved = characters(a.get("unresolved_source_character_ids")), dead = characters(a.get("dead_source_character_ids"));
            require(ready == complete, "ally availability must describe a complete native collection");
            require(!complete || observed.isPresent() && unresolved.isPresent() && dead.isPresent() && unresolved.orElseThrow().isEmpty(), "complete allies require diagnostic arrays and no unresolved sources");
            require(observed.isPresent() ? unresolved.isPresent() && dead.isPresent() : unresolved.isEmpty() && dead.isEmpty(), "unread/observed allies have inconsistent diagnostic presence");
            require(observed.isEmpty() || !observed.orElseThrow().contains(owner), "owner cannot be its own ally");
            Set<FullId> disjoint = new HashSet<>();
            for (var group : List.of(observed, unresolved, dead)) for (var member : group.orElse(List.of())) require(disjoint.add(member), "observed, unresolved and dead ally IDs overlap");
            owners.addAll(observed.orElse(List.of())); allies.add(new Allies(owner, ready, why, complete, observed, unresolved, dead));
        }
        List<Force> forces = forces(n.get("owner_forces"), owners); Force actorForce = forces.stream().filter(row -> row.owner().value() == actor.value()).findFirst().orElseThrow();
        Optional<Long> expectedLower = actorForce.unraisedAvailable() && actorForce.nativeRaiseLegal().equals(Optional.of(true))
                ? actorForce.unraisedSoldiers().map(Integer::longValue) : Optional.empty();
        Optional<Long> lower = nullable(n.get("actor_ready_unraised_lower_soldiers"), PrewarPartialCodec::count);
        require(lower.equals(expectedLower), "actor lower bound requires native raise legality and observed unraised count");
        require(n.get("enemy_upper_soldiers").isNull(), "partial observation cannot invent an enemy upper bound");
        no(n.get("enemy_force_coverage_complete")); no(n.get("complete_initial_participants_ready")); no(n.get("automatic_declaration_enabled"));
        ObjectNode normalized = n.deepCopy().put("executable_sha256", EXE); normalized.set("selected_declaration", expectedSelected);
        return new Observation(epoch, nativeRevision, publicRevision, date, actor, currentDeclaration, effective, actualExecution,
                allies, forces, lower, DriverJson.object(bytes(normalized), DriverJson.MAX_NATIVE_BYTES));
    }
    private static List<Force> forces(JsonNode raw, Set<FullId> expectedOwners) {
        List<Force> forces = new ArrayList<>(); Set<FullId> owners = new HashSet<>(); Set<PublicUnitId> armiesSeen = new HashSet<>();
        for (JsonNode value : array(raw, row -> row)) {
            ObjectNode f = StrictJson.object(value, FORCES); FullId owner = full(f.get("owner_character_id"));
            require(expectedOwners.contains(owner) && owners.add(owner), "force owner is repeated or not primary/observed ally");
            boolean raised = bool(f.get("raised_available")); Optional<String> raisedReason = reason(f.get("raised_unavailable_reason"), raised);
            Optional<List<RaisedArmy>> armyRows = nullable(f.get("raised_armies"), rows -> array(rows, row -> {
                ObjectNode a = closed(row, "army_id", "current_soldiers", "maximum_soldiers"); PublicUnitId unit = unit(a.get("army_id"));
                require(armiesSeen.add(unit), "raised armies repeat one public CUnit ID");
                return new RaisedArmy(unit, nullable(a.get("current_soldiers"), ArmyJson::nonnegative), nullable(a.get("maximum_soldiers"), ArmyJson::nonnegative));
            }));
            long currentSum = 0, maximumSum = 0; boolean complete = armyRows.isPresent();
            for (RaisedArmy army : armyRows.orElse(List.of())) {
                complete &= army.currentSoldiers().isPresent() && army.maximumSoldiers().isPresent();
                currentSum = sum(currentSum, army.currentSoldiers().orElse(0)); maximumSum = sum(maximumSum, army.maximumSoldiers().orElse(0));
            }
            Optional<Long> current = nullable(f.get("raised_current_soldiers"), PrewarPartialCodec::count), maximum = nullable(f.get("raised_maximum_soldiers"), PrewarPartialCodec::count);
            require(raised ? complete && current.equals(Optional.of(currentSum)) && maximum.equals(Optional.of(maximumSum)) : current.isEmpty() && maximum.isEmpty(),
                    "raised aggregates require all matching actual rows; incomplete observations cannot claim aggregates");
            boolean unraised = bool(f.get("unraised_available")); Optional<String> unraisedReason = reason(f.get("unraised_unavailable_reason"), unraised);
            Optional<Integer> unraisedCount = nullable(f.get("unraised_soldiers"), ArmyJson::nonnegative); require(unraised == unraisedCount.isPresent(), "unraised readiness differs from observed count");
            Optional<Boolean> legal = nullable(f.get("native_raise_legal"), ArmyJson::bool);
            forces.add(new Force(owner, raised, raisedReason, armyRows, current, maximum, unraised, unraisedReason, unraisedCount, legal));
        }
        require(owners.equals(expectedOwners), "force rows omitted a primary or observed ally"); return List.copyOf(forces);
    }
    public static ObjectNode encode(Observation value) { return object(OpportunityJson.toNode(value.normalized())).deepCopy(); }
    private static ObjectNode selected(DeclarationContract.Choice value) {
        ObjectNode n = DeclarationContract.encodeChoice(value); n.remove("source"); n.remove("declaration_id"); return selectedNode(n);
    }
    private static ObjectNode selectedNode(JsonNode raw) {
        ObjectNode n = StrictJson.object(raw, SELECTED); id(n.get("target_character_id")); nonnegative(n.get("casus_belli_index"));
        StrictJson.integer(n.get("configuration_index"), -1, Integer.MAX_VALUE); StrictJson.integer(n.get("claimant_character_id"), -1, Integer.MAX_VALUE);
        String key = nonempty(n.get("casus_belli_key")); require(key.equals(key.strip()), "CB key cannot carry surrounding whitespace");
        array(n.get("target_title_ids"), ArmyJson::nonnegative); return parse(bytes(n));
    }
    private static Optional<List<FullId>> characters(JsonNode n) {
        return nullable(n, value -> { var rows = array(value, ArmyJson::full); require(new HashSet<>(rows).size() == rows.size(), "CharacterID array repeats a full generation"); return rows; });
    }
    private static long count(JsonNode n) { return StrictJson.integer(n, 0, Long.MAX_VALUE); }
    private static long sum(long a, int b) { try { return Math.addExact(a, b); } catch (ArithmeticException overflow) { throw new IllegalArgumentException("raised soldier totals overflow", overflow); } }
    private static Optional<String> reason(JsonNode n, boolean ready) {
        require(n != null, "required reason slot absent"); if (ready) { require(n.isNull(), "available reason must be null"); return Optional.empty(); }
        String value = nonempty(n); require(!value.isBlank(), "unavailable stage reason required"); return Optional.of(value);
    }
    private static <T> Optional<T> nullable(JsonNode n, java.util.function.Function<JsonNode,T> decoder) {
        require(n != null, "required nullable slot absent"); return n.isNull() ? Optional.empty() : Optional.of(decoder.apply(n));
    }
    private static <T> Optional<List<T>> copied(Optional<List<T>> input) { Objects.requireNonNull(input); return input.map(List::copyOf); }
}
