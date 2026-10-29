package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

/** The production archived Start verifier must read two distinct actual paused-pump packets. */
final class GameplayStartPumpTest {
    @Test void laterActualPausedPumpPassesWithExactIntegerDateAndSequence() {
        assertDoesNotThrow(()->GameplayStartEffects.verifyPump(packet(1,"5",true,53144328),packet(2,"6",true,53144328),BigInteger.valueOf(53144328)));
    }
    @Test void sameAckOrSamePumpCannotBecomeIndependentApplicationMainProgress() {
        byte[] first=packet(1,"5",true,53144328);
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.verifyPump(first,first,BigInteger.valueOf(53144328)));
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.verifyPump(first,packet(2,"5",true,53144328),BigInteger.valueOf(53144328)));
    }
    @Test void unpausedWrongDateBooleanPumpAndBrokenFramingAreRejected() {
        byte[] first=packet(1,"5",true,53144328);
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.verifyPump(first,packet(2,"6",false,53144328),BigInteger.valueOf(53144328)));
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.verifyPump(first,packet(2,"6",true,53144352),BigInteger.valueOf(53144328)));
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.verifyPump(first,packet(2,"true",true,53144328),BigInteger.valueOf(53144328)));
        byte[] malformed=packet(2,"6",true,53144328);malformed[0]=0;
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.verifyPump(first,malformed,BigInteger.valueOf(53144328)));
    }
    private static byte[] packet(int sequence,String epoch,boolean paused,int date) {
        String json="{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":"+sequence+",\"main_thread_query_mailbox_v1\":{"
                +"\"installed\":true,\"ready\":true,\"stop\":false,\"executor_submission_enabled\":true,\"failure\":0,\"paused\":"+paused
                +",\"date_raw\":"+date+",\"pump_epochs\":"+epoch+"}}";
        byte[] body=json.getBytes(StandardCharsets.UTF_8);
        return ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
    }
}
