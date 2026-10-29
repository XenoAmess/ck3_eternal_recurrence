package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.application.advance.PendingUiLifeAdvance;
import org.xar.ck3.control.application.action.PhysicalActionCodec;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence;
import org.xar.ck3.control.application.effects.NativeFinanceEffects;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionService;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage;

/** Uses the one actual full configuration fixture and its already constructed products; no synthetic Inputs/Core/Game. */
class RootRuntimeSourceClosureConsumerTest {
    private record Unit(RootRuntimeSelectedSources.Module module,Class<?> implementation) { }
    @Test void actualTotalProducerRetainsPendingUiAndPublicIdentityBeforeAnyConsumerRequeriesSources()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var retained=List.copyOf(input.selected().retainedSources());
        // Capture before any javaSource call: a test must not repair a missing production registration itself.
        for(var unit:List.of(new Unit(APPLICATION,PendingUiLifeAdvance.class),new Unit(CONTRACTS,NativeCharacterId.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.checkpoint.PublicCheckpointMaterialCapture.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData.class),
                new Unit(LOCAL_SERVICE,RootManagedSessionScope.class),new Unit(LOCAL_SERVICE,RootSavedOrdinaryReopen.class),new Unit(LOCAL_SERVICE,RootSaveCheckpointCommandProducer.class),
                new Unit(LOCAL_SERVICE,RootArmyReadPacketVerifier.class),new Unit(LOCAL_SERVICE,RootPublicStepFailureOriginals.class),
                new Unit(LOCAL_SERVICE,RootUnresolvedHistoryQualification.class),new Unit(LOCAL_SERVICE,RootRejectedPublicReadCollector.class),
                new Unit(LOCAL_SERVICE,RootPhysicalStatusReadAuthority.class),new Unit(LOCAL_SERVICE,RootDirectFixedWindowQueryAuthority.class),
                new Unit(LOCAL_SERVICE,RootMenuPhysicalStatusReads.class),
                new Unit(LOCAL_SERVICE,RootUnknownSentinelReadProfile.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.reads.PlanningPublicReadCollection.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.action.PauseConfirmation.class))){
            ExactRef original=expected(input,unit);
            assertTrue(retained.contains(original),"actual total producer omitted retained execution source "+unit.implementation().getName());
            input.plan().sources().requireLoadedClass(unit.implementation());
        }
        input.selected().requireInputs(input.inputs());input.selected().requireLoadedClasses(input.plan());
        assertSame(actual.factory(),actual.definitions().driverProductSources());
        var frontend=input.frontend();
        assertSame(frontend,actual.definitions().catalogFactory().sources().frontend());
        assertSame(frontend.initialPolicy(),frontend.originalDriverImport().frozenProfile().initialPolicy());
        assertEquals(frontend.originalDriverImport().frozenProfile().fixture().isPresent(),frontend.fixtureSources().isPresent());
    }
    @Test void actualStockConfigurationRetainsItsOriginalPairAndPinsWithoutGrantingAdmission()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var stock=input.settings().configuration().stockRead();
        var supplied=actual.definitions().catalogFactory().sources().army().stockConfiguration();
        assertEquals(stock!=null,supplied.isPresent(),"the actual Army product must preserve the explicitly configured Stock branch");
        input.settings().requireCurrent(input.clock());
        if(stock!=null){
            var configured=supplied.orElseThrow();
            assertSame(stock.limits(),configured.limits());
            assertSame(stock.pair(),configured.pair());assertSame(stock.pins(),configured.pins());
            for(var original:stock.originals())assertTrue(input.settings().retainedOriginals().contains(original),"actual settings lost a Stock input original");
        }
        var selected=input.selected();var retained=List.copyOf(selected.retainedSources());
        var formatter=new Unit(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.activity.ActivityPublic64.class);
        assertTrue(retained.contains(expected(input,formatter)),"actual total source producer omitted the Activity formatter");
        input.plan().sources().requireLoadedClass(formatter.implementation());
        selected.requireInputs(input.inputs());selected.requireLoadedClasses(input.plan());actual.factory().requireCurrent();
    }
    @Test void actualSettingsPersistTheStrictStockContractAndOriginalCustody(@TempDir Path temporary)throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var configured=input.settings().configuration();
        byte[] encoded=RootRuntimeDomainSettings.encode(configured);
        assertEquals(configured,RootRuntimeDomainSettings.decode(encoded));
        assertArrayEquals(encoded,RootRuntimeDomainSettings.encode(RootRuntimeDomainSettings.decode(encoded)));
        Path document=temporary.resolve("actual-domain-settings-v6.json");
        Files.write(document,encoded);
        var persisted=RootRuntimeDomainSettings.readExact(SharedSourceFiles.observe(document).source(),input.clock());
        assertEquals(configured,persisted.configuration());
        assertTrue(persisted.retainedOriginals().containsAll(configured.formalWar().originals()));
        assertTrue(persisted.retainedOriginals().containsAll(configured.normalExit().originals()));
        if(configured.stockRead()!=null)
            assertTrue(persisted.retainedOriginals().containsAll(configured.stockRead().originals()));
        persisted.requireCurrent(input.clock());
        Files.write(document,new byte[]{'\n'},StandardOpenOption.APPEND);
        assertThrows(IOException.class,()->persisted.requireCurrent(input.clock()));
    }
    @Test void actualSettingsRejectMissingOldOrCoercedStockWireFields()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        byte[] encoded=RootRuntimeDomainSettings.encode(input.settings().configuration());
        ObjectNode missing=settingsWire(encoded);missing.remove("stock_read");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(settingsBytes(missing)));
        ObjectNode old=settingsWire(encoded);old.put("schema","xar.java-root-domain-settings/v5");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(settingsBytes(old)));
        ObjectNode wrongStock=settingsWire(encoded);wrongStock.put("stock_read",false);
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(settingsBytes(wrongStock)));
        ObjectNode wrongName=settingsWire(encoded);wrongName.set("stock_reads",wrongName.remove("stock_read"));
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(settingsBytes(wrongName)));
        ObjectNode booleanBudget=settingsWire(encoded);((ObjectNode)booleanBudget.get("lifecycle")).put("action_budget_millis",true);
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(settingsBytes(booleanBudget)));
        ObjectNode fractionalBudget=settingsWire(encoded);((ObjectNode)fractionalBudget.get("lifecycle")).put("action_budget_millis",1.0);
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(settingsBytes(fractionalBudget)));
        ObjectNode unconfigured=settingsWire(encoded);unconfigured.putNull("stock_read");
        assertNull(RootRuntimeDomainSettings.decode(settingsBytes(unconfigured)).stockRead());
        input.settings().requireCurrent(input.clock());actual.factory().requireCurrent();
    }
    private static ObjectNode settingsWire(byte[] encoded)throws IOException {
        return ControlBuild.strictMapper().readValue(encoded,ObjectNode.class);
    }
    private static byte[] settingsBytes(ObjectNode wire)throws IOException {
        // Malformed boundary inputs must reach the decoder instead of failing producer canonicalization first.
        return ControlBuild.strictMapper().writeValueAsBytes(wire);
    }
    @Test void realActionMaterialFactoryConsumesQualifiedPhysicalGiftPilgrimAndCloseReaders()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        // Capture before prepare/javaSource: the consumer must not repair its own startup registration.
        var retained=List.copyOf(input.selected().retainedSources());
        var readerUnits=List.of(
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.NativeEffectEvidence.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.NativeEffectRegistry.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.RootGuardEvidence.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.advance.LifeAdvanceEvidence.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.advance.LifeAdvanceRootReplay.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.routecontact.RouteContactEvidenceArchive.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.routecontact.RouteContactSteps.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.family.FamilySendObservation.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.planning.military.WarHistorySteps.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.driver.DriverJson.class),
                new Unit(LOCAL_SERVICE,org.xar.ck3.control.service.sway.SwayRuntimeInstaller.class),
                new Unit(LOCAL_SERVICE,RootFamilySendRecordingMaterial.class),
                new Unit(LOCAL_SERVICE,RootDriverTransportRuntimeFactory.class),
                new Unit(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling.class),
                new Unit(APPLICATION,GiftActionHistoryEvidence.class),
                new Unit(APPLICATION,PhysicalActionCodec.class),new Unit(APPLICATION,FinanceReadContracts.class),
                new Unit(APPLICATION,NativeFinanceEffects.class),
                new Unit(LOCAL_SERVICE,RootGuiPresentation.class),new Unit(LOCAL_SERVICE,RootReligionPilgrimage.class),
                new Unit(LOCAL_SERVICE,RootNaturalTimeline.class),new Unit(LOCAL_SERVICE,RootPendingUiRuntime.class),
                new Unit(LOCAL_SERVICE,RootLifecycleRuntimeFactory.class),
                new Unit(NATIVE_TRANSPORT,ReligionService.class),new Unit(NATIVE_TRANSPORT,ReligionPilgrimage.class));
        var expectedReaders=new ArrayList<ExactRef>();
        for(var unit:readerUnits){
            var original=expected(input,unit);expectedReaders.add(original);
            assertTrue(retained.contains(original),"actual startup omitted a material reader before consumer lookup: "+unit.implementation().getName());
            input.plan().sources().requireLoadedClass(unit.implementation());
        }
        // These remain real startup/domain dependencies, outside this factory's direct reader inventory.
        for(var unit:List.of(new Unit(LOCAL_SERVICE,RootMilitaryControlStepRuntime.class),
                new Unit(LOCAL_SERVICE,RootRouteContactAdvanceRuntime.class),
                new Unit(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlActions.class),
                new Unit(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation.class))){
            assertTrue(retained.contains(expected(input,unit)),"actual startup lost its installed domain dependency: "+unit.implementation().getName());
            input.plan().sources().requireLoadedClass(unit.implementation());
        }
        var material=RootActionHistorySourcesFactory.prepare(input.inputs(),input.selected(),input.originals(),input.clock());
        var sources=material.sources();var readers=sources.materialReaders();
        assertEquals(27,expectedReaders.size());assertEquals(27,readers.size());
        assertEquals(new java.util.HashSet<>(expectedReaders),new java.util.HashSet<>(readers),
                "actual factory must retain the exact source-bound reader contract, from the actual H5 source41 factory");
        assertEquals(readers.size(),readers.stream().distinct().count());
        assertTrue(readers.size()<=32,"32 is the Sources DTO upper bound, not a required inventory size");
        // Use only existing exact retained originals to exercise that bound; no source or owner is fabricated.
        var overflow=new ArrayList<>(readers);
        for(var original:retained){if(overflow.size()==33)break;if(!overflow.contains(original))overflow.add(original);}
        assertEquals(33,overflow.size());
        assertThrows(IllegalArgumentException.class,()->new RootActionHistoryMaterialSourceFactory.Sources(
                sources.implementation(),sources.codec(),sources.publisher(),sources.recordingPolicy(),overflow));
        input.selected().requireCurrent();input.selected().requireLoadedClasses(input.plan());actual.factory().requireCurrent();
    }
    @Test void realReadHistoryConsumerRetainsFiniteFailureSourcesInsideTheConfiguredClosure()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var retained=List.copyOf(input.selected().retainedSources());
        var configured=input.inputs().closure(RootRuntimeDefinitionModel.ClosureRole.READ_HISTORY);
        var consumer=actual.definitions().catalogFactory().sources().readHistoryProducers();
        assertEquals(configured,consumer,"actual read-history catalog must consume the selected original closure");
        for(var unit:List.of(new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReadHistoryFailureMaterial.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverExecuteReadHistoryRegistry.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReturnedActionHistoryMaterial.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryMaterial.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.class),
                new Unit(LOCAL_SERVICE,RootPublicStepFailureOriginals.class),new Unit(LOCAL_SERVICE,RootApplicationAssembly.class),
                new Unit(LOCAL_SERVICE,RootApplicationSession.class),new Unit(LOCAL_SERVICE,RootNativeSourceAuthority.class))){
            var original=expected(input,unit);
            assertTrue(retained.contains(original),"actual total source producer omitted finite failed-read implementation");
            assertTrue(configured.contains(original),"configured READ_HISTORY omitted the exact current failed-read source");
            assertTrue(consumer.contains(original),"actual catalog read-history consumer lost a failed-read source");
            input.plan().sources().requireLoadedClass(unit.implementation());
        }
        for(Class<?> implementation:org.xar.ck3.control.application.driver.DriverReadHistoryPublisher.implementationTypes()){
            var original=expected(input,new Unit(APPLICATION,implementation));
            assertTrue(retained.contains(original),"actual source producer omitted a publisher implementation");
            assertTrue(configured.contains(original),"configured READ_HISTORY omitted the exact publisher implementation");
            assertTrue(consumer.contains(original),"actual catalog lost a publisher implementation");
            input.plan().sources().requireLoadedClass(implementation);
        }
        input.selected().requireInputs(input.inputs());input.selected().requireLoadedClasses(input.plan());
        actual.factory().requireCurrent();
    }
    @Test void actualReadHistoryClosureSerdePreservesExactSourcesAndRejectsMissingOrChangedProducer()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var configured=input.inputs().closure(RootRuntimeDefinitionModel.ClosureRole.READ_HISTORY);
        var mapper=ControlBuild.strictMapper();
        var listType=mapper.getTypeFactory().constructCollectionType(List.class,ExactRef.class);
        byte[] encoded=mapper.writeValueAsBytes(configured);
        List<ExactRef> restored=mapper.readValue(encoded,listType);
        assertEquals(configured,restored);
        assertEquals(restored,actual.definitions().catalogFactory().sources().readHistoryProducers());
        RootRuntimeSourceProducts.requireReadHistoryClosure(input.inputs(),input.selected(),restored);
        var original=expected(input,new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.class));
        var missing=new ArrayList<>(restored);assertTrue(missing.remove(original));
        assertThrows(IOException.class,()->RootRuntimeSourceProducts.requireReadHistoryClosure(input.inputs(),input.selected(),missing));
        var changed=new ArrayList<>(restored);
        String changedSha=(original.sha256().charAt(0)=='0'?"1":"0")+original.sha256().substring(1);
        changed.set(changed.indexOf(original),new ExactRef(original.path(),original.bytes(),changedSha));
        assertThrows(IOException.class,()->RootRuntimeSourceProducts.requireReadHistoryClosure(input.inputs(),input.selected(),changed));
        var wire=mapper.readTree(encoded);
        ((ObjectNode)wire.get(0)).put("bytes",true);
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(wire),listType));
        input.selected().requireInputs(input.inputs());input.selected().requireLoadedClasses(input.plan());
        actual.factory().requireCurrent();
    }
    @Test void realRoutePreparedRetainsTheExactCapabilityAndExistingCampaignDeadline()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var retained=List.copyOf(input.selected().retainedSources());
        var domains=actual.definitions().catalogFactory().sources().remainingDomains();
        var route=domains.routeAdvancePrepared();
        assertSame(route,domains.routeAdvancePrepared());
        assertEquals(RootRuntimeSourceProducts.exact(input.inputs().data(RootRuntimeDefinitionModel.DataRole.CAPABILITY_CONFIGURATION)),route.configuration().original());
        assertEquals(RootRuntimeSourceProducts.exact(input.inputs().data(RootRuntimeDefinitionModel.DataRole.CAMPAIGN_DEADLINE)),route.configuration().deadline().original());
        assertEquals(45,route.sources().all().size());
        for(var original:route.sources().all())assertTrue(retained.contains(original),"actual Route supplier omitted a retained source");
        for(var unit:List.of(new Unit(LOCAL_SERVICE,RootRouteContactAdvanceSourcesFactory.class),
                new Unit(LOCAL_SERVICE,RootRouteContactAdvanceRuntime.class),new Unit(LOCAL_SERVICE,RootRouteContactAdvanceResult.class),
                new Unit(LOCAL_SERVICE,RootRouteContactAdvancePublicProducts.class),new Unit(LOCAL_SERVICE,RootPublicStepFailureOriginals.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.routecontact.RouteContactComposite.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.routecontact.RouteContactEvidenceCodec.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.routecontact.RouteContactArchivedVerifier.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.capabilities.DynamicCapabilities.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.advance.AdvancePrimitiveEvidence.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay.class))){
            assertTrue(route.sources().all().contains(expected(input,unit)),"actual Route source closure lost "+unit.implementation().getName());
            input.plan().sources().requireLoadedClass(unit.implementation());
        }
        input.selected().requireInputs(input.inputs());input.selected().requireLoadedClasses(input.plan());
        actual.factory().requireCurrent();
    }
    @Test void actualMilitaryConstructorRetainsTheOneControlsPreparedAndItsLoadedSource()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var retained=List.copyOf(input.selected().retainedSources());
        var required=List.of(new Unit(LOCAL_SERVICE,RootMilitaryControlStepRuntime.class),
                new Unit(LOCAL_SERVICE,RootArmyStructuralStepRuntime.class),
                new Unit(LOCAL_SERVICE,RootPublicPauseRuntime.class),
                new Unit(LOCAL_SERVICE,RootPublicPauseStepProducts.class),
                new Unit(LOCAL_SERVICE,RootPublicPausePublicResult.class),
                new Unit(LOCAL_SERVICE,RootPublicPauseArchiveClassifier.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.effects.control.ControlSequenceObservation.class),
                new Unit(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralActions.class),
                new Unit(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralActionCodec.class),
                new Unit(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralEffects.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReturnedActionHistoryMaterial.class),
                new Unit(APPLICATION,org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.class));
        for(var unit:required){
            assertTrue(retained.contains(expected(input,unit)),"actual total constructor omitted military producer source: "+unit.implementation().getName());
            input.plan().sources().requireLoadedClass(unit.implementation());
        }
        var military=actual.definitions().catalogFactory().sources().military();
        assertNotNull(military.structural());assertSame(military.structural(),actual.definitions().catalogFactory().sources().military().structural());
        // The real producer verifies the complete native proof before constructing structural Sources4.
        // Installed source identity still requires the original Runtime checks; this consumer grants no live qualification.
        input.plan().sources().verify();
        assertNotNull(military.controls());assertSame(military.controls(),actual.definitions().catalogFactory().sources().military().controls());
        assertNotNull(military.publicPause());assertSame(military.publicPause(),actual.definitions().catalogFactory().sources().military().publicPause());
        input.selected().requireInputs(input.inputs());input.selected().requireLoadedClasses(input.plan());
    }
    private static ExactRef expected(RootDriverProductSourcesFactory.Input input,Unit unit)throws IOException {
        String target=unit.module().directory()+"/src/main/java/"+unit.implementation().getName().replace('.','/')+".java";
        var selected=input.inputs().sourceIndex().stream().filter(row->row.targetRelative().equals(target)).toList();
        if(selected.size()!=1)throw new IOException("actual complete configuration has no unique source for required consumer: "+target);
        return selected.getFirst().sourceRef();
    }
}
