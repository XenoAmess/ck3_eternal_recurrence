package org.xar.ck3.control.service.root;

import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeUiParsedReturn;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** Actual software coordinator/archive/Root guard originals. The malformed UI result remains UNKNOWN, never Native Ready. */
final class RootArtifactsParsedReturnTest {
    @TempDir Path temporary;
    @Test void realCorrelatedAckIsPreservedBeforeFailedUiNormalizationAndUnknownRetainsTheArtifact()throws Exception {
        var actual=new AtomicReference<ActionWriterIntegrationFixture>();var preserved=new AtomicReference<ExactRef>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("navigate-ingame-ui-v1"),
                "game.command.navigate-ingame-ui-v1",(command,attempt,dispatch)->{
            var fixture=actual.get();
            try {
                var same=fixture.writer.borrowedSession();var archive=fixture.archive.withSession(same);
                var before=RootGuardEvidence.loadFrame(attempt.guard(),archive,fixture.frameLoader());
                var ack=(NativeActionPort.AckReceived)dispatch;
                ExactRef ref=RootArtifactsSourcesFactory.preserveParsedReturn(fixture.archive,same,command,attempt,ack,before);
                preserved.set(ref);var frame=ArtifactsService.actualFrame(before);
                assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(new RelicPair(Method.SELECT_RELIC,frame.publicRevision(),7,8),frame,
                        new NativeEnvelope(ack.requestId(),StrictJson.parse(ack.originalFrame().bytes()),frame)));
                return new ActionPorts.Pending("actual malformed UI remains UNKNOWN with its unvalidated parsed original",List.of(ref));
            }catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
        },()->{},()->new RawJson(StrictJson.canonical(StrictJson.object().put("software_fixture_only",true).put("available",true))));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("malformed-original-ui"),false,scenario)){
            actual.set(fixture);var receipt=fixture.coordinator.execute(fixture.command("parsed-original-unknown"));
            var unknown=assertInstanceOf(ActionState.Unknown.class,receipt.state());assertEquals(List.of(preserved.get()),unknown.evidence());
            assertFalse(receipt.settled());
            fixture.writer.locked(same->{
                var archive=fixture.archive.withSession(same);var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();
                var ack=receipt.ack().orElseThrow();var before=RootGuardEvidence.loadFrame(attempt.guard(),archive,fixture.frameLoader());
                var original=NativeUiParsedReturn.encode(ack.outbound().orElseThrow().originalPacket(),ack.originalPacket(),before.semantic());
                byte[] stored=fixture.archive.readArtifact(same,preserved.get(),NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);assertArrayEquals(original.bytes(),stored);
                var decoded=NativeUiParsedReturn.decode(stored);assertEquals(before.semantic(),decoded.get("actual_pre_submission_snapshot"));
                var body=OpportunityJson.toNode(decoded);assertEquals(NativeUiParsedReturn.SCHEMA,body.get("schema").textValue());
                assertEquals("unvalidated",body.get("validation_state").textValue());assertFalse(body.get("wire_bytes_preserved").booleanValue());
                assertEquals(OpportunityJson.toNode(before.semantic()),body.get("actual_pre_submission_snapshot"));
                assertEquals(StrictJson.parse(ack.originalFrame().bytes()),body.get("original_parsed_command_result"));
                assertNotEquals(archive.referenceOf(ack).path(),preserved.get().path());
                var output=StrictJson.object().put("business_outcome_observed",false).put("automatic_retry",false);
                output.set("native_ui_raw_return_receipt",NativeUiParsedReturn.reference(preserved.get()));
                var wire=PublicMcpDirectory.CallResult.fromBusinessJson(new RawJson(StrictJson.canonical(output)));
                assertEquals(output,StrictJson.parse(wire.bytes()).get("structuredContent"));
                var wrong=new ActionCommand(receipt.command().actionId(),receipt.command().before(),receipt.command().source(),"another-original-session",
                        receipt.command().operation(),receipt.command().arguments(),receipt.command().expected(),receipt.command().claims(),receipt.command().deadline());
                assertThrows(IllegalArgumentException.class,()->RootArtifactsSourcesFactory.preserveParsedReturn(fixture.archive,same,wrong,attempt,ack,before));
                return null;
            });
        }
    }
}
