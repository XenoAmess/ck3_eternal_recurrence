package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;

/** Actual registry identity to typed classification. These software handlers never prepare or observe a Game. */
final class RootAubControlClassificationTest {
    private static final ExactRef SOURCE = new ExactRef("software-aub-control-source", 1, "a".repeat(64));
    static RootExecutableBindings.ActionBinding action(String operation) {
        var effect = new NativeEffectRegistry.Binding(new OperationKey(operation), SOURCE,
                command -> { throw new AssertionError("metadata cannot prepare Native"); },
                (command, attempt, outcome) -> { throw new AssertionError("metadata cannot observe Native"); });
        return new RootExecutableBindings.ActionBinding(effect, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("software-capability"), SOURCE);
    }
    static RootExecutableBindings catalog(List<RootExecutableBindings.ActionBinding> actions) {
        var replays = actions.stream().map(action -> new NativeRecordedEvidenceVerifier.Binding(action.effect().operation(), SOURCE,
                (head, receipt, archive) -> { throw new AssertionError("metadata cannot verify actual archived Native evidence"); })).toList();
        var actual = RootExecutableBindings.freeze(actions, RootReadContractCatalog.staticOnly(List.of()), List.of(),
                replays, List.of(), List.of(), 8); actual.requireCompleteArchiveCoverage(); return actual;
    }
    @Test void onlyBothIdenticalInstalledAubHandlersReceiveTheSeparateControlKind() {
        var select = action(AubOperations.SELECT); var confirm = action(AubOperations.CONFIRM); var actual = catalog(List.of(select, confirm));
        for (String operation : List.of(AubOperations.SELECT, AubOperations.CONFIRM)) {
            var typed = assertInstanceOf(RootPlanningInputsFactory.SystemControl.class,
                    RootPlanningDomainCatalog.classifyAubControl(actual, select, confirm, new OperationKey(operation)).orElseThrow());
            assertEquals(RootPlanningInputsFactory.ControlKind.AUB_POLICY_CONTROL, typed.kind());
            assertNotEquals(RootPlanningInputsFactory.ControlKind.CHECKPOINT_SAVE, typed.kind());
        }
    }
    @Test void identicalOperationAndSourceCannotReplaceEitherInstalledHandler() {
        var select = action(AubOperations.SELECT); var confirm = action(AubOperations.CONFIRM); var actual = catalog(List.of(select, confirm));
        assertThrows(IllegalArgumentException.class, () -> RootPlanningDomainCatalog.classifyAubControl(actual,
                action(AubOperations.SELECT), confirm, new OperationKey(AubOperations.SELECT)));
        assertThrows(IllegalArgumentException.class, () -> RootPlanningDomainCatalog.classifyAubControl(actual,
                select, action(AubOperations.CONFIRM), new OperationKey(AubOperations.CONFIRM)));
        assertSame(select.effect(), actual.actualActionBinding(new OperationKey(AubOperations.SELECT)).orElseThrow());
        assertSame(confirm.effect(), actual.actualActionBinding(new OperationKey(AubOperations.CONFIRM)).orElseThrow());
    }
    @Test void partialPairAndSimilarLiteralsCannotGrantControlClassification() {
        var select = action(AubOperations.SELECT); var confirm = action(AubOperations.CONFIRM);
        assertThrows(IllegalArgumentException.class, () -> RootPlanningDomainCatalog.classifyAubControl(catalog(List.of(select)),
                select, confirm, new OperationKey(AubOperations.SELECT)));
        var actual = catalog(List.of(select, confirm));
        assertTrue(RootPlanningDomainCatalog.classifyAubControl(actual, select, confirm, new OperationKey(AubOperations.SELECT + "-copy")).isEmpty());
        assertTrue(RootPlanningDomainCatalog.classifyAubControl(actual, select, confirm, RootSaveRuntime.OPERATION).isEmpty());
    }
}
