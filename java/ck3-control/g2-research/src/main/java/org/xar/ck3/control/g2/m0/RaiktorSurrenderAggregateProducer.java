package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.warpolicy.NativeRaiktorAggregate;
import org.xar.ck3.control.warpolicy.NativeRaiktorTruce;
import org.xar.ck3.control.warpolicy.NativeRaiktorWarBound;
import org.xar.ck3.control.warpolicy.NativeTerminationTerms;

/** Original pure aggregate and session-binding producers; unavailable native domains remain unavailable. */
public final class RaiktorSurrenderAggregateProducer {
    private static final List<String> SNAPSHOT = List.of("snapshot_id", "revision", "native_revision", "date_raw", "paused",
            "episode_run_id", "episode_character_id");
    private static final List<String> RECEIPT = List.of("queried_snapshot_id", "queried_revision", "queried_native_revision",
            "queried_connection_generation", "episode_run_id");
    private static final List<String> DIAGNOSTIC = List.of("connection_generation", "bridge_pid");
    private static final List<String> READINESS = List.of("snapshot_binding_ready", "query_receipt_binding_ready",
            "same_frame_revision_ready", "episode_owner_ready", "process_binding_ready", "aggregate_session_binding_ready");
    private RaiktorSurrenderAggregateProducer() { }

    public static ObjectNode validateAggregate(JsonNode raw) {
        ObjectNode aggregate = object(raw, "aggregate");
        return NativeRaiktorAggregate.normalize(aggregate, NativeRaiktorAggregate.frame(aggregate.get("frame")));
    }
    public static ObjectNode validateAggregate(JsonNode raw, RaiktorExitObservationCodec.ExpectedBinding expected) {
        ObjectNode aggregate = validateAggregate(raw); var frame = NativeRaiktorAggregate.frame(aggregate.get("frame"));
        require(frame.snapshotRevision().equals(expected.snapshotRevision()) && frame.nativeRevision().equals(expected.nativeRevision())
                && BigInteger.valueOf(frame.dateRaw()).equals(expected.dateRaw()) && BigInteger.valueOf(frame.warId()).equals(expected.warId())
                && BigInteger.valueOf(frame.attacker()).equals(expected.episodeCharacterId()), "aggregate crossed the bound paused session");
        return aggregate;
    }

    /** Attach only the pure projection derived from the actual query result and its actual receipt fields. */
    public static ObjectNode attachSession(JsonNode snapshot, JsonNode termsQuery, JsonNode passiveTruceEvidence) {
        ObjectNode query = object(termsQuery, "terms query").deepCopy();
        ObjectNode rawTerms = object(query.get("war_termination_terms"), "native terms");
        int warId = positive32(rawTerms.get("war_id"), "war_id");
        ObjectNode terms = NativeTerminationTerms.normalize(rawTerms, warId);
        Optional<ObjectNode> aggregate = project(snapshot, terms, passiveTruceEvidence, terms.get("generic_war_bound_current"));
        query.set("raiktor_surrender_aggregate_session", bind(snapshot, query, aggregate.orElse(null)));
        return query;
    }

    public static Optional<ObjectNode> project(JsonNode snapshotValue, JsonNode termsValue,
            JsonNode passiveTruceEvidence, JsonNode genericWarBoundValue) {
        if (!(snapshotValue instanceof ObjectNode snapshot) || !(termsValue instanceof ObjectNode terms)
                || !"available".equals(terms.path("status").asText())
                || !NativeTerminationTerms.RAIKTOR.equals(terms.path("supported_slice").asText())) return Optional.empty();
        try {
            int warId = positive32(terms.get("war_id"), "war_id");
            NativeTerminationTerms.normalize(terms, warId);
            ObjectNode binding = RaiktorWhitePeaceProjectionProducer.snapshotBinding(snapshot, warId);
            ObjectNode selected = null;
            for (JsonNode value : array(snapshot.get("active_wars"), "active wars")) {
                if (value instanceof ObjectNode war && same(war.get("war_id"), terms.get("war_id"))) {
                    if (selected != null) return Optional.empty(); selected = war;
                }
            }
            require(selected != null, "selected active war unavailable");
            int attacker = positive32(snapshot.get("episode_character_id"), "attacker");
            int defender = positive32(selected.get("primary_opponent_character_id"), "defender");
            int claimant = positive32(terms.get("claimant_character_id"), "claimant");
            ObjectNode cb = object(terms.get("casus_belli"), "CB"); require(text(cb.get("canonical_key"), "CB key").equals("raiktor_claim_cb"), "wrong CB");
            var frame = new NativeRaiktorAggregate.Frame(positiveU64(snapshot.get("revision")), positiveU64(snapshot.get("native_revision")),
                    i32(snapshot.get("date_raw"), "date_raw"), warId, Math.toIntExact(number(cb.get("database_index"), 0, Integer.MAX_VALUE, "CB index")),
                    attacker, defender, claimant);
            ObjectNode claims = StrictJson.object();
            for (String key : List.of("target_title_ids", "claims", "attacker_defeat")) claims.set(key, terms.get(key).deepCopy());
            claims.put("target_order_stable", true); claims.put("claim_rows_stable", true);
            ObjectNode domains = StrictJson.object();
            ObjectNode gold = copyPayload(terms.get("gold_reparations"), "actual_amount_observable",
                    List.of("attacker_current_gold", "defender_current_gold", "attacker_authoritative_monthly_gold_income",
                            "defender_authoritative_monthly_gold_income", "actual_transfer"));
            if (gold != null) gold.put("exact_primary_transfer_observed", true);
            ObjectNode prestige = copyPayload(terms.get("attacker_fame"), "actual_delta_observable",
                    List.of("attacker_current_prestige", "cb_prestige_factor", "attacker_prestige_delta"));
            if (prestige != null) prestige.put("exact_factor_and_attacker_delta_observed", true);
            ObjectNode prisoners = copyPayload(terms.get("prisoner_release"), "actual_pairs_observable",
                    List.of("attacker_participant_ids", "defender_participant_ids", "attacker_release_candidate_ids",
                            "defender_release_candidate_ids", "release_pairs", "full_participant_scan", "primary_and_first_three_successors_scanned"));
            ObjectNode favor = copyPayload(terms.get("conditional_favor_hook"), "actual_applies_observable",
                    List.of("claimant_distinct_from_attacker", "original_visible_root_traversed", "will_apply"));
            ObjectNode truce = passiveTruce(passiveTruceEvidence, binding, frame).orElse(null);
            ObjectNode generic = null;
            if (genericWarBoundValue instanceof ObjectNode rawGeneric) {
                try {
                    ObjectNode active = object(rawGeneric.get("active_frame"), "generic active frame");
                    require(integer(active.get("active_casus_belli_database_index"), "generic CB").equals(BigInteger.valueOf(frame.casusBelliIndex())),
                            "generic CB differs");
                    generic = NativeRaiktorWarBound.normalize(rawGeneric, warId, attacker, defender,
                            frame.snapshotRevision(), frame.nativeRevision(), frame.dateRaw());
                } catch (IllegalArgumentException invalid) { generic = null; }
            }
            List<ObjectNode> payloads = java.util.Arrays.asList(gold, prestige, prisoners, favor, truce, generic);
            List<String> missing = new ArrayList<>(); ObjectNode readiness = StrictJson.object(); readiness.put("claims_base_ready", true);
            for (int index = 1; index < NativeRaiktorAggregate.ORDER.size(); index++) {
                String name = NativeRaiktorAggregate.ORDER.get(index); ObjectNode payload = payloads.get(index - 1);
                domains.set(name, wrap(frame, payload)); readiness.put(name + "_ready", payload != null); if (payload == null) missing.add(name);
            }
            boolean complete = missing.isEmpty(); readiness.put("postwar_cleanup_ready", generic != null && isTrue(generic.path("cleanup").get("observable")));
            for (String key : List.of("source_specific_war_bound_ready", "pre_soldiers_ready", "proven_soldier_loss_ready", "automatic_surrender_ready"))
                readiness.put(key, false);
            readiness.put("six_dynamic_domains_ready", complete); readiness.put("same_frame_stable", complete); readiness.put("action_terms_ready", complete);
            ObjectNode result = StrictJson.object(); result.put("schema_version", 1); result.put("backend_id", NativeRaiktorAggregate.BACKEND);
            result.put("status", complete ? "complete" : "incomplete"); result.putNull("failure"); result.set("frame", frame.toJson());
            result.set("claims_base", wrap(frame, claims)); result.set("domains", domains); strings(result, "missing_domains", missing); result.set("readiness", readiness);
            return Optional.of(NativeRaiktorAggregate.normalize(result, frame));
        } catch (IllegalArgumentException invalid) { return Optional.empty(); }
    }

    /** Boundary failures remain the original typed unavailable receipt, not an exception or an invented identity. */
    public static ObjectNode bind(JsonNode snapshotValue, JsonNode queryReceiptValue, JsonNode aggregateValue) {
        ObjectNode snapshot = snapshotValue instanceof ObjectNode row ? row : StrictJson.object();
        ObjectNode receipt = queryReceiptValue instanceof ObjectNode row ? row : StrictJson.object();
        ObjectNode diagnostics = snapshot.get("diagnostics") instanceof ObjectNode row ? row : StrictJson.object();
        ObjectNode observed = StrictJson.object(); for (String field : SNAPSHOT) observed.set("snapshot." + field, snapshot.get(field));
        for (String field : RECEIPT) observed.set("receipt." + field, receipt.get(field));
        for (String field : DIAGNOSTIC) observed.set("diagnostics." + field, diagnostics.get(field));
        List<String> missing = new ArrayList<>(); observed.fields().forEachRemaining(entry -> { if (entry.getValue().isNull()) missing.add(entry.getKey()); });
        if (!missing.isEmpty()) return unavailable("missing_binding_fields", missing, observed);
        List<String> invalid = new ArrayList<>();
        for (String key : List.of("snapshot.snapshot_id", "snapshot.episode_run_id", "receipt.queried_snapshot_id", "receipt.episode_run_id")) {
            JsonNode raw = observed.get(key); if (!raw.isTextual() || raw.textValue().strip().isEmpty()) invalid.add(key);
        }
        for (String key : List.of("snapshot.revision", "snapshot.native_revision", "snapshot.episode_character_id", "receipt.queried_revision",
                "receipt.queried_native_revision", "receipt.queried_connection_generation", "diagnostics.connection_generation", "diagnostics.bridge_pid")) {
            JsonNode raw = observed.get(key); if (!raw.isIntegralNumber() || raw.bigIntegerValue().signum() <= 0) invalid.add(key);
        }
        if (!observed.get("snapshot.date_raw").isIntegralNumber()) invalid.add("snapshot.date_raw");
        if (!isTrue(observed.get("snapshot.paused"))) invalid.add("snapshot.paused");
        if (!invalid.isEmpty()) return unavailable("invalid_binding_fields", invalid, observed);
        List<String> drift = new ArrayList<>();
        for (String[] pair : new String[][] {{"snapshot.snapshot_id", "receipt.queried_snapshot_id"}, {"snapshot.revision", "receipt.queried_revision"},
                {"snapshot.native_revision", "receipt.queried_native_revision"}, {"diagnostics.connection_generation", "receipt.queried_connection_generation"},
                {"snapshot.episode_run_id", "receipt.episode_run_id"}}) if (!same(observed.get(pair[0]), observed.get(pair[1]))) {
                    drift.add(pair[0]); drift.add(pair[1]);
                }
        if (!drift.isEmpty()) return unavailable("session_binding_mismatch", drift, observed);
        if (!(aggregateValue instanceof ObjectNode aggregate) || !(aggregate.get("frame") instanceof ObjectNode frame))
            return unavailable("aggregate_frame_unavailable", List.of("aggregate.frame"), observed);
        for (String[] pair : new String[][] {{"snapshot.revision", "snapshot_revision"}, {"snapshot.native_revision", "native_revision"},
                {"snapshot.date_raw", "date_raw"}, {"snapshot.paused", "paused"}, {"snapshot.episode_character_id", "primary_attacker_character_id"}}) {
            if (!same(observed.get(pair[0]), frame.get(pair[1]))) drift.add("aggregate.frame." + pair[1]);
        }
        if (!drift.isEmpty()) return unavailable("aggregate_frame_mismatch", drift, observed);
        ObjectNode normalized;
        try { normalized = validateAggregate(aggregate); }
        catch (IllegalArgumentException failure) { return unavailable("aggregate_contract_unavailable", List.of("aggregate"), observed); }
        ObjectNode binding = StrictJson.object(); binding.set("snapshot_id", observed.get("snapshot.snapshot_id"));
        binding.set("snapshot_revision", observed.get("snapshot.revision")); binding.set("native_revision", observed.get("snapshot.native_revision"));
        binding.set("date_raw", observed.get("snapshot.date_raw")); binding.set("connection_generation", observed.get("diagnostics.connection_generation"));
        binding.set("episode_run_id", observed.get("snapshot.episode_run_id")); binding.set("episode_character_id", observed.get("snapshot.episode_character_id"));
        binding.set("process_id", observed.get("diagnostics.bridge_pid")); binding.set("war_id", frame.get("war_id"));
        ObjectNode result = StrictJson.object(); result.put("schema_version", 1); result.put("backend_id", RaiktorExitObservationCodec.SESSION_BACKEND);
        result.put("status", "available"); result.putNull("failure"); result.set("binding", binding); result.set("aggregate", normalized);
        ObjectNode ready = result.putObject("readiness"); for (String key : READINESS) ready.put(key, true); return result;
    }
    private static ObjectNode unavailable(String code, List<String> fields, ObjectNode observed) {
        ObjectNode result = StrictJson.object(); result.put("schema_version", 1); result.put("backend_id", RaiktorExitObservationCodec.SESSION_BACKEND);
        result.put("status", "unavailable"); ObjectNode failure = result.putObject("failure"); failure.put("code", code);
        strings(failure, "fields", List.copyOf(new TreeSet<>(fields))); result.putNull("binding"); result.putNull("aggregate");
        result.set("observed_binding", observed.deepCopy()); ObjectNode ready = result.putObject("readiness"); for (String key : READINESS) ready.put(key, false);
        return result;
    }
    private static ObjectNode wrap(NativeRaiktorAggregate.Frame frame, ObjectNode payload) {
        ObjectNode row = StrictJson.object(); row.put("available", payload != null);
        if (payload != null) { row.set("frame", frame.toJson()); row.set("payload", payload); } return row;
    }
    private static ObjectNode copyPayload(JsonNode raw, String readiness, List<String> keys) {
        if (!(raw instanceof ObjectNode value) || !isTrue(value.get(readiness))) return null;
        ObjectNode result = StrictJson.object(); for (String key : keys) result.set(key, copy(value.get(key)));
        result.put("same_frame_stable", true); return result;
    }
    private static boolean isTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static BigInteger positiveU64(JsonNode value) {
        BigInteger integer = integer(value, "revision"); require(integer.signum() > 0 && integer.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 required"); return integer;
    }

    private static Optional<ObjectNode> passiveTruce(JsonNode raw, ObjectNode binding, NativeRaiktorAggregate.Frame frame) {
        if (!(raw instanceof ObjectNode value)) return Optional.empty();
        try {
            ObjectNode evidence = object(value.get("input_evidence"), "passive input evidence");
            ObjectNode proofs = object(value.get("proofs"), "passive proofs"); ObjectNode observer = object(value.get("observer"), "passive observer");
            ObjectNode evaluated = object(value.get("evaluated_days"), "evaluated days"); ObjectNode session = object(value.get("session_identity"), "passive session");
            ObjectNode readiness = object(value.get("readiness"), "passive readiness"); ObjectNode boundaries = object(value.get("boundaries"), "passive boundaries");
            require(text(value.get("contract"), "passive contract").equals("g2-truce-native-callsite-observer-live-postprocess-v1")
                    && text(value.get("status"), "passive status").equals("GREEN")
                    && text(value.get("classification"), "passive classification").equals("two_site_return_observed"), "passive observer not GREEN");
            require(text(evidence.get("runner_report_sha256"), "runner report SHA").matches("[0-9a-fA-F]{64}")
                    && text(evidence.get("manifest_sha256"), "manifest SHA").equals("469ACAC772AFBA730FD4C669ADE3CFB2728AC0F81B796C9BEF88B5C093B64FDD")
                    && text(evidence.get("expected_manifest_sha256"), "expected manifest SHA").equals("469ACAC772AFBA730FD4C669ADE3CFB2728AC0F81B796C9BEF88B5C093B64FDD")
                    && text(evidence.get("source_commit"), "source commit").equals("36fafd811b29bba11758d1ebc3929be8cbd4c9d4")
                    && text(evidence.get("source_zip_sha256"), "source ZIP SHA").equals("F3F3E81EFFE0D832A280A81AF96FC2FB267BE6D9A134AB3A0F35F3BA95841E17"),
                    "passive source evidence differs");
            for (String key : List.of("manifest", "runner_policy", "session_identity")) require(isTrue(proofs.path(key).get("ok")), "passive proof unavailable");
            require(isTrue(proofs.get("samples_bounded")) && array(proofs.get("sample_errors"), "sample errors").isEmpty()
                    && array(proofs.get("counter_regressions"), "counter regressions").isEmpty() && isTrue(proofs.get("stable_two_final_samples")),
                    "passive samples not stable");
            require(!bool(readiness.get("promoted"), "promoted") && !bool(readiness.get("public_readiness_changed"), "readiness changed"),
                    "passive readiness promotion forbidden");
            for (String key : List.of("direct_evaluator_invoked_by_postprocessor", "context_effect_executed", "mutation_executed"))
                require(!bool(boundaries.get(key), key), "passive observer mutation forbidden");
            int days = Math.toIntExact(number(evaluated.get("site_0"), 0, Integer.MAX_VALUE, "evaluated days"));
            require(isTrue(evaluated.get("observable")) && text(evaluated.get("source"), "evaluated source").equals("native return EAX")
                    && integer(evaluated.get("site_1"), "second days").equals(BigInteger.valueOf(days)), "passive returns differ");
            var rows = array(observer.get("final_callsites"), "final callsites"); require(rows.size() == 2, "two passive returns required");
            int[] addresses = {0x2EDAF0F, 0x2EDB59E};
            for (int index = 0; index < 2; index++) {
                ObjectNode row = object(rows.get(index), "callsite");
                require(integer(row.get("call_instruction_rva"), "call RVA").equals(BigInteger.valueOf(addresses[index]))
                        && integer(row.get("post_call_count"), "post call count").signum() > 0
                        && integer(row.get("last_return_eax"), "return EAX").equals(BigInteger.valueOf(days)), "passive callsite differs");
            }
            ObjectNode expected = binding.deepCopy(); expected.remove("war_id"); require(same(session, expected), "passive session identity differs");
            ObjectNode result = StrictJson.object(); result.put("schema_version", 1); result.put("backend_id", NativeRaiktorTruce.BACKEND);
            result.put("status", "available"); result.putNull("failure");
            for (String key : List.of("snapshot_revision", "native_revision", "date_raw", "paused", "war_id", "active_casus_belli_database_index",
                    "active_casus_belli_key")) result.set(key, frame.toJson().get(key));
            result.put("owner_character_id", frame.attacker()); result.put("toward_character_id", frame.defender()); result.put("evaluated_days", days);
            result.put("pointer_shape_verified", true); result.put("evaluator_double_read_stable", true); result.put("same_frame_stable", true);
            result.put("expiry_observable", false); result.putNull("expiry_date_raw"); return Optional.of(NativeRaiktorTruce.normalize(result, frame));
        } catch (IllegalArgumentException failure) { return Optional.empty(); }
    }
}
