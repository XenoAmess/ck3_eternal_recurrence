package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryMaterial.*;

/** Complete software DATA and serde only; no Source, private invocation, Known or Managed scope is fabricated. */
final class DriverReturnedPublicReadHistoryMaterialTest {
    private static final String H="query-route-contact-horizon-v1-0-to-9-h-1-2",P="preview-move-army-0-to-9";
    private static Obj json(String raw){return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
    private static Obj change(Obj row,String key,Value value){var fields=new LinkedHashMap<>(row.members());fields.put(key,value);return new Obj(fields);}
    private static ExactRef ref(String name){return new ExactRef("shape-only-not-a-live-source/"+name,1,"a".repeat(64));}
    private static Obj horizon(){return json("""
            {"schema":"xar.route-contact-readonly-unavailable.v1","step":"query-route-contact-horizon-v1-0-to-9-h-1-2",
             "accepted":false,"available":false,"status":"unavailable","read_only":true,"business_submission":false,
             "replay_allowed":false,"replan_required":true,"route_contact_horizon":null,"backend_id":"native-headless",
             "opaque":{"ordered":[3,1],"null":null}}
            """);}
    private static Obj preview(){return json("""
            {"step":"preview-move-army-0-to-9","accepted":false,"status":"deferred","backend_id":"native-headless",
             "route_preview":{"status":"deferred","reason":"army_not_move_ready","army_id":0,"target_province_id":9,
              "origin_province_id":-1,"route_province_ids":[],"native_error":"CK3 army state rejects movement"},
             "opaque":{"literal":"001","missing_null":null}}
            """);}
    @Test void onlyTheTwoOriginalReturnedPoliciesAndTheirOwningParsersAreAccepted() {
        for(var entry:Map.of(Kind.HORIZON_UNAVAILABLE,horizon(),Kind.PREVIEW_DEFERRED,preview()).entrySet()) {
            String logical=entry.getKey()==Kind.HORIZON_UNAVAILABLE?H:P;
            var value=new Projection(entry.getKey(),new OperationKey(logical),new OperationKey("actual-encoded-command"),
                    RawJson.fullMaterial(DriverJson.encode(entry.getValue())),new PublicNumbers(List.of()),List.of(ref("formatter.java")));
            assertEquals(entry.getValue(),DriverJson.object(value.fullResult().bytes(),DriverJson.MAX_NATIVE_BYTES));
            assertEquals(new OperationKey("actual-encoded-command"),value.originalCommand());
        }
        for(String invalid:List.of("query-route-contact-horizon-v1-0-to-9-h-1-0",
                "query-route-contact-horizon-v1-0-to-9-h-2-2","query-route-contact-horizon-v1-00-to-9-h-1-2",
                "advance-route-contact-horizon-v1-0-to-9-h-1-2","query-army-strengths-v1"))
            assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.requireLogical(Kind.HORIZON_UNAVAILABLE,new OperationKey(invalid)));
        for(String invalid:List.of("preview-move-army-00-to-9","preview-move-army-0-to-0","preview-move-army-2147483648-to-9","move-army-0-to-9"))
            assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.requireLogical(Kind.PREVIEW_DEFERRED,new OperationKey(invalid)));
    }
    @Test void wrongTypedReturnedSurfaceCannotBecomeTheOtherPolicyOrASuccessfulRead() {
        for(Obj invalid:List.of(change(horizon(),"accepted",new IntegerValue(BigInteger.ZERO)),change(horizon(),"accepted",new Bool(true)),
                change(horizon(),"read_only",new IntegerValue(BigInteger.ONE)),change(horizon(),"route_contact_horizon",new Obj(Map.of())),
                change(horizon(),"schema",new Text("xar.other-unavailable/v1")),change(horizon(),"step",new Text(P))))
            assertThrows(IllegalArgumentException.class,()->new Projection(Kind.HORIZON_UNAVAILABLE,new OperationKey(H),new OperationKey(H),
                    RawJson.fullMaterial(DriverJson.encode(invalid)),new PublicNumbers(List.of()),List.of(ref("source"))));
        var missing=new LinkedHashMap<>(horizon().members());missing.remove("route_contact_horizon");
        assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.requireReport(Kind.HORIZON_UNAVAILABLE,new OperationKey(H),new Obj(missing)));
        Obj wrongPreview=change(preview(),"route_preview",json("{\"status\":\"deferred\",\"reason\":\"army_not_move_ready\",\"army_id\":false,\"target_province_id\":9}"));
        assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.requireReport(Kind.PREVIEW_DEFERRED,new OperationKey(P),wrongPreview));
    }
    @Test void invocationDataCopiesItsSourceClosureAndUsesTheOneStrictSerdeWithoutMintingAToken() {
        var frames=new FrameOriginals(ref("driver"),ref("known"),ref("native"),ref("facts"),ref("readback-native"),ref("readback-facts"));
        var mutable=new ArrayList<>(List.of(ref("actual-source.java")));
        var input=new InvocationData(ref("actual-cp19-metadata"),new OperationKey("encoded-original"),frames,ref("caller"),ref("epoch"),7,"b".repeat(64),mutable);
        mutable.clear();assertEquals(1,input.producerSources().size());assertThrows(UnsupportedOperationException.class,()->input.producerSources().clear());
        var encoded=DriverReturnedPublicReadHistoryRowProducer.invocationJson(input);
        assertEquals(input,DriverReturnedPublicReadHistoryRowProducer.decodeInvocation(encoded.bytes()));
        Obj wire=DriverJson.object(encoded.bytes(),DriverJson.MAX_NATIVE_BYTES);
        for(Obj invalid:List.of(change(wire,"head_sequence",new Bool(true)),change(wire,"head_sequence",new Text("07")),
                change(wire,"head_sequence",new IntegerValue(BigInteger.valueOf(7))),change(wire,"unknown_alias",Nil.INSTANCE)))
            assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.decodeInvocation(DriverJson.encode(invalid)));
        assertEquals(0,CandidateTokenCount.count());
    }
    /** There is no public constructor for the live private candidate; pure data never constructs one. */
    private static final class CandidateTokenCount {
        static int count(){return DriverReturnedPublicReadHistoryRowProducer.Candidate.class.getConstructors().length;}
    }
}

