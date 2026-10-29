package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;

final class NativeEffectRegistryTest {
    private static final ExactRef SOURCE = new ExactRef("software-fixture:verifier", 1, "a".repeat(64));
    @Test void exactRegistrationRejectsTwoOwnersAndDoesNotGrantPrefixes() {
        var operation = new OperationKey("save-checkpoint");
        var binding = NativeEffectRegistry.Binding.existing(operation, SOURCE, command -> { throw new UnsupportedOperationException(); },
                (command, attempt, dispatch) -> new ActionPorts.Pending("fixture unavailable", List.of()));
        assertThrows(IllegalArgumentException.class, () -> new NativeEffectRegistry(List.of(binding, binding), 8));
        var registry = new NativeEffectRegistry(List.of(binding), 8);
        assertTrue(registry.supports(operation)); assertFalse(registry.supports(new OperationKey("save-checkpoint-other")));
        assertTrue(registry.compatibleResult("unseen", "unseen").isEmpty());
    }
    @Test void pendingCannotBecomeSuccessfulHistoryAndRegistryCannotSubmit() {
        assertThrows(IllegalArgumentException.class, () -> new NativeEffectRegistry.Projected(new ActionPorts.Pending("actual effect missing", List.of()),
                Optional.of(new RawJson("{\"accepted\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)))));
        assertFalse(java.util.Arrays.stream(NativeEffectRegistry.class.getMethods()).anyMatch(method -> method.getName().equals("submit")));
    }
    @Test void nativeOperationIdsRejectAliasesOverflowAndUnrelatedNames() {
        assertEquals(17L, NativeWarExitEffects.warId(new OperationKey("offer-white-peace-17")));
        assertEquals(0L, NativeWarExitEffects.warId(new OperationKey("enforce-demands-0")));
        assertEquals(9007199254740991L, NativeWarExitEffects.warId(new OperationKey("enforce-demands-9007199254740991")));
        assertThrows(IllegalArgumentException.class, () -> NativeWarExitEffects.warId(new OperationKey("offer-white-peace-017")));
        assertThrows(IllegalArgumentException.class, () -> NativeWarExitEffects.warId(new OperationKey("surrender-war-9999999999")));
        assertThrows(IllegalArgumentException.class, () -> NativeArmyMoveEffects.parse(new OperationKey("preview-move-army-1-to-2")));
    }
}

