package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.contracts.ExactRef;

/** Descriptor/registration contract tests only. No constructor or metadata selection is native authority. */
final class OriginAwareBindingsTest {
    private static final ExactRef SOURCE = new ExactRef("D:/descriptor-fixture/source.java", 1, "a".repeat(64));
    private static final ExactRef OTHER = new ExactRef("D:/descriptor-fixture/other.java", 1, "b".repeat(64));
    private static final OperationKey READ = new OperationKey("inspect-gui-window-tree-v1");
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static ReadContract<PlanningReadReceipt> read(String id, ReadContract.GuardMode mode, ExactRef source) {
        return new ReadContract<>(id, READ, Optional.of("game.command.inspect-gui-window-tree-v1"), "descriptor-contract-only",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, mode, source,
                request -> new NativeRequest(READ.value(), "game.command.inspect-gui-window-tree-v1", raw("{}")), receipt -> receipt);
    }
    @Test void actualCatalogKeepsTwoTypedReadIdentitiesAndOriginSelectionCannotPickFirst() {
        var gameplay = read("descriptor:gameplay", ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, SOURCE);
        var frontend = read("descriptor:frontend", ReadContract.GuardMode.FRONTEND_SESSION, OTHER);
        var reads = RootReadContractCatalog.staticOnly(List.of(gameplay, frontend));
        var actual = RootExecutableBindings.freeze(List.of(), reads, List.of(), 4);
        assertTrue(reads.containsIdentity(gameplay)); assertTrue(reads.containsIdentity(frontend));
        assertEquals(SOURCE, actual.resolve(READ, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).orElseThrow().implementationSource());
        assertEquals(OTHER, actual.resolve(READ, ReadContract.GuardMode.FRONTEND_SESSION).orElseThrow().implementationSource());
        assertTrue(actual.resolve(READ, ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION).isEmpty());
        assertTrue(actual.resolve(READ, ReadContract.GuardMode.RECONCILIATION_OBSERVATION).isEmpty());
        assertThrows(IllegalArgumentException.class, () -> actual.resolve(READ));
        assertThrows(IllegalArgumentException.class, () -> actual.containsExact(READ));
        assertTrue(actual.effects().installed().isEmpty()); assertTrue(actual.archivedBindings().isEmpty());
    }
    @Test void identicalReadDescriptorsCoalesceButConflictingSameOriginDefinitionsDoNot() {
        var first = read("descriptor:first", ReadContract.GuardMode.FRONTEND_SESSION, SOURCE);
        var second = read("descriptor:second", ReadContract.GuardMode.FRONTEND_SESSION, SOURCE);
        var equivalent = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of(first, second)), List.of(), 4);
        assertEquals(SOURCE, equivalent.resolve(READ).orElseThrow().implementationSource());
        var other = read("descriptor:other", ReadContract.GuardMode.FRONTEND_SESSION, OTHER);
        var conflict = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of(first, other)), List.of(), 4);
        assertThrows(IllegalArgumentException.class, () -> conflict.resolve(READ, ReadContract.GuardMode.FRONTEND_SESSION));
        assertThrows(IllegalArgumentException.class, () -> conflict.resolve(READ));
    }
    @Test void oldSingleModeActionDoesNotAcquireSuccessionGameplayOrAnyReadOnlyOrigin() {
        var operation = new OperationKey("continue-death-succession-modal-v1");
        var effect = new NativeEffectRegistry.Binding(operation, SOURCE,
                command -> { throw new AssertionError("descriptor test cannot prepare a native request"); },
                (command, attempt, outcome) -> { throw new AssertionError("descriptor test cannot observe business success"); });
        var binding = new RootExecutableBindings.ActionBinding(effect, ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, Optional.empty(), SOURCE);
        var actual = RootExecutableBindings.freeze(List.of(binding), RootReadContractCatalog.staticOnly(List.of()), List.of(), 4);
        assertEquals(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, actual.resolve(operation).orElseThrow().guardMode());
        assertTrue(actual.resolve(operation, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).isEmpty());
        assertTrue(actual.resolve(operation, ReadContract.GuardMode.FRONTEND_SESSION).isEmpty());
        assertTrue(actual.resolve(operation, ReadContract.GuardMode.RECONCILIATION_OBSERVATION).isEmpty());
        assertSame(effect, actual.actualActionBinding(operation).orElseThrow());
        assertThrows(IllegalArgumentException.class, actual::requireCompleteArchiveCoverage);
    }
    @Test void unrelatedOrDetachedPreparationCannotInstallTheFiniteSuccessionProofSeam() {
        RootExecutableBindings.SuccessionUiOriginProof detached = new RootExecutableBindings.SuccessionUiOriginProof() {
            @Override public ExactRef successionUiDefinitionSource() { return SOURCE; }
            @Override public NativeRequest prepare(ActionCommand command) { throw new AssertionError("no actual source-owned provider"); }
            @Override public void requireSuccessionOrigin(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, ActionCommand command) {
                throw new AssertionError("registration rejection must happen before qualification");
            }
        };
        var effect = new NativeEffectRegistry.Binding(new OperationKey("continue-death-succession-modal-v1"), SOURCE,
                command -> { throw new AssertionError("no preparation"); }, (command, attempt, outcome) -> { throw new AssertionError("no observation"); });
        assertThrows(IllegalArgumentException.class, () -> new RootExecutableBindings.ActionBinding(effect,
                ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, Optional.empty(), SOURCE, Optional.of(detached)));
        var wrongOperation = new NativeEffectRegistry.Binding(new OperationKey("unrelated-native-action-v1"), SOURCE,
                detached, (command, attempt, outcome) -> { throw new AssertionError("no observation"); });
        assertThrows(IllegalArgumentException.class, () -> new RootExecutableBindings.ActionBinding(wrongOperation,
                ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, Optional.empty(), SOURCE, Optional.of(detached)));
        var sameProducer = new NativeEffectRegistry.Binding(effect.operation(), SOURCE, detached,
                (command, attempt, outcome) -> { throw new AssertionError("no observation"); });
        assertThrows(IllegalArgumentException.class, () -> new RootExecutableBindings.ActionBinding(sameProducer,
                ReadContract.GuardMode.FRONTEND_SESSION, Optional.empty(), SOURCE, Optional.of(detached)));
    }
}
