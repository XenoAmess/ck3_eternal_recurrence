package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.lang.reflect.Proxy;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;

/** Terminal DATA/serialization seam only; public FullSnapshot values grant no physical source or Game authority. */
final class DriverTerminalStrategyStateTest {
    private record Terminal(DriverCapabilityStateProducerTest.Fixture fixture,Known known,
            DriverObservationAssembler.FullSnapshot full,LifecycleIdentity identity) { }
    private Terminal terminal() {
        var f=DriverCapabilityStateProducerTest.fresh();Known before=DriverCapabilityStateProducerTest.published(f);
        Obj raw=DriverJson.object(f.actual().state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        raw=raw.with("played_character",object(raw.get("played_character"),"played_character").with("alive",new Bool(false)));
        var actual=DriverObservationAssemblerTest.actual(new String(DriverJson.encode(raw),java.nio.charset.StandardCharsets.UTF_8));
        var extras=new LinkedHashMap<>(before.auxiliary().members());
        for(String key:List.of("backend_id","source","diagnostics"))extras.put(key,before.observation().orElseThrow().originalSemanticFields().get(key));
        var driver=f.archive().materialReferenceOf(new RawJson(before.driver().encode()));
        var manifest=DriverObservationEvidenceReader.encode(before,actual,f.frame().identity().frame().revision(),f.frame().identity().observationVersion(),f.frame().source(),new Obj(extras),driver);
        var manifestRef=f.archive().preserveMaterial(manifest);var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(before.driver().encode()),actual);
        var known=new Known(before.driver(),before.stamp(),before.originalHistoryBasis(),before.actionRows(),before.auxiliary(),before.loop(),Optional.of(facts));
        var full=new DriverObservationAssembler().projectFull(actual,facts,f.archive().preserveNativeFrame(actual));
        var hello=f.archive().preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("role",new Text("software-original-terminal-hello"))))));
        var qualification=f.archive().preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("role",new Text("software-original-terminal-source"))))));
        var projected=assertInstanceOf(LifecycleOriginFactory.Projected.class,LifecycleOriginFactory.project(full,hello,driver,qualification));
        assertEquals(LifecycleIdentity.TerminalReason.DEAD,projected.identity().terminalReason());
        return new Terminal(f,known,full,projected.identity());
    }
    private DriverPersistentPlanningState.Publication canonical(Terminal t) throws Exception {
        return DriverPersistentPlanningState.crossRun(canonicalSession(t,CrossRunPlanning.empty()),t.known(),t.fixture().archive());
    }
    private ContinuityStorePort.Session canonicalSession(Terminal t,CrossRunPlanning.State state) {
        var archive=t.fixture().archive();byte[] bytes=CrossRunPlanning.encodeState(state);ExactRef body=archive.preserveMaterial(new RawJson(bytes));
        var identity=new WriterContracts.FileIdentity("1","9007199254740993","134000000000000001",Instant.parse("2026-10-23T00:00:00Z").toString(),body.bytes());
        var reference=new DomainBodies.BodyRef(DomainBodies.Slot.CROSS_RUN_PLANNING,CrossRunPlanningDomain.CONTRACT_SCHEMA,body,identity,List.of(t.fixture().initial().source()));
        var available=new DomainBodies.Available(reference,WriterContracts.canonical(bytes),t.fixture().initial().source(),List.of());
        var actualPin=new WriterContracts.Pin(body,identity);
        return (ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(proxy,method,args)->{
            if(method.getName().equals("readDomain")){assertEquals(DomainBodies.Slot.CROSS_RUN_PLANNING,args[0]);return available;}
            if(method.getName().equals("capturePin")){
                assertEquals(body,args[0]);assertEquals(CrossRunPlanning.MAX_BYTES,args[1]);return actualPin;
            }
            if(method.getName().equals("readPinned")){
                assertEquals(actualPin,args[0]);int maximum=(Integer)args[1];
                assertTrue(maximum>0);byte[] original=archive.loadMaterial(actualPin.reference()).bytes();
                assertTrue(original.length<=maximum);assertEquals(body.bytes(),original.length);
                assertEquals(body.sha256(),DriverJson.sha256(original));return original.clone();
            }
            if(method.getName().equals("verifyPin")){
                assertEquals(actualPin,args[0]);byte[] original=archive.loadMaterial(actualPin.reference()).bytes();
                assertEquals(identity.bytes(),original.length);assertEquals(body.sha256(),DriverJson.sha256(original));return null;
            }
            throw new UnsupportedOperationException("terminal data regression cannot execute a writer or Native action: "+method.getName());
        });
    }
    @Test void actualTerminalVerifierRequiresTheCurrentCanonicalBodyAndCannotReuseAnArchivedStrategyAfterDomainChange() throws Exception {
        var t=terminal();var archive=t.fixture().archive();var same=canonicalSession(t,CrossRunPlanning.empty());
        var canonical=DriverPersistentPlanningState.crossRun(same,t.known(),archive);
        var publication=DriverCapabilityStateProducer.observeTerminalStrategy(t.full(),t.identity(),t.known(),canonical,archive);
        var repository=new DriverFactsRepository(t.known());
        repository.locked(current->{repository.publishCapabilityInputs(t.known().stamp(),publication.expectedAuxiliarySha256(),publication);return null;});
        var after=repository.locked(current->(Known)current);
        assertEquals(CrossRunPlanning.empty(),DriverCapabilityStateProducer.requireCurrentTerminalStrategy(same,after,archive));
        var changed=new CrossRunPlanning.State(List.of(),CrossRunPlanning.empty().nextRunPlan(),Optional.of(Instant.parse("2026-10-24T00:00:00Z")));
        var changedSession=canonicalSession(t,changed);
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.requireCurrentTerminalStrategy(changedSession,after,archive));
        var forged=new Known(after.driver(),after.stamp(),after.originalHistoryBasis(),after.actionRows(),
                after.auxiliary().with("one_life_strategy",new Obj(Map.of())),after.loop(),after.observation());
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.requireCurrentTerminalStrategy(same,forged,archive));
    }
    @Test void sourceBoundTerminalStrategyUsesItsOwnSerializationAndCannotBecomeAnOrdinaryCapabilityCapsule() throws Exception {
        var t=terminal();var archive=t.fixture().archive();
        var produced=DriverCapabilityStateProducer.observeTerminalStrategy(t.full(),t.identity(),t.known(),canonical(t),archive);
        var repository=new DriverFactsRepository(t.known());
        repository.locked(current->{repository.publishCapabilityInputs(t.known().stamp(),produced.expectedAuxiliarySha256(),produced);return null;});
        Known after=repository.locked(current->(Known)current);
        assertSame(Nil.INSTANCE,after.auxiliary().get(DriverRuntimeCapabilities.AUXILIARY_KEY));
        assertEquals(produced.auxiliary(),DriverCapabilityStateProducer.replayTerminal(after,produced.source(),archive));
        assertEquals(produced.auxiliary(),DriverJson.object(DriverJson.encode(produced.auxiliary()),DriverJson.MAX_NATIVE_BYTES));
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.replay(t.fixture().frame(),after,produced.source(),archive));
        var state=DriverJson.object(archive.loadMaterial(produced.source()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(new Text(DriverCapabilityStateProducer.TERMINAL_STATE_SCHEMA),state.get("schema"));
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.application.capabilities.DynamicCapabilities.DriverInputs.decode(t.fixture().frame(),after,produced.source(),DriverJson.encode(state)));
    }
    @Test void terminalReplayRejectsChangedCanonicalStrategyAndWrongActualLifecycleIdentity() throws Exception {
        var t=terminal();var archive=t.fixture().archive();var canonical=canonical(t);
        var produced=DriverCapabilityStateProducer.observeTerminalStrategy(t.full(),t.identity(),t.known(),canonical,archive);
        var after=new Known(t.known().driver(),t.known().stamp(),t.known().originalHistoryBasis(),t.known().actionRows(),produced.auxiliary(),t.known().loop(),t.known().observation());
        var state=DriverJson.object(archive.loadMaterial(produced.source()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var owner=object(state.get("owner_auxiliary"),"owner_auxiliary").with("one_life_strategy",new Obj(Map.of()));
        var changed=archive.preserveMaterial(new RawJson(DriverJson.encode(state.with("owner_auxiliary",owner))));
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.replayTerminal(after,changed,archive));
        var identity=t.identity();var shifted=new LifecycleIdentity(identity.machineId(),identity.game(),"wrong-terminal-session",identity.connectionGeneration(),identity.subject(),identity.frame(),identity.currentPlayer(),identity.terminalReason(),identity.evidence(),identity.observedAt());
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.observeTerminalStrategy(t.full(),shifted,t.known(),canonical,archive));
    }
    @Test void samePidWithDifferentNativeBirthCannotPublishTerminalStrategy() throws Exception {
        var t=terminal();var old=t.known().stamp();var game=old.game();
        var otherBirth=new org.xar.ck3.control.contracts.GameGeneration(game.pid(),new org.xar.ck3.control.contracts.PythonOnlyUInt64(game.creationFiletime().value().add(java.math.BigInteger.ONE)));
        var stamp=new DriverSnapshotFacts.Stamp(old.driverVersion(),old.episodeEpoch(),otherBirth,old.episodeRunId(),old.driverSha256());
        var original=t.known().observation().orElseThrow();var transport=original.transport();
        var otherTransport=new NativeObservationPort.TransportSession(transport.machineId(),otherBirth,transport.connectionGeneration(),transport.sessionId());
        // Keep the public Known value internally consistent. The terminal FullSnapshot still has its actual original birth.
        var otherFacts=new DriverObservationFacts(original.driver(),original.driverVersion(),original.episodeEpoch(),otherTransport,
                original.snapshotId(),original.nativeRevision(),original.nativeStateSha256(),original.publicRevision(),original.observationVersion(),
                original.source(),original.originalSemanticFields(),original.semanticFactsEvidence());
        var crossed=new Known(t.known().driver(),stamp,t.known().originalHistoryBasis(),t.known().actionRows(),t.known().auxiliary(),t.known().loop(),Optional.of(otherFacts));
        var crossedTerminal=new Terminal(t.fixture(),crossed,t.full(),t.identity());var actual=canonical(crossedTerminal);
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.observeTerminalStrategy(t.full(),t.identity(),crossed,actual,t.fixture().archive()));
    }
}
