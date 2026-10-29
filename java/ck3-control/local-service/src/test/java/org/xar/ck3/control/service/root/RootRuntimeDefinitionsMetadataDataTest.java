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

/** Recorded source metadata is DATA; these fixtures grant no installed runtime or Game authority. */
class RootRuntimeDefinitionsMetadataDataTest {
    @TempDir Path root;
    private static final String SHA="a".repeat(64);
    private static final Clock CLOCK=Clock.fixed(Instant.parse("2030-01-01T00:00:00Z"),ZoneOffset.UTC);

    private ObjectNode graph() {
        var graph=org.xar.ck3.control.contracts.StrictJson.object();
        graph.put("schema","xar.java.single-winner-source-index/v1");graph.put("machine_id","definition-fixture-machine");
        graph.put("owner","/root/source_graph");graph.put("observed_at_utc","2026-10-24T00:00:00Z");
        graph.put("status","SOURCE_ONLY_NOT_RUNTIME_QUALIFICATION");
        graph.set("input_ref",ControlBuild.strictMapper().valueToTree(pin(root.resolve("removed-ancestry.json"))));
        graph.put("parent_pom_order_only_supersedes_input02",true);
        graph.set("selected_files",ControlBuild.strictMapper().valueToTree(List.of(new SelectedSource(
                "local-service/src/main/java/fixture/Removed.java",new ExactRef(root.resolve("Removed.java").toString(),1,SHA)))));
        return graph;
    }
    private SourceIndex index(ObjectNode graph,String name)throws Exception {
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(graph);Path gzip=root.resolve(name);
        try(var out=new java.util.zip.GZIPOutputStream(Files.newOutputStream(gzip))){out.write(raw);}
        return new SourceIndex(FileRef.measure(gzip),raw.length,org.xar.ck3.control.build.OriginalMcpCapture.sha256(raw));
    }
    @Test void recordedMetadataTableDoesNotRequireHistoricalAncestrySourceFilesOrCurrentMachine()throws Exception {
        ObjectNode graph=graph();SourceIndex index=index(graph,"index.gz");
        var selected=RootRuntimeDefinitions.readSourceIndex(index,"different-current-machine",CLOCK);
        assertEquals(1,selected.size());assertEquals("local-service/src/main/java/fixture/Removed.java",selected.get(0).targetRelative());
        assertFalse(Files.exists(Path.of(selected.get(0).sourceRef().path())));
        assertEquals(pin(root.resolve("removed-ancestry.json")),RootRuntimeDefinitions.sourceIndexOriginalInput(index));
        assertFalse(Files.exists(root.resolve("removed-ancestry.json")));
    }
    @Test void configuredSourceMetadataDoesNotRequireHistoricalJavaBodiesOrMigrationQualification()throws Exception {
        Configuration configuration=configuration();
        assertFalse(Files.exists(Path.of(configuration.sources().get(0).selected().sourceRef().path())));
        assertDoesNotThrow(()->RootRuntimeDefinitions.verifySources(configuration,List.of()));
        assertTrue(RootRuntimeDefinitions.configuredSources(configuration).contains(configuration.sources().get(0).selected()));
    }
    @Test void uniqueIndexCodecStillRejectsMalformedFieldsDuplicateTargetsAndWrongBytes()throws Exception {
        var original=graph();var badSchema=original.deepCopy();badSchema.put("schema","old");
        var badInteger=original.deepCopy();((ObjectNode)badInteger.at("/selected_files/0/source_ref")).put("bytes",1.0);
        var badBoolean=original.deepCopy();((ObjectNode)badBoolean.at("/selected_files/0/source_ref")).put("bytes",true);
        var duplicate=original.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)duplicate.get("selected_files")).add(duplicate.get("selected_files").get(0).deepCopy());
        int count=0;for(var bad:List.of(badSchema,badInteger,badBoolean,duplicate)){
            var index=index(bad,"bad-"+(count++)+".gz");
            assertThrows(IOException.class,()->RootRuntimeDefinitions.readSourceIndex(index,"definition-fixture-machine",CLOCK));
        }
        var index=index(original,"wrong-sha.gz");
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readSourceIndex(new SourceIndex(index.compressedRef(),index.uncompressedBytes(),"0".repeat(64)),"definition-fixture-machine",CLOCK));
    }
    @Test void requiredDataReaderKeepsExpectedByteCountAndShaAndAcceptsIdenticalReplacement()throws Exception {
        Path data=root.resolve("data.json");Files.writeString(data,"{\"schema\":\"fixture\"}");var ref=FileRef.measure(data);
        byte[] bytes=Files.readAllBytes(data);assertArrayEquals(bytes,RootRuntimeDefinitions.read(ref,4096));
        Path replacement=root.resolve("replacement.json");Files.write(replacement,bytes);Files.move(replacement,data,StandardCopyOption.REPLACE_EXISTING);
        assertArrayEquals(bytes,RootRuntimeDefinitions.read(ref,4096));
        byte[] changed=bytes.clone();changed[1]^=1;Files.write(data,changed);
        assertThrows(IOException.class,()->RootRuntimeDefinitions.read(ref,4096));
        Files.write(data,bytes);assertThrows(IOException.class,()->RootRuntimeDefinitions.read(new FileRef(data.toString(),ref.bytes()+1,ref.sha256()),4096));
    }
    @Test void contradictoryBodiesForOneRecordedTargetRemainAnInvalidMetadataContract()throws Exception {
        var original=configuration();var mapper=ControlBuild.strictMapper();
        ObjectNode encoded=(ObjectNode)mapper.readTree(RootRuntimeDefinitions.encodeConfiguration(original));
        for(var closure:encoded.get("closures"))if(closure.get("role").textValue().equals(ClosureRole.SWAY.name()))
            ((ObjectNode)closure.at("/sources/0/source_ref")).put("sha256","b".repeat(64));
        Configuration conflicting=RootRuntimeDefinitions.decodeConfiguration(mapper.writeValueAsBytes(encoded));
        var failure=assertThrows(IOException.class,()->RootRuntimeDefinitions.verifySources(conflicting,List.of()));
        assertTrue(failure.getMessage().contains("different bodies to one source target"),failure.toString());
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
