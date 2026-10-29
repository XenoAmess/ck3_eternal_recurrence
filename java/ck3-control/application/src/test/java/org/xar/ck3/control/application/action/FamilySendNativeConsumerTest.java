package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.contracts.ExactRef;

/** Uses core's one DATA-only vector to exercise the actual registry refusal path. No source or writer authority is faked. */
final class FamilySendNativeConsumerTest {
    @Test void constructedSendDataCannotPassTheActualRegistryWithoutOriginalCustody() {
        var value=FamilySendCoreContractTest.vector();
        var projected=new NativeEffectRegistry.Projected(new ActionPorts.FamilySendObserved(value.observation()),Optional.empty());
        assertEquals(value.observation(),((ActionPorts.FamilySendObserved)projected.result()).observation());
        var source=new ExactRef("D:/family-send-data/negative-only-handler-source",1,"a".repeat(64));
        var binding=new NativeEffectRegistry.Binding(value.command().operation(),source,
                command->value.attempt().preparedRequest(),(command,attempt,dispatch)->projected);
        var registry=new NativeEffectRegistry(List.of(binding),1);
        assertThrows(IllegalArgumentException.class,()->registry.observe(value.command(),value.attempt(),value.dispatch()),
                "actual registry must invoke the dispatch-aware shared validation before retaining any result");
        assertTrue(registry.compatibleResult(value.command().actionId(),value.attempt().requestId()).isEmpty());
    }

    @Test void missingActualObserverStaysPendingAndFamilySendCannotAdvertiseLegacyBusinessSuccess() {
        var value=FamilySendCoreContractTest.vector();
        var registry=new NativeEffectRegistry(List.of(),1);
        assertInstanceOf(ActionPorts.Pending.class,registry.observe(value.command(),value.attempt(),value.dispatch()));
        assertThrows(IllegalArgumentException.class,()->new NativeEffectRegistry.Projected(
                new ActionPorts.FamilySendObserved(value.observation()),Optional.of(new RawJson(new byte[]{'{','}'}))));
        assertTrue(registry.compatibleResult(value.command().actionId(),value.attempt().requestId()).isEmpty());
    }
}
