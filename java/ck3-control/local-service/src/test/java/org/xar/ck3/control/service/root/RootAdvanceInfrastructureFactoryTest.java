package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual pre-adoption factory/catalog producers; source inputs are explicit synthetic configuration, never Game authority. */
final class RootAdvanceInfrastructureFactoryTest {
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef original(RawJson body){return new ExactRef("fixture/advance-timings.json",body.bytes().length,ActionCodec.sha256(body.bytes()));}
    private static RawJson valid(){return RootAdvanceInfrastructureFactory.Timings.encode(16,Duration.ofSeconds(1),Duration.ofSeconds(2));}
    @Test void actualTypedTimingProducerRoundTripsItsOwnRetainedBytesAtBothBounds() {
        for(int frames:List.of(1,65536)) {
            Duration command=frames==1?Duration.ofMillis(1):Duration.ofMinutes(5);
            Duration advance=frames==1?Duration.ofMillis(1):Duration.ofHours(1);
            RawJson body=RootAdvanceInfrastructureFactory.Timings.encode(frames,command,advance);
            ExactRef ref=original(body);
            var decoded=RootAdvanceInfrastructureFactory.Timings.decode(ref,body);
            assertEquals(new RootAdvanceInfrastructureFactory.Timings(ref,frames,command,advance),decoded);
            assertArrayEquals(body.bytes(),RootAdvanceInfrastructureFactory.Timings.encode(decoded.maximumFrames(),decoded.commandTimeout(),decoded.advanceTimeout()).bytes());
        }
    }
    @Test void timingProducerAndDirectConstructorRejectPrecisionLossAndInvalidLimits() {
        Duration millisecond=Duration.ofMillis(1);
        var ref=original(valid());
        for(Duration invalid:List.of(Duration.ZERO,Duration.ofNanos(-1),Duration.ofNanos(1),Duration.ofNanos(1000001),
                Duration.ofSeconds(1).plusNanos(1),Duration.ofMinutes(5).plusMillis(1))) {
            assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.encode(1,invalid,millisecond));
            assertThrows(IllegalArgumentException.class,()->new RootAdvanceInfrastructureFactory.Timings(ref,1,invalid,millisecond));
        }
        for(Duration invalid:List.of(Duration.ZERO,Duration.ofNanos(-1),Duration.ofNanos(999999),
                Duration.ofSeconds(1).plusNanos(999999),Duration.ofHours(1).plusMillis(1))) {
            assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.encode(1,millisecond,invalid));
            assertThrows(IllegalArgumentException.class,()->new RootAdvanceInfrastructureFactory.Timings(ref,1,millisecond,invalid));
        }
        for(int invalid:List.of(0,-1,65537,Integer.MAX_VALUE)) {
            assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.encode(invalid,millisecond,millisecond));
            assertThrows(IllegalArgumentException.class,()->new RootAdvanceInfrastructureFactory.Timings(ref,invalid,millisecond,millisecond));
        }
    }
    @Test void actualTimingJsonRetainsItsExactOriginalAndRejectsWrongTypesMissingAndAliases() {
        var body=valid();var ref=original(body);
        var timings=RootAdvanceInfrastructureFactory.Timings.decode(ref,body);
        assertEquals(ref,timings.original());assertEquals(16,timings.maximumFrames());
        assertEquals(Duration.ofSeconds(1),timings.commandTimeout());assertEquals(Duration.ofSeconds(2),timings.advanceTimeout());
        for(String replacement:List.of("true","16.0","null","0","65537")) {
            RawJson wrong=raw(new String(body.bytes(),StandardCharsets.UTF_8).replace("\"maximum_frames\":16","\"maximum_frames\":"+replacement));
            assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.decode(original(wrong),wrong));
        }
        for(String field:List.of("command_timeout_millis","advance_timeout_millis")) {
            String token=field.equals("command_timeout_millis")?"1000":"2000";
            for(String replacement:List.of("true","1.0","null","0","3600001")) {
                RawJson wrong=raw(new String(body.bytes(),StandardCharsets.UTF_8).replace("\""+field+"\":"+token,"\""+field+"\":"+replacement));
                assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.decode(original(wrong),wrong));
            }
        }
        RawJson missing=raw(new String(body.bytes(),StandardCharsets.UTF_8).replace(",\"maximum_frames\":16",""));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.decode(original(missing),missing));
        RawJson alias=raw(new String(body.bytes(),StandardCharsets.UTF_8).replace("\"maximum_frames\"","\"frame_limit\""));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.decode(original(alias),alias));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.decode(new ExactRef(ref.path(),ref.bytes()+1,ref.sha256()),body));
        RawJson changed=RootAdvanceInfrastructureFactory.Timings.encode(17,Duration.ofSeconds(1),Duration.ofSeconds(2));
        assertEquals(body.bytes().length,changed.bytes().length);
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.decode(ref,changed));
    }
    @Test void preparedStatusObjectIsTheExactEarlyInstalledCatalogObjectWithoutAdoptingAStubDriver() {
        RawJson body=valid();ExactRef ref=original(body);
        var sources=new RootAdvanceInfrastructureFactory.Sources(ref,ref,ref,ref,ref,ref);
        var prepared=new RootAdvanceInfrastructureFactory.Prepared(sources,RootAdvanceInfrastructureFactory.Timings.decode(ref,body));
        var actual=prepared.statusContract();
        var unknown=prepared.unknownStatusContract();var terminal=prepared.terminalStatusContract();var physical=prepared.physicalStatusContract();
        var catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(actual,ref),
                new RootReadContractCatalog.InstalledRead(unknown,ref),new RootReadContractCatalog.InstalledRead(terminal,ref),
                new RootReadContractCatalog.InstalledRead(physical,ref)),List.of());
        RootUnknownSentinelReadProfile.requireProfile(unknown);
        RootUnknownSentinelReadProfile.requireTerminalProfile(terminal);
        RootUnknownSentinelReadProfile.requirePhysicalProfile(physical);
        for(var profile:List.of(unknown,terminal,physical)) {
            assertTrue(catalog.containsIdentity(profile));assertNotSame(actual,profile);
            assertEquals(actual.sourceRef(),profile.sourceRef());assertEquals(actual.operation(),profile.operation());
            assertTrue(profile.hasPureReplay());assertNotEquals(actual.contractId(),profile.contractId());
        }
        assertSame(unknown,prepared.unknownStatusContract());assertSame(terminal,prepared.terminalStatusContract());
        assertSame(physical,prepared.physicalStatusContract());
        assertSame(actual,prepared.statusContract());assertTrue(catalog.containsIdentity(actual));
        assertFalse(catalog.containsIdentity(ClockStatusRead.registeredContract(ref)));
        assertEquals(ClockStatusRead.CONTRACT_ID,actual.contractId());assertEquals(ClockStatusRead.STEP,actual.operation().value());
        assertEquals(ref,actual.sourceRef());assertTrue(actual.hasPureReplay());
        assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,actual.guardMode());
    }
    @Test void dynamicClockFamiliesRequireTheirActualCanonicalTypedOperation() {
        var arm=new OperationKey(ClockStatusRead.ARM_PREFIX+"100-to-124-speed-2-mode-terminal-a-2-11-22");
        assertEquals(arm,new RootAdvanceInfrastructureFactory.Arm(arm).operation());
        var cancel=new OperationKey(ClockStatusRead.CANCEL_PREFIX+"18446744073709551615");
        assertEquals(cancel,new RootAdvanceInfrastructureFactory.Cancel(cancel).operation());
        for(String step:List.of("pause-map",ClockStatusRead.ARM_PREFIX+"100-to-124-speed-6-mode-terminal-a-0",ClockStatusRead.ARM_PREFIX+"100-to-124-speed-2-mode-terminal-a-2-11-11"))
            assertThrows(IllegalArgumentException.class,()->new RootAdvanceInfrastructureFactory.Arm(new OperationKey(step)));
        for(String step:List.of("pause-map",ClockStatusRead.CANCEL_PREFIX+"0",ClockStatusRead.CANCEL_PREFIX+"01",ClockStatusRead.CANCEL_PREFIX+"18446744073709551616"))
            assertThrows(IllegalArgumentException.class,()->new RootAdvanceInfrastructureFactory.Cancel(new OperationKey(step)));
    }
}
