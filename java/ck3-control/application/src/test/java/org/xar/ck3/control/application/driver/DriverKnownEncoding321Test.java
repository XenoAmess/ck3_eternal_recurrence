package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public immutable DATA only. Synthetic refs grant no file, Root, writer or Native authority. */
public final class DriverKnownEncoding321Test {
    private static final String HASH0="0".repeat(64);
    private static final long VERSION=7L;
    private static final long EPOCH=3L;
    private static final OpportunityJson.Obj EMPTY=new OpportunityJson.Obj(Map.of());
    private static GameGeneration game(long pid,long birth) {
        return new GameGeneration(pid,new PythonOnlyUInt64(BigInteger.valueOf(birth)));
    }
    private static ExactRef history(long bytes) {
        return new ExactRef("fixture-only/history321.json",bytes,HASH0);
    }
    private static DriverStateSnapshot.Complete driver(DriverStateSnapshot.Slot goal) {
        var nil=new DriverStateSnapshot.NullValue();
        return new DriverStateSnapshot.Complete(
                new DriverStateSnapshot.Session("pipe-fixture321",321L,BigInteger.valueOf(42),"episode-fixture321"),
                List.of(),nil,nil,nil,nil,nil,goal,nil);
    }
    private static DriverStateSnapshot.Value slot(String json) {
        return new DriverStateSnapshot.Value(json.getBytes(StandardCharsets.UTF_8));
    }
    private static DriverStateSnapshot.Value nestedSlot(int arrays) {
        return slot("[".repeat(arrays)+"0"+"]".repeat(arrays));
    }
    private static DriverSnapshotFacts.Stamp stamp(DriverStateSnapshot.Complete driver) {
        return new DriverSnapshotFacts.Stamp(VERSION,EPOCH,game(321L,1L),
                driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
    }
    private static NativeObservationPort.TransportSession transport(GameGeneration game,
            BigInteger connection,String sessionId) {
        return new NativeObservationPort.TransportSession("fixture321",game,connection,sessionId);
    }
    private static DriverObservationFacts observation(DriverStateSnapshot.Complete driver,
            long version,long epoch,NativeObservationPort.TransportSession transport,long observationVersion) {
        return new DriverObservationFacts(driver,version,epoch,transport,"snapshot-fixture321",BigInteger.ONE,
                HASH0,BigInteger.ONE,observationVersion,
                new G2Source("fixture321","2026-11-02T00:00:00Z","fixture-build321",history(1L)),EMPTY,history(1L));
    }
    private static DriverSnapshotFacts.Known known(DriverStateSnapshot.Complete driver,
            DriverSnapshotFacts.Stamp stamp,ExactRef history,DriverObservationFacts observation) {
        return new DriverSnapshotFacts.Known(driver,stamp,history,List.of(),EMPTY,Optional.empty(),Optional.of(observation));
    }
    @Test void observationEqualityAndMismatchGates() {
        var baseDriver = driver(slot("{}"));
        var baseStamp = stamp(baseDriver);
        var baseHistory = history(1L);
        var baseTransport = transport(game(321L, 1L), BigInteger.ONE, "session-a");
        var baseObservation = observation(baseDriver, VERSION, EPOCH, baseTransport, 1L);

        // Valid same-instance observation acceptance
        var sameInstance = new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(baseObservation));
        assertSame(baseObservation, sameInstance.observation().orElseThrow());
        assertSame(baseDriver, sameInstance.driver());

        // Separately constructed but byte-equal Driver acceptance
        var equalDriver = driver(slot("{}"));
        assertNotSame(baseDriver, equalDriver);
        assertArrayEquals(baseDriver.encode(), equalDriver.encode());
        var equalObservation = observation(equalDriver, VERSION, EPOCH, baseTransport, 1L);
        var equalAcceptance = new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(equalObservation));
        assertSame(equalObservation, equalAcceptance.observation().orElseThrow());

        // Different observation Driver mismatch (not byte-equal)
        var differentDriver = driver(slot("{\"x\":1}"));
        var differentObservation = observation(differentDriver, VERSION, EPOCH, baseTransport, 1L);
        assertThrows(ContractViolationException.class, () -> new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(differentObservation)));

        // Wrong stamp SHA
        var wrongShaStamp = new DriverSnapshotFacts.Stamp(VERSION, EPOCH, game(321L, 1L), baseDriver.session().episodeRunId(), "1".repeat(64));
        assertThrows(ContractViolationException.class, () -> new DriverSnapshotFacts.Known(baseDriver, wrongShaStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(baseObservation)));

        // Wrong stamp runId
        var wrongRunStamp = new DriverSnapshotFacts.Stamp(VERSION, EPOCH, game(321L, 1L), "wrong-run", DriverJson.sha256(baseDriver.encode()));
        assertThrows(ContractViolationException.class, () -> new DriverSnapshotFacts.Known(baseDriver, wrongRunStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(baseObservation)));

        // Wrong stamp PID
        var wrongPidStamp = new DriverSnapshotFacts.Stamp(VERSION, EPOCH, game(999L, 1L), baseDriver.session().episodeRunId(), DriverJson.sha256(baseDriver.encode()));
        assertThrows(ContractViolationException.class, () -> new DriverSnapshotFacts.Known(baseDriver, wrongPidStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(baseObservation)));

        // Observation driverVersion mismatch
        var versionMismatch = observation(baseDriver, VERSION + 1, EPOCH, baseTransport, 1L);
        assertThrows(ContractViolationException.class, () -> new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(versionMismatch)));

        // Observation epoch mismatch
        var epochMismatch = observation(baseDriver, VERSION, EPOCH + 1, baseTransport, 1L);
        assertThrows(ContractViolationException.class, () -> new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(epochMismatch)));

        // Observation transport.game mismatch
        var gameMismatch = observation(baseDriver, VERSION, EPOCH, transport(game(888L, 1L), BigInteger.ONE, "session-a"), 1L);
        assertThrows(ContractViolationException.class, () -> new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(gameMismatch)));

        // Original allowance: different valid connection/session identity within same Game
        var differentIdentity = observation(baseDriver, VERSION, EPOCH, transport(game(321L, 1L), BigInteger.TWO, "session-b"), 1L);
        var allowedIdentity = new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(differentIdentity));
        assertSame(differentIdentity, allowedIdentity.observation().orElseThrow());

        // Original allowance: another positive observationVersion
        var differentVersion = observation(baseDriver, VERSION, EPOCH, baseTransport, 2L);
        var allowedVersion = new DriverSnapshotFacts.Known(baseDriver, baseStamp, baseHistory, List.of(), EMPTY, Optional.empty(), Optional.of(differentVersion));
        assertSame(differentVersion, allowedVersion.observation().orElseThrow());
    }
    @Test void historyGuardAndCompleteEncodingCannotBeSkipped() {
        // 1. Construct a standalone deep Slot that is valid in isolation (depth 64) but makes the full envelope illegal (depth 65).
        //    FullJsonTree enforces maxNestingDepth(64). A slot with 64 nested arrays is <= 64.
        String deepJson = "[".repeat(64) + "0" + "]".repeat(64);
        DriverStateSnapshot.Value deepSlot = slot(deepJson);
        assertNotNull(deepSlot);
        assertTrue(deepSlot.json().length > 0);

        // 2. Construct a shallow Slot (depth 63) for positive control.
        //    Complete adds one level, resulting in depth 64, which is valid.
        String shallowJson = "[".repeat(63) + "0" + "]".repeat(63);
        DriverStateSnapshot.Value shallowSlot = slot(shallowJson);
        assertNotNull(shallowSlot);

        // 3. Build a Complete Driver with the shallow slot (valid depth) to verify positive control path.
        DriverStateSnapshot.Complete shallowDriver = driver(shallowSlot);
        assertNotNull(shallowDriver);
        // Verify shallow driver encodes successfully (depth <= 64)
        byte[] shallowBytes = shallowDriver.encode();
        assertTrue(shallowBytes.length > 0);

        // 4. Build a Complete Driver with the deep slot (invalid depth for full envelope).
        //    The Session and other slots are valid, but the 'campaignGoal' slot (last param in driver helper) is deep.
        //    Note: driver() helper puts the 'goal' slot into 'campaignGoal'.
        DriverStateSnapshot.Complete deepDriver = driver(deepSlot);
        assertNotNull(deepDriver);

        // 5. Verify that encoding the deep driver fails due to depth constraint.
        //    FullJsonTree.encode calls validate() which checks depth <= 64.
        //    The error message is "bounded complete JSON tree required".
        Exception encodeError = null;
        try {
            deepDriver.encode();
        } catch (Exception e) {
            encodeError = e;
        }
        assertNotNull(encodeError, "Deep driver encode must fail");
        assertTrue(encodeError instanceof ContractViolationException, "Encode error must be ContractViolationException");
        assertEquals("bounded complete JSON tree required", encodeError.getMessage());

        // 6. Test Original First-Error Order: Nonpositive history-ref must fail before encode.
        //    DriverSnapshotFacts.Known constructor validates history ref bytes > 0 BEFORE calling driver.encode() for stamp check.
        ExactRef invalidHistory = new ExactRef("path", 0, HASH0); // bytes=0 is invalid
        // Construct Stamp manually to avoid helper encoding issues if any, but Stamp helper uses driver.encode().
        // We need a valid-format Stamp DATA directly when testing a deliberately unencodable Complete.
        DriverSnapshotFacts.Stamp dummyStamp = new DriverSnapshotFacts.Stamp(VERSION, EPOCH, game(321L, 1L), "episode-fixture321", HASH0);

        Exception historyError = null;
        try {
            // Construct Known with deepDriver and invalid history.
            // Use actual same-instance observation for both Known calls with deepDriver.
            DriverObservationFacts obs = observation(deepDriver, VERSION, EPOCH, transport(game(321L, 1L), BigInteger.ONE, "session-fixture321"), 1L);
            new DriverSnapshotFacts.Known(deepDriver, dummyStamp, invalidHistory, List.of(), EMPTY, Optional.empty(), Optional.of(obs));
        } catch (Exception e) {
            historyError = e;
        }
        assertNotNull(historyError, "Invalid history ref must fail");
        assertTrue(historyError instanceof ContractViolationException, "History error must be ContractViolationException");
        assertEquals("full Driver facts/stamp mismatch", historyError.getMessage());

        // 7. Test Positive History-Ref with Deep Driver: Encode must fail.
        //    Now history ref is valid (bytes > 0). The constructor proceeds to driver.encode().
        ExactRef validHistory = new ExactRef("path", 1, HASH0);
        Exception encodeError2 = null;
        try {
            // Reuse dummyStamp. Note: The stamp check compares stamp.driverSha256() with DriverJson.sha256(driver.encode()).
            // Since driver.encode() throws, we expect the encode exception to propagate.
            // Use actual same-instance observation for both Known calls with deepDriver.
            DriverObservationFacts obs = observation(deepDriver, VERSION, EPOCH, transport(game(321L, 1L), BigInteger.ONE, "session-fixture321"), 1L);
            new DriverSnapshotFacts.Known(deepDriver, dummyStamp, validHistory, List.of(), EMPTY, Optional.empty(), Optional.of(obs));
        } catch (Exception e) {
            encodeError2 = e;
        }
        assertNotNull(encodeError2, "Deep driver with valid history must fail on encode");
        assertTrue(encodeError2 instanceof ContractViolationException, "Encode error must be ContractViolationException");
        assertEquals("bounded complete JSON tree required", encodeError2.getMessage());

        // 8. Include successful Known shallow positive.
        //    Construct Stamp for shallowDriver using helper (which encodes successfully).
        DriverSnapshotFacts.Stamp shallowStamp = stamp(shallowDriver);
        DriverObservationFacts shallowObs = observation(shallowDriver, VERSION, EPOCH, transport(game(321L, 1L), BigInteger.ONE, "session-fixture321"), 1L);
        DriverSnapshotFacts.Known shallowKnown = new DriverSnapshotFacts.Known(shallowDriver, shallowStamp, validHistory, List.of(), EMPTY, Optional.empty(), Optional.of(shallowObs));
        assertNotNull(shallowKnown);
      }
}
