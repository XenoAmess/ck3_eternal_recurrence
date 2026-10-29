package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Unqualified source DATA tests only. Actual central attempt/archive/writer positives live in the sole publication fixture. */
final class DriverFailedReadHistoryRowProducerTest {
    @Test void finiteErrorDataRoundTripsWithoutInventingResultOrAfterFrame() {
        var original=row();var decoded=DriverFailedReadHistoryRowProducer.decode(original.encode());assertEquals(original,decoded);
        assertFalse(decoded.ok());assertFalse(decoded.toJson().members().containsKey("result"));
        assertEquals("IllegalStateException: native decode failed",decoded.error());
        assertEquals(original.source(),decoded.source());assertEquals(original.index(),decoded.historyEntry().index());
        assertEquals(9,decoded.source().evidence().size());
        assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(encode(changed(original.toJson(),"result",Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(encode(changed(original.toJson(),"ok",new Bool(true)))));
        assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(encode(changed(original.toJson(),"index",new Bool(true)))));
    }
    @Test void commandKindAndSourceRemainFiniteAcrossSerde() {
        var original=row();
        assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(encode(changed(original.toJson(),"command",new Text("player-rite-creation-action-v1")))));
        var source=OpportunityJson.object(original.toJson().get(DriverFailedReadHistoryRowProducer.SOURCE_FIELD),"source");
        for(String field:List.of("schema","kind")) {
            Obj malformed=changed(source,field,new Text("unknown"));
            assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(encode(changed(original.toJson(),DriverFailedReadHistoryRowProducer.SOURCE_FIELD,malformed))));
        }
        var missing=new LinkedHashMap<String,Value>(original.toJson().members());missing.remove("error");
        assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(encode(new Obj(missing))));
        var extra=changed(source,"after_frame",new Text("invented"));
        assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(encode(changed(original.toJson(),DriverFailedReadHistoryRowProducer.SOURCE_FIELD,extra))));
    }
    @Test void invalidOriginalReferencesAndComponentListsCannotBecomeSourceData() {
        var s=row().source();
        assertThrows(IllegalArgumentException.class,()->new DriverFailedReadHistoryRowProducer.Source(s.kind(),s.contractId(),s.requestId(),
                s.attempt(),s.beforeDriver(),s.driverFacts(),s.nativeFrame(),List.of(ref(8),ref(8)),s.supportingEvidence(),s.producerSources()));
        assertThrows(IllegalArgumentException.class,()->new DriverFailedReadHistoryRowProducer.Source(s.kind(),s.contractId(),s.requestId(),
                s.attempt(),s.beforeDriver(),s.driverFacts(),s.nativeFrame(),List.of(),List.of(ref(4)),s.producerSources()));
        assertThrows(IllegalArgumentException.class,()->new DriverFailedReadHistoryRowProducer.Source(s.kind(),s.contractId(),s.requestId(),
                s.attempt(),s.beforeDriver(),s.driverFacts(),s.nativeFrame(),List.of(),s.supportingEvidence(),List.of()));
    }
    @Test void unavailableErrorMatchesActualJavaSurfaceWithoutAcceptingCallerThrowable() {
        var actual=new PlanningReadResult.Unavailable<Object>("native decode failed",Optional.empty());
        var thrown=DriverReadHistoryFailureMaterial.unavailableException(actual);
        assertEquals(IllegalStateException.class,thrown.getClass());assertEquals(actual.reason(),thrown.getMessage());
        assertEquals(thrown.getClass().getSimpleName()+": "+thrown.getMessage(),DriverReadHistoryFailureMaterial.unavailableError(actual));
        var absent=new DriverReadHistoryFailureMaterial.Unrecorded(DriverReadHistoryFailureMaterial.Reason.NO_ORIGINAL_ATTEMPT,"no actual prepared attempt");
        assertEquals(DriverReadHistoryFailureMaterial.Reason.NO_ORIGINAL_ATTEMPT,absent.reason());
        assertThrows(IllegalArgumentException.class,()->new DriverReadHistoryFailureMaterial.StorageDiagnostic("IOException","x".repeat(8193)));
    }
    private static DriverFailedReadHistoryRowProducer.RawHistoryRow row() {
        var source=new DriverFailedReadHistoryRowProducer.Source(DriverReadHistoryFailureMaterial.Kind.ARMY_STRENGTHS,"army/actual","actual-request",
                ref(0),ref(1),ref(2),ref(3),List.of(ref(8)),List.of(ref(4),ref(5),ref(6),ref(7)),List.of(ref(7)));
        return new DriverFailedReadHistoryRowProducer.RawHistoryRow(1,DriverFailedReadHistoryRowProducer.STEP,false,"IllegalStateException: native decode failed",source);
    }
    private static ExactRef ref(int value){return new ExactRef("data-only/"+value,1,"%064x".formatted(value+1));}
    private static Obj changed(Obj original,String key,Value value){var fields=new LinkedHashMap<String,Value>(original.members());fields.put(key,value);return new Obj(fields);}
    private static byte[] encode(Obj value){return OpportunityJson.encode(value);}
}
