package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.junit.jupiter.api.Assertions.*;

/** Same original software producer from Known11 -> actual installed native decoder and explicit history profiles. */
final class PendingNativeEnvelopeBoundaryTest {
    private static final ExactRef REF=new ExactRef("software/pending-envelope-source",1,"a".repeat(64));
    @Test void actualReadContractOnlyConsumesOriginalNativeSevenFields()throws Exception {
        ObjectNode row=object(InteractionDirectPublicProductionTest.original().get("pending"));
        Context context=InteractionDirectPublicProductionTest.project(InteractionDirectPublicProductionTest.frame(object(row.get("frame")),Build.WANDERER6),Build.WANDERER6);
        var contract=PendingInteractionContracts.pending(REF);ObjectNode input=InteractionArguments.body(context).put("pending_id",context.controls().pending().instance().value());
        var request=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),contract.operation(),InteractionArguments.app(input),context.deadline());
        var receipt=InteractionDirectPublicProductionTest.receipt(contract,request,raw(row.get("native")));
        PendingContext expected=PendingContextCodec.decodeNative(raw(row.get("native")),context,context.controls().pending().instance());
        assertEquals(expected,contract.decode(receipt));assertEquals(expected,contract.replay(receipt));
        ObjectNode recorded=recorded(object(row.get("native")),context);
        var wrong=InteractionDirectPublicProductionTest.receipt(contract,request,raw(recorded));
        assertThrows(IllegalArgumentException.class,()->contract.decode(wrong));assertThrows(IllegalArgumentException.class,()->contract.replay(wrong));
        assertEquals(expected,PendingContextCodec.decode(raw(recorded),context,context.controls().pending().instance()));
    }
    @Test void nativeAndOriginalRecordedDriverPublicProfilesKeepExactSerializationAndLegacyAbsence()throws Exception {
        ObjectNode row=object(InteractionDirectPublicProductionTest.original().get("pending"));
        Context context=InteractionDirectPublicProductionTest.project(InteractionDirectPublicProductionTest.frame(object(row.get("frame")),Build.WANDERER6),Build.WANDERER6);
        var id=context.controls().pending().instance();ObjectNode nativeResult=object(row.get("native"));PendingContext typed=PendingContextCodec.decodeNative(raw(nativeResult),context,id);
        ObjectNode recorded=recorded(nativeResult,context),legacy=recorded.deepCopy();legacy.remove("backend_id");byte[] original=DriverJson.encodeNode(legacy);
        ObjectNode exact=object(row.get("public")),driver=exact.deepCopy();driver.remove(List.of("source","scope","binding"));
        for(ObjectNode profile:List.of(nativeResult,recorded,legacy,driver,exact)) {
            assertEquals(typed,PendingContextCodec.decode(raw(profile),context,id));
            ObjectNode replay=object(DriverJson.toNode(DriverJson.object(DriverJson.encodeNode(profile),DriverJson.MAX_NATIVE_BYTES)));
            assertEquals(DriverJson.fromNode(profile),DriverJson.fromNode(replay));assertEquals(typed,PendingContextCodec.decode(raw(replay),context,id));
        }
        assertArrayEquals(original,DriverJson.encodeNode(legacy));assertFalse(legacy.has("backend_id"));
        assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decodeNative(raw(legacy),context,id));
        assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decodeNative(raw(exact),context,id));
    }
    @Test void extraMissingNullWrongTypeBackendMirrorSourceAndHeaderCannotBorrowAnotherProfile()throws Exception {
        ObjectNode row=object(InteractionDirectPublicProductionTest.original().get("pending"));
        Context context=InteractionDirectPublicProductionTest.project(InteractionDirectPublicProductionTest.frame(object(row.get("frame")),Build.WANDERER6),Build.WANDERER6);var id=context.controls().pending().instance();
        List<java.util.function.Consumer<ObjectNode>> nativeMutations=List.of(value->value.remove("backend_id"),value->value.putNull("backend_id"),
                value->value.put("backend_id",true),value->value.put("backend_id","other-driver"),value->value.put("extra",1),
                value->value.put("queried_revision",context.before().frame().revision()));
        for(var mutate:nativeMutations){ObjectNode changed=object(row.get("native")).deepCopy();mutate.accept(changed);
            assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decodeNative(raw(changed),context,id));}
        List<java.util.function.Consumer<ObjectNode>> publicMutations=List.of(value->value.remove("queried_native_revision"),value->value.put("queried_revision",true),
                value->value.put("pending_character_interaction_context_ready",true),value->value.put("schema_version",true),
                value->object(value.get("binding")).put("pending_interaction_id",id.value()+1),value->object(value.get("source")).put("backend_id","other-driver"),
                value->object(value.get("source")).put("native_revision",context.revision().add(java.math.BigInteger.ONE)),value->value.putNull("scope"));
        for(var mutate:publicMutations){ObjectNode changed=object(row.get("public")).deepCopy();mutate.accept(changed);
            assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(raw(changed),context,id));}
    }
    private static ObjectNode recorded(ObjectNode nativeResult,Context context){return nativeResult.deepCopy().put("queried_snapshot_id",context.before().frame().snapshotId()).put("queried_revision",context.before().frame().revision()).put("queried_native_revision",context.revision());}
    private static ObjectNode object(JsonNode node){assertInstanceOf(ObjectNode.class,node);return (ObjectNode)node;}
    private static RawJson raw(JsonNode value){return new RawJson(DriverJson.encodeNode(value));}
}
