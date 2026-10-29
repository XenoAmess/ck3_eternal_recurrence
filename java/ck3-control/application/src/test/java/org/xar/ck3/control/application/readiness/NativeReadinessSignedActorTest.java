package org.xar.ck3.control.application.readiness;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Boundary tests only. driver_snapshot actor21 owns actual pipe/Driver -> Complete -> assessment regression.
 * No artificial Complete, Root, process or Game qualification is constructed here.
 * Old Python upstream semantic rejection is deliberately corrected, not used as a success oracle;
 * its readiness predicate itself already distinguishes integer from boolean without a positive-only check.
 */
final class NativeReadinessSignedActorTest {
    @Test void signedPolicyAndSemanticDecoderPreserveTheExactNativeInt32AndSerde() {
        for(int actor:new int[]{Integer.MIN_VALUE,-2147483646,-2,0,1,Integer.MAX_VALUE}) {
            var expected=BigInteger.valueOf(actor);
            var policy=new NativeReadiness.Policy(false,false,Optional.of(expected),Duration.ZERO,false);
            assertEquals(expected,policy.expectedActor().orElseThrow());
            assertEquals(expected,NativeCharacterId.fromJson(NativeCharacterId.of(actor).toJson()).asBigInteger());
            var semantic=object("{\"actor\":"+actor+"}");
            assertEquals(expected,NativeReadiness.character(semantic,"actor"));
            var restored=DriverJson.object(DriverJson.encode(semantic),DriverJson.MAX_NATIVE_BYTES);
            assertEquals(expected,NativeReadiness.character(restored,"actor"));
        }
    }
    @Test void sentinelOverflowAndWrongJsonTypesNeverAliasPublicNativeIdentity() {
        for(BigInteger invalid:List.of(BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE),new BigInteger("4294967294"))) {
            assertThrows(IllegalArgumentException.class,()->new NativeReadiness.Policy(false,false,Optional.of(invalid),Duration.ZERO,false));
        }
        for(String token:List.of("-1","2147483648","-2147483649","4294967294","true","false","-2.0","null","\"-2\"","[]","{}")) {
            var value=object("{\"actor\":"+token+"}");
            assertThrows(IllegalArgumentException.class,()->NativeReadiness.character(value,"actor"),token);
        }
        assertThrows(IllegalArgumentException.class,()->NativeReadiness.character(object("{}"),"actor"));
    }
    @Test void transportRevisionAndStabilityDomainsRemainIndependentFromCharacterIdentity() {
        assertEquals(BigInteger.valueOf(-2),NativeReadiness.character(object("{\"actor\":-2}"),"actor"));
        for(String token:List.of("-2","0","true","1.0","null","\"1\"")) {
            assertThrows(IllegalArgumentException.class,()->NativeReadiness.positive(object("{\"revision\":"+token+"}"),"revision"));
        }
        assertEquals(BigInteger.ONE,NativeReadiness.positive(object("{\"revision\":1}"),"revision"));
        assertThrows(IllegalArgumentException.class,()->new NativeReadiness.Policy(false,false,Optional.of(BigInteger.valueOf(-2)),Duration.ofNanos(-1),false));
        assertThrows(IllegalArgumentException.class,()->new NativeReadiness.Policy(false,false,Optional.of(BigInteger.valueOf(-2)),Duration.ofDays(2),false));
    }
    private static OpportunityJson.Obj object(String value){return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
}

