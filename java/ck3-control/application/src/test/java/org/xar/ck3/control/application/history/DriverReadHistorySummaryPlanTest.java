package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.*;

/** Plan/summary DATA only. These callbacks mint no actual Store Result, Known, writer or Source authority. */
final class DriverReadHistorySummaryPlanTest {
    @Test void planConstructionAndReadonlyReplayDoNotCaptureAndLiveCaptureIsOnce() throws Exception {
        var captures=new AtomicInteger();var replays=new AtomicInteger();var validations=new AtomicInteger();
        SummaryProjection original=summary(storage("disabled"));
        var plan=new ArmySummaryPlan(()->{captures.incrementAndGet();return original;},raw->{replays.incrementAndGet();return summary(raw);},
                value->{assertSame(original,value);validations.incrementAndGet();},List.of(source()));
        assertEquals(Kind.ARMY_STRENGTHS,plan.kind());assertEquals(0,captures.get());
        SummaryProjection replayed=plan.replayOriginal(original.storageOriginal());
        assertEquals(original.summary(),replayed.summary());assertEquals(0,captures.get());assertEquals(1,replays.get());
        assertThrows(IllegalArgumentException.class,()->plan.requireOriginal(replayed));
        assertSame(original,plan.captureOriginal());assertSame(original,plan.captureOriginal());assertEquals(1,captures.get());
        plan.requireOriginal(original);assertEquals(1,validations.get());
        assertThrows(IllegalArgumentException.class,()->plan.requireOriginal(replayed));
        assertInstanceOf(SummaryStored.class,new SummaryStored(new ExactRef("actual-small-row-data-only",1,"2".repeat(64))));
    }
    @Test void captureFailureIsTerminalAndCannotRetryStorage() {
        var captures=new AtomicInteger();var plan=new ArmySummaryPlan(()->{captures.incrementAndGet();throw new IOException("actual capture failed");},
                DriverReadHistorySummaryPlanTest::summary,value->{},List.of(source()));
        assertThrows(IOException.class,plan::captureOriginal);assertEquals(1,captures.get());
        assertThrows(IllegalArgumentException.class,plan::captureOriginal);assertEquals(1,captures.get());
    }
    @Test void replayCannotReplaceArchivedStorageOriginalOrOmitInstalledSources() {
        RawJson actual=storage("disabled"),different=storage("budget_exhausted");
        var plan=new ArmySummaryPlan(()->summary(actual),ignored->summary(different),value->{},List.of(source()));
        assertThrows(IllegalArgumentException.class,()->plan.replayOriginal(actual));
        var other=new ExactRef("foreign-source-data-only",1,"3".repeat(64));
        var noClosure=new ArmySummaryPlan(()->new SummaryProjection(summary(actual).summary(),summary(actual).publicNumbers(),actual,List.of(),List.of(other)),
                DriverReadHistorySummaryPlanTest::summary,value->{},List.of(source()));
        assertThrows(IllegalArgumentException.class,noClosure::captureOriginal);
        assertThrows(IllegalArgumentException.class,noClosure::captureOriginal);
    }
    @Test void compactNumericAndTypedPublicPairRoundtripWithoutInventingFullResultOrFrameFields() {
        var original=summary(storage("disabled"));Obj numeric=DriverJson.object(original.summary().bytes(),RawJson.MAXIMUM_BYTES);
        var roles=PublicNumbers.fromJson(OpportunityJson.parse(OpportunityJson.encode(original.publicNumbers().toJson())));
        Obj publicBody=roles.toPublic(numeric);assertEquals(new Text("18446744073709551615"),publicBody.get("query_sequence"));
        assertEquals(numeric,roles.fromPublic(publicBody));assertFalse(numeric.members().containsKey("army_strengths"));
        assertFalse(numeric.members().containsKey("queried_connection_generation"));assertFalse(numeric.members().containsKey("queried_date_raw"));
        assertTrue(original.materialEvidence().isEmpty());
        for(Value wrong:List.of(new Bool(true),new Text("0"),new DecimalValue("0.0"),Nil.INSTANCE,new IntegerValue(BigInteger.ONE))) {
            Obj malformed=numeric.with("army_count",wrong);
            var publicWrong=malformed.with("query_sequence",new Text("18446744073709551615"));
            var publicRoles=PublicNumbers.fromResults(raw(malformed),raw(publicWrong));
            assertThrows(IllegalArgumentException.class,()->new SummaryProjection(raw(malformed),publicRoles,original.storageOriginal(),List.of(),List.of(source())));
        }
        assertThrows(IllegalArgumentException.class,()->new SummaryProjection(raw(numeric.with("full_result_preserved",Nil.INSTANCE)),original.publicNumbers(),original.storageOriginal(),List.of(),List.of(source())));
    }
    private static SummaryProjection summary(RawJson storage) {
        Obj numeric=new Obj(Map.of("history_summary_schema",new Text("xar.ck3.army-query-history-summary.v1"),"step",new Text("query-army-strengths-v1"),
                "accepted",new Bool(true),"status",new Text("completed"),"query_sequence",new IntegerValue(new BigInteger("18446744073709551615")),
                "army_count",new IntegerValue(BigInteger.ZERO),"armies",new Arr(List.of()),"full_result_preserved",new Bool(false),
                "unavailable_reason",new Text("sidecar_disabled_by_session_budget")));
        var roles=PublicNumbers.fromResults(raw(numeric),raw(numeric.with("query_sequence",new Text("18446744073709551615"))));
        return new SummaryProjection(raw(numeric),roles,storage,List.of(),List.of(source()));
    }
    private static RawJson storage(String status){return raw(new Obj(Map.of("status",new Text(status))));}
    private static RawJson raw(Obj value){return new RawJson(OpportunityJson.encode(value));}
    private static ExactRef source(){return new ExactRef("data-only-installed-source",1,"1".repeat(64));}
}
