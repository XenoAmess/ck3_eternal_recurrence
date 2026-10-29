package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import org.xar.ck3.control.nativebridge.capabilities.army.NativePropertyFold2303120.Block;

/** Typed source evidence to complete group PCs and exact weighted requests, without native initialization. */
public final class BattlePersonProvinceCalculation {
    private BattlePersonProvinceCalculation() { }
    public static final String INCOMING_STAGE = "post2920D60_pre291CD9D";
    public static final String PROSPECTIVE_STAGE = "post2921350_pre291CDA8";
    private static final String COLD = BattlePersonProvinceCodec.COLD_REASON;
    public enum Resolution { REGISTRY_FULL_ID, NATIVE_FALLBACK }
    public enum TierSelection { INDEXED_TIER, COLD_DEFAULT_5D65B00, INITIALIZED_DEFAULT_5D65B00 }
    public record WalkEvidence(OptionalInt tier, OptionalInt childrenCount, boolean childIdsPresent, boolean collected, Optional<String> reason) {
        public WalkEvidence { Objects.requireNonNull(tier); Objects.requireNonNull(childrenCount); Objects.requireNonNull(reason); }
    }
    public record PcEvidence(Optional<String> identity, Optional<Block> block, boolean ready) {
        public PcEvidence { Objects.requireNonNull(identity); Objects.requireNonNull(block); }
    }
    public record SourceEvidence(int nativeIndex, OptionalInt group, Optional<String> reason, Optional<Resolution> resolution,
            Optional<String> identity, Optional<String> definitionIdentity, boolean mapReady, Optional<String> mapReason,
            boolean tiersReady, Optional<String> tierReason, Optional<TierSelection> tierSelection, OptionalInt defaultGuard, PcEvidence pc) {
        public SourceEvidence {
            Objects.requireNonNull(group); Objects.requireNonNull(reason); Objects.requireNonNull(resolution);
            Objects.requireNonNull(identity); Objects.requireNonNull(definitionIdentity); Objects.requireNonNull(mapReason);
            Objects.requireNonNull(tierReason); Objects.requireNonNull(tierSelection); Objects.requireNonNull(defaultGuard); Objects.requireNonNull(pc);
        }
    }
    public record ProvinceEvidence(int nativeIndex, Optional<String> identity, boolean stepsPresent, boolean stepReasonsClear,
            OptionalInt lastTier, Optional<Boolean> admitted, OptionalInt sourceCount, boolean sourceIdsPresent, List<SourceEvidence> sources) {
        public ProvinceEvidence {
            Objects.requireNonNull(identity); Objects.requireNonNull(lastTier); Objects.requireNonNull(admitted); Objects.requireNonNull(sourceCount);
            sources = List.copyOf(sources);
        }
    }
    public record Evidence(int characterId, Optional<String> characterIdentity, boolean ready, Optional<String> reason,
            boolean titleSourceReady, OptionalInt titleCount, List<WalkEvidence> walk, List<ProvinceEvidence> provinces,
            boolean managerReady, OptionalInt groupCount) {
        public Evidence {
            Objects.requireNonNull(characterIdentity); Objects.requireNonNull(reason); Objects.requireNonNull(titleCount); Objects.requireNonNull(groupCount);
            walk = List.copyOf(walk); provinces = List.copyOf(provinces);
        }
    }
    public record Occurrence(int provinceNativeIndex, int sourceNativeIndex, Optional<String> propertyIdentity, boolean modeledColdReturn) {
        public Occurrence { Objects.requireNonNull(propertyIdentity); }
        public ObjectNode toJson() {
            ObjectNode row = object(); row.put("province_native_index", provinceNativeIndex); row.put("source_native_index", sourceNativeIndex);
            if (propertyIdentity.isPresent()) row.put("property_identity", propertyIdentity.orElseThrow()); else row.putNull("property_identity");
            if (modeledColdReturn) { row.put("kind", "modeled_2560620_normal_return"); row.put("tier_pc_source_rva", 0x5D65E80); row.put("raw_pc_observed", false); }
            return row;
        }
    }
    public record BoundUpdate(Occurrence occurrence, NativePropertyFold2303120.Update update) {
        public BoundUpdate { Objects.requireNonNull(occurrence); Objects.requireNonNull(update); }
        public ObjectNode toJson() { ObjectNode row = occurrence.toJson(); row.setAll(update.toJson()); return row; }
    }
    public record Group(int nativeIndex, boolean ready, Optional<String> reason, Block propertyBlock,
            List<Occurrence> innerOccurrences, List<BoundUpdate> updates) {
        public Group { Objects.requireNonNull(reason); Objects.requireNonNull(propertyBlock); innerOccurrences = List.copyOf(innerOccurrences); updates = List.copyOf(updates); }
        public ObjectNode toJson() {
            ObjectNode row = object(); row.put("native_index", nativeIndex); row.put("ready", ready);
            if (reason.isPresent()) row.put("reason", reason.orElseThrow()); else row.putNull("reason");
            row.set("property_block", propertyBlock.toJson()); var occurrences = row.putArray("inner_occurrences");
            innerOccurrences.forEach(value -> occurrences.add(value.toJson())); var changes = row.putArray("updates");
            updates.forEach(value -> changes.add(value.toJson())); return row;
        }
    }
    public record WeightedRequest(int sourceOrdinal, String sourceName, int firstRowIndex, int rowCount,
            String definitionIdentity, Block basePropertyBlock, long weightQ64) {
        public WeightedRequest { Objects.requireNonNull(sourceName); Objects.requireNonNull(definitionIdentity); Objects.requireNonNull(basePropertyBlock); }
        public ObjectNode toJson() {
            ObjectNode row = object(); row.put("source_ordinal", sourceOrdinal); row.put("source_name", sourceName);
            row.put("first_row_index", firstRowIndex); row.put("row_count", rowCount); row.put("definition_identity", definitionIdentity);
            row.set("base_property_block", basePropertyBlock.toJson()); row.put("weight_q64", weightQ64); return row;
        }
    }
    public record ColdProjection(int characterFullId, int provinceNativeIndex, int sourceNativeIndex, OptionalInt groupIndex,
            Optional<String> actualSourceIdentity, TierSelection actualSelection, int actualDefaultGuard) {
        public ColdProjection {
            Objects.requireNonNull(groupIndex); Objects.requireNonNull(actualSourceIdentity);
            require(actualSelection == TierSelection.COLD_DEFAULT_5D65B00 && (actualDefaultGuard == 0 || actualDefaultGuard == -1),
                    BattlePersonProvinceCodec.FIELD, "only named modeled cold normal-return premise may be projected");
        }
        public ObjectNode toJson() {
            ObjectNode row = object(); row.put("kind", "modeled_2560620_normal_return"); row.put("character_full_id", characterFullId);
            row.put("province_native_index", provinceNativeIndex); row.put("source_native_index", sourceNativeIndex);
            if (groupIndex.isPresent()) row.put("group_index", groupIndex.getAsInt()); else row.putNull("group_index");
            if (actualSourceIdentity.isPresent()) row.put("actual_source_identity", actualSourceIdentity.orElseThrow()); else row.putNull("actual_source_identity");
            row.put("actual_selection", "cold_default_5d65b00"); row.put("actual_default_guard_raw_i32", actualDefaultGuard);
            row.put("raw_missing_reason", COLD); row.put("raw_pc_observed", false); row.put("constructor_rva", 0x2560620);
            row.put("normal_return_rva", 0x256070D); row.put("tier_record_rva", 0x5D65B00); row.put("tier_pc_rva", 0x5D65E80);
            row.put("constructor_code_sha256", "4e48abb51e27db4e25421a904df62bc204e963690563076f4074bad5c99ced5f");
            row.put("key_count", 0); row.put("value_count", 0); row.put("normal_return_premise", true);
            row.put("native_initializer_invoked", false); row.put("actual_tls_sync_recheck_or_completion_observed", false); return row;
        }
    }

    /** All dynamic JSON is validated before constructing immutable calculation evidence. */
    public static Optional<Evidence> decode(JsonNode raw) {
        JsonNode leaf = BattlePersonProvinceCodec.normalize(raw, BattlePersonProvinceCodec.FIELD);
        if (nil(leaf)) return Optional.empty();
        List<WalkEvidence> walk = new ArrayList<>();
        for (JsonNode row : leaf.get("title_walk"))
            walk.add(new WalkEvidence(optInt(row.get("tier_raw_i32")), optInt(row.get("children_count_raw")), !nil(row.get("child_ids_u32")),
                    yes(row.get("collected")), optText(row.get("reason"))));
        List<ProvinceEvidence> provinces = new ArrayList<>();
        for (JsonNode province : leaf.get("provinces")) {
            List<SourceEvidence> sources = new ArrayList<>();
            for (JsonNode source : province.get("sources")) {
                JsonNode map = source.get("map"), tiers = source.get("tiers"), pc = tiers.get("pc");
                sources.add(new SourceEvidence(integer(source.get("native_index")).intValueExact(), optInt(source.get("group_index_raw_i32")),
                        optText(source.get("reason")), resolution(source.get("selection")), optText(source.get("object_identity")),
                        optText(source.get("definition_identity")), yes(map.get("ready")), optText(map.get("reason")),
                        yes(tiers.get("ready")), optText(tiers.get("reason")), tier(tiers.get("selection")), optInt(tiers.get("default_guard_raw_i32")),
                        new PcEvidence(optText(pc.get("property_identity")), readBlock(pc.get("property_block")), BattlePersonLateWire.pcReady(pc))));
            }
            JsonNode steps = province.get("steps"); boolean clear = true;
            for (JsonNode step : steps) clear &= nil(step.get("reason"));
            provinces.add(new ProvinceEvidence(integer(province.get("native_index")).intValueExact(), optText(province.get("province_identity")),
                    !steps.isEmpty(), clear, steps.isEmpty() ? OptionalInt.empty() : optInt(steps.get(steps.size() - 1).get("tier_raw_i32")),
                    nil(province.get("admitted")) ? Optional.empty() : Optional.of(province.get("admitted").booleanValue()),
                    optInt(province.get("source_count_raw")), !nil(province.get("source_ids_u32")), sources));
        }
        JsonNode titles = leaf.get("title_source"), manager = leaf.get("manager");
        return Optional.of(new Evidence(integer(leaf.get("character_id")).intValueExact(), optText(leaf.get("character_identity")),
                yes(leaf.get("ready")), optText(leaf.get("reason")), yes(titles.get("ready")), optInt(titles.get("count_raw")),
                walk, provinces, yes(manager.get("ready")), optInt(manager.get("group_count_raw_i32"))));
    }
    public static Evidence fromSection(JsonNode section) {
        require(section != null && section.isObject(), BattlePersonProvinceCodec.FIELD, "source section object required");
        JsonNode raw = section.get(BattlePersonProvinceCodec.FIELD);
        require(raw != null, BattlePersonProvinceCodec.FIELD, "required source leaf absent");
        Evidence result = decode(raw).orElseThrow(() -> bad(BattlePersonProvinceCodec.FIELD, "required source leaf unavailable"));
        BigInteger actor = integer(number(section.get("character_id"), "current_context_source_inputs.character_id", 32, false, false));
        require(actor.intValueExact() == result.characterId(), BattlePersonProvinceCodec.FIELD, "character disagrees with source actor"); return result;
    }
    /** The caller supplies its admitted materialization bound; exceeding it is explicit refusal. */
    public static List<Group> groups(Evidence leaf, boolean projectColdNormalReturn, int maximumGroups) {
        Objects.requireNonNull(leaf);
        require(leaf.managerReady() && leaf.groupCount().isPresent(), BattlePersonProvinceCodec.FIELD, "required actual manager unavailable");
        int count = leaf.groupCount().getAsInt();
        require(maximumGroups >= 0 && count >= 0 && count <= maximumGroups, BattlePersonProvinceCodec.FIELD, "actual manager exceeds admitted group bound");
        List<MutableGroup> groups = new ArrayList<>(); for (int i = 0; i < count; i++) groups.add(new MutableGroup(i));
        boolean complete = leaf.titleSourceReady(); BigInteger expected = complete && leaf.titleCount().isPresent() ? BigInteger.valueOf(leaf.titleCount().getAsInt()) : null;
        for (WalkEvidence visit : leaf.walk()) {
            if (visit.tier().isEmpty() || visit.reason().isPresent()) complete = false;
            else if (visit.tier().getAsInt() > 1) {
                if (visit.childrenCount().isEmpty() || visit.childrenCount().getAsInt() < 0 || !visit.childIdsPresent()) complete = false;
                else if (expected != null) expected = expected.add(BigInteger.valueOf(visit.childrenCount().getAsInt()));
            }
        }
        complete &= expected != null && expected.equals(BigInteger.valueOf(leaf.walk().size()));
        long collected = leaf.walk().stream().filter(WalkEvidence::collected).count(); complete &= leaf.provinces().size() == collected;
        for (ProvinceEvidence province : leaf.provinces()) {
            if (!province.stepsPresent() || !province.stepReasonsClear() || province.lastTier().isEmpty()
                    || province.lastTier().getAsInt() == 2 || province.identity().isEmpty()) { complete = false; continue; }
            if (province.admitted().equals(Optional.of(false))) continue;
            if (!province.admitted().equals(Optional.of(true)) || province.sourceCount().isEmpty()
                    || province.sourceCount().getAsInt() < 0 || !province.sourceIdsPresent()
                    || province.sources().size() != province.sourceCount().getAsInt()) { complete = false; continue; }
            for (SourceEvidence source : province.sources()) {
                if (source.group().isEmpty() || source.group().getAsInt() < 0 || source.group().getAsInt() >= count) { complete = false; continue; }
                MutableGroup group = groups.get(source.group().getAsInt()); boolean projected = projectColdNormalReturn && cold(source);
                if ((source.reason().isPresent() || source.resolution().isEmpty() || source.identity().isEmpty()
                        || source.definitionIdentity().isEmpty() || !source.mapReady() || !source.tiersReady()) && !projected) {
                    group.ready = false; group.reason = first(source.reason(), source.mapReason(), source.tierReason(),
                            Optional.of("following2921350_source_identity_unavailable")); continue;
                }
                Block block = projected ? Block.empty() : source.pc().block().orElseThrow(() -> bad(BattlePersonProvinceCodec.FIELD, "demanded property block unavailable"));
                Occurrence occurrence = new Occurrence(province.nativeIndex(), source.nativeIndex(), source.pc().identity(), projected);
                group.occurrences.add(occurrence);
                if (!block.keysU16().isEmpty()) {
                    var folded = NativePropertyFold2303120.fold(group.block, block, 100000L); group.block = folded.block();
                    for (var update : folded.updates()) group.updates.add(new BoundUpdate(occurrence, update));
                }
            }
        }
        if (!complete) for (MutableGroup group : groups) {
            group.ready = false; group.reason = Optional.of("following2921350_complete_occurrence_stream_unavailable");
        }
        return groups.stream().map(MutableGroup::freeze).toList();
    }
    public static List<WeightedRequest> requests(Evidence leaf, boolean projectColdNormalReturn, int maximumGroups) {
        require(leaf.ready() || projectColdNormalReturn && leaf.reason().equals(Optional.of(COLD)) && leaf.characterIdentity().isPresent(),
                BattlePersonProvinceCodec.FIELD, "required source leaf unavailable");
        List<WeightedRequest> result = new ArrayList<>();
        for (Group group : groups(leaf, projectColdNormalReturn, maximumGroups)) result.addAll(requestsForGroup(leaf, group));
        return List.copyOf(result);
    }
    public static List<WeightedRequest> requestsForGroup(Evidence leaf, Group group) {
        Objects.requireNonNull(leaf); Objects.requireNonNull(group);
        require(group.ready(), BattlePersonProvinceCodec.FIELD, "required group source unavailable");
        if (group.propertyBlock().keysU16().isEmpty()) return List.of();
        String identity = leaf.characterIdentity().orElseThrow(() -> bad(BattlePersonProvinceCodec.FIELD, "actual character identity unavailable"));
        return List.of(new WeightedRequest(0, "following_2921350_group", group.nativeIndex(), 1,
                "following2921350:" + identity + ":group" + group.nativeIndex(), group.propertyBlock(), 100000L));
    }
    public static List<WeightedRequest> requestsForCurrentSection(JsonNode section, boolean projectColdNormalReturn, int maximumGroups) {
        return requests(fromSection(section), projectColdNormalReturn, maximumGroups);
    }
    public static List<WeightedRequest> requestsForCurrentGroup(JsonNode section, int groupIndex, boolean projectColdNormalReturn, int maximumGroups) {
        Evidence leaf = fromSection(section); List<Group> groups = groups(leaf, projectColdNormalReturn, maximumGroups);
        require(groupIndex >= 0 && groupIndex < groups.size(), BattlePersonProvinceCodec.FIELD, "group index outside actual manager dimension");
        return requestsForGroup(leaf, groups.get(groupIndex));
    }
    public static List<ColdProjection> coldNormalReturnProjections(Evidence leaf) {
        List<ColdProjection> result = new ArrayList<>();
        for (ProvinceEvidence province : leaf.provinces()) for (SourceEvidence source : province.sources()) if (cold(source))
            result.add(new ColdProjection(leaf.characterId(), province.nativeIndex(), source.nativeIndex(), source.group(),
                    source.identity(), TierSelection.COLD_DEFAULT_5D65B00, source.defaultGuard().orElseThrow()));
        return List.copyOf(result);
    }
    private static boolean cold(SourceEvidence source) {
        return (source.reason().isEmpty() || source.reason().equals(Optional.of(COLD))) && source.mapReady()
                && source.resolution().isPresent() && source.identity().isPresent() && source.definitionIdentity().isPresent()
                && source.tierSelection().equals(Optional.of(TierSelection.COLD_DEFAULT_5D65B00))
                && source.defaultGuard().isPresent() && (source.defaultGuard().getAsInt() == 0 || source.defaultGuard().getAsInt() == -1)
                && source.tierReason().equals(Optional.of(COLD)) && source.pc().identity().isEmpty() && source.pc().block().isEmpty();
    }
    private static Optional<Block> readBlock(JsonNode raw) {
        if (nil(raw)) return Optional.empty(); BigInteger count = integer(raw.get("keys_count"));
        if (count == null || count.signum() < 0 || !propertiesReady(raw)) return Optional.empty();
        int n = count.intValueExact(); if (n == 0) return Optional.of(Block.empty());
        List<Integer> keys = new ArrayList<>(); List<Long> values = new ArrayList<>();
        for (int i = 0; i < n; i++) { keys.add(integer(raw.get("keys_u16").get(i)).intValueExact()); values.add(integer(raw.get("values_q64").get(i)).longValueExact()); }
        return Optional.of(new Block(keys, values));
    }
    private static Optional<String> optText(JsonNode raw) { return Optional.ofNullable(string(raw)); }
    private static OptionalInt optInt(JsonNode raw) { return nil(raw) ? OptionalInt.empty() : OptionalInt.of(integer(raw).intValueExact()); }
    private static Optional<Resolution> resolution(JsonNode raw) {
        if (nil(raw)) return Optional.empty(); return Optional.of(switch (string(raw)) {
            case "registry_full_id" -> Resolution.REGISTRY_FULL_ID; case "native_fallback" -> Resolution.NATIVE_FALLBACK;
            default -> throw bad(BattlePersonProvinceCodec.FIELD, "unvalidated resolution");
        });
    }
    private static Optional<TierSelection> tier(JsonNode raw) {
        if (nil(raw)) return Optional.empty(); return Optional.of(switch (string(raw)) {
            case "indexed_tier" -> TierSelection.INDEXED_TIER; case "cold_default_5d65b00" -> TierSelection.COLD_DEFAULT_5D65B00;
            case "initialized_default_5d65b00" -> TierSelection.INITIALIZED_DEFAULT_5D65B00;
            default -> throw bad(BattlePersonProvinceCodec.FIELD, "unvalidated tier selection");
        });
    }
    @SafeVarargs private static Optional<String> first(Optional<String>... values) { for (Optional<String> value : values) if (value.isPresent()) return value; return Optional.empty(); }
    private static boolean yes(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static final class MutableGroup {
        final int index; boolean ready = true; Optional<String> reason = Optional.empty(); Block block = Block.empty();
        final List<Occurrence> occurrences = new ArrayList<>(); final List<BoundUpdate> updates = new ArrayList<>();
        MutableGroup(int index) { this.index = index; }
        Group freeze() { return new Group(index, ready, reason, block, occurrences, updates); }
    }
}
