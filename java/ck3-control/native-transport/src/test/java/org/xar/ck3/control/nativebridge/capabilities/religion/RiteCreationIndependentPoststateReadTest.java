package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.EpisodeScope;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.Outcome;
import org.xar.ck3.control.application.ritecreation.RiteCreationIndependentPoststate;
import org.xar.ck3.control.contracts.semantic.NativePlayerReligionContext;
import static org.junit.jupiter.api.Assertions.*;

/** Reuses the actual pinned C++ software-packet producer/reader fixture.
 * Controlled .2 -> .4 remap is explicit; these Complete records are software data, never managed Root authority. */
final class RiteCreationIndependentPoststateReadTest {
    @TempDir Path temporary;
    private static final EpisodeScope SCOPE=new EpisodeScope("fixture-episode");
    private static ObjectNode remap(ObjectNode frame){
        var result=(ObjectNode)frame.get("result");PlayerReligionContextReadTest.remapFour(result);
        var context=(ObjectNode)result.get("player_religion_context");PlayerReligionContextReadTest.remapFour(context);
        context.put("schema",PlayerReligionContext.Build.CROZIER4.schema());return frame;
    }
    private static Complete softwareComplete(PlanningReadReceipt receipt,long piety){
        var n=PlayerReligionContextReadTest.snapshot();n.put("episode_run_id","fixture-episode");
        n.putObject("played_character_piety").put("raw",piety).put("scale",100000);
        var d=(ObjectNode)n.get("diagnostics");d.put("connection_generation",11);
        ((ObjectNode)d.get("hello")).put("pid",42).put("expected_ck3_version",PlayerReligionContext.Build.CROZIER4.version())
            .put("expected_ck3_sha256",PlayerReligionContext.Build.CROZIER4.sha256()).put("ck3_build_match",true).put("game_adapter_id","ck3-1.20.0.4-msvc-x64");
        return new Complete(receipt.request().before(),receipt.request().source(),receipt.request().sessionId(),BigInteger.valueOf(11),
            DriverJson.object(n.toString().getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES),
            receipt.before().binding().nativeEvidence(),receipt.before().binding().observedAt(),"a".repeat(64));
    }
    @Test void everyPinnedOriginalPacketReachesRegisteredReaderSharedLowerDiagnosticConsumerAndSerde()throws Exception{
        var producer=PlayerReligionContextReadTest.fixtureAt(temporary);
        for(String name:List.of("current-zero","signed-values","native-default","legal-absent","faith-unavailable","fervor-unavailable")){
            // No .4 Game result is inferred from this schema/build remap of a real pinned software fixture.
            var first=producer.receipt(remap(producer.fixture(name)));var last=producer.receipt(remap(producer.fixture(name)));
            var before=RiteCreationIndependentPoststateRead.decode(softwareComplete(first,Long.MIN_VALUE),SCOPE,first);
            var after=RiteCreationIndependentPoststateRead.decode(softwareComplete(last,Long.MAX_VALUE),SCOPE,last);
            assertSame(first,before.receipt());assertEquals(NativePlayerReligionContext.decode(PlayerReligionContextRead.decode(first).context().encode()),before.observation().context());
            var result=RiteCreationIndependentPoststateRead.evaluate(before,after,Outcome.EDIT_RITE,OptionalLong.empty());
            assertEquals(new BigInteger("18446744073709551615"),result.delta().orElseThrow());
            assertEquals(result,RiteCreationIndependentPoststate.decode(RiteCreationIndependentPoststate.encode(result)),name);
            assertFalse(result.actionReady());assertFalse(result.businessOutcomeVerified());
        }
    }
    @Test void actualOriginalPacketTokenContextAndCompleteSourceCannotBeReplaced()throws Exception{
        var producer=PlayerReligionContextReadTest.fixtureAt(temporary);var receipt=producer.receipt(remap(producer.fixture("current-zero")));
        var complete=softwareComplete(receipt,100000);var retained=RiteCreationIndependentPoststateRead.decode(complete,SCOPE,receipt);
        var token=new NativeActionPort.AckReceived(receipt.requestId(),true,Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))),receipt.original().originalFrame(),receipt.original().originalPacket());
        var tampered=new PlanningReadReceipt(receipt.request(),receipt.contractId(),receipt.requestId(),receipt.before(),receipt.after(),token);
        assertThrows(IllegalArgumentException.class,()->RiteCreationIndependentPoststateRead.decode(complete,SCOPE,tampered));
        var otherSession=new Complete(complete.identity(),complete.source(),"other-session",complete.connectionGeneration(),complete.semantic(),complete.originalEvidence(),complete.observedAt(),complete.fullBindingSha256());
        assertThrows(IllegalArgumentException.class,()->RiteCreationIndependentPoststateRead.decode(otherSession,SCOPE,receipt));
        var otherGeneration=new Complete(complete.identity(),complete.source(),complete.sessionId(),BigInteger.valueOf(12),complete.semantic(),complete.originalEvidence(),complete.observedAt(),complete.fullBindingSha256());
        assertThrows(IllegalArgumentException.class,()->RiteCreationIndependentPoststateRead.decode(otherGeneration,SCOPE,receipt));
        var wrong=remap(producer.fixture("current-zero"));((ObjectNode)wrong.get("result").get("player_religion_context")).put("played_character_id",50331653);
        var wrongReceipt=producer.receipt(wrong);assertThrows(IllegalArgumentException.class,()->RiteCreationIndependentPoststateRead.decode(softwareComplete(wrongReceipt,0),SCOPE,wrongReceipt));
        assertSame(receipt,retained.receipt(),"failed paths retain the original receipt");
    }
    @Test void existingBoundedPublicApiDelegatesWithoutNarrowingTheGeneralOriginalDiagnosticDomain()throws Exception{
        var producer=PlayerReligionContextReadTest.fixtureAt(temporary);var frame=producer.fixture("current-zero");
        var original=(ObjectNode)frame.get("result").get("player_religion_context");var existing=PlayerReligionContext.decode(original);
        assertEquals(NativePlayerReligionContext.decode(existing.encode()),NativePlayerReligionContext.decode(original));
        assertEquals(existing,PlayerReligionContext.decode(existing.encode()));
        var wide=original.deepCopy().put("available",false).put("unavailable_reason","diagnostic-source-unavailable")
            .put("date_raw",new BigInteger("-12345678901234567890")).put("played_character_id",new BigInteger("12345678901234567890"));
        assertEquals(NativePlayerReligionContext.decode(wide),NativePlayerReligionContext.decode(NativePlayerReligionContext.decode(wide).encode()));
        assertThrows(IllegalArgumentException.class,()->PlayerReligionContext.decode(wide),"legacy bounded reader API remains bounded");
        for(String field:List.of("date_raw","played_character_id","rite_id","faith_fervor_raw","capture_epoch")){
            var bad=original.deepCopy().put(field,true);assertThrows(IllegalArgumentException.class,()->NativePlayerReligionContext.decode(bad));
            var fraction=original.deepCopy().put(field,1.0);assertThrows(IllegalArgumentException.class,()->NativePlayerReligionContext.decode(fraction));
        }
    }
}

