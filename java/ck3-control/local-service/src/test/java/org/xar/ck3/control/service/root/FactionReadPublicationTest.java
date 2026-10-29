package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.warentry.WarEntryCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;

/** Real central coordinator/guards/archive and Driver producer/CAS, with only the Native packet edge simulated.
 * The callback calls the actual shared producer directly: this is not an instantiated DriverCapabilityRuntime.
 * Actual Runtime dispatch uses the same supports/observeSemanticRead branch; no second observer is installed here.
 */
public final class FactionReadPublicationTest {
    @TempDir Path directory;
    private static final String RESOURCE_SHA = "32965884067c0d6d54b75aa6273e784564b6a219a2f7693e38fe257dc622748a";
    public record Published(DriverObservationAssembler.Complete frame,RawJson publicSnapshot,
                            FactionReadObservation observation,ExactRef originalReceipt,int nativeReadWrites) { }
    private enum NativeFault { NONE, ACTOR, DATE, NATIVE_REVISION, BOOLEAN_SEQUENCE, OPERATION, COUNTY_EXPOSURE }

    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(
            AtomicReference<FactionAlertReadService.Contracts> installed,
            AtomicReference<DriverObservationAssembler.Complete> held,boolean unavailable) throws Exception {
        return scenario(installed,held,unavailable,NativeFault.NONE);
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(
            AtomicReference<FactionAlertReadService.Contracts> installed,
            AtomicReference<DriverObservationAssembler.Complete> held,boolean unavailable,NativeFault fault) throws Exception {
        ObjectNode template=originalNativeBody();
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(
                FactionAlertModel.Build.CK3_12004.sha256().toLowerCase(Locale.ROOT),"ck3-1.20.0.4-msvc-x64",
                ignored->List.of(),request->{
                    assertEquals(FactionAlertReadService.STEP,request.step());
                    var frame=java.util.Objects.requireNonNull(held.get(),"native response belongs to the actual held request frame");
                    var identity=frame.identity().frame().identity();ObjectNode body=template.deepCopy();
                    body.put("snapshot_revision",identity.nativeRevision()).put("date_raw",identity.dateRaw())
                            .put("player_character_id",identity.player());
                    ObjectNode counties=(ObjectNode)body.get("player_subrealm_geographic_counties_v1");
                    counties.put("snapshot_revision",identity.nativeRevision()).put("date_raw",identity.dateRaw())
                            .put("actor_character_id",identity.player());
                    if(unavailable)body=unavailableNativeBody(body);
                    ObjectNode result=StrictJson.object().put("step",FactionAlertReadService.STEP).put("accepted",true)
                            .put("status",unavailable?"unavailable":"available").put("query_sequence",1)
                            .put("snapshot_revision",identity.nativeRevision()).put("player_faction_alerts_ready",!unavailable)
                            .put("backend_id","native-headless");result.set("player_faction_alerts",body);
                    switch(fault) {
                        case NONE -> { }
                        case COUNTY_EXPOSURE -> {
                            assertEquals(0,body.path("targeting_faction_count").intValue());
                            int county=body.path("player_subrealm_geographic_counties_v1").path("county_title_ids").get(0).intValue();
                            ObjectNode exposure=StrictJson.object().put("county_title_id",county).put("faction_id",33554434)
                                    .put("faction_type_key","populist_faction").put("target_character_id",identity.player().add(BigInteger.ONE))
                                    .put("dangerous_by_stock_rule",true)
                                    .put("danger_reason","player_county_in_powerful_liege_targeting_populist_faction");
                            exposure.set("power",StrictJson.object().put("raw",8000000).put("scale",100000));
                            exposure.set("power_threshold",StrictJson.object().put("raw",7500000).put("scale",100000));
                            body.withArray("county_exposures").add(exposure);
                            ObjectNode planner=(ObjectNode)body.get("planner_projection");
                            planner.put("present",true).put("dangerous",true);planner.withArray("exposed_county_title_ids").add(county);
                        }
                        case ACTOR -> {
                            body.put("player_character_id",identity.player().add(BigInteger.ONE));
                            counties.put("actor_character_id",identity.player().add(BigInteger.ONE));
                        }
                        case DATE -> {
                            body.put("date_raw",identity.dateRaw().add(BigInteger.ONE));
                            counties.put("date_raw",identity.dateRaw().add(BigInteger.ONE));
                        }
                        case NATIVE_REVISION -> {
                            result.put("snapshot_revision",identity.nativeRevision().add(BigInteger.ONE));
                            body.put("snapshot_revision",identity.nativeRevision().add(BigInteger.ONE));
                            counties.put("snapshot_revision",identity.nativeRevision().add(BigInteger.ONE));
                        }
                        case BOOLEAN_SEQUENCE -> result.put("query_sequence",true);
                        case OPERATION -> result.put("step","foreign_faction_query");
                    }
                    return new RawJson(StrictJson.canonical(result));
                },Optional.of("1.20.0.4"),Set.of(FactionAlertReadService.CAPABILITY),source->{
                    var contracts=new FactionAlertReadService.Contracts(source,source);
                    assertTrue(installed.compareAndSet(null,contracts));return contracts.families();
                });
    }
    /** Immutable software Native packet DATA only; no Realm lifecycle/selected-read test helper is imported. */
    private static ObjectNode originalNativeBody() throws Exception {
        byte[] original;
        try(var stream=FactionReadPublicationTest.class.getResourceAsStream("/realm-ordinary/producer-bases.json")) {
            assertNotNull(stream,"original Native fixture resource is required");original=stream.readAllBytes();
        }
        assertEquals(RESOURCE_SHA,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        var source=StrictJson.parse(original,100_000).path("bases").path("first").path("faction_result").path("player_faction_alerts");
        return assertInstanceOf(ObjectNode.class,source).deepCopy();
    }
    private static ObjectNode unavailableNativeBody(ObjectNode original) {
        ObjectNode body=original.deepCopy();body.put("status","unavailable");
        body.putNull("player_character_id");body.putNull("targeting_faction_count");
        body.put("unavailable_reason","state_changed");body.remove("player_subrealm_geographic_counties_v1");
        ObjectNode ready=assertInstanceOf(ObjectNode.class,body.get("readiness"));
        for(String field:List.of("targeting_count_ready","identity_ready","targeting_rows_ready","county_exposure_ready",
                "stock_dangerous_predicate_ready","same_frame_ready","alert_ready","exact_ultimatum_timing_ready"))ready.put(field,false);
        ObjectNode planner=assertInstanceOf(ObjectNode.class,body.get("planner_projection"));
        planner.put("status","unavailable");planner.putNull("present");planner.putNull("dangerous");return body;
    }
    /** Change only the simulated Native packet edge; real receiver/source/Driver producers derive both revision roles. */
    private static ObservationIdentity separatedInitialFrame(ActionWriterIntegrationFixture fixture) throws Exception {
        var first=fixture.ready();
        byte[] original=fixture.writer.locked(same->fixture.collector.current(same,first.request().before(),Instant.now().plusSeconds(20),
                lease->fixture.archive.withSession(same).loadNativeFrame(lease.frame().originalEvidence())));
        assertTrue(original.length>=5);
        assertEquals(original.length-4,ByteBuffer.wrap(original,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        ObjectNode envelope=assertInstanceOf(ObjectNode.class,StrictJson.parse(Arrays.copyOfRange(original,4,original.length),StrictJson.EXPLICIT_MAX_BYTES));
        assertEquals("state_snapshot",envelope.path("type").textValue());
        envelope.put("snapshot_id","fixture-faction-separated").put("revision",envelope.path("revision").bigIntegerValue().add(BigInteger.valueOf(100)));
        fixture.enqueueSoftwareNativePacket(packet(envelope));
        fixture.physicalInputs().transport().observe(Instant.now().plusSeconds(20));
        ObservationIdentity actual=fixture.ready().request().before();
        assertNotEquals(actual.frame().revision(),actual.frame().identity().nativeRevision(),"actual public/native revision roles must be distinct");
        return actual;
    }
    private static void initialize(ActionWriterIntegrationFixture fixture,Session same,ObservationIdentity initial) throws IOException {
        fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=fixture.archive.preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("actual_software_start_policy",new Bool(true))))));
            var publication=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),publication.expectedAuxiliarySha256(),publication);return null;
        });
    }
    private static PlanningReadResult<FactionAlertReadService.Observation> read(
            ActionWriterIntegrationFixture fixture,Session same,FactionAlertReadService.Contracts contracts,
            DriverObservationAssembler.Complete frame,Instant deadline) {
        RawJson wars=new RawJson(DriverJson.encode(frame.semantic().get("active_wars")));
        var context=new FactionAlertReadService.Context(frame.identity(),frame.source(),frame.sessionId(),deadline,
                new FactionAlertReadService.SameFrameWars(frame.identity(),wars),text(frame.semantic().get("backend_id"),"backend"));
        var selected=new FactionAlertReadService.Selection(new FactionAlertReadService.Query(frame.identity().frame().revision()),context);
        var issued=contracts.issue(fixture.reads.catalog(),selected);
        return fixture.reads.read(same,issued,FactionAlertReadService.request(selected));
    }
    private static void bindRefresh(ActionWriterIntegrationFixture fixture) {
        fixture.driverAuthority().bindCapabilityObservation((nativeFrame,known)->{
            try {
                var originals=fixture.archive.withSession(fixture.writer.borrowedSession());
                var reference=originals.preserveNativeFrame(nativeFrame);
                var frame=new DriverObservationAssembler().assemble(nativeFrame,known.observation().orElseThrow(),reference);
                return DriverCapabilityStateProducer.refresh(assertInstanceOf(DriverObservationAssembler.Complete.class,frame,()->"actual fixture refresh join: "+frame),known,originals);
            } catch(IOException failure) {
                throw new UncheckedIOException(failure);
            }
        });
    }
    /** A test-only actual central READ/producer result, never a prebuilt plan, report, summary or Known DTO. */
    public static Published published(Path directory,boolean unavailable) throws Exception {
        return published(directory,unavailable,false);
    }
    private static Published published(Path directory,boolean unavailable,boolean advanceNativeFrame) throws Exception {
        return published(directory,unavailable,advanceNativeFrame,false);
    }
    private static Published published(Path directory,boolean unavailable,boolean advanceNativeFrame,boolean replayColdSource) throws Exception {
        return published(directory,unavailable,advanceNativeFrame,replayColdSource,NativeFault.NONE);
    }
    private static Published published(Path directory,boolean unavailable,boolean advanceNativeFrame,boolean replayColdSource,NativeFault nativeBody) throws Exception {
        var installed=new AtomicReference<FactionAlertReadService.Contracts>();
        var held=new AtomicReference<DriverObservationAssembler.Complete>();
        var original=new AtomicReference<PlanningReadResult.Known<FactionAlertReadService.Observation>>();
        var delivered=new AtomicInteger();var result=new AtomicReference<Published>();
        try(var fixture=new ActionWriterIntegrationFixture(directory,false,scenario(installed,held,unavailable,nativeBody))) {
            fixture.bindKnownReadObserver((same,identical,actual)->{
                if(!FactionAlertModel.STEP.equals(actual.receipt().request().operation().value()))return;
                assertTrue(DriverSemanticReadState.supports(actual));delivered.incrementAndGet();
                assertInstanceOf(FactionReadObservation.class,actual.value());
                try {
                    fixture.driverAuthority().withFrozenFacts(same,frozen->{
                        var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                        var originals=fixture.archive.withSession(same);
                        var frame=RootGuardEvidence.loadFrame(actual.receipt().after().binding(),originals,fixture.frameLoader());
                        assertEquals(actual.receipt().request().before(),frame.identity());
                        assertEquals(actual.receipt().request().source(),frame.source());
                        assertEquals(actual.receipt().request().sessionId(),frame.sessionId());
                        var observed=known.observation().orElseThrow();
                        assertEquals(known.stamp().driverVersion(),observed.driverVersion());
                        assertEquals(frame.identity().frame().snapshotId(),observed.snapshotId());
                        assertEquals(frame.identity().frame().revision(),observed.publicRevision());
                        var publication=DriverCapabilityStateProducer.observeSemanticRead(frame,known,identical,actual,originals);
                        var replayed=DriverCapabilityStateProducer.replay(frame,known,publication.source(),originals);
                        assertEquals(DriverJson.object(((FactionReadObservation)actual.value()).normalizedAlert().bytes(),RawJson.MAXIMUM_BYTES),
                                replayed.get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
                        fixture.driverAuthority().publishCapabilityInputs(same,known.stamp(),publication.expectedAuxiliarySha256(),publication);
                        return null;
                    });
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            var initial=separatedInitialFrame(fixture);
            fixture.writer.locked(same->{
                initialize(fixture,same,initial);
                bindRefresh(fixture);
                fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
                    held.set(lease.frame());try {
                        var actual=read(fixture,same,installed.get(),lease.frame(),lease.validUntil());
                        if(!(actual instanceof PlanningReadResult.Known<FactionAlertReadService.Observation> known))
                            throw new AssertionError("actual original faction READ unavailable: "+actual);
                        original.set(known);assertEquals(1,delivered.get());assertEquals(1,fixture.scenarioReadWrites());
                    }finally{held.set(null);}return null;
                });
                fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
                    var known=original.get();Obj payload=DriverJson.object(known.value().normalizedAlert().bytes(),RawJson.MAXIMUM_BYTES);
                    assertEquals(payload,lease.frame().semantic().get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
                    Obj sources=object(lease.driver().auxiliary().get(DriverSemanticReadState.SOURCES),"semantic sources");
                    assertEquals(DriverObservationEvidenceReader.reference(known.originalReceipt()),object(sources.get("FACTION_ALERTS"),"faction source").get("receipt"));
                    assertTrue(lease.driver().driver().commandHistory().isEmpty(),"faction uses one source-owned semantic slot, no invented canonical history row");
                    var collected=WarEntryCollector.collect(lease.frame().semantic(),List.of());
                    assertEquals(payload,collected.factionAlert().orElseThrow());
                    RawJson wire=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                    Obj publicSnapshot=DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES);
                    Obj body=object(publicSnapshot.get(DriverSemanticReadState.FACTION_ALERTS_FIELD),"public faction body");
                    assertInstanceOf(Text.class,body.get("snapshot_revision"));
                    if(unavailable){assertEquals(Nil.INSTANCE,body.get("player_character_id"));assertEquals(new Text("unavailable"),body.get("status"));}
                    else assertInstanceOf(Text.class,object(body.get("player_subrealm_geographic_counties_v1"),"county body").get("snapshot_revision"));
                    assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(wire));
                    assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
                    if(replayColdSource) {
                        var originals=fixture.archive.withSession(same);
                        byte[] packet=originals.loadNativeFrame(lease.frame().originalEvidence());
                        assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
                        ObjectNode envelope=assertInstanceOf(ObjectNode.class,StrictJson.parse(Arrays.copyOfRange(packet,4,packet.length),StrictJson.EXPLICIT_MAX_BYTES));
                        Obj nativeState=object(DriverJson.fromNode(envelope.get("state")),"actual original native state");
                        Obj cold=RootRestoreMaterialProjection.reduceAuxiliary(lease.driver().auxiliary(),nativeState);
                        // The actual natural-successor reducer calls this same cache-clear producer.
                        // This checks shared DATA reduction, without minting a successor or private lifecycle proof.
                        Obj successorCleared=org.xar.ck3.control.application.lifecycle.LifecycleReducer.clearEpisodeCaches(lease.driver().auxiliary());
                        assertEquals(Nil.INSTANCE,successorCleared.get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
                        assertEquals(sources,successorCleared.get(DriverSemanticReadState.SOURCES));
                        org.xar.ck3.control.application.driver.DriverFactionReplayAssertions.requireOriginalSources(successorCleared,originals);
                        assertEquals(Nil.INSTANCE,cold.get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
                        assertEquals(sources,cold.get(DriverSemanticReadState.SOURCES),"cold clearing retains the actual original source table");
                        Obj roundtrip=DriverJson.object(DriverJson.encode(cold),RawJson.MAXIMUM_BYTES);
                        org.xar.ck3.control.application.driver.DriverFactionReplayAssertions.requireOriginalSources(roundtrip,originals);
                        assertEquals(Nil.INSTANCE,roundtrip.get(DriverSemanticReadState.FACTION_ALERTS_FIELD),"replaying old evidence must not revive the old current slot");
                        Obj substituted=roundtrip.with(DriverSemanticReadState.FACTION_ALERTS_FIELD,
                                payload.with("player_character_id",new IntegerValue(lease.frame().identity().frame().identity().player().add(BigInteger.ONE))));
                        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.application.driver.DriverFactionReplayAssertions.requireOriginalSources(substituted,originals),
                                "a populated body cannot borrow the preserved receipt of another actor");
                        Obj badSource=object(sources.get("FACTION_ALERTS"),"original faction source").with("receipt",
                                object(object(sources.get("FACTION_ALERTS"),"original faction source").get("receipt"),"receipt").with("sha256",new Text("0".repeat(64))));
                        Obj forged=roundtrip.with(DriverSemanticReadState.SOURCES,sources.with("FACTION_ALERTS",badSource));
                        assertThrows(RuntimeException.class,()->org.xar.ck3.control.application.driver.DriverFactionReplayAssertions.requireOriginalSources(forged,originals),
                                "cold history still requires the identical archived receipt");
                        assertEquals(1,fixture.scenarioReadWrites(),"cold projection and original replay cannot issue another native query");
                    }
                    result.set(new Published(lease.frame(),wire,known.value(),known.originalReceipt(),fixture.scenarioReadWrites()));return null;
                });
                return null;
            });
                if(advanceNativeFrame) {
                    byte[] nativeOriginal=fixture.writer.locked(same->fixture.archive.withSession(same).loadNativeFrame(original.get().receipt().before().binding().nativeEvidence()));
                    assertTrue(nativeOriginal.length>=5);
                    assertEquals(nativeOriginal.length-4,ByteBuffer.wrap(nativeOriginal,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
                    ObjectNode envelope=(ObjectNode)StrictJson.parse(Arrays.copyOfRange(nativeOriginal,4,nativeOriginal.length),StrictJson.EXPLICIT_MAX_BYTES);
                    assertEquals("state_snapshot",envelope.get("type").textValue());
                    ObjectNode state=(ObjectNode)envelope.get("state");
                    state.put("date_raw",state.get("date_raw").bigIntegerValue().add(BigInteger.valueOf(org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.TICKS_PER_DAY)));
                    envelope.put("snapshot_id","fixture-faction-next").put("revision",envelope.get("revision").bigIntegerValue().add(BigInteger.ONE));
                    fixture.enqueueSoftwareNativePacket(packet(envelope));
                    ObservationIdentity next;
                    try{fixture.physicalInputs().transport().observe(Instant.now().plusSeconds(20));next=fixture.ready().request().before();}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    fixture.writer.locked(same->fixture.collector.current(same,next,Instant.now().plusSeconds(20),lease->{
                        assertNotEquals(initial,lease.frame().identity());
                        assertEquals(Nil.INSTANCE,lease.frame().semantic().get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
                        assertTrue(WarEntryCollector.collect(lease.frame().semantic(),List.of()).factionAlert().isEmpty());
                        assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true))));
                        assertEquals(1,fixture.scenarioReadWrites(),"source invalidation itself must not send another faction query");return null;
                    }));
                }
        }
        return java.util.Objects.requireNonNull(result.get());
    }
    private static byte[] packet(ObjectNode envelope) {
        byte[] payload=StrictJson.canonical(envelope);
        return ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
    }
    @Test void actualCentralZeroTargetReadRetainsExternalCountyDangerThroughPublicProjection() throws Exception {
        Published actual=published(directory.resolve("zero-target-county-danger"),false,false,true,NativeFault.COUNTY_EXPOSURE);
        var frame=assertInstanceOf(FactionAlertModel.Available.class,actual.observation().frame());
        assertEquals(0,frame.targetingFactionCount());assertEquals(1,frame.countyExposures().size());
        Obj publicSnapshot=PublicSnapshotCodec.decode(actual.publicSnapshot());
        Obj alert=WarEntryCollector.collect(publicSnapshot,List.of()).factionAlert().orElseThrow();
        assertEquals(DriverJson.object(actual.observation().normalizedAlert().bytes(),RawJson.MAXIMUM_BYTES),alert);
        // Pure count DATA from the actual read, not a privately issued CampaignRoot/lifecycle proof.
        Obj count=new Obj(Map.of("player_targeting_faction_count",alert.get("targeting_faction_count")));
        Obj context=WarEntryCollector.factionContext(count,alert);
        assertEquals(new Text("dangerous"),context.get("status"));
        assertEquals(new Bool(false),context.get("prior_scope_eligible"));
        assertEquals(1,array(context.get("exposed_county_title_ids"),"exposed counties").size());
        assertEquals(1,actual.nativeReadWrites());
    }
    @Test void actualCentralAvailableReadPublishesBothRevisionRolesAndInvalidatesOnTheNextNativeFrame() throws Exception {
        Published actual=published(directory.resolve("available"),false,true);
        assertInstanceOf(FactionAlertModel.Available.class,actual.observation().frame());
        assertEquals(1,actual.nativeReadWrites());
        ObjectNode wire=(ObjectNode)StrictJson.parse(actual.publicSnapshot().bytes(),StrictJson.EXPLICIT_MAX_BYTES);
        ((ObjectNode)wire.get(DriverSemanticReadState.FACTION_ALERTS_FIELD)).put("snapshot_revision",1);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(new RawJson(StrictJson.canonical(wire))));
        ObjectNode foreign=(ObjectNode)StrictJson.parse(actual.publicSnapshot().bytes(),StrictJson.EXPLICIT_MAX_BYTES);
        ObjectNode alert=(ObjectNode)foreign.get(DriverSemanticReadState.FACTION_ALERTS_FIELD);
        BigInteger foreignActor=alert.get("player_character_id").bigIntegerValue().add(BigInteger.ONE);
        alert.put("player_character_id",foreignActor);
        ((ObjectNode)alert.get("player_subrealm_geographic_counties_v1")).put("actor_character_id",foreignActor);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(new RawJson(StrictJson.canonical(foreign))),
                "a body with internally matching foreign actor must still match the actual outer Snapshot actor");
    }
    @Test void actualSourcedColdClearRetainsOriginalReplayAndRejectsRepopulatedOrSubstitutedSources() throws Exception {
        Published actual=published(directory.resolve("sourced-cold"),false,false,true);
        assertInstanceOf(FactionAlertModel.Available.class,actual.observation().frame());
        assertEquals(1,actual.nativeReadWrites());
    }
    @Test void actualCentralUnavailableReadRetainsTheNullActorSoTheCollectorDoesNotDropItsRefusal() throws Exception {
        Published actual=published(directory.resolve("unavailable"),true);
        assertInstanceOf(FactionAlertModel.Unavailable.class,actual.observation().frame());
        Obj alert=WarEntryCollector.collect(actual.frame().semantic(),List.of()).factionAlert().orElseThrow();
        assertEquals(new Text("unavailable"),alert.get("status"));assertEquals(Nil.INSTANCE,alert.get("player_character_id"));
        assertEquals(1,actual.nativeReadWrites());
    }
    /** Pure body serialization boundary, separate from the actual central READ/CAS assertions above. */
    @Test void sharedBodyCodecPreservesFullUint64AndRejectsNonStringPublicRevisions() throws Exception {
        Published actual=published(directory.resolve("uint64-body"),false);
        ObjectNode numeric=assertInstanceOf(ObjectNode.class,StrictJson.parse(actual.observation().normalizedAlert().bytes(),StrictJson.EXPLICIT_MAX_BYTES));
        numeric.put("snapshot_revision",StrictJson.UINT64_MAX);
        assertInstanceOf(ObjectNode.class,numeric.get("player_subrealm_geographic_counties_v1")).put("snapshot_revision",StrictJson.UINT64_MAX);
        var expected=new FactionAlertModel.ExpectedFrame(actual.frame().identity().frame().identity().dateRaw().intValueExact(),
                StrictJson.UINT64_MAX,Optional.of(FactionAlertModel.Build.CK3_12004));
        RawJson wire=FactionReadReplay.encodeSemanticBody(new RawJson(StrictJson.canonical(numeric)),expected);
        ObjectNode external=assertInstanceOf(ObjectNode.class,StrictJson.parse(wire.bytes(),StrictJson.EXPLICIT_MAX_BYTES));
        assertEquals(StrictJson.UINT64_MAX.toString(),external.path("snapshot_revision").textValue());
        assertEquals(StrictJson.UINT64_MAX.toString(),external.path("player_subrealm_geographic_counties_v1").path("snapshot_revision").textValue());
        assertEquals(numeric,StrictJson.parse(FactionReadReplay.decodeSemanticBody(wire,expected).bytes(),StrictJson.EXPLICIT_MAX_BYTES));
        for(String malformed:List.of("01","+1","1.0","18446744073709551616")) {
            ObjectNode bad=external.deepCopy();bad.put("snapshot_revision",malformed);
            assertThrows(IllegalArgumentException.class,()->FactionReadReplay.decodeSemanticBody(new RawJson(StrictJson.canonical(bad)),expected));
        }
        ObjectNode wrongType=external.deepCopy();wrongType.put("snapshot_revision",true);
        assertThrows(IllegalArgumentException.class,()->FactionReadReplay.decodeSemanticBody(new RawJson(StrictJson.canonical(wrongType)),expected));
        ObjectNode missing=external.deepCopy();missing.remove("snapshot_revision");
        assertThrows(IllegalArgumentException.class,()->FactionReadReplay.decodeSemanticBody(new RawJson(StrictJson.canonical(missing)),expected));
    }
    @Test void actualTransportUnknownPublishesNoFactionValueAndReceivesNoKnownCredit() throws Exception {
        var installed=new AtomicReference<FactionAlertReadService.Contracts>();
        var held=new AtomicReference<DriverObservationAssembler.Complete>();var delivered=new AtomicInteger();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("transport-unknown"),false,scenario(installed,held,false))) {
            fixture.loseReadAckOnce();fixture.bindKnownReadObserver((same,contract,known)->{
                    if(FactionAlertModel.STEP.equals(known.receipt().request().operation().value()))delivered.incrementAndGet();
                });
            var initial=separatedInitialFrame(fixture);
            fixture.writer.locked(same->{
                initialize(fixture,same,initial);
                bindRefresh(fixture);
                fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
                    held.set(lease.frame());try {
                        var result=read(fixture,same,installed.get(),lease.frame(),lease.validUntil());
                        if(!(result instanceof PlanningReadResult.Unavailable<FactionAlertReadService.Observation> unavailable))
                            throw new AssertionError("lost original response must remain Unavailable: "+result);
                        var unknown=assertInstanceOf(NativeActionPort.Unknown.class,unavailable.original().orElseThrow());
                        assertEquals(NativeActionPort.FailureStage.RESPONSE_WAIT,unknown.failureCause().orElseThrow().stage());
                        assertTrue(WarEntryCollector.collect(lease.frame().semantic(),List.of()).factionAlert().isEmpty());
                    }finally{held.set(null);}return null;
                });
                fixture.driverAuthority().withFrozenFacts(same,frozen->{
                    var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                    assertEquals(Nil.INSTANCE,known.auxiliary().get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
                    assertFalse(object(known.auxiliary().get(DriverSemanticReadState.SOURCES),"source table").members().containsKey("FACTION_ALERTS"));
                    return null;
                });return null;
            });
            assertEquals(0,delivered.get());assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void actualAcknowledgedWrongNativeBodiesCannotBecomeKnownOrPublishASemanticSource() throws Exception {
        for(NativeFault fault:List.of(NativeFault.ACTOR,NativeFault.DATE,NativeFault.NATIVE_REVISION,
                NativeFault.BOOLEAN_SEQUENCE,NativeFault.OPERATION)) {
            var installed=new AtomicReference<FactionAlertReadService.Contracts>();
            var held=new AtomicReference<DriverObservationAssembler.Complete>();var delivered=new AtomicInteger();
            try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("wrong-native-"+fault.name()),false,
                    scenario(installed,held,false,fault))) {
                fixture.bindKnownReadObserver((same,contract,known)->{
                    if(FactionAlertModel.STEP.equals(known.receipt().request().operation().value()))delivered.incrementAndGet();
                });
                var initial=separatedInitialFrame(fixture);
                fixture.writer.locked(same->{
                    initialize(fixture,same,initial);bindRefresh(fixture);
                    fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
                        held.set(lease.frame());try {
                            var result=read(fixture,same,installed.get(),lease.frame(),lease.validUntil());
                            if(!(result instanceof PlanningReadResult.Unavailable<FactionAlertReadService.Observation> unavailable))
                                throw new AssertionError("acknowledged wrong Native body must remain Unavailable: "+fault+" "+result);
                            var acknowledged=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original().orElseThrow());
                            assertTrue(acknowledged.nativeOk(),"ACK must not grant a wrong body Known/publication credit");
                        }finally{held.set(null);}return null;
                    });
                    fixture.driverAuthority().withFrozenFacts(same,frozen->{
                        var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                        assertEquals(Nil.INSTANCE,known.auxiliary().get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
                        assertFalse(object(known.auxiliary().get(DriverSemanticReadState.SOURCES),"source table").members().containsKey("FACTION_ALERTS"));
                        return null;
                    });return null;
                });
                assertEquals(0,delivered.get());assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
            }
        }
    }
}
