package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.GameIdentity;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.Observation;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer.Consumed;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer.Publication;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Reconciliation;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Verdict;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Context;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** All frame/process/checkpoint contents are explicit software fixtures, never live M7 credit. */
final class M7OrdinaryPlanConsumerTest {
    @TempDir Path temporary;

    @Test void actualGovernmentProducerReachesEveryConsumerAndFreshPersistenceReader() throws IOException {
        ObjectNode request = baseRequest();
        Context produced = produced(request);
        Goal goal = goal(request);
        Observation frame = frame(request, goal, produced.governmentKey(), produced.adapterFamily());
        for (Publication publication : Publication.values()) {
            Consumed actual = M7OrdinaryPlanConsumer.consume(publication, frame, "life-advance", Optional.of(produced));
            byte[] encoded = M7OrdinaryPlanConsumer.encode(actual);
            Path file = temporary.resolve(publication.wire() + ".receipt.json");
            Files.write(file, encoded, StandardOpenOption.CREATE_NEW);
            Consumed fresh = M7OrdinaryPlanConsumer.decode(Files.readAllBytes(file));
            assertEquals(StrictJson.parse(encoded, M7OrdinaryPlanConsumer.MAX_BYTES),
                    StrictJson.parse(M7OrdinaryPlanConsumer.encode(fresh), M7OrdinaryPlanConsumer.MAX_BYTES));
            assertEquals(goal, fresh.observation().goal());
            assertEquals(frame, fresh.observation(), "all machine/source/Game/frame/episode/goal fields survive the fresh reader");
            assertEquals(OrdinaryCampaignGoal.plan(goal), fresh.campaignGoalPlanUsed());
            assertEquals("life-advance", fresh.selectedStep());
            assertEquals(produced.governmentKey(), fresh.campaignGovernmentContextUsed().orElseThrow().governmentKey());
            assertFalse(fresh.gameActionsSubmitted()); assertFalse(fresh.coldAuthorityGranted()); assertFalse(fresh.replayAuthorized());
        }
    }

    @Test void hostCompositionUsesTheSameProducerAndConsumerNotASeparatePlanRule() throws IOException {
        ObjectNode request = baseRequest(); Context context = produced(request); Goal goal = goal(request);
        Observation frame = frame(request, goal, context.governmentKey(), context.adapterFamily());
        ObjectNode input = StrictJson.object(); input.put("schema", M7OrdinaryPlanConsumer.INPUT_SCHEMA);
        input.put("publication", "ordinary_plan"); input.set("observation", StrictJson.parse(CheckpointContinuity.encodeObservation(frame)));
        input.put("selected_step", "query-arrange-marriage-choices-v1");
        input.set("government_context", StrictJson.parse(GovernmentContextCodec.encode(context)));
        byte[] before = raw(input);
        Consumed consumed = M7OrdinaryPlanConsumer.decode(M7OrdinaryPlanConsumer.compose(before));
        assertArrayEquals(before, raw(input));
        assertEquals("query-arrange-marriage-choices-v1", consumed.selectedStep());
        assertEquals(List.of(100, 60), consumed.campaignGoalPlanUsed().priorities().stream().map(OrdinaryCampaignGoal.Priority::priority).toList());
        assertEquals("marriage", consumed.campaignGoalPlanUsed().focus());
    }

    @Test void originalProducerToDomainWireResponseAndFreshPersistedOrdinaryConsumer() throws IOException {
        ObjectNode producerInput = baseRequest(); Context context = produced(producerInput); Goal goal = goal(producerInput);
        Observation frame = frame(producerInput, goal, context.governmentKey(), context.adapterFamily());
        byte[] retainedProducerInput = raw(producerInput);
        Path sourceFile = temporary.resolve("synthetic-ordinary-producer-input.json");
        Files.write(sourceFile, retainedProducerInput, StandardOpenOption.CREATE_NEW);
        G2Source source = new G2Source("synthetic-m7-machine", "2026-10-22T20:00:00Z", "1.20.0.2-fixture",
                new ExactRef(sourceFile.toString(), retainedProducerInput.length, sha256(retainedProducerInput)));
        ObjectNode payload = StrictJson.object(); payload.put("operation", "ordinary_plan_consume");
        ObjectNode input = payload.putObject("input"); input.put("schema", M7OrdinaryPlanConsumer.INPUT_SCHEMA);
        input.put("publication", "ordinary_plan"); input.set("observation", StrictJson.parse(CheckpointContinuity.encodeObservation(frame)));
        input.put("selected_step", "life-advance"); input.set("government_context", StrictJson.parse(GovernmentContextCodec.encode(context)));
        G2Request original = new G2Request("synthetic-m7-wire-roundtrip", Milestone.M7, source,
                ProjectionJson.object(raw(payload), ProjectionJson.MAX_BYTES));
        var engine = new G2ResearchEngine(List.of(new M7Research()));
        var response = engine.evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(original)));
        assertEquals(original.source(), response.source()); assertEquals(original.requestId(), response.requestId());
        G2Source crossedSource = new G2Source("different-synthetic-machine", source.observedAtUtc(), source.exactBuild(), source.sourceRef());
        assertThrows(IllegalArgumentException.class, () -> engine.evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(
                new G2Request(original.requestId(), Milestone.M7, crossedSource, original.payload())))));
        Path retained = temporary.resolve("synthetic-m7-wire-response.json");
        Files.write(retained, G2Wire.encodeResponse(response), StandardOpenOption.CREATE_NEW);
        var freshWire = G2Wire.decodeResponse(Files.readAllBytes(retained));
        Consumed freshConsumer = M7OrdinaryPlanConsumer.decode(freshWire.result().bytes());
        assertEquals(source, freshWire.source()); assertEquals(frame, freshConsumer.observation());
        assertEquals(OrdinaryCampaignGoal.plan(goal), freshConsumer.campaignGoalPlanUsed());
        assertEquals("life-advance", freshConsumer.selectedStep());
        assertArrayEquals(retainedProducerInput, Files.readAllBytes(sourceFile));
        assertFalse(freshConsumer.gameActionsSubmitted()); assertFalse(freshConsumer.coldAuthorityGranted()); assertFalse(freshConsumer.replayAuthorized());
    }

    @Test void checkpointRoundTripThenMatchedNaturalTransitionConsumesTheSameIntent() throws IOException {
        ObjectNode request = baseRequest(); Goal original = goal(request);
        Observation before = frame(request, original, null, null);
        Path retained = temporary.resolve("synthetic-retained-intent.receipt.json");
        Files.write(retained, M7OrdinaryPlanConsumer.encode(M7OrdinaryPlanConsumer.consume(
                Publication.CHECKPOINT_READER, before, "life-advance", Optional.empty())), StandardOpenOption.CREATE_NEW);
        Goal restored = M7OrdinaryPlanConsumer.decode(Files.readAllBytes(retained)).observation().goal();
        Observation replacement = new Observation(before.machineId(), before.sourceEpoch(),
                new GameIdentity(202L, "20261023091345.123456+480", "C:/synthetic/ck3.exe"),
                before.snapshotId(), before.revision(), before.nativeRevision(), before.episodeRunId(),
                before.actorCharacterId(), before.dateRaw(), restored, null, null);
        var comparison = CheckpointContinuity.compare(before, replacement);
        assertTrue(comparison.sameGoal()); assertTrue(comparison.sameCampaignOrigin());
        assertTrue(comparison.sameRulerEpisode()); assertFalse(comparison.sameGameIdentity());
        assertFalse(comparison.grantsColdAuthority()); assertFalse(comparison.actionReplayAuthorized());

        Goal continued = OrdinaryCampaignGoal.continueGoal(restored, new Reconciliation(Verdict.MATCHED,
                restored.currentCharacterId(), 40_000L, List.of(10L, 11L), List.of(12L), List.of()));
        Observation successor = new Observation(replacement.machineId(), replacement.sourceEpoch(), replacement.game(),
                "synthetic:m7:successor", 43L, replacement.nativeRevision() + 1L, "synthetic-successor-episode",
                continued.currentCharacterId(), replacement.dateRaw() + 24L, continued, null, null);
        Consumed following = M7OrdinaryPlanConsumer.decode(M7OrdinaryPlanConsumer.encode(M7OrdinaryPlanConsumer.consume(
                Publication.SUCCESSOR_PLAN, successor, "query-arrange-marriage-choices-v1", Optional.empty())));
        assertEquals(original.campaignId(), following.observation().goal().campaignId());
        assertEquals(original.originCharacterId(), following.observation().goal().originCharacterId());
        assertEquals(40_000L, following.campaignGoalPlanUsed().currentCharacterId());
        assertEquals(1L, following.campaignGoalPlanUsed().progress().reconciledSuccessions());
        assertEquals(List.of(10L, 11L), following.campaignGoalPlanUsed().progress().lastSuccession().orElseThrow().matchedInheritedTitleIds());
        assertFalse(following.replayAuthorized());
    }

    @Test void unknownAndEveryUnmatchedReconciliationLeaveThePersistedIntentUnchanged() throws IOException {
        Goal original = goal(baseRequest()); byte[] before = GoalCodec.encodeGoal(original);
        for (Verdict verdict : Verdict.values()) if (verdict != Verdict.MATCHED) {
            assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.continueGoal(original,
                    new Reconciliation(verdict, original.currentCharacterId(), 40_000L, List.of(10L), List.of(), List.of())), verdict.name());
            assertArrayEquals(before, GoalCodec.encodeGoal(original));
        }
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.continueGoal(original,
                new Reconciliation(Verdict.MATCHED, 999L, 40_000L, List.of(10L), List.of(), List.of())));
        assertArrayEquals(before, GoalCodec.encodeGoal(original));
    }

    @Test void exactGovernmentKeysRemainSeparateFromTheirSharedFamilyWithoutLiveCredit() throws IOException {
        ObjectNode feudalRequest = baseRequest(); Context feudal = produced(feudalRequest);
        ObjectNode clanRequest = feudalRequest.deepCopy();
        ObjectNode government = (ObjectNode) clanRequest.path("government_observation").path("government");
        government.put("key", "clan_government"); government.putArray("flags").add("government_is_clan");
        Context clan = produced(clanRequest); Goal goal = goal(feudalRequest);
        assertEquals("feudal_government", feudal.governmentKey()); assertEquals("clan_government", clan.governmentKey());
        assertEquals("core_landed", feudal.adapterFamily()); assertEquals(feudal.adapterFamily(), clan.adapterFamily());
        Observation feudalFrame = frame(feudalRequest, goal, feudal.governmentKey(), feudal.adapterFamily());
        Observation clanFrame = frame(clanRequest, goal, clan.governmentKey(), clan.adapterFamily());
        var facts = CheckpointContinuity.compare(feudalFrame, clanFrame);
        assertTrue(facts.governmentKeyChanged()); assertFalse(facts.adapterFamilyChanged());
        assertFalse(facts.grantsColdAuthority()); assertFalse(facts.actionReplayAuthorized());
        Consumed persisted = M7OrdinaryPlanConsumer.decode(M7OrdinaryPlanConsumer.encode(
                M7OrdinaryPlanConsumer.consume(Publication.ORDINARY_PLAN, clanFrame, "life-advance", Optional.of(clan))));
        assertEquals("clan_government", persisted.campaignGovernmentContextUsed().orElseThrow().governmentKey());
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.consume(
                Publication.ORDINARY_PLAN, feudalFrame, "life-advance", Optional.of(clan)));
    }

    @Test void absentAndExplicitNotQueriedGovernmentInputsDoNotAddAQueryGate() throws IOException {
        ObjectNode request = baseRequest(); Goal goal = goal(request); request.put("query_permitted", false);
        Context notQueried = produced(request); assertFalse(notQueried.ordinaryGoalContextReady());
        Observation frame = frame(request, goal, null, null);
        for (Optional<Context> context : List.of(Optional.<Context>empty(), Optional.of(notQueried))) {
            Consumed result = M7OrdinaryPlanConsumer.decode(M7OrdinaryPlanConsumer.encode(M7OrdinaryPlanConsumer.consume(
                    Publication.ORDINARY_PLAN, frame, "life-advance", context)));
            assertEquals("life-advance", result.selectedStep());
            assertEquals(context.isPresent(), result.campaignGovernmentContextUsed().isPresent());
            assertFalse(result.gameActionsSubmitted()); assertFalse(result.replayAuthorized());
        }
    }

    @Test void nativeDecimalExtensionsSurviveProducerAndPersistedConsumerValueDomain() throws IOException {
        ObjectNode request = baseRequest();
        ((ObjectNode) request.get("government_observation")).putObject("future_native_metadata").put("fractional_measurement", 1.25);
        Context context = produced(request); Goal goal = goal(request);
        Consumed consumed = M7OrdinaryPlanConsumer.consume(Publication.ORDINARY_PLAN,
                frame(request, goal, context.governmentKey(), context.adapterFamily()), "life-advance", Optional.of(context));
        byte[] first = M7OrdinaryPlanConsumer.encode(consumed);
        byte[] second = M7OrdinaryPlanConsumer.encode(M7OrdinaryPlanConsumer.decode(first));
        assertEquals(StrictJson.parse(first, M7OrdinaryPlanConsumer.MAX_BYTES), StrictJson.parse(second, M7OrdinaryPlanConsumer.MAX_BYTES));
        assertEquals(StrictJson.parse(raw(request.get("government_observation")), M7OrdinaryPlanConsumer.MAX_BYTES),
                StrictJson.parse(second, M7OrdinaryPlanConsumer.MAX_BYTES)
                .path("campaign_government_context_used").get("government_runtime_adapter"));
    }

    @Test void crossedActorDateRevisionAndCampaignAreRejectedBeforePublication() throws IOException {
        ObjectNode request = baseRequest(); Context context = produced(request); Goal goal = goal(request);
        Observation valid = frame(request, goal, context.governmentKey(), context.adapterFamily());
        for (Observation bad : List.of(
                new Observation(valid.machineId(), valid.sourceEpoch(), valid.game(), valid.snapshotId(), valid.revision(),
                        valid.nativeRevision() + 1L, valid.episodeRunId(), valid.actorCharacterId(), valid.dateRaw(), goal, valid.governmentKey(), valid.adapterFamily()),
                new Observation(valid.machineId(), valid.sourceEpoch(), valid.game(), valid.snapshotId(), valid.revision(),
                        valid.nativeRevision(), valid.episodeRunId(), valid.actorCharacterId(), valid.dateRaw() + 24L, goal, valid.governmentKey(), valid.adapterFamily()),
                new Observation(valid.machineId(), valid.sourceEpoch(), valid.game(), valid.snapshotId(), valid.revision(),
                        valid.nativeRevision(), valid.episodeRunId(), valid.actorCharacterId(), valid.dateRaw(),
                        OrdinaryCampaignGoal.newGoal("different-campaign", valid.actorCharacterId()), valid.governmentKey(), valid.adapterFamily()))) {
            assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.consume(
                    Publication.ORDINARY_PLAN, bad, "life-advance", Optional.of(context)));
        }
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.consume(Publication.ORDINARY_PLAN,
                new Observation(valid.machineId(), valid.sourceEpoch(), valid.game(), valid.snapshotId(), valid.revision(),
                        valid.nativeRevision(), valid.episodeRunId(), valid.actorCharacterId() + 1L, valid.dateRaw(), goal,
                        valid.governmentKey(), valid.adapterFamily()), "life-advance", Optional.empty()));
    }

    @Test void producerCurrentGoalMismatchCannotBeRelabeledAsTheObservedPlayerFrame() throws IOException {
        ObjectNode request = baseRequest();
        ((ObjectNode) request.path("snapshot").get("campaign_goal")).put("current_character_id", 100L);
        Context mismatch = produced(request);
        assertEquals("ordinary_goal_current_ruler_not_matched", mismatch.unavailableReason());
        assertFalse(mismatch.ordinaryGoalContextReady());
        Goal mismatchedGoal = goal(request);
        Observation mislabeled = frame(request, mismatchedGoal, mismatch.governmentKey(), mismatch.adapterFamily());
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.consume(
                Publication.ORDINARY_PLAN, mislabeled, "life-advance", Optional.of(mismatch)));
    }

    @Test void persistedPlanMeaningAndForbiddenAuthorityFlagsCannotBeChanged() throws IOException {
        ObjectNode request = baseRequest(); Context context = produced(request); Goal goal = goal(request);
        byte[] original = M7OrdinaryPlanConsumer.encode(M7OrdinaryPlanConsumer.consume(Publication.ORDINARY_PLAN,
                frame(request, goal, context.governmentKey(), context.adapterFamily()), "life-advance", Optional.of(context)));
        for (String field : List.of("game_actions_submitted", "cold_authority_granted", "replay_authorized")) {
            ObjectNode changed = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES); changed.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(raw(changed)), field);
        }
        ObjectNode changed = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES);
        ((ObjectNode) changed.get("campaign_goal_plan_used")).put("current_character_id", goal.currentCharacterId() + 1L);
        byte[] changedActor = raw(changed);
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(changedActor));
        changed = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES);
        ((ObjectNode) changed.get("campaign_goal_plan_used")).put("focus", "war");
        byte[] changedFocus = raw(changed);
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(changedFocus));
    }

    @Test void consumerWireRejectsWrongTokensMissingFieldsDuplicatesAndUnknownLocations() throws IOException {
        ObjectNode request = baseRequest(); Goal goal = goal(request);
        byte[] valid = M7OrdinaryPlanConsumer.encode(M7OrdinaryPlanConsumer.consume(Publication.ORDINARY_PLAN,
                frame(request, goal, null, null), "life-advance", Optional.empty()));
        for (String field : List.of("schema", "publication", "observation", "selected_step",
                "campaign_goal_plan_used", "campaign_government_context_used", "game_actions_submitted", "cold_authority_granted", "replay_authorized")) {
            ObjectNode missing = (ObjectNode) StrictJson.parse(valid, M7OrdinaryPlanConsumer.MAX_BYTES); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(raw(missing)), field);
        }
        for (String token : List.of("true", "1", "1.0", "null")) {
            ObjectNode changed = (ObjectNode) StrictJson.parse(valid, M7OrdinaryPlanConsumer.MAX_BYTES);
            changed.set("selected_step", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(raw(changed)), token);
        }
        String text = new String(valid, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode((text + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode((text.substring(0, text.length() - 1)
                + ",\"publication\":\"ordinary_plan\"}").getBytes(StandardCharsets.UTF_8)));
        ObjectNode wrong = (ObjectNode) StrictJson.parse(valid, M7OrdinaryPlanConsumer.MAX_BYTES); wrong.put("publication", "legacy_nonwar");
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(raw(wrong)));
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(new byte[] {(byte) 0xc3, 0x28}));
    }

    private static ObjectNode baseRequest() throws IOException {
        JsonNode golden;
        try (InputStream input = M7OrdinaryPlanConsumerTest.class.getResourceAsStream("/government/original-producer-golden.json")) {
            assertNotNull(input, "mandatory original producer resource is required; no skipped environment or machine-local path fallback");
            golden = StrictJson.parse(input.readAllBytes());
        }
        assertEquals("xar.java-government-context-original-producer-golden/v1", golden.path("schema").textValue());
        assertTrue(golden.path("source_refs_unchanged").booleanValue());
        return (ObjectNode) golden.get("base_request").deepCopy();
    }
    private static Context produced(ObjectNode request) {
        return GovernmentContextCodec.decodeContext(GovernmentContextCodec.compose(raw(request)));
    }
    private static Goal goal(ObjectNode request) { return GoalCodec.decodeGoal(raw(request.path("snapshot").get("campaign_goal"))); }
    private static Observation frame(ObjectNode request, Goal goal, String key, String family) {
        JsonNode snapshot = request.get("snapshot");
        return new Observation("synthetic-m7-machine", "a".repeat(64),
                new GameIdentity(101L, "20261023081234.123456+480", "C:/synthetic/ck3.exe"),
                "synthetic:m7:frame", 42L, snapshot.get("native_revision").longValue(), "synthetic-original-episode",
                goal.currentCharacterId(), snapshot.get("date_raw").longValue(), goal, key, family);
    }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static String sha256(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 required by Java", error); }
    }
}
