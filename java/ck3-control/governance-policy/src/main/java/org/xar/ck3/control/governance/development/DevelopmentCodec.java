package org.xar.ck3.control.governance.development;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import static org.xar.ck3.control.governance.council.CouncilCodec.*;
import static org.xar.ck3.control.governance.development.DevelopmentModels.*;

/** Exact Python producer profiles; a current native target predicate does not authorize a task action. */
public final class DevelopmentCodec {
    private DevelopmentCodec() { }
    public static final String MATERIAL_STAGE = "native_player_realm_develop_county_material_v1";
    public static final String LEGACY_STAGE = "exact_build_contract_fixture_pending_live_reader";
    private static final Set<String> COMMON = Set.of("schema_version", "contract_stage", "status", "unavailable_reason",
            "snapshot_revision", "observed_date_raw", "player_character_id", "steward_character_id", "task_key", "shown", "valid",
            "task_failure_reason", "candidates", "same_frame_stable", "readiness", "provenance");
    private static final Set<String> MATERIAL_EXTRA = Set.of("current_active_task_binding", "candidate_collection_scope", "candidate_collection_complete");
    private static final Set<String> LEGACY_EXTRA = Set.of("steward_increase_development_value_raw", "current_gold_raw",
            "no_ai_increase_development", "has_active_improve_development_directive", "target_selection_mode");

    public static Observation decode(byte[] bytes, Frame expected) {
        Objects.requireNonNull(expected); ObjectNode value = object(StrictJson.parse(bytes));
        String stage = text(value, "contract_stage");
        boolean material = stage.equals(MATERIAL_STAGE);
        StrictJson.require(material || stage.equals(LEGACY_STAGE), "unknown Develop County producer profile");
        Set<String> fields = new HashSet<>(COMMON); fields.addAll(material ? MATERIAL_EXTRA : LEGACY_EXTRA);
        StrictJson.object(value, fields);
        number(value, "schema_version", 1, 1);
        StrictJson.require(u64(value.get("snapshot_revision"), true).equals(expected.nativeRevision()), "development native revision drift");
        StrictJson.require(text(value, "task_key").equals("task_develop_county"), "fixed Develop County task required");
        Provenance provenance = provenance(value.get("provenance"), material);
        if (material) StrictJson.require(text(value, "candidate_collection_scope").equals("player_realm"), "material collection scope mismatch");
        else StrictJson.require(text(value, "target_selection_mode").equals("engine_random_unscored"), "legacy selection mode mismatch");
        JsonNode rows = value.get("candidates"); StrictJson.require(rows != null && rows.isArray(), "development candidate list required");
        String status = text(value, "status");
        CouncilModels.JsonBody original = new CouncilModels.JsonBody(bytes);
        if (status.equals("unavailable")) {
            String reason = stable(text(value, "unavailable_reason"));
            if (!material) StrictJson.require(Set.of("reader_not_implemented", "unsupported_build", "requires_application_main", "requires_paused", "state_changed").contains(reason), "unknown legacy unavailable reason");
            Optional<Integer> observed = isNull(value.get("observed_date_raw")) ? Optional.empty()
                    : Optional.of((int) number(value, "observed_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE));
            for (String field : List.of("player_character_id", "steward_character_id", "shown", "valid", "task_failure_reason")) nullValue(value.get(field));
            if (material) {
                nullValue(value.get("current_active_task_binding"));
                StrictJson.require(!bool(value.get("candidate_collection_complete")), "unavailable material invented complete collection");
            } else for (String field : List.of("steward_increase_development_value_raw", "current_gold_raw", "no_ai_increase_development", "has_active_improve_development_directive")) nullValue(value.get(field));
            StrictJson.require(rows.isEmpty() && !bool(value.get("same_frame_stable")) && !bool(value.get("readiness")), "unavailable development invented observations");
            return new Unavailable(expected, provenance, material ? Profile.NATIVE_MATERIAL : Profile.LEGACY_AI_FIXTURE, observed, reason, original);
        }
        StrictJson.require(status.equals("available"), "unknown development availability state");
        nullValue(value.get("unavailable_reason"));
        StrictJson.require(number(value, "observed_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == expected.dateRaw(), "development date drift");
        StrictJson.trueValue(value.get("same_frame_stable")); StrictJson.trueValue(value.get("readiness"));
        boolean shown = bool(value.get("shown")), valid = bool(value.get("valid"));
        Optional<String> failure = isNull(value.get("task_failure_reason")) ? Optional.empty() : Optional.of(stable(text(value, "task_failure_reason")));
        if (material) {
            StrictJson.trueValue(value.get("candidate_collection_complete"));
            long owner = unsigned(value, "player_character_id"), steward = unsigned(value, "steward_character_id");
            List<MaterialCandidate> candidates = new ArrayList<>();
            for (JsonNode raw : rows) candidates.add(materialCandidate(raw));
            return new Material(expected, provenance, owner, steward, shown, valid, failure,
                    binding(value.get("current_active_task_binding"), steward), candidates, original);
        }
        List<LegacyCandidate> candidates = new ArrayList<>();
        Set<Integer> titles = new HashSet<>(), provinces = new HashSet<>();
        for (JsonNode raw : rows) {
            LegacyCandidate candidate = legacyCandidate(raw);
            StrictJson.require(titles.add(candidate.countyTitleId()) && provinces.add(candidate.capitalProvinceId()), "duplicate legacy candidate title/province");
            candidates.add(candidate);
        }
        return new Legacy(expected, provenance, positive(value, "player_character_id"), positive(value, "steward_character_id"), shown, valid, failure,
                number(value, "steward_increase_development_value_raw", Long.MIN_VALUE, Long.MAX_VALUE),
                number(value, "current_gold_raw", Long.MIN_VALUE, Long.MAX_VALUE), bool(value.get("no_ai_increase_development")),
                bool(value.get("has_active_improve_development_directive")), candidates, original);
    }
    public static byte[] encode(Observation value) { return Objects.requireNonNull(value).original().bytes(); }
    private static Provenance provenance(JsonNode raw, boolean material) {
        ObjectNode row = StrictJson.object(raw, Set.of("game_version", "executable_sha256", "backend_id", "reader_mode", "next_reverse_engineering_entry"));
        Provenance result = new Provenance(text(row, "game_version"), text(row, "executable_sha256"), text(row, "backend_id"), text(row, "reader_mode"), text(row, "next_reverse_engineering_entry"));
        CouncilCodec.requireBuild(result.gameVersion(), result.executableSha256());
        // Python compares this complete frozen provenance dictionary exactly; its source hashes are uppercase.
        StrictJson.require(result.executableSha256().matches("[0-9A-F]{64}"), "development frozen provenance SHA representation mismatch");
        if (material) {
            StrictJson.require(Set.of("1.20.0.3", "1.20.0.4").contains(result.gameVersion())
                    && result.backendId().equals("ck3-" + result.gameVersion() + "-native-steward-develop-county-material-v1")
                    && result.readerMode().equals("native_player_realm_enumerator_predicates_and_current_growth")
                    && result.nextReverseEngineeringEntry().equals("native_develop_county_ai_inputs_and_proposed_task_growth"), "material exact native reader provenance mismatch");
        } else StrictJson.require(result.gameVersion().equals("1.19.0.6")
                && result.backendId().equals("ck3-1.19.0.6-native-steward-develop-county-candidates-v1")
                && result.readerMode().equals("contract_fixture_pending_live_reader")
                && result.nextReverseEngineeringEntry().equals("task_develop_county_native_candidate_enumerator_and_final_legality_call"), "legacy exact fixture provenance mismatch");
        return result;
    }
    private static MaterialCandidate materialCandidate(JsonNode raw) {
        ObjectNode row = StrictJson.object(raw, Set.of("county_title_id", "capital_province_id", "holder_character_id", "is_player_capital", "directly_held_by_player",
                "native_collection_ordinal", "native_target_valid", "monthly_development_rate", "development_progress"));
        ObjectNode progress = StrictJson.object(row.get("development_progress"), Set.of("current", "maximum"));
        return new MaterialCandidate(unsigned(row, "county_title_id"), positive(row, "capital_province_id"), unsigned(row, "holder_character_id"),
                bool(row.get("is_player_capital")), bool(row.get("directly_held_by_player")), number(row, "native_collection_ordinal", 0, 0xffff_ffffL),
                bool(row.get("native_target_valid")), fixed(row.get("monthly_development_rate")), fixed(progress.get("current")), fixed(progress.get("maximum")));
    }
    private static Binding binding(JsonNode raw, long steward) {
        ObjectNode row = StrictJson.object(raw, Set.of("position_key", "incumbent_character_id", "task_key", "task_type", "target", "frozen", "progress"));
        StrictJson.require(text(row, "position_key").equals("councillor_steward") && unsigned(row, "incumbent_character_id") == steward, "current native Steward binding mismatch");
        Target target = switch (text(row, "task_type")) {
            case "general" -> { nullValue(row.get("target")); yield new General(); }
            case "county" -> {
                ObjectNode value = StrictJson.object(row.get("target"), Set.of("kind", "province_id"));
                StrictJson.require(text(value, "kind").equals("province"), "county target kind mismatch"); yield new County(positive(value, "province_id"));
            }
            case "court" -> {
                ObjectNode value = StrictJson.object(row.get("target"), Set.of("kind", "character_id"));
                StrictJson.require(text(value, "kind").equals("character"), "court target kind mismatch"); yield new Court(unsigned(value, "character_id"));
            }
            default -> throw new IllegalArgumentException("unknown current task type");
        };
        ObjectNode progress = StrictJson.object(row.get("progress"), Set.of("kind", "current", "maximum"));
        ProgressKind kind = switch (text(progress, "kind")) {
            case "infinite" -> ProgressKind.INFINITE; case "percentage" -> ProgressKind.PERCENTAGE; case "value" -> ProgressKind.VALUE;
            default -> throw new IllegalArgumentException("unknown current task progress kind");
        };
        Optional<CouncilModels.Fixed> current = isNull(progress.get("current")) ? Optional.empty() : Optional.of(fixed(progress.get("current")));
        Optional<CouncilModels.Fixed> maximum = isNull(progress.get("maximum")) ? Optional.empty() : Optional.of(fixed(progress.get("maximum")));
        return new Binding(steward, stable(text(row, "task_key")), target, bool(row.get("frozen")), new Progress(kind, current, maximum));
    }
    private static LegacyCandidate legacyCandidate(JsonNode raw) {
        ObjectNode row = StrictJson.object(raw, Set.of("county_title_id", "capital_province_id", "holder_character_id", "is_player_capital", "directly_held_by_player", "native_legal",
                "development_level_raw", "development_progress_raw", "monthly_development_rate_raw", "max_development_level_raw", "terrain_key", "same_culture_as_player", "cultural_acceptance_threshold_passed"));
        StrictJson.trueValue(row.get("native_legal"));
        return new LegacyCandidate(positive(row, "county_title_id"), positive(row, "capital_province_id"), positive(row, "holder_character_id"),
                bool(row.get("is_player_capital")), bool(row.get("directly_held_by_player")), (int) number(row, "development_level_raw", 0, Integer.MAX_VALUE),
                number(row, "development_progress_raw", Long.MIN_VALUE, Long.MAX_VALUE), number(row, "monthly_development_rate_raw", Long.MIN_VALUE, Long.MAX_VALUE),
                (int) number(row, "max_development_level_raw", 0, Integer.MAX_VALUE), stable(text(row, "terrain_key")),
                bool(row.get("same_culture_as_player")), bool(row.get("cultural_acceptance_threshold_passed")));
    }
    private static long unsigned(ObjectNode row, String key) { return number(row, key, 1, 0xffff_ffffL); }
    private static int positive(ObjectNode row, String key) { return (int) number(row, key, 1, Integer.MAX_VALUE); }
}
