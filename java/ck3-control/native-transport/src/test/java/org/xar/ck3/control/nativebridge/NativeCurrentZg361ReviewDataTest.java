package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** New review Java DATA only. No C++ frame, actual requirements or live four-line UI proof is invented. */
final class NativeCurrentZg361ReviewDataTest {
    private static CurrentZg361Ae2Source source(CurrentZg361Ae2Source.Review review) {
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.REVIEW,Optional.empty(),Optional.empty(),Optional.of(review));
    }
    private static CurrentZg361Ae2Source.Review complete(String description, boolean hasRequirements) {
        // Actual complete DATA is not gated on detailEnabled/resident/list visibility/modal or HasRequirements=true.
        return new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,false,false,true,false,true,true,true,true,
                true,false,true,Optional.of(CurrentZg361Ae2.REVIEW_DEFINITION),Optional.of(hasRequirements),Optional.of(description));
    }
    private static CoreFrame.Partial core() {
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(0,3,true,0,true,true,-2,true));
    }
    private static CurrentLetterResult.OwnerWitness owner() {
        return new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4);
    }

    @Test void completeFalseHasRequirementsAndEmptyOrFullUnicodeDescriptionAreActualData() throws Exception {
        String utf8Limit = "\uD83D\uDE00".repeat(4096);
        for (String description : List.of("","#P exact\0rich#!\r\n\t\u0001",utf8Limit)) {
            var review = complete(description,false); var original = source(review);
            assertFalse(review.detailEnabled()); assertEquals(Optional.of(false),review.hasRequirements());
            assertEquals(Optional.of(description),review.requirementsDescription()); assertTrue(review.requirementsComplete());
            assertEquals(3,StrictJson.object(original.encode(),Set.of("schema","kind","review")).size());
            assertEquals(15,original.encode().get("review").size());
            assertEquals(original,CurrentZg361Ae2Source.decode(original.encode()));
            assertTrue(original.actionAdmissible(CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS));
            assertFalse(original.actionAdmissible(CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL));
        }
        assertThrows(IllegalArgumentException.class,()->complete(utf8Limit+"x",false));
        assertThrows(IllegalArgumentException.class,()->complete("\uD800",true));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,
                true,false,true,false,true,true,false,true,true,false,false,Optional.of(CurrentZg361Ae2.REVIEW_DEFINITION),Optional.of(false),Optional.empty()));
    }

    @Test void fixedTargetIsNotActualSelectionAndOldThreeArgumentUnionKeepsExactlyFourKeys() throws Exception {
        var wrongSelected = new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,true,true,true,false,true,true,false,true,
                false,true,false,Optional.of("actual_other_decision"),Optional.empty(),Optional.empty());
        assertTrue(wrongSelected.openDetailAdmissible()); assertFalse(wrongSelected.selectedReview());
        assertEquals(Optional.of("actual_other_decision"),wrongSelected.selectedDefinitionKey());
        assertEquals(source(wrongSelected),CurrentZg361Ae2Source.decode(source(wrongSelected).encode()));
        var hiddenFixed = new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,false,false,false,false,false,false,false,false,
                false,false,false,Optional.of(CurrentZg361Ae2.REVIEW_DEFINITION),Optional.empty(),Optional.empty());
        assertFalse(hiddenFixed.selectedReview());
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,
                true,true,true,true,true,true,false,true,true,false,false,Optional.of("actual_other_decision"),Optional.empty(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Review("wrong_fixed_target",false,false,false,false,false,false,
                false,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty()));
        var controls = new CurrentZg361Ae2Source.Controls(false,false,false,false,false,false,false,Optional.empty(),List.of());
        var old = new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.CONTROLS,Optional.of(controls),Optional.empty());
        assertEquals(4,old.encode().size()); assertFalse(old.encode().has("review")); assertTrue(old.review().isEmpty());
        assertEquals(old,CurrentZg361Ae2Source.decode(old.encode()));
        var extraReview = old.encode(); extraReview.putNull("review");
        assertThrows(IOException.class,()->CurrentZg361Ae2Source.decode(extraReview));
        var mixed = source(complete("",false)).encode(); mixed.putNull("controls"); mixed.putNull("events");
        assertThrows(IOException.class,()->CurrentZg361Ae2Source.decode(mixed));
        assertEquals(2,CurrentZg361Ae2Source.Control.values().length);
        assertThrows(IOException.class,()->CurrentZg361Ae2Source.Control.parse("review"));
    }

    @Test void appendedActionsUseOnlyTheirOwnCapabilitiesAndOriginalTwentyFieldBeforeSourceResult() throws Exception {
        assertEquals(8,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS.ordinal());
        assertEquals(9,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL.ordinal());
        for (var action : List.of(CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL)) {
            BigInteger generation = action.queryOnly()?BigInteger.ZERO:NativeWire.UINT64_MAX;
            var request = CurrentZg361Ae2.request(core(),action,generation,generation);
            assertEquals(action.queryOnly()?CurrentZg361Ae2.REVIEW_QUERY_CAPABILITY:CurrentZg361Ae2.REVIEW_DETAIL_CAPABILITY,
                    request.requiredCapability().orElseThrow());
            var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","zg361_ae2"));
            assertEquals(action.wire(),fields.get("zg361_ae2").get("action").textValue());
            assertEquals(generation.toString(),fields.get("zg361_ae2").get("provider_generation").textValue());
            assertEquals(9,fields.get("zg361_ae2").size());
        }
        var before = source(new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,true,true,false,false,true,true,false,true,
                false,true,false,Optional.empty(),Optional.empty(),Optional.empty()));
        var dispatch = new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL,CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,
                true,true,true,BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),Optional.of(core().prefix()),Optional.of(owner()),
                Optional.of(before),Optional.empty());
        assertEquals(dispatch,CurrentZg361Ae2Result.decode(dispatch.encode()));
        assertEquals(20,NativeWire.parse(dispatch.encode().bytes()).size()); assertFalse(dispatch.nativeHandled());
        assertFalse(dispatch.source().orElseThrow().review().orElseThrow().detailVisible()); // Original beforeSource, not opened poststate.
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.CONFIRM_PRESENT,
                CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED,true,true,true,BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),
                Optional.of(core().prefix()),Optional.of(owner()),Optional.of(before),Optional.empty()));
        var available = new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,CurrentZg361Ae2Result.Status.AVAILABLE,
                false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,Optional.of(core().prefix()),Optional.of(owner()),
                Optional.of(source(complete("",false))),Optional.empty());
        assertEquals(available,CurrentZg361Ae2Result.decode(available.encode()));
        assertEquals(Optional.of(false),available.source().orElseThrow().review().orElseThrow().hasRequirements());
    }
}
