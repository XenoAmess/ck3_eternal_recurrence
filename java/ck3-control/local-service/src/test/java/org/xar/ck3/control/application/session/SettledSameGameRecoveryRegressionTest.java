package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.lang.reflect.InvocationTargetException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/**
 * A minimized, relocated software fixture derived from canonical1..35 feeds the production reader/reducer/Controller.
 * Original machine paths and unrelated domains are removed. Future writes remain in memory. Fresh SEM uses an explicit verifier test double;
 * no Native port, Game action, physical Pin admission or real game-day claim exists.
 */
final class SettledSameGameRecoveryRegressionTest {
    @org.junit.jupiter.api.io.TempDir Path temporary;
    private Fixture fixture() throws IOException {return new Fixture(PortableSettledFixture.materialize(temporary));}
    private static final String MACHINE="settled-recovery-fixture";
    private static final String BATCH="settled-fixture-ordinary-0";

    @Test void actual35ReaderRetainsTheAppliedOpeningWithoutCaptureOrCredit() throws Exception {
        var f=fixture();var data=f.read();
        assertEquals(35,data.canonicalSequence());assertRetained(data);
        assertEquals(0,f.commits);assertEquals(1,data.settledActions().size());
        assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,data.settledActions().getFirst().outcome());
        assertTrue(new String(DriverJson.encode(data.settledActions().getFirst().command().arguments()),java.nio.charset.StandardCharsets.UTF_8).contains("martial_authority_focus"));
        assertTrue(data.history().size()>=35);f.assertNoCredit();
    }

    @Test void actual35RepairThenReadyReentryRestoresDirtyControllerWithoutAnotherCommitOrCycle() throws Exception {
        var f=fixture();var first=f.read();var cycle=f.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).deepCopy();
        var fresh=f.semantic(first,0,0,1);f.allow(fresh);
        f.locked(same->{f.journal.recoverSettledSameGame(same,first,fresh);return null;});
        assertEquals(1,f.commits);assertEquals(ContinuityState.Status.RUNNING,f.current.status());
        assertTrue(ContinuityJson.same(cycle,f.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD)));
        var firstController=f.controller(first.source().sourceRef());
        f.locked(same->{firstController.restoreSettledSameGame(same,first);return null;});
        assertController(firstController,first);f.assertNoCredit();

        // A new Journal represents a new business process after catalog/session installation failed.
        f.newJournal();var ready=f.read();assertRetained(ready);
        var newer=f.semantic(ready,1,24,1);f.allow(newer);
        f.locked(same->{f.journal.recoverSettledSameGame(same,ready,newer);return null;});
        var retried=f.controller(ready.source().sourceRef());
        f.locked(same->{retried.restoreSettledSameGame(same,ready);return null;});
        assertController(retried,ready);
        assertEquals(1,f.commits,"READY reentry must only adopt the retained recovery");
        assertEquals(1,f.current.toJson().path(WriterContracts.ORDINARY_CYCLE_FIELD).path("completed_cycles").longValue());
        assertTrue(ContinuityJson.same(cycle,f.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD)));
        f.assertNoCredit();
    }

    @Test void recoveryAcceptsProjectedNewHelloAndMonotonicNativeDateWithoutSavedCredit() throws Exception {
        var f=fixture();var data=f.read();
        var fresh=f.semantic(data,1,24,1);f.allow(fresh);
        f.locked(same->{f.journal.recoverSettledSameGame(same,data,fresh);return null;});
        assertEquals(data.latestCycleSemantic().frame().frame().identity().dateRaw().longValueExact()+24,
                f.current.toJson().path("latest_binding").path("date_raw").longValue());
        assertEquals(data.latestObservedFrame().frame().revision().add(BigInteger.ONE),fresh.frame().frame().revision(),"new HELLO raw revision one projects above retained public baseline");
        assertEquals(1,f.current.toJson().path(WriterContracts.ORDINARY_CYCLE_FIELD).path("completed_cycles").longValue());
        var proof=f.locked(same->f.journal.cycleProof(same,f.owner,fresh)).orElseThrow();
        assertEquals(1,proof.completedCycles(),"next ordinary entry must accept the new observed binding");
        f.assertNoCredit();
    }

    @Test void recoveryRejectsNativeOrDateRegressionWithoutPublishing() throws Exception {
        for(int kind=0;kind<2;kind++) {
            var f=fixture();var data=f.read();var fresh=f.semantic(data,kind==0?-1:0,kind==1?-24:0,1);f.allow(fresh);
            assertThrows(IllegalArgumentException.class,()->f.locked(same->{f.journal.recoverSettledSameGame(same,data,fresh);return null;}));
            assertEquals(0,f.commits);assertEquals(ContinuityState.Status.REPAIR_REQUIRED,f.current.status());f.assertNoCredit();
        }
    }

    @Test void recoveryRejectsProjectedPublicRegressionWithoutPublishing() throws Exception {
        var f=fixture();var data=f.read();var fresh=f.semantic(data,0,0,-1);f.allow(fresh);
        assertThrows(IllegalArgumentException.class,()->f.locked(same->{f.journal.recoverSettledSameGame(same,data,fresh);return null;}));
        assertEquals(0,f.commits);f.assertNoCredit();
    }

    @Test void actualRead33AfterFrameEntersOrdinaryProofWhileCompletedCycleAndBindingRemainOlder() throws Exception {
        var f=fixture();var data=f.read();var observed=f.semantic(data,0,0,1);f.allow(observed);
        f.current=f.edges.get(33L).after();
        long boundNative=f.current.toJson().path("latest_binding").path("native_revision").longValue();
        assertTrue(boundNative<observed.frame().frame().identity().nativeRevision().longValueExact());
        assertEquals(BigInteger.valueOf(6),observed.frame().frame().identity().nativeRevision());
        var proof=f.locked(same->f.journal.cycleProof(same,f.owner,observed)).orElseThrow();
        assertEquals(1,proof.completedCycles());assertEquals(0,f.commits);
        assertEquals(boundNative,f.current.toJson().path("latest_binding").path("native_revision").longValue(),"READ bridge must not rewrite canonical binding");
        for(int kind=0;kind<2;kind++) {
            var unrecorded=f.semantic(data,kind==0?1:0,kind==1?24:0,1);f.allow(unrecorded);
            assertThrows(IllegalArgumentException.class,()->f.locked(same->f.journal.cycleProof(same,f.owner,unrecorded)),"an unrecorded native/date cannot borrow the READ frontier");
        }
        f.assertNoCredit();
    }

    @Test void malformedLatestBindingRejectsAtTheJsonBoundaryWithoutRuntimeCastFailure() throws Exception {
        for(int kind=0;kind<2;kind++) {
            var f=fixture();var data=f.read();var fresh=f.semantic(data,0,0,1);f.allow(fresh);
            f.locked(same->{f.journal.recoverSettledSameGame(same,data,fresh);return null;});
            var row=f.current.toJson();
            if(kind==0)row.set("latest_binding",StrictJson.object().putArray("unexpected"));
            else ((ObjectNode)row.get("latest_binding")).put("native_revision",true);
            assertThrows(IllegalArgumentException.class,()->{
                f.current=ContinuityState.fromJson(row,MACHINE);
                f.locked(same->f.journal.cycleProof(same,f.owner,fresh));
            });
            assertEquals(1,f.commits);
        }
    }

    @Test void readyFreshObservationPrivatelyBridgesNewHelloWithoutReadOrCanonicalMutation() throws Exception {
        var f=fixture();var first=f.read();var repair=f.semantic(first,0,0,1);f.allow(repair);
        f.locked(same->{f.journal.recoverSettledSameGame(same,first,repair);return null;});
        f.newJournal();var ready=f.read();var fresh=f.semantic(ready,1,24,1);f.allow(fresh);
        byte[] before=f.current.canonicalBytes();
        assertThrows(IllegalArgumentException.class,()->f.locked(same->f.journal.cycleProof(same,f.owner,fresh)),
                "a semantic passed to cycleProof cannot create the private recovery bridge");
        assertTrue(f.locked(same->f.journal.recoverSettledSameGame(same,ready,fresh)).isEmpty());
        assertArrayEquals(before,f.current.canonicalBytes());assertEquals(1,f.commits);
        var proof=f.locked(same->f.journal.cycleProof(same,f.owner,fresh)).orElseThrow();
        assertEquals(1,proof.completedCycles());assertArrayEquals(before,f.current.canonicalBytes());
        for(int kind=0;kind<2;kind++) {
            var unadopted=f.semantic(ready,kind==0?2:1,kind==1?48:24,2);f.allow(unadopted);
            assertThrows(IllegalArgumentException.class,()->f.locked(same->f.journal.cycleProof(same,f.owner,unadopted)),
                    "arbitrary newer Native/date cannot borrow the privately adopted exact frame");
        }
        f.assertNoCredit();
    }

    @Test void nextValidatedCanonicalAppliedGuardCanRetainAboveThePrivateFreshFrontier() throws Exception {
        var f=fixture();var first=f.read();var repair=f.semantic(first,0,0,1);f.allow(repair);
        f.locked(same->{f.journal.recoverSettledSameGame(same,first,repair);return null;});
        f.newJournal();var ready=f.read();var fresh=f.semantic(ready,1,24,1);f.allow(fresh);
        f.locked(same->f.journal.recoverSettledSameGame(same,ready,fresh));
        var preparedFrame=f.semantic(ready,2,24,2).frame();
        var next=f.softwareApplied(ready,preparedFrame,"software-next-canonical");
        var nextRef=f.installSoftwareCanonical(next);
        f.acceptedOperations=Set.of("SETTLED_SAME_GAME_RECOVERY","RETAIN");
        f.journal.retainCycle(f.owner,next);
        assertEquals(nextRef,ExactRef.fromJson(f.current.toJson().path(WriterContracts.ORDINARY_CYCLE_FIELD).get("pending_receipt")));
        assertEquals(1,f.current.toJson().path(WriterContracts.ORDINARY_CYCLE_FIELD).path("completed_cycles").longValue());
        assertEquals(2,f.commits,"only recovery and the new canonical RETAIN may commit");f.assertNoCredit();
    }

    @Test void uncataloguedAppliedGuardCannotBorrowThePrivateFreshActionBridge() throws Exception {
        var f=fixture();var first=f.read();var repair=f.semantic(first,0,0,1);f.allow(repair);
        f.locked(same->{f.journal.recoverSettledSameGame(same,first,repair);return null;});
        f.newJournal();var ready=f.read();var fresh=f.semantic(ready,1,24,1);f.allow(fresh);
        f.locked(same->f.journal.recoverSettledSameGame(same,ready,fresh));
        var unregistered=f.softwareApplied(ready,f.semantic(ready,2,24,2).frame(),"software-not-canonical");
        f.rememberSoftwareReceipt(unregistered);
        byte[] before=f.current.canonicalBytes();f.acceptedOperations=Set.of("SETTLED_SAME_GAME_RECOVERY","RETAIN");
        assertThrows(IllegalArgumentException.class,()->f.journal.retainCycle(f.owner,unregistered));
        assertArrayEquals(before,f.current.canonicalBytes());assertEquals(1,f.commits);f.assertNoCredit();
    }

    @Test void settledOpeningCannotBeRetainedOrSettledAgainAfterRecovery() throws Exception {
        var f=fixture();var data=f.read();var fresh=f.semantic(data,0,0,1);f.allow(fresh);
        f.locked(same->{f.journal.recoverSettledSameGame(same,data,fresh);return null;});
        var original=data.settledActions().getFirst();
        f.journal.retainCycle(f.owner,original);
        f.allow(data.latestCycleSemantic());
        var proof=f.journal.settleCycle(f.owner,original,data.latestCycleSemantic());
        assertEquals(1,proof.completedCycles());assertEquals(1,f.commits);
        assertTrue(f.current.toJson().path(WriterContracts.ORDINARY_CYCLE_FIELD).path("pending_receipt").isNull());f.assertNoCredit();
    }

    private static void assertRetained(ContinuityBatchJournal.SettledSameGameData data) {
        assertTrue(data.controller().dirty());assertEquals(1,data.controller().nextBatchSequence());
        assertEquals(Set.of(BATCH),data.controller().usedBatches());assertEquals(1,data.controller().unsavedGameplayActions().size());
        assertEquals(0,data.controller().eligibleSinceSave());assertEquals(0,data.controller().totalCommittedDays());
        assertTrue(data.controller().savedPair().isEmpty());assertFalse(data.controller().quarantined());assertFalse(data.controller().localUnresolved());
        assertEquals(data.settledActions().getFirst().command().actionId(),data.controller().unsavedGameplayActions().iterator().next());
        assertEquals(3,data.retainedFacts().stamp().driverVersion());
    }

    private static void assertController(SessionController controller,ContinuityBatchJournal.SettledSameGameData data) throws Exception {
        assertTrue((boolean)field(controller,"dirty"));assertEquals(data.controller().unsavedGameplayActions(),field(controller,"unsavedGameplayActions"));
        assertEquals(Set.of(BATCH),field(controller,"usedBatches"));assertEquals(0,field(controller,"eligibleSinceSave"));
        assertEquals(0L,field(controller,"totalCommittedDays"));assertFalse(controller.isRunning());assertFalse(controller.isQuarantined());
        assertTrue(controller.savedPair().isEmpty());assertTrue(controller.lastReport().isEmpty());
    }
    private static Object field(SessionController controller,String name) throws Exception {
        var field=SessionController.class.getDeclaredField(name);field.setAccessible(true);return field.get(controller);
    }

    static final class Fixture implements ContinuityStorePort {
        final Path root;
        private final TreeMap<Long,WriterContracts.Pin> pins=new TreeMap<>();
        private final TreeMap<Long,WriterContracts.HistoricalTransition> edges=new TreeMap<>();
        private final Map<ExactRef,byte[]> memory=new HashMap<>();
        final SessionIdentity owner;
        final PortableRecoveryDataArchive archive;
        final ActionPorts.OutcomeArchive outcomes;
        private final Map<ExactRef,ActionReceipt> softwareReceipts=new HashMap<>();
        private final Map<ActionReceipt,ExactRef> softwareReceiptRefs=new HashMap<>();
        private final Map<ExactRef,ActionRecord> softwareRecords=new HashMap<>();
        final OrdinaryCycleTransitions authority;
        ContinuityBatchJournal journal;
        ContinuityState current;
        final long savedDate;
        final long savedCycles;
        SemanticEvidence allowed;
        WriterContracts.Prepared lastPrepared;
        WriterContracts.Receipt lastReceipt;
        int commits;
        Set<String> acceptedOperations=Set.of("SETTLED_SAME_GAME_RECOVERY");
        Set<String> acceptedBatchBoundaries=Set.of();
        private boolean active;
        private Thread thread;
        private final Session session=new Session() {
            @Override public void requireWriter(Path ignored) {throw new AssertionError("no physical writer authority");}
            @Override public WriterContracts.Head head(){requireActive();return Fixture.this.head();}
            @Override public ExactRef persistedHead(){requireActive();return Fixture.this.persistedHead();}
            @Override public WriterContracts.Pin capturePin(ExactRef ref,int maximum)throws IOException {requireActive();read(ref,maximum);return pin(ref);}
            @Override public void verifyPin(WriterContracts.Pin pin)throws IOException {requireActive();read(pin.reference(),WriterContracts.MAX_PIN_BYTES);}
            @Override public byte[] readPinned(WriterContracts.Pin pin,int maximum)throws IOException {requireActive();return read(pin.reference(),maximum);}
            @Override public List<WriterContracts.HistoricalTransition> readHistoricalTransitions(List<WriterContracts.Pin> requested) {
                requireActive();var found=new ArrayList<WriterContracts.HistoricalTransition>();
                for(var pin:requested){long n=Long.parseLong(Path.of(pin.reference().path()).getFileName().toString().substring(0,8));assertEquals(pins.get(n),pin);found.add(edges.get(n));}
                return List.copyOf(found);
            }
            @Override public WriterContracts.Head requireHistoricalHead(long n,String digest) {
                requireActive();var edge=edges.get(n);assertNotNull(edge);assertEquals(digest,ContinuityJson.digest(edge.after().toJson()));
                return new WriterContracts.Head(edge.after(),List.copyOf(pins.headMap(n,true).values()),List.of(),List.of(),false);
            }
            @Override public ContinuityState requireHistoricalState(long n,String digest) {
                requireActive();var edge=edges.get(n);assertNotNull(edge);assertEquals(digest,ContinuityJson.digest(edge.after().toJson()));return edge.after();
            }
            @Override public void requireCommitted(WriterContracts.Prepared original,WriterContracts.Receipt receipt) {
                requireActive();assertSame(lastPrepared,original);assertSame(lastReceipt,receipt);assertEquals(current.sequence(),receipt.head().sequence());
            }
            @Override public void requireDomainImportContinuation(long n,String digest) {
                requireActive();var edge=edges.get(n);assertNotNull(edge);assertEquals(digest,ContinuityJson.digest(edge.after().toJson()));
                for(var descendant:edges.tailMap(n,false).values())assertEquals(DomainBodies.IMPORT_KIND,descendant.kind());
            }
            @Override public WriterContracts.Prepared preview(WriterContracts.Request request)throws IOException {
                requireActive();assertNotNull(allowed,"read-only DATA must not prepare an event");
                if(request.kind().equals(OrdinaryCycleTransitions.BATCH_KIND)) {
                    assertTrue(acceptedBatchBoundaries.contains(request.detailsObject().path("boundary").asText()),"only explicitly selected software batch boundaries");
                    assertTrue(request.detailsObject().path("checkpoint_pair").isNull(),"no software SAVE pair");
                    assertTrue(request.detailsObject().path("completed_cycle_proof").isNull(),"no software cycle credit");
                } else {
                    assertEquals(OrdinaryCycleTransitions.CYCLE_KIND,request.kind());
                    assertTrue(acceptedOperations.contains(request.detailsObject().path("operation").asText()),"no repeated SETTLE/FOCUS/SAVE");
                }
                var before=head();var checked=authority.revalidate(before,request);
                return new WriterContracts.Prepared(before,request,List.of(),List.of(),authority.reduce(current,request),checked);
            }
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared)throws IOException {
                requireActive();assertEquals(head().digest(),prepared.predecessor().digest());
                assertEquals(prepared.preconditionDigest(),authority.revalidate(head(),prepared.request()));
                var reduced=authority.reduce(current,prepared.request());assertArrayEquals(prepared.reduced().canonicalBytes(),reduced.canonicalBytes());
                var before=current;var row=reduced.toJson();row.put("sequence",current.sequence()+1);row.put("last_event_identity",prepared.request().identity());
                current=ContinuityState.fromJson(row,MACHINE);commits++;
                var event=StrictJson.object();event.put("kind",prepared.request().kind());event.put("identity",prepared.request().identity());event.set("details",prepared.request().detailsObject());event.set("after",current.toJson());
                byte[] bytes=ContinuityJson.canonical(event,ContinuityJson.LEDGER_MAX_BYTES);var reference=reference(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS").resolve(String.format(java.util.Locale.ROOT,"%08d.json",current.sequence())),bytes);
                memory.put(reference,bytes);var eventPin=pin(reference);pins.put(current.sequence(),eventPin);
                edges.put(current.sequence(),new WriterContracts.HistoricalTransition(current.sequence(),prepared.request().kind(),prepared.request().details(),prepared.request().identity(),before,current,eventPin));
                lastPrepared=prepared;lastReceipt=new WriterContracts.Receipt(WriterContracts.Disposition.COMMITTED,current,prepared.request().identity(),1,false);return lastReceipt;
            }
        };

        List<WriterContracts.HistoricalTransition> history() {return List.copyOf(edges.values());}

        Fixture(Path actualRoot) throws IOException {
            root=actualRoot;
            var before=state(ContinuityJson.parseObject(Files.readAllBytes(root.resolve("genesis-anchor.json")),ContinuityJson.LEDGER_MAX_BYTES));
            long lastSequence=state(ContinuityJson.parseObject(Files.readAllBytes(root.resolve("continuity.json")),ContinuityJson.LEDGER_MAX_BYTES)).sequence();
            for(long n=1;n<=lastSequence;n++) {
                Path path=root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS").resolve(String.format(java.util.Locale.ROOT,"%08d.json",n));
                byte[] bytes=Files.readAllBytes(path);var event=ContinuityJson.parseObject(bytes,ContinuityJson.LEDGER_MAX_BYTES);var after=state(event.get("after"));
                var eventPin=pin(reference(path,bytes));pins.put(n,eventPin);
                edges.put(n,new WriterContracts.HistoricalTransition(n,StrictJson.text(event.get("kind")),ContinuityJson.canonical(event.get("details")),StrictJson.text(event.get("identity")),before,after,eventPin));before=after;
            }
            current=before;savedDate=current.settledDateRaw();savedCycles=current.settledCycles();
            owner=OrdinaryCycleTransitions.sessionFromJson(current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).get("session"));
            archive=new PortableRecoveryDataArchive(this::requireSession);
            outcomes=withSoftwareCanonical(archive.proxy());
            authority=new OrdinaryCycleTransitions(outcomes,(same,actual,semantic)->{
                requireSession(same);assertEquals(owner,actual);assertEquals(allowed,semantic,"only explicit software fresh SEM is admitted");
                return new OrdinaryCycleTransitions.VerifiedSemantic(semantic.frame(),semantic.observedAt(),"explicit-fixture-sem","b".repeat(64));
            },(same,actual,pair,proof)->{throw new AssertionError("no SAVE");},new OriginalWindowReducer.Policy(current.toJson().path("target_days").longValue()),this::requireSession);
            newJournal();
        }
        void newJournal(){journal=new ContinuityBatchJournal(this,authority);}
        private ActionPorts.OutcomeArchive withSoftwareCanonical(ActionPorts.OutcomeArchive original) {
            return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                String name=method.getName();
                if(name.equals("withSession")){requireSession((Session)args[0]);return proxy;}
                if(name.equals("inSession")){requireSession((Session)args[0]);try{return java.util.function.Function.class.getMethod("apply",Object.class).invoke(args[1],proxy);}catch(InvocationTargetException failure){throw failure.getCause();}}
                if(name.equals("loadReceipt")&&softwareReceipts.containsKey(args[0]))return softwareReceipts.get(args[0]);
                if(name.equals("receiptReferenceOf")&&softwareReceiptRefs.containsKey(args[0]))return softwareReceiptRefs.get(args[0]);
                if(name.equals("loadRecord")&&softwareRecords.containsKey(args[0]))return softwareRecords.get(args[0]);
                try{return method.invoke(original,args);}catch(InvocationTargetException failure){throw failure.getCause();}
            });
        }
        /** Explicit software action: production transitions and receipt/record codecs validate it; no Native dispatch exists. */
        ActionReceipt softwareApplied(ContinuityBatchJournal.SettledSameGameData data,ObservationIdentity before,String id) {
            var source=data.source();var old=data.latestCycleSemantic();var operation=new OperationKey("software-native-mutation");
            var flags=List.<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue>of(
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("native.gameplay_verified"),true));
            var command=new ActionCommand(id,before,source,owner.sessionId(),operation,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,before,source,"software-postcondition/v1",flags),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),old.observedAt().plusSeconds(60));
            var guard=new GuardEvidence(before,source,owner.sessionId(),BigInteger.valueOf(5),operation,old.originalNativePacket(),old.driverStamp(),
                "explicit-software-guard",old.observedAt().plusSeconds(2),command.deadline());
            var after=new ObservationIdentity(before.machineId(),before.game(),new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                before.frame().identity().player(),before.frame().identity().nativeRevision().add(BigInteger.ONE),before.frame().identity().dateRaw()),
                "software-action-after",before.frame().revision().add(BigInteger.ONE),before.frame().episodeRunId()),before.observationVersion());
            var effect=new ActionState.EffectObservation(after,source,owner.sessionId(),"software-postcondition/v1",flags,new ObservationProvenance.Query("software-independent-read"),
                old.observedAt().plusSeconds(4),old.semantic());
            var execution=new CompositeExecution("software-regression/v1",old.observedAt().plusSeconds(2),guard,List.of());
            String body=ActionCodec.bodySha256(command);long sequence=current.sequence();
            var intent=new ActionReceipt(1,sequence+1,command,body,new ActionState.IntentDurable());
            ActionTransitions.validate(Optional.empty(),command,body,intent.state());
            var running=new ActionReceipt(1,sequence+2,command,body,new ActionState.CompositeRunning(execution));
            ActionTransitions.validate(Optional.of(intent),command,body,running.state());
            var applied=new ActionReceipt(1,sequence+3,command,body,new ActionState.CompositeSettled(execution,new ActionState.Applied(effect)));
            ActionTransitions.validate(Optional.of(running),command,body,applied.state());
            ActionEffects.validateCompositeChildren(execution,((ActionState.CompositeSettled)applied.state()).settlement(),List.of());
            return applied;
        }
        ExactRef rememberSoftwareReceipt(ActionReceipt receipt) {
            byte[] bytes=ActionReceiptCodec.encodeReceipt(receipt,outcomes);var ref=reference(root.resolve(receipt.command().actionId()+"-receipt-memory.json"),bytes);
            softwareReceipts.put(ref,receipt);softwareReceiptRefs.put(receipt,ref);memory.put(ref,bytes);
            assertEquals(receipt,ActionReceiptCodec.decodeReceipt(bytes,outcomes));return ref;
        }
        ExactRef installSoftwareCanonical(ActionReceipt receipt) {
            var receiptRef=rememberSoftwareReceipt(receipt);
            var record=new ActionRecord(receipt,ContinuityActionJournal.recordHead(current));byte[] bytes=ActionRecordCodec.encode(record,outcomes);
            var ref=reference(root.resolve(receipt.command().actionId()+"-record-memory.json"),bytes);softwareRecords.put(ref,record);memory.put(ref,bytes);
            assertEquals(record,ActionRecordCodec.decode(bytes,outcomes));
            var row=current.toJson();row.put("sequence",receipt.sequence());row.set(ContinuityActionJournal.STATE_FIELD,ref.toJson());current=state(row);
            return receiptRef;
        }
        ContinuityBatchJournal.SettledSameGameData read()throws IOException{return locked(same->journal.readSettledSameGame(same,owner));}
        void allow(SemanticEvidence semantic){allowed=semantic;}
        SemanticEvidence semantic(ContinuityBatchJournal.SettledSameGameData data,long nativeDelta,long dateDelta,long publicRevision) {
            var previous=data.latestCycleSemantic();var old=data.latestObservedFrame();var frame=old.frame();var id=frame.identity();
            var fresh=new ObservationIdentity(old.machineId(),old.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(id.player(),id.nativeRevision().add(BigInteger.valueOf(nativeDelta)),id.dateRaw().add(BigInteger.valueOf(dateDelta))),
                "software-new-hello-"+nativeDelta+"-"+dateDelta,frame.revision().add(BigInteger.valueOf(publicRevision)),frame.episodeRunId()),old.observationVersion());
            return new SemanticEvidence(fresh,previous.semantic(),previous.originalNativePacket(),previous.driverStamp(),previous.originalDriver(),previous.observedAt().plusSeconds(1));
        }
        void assertNoCredit(){assertEquals(savedDate,current.settledDateRaw());assertEquals(savedCycles,current.settledCycles());}
        private byte[] read(ExactRef ref,int maximum)throws IOException {
            if(memory.containsKey(ref)){var bytes=memory.get(ref);assertTrue(bytes.length<=maximum);return bytes.clone();}
            return PortableRecoveryDataArchive.readExact(ref,maximum);
        }
        private ContinuityState state(JsonNode row){return ContinuityState.fromJson(row,MACHINE);}
        private WriterContracts.Head head(){return new WriterContracts.Head(current,List.copyOf(pins.values()),List.of(),List.of(),false);}
        private void requireActive(){assertTrue(active&&thread==Thread.currentThread());}
        @Override public void requireSession(Session same){requireActive();assertSame(session,same);}
        @Override public <T> T locked(SessionWork<T> work)throws IOException {
            assertFalse(active);active=true;thread=Thread.currentThread();try{return work.run(session);}finally{active=false;thread=null;}
        }
        @Override public ExactRef persistedHead(){return reference(root.resolve("continuity.json"),current.canonicalBytes());}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("no external preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("no external commit");}

        SessionController controller(ExactRef source) {
            var noFiles=refusing(CheckpointFiles.class);var noSnapshot=new DriverCheckpointStore.SnapshotSupplier(){
                @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw new AssertionError("no Driver freeze");}
            };
            var drivers=new DriverCheckpointStore(noFiles,root.resolve("unused-Driver.json"),"settled-recovery-test",noSnapshot);
            CheckpointRequest.ObservationPort noCheckpoint=until->{throw new AssertionError("no checkpoint observation");};
            var clock=Clock.fixed(Instant.parse("2026-10-30T13:50:00Z"),ZoneOffset.UTC);
            var saves=new CheckpointService(noFiles,drivers,noCheckpoint,root.resolve("unused-save-evidence"),clock,(pair,receipt)->{throw new AssertionError("no seed adoption");});
            var requests=new CheckpointRequestFactory(root.resolve("unused.ck3"),noCheckpoint);
            var planner=new OrdinaryPlanner(List.of(),clock,new RealmLifecycle(source));
            return new SessionController(owner,refusing(LifecyclePort.class),refusing(ObservationPort.class),planner,refusing(ActionCoordinatorPort.class),saves,requests,journal,
                refusing(OfflineAnalysisPort.class),refusing(SessionClock.class),Optional.empty(),0,refusing(OrdinaryPlanCompletion.PlanningScope.class),refusing(EpisodeContinuation.class));
        }
    }
    private static ExactRef reference(Path path,byte[] bytes){return new ExactRef(path.toAbsolutePath().toString(),bytes.length,DriverJson.sha256(bytes));}
    private static WriterContracts.Pin pin(ExactRef ref){return new WriterContracts.Pin(ref,new WriterContracts.FileIdentity("0","0","0","2026-10-30T00:00:00Z",ref.bytes()));}
    private static <T> T refusing(Class<T> type){return type.cast(Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},(proxy,method,args)->{throw new AssertionError("no execution port "+type.getSimpleName()+"."+method.getName());}));}
}
