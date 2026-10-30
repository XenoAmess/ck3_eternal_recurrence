package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;

/** Original Native allocator->reader->public serializer bare-frame WriteFrame packet.
 * This first fixture is not a NativeWire command_result envelope or ordinary Collector read. */
final class FactionNativePublicPacketTest {
    @Test void actualNativeAllocatorFirstGenerationZeroReachesPublicNormalizer()throws Exception {
        byte[] original;try(var input=getClass().getResourceAsStream("/finance/faction-generation-native90/public-first-zero/public-alerts.json.packet.bin")){assertNotNull(input,"unique actual Native packet");original=input.readAllBytes();}
        assertEquals(original.length-4,ByteBuffer.wrap(original,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());byte[] payload=Arrays.copyOfRange(original,4,original.length);var frame=StrictJson.parse(payload);
        var expected=new FactionAlertModel.ExpectedFrame(frame.get("date_raw").intValue(),frame.get("snapshot_revision").bigIntegerValue(),Optional.of(FactionAlertModel.Build.CK3_12004));
        var available=assertInstanceOf(FactionAlertModel.Available.class,FactionAlertsCodec.normalize(payload,expected).frame());
        assertEquals(1,available.targetingFactionCount());assertEquals(0,available.targetingFactions().getFirst().factionId());assertEquals(BigInteger.ONE,available.snapshotRevision());
        assertEquals(0,assertInstanceOf(FactionAlertModel.AvailablePlanner.class,available.planner()).dangerousFactionIds().getFirst());
    }
}
