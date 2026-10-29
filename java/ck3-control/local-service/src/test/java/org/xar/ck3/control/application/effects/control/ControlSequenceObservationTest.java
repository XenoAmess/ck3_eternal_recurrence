package org.xar.ck3.control.application.effects.control;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** DATA round trips use actual writer-held immutable refs; they grant no native or running-map permission. */
final class ControlSequenceObservationTest {
    @TempDir Path root;
    @Test void actualWriterMaterialAndOriginalCommandBytesRoundTripWithoutInferringCanonicalChildren()throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(root.resolve("data-roundtrip"),false)) {
            var base=actual.command("original-pause-parent-data");
            var parent=new ActionCommand(base.actionId(),base.before(),base.source(),base.sessionId(),ControlSequenceObservation.OPERATION,
                    new OpportunityJson.Obj(Map.of()),new ExpectedPostcondition(1,base.before(),base.source(),ControlSequenceObservation.OBSERVER,ControlSequenceObservation.expected()),base.claims(),base.deadline());
            int nativeWrites=actual.nativeActionWrites();byte[] ledger=actual.ledgerBytes();
            actual.writer.locked(same->{
                var archive=actual.archive.withSession(same);var original=new RawJson(StrictJson.canonical(StrictJson.object().put("scope","DATA-only-not-canonical-child-or-guard")));
                var reference=archive.preserveMaterial(original);
                var data=new ControlSequenceObservation(parent,ControlSequenceObservation.Mode.DIRECT_PAUSE,parent.before(),reference,
                        List.of(new ControlSequenceObservation.Child("data-locator-not-a-canonical-child","a".repeat(64),reference)),List.of(reference));
                var restored=ControlSequenceObservation.decode(data.encode());assertEquals(data,restored);
                assertArrayEquals(ActionCodec.encodeCommand(parent),ActionCodec.encodeCommand(restored.parent()));assertEquals(ActionCodec.bodySha256(parent),ActionCodec.bodySha256(restored.parent()));
                assertThrows(RuntimeException.class,()->archive.loadReceipt(reference),"a material locator cannot grant canonical child authority");
                var bad=StrictJson.parse(data.encode());((com.fasterxml.jackson.databind.node.ObjectNode)bad).put("kind","GENERIC_NATIVE_RETRY");
                assertThrows(IllegalArgumentException.class,()->ControlSequenceObservation.decode(StrictJson.canonical(bad)));
                ((com.fasterxml.jackson.databind.node.ObjectNode)bad).put("kind",data.kind().name()).put("mode","RETRIED_PAUSE");
                assertThrows(IllegalArgumentException.class,()->ControlSequenceObservation.decode(StrictJson.canonical(bad)),"a one-child locator cannot authorize a second native submission");
                return null;
            });
            assertEquals(nativeWrites,actual.nativeActionWrites());assertArrayEquals(ledger,actual.ledgerBytes());
        }
    }
}
