package org.xar.ck3.control.application.action.ordinary;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure one-send lineage. An ACK, query, reconnect or timeout never releases an earlier claim. */
public final class OrdinaryOnceClaims {
    public static final String SCHEMA = "xar.ck3.ordinary-once-claim-domain/v1";
    public static final int MAX_BYTES = 1 << 20;
    private OrdinaryOnceClaims() { }
    public record Identity(String machineId, long gamePid, String creationFiletimeDecimal,
            long actorId, String interactionKey, long recipientId) {
        public Identity {
            need(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{2,127}"), "explicit machine identity");
            need(gamePid > 0 && gamePid <= 0xffff_ffffL, "native PID"); decimal(creationFiletimeDecimal, true);
            NativeCharacterId.of(actorId); character(recipientId); key(interactionKey);
        }
        public String stableActionId() { return "ordinary-" + ActionCodec.sha256(StrictJson.canonical(identity(this))); }
    }
    /** Identity/time values retain a decimal-string JSON representation; the native protocol remains separate. */
    public record Binding(String snapshotId, String publicRevisionDecimal, String nativeRevisionDecimal,
            String dateRawDecimal, String connectionGenerationDecimal, String episodeRunId) {
        public Binding {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            decimal(publicRevisionDecimal, true); decimal(nativeRevisionDecimal, true);
            decimal(dateRawDecimal, false); decimal(connectionGenerationDecimal, true);
        }
    }
    public record Request(Identity identity, Binding binding, String requestId) {
        public Request { Objects.requireNonNull(identity); Objects.requireNonNull(binding); requestId = id(requestId); }
    }
    /** This is original evidence, not a boolean authorization. Root must re-run its pinned independent verifier. */
    public record Permit(ExactRef authorization, ExactRef registry, ExactRef verifierBundle, ExactRef consumptionManifest,
            ExactRef parentClaim, String previousRequestId, String nextIntentId) {
        public Permit {
            for (ExactRef ref : List.of(authorization, registry, verifierBundle, consumptionManifest, parentClaim))
                need(ref.bytes() > 0, "nonempty original permit and verifier evidence");
            previousRequestId = id(previousRequestId);
            need(nextIntentId != null && nextIntentId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,95}"), "portable Root next-intent identity");
        }
    }
    public record Lineage(Permit permit, String consumedByRequestId) {
        public Lineage { Objects.requireNonNull(permit); consumedByRequestId = id(consumedByRequestId); }
    }
    public record Claim(Request request, long ordinal, Optional<Lineage> lineage) {
        public Claim {
            Objects.requireNonNull(request); need(ordinal >= 0 && ordinal <= 0xffff_ffffL, "claim ordinal");
            lineage = Objects.requireNonNull(lineage);
            need((ordinal == 0) == lineage.isEmpty(), "first claim has no fabricated parent");
            lineage.ifPresent(value -> need(value.consumedByRequestId().equals(request.requestId()), "claim consumption request binding"));
        }
    }
    public record RetainedClaim(Claim claim, ExactRef original) {
        public RetainedClaim {
            Objects.requireNonNull(claim); Objects.requireNonNull(original); byte[] raw = encodeClaim(claim);
            need(original.bytes() == raw.length && original.sha256().equals(ActionCodec.sha256(raw)), "claim body content binding");
        }
    }
    public record Consumption(Request request, Permit permit) {
        public Consumption { Objects.requireNonNull(request); Objects.requireNonNull(permit); }
    }
    /** Legacy rounded/missing process birth remains an unresolved blocker, never a fabricated exact FILETIME. */
    public record LegacyBlocker(String machineId, long gamePid, long actorId, String interactionKey, long recipientId,
            ExactRef originalClaim, String reason) {
        public LegacyBlocker {
            StrictJson.text(machineId); need(gamePid > 0 && gamePid <= 0xffff_ffffL, "legacy PID"); NativeCharacterId.of(actorId); character(recipientId); key(interactionKey);
            Objects.requireNonNull(originalClaim); need(originalClaim.bytes() > 0, "original unresolved legacy claim"); StrictJson.text(reason);
        }
        public boolean blocks(Identity identity) {
            return machineId.equals(identity.machineId()) && gamePid == identity.gamePid() && actorId == identity.actorId()
                    && interactionKey.equals(identity.interactionKey()) && recipientId == identity.recipientId();
        }
    }
    public record State(String machineId, List<RetainedClaim> claims, List<Consumption> consumptions, List<LegacyBlocker> legacyBlockers) {
        public State {
            StrictJson.text(machineId); claims = List.copyOf(claims); consumptions = List.copyOf(consumptions); legacyBlockers = List.copyOf(legacyBlockers);
            need(claims.size() <= 4096 && consumptions.size() <= 4096 && legacyBlockers.size() <= 4096, "finite complete claim domain");
            legacyBlockers.forEach(row -> need(row.machineId().equals(machineId), "legacy claim machine"));
            Set<String> requests = new java.util.HashSet<>(), permits = new java.util.HashSet<>();
            for (RetainedClaim claim : claims) {
                need(claim.claim().request().identity().machineId().equals(machineId), "claim machine");
                need(requests.add(claim.claim().request().requestId()), "duplicate original claim request");
            }
            for (Consumption consumed : consumptions) {
                need(consumed.request().identity().machineId().equals(machineId), "consumption machine");
                need(permits.add(consumed.permit().authorization().sha256()), "a permit is permanently single-use");
            }
            List<Identity> identities = claims.stream().map(row -> row.claim().request().identity()).distinct().toList();
            for (Identity identity : identities) {
                List<RetainedClaim> chain = claims.stream().filter(row -> row.claim().request().identity().equals(identity)).toList();
                for (int index = 0; index < chain.size(); index++) {
                    Claim current = chain.get(index).claim(); need(current.ordinal() == index, "incomplete ordinary claim lineage");
                    if (index > 0) {
                        Lineage lineage = current.lineage().orElseThrow(); RetainedClaim previous = chain.get(index - 1);
                        need(lineage.permit().parentClaim().equals(previous.original())
                                && lineage.permit().previousRequestId().equals(previous.claim().request().requestId()), "ordinary claim parent identity");
                        need(consumptions.contains(new Consumption(current.request(), lineage.permit())), "claim lacks prior durable permit consumption");
                    }
                }
            }
        }
        public Optional<RetainedClaim> latest(Identity identity) {
            List<RetainedClaim> rows = claims.stream().filter(row -> row.claim().request().identity().equals(identity)).toList();
            return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getLast());
        }
    }
    /** Invoke only after Root independently verifies the original event/save round evidence. Commit before creating the next claim. */
    public static State consume(State before, Request request, Permit permit) {
        need(before.machineId().equals(request.identity().machineId()), "current claim machine");
        RetainedClaim previous = before.latest(request.identity()).orElseThrow(() -> new IllegalArgumentException("no parent ordinary claim"));
        need(permit.parentClaim().equals(previous.original())
                && permit.previousRequestId().equals(previous.claim().request().requestId())
                && !request.requestId().equals(permit.previousRequestId()), "permit must bind the latest pair and a new request");
        need(before.consumptions().stream().noneMatch(row -> row.permit().authorization().equals(permit.authorization())
                || row.permit().nextIntentId().equals(permit.nextIntentId()) || row.request().requestId().equals(request.requestId())),
                "consumed permit/intent/request cannot be restored after a crash");
        List<Consumption> consumed = new ArrayList<>(before.consumptions()); consumed.add(new Consumption(request, permit));
        return new State(before.machineId(), before.claims(), consumed, before.legacyBlockers());
    }
    public static Claim prepareClaim(State before, Request request) {
        need(before.machineId().equals(request.identity().machineId()), "claim machine differs");
        need(before.legacyBlockers().stream().noneMatch(row -> row.blocks(request.identity())), "original legacy claim process provenance is unresolved; no retry");
        need(before.claims().stream().noneMatch(row -> samePair(row.claim().request().identity(), request.identity())
                && !row.claim().request().identity().creationFiletimeDecimal().equals(request.identity().creationFiletimeDecimal())),
                "ordinary process provenance changed; unresolved evidence cannot be bypassed");
        need(before.claims().stream().noneMatch(row -> row.claim().request().requestId().equals(request.requestId())), "original request already claimed; no replay");
        Optional<RetainedClaim> previous = before.latest(request.identity());
        if (previous.isEmpty()) {
            need(before.consumptions().stream().noneMatch(row -> row.request().requestId().equals(request.requestId())), "first claim cannot use a parent permit");
            return new Claim(request, 0, Optional.empty());
        }
        List<Consumption> matches = before.consumptions().stream().filter(row -> row.request().equals(request)).toList();
        need(matches.size() == 1, "ordinary pair already claimed; independent consumed next-intent permit required");
        Permit permit = matches.getFirst().permit();
        need(permit.parentClaim().equals(previous.orElseThrow().original())
                && permit.previousRequestId().equals(previous.orElseThrow().claim().request().requestId()), "pair changed after permit consumption");
        return new Claim(request, Math.addExact(previous.orElseThrow().claim().ordinal(), 1), Optional.of(new Lineage(permit, request.requestId())));
    }
    public static State append(State before, RetainedClaim next) {
        need(prepareClaim(before, next.claim().request()).equals(next.claim()), "claim differs from complete pure reducer");
        List<RetainedClaim> claims = new ArrayList<>(before.claims()); claims.add(next);
        return new State(before.machineId(), claims, before.consumptions(), before.legacyBlockers());
    }
    public static byte[] encode(State state) {
        ObjectNode n = StrictJson.object().put("schema", SCHEMA).put("machine_id", state.machineId());
        var claims = n.putArray("claims"); for (RetainedClaim row : state.claims()) {
            ObjectNode entry = claims.addObject(); entry.set("claim", claim(row.claim())); entry.set("original", row.original().toJson());
        }
        var consumed = n.putArray("consumptions"); for (Consumption row : state.consumptions()) {
            ObjectNode entry = consumed.addObject(); entry.set("request", request(row.request())); entry.set("permit", permit(row.permit()));
        }
        var legacy = n.putArray("legacy_blockers"); for (LegacyBlocker row : state.legacyBlockers()) {
            ObjectNode entry = legacy.addObject().put("machine_id", row.machineId()).put("game_pid", row.gamePid()).put("actor_id", row.actorId())
                    .put("interaction_key", row.interactionKey()).put("recipient_id", row.recipientId()).put("reason", row.reason()); entry.set("original_claim", row.originalClaim().toJson());
        }
        return StrictJson.canonical(n, MAX_BYTES);
    }
    public static State decode(byte[] raw) {
        ObjectNode n = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "machine_id", "claims", "consumptions", "legacy_blockers"));
        need(SCHEMA.equals(StrictJson.text(n.get("schema"))), "ordinary claim domain schema");
        List<RetainedClaim> claims = new ArrayList<>(); JsonNode claimRows = n.get("claims"), consumedRows = n.get("consumptions");
        need(claimRows.isArray() && consumedRows.isArray(), "missing/null/array ordinary domain distinction");
        for (JsonNode value : claimRows) {
            ObjectNode row = StrictJson.object(value, Set.of("claim", "original"));
            claims.add(new RetainedClaim(readClaim(row.get("claim")), ExactRef.fromJson(row.get("original"))));
        }
        List<Consumption> consumed = new ArrayList<>(); for (JsonNode value : consumedRows) {
            ObjectNode row = StrictJson.object(value, Set.of("request", "permit")); consumed.add(new Consumption(readRequest(row.get("request")), readPermit(row.get("permit"))));
        }
        JsonNode blockedRows = n.get("legacy_blockers"); need(blockedRows.isArray(), "legacy blockers remain an explicit array");
        List<LegacyBlocker> blocked = new ArrayList<>(); for (JsonNode value : blockedRows) {
            ObjectNode row = StrictJson.object(value, Set.of("machine_id", "game_pid", "actor_id", "interaction_key", "recipient_id", "reason", "original_claim"));
            blocked.add(new LegacyBlocker(StrictJson.text(row.get("machine_id")), StrictJson.integer(row.get("game_pid"), 1, 0xffff_ffffL),
                    NativeCharacterId.fromJson(row.get("actor_id")).value(), StrictJson.text(row.get("interaction_key")), StrictJson.integer(row.get("recipient_id"), 1, 0xffff_fffeL),
                    ExactRef.fromJson(row.get("original_claim")), StrictJson.text(row.get("reason"))));
        }
        return new State(StrictJson.text(n.get("machine_id")), claims, consumed, blocked);
    }
    public static byte[] encodeClaim(Claim value) { return StrictJson.canonical(claim(value), MAX_BYTES); }
    public static ObjectNode request(Request value) {
        ObjectNode n = StrictJson.object(); n.set("identity", identity(value.identity())); n.set("binding", binding(value.binding())); return n.put("request_id", value.requestId());
    }
    public static Request readRequest(JsonNode value) {
        ObjectNode n = StrictJson.object(value, Set.of("identity", "binding", "request_id"));
        return new Request(readIdentity(n.get("identity")), readBinding(n.get("binding")), StrictJson.text(n.get("request_id")));
    }
    public static ObjectNode permit(Permit value) {
        ObjectNode n = StrictJson.object(); n.set("authorization", value.authorization().toJson()); n.set("registry", value.registry().toJson());
        n.set("verifier_bundle", value.verifierBundle().toJson()); n.set("consumption_manifest", value.consumptionManifest().toJson());
        n.set("parent_claim", value.parentClaim().toJson()); return n.put("previous_request_id", value.previousRequestId()).put("next_intent_id", value.nextIntentId());
    }
    public static Permit readPermit(JsonNode value) {
        ObjectNode n = StrictJson.object(value, Set.of("authorization", "registry", "verifier_bundle", "consumption_manifest", "parent_claim", "previous_request_id", "next_intent_id"));
        return new Permit(ExactRef.fromJson(n.get("authorization")), ExactRef.fromJson(n.get("registry")), ExactRef.fromJson(n.get("verifier_bundle")),
                ExactRef.fromJson(n.get("consumption_manifest")), ExactRef.fromJson(n.get("parent_claim")), StrictJson.text(n.get("previous_request_id")), StrictJson.text(n.get("next_intent_id")));
    }
    private static ObjectNode claim(Claim value) {
        ObjectNode n = request(value.request()).put("ordinal", value.ordinal()).put("status", "claimed_result_unknown_no_retry");
        if (value.lineage().isEmpty()) n.putNull("new_intent_lineage"); else {
            Lineage lineage = value.lineage().orElseThrow(); ObjectNode row = n.putObject("new_intent_lineage"); row.set("permit", permit(lineage.permit())); row.put("consumed_by_request_id", lineage.consumedByRequestId());
        }
        return n;
    }
    private static Claim readClaim(JsonNode value) {
        ObjectNode n = StrictJson.object(value, Set.of("identity", "binding", "request_id", "ordinal", "status", "new_intent_lineage"));
        need("claimed_result_unknown_no_retry".equals(StrictJson.text(n.get("status"))), "ACK cannot release claim status");
        Optional<Lineage> lineage = Optional.empty(); if (!n.get("new_intent_lineage").isNull()) {
            ObjectNode row = StrictJson.object(n.get("new_intent_lineage"), Set.of("permit", "consumed_by_request_id"));
            lineage = Optional.of(new Lineage(readPermit(row.get("permit")), StrictJson.text(row.get("consumed_by_request_id"))));
        }
        return new Claim(new Request(readIdentity(n.get("identity")), readBinding(n.get("binding")), StrictJson.text(n.get("request_id"))), StrictJson.integer(n.get("ordinal"), 0, 0xffff_ffffL), lineage);
    }
    private static ObjectNode identity(Identity value) {
        return StrictJson.object().put("machine_id", value.machineId()).put("game_pid", value.gamePid()).put("creation_filetime_decimal", value.creationFiletimeDecimal())
                .put("actor_id", value.actorId()).put("interaction_key", value.interactionKey()).put("recipient_id", value.recipientId());
    }
    private static Identity readIdentity(JsonNode value) {
        ObjectNode n = StrictJson.object(value, Set.of("machine_id", "game_pid", "creation_filetime_decimal", "actor_id", "interaction_key", "recipient_id"));
        return new Identity(StrictJson.text(n.get("machine_id")), StrictJson.integer(n.get("game_pid"), 1, 0xffff_ffffL), StrictJson.text(n.get("creation_filetime_decimal")),
                NativeCharacterId.fromJson(n.get("actor_id")).value(), StrictJson.text(n.get("interaction_key")), StrictJson.integer(n.get("recipient_id"), 1, 0xffff_fffeL));
    }
    private static ObjectNode binding(Binding value) {
        return StrictJson.object().put("snapshot_id", value.snapshotId()).put("public_revision_decimal", value.publicRevisionDecimal()).put("native_revision_decimal", value.nativeRevisionDecimal())
                .put("date_raw_decimal", value.dateRawDecimal()).put("connection_generation_decimal", value.connectionGenerationDecimal()).put("episode_run_id", value.episodeRunId());
    }
    private static Binding readBinding(JsonNode value) {
        ObjectNode n = StrictJson.object(value, Set.of("snapshot_id", "public_revision_decimal", "native_revision_decimal", "date_raw_decimal", "connection_generation_decimal", "episode_run_id"));
        return new Binding(StrictJson.text(n.get("snapshot_id")), StrictJson.text(n.get("public_revision_decimal")), StrictJson.text(n.get("native_revision_decimal")),
                StrictJson.text(n.get("date_raw_decimal")), StrictJson.text(n.get("connection_generation_decimal")), StrictJson.text(n.get("episode_run_id")));
    }
    private static void character(long value) { need(value > 0 && value <= 0xffff_fffeL, "full generation-bearing Character ID"); }
    private static boolean samePair(Identity left, Identity right) {
        return left.machineId().equals(right.machineId()) && left.gamePid() == right.gamePid() && left.actorId() == right.actorId()
                && left.interactionKey().equals(right.interactionKey()) && left.recipientId() == right.recipientId();
    }
    private static void key(String value) { need(value != null && value.matches("[A-Za-z0-9_]{1,128}"), "original ASCII interaction key"); }
    private static String id(String value) { need(value != null && value.matches("[A-Za-z0-9_.:-]{1,128}"), "bounded exact request/intent ID"); return value; }
    private static void decimal(String value, boolean positive) {
        need(value != null && value.matches("0|[1-9][0-9]{0,19}"), "canonical decimal uint64 string");
        BigInteger integer = new BigInteger(value); need(integer.compareTo(StrictJson.UINT64_MAX) <= 0 && (!positive || integer.signum() > 0), "uint64 identity/time range");
    }
    private static void need(boolean value, String message) { StrictJson.require(value, message); }
}
