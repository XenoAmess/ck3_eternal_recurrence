package org.xar.ck3.control.application.driver;

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
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004;


/** New same-scope pending public ROOT software regression; no actual Game authority. */
final class PendingRootRead216Test {
    private static final String PROFILE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    @TempDir Path directory;

    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> target,AtomicReference<ExactRef> source) throws IOException {
        return scenario(target,source,false);
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> target,AtomicReference<ExactRef> source,boolean strictOptional) throws IOException {
        return scenario(target,source,strictOptional?1:0);
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> target,AtomicReference<ExactRef> source,int optionalMode) throws IOException {
        RawJson packet=switch(optionalMode){case 0->packet();case 1->packetWithStrictOptional();case 2->packetWithMalformedOptionalRevision();default->throw new IllegalArgumentException("unknown software optional variant");};
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(PROFILE,"actual-root-read-history",ref->{
            source.set(ref);var definitions=new FinanceReadContracts(query->{
                String permission="game.command."+query.operation().value();return new FinanceReadContracts.Registration(ref,
                    new FinanceReadContracts.Permission(Optional.of(permission),permission,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP));
            });
            target.set(definitions);return List.of(definitions.contract(FinanceReadContracts.Query.ROOT),definitions.contract(FinanceReadContracts.Query.CASH));
        },request->{
            if(request.step().equals(FinanceReadContracts.Query.CASH.operation().value())) {
                Obj fields=DriverJson.object(request.additionalFields().bytes(),RawJson.MAXIMUM_BYTES);
                assertEquals(Set.of("expected_snapshot_revision"),fields.members().keySet());
                return new RawJson(DriverJson.encode(new Obj(Map.of("step",new Text(request.step()),"accepted",new Bool(true)))));
            }
            assertEquals(FinanceReadContracts.Query.ROOT.operation().value(),request.step());
            assertTrue(request.additionalFields().objectFieldNames().isEmpty(),"typed public/internal capture wrapper must never leak into native additional fields");return packet;
        },Optional.of("1.20.0.4"),Set.of());
    }
    private static RawJson packet() throws IOException {
        try(var input=PendingRootRead216Test.class.getResourceAsStream("campaign-root-native-v1-fixture.json")) {
            if(input==null)throw new IOException("exact ROOT software packet resource missing");return new RawJson(input.readAllBytes());
        }
    }
    private static RawJson packetWithStrictOptional() throws IOException {
        var core=new NativePlayerHeirObservation12004.Core(ActionWriterIntegrationFixture.INITIAL_DATE_RAW,true,0,0,true,true,73,true);
        var observation=new NativePlayerHeirObservation12004.Observation(true,null,true,true,core,core,true,true,73,74,true,true,true,
                new NativePlayerHeirObservation12004.Lineage(1,2),null);
        var component=new NativePlayerHeirObservation12004.Component(BigInteger.ONE,true,observation);
        Obj result=DriverJson.object(packet().bytes(),RawJson.MAXIMUM_BYTES);
        Obj root=object(result.get("campaign_root_context"),"software original root");
        Obj encoded=DriverJson.object(NativePlayerHeirObservation12004.encodeComponent(component),RawJson.MAXIMUM_BYTES);
        return new RawJson(DriverJson.encode(result.with("campaign_root_context",root.with(NativePlayerHeirObservation12004.COMPONENT,encoded))));
    }
    private static RawJson packetWithMalformedOptionalRevision() throws IOException {
        Obj result=DriverJson.object(packetWithStrictOptional().bytes(),RawJson.MAXIMUM_BYTES);
        Obj root=object(result.get("campaign_root_context"),"strict software root");
        Obj component=object(root.get(NativePlayerHeirObservation12004.COMPONENT),"original typed component").with("snapshot_revision",new Text("1"));
        return new RawJson(DriverJson.encode(result.with("campaign_root_context",root.with(NativePlayerHeirObservation12004.COMPONENT,component))));
    }
    private static DriverReadHistoryPublisher publisher(ActionWriterIntegrationFixture fixture,ExactRef source) throws IOException {
        var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(source));
        fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
        fixture.bindKnownReadObserver(publisher::enqueue);return publisher;
    }
    private static PlanningReadResult.Known<FinanceReadContracts.Packet> known(PlanningReadResult<FinanceReadContracts.Packet> result) {
        if(result instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known)return known;throw new AssertionError(result);
    }
    private static PlanningReadRequest query(ReadContract<FinanceReadContracts.Packet> contract,PlanningRequest request,FinanceReadContracts.RootCapture capture) {
        return new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),FinanceReadContracts.rootArguments(capture),request.deadline());
    }
    private static PlanningRequest planning(DriverObservationAssembler.Complete frame) {
        var observation=new PlanningObservation(frame.semantic(),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),Instant.now().plusSeconds(20),observation);
    }
    private static void initialize(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session same,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity initial) throws IOException {
        fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=fixture.archive.preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("actual_software_start_policy",new Bool(true))))));
            var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
        });
    }

    @Test void pendingCanonicalReadReusesOneActualLiveQueryAcrossFourConsumersAndFlushesOnce() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("pending-root-216"),false,scenario(definitions,source))) {
            var publisher=publisher(fixture,source.get());var initial=fixture.ready();
            var original=new AtomicReference<PlanningReadResult.Known<FinanceReadContracts.Packet>>();
            var currentRequest=new AtomicReference<PlanningReadRequest>();
            var contract=new AtomicReference<ReadContract<FinanceReadContracts.Packet>>();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var request=planning(lease.frame());
                    var c=definitions.get().contract(FinanceReadContracts.Query.ROOT);contract.set(c);
                    var q=query(c,request,FinanceReadContracts.RootCapture.PUBLIC_QUERY);currentRequest.set(q);
                    int writesBefore=fixture.scenarioReadWrites();
                    // Consumer 1: No pending cache, must perform live read.
                    var first=publisher.pendingCanonicalRead(same,c,q);
                    assertTrue(first.isEmpty(),"first pending read must be empty before live query");
                    var live=known(definitions.get().read(same,FinanceReadContracts.Query.ROOT,fixture.reads,request));
                    original.set(live);
                    assertEquals(writesBefore+1,fixture.scenarioReadWrites(),"exactly one live query occurred");
                    assertTrue(publisher.hasPending(same),"live read must enqueue pending row");
                    // Consumers 2-4: Must hit pendingCanonicalRead without new live queries.
                    for(int i=0;i<3;i++) {
                        var hit=publisher.pendingCanonicalRead(same,c,q).orElseThrow();
                        assertEquals(original.get().receipt(),hit.receipt());
                        assertEquals(original.get().originalReceipt(),hit.originalReceipt());
                        assertEquals(original.get().value().result(),hit.value().result());
                        assertEquals(original.get().value().originalResult(),hit.value().originalResult());
                        assertArrayEquals(original.get().value().originalFrame(),hit.value().originalFrame());
                    }
                    assertEquals(writesBefore+1,fixture.scenarioReadWrites(),"pending hits must not increase live writes");
                    // Negative: Changed arguments (INTERNAL capture) must miss.
                    var internalQuery=query(c,request,FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS);
                    assertTrue(publisher.pendingCanonicalRead(same,c,internalQuery).isEmpty(),"changed capture context must miss");
                    // Negative: Distinct contract instance (same operation/source) must miss/fail-closed.
                    var otherDefinitions=new FinanceReadContracts(query->{
                        String permission="game.command."+query.operation().value();
                        return new FinanceReadContracts.Registration(source.get(),
                            new FinanceReadContracts.Permission(java.util.Optional.of(permission),permission,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP));
                    });
                    var otherContract=otherDefinitions.contract(FinanceReadContracts.Query.ROOT);
                    assertThrows(IllegalArgumentException.class,()->publisher.pendingCanonicalRead(same,otherContract,q),
                            "same-value detached contract cannot acquire the actual installed identity");
                    var changedDeadline=new PlanningReadRequest(q.origin(),q.source(),q.sessionId(),q.operation(),q.arguments(),q.deadline().minusMillis(1));
                    assertTrue(publisher.pendingCanonicalRead(same,c,changedDeadline).isEmpty(),"the full request includes its original deadline");
                    var changedSession=new PlanningReadRequest(q.origin(),q.source(),q.sessionId()+"-other",q.operation(),q.arguments(),q.deadline());
                    assertTrue(publisher.pendingCanonicalRead(same,c,changedSession).isEmpty(),"another request session cannot reuse this original");
                    return null;
                });
                // Flush once.
                var committed=publisher.flushActualReads(same).orElseThrow();
                assertEquals(1,committed.actual().head().sequence());
                assertFalse(publisher.hasPending(same));
                // Post-flush: pendingCanonicalRead must be empty (no longer pending).
                var postFlush=publisher.pendingCanonicalRead(same,contract.get(),currentRequest.get());
                assertTrue(postFlush.isEmpty(),"pending read must be empty after flush");
                // A committed Driver is reacquired through the actual collector before existing canonical replay.
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var complete=lease.driver().driver();
                    assertEquals(1,complete.commandHistory().size(),"four consumers publish one genuine ROOT history row");
                    var row=DriverReadHistoryRowProducer.decode(complete.commandHistory().getFirst().originalRow().json());
                    assertEquals(original.get().originalReceipt(),row.provenance().originalReceipt());
                    var fresh=query(contract.get(),planning(lease.frame()),FinanceReadContracts.RootCapture.PUBLIC_QUERY);
                    assertTrue(publisher.pendingCanonicalRead(same,contract.get(),fresh).isEmpty());
                    int writes=fixture.scenarioReadWrites();
                    var witness=publisher.canonicalReadWitness(same,contract.get(),fresh).orElseThrow();
                    var replay=witness.requireCurrent(same,contract.get(),fresh);
                    assertEquals(original.get().receipt(),replay.receipt());
                    assertEquals(original.get().originalReceipt(),replay.originalReceipt());
                    assertEquals(writes,fixture.scenarioReadWrites());
                    return null;
                });
                assertEquals(0,fixture.nativeActionWrites());
                return null;
            });
        }
    }
}
