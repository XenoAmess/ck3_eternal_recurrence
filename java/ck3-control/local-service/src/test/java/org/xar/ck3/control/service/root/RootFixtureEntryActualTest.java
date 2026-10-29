package org.xar.ck3.control.service.root;

import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterTransactionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Runs the same actual Root/registered workflow provider as the central fixture tests. No fabricated Managed or scope. */
public final class RootFixtureEntryActualTest {
    private static FixtureCompositeActualTest.Inputs actual()throws Exception {
        var producers=ServiceLoader.load(FixtureCompositeActualTest.InputsProducer.class).stream().toList();
        if(producers.size()!=1)throw new IllegalStateException("MISSING_ACTUAL_ROOT_FIXTURE_COMPOSITE_INPUTS_NOT_RUN: ENTRY_FULL_HISTORY");
        var input=producers.getFirst().get().open(FixtureCompositeActualTest.Scenario.COMPLETE);
        assertSame(input.catalog().context().writer(),input.menu().writer);
        assertSame(input.catalog().context().core().actions(),input.menu().coordinator);return input;
    }
    @Test void realStartupEventAndReadHistorySurviveEntryAndItsOriginalTransactionRoundTrip()throws Exception {
        var input=actual();var parent=input.menu().execute(input.parent());var context=input.catalog().context();
        var completed=assertInstanceOf(ActionState.FixtureBusinessCompleted.class,
                assertInstanceOf(ActionState.CompositeSettled.class,parent.state()).settlement()).observation();
        context.writer().locked(same->{
            var bound=context.archive().withSession(same);
            var children=ActionTransitions.composite(parent.state()).orElseThrow().children().stream()
                    .map(value->{try {return ContinuityActionJournal.lookup(same.head().state(),value.actionId(),bound).orElseThrow();}
                        catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}).toList();
            assertTrue(children.stream().anyMatch(value->value.command().origin() instanceof CommandOrigin.Gameplay),
                    "the actual COMPLETE fixture provider must exercise a real startup event child for this regression");
            var prepared=WriterTransactionCodec.decodePrepared(context.archive().readArtifact(same,completed.entryPrepared(),
                    WriterTransactionCodec.MAXIMUM_BYTES),context.source().machineId());
            var receipt=WriterTransactionCodec.decodeReceipt(context.archive().readArtifact(same,completed.entryReceipt(),
                    WriterTransactionCodec.MAXIMUM_BYTES),context.source().machineId());
            same.requireCommitted(prepared,receipt);
            context.frontend().entryAuthority().verifyFixtureEntry(same,completed);
            var before=prepared.predecessor().state().toJson();var after=prepared.reduced().toJson();
            assertEquals(before.get(WriterContracts.DRIVER_READ_HISTORY_FIELD),after.get(WriterContracts.DRIVER_READ_HISTORY_FIELD));
            assertEquals(before.get(WriterContracts.DRIVER_ACTION_HISTORY_FIELD),after.get(WriterContracts.DRIVER_ACTION_HISTORY_FIELD));
            var full=ExactRef.fromJson(prepared.request().detailsObject().get("full_driver"));
            assertEquals(full,ExactRef.fromJson(after.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)));
            var driver=DriverStateSnapshot.decodeComplete(context.archive().readArtifact(same,full,
                    org.xar.ck3.control.application.readiness.ReadinessArchive.Role.DRIVER.maximumBytes()));
            assertFalse(driver.commandHistory().isEmpty(),"startup's real original history must not be replaced by an empty Driver");
            assertArrayEquals(driver.encode(),DriverStateSnapshot.decodeComplete(driver.encode()).encode());
            assertArrayEquals(WriterTransactionCodec.encodePrepared(prepared),WriterTransactionCodec.encodePrepared(
                    WriterTransactionCodec.decodePrepared(WriterTransactionCodec.encodePrepared(prepared),context.source().machineId())));
            assertEquals(completed.evidence().originalStart(),children.stream().filter(value->value.command().actionId()
                    .equals(completed.evidence().originalStart().command().actionId())).findFirst().orElseThrow());
            return null;
        });
        assertFalse(parent.visibleGameplay());assertFalse(parent.eligibleAdvance());
    }
    @Test void actualScenarioActorPublicationAndNativeCampaignSemanticsSurviveTheTrueEntryHandoff()throws Exception {
        var input=actual();
        assertEquals(FixturePlan.Kind.SCENARIO,FixturePlan.requireParent(input.parent()).kind(),
                "this actual provider must exercise the original scenario actor-switch branch");
        var parent=input.menu().execute(input.parent());var context=input.catalog().context();
        var business=assertInstanceOf(ActionState.FixtureBusinessCompleted.class,
                assertInstanceOf(ActionState.CompositeSettled.class,parent.state()).settlement()).observation();
        var staged=context.frontend().initialDriver().current(business.evidence().originalStart().command().actionId());
        var first=staged.firstMapFrame();var finalFrame=staged.frame();var adopted=context.adopted();
        assertTrue(staged.fixtureRetired());assertSame(adopted.producer(),context.optionalDriverProducer().orElseThrow());
        assertNotEquals(first.identity().frame().identity().player(),finalFrame.identity().frame().identity().player());
        assertEquals(first.identity().frame().episodeRunId(),finalFrame.identity().frame().episodeRunId());
        var original=finalFrame.originalProjection().orElseThrow();
        org.xar.ck3.control.application.driver.NativeCampaignProjection.requireJoinedSnapshot(original,
                RawJson.fullMaterial(org.xar.ck3.control.application.driver.DriverJson.encode(finalFrame.semantic())));
        var next=assertInstanceOf(org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received.class,
                context.transport().readFreshFullState(input.deadline()));
        org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.verifyAfter(staged.latestFixtureRead().acknowledgement(),next);
        context.writer().locked(same->{
            staged.requireNativeCampaignObservationOwner(same,context.game(),context.source());
            var known=adopted.authority().withFrozenFacts(same,frozen->assertInstanceOf(
                    org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known.class,frozen.state()));
            assertTrue(org.xar.ck3.control.application.driver.InitialDriverState.fixtureActorPublicationReference(known).isPresent());
            var facts=assertInstanceOf(org.xar.ck3.control.application.driver.DriverObservationFacts.Known.class,
                    adopted.producer().read(next.originalFrame())).facts();
            assertTrue(facts.publicRevision().compareTo(original.facts().publicRevision())>=0);
            var packet=context.archive().withSession(same).preserveNativeFrame(next.originalFrame());
            var joined=assertInstanceOf(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete.class,
                    new org.xar.ck3.control.application.driver.DriverObservationAssembler().assemble(next.originalFrame(),facts,packet));
            org.xar.ck3.control.application.driver.NativeCampaignProjection.requireJoinedSnapshot(
                    joined.originalProjection().orElseThrow(),RawJson.fullMaterial(
                            org.xar.ck3.control.application.driver.DriverJson.encode(joined.semantic())));
            assertEquals(finalFrame.identity().frame().episodeRunId(),joined.identity().frame().episodeRunId());
            assertEquals(finalFrame.identity().frame().identity().player(),joined.identity().frame().identity().player());
            context.semanticVerifier().verify(same,new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(
                    context.game().machineId(),context.game().generation(),context.game().sessionId()),staged.semantic());
            return null;
        });
    }
    @Test void canonicalDataCannotReopenTheFixtureActionGuardAfterItsPrivateCallbackRetires()throws Exception {
        var input=actual();var parent=input.menu().execute(input.parent());var context=input.catalog().context();
        assertInstanceOf(ActionState.FixtureBusinessCompleted.class,assertInstanceOf(ActionState.CompositeSettled.class,parent.state()).settlement());
        assertThrows(IllegalStateException.class,RootFixtureQualifiedScope::required);
        context.writer().locked(same->{
            var archive=context.archive().withSession(same);var execution=ActionTransitions.composite(parent.state()).orElseThrow();
            new ActionChildPlanningScope.FixtureCursor(parent,execution,execution.children().stream()
                    .map(value->{try {return ContinuityActionJournal.lookup(same.head().state(),value.actionId(),archive).orElseThrow();}
                        catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}).toList());
            assertThrows(java.io.IOException.class,()->ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent.command(),execution.handlerId()));
            assertThrows(IllegalStateException.class,RootFixtureQualifiedScope::required);
            var wire=ActionReceiptCodec.encodeReceipt(parent,archive);
            assertEquals(parent,ActionReceiptCodec.decodeReceipt(wire,archive));return null;
        });
    }
}

