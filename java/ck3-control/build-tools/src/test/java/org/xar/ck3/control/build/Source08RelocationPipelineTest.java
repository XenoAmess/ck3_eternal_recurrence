package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class Source08RelocationPipelineTest {
    @TempDir Path temporary;

    @Test void realInputRequestPlanEntryPointsRetainHistoricalLayersAndProtectedInventory() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        FileRef input = SourceRelocationTestSupport.json(temporary.resolve("input.json"), fixture.input());
        assertEquals(fixture.input(), ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(input.path())), Source08Assembly.Input.class));
        Path request = temporary.resolve("request.json"), audit = temporary.resolve("audit.json"), output = temporary.resolve("plan.json");
        Source08Assembly.main(new String[] {input.path(), request.toString(), audit.toString()});
        var produced = SourceGraphPlanProducer.readRequest(FileRef.measure(request));
        assertEquals(SourceGraphPlanProducer.RELOCATION_REQUEST_SCHEMA, produced.schema());
        assertEquals(fixture.history(), produced.layers().subList(0, fixture.history().size()));
        assertEquals(fixture.input().relocations(), produced.relocations());
        SourceGraphPlanProducer.main(new String[] {request.toString(), output.toString()});
        var plan = CompleteSourceGraph.readPlan(FileRef.measure(output));
        assertEquals(fixture.originals(), CompleteSourceGraph.baselineFiles(plan));
        assertEquals(fixture.input().relocations(), plan.relocations());
        var recorded = ControlBuild.strictMapper().readValue(Files.readAllBytes(audit), Source08Assembly.Audit.class);
        assertEquals(fixture.history().size(), recorded.source07LayersRetained());
        assertFalse(recorded.sourceBodiesCopied()); assertFalse(recorded.typedPlanProduced()); assertFalse(recorded.compiled());
        input.verify(); fixture.authority().verify(); fixture.baseline().inventoryRef().verify();
    }
    @Test void v1InputAndRequestKeepTheirExactHistoricalFieldDomain() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var current = fixture.input();
        var old = new Source08Assembly.Input(Source08Assembly.INPUT_SCHEMA, current.machineId(), current.observedAtUtc(),
                current.plan16RequestRef(), current.source07RequestRef(), current.profile(), current.modules(), current.owners(), List.of());
        byte[] input = ControlBuild.strictMapper().writeValueAsBytes(old);
        assertFalse(new String(input, java.nio.charset.StandardCharsets.UTF_8).contains("\"relocations\""));
        assertEquals(old, ControlBuild.strictMapper().readValue(input, Source08Assembly.Input.class));
        var request = Source08Assembly.prepare(old);
        assertEquals(SourceGraphPlanProducer.REQUEST_SCHEMA, request.schema());
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(request);
        assertFalse(new String(encoded, java.nio.charset.StandardCharsets.UTF_8).contains("\"relocations\""));
        assertEquals(request, ControlBuild.strictMapper().readValue(encoded, SourceGraphPlanProducer.Request.class));
        String wrong = new String(encoded, java.nio.charset.StandardCharsets.UTF_8).replace("assembly-request/v1", "assembly-request/v2");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(wrong, SourceGraphPlanProducer.Request.class));
    }
    @Test void missingWrongAuthorityAndChangedHistoricalLayerCannotAuthorizeAMove() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var current = fixture.input();
        FileRef alien = SourceRelocationTestSupport.write(temporary.resolve("outside-owner.json"), "{}");
        List<Relocation> outside = current.relocations().stream().map(move -> new Relocation(move.oldTargetRelative(),
                move.newTargetRelative(), move.sourceRef(), alien)).toList();
        var invalid = new Source08Assembly.Input(Source08Assembly.RELOCATION_INPUT_SCHEMA, current.machineId(), current.observedAtUtc(),
                current.plan16RequestRef(), current.source07RequestRef(), current.profile(), current.modules(), current.owners(), List.of(), outside);
        assertThrows(IOException.class, () -> Source08Assembly.prepare(invalid));
        Path old = Path.of(fixture.history().getFirst().ownerMapRef().path()); Files.writeString(old, "{\"changed\":true}");
        assertThrows(IOException.class, () -> Source08Assembly.prepare(current));
    }
    @Test void strictV2RequestAndInputDoNotAcceptNullAliasesOrMissingMoveProof() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var mapper = ControlBuild.strictMapper();
        var tree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.valueToTree(fixture.input());
        tree.remove("relocations"); assertThrows(IOException.class, () -> mapper.treeToValue(tree, Source08Assembly.Input.class));
        tree.set("relocations", com.fasterxml.jackson.databind.node.NullNode.instance);
        assertThrows(IOException.class, () -> mapper.treeToValue(tree, Source08Assembly.Input.class));
        var request = Source08Assembly.prepare(fixture.input());
        var requestTree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.valueToTree(request);
        var move = (com.fasterxml.jackson.databind.node.ObjectNode) requestTree.path("relocations").get(0);
        move.remove("selection_ref"); assertThrows(IOException.class, () -> mapper.treeToValue(requestTree, SourceGraphPlanProducer.Request.class));
        move.set("selection_ref", mapper.valueToTree(fixture.authority())); move.put("source", "alias");
        assertThrows(IOException.class, () -> mapper.treeToValue(requestTree, SourceGraphPlanProducer.Request.class));
    }
}
