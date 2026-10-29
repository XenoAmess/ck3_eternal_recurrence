package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Exact archived Driver producer -> full assembler -> sole observation codec; software inputs only. */
final class PublicRevisionObservationTest {
    @Test void actualManifestProducerAndAllImmediateObservationConsumersPreserveZeroAndWidePublicCounters() {
        for(BigInteger revision:List.of(BigInteger.ZERO,BigInteger.ONE.shiftLeft(64),BigInteger.ONE.shiftLeft(100))) {
            var actual=DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
            var known=DriverStateAssemblerTest.known();
            var manifest=DriverObservationEvidenceReader.encode(known,actual,revision,1,DriverStateAssemblerTest.source(),
                    new OpportunityJson.Obj(Map.of()),DriverStateAssemblerTest.ref(known.driver().encode()));
            var manifestRef=DriverStateAssemblerTest.ref(manifest.bytes());
            var replay=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,actual.originalPacket());
            var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(known.driver().encode()),replay);
            var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(
                    replay,facts,DriverStateAssemblerTest.ref(replay.originalPacket())));
            assertEquals(revision,complete.identity().frame().revision());
            assertEquals(revision,OpportunityJson.integer(complete.semantic().get("revision"),"revision"));
            var wire=ProposalLifecycleCodec.observation(complete.identity());
            assertEquals(revision.toString(),wire.path("frame").path("revision").textValue());
            assertEquals(complete.identity(),ProposalLifecycleCodec.decodeObservation(wire));
            assertEquals(actual.nativeRevision(),complete.identity().frame().identity().nativeRevision());
            for(String wrong:List.of("true","1.0","null","-1")) {
                var changed=wire.deepCopy();changed.withObject("/frame").set("revision",org.xar.ck3.control.contracts.StrictJson.parse(wrong.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->ProposalLifecycleCodec.decodeObservation(changed));
            }
        }
    }
}
