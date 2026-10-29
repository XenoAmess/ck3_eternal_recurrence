package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.CampaignEvidence;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Consumption;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Gate;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NamedGainEvidence;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NamedValue;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Stamp;
import org.xar.ck3.control.g2.m6.G2M6Contracts.StartEvidence;
import org.xar.ck3.control.g2.m6.G2M6Contracts.StartOrigin;
import org.xar.ck3.control.g2.m6.G2M6Contracts.TerminalCause;
import org.xar.ck3.control.g2.m6.G2M6Contracts.TerminalEvidence;

/** Synthetic evidence-contract checks. These fixtures confer no original SDK, natural-game or milestone qualification. */
final class M6ResearchTest {
    private static final M6Research DOMAIN = new M6Research();
    private static final ProjectionJson EMPTY = json("{}");
    private static final Identity IDENTITY = new Identity("synthetic-sway-action",31254,33946,2,0);

    private static ProjectionJson json(String value) {
        return ProjectionJson.object(value.getBytes(StandardCharsets.UTF_8),StrictJson.INPUT_MAX_BYTES);
    }
    private static Stamp stamp(int revision) { return new Stamp(BigInteger.valueOf(revision),53144328+24*revision); }
    private static Consumption consumed(int revision) { return new Consumption(true,Optional.of(stamp(revision))); }
    private static NamedValue absent() { return new NamedValue(true,false,Optional.empty()); }
    private static NamedValue present(int value) { return new NamedValue(true,true,Optional.of(BigInteger.valueOf(value))); }
    private static StartEvidence start(StartOrigin origin) {
        return new StartEvidence(stamp(1),stamp(2),true,origin,consumed(3));
    }
    private static NamedGainEvidence gain(NamedValue before, NamedValue after, boolean incremental, boolean active) {
        return new NamedGainEvidence(stamp(4),before,stamp(5),after,incremental,active,consumed(6));
    }
    private static TerminalEvidence terminal(TerminalCause cause, boolean natural, boolean observed, Consumption consumption) {
        return new TerminalEvidence(stamp(7),natural,observed,cause,cause==TerminalCause.AUTHORED_SWAY_COMPLETE_100,consumption);
    }
    private static Episode episode(StartEvidence start, NamedGainEvidence gain, TerminalEvidence terminal) {
        return new Episode(IDENTITY,Optional.ofNullable(start),Optional.ofNullable(gain),Optional.ofNullable(terminal),EMPTY);
    }
    private static Episode complete(TerminalCause cause) {
        return episode(start(StartOrigin.ORDINARY_FULL_PLANNER),gain(absent(),present(25),true,true),
                terminal(cause,true,true,consumed(8)));
    }
    private static CampaignEvidence campaign(List<Episode> episodes) {
        return new CampaignEvidence(new G2Source("synthetic-test-machine","2026-10-23T00:00:00Z","1.20.0.4",
                new ExactRef("D:/synthetic-m6/closed-ledger.json",2,"a".repeat(64))),episodes,EMPTY);
    }

    @Test void neutralNaturalRetainedEndPreparesPacketWithoutInventingSuccessCause() {
        var result = DOMAIN.evaluateEpisode(complete(TerminalCause.TERMINATED_UNATTRIBUTED));
        assertTrue(result.evidencePacketReady()); assertFalse(result.usefulSchemeComplete());
        assertTrue(result.missing().isEmpty());
    }

    @Test void attributedChainStillCannotCompleteTheOtherThreeM6LifecyclesOrGrantSubmission() {
        var result = DOMAIN.evaluateCampaign(campaign(List.of(complete(TerminalCause.AUTHORED_SWAY_COMPLETE_100))));
        assertTrue(result.evidencePacketReady()); assertTrue(result.schemeComplete());
        assertFalse(result.wholeM6Complete()); assertFalse(result.grantsSubmissionAuthority());
        var wire = StrictJson.parse(DOMAIN.toJson(result).bytes());
        assertEquals("in_progress",wire.get("milestone_status").textValue());
        assertFalse(wire.get("whole_m6_complete").booleanValue()); assertFalse(wire.get("grants_submission_authority").booleanValue());
        assertEquals(0,wire.get("game_day_credit").intValue()); assertEquals(0,wire.get("ordinary_cycle_credit").intValue());
    }

    @Test void positiveNamedGainAndCanContinueDiagnosticsCannotStandInForTerminal() {
        Episode withoutTerminal = episode(start(StartOrigin.ORDINARY_FULL_PLANNER),gain(absent(),present(25),true,true),null);
        var result = DOMAIN.evaluateEpisode(withoutTerminal);
        assertTrue(result.satisfied().contains(Gate.INCREMENTAL_NAMED_GAIN));
        assertFalse(result.evidencePacketReady()); assertFalse(result.usefulSchemeComplete());
        assertTrue(result.missing().contains(Gate.NATURAL_RETAINED_TERMINAL));
    }

    @Test void persistentPositiveModifierAndTotalOpinionCannotBeRecountedAsANewNamedGain() {
        Episode persistent = episode(start(StartOrigin.ORDINARY_FULL_PLANNER),gain(present(25),present(25),true,true),
                terminal(TerminalCause.TERMINATED_UNATTRIBUTED,true,true,consumed(8)));
        assertTrue(DOMAIN.evaluateEpisode(persistent).missing().contains(Gate.INCREMENTAL_NAMED_GAIN));
        Episode opinionOnly = new Episode(IDENTITY,Optional.of(start(StartOrigin.ORDINARY_FULL_PLANNER)),Optional.empty(),
                Optional.of(terminal(TerminalCause.TERMINATED_UNATTRIBUTED,true,true,consumed(8))),
                json("{\"target_opinion_of_actor\":100,\"CanContinue\":true}"));
        assertTrue(DOMAIN.evaluateEpisode(opinionOnly).missing().contains(Gate.INCREMENTAL_NAMED_GAIN));
    }

    @Test void unreadBaselineAndInactiveMaterialDoNotProvideAnEarlyActiveBaseline() {
        NamedValue unread = new NamedValue(false,false,Optional.empty());
        for (NamedGainEvidence material : List.of(gain(unread,present(25),true,true),gain(absent(),present(25),true,false))) {
            var result = DOMAIN.evaluateEpisode(episode(start(StartOrigin.ORDINARY_FULL_PLANNER),material,
                    terminal(TerminalCause.TERMINATED_UNATTRIBUTED,true,true,consumed(8))));
            assertTrue(result.missing().contains(Gate.EARLY_NAMED_BASELINE)); assertFalse(result.evidencePacketReady());
        }
    }

    @Test void manualUnknownAndRecoveredStartIdentityNeverBecomeAnOrdinaryStart() {
        for (StartOrigin origin : List.of(StartOrigin.EXPLICIT_TARGET,StartOrigin.RECOVERED_IDENTITY_ONLY,StartOrigin.UNKNOWN)) {
            var result = DOMAIN.evaluateEpisode(episode(start(origin),gain(absent(),present(25),true,true),
                    terminal(TerminalCause.TERMINATED_UNATTRIBUTED,true,true,consumed(8))));
            assertTrue(result.missing().contains(Gate.ORDINARY_START)); assertFalse(result.evidencePacketReady());
        }
    }

    @Test void missingInstanceAndReusedStorageDoNotCreateAnObservedTerminal() {
        var result = DOMAIN.evaluateEpisode(episode(start(StartOrigin.ORDINARY_FULL_PLANNER),gain(absent(),present(25),true,true),
                terminal(TerminalCause.UNKNOWN,true,false,consumed(8))));
        assertTrue(result.missing().contains(Gate.NATURAL_RETAINED_TERMINAL)); assertFalse(result.evidencePacketReady());
    }

    @Test void typedStopOrNonNaturalEndCannotPrepareTheNaturalPacket() {
        var result = DOMAIN.evaluateEpisode(episode(start(StartOrigin.ORDINARY_FULL_PLANNER),gain(absent(),present(25),true,true),
                terminal(TerminalCause.AUTHORED_SWAY_COMPLETE_100,false,true,consumed(8))));
        assertTrue(result.missing().contains(Gate.NATURAL_RETAINED_TERMINAL)); assertFalse(result.usefulSchemeComplete());
    }

    @Test void olderConsumedStampSurvivesRefreshWithoutQualifyingTheNewTerminal() {
        Consumption retainedOldConsumption = consumed(6);
        TerminalEvidence refreshed = terminal(TerminalCause.TERMINATED_UNATTRIBUTED,true,true,retainedOldConsumption);
        var result = DOMAIN.evaluateEpisode(episode(start(StartOrigin.ORDINARY_FULL_PLANNER),gain(absent(),present(25),true,true),refreshed));
        assertTrue(refreshed.consumption().nextTurnConsumed());
        assertEquals(stamp(6),refreshed.consumption().following().orElseThrow());
        assertTrue(result.missing().contains(Gate.LATER_ORDINARY_CONSUMPTION)); assertFalse(result.evidencePacketReady());
    }

    @Test void retainedArchivedEpisodeIsNotReboundToTheCurrentRulerOrCountedTwice() {
        Episode old = complete(TerminalCause.TERMINATED_UNATTRIBUTED);
        Identity newRuler = new Identity("synthetic-successor-action",40526,34973,83887164,5);
        Episode current = new Episode(newRuler,Optional.empty(),Optional.empty(),Optional.empty(),EMPTY);
        var result = DOMAIN.evaluateCampaign(campaign(List.of(current,old)));
        assertEquals(2,result.episodes().size()); assertTrue(result.episodes().get(1).evidencePacketReady());
        assertEquals(31254,result.episodes().get(1).identity().actorCharacterId());
        assertEquals(40526,result.episodes().getFirst().identity().actorCharacterId());
        assertThrows(ContractViolationException.class,() -> campaign(List.of(old,old)));
    }

    @Test void generationZeroAndExactHighNativeRevisionRemainValidWhileMismatchesReject() {
        assertEquals(0,IDENTITY.schemeInstanceGeneration());
        BigInteger large = new BigInteger("18446744073709551615");
        assertEquals(large,new Stamp(large,53144328).nativeRevision());
        assertThrows(ContractViolationException.class,() -> new Identity("bad",31254,33946,2,1));
        assertEquals(0,new Identity("zero-instance",31254,33946,0,0).schemeInstanceId());
        assertThrows(ContractViolationException.class,() -> new Identity("bad",31254,33946,-1,0));
        assertThrows(ContractViolationException.class,() -> new Stamp(large.add(BigInteger.ONE),53144328));
        assertThrows(ContractViolationException.class,() -> new TerminalEvidence(stamp(7),true,true,
                TerminalCause.TERMINATED_UNATTRIBUTED,true,consumed(8)));
    }
}

