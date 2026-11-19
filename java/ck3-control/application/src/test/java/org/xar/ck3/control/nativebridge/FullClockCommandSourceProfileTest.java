package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public command DATA only, without a Root, Driver, canonical intent or Native permit. */
final class FullClockCommandSourceProfileTest {
    @Test void ordinaryAdvanceUsesTheSelectedExactClaimAndUnknownSourcesStayOpaque() {
        for(var build:List.of(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580)) {
            var command=command("pause-map",build.executableSha256());byte[] before=ActionCodec.encodeCommand(command);
            var request=AdvancePrimitives.prepareRequest(command);
            var claim=StrictJson.parse(request.additionalFields().bytes()).path("full_snapshot_clock_control");
            assertTrue(build.executableSha256().equalsIgnoreCase(claim.path("executable_sha256").textValue()));
            assertEquals(build.coreFullAdapterId(),claim.path("adapter_id").textValue());
            assertArrayEquals(FullSnapshotClockControl.additionalFields(command).bytes(),request.additionalFields().bytes());
            assertArrayEquals(before,ActionCodec.encodeCommand(command));
        }
        assertTrue(StrictJson.parse(FullSnapshotClockControl.additionalFields(command("pause-map","unreviewed")).bytes()).isEmpty());
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.additionalFields(command("save-checkpoint",ExactCk3Build.CK3_1210_STEAM_26757580.executableSha256())));
        var old=FullSnapshotClockControl.request("pause-map","native:36",BigInteger.valueOf(36),Instant.parse("2027-01-01T00:00:00Z"));
        assertEquals(ExactCk3Build.CK3_1210.coreFullAdapterId(),StrictJson.parse(old.additionalFields().bytes()).path("full_snapshot_clock_control").path("adapter_id").textValue());
    }
    private static ActionCommand command(String operation,String exactBuild) {
        String machine="clock-profile-data",session="clock-profile-data-session";
        var game=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE));
        var before=new ProposalLifecycle.ObservationIdentity(machine,game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(7),BigInteger.valueOf(36),BigInteger.valueOf(123456)),
                "native:36",BigInteger.ONE,session),1);
        var source=new G2Source(machine,"2026-11-18T00:00:00Z",exactBuild,new ExactRef("data-only/source",1,"0".repeat(64)));
        var expectation=new ProposalLifecycle.ExpectedPostcondition(1,before,source,"data-only/clock",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"),true)));
        return new ActionCommand("clock-profile-data-command",before,source,session,new OperationKey(operation),
                new OpportunityJson.Obj(Map.of()),expectation,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),
                Instant.parse("2027-01-01T00:00:00Z"));
    }
}
