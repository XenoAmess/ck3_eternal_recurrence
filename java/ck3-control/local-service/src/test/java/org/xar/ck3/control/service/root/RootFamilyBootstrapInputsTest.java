package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.family.FamilyInitialData;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Actual Java bootstrap producer, native temporary files and the existing input Guard.
 * Test issuer cards and Configuration source pins are software DATA; no runtime, writer or Game is admitted.
 */
final class RootFamilyBootstrapInputsTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-25T20:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private static final String SHA="a".repeat(64);
    private record Inputs(Path asset,List<RootJavaBootstrapInputs.Item> items,Configuration original,
            FamilyInitialData.Documents documents) { }
    private static FileRef write(Path path,byte[] bytes)throws IOException {
        Files.write(path,bytes);return FileRef.measure(path);
    }
    private Inputs inputs()throws IOException {
        Path asset=Files.createDirectory(root.resolve("asset"));
        var documents=new FamilyInitialData.Documents(new FamilyInitialData.Body(Slot.FAMILY,FamilyInitialData.History.ABSENT),
                new FamilyInitialData.Body(Slot.CHILD_MATRILINEAL,FamilyInitialData.History.EMPTY),
                new FamilyInitialData.Body(Slot.DEFAULT_MARRIAGE,FamilyInitialData.History.ABSENT));
        var items=new ArrayList<RootJavaBootstrapInputs.Item>();
        for(var body:documents.bodies()) {
            Kind kind=switch(body.slot()) {
                case FAMILY->Kind.FAMILY_DOMAIN;case CHILD_MATRILINEAL->Kind.CHILD_MATRILINEAL_DOMAIN;
                case DEFAULT_MARRIAGE->Kind.DEFAULT_MARRIAGE_DOMAIN;default->throw new AssertionError();
            };
            FileRef original=write(root.resolve(kind.name()+"-original.json"),FamilyInitialData.encode(body));
            items.add(new RootJavaBootstrapInputs.Item(kind,original,asset.resolve(kind.name()+".json").toString()));
        }
        FileRef other=write(root.resolve("other-required-data.json"),"{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        Configuration configuration=configuration(other);
        FileRef original=write(root.resolve("definitions-original.json"),RootRuntimeDefinitions.encodeConfiguration(configuration));
        items.add(new RootJavaBootstrapInputs.Item(Kind.RUNTIME_DEFINITIONS,original,asset.resolve("definitions.json").toString()));
        return new Inputs(asset,List.copyOf(items),configuration,documents);
    }
    private RootJavaBootstrapInputs.Request request(Inputs input,RootJavaBootstrapInputs.Mode mode,FileRef binding) {
        return new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,WindowsJobProcess.currentMachineId(),
                NOW.plusSeconds(3600).toString(),mode,binding,input.items());
    }
    /** Same existing Guard fixture records as RootBootstrapOutputGuardTest, with the real typed four-output quote. */
    private FileRef authority(Path asset,List<Output> outputs)throws IOException {
        Path control=Files.createDirectory(root.resolve("control"));String machine=WindowsJobProcess.currentMachineId();
        String observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","family-bootstrap-fixture",observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,outputs,List.of(),List.of());
        FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
        FileRef census=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef,CLOCK)));
        var policy=StrictJson.object();policy.put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","software-fixture-actual-volume-observation").put("machine_id",machine)
                .put("total_bytes",total).put("usable_bytes",free).put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"family-bootstrap-fixture",NOW.toString(),review,
                policyRef,declarationRef,census,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        return write(control.resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,
                "family-bootstrap-fixture",NOW.toString(),review,declarationRef,census,capacity)));
    }
    @Test void actualBootstrapWritesThreeTypedOriginalsAndDefinitionsConsumesTheirExactNewPins()throws Exception {
        Inputs input=inputs();var quote=RootJavaBootstrapInputs.prepare(request(input,RootJavaBootstrapInputs.Mode.QUOTE,null),CLOCK);
        assertEquals(4,quote.quote().size());
        FileRef binding=authority(input.asset(),quote.quote());
        var explicit=request(input,RootJavaBootstrapInputs.Mode.CREATE_NEW,binding);
        assertEquals(explicit,RootJavaBootstrapInputs.decodeRequest(RootJavaBootstrapInputs.encodeRequest(explicit)));
        var prepared=RootJavaBootstrapInputs.prepare(explicit,CLOCK);
        assertEquals(quote.quote(),prepared.quote());
        var written=prepared.createNew(CLOCK);assertEquals(4,written.size());
        var definitions=written.stream().filter(value->value.kind()==Kind.RUNTIME_DEFINITIONS).findFirst().orElseThrow();
        var current=RootRuntimeDefinitions.decodeConfiguration(RootRuntimeDefinitions.read(definitions.original(),RootRuntimeDefinitions.MAXIMUM_BYTES));
        assertEquals(input.original().applicationRef(),current.applicationRef());
        for(var body:input.documents().bodies()) {
            DataRole role=switch(body.slot()) {
                case FAMILY->DataRole.FAMILY_DOMAIN;case CHILD_MATRILINEAL->DataRole.CHILD_MATRILINEAL_DOMAIN;
                case DEFAULT_MARRIAGE->DataRole.DEFAULT_MARRIAGE_DOMAIN;default->throw new AssertionError();
            };
            Kind kind=Kind.valueOf(role.name());
            var actual=written.stream().filter(value->value.kind()==kind).findFirst().orElseThrow();
            assertEquals(actual.original(),current.data(role));
            assertNotEquals(input.original().data(role),current.data(role));
            assertEquals(body,FamilyInitialData.decode(body.slot(),RootRuntimeDefinitions.readData(new DataPin(role,current.data(role)))));
        }
        for(var pin:input.original().originalData())
            if(pin.role()!=DataRole.FAMILY_DOMAIN&&pin.role()!=DataRole.CHILD_MATRILINEAL_DOMAIN&&pin.role()!=DataRole.DEFAULT_MARRIAGE_DOMAIN)
                assertEquals(pin.originalRef(),current.data(pin.role()));
        var originals=new RootNativeFamilySourcesFactory.OriginalDocuments(exact(current.data(DataRole.FAMILY_DOMAIN)),
                exact(current.data(DataRole.CHILD_MATRILINEAL_DOMAIN)),exact(current.data(DataRole.DEFAULT_MARRIAGE_DOMAIN)));
        assertEquals(3,originals.selected().size());
        assertEquals(exact(current.data(DataRole.FAMILY_DOMAIN)),originals.selected().get(Slot.FAMILY));
        assertEquals(exact(current.data(DataRole.CHILD_MATRILINEAL_DOMAIN)),originals.selected().get(Slot.CHILD_MATRILINEAL));
        assertEquals(exact(current.data(DataRole.DEFAULT_MARRIAGE_DOMAIN)),originals.selected().get(Slot.DEFAULT_MARRIAGE));
    }
    @Test void incompleteThreeSlotRequestAndWrongSlotOriginalFailBeforeAnyOutput()throws Exception {
        Inputs input=inputs();
        var incomplete=input.items().stream().filter(item->item.kind()!=Kind.DEFAULT_MARRIAGE_DOMAIN).toList();
        assertThrows(IllegalArgumentException.class,()->new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,
                WindowsJobProcess.currentMachineId(),NOW.plusSeconds(3600).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,incomplete));
        var wrong=new ArrayList<>(input.items());
        var family=wrong.stream().filter(item->item.kind()==Kind.FAMILY_DOMAIN).findFirst().orElseThrow();
        for(int i=0;i<wrong.size();i++)if(wrong.get(i).kind()==Kind.CHILD_MATRILINEAL_DOMAIN)
            wrong.set(i,new RootJavaBootstrapInputs.Item(Kind.CHILD_MATRILINEAL_DOMAIN,family.original(),wrong.get(i).target()));
        var request=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,WindowsJobProcess.currentMachineId(),
                NOW.plusSeconds(3600).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,wrong);
        assertThrows(IllegalArgumentException.class,()->RootJavaBootstrapInputs.prepare(request,CLOCK));
        try(var paths=Files.list(input.asset())){assertEquals(0,paths.count());}
    }
    @Test void firstOriginalsArePublishedFromExplicitTypedInitialDataWithoutExistingFamilyFiles()throws Exception {
        Path asset=Files.createDirectory(root.resolve("first-family"));
        var documents=FamilyInitialData.fresh();
        var quoteRequest=new RootJavaBootstrapInputs.FamilyRequest(RootJavaBootstrapInputs.FAMILY_SCHEMA,
                WindowsJobProcess.currentMachineId(),NOW.plusSeconds(3600).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,
                asset.resolve("family.json").toString(),asset.resolve("matrilineal.json").toString(),
                asset.resolve("default-marriage.json").toString(),documents);
        var quote=RootJavaBootstrapInputs.prepareFamily(quoteRequest,CLOCK).quote();
        assertEquals(3,quote.size());
        assertEquals(List.of(Kind.FAMILY_DOMAIN,Kind.CHILD_MATRILINEAL_DOMAIN,Kind.DEFAULT_MARRIAGE_DOMAIN),
                quote.stream().map(Output::kind).toList());
        try(var paths=Files.list(asset)){assertEquals(0,paths.count());}
        var request=new RootJavaBootstrapInputs.FamilyRequest(quoteRequest.schema(),quoteRequest.machineId(),
                quoteRequest.reviewAtUtc(),RootJavaBootstrapInputs.Mode.CREATE_NEW,authority(asset,quote),
                quoteRequest.familyTarget(),quoteRequest.childMatrilinealTarget(),quoteRequest.defaultMarriageTarget(),documents);
        byte[] wire=RootJavaBootstrapInputs.encodeFamilyRequest(request);
        assertEquals(request,RootJavaBootstrapInputs.decodeFamilyRequest(wire));
        var published=RootJavaBootstrapInputs.prepareFamily(RootJavaBootstrapInputs.decodeFamilyRequest(wire),CLOCK).createNew(CLOCK);
        var pins=published.definitionInputs();assertEquals(3,pins.size());
        assertEquals(List.of(DataRole.FAMILY_DOMAIN,DataRole.CHILD_MATRILINEAL_DOMAIN,DataRole.DEFAULT_MARRIAGE_DOMAIN),
                pins.stream().map(DataPin::role).toList());
        assertEquals(documents.family(),FamilyInitialData.decode(Slot.FAMILY,RootRuntimeDefinitions.readData(pins.get(0))));
        assertEquals(documents.childMatrilineal(),FamilyInitialData.decode(Slot.CHILD_MATRILINEAL,RootRuntimeDefinitions.readData(pins.get(1))));
        assertEquals(documents.defaultMarriage(),FamilyInitialData.decode(Slot.DEFAULT_MARRIAGE,RootRuntimeDefinitions.readData(pins.get(2))));
        assertEquals(3,published.originalDocuments().selected().size());
    }
    /** Existing Definitions test's strict configuration fixture. These pins are never runtime-qualified or imported. */
    private Configuration configuration(FileRef input) {
        Build build=new Build("1.20.0.4",SHA);
        var sources=Arrays.stream(SourceRole.values()).map(role->{
            SourceKind kind=expectedKind(role);String suffix=switch(kind){case JAVA->".java";case NATIVE->".cpp";case ORIGINAL_PYTHON->".py";case STOCK_SCRIPT->".txt";};
            String target=role==SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION?ARMY_WAR_EXIT_TRUCE_TARGET:"local-service/src/main/java/fixture/"+role.name()+suffix;
            return new SourcePin(role,kind,new SelectedSource(target,new ExactRef(root.resolve(role.name()+suffix).toString(),1,SHA)));
        }).toList();
        SelectedSource java=sources.stream().filter(source->source.kind()==SourceKind.JAVA).findFirst().orElseThrow().selected();
        SelectedSource ledger=sources.stream().filter(source->source.role()==SourceRole.PRISONER_EPISODE_LEDGER).findFirst().orElseThrow().selected();
        var closures=Arrays.stream(ClosureRole.values()).map(role->new ProducerClosure(role,role==ClosureRole.PRISONER_DOMAIN?List.of(java,ledger):List.of(java))).toList();
        var data=Arrays.stream(DataRole.values()).map(role->new DataPin(role,input)).toList();
        var permission=new ReadPermission(null,"fixture-permission",PermissionMode.SOURCE_QUALIFIED_PRIVATE,WireProfile.EXECUTE_STEP);
        var finance=Arrays.stream(FinanceQuery.values()).map(query->new FinanceRead(query,java,permission)).toList();
        var activity=new ActivityInputs(Arrays.stream(ActivityNativeContracts.Query.values()).map(query->new ActivityQuery(query,java)).toList(),
                Arrays.stream(ActivityActionRoutes.Kind.values()).map(kind->new ActivityMutation(kind,java)).toList());
        return new Configuration(SCHEMA,WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),
                input,input,input,input,new SourceIndex(input,1,SHA),sources,closures,data,
                new GovInputs(build,"fixture-governance",List.copyOf(GovernanceActionPreparation.OPERATIONS),10,3),new FinanceInputs(finance,java,permission),
                new ArmyInputs(1000,2000,"fixture-army"),new PrisonerInputs(build,"fixture-prisoners"),new FamilyInputs(true,true,true,true,null),
                new FrontendInputs(build,1000,1000,8,32,"fixture-frontend"),new InteractionInputs(build,List.of(0L),List.of(List.of(0)),List.of(0)),activity,
                new CrossRunInputs(new OriginalHistory(root.resolve("one-life-history.json").toString(),null)),
                new IncidentInputs(root.resolve("incidents").toString(),root.resolve("scans").toString(),65536),
                new PublicInputs(1000,2000,List.of(PublicMethod.values()[0])),new StartupInputs(16,1000,"fixture-startup"));
    }
    private static ExactRef exact(FileRef value){return new ExactRef(value.path(),value.bytes(),value.sha256());}
}


