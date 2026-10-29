package org.xar.ck3.control.application.action.ordinary;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure reducer/serialization regressions. These tests confer no Root permit, storage or Native authority. */
final class OrdinaryOnceClaimsTest {
    @TempDir Path temporary;
    private Identity identity(String birth) { return new Identity("fixture-machine", 121, birth, -294967295L, "educate_child_interaction", 4_000_000_002L); }
    private Request request(String id, String generation) { return new Request(identity("134999999999999999"), new Binding("native:42", "54", "42", "831000", generation, "episode-1066"), id); }
    private State empty() { return new State("fixture-machine", List.of(), List.of(), List.of()); }
    private ExactRef ref(String name, byte[] raw) { return new ExactRef(temporary.resolve(name).toString(), raw.length, ActionCodec.sha256(raw)); }
    private RetainedClaim retained(Claim claim) { return new RetainedClaim(claim, ref("claim-" + claim.ordinal() + ".json", encodeClaim(claim))); }
    private State first() { return append(empty(), retained(prepareClaim(empty(), request("request-first", "1")))); }
    private Permit permit(State state, String next) {
        RetainedClaim old = state.claims().getLast(); byte[] proof = ("fixture Root proof: " + next).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        return new Permit(ref("permit-" + next, proof), ref("registry", new byte[] {1}), ref("bundle", new byte[] {2}),
                ref("manifest", new byte[] {3}), old.original(), old.claim().request().requestId(), next);
    }
    @Test void actualIdentityRoundtripPreservesFullIdsAndFiletimeBeyondJavascriptPrecision() {
        State state = first(); assertEquals(state, decode(encode(state)));
        String wire = new String(encode(state), java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(wire.contains("\"creation_filetime_decimal\":\"134999999999999999\""));
        assertTrue(wire.contains("-294967295")); assertEquals(identity("134999999999999999").stableActionId(), state.claims().getFirst().claim().request().identity().stableActionId());
    }
    @Test void newRequestConnectionOrQueryCannotTurnAnUnresolvedPairIntoANewRound() {
        State state = first();
        assertThrows(IllegalArgumentException.class, () -> prepareClaim(state, request("request-first", "1")));
        assertThrows(IllegalArgumentException.class, () -> prepareClaim(state, request("request-after-ack", "1")));
        assertThrows(IllegalArgumentException.class, () -> prepareClaim(state, request("request-after-reconnect", "2")));
        assertThrows(IllegalArgumentException.class, () -> prepareClaim(state, new Request(identity("134999999999999998"), request("fresh", "2").binding(), "new-process-same-pid")));
    }
    @Test void independentPermitConsumptionIsDurableBeforeTheNextClaimAndRemainsSingleUse() {
        State before = first(); Request request = request("request-next", "2"); Permit permit = permit(before, "independent-round-2");
        State consumed = consume(before, request, permit);
        assertEquals(1, consumed.claims().size()); assertEquals(1, consumed.consumptions().size());
        assertEquals(consumed, decode(encode(consumed)), "consumed-but-not-published crash state survives persistence");
        assertThrows(IllegalArgumentException.class, () -> consume(consumed, request, permit));
        Claim next = prepareClaim(consumed, request); assertEquals(1, next.ordinal());
        State after = append(consumed, retained(next)); assertEquals(after, decode(encode(after)));
        assertThrows(IllegalArgumentException.class, () -> prepareClaim(after, request("third-without-proof", "3")));
    }
    @Test void wrongParentRequestAndClaimContentCannotCrossTheClaimBoundary() {
        State before = first(); Permit original = permit(before, "new-round");
        Permit wrong = new Permit(original.authorization(), original.registry(), original.verifierBundle(), original.consumptionManifest(),
                original.parentClaim(), "different-request", original.nextIntentId());
        assertThrows(IllegalArgumentException.class, () -> consume(before, request("next", "2"), wrong));
        Claim claim = prepareClaim(empty(), request("first", "1"));
        assertThrows(IllegalArgumentException.class, () -> new RetainedClaim(claim, ref("wrong", new byte[] {9})));
    }
    @Test void unresolvedLegacyRoundedBirthSurvivesWithoutInventingAnExactIdentity() {
        Request request = request("fresh", "3"); Identity pair = request.identity();
        State blocked = new State("fixture-machine", List.of(), List.of(), List.of(new LegacyBlocker(pair.machineId(), pair.gamePid(), pair.actorId(),
                pair.interactionKey(), pair.recipientId(), ref("legacy-rounded.claim.json", new byte[] {7}), "legacy process birth lacks an exact native proof")));
        assertEquals(blocked, decode(encode(blocked)));
        assertThrows(IllegalArgumentException.class, () -> prepareClaim(blocked, request));
    }
    @Test void decoderRejectsWrongMissingBooleanFloatNullAndDuplicateFields() {
        byte[] valid = encode(first()); ObjectNode root = (ObjectNode) StrictJson.parse(valid, MAX_BYTES);
        ObjectNode claim = (ObjectNode) root.path("claims").get(0).path("claim");
        claim.put("ordinal", true); ObjectNode booleanNode = root;
        assertThrows(IllegalArgumentException.class, () -> decode(StrictJson.canonical(booleanNode, MAX_BYTES)));
        root = (ObjectNode) StrictJson.parse(valid, MAX_BYTES); ((ObjectNode) root.path("claims").get(0).path("claim")).put("ordinal", 0.0);
        ObjectNode floating = root; assertThrows(IllegalArgumentException.class, () -> decode(floating.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        root = (ObjectNode) StrictJson.parse(valid, MAX_BYTES); root.putNull("claims"); ObjectNode nulled = root;
        assertThrows(IllegalArgumentException.class, () -> decode(StrictJson.canonical(nulled, MAX_BYTES)));
        root = (ObjectNode) StrictJson.parse(valid, MAX_BYTES); root.remove("consumptions"); ObjectNode missing = root;
        assertThrows(IllegalArgumentException.class, () -> decode(StrictJson.canonical(missing, MAX_BYTES)));
        String wire = new String(valid, java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> decode(wire.replaceFirst("\\{", "{\"schema\":\"duplicate\",").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void sharedIntentRejectsMissingEducationAndPreservesExplicitEmptyOptions() {
        var value = new OrdinaryInitiationIntent("educate_child_interaction", 4_000_000_001L,
                Optional.of(new OrdinaryInitiationIntent.Education(4_000_000_001L, 4_000_000_002L, List.of())), Optional.empty());
        assertEquals(value, OrdinaryInitiationIntent.fromJson(value.toJson()));
        assertThrows(IllegalArgumentException.class, () -> new OrdinaryInitiationIntent("educate_child_interaction", 4_000_000_002L, value.education(), Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> new OrdinaryInitiationIntent("educate_child_interaction", 1, Optional.empty(), Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryInitiationIntent.fromJson(value.toJson().with("recipient_id", new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true))));
    }
}
