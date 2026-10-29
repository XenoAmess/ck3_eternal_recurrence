package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;

final class GiftProcessIdentityTest {
    private static final int PID=23456;
    private static GameGeneration game(String timestamp) {
        Instant instant=Instant.parse(timestamp);
        BigInteger ticks=BigInteger.valueOf(instant.getEpochSecond()).add(new BigInteger("11644473600"))
                .multiply(BigInteger.valueOf(10000000)).add(BigInteger.valueOf(instant.getNano()/100));
        return new GameGeneration(PID,new PythonOnlyUInt64(ticks));
    }
    private static ProcessIdentity source(String timestamp) { return new ProcessIdentity(BigInteger.valueOf(PID),timestamp); }

    @Test void exactFiletimeKeepsAllTicksAndAcceptsEquivalentIsoSpelling() {
        var actual=game("2026-10-24T00:00:00.123456700Z");
        assertEquals("2026-10-24T00:00:00.123456700Z",GiftProcessIdentity.actual(actual).creationDate());
        assertEquals(GiftProcessIdentity.Relation.SAME,GiftProcessIdentity.compare(source("2026-10-24T00:00:00.1234567Z"),actual));
        assertEquals(GiftProcessIdentity.Relation.SAME,GiftProcessIdentity.compare(source("2026-10-24T00:00:00.123456700+00:00"),actual));
        assertEquals(GiftProcessIdentity.Relation.DIFFERENT,GiftProcessIdentity.compare(source("2026-10-24T00:00:00.1234568Z"),actual));
    }
    @Test void oldMicrosecondTruncationOrRoundingCannotProveReplacementAtTheSamePid() {
        var actual=game("2026-10-24T00:00:00.123456700Z");
        for(String original:new String[]{"20261024000000.123456+000","20261024080000.123456+480",
                "2026-10-24T00:00:00.123456+00:00","2026-10-24T00:00:00.123457+00:00",
                "2026-10-24T00:00:00Z"})
            assertEquals(GiftProcessIdentity.Relation.UNAVAILABLE,GiftProcessIdentity.compare(source(original),actual),original);
    }
    @Test void actualDifferentBirthAndPidRequireSupportedOriginalIdentity() {
        var actual=game("2026-10-24T00:00:00.123456700Z");
        assertEquals(GiftProcessIdentity.Relation.DIFFERENT,GiftProcessIdentity.compare(source("20261023000000.123456+000"),actual));
        var otherPid=new ProcessIdentity(BigInteger.valueOf(PID+1),"20261024000000.123456+000");
        assertEquals(GiftProcessIdentity.Relation.DIFFERENT,GiftProcessIdentity.compare(otherPid,actual));
        assertEquals(GiftProcessIdentity.Relation.UNAVAILABLE,GiftProcessIdentity.compare(new ProcessIdentity(BigInteger.valueOf(PID+1),"unknown"),actual));
        assertEquals(GiftProcessIdentity.Relation.UNAVAILABLE,GiftProcessIdentity.compare(source("2026-10-24T00:00:00.123456701Z"),actual));
    }
}
