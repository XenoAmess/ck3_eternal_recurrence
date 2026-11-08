package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.CleanupMode;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeConstructionEffects;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Same-call decoded DATA reuse with actual writer/CAS reads; the delegate below is explicitly a spy.
 * No Loaded is minted by reflection. The private resolver is invoked only with public-produced Loaded
 * to observe its returned identity; the real Native-positive OUTCOME is a separate existing software test.
 */
final class ConstructionOutcomeOriginal133Test {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;

    @Test void sameCallHitStillReadsTwiceAndDifferentReferenceOrInlineRetainsOldPath() throws Exception {
        Obj full=quote(true),small=quote(false);byte[] exact=DriverJson.encode(full);
        var observed=ObservedRequest.fromFullMaterial(exact);
        assertTrue(exact.length>6_000_000);
        try(var a=new Store(directory.resolve("first"));var b=new Store(directory.resolve("other-reference"))) {
            Obj manifestA=a.writer.locked(same->new ConstructionOriginalSource(a.archive,a.writer::borrowedSession).preserve(observed));
            Obj manifestB=b.writer.locked(same->new ConstructionOriginalSource(b.archive,b.writer::borrowedSession).preserve(observed));
            assertNotEquals(reference(manifestA),reference(manifestB));
            assertEquals(reference(manifestA).sha256(),reference(manifestB).sha256());
            var commandA=command(a.source,full,manifestA,"p133-same-call-data");
            var commandB=command(b.source,full,manifestB,"p133-foreign-reference-data");
            byte[] canonical=ActionCodec.encodeCommand(commandA);
            ConstructionOriginalSource.Loaded first=a.writer.locked(same->{
                String head=same.head().digest();var counting=new CountingArchive(a.archive);
                var original=ConstructionOriginalSource.resolveCommand(same,counting.port(),commandA);
                assertEquals(1,counting.loads);assertEquals(reference(manifestA),fullReference(original));
                var hit=resolveCandidate(same,counting.port(),commandA,original);
                assertEquals(2,counting.loads);assertSame(original,hit);assertSame(original.original(),hit.original());
                assertSame(original.observed(),hit.observed());
                var oldNull=resolveCandidate(same,counting.port(),commandA,null);
                assertEquals(3,counting.loads);assertNotSame(original,oldNull);
                assertArrayEquals(exact,oldNull.observed().original());
                assertArrayEquals(DriverJson.encode(original.original()),DriverJson.encode(oldNull.original()));
                assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(OrdinaryWartimeConstruction.compose(original.observed().input())),
                        OrdinaryWartimeConstructionCodec.encode(OrdinaryWartimeConstruction.compose(oldNull.observed().input())));
                assertArrayEquals(original.observed().input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow(),
                        oldNull.observed().input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow());
                byte[] caller=original.observed().original();caller[0]='!';assertArrayEquals(exact,original.observed().original());

                counting.clear();var firstRead=ConstructionOriginalSource.resolveCommand(same,counting.port(),commandA);
                var delegates=new AtomicInteger();
                var spy=new NativeRecordedEvidenceVerifier.Binding(commandA.operation(),a.source,(actualHead,receipt,archive)->{
                    assertEquals(2,counting.loads,"both real full reads must precede DATA-only delegate");delegates.incrementAndGet();
                });
                ConstructionOriginalSource.verifyArchived(spy,()->same,same.head(),receipt(commandA),counting.port(),firstRead);
                assertEquals(2,counting.loads);assertEquals(List.of(reference(manifestA),reference(manifestA)),counting.references);
                assertEquals(1,delegates.get());
                counting.clear();ConstructionOriginalSource.resolveCommand(same,counting.port(),commandA);
                ConstructionOriginalSource.archivedBinding(spy,()->same).verifier().verify(same.head(),receipt(commandA),counting.port());
                assertEquals(2,counting.loads);assertEquals(2,delegates.get(),"old public binding still performs its independent read");
                assertArrayEquals(canonical,ActionCodec.encodeCommand(commandA));assertEquals(head,same.head().digest());return original;
            });
            b.writer.locked(same->{
                String head=same.head().digest();var counting=new CountingArchive(b.archive);
                var fallback=resolveCandidate(same,counting.port(),commandB,first);
                assertEquals(1,counting.loads);assertNotSame(first,fallback);
                assertEquals(reference(manifestB),fullReference(fallback));assertArrayEquals(exact,fallback.observed().original());
                assertArrayEquals(DriverJson.encode(first.original()),DriverJson.encode(fallback.original()));
                assertEquals(head,same.head().digest());return null;
            });
            var smallObserved=new ObservedRequest(DriverJson.encode(small));
            Obj inline=a.writer.locked(same->new ConstructionOriginalSource(a.archive,a.writer::borrowedSession).preserve(smallObserved));
            var smallCommand=command(a.source,small,inline,"p133-old-inline-data");
            a.writer.locked(same->{
                String head=same.head().digest();var counting=new CountingArchive(a.archive);
                var legacy=resolveCandidate(same,counting.port(),smallCommand,first);
                assertNull(fullReference(legacy));assertNotSame(first,legacy);assertEquals(0,counting.loads);
                assertArrayEquals(new ObservedRequest(encode(inline)).original(),legacy.observed().original());
                var delegates=new AtomicInteger();
                ConstructionOriginalSource.verifyArchived(new NativeRecordedEvidenceVerifier.Binding(smallCommand.operation(),a.source,
                        (actualHead,receipt,archive)->delegates.incrementAndGet()),()->same,same.head(),receipt(smallCommand),counting.port(),first);
                assertEquals(1,delegates.get());assertEquals(0,counting.loads);assertEquals(head,same.head().digest());return null;
            });
        }
    }

    @Test void hitCandidateNeverReplacesFreshHeaderFrameMissingOrCorruptedPhysicalChecks() throws Exception {
        Obj full=quote(true);byte[] exact=DriverJson.encode(full);var observed=ObservedRequest.fromFullMaterial(exact);
        try(var f=new Store(directory.resolve("fresh-failures"))) {
            Obj manifest=f.writer.locked(same->new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(observed));
            var command=command(f.source,full,manifest,"p133-fresh-failure-data");
            Obj wrongHeader=manifest.with("financing_request",object(manifest.get("financing_request"),"financing")
                    .with("schema",new Text("p133-different-complete-financing-header")));
            var headerCommand=command(f.source,full,wrongHeader,"p133-header-mismatch-data");
            var frame=command.before().frame();
            var wrongBefore=new ProposalLifecycle.ObservationIdentity(command.before().machineId(),command.before().game(),
                    new JointBudgetSelector.ProposalFrame(frame.identity(),frame.snapshotId(),frame.revision().add(BigInteger.ONE),frame.episodeRunId()),
                    command.before().observationVersion());
            var frameCommand=new ActionCommand("p133-crossed-command-frame-data",wrongBefore,command.source(),command.sessionId(),command.operation(),
                    command.arguments(),NativeConstructionEffects.expected(wrongBefore,command.source(),command.arguments()),command.claims(),command.deadline());
            f.writer.locked(same->{
                String head=same.head().digest();var counting=new CountingArchive(f.archive);
                var first=ConstructionOriginalSource.resolveCommand(same,counting.port(),command);
                var delegates=new AtomicInteger();var spy=new NativeRecordedEvidenceVerifier.Binding(command.operation(),f.source,
                        (actualHead,receipt,archive)->delegates.incrementAndGet());
                counting.clear();var headerFailure=assertThrows(IllegalArgumentException.class,()->
                        ConstructionOriginalSource.verifyArchived(spy,()->same,same.head(),receipt(headerCommand),counting.port(),first));
                assertEquals("construction manifest financing differs from full original",headerFailure.getMessage());
                assertEquals(1,counting.loads);assertEquals(0,delegates.get());
                counting.clear();var frameFailure=assertThrows(IllegalArgumentException.class,()->
                        ConstructionOriginalSource.verifyArchived(spy,()->same,same.head(),receipt(frameCommand),counting.port(),first));
                assertEquals("construction full original crossed command frame",frameFailure.getMessage());
                assertEquals(1,counting.loads);assertEquals(0,delegates.get());
                Path payload=Path.of(reference(manifest).path()),held=payload.resolveSibling(payload.getFileName()+".held");
                Files.move(payload,held);
                try {
                    counting.clear();assertThrows(RuntimeException.class,()->
                            ConstructionOriginalSource.verifyArchived(spy,()->same,same.head(),receipt(command),counting.port(),first));
                    assertEquals(1,counting.loads);assertEquals(0,delegates.get());
                } finally {Files.move(held,payload);}
                byte[] damaged=exact.clone();damaged[0]='[';Files.write(payload,damaged);
                try {
                    counting.clear();assertThrows(RuntimeException.class,()->
                            ConstructionOriginalSource.verifyArchived(spy,()->same,same.head(),receipt(command),counting.port(),first));
                    assertEquals(1,counting.loads);assertEquals(0,delegates.get(),"physical length/SHA/archive failure must precede delegate");
                } finally {Files.write(payload,exact);}
                assertArrayEquals(exact,Files.readAllBytes(payload));assertArrayEquals(exact,first.observed().original());
                assertEquals(head,same.head().digest());return null;
            });
        }
    }

    private static ConstructionOriginalSource.Loaded resolveCandidate(Session same,ActionPorts.OutcomeArchive archive,
            ActionCommand command,ConstructionOriginalSource.Loaded candidate) {
        try {
            var method=ConstructionOriginalSource.class.getDeclaredMethod("resolveCommand",Session.class,ActionPorts.OutcomeArchive.class,
                    ActionCommand.class,ConstructionOriginalSource.Loaded.class);method.setAccessible(true);
            return (ConstructionOriginalSource.Loaded)method.invoke(null,same,archive,command,candidate);
        } catch(InvocationTargetException failure) {
            if(failure.getCause() instanceof RuntimeException runtime)throw runtime;
            if(failure.getCause() instanceof Error error)throw error;
            throw new IllegalStateException(failure.getCause());
        } catch(ReflectiveOperationException failure) {throw new IllegalStateException(failure);}
    }
    private static ExactRef fullReference(ConstructionOriginalSource.Loaded loaded) {
        try {var field=ConstructionOriginalSource.Loaded.class.getDeclaredField("fullInputReference");field.setAccessible(true);return (ExactRef)field.get(loaded);}
        catch(ReflectiveOperationException failure){throw new IllegalStateException(failure);}
    }
    private static ActionReceipt receipt(ActionCommand command) {
        return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());
    }
    private static Obj quote(boolean large)throws Exception {
        var method=ConstructionFullCustody113Test.class.getDeclaredMethod("quote",boolean.class);method.setAccessible(true);return (Obj)method.invoke(null,large);
    }
    private static ActionCommand command(ExactRef source,Obj full,Obj supplied,String id) {
        try {var method=ConstructionFullCustody113Test.class.getDeclaredMethod("command",ExactRef.class,Obj.class,Obj.class,String.class);
            method.setAccessible(true);return (ActionCommand)method.invoke(null,source,full,supplied,id);
        }catch(ReflectiveOperationException failure){throw new IllegalStateException(failure instanceof InvocationTargetException?failure.getCause():failure);}
    }
    private static ExactRef reference(Obj manifest){return ExactRef.fromJson(StrictJson.parse(DriverJson.encode(object(manifest.get("input_ref"),"reference"))));}
    private static ExactRef exact(Path path)throws IOException{byte[] b=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),b.length,ActionCodec.sha256(b));}
    /** Counts calls while delegating every actual operation, including withSession and all original exceptions. */
    private static final class CountingArchive {
        final ActionPorts.OutcomeArchive original;int loads;final List<ExactRef> references=new ArrayList<>();
        CountingArchive(ActionPorts.OutcomeArchive original){this.original=original;}
        void clear(){loads=0;references.clear();}
        ActionPorts.OutcomeArchive port(){return wrap(original);}
        private ActionPorts.OutcomeArchive wrap(ActionPorts.OutcomeArchive actual) {
            return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                        if(method.getName().equals("loadFullMaterial")){loads++;references.add((ExactRef)args[0]);}
                        try {Object result=method.invoke(actual,args);
                            return method.getName().equals("withSession")?wrap((ActionPorts.OutcomeArchive)result):result;
                        }catch(InvocationTargetException failure){throw failure.getCause();}
                    });
        }
    }
    private static final class Store implements AutoCloseable {
        final StorageWriteGuardTestSupport guard;final ImmutableArtifactStore store;final ContinuityWriter writer;
        final NativeOutcomeArchive archive;final ExactRef source;
        Store(Path root)throws IOException {
            Files.createDirectories(root);var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1").put("machine_id","construction-full-original-software-machine")
                    .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25)
                    .put("start_date_raw",1000).put("target_date_raw",263992).put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1)
                    .put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
            state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");state.putNull("latest_binding");state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
            Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");Files.write(snapshot,ContinuityJson.canonical(state));Files.write(anchor,ContinuityJson.canonical(state));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path producer=root.resolve("p133-software-source.txt");Files.writeString(producer,"P133 independent SOFTWARE source metadata, never Root authority",StandardCharsets.UTF_8);source=exact(producer);
            var layout=new Layout(snapshot,exact(anchor),"construction-full-original-software-machine");Path objects=root.resolve("objects");Files.createDirectory(objects);
            guard=StorageWriteGuardTestSupport.create(root,layout.lock(),32*1024*1024);store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(objects,layout.lock(),32*1024*1024),guard);
            writer=new ContinuityWriter(layout,List.of(source),new TransitionAuthority(){
                public String revalidate(ContinuityState head,Request request){throw new AssertionError("no mutation in custody DATA");}
                public ContinuityState reduce(ContinuityState head,Request request){throw new AssertionError("no mutation in custody DATA");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),guard);archive=new NativeOutcomeArchive(store,writer);
        }
        public void close()throws IOException{guard.close();}
    }
}
