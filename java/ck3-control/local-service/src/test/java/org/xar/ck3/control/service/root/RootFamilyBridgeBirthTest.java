package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.family.FamilyPorts.BridgeIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class RootFamilyBridgeBirthTest {
    private static GameGeneration game(String ticks) {return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger(ticks)));}
    private static Obj retained(String birth,long pid) {return new Obj(Map.of("source_bridge_pid",new IntegerValue(BigInteger.valueOf(pid)),"source_bridge_creation_date",new Text(birth)));}
    @Test void actualFiletimeEpochConversionKeepsAllSevenFractionDigits() {
        assertEquals("1970-01-01T00:00:00.0000000Z",RootFamilyBridge.creationToken(game("116444736000000000")));
        assertEquals("1970-01-01T00:00:00.0000001Z",RootFamilyBridge.creationToken(game("116444736000000001")));
        assertEquals("1969-12-31T23:59:59.9999999Z",RootFamilyBridge.creationToken(game("116444735999999999")));
    }
    @Test void originalCimAndIsoBirthProfilesMatchWithoutChangingTheRetainedSpelling() {
        var original=retained("19700101080000.000000+480",42);var before=original;
        var identity=new BridgeIdentity(42,RootFamilyBridge.creationToken(game("116444736000000000")));
        assertTrue(identity.matches(original,"source_"));assertSame(before,original);
        assertFalse(identity.matches(retained("19700101080001.000000+480",42),"source_"));
        assertFalse(identity.matches(retained("19700101080000.000000+480",43),"source_"));
    }
    @Test void ASubMicrosecondBirthCannotBeRoundedIntoAnOldCimIdentity() {
        var identity=new BridgeIdentity(42,RootFamilyBridge.creationToken(game("116444736000000001")));
        assertFalse(identity.matches(retained("19700101000000.000000+000",42),"source_"));
        assertTrue(identity.matches(retained("1970-01-01T00:00:00.0000001Z",42),"source_"));
    }
}
