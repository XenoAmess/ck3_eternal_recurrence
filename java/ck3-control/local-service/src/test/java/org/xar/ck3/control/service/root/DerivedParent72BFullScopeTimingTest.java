package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Finite controlled DATA full-scope timing only. No Runtime/game speed or successful action proof. */
final class DerivedParent72BFullScopeTimingTest {
    private static final ActionPorts.HistoricalReadLimits LIMITS=new ActionPorts.HistoricalReadLimits(4096,256L*1024*1024,8192);
    @TempDir Path temporary;
    private int ordinal;

    @Test void fixedTwoNaturalCanonicalCutsWarmABThenFourABBAFullScopeRounds() throws Exception {
        long setupBegan=System.nanoTime();
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("same-real-fixture"),true)) {
            Original small=original(fixture);
            emitSetup("original",small,System.nanoTime()-setupBegan);
            int originalWrites=fixture.nativeActionWrites(),originalReads=fixture.nativeReadWrites();
            assertEquals(4,small.currentRecordOrder().size(),"the original natural fixture cut is not silently retuned");
            // Existing transitions alone authorize archival growth; no new protocol, dispatch or guard.
            // A rejection retains its actual failure/limitation instead of forcing either target.
            ActionState.Unknown retained=assertInstanceOf(ActionState.Unknown.class,small.unknown().state());
            ActionState.Unknown same=new ActionState.Unknown(retained.attempt(),retained.dispatch(),retained.reason(),retained.evidence());
            try {ActionTransitions.validate(Optional.of(small.unknown()),small.unknown().command(),small.unknown().bodySha256(),same);}
            catch(IllegalArgumentException unsupported) {
                var row=StrictJson.object().put("schema","xar.canonical72b-growth/v1").put("accepted",false)
                        .put("reason",String.valueOf(unsupported.getMessage())).put("all_requested_cuts_not_run",true);
                System.out.println(row);return;
            }
            int previousCount=small.currentRecordOrder().size();
            for(int target:List.of(16,32)) {
                long growthBegan=System.nanoTime();
                try {
                    for(int i=0;i<target-previousCount;i++) fixture.journal.locked(locked->{
                        ActionReceipt prior=locked.find(small.unknown().command().actionId()).orElseThrow();
                        ActionState.Unknown value=assertInstanceOf(ActionState.Unknown.class,prior.state());
                        var next=new ActionState.Unknown(value.attempt(),value.dispatch(),value.reason(),value.evidence());
                        ActionTransitions.validate(Optional.of(prior),prior.command(),prior.bodySha256(),next);
                        ActionReceipt appended=locked.append(prior.command(),prior.bodySha256(),next);
                        assertEquals(prior.command(),appended.command());assertEquals(prior.bodySha256(),appended.bodySha256());
                        assertEquals(value.attempt(),ActionTransitions.attempt(appended.state()));
                        assertEquals(value.dispatch(),ActionTransitions.dispatch(appended.state()));
                        assertEquals(value.evidence(),assertInstanceOf(ActionState.Unknown.class,appended.state()).evidence());
                        assertFalse(appended.settled());assertFalse(appended.eligibleAdvance());return appended;
                    });
                } catch(RuntimeException|Error failure) {
                    System.out.println(StrictJson.object().put("schema","xar.canonical72b-growth/v1").put("accepted",false)
                            .put("nanos",System.nanoTime()-growthBegan).put("error_class",failure.getClass().getName())
                            .put("error_message",String.valueOf(failure.getMessage())));
                    throw failure;
                }
                Original large=currentCut(fixture,small);
                emitSetup("grown",large,System.nanoTime()-growthBegan);
                assertEquals(target,large.currentRecordOrder().size());
                assertEquals(small.intentReference(),large.intentReference());
                assertEquals(originalWrites,fixture.nativeActionWrites());assertEquals(originalReads,fixture.nativeReadWrites());
                measureCut(fixture,large,originalWrites,originalReads);
                previousCount=target;
            }
        }
    }

    private void measureCut(ActionWriterIntegrationFixture fixture,Original cut,int writes,int reads) throws Exception {
        assertTrue(cut.currentRecordOrder().size()==16||cut.currentRecordOrder().size()==32);
        ContinuityState originalState=cut.current().state();
        ContinuityState equalClone=ContinuityState.fromJson(originalState.toJson(),originalState.machineId());
        byte[] ledgerBefore=fixture.ledgerBytes();
        sample(fixture,cut,equalClone,"warmup","A",0);
        sample(fixture,cut,equalClone,"warmup","B",1);
        int index=0;
        for(int round=0;round<4;round++)for(String variant:List.of("A","B","B","A"))
            sample(fixture,cut,equalClone,"measure",variant,index++);
        assertEquals(16,index);
        assertArrayEquals(ledgerBefore,fixture.ledgerBytes(),"read-only timed scopes never append/change the captured state");
        assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
    }

    private void sample(ActionWriterIntegrationFixture fixture,Original cut,ContinuityState equalClone,
            String phase,String variant,int index) throws Exception {
        int number=ordinal++;
        String label="n"+cut.currentRecordOrder().size()+"-"+phase+"-"+index+"-"+variant;
        System.getLogger(ImmutableArtifactStore.class.getName()).log(System.Logger.Level.INFO,"CANONICAL72B_TIMING_BEGIN label="+label);
        ActionReceipt actual=null;Throwable failed=null;
        long began=System.nanoTime();
        try {
            actual=fixture.writer.locked(same->fixture.archive.inSession(same,ignored->{
                try {
                    return fixture.archive.inHistoricalReadScope(same,LIMITS,archive->{
                        if(variant.equals("A"))return RootDerivedChildAuthority.loadDerivedParentForHistoricalValidation(
                                cut.current().state(),equalClone,cut.intentReference(),archive);
                        // Frozen original three-line membership body, with the same actual Native archive.
                        // No public Proxy/reflection/adapter cost is added to the baseline timing.
                        ActionReceipt parent=archive.loadReceipt(cut.intentReference());
                        ContinuityActionJournal.requireHistoricalReceipt(cut.current().state(),parent,archive);
                        ContinuityActionJournal.requireHistoricalReceipt(equalClone,parent,archive);
                        return parent;
                    });
                } catch(IOException failure){throw new UncheckedIOException(failure);}
            }));
        } catch(Throwable failure){failed=failure;}
        long ended=System.nanoTime();
        boolean equal=failed==null&&cut.intent().equals(actual);
        var row=StrictJson.object().put("schema","xar.canonical72b-full-scope-timing/v1").put("phase",phase)
                .put("ordinal",number).put("index",index).put("variant",variant).put("chain_records",cut.currentRecordOrder().size())
                .put("scope_nanos",ended-began).put("scope_returned",failed==null).put("result_equal",equal);
        if(failed!=null)row.put("error_class",failed.getClass().getName()).put("error_message",String.valueOf(failed.getMessage()));
        System.out.println(row);
        System.getLogger(ImmutableArtifactStore.class.getName()).log(System.Logger.Level.INFO,"CANONICAL72B_TIMING_END label="+label);
        // Fail-stop: the raw failed sample is retained, never omitted/retried/replaced. Normal equality is outside endpoints.
        if(failed instanceof Error error)throw error;
        if(failed instanceof Exception exception)throw exception;
        assertNull(failed);assertEquals(cut.intent(),actual);assertTrue(ended>=began);
    }

    private static void emitSetup(String kind,Original cut,long nanos) {
        var row=StrictJson.object().put("schema","xar.canonical72b-timing-setup/v1").put("kind",kind).put("nanos",nanos)
                .put("chain_records",cut.currentRecordOrder().size()).put("state_sequence",cut.current().state().sequence())
                .put("head_digest",cut.current().digest()).put("scope","controlled DATA membership; not Runtime or game performance");
        row.set("parent_receipt",cut.intentReference().toJson());System.out.println(row);
    }

    private static Original currentCut(ActionWriterIntegrationFixture fixture,Original prior) throws IOException {
        return fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
            try {
                var head=same.head();var refs=new ArrayList<ExactRef>();var next=ContinuityActionJournal.recordHead(head.state());
                while(next.isPresent()) {ExactRef ref=next.orElseThrow();refs.add(ref);next=archive.loadRecord(ref).previous();}
                var latest=ContinuityActionJournal.lookup(head.state(),prior.unknown().command().actionId(),archive).orElseThrow();
                return new Original(prior.intent(),prior.intentReference(),latest,prior.atIntent(),head,List.copyOf(refs));
            } catch(IOException failure){throw new UncheckedIOException(failure);}
        }));
    }
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

}
