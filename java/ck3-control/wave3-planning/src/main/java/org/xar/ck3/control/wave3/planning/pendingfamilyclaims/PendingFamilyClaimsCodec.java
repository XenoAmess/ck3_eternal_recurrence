package org.xar.ck3.control.wave3.planning.pendingfamilyclaims;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave3.planning.pendingfamilyclaims.PendingFamilyClaims.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Strict wire entry for the two actual peacetime collector claim producers. */
public final class PendingFamilyClaimsCodec {
    public static final String SCHEMA = "xar.java.pending-family-claims-request.v1";
    private PendingFamilyClaimsCodec() { }
    public static byte[] project(byte[] raw) {
        Obj request = object(OpportunityJson.parse(raw), "request");
        require(request.members().keySet().equals(Set.of("schema", "operation", "frame", "pending")), "exact request fields");
        require(new Text(SCHEMA).equals(request.get("schema")), "request schema");
        Frame observed = observedFrame(object(request.get("frame"), "frame"));
        ActorEpisode current = new ActorEpisode(observed.playedCharacterId(), observed.episodeRunId());
        Value pending = request.get("pending"); Claims claims;
        switch (text(request.get("operation"), "operation")) {
            case "family" -> claims = family(current, pending == Nil.INSTANCE ? Optional.empty() : Optional.of(familyPending(object(pending, "family pending"))));
            case "child_default" -> claims = childDefault(current, pending == Nil.INSTANCE ? Optional.empty() : Optional.of(childPending(object(pending, "child pending"))));
            default -> throw new IllegalArgumentException("unsupported pending claims operation");
        }
        return OpportunityJson.encode(toJson(claims));
    }
    /** Legacy ledger JSON is validated once before a caller enters the typed claim producer. */
    public static Optional<FamilyPending> decodeFamilyPending(byte[] raw) {
        Value value = OpportunityJson.parse(raw);
        return value == Nil.INSTANCE ? Optional.empty() : Optional.of(familyPending(object(value, "family pending")));
    }
    public static Optional<ChildPending> decodeChildPending(byte[] raw) {
        Value value = OpportunityJson.parse(raw);
        return value == Nil.INSTANCE ? Optional.empty() : Optional.of(childPending(object(value, "child pending")));
    }
    public static Obj toJson(Claims claims) {
        java.util.Objects.requireNonNull(claims);
        return new Obj(Map.of("ally_character_ids", integers(claims.allyCharacterIds()),
                "character_ids", integers(claims.characterIds()), "commitment_keys", new Arr(claims.commitmentKeys().stream().<Value>map(Text::new).toList())));
    }
    private static Frame observedFrame(Obj frame) {
        require(frame.members().keySet().equals(Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id")), "exact observed frame");
        return new Frame(integer(frame.get("played_character_id"), "actor"), integer(frame.get("native_revision"), "native revision"), integer(frame.get("date_raw"), "date"),
                text(frame.get("snapshot_id"), "snapshot"), integer(frame.get("revision"), "revision"), text(frame.get("episode_run_id"), "episode"));
    }
    private static ActorEpisode scope(Obj pending) { return new ActorEpisode(integer(pending.get("played_character_id"), "pending actor"), text(pending.get("episode_run_id"), "pending episode")); }
    private static FamilyPending familyPending(Obj pending) {
        Value attempted = pending.get("preproposal_realm_alliance_attempt_if_accepted");
        AllianceIntent intent = attempted == null ? AllianceIntent.HISTORICAL_CONSERVATIVE
                : bool(attempted, "pending family alliance attempt") ? AllianceIntent.EXPLICIT_ATTEMPT : AllianceIntent.EXPLICIT_NO_ATTEMPT;
        return new FamilyPending(scope(pending), integer(pending.get("heir_character_id"), "heir"), integer(pending.get("candidate_character_id"), "candidate"), integer(pending.get("recipient_character_id"), "recipient"), intent);
    }
    private static ChildPending childPending(Obj pending) {
        Obj projection = object(pending.get("selected_value_projection"), "selected child projection"), costs = object(projection.get("generic_costs"), "child generic costs");
        require(new Text("on_send").equals(costs.get("application_timing")), "child on-send resource projection required");
        List<AlliancePair> pairs = new ArrayList<>();
        for (Value value : array(projection.get("possible_alliance_pairs"), "child alliance pairs")) {
            Obj pair = object(value, "alliance pair");
            pairs.add(new AlliancePair(integer(pair.get("first_character_id"), "first ally"), integer(pair.get("second_character_id"), "second ally"), bool(pair.get("would_attempt_if_accepted"), "alliance attempt")));
        }
        return new ChildPending(scope(pending), integer(pending.get("heir_character_id"), "child subject"), integer(pending.get("candidate_character_id"), "child candidate"), integer(pending.get("recipient_character_id"), "child recipient"), pairs);
    }
    private static Arr integers(List<BigInteger> values) { return new Arr(values.stream().<Value>map(IntegerValue::new).toList()); }
}
