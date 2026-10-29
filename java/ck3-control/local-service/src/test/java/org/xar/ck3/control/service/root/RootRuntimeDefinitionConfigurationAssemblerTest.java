package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionConfigurationAssembler.DeclaredDomainInputs;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionConfigurationAssembler.PhysicalOriginals;

/** Pure cases below are complete shape-only DATA, never physical inputs or readiness.
 * Independent typed groups reach actual composition without a source or publication authority. */
class RootRuntimeDefinitionConfigurationAssemblerTest {
    private static final Path SHAPE=Path.of("definition-assembly-shape-only").toAbsolutePath().normalize();
    private static final Instant OBSERVED=Instant.parse("2026-10-24T09:30:00Z");
    private static final Instant REVIEW=Instant.parse("2026-10-24T10:30:00Z");
    private static final String HASH="0".repeat(64);

    @Test void twoIndependentCompleteGroupsUseTheOnlyConfigurationAndPublicationCodecs()throws Exception {
        PhysicalOriginals physical=shapePhysical();DeclaredDomainInputs domains=shapeDomains();
        var config=RootRuntimeDefinitionConfigurationAssembler.configuration(physical,domains,"software-test-machine",OBSERVED,REVIEW);
        assertEquals(physical.applicationRef(),config.applicationRef());assertEquals(physical.sources(),config.sources());
        assertEquals(physical.closures(),config.closures());assertEquals(physical.originalData(),config.originalData());
        assertEquals(domains.governance(),config.governance());assertEquals(domains.finance(),config.finance());
        assertEquals(domains.army(),config.army());assertEquals(domains.prisoners(),config.prisoners());
        assertEquals(domains.family(),config.family());assertEquals(domains.frontend(),config.frontend());
        assertEquals(domains.interactions(),config.interactions());assertEquals(domains.activity(),config.activity());
        assertEquals(domains.crossRun(),config.crossRun());assertEquals(domains.incidents(),config.incidents());
        assertEquals(domains.publicCatalog(),config.publicCatalog());assertEquals(domains.startup(),config.startup());
        byte[] encoded=RootRuntimeDefinitions.encodeConfiguration(config);
        assertEquals(config,RootRuntimeDefinitions.decodeConfiguration(encoded));
        var request=new RootRuntimeDefinitionsPublisher.Request(RootRuntimeDefinitionsPublisher.SCHEMA,config,
                shapeFile("binding.json"),SHAPE.resolve("first-definitions.json").toString());
        assertEquals(request,RootRuntimeDefinitionsPublisher.decodeRequest(RootRuntimeDefinitionsPublisher.encodeRequest(request)));
        // These pure constructors/codecs deliberately never call Publisher.prepare or issue a native/output witness.
        assertFalse(Files.exists(SHAPE.resolve("first-definitions.json"),LinkOption.NOFOLLOW_LINKS));
    }

    @Test void publicationQuoteRetainsOneExplicitObservationWhileTheActualFreshnessClockMayAdvance()throws Exception {
        var physical=shapePhysical();var domains=shapeDomains();
        var held=RootRuntimeDefinitionConfigurationAssembler.configuration(physical,domains,"software-test-machine",OBSERVED,REVIEW);
        byte[] quote=RootRuntimeDefinitions.encodeConfiguration(held);
        var admitted=RootRuntimeDefinitionConfigurationAssembler.configuration(physical,domains,"software-test-machine",OBSERVED,REVIEW);
        assertArrayEquals(quote,RootRuntimeDefinitions.encodeConfiguration(admitted));
        // This is the actual first-version failure mechanism: refreshing a header while awaiting the issuer changes the quoted DATA.
        var changedHeader=RootRuntimeDefinitionConfigurationAssembler.configuration(physical,domains,"software-test-machine",OBSERVED.plusSeconds(1),REVIEW);
        assertFalse(Arrays.equals(quote,RootRuntimeDefinitions.encodeConfiguration(changedHeader)));
        assertEquals(held,RootRuntimeDefinitions.decodeConfiguration(quote));
    }

    @Test void theExistingModelRejectsMissingRolesDuplicateRolesNullDomainsAndInvalidReview() {
        var physical=shapePhysical();var domains=shapeDomains();
        var missing=new PhysicalOriginals(physical.applicationRef(),physical.storageLeaseRef(),physical.nativeLaunchPlanRef(),
                physical.runtimePackageRequestRef(),physical.sourceIndex(),physical.sources().subList(1,physical.sources().size()),
                physical.closures(),physical.originalData());
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitionConfigurationAssembler.configuration(
                missing,domains,"software-test-machine",OBSERVED,REVIEW));
        var duplicate=new ArrayList<>(physical.sources());duplicate.set(0,duplicate.get(1));
        var wrong=new PhysicalOriginals(physical.applicationRef(),physical.storageLeaseRef(),physical.nativeLaunchPlanRef(),
                physical.runtimePackageRequestRef(),physical.sourceIndex(),duplicate,physical.closures(),physical.originalData());
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitionConfigurationAssembler.configuration(
                wrong,domains,"software-test-machine",OBSERVED,REVIEW));
        assertThrows(NullPointerException.class,()->new DeclaredDomainInputs(domains.governance(),domains.finance(),domains.army(),
                domains.prisoners(),domains.family(),domains.frontend(),domains.interactions(),domains.activity(),domains.crossRun(),
                domains.incidents(),domains.publicCatalog(),null));
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitionConfigurationAssembler.configuration(
                physical,domains,"software-test-machine",OBSERVED,OBSERVED));
        for(DataRole role:DataRole.values())if(role!=DataRole.ROLLBACK_PROOF) {
            var rows=physical.originalData().stream().filter(row->row.role()!=role).toList();
            var lacking=new PhysicalOriginals(physical.applicationRef(),physical.storageLeaseRef(),physical.nativeLaunchPlanRef(),
                    physical.runtimePackageRequestRef(),physical.sourceIndex(),physical.sources(),physical.closures(),rows);
            assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitionConfigurationAssembler.configuration(
                    lacking,domains,"software-test-machine",OBSERVED,REVIEW),role.name());
        }
    }

    @Test void independentPhysicalListsAreCopiedAndWrongWireFieldsStillReachTheUniqueStrictDecoder()throws Exception {
        var original=shapePhysical();var sources=new ArrayList<>(original.sources());
        var physical=new PhysicalOriginals(original.applicationRef(),original.storageLeaseRef(),original.nativeLaunchPlanRef(),
                original.runtimePackageRequestRef(),original.sourceIndex(),sources,original.closures(),original.originalData());
        sources.clear();assertEquals(SourceRole.values().length,physical.sources().size());
        assertThrows(UnsupportedOperationException.class,()->physical.sources().clear());
        var config=RootRuntimeDefinitionConfigurationAssembler.configuration(physical,shapeDomains(),"software-test-machine",OBSERVED,REVIEW);
        var request=new RootRuntimeDefinitionsPublisher.Request(RootRuntimeDefinitionsPublisher.SCHEMA,config,
                shapeFile("binding.json"),SHAPE.resolve("first-definitions.json").toString());
        var mapper=ControlBuild.strictMapper();byte[] wire=RootRuntimeDefinitionsPublisher.encodeRequest(request);
        var missing=(ObjectNode)mapper.readTree(wire);((ObjectNode)missing.get("configuration")).remove("startup");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(missing)));
        var wrongType=(ObjectNode)mapper.readTree(wire);((ObjectNode)wrongType.get("output_binding_ref")).put("bytes",true);
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(wrongType)));
        var absent=(ObjectNode)mapper.readTree(wire);absent.putNull("configuration");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(absent)));
        var template=(ObjectNode)mapper.readTree(wire);template.put("configuration_template","not accepted");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(template)));
    }

    @Test void dataCompositionPreservesDeclaredClosuresWithoutSourceCohortQualification() {
        var complete=shapePhysical();var original=complete.closures().stream().filter(row->row.role()==ClosureRole.SWAY).findFirst().orElseThrow();
        for(var missing:original.sources()) {
            if(missing.equals(complete.sources().stream().filter(row->row.role()==SourceRole.PRISONER_EPISODE_LEDGER).findFirst().orElseThrow().selected()))continue;
            var reduced=new ProducerClosure(ClosureRole.SWAY,original.sources().stream().filter(row->row!=missing).toList());
            var closures=complete.closures().stream().map(row->row.role()==ClosureRole.SWAY?reduced:row).toList();
            var incomplete=new PhysicalOriginals(complete.applicationRef(),complete.storageLeaseRef(),complete.nativeLaunchPlanRef(),
                    complete.runtimePackageRequestRef(),complete.sourceIndex(),complete.sources(),closures,complete.originalData());
            var composed=RootRuntimeDefinitionConfigurationAssembler.configuration(incomplete,shapeDomains(),"software-test-machine",OBSERVED,REVIEW);
            assertEquals(closures,composed.closures());
        }
    }

    @Test void independentDataGroupsReachPublisherAndRequestWithoutSourceAuthorityOrWritingDefinitions()throws Exception {
        var physical=shapePhysical();var domains=shapeDomains();Path target=SHAPE.resolve("independent-definitions.json");
        var assembled=RootRuntimeDefinitionConfigurationAssembler.assemble(physical,domains,OBSERVED,REVIEW,
                shapeFile("passive-binding.json"),target,Clock.systemUTC());
        var compatible=RootRuntimeDefinitionConfigurationAssembler.assemble(physical,domains,OBSERVED,REVIEW,
                shapeFile("passive-binding.json"),target,null,null,Clock.systemUTC());
        assertEquals(assembled.request(),compatible.request());assertArrayEquals(assembled.requestBytes(),compatible.requestBytes());
        assembled.requireCurrent(Clock.fixed(REVIEW.plusSeconds(86400),java.time.ZoneOffset.UTC));
        assertEquals(OBSERVED.toString(),assembled.request().configuration().observedAtUtc());
        assertEquals(REVIEW.toString(),assembled.request().configuration().reviewAtUtc());
        assertEquals(org.xar.ck3.control.build.WindowsJobProcess.currentMachineId(),assembled.request().configuration().machineId());
        assertEquals(physical.sources(),assembled.request().configuration().sources());assertEquals(domains.startup(),assembled.request().configuration().startup());
        assertEquals(assembled.request(),RootRuntimeDefinitionsPublisher.decodeRequest(assembled.requestBytes()));
        assertFalse(Files.exists(target,LinkOption.NOFOLLOW_LINKS));
    }

    private static FileRef shapeFile(String name){return new FileRef(SHAPE.resolve(name).toString(),1,HASH);}
    private static SelectedSource shapeSource(String target){return new SelectedSource(target,new ExactRef(SHAPE.resolve(Path.of(target).getFileName()).toString(),1,HASH));}
    private static PhysicalOriginals shapePhysical() {
        var sources=new ArrayList<SourcePin>();
        for(SourceRole role:SourceRole.values()) {
            SourceKind kind=RootRuntimeDefinitionModel.expectedKind(role);
            String suffix=switch(kind){case JAVA->".java";case NATIVE->".cpp";case ORIGINAL_PYTHON->".py";case STOCK_SCRIPT->".txt";};
            String target=role==SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION?ARMY_WAR_EXIT_TRUCE_TARGET:"shape/"+role.name()+suffix;
            sources.add(new SourcePin(role,kind,shapeSource(target)));
        }
        SelectedSource episode=sources.stream().filter(row->row.role()==SourceRole.PRISONER_EPISODE_LEDGER).findFirst().orElseThrow().selected();
        var sway=new ArrayList<SelectedSource>();sway.add(episode);
        for(String name:List.of("RootPublicPauseRuntime","RootPublicPauseStepProducts","RootPublicPausePublicResult","RootPublicPauseArchiveClassifier"))
            sway.add(shapeSource("local-service/src/main/java/org/xar/ck3/control/service/root/"+name+".java"));
        sway.add(shapeSource("application/src/main/java/org/xar/ck3/control/application/advance/GenericPublicPauseRecovery.java"));
        sway.add(shapeSource("application/src/main/java/org/xar/ck3/control/application/effects/control/ControlSequenceObservation.java"));
        sway.add(sources.stream().filter(row->row.role()==SourceRole.FRONTEND_ORIGINAL_DRIVER).findFirst().orElseThrow().selected());
        var closures=Arrays.stream(ClosureRole.values()).map(role->new ProducerClosure(role,role==ClosureRole.SWAY?sway:List.of(episode))).toList();
        var data=Arrays.stream(DataRole.values()).filter(role->role!=DataRole.ROLLBACK_PROOF)
                .map(role->new DataPin(role,shapeFile(role.name()+".json"))).toList();
        return new PhysicalOriginals(shapeFile("application.json"),shapeFile("lease.json"),shapeFile("plan.json"),shapeFile("runtime-request.json"),
                new SourceIndex(shapeFile("source-index.json.gz"),1,HASH),sources,closures,data);
    }
    private static DeclaredDomainInputs shapeDomains() {
        var build=new Build("1.20.0.4",HASH);
        var reads=Arrays.stream(FinanceQuery.values()).map(query->new FinanceRead(query,shapeSource("shape/"+query.name()+".java"),
                new ReadPermission("shape-capability-"+query.name(),"shape-permission-"+query.name(),PermissionMode.ADVERTISED_CAPABILITY,WireProfile.EXECUTE_STEP))).toList();
        var finance=new FinanceInputs(reads,shapeSource("shape/GiftCold.java"),
                new ReadPermission("shape-gift-cold","shape-gift-permission",PermissionMode.ADVERTISED_CAPABILITY,WireProfile.EXECUTE_STEP));
        var activity=new ActivityInputs(Arrays.stream(ActivityNativeContracts.Query.values())
                .map(query->new ActivityQuery(query,shapeSource("shape/ActivityRead"+query.name()+".java"))).toList(),
                Arrays.stream(ActivityActionRoutes.Kind.values()).map(kind->new ActivityMutation(kind,shapeSource("shape/ActivityAction"+kind.name()+".java"))).toList());
        return new DeclaredDomainInputs(new GovInputs(build,"shape-governance",
                List.of(GovernanceActionPreparation.OPERATIONS.stream().sorted().findFirst().orElseThrow()),1,3),finance,
                new ArmyInputs(1000,1000,"shape-army"),new PrisonerInputs(build,"shape-prisoner"),
                new FamilyInputs(true,true,true,true,new MatrilinealPair(1,2)),new FrontendInputs(build,1000,1000,1,1,"shape-frontend"),
                new InteractionInputs(build,List.of(1L),List.of(List.of(1)),List.of(1)),activity,
                new CrossRunInputs(new OriginalHistory(SHAPE.resolve("one-life-history.json").toString(),shapeFile("one-life-history.json"))),
                new IncidentInputs(SHAPE.resolve("incidents").toString(),SHAPE.resolve("scans").toString(),4096),
                new PublicInputs(1000,1000,List.of(PublicMethod.values()[0])),new StartupInputs(1,1000,"shape-startup"));
    }
}
