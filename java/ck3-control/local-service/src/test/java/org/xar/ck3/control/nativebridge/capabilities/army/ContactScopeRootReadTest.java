package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
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
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Actual collector/READ guard/transport/archive/sole publisher/writer/snapshot chain with controlled software packets.
 * No live Game, native-source qualification, speed, cold-restoration or gameplay credit is claimed. */
final class ContactScopeRootReadTest {
    private static final String PROFILE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    @TempDir Path directory;
    @Test void bothRealContactFamiliesPublishAndReconstructThroughTheSoleCanonicalWriterAndPublicSnapshot()throws Exception {
        for(boolean projected:List.of(true,false)) {
            var ports=new AtomicReference<ContactScopeReads.ActualPorts>();var producer=new AtomicReference<ContactScopeReads>();
            var source=new AtomicReference<ExactRef>();var nativeResult=new AtomicReference<RawJson>();
            var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(PROFILE,"actual-contact-read-history",ref->{source.set(ref);return List.of();},
                    request->{assertTrue(request.additionalFields().objectFieldNames().isEmpty());return Objects.requireNonNull(nativeResult.get(),"the actual query result was not prepared");},
                    Optional.of("1.20.0.4"),Set.of(),ref->{
                        var actual=new ContactScopeReads(ref,ref,()->Objects.requireNonNull(ports.get(),"the actual fixture ports are not installed"));
                        producer.set(actual);return actual.families();
                    });
            try(var fixture=new ActionWriterIntegrationFixture(directory.resolve(projected?"projected":"actual"),false,scenario)) {
                ports.set(new ContactScopeReads.ActualPorts(fixture.reads,fixture.archive,fixture.frameLoader(),()->borrowed(fixture)));
                var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.actualReadCatalog(),List.of(source.get()));
                fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
                fixture.bindKnownReadObserver(publisher::enqueue);
                var first=fixture.ready();var body=originalScope(projected);var query=ContactScopeObservation.parseQuery(projected
                        ?"query-projected-contact-scope-v1-11-to-31-from-30":"query-actual-contact-scope-v1-11-at-2585");
                byte[] original=fixture.writer.locked(same->fixture.collector.current(same,first.request().before(),Instant.now().plusSeconds(20),
                        lease->fixture.archive.withSession(same).loadNativeFrame(lease.frame().originalEvidence())));
                NativeWire.Snapshot raw=(NativeWire.Snapshot)NativeWire.decode(original);
                ObjectNode state=parse(raw.state().value());
                state.putArray("player_armies").add(empty().put("army_id",11).put("controllable",true).put("owner_character_id",73)
                        .put("current_province_id",projected?30:2585));
                ObjectNode next=empty().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",raw.snapshotId()).put("revision",raw.revision().add(BigInteger.ONE));
                next.set("state",state);fixture.enqueueSoftwareNativePacket(NativeWire.packet(bytes(next)));
                var ready=fixture.ready();var originalRead=new AtomicReference<PlanningReadResult.Known<ContactScopeObservation>>();
                var originalContract=new AtomicReference<ReadContract<ContactScopeObservation>>();
                fixture.writer.locked(same->{
                    initialize(fixture,same,ready.request().before());
                    fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),lease->{
                        var selection=ContactScopeReads.Selection.current(query,lease.frame(),Instant.now().plusSeconds(20));
                        ObjectNode scope=body.deepCopy().put("snapshot_revision",selection.context().nativeRevision()).put("date_raw",selection.context().dateRaw()).put("subject_owner_character_id",73);
                        ObjectNode result=empty().put("step",query.step()).put("accepted",true).put("status","available").put("query_sequence",StrictJson.UINT64_MAX)
                                .put("snapshot_revision",selection.context().nativeRevision());
                        if(projected) result.put("backend_id","native-headless");
                        assertEquals(projected,result.has("backend_id"));
                        result.set(projected?"projected_contact_scope":"actual_contact_scope",scope);nativeResult.set(new RawJson(bytes(result)));
                        int writes=fixture.scenarioReadWrites();
                        originalContract.set(producer.get().contract(fixture.actualReadCatalog(),selection));
                        var known=known(producer.get().collect(same,fixture.actualReadCatalog(),selection));originalRead.set(known);
                        assertEquals(projected,known.value().backendId().isPresent());
                        assertEquals(writes+1,fixture.scenarioReadWrites());assertTrue(publisher.hasPending(same));
                        assertEquals(known.receipt(),fixture.archive.withSession(same).loadRead(known.originalReceipt()));
                        assertEquals(known.originalReceipt(),fixture.archive.withSession(same).readReferenceOf(known.receipt()));
                        assertThrows(IllegalArgumentException.class,()->publisher.flushActualReads(same));return null;
                    });
                    assertEquals(1,publisher.flushActualReads(same).orElseThrow().actual().head().sequence());
                    fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),lease->{
                        var history=lease.driver().driver().commandHistory();assertEquals(1,history.size());
                        var row=DriverReadHistoryRowProducer.decode(history.getFirst().originalRow().json());
                        assertEquals(projected?DriverReadHistoryRowProducer.Kind.PROJECTED_CONTACT_SCOPE:DriverReadHistoryRowProducer.Kind.ACTUAL_CONTACT_SCOPE,row.provenance().kind());
                        assertEquals(originalRead.get().originalReceipt(),row.provenance().originalReceipt());
                        assertEquals(originalRead.get().value().normalizedResult(),row.result());
                        assertEquals(projected,row.result().members().containsKey("backend_id"));
                        RawJson publicSnapshot=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                        ObjectNode publicData=parse(publicSnapshot.bytes());ObjectNode publicResult=object(publicData.withArray("native_command_history").get(0).get("result"));
                        assertEquals(StrictJson.UINT64_MAX.toString(),text(publicResult.get("query_sequence")));
                        assertEquals(projected,publicResult.has("backend_id"));
                        assertTrue(publicResult.get("snapshot_revision").isTextual());
                        assertTrue(publicResult.get(projected?"projected_contact_scope":"actual_contact_scope").get("snapshot_revision").isTextual());
                        assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(publicSnapshot));
                        var selection=ContactScopeReads.Selection.current(query,lease.frame(),Instant.now().plusSeconds(20));
                        var contract=producer.get().contract(fixture.actualReadCatalog(),selection);
                        var request=new PlanningReadRequest(selection.context().before(),selection.context().source(),selection.context().sessionId(),contract.operation(),DriverJson.object(new byte[]{'{','}'},2),selection.context().deadline());
                        int writes=fixture.scenarioReadWrites();String head=same.head().digest();
                        var replay=DriverReadHistoryRowProducer.replayCanonical(fixture.archive.withSession(same),fixture.actualReadCatalog(),originalContract.get(),row);
                        assertEquals(originalRead.get().receipt(),replay.receipt());assertEquals(originalRead.get().originalReceipt(),replay.originalReceipt());
                        assertEquals(originalRead.get().value(),replay.value());assertEquals(writes,fixture.scenarioReadWrites());assertEquals(head,same.head().digest());
                        // Archive replay is DATA. A changed public source frame must not obtain current Contact eligibility.
                        if(!originalRead.get().receipt().request().before().equals(request.before()))
                            assertTrue(publisher.canonicalReadWitness(same,contract,request).isEmpty());
                        var publicRead=ContactScopePublicCodec.capture(query,replay);assertEquals(publicRead,ContactScopePublicCodec.decode(ContactScopePublicCodec.encode(publicRead)));
                        var originalPublic=ContactScopePublicCodec.encodeOriginal(replay.value());
                        assertEquals(replay.value(),ContactScopePublicCodec.decodeOriginal(originalPublic));
                        ObjectNode generic=parse(originalPublic.bytes()),dedicated=parse(ContactScopePublicCodec.encode(publicRead).bytes());
                        assertFalse(generic.has("original_read_receipt"));dedicated.remove("original_read_receipt");assertEquals(generic,dedicated);
                        assertEquals(projected,generic.has("backend_id"));assertEquals(projected,dedicated.has("backend_id"));
                        assertEquals(writes,fixture.scenarioReadWrites());assertEquals(head,same.head().digest());
                        return null;
                    });
                    assertFalse(publisher.hasPending(same));assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
                });
            }
        }
    }
    private static ContinuityStorePort.Session borrowed(ActionWriterIntegrationFixture fixture) {
        try{return fixture.writer.borrowedSession();}catch(IOException error){throw new UncheckedIOException(error);}
    }
    private static PlanningReadResult.Known<ContactScopeObservation> known(PlanningReadResult<ContactScopeObservation> actual) {
        if(actual instanceof PlanningReadResult.Known<ContactScopeObservation> known)return known;throw new AssertionError(actual);
    }
    private static ObjectNode originalScope(boolean projected)throws IOException {
        String root=System.getProperty("xar.repository.root");assertNotNull(root,"actual complete CI repository input is required");
        Path java=Path.of(root,"java","ck3-control");
        if(projected) {
            ObjectNode golden=parse(Files.readAllBytes(java.resolve("military-policy/src/test/resources/projectedcontact/producer-golden-v1.json")));
            return object(golden.withArray("cases").get(0).get("expected").get("projection"));
        }
        ObjectNode golden=parse(Files.readAllBytes(java.resolve("wave2-military/src/test/resources/actualcontact/producer-golden-v1.json")));
        return object(golden.get("bases").get("new_attacker").get("scope"));
    }
    private static void initialize(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session same,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before)throws IOException {
        fixture.collector.current(same,before,Instant.now().plusSeconds(20),lease->{
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=fixture.archive.preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("actual_contact_software_start_policy",new OpportunityJson.Bool(true))))));
            var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
        });
    }
}
