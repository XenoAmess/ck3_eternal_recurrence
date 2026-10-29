package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootDriverLifecyclePublicCodec.*;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original producer fixtures are software DATA; malformed role scalars confer no action authority. */
final class RootDriverLifecycleEndingRoleTypesTest {
    private record Original(SubmittedClose source,RawJson life) { }
    private static Original retained;
    private static synchronized Original original() throws Exception {
        if(retained!=null)return retained;
        var corpusMethod=RootDriverLifecyclePublicCodecTest.class.getDeclaredMethod("originalCases");corpusMethod.setAccessible(true);
        var corpus=assertInstanceOf(OpportunityJson.Obj.class,corpusMethod.invoke(null));
        var row=OpportunityJson.object(OpportunityJson.array(corpus.get("cases"),"cases").getFirst(),"case");
        var materialMethod=RootDriverLifecyclePublicCodecTest.class.getDeclaredMethod("material",OpportunityJson.Obj.class);materialMethod.setAccessible(true);
        var source=assertInstanceOf(SubmittedClose.class,materialMethod.invoke(null,row));
        var lifeMethod=RootDriverLifecyclePublicCodecTest.class.getDeclaredMethod("producedLife",int.class);lifeMethod.setAccessible(true);
        retained=new Original(source,assertInstanceOf(RawJson.class,lifeMethod.invoke(null,source.startingDateRaw())));return retained;
    }
    private static SubmittedClose submitted(RawJson ending) throws Exception {
        var original=original();var source=original.source();
        return new SubmittedClose(ClosePhase.POST_ADVANCE_UNCONFIRMED,source.submissionAck(),source.initialQuery(),source.postAttempts(),source.startingDateRaw(),ending,Optional.of(original.life()),source.failure());
    }
    private static RawJson nested(String field,OpportunityJson.Value bad) throws Exception {
        var row=DriverJson.object(original().source().endingSnapshot().bytes(),RawJson.MAXIMUM_BYTES);
        var player=OpportunityJson.object(row.get("played_character"),"played_character");
        return new RawJson(DriverJson.encode(row.with("played_character",player.with(field,bad))));
    }
    private static RawJson publicEnding(String field,boolean actor) throws Exception {
        RawJson valid=encodeCloseMaterial(submitted(original().source().endingSnapshot()));
        assertArrayEquals(valid.bytes(),encodeCloseData(decodeCloseData(valid)).bytes());
        var row=PublicDataJson.object(valid);
        var ending=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,row.get("post_advance_snapshot"));
        if(actor)ending.put(field,true);else ending.put(field,1);
        return PublicDataJson.encode(row);
    }
    @Test void nestedActorBooleanIsRejected() throws Exception {
        var bad=nested("character_id",new OpportunityJson.Bool(true));
        assertThrows(IllegalArgumentException.class,()->submitted(bad));
    }
    @Test void nestedAliveIntegerIsRejected() throws Exception {
        var bad=nested("alive",new OpportunityJson.IntegerValue(java.math.BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->submitted(bad));
    }
    @Test void publicEndingActorBooleanIsRejected() throws Exception {
        var bad=publicEnding("played_character_id",true);
        assertThrows(IllegalArgumentException.class,()->decodeCloseData(bad));
    }
    @Test void publicEndingAliveIntegerIsRejected() throws Exception {
        var bad=publicEnding("played_character_alive",false);
        assertThrows(IllegalArgumentException.class,()->decodeCloseData(bad));
    }
}
