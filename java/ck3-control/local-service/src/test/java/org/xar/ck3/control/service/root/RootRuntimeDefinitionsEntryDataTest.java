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

/** Actual readExact entry failure routing with necessary DATA; no formal capture or Game receipt is invented. */
class RootRuntimeDefinitionsEntryDataTest {
    @TempDir Path root;
    private static final String SHA="a".repeat(64);
    private static final Clock CLOCK=Clock.fixed(Instant.parse("2030-01-01T00:00:00Z"),ZoneOffset.UTC);
    private record Fixture(FileRef definitions,Path expectedMissing) { }
    private FileRef write(Path target,byte[] bytes)throws Exception {
        Files.write(target,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);return FileRef.measure(target);
    }
    private Fixture prefix(int present)throws Exception {
        Configuration config=configuration();String machine=config.machineId();
        Path appPath=root.resolve("application.json"),leasePath=root.resolve("lease.json"),eventPath=root.resolve("events.json"),capturePath=root.resolve("missing-formal-actual.json");
        FileRef app=pin(appPath),lease=pin(leasePath),events=pin(eventPath),capture=pin(capturePath);
        SourceIndex index=new SourceIndex(pin(root.resolve("index.gz")),1,SHA);
        if(present>=1) {
            var layout=new org.xar.ck3.control.continuity.writer.WriterContracts.Layout(root.resolve("ledger/snapshot.json"),
                    new ExactRef(root.resolve("removed-anchor.json").toString(),1,SHA),machine);
            var application=new RootApplicationConfiguration(machine,org.xar.ck3.control.build.runtime.HostMode.COMPLETE_MIGRATION,
                    Instant.parse(config.reviewAtUtc()),new ExactRef(config.nativeLaunchPlanRef().path(),1,SHA),layout,
                    List.of(new ExactRef(root.resolve("removed-writer.java").toString(),1,SHA)),root.resolve("artifacts"),1048576);
            app=write(appPath,org.xar.ck3.control.contracts.StrictJson.canonical(application.toJson(),RootApplicationConfiguration.MAXIMUM_BYTES));
        }
        if(present>=2) {
            var passive=pin(root.resolve("removed-storage-issuer.json"));
            var storage=new StorageLease(LEASE_SCHEMA,"ROOT_GAME_RUNTIME",machine,"/root",config.observedAtUtc(),config.reviewAtUtc(),
                    passive,passive,passive,passive,1048576,List.of(new RootBudget(root.resolve("declared-storage").toString(),65536)),
                    List.of(new VolumeThreshold(root.toString(),0,0)));
            lease=write(leasePath,org.xar.ck3.control.contracts.StrictJson.canonical(ControlBuild.strictMapper().valueToTree(storage),RootRuntimeDefinitions.MAXIMUM_BYTES));
        }
        if(present>=3)index=index(graph(),"index.gz");
        if(present>=4) {
            var context=new org.xar.ck3.control.contracts.projection.EventSourceReadContext(machine,root.resolve("event-state"),root.resolve("stock-game"),List.of());
            events=write(eventPath,RootRuntimeDefinitions.encodeEventSources(context));
        }
        var encoded=(ObjectNode)ControlBuild.strictMapper().readTree(RootRuntimeDefinitions.encodeConfiguration(config));
        encoded.set("application_ref",ControlBuild.strictMapper().valueToTree(app));encoded.set("storage_lease_ref",ControlBuild.strictMapper().valueToTree(lease));
        encoded.set("source_index",ControlBuild.strictMapper().valueToTree(index));
        for(var data:encoded.get("original_data")) {
            String role=data.get("role").textValue();
            if(role.equals(DataRole.TRUSTED_EVENT_SOURCE_CONTEXT.name()))((ObjectNode)data).set("original_ref",ControlBuild.strictMapper().valueToTree(events));
            if(role.equals(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT.name()))((ObjectNode)data).set("original_ref",ControlBuild.strictMapper().valueToTree(capture));
        }
        var actual=RootRuntimeDefinitions.decodeConfiguration(ControlBuild.strictMapper().writeValueAsBytes(encoded));
        FileRef definitions=write(root.resolve("definitions.json"),RootRuntimeDefinitions.encodeConfiguration(actual));
        Path missing=switch(present){case 0->appPath;case 1->leasePath;case 2->root.resolve("index.gz");case 3->eventPath;default->capturePath;};
        return new Fixture(definitions,missing);
    }
    private void missingNecessaryData(int present)throws Exception {
        var fixture=prefix(present);
        var failure=assertThrows(java.nio.file.NoSuchFileException.class,()->RootRuntimeDefinitions.readExact(fixture.definitions(),CLOCK));
        assertEquals(fixture.expectedMissing(),Path.of(failure.getFile()));
        assertFalse(Files.exists(root.resolve("removed-writer.java")));assertFalse(Files.exists(root.resolve("missing-required.json")));
    }
    @Test void actualEntryReadsRequiredApplicationInsteadOfHistoricalCurrentReviewGate()throws Exception {missingNecessaryData(0);}
    @Test void actualEntryDecodesStaleApplicationDataBeforeRequiredStorageData()throws Exception {missingNecessaryData(1);}
    @Test void actualEntryDecodesStorageDataBeforeRecordedMetadataTable()throws Exception {missingNecessaryData(2);}
    @Test void actualEntryDoesNotOpenHistoricalSourceBodiesBeforeRequiredEventConfiguration()throws Exception {missingNecessaryData(3);}
    @Test void actualEntryReportsMissingFormalCaptureDataWithoutInventingAReceipt()throws Exception {missingNecessaryData(4);}

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
