package org.xar.ck3.control.wave2.events.eventtraits;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection;
import org.xar.ck3.control.wave2.events.eventoutcome.EventOutcomeConsumerPort.EpisodeSource;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Available;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Frame;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Traits;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome.PlanInput;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome.PublicFrame;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome.Selection;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome.Status;

final class PoetTraitOutcomeTest {
    // Public/native deliberately differ, as they do on the real Driver chain.
    private static final PublicFrame START = frame("public:900", 900, 51, 53144520, 29829);
    private static final PublicFrame END = frame("public:902", 902, 53, 53144520, 29829);
    private static PublicFrame frame(String id, int revision, int nativeRevision, int date, int player) {
        return new PublicFrame(id, BigInteger.valueOf(revision), new Frame(BigInteger.valueOf(nativeRevision), date, player));
    }
    private static ScalarEventOutcome.Decision decision(int index) {
        return new ScalarEventOutcome.Decision("recommended", PoetTraitOutcome.EVENT, "1.20.0.4", BigInteger.valueOf(index + 1L), BigInteger.valueOf(index), null);
    }
    private static Available observed(PublicFrame frame, boolean poet, boolean journaller) { return new Available(frame.nativeFrame(), new Traits(poet, journaller)); }
    private static PlanInput input(int index) { return new PlanInput(decision(index), START, observed(START, false, false)); }
    private static Selection selection(boolean advanced, PublicFrame end, boolean poet, boolean journaller) {
        return new Selection(advanced, START, end, observed(START, false, false), observed(end, poet, journaller));
    }
    private static VanillaOptionProjection.Result projection(int index) {
        var binding = new VanillaOptionProjection.RegistryBinding(PoetTraitOutcome.EVENT, "1.20.0.4", EventTraitMembership.EXECUTABLE_SHA256,
            VanillaOptionProjection.RegistryState.AVAILABLE, List.of(new VanillaOptionProjection.SourceAnchor(PoetTraitOutcome.SOURCE_PATH,
                PoetTraitOutcome.SOURCE_SHA256, PoetTraitOutcome.SOURCE_SHA256)));
        var contract = new VanillaOptionProjection.OptionContract(3, List.of(0, 1, 2), index, index + 1, List.of(), List.of(3));
        return VanillaOptionProjection.project(new VanillaOptionProjection.Request(binding, contract, List.of(
            new VanillaOptionProjection.RenderedOption(0, 0, true, true, false, false),
            new VanillaOptionProjection.RenderedOption(1, 1, true, true, false, false),
            new VanillaOptionProjection.RenderedOption(2, 2, true, true, false, false)), 3));
    }

    @Test void bothPersistentTraitsUseTheirIndependentFactWithNullGenericProfile() {
        for (int index = 0; index <= 1; index++) {
            var expected = PoetTraitOutcome.plan(input(index)).orElseThrow();
            assertInstanceOf(PoetTraitOutcome.Ready.class, expected);
            var result = PoetTraitOutcome.evaluate(expected, selection(true, END, index == 0, index == 1));
            assertEquals(Status.VERIFIED_CHANGE, result.status()); assertEquals(1, result.delta());
            assertEquals(true, result.materialChangeObserved());
            var encoded = StrictJson.parse(PoetTraitOutcome.encode(result));
            assertEquals("false_to_true", encoded.get("expected_relation").textValue());
            assertFalse(encoded.get("starting_value").booleanValue()); assertTrue(encoded.get("ending_value").booleanValue());
            assertEquals(BigInteger.valueOf(51), encoded.get("starting_native_revision").bigIntegerValue());
            assertEquals(BigInteger.valueOf(900), encoded.get("starting_revision").bigIntegerValue());
            assertFalse(result.actionAuthorized()); assertFalse(result.replayAuthorized()); assertFalse(result.saveCreditGranted());
        }
    }

    @Test void windowDisappearanceAndAckCannotReplaceTraitChange() {
        var expected = PoetTraitOutcome.plan(input(1)).orElseThrow();
        assertEquals(Status.FAILED, PoetTraitOutcome.evaluate(expected, selection(true, END, false, false)).status());
        assertEquals(Status.FAILED, PoetTraitOutcome.evaluate(expected, selection(false, END, false, true)).status());
        EpisodeSource source = new EpisodeSource("fixture-machine", "fixture-episode", "fixture-generation", 17, PoetTraitOutcome.SOURCE_SHA256);
        var attached = PoetTraitOutcomeConsumerPort.attach(source, source, projection(1), input(1), true, selection(true, END, false, false));
        var evaluated = assertInstanceOf(PoetTraitOutcomeConsumerPort.Evaluated.class, attached);
        assertEquals(true, evaluated.submissionAckAccepted()); assertEquals(Status.FAILED, evaluated.materialResult().status());
        // Missing ACK is retained but independent material observations still decide their own result.
        var noAck = assertInstanceOf(PoetTraitOutcomeConsumerPort.Evaluated.class,
            PoetTraitOutcomeConsumerPort.attach(source, source, projection(1), input(1), null, selection(true, END, false, true)));
        assertNull(noAck.submissionAckAccepted()); assertEquals(Status.VERIFIED_CHANGE, noAck.materialResult().status());
    }

    @Test void newPublicFrameAloneOrCrossDatePlayerNativeFrameCannotVerify() {
        var expected = PoetTraitOutcome.plan(input(0)).orElseThrow();
        for (PublicFrame wrong : List.of(frame("public:902", 902, 51, 53144520, 29829),
                frame("public:900", 902, 53, 53144520, 29829), frame("public:902", 900, 53, 53144520, 29829),
                frame("public:902", 902, 53, 53144544, 29829), frame("public:902", 902, 53, 53144520, 29830))) {
            assertEquals(Status.FAILED, PoetTraitOutcome.evaluate(expected, selection(true, wrong, true, false)).status());
        }
        var missing = PoetTraitOutcome.evaluate(expected, new Selection(true, START, END, observed(START, false, false), null));
        assertEquals(Status.UNAVAILABLE, missing.status()); assertNull(missing.materialChangeObserved());
        assertTrue(StrictJson.parse(PoetTraitOutcome.encode(missing)).get("ending_value").isNull());
    }

    @Test void alreadyOwnedUnavailableAndUnsupportedRoutesStayDistinct() {
        var owned = PoetTraitOutcome.plan(new PlanInput(decision(0), START, observed(START, true, false))).orElseThrow();
        assertInstanceOf(PoetTraitOutcome.Unavailable.class, owned);
        assertEquals(Status.UNAVAILABLE, PoetTraitOutcome.evaluate(owned, selection(true, END, true, false)).status());
        assertInstanceOf(PoetTraitOutcome.Unavailable.class, PoetTraitOutcome.plan(new PlanInput(decision(1), START, null)).orElseThrow());
        assertTrue(PoetTraitOutcome.plan(input(2)).isEmpty());
        var oldBuild = new ScalarEventOutcome.Decision("recommended", PoetTraitOutcome.EVENT, "1.19.0.6", BigInteger.ONE, BigInteger.ZERO, null);
        assertTrue(PoetTraitOutcome.plan(new PlanInput(oldBuild, START, observed(START, false, false))).isEmpty());
    }

    @Test void sourceGenerationAndAuthoredNativeMappingRemainRequired() {
        EpisodeSource source = new EpisodeSource("fixture-machine", "fixture-episode", "fixture-generation", 17, PoetTraitOutcome.SOURCE_SHA256);
        EpisodeSource changed = new EpisodeSource("fixture-machine", "fixture-episode", "fixture-generation-2", 17, PoetTraitOutcome.SOURCE_SHA256);
        assertInstanceOf(PoetTraitOutcomeConsumerPort.Rejected.class,
            PoetTraitOutcomeConsumerPort.attach(source, changed, projection(0), input(0), true, selection(true, END, true, false)));
        assertInstanceOf(PoetTraitOutcomeConsumerPort.Rejected.class,
            PoetTraitOutcomeConsumerPort.attach(source, source, projection(1), input(0), true, selection(true, END, true, false)));
        EpisodeSource wrongSource = new EpisodeSource("fixture-machine", "fixture-episode", "fixture-generation", 17, "A".repeat(64));
        assertInstanceOf(PoetTraitOutcomeConsumerPort.Rejected.class,
            PoetTraitOutcomeConsumerPort.attach(wrongSource, wrongSource, projection(0), input(0), true, selection(true, END, true, false)));
    }
}
