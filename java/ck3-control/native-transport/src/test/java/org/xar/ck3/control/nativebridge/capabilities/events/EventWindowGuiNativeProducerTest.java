package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

/** Retained outputs of the owned Native software fixture, with no live Game or complete Bridge claim. */
final class EventWindowGuiNativeProducerTest {
    private static final List<String> CASES=List.of("timer-equal-raw-enabled","callback-false-raw-enabled",
            "gate-passes-control","raw-disabled-fallback-valid","native-binding-unavailable","native-read-unavailable");
    private static Binding binding() { return new Binding(Build.CROZIER2,BigInteger.valueOf(17),741221,0x01000029); }
    private static RawJson original(String name,int version)throws Exception {
        try(var input=EventWindowGuiNativeProducerTest.class.getResourceAsStream("/event-gui-v2/"+name+".v"+version+".json")) {
            assertNotNull(input,"retained exact Native serializer resource is required");
            return new RawJson(input.readAllBytes());
        }
    }
    private static Available decode(RawJson original) { return assertInstanceOf(Available.class,EventWindowCodec.decode(original,binding())); }

    @Test void actualNativeV1PayloadsKeepRawFlagsAndDoNotInventAnObservation()throws Exception {
        for(String name:CASES) {
            RawJson original=original(name,1);
            Available context=decode(original); Option option=context.firstDisplayed().orElseThrow();
            assertInstanceOf(GuiAvailabilityObservation.LegacyNotReported.class,option.guiAvailability());
            assertEquals(option.enabled(),option.selectionAllowed(),name);
            assertArrayEquals(original.bytes(),EventWindowCodec.encode(context).bytes(),name);
        }
    }
    @Test void actualNativeV2PayloadsRetainIndependentValidityAndUnknownReasons()throws Exception {
        for(String name:CASES) {
            RawJson original=original(name,2);
            Available context=decode(original); Option option=context.firstDisplayed().orElseThrow();
            Option legacy=decode(original(name,1)).firstDisplayed().orElseThrow();
            assertEquals(legacy.enabled(),option.enabled(),name);
            assertEquals(legacy.fallback(),option.fallback(),name);
            assertEquals(legacy.nativeOptionIndex(),option.nativeOptionIndex(),name);
            if(name.startsWith("native-")) {
                GuiAvailabilityObservation.Unobserved observation=assertInstanceOf(GuiAvailabilityObservation.Unobserved.class,option.guiAvailability());
                assertEquals(name.equals("native-binding-unavailable")?GuiAvailabilityObservation.Reason.NATIVE_BINDING_UNAVAILABLE:
                    GuiAvailabilityObservation.Reason.NATIVE_READ_UNAVAILABLE,observation.reason());
                assertEquals(option.enabled(),option.selectionAllowed(),name);
            } else {
                boolean expected=name.equals("gate-passes-control")||name.equals("raw-disabled-fallback-valid");
                assertEquals(new GuiAvailabilityObservation.Observed(expected),option.guiAvailability(),name);
                assertEquals(expected,option.selectionAllowed(),name);
                if(name.equals("raw-disabled-fallback-valid")) {
                    assertFalse(option.enabled()); assertTrue(option.fallback()); assertTrue(option.selectionAllowed());
                }
            }
            assertArrayEquals(original.bytes(),EventWindowCodec.encode(context).bytes(),name);
            assertEquals(context,EventWindowCodec.decode(EventWindowCodec.encode(context),binding()),name);
        }
    }
    @Test void ambiguousNativeV2RemainsUnavailableWithoutOptionsOrReadiness()throws Exception {
        RawJson original=original("ambiguous-no-native-gate",2);
        Unavailable context=assertInstanceOf(Unavailable.class,EventWindowCodec.decode(original,binding()));
        assertEquals(2,context.windowMatchCount());
        assertEquals("event_window_ambiguous",context.reason());
        assertFalse(context.readiness().optionPresentation());
        assertFalse(context.readiness().semanticDecision());
        assertArrayEquals(original.bytes(),EventWindowCodec.encode(context).bytes());
    }
}
