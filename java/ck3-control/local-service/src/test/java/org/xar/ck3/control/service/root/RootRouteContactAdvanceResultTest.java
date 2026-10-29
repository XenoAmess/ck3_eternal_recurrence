package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;

/** Existing typed AdvanceResult producer -> Route representation -> strict paired decode.
 * These DATA tests grant no Root, clock admission, refreshed packet or native business success. */
final class RootRouteContactAdvanceResultTest {
    private static final OperationKey STEP=new OperationKey("advance-route-contact-horizon-v1-10-to-90-h-2-20-30");
    private static RawJson partial(BigInteger endingRevision) {
        // Shared test-only helper owns the original typed Command/Plan/Frame/Outcome producer.
        RawJson original=RootLifeAdvancePublicResultTest.producedClockReport(STEP,endingRevision);
        Obj result=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        var refresh=new LinkedHashMap<String,Value>();
        refresh.put("attempted",new Bool(true));refresh.put("ack_status",new Text("already_paused"));
        refresh.put("from_snapshot_id",result.get("starting_snapshot_id"));
        refresh.put("from_revision",result.get("starting_revision"));
        refresh.put("from_native_revision",result.get("starting_native_revision"));
        refresh.put("to_snapshot_id",result.get("snapshot_id"));refresh.put("to_revision",result.get("revision"));
        refresh.put("to_native_revision",result.get("native_revision"));refresh.put("date_raw",result.get("ending_date_raw"));
        return new RawJson(DriverJson.encode(result.with("contact_refresh",new Obj(refresh))));
    }
    @Test void actualClockProducerKeepsBeyondUint64And4300DigitRefreshRevisionsExactly() {
        for(BigInteger revision:new BigInteger[]{BigInteger.ONE.shiftLeft(64),new BigInteger("9".repeat(4300))}) {
            RawJson original=partial(revision);RawJson wire=RootRouteContactAdvanceResult.encode(original,STEP);
            Obj publicResult=DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES);
            assertEquals(new Text(revision.toString()),publicResult.get("revision"));
            assertEquals(new Text(revision.toString()),object(publicResult.get("contact_refresh"),"contact_refresh").get("to_revision"));
            assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),
                    DriverJson.object(RootRouteContactAdvanceResult.decode(wire,STEP).bytes(),RawJson.MAXIMUM_BYTES));
            assertEquals(wire,RootRouteContactAdvanceResult.encode(RootRouteContactAdvanceResult.decode(wire,STEP),STEP));
        }
    }
    @Test void missingNullAndWrongRefreshRolesCannotBecomeCanonicalPublicIntegers() {
        Obj actual=DriverJson.object(partial(BigInteger.TEN).bytes(),RawJson.MAXIMUM_BYTES);
        Obj refresh=object(actual.get("contact_refresh"),"contact_refresh");
        for(Value wrong:new Value[]{new Bool(true),new DecimalValue("1.0"),new IntegerValue(BigInteger.valueOf(-1)),
                new Text("1"),new IntegerValue(new BigInteger("1"+"0".repeat(4300)))}) {
            var broken=RawJson.fullMaterial(DriverJson.encode(actual.with("contact_refresh",refresh.with("to_revision",wrong))));
            assertThrows(IllegalArgumentException.class,()->RootRouteContactAdvanceResult.encode(broken,STEP));
        }
        var missing=new LinkedHashMap<>(refresh.members());missing.remove("to_revision");
        assertThrows(IllegalArgumentException.class,()->RootRouteContactAdvanceResult.encode(
                new RawJson(DriverJson.encode(actual.with("contact_refresh",new Obj(missing)))),STEP));
        // A real attempted refresh may have no published successor. Explicit null survives as null.
        var noSuccessor=new RawJson(DriverJson.encode(actual.with("contact_refresh",refresh.with("to_revision",Nil.INSTANCE).with("to_native_revision",Nil.INSTANCE))));
        var wire=RootRouteContactAdvanceResult.encode(noSuccessor,STEP);
        assertEquals(Nil.INSTANCE,object(DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES).get("contact_refresh"),"refresh").get("to_revision"));
        assertEquals(DriverJson.object(noSuccessor.bytes(),RawJson.MAXIMUM_BYTES),
                DriverJson.object(RootRouteContactAdvanceResult.decode(wire,STEP).bytes(),RawJson.MAXIMUM_BYTES));
    }
    @Test void publicRefreshStringsAndTheOriginalParsedStepRemainDistinctTypedRoles() {
        var wire=RootRouteContactAdvanceResult.encode(partial(BigInteger.ONE.shiftLeft(64)),STEP);
        Obj root=DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES);Obj refresh=object(root.get("contact_refresh"),"refresh");
        for(Value wrong:new Value[]{new IntegerValue(BigInteger.TEN),new Text("01"),new Text("-1"),new Text("1"+"0".repeat(4300))}) {
            var broken=new RawJson(DriverJson.encode(root.with("contact_refresh",refresh.with("to_revision",wrong))));
            assertThrows(IllegalArgumentException.class,()->RootRouteContactAdvanceResult.decode(broken,STEP));
        }
        assertThrows(IllegalArgumentException.class,()->RootRouteContactAdvanceResult.encode(wire,STEP));
        assertThrows(IllegalArgumentException.class,()->RootRouteContactAdvanceResult.decode(wire,
                new OperationKey("advance-route-contact-horizon-v1-10-to-91-h-2-20-30")));
        assertThrows(IllegalArgumentException.class,()->RootRouteContactAdvanceResult.decode(wire,
                new OperationKey("advance-route-contact-window-v1-10-to-90-days-2-h-2-20-30")));
    }
}

