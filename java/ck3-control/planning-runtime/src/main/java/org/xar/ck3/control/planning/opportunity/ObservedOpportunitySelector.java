package org.xar.ck3.control.planning.opportunity;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Same-frame analytic arbitration only. Domain owners retain legality, value and submission authority. */
public final class ObservedOpportunitySelector {
    private ObservedOpportunitySelector() { }
    public enum Domain { war, council, marriage, diplomacy, building, lifestyle }
    public enum WarOperation { entry, active_defensive_continuation }
    public enum Reason { eligible, shared_gold_budget, army_not_controllable,
        existing_commitment_conflict, war_slot_budget, projected_supply_deficit }
    private record Frame(BigInteger playedCharacterId, BigInteger nativeRevision, BigInteger dateRaw,
                        String snapshotId, BigInteger revision, String episodeRunId) { }
    private record Claims(List<BigInteger> armies, List<BigInteger> allies,
                         List<BigInteger> characters, List<String> keys) {
        public Claims { armies = List.copyOf(armies); allies = List.copyOf(allies);
            characters = List.copyOf(characters); keys = List.copyOf(keys); }
    }
    private record Proposal(String candidateId, Domain domain, String sourcePolicy, Frame frame,
                           BigInteger goldCost, BigInteger minimumReserve, BigInteger supply,
                           int warSlots, WarOperation warOperation, Claims claims, Obj evidence,
                           Obj normalizedFields) { }
    private record Commitments(Frame frame, BigInteger gold, BigInteger pendingWars, Claims claims) { }
    private record Request(Frame frame, BigInteger treasury, int activeWars, Set<BigInteger> usableArmies,
                          boolean hasAnyArmies, List<Proposal> proposals, Commitments commitments,
                          BigInteger goldReserve, BigInteger maxActiveWars) {
        public Request { usableArmies = Set.copyOf(usableArmies); proposals = List.copyOf(proposals); }
    }
    private record Evaluation(Proposal proposal, Reason reason) { }
    private record Result(Frame frame, List<Evaluation> evaluated, String selectedCandidateId,
                         boolean incomePreferenceApplied) {
        public Result { evaluated = List.copyOf(evaluated); }
        public boolean formalActionReady() { return false; }
    }
    public static final List<String> SELECTION_BASIS = List.of("family_policy_rank_within_marriage",
            "observed_stock_dangerous_faction_response_in_peace", "positive_authored_building_income_in_peace",
            "war_slot_claim", "army_claim_count", "ally_claim_count", "gold_cost_raw", "commitment_key_count",
            "character_claim_count", "projected_supply_margin_raw_desc", "domain", "candidate_id");

    public static byte[] select(byte[] requestBody) {
        return OpportunityJson.encode(encode(select(decode(OpportunityJson.parse(requestBody)))));
    }
    public static byte[] selectComplete(byte[] requestBody, int maximumBytes) {
        return OpportunityJson.encode(encode(select(decode(OpportunityJson.parseComplete(requestBody, maximumBytes)))));
    }
    /** Shared normalizer for the existing shortlist consumer; grants no selection or execution authority. */
    public static byte[] normalizeProposal(byte[] requestBody) {
        Obj request = object(OpportunityJson.parse(requestBody), "normalization request");
        require(request.members().keySet().equals(Set.of("frame", "proposal")), "normalization request fields");
        Frame expected = frame(object(request.get("frame"), "frame"), true);
        return OpportunityJson.encode(proposal(object(request.get("proposal"), "proposal"), expected).normalizedFields());
    }
    /** Shared six-field projection for the existing callers; grants no source qualification. */
    public static byte[] observedFrame(byte[] snapshotBody) {
        Obj snapshot = object(OpportunityJson.parse(snapshotBody), "snapshot");
        return OpportunityJson.encode(encodeFrame(frame(snapshot, false)));
    }
    private static Request decode(Value document) {
        Obj input = object(document, "request");
        require(input.members().keySet().equals(Set.of("snapshot", "proposals", "commitments",
                "gold_reserve_raw", "max_active_wars")), "request fields must match selector arguments");
        Obj snapshot = object(input.get("snapshot"), "snapshot");
        require(bool(snapshot.get("paused"), "paused") && bool(snapshot.get("map_ready"), "map_ready"),
                "paused map required");
        Frame frame = frame(snapshot, false);
        Obj gold = object(snapshot.get("played_character_gold"), "played_character_gold");
        BigInteger treasury = integer(gold.get("raw"), "gold.raw");
        require(integer(gold.get("scale"), "gold.scale").equals(BigInteger.valueOf(100000)), "gold scale");
        List<Value> wars = array(snapshot.get("active_wars"), "active_wars");
        for (Value war : wars) integer(object(war, "war").get("war_id"), "war_id");
        List<Value> armies = array(snapshot.get("player_armies"), "player_armies");
        Set<BigInteger> usableArmies = new HashSet<>();
        for (Value value : armies) {
            Obj army = object(value, "army"); BigInteger id = integer(army.get("army_id"), "army_id");
            if (bool(army.get("controllable"), "controllable")) usableArmies.add(id);
        }
        Obj committed = object(input.get("commitments"), "commitments");
        Frame committedFrame = frame(object(committed.get("frame"), "commitments.frame"), true);
        require(frame.equals(committedFrame), "commitments crossed the observed frame");
        Commitments commitments = new Commitments(committedFrame,
                nonnegative(committed.get("gold_raw"), "commitments.gold_raw"),
                nonnegative(committed.get("pending_war_slots"), "pending_war_slots"), claims(committed));
        List<Proposal> proposals = new ArrayList<>(); Set<String> identities = new HashSet<>();
        for (Value row : array(input.get("proposals"), "proposals")) {
            Proposal proposal = proposal(object(row, "proposal"), frame);
            require(identities.add(proposal.candidateId()), "duplicate candidate identity"); proposals.add(proposal);
        }
        return new Request(frame, treasury, wars.size(), usableArmies, !armies.isEmpty(), proposals,
                commitments, nonnegative(input.get("gold_reserve_raw"), "gold_reserve_raw"),
                nonnegative(input.get("max_active_wars"), "max_active_wars"));
    }
    private static Frame frame(Obj row, boolean exact) {
        if (exact) require(row.members().keySet().equals(Set.of("played_character_id", "native_revision",
                "date_raw", "snapshot_id", "revision", "episode_run_id")), "exact six-field observed frame required");
        Value player = row.get("played_character_id");
        if (!exact && (player == null || player == Nil.INSTANCE) && row.get("played_character") instanceof Obj played)
            player = played.get("character_id");
        return new Frame(nativeCharacter(player, "played_character_id"), positive(row.get("native_revision"), "native_revision"),
                nonnegative(row.get("date_raw"), "date_raw"), text(row.get("snapshot_id"), "snapshot_id"),
                positive(row.get("revision"), "revision"), text(row.get("episode_run_id"), "episode_run_id"));
    }
    private static BigInteger nativeCharacter(Value value, String name) {
        BigInteger actual = integer(value, name);
        try { return NativeCharacterId.of(actual).asBigInteger(); }
        catch (IllegalArgumentException invalid) {
            throw new ProjectionDomainRejection(name + " must be a native signed-i32 ID other than -1");
        }
    }
    // Only explicit observed-input predicates are public domain refusals. Parsing,
    // serialization and internal selection failures retain their original error types.
    private static Obj object(Value value, String name) {
        require(value instanceof Obj, name + " must be an object"); return (Obj) value;
    }
    private static List<Value> array(Value value, String name) {
        require(value instanceof Arr, name + " must be an array"); return ((Arr) value).items();
    }
    private static String text(Value value, String name) {
        require(value instanceof Text && !((Text) value).value().isEmpty(), name + " must be nonempty text");
        return ((Text) value).value();
    }
    private static BigInteger integer(Value value, String name) {
        require(value instanceof IntegerValue, name + " must be an integer token"); return ((IntegerValue) value).value();
    }
    private static BigInteger nonnegative(Value value, String name) {
        BigInteger result = integer(value, name); require(result.signum() >= 0, name + " must be nonnegative"); return result;
    }
    private static boolean bool(Value value, String name) {
        require(value instanceof Bool, name + " must be a boolean"); return ((Bool) value).value();
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new ProjectionDomainRejection(message);
    }
    private static BigInteger positive(Value value, String name) {
        BigInteger result = integer(value, name); require(result.signum() > 0, name + " must be positive"); return result;
    }
    private static Proposal proposal(Obj row, Frame expected) {
        require(text(row.get("schema"), "schema").equals("xar.ck3.m5-observed-opportunity.v1"), "proposal schema");
        Frame observed = frame(object(row.get("frame"), "proposal.frame"), true);
        require(observed.equals(expected), "proposal crossed the observed frame");
        require(bool(row.get("domain_policy_ready"), "domain_policy_ready"), "domain policy not ready");
        String id = text(row.get("candidate_id"), "candidate_id");
        String policy = text(row.get("source_policy"), "source_policy");
        Domain domain;
        String domainWire = text(row.get("domain"), "domain");
        try { domain = Domain.valueOf(domainWire); }
        catch (IllegalArgumentException error) { throw new ProjectionDomainRejection("unsupported domain"); }
        BigInteger cost = nonnegative(row.get("gold_cost_raw"), "gold_cost_raw");
        BigInteger reserve = nonnegative(row.get("minimum_gold_reserve_raw"), "minimum_gold_reserve_raw");
        BigInteger slots = nonnegative(row.get("war_slot_claim"), "war_slot_claim");
        require(slots.compareTo(BigInteger.ONE) <= 0, "war_slot_claim must be zero or one");
        BigInteger supply = null; WarOperation operation = null; Obj normalized = row;
        Value supplyValue = row.get("projected_supply_margin_raw");
        Value operationValue = row.get("war_operation");
        if (domain == Domain.war) {
            supply = integer(supplyValue, "war measured supply");
            if ((operationValue == null || operationValue == Nil.INSTANCE) && slots.equals(BigInteger.ONE))
                operation = WarOperation.entry;
            else {
                String operationWire = text(operationValue, "war_operation");
                try { operation = WarOperation.valueOf(operationWire); }
                catch (IllegalArgumentException error) { throw new ProjectionDomainRejection("unsupported war operation"); }
            }
            require(operation == WarOperation.entry ? slots.equals(BigInteger.ONE) : slots.signum() == 0,
                    "war operation/slot mismatch");
            normalized = normalized.with("war_operation", new Text(operation.name()));
        } else {
            require(supplyValue == null || supplyValue == Nil.INSTANCE, "non-war supply must be null or absent");
            require(slots.signum() == 0 && (operationValue == null || operationValue == Nil.INSTANCE), "non-war slot/operation");
        }
        Claims claims = claims(row);
        require(domain != Domain.war || !claims.armies().isEmpty(), "war requires army claims");
        require(domain != Domain.marriage || claims.characters().size() >= 2 && !claims.keys().isEmpty(),
                "marriage lacks observed roles/commitment");
        require(domain != Domain.lifestyle || claims.armies().isEmpty() && claims.allies().isEmpty()
                && claims.characters().isEmpty() && claims.keys().size() == 1
                && claims.keys().getFirst().startsWith("lifestyle-perk-point:"), "lifestyle point claims");
        normalized = normalized.with("army_ids", integers(claims.armies())).with("ally_character_ids", integers(claims.allies()))
                .with("character_ids", integers(claims.characters())).with("commitment_keys", strings(claims.keys()));
        // Evidence and extension fields belong to domain producers. Preserve them as immutable JSON;
        // only exact integer/boolean observations below participate in this selector's ranking.
        Obj evidence = object(row.get("evidence"), "evidence");
        return new Proposal(id, domain, policy, observed, cost, reserve, supply, slots.intValueExact(), operation,
                claims, evidence, normalized);
    }
    private static Claims claims(Obj row) {
        List<BigInteger> armies = claimIds(row.get("army_ids"), "army_ids", false);
        List<BigInteger> allies = claimIds(row.get("ally_character_ids"), "ally_character_ids", true);
        List<BigInteger> characters = claimIds(row.get("character_ids"), "character_ids", true);
        List<String> keys = new ArrayList<>();
        for (Value value : array(row.get("commitment_keys"), "commitment_keys")) keys.add(text(value, "commitment key"));
        require(new HashSet<>(keys).size() == keys.size(), "duplicate commitment key"); keys.sort(ObservedOpportunitySelector::compareText);
        return new Claims(armies, allies, characters, keys);
    }
    private static List<BigInteger> claimIds(Value values, String name, boolean character) {
        List<BigInteger> result = new ArrayList<>();
        for (Value value : array(values, name)) result.add(character ? nativeCharacter(value, name) : nonnegative(value, name));
        require(new HashSet<>(result).size() == result.size(), "duplicate resource identity"); result.sort(Comparator.naturalOrder());
        return result;
    }
    private static Result select(Request request) {
        List<Evaluation> evaluated = new ArrayList<>(); List<Proposal> eligible = new ArrayList<>();
        for (Proposal proposal : request.proposals()) {
            Reason reason = Reason.eligible; Claims claims = proposal.claims();
            BigInteger reserve = request.goldReserve().max(proposal.minimumReserve());
            if (proposal.goldCost().add(request.commitments().gold()).add(reserve).compareTo(request.treasury()) > 0)
                reason = Reason.shared_gold_budget;
            else if (!request.usableArmies().containsAll(claims.armies())) reason = Reason.army_not_controllable;
            else if (conflicts(claims, request.commitments().claims())) reason = Reason.existing_commitment_conflict;
            else if (proposal.warSlots() > 0 && BigInteger.valueOf(request.activeWars()).add(request.commitments().pendingWars())
                    .add(BigInteger.valueOf(proposal.warSlots())).compareTo(request.maxActiveWars()) > 0) reason = Reason.war_slot_budget;
            else if (proposal.domain() == Domain.war && proposal.supply().signum() < 0) reason = Reason.projected_supply_deficit;
            evaluated.add(new Evaluation(proposal, reason)); if (reason == Reason.eligible) eligible.add(proposal);
        }
        Proposal familyBest = null;
        for (Proposal proposal : eligible) if (proposal.domain() == Domain.marriage
                && (familyBest == null || compareFamily(proposal, familyBest) < 0)) familyBest = proposal;
        if (familyBest != null) { eligible.removeIf(proposal -> proposal.domain() == Domain.marriage); eligible.add(familyBest); }
        boolean preferIncome = request.activeWars() == 0 && !request.hasAnyArmies()
                && evaluated.stream().allMatch(row -> row.proposal().domain() == Domain.building || row.proposal().domain() == Domain.diplomacy);
        Proposal selected = null;
        for (Proposal proposal : eligible) if (selected == null || compareOpportunity(proposal, selected, preferIncome) < 0) selected = proposal;
        return new Result(request.frame(), evaluated, selected == null ? null : selected.candidateId(), preferIncome);
    }
    private static boolean conflicts(Claims first, Claims second) {
        return overlap(first.armies(), second.armies()) || overlap(first.allies(), second.allies())
                || overlap(first.characters(), second.characters()) || overlap(first.keys(), second.keys());
    }
    private static <T> boolean overlap(List<T> first, List<T> second) { return first.stream().anyMatch(second::contains); }
    private static BigInteger observedInteger(Obj evidence, String key) {
        return evidence.get(key) instanceof IntegerValue integer ? integer.value() : null;
    }
    private static boolean dangerous(Proposal row) {
        return row.domain() == Domain.diplomacy && row.evidence().get("stock_threat_response") instanceof Obj threat
                && new Text("observed").equals(threat.get("status")) && new Bool(true).equals(threat.get("dangerous_response_ready"));
    }
    private static int compareOpportunity(Proposal first, Proposal second, boolean preferIncome) {
        BigInteger firstIncome = observedInteger(first.evidence(), "authored_monthly_income_hundredths");
        BigInteger secondIncome = observedInteger(second.evidence(), "authored_monthly_income_hundredths");
        int result = Boolean.compare(!(preferIncome && dangerous(first)), !(preferIncome && dangerous(second)));
        if (result == 0) result = Boolean.compare(!(preferIncome && first.domain() == Domain.building && firstIncome != null && firstIncome.signum() > 0),
                !(preferIncome && second.domain() == Domain.building && secondIncome != null && secondIncome.signum() > 0));
        if (result == 0) result = Integer.compare(first.warSlots(), second.warSlots());
        if (result == 0) result = Integer.compare(first.claims().armies().size(), second.claims().armies().size());
        if (result == 0) result = Integer.compare(first.claims().allies().size(), second.claims().allies().size());
        if (result == 0) result = first.goldCost().compareTo(second.goldCost());
        if (result == 0) result = Integer.compare(first.claims().keys().size(), second.claims().keys().size());
        if (result == 0) result = Integer.compare(first.claims().characters().size(), second.claims().characters().size());
        if (result == 0) result = zero(second.supply()).compareTo(zero(first.supply()));
        if (result == 0) result = compareText(first.domain().name(), second.domain().name());
        if (result == 0) result = compareText(first.candidateId(), second.candidateId());
        return result;
    }
    private static BigInteger zero(BigInteger value) { return value == null ? BigInteger.ZERO : value; }
    private record FamilyKey(int outcome, BigInteger ageGap, BigInteger negativeAcceptance, BigInteger candidate) { }
    private static FamilyKey familyKey(Proposal row) {
        Obj evidence = row.evidence(); BigInteger heir = observedInteger(evidence, "heir_adult_measure_raw");
        BigInteger candidateAge = observedInteger(evidence, "candidate_adult_measure_raw");
        BigInteger acceptance = observedInteger(evidence, "recipient_ai_accept_raw");
        BigInteger candidate = observedInteger(evidence, "candidate_character_id");
        if (candidate == null || candidate.signum() <= 0) candidate = BigInteger.ONE.shiftLeft(63);
        if (heir == null || candidateAge == null || acceptance == null) return new FamilyKey(2, BigInteger.ZERO, BigInteger.ZERO, candidate);
        return new FamilyKey(new Text("marriage").equals(evidence.get("predicted_outcome_if_accepted")) ? 0 : 1,
                heir.subtract(candidateAge).abs(), acceptance.negate(), candidate);
    }
    private static int compareFamily(Proposal first, Proposal second) {
        FamilyKey a = familyKey(first), b = familyKey(second); int result = Integer.compare(a.outcome(), b.outcome());
        if (result == 0) result = a.ageGap().compareTo(b.ageGap());
        if (result == 0) result = a.negativeAcceptance().compareTo(b.negativeAcceptance());
        if (result == 0) result = a.candidate().compareTo(b.candidate());
        if (result == 0) result = compareText(first.candidateId(), second.candidateId()); return result;
    }
    // Python orders Unicode scalar values, while String.compareTo orders UTF-16 code units.
    private static int compareText(String first, String second) {
        int a = 0, b = 0;
        while (a < first.length() && b < second.length()) {
            int ca = first.codePointAt(a), cb = second.codePointAt(b);
            if (ca != cb) return Integer.compare(ca, cb); a += Character.charCount(ca); b += Character.charCount(cb);
        }
        return Integer.compare(first.length() - a, second.length() - b);
    }
    private static Obj encode(Result result) {
        Map<String, Value> fields = new LinkedHashMap<>(); fields.put("policy", new Text("g2-m5-observed-opportunity-selector-v1"));
        fields.put("frame", encodeFrame(result.frame())); fields.put("status", new Text(result.selectedCandidateId() == null ? "wait" : "selected"));
        List<Value> evaluations = new ArrayList<>();
        for (Evaluation evaluation : result.evaluated()) evaluations.add(evaluation.proposal().normalizedFields().with("reason", new Text(evaluation.reason().name())));
        fields.put("evaluated", new Arr(evaluations)); fields.put("selected_candidate_id", result.selectedCandidateId() == null ? Nil.INSTANCE : new Text(result.selectedCandidateId()));
        fields.put("income_preference_applied", new Bool(result.incomePreferenceApplied())); fields.put("selection_basis", strings(SELECTION_BASIS));
        fields.put("selected_step", Nil.INSTANCE); fields.put("formal_action_ready", new Bool(false)); return new Obj(fields);
    }
    private static Obj encodeFrame(Frame frame) {
        return new Obj(Map.of("played_character_id", new IntegerValue(frame.playedCharacterId()), "native_revision", new IntegerValue(frame.nativeRevision()),
                "date_raw", new IntegerValue(frame.dateRaw()), "snapshot_id", new Text(frame.snapshotId()), "revision", new IntegerValue(frame.revision()),
                "episode_run_id", new Text(frame.episodeRunId())));
    }
    private static Arr integers(List<BigInteger> values) { return new Arr(values.stream().<Value>map(IntegerValue::new).toList()); }
    private static Arr strings(List<String> values) { return new Arr(values.stream().<Value>map(Text::new).toList()); }
}


