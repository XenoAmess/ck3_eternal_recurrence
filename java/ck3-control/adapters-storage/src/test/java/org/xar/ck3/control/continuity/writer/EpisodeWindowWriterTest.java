package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.contracts.*;

/** Real original Windows writer and finite persistence. Fixture custody is software only, never Game/SAVE qualification. */
final class EpisodeWindowWriterTest {
    @TempDir Path temporary;
    private static final class Fixture {
        final WriterFixture files;
        final Layout layout;
        final AtomicInteger validations=new AtomicInteger();
        final AtomicBoolean firstSaveConfirmed=new AtomicBoolean();
        final AtomicBoolean mutateOnValidation=new AtomicBoolean();
        final TransitionAuthority authority;
        ContinuityWriter writer;
        EpisodeWindow.Begin begin;
        final ExactRef pair,receipt,driver;
        Fixture(Path root)throws IOException{
            assertTrue(Platform.isWindows(),"real Windows ledger identity/lock fixture requires Windows");
            files=new WriterFixture(root);
            ObjectNode seed=WriterFixture.state();seed.putNull("unknown_actions");seed.putObject("unknown_requests").put("original_request","UNKNOWN");
            Files.write(files.layout.snapshot(),ContinuityJson.canonical(seed));Files.write(Path.of(files.layout.anchor().path()),ContinuityJson.canonical(seed));
            layout=new Layout(files.layout.snapshot(),LedgerFiles.read(Path.of(files.layout.anchor().path()),65_536).pin().reference(),WriterFixture.MACHINE);
            pair=write(root.resolve("fixture-pair.json"),"{\"fixture\":\"pair\"}");
            receipt=write(root.resolve("fixture-save-receipt.json"),"{\"fixture\":\"canonical-save\"}");
            driver=write(root.resolve("fixture-driver.json"),"{\"fixture\":\"driver\"}");
            EpisodeWindowAuthority windows=new EpisodeWindowAuthority(new EpisodeWindowAuthority.Verifier(){
                @Override public String requireBegin(Head actual,EpisodeWindow.Begin requested)throws IOException{
                    writer.requireSession(writer.borrowedSession());assertEquals(actual.digest(),writer.borrowedSession().head().digest());
                    assertEquals(begin,requested);validations.incrementAndGet();
                    if(mutateOnValidation.compareAndSet(true,false))Files.writeString(Path.of(driver.path()),"changed during actual same-lock revalidation");
                    return ContinuityJson.digest(requested.toJson());
                }
                @Override public String requireBaseline(Head actual,EpisodeWindow.Baseline requested)throws IOException{
                    writer.requireSession(writer.borrowedSession());assertEquals(actual.digest(),writer.borrowedSession().head().digest());
                    if(!firstSaveConfirmed.get())throw new IOException("fixture has no confirmed first SAVE custody");
                    writer.borrowedSession().requireEpisodeWindowBegin(requested.begin());
                    StrictJson.require(requested.pairRef().equals(pair)&&requested.canonicalSaveReceiptRef().equals(receipt),"actual fixture originals differ");
                    validations.incrementAndGet();return requested.proofDigest();
                }
            });
            authority=new TransitionAuthority(){
                @Override public String revalidate(ContinuityState before,Request request){throw new AssertionError("must receive actual full Head");}
                @Override public String revalidate(Head before,Request request)throws IOException{
                    return EpisodeWindow.isTransition(request.kind())?windows.revalidate(before,request):ContinuityJson.digest(request.detailsObject());
                }
                @Override public ContinuityState reduce(ContinuityState before,Request request){
                    if(EpisodeWindow.isTransition(request.kind()))return windows.reduce(before,request);
                    if("fixture.lifecycle".equals(request.kind())){
                        ObjectNode next=before.toJson();next.put("fixture_lifecycle",StrictJson.text(request.detailsObject().get("evidence_id")));
                        return ContinuityState.fromJson(next,before.machineId());
                    }
                    return OriginalWindowReducer.reduce(before,request);
                }
            };
            writer=newWriter(WriterFaultProbe.NONE);
            Request lifecycle=marker("fixture.lifecycle","actual-temporary-lifecycle");
            Receipt committed=writer.commit(writer.preview(lifecycle));
            ExactRef lifecycleRef=LedgerFiles.read(files.layout.event(committed.head().sequence()),65_536).pin().reference();
            begin=new EpisodeWindow.Begin("next-1",identity(123,"133000000000000001","old-session","old-episode",0,42,1000),
                    identity(456,"133000000000000002","new-session","new-episode",1,43,500),1,2,"parent-next-1",committed.head().sequence(),
                    committed.eventIdentity(),lifecycleRef,driver,List.of());
        }
        ContinuityWriter newWriter(WriterFaultProbe faults)throws IOException{
            if(files.storage.hasUnknownWrite())files.storage.reconcileStorageOnly();
            return new ContinuityWriter(layout, List.of(LedgerFiles.read(files.source,65_536).pin().reference()), authority, Clock.systemUTC(), ContinuityWriter.Extensions.none(), StorageWriteGuardTestSupport.forLayout(layout), faults);
        }
        EpisodeWindow.CommittedBegin begin()throws IOException{return writer.locked(session->session.beginEpisodeWindow(begin));}
        EpisodeWindow.Baseline baseline(EpisodeWindow.CommittedBegin committed){
            return new EpisodeWindow.Baseline(committed,"first-save-only-once",pair,pair.sha256(),receipt,"a".repeat(64),begin.after());
        }
    }
    private static ExactRef write(Path path,String body)throws IOException{Files.writeString(path,body);return LedgerFiles.read(path,65_536).pin().reference();}
    private static EpisodeWindow.Identity identity(long pid,String born,String session,String episode,long epoch,long actor,long date){
        ObjectNode game=StrictJson.object();game.put("pid",pid);game.put("creation_filetime",born);
        return new EpisodeWindow.Identity(WriterFixture.MACHINE,GameGeneration.fromJson(game),session,episode,epoch,actor,date);
    }
    private static Request marker(String kind,String evidence){ObjectNode row=StrictJson.object();row.put("source","actual-software-fixture");row.put("evidence_id",evidence);return new Request(kind,ContinuityJson.canonical(row),List.of());}

    @Test void typedProducerAndAllWindowEnvelopesRoundTripWithoutLosingNativeIdentity()throws Exception{
        Fixture f=new Fixture(temporary.resolve("roundtrip"));var begin=f.begin();var baseline=f.baseline(begin);
        assertEquals(f.begin,EpisodeWindow.Begin.fromJson(f.begin.toJson()));
        assertEquals(begin,EpisodeWindow.CommittedBegin.fromJson(begin.toJson()));
        assertEquals(baseline,EpisodeWindow.Baseline.fromJson(baseline.toJson()));
        assertEquals(f.begin.request().identity(),EpisodeWindow.begin(f.begin.request()).request().identity());
        f.firstSaveConfirmed.set(true);var active=f.writer.locked(s->s.baselineEpisodeWindow(baseline));
        assertEquals(active,EpisodeWindow.CommittedBaseline.fromJson(active.toJson()));
        assertEquals("133000000000000002",active.baseline().savedIdentity().toJson().path("game").path("creation_filetime").textValue());
    }
    @Test void missingNullWrongFieldsAndEqualNumericWrongTypesFailClosed()throws Exception{
        Fixture f=new Fixture(temporary.resolve("invalid"));ObjectNode encoded=f.begin.toJson();
        ObjectNode missing=encoded.deepCopy();missing.remove("evidence");assertThrows(ContractViolationException.class,()->EpisodeWindow.Begin.fromJson(missing));
        ObjectNode nullable=encoded.deepCopy();nullable.putNull("evidence");assertThrows(ContractViolationException.class,()->EpisodeWindow.Begin.fromJson(nullable));
        ObjectNode alias=encoded.deepCopy();alias.put("window_id",2);assertThrows(ContractViolationException.class,()->EpisodeWindow.Begin.fromJson(alias));
        for(var wrong:List.of(StrictJson.object().put("x",true).get("x"),StrictJson.object().put("x",2.0).get("x"))){
            ObjectNode bad=encoded.deepCopy();bad.set("new_window_id",wrong);assertThrows(ContractViolationException.class,()->EpisodeWindow.Begin.fromJson(bad));
        }
        ObjectNode badIdentity=f.begin.after().toJson();((ObjectNode)badIdentity.get("game")).put("creation_filetime",133000000000000002L);
        assertThrows(ContractViolationException.class,()->EpisodeWindow.Identity.fromJson(badIdentity));
    }
    @Test void awaitingCannotAdvanceAndActiveStartsAtTheActualFirstPairWithoutErasingUnknown()throws Exception{
        Fixture f=new Fixture(temporary.resolve("active"));var begin=f.begin();
        Head waiting=f.writer.locked(ContinuityStorePort.Session::head);assertEquals(ContinuityState.Status.AWAITING_FIRST_SAVE,waiting.state().status());
        assertEquals(1,waiting.state().origin().windowId());
        assertThrows(ContractViolationException.class,()->f.writer.preview(WriterFixture.settled("cannot-advance",1001,2)));
        assertThrows(IOException.class,()->f.writer.locked(s->s.baselineEpisodeWindow(f.baseline(begin))));
        assertFalse(Files.exists(f.files.layout.event(3)));f.firstSaveConfirmed.set(true);
        var active=f.writer.locked(s->s.baselineEpisodeWindow(f.baseline(begin)));Head actual=f.writer.locked(ContinuityStorePort.Session::head);
        assertEquals(2,actual.state().origin().windowId());assertEquals(500,actual.state().origin().startDateRaw());assertEquals(0,actual.state().settledCycles());
        assertEquals(WriterFixture.state().get("pending_cycle"),actual.state().toJson().get("pending_cycle"));
        assertEquals(WriterFixture.state().get("NEXT"),actual.state().toJson().get("NEXT"));
        assertTrue(actual.state().toJson().has("unknown_actions"));assertTrue(actual.state().toJson().get("unknown_actions").isNull());
        assertEquals("UNKNOWN",actual.state().toJson().path("unknown_requests").path("original_request").textValue());
        assertFalse(actual.state().toJson().has("pending_checkpoint"));
        f.writer.locked(s->{s.requireEpisodeWindowBegin(begin);s.requireEpisodeWindowActive(active);return null;});
    }
    @Test void samePairDuplicateOnlyReadsItsCommittedEventAndNeverCreatesASecondSaveOrEvent()throws Exception{
        Fixture f=new Fixture(temporary.resolve("duplicate"));var begin=f.begin();f.firstSaveConfirmed.set(true);var baseline=f.baseline(begin);
        var active=f.writer.locked(s->s.baselineEpisodeWindow(baseline));
        byte[] snapshot=Files.readAllBytes(f.files.layout.snapshot());var duplicate=f.writer.locked(s->s.baselineEpisodeWindow(baseline));
        assertEquals(active,duplicate);assertArrayEquals(snapshot,Files.readAllBytes(f.files.layout.snapshot()));assertFalse(Files.exists(f.files.layout.event(4)));
        ExactRef another=write(temporary.resolve("different-pair.json"),"{\"fixture\":\"different pair\"}");
        var changed=new EpisodeWindow.Baseline(begin,baseline.saveActionId(),another,another.sha256(),baseline.canonicalSaveReceiptRef(),baseline.proofDigest(),baseline.savedIdentity());
        assertThrows(Exception.class,()->f.writer.locked(s->s.baselineEpisodeWindow(changed)));assertFalse(Files.exists(f.files.layout.event(4)));
    }
    @Test void realEventPublishedCrashRecoversItsExactBaselineRatherThanSubmittingAnotherSave()throws Exception{
        Fixture f=new Fixture(temporary.resolve("crash"));var begin=f.begin();var baseline=f.baseline(begin);f.firstSaveConfirmed.set(true);
        f.writer=f.newWriter((boundary,sequence)->{if(boundary==WriterFaultProbe.Boundary.EVENT_PUBLISHED&&sequence==3)throw new IOException("actual event was durably written; injected crash");});
        assertThrows(CommitUncertainException.class,()->f.writer.locked(s->s.baselineEpisodeWindow(baseline)));
        assertTrue(Files.exists(f.files.layout.event(3)));f.writer=f.newWriter(WriterFaultProbe.NONE);
        var restored=f.writer.locked(s->s.baselineEpisodeWindow(baseline));
        assertEquals(3,restored.sequence());assertFalse(f.writer.locked(ContinuityStorePort.Session::head).snapshotNeedsRecovery());
        assertFalse(Files.exists(f.files.layout.event(4)));
    }
    @Test void wholeReducerRejectsAResetOrHiddenUnknownMutationEvenWhenEnvelopeHashesMatch()throws Exception{
        Fixture f=new Fixture(temporary.resolve("tamper"));var begin=f.begin();f.firstSaveConfirmed.set(true);f.writer.locked(s->s.baselineEpisodeWindow(f.baseline(begin)));
        ObjectNode event=ContinuityJson.parseObject(Files.readAllBytes(f.files.layout.event(3)),ContinuityJson.DOCUMENT_MAX_BYTES);
        ObjectNode after=(ObjectNode)event.get("after");after.remove("pending_cycle");
        Files.write(f.files.layout.event(3),ContinuityJson.canonical(event));Files.write(f.files.layout.snapshot(),ContinuityJson.canonical(after));
        assertThrows(ContractViolationException.class,()->f.writer.locked(ContinuityStorePort.Session::head));
    }
    @Test void sameBytesReplacementCannotStandInForTheOriginalBeginFileIdentity()throws Exception{
        Fixture f=new Fixture(temporary.resolve("file-id"));var begin=f.begin();
        Path event=Path.of(begin.eventRef().path()),old=event.resolveSibling("retained-original-begin.json");
        Files.move(event,old);Files.write(event,Files.readAllBytes(old));
        f.writer.locked(s->{assertThrows(ContractViolationException.class,()->s.requireEpisodeWindowBegin(begin));return null;});
    }
    @Test void revalidationSourceDriftAndAnUnresolvedSecondBeginCannotWrite()throws Exception{
        Fixture f=new Fixture(temporary.resolve("drift"));f.mutateOnValidation.set(true);
        assertThrows(Exception.class,f::begin);assertFalse(Files.exists(f.files.layout.event(2)));
        Fixture other=new Fixture(temporary.resolve("unresolved"));other.begin();
        var again=new EpisodeWindow.Begin("again",other.begin.after(),identity(789,"133000000000000003","third-session","third-episode",2,44,300),
                2,3,"next-parent-2",1,other.begin.lifecycleEventIdentity(),other.begin.lifecycleEventRef(),other.driver,List.of());
        assertThrows(ContractViolationException.class,()->EpisodeWindow.reduce(other.writer.locked(ContinuityStorePort.Session::head).state(),again.request()));
        assertFalse(Files.exists(other.files.layout.event(3)));
    }
    @Test void activeAncestrySurvivesLaterLegitimateProgressWithoutChangingItsFirstPair()throws Exception{
        Fixture f=new Fixture(temporary.resolve("later"));var begin=f.begin();f.firstSaveConfirmed.set(true);var active=f.writer.locked(s->s.baselineEpisodeWindow(f.baseline(begin)));
        f.writer.commit(f.writer.preview(WriterFixture.settled("actual-later-batch",524,1)));
        byte[] snapshot=Files.readAllBytes(f.files.layout.snapshot());int calls=f.validations.get();
        f.writer.locked(s->{s.requireEpisodeWindowBegin(begin);s.requireEpisodeWindowActive(active);return null;});
        assertEquals(calls,f.validations.get(),"read-only ancestry cannot invoke live private custody callbacks");
        assertArrayEquals(snapshot,Files.readAllBytes(f.files.layout.snapshot()));assertFalse(Files.exists(f.files.layout.event(5)));
    }
    @Test void olderWindowBaselineRemainsHistoricalKnowledgeButCannotGrantCurrentActiveEligibility()throws Exception{
        Fixture f=new Fixture(temporary.resolve("historical-old"));var firstBegin=f.begin();f.firstSaveConfirmed.set(true);
        var first=f.writer.locked(s->s.baselineEpisodeWindow(f.baseline(firstBegin)));
        Receipt nextLifecycle=f.writer.commit(f.writer.preview(marker("fixture.lifecycle","actual-next-temporary-lifecycle")));
        ExactRef lifecycle=LedgerFiles.read(f.files.layout.event(nextLifecycle.head().sequence()),65_536).pin().reference();
        f.begin=new EpisodeWindow.Begin("next-2",f.begin.after(),identity(789,"133000000000000003","third-session","third-episode",2,44,300),
                2,3,"parent-next-2",nextLifecycle.head().sequence(),nextLifecycle.eventIdentity(),lifecycle,f.driver,List.of());
        f.begin();byte[] snapshot=Files.readAllBytes(f.files.layout.snapshot());int calls=f.validations.get();
        f.writer.locked(s->{
            s.requireHistoricalEpisodeWindowBaseline(first);
            assertThrows(ContractViolationException.class,()->s.requireEpisodeWindowBegin(firstBegin));
            assertThrows(ContractViolationException.class,()->s.requireEpisodeWindowActive(first));return null;
        });
        assertEquals(calls,f.validations.get());assertArrayEquals(snapshot,Files.readAllBytes(f.files.layout.snapshot()));
        assertFalse(Files.exists(f.files.layout.event(6)));
    }
    @Test void generalCanonicalHeadReaderRejectsReplacementOfTheBeginPinAlreadyRetainedByBaseline()throws Exception{
        Fixture f=new Fixture(temporary.resolve("general-head-file-id"));var begin=f.begin();f.firstSaveConfirmed.set(true);
        f.writer.locked(s->s.baselineEpisodeWindow(f.baseline(begin)));
        Path event=Path.of(begin.eventRef().path()),original=event.resolveSibling("original-before-replacement.json");
        Files.move(event,original);Files.write(event,Files.readAllBytes(original));
        assertThrows(ContractViolationException.class,()->f.writer.locked(ContinuityStorePort.Session::head));
        assertFalse(Files.exists(f.files.layout.event(4)));
    }
}
