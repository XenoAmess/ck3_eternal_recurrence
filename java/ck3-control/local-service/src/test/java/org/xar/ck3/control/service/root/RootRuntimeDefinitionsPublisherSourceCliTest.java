package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Actual CLI DATA flow; missing historical inputs are intentional and grant no runtime authority. */
@org.junit.jupiter.api.parallel.ResourceLock(org.junit.jupiter.api.parallel.Resources.SYSTEM_OUT)
class RootRuntimeDefinitionsPublisherSourceCliTest {
    @TempDir Path root;
    private static final String SHA="a".repeat(64);
    private static final Clock CLOCK=Clock.fixed(Instant.parse("2030-01-01T00:00:00Z"),ZoneOffset.UTC);

    private RootRuntimeDefinitionsPublisher.SourceDeclaration declaration() {
        var c=configuration();
        var physical=new RootRuntimeDefinitionConfigurationAssembler.PhysicalOriginals(c.applicationRef(),c.storageLeaseRef(),
                c.nativeLaunchPlanRef(),c.runtimePackageRequestRef(),c.sourceIndex(),c.sources(),c.closures(),c.originalData());
        var domains=new RootRuntimeDefinitionConfigurationAssembler.DeclaredDomainInputs(c.governance(),c.finance(),c.army(),
                c.prisoners(),c.family(),c.frontend(),c.interactions(),c.activity(),c.crossRun(),c.incidents(),c.publicCatalog(),c.startup());
        return new RootRuntimeDefinitionsPublisher.SourceDeclaration(RootRuntimeDefinitionsPublisher.SOURCE_DECLARATION_SCHEMA,
                c.machineId(),c.observedAtUtc(),c.reviewAtUtc(),physical,domains);
    }
    private FileRef write(Path target,byte[] bytes)throws IOException {
        Files.write(target,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);return FileRef.measure(target);
    }
    private static String invoke(String...args)throws Exception {
        var prior=System.out;var bytes=new java.io.ByteArrayOutputStream();
        try(var output=new java.io.PrintStream(bytes,true,java.nio.charset.StandardCharsets.UTF_8)) {
            System.setOut(output);RootRuntimeDefinitionsPublisher.main(args);
        } finally {System.setOut(prior);}
        return bytes.toString(java.nio.charset.StandardCharsets.UTF_8);
    }
    private static void assertQuote(String value,RootBootstrapOutputContract.Kind kind)throws IOException {
        var quote=RootBootstrapProtocol.line(value.getBytes(java.nio.charset.StandardCharsets.UTF_8),RootBootstrapProtocol.Quote.class);
        var actual=assertInstanceOf(RootBootstrapProtocol.OrdinaryQuote.class,quote);
        assertEquals(kind.name(),actual.phase());assertEquals(1,actual.outputs().size());assertEquals(kind,actual.outputs().getFirst().kind());
    }
    @Test void actualCliSourceRequestAndDefinitionsPublishWithoutHistoricalSourceOrIssuerInputs()throws Exception {
        var source=declaration();var sourceRef=write(root.resolve("source-request.json"),RootRuntimeDefinitionsPublisher.encodeSourceDeclaration(source));
        var absent=pin(root.resolve("never-produced-card.json"));Path selected=root.resolve("source-declaration.json");
        assertFalse(Files.exists(Path.of(source.physical().sourceIndex().compressedRef().path())));
        assertQuote(invoke("quote-source-declaration",sourceRef.path(),Long.toString(sourceRef.bytes()),sourceRef.sha256(),"--target",selected.toString()),RootBootstrapOutputContract.Kind.RUNTIME_DEFINITIONS_SOURCE_DECLARATION);
        assertFalse(Files.exists(selected));
        String sourceOutput=invoke("publish-source-declaration",sourceRef.path(),Long.toString(sourceRef.bytes()),sourceRef.sha256(),
                "--output-binding",absent.path(),"1",absent.sha256(),"--target",selected.toString());
        assertFalse(sourceOutput.isBlank());assertEquals(source,RootRuntimeDefinitionsPublisher.decodeSourceDeclaration(Files.readAllBytes(selected)));
        var selectedRef=FileRef.measure(selected);Path requestFile=root.resolve("publication-request.json"),definitions=root.resolve("definitions.json");
        assertQuote(invoke("quote-definitions",selectedRef.path(),Long.toString(selectedRef.bytes()),selectedRef.sha256(),"--target",definitions.toString()),RootBootstrapOutputContract.Kind.RUNTIME_DEFINITIONS);
        assertQuote(invoke("quote-request",selectedRef.path(),Long.toString(selectedRef.bytes()),selectedRef.sha256(),"--definitions-binding",absent.path(),"1",absent.sha256(),"--definitions-target",definitions.toString(),"--request-target",requestFile.toString()),RootBootstrapOutputContract.Kind.RUNTIME_DEFINITIONS_PUBLICATION_REQUEST);
        assertFalse(Files.exists(requestFile));assertFalse(Files.exists(definitions));
        String requestOutput=invoke("publish-request",selectedRef.path(),Long.toString(selectedRef.bytes()),selectedRef.sha256(),
                "--definitions-binding",absent.path(),"1",absent.sha256(),"--definitions-target",definitions.toString(),
                "--request-target",requestFile.toString(),"--request-binding",absent.path(),"1",absent.sha256());
        assertFalse(requestOutput.isBlank());var request=RootRuntimeDefinitionsPublisher.decodeRequest(Files.readAllBytes(requestFile));
        assertEquals(configuration(),request.configuration());assertFalse(Files.exists(definitions));
        var requestRef=FileRef.measure(requestFile);String definitionsOutput=invoke(requestRef.path(),Long.toString(requestRef.bytes()),requestRef.sha256());
        assertFalse(definitionsOutput.isBlank());assertEquals(request.configuration(),RootRuntimeDefinitions.decodeConfiguration(Files.readAllBytes(definitions)));
        assertFalse(Files.exists(Path.of(absent.path())));assertFalse(Files.exists(Path.of(source.physical().nativeLaunchPlanRef().path())));
    }

    @Test void directConfigurationDataNeedsNoPlanCaptureCensusOrOutputCard()throws Exception {
        var configuration=configuration();var prepared=RootRuntimeDefinitionsPublisher.prepare(configuration,CLOCK);
        var binding=pin(root.resolve("missing-output-card.json"));Path target=root.resolve("configuration-data.json");
        var published=prepared.publish(binding,target,CLOCK);assertEquals(configuration,published.readConfiguration(CLOCK));
        published.requireCurrent(Clock.fixed(Instant.parse("2040-01-01T00:00:00Z"),ZoneOffset.UTC));
        assertEquals(configuration,published.readConfiguration(CLOCK));assertEquals(published.original(),published.actualWitness().source());
        assertThrows(IOException.class,()->prepared.publish(target,CLOCK));
        assertFalse(Files.exists(Path.of(binding.path())));assertFalse(Files.exists(Path.of(configuration.storageLeaseRef().path())));
    }
    @Test void sourceAdmissionModePreservesOtherPassiveFieldsWithoutOpeningTheAdmission()throws Exception {
        var source=declaration();var sourceRef=write(root.resolve("admission-source-request.json"),RootRuntimeDefinitionsPublisher.encodeSourceDeclaration(source));
        var admission=pin(root.resolve("missing-admission.json"));var binding=pin(root.resolve("missing-admission-card.json"));
        Path target=root.resolve("admission-source-declaration.json");
        assertQuote(invoke("quote-admission-source-declaration",sourceRef.path(),Long.toString(sourceRef.bytes()),sourceRef.sha256(),"--admission",admission.path(),"1",admission.sha256(),"--target",target.toString()),RootBootstrapOutputContract.Kind.RUNTIME_DEFINITIONS_SOURCE_DECLARATION);
        assertFalse(Files.exists(target));
        invoke("publish-admission-source-declaration",sourceRef.path(),Long.toString(sourceRef.bytes()),sourceRef.sha256(),
                "--admission",admission.path(),"1",admission.sha256(),"--output-binding",binding.path(),"1",binding.sha256(),"--target",target.toString());
        var actual=RootRuntimeDefinitionsPublisher.decodeSourceDeclaration(Files.readAllBytes(target));
        assertEquals(RootRuntimeDefinitionsPublisher.withPublicAdmissionSource(source,admission),actual);
        assertEquals(source.domains(),actual.domains());assertEquals(source.observedAtUtc(),actual.observedAtUtc());assertEquals(source.reviewAtUtc(),actual.reviewAtUtc());
        assertFalse(Files.exists(Path.of(admission.path())));assertFalse(Files.exists(Path.of(binding.path())));
    }
    @Test void sourceDeclarationKeepsUniqueStrictNestedFieldAndVersionCodec()throws Exception {
        byte[] encoded=RootRuntimeDefinitionsPublisher.encodeSourceDeclaration(declaration());var mapper=ControlBuild.strictMapper();
        ObjectNode missing=(ObjectNode)mapper.readTree(encoded);missing.remove("domains");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeSourceDeclaration(mapper.writeValueAsBytes(missing)));
        ObjectNode bool=(ObjectNode)mapper.readTree(encoded);((ObjectNode)bool.path("physical").path("application_ref")).put("bytes",true);
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeSourceDeclaration(mapper.writeValueAsBytes(bool)));
        ObjectNode fraction=(ObjectNode)mapper.readTree(encoded);((ObjectNode)fraction.path("domains").path("frontend")).put("retained_frames",1.5);
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeSourceDeclaration(mapper.writeValueAsBytes(fraction)));
        ObjectNode unknown=(ObjectNode)mapper.readTree(encoded);unknown.put("default_sources",true);
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeSourceDeclaration(mapper.writeValueAsBytes(unknown)));
        ObjectNode version=(ObjectNode)mapper.readTree(encoded);version.put("schema","xar.root-runtime-definitions-source-declaration/v0");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeSourceDeclaration(mapper.writeValueAsBytes(version)));
    }
    @Test void cliRejectsMalformedOrderedArgumentsAndCreateOnlyDataTarget()throws Exception {
        String absent=root.resolve("never-read.json").toString(),sha=SHA,target=root.resolve("never-created.json").toString();
        for(String count:List.of("0","01","true","1.5","1048577"))
            assertThrows(IllegalArgumentException.class,()->invoke("quote-definitions",absent,count,sha,"--target",target));
        assertThrows(IllegalArgumentException.class,()->invoke("publish-source-declaration",absent,"1",sha,"--target",target));
        assertFalse(Files.exists(Path.of(target)));
        var prepared=RootRuntimeDefinitionsPublisher.prepare(configuration(),CLOCK);
        assertThrows(IllegalArgumentException.class,()->prepared.publish(Path.of("relative.json"),CLOCK));
        Path existing=root.resolve("existing.json");byte[] unchanged={1,2,3};Files.write(existing,unchanged);
        assertThrows(IOException.class,()->prepared.publish(existing,CLOCK));assertArrayEquals(unchanged,Files.readAllBytes(existing));
    }
    @Test void configurationConsumerRejectsByteDriftAndAcceptsSameByteReplacement()throws Exception {
        var prepared=RootRuntimeDefinitionsPublisher.prepare(configuration(),CLOCK);Path target=root.resolve("replaceable.json");
        var published=prepared.publish(target,CLOCK);byte[] original=Files.readAllBytes(target);
        ObjectNode reordered=(ObjectNode)ControlBuild.strictMapper().readTree(original);var schema=reordered.remove("schema");reordered.set("schema",schema);
        byte[] sameValue=ControlBuild.strictMapper().writeValueAsBytes(reordered);assertFalse(Arrays.equals(original,sameValue));
        assertEquals(prepared.configuration(),RootRuntimeDefinitions.decodeConfiguration(sameValue));Files.write(target,sameValue);
        assertThrows(IOException.class,()->published.readConfiguration(CLOCK));
        Path replacement=root.resolve("replacement.json");Files.write(replacement,original);Files.move(replacement,target,StandardCopyOption.REPLACE_EXISTING);
        assertEquals(prepared.configuration(),published.readConfiguration(CLOCK));published.requireCurrent(CLOCK);
    }

    @Test void assemblerCompatibilityAndDirectCompositionFeedTheActualRequestConsumerWithoutAuthorityObjects()throws Exception {
        var source=declaration();var absent=pin(root.resolve("absent-assembler-binding.json"));Path target=root.resolve("assembled-definitions.json");
        Instant observed=Instant.parse(source.observedAtUtc()),review=Instant.parse(source.reviewAtUtc());
        var assembled=RootRuntimeDefinitionConfigurationAssembler.assemble(source.physical(),source.domains(),observed,review,absent,target,CLOCK);
        var compatible=RootRuntimeDefinitionConfigurationAssembler.assemble(source.physical(),source.domains(),observed,review,absent,target,null,null,CLOCK);
        assertEquals(assembled.request(),compatible.request());assertArrayEquals(assembled.requestBytes(),compatible.requestBytes());
        assertEquals(source.observedAtUtc(),assembled.request().configuration().observedAtUtc());
        assertEquals(source.reviewAtUtc(),assembled.request().configuration().reviewAtUtc());
        assertEquals(org.xar.ck3.control.build.WindowsJobProcess.currentMachineId(),assembled.request().configuration().machineId());
        assembled.requireCurrent(CLOCK);compatible.requireCurrent(Clock.fixed(Instant.parse("2040-01-01T00:00:00Z"),ZoneOffset.UTC));
        var request=RootRuntimeDefinitionsPublicationRequestProducer.prepare(assembled.request()).publish(root.resolve("assembled-request.json"),CLOCK);
        assertEquals(assembled.request().configuration(),request.execute(CLOCK).readConfiguration(CLOCK));
        assertFalse(Files.exists(Path.of(absent.path())));assertFalse(Files.exists(Path.of(source.physical().nativeLaunchPlanRef().path())));
    }

    /** Existing Definitions codec fixture structure: complete typed configuration, no physical source claim. */
    private Configuration configuration() {
        FileRef input = pin(root.resolve("missing-required.json")); Build build = new Build("1.20.0.4", SHA);
        List<SourcePin> sources = Arrays.stream(SourceRole.values()).map(role -> {
            SourceKind kind = expectedKind(role); String suffix = switch (kind) {
                case JAVA -> ".java"; case NATIVE -> ".cpp"; case ORIGINAL_PYTHON -> ".py"; case STOCK_SCRIPT -> ".txt";
            };
            String target = role == SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION ? ARMY_WAR_EXIT_TRUCE_TARGET
                    : "local-service/src/main/java/fixture/" + role.name() + suffix;
            return new SourcePin(role, kind, new SelectedSource(target, new ExactRef(root.resolve(role.name() + suffix).toString(), 1, SHA)));
        }).toList();
        SelectedSource java = sources.stream().filter(source -> source.kind() == SourceKind.JAVA).findFirst().orElseThrow().selected();
        SelectedSource episode = sources.stream().filter(source -> source.role() == SourceRole.PRISONER_EPISODE_LEDGER).findFirst().orElseThrow().selected();
        List<ProducerClosure> closures = Arrays.stream(ClosureRole.values()).map(role -> new ProducerClosure(role,
                role == ClosureRole.PRISONER_DOMAIN ? List.of(java, episode) : List.of(java))).toList();
        List<DataPin> data = Arrays.stream(DataRole.values()).map(role -> new DataPin(role, input)).toList();
        ReadPermission permission = new ReadPermission(null, "fixture-permission", PermissionMode.SOURCE_QUALIFIED_PRIVATE, WireProfile.EXECUTE_STEP);
        List<FinanceRead> finance = Arrays.stream(FinanceQuery.values()).map(query -> new FinanceRead(query, java, permission)).toList();
        var activity = new ActivityInputs(Arrays.stream(ActivityNativeContracts.Query.values()).map(query -> new ActivityQuery(query, java)).toList(),
                Arrays.stream(ActivityActionRoutes.Kind.values()).map(kind -> new ActivityMutation(kind, java)).toList());
        return new Configuration(SCHEMA, "definition-fixture-machine", "2026-10-24T00:00:00Z", "2026-10-24T01:00:00Z",
                input, input, input, input, new SourceIndex(input, 1, SHA), sources, closures, data,
                new GovInputs(build, "fixture-governance", List.copyOf(GovernanceActionPreparation.OPERATIONS), 10, 3),
                new FinanceInputs(finance, java, permission), new ArmyInputs(1000, 2000, "fixture-army"),
                new PrisonerInputs(build, "fixture-prisoners"), new FamilyInputs(true, true, true, true, null),
                new FrontendInputs(build, 1000, 1000, 8, 32, "fixture-frontend"),
                new InteractionInputs(build, List.of(0L), List.of(List.of(0)), List.of(0)), activity,
                new CrossRunInputs(new OriginalHistory(root.resolve("strategy/one-life-history.json").toString(), null)),
                new IncidentInputs(root.resolve("incidents").toString(), root.resolve("scans").toString(), 65536),
                new PublicInputs(1000, 2000, List.of(PublicMethod.values()[0])), new StartupInputs(16, 1000, "fixture-startup"));
    }
    private FileRef pin(Path path) { return new FileRef(path.toString(), 1, SHA); }
}
