package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual writer/CAS historical DATA membership only. This never installs or fabricates a Root/derived guard. */
final class DerivedParentCanonical72BTest {
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(64, 8L*1024*1024, 128);
    @TempDir Path temporary;

    private record Original(ActionReceipt intent, ExactRef intentReference, ActionReceipt unknown,
            WriterContracts.Head atIntent, WriterContracts.Head current, List<ExactRef> currentRecordOrder) { }

    private static Original original(ActionWriterIntegrationFixture fixture) throws Exception {
        var initialPoint=new AtomicReference<WriterContracts.Head>();
        var intentPoint=new AtomicReference<WriterContracts.Head>();
        fixture.bindGuardObserver((head,command)->{
            if (!initialPoint.compareAndSet(null,head)) intentPoint.set(head);
        });
        ActionCommand command=fixture.command("canonical72b-data-only");
        ActionReceipt unknown=fixture.coordinator.execute(command);
        assertInstanceOf(ActionState.Unknown.class,unknown.state());
        assertNotNull(intentPoint.get());
        return fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
            try {
                WriterContracts.Head head=same.head();
                var order=new ArrayList<ExactRef>();ActionReceipt intent=null;
                var next=ContinuityActionJournal.recordHead(head.state());
                while(next.isPresent()) {
                    ExactRef ref=next.orElseThrow();order.add(ref);ActionRecord record=archive.loadRecord(ref);
                    if(record.receipt().state() instanceof ActionState.IntentDurable) intent=record.receipt();
                    next=record.previous();
                }
                assertNotNull(intent);assertTrue(order.size()>=3,"genuine canonical chain includes multiple original transitions");
                assertEquals(intentPoint.get().state().toJson(),same.requireHistoricalState(intentPoint.get().state().sequence(),intentPoint.get().digest()).toJson());
                // Resolve/preserve this original reference before every read-only historical scope.
                ExactRef ref=archive.receiptReferenceOf(intent);
                return new Original(intent,ref,unknown,intentPoint.get(),head,List.copyOf(order));
            } catch(IOException failure){throw new UncheckedIOException(failure);}
        }));
    }

    @Test void actualNativeHistoricalRouterMatchesPlainFullRouteAndReopensItsExactCanonicalData() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-held-history"),true)) {
            Original original=original(fixture);
            int actionWrites=fixture.nativeActionWrites(), nativeReads=fixture.nativeReadWrites();
            ContinuityState current=original.current().state();
            ContinuityState equalObject=ContinuityState.fromJson(current.toJson(),current.machineId());
            assertNotSame(current,equalObject);assertEquals(current.toJson(),equalObject.toJson());
            scope(fixture,"typed-same-head",archive->{
                assertInstanceOf(NativeOutcomeArchive.class,archive);
                ActionReceipt selected=RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(current,equalObject,original.intentReference(),archive);
                assertEquals(original.intent(),selected);
                assertArrayEquals(ActionReceiptCodec.encodeReceipt(original.intent(),archive),ActionReceiptCodec.encodeReceipt(selected,archive));
                return null;
            });
            scope(fixture,"plain-same-head",archive->{
                Probe probe=new Probe(archive,original.currentRecordOrder().getFirst());
                assertFalse(probe.port instanceof NativeOutcomeArchive);
                assertEquals(original.intent(),RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(current,equalObject,original.intentReference(),probe.port));
                assertEquals(join(original.currentRecordOrder(),original.currentRecordOrder()),probe.recordReads,
                        "arbitrary public archive performs both original complete walks, without an opt-in default");
                assertEquals("loadReceipt",probe.events.getFirst());
                return null;
            });
            scope(fixture,"typed-different-head",archive->{
                ActionReceipt selected=RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(original.atIntent().state(),current,original.intentReference(),archive);
                assertEquals(original.intent(),selected);
                return null;
            });
            // A real bound Session without HistoricalReads custody keeps the existing full route.
            fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
                assertEquals(original.intent(),RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(current,equalObject,original.intentReference(),archive));
                return null;
            }));
            assertEquals(actionWrites,fixture.nativeActionWrites());assertEquals(nativeReads,fixture.nativeReadWrites());
            assertEquals(1,actionWrites);assertFalse(original.unknown().settled());assertFalse(original.unknown().eligibleAdvance());
        }
    }

    @Test void publicFallbackPreservesParentFirstBothCompleteReadersAndLaterFreshFailures() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("plain-errors"),true)) {
            Original original=original(fixture);ContinuityState current=original.current().state();
            int actionWrites=fixture.nativeActionWrites(),nativeReads=fixture.nativeReadWrites();
            var sentinel=new IllegalStateException("second original head is freshly unavailable");
            scope(fixture,"plain-second-failure",archive->{
                Probe probe=new Probe(archive,original.currentRecordOrder().getFirst());probe.secondHeadFailure=sentinel;
                assertSame(sentinel,assertThrows(IllegalStateException.class,()->
                        RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(current,current,original.intentReference(),probe.port)));
                assertEquals(join(original.currentRecordOrder(),List.of(original.currentRecordOrder().getFirst())),probe.recordReads,
                        "complete first chain and its body equality cannot hide the next original read failure");
                assertEquals("loadReceipt",probe.events.getFirst());return null;
            });
            var parentFailure=new IllegalStateException("original parent cannot be decoded");
            scope(fixture,"plain-parent-first",archive->{
                Probe probe=new Probe(archive,original.currentRecordOrder().getFirst());probe.parentFailure=parentFailure;
                assertSame(parentFailure,assertThrows(IllegalStateException.class,()->
                        RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(current,current,original.intentReference(),probe.port)));
                assertEquals(List.of("loadReceipt"),probe.events);assertTrue(probe.recordReads.isEmpty());return null;
            });
            var foreignRow=current.toJson();foreignRow.put("machine_id","foreign-machine");
            var foreign=ContinuityState.fromJson(foreignRow,"foreign-machine");
            scope(fixture,"plain-second-header",archive->{
                Probe probe=new Probe(archive,original.currentRecordOrder().getFirst());
                var failure=assertThrows(IllegalArgumentException.class,()->
                        RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(current,foreign,original.intentReference(),probe.port));
                assertEquals("historical receipt crossed actual writer machine/sequence",failure.getMessage());
                assertEquals(original.currentRecordOrder(),probe.recordReads,"second top/header error still follows the complete first membership reader");
                return null;
            });
            scope(fixture,"typed-after-public-failures",archive->{
                assertEquals(original.intent(),RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(current,current,original.intentReference(),archive));
                return null;
            });
            assertEquals(actionWrites,fixture.nativeActionWrites());assertEquals(nativeReads,fixture.nativeReadWrites());
            assertEquals(1,actionWrites);
        }
    }

    private static List<ExactRef> join(List<ExactRef> first,List<ExactRef> second){var values=new ArrayList<>(first);values.addAll(second);return List.copyOf(values);}

    private static <T>T scope(ActionWriterIntegrationFixture fixture,String label,Function<ActionPorts.OutcomeArchive,T> work) throws IOException {
        System.getLogger(ImmutableArtifactStore.class.getName()).log(System.Logger.Level.INFO,"CANONICAL72B_TEST_SCOPE_BEGIN label="+label);
        try {
            return fixture.writer.locked(same->fixture.archive.inHistoricalReadScope(same,LIMITS,work::apply));
        } finally {
            System.getLogger(ImmutableArtifactStore.class.getName()).log(System.Logger.Level.INFO,"CANONICAL72B_TEST_SCOPE_END label="+label);
        }
    }

    /** Observable calls through the original public Archive contract, never a private cache/token counter. */
    private static final class Probe {
        final List<String> events=new ArrayList<>();final List<ExactRef> recordReads=new ArrayList<>();
        final ActionPorts.OutcomeArchive port;final ExactRef head;int headOccurrences;
        RuntimeException secondHeadFailure,parentFailure;
        Probe(ActionPorts.OutcomeArchive actual,ExactRef head){
            this.head=head;
            port=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                if(method.getName().equals("loadReceipt")) {
                    events.add("loadReceipt");if(parentFailure!=null)throw parentFailure;
                } else if(method.getName().equals("loadRecord")) {
                    ExactRef ref=(ExactRef)args[0];events.add("loadRecord");recordReads.add(ref);
                    if(ref.equals(head)&&++headOccurrences==2&&secondHeadFailure!=null)throw secondHeadFailure;
                }
                try{return method.invoke(actual,args);}catch(InvocationTargetException failure){throw failure.getCause();}
            });
        }
    }
}
