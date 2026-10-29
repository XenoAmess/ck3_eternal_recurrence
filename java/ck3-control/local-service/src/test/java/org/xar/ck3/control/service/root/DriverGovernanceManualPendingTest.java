package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.crownauthority.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure original producer -> actual request encoder -> pending producer. Synthetic enclosing identity grants no Core/native permission. */
final class DriverGovernanceManualPendingTest {
    @Test void explicitNondefaultLawAndMissingCallerLimitsReachTheSamePendingAndSerdeConsumers()throws Exception {
        String path=System.getProperty("xar.governance.crown.golden.path");assertNotNull(path,"required retained actual Crown producer golden missing");
        var original=StrictJson.parse(Files.readAllBytes(Path.of(path))).get("cases").get(0).get("input").get("readback");
        var data=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(original));assertEquals("crown_authority_1",CrownAuthorityPolicy.choose(data).lawKey());
        var source=new G2Source("software-governance-only",Instant.EPOCH.toString(),data.sourceFrame().exactCk3Build(),new ExactRef("synthetic-source-only",1,"a".repeat(64)));
        var frame=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(data.sourceFrame().playerCharacterId(),data.sourceFrame().queriedNativeRevision(),data.sourceFrame().dateRaw()),data.sourceFrame().queriedSnapshotId(),data.sourceFrame().queriedRevision(),"software-episode"),1);
        var fields=StrictJson.object().put("law_key","crown_authority_2").put("caller_request_id","native-caller-id");fields.set("readback",original);fields.set("caller_budgets",StrictJson.object());
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,frame,source,"xar.java.governance-independent-effect/v1",List.of(new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("crown.effective_law_key"),"crown_authority_2")));
        var command=new ActionCommand("software-manual-crown",frame,source,"software-session",new OperationKey(GovernanceActionPreparation.CROWN),(OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(fields)),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.parse("2026-10-24T00:00:30Z"));
        var producer=new GovernanceActionPreparation(data.sourceFrame().exactCk3Build(),data.sourceFrame().exeSha256(),(same,value,id)->{throw new AssertionError("Crown cannot enter Council preflight");},(same,value)->{throw new AssertionError("Crown cannot enter LIFE preflight");});
        var prepared=producer.prepare(command,"root-physical-request");var wire=StrictJson.parse(prepared.additionalFields().bytes());assertEquals("native-caller-id",wire.get("submitted_request_id").textValue());assertFalse(wire.has("budget_gold_raw"));
        var pending=RootGovernanceDomains.makePending(command,prepared);var body=StrictJson.parse(pending.bytes());assertEquals("native-caller-id",body.get("action_id").textValue());assertEquals("crown_authority_2",body.get("law_key").textValue());
        assertEquals(0,body.get("budgets").size());assertEquals("explicit_public_caller_native_final_law_and_limits",body.get("choice").get("reason").textValue());assertArrayEquals(pending.bytes(),StrictJson.canonical(body));
    }
}
