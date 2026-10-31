package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual coordinator control flow over explicit software journal DATA; no Game or native authority is synthesized. */
public final class PreIntentPreparationRejectionTest {
    private static final Instant NOW=Instant.parse("2026-10-23T18:00:00Z");
    private static final ExactRef REF=new ExactRef("D:/software-preintent120/original",1,"a".repeat(64));
    private static ActionCommand command(String id) {
        var source=new G2Source("software-preintent120",NOW.toString(),"1.20.0.4",REF);
        var before=new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(100)),
                        "native:1",BigInteger.ONE,"software-episode"),1);
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,before,source,"paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
        return new ActionCommand(id,before,source,"software-session",new OperationKey("pause-map"),new OpportunityJson.Obj(Map.of()),expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
    }
    private static GuardEvidence guard(ActionCommand command) {
        return guard(command,NOW);
    }
    private static GuardEvidence guard(ActionCommand command,Instant at) {
        return new GuardEvidence(command.before(),command.source(),command.sessionId(),BigInteger.ONE,command.operation(),REF,REF,
                "software-authority",at,command.deadline());
    }
    private static final class Journal implements ActionJournal,ActionJournal.LockedJournal {
        final Map<String,ActionReceipt> records=new LinkedHashMap<>();
        int sequence;
        int readOnlyChanges;
        ExactRef actionHead;
        @Override public <T>T locked(Function<ActionJournal.LockedJournal,T> work){return work.apply(this);}
        @Override public Optional<ActionReceipt> find(String id){return Optional.ofNullable(records.get(id));}
        @Override public List<ActionReceipt> unresolved(){return records.values().stream().filter(value->!value.settled()).toList();}
        @Override public WriterContracts.Head head(){
            var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id","software-preintent120")
                    .put("sequence",sequence+readOnlyChanges).put("window_id",1).put("status","running")
                    .put("start_date_raw",100).put("target_days",1).put("target_date_raw",124)
                    .put("last_settled_cycles",0).put("last_settled_date_raw",100);
            if(actionHead!=null)row.set(WriterContracts.ACTION_LIFECYCLE_FIELD,actionHead.toJson());
            return new WriterContracts.Head(ContinuityState.fromJson(row,"software-preintent120"),List.of(),List.of(),List.of(),false);
        }
        @Override public ContinuityStorePort.Session writerSession(){
            return (ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},
                    (proxy,method,args)->{if(method.getName().equals("head"))return head();throw new IOException("no software file/native IO: "+method.getName());});
        }
        @Override public ActionJournal.Snapshot snapshot(){
            return new ActionJournal.Snapshot(sequence+readOnlyChanges,head().digest(),new ArrayList<>(records.values()),new ActionJournal.MissingHistoryBasis());
        }
        @Override public ActionReceipt append(ActionCommand command,String digest,ActionState state){
            ActionTransitions.validate(find(command.actionId()),command,digest,state);
            var receipt=new ActionReceipt(1,++sequence,command,digest,state);records.put(command.actionId(),receipt);
            actionHead=new ExactRef("D:/software-preintent120/record-"+sequence,1,ActionCodec.sha256(new byte[]{(byte)sequence}));return receipt;
        }
    }
    private static ActionCoordinator coordinator(Journal journal,ActionPorts.PreparationPort prepare,
            ActionPorts.GuardPort guards,NativeActionPort nativePort){
        return new ActionCoordinator("software-authority",journal,guards,prepare,nativePort,
                (command,attempt,dispatch)->new ActionPorts.Pending("software observer retains original",List.of(REF)),Clock.fixed(NOW,ZoneOffset.UTC));
    }
    private static NativeActionPort noNative(){return (permit,request,deadline)->{throw new AssertionError("pre-intent rejection reached native submit");};}
    /** Reuses the real coordinator to issue the package-only control signal for Controller integration vectors. */
    public static PreIntentContractRejection rejectBeforeIntent(ActionCommand selected){
        var journal=new Journal();
        var at=selected.deadline().minusSeconds(1);
        try {
            new ActionCoordinator("software-authority",journal,(head,command)->guard(command,at),
                    command->{throw new ContractViolationException("held planning semantic differs from lease frame");},noNative(),
                    (command,attempt,dispatch)->new ActionPorts.Pending("software observer",List.of(REF)),Clock.fixed(at,ZoneOffset.UTC)).execute(selected);
        }catch(PreIntentContractRejection rejected){return rejected;}
        throw new AssertionError("expected typed pre-intent rejection");
    }
    public static PreIntentContractRejection rejectAnotherCommand(ActionCommand selected){
        var changed=new ActionCommand(selected.actionId(),selected.origin(),selected.source(),selected.sessionId(),selected.operation(),
                selected.arguments(),selected.expectation(),selected.claims(),selected.deadline().plusSeconds(1));
        return rejectBeforeIntent(changed);
    }
    @Test public void contractFailureBeforeIntentRetainsCauseWithoutAReceipt(){
        var selected=command("pre-intent-contract");var rejected=rejectBeforeIntent(selected);
        assertEquals(selected,rejected.command());assertInstanceOf(ContractViolationException.class,rejected.getCause());
        assertTrue(rejected.getMessage().contains("held planning semantic differs from lease frame"));
    }
    @Test public void readOnlyLedgerProgressDoesNotBecomeActionProgress(){
        var journal=new Journal();var selected=command("read-progress");
        var rejected=assertThrows(PreIntentContractRejection.class,()->coordinator(journal,command->{journal.readOnlyChanges++;throw new ContractViolationException("read-data rejected");},
                (head,command)->guard(command),noNative()).execute(selected));
        assertEquals(selected,rejected.command());assertEquals(1,journal.readOnlyChanges);assertTrue(journal.records.isEmpty());
    }
    @Test public void anotherActionProgressCannotBecomeASourceRejection(){
        var journal=new Journal();var selected=command("selected");var other=command("owned-child");
        var failure=assertThrows(ContractViolationException.class,()->coordinator(journal,command->{journal.append(other,ActionCodec.bodySha256(other),new ActionState.IntentDurable());throw new ContractViolationException("failed after owned action progress");},
                (head,command)->guard(command),noNative()).execute(selected));
        assertEquals("failed after owned action progress",failure.getMessage());assertFalse(journal.find(selected.actionId()).isPresent());assertTrue(journal.find(other.actionId()).isPresent());
    }
    @Test public void arbitraryPreparationFailureRemainsUntyped(){
        var journal=new Journal();var original=new IllegalStateException("unclassified preparation failure");
        assertSame(original,assertThrows(IllegalStateException.class,()->coordinator(journal,command->{throw original;},
                (head,command)->guard(command),noNative()).execute(command("generic-runtime"))));
        assertTrue(journal.records.isEmpty());
    }
    @Test public void secondGuardContractFailureKeepsItsDurableIntent(){
        var journal=new Journal();int[] guards={0};var selected=command("second-guard");
        assertThrows(ContractViolationException.class,()->coordinator(journal,command->new NativeRequest("pause-map",Optional.empty(),new RawJson(new byte[]{'{','}'})),
                (head,command)->{if(++guards[0]==2)throw new ContractViolationException("actual second guard rejected");return guard(command);},noNative()).execute(selected));
        assertInstanceOf(ActionState.IntentDurable.class,journal.find(selected.actionId()).orElseThrow().state());
    }
    @Test public void nativeContractFailureRemainsUnknownAndNeverReplays(){
        var journal=new Journal();int[] writes={0};var selected=command("native-failure");
        var coordinator=coordinator(journal,command->new NativeRequest("pause-map",Optional.empty(),new RawJson(new byte[]{'{','}'})),
                (head,command)->guard(command),(permit,request,deadline)->{permit.consumeOnce();writes[0]++;throw new ContractViolationException("native completion failed");});
        var result=coordinator.execute(selected);assertInstanceOf(ActionState.Unknown.class,result.state());assertEquals(1,writes[0]);
        assertEquals(result,coordinator.execute(selected));assertEquals(1,writes[0]);
    }
}
