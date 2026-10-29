package org.xar.ck3.control.wave2.military.exitresult;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.wave2.military.exitresult.ExitMaterialContracts.absent;
import static org.xar.ck3.control.wave2.military.exitresult.ExitMaterialContracts.actualTrue;
import static org.xar.ck3.control.wave2.military.exitresult.ExitMaterialContracts.integer;
import static org.xar.ck3.control.wave2.military.exitresult.ExitMaterialContracts.integer64;
import static org.xar.ck3.control.wave2.military.exitresult.ExitMaterialContracts.object;
import static org.xar.ck3.control.wave2.military.exitresult.ExitMaterialContracts.sameInteger;
import static org.xar.ck3.control.wave2.military.exitresult.ExitMaterialContracts.textEquals;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Action;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Availability;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Bound;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.ClaimRow;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Claims;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.ClaimsNotObserved;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.ClaimsUnavailable;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.FixedValue;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Frame;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.NativeClaims;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.NativeTitles;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.NativeTruce;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.PlayerSide;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Receipt;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.RequestedOutcome;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Resource;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.ResourceObservation;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TitleRow;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Titles;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TitlesNotObserved;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TitlesUnavailable;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Truce;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TruceNotObserved;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TruceStatus;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TruceUnavailable;

/** Complete actual composer closure. Query or action transports are never executed by this class. */
public final class OrdinaryWarExitObservationCodec {
    private static final Set<String> INPUT_FIELDS = Set.of("before_snapshot", "post_snapshot", "action_result",
            "claims_result", "title_holder_results", "truce_result");
    /** Different original contracts: native observers admit the actual enforce safe-integer ID domain,
     * while the old generic Driver compositor returns null outside positive signed int32 for every route. */
    public enum ActionProfile { NATIVE_OBSERVATION, ORIGINAL_DRIVER }
    private OrdinaryWarExitObservationCodec() { }

    /** Explicit adapter envelope; nullable observations are required keys rather than aliases. */
    public static Receipt decodeAndCompose(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES), INPUT_FIELDS);
        return composeProjection(input.get("before_snapshot"), input.get("post_snapshot"), input.get("action_result"),
                input.get("claims_result"), input.get("title_holder_results"), input.get("truce_result"), ActionProfile.NATIVE_OBSERVATION);
    }
    public static byte[] evaluate(byte[] raw) { return encode(decodeAndCompose(raw)); }

    /** One original outcome-specific literal grammar, shared with the live/cold observer. No ACK or action permission. */
    public static Action actionForLiteral(String literal) {
        Action action = parseAction(StrictJson.object().put("step", literal).put("accepted", false));
        require(action != null, "canonical outcome-specific original public war literal required");
        return action;
    }

    /** Same pure composer for already decoded, source-bound complete frames. This creates no read/Root
     * authority and serializes neither input frame; the caller retains its actual bounded Driver inputs. */
    public static Receipt compose(JsonNode beforeSnapshot, JsonNode postSnapshot, JsonNode actionResult,
                                  JsonNode claimsResult, JsonNode titleHolderResults, JsonNode truceResult) {
        return compose(ActionProfile.NATIVE_OBSERVATION, beforeSnapshot, postSnapshot, actionResult, claimsResult, titleHolderResults, truceResult);
    }

    /** Pure material projection of one original native truce result. The caller still proves its
     * receipt, source and original pending after-frame; these added frame fields grant no authority.
     * The retained Native token is never changed and the SDK envelope contract remains separate. */
    public static Receipt composeNativeTruce(JsonNode beforeSnapshot, JsonNode postSnapshot,
                                             JsonNode actionResult, JsonNode originalNativeTruce) {
        Frame post = frame(postSnapshot);
        ObjectNode material = StrictJson.object(originalNativeTruce, Set.of("step", "accepted", "query_sequence",
                "snapshot_revision", "date_raw", "backend_id", "read_only", "raiktor_actual_truce_expiry")).deepCopy();
        require(sameInteger(material.get("snapshot_revision"), post.nativeRevision())
                && sameInteger(material.get("date_raw"), post.dateRaw()),
                "original native truce envelope differs from its source-bound post frame");
        material.put("queried_snapshot_id", post.snapshotId());
        material.put("queried_revision", post.revision());
        material.put("queried_native_revision", post.nativeRevision());
        return compose(beforeSnapshot, postSnapshot, actionResult, null, null, material);
    }

    /** Complete original generic Driver result uses its own original eligibility, without changing
     * the native observer or broadening any preparation/read permission. */
    public static Receipt compose(ActionProfile profile, JsonNode beforeSnapshot, JsonNode postSnapshot,
                                  JsonNode actionResult, JsonNode claimsResult, JsonNode titleHolderResults, JsonNode truceResult) {
        require(profile != null, "explicit original action profile required");
        return composeProjection(beforeSnapshot, postSnapshot, actionResult, claimsResult, titleHolderResults, truceResult, profile);
    }

    private static Receipt composeProjection(JsonNode beforeSnapshot, JsonNode postSnapshot, JsonNode actionResult,
                                             JsonNode claimsResult, JsonNode titleHolderResults, JsonNode truceResult, ActionProfile profile) {
        Action action = parseAction(actionResult, profile);
        if (action == null) { return null; }
        List<String> issues = new ArrayList<>();
        List<ResourceObservation> resources = new ArrayList<>();
        Claims claims = new ClaimsNotObserved();
        Titles titles = new TitlesNotObserved();
        Truce truce = new TruceNotObserved();
        Bound bound;
        try {
            Frame before = frame(beforeSnapshot);
            Frame post = frame(postSnapshot);
            require(before.episodeRunId().equals(post.episodeRunId()) && before.actorCharacterId() == post.actorCharacterId()
                    && before.bridgePid() == post.bridgePid() && before.connectionGeneration() == post.connectionGeneration()
                    && post.dateRaw() >= before.dateRaw() && post.revision().compareTo(before.revision()) >= 0
                    && post.nativeRevision().compareTo(before.nativeRevision()) >= 0, "post frame crossed action identity");
            List<JsonNode> matching = wars(beforeSnapshot).stream()
                    .filter(row -> row.get("war_id").longValue() == action.warId()).toList();
            require(matching.size() == 1 && (textEquals(matching.get(0).get("player_side"), "attacker")
                    || textEquals(matching.get(0).get("player_side"), "defender")), "pre-action full WarID/side unavailable");
            JsonNode war = matching.get(0);
            PlayerSide side = textEquals(war.get("player_side"), "attacker") ? PlayerSide.ATTACKER : PlayerSide.DEFENDER;
            int opponent = integer(war.get("primary_opponent_character_id"), 0);
            JsonNode rawTitles = war.get("targeted_title_ids");
            List<Integer> ids = rawTitles != null && rawTitles.isArray() && rawTitles.isEmpty()
                    ? List.of() : ExitMaterialContracts.titleIds(rawTitles);
            List<Integer> rendered = ids.subList(0, Math.min(ids.size(), OrdinaryWarExitObservation.MAXIMUM_OBSERVED_TITLES));
            boolean warAbsent = wars(postSnapshot).stream().noneMatch(row -> row.get("war_id").longValue() == action.warId());
            bound = new Bound(before, post, warAbsent, side, opponent, rendered, ids.size());
        } catch (ContractViolationException unavailableIdentity) {
            issues.add(unavailableIdentity.getMessage());
            return new Receipt(action, null, resources, claims, titles, truce, issues);
        }
        if (!bound.warAbsent()) { return new Receipt(action, bound, resources, claims, titles, truce, issues); }
        for (Resource resource : Resource.values()) {
            resources.add(new ResourceObservation(resource, fixed(beforeSnapshot.get("played_character_" + resource.wire())),
                    fixed(postSnapshot.get("played_character_" + resource.wire())), bound.before().dateRaw() == bound.post().dateRaw()));
        }
        if (!absent(claimsResult)) {
            try { claims = ExitMaterialContracts.claims(claimsResult, bound.post(), bound.renderedTitleIds()); }
            catch (ContractViolationException unavailableClaims) {
                claims = new ClaimsUnavailable();
                issues.add("claims: " + unavailableClaims.getMessage());
            }
        }
        if (!absent(titleHolderResults)) {
            try {
                require(titleHolderResults.isArray() && titleHolderResults.size() <= bound.renderedTitleIds().size(),
                        "bounded title result list unavailable");
                List<TitleRow> rows = new ArrayList<>();
                Set<Integer> seen = new HashSet<>();
                for (JsonNode result : titleHolderResults) {
                    rows.add(ExitMaterialContracts.title(result, bound.post(), bound.renderedTitleIds(), seen));
                }
                titles = new NativeTitles(rows, bound.targetTitleCount());
            } catch (ContractViolationException unavailableTitles) {
                titles = new TitlesUnavailable();
                issues.add("titles: " + unavailableTitles.getMessage());
            }
        }
        if (!absent(truceResult)) {
            try { truce = ExitMaterialContracts.truce(truceResult, bound.post(), bound.opponentCharacterId()); }
            catch (ContractViolationException unavailableTruce) {
                truce = new TruceUnavailable();
                issues.add("truce: " + unavailableTruce.getMessage());
            }
        }
        return new Receipt(action, bound, resources, claims, titles, truce, issues);
    }

    private static Action parseAction(JsonNode value) { return parseAction(value, ActionProfile.NATIVE_OBSERVATION); }
    private static Action parseAction(JsonNode value, ActionProfile profile) {
        if (value == null || !value.isObject() || value.get("step") == null || !value.get("step").isTextual()) { return null; }
        String step = value.get("step").textValue();
        String[] prefixes = {"enforce-demands-", "offer-white-peace-", "surrender-war-"};
        RequestedOutcome[] outcomes = {RequestedOutcome.PLAYER_VICTORY, RequestedOutcome.WHITE_PEACE, RequestedOutcome.PLAYER_DEFEAT};
        for (int index = 0; index < prefixes.length; index++) {
            if (step.startsWith(prefixes[index])) {
                String suffix = step.substring(prefixes[index].length());
                boolean nativeEnforce = index == 0 && profile == ActionProfile.NATIVE_OBSERVATION;
                if (!suffix.matches(nativeEnforce ? "0|[1-9][0-9]*" : "[1-9][0-9]{0,9}")) { return null; }
                BigInteger warId = new BigInteger(suffix);
                BigInteger maximum = nativeEnforce ? BigInteger.valueOf(9007199254740991L) : BigInteger.valueOf(Integer.MAX_VALUE);
                if (warId.compareTo(maximum) > 0) { return null; }
                return new Action(warId.longValueExact(), outcomes[index], actualTrue(value.get("accepted")));
            }
        }
        return null;
    }

    private static Frame frame(JsonNode value) {
        object(value, "snapshot unavailable");
        JsonNode played = value.get("played_character");
        JsonNode diagnostics = value.get("diagnostics");
        require(actualTrue(value.get("paused")) && actualTrue(value.get("map_ready")) && played != null && played.isObject()
                && actualTrue(played.get("alive")) && diagnostics != null && diagnostics.isObject(), "living paused map frame unavailable");
        JsonNode hello = diagnostics.get("hello");
        require(hello != null && hello.isObject(), "native build provenance unavailable");
        JsonNode version = hello.has("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version");
        JsonNode sha = hello.has("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256");
        require(textEquals(version, "1.20.0.4") && ExitMaterialContracts.currentSha(sha), "current4 build provenance unavailable");
        require(value.get("snapshot_id") != null && value.get("snapshot_id").isTextual() && !value.get("snapshot_id").textValue().isEmpty()
                && value.get("episode_run_id") != null && value.get("episode_run_id").isTextual() && !value.get("episode_run_id").textValue().isEmpty(),
                "snapshot/episode identity unavailable");
        return new Frame(value.get("snapshot_id").textValue(), integer64(value.get("revision"), true),
                integer64(value.get("native_revision"), true), integer(value.get("date_raw"), Integer.MIN_VALUE),
                value.get("episode_run_id").textValue(), integer(played.get("character_id"), 0),
                integer(diagnostics.get("bridge_pid"), 1), integer(diagnostics.get("connection_generation"), 1));
    }
    private static List<JsonNode> wars(JsonNode snapshot) {
        JsonNode rows = snapshot.get("active_wars");
        require(rows != null && rows.isArray(), "active-war observation unavailable");
        List<JsonNode> output = new ArrayList<>();
        Set<Long> ids = new HashSet<>();
        for (JsonNode row : rows) { require(row.isObject(), "active-war observation unavailable"); }
        for (JsonNode row : rows) {
            long id = StrictJson.integer(row.get("war_id"), 0, 9007199254740991L);
            require(ids.add(id), "active-war observation duplicated");
            output.add(row);
        }
        return output;
    }
    private static FixedValue fixed(JsonNode value) {
        if (value == null || !value.isObject() || value.get("raw") == null || !value.get("raw").isIntegralNumber()
                || value.get("raw").bigIntegerValue().compareTo(BigInteger.valueOf(Long.MIN_VALUE)) < 0
                || value.get("raw").bigIntegerValue().compareTo(BigInteger.valueOf(Long.MAX_VALUE)) > 0
                || !sameInteger(value.get("scale"), 100_000)) { return null; }
        return new FixedValue(value.get("raw").bigIntegerValue());
    }

    public static byte[] encode(Receipt receipt) {
        if (receipt == null) { return StrictJson.canonical(NullNode.instance); }
        ObjectNode result = StrictJson.object();
        result.put("schema", OrdinaryWarExitObservation.SCHEMA);
        Bound bound = receipt.bound();
        result.put("status", bound == null ? "unbound" : bound.warAbsent() ? "war_absent" : "war_present");
        result.put("war_id", receipt.action().warId());
        result.put("requested_outcome", receipt.action().requestedOutcome().wire());
        if (bound == null) { result.putNull("requested_native_outcome"); result.putNull("war_absence_observed"); }
        else {
            result.put("requested_native_outcome", bound.nativeOutcome(receipt.action().requestedOutcome()).wire());
            result.put("war_absence_observed", bound.warAbsent());
        }
        result.put("command_acknowledged", receipt.action().acknowledged());
        result.putNull("observed_result_identity");
        result.put("result_identity_reason", "no_independent_result_observer");
        result.set("before_frame", bound == null ? NullNode.instance : frameNode(bound.before()));
        result.set("post_frame", bound == null ? NullNode.instance : frameNode(bound.post()));
        if (bound != null) {
            result.put("player_side", bound.side().wire());
            result.put("opponent_character_id", bound.opponentCharacterId());
            ArrayNode targets = result.putArray("target_title_ids");
            bound.renderedTitleIds().forEach(targets::add);
            result.put("target_title_count", bound.targetTitleCount());
            result.put("target_titles_omitted", bound.targetTitleCount() - bound.renderedTitleIds().size());
        }
        ObjectNode resources = result.putObject("resources");
        for (ResourceObservation value : receipt.resources()) {
            ObjectNode row = resources.putObject(value.resource().wire());
            row.put("status", value.before() != null && value.after() != null ? "observed" : "unavailable");
            row.set("before", fixedNode(value.before())); row.set("after", fixedNode(value.after()));
            if (value.deltaRaw() == null) { row.putNull("delta_raw"); } else { row.put("delta_raw", value.deltaRaw()); }
            row.put("same_date", value.sameDate()); row.put("action_attribution", "unproven");
        }
        ObjectNode claims = result.putObject("claims");
        if (receipt.claims() instanceof NativeClaims nativeClaims) {
            claims.put("status", nativeClaims.availability().wire());
            if (nativeClaims.rows() == null) { claims.putNull("rows"); }
            else {
                ArrayNode rows = claims.putArray("rows");
                for (ClaimRow claim : nativeClaims.rows()) {
                    ObjectNode row = rows.addObject();
                    row.put("title_id", claim.titleId()); row.put("present", claim.present()); row.put("state", claim.state().wire());
                    if (claim.strong() == null) { row.putNull("strong"); } else { row.put("strong", claim.strong()); }
                    if (claim.implicit() == null) { row.putNull("implicit"); } else { row.put("implicit", claim.implicit()); }
                }
            }
            claims.put("query_sequence", nativeClaims.querySequence());
            putNullable(claims, "unavailable_reason", nativeClaims.unavailableReason());
        } else { claims.put("status", receipt.claims() instanceof ClaimsUnavailable ? "unavailable" : "not_observed"); claims.putNull("rows"); }
        ObjectNode titles = result.putObject("titles");
        ArrayNode titleRows = titles.putArray("rows");
        if (receipt.titles() instanceof NativeTitles nativeTitles) {
            titles.put("status", nativeTitles.rows().isEmpty() ? "not_observed" : "observed");
            for (TitleRow title : nativeTitles.rows()) {
                ObjectNode row = titleRows.addObject();
                row.put("title_id", title.titleId()); row.put("status", title.availability().wire());
                putNullable(row, "holder_character_id", title.holderCharacterId());
                putNullable(row, "holder_immediate_liege_character_id", title.immediateLiegeCharacterId());
                putNullable(row, "holder_top_liege_character_id", title.topLiegeCharacterId());
                if (title.holderInPlayerRealm() == null) { row.putNull("holder_in_player_realm"); }
                else { row.put("holder_in_player_realm", title.holderInPlayerRealm()); }
                putNullable(row, "unavailable_reason", title.unavailableReason());
            }
            titles.put("observed_target_count", nativeTitles.rows().size());
            titles.put("all_frozen_targets_observed", nativeTitles.allFrozenTargetsObserved());
        } else { titles.put("status", receipt.titles() instanceof TitlesUnavailable ? "unavailable" : "not_observed"); }
        ObjectNode truce = result.putObject("truce");
        if (receipt.truce() instanceof NativeTruce nativeTruce) {
            truce.put("status", nativeTruce.status().wire());
            truce.put("owner_character_id", nativeTruce.ownerCharacterId()); truce.put("toward_character_id", nativeTruce.towardCharacterId());
            truce.put("native_has_truce", nativeTruce.status() == TruceStatus.AVAILABLE);
            putNullable(truce, "expiry_date_raw", nativeTruce.expiryDateRaw());
            truce.put("temporal_semantics", "post_application_persisted_relation_state");
            putNullable(truce, "unavailable_reason", nativeTruce.unavailableReason());
            truce.put("direction", "player_toward_opponent"); truce.put("query_sequence", nativeTruce.querySequence());
        } else { truce.put("status", receipt.truce() instanceof TruceUnavailable ? "unavailable" : "not_observed"); truce.putNull("expiry_date_raw"); }
        ArrayNode issues = result.putArray("issues"); receipt.issues().forEach(issues::add);
        return StrictJson.canonical(result);
    }
    private static ObjectNode frameNode(Frame value) {
        ObjectNode row = StrictJson.object();
        row.put("snapshot_id", value.snapshotId()); row.put("revision", value.revision()); row.put("native_revision", value.nativeRevision());
        row.put("date_raw", value.dateRaw()); row.put("episode_run_id", value.episodeRunId()); row.put("actor_character_id", value.actorCharacterId());
        row.put("bridge_pid", value.bridgePid()); row.put("connection_generation", value.connectionGeneration());
        return row;
    }
    private static JsonNode fixedNode(FixedValue value) {
        if (value == null) { return NullNode.instance; }
        ObjectNode row = StrictJson.object(); row.put("raw", value.raw()); row.put("scale", 100_000); return row;
    }
    private static void putNullable(ObjectNode row, String field, String value) {
        if (value == null) { row.putNull(field); } else { row.put(field, value); }
    }
    private static void putNullable(ObjectNode row, String field, Integer value) {
        if (value == null) { row.putNull(field); } else { row.put(field, value); }
    }
}

