package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionFixtures.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Action;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** New pure current-frame guard only. Software Complete DATA is not Root/game admission. */
final class KnownPendingInteractionCurrent223Test {
    @Test void actualKnownPolicyPreparerAndCurrentProjectionShareTheOriginalSignedPending() {
        for (String key : List.of("spar_with_knight_interaction", "perk_alliance_interaction")) {
            Fixture fixture = policyFixture(key);
            assertEquals(key.equals("spar_with_knight_interaction") ? Action.REJECT.step() : Action.ACCEPT.step(),
                    fixture.command().operation().value());
            RootInteractionContextProjection.requireExact(fixture.current(), fixture.context());
            assertEquals(fixture.context(), InteractionArguments.context(fixture.command()));
            NativeRequest before = KnownPendingInteractionEffects.preparation().prepare(fixture.command(), "before-current-guard");
            assertDoesNotThrow(() -> KnownPendingInteractionEffects.requireCurrent(fixture.current(), fixture.command()));
            NativeRequest after = KnownPendingInteractionEffects.preparation().prepare(fixture.command(), "after-current-guard");
            assertEquals(before, after);
            assertEquals(PENDING, InteractionJson.parse(after.additionalFields()).path("pending_interaction_id").intValue());
            assertEquals(fixture.command().operation().value(), after.step());
        }
    }

    @Test void actualExplicitNotificationProducerUsesTheSameCurrentGuardWithoutFakeNormalReply() {
        Complete current = complete(true);
        Context context = new RootInteractionContextProjection(Build.CROZIER4).project(current, NOW.plusSeconds(60));
        Action requested = Action.ACKNOWLEDGE;
        ExpectedPostcondition expected = KnownPendingInteractionCommands.expected(context, requested);
        Claims claims = new Claims(Set.of(), Set.of(), Set.of(), Set.of());
        var arguments = KnownPendingInteractionCommands.arguments(new ActionContext(context, "explicit-notification", expected, claims), requested);
        ActionCommand command = new ActionCommand("explicit-notification", context.before(), context.source(), context.sessionId(),
                new OperationKey(requested.step()), InteractionArguments.app(arguments), expected, claims, context.deadline());
        assertEquals(KnownPendingInteractionPostcondition.SCHEMA, command.expected().observerSchema());
        assertDoesNotThrow(() -> KnownPendingInteractionEffects.requireCurrent(current, command));
        assertEquals(requested.step(), KnownPendingInteractionEffects.preparation().prepare(command).step());
        Complete wrongChannel = changed(current, semantic -> ((ObjectNode) semantic.get("pending_character_interaction"))
                .put("auto_accept_notification", false));
        assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionEffects.requireCurrent(wrongChannel, command));
    }

    @Test void everyRetainedFullControlMustStillDescribeTheActualCurrentDriver() {
        Fixture fixture = policyFixture("spar_with_knight_interaction");
        List<Consumer<ObjectNode>> mutations = List.of(
                semantic -> ((ObjectNode) semantic.get("pending_character_interaction")).put("instance_id", PENDING + 1),
                semantic -> ((ObjectNode) semantic.get("pending_character_interaction")).put("sender_character_id", SENDER + 1),
                semantic -> ((ObjectNode) semantic.get("pending_character_interaction")).put("auto_accept_notification", true),
                semantic -> semantic.putNull("pending_character_interaction"),
                semantic -> semantic.put("paused", false),
                semantic -> semantic.put("map_ready", false),
                semantic -> semantic.put("speed", 2),
                semantic -> semantic.put("local_player_id", PLAYER + 1),
                semantic -> ((ObjectNode) semantic.get("played_character")).put("alive", false),
                semantic -> ((ObjectNode) semantic.get("played_character")).put("betrothed_id", 999),
                semantic -> ((ObjectNode) semantic.get("played_character")).withArray("spouse_ids").add(999),
                semantic -> semantic.putObject("active_event").put("instance_id", 9),
                semantic -> semantic.put("episode_run_id", "other-episode"));
        for (Consumer<ObjectNode> mutation : mutations) {
            Complete actual = changed(fixture.current(), mutation);
            assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionEffects.requireCurrent(actual, fixture.command()));
        }
    }

    @Test void connectionFullFrameSessionSourceAndQualifiedBuildCannotBeSubstituted() {
        Fixture fixture = policyFixture("spar_with_knight_interaction");
        Complete base = fixture.current();
        List<Complete> changed = new ArrayList<>();
        changed.add(copy(base, base.identity(), base.source(), base.sessionId(), BigInteger.TWO, base.semantic()));
        changed.add(copy(base, base.identity(), base.source(), "another-session", base.connectionGeneration(), base.semantic()));
        G2Source otherSource = new G2Source(base.source().machineId(), base.source().observedAtUtc(),
                base.source().exactBuild(), new org.xar.ck3.control.contracts.ExactRef("different-original-source", 1, "c".repeat(64)));
        changed.add(copy(base, base.identity(), otherSource, base.sessionId(), base.connectionGeneration(), base.semantic()));
        var frame = base.identity().frame();
        ObservationIdentity next = new ObservationIdentity(base.identity().machineId(), base.identity().game(),
                new ProposalFrame(new Frame(frame.identity().player(), frame.identity().nativeRevision().add(BigInteger.ONE),
                        frame.identity().dateRaw()), "different-current-frame", frame.revision().add(BigInteger.ONE), frame.episodeRunId()),
                base.identity().observationVersion());
        ObjectNode nextSemantic = (ObjectNode) DriverJson.toNode(base.semantic());
        nextSemantic.put("snapshot_id", next.frame().snapshotId()).put("revision", next.frame().revision())
                .put("native_revision", next.frame().identity().nativeRevision());
        changed.add(copy(base, next, base.source(), base.sessionId(), base.connectionGeneration(), InteractionArguments.app(nextSemantic)));
        changed.add(changed(base, semantic -> ((ObjectNode) semantic.path("diagnostics").get("hello"))
                .put("expected_ck3_sha256", "0".repeat(64))));
        changed.add(changed(base, semantic -> ((ObjectNode) semantic.path("diagnostics").get("hello"))
                .put("expected_ck3_version", "1.20.0.3")));
        for (Complete actual : changed) {
            assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionEffects.requireCurrent(actual, fixture.command()));
        }
    }

    @Test void preparedKnownPlanStillRejectsWrongOperationExpectedAndMalformedOriginal() {
        Fixture fixture = policyFixture("spar_with_knight_interaction");
        ActionCommand original = fixture.command();
        List<ActionCommand> invalid = new ArrayList<>();
        invalid.add(copyCommand(original, new OperationKey(Action.ACCEPT.step()), original.arguments(), original.expected()));
        ExpectedPostcondition wrongExpected = new ExpectedPostcondition(1, original.before(), original.source(),
                KnownPendingInteractionPostcondition.SCHEMA, List.of(new ExpectedBoolean(new FieldKey("pending.reply_observed"), false)));
        invalid.add(copyCommand(original, original.operation(), original.arguments(), wrongExpected));
        List<Consumer<ObjectNode>> mutations = List.of(
                args -> args.put("pending_id", PENDING + 1),
                args -> args.put("mutation_kind", "OTHER"),
                args -> args.put("accept", true),
                args -> args.putNull("known_pending_plan"),
                args -> ((ObjectNode) args.get("known_pending_plan")).remove("original_context_wrapper"),
                args -> ((ObjectNode) args.path("known_pending_plan").get("original_context_wrapper")).put("queried_revision", 999),
                args -> ((ObjectNode) args.path("known_pending_plan").path("original_context_wrapper")
                        .path("pending_character_interaction_context").get("provenance")).put("reply_validator_rva", "0x1"),
                args -> ((ObjectNode) args.path("known_pending_plan").get("java_policy_plan")).put("schema", "unsupported-plan-v99"));
        for (Consumer<ObjectNode> mutation : mutations) {
            ObjectNode args = InteractionArguments.parseApp(original.arguments()); mutation.accept(args);
            invalid.add(copyCommand(original, original.operation(), InteractionArguments.app(args), original.expected()));
        }
        for (ActionCommand command : invalid) {
            assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionEffects.requireCurrent(fixture.current(), command));
        }
    }

    @Test void pureCurrentValidationPreservesCompleteCommandArgumentsExpectedClaimsAndIdentity() {
        Fixture fixture = policyFixture("spar_with_knight_interaction");
        ActionCommand command = fixture.command();
        byte[] encoded = ActionCodec.encodeCommand(command), semantic = DriverJson.encode(fixture.current().semantic());
        String sha = ActionCodec.bodySha256(command);
        var expected = command.expected(); var claims = command.claims(); var arguments = command.arguments();
        ActionCommand cold = ActionCodec.decodeCommand(encoded);
        assertDoesNotThrow(() -> KnownPendingInteractionEffects.requireCurrent(fixture.current(), cold));
        assertArrayEquals(encoded, ActionCodec.encodeCommand(cold));
        assertArrayEquals(semantic, DriverJson.encode(fixture.current().semantic()));
        assertEquals(sha, ActionCodec.bodySha256(cold)); assertEquals(command.actionId(), cold.actionId());
        assertEquals(arguments, cold.arguments()); assertEquals(expected, cold.expected()); assertEquals(claims, cold.claims());
        assertEquals(command.origin(), cold.origin()); assertEquals(command.source(), cold.source());
        assertEquals(command.sessionId(), cold.sessionId()); assertEquals(command.deadline(), cold.deadline());
        assertEquals(command.protocolIdentity(), cold.protocolIdentity());
    }

    private record Fixture(Complete current, Context context, ActionCommand command) { }

    private static Fixture policyFixture(String key) {
        Complete actual = complete(false);
        Context context = new RootInteractionContextProjection(Build.CROZIER4).project(actual, NOW.plusSeconds(60));
        RootInteractionContextProjection.requireExact(actual, context);
        ObjectNode original = wire(context, key);
        var request = request(context, (ObjectNode) DriverJson.toNode(actual.semantic()), original, steps());
        var policy = new KnownPendingInteractionPolicy(SOURCE, ignored -> context, noReads(),
                PendingInteractionContracts.pending(SOURCE), operation -> Optional.empty());
        var chosen = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluateCore(request, OrdinaryPolicy.Draft.empty()));
        ActionCommand command = chosen.draft().command().orElseThrow();
        assertEquals(KnownPendingInteractionPostcondition.SCHEMA, command.expected().observerSchema());
        assertTrue(command.arguments().get("known_pending_plan") instanceof OpportunityJson.Obj);
        return new Fixture(actual, context, command);
    }

    /** Public legacy Complete constructor is the same legal software-DATA route used by existing consumer tests. */
    private static Complete complete(boolean notification) {
        ObservationIdentity identity = new ObservationIdentity("known-current-fixture",
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(PLAYER), BigInteger.valueOf(41), BigInteger.valueOf(24000)),
                        "known-current-frame-7", BigInteger.valueOf(7), "known-current-episode"), 1);
        G2Source source = new G2Source(identity.machineId(), NOW.toString(), "1.20.0.4@sha256:" + Build.CROZIER4.sha256(), SOURCE);
        ObjectNode semantic = InteractionJson.F.objectNode().put("snapshot_id", identity.frame().snapshotId())
                .put("revision", identity.frame().revision()).put("native_revision", identity.frame().identity().nativeRevision())
                .put("date_raw", identity.frame().identity().dateRaw()).put("episode_run_id", identity.frame().episodeRunId())
                .put("episode_character_id", PLAYER).put("local_player_id", PLAYER).put("paused", true).put("map_ready", true).put("speed", 1);
        semantic.putNull("active_event"); semantic.putNull("current_event"); semantic.putNull("one_life_terminal_reason");
        semantic.putArray("active_wars"); semantic.putArray("player_armies");
        semantic.putObject("pending_character_interaction").put("instance_id", PENDING).put("sender_character_id", SENDER)
                .put("auto_accept_notification", notification);
        semantic.putObject("played_character").put("character_id", PLAYER).put("alive", true).putNull("betrothed_id").putArray("spouse_ids");
        semantic.putObject("played_character_gold").put("raw", 100000).put("scale", 100000);
        semantic.putObject("diagnostics").put("connection_generation", 1).put("bridge_pid", 123).putObject("hello")
                .put("expected_ck3_version", Build.CROZIER4.version()).put("expected_ck3_sha256", Build.CROZIER4.sha256());
        OpportunityJson.Obj complete = InteractionArguments.app(semantic);
        return new Complete(identity, source, "known-current-session", BigInteger.ONE, complete, SOURCE, NOW,
                DriverObservationAssembler.bindingSha256(complete));
    }

    private static Complete changed(Complete before, Consumer<ObjectNode> mutation) {
        ObjectNode semantic = (ObjectNode) DriverJson.toNode(before.semantic()); mutation.accept(semantic);
        return copy(before, before.identity(), before.source(), before.sessionId(), before.connectionGeneration(), InteractionArguments.app(semantic));
    }

    private static Complete copy(Complete before, ObservationIdentity identity, G2Source source, String session,
            BigInteger connection, OpportunityJson.Obj semantic) {
        return new Complete(identity, source, session, connection, semantic, before.originalEvidence(), before.observedAt(),
                DriverObservationAssembler.bindingSha256(semantic));
    }

    private static ActionCommand copyCommand(ActionCommand before, OperationKey operation,
            OpportunityJson.Obj arguments, ExpectedPostcondition expected) {
        return new ActionCommand(before.actionId(), before.before(), before.source(), before.sessionId(), operation,
                arguments, expected, before.claims(), before.deadline());
    }
}
