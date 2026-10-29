package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original proposal cooldown/CB fence and declaration latch; this code never submits or marks an ACK Applied. */
public final class OrdinaryWarAdmissionRules {
    private OrdinaryWarAdmissionRules() { }
    public static final BigInteger COOLDOWN_RAW = BigInteger.valueOf(30L * 24L);
    public enum Declaration { CLEAR, ORIGINAL_UNRESOLVED }
    public record DeclarationBefore(List<Integer> fullWarIds, int actorCharacterId, int bridgePid, BigInteger connectionGeneration) {
        public DeclarationBefore { fullWarIds = List.copyOf(fullWarIds); Objects.requireNonNull(connectionGeneration); }
    }
    /** The original prepare gate's complete before-war inventory and physical owner; this is DATA, never a submit permit. */
    public static DeclarationBefore declarationBefore(Obj actualSnapshot) {
        Value raw = actualSnapshot.get("active_wars");
        StrictJson.require(raw instanceof Arr wars && wars.items().size() <= 256, "bounded actual before-war inventory required");
        List<Integer> ids = new java.util.ArrayList<>();
        for (Value value : ((Arr) raw).items()) {
            BigInteger id = OpportunityJson.integer(OpportunityJson.object(value, "actual before-war row").get("war_id"), "full before-war ID");
            StrictJson.require(id.signum() >= 0 && id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "actual before-war ID is outside original scope");
            ids.add(id.intValueExact());
        }
        StrictJson.require(ids.stream().distinct().count() == ids.size(), "actual before-war inventory contains duplicate full IDs");
        var player = OpportunityJson.object(actualSnapshot.get("played_character"), "actual declaration player");
        var diagnostic = OpportunityJson.object(actualSnapshot.get("diagnostics"), "actual declaration diagnostics");
        var hello = OpportunityJson.object(diagnostic.get("hello"), "actual declaration hello");
        int actor = positiveI32(player.get("character_id")), pid = positiveI32(diagnostic.get("bridge_pid"));
        StrictJson.require(pid == positiveI32(hello.get("pid")), "actual declaration bridge and hello PID differ");
        BigInteger generation = OpportunityJson.integer(diagnostic.get("connection_generation"), "actual native connection generation");
        StrictJson.require(generation.signum() > 0, "actual declaration connection generation is unavailable");
        return new DeclarationBefore(ids, actor, pid, generation);
    }
    public static Optional<Obj> whitePeaceFence(Arr history, int warId, Value episode, OrdinaryWhitePeacePolicy.Variant variant) {
        if (variant != OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE) return Optional.empty();
        for (int i = history.items().size() - 1; i >= 0; i--) {
            Obj action = action(history.items().get(i), warId, episode); if (action == null) continue;
            Obj cb = object(action.get("casus_belli"));
            if (cb != null && text(cb.get("canonical_key"), "individual_county_de_jure_cb") && integer(cb.get("database_index")).filter(v -> v.equals(BigInteger.valueOf(17))).isPresent())
                return Optional.of(action);
        }
        return Optional.empty();
    }
    public static Optional<Obj> whitePeaceCooldown(Arr history, int warId, Value dateRaw, Value episode) {
        Optional<BigInteger> current = integer(dateRaw);
        if (current.isEmpty()) return Optional.of(new Obj(java.util.Map.of("status", new Text("invalid_current_date"))));
        for (int i = history.items().size() - 1; i >= 0; i--) {
            Obj row = OpportunityJson.object(history.items().get(i), "original history row"); Obj action = action(row, warId, episode); if (action == null) continue;
            Optional<BigInteger> submitted = integer(action.get("submitted_date_raw"));
            if (submitted.isEmpty()) return Optional.of(new Obj(java.util.Map.of("status", new Text("malformed_submission_history"))));
            BigInteger elapsed = current.orElseThrow().subtract(submitted.orElseThrow());
            if (elapsed.compareTo(COOLDOWN_RAW) < 0) {
                java.util.Map<String,Value> fields = new java.util.LinkedHashMap<>(); fields.put("status", new Text("cooldown"));
                fields.put("submitted_date_raw", new IntegerValue(submitted.orElseThrow())); fields.put("elapsed_raw", new IntegerValue(elapsed));
                fields.put("remaining_raw", new IntegerValue(COOLDOWN_RAW.subtract(elapsed))); fields.put("history_index", row.get("index") == null ? Nil.INSTANCE : row.get("index"));
                return Optional.of(new Obj(fields));
            }
            return Optional.empty();
        }
        return Optional.empty();
    }
    public static Declaration declaration(Obj actualSnapshot, List<ActionReceipt> canonical) {
        Value raw = actualSnapshot.get("war_declaration_continuity_v1");
        if (raw != null && raw != Nil.INSTANCE) {
            Obj state = OpportunityJson.object(raw, "original declaration continuity");
            StrictJson.require(text(state.get("schema"), "war-declaration-continuity-v1"), "unknown declaration continuity schema cannot grant a new submit");
            String status = OpportunityJson.text(state.get("status"), "original declaration state");
            if (!List.of("war_started", "native_rejected", "not_submitted").contains(status)) return Declaration.ORIGINAL_UNRESOLVED;
        }
        Obj player = OpportunityJson.object(actualSnapshot.get("played_character"), "actual player"); Value episode = actualSnapshot.get("episode_run_id");
        StrictJson.require(episode == Nil.INSTANCE || episode instanceof Text, "actual declaration episode must preserve explicit null or text");
        OpportunityJson.integer(player.get("character_id"), "actual player identity");
        for (ActionReceipt receipt : List.copyOf(canonical)) {
            if (!(receipt.command().origin() instanceof CommandOrigin.Gameplay) || receipt.settled() || !receipt.command().operation().value().startsWith("declare-war-")) continue;
            var before = receipt.command().before();
            boolean sameEpisode = episode == Nil.INSTANCE ? before.frame().episodeRunId() == null
                    : episode instanceof Text text && Objects.equals(before.frame().episodeRunId(), text.value());
            if (sameEpisode && ActionTransitions.attempt(receipt.state()).isPresent())
                return Declaration.ORIGINAL_UNRESOLVED;
        }
        return Declaration.CLEAR;
    }
    private static Obj action(Value value, int war, Value episode) { return action(OpportunityJson.object(value, "original history row"), war, episode); }
    private static Obj action(Obj row, int war, Value episode) {
        if (!text(row.get("command"), "offer-white-peace-" + war) || !truth(row.get("ok"))) return null;
        Obj result = object(row.get("result")), action = result == null ? null : object(result.get("war_termination_result"));
        if (action == null || !integer(action.get("war_id")).filter(id -> id.equals(BigInteger.valueOf(war))).isPresent()
                || !text(action.get("outcome"), "white_peace") || !Objects.equals(action.get("episode_run_id"), episode)
                || !(text(action.get("status"), "submitted_pending") || text(action.get("status"), "applied"))) return null;
        return action;
    }
    private static Obj object(Value value) { return value == null || value == Nil.INSTANCE ? null : OpportunityJson.object(value, "original admission object"); }
    private static boolean text(Value value, String expected) { return value instanceof Text text && text.value().equals(expected); }
    private static boolean truth(Value value) { return value instanceof Bool bool && bool.value(); }
    private static Optional<BigInteger> integer(Value value) { return value instanceof IntegerValue integer ? Optional.of(integer.value()) : Optional.empty(); }
    private static int positiveI32(Value value) {
        BigInteger id = OpportunityJson.integer(value, "positive actual declaration owner identity");
        StrictJson.require(id.signum() > 0 && id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "actual declaration owner identity is outside original scope");
        return id.intValueExact();
    }
}
