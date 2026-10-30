package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

/** Actual retained packets of the published-base Native GUI-only candidate; no live Game or full Bridge claim. */
final class EventWindowGuiNamedScopeProducerTest {
    private static Binding binding() { return new Binding(Build.CROZIER2,BigInteger.valueOf(17),741221,0x01000029); }
    private static RawJson original(String name)throws Exception {
        try(var input=EventWindowGuiNamedScopeProducerTest.class.getResourceAsStream("/event-gui-v2/"+name+".json")) {
            assertNotNull(input,"retained published-base Native packet is required");
            return new RawJson(input.readAllBytes());
        }
    }
    @Test void unresolvedNamedCharacterRemainsAnAvailableFrameWithUnavailableIdentityForBothVersions()throws Exception {
        for(int version:new int[]{1,2}) {
            RawJson packet=original("named-character-identity-unavailable.v"+version);
            Available context=assertInstanceOf(Available.class,EventWindowCodec.decode(packet,binding()));
            assertEquals(2,context.savedScopes().size());
            Scope named=context.savedScopes().getFirst().scope();
            assertEquals(4,named.rawTypeIndex()); assertEquals("character",named.typeKey()); assertEquals(2,named.subtype());
            UnavailableIdentity identity=assertInstanceOf(UnavailableIdentity.class,named.identity());
            assertEquals(IdentityReason.CHARACTER_SCOPE_IDENTITY_UNAVAILABLE,identity.reason());
            assertTrue(context.readiness().optionPresentation());
            Option option=context.firstDisplayed().orElseThrow(); assertTrue(option.enabled());
            assertEquals(5,option.indicators().size());
            if(version==1) assertInstanceOf(GuiAvailabilityObservation.LegacyNotReported.class,option.guiAvailability());
            else assertEquals(new GuiAvailabilityObservation.Observed(true),option.guiAvailability());
            assertArrayEquals(packet.bytes(),EventWindowCodec.encode(context).bytes());
        }
    }
    @Test void namedTokenDriftRetainsTheNativeUnavailableResultWithoutOptionsOrGuiObservation()throws Exception {
        RawJson packet=original("named-character-token-drift.v2");
        Unavailable context=assertInstanceOf(Unavailable.class,EventWindowCodec.decode(packet,binding()));
        assertEquals(1,context.windowMatchCount()); assertEquals("event_scope_changed",context.reason());
        assertFalse(context.readiness().optionPresentation()); assertFalse(context.readiness().savedScopes());
        var fields=EventWindowCodec.parse(EventWindowCodec.encode(context));
        assertTrue(fields.get("options").isNull()); assertTrue(fields.get("saved_scopes").isNull());
        assertArrayEquals(packet.bytes(),EventWindowCodec.encode(context).bytes());
    }
}
