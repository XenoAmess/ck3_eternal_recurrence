package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.*;

/** Unqualified closed summary/source DATA only. Actual installed Store/private candidate publication is separately tested. */
final class DriverArmySummaryHistoryRowProducerTest {
    @Test void actualCompactShapeAndRolesKeepNumericDomainsAcrossPersistentRoundtrip() {
        RawHistoryRow original=row();RawHistoryRow retained=DriverArmySummaryHistoryRowProducer.decode(original.encode());assertEquals(original,retained);
        assertEquals(original.index(),retained.historyEntry().index());assertFalse(retained.result().members().containsKey("army_strengths"));
        assertFalse(retained.result().members().containsKey("queried_date_raw"));assertFalse(retained.result().members().containsKey("queried_connection_generation"));
        Value header=retained.toJson().get(DriverArmySummaryHistoryRowProducer.SOURCE_FIELD);
        PublicNumbers roles=DriverArmySummaryHistoryRowProducer.publicNumbersFromSource(header);
        Obj exposed=roles.toPublic(retained.result());assertEquals(new Text("18446744073709551615"),exposed.get("query_sequence"));
        assertEquals(retained.result(),roles.fromPublic(exposed));assertEquals(original.source().storageOriginal(),retained.source().storageOriginal());
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(original.encode()));
        assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.decode(original.encode()));
    }
    @Test void sourceDiscriminatorClosedKeysAndOriginalMetadataCannotDrift() {
        RawHistoryRow original=row();Obj body=original.toJson();String field=DriverArmySummaryHistoryRowProducer.SOURCE_FIELD;
        Obj source=OpportunityJson.object(body.get(field),"summary source");
        for(Obj bad:List.of(source.with("kind",new Text("ARMY_STRENGTHS")),source.with("schema",new Text("xar.driver-rich-read-history-source/v1")),
                source.with("full_result",refJson(ref(8))))) {
            assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.decode(OpportunityJson.encode(body.with(field,bad))));
            assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.publicNumbersFromSource(bad));
        }
        for(String key:List.of("queried_snapshot_id","queried_revision","queried_native_revision","query_sequence")) {
            Value bad=key.equals("queried_snapshot_id")?new Text("foreign"):new IntegerValue(BigInteger.valueOf(99));
            assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.decode(OpportunityJson.encode(body.with("result",original.result().with(key,bad)))));
        }
        var missing=new LinkedHashMap<String,Value>(source.members());missing.remove("storage_original");
        assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.decode(OpportunityJson.encode(body.with(field,new Obj(missing)))));
    }
    @Test void countersAndSummaryFieldsRejectWrongJsonTypesWithoutChangingNativeFrameDomain() {
        RawHistoryRow original=row();Obj body=original.toJson();String field=DriverArmySummaryHistoryRowProducer.SOURCE_FIELD;
        Obj source=OpportunityJson.object(body.get(field),"summary source");
        for(String key:List.of("connection_generation","query_sequence"))for(Value bad:List.of(new Text("1"),new Bool(true),new DecimalValue("1.0"),Nil.INSTANCE,
                new IntegerValue(BigInteger.ZERO),new IntegerValue(StrictJson.UINT64_MAX.add(BigInteger.ONE))))
            assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.decode(OpportunityJson.encode(body.with(field,source.with(key,bad)))));
        for(Value bad:List.of(new Bool(false),new Text("0"),new DecimalValue("0.0"),Nil.INSTANCE,new IntegerValue(BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(1,DriverArmySummaryHistoryRowProducer.OPERATION,true,original.result().with("army_count",bad),original.source()));
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(1,DriverArmySummaryHistoryRowProducer.OPERATION,true,original.result().with("full_result_preserved",Nil.INSTANCE),original.source()));
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(1,DriverArmySummaryHistoryRowProducer.OPERATION,false,original.result(),original.source()));
    }

    @Test void componentCustodyAndEvidenceRemainExplicitWithoutAFullArtifactAlias() {
        var s=row().source();
        assertTrue(s.evidence().containsAll(List.of(s.originalReceipt(),s.definitionSource(),s.decoderSource(),s.storageOriginal())));
        assertThrows(IllegalArgumentException.class,()->new Source(s.original(),List.of(s.original(),s.original()),s.sourceFrame(),s.source(),s.sessionId(),
                s.connectionGeneration(),s.querySequence(),s.arguments(),s.storageOriginal(),s.publicNumbers(),s.supportingEvidence(),s.producerSources()));
        assertThrows(IllegalArgumentException.class,()->new Source(s.original(),List.of(),s.sourceFrame(),s.source(),s.sessionId(),
                s.connectionGeneration(),s.querySequence(),s.arguments(),s.storageOriginal(),s.publicNumbers(),s.supportingEvidence(),s.producerSources()));
        assertThrows(IllegalArgumentException.class,()->new Source(s.original(),s.components(),s.sourceFrame(),s.source(),s.sessionId(),
                s.connectionGeneration(),s.querySequence(),s.arguments(),s.storageOriginal(),s.publicNumbers(),s.supportingEvidence(),List.of()));
    }
    private static RawHistoryRow row() {
        var frame=new ObservationIdentity("fixture-machine",new GameGeneration(23456,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(12),BigInteger.valueOf(53290200)),
                        "native:9",BigInteger.valueOf(9),"native-29829-original"),1);
        Obj numeric=new Obj(Map.of("history_summary_schema",new Text("xar.ck3.army-query-history-summary.v1"),"step",new Text(DriverArmySummaryHistoryRowProducer.OPERATION),
                "accepted",new Bool(true),"status",new Text("completed"),"query_sequence",new IntegerValue(StrictJson.UINT64_MAX),
                "queried_snapshot_id",new Text("native:9"),"queried_revision",new IntegerValue(BigInteger.valueOf(9)),"queried_native_revision",new IntegerValue(BigInteger.valueOf(12)),
                "army_count",new IntegerValue(BigInteger.ZERO),"armies",new Arr(List.of()))).with("full_result_preserved",new Bool(false));
        PublicNumbers roles=PublicNumbers.fromResults(new RawJson(OpportunityJson.encode(numeric)),new RawJson(OpportunityJson.encode(numeric.with("query_sequence",new Text(StrictJson.UINT64_MAX.toString())))));
        var original=new ReadBinding("data-only-army-read",ref(1),ref(2),ref(3));
        var source=new Source(original,List.of(original),frame,new G2Source("fixture-machine","2026-10-24T00:00:00Z","1.20.0.4",ref(0)),"data-only-session",
                StrictJson.UINT64_MAX,StrictJson.UINT64_MAX,new Obj(Map.of()),ref(6),roles,List.of(ref(4),ref(6)),List.of(ref(5)));
        return new RawHistoryRow(1,DriverArmySummaryHistoryRowProducer.OPERATION,true,numeric,source);
    }
    private static Obj refJson(ExactRef ref){return org.xar.ck3.control.application.driver.DriverJson.object(StrictJson.canonical(ref.toJson()),1048576);}
    private static ExactRef ref(int id){return new ExactRef("data-only-summary/"+id,1,"%064x".formatted(id+1));}
}
