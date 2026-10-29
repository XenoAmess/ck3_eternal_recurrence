package org.xar.ck3.control.wave2.military.commander;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;
import static org.xar.ck3.control.wave2.military.commander.CommanderQuality.*;

/** Complete source-bound commander candidate DTO. Target reads do not change eligibility or the existing quality policy. */
public final class ArmyCommanderCandidatesCodec {
    public static final int MAX_BYTES = 64 * 1024 * 1024;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxStringLength(MAX_BYTES).maxNumberLength(1000).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    public static final String QUERY_TARGET_CAPABILITY = "game.command.query-army-commander-candidates-v1-for-army-N-at-province-P";
    private static final String PREFIX = "query-army-commander-candidates-v1-for-army-";
    private static final String CAPACITY_SCHEMA = "xar.ck3.commander-conditional-supply-capacity.12004.v1";
    private static final String BUILD_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Set<String> HEADER = keys("schema status snapshot_revision date_raw army_id native_carmy_id owner_character_id target_province_id eligibility_mode collection_filter_now collection_allow_guests current_commander candidate_collection_complete candidate_source_count candidates unavailable_reason current_movement_speed");
    private static final Set<String> CURRENT = keys("status character_id unavailable_reason current_total_martial current_native_ai_base_quality");
    private static final Set<String> CANDIDATE = keys("character_id available final_eligibility_observable can_assign quality_observable native_ai_base_quality generic_advantage_points siege_phase_time_modifier_raw unavailable_reason target_roll_bounds conditional_supply_capacity_v1");
    private static final Set<String> MOVEMENT = keys("schema source snapshot_revision date_raw context_observable public_cunit_id native_carmy_id owner_character_id current_commander_character_id current_province_id move_target_province_id route_source_count route_read_status army_state_code army_state in_combat retreating land naval current_edge");
    private ArmyCommanderCandidatesCodec() { }

    public record Province(int value) { public Province { require(value > 0, "positive native int32 ProvinceID required"); } }
    public enum CollectionStatus { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum RateStatus { AVAILABLE, UNAVAILABLE, NOT_APPLICABLE }
    public enum RouteStatus { NOT_ATTEMPTED, COMPLETE_EMPTY, COMPLETE_NONEMPTY, TARGET_ONLY, INVALID_HEADER, UNRESOLVED_ENTRY }
    public record Expected(NativeId army, BigInteger nativeRevision, BigInteger dateRaw, Optional<Province> target) {
        public Expected { Objects.requireNonNull(army); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(target); }
    }
    public record QueryStep(NativeId army, Optional<Province> target) {
        public QueryStep { Objects.requireNonNull(army); Objects.requireNonNull(target); }
        public String step() { return PREFIX + army.value() + target.map(p -> "-at-province-" + p.value()).orElse(""); }
        public String capability() { return target.isPresent() ? QUERY_TARGET_CAPABILITY : QUERY_CAPABILITY; }
    }
    /** Extensible original JSON is isolated here. Known contract fields are never stored as unvalidated extras. */
    public static final class Extensions {
        private final ObjectNode values;
        private Extensions(ObjectNode values) { this.values = values.deepCopy(); }
        public ObjectNode json() { return values.deepCopy(); }
        @Override public boolean equals(Object other) { return other instanceof Extensions e && values.equals(e.values); }
        @Override public int hashCode() { return values.hashCode(); }
    }
    public record Score(CurrentQuality quality, Extensions extras) { public Score { Objects.requireNonNull(quality); Objects.requireNonNull(extras); } }
    public record Current(RoleStatus status, Field<NativeId> character, Field<String> reason,
            Field<Score> quality, Field<Score> martial, Extensions extras) {
        public Current { Objects.requireNonNull(status); Objects.requireNonNull(character); Objects.requireNonNull(reason); Objects.requireNonNull(quality); Objects.requireNonNull(martial); Objects.requireNonNull(extras); }
        public CurrentRole core() { return new CurrentRole(status, character.value(), map(quality, Score::quality)); }
    }
    public record RollBounds(ObservationStatus status, Province target, Integer minimum, Integer maximum,
            String reason, Extensions extras) { public RollBounds { Objects.requireNonNull(status); Objects.requireNonNull(target); Objects.requireNonNull(extras); } }
    public record Capacity(ObservationStatus status, NativeId sourceCharacter, Long loadedFull, Long additive,
            Long multiplicative, Long conditional, String reason) { public Capacity { Objects.requireNonNull(status); } }
    public record Row(Field<NativeId> character, boolean available, boolean eligibilityObservable, Field<Boolean> canAssign,
            boolean qualityObservable, Field<Integer> quality, Field<Integer> advantage, Long siegePhaseRaw,
            Field<String> reason, Field<RollBounds> rolls, Field<Capacity> capacity, Extensions extras) {
        public Row { Objects.requireNonNull(character); Objects.requireNonNull(canAssign); Objects.requireNonNull(quality); Objects.requireNonNull(advantage); Objects.requireNonNull(reason); Objects.requireNonNull(rolls); Objects.requireNonNull(capacity); Objects.requireNonNull(extras); }
        public Candidate core() { return new Candidate(character.value(), available, eligibilityObservable, canAssign.value(), qualityObservable, quality.value(), advantage.value()); }
    }
    public record Rate(RateStatus status, Field<Long> raw, String getter, Field<String> reason, Extensions extras) {
        public Rate { Objects.requireNonNull(status); Objects.requireNonNull(raw); Objects.requireNonNull(getter); Objects.requireNonNull(reason); Objects.requireNonNull(extras); }
    }
    public record Movement(String schema, BigInteger nativeRevision, BigInteger dateRaw, boolean contextObservable,
            Field<NativeId> army, Field<NativeId> nativeArmy, Field<NativeId> owner, Field<NativeId> commander,
            Field<Province> currentProvince, Field<Province> moveTarget, Field<Integer> routeCount, RouteStatus routeStatus,
            Field<Integer> stateCode, Field<String> state, Field<Boolean> inCombat, Field<Boolean> retreating,
            Rate land, Rate naval, Rate currentEdge, Extensions extras) {
        public Movement { Objects.requireNonNull(schema); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(routeStatus); Objects.requireNonNull(land); Objects.requireNonNull(naval); Objects.requireNonNull(currentEdge); Objects.requireNonNull(extras); }
    }
    public record Observation(String schema, CollectionStatus status, BigInteger nativeRevision, BigInteger dateRaw,
            NativeId army, Field<NativeId> nativeArmy, Field<NativeId> owner, Field<Province> target, Current current,
            boolean collectionComplete, BigInteger sourceCount, List<Row> rows, Field<String> reason,
            Field<Movement> movement, Extensions extras) {
        public Observation { Objects.requireNonNull(schema); Objects.requireNonNull(status); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(army); Objects.requireNonNull(nativeArmy); Objects.requireNonNull(owner); Objects.requireNonNull(target); Objects.requireNonNull(current); Objects.requireNonNull(sourceCount); rows = List.copyOf(rows); Objects.requireNonNull(reason); Objects.requireNonNull(movement); Objects.requireNonNull(extras); }
        public Candidates qualityInput() {
            // The original proposal indexes these fields directly; normalization itself preserves legacy omissions.
            require(nativeArmy.presence() != Presence.MISSING && owner.presence() != Presence.MISSING && current.character().presence() != Presence.MISSING, "proposal requires original parent identity fields");
            List<Candidate> candidates = new ArrayList<>();
            for (Row row : rows) {
                if (row.available() && row.eligibilityObservable() && Boolean.TRUE.equals(row.canAssign().value()) && row.qualityObservable()) require(row.character().presence() != Presence.MISSING, "eligible proposal row lacks original character_id");
                candidates.add(row.core());
            }
            return new Candidates(army, nativeArmy.value(), owner.value(), current.core(), collectionComplete, sourceCount, candidates);
        }
    }
    public record ObservedQuery(Observation normalized, Frame frame, Proposal proposal) {
        public ObservedQuery { Objects.requireNonNull(normalized); Objects.requireNonNull(frame); Objects.requireNonNull(proposal); }
        public ObjectNode normalizedJson() { return node(normalized); }
        public ObjectNode publicV2NormalizedJson() { return publicV2Node(normalized); }
    }

    public static Optional<QueryStep> parseStep(String step) {
        if (step == null || !step.startsWith(PREFIX)) return Optional.empty(); String tail = step.substring(PREFIX.length()); String[] tokens = tail.split("-at-province-", -1);
        if (tokens.length < 1 || tokens.length > 2) return Optional.empty();
        try { NativeId army = new NativeId(canonical(tokens[0], false)); Optional<Province> target = tokens.length == 2 ? Optional.of(new Province(canonical(tokens[1], true))) : Optional.empty(); return Optional.of(new QueryStep(army, target)); }
        catch (IllegalArgumentException malformed) { return Optional.empty(); }
    }
    /** Full observed DTO boundary, including original decimal extension fields. The small proposal parser is not used for native frames. */
    public static JsonNode parseJson(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded nonempty commander JSON required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode value = JSON.readTree(text); require(value != null, "commander JSON value required"); return value;
        } catch (IOException malformed) { throw new ProjectionDomainRejection("invalid full commander JSON: " + malformed.getMessage()); }
    }
    public static byte[] encodeJson(JsonNode value) {
        Objects.requireNonNull(value); boundedDepth(value, 0);
        try { byte[] raw = JSON.writeValueAsBytes(value); require(raw.length <= MAX_BYTES, "commander JSON exceeds full frame byte budget"); return raw; }
        catch (IOException malformed) { throw new IllegalArgumentException("full commander JSON serialization failed", malformed); }
    }
    private static void boundedDepth(JsonNode value, int depth) { require(depth <= 64, "commander JSON nesting exceeds 64"); if (value.isContainerNode()) value.forEach(child -> boundedDepth(child, depth + 1)); }
    /** Explicit relocation of an existing SDK subtree. It carries original bytes, never a new domain decision. */
    public record OriginalAlias(String outputPointer, String sourcePointer) {
        public OriginalAlias { Objects.requireNonNull(outputPointer); Objects.requireNonNull(sourcePointer); require(outputPointer.startsWith("/") && sourcePointer.startsWith("/"), "original commander alias must use JSON pointers"); }
    }
    public static byte[] encodePreserving(byte[] original, JsonNode result, String origin, List<OriginalAlias> aliases) {
        Objects.requireNonNull(result); Objects.requireNonNull(origin); require(origin.isEmpty() || origin.startsWith("/"), "original commander origin must be a JSON pointer");
        boundedDepth(result, 0); return new OriginalSource(original).merge(result, origin, List.copyOf(aliases));
    }
    private record TokenSpan(int begin, int end) { }
    /** Same original-token preservation as the selected formal consumer, with this DTO's full-frame budget. */
    private static final class OriginalSource {
        private final byte[] raw;
        private final JsonNode tree;
        private final Map<String,TokenSpan> spans = new LinkedHashMap<>();
        private OriginalSource(byte[] original) {
            tree = parseJson(original); raw = original.clone();
            try (JsonParser parser = JSON.getFactory().createParser(raw)) { parser.nextToken(); collect(parser, ""); }
            catch (IOException malformed) { throw new ProjectionDomainRejection("invalid original commander JSON tokens: " + malformed.getMessage()); }
        }
        private void collect(JsonParser parser, String pointer) throws IOException {
            int begin = Math.toIntExact(parser.currentTokenLocation().getByteOffset()); JsonToken token = parser.currentToken();
            if (token == JsonToken.START_OBJECT) {
                while (parser.nextToken() != JsonToken.END_OBJECT) { String name = parser.currentName(); parser.nextToken(); collect(parser, pointer + "/" + escape(name)); }
            } else if (token == JsonToken.START_ARRAY) {
                int index = 0; while (parser.nextToken() != JsonToken.END_ARRAY) collect(parser, pointer + "/" + index++);
            }
            parser.finishToken(); spans.put(pointer, new TokenSpan(begin, Math.toIntExact(parser.currentLocation().getByteOffset())));
        }
        private byte[] merge(JsonNode result, String origin, List<OriginalAlias> aliases) {
            ByteArrayOutputStream out = new ByteArrayOutputStream(); emit(result, "", origin, aliases, out); return out.toByteArray();
        }
        private void emit(JsonNode value, String outputPath, String origin, List<OriginalAlias> aliases, ByteArrayOutputStream out) {
            String actualOrigin = origin;
            for (OriginalAlias alias : aliases) if (alias.outputPointer().equals(outputPath)) actualOrigin = alias.sourcePointer();
            JsonNode original = tree.at(actualOrigin);
            if (!original.isMissingNode() && value.equals(original)) { TokenSpan span = spans.get(actualOrigin); if (span == null) throw new IllegalStateException("actual commander source token missing"); append(out, java.util.Arrays.copyOfRange(raw, span.begin(), span.end())); return; }
            if (value.isObject()) {
                append(out, ascii("{")); boolean first = true;
                for (var field : value.properties()) { if (!first) append(out, ascii(",")); first = false; append(out, encodeJson(StrictJson.object().textNode(field.getKey()))); append(out, ascii(":")); String suffix = "/" + escape(field.getKey()); emit(field.getValue(), outputPath + suffix, actualOrigin + suffix, aliases, out); }
                append(out, ascii("}"));
            } else if (value.isArray()) {
                append(out, ascii("[")); for (int i = 0; i < value.size(); i++) { if (i > 0) append(out, ascii(",")); emit(value.get(i), outputPath + "/" + i, actualOrigin + "/" + i, aliases, out); } append(out, ascii("]"));
            } else if (value.isFloatingPointNumber()) { throw new IllegalArgumentException("result decimal lacks its declared original commander SDK pointer"); }
            else append(out, encodeJson(value));
        }
        private static String escape(String key) { return key.replace("~", "~0").replace("/", "~1"); }
        private static byte[] ascii(String value) { return value.getBytes(StandardCharsets.US_ASCII); }
        private static void append(ByteArrayOutputStream out, byte[] value) { require(out.size() + value.length <= MAX_BYTES, "commander source-preserving JSON exceeds full-frame byte budget"); out.writeBytes(value); }
    }
    public static Observation normalize(byte[] raw, Expected expected) { return normalize(parseJson(raw), expected); }
    public static Observation normalize(JsonNode raw, Expected expected) {
        Objects.requireNonNull(expected); ObjectNode n = object(raw); String schema = text(n.get("schema"));
        require(Set.of("ck3_12003_army_commander_candidates_v1", "ck3_12004_army_commander_candidates_v1").contains(schema), "unsupported native commander candidates schema");
        CollectionStatus status = enumeration(n.get("status"), CollectionStatus.class); BigInteger revision = integer(n.get("snapshot_revision")), date = integer(n.get("date_raw")); NativeId army = id(n.get("army_id"));
        require(army.equals(expected.army()) && revision.equals(expected.nativeRevision()) && date.equals(expected.dateRaw()), "native commander payload crossed requested army/revision/date");
        Field<Province> target = field(n, "target_province_id", ArmyCommanderCandidatesCodec::province);
        if (expected.target().isEmpty()) require(target.value() == null, "native commander target was not requested"); else require(expected.target().get().equals(target.value()), "native commander target differs from requested Province");
        Field<NativeId> nativeArmy = field(n, "native_carmy_id", ArmyCommanderCandidatesCodec::id), owner = field(n, "owner_character_id", ArmyCommanderCandidatesCodec::id);
        require(integer(n.get("eligibility_mode")).equals(BigInteger.ONE) && !bool(n.get("collection_filter_now")) && bool(n.get("collection_allow_guests")), "native commander collection mode differs");
        Current current = current(n.get("current_commander")); boolean complete = bool(n.get("candidate_collection_complete")); BigInteger count = integer(n.get("candidate_source_count")); require(count.signum() >= 0, "candidate source count is negative");
        List<Row> rows = new ArrayList<>(); for (JsonNode row : array(n.get("candidates"))) rows.add(row(row, expected.target(), schema));
        Field<Movement> movement = field(n, "current_movement_speed", value -> movement(value, expected, nativeArmy.value(), owner.value(), current));
        return new Observation(schema, status, revision, date, army, nativeArmy, owner, target, current, complete, count, rows, field(n, "unavailable_reason", ArmyCommanderCandidatesCodec::text), movement, extras(n, HEADER));
    }
    public static Proposal propose(Observation input, Frame frame) {
        require(input.nativeRevision().equals(frame.nativeRevision()) && input.dateRaw().equals(frame.dateRaw()), "proposal crossed normalized native frame");
        return CommanderQuality.propose(input.qualityInput(), frame);
    }
    private static Current current(JsonNode raw) {
        ObjectNode n = object(raw); RoleStatus status = enumeration(n.get("status"), RoleStatus.class); Field<NativeId> id = field(n, "character_id", ArmyCommanderCandidatesCodec::id);
        require(status != RoleStatus.AVAILABLE || id.value() != null, "available current commander lacks original ID"); require(status != RoleStatus.ABSENT || id.value() == null, "absent current commander has ID");
        Field<Score> quality = field(n, "current_native_ai_base_quality", value -> score(value, id.value(), status, false));
        Field<Score> martial = field(n, "current_total_martial", value -> score(value, id.value(), status, true));
        return new Current(status, id, field(n, "unavailable_reason", ArmyCommanderCandidatesCodec::text), quality, martial, extras(n, CURRENT));
    }
    private static Score score(JsonNode raw, NativeId parent, RoleStatus role, boolean martial) {
        ObjectNode n = object(raw); Set<String> known = martial ? keys("status source source_character_id skill_index value unavailable_reason") : keys("status source source_character_id value unavailable_reason"); required(n, known);
        eq(n.get("source"), martial ? "native_current_assigned_commander_total_skill_cache" : "native_current_assigned_commander_ai_base_quality");
        if (martial) require(integer(n.get("skill_index")).equals(BigInteger.ONE), "current martial must use total skill index 1");
        ObservationStatus status = enumeration(n.get("status"), ObservationStatus.class); NativeId source = nullable(n.get("source_character_id"), ArmyCommanderCandidatesCodec::id); require(Objects.equals(source, parent), "current score source differs from assigned commander");
        Integer value = nullable(n.get("value"), ArmyCommanderCandidatesCodec::i32); String reason = nullable(n.get("unavailable_reason"), ArmyCommanderCandidatesCodec::text);
        require(status == ObservationStatus.AVAILABLE ? role == RoleStatus.AVAILABLE && source != null && value != null && reason == null : value == null && nonblank(reason), "current score availability/value/reason differs");
        return new Score(new CurrentQuality(status, source, value, reason), extras(n, known));
    }
    private static Row row(JsonNode raw, Optional<Province> target, String schema) {
        ObjectNode n = object(raw); Field<NativeId> id = field(n, "character_id", ArmyCommanderCandidatesCodec::id); boolean available = bool(n.get("available")), eligible = bool(n.get("final_eligibility_observable")), qualityObservable = bool(n.get("quality_observable"));
        Field<Boolean> assign = field(n, "can_assign", ArmyCommanderCandidatesCodec::bool); Field<Integer> quality = field(n, "native_ai_base_quality", ArmyCommanderCandidatesCodec::i32), advantage = field(n, "generic_advantage_points", ArmyCommanderCandidatesCodec::i32);
        require(eligible == (assign.value() != null) && qualityObservable == (quality.value() != null) && qualityObservable == (advantage.value() != null), "independent candidate observation status/value differs");
        Long phase = nullable(n.get("siege_phase_time_modifier_raw"), ArmyCommanderCandidatesCodec::i64);
        return new Row(id, available, eligible, assign, qualityObservable, quality, advantage, phase, field(n, "unavailable_reason", ArmyCommanderCandidatesCodec::text),
                field(n, "target_roll_bounds", value -> rolls(value, target)), field(n, "conditional_supply_capacity_v1", value -> capacity(value, id.value(), schema)), extras(n, CANDIDATE));
    }
    private static RollBounds rolls(JsonNode raw, Optional<Province> target) {
        require(target.isPresent(), "target roll observation lacks requested Province"); ObjectNode n = object(raw); required(n, keys("effective_min_roll effective_max_roll unavailable_reason"));
        ObservationStatus status = enumeration(n.get("status"), ObservationStatus.class); eq(n.get("source"), "native_current_candidate_target_roll_context"); Province source = province(n.get("source_target_province_id")); require(target.get().equals(source), "candidate roll Province differs from request");
        Integer min = nullable(n.get("effective_min_roll"), ArmyCommanderCandidatesCodec::i32), max = nullable(n.get("effective_max_roll"), ArmyCommanderCandidatesCodec::i32); String reason = nullable(n.get("unavailable_reason"), ArmyCommanderCandidatesCodec::text);
        require(status == ObservationStatus.AVAILABLE ? min != null && max != null && reason == null : min == null && max == null && nonblank(reason), "roll status/value/reason differs");
        return new RollBounds(status, source, min, max, reason, extras(n, keys("status source source_target_province_id effective_min_roll effective_max_roll unavailable_reason")));
    }
    private static Capacity capacity(JsonNode raw, NativeId character, String schema) {
        require(schema.equals("ck3_12004_army_commander_candidates_v1"), "conditional capacity requires actual .4 candidate schema");
        ObjectNode n = closedObject(raw, keys("schema status source_character_id scale loaded_full_raw additive_modifier_raw multiplicative_modifier_raw conditional_capacity_raw assignment_applied assumption unavailable_reason provenance"));
        eq(n.get("schema"), CAPACITY_SCHEMA); ObservationStatus status = enumeration(n.get("status"), ObservationStatus.class); require(integer(n.get("scale")).equals(BigInteger.valueOf(100000)) && !bool(n.get("assignment_applied")), "capacity scale/assignment state differs"); eq(n.get("assumption"), "candidate_aggregate_unchanged_after_assignment");
        ObjectNode p = closedObject(n.get("provenance"), keys("game_version executable_sha256 capacity_rva loaded_full_rva additive_modifier_id multiplicative_modifier_id"));
        eq(p.get("game_version"), "1.20.0.4"); eq(p.get("executable_sha256"), BUILD_SHA); constant(p, "capacity_rva", 0x2c53bf0); constant(p, "loaded_full_rva", 0x5c68c70); constant(p, "additive_modifier_id", 467); constant(p, "multiplicative_modifier_id", 468);
        NativeId source = nullable(n.get("source_character_id"), ArmyCommanderCandidatesCodec::id); require(Objects.equals(source, character), "conditional capacity source differs from candidate");
        Long loaded = raw64(n.get("loaded_full_raw")), add = raw64(n.get("additive_modifier_raw")), mult = raw64(n.get("multiplicative_modifier_raw")), conditional = raw64(n.get("conditional_capacity_raw")); String reason = nullable(n.get("unavailable_reason"), ArmyCommanderCandidatesCodec::text);
        if (status == ObservationStatus.AVAILABLE) { require(source != null && loaded != null && add != null && mult != null && conditional != null && reason == null, "available capacity lacks native inputs");
            require(conditional == LandStockPolicy.nativeFixedMultiply(loaded + add, 100000L + mult), "conditional capacity differs from native wrapped fixed multiply"); }
        else require(conditional == null && nonblank(reason), "unavailable capacity requires null derived value and concrete reason");
        return new Capacity(status, source, loaded, add, mult, conditional, reason);
    }
    private static Movement movement(JsonNode raw, Expected expected, NativeId nativeArmy, NativeId owner, Current current) {
        ObjectNode n = object(raw); String schema = text(n.get("schema")); require(Set.of("ck3_12003_army_current_movement_speed_v1", "ck3_12004_army_current_movement_speed_v1").contains(schema), "unsupported selected-unit movement schema"); eq(n.get("source"), "native_selected_cunit_movement_rates");
        BigInteger revision = integer(n.get("snapshot_revision")), date = integer(n.get("date_raw")); require(revision.equals(expected.nativeRevision()) && date.equals(expected.dateRaw()), "selected-unit movement native frame differs"); boolean observable = bool(n.get("context_observable"));
        Field<NativeId> army = field(n, "public_cunit_id", ArmyCommanderCandidatesCodec::id), nativeId = field(n, "native_carmy_id", ArmyCommanderCandidatesCodec::id), ownerId = field(n, "owner_character_id", ArmyCommanderCandidatesCodec::id), commander = field(n, "current_commander_character_id", ArmyCommanderCandidatesCodec::id);
        Field<Province> currentProvince = field(n, "current_province_id", ArmyCommanderCandidatesCodec::province), target = field(n, "move_target_province_id", ArmyCommanderCandidatesCodec::province);
        Field<Integer> count = field(n, "route_source_count", ArmyCommanderCandidatesCodec::i32); require(count.value() == null || count.value() >= 0, "selected-unit route count cannot be negative"); RouteStatus route = enumeration(n.get("route_read_status"), RouteStatus.class);
        Field<Integer> code = field(n, "army_state_code", ArmyCommanderCandidatesCodec::i32); Field<String> state = field(n, "army_state", ArmyCommanderCandidatesCodec::text); Field<Boolean> combat = field(n, "in_combat", ArmyCommanderCandidatesCodec::bool), retreat = field(n, "retreating", ArmyCommanderCandidatesCodec::bool);
        if (observable) {
            require(expected.army().equals(army.value()) && nativeId.value() != null && ownerId.value() != null && (nativeArmy == null || nativeArmy.equals(nativeId.value())) && (owner == null || owner.equals(ownerId.value())), "selected-unit movement receiver differs");
            if (current.status() == RoleStatus.AVAILABLE || current.status() == RoleStatus.ABSENT) require(Objects.equals(current.character().value(), commander.value()), "selected-unit current commander differs");
            require(code.value() != null && state.value() != null && combat.value() != null && retreat.value() != null, "observable selected-unit state lacks actual values");
        } else for (Field<?> value : List.of(army, nativeId, ownerId, commander, currentProvince, target, count, code, state, combat, retreat)) require(value.value() == null, "unavailable selected-unit context must preserve unknown values");
        return new Movement(schema, revision, date, observable, army, nativeId, ownerId, commander, currentProvince, target, count, route, code, state, combat, retreat,
                rate(n.get("land"), false, route, Set.of("0x24AA940", "0x24AA920")), rate(n.get("naval"), false, route, Set.of("0x24AAC00", "0x24AABE0")),
                rate(n.get("current_edge"), true, route, Set.of("0x24AB5C0", "0x24AB5A0")), extras(n, MOVEMENT));
    }
    private static Rate rate(JsonNode raw, boolean edge, RouteStatus route, Set<String> getters) {
        ObjectNode n = object(raw); RateStatus status = enumeration(n.get("status"), RateStatus.class); require(edge || status != RateStatus.NOT_APPLICABLE, "only current edge can be not applicable"); require(integer(n.get("scale")).equals(BigInteger.valueOf(100000)), "movement rate exact scale differs");
        String getter = text(n.get("native_getter_rva")); require(getters.contains(getter), "movement rate native getter differs"); Field<Long> value = field(n, "raw", ArmyCommanderCandidatesCodec::i64); require((status == RateStatus.AVAILABLE) == (value.value() != null), "movement rate status/raw differs");
        Field<String> reason = field(n, "unavailable_reason", ArmyCommanderCandidatesCodec::text); if (status == RateStatus.NOT_APPLICABLE) require(route == RouteStatus.COMPLETE_EMPTY && "empty_route".equals(reason.value()), "not-applicable edge requires original complete empty route");
        return new Rate(status, value, getter, reason, extras(n, keys("status raw scale native_getter_rva unavailable_reason")));
    }

    public static byte[] encode(Observation value) { return encodeJson(node(value)); }
    public static ObjectNode node(Observation value) {
        ObjectNode n = value.extras().json().put("schema", value.schema()).put("status", wire(value.status())).put("snapshot_revision", value.nativeRevision()).put("date_raw", value.dateRaw()).put("army_id", value.army().value());
        write(n, "native_carmy_id", value.nativeArmy(), ArmyCommanderCandidatesCodec::idNode); write(n, "owner_character_id", value.owner(), ArmyCommanderCandidatesCodec::idNode); write(n, "target_province_id", value.target(), p -> StrictJson.object().numberNode(p.value()));
        n.put("eligibility_mode", 1).put("collection_filter_now", false).put("collection_allow_guests", true).put("candidate_collection_complete", value.collectionComplete()).put("candidate_source_count", value.sourceCount()); n.set("current_commander", currentNode(value.current()));
        ArrayNode rows = n.putArray("candidates"); value.rows().forEach(row -> rows.add(rowNode(row))); write(n, "unavailable_reason", value.reason(), v -> StrictJson.object().textNode(v)); write(n, "current_movement_speed", value.movement(), ArmyCommanderCandidatesCodec::movementNode); return n;
    }
    private static ObjectNode currentNode(Current value) {
        ObjectNode n = value.extras().json().put("status", wire(value.status())); write(n, "character_id", value.character(), ArmyCommanderCandidatesCodec::idNode); write(n, "unavailable_reason", value.reason(), v -> StrictJson.object().textNode(v)); write(n, "current_native_ai_base_quality", value.quality(), v -> scoreNode(v, false)); write(n, "current_total_martial", value.martial(), v -> scoreNode(v, true)); return n;
    }
    private static ObjectNode scoreNode(Score value, boolean martial) {
        CurrentQuality q = value.quality(); ObjectNode n = value.extras().json().put("status", wire(q.status())).put("source", martial ? "native_current_assigned_commander_total_skill_cache" : "native_current_assigned_commander_ai_base_quality");
        n.set("source_character_id", q.sourceCharacterId() == null ? NullNode.getInstance() : idNode(q.sourceCharacterId())); number(n, "value", q.value()); string(n, "unavailable_reason", q.unavailableReason()); if (martial) n.put("skill_index", 1); return n;
    }
    private static ObjectNode rowNode(Row value) {
        ObjectNode n = value.extras().json().put("available", value.available()).put("final_eligibility_observable", value.eligibilityObservable()).put("quality_observable", value.qualityObservable());
        write(n, "character_id", value.character(), ArmyCommanderCandidatesCodec::idNode); write(n, "can_assign", value.canAssign(), v -> StrictJson.object().booleanNode(v)); write(n, "native_ai_base_quality", value.quality(), v -> StrictJson.object().numberNode(v)); write(n, "generic_advantage_points", value.advantage(), v -> StrictJson.object().numberNode(v));
        number(n, "siege_phase_time_modifier_raw", value.siegePhaseRaw()); write(n, "unavailable_reason", value.reason(), v -> StrictJson.object().textNode(v)); write(n, "target_roll_bounds", value.rolls(), ArmyCommanderCandidatesCodec::rollNode); write(n, "conditional_supply_capacity_v1", value.capacity(), ArmyCommanderCandidatesCodec::capacityNode); return n;
    }
    private static ObjectNode rollNode(RollBounds value) {
        ObjectNode n = value.extras().json().put("status", wire(value.status())).put("source", "native_current_candidate_target_roll_context").put("source_target_province_id", value.target().value()); number(n, "effective_min_roll", value.minimum()); number(n, "effective_max_roll", value.maximum()); string(n, "unavailable_reason", value.reason()); return n;
    }
    private static ObjectNode capacityNode(Capacity value) {
        ObjectNode n = StrictJson.object().put("schema", CAPACITY_SCHEMA).put("status", wire(value.status())).put("scale", 100000).put("assignment_applied", false).put("assumption", "candidate_aggregate_unchanged_after_assignment"); n.set("source_character_id", value.sourceCharacter() == null ? NullNode.getInstance() : idNode(value.sourceCharacter()));
        decimal(n, "loaded_full_raw", value.loadedFull()); decimal(n, "additive_modifier_raw", value.additive()); decimal(n, "multiplicative_modifier_raw", value.multiplicative()); decimal(n, "conditional_capacity_raw", value.conditional()); string(n, "unavailable_reason", value.reason());
        n.putObject("provenance").put("game_version", "1.20.0.4").put("executable_sha256", BUILD_SHA).put("capacity_rva", 0x2c53bf0).put("loaded_full_rva", 0x5c68c70).put("additive_modifier_id", 467).put("multiplicative_modifier_id", 468); return n;
    }
    private static ObjectNode movementNode(Movement v) {
        ObjectNode n = v.extras().json().put("schema", v.schema()).put("source", "native_selected_cunit_movement_rates").put("snapshot_revision", v.nativeRevision()).put("date_raw", v.dateRaw()).put("context_observable", v.contextObservable()).put("route_read_status", wire(v.routeStatus()));
        write(n, "public_cunit_id", v.army(), ArmyCommanderCandidatesCodec::idNode); write(n, "native_carmy_id", v.nativeArmy(), ArmyCommanderCandidatesCodec::idNode); write(n, "owner_character_id", v.owner(), ArmyCommanderCandidatesCodec::idNode); write(n, "current_commander_character_id", v.commander(), ArmyCommanderCandidatesCodec::idNode);
        write(n, "current_province_id", v.currentProvince(), p -> StrictJson.object().numberNode(p.value())); write(n, "move_target_province_id", v.moveTarget(), p -> StrictJson.object().numberNode(p.value())); write(n, "route_source_count", v.routeCount(), p -> StrictJson.object().numberNode(p)); write(n, "army_state_code", v.stateCode(), p -> StrictJson.object().numberNode(p)); write(n, "army_state", v.state(), p -> StrictJson.object().textNode(p)); write(n, "in_combat", v.inCombat(), p -> StrictJson.object().booleanNode(p)); write(n, "retreating", v.retreating(), p -> StrictJson.object().booleanNode(p)); n.set("land", rateNode(v.land())); n.set("naval", rateNode(v.naval())); n.set("current_edge", rateNode(v.currentEdge())); return n;
    }
    private static ObjectNode rateNode(Rate v) {
        ObjectNode n = v.extras().json().put("status", wire(v.status())).put("scale", 100000).put("native_getter_rva", v.getter()); write(n, "raw", v.raw(), p -> StrictJson.object().numberNode(p)); write(n, "unavailable_reason", v.reason(), p -> StrictJson.object().textNode(p)); return n;
    }
    /** Declared public v2 numeric representation; raw native DTO serialization above remains unchanged. */
    public static ObjectNode publicV2Node(Observation value) {
        ObjectNode n = node(value); n.put("snapshot_revision", value.nativeRevision().toString()).put("date_raw", value.dateRaw().toString()).put("candidate_source_count", value.sourceCount().toString());
        for (JsonNode row : n.withArray("candidates")) if (row.hasNonNull("siege_phase_time_modifier_raw")) ((ObjectNode) row).put("siege_phase_time_modifier_raw", row.get("siege_phase_time_modifier_raw").bigIntegerValue().toString());
        if (n.hasNonNull("current_movement_speed")) { ObjectNode m = (ObjectNode) n.get("current_movement_speed"); m.put("snapshot_revision", value.movement().value().nativeRevision().toString()).put("date_raw", value.movement().value().dateRaw().toString());
            for (String key : List.of("land", "naval", "current_edge")) { ObjectNode rate = (ObjectNode) m.get(key); if (rate.hasNonNull("raw")) rate.put("raw", rate.get("raw").bigIntegerValue().toString()); } }
        safePublicIntegers(n); return n;
    }

    private static void safePublicIntegers(JsonNode n) {
        if (n.isIntegralNumber()) require(n.bigIntegerValue().abs().compareTo(BigInteger.valueOf(9007199254740991L)) <= 0, "undeclared wide extension integer must retain its native archive instead of a rounded public JSON number");
        else if (n.isContainerNode()) n.forEach(ArmyCommanderCandidatesCodec::safePublicIntegers);
    }

    private static Extensions extras(ObjectNode n, Set<String> known) { ObjectNode copy = n.deepCopy(); known.forEach(copy::remove); return new Extensions(copy); }
    private static <T> Field<T> field(ObjectNode n, String key, Function<JsonNode,T> decoder) { if (!n.has(key)) return Field.missing(); return n.get(key).isNull() ? Field.nullValue() : Field.of(decoder.apply(n.get(key))); }
    private static <A,B> Field<B> map(Field<A> field, Function<A,B> mapper) { return switch (field.presence()) { case MISSING -> Field.missing(); case NULL -> Field.nullValue(); case VALUE -> Field.of(mapper.apply(field.value())); }; }
    private static <T> void write(ObjectNode n, String key, Field<T> field, Function<T,JsonNode> encoder) { if (field.presence() != Presence.MISSING) n.set(key, field.presence() == Presence.NULL ? NullNode.getInstance() : encoder.apply(field.value())); }
    private static <T> T nullable(JsonNode n, Function<JsonNode,T> decoder) { return n == null || n.isNull() ? null : decoder.apply(n); }
    private static ObjectNode object(JsonNode n) { require(n != null && n.isObject(), "commander native object required"); return (ObjectNode) n; }
    private static ArrayNode array(JsonNode n) { require(n != null && n.isArray(), "commander candidate array required"); return (ArrayNode) n; }
    private static NativeId id(JsonNode n) { return new NativeId((int) boundedInteger(n, 0, Integer.MAX_VALUE)); }
    private static Province province(JsonNode n) { return new Province((int) boundedInteger(n, 1, Integer.MAX_VALUE)); }
    private static JsonNode idNode(NativeId id) { return StrictJson.object().numberNode(id.value()); }
    private static int i32(JsonNode n) { return (int) boundedInteger(n, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static long i64(JsonNode n) { return boundedInteger(n, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static BigInteger integer(JsonNode n) { require(n != null && n.isIntegralNumber(), "exact integer token required"); return n.bigIntegerValue(); }
    private static String text(JsonNode n) { require(n != null && n.isTextual(), "exact native string required"); return n.textValue(); }
    private static boolean bool(JsonNode n) { require(n != null && n.isBoolean(), "exact native boolean required"); return n.booleanValue(); }
    private static int canonical(String token, boolean positive) { require(token.matches("0|[1-9][0-9]*"), "canonical unsigned decimal token required"); int value = Integer.parseInt(token); require(!positive || value > 0, "positive Province token required"); return value; }
    private static Long raw64(JsonNode n) { if (n.isNull()) return null; String token = text(n); require(token.matches("0|-?[1-9][0-9]*"), "canonical signed64 decimal string required"); try { return Long.valueOf(token); } catch (NumberFormatException malformed) { throw new ProjectionDomainRejection("capacity decimal exceeds signed64 native domain"); } }
    private static boolean nonblank(String reason) { return reason != null && reason.codePoints().anyMatch(c -> !Character.isWhitespace(c) && !Character.isSpaceChar(c) && c != 0x85); }
    private static void required(ObjectNode n, Set<String> keys) { for (String key : keys) require(n.has(key), "missing native observation field: " + key); }
    private static Set<String> keys(String names) { return Set.of(names.split(" ")); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(java.util.Locale.ROOT); }
    private static <T extends Enum<T>> T enumeration(JsonNode n, Class<T> type) { String wire = text(n); T value; try { value = Enum.valueOf(type, wire.toUpperCase(java.util.Locale.ROOT)); } catch (IllegalArgumentException malformed) { throw new ProjectionDomainRejection("invalid commander native status"); } require(wire(value).equals(wire), "exact native status spelling required"); return value; }
    private static void eq(JsonNode n, String value) { require(value.equals(text(n)), "native source/schema differs"); }
    private static void constant(ObjectNode n, String key, long value) { require(integer(n.get(key)).equals(BigInteger.valueOf(value)), "native exact-build provenance differs: " + key); }
    private static void number(ObjectNode n, String key, Number value) { if (value == null) n.putNull(key); else n.put(key, value.longValue()); }
    private static void string(ObjectNode n, String key, String value) { if (value == null) n.putNull(key); else n.put(key, value); }
    private static void decimal(ObjectNode n, String key, Long value) { if (value == null) n.putNull(key); else n.put(key, value.toString()); }
    private static void require(boolean value, String message) { if (!value) throw new ProjectionDomainRejection(message); }
    private static long boundedInteger(JsonNode value, long minimum, long maximum) {
        try { return StrictJson.integer(value, minimum, maximum); } catch (ContractViolationException error) { throw new ProjectionDomainRejection(error.getMessage()); }
    }
    private static ObjectNode closedObject(JsonNode value, Set<String> keys) {
        try { return StrictJson.object(value, keys); } catch (ContractViolationException error) { throw new ProjectionDomainRejection(error.getMessage()); }
    }
}
