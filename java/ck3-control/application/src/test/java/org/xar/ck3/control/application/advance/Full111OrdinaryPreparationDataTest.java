package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public immutable DATA only. These fixtures cannot supply an actual Native Full, Root owner or submit permit. */
final class Full111OrdinaryPreparationDataTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final Instant DEADLINE=Instant.parse("2030-01-02T03:04:05.123456789Z");
    private static final String ARM="research-arm-tactical-daily-sentinel-v1-53179368-to-53179392-speed-3-mode-terminal-a-0";
    @TempDir Path temporary;

    @Test void currentExecutableAloneRetainsTheOriginalEmptyFields()throws Exception {
        var command=command(FULL,"pause-map");
        assertEquals("{}",new String(AdvancePrimitives.prepareRequest(command).additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8));
        assertEquals("{}",new String(FullSnapshotDateSentinelArm.additionalFields(command(FULL,ARM)).bytes(),java.nio.charset.StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->AdvancePrimitives.prepareRequest(command,ExactCk3Build.CK3_121003_STEAM_26785313));
        assertThrows(IllegalArgumentException.class,()->AdvancePrimitives.prepareRequest(command(ExactCk3Build.CK3_1210,"pause-map"),FULL));
    }

    @Test void explicitSourceDataBuildsCanonicalClockWithoutChangingTheOriginalCommand()throws Exception {
        for(String step:new String[]{"pause-map","resume-map","set-speed-1","set-speed-5"}) {
            var command=command(FULL,step);String body=ActionCodec.bodySha256(command);var before=command.before();
            var request=AdvancePrimitives.prepareRequest(command,FULL);
            assertEquals(FullSnapshotClockControl.request(FULL,step,"native:10",BigInteger.TEN,DEADLINE),request);
            var claim=StrictJson.parse(request.additionalFields().bytes()).path("full_snapshot_clock_control");
            assertEquals(8,claim.size());assertEquals(FULL.coreFullAdapterId(),claim.path("adapter_id").textValue());
            assertEquals(FULL.coreFullBackend(),claim.path("backend").textValue());
            assertTrue(claim.path("native_revision").isIntegralNumber());assertEquals(BigInteger.TEN,claim.path("native_revision").bigIntegerValue());
            assertEquals(DEADLINE.toEpochMilli(),claim.path("deadline_unix_ms").longValue());
            assertSame(before,command.before());assertEquals(DEADLINE,command.deadline());assertEquals(body,ActionCodec.bodySha256(command));
        }
    }

    @Test void explicitArmDataAndLegacyCanonicalRequestsRemainSeparate()throws Exception {
        var arm=command(FULL,ARM);
        assertEquals(FullSnapshotDateSentinelArm.request(FULL,ARM,"native:10",BigInteger.TEN,DEADLINE),
                AdvancePrimitives.prepareRequest(arm,FULL));
        var cancel=command(FULL,ClockStatusRead.CANCEL_PREFIX+"7");
        assertEquals("{}",new String(AdvancePrimitives.prepareRequest(cancel).additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->AdvancePrimitives.prepareRequest(cancel,FULL));
        for(var legacy:new ExactCk3Build[]{ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580}) {
            var old=command(legacy,"pause-map");
            assertEquals(AdvancePrimitives.prepareRequest(old),AdvancePrimitives.prepareRequest(old,legacy));
        }
    }

    @Test void prefixShapeGrammarDoesNotAcceptChangedClaimsOrGrantSourceQualification()throws Exception {
        var command=command(FULL,"resume-map");var canonical=AdvancePrimitives.prepareRequest(command,FULL);
        // This predicate is shape-only. Actual archive replay must independently verify the complete original guard/frame.
        assertTrue(AdvancePrimitives.matchesCanonicalPreparationData(command,canonical));
        var changed=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(canonical.additionalFields().bytes());
        ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("full_snapshot_clock_control")).put("deadline_unix_ms",DEADLINE.toEpochMilli()+1);
        var altered=new NativeRequest(canonical.step(),canonical.requiredCapability(),new RawJson(StrictJson.canonical(changed)));
        assertFalse(AdvancePrimitives.matchesCanonicalPreparationData(command,altered));
        assertFalse(AdvancePrimitives.matchesCanonicalPreparationData(command,
                new NativeRequest(canonical.step(),"game.command.pause-map",canonical.additionalFields())));
    }

    private ActionCommand command(ExactCk3Build build,String step)throws Exception {
        byte[] data=new byte[]{'{','}'};Path file=temporary.resolve(build.name()+".json");Files.write(file,data);
        var source=new G2Source("software-fixture-machine","2030-01-02T03:00:00Z",build.executableSha256(),
                new ExactRef(file.toString(),data.length,ActionCodec.sha256(data)));
        var identity=new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.TEN,BigInteger.valueOf(53179368));
        var frame=new JointBudgetSelector.ProposalFrame(identity,"native:10",BigInteger.ONE,"software-fixture-episode");
        var before=new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993"))),frame,1);
        var operation=new OperationKey(step);var arguments=new OpportunityJson.Obj(Map.of());
        return new ActionCommand("software111-"+(step.startsWith("research-")?"sentinel":step),before,source,"software-fixture-session",
                operation,arguments,AdvancePrimitives.expected(before,source,operation,arguments),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
    }
}
