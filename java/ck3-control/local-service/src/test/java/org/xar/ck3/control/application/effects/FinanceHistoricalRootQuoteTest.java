package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual central read -> sole canonical READ writer -> actual later market guard -> quote historical qualification.
 * This tests read evidence, not full finance affordability, native spending, a private Root Ready or live gameplay. */
final class FinanceHistoricalRootQuoteTest {
    @TempDir Path directory;
    private record Target(PlanningReadReceipt market,FinanceEvidenceArchive.HistoricalTarget actual) { }
    @Test void canonicalOldRootCanReachTheActualQuoteTargetAndReplayAfterAnOutsideIntent()throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("historical-finance-root"),false,scenario(definitions,source))) {
            var publisher=publisher(fixture,source.get());var root=new AtomicReference<PlanningReadReceipt>();var target=new AtomicReference<Target>();
            var initial=fixture.ready();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    root.set(known(definitions.get().read(same,FinanceReadContracts.Query.ROOT,fixture.reads,planning(lease.frame()))).receipt());return null;
                });
                publisher.flushActualReads(same).orElseThrow();
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var market=known(definitions.get().read(same,FinanceReadContracts.Query.MERCENARIES,fixture.reads,planning(lease.frame()))).receipt();
                    var archive=archive(fixture,same,definitions.get(),source.get(),publisher);
                    var actual=archive.quoteTarget(List.of(root.get(),market),lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),fixture.archive.withSession(same));
                    target.set(new Target(market,actual));
                    assertTrue(root.get().request().before().frame().revision().compareTo(lease.frame().identity().frame().revision())<0);
                    assertComplete(lease.frame(),archive.verifyRead(root.get(),lease.frame().identity(),
                            lease.frame().source(),lease.frame().sessionId(),fixture.archive.withSession(same),Optional.of(actual)));
                    assertEquals(root.get(),fixture.archive.withSession(same).loadRead(fixture.archive.withSession(same).readReferenceOf(root.get())));
                    return null;
                });return null;
            });
            // A real independent canonical action adds an INTENT outside the historical quote interval.
            // Its result is not credited as a Gift, payment or game advance.
            fixture.coordinator.execute(fixture.command("outside-old-finance-quote"));
            fixture.writer.locked(same->{
                var old=target.get().actual();assertTrue(same.head().state().sequence()>RootGuardEvidence.writerPoint(old.guard(),fixture.archive.withSession(same)).sequence());
                var replay=archive(fixture,same,definitions.get(),source.get(),publisher).verifyRead(root.get(),old.frame().identity(),old.frame().source(),
                        old.frame().sessionId(),fixture.archive.withSession(same),Optional.of(old));
                assertComplete(old.frame(),replay);assertEquals(1,fixture.nativeActionWrites());return null;
            });
        }
    }
    @Test void sameNativeShapeCannotReplaceTheActualMarketGuardAndInternalRootCannotAuthorizeQuote()throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("historical-finance-rejection"),false,scenario(definitions,source))) {
            var publisher=publisher(fixture,source.get());var root=new AtomicReference<PlanningReadReceipt>();var initial=fixture.ready();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    root.set(known(definitions.get().read(same,FinanceReadContracts.Query.ROOT,fixture.reads,planning(lease.frame()))).receipt());return null;
                });publisher.flushActualReads(same).orElseThrow();
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var archive=archive(fixture,same,definitions.get(),source.get(),publisher);var scoped=fixture.archive.withSession(same);
                    var market=known(definitions.get().read(same,FinanceReadContracts.Query.MERCENARIES,fixture.reads,planning(lease.frame()))).receipt();
                    var frame=lease.frame();var changed=new DriverObservationAssembler.Complete(frame.identity(),frame.source(),frame.sessionId(),
                            frame.connectionGeneration(),frame.semantic().with("not_in_original_guard",new Bool(true)),frame.originalEvidence(),frame.observedAt(),frame.fullBindingSha256());
                    assertThrows(IllegalArgumentException.class,()->archive.verifyRead(root.get(),frame.identity(),frame.source(),frame.sessionId(),scoped,
                            Optional.of(new FinanceEvidenceArchive.HistoricalTarget(market.before().binding(),changed))));
                    assertThrows(IllegalArgumentException.class,()->archive.verifyRead(root.get(),frame.identity(),frame.source(),frame.sessionId(),scoped,Optional.empty()));
                    var internal=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),FinanceReadContracts.Query.ROOT.operation(),
                            FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),Instant.now().plusSeconds(20));
                    var internalRead=known(fixture.reads.read(same,definitions.get().contract(FinanceReadContracts.Query.ROOT),internal)).receipt();
                    assertThrows(IllegalArgumentException.class,()->archive.verifyRead(internalRead,frame.identity(),frame.source(),frame.sessionId(),scoped,Optional.empty()));
                    return null;
                });assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }
    private static void assertComplete(DriverObservationAssembler.Complete actual,DriverObservationAssembler.Complete replay) {
        assertEquals(actual,replay);assertEquals(actual.semantic(),replay.semantic());
    }
    private static FinanceEvidenceArchive archive(ActionWriterIntegrationFixture fixture,Session same,FinanceReadContracts definitions,
            ExactRef source,DriverReadHistoryPublisher publisher) {
        return new FinanceEvidenceArchive(fixture.writer,fixture.archive,()->same,fixture.physicalInputs().originals(),fixture.frameLoader(),definitions,List.of(),source,
                (held,root,guard,frame,scoped)->{
                    StrictJson.require(same==held,"actual quote must retain the same held writer");RootGuardEvidence.requireHistory(guard,scoped,held);
                    StrictJson.require(frame.equals(RootGuardEvidence.loadFrame(guard,scoped,fixture.frameLoader())),"quote target guard/frame originals differ");
                    var proof=publisher.requireHistoricalReadOnlyExtension(held,root,guard,frame).requireHistorical(held);
                    StrictJson.require(root.equals(proof.originalRead())&&scoped.readReferenceOf(root).equals(proof.originalReceipt())
                            &&frame.equals(proof.targetObserved()),"historical quote proof changed actual endpoints");
                });
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> selected,AtomicReference<ExactRef> source)throws IOException {
        RawJson packet;
        try(var stream=FinanceHistoricalRootQuoteTest.class.getResourceAsStream("/org/xar/ck3/control/application/driver/campaign-root-native-v1-fixture.json")) {
            if(stream==null)throw new IOException("retained canonical ROOT producer resource missing");packet=new RawJson(stream.readAllBytes());
        }
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("e".repeat(64),"finance-historical-root-read",ref->{
            source.set(ref);var definitions=new FinanceReadContracts(query->{String permission="game.command."+query.operation().value();
                return new FinanceReadContracts.Registration(ref,new FinanceReadContracts.Permission(Optional.of(permission),permission,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP));});
            selected.set(definitions);return List.of(definitions.contract(FinanceReadContracts.Query.ROOT),definitions.contract(FinanceReadContracts.Query.MERCENARIES));
        },request->{
            if(request.step().equals(FinanceReadContracts.Query.ROOT.operation().value()))return packet;
            assertEquals(FinanceReadContracts.Query.MERCENARIES.operation().value(),request.step());
            return new RawJson(DriverJson.encode(new Obj(Map.of("step",new Text(request.step()),"accepted",new Bool(true)))));
        },Optional.of("1.20.0.4"),Set.of());
    }
    private static DriverReadHistoryPublisher publisher(ActionWriterIntegrationFixture fixture,ExactRef source)throws IOException {
        var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(source));
        fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);fixture.bindKnownReadObserver(publisher::enqueue);return publisher;
    }
    private static PlanningReadResult.Known<FinanceReadContracts.Packet> known(PlanningReadResult<FinanceReadContracts.Packet> result) {
        if(result instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known)return known;throw new AssertionError(result);
    }
    private static PlanningRequest planning(DriverObservationAssembler.Complete frame) {
        var observation=new PlanningObservation(frame.semantic(),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),Instant.now().plusSeconds(20),observation);
    }
    private static void initialize(ActionWriterIntegrationFixture fixture,Session same,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity initial)throws IOException {
        fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=fixture.archive.preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("actual_software_start_policy",new Bool(true))))));
            var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
        });
    }
}
