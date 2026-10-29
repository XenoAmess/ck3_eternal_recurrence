package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;

/** Software producer/custody regressions. None of these packets grants a live Game qualification. */
final class DriverPersistentPlanningStateTest {
    @TempDir Path directory;
    private record Configured(DriverCapabilityStateProducerTest.Fixture fixture,Known current) { }
    private Configured configured() {
        var f=DriverCapabilityStateProducerTest.fresh();Path root=directory.toAbsolutePath().normalize();
        var config=new DynamicCapabilities.Configuration(Optional.of(root),Optional.empty(),3,3,false,false);
        var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.of(root.resolve("queue")),Optional.of(root.resolve("driver.json")));
        ExactRef policy=f.archive().preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("policy",new Text("controlled-software-source"))))));
        var initial=DriverCapabilityStateProducer.initializeNewEpisode(f.frame(),f.current(),config,presentation,policy,f.archive());
        return new Configured(f,with(f.current(),initial.auxiliary()));
    }
    @Test void configuredActualAbsencePublishesOnceAndRoundTripsThroughSoleProducerAndRepository() throws Exception {
        var c=configured();var f=c.fixture();var original=c.current();
        var persistent=DriverPersistentPlanningState.initializeCooldown(f.frame(),original,new NativeCheckpointFiles(),f.archive());
        var publication=DriverCapabilityStateProducer.observePersistentPlanning(f.frame(),original,persistent,f.archive());
        var repository=new DriverFactsRepository(original);
        repository.locked(current->{repository.publishCapabilityInputs(original.stamp(),publication.expectedAuxiliarySha256(),publication);return null;});
        var after=repository.locked(current->(Known)current);
        assertEquals(publication.auxiliary(),DriverCapabilityStateProducer.replay(f.frame(),after,publication.source(),f.archive()));
        assertEquals(publication.auxiliary(),DriverJson.object(DriverJson.encode(publication.auxiliary()),DriverJson.MAX_NATIVE_BYTES));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.initializeCooldown(f.frame(),after,new NativeCheckpointFiles(),f.archive()));
        assertThrows(IllegalArgumentException.class,()->repository.locked(current->{repository.publishCapabilityInputs(original.stamp(),publication.expectedAuxiliarySha256(),publication);return null;}));
    }
    @Test void serializedPersistentStateCannotChangeFieldsOrOmitItsOriginalSource() throws Exception {
        var c=configured();var f=c.fixture();var publication=DriverPersistentPlanningState.initializeCooldown(f.frame(),c.current(),new NativeCheckpointFiles(),f.archive());
        DriverPersistentPlanningState.replay(publication.auxiliary(),f.archive());
        var state=object(publication.auxiliary().get(DriverPersistentPlanningState.COOLDOWN_STATE),"state");
        var wrong=publication.auxiliary().with(DriverPersistentPlanningState.COOLDOWN_STATE,state.with("actor_character_id",new Bool(true)));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(wrong,f.archive()));
        var fields=new java.util.LinkedHashMap<>(publication.auxiliary().members());fields.remove(DriverPersistentPlanningState.COOLDOWN_SOURCE);
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(new Obj(fields),f.archive()));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(publication.auxiliary().with(DeclarationOpportunityCooldown.VIEW_KEY,Nil.INSTANCE),f.archive()));
    }
    @Test void originalLegacyFileIsActuallyReadAndAChangedArchivedCaptureFailsReplay() throws Exception {
        var c=configured();var f=c.fixture();var files=new NativeCheckpointFiles();
        byte[] original=org.xar.ck3.control.contracts.StrictJson.canonical(DeclarationOpportunityCooldown.encode(DeclarationOpportunityCooldown.initial(DeclarationOpportunityCooldown.frame(f.frame()))));
        files.createNew(directory.toAbsolutePath().resolve(DeclarationOpportunityCooldown.LEGACY_FILENAME),original);
        var publication=DriverPersistentPlanningState.initializeCooldown(f.frame(),c.current(),files,f.archive());
        DriverPersistentPlanningState.replay(publication.auxiliary(),f.archive());
        var proof=DriverJson.object(f.archive().loadMaterial(publication.source()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var input=object(proof.get("input"),"input");var file=object(input.get("original"),"original");
        var archived=DriverObservationEvidenceReader.reference(file.get("archived"));
        f.archive().materials.put(archived,new RawJson(DriverJson.encode(new Obj(Map.of("corrupted",new Bool(true))))));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(publication.auxiliary(),f.archive()));
    }
    @Test void absentConfiguredDirectoryIsIncompleteRatherThanAnEmptyCooldown() {
        var f=DriverCapabilityStateProducerTest.fresh();
        assertThrows(IOException.class,()->DriverPersistentPlanningState.initializeCooldown(f.frame(),DriverCapabilityStateProducerTest.published(f),new NativeCheckpointFiles(),f.archive()));
    }
    @Test void initialBaselineWatermarkIsExplicitAndCannotDisappearInSerialization() throws Exception {
        var c=configured();var f=c.fixture();var publication=DriverPersistentPlanningState.initializeCooldown(f.frame(),c.current(),new NativeCheckpointFiles(),f.archive());
        var proof=DriverJson.object(f.archive().loadMaterial(publication.source()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(new Text("xar.driver-persistent-planning-source/v2"),proof.get("schema"));
        var input=object(proof.get("input"),"input");assertEquals(new Arr(List.of()),input.get("baseline_receipts"));
        assertEquals(proof,DriverJson.object(DriverJson.encode(proof),DriverJson.MAX_NATIVE_BYTES));
        var fields=new java.util.LinkedHashMap<>(input.members());fields.remove("baseline_receipts");
        var source=f.archive().preserveMaterial(new RawJson(DriverJson.encode(proof.with("input",new Obj(fields)))));
        var changed=publication.auxiliary().with(DriverPersistentPlanningState.COOLDOWN_SOURCE,DriverRuntimeCapabilities.referenceJson(source));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(changed,f.archive()));
    }
    @Test void canonicalCrossRunBodyIsPinnedThenArchivedAndAllConsumersRejectAnInventedStrategy() throws Exception {
        crossRunBody(CrossRunPlanning.encodeState(CrossRunPlanning.empty()));
    }
    @Test void originalInsertionOrderBodyKeepsExactBytesThroughCanonicalViewAndPersistentReplay() throws Exception {
        Obj canonical=DriverJson.object(CrossRunPlanning.encodeState(CrossRunPlanning.empty()),CrossRunPlanning.MAX_BYTES);
        var fields=new java.util.LinkedHashMap<String,Value>();
        for(String name:List.of("next_run_plan","episodes","continue_as_heir_after_death","mode","format_version"))fields.put(name,canonical.get(name));
        byte[] legacy=org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(new Obj(fields));
        assertFalse(java.util.Arrays.equals(legacy,CrossRunPlanning.encodeState(CrossRunPlanning.empty())));
        crossRunBody(legacy);
    }
    private void crossRunBody(byte[] original) throws Exception {
        var f=DriverCapabilityStateProducerTest.fresh();Known current=DriverCapabilityStateProducerTest.published(f);
        ExactRef body=f.archive().preserveMaterial(new RawJson(original));
        var identity=new WriterContracts.FileIdentity("1","9007199254740993","134000000000000001",Instant.parse("2026-10-23T00:00:00Z").toString(),body.bytes());
        var reference=new DomainBodies.BodyRef(DomainBodies.Slot.CROSS_RUN_PLANNING,CrossRunPlanningDomain.CONTRACT_SCHEMA,body,identity,List.of(f.initial().source()));
        var available=new DomainBodies.Available(reference,WriterContracts.canonical(original),f.initial().source(),List.of());AtomicInteger pins=new AtomicInteger();
        var actualBytes=new java.util.concurrent.atomic.AtomicReference<>(original);
        var same=(ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(proxy,method,args)->{
            if(method.getName().equals("readDomain")){assertEquals(DomainBodies.Slot.CROSS_RUN_PLANNING,args[0]);return available;}
            if(method.getName().equals("capturePin")){assertEquals(body,args[0]);pins.incrementAndGet();return new WriterContracts.Pin(body,identity);}
            if(method.getName().equals("readPinned")){assertEquals(new WriterContracts.Pin(body,identity),args[0]);return actualBytes.get().clone();}
            if(method.getName().equals("verifyPin"))return null;
            throw new UnsupportedOperationException("strategy projection may not write the ledger: "+method.getName());
        });
        var publication=DriverPersistentPlanningState.crossRun(same,current,f.archive());assertEquals(1,pins.get());
        var proof=DriverJson.object(f.archive().loadMaterial(publication.source()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(body,DriverObservationEvidenceReader.reference(proof.get("body")));
        assertArrayEquals(original,f.archive().loadMaterial(DriverObservationEvidenceReader.reference(proof.get("archived_body"))).bytes());
        var produced=DriverCapabilityStateProducer.observePersistentPlanning(f.frame(),current,publication,f.archive());
        var after=with(current,produced.auxiliary());assertEquals(after.auxiliary(),DriverCapabilityStateProducer.replay(f.frame(),after,produced.source(),f.archive()));
        assertEquals(CrossRunPlanning.empty(),DriverPersistentPlanningState.requireCurrentStrategy(same,after,f.archive()));
        byte[] changed=original.clone();changed[0]='!';actualBytes.set(changed);
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.requireCurrentStrategy(same,after,f.archive()));
        actualBytes.set(original);
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(publication.auxiliary().with("one_life_strategy",new Obj(Map.of())),f.archive()));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(new Obj(Map.of("one_life_strategy",new Obj(Map.of()))),f.archive()));
    }

    @Test void bareOrdinaryEntryMustPublishRealConfigurationBeforeCooldownAndCannotResetIt() throws Exception {
        var f=DriverCapabilityStateProducerTest.fresh();Known bare=f.current();
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.initializeCooldown(f.frame(),bare,new NativeCheckpointFiles(),f.archive()));
        Path state=directory.toAbsolutePath().normalize();
        var configuration=new DynamicCapabilities.Configuration(Optional.of(state),Optional.empty(),1,1,false,false);
        var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.of(state.resolve("queue")),Optional.of(state.resolve("driver.json")));
        byte[] lifecycle=org.xar.ck3.control.contracts.StrictJson.canonical(
                org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson());
        ExactRef policy=f.archive().preserveMaterial(new RawJson(lifecycle));
        var initial=DriverCapabilityStateProducer.initializeNewEpisode(f.frame(),bare,configuration,presentation,policy,f.archive());
        var repository=new DriverFactsRepository(bare);
        repository.locked(current->{repository.publishCapabilityInputs(initial.expectedStamp(),initial.expectedAuxiliarySha256(),initial);return null;});
        Known configured=repository.locked(current->(Known)current);
        assertEquals(configuration,DynamicCapabilities.decodeConfiguration(object(configured.auxiliary().get("capability_configuration"),"configuration")));
        assertArrayEquals(lifecycle,f.archive().loadMaterial(policy).bytes());
        var cooldown=DriverPersistentPlanningState.initializeCooldown(f.frame(),configured,new NativeCheckpointFiles(),f.archive());
        var publication=DriverCapabilityStateProducer.observePersistentPlanning(f.frame(),configured,cooldown,f.archive());
        repository.locked(current->{repository.publishCapabilityInputs(publication.expectedStamp(),publication.expectedAuxiliarySha256(),publication);return null;});
        Known after=repository.locked(current->(Known)current);
        assertEquals(after.auxiliary(),DriverCapabilityStateProducer.replay(f.frame(),after,publication.source(),f.archive()));
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.initializeNewEpisode(f.frame(),after,configuration,presentation,policy,f.archive()));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.initializeCooldown(f.frame(),after,new NativeCheckpointFiles(),f.archive()));
    }
    private static Known with(Known original,Obj auxiliary){return new Known(original.driver(),original.stamp(),original.originalHistoryBasis(),original.actionRows(),auxiliary,original.loop(),original.observation());}
}
