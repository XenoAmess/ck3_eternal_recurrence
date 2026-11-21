package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA for Main selection and the independent after-Core predicate; no live date credit. */
final class NativeOwnerCurrentDateAdvanceSelectionTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static ObjectNode configuration(){
        return StrictJson.object().put("schema","xar.native-owner-snapshot-config/v17").put("mode","current_date_advance")
                .put("maximum_status_polls",64).put("status_poll_interval_ms",500);
    }
    private static CoreFrame.Partial core(int date,int speed,boolean paused,int player,boolean map,boolean has,int actor,boolean alive){
        return new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(date,speed,paused,player,map,has,actor,alive));
    }
    private static CoreFrame.Partial source(){return core(53144376,1,true,0,true,true,36423,true);}
    private static CoreFrame.Partial after(){return core(53144400,1,true,0,true,true,36423,true);}

    @Test void currentModeRequiresItsOwnSchemaAndBoundedReadonlyPolling(){
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DATE_ADVANCE,NativeOwnerSnapshotMain268.observationMode(configuration()));
        for(String field:new String[]{"maximum_status_polls","status_poll_interval_ms"}){
            var missing=configuration();missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
            for(String token:new String[]{"true","1.0","null","\"64\""}){
                var row=configuration();row.set(field,StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
            }
        }
        for(int polls:new int[]{0,129})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("maximum_status_polls",polls)));
        for(int millis:new int[]{99,5001})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("status_poll_interval_ms",millis)));
    }
    @Test void currentModeCannotBorrowConfiguredCoreTargetsOperationsOrOtherModes(){
        for(String field:new String[]{"expected_core","target_date_raw","operation_id","deadline_unix_ms","connection_generation","core_prefix_only",
                "control_step","window_name","expected_source_rite_id","navigation_action","rite_action","checkpoint_archive_path","previous_checkpoint_source","unknown"}){
            var row=configuration().put(field,"forged");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row),field);
        }
    }
    @Test void legacyFullDateAndClockModesKeepTheirOriginalVersions(){
        var old=configuration().put("schema","xar.native-owner-snapshot-config/v8").put("mode","date_sentinel_advance_one_day");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.DATE_ADVANCE,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("mode","date_sentinel_advance_one_day")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.deepCopy().put("mode","current_date_advance")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.FULL_CLOCK,NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v7").put("mode","full_snapshot_clock_control").put("control_step","set-speed-1")));
    }
    @Test void independentlyReceivedCurrentCoreCanProveOnlyAnExactPausedLivingDay(){
        assertSame(source().getClass(),assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDateSource(source())).getClass());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDateAfter(source(),after()));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDateAfter(
                core(Integer.MAX_VALUE-24,5,true,2,true,true,7,true),core(Integer.MAX_VALUE,5,true,2,true,true,7,true)));
    }
    @Test void dateUndershootOvershootSameDateAndOverflowAreRejected(){
        for(int raw:new int[]{53144376,53144399,53144401,53144424})
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDateAfter(source(),core(raw,1,true,0,true,true,36423,true)));
        for(int raw:new int[]{0,-1,Integer.MAX_VALUE-23,Integer.MAX_VALUE})
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDateSource(core(raw,1,true,0,true,true,36423,true)));
    }
    @Test void afterCoreMustKeepActualActorPlayerSpeedPauseAndLivingMap(){
        for(var wrong:new CoreFrame[]{core(53144400,2,true,0,true,true,36423,true),core(53144400,1,true,1,true,true,36423,true),
                core(53144400,1,true,0,true,true,36424,true),core(53144400,1,false,0,true,true,36423,true),
                core(53144400,1,true,0,false,true,36423,true),core(53144400,1,true,0,true,true,36423,false),
                core(53144400,1,true,0,true,false,-1,false),core(53144400,1,true,-1,true,true,36423,true)})
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDateAfter(source(),wrong));
    }
    @Test void legacyAndFullBuildOrUnavailableNeverStandInForCurrentNarrowCore(){
        for(var build:new ExactCk3Build[]{ExactCk3Build.CK3_12004,ExactCk3Build.CK3_1210,ExactCk3Build.CK3_121003_STEAM_26785313_FULL111}){
            var wrong=new CoreFrame.Partial(build,source().prefix());
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDateSource(wrong));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDateAfter(source(),new CoreFrame.Partial(build,after().prefix())));
        }
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDateSource(new CoreFrame.Unavailable(BUILD,true,"NoGame DATA")));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDateAfter(source(),new CoreFrame.Unavailable(BUILD,false,"unobserved DATA")));
    }
}
