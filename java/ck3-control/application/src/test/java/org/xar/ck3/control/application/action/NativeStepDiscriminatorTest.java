package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.BiFunction;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.ritecreation.RiteCreationCodec;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real pure Rite producer through actual shared registrations. These DATA vectors grant no Game/source authority. */
final class NativeStepDiscriminatorTest {
    private static final Frame FRAME = new Frame("native-1", BigInteger.ONE, BigInteger.ONE, BigInteger.ONE,
            123, 29829, 100, new EpisodeScope("episode-1"));

    private static NativeRequest nativeRequest(RiteCreation selected, String actualRequestId) {
        Write action = switch (selected) {
            case PREVIEW -> null;
            case OPEN_CREATE_DRAFT -> new OpenCreate();
            case OPEN_EDIT_CURRENT_RITE_DRAFT -> new OpenEdit();
            case SELECT_CORE_TENET -> new CoreTenet(0, new Definition("tenet_test"));
            case SELECT_DOCTRINE -> new Doctrine(new Definition("group_test"), new Definition("doctrine_test"));
            case SET_NAME_FIELD -> new Name(NameField.NAME, "original native name");
            case PREPARE_CONFIRMATION -> new Prepare(new Identity("a".repeat(64)), Outcome.CREATE_RITE);
            case CONFIRM_ONCE -> new Confirm(new Identity("a".repeat(64)), Outcome.CREATE_RITE);
        };
        var fields = new NativeFields(selected, new SourceRite(7), Optional.ofNullable(action),
                selected == RiteCreation.CONFIRM_ONCE ? Optional.of(actualRequestId) : Optional.empty());
        var actual = RiteCreationCodec.nativeFields(fields, FRAME);
        return new NativeRequest(selected.nativeStep(), Optional.of(selected.capability()),
                RiteCreationCodec.raw(OpportunityJson.toNode(actual)));
    }
    private static ReadContract<String> readContract(RiteCreation operation,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare) {
        return new ReadContract<>("rite/" + operation.wire(), operation.operationKey(), Optional.of(operation.capability()),
                operation.capability(), ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, ActionCoordinatorTest.REF, prepare,
                receipt -> "source-only", receipt -> "source-only");
    }
    private static NativeEffectRegistry.Binding binding(RiteCreation operation) {
        var prepare = new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) {
                throw new UnsupportedOperationException("the real protocol request identity is required");
            }
            @Override public NativeRequest prepare(ActionCommand command, String requestId) {
                return nativeRequest(operation, requestId);
            }
        };
        return new NativeEffectRegistry.Binding(operation.operationKey(), ActionCoordinatorTest.REF, prepare,
                (command, attempt, dispatch) -> NativeEffectRegistry.Projected.pending("DATA has no actual native poststate", List.of()));
    }

    @Test void allEightActualPureProducersRetainOriginalWireAndStrictIdentitySerde() {
        for (RiteCreation operation : RiteCreation.values()) {
            var request = nativeRequest(operation, "actual-request-1");
            NativeStepDiscriminator.requireRequest(operation.operationKey(), operation.kind(), request);
            NativeStepDiscriminator.requireWire(operation.operationKey(), operation.kind(), request.step(), request.additionalFields());
            assertNotEquals(operation.operationKey().value(), request.step());
            assertEquals(operation, RiteCreation.parse(operation.wire()));
            var identity = NativeStepDiscriminator.identity(operation.operationKey());
            assertEquals(operation.nativeStep(), identity.nativeStep()); assertEquals(Optional.of(operation), identity.selector());
            var encoded = StrictJson.canonical(NativeStepDiscriminator.toJson(identity));
            assertEquals(identity, NativeStepDiscriminator.fromJson(StrictJson.parse(encoded)));
            var command = ActionCoordinatorTest.command("rite-" + operation.wire(), operation.operationKey().value());
            assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        }
    }

    @Test void rootInventorySeparatesPreviewAndSevenActionsOnTheSameActualWireStep() {
        var preview = readContract(RiteCreation.PREVIEW, (request, id) -> nativeRequest(RiteCreation.PREVIEW, id));
        var actions = new ArrayList<RootExecutableBindings.ActionBinding>();
        for (RiteCreation operation : RiteCreation.values()) if (operation.kind() == ExecutableStepBindings.Kind.ACTION)
            actions.add(new RootExecutableBindings.ActionBinding(binding(operation), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(operation.capability()), ActionCoordinatorTest.REF));
        var root = RootExecutableBindings.freeze(actions, RootReadContractCatalog.staticOnly(List.of(preview)), List.of(), 16);
        assertEquals(8, root.installed().size());
        assertEquals(8, root.installed().stream().map(ExecutableStepBindings.InstalledStep::operation).distinct().count());
        assertEquals(1, root.installed().stream().map(value -> value.nativeIdentity().nativeStep()).distinct().count());
        assertEquals(ExecutableStepBindings.Kind.READ, root.resolve(RiteCreation.PREVIEW.operationKey()).orElseThrow().kind());
        var request = new PlanningReadRequest(ActionCoordinatorTest.frame(1), ActionCoordinatorTest.SOURCE, "session-1",
                RiteCreation.PREVIEW.operationKey(), new OpportunityJson.Obj(java.util.Map.of()), ActionCoordinatorTest.NOW.plusSeconds(10));
        assertEquals(nativeRequest(RiteCreation.PREVIEW, "real-preview"), preview.prepare(request, "real-preview"));
        for (RiteCreation operation : RiteCreation.values()) if (operation.kind() == ExecutableStepBindings.Kind.ACTION) {
            var command = ActionCoordinatorTest.command("root-" + operation.wire(), operation.operationKey().value());
            assertEquals(nativeRequest(operation, "actual-protocol"), root.prepare(command, "actual-protocol"));
            assertEquals(nativeRequest(operation, "actual-protocol"), root.effects().prepare(command, "actual-protocol"));
        }
        assertThrows(IllegalArgumentException.class, () -> RootExecutableBindings.freeze(
                List.of(actions.getFirst(), actions.getFirst()), RootReadContractCatalog.staticOnly(List.of(preview)), List.of(), 16));
    }

    @Test void wrongKindBareOrUnknownSelectorCannotRegisterOrPrepare() {
        assertThrows(IllegalArgumentException.class, () -> binding(RiteCreation.PREVIEW));
        assertThrows(IllegalArgumentException.class, () -> readContract(RiteCreation.CONFIRM_ONCE,
                (request, id) -> nativeRequest(RiteCreation.CONFIRM_ONCE, id)));
        for (String operation : List.of(RiteCreation.PREVIEW.nativeStep(), RiteCreation.PREVIEW.nativeStep() + ":unknown",
                RiteCreation.PREVIEW.nativeStep() + ":PREVIEW"))
            assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.identity(new OperationKey(operation)));
        for (RiteCreation operation : RiteCreation.values()) {
            assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.requireRegistration(
                    operation.operationKey(), ExecutableStepBindings.Kind.COMPOSITE, Optional.of(operation.capability())));
            assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.requireRegistration(
                    operation.operationKey(), operation.kind(), Optional.empty()));
            var wrong = new NativeRequest(operation.nativeStep(), Optional.of(operation.capability()),
                    new RawJson("{\"operation\":true}".getBytes(StandardCharsets.UTF_8)));
            assertFalse(NativeStepDiscriminator.matchesRequest(operation.operationKey(), operation.kind(), wrong));
        }
        var wrongPrepare = readContract(RiteCreation.PREVIEW, (request, id) -> nativeRequest(RiteCreation.OPEN_CREATE_DRAFT, id));
        var request = new PlanningReadRequest(ActionCoordinatorTest.frame(1), ActionCoordinatorTest.SOURCE, "session-1",
                RiteCreation.PREVIEW.operationKey(), new OpportunityJson.Obj(java.util.Map.of()), ActionCoordinatorTest.NOW.plusSeconds(10));
        assertThrows(IllegalArgumentException.class, () -> wrongPrepare.prepare(request, "original-preview"));
        assertFalse(NativeStepDiscriminator.matchesRequest(RiteCreation.PREVIEW.operationKey(), ExecutableStepBindings.Kind.ACTION,
                nativeRequest(RiteCreation.PREVIEW, "cannot-write")));
    }

    @Test void identitySchemaAndSelectorTypesAreClosedAndPlainRequestsKeepTheirOriginalBudget() {
        var identity = NativeStepDiscriminator.identity(RiteCreation.PREVIEW.operationKey());
        var row = NativeStepDiscriminator.toJson(identity);
        for (String missing : List.of("schema", "operation", "native_step", "selector")) {
            var bad = row.deepCopy(); bad.remove(missing);
            assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.fromJson(bad));
        }
        var badType = row.deepCopy(); badType.put("selector", true);
        assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.fromJson(badType));
        var mixed = row.deepCopy(); mixed.put("selector", RiteCreation.CONFIRM_ONCE.wire());
        assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.fromJson(mixed));
        var unknown = row.deepCopy(); unknown.put("extra", 1);
        assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.fromJson(unknown));
        var plain = new OperationKey("existing-plain-step");
        var large = new RawJson(("{\"payload\":\"" + "x".repeat((1 << 20) + 1) + "\"}").getBytes(StandardCharsets.UTF_8));
        NativeStepDiscriminator.requireRequest(plain, ExecutableStepBindings.Kind.ACTION, new NativeRequest(plain.value(), Optional.empty(), large));
        var plainIdentity = NativeStepDiscriminator.identity(plain);
        assertTrue(plainIdentity.selector().isEmpty()); assertTrue(NativeStepDiscriminator.toJson(plainIdentity).get("selector").isNull());
        assertEquals(plainIdentity, NativeStepDiscriminator.fromJson(NativeStepDiscriminator.toJson(plainIdentity)));
    }

    @org.junit.jupiter.api.Test void actualNormalExitFiveSelectorsRetainActionFieldWireAndKind() {
        for (var value : NativeStepDiscriminator.NormalExit.values()) {
            var fields = new RawJson(("{\"action\":\"" + value.wire() + "\"}").getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var request = new NativeRequest(value.nativeStep(), Optional.of(value.capability()), fields);
            NativeStepDiscriminator.requireRequest(value.operationKey(), value.kind(), request);
            var current = NativeStepDiscriminator.identity(value.operationKey());
            assertEquals("normal-exit-map-v1", current.nativeStep());
            assertEquals("normal-exit-map-v1", value.capability());
            assertEquals(value, current.selector().orElseThrow());
            assertEquals(current, NativeStepDiscriminator.fromJson(NativeStepDiscriminator.toJson(current)));
            var wrongField = new NativeRequest(value.nativeStep(), Optional.of(value.capability()),
                    new RawJson(("{\"operation\":\"" + value.wire() + "\"}").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertFalse(NativeStepDiscriminator.matchesRequest(value.operationKey(), value.kind(), wrongField));
            var wrongKind = value.kind() == ExecutableStepBindings.Kind.READ ? ExecutableStepBindings.Kind.ACTION : ExecutableStepBindings.Kind.READ;
            assertFalse(NativeStepDiscriminator.matchesRequest(value.operationKey(), wrongKind, request));
            assertFalse(NativeStepDiscriminator.matchesRequest(value.operationKey(), value.kind(),
                    new NativeRequest(value.nativeStep(), Optional.of("game.command.normal-exit-map-v1"), fields)));
            for (String token : List.of("false", "1.0", "null", "[]")) {
                var bad = new NativeRequest(value.nativeStep(), Optional.of(value.capability()),
                        new RawJson(("{\"action\":" + token + "}").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertFalse(NativeStepDiscriminator.matchesRequest(value.operationKey(), value.kind(), bad));
            }
        }
        assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.identity(new OperationKey("normal-exit-map-v1")));
        assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.identity(new OperationKey("normal-exit-map-v1:unknown")));
    }
    @org.junit.jupiter.api.Test void historicalIdentityV1RetainsItsOwnVersionAndCannotRecognizeNewExitFamily() {
        var historical = NativeStepDiscriminator.toJson(NativeStepDiscriminator.identity(RiteCreation.PREVIEW.operationKey()));
        historical.put("schema", NativeStepDiscriminator.LEGACY_SCHEMA);
        var loaded = NativeStepDiscriminator.fromJson(historical);
        assertEquals(NativeStepDiscriminator.IdentityVersion.HISTORICAL_V1, loaded.version());
        assertEquals(historical, NativeStepDiscriminator.toJson(loaded));
        for (var value : NativeStepDiscriminator.NormalExit.values()) {
            var wrongVersion = NativeStepDiscriminator.toJson(NativeStepDiscriminator.identity(value.operationKey()));
            wrongVersion.put("schema", NativeStepDiscriminator.LEGACY_SCHEMA);
            assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.fromJson(wrongVersion));
        }
    }
}
