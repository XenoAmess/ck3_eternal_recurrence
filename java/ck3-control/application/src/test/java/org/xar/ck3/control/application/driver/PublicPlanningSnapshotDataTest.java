package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.*;
import org.xar.ck3.control.application.history.DriverExecuteReadHistoryRegistry;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Typed DATA rows and original Native/Driver assembler fixture. No private archive Candidate, live PLAN,
 * Complete/source authority, query or registration is manufactured by the new DATA adapters. */
final class PublicPlanningSnapshotDataTest {
    private static Obj semantic() {
        return assertInstanceOf(DriverObservationAssembler.Complete.class,DriverObservationAssemblerTest.join(DriverObservationAssemblerTest.STATE)).semantic();
    }
    private static RawJson raw(Obj value){return new RawJson(DriverJson.encode(value));}
    private static Arr rows(Obj original){return new Arr(array(original.get("native_command_history"),"history"));}
    @Test void fullAndOriginalTranscriptAbsentPlanningSnapshotsUseTheSameOwningRolesAndInverse() {
        Obj actual=semantic().with("native_revision",new IntegerValue(StrictJson.UINT64_MAX));
        var full=PublicSnapshotCodec.encodePlanningSnapshotData(raw(actual));
        assertEquals(PublicSnapshotCodec.encodeSemanticData(raw(actual)),full);
        assertEquals(actual,DriverJson.object(PublicSnapshotCodec.decodePlanningSnapshotData(full).bytes(),RawJson.MAXIMUM_BYTES));
        var fields=new LinkedHashMap<>(actual.members());for(String key:List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures"))fields.remove(key);
        Obj absent=new Obj(fields);RawJson publicAbsent=PublicSnapshotCodec.encodePlanningSnapshotData(raw(absent));
        assertEquals(absent,DriverJson.object(PublicSnapshotCodec.decodePlanningSnapshotData(publicAbsent).bytes(),RawJson.MAXIMUM_BYTES));
        Obj exposed=DriverJson.object(publicAbsent.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new Text(StrictJson.UINT64_MAX.toString()),exposed.get("native_revision"));
        for(String key:List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures"))assertFalse(exposed.members().containsKey(key));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningSnapshotData(raw(absent.with("native_rollback_war_failure",Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningSnapshotData(raw(absent.with("revision",new Bool(true)))));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningSnapshotData(new RawJson(DriverObservationAssemblerTest.STATE.getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
    @Test void finiteExecuteRowsUseOneOwningResultTransformationAndPreserveExplicitMissingNativeSequenceAsNull() {
        for(boolean nativeSequence:List.of(false,true)) {
            var produced=row(nativeSequence);assertEquals(produced,DriverExecuteQueryHistoryRowProducer.decode(produced.encode()));
            Arr original=new Arr(List.of(produced.toJson()));Arr encoded=PublicSnapshotCodec.encodePlanningHistoryData(original);
            assertEquals(original,PublicSnapshotCodec.decodePlanningHistoryData(encoded));
            Obj exposed=object(array(encoded,"history").getFirst(),"row");Obj source=object(exposed.get(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD),"source");
            assertEquals(new Text(StrictJson.UINT64_MAX.toString()),source.get("connection_generation"));
            assertEquals(nativeSequence?new Text(StrictJson.UINT64_MAX.toString()):Nil.INSTANCE,source.get("query_sequence"));
            assertEquals(new Text(Long.toString(Long.MAX_VALUE)),object(exposed.get("result"),"result").get("source_metric"));
            assertEquals(object(produced.toJson().get(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD),"originalSource").get("source_frame"),source.get("source_frame"));
            Obj complete=semantic().with("native_command_history",original);
            Obj publicComplete=DriverJson.object(PublicSnapshotCodec.encodePlanningSnapshotData(raw(complete)).bytes(),RawJson.MAXIMUM_BYTES);
            assertEquals(encoded,rows(publicComplete));
            assertEquals(complete,DriverJson.object(PublicSnapshotCodec.decodePlanningSnapshotData(raw(publicComplete)).bytes(),RawJson.MAXIMUM_BYTES));
        }
    }
    @Test void malformedFiniteSourceAndUnknownWideHistoryCannotAcquireGuessedNumberRoles() {
        Arr valid=PublicSnapshotCodec.encodePlanningHistoryData(new Arr(List.of(row(true).toJson())));
        Obj row=object(array(valid,"history").getFirst(),"row");String field=DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD;Obj source=object(row.get(field),"source");
        for(Value wrong:List.of(new Bool(true),new IntegerValue(BigInteger.ONE),new Text("01"),new Text(StrictJson.UINT64_MAX.add(BigInteger.ONE).toString()),Nil.INSTANCE))
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningHistoryData(new Arr(List.of(row.with(field,source.with("connection_generation",wrong))))));
        for(Obj wrong:List.of(source.with("schema",new Text("xar.driver-rich-read-history-source/v1")),source.with("query_sequence",new Bool(true)),source.with("public_number_roles",new Arr(List.of()))))
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningHistoryData(new Arr(List.of(row.with(field,wrong)))));
        var missing=new LinkedHashMap<>(source.members());missing.remove("query_sequence");
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningHistoryData(new Arr(List.of(row.with(field,new Obj(missing))))));
        Obj unqualified=new Obj(java.util.Map.of()).with("index",new IntegerValue(BigInteger.ONE)).with("command",new Text("unqualified-extension"))
                .with("ok",new Bool(true)).with("result",new Obj(java.util.Map.of()).with("unproved_id",new IntegerValue(BigInteger.valueOf(Long.MAX_VALUE))));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningHistoryData(new Arr(List.of(unqualified))));
        assertEquals(new Arr(List.of()),PublicSnapshotCodec.decodePlanningHistoryData(PublicSnapshotCodec.encodePlanningHistoryData(new Arr(List.of()))));
    }
    /** Only public Source DATA constructors, not the private installed projection/archive Candidate path. */
    private static RawHistoryRow row(boolean sequence) {
        var operation=DriverExecuteReadHistoryRegistry.Entry.CAREER_OWNER.logicalOperation();
        var originalCommand=new OperationKey(operation.value()+"-73-61");
        Obj result=new Obj(java.util.Map.of()).with("step",new Text(operation.value())).with("accepted",new Bool(true)).with("status",new Text("available"))
                .with("source_metric",new IntegerValue(BigInteger.valueOf(Long.MAX_VALUE)));
        if(sequence)result=result.with("query_sequence",new IntegerValue(StrictJson.UINT64_MAX));
        Obj exposed=result.with("source_metric",new Text(Long.toString(Long.MAX_VALUE)));
        if(sequence)exposed=exposed.with("query_sequence",new Text(StrictJson.UINT64_MAX.toString()));
        var numbers=PublicNumbers.fromResults(raw(result),raw(exposed));
        var binding=new ReadBinding("data-only-execute-read","data-only-request",ref(1),ref(2),ref(3),ref(4),
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,Optional.of("data-only-read-capability"),"data-only-permission");
        List<ExactRef> closure=List.of(ref(1),ref(2),ref(3),ref(4),ref(5),ref(6),ref(7));
        var source=new Source(binding,operation,originalCommand,DriverStateAssemblerTest.identity(),DriverStateAssemblerTest.source(),"data-only-held-session",StrictJson.UINT64_MAX,
                sequence?Optional.of(StrictJson.UINT64_MAX):Optional.empty(),new Obj(java.util.Map.of()),ref(5),numbers,closure,List.of(ref(6)),List.of(ref(7)));
        return new RawHistoryRow(3,originalCommand.value(),true,result,source);
    }
    private static ExactRef ref(int value){return new ExactRef("data-only-plan-history/"+value,1,"%064x".formatted(value));}
}
