package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.junit.jupiter.api.Assertions.*;

/** The actual transition predecessor guard consumes retained canonical data without reopening Java source files. */
final class OpeningRetainedBodyTest {
    private static final String MACHINE="opening-retained-fixture";
    private static final String AT="2026-10-29T16:30:00Z";
    private static final ExactRef HISTORICAL=new ExactRef("missing-old-opening.java",1,"a".repeat(64));
    private static final ExactRef CURRENT=new ExactRef("new-current-opening.java",1,"b".repeat(64));
    private static final ExactRef COMMAND=new ExactRef("retained-unknown-command",1,"c".repeat(64));
    private record Fixture(GovernanceOpeningDocument.Document document,byte[] bytes,
            DomainBodies.BodyRef member,WriterContracts.Head head) { }

    private static Fixture retained() {
        var source=new G2Source(MACHINE,AT,"1.20.0.4",HISTORICAL);
        var observed=new ObservationIdentity(MACHINE,new GameGeneration(123,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.TEN,BigInteger.valueOf(1000)),
                        "retained-frame",BigInteger.TEN,"retained-episode"),1);
        var document=new GovernanceOpeningDocument.Document(observed,source,"retained-session",OpeningStage.AWAIT_RECEIPT,
                Optional.empty(),Optional.empty(),List.of(COMMAND),Optional.of(COMMAND),Optional.empty());
        byte[] bytes=GovernanceOpeningDocument.encode(document);
        var payload=new ExactRef("retained-opening-body",bytes.length,ActionCodec.sha256(bytes));
        var member=new DomainBodies.BodyRef(DomainBodies.Slot.OPENING_GATE,GovernanceOpeningDocument.SCHEMA,payload,
                new WriterContracts.FileIdentity("1","2","133700000000000001",AT,bytes.length),List.of(HISTORICAL));
        var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE)
                .put("sequence",0).put("window_id",1).put("status","running").put("start_date_raw",1000)
                .put("target_days",1).put("target_date_raw",1024).put("last_settled_cycles",0).put("last_settled_date_raw",1000);
        var state=DomainBodies.reduceImport(ContinuityState.fromJson(row,MACHINE),member);
        return new Fixture(document,bytes,member,new WriterContracts.Head(state,List.of(),List.of(),List.of(),false));
    }
    @Test void historicalTraceKeepsTheExactPendingOriginalOnItsCanonicalHead() {
        var f=retained();String headBefore=f.head().digest();
        assertNotEquals(List.of(CURRENT),f.member().producerSources());
        assertDoesNotThrow(()->OpeningTransitions.requireRetainedPrevious(f.head(),f.member(),f.member().payload()));
        var decoded=GovernanceOpeningDocument.decode(f.bytes());
        assertEquals(f.document(),decoded);assertEquals(OpeningStage.AWAIT_RECEIPT,decoded.stage());
        assertEquals(Optional.of(COMMAND),decoded.preparedCommand());assertTrue(decoded.actionReceipt().isEmpty());
        assertTrue(decoded.checkpoint().isEmpty());assertArrayEquals(f.bytes(),GovernanceOpeningDocument.encode(decoded));
        assertEquals(headBefore,f.head().digest());assertEquals(0,f.head().state().sequence());
        assertEquals(List.of(HISTORICAL),f.member().producerSources());
    }
    @Test void differentPayloadAndMissingCanonicalMemberStillFail() {
        var f=retained();
        assertThrows(IllegalArgumentException.class,()->OpeningTransitions.requireRetainedPrevious(f.head(),f.member(),CURRENT));
        var replacement=new DomainBodies.BodyRef(f.member().slot(),f.member().contractSchema(),
                new ExactRef("other-body",f.bytes().length,"d".repeat(64)),f.member().identity(),f.member().producerSources());
        assertThrows(IllegalArgumentException.class,()->OpeningTransitions.requireRetainedPrevious(f.head(),replacement,replacement.payload()));
    }
    @Test void nativeIdentityHistoricalTraceSlotAndSchemaCannotReplaceTheCanonicalMember() {
        var f=retained();var member=f.member();
        var otherIdentity=new WriterContracts.FileIdentity("1","3","133700000000000001",AT,f.bytes().length);
        for(var changed:List.of(
                new DomainBodies.BodyRef(member.slot(),member.contractSchema(),member.payload(),otherIdentity,member.producerSources()),
                new DomainBodies.BodyRef(member.slot(),member.contractSchema(),member.payload(),member.identity(),List.of(CURRENT)),
                new DomainBodies.BodyRef(DomainBodies.Slot.FEAST,member.contractSchema(),member.payload(),member.identity(),member.producerSources()),
                new DomainBodies.BodyRef(member.slot(),"wrong-schema",member.payload(),member.identity(),member.producerSources())))
            assertThrows(IllegalArgumentException.class,()->OpeningTransitions.requireRetainedPrevious(f.head(),changed,changed.payload()));
    }
    @Test void retainedPayloadStillUsesTheActualDocumentSchemaAndUnknownLifecycleRules() {
        var f=retained();var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(f.bytes());
        row.put("schema","wrong-schema");
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.decode(StrictJson.canonical(row)));
        row.put("schema",GovernanceOpeningDocument.SCHEMA);row.put("stage",OpeningStage.COMPLETE.name());
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.decode(StrictJson.canonical(row)));
        assertEquals(OpeningStage.AWAIT_RECEIPT,GovernanceOpeningDocument.decode(f.bytes()).stage());
    }
}
