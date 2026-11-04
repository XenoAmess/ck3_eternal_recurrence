package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.AbstractList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.continuity.writer.WriterContracts.Request;

/** Pure production core DATA. Synthetic references confer no file, writer, SAVE or Game authority. */
final class HistoryBoundedEpisodeAncestryTest {
    private static final String MACHINE="fixture-machine";
    private static final String UTC="2026-10-24T00:00:00Z";

    private record Chain(ContinuityState anchor,ContinuityEvent lifecycle,ContinuityEvent beginEvent,
                         ContinuityEvent baselineEvent,EpisodeWindow.Begin begin,Pin beginPin,List<byte[]> documents) { }

    private static String sha(byte[] raw) {
        try {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
        catch(NoSuchAlgorithmException impossible) {throw new AssertionError(impossible);}
    }
    private static ExactRef literalRef(String name,char digest) {
        return new ExactRef("/fixture-only/"+name,1,String.valueOf(digest).repeat(64));
    }
    private static ExactRef exactRef(String name,byte[] raw) {
        return new ExactRef("/fixture-only/"+name,raw.length,sha(raw));
    }
    private static GameGeneration game(long pid,String birth) {
        ObjectNode value=StrictJson.object();value.put("pid",pid);value.put("creation_filetime",birth);
        return GameGeneration.fromJson(value);
    }
    private static ContinuityState anchor() {
        ObjectNode row=StrictJson.object();
        row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",MACHINE);row.put("sequence",0);
        row.put("window_id",1);row.put("status","running");row.put("target_days",10958);
        row.put("start_date_raw",1000);row.put("target_date_raw",1000+10958*24);
        row.put("last_settled_cycles",4);row.put("last_settled_date_raw",1000);
        row.set("game_binding",game(123,"133000000000000001").toJson());
        row.putObject("pending_cycle").put("stage","auto_unsettled").put("sequence",5);
        row.putNull("unknown_actions");row.putObject("unknown_requests").put("original_request","UNKNOWN");row.put("NEXT",6);
        return ContinuityState.fromJson(row,MACHINE);
    }
    /** Only creates input envelopes; all reduction/envelope checks run in the real production classes. */
    private static ContinuityEvent event(ContinuityState previous,Request request,ContinuityState reduced) {
        long sequence=previous.sequence()+1;
        ObjectNode after=reduced.toJson();after.put("sequence",sequence);after.put("last_event_identity",request.identity());
        var input=new ContinuityEvent(sequence,UTC,request.kind(),request.details(),request.identity(),
                ContinuityJson.digest(previous.toJson()),ContinuityState.fromJson(after,MACHINE));
        return ContinuityEvent.fromJson(input.toJson(),previous);
    }
    private static byte[] raw(ContinuityEvent event) {return ContinuityJson.canonical(event.toJson());}
    private static List<byte[]> changingDocuments(List<byte[]> originals,byte[] replacement,AtomicInteger beginReads) {
        return new AbstractList<>() {
            @Override public byte[] get(int index) {
                if(index==1)return beginReads.incrementAndGet()==1?originals.get(index):replacement;
                return originals.get(index);
            }
            @Override public int size() {return originals.size();}
        };
    }
    private static EpisodeWindow.Baseline baseline(EpisodeWindow.CommittedBegin begin) {
        return new EpisodeWindow.Baseline(begin,"fixture-first-save",literalRef("pair.json",'4'),"4".repeat(64),
                literalRef("first-save-receipt.json",'5'),"a".repeat(64),begin.begin().after());
    }
    private static Chain chain() {
        ContinuityState anchor=anchor();
        ObjectNode details=StrictJson.object();details.put("evidence_id","fixture-lifecycle");details.put("source","explicit-lifecycle-DATA");
        Request lifecycleRequest=new Request("fixture.lifecycle",ContinuityJson.canonical(details),List.of());
        ObjectNode marked=anchor.toJson();marked.put("fixture_marker","original-lifecycle");
        ContinuityEvent lifecycle=event(anchor,lifecycleRequest,ContinuityState.fromJson(marked,MACHINE));
        byte[] lifecycleRaw=raw(lifecycle);
        var before=new EpisodeWindow.Identity(MACHINE,game(123,"133000000000000001"),"old-session","old-episode",0,42,1000);
        var after=new EpisodeWindow.Identity(MACHINE,game(456,"133000000000000002"),"new-session","new-episode",1,43,500);
        var begin=new EpisodeWindow.Begin("fixture-BEGIN",before,after,1,2,"fixture-parent",lifecycle.sequence(),
                lifecycle.identity(),exactRef("lifecycle.json",lifecycleRaw),literalRef("adopted-driver.json",'2'),List.of());
        ContinuityEvent beginEvent=event(lifecycle.after(),begin.request(),EpisodeWindow.reduce(lifecycle.after(),begin.request()));
        byte[] beginRaw=raw(beginEvent);
        ExactRef beginRef=exactRef("begin-event.json",beginRaw);
        Pin beginPin=new Pin(beginRef,new FileIdentity("1","9007199254740993","133000000000000001",UTC,beginRef.bytes()));
        var committed=new EpisodeWindow.CommittedBegin(begin,beginEvent.sequence(),beginEvent.identity(),
                ContinuityJson.digest(beginEvent.after().toJson()),beginPin);
        EpisodeWindow.Baseline baseline=baseline(committed);
        ContinuityEvent baselineEvent=event(beginEvent.after(),baseline.request(),EpisodeWindow.reduce(beginEvent.after(),baseline.request()));
        return new Chain(anchor,lifecycle,beginEvent,baselineEvent,begin,beginPin,List.of(lifecycleRaw,beginRaw,raw(baselineEvent)));
    }

    @Test void boundedProjectionMatchesOriginalEpisodeAncestryAndSnapshotRecovery() {
        Chain fixture=chain();List<byte[]> originals=fixture.documents().stream().map(byte[]::clone).toList();
        for(ContinuityState snapshot:List.of(fixture.anchor(),fixture.beginEvent().after(),fixture.baselineEvent().after())) {
            var old=ContinuityHistory.preview(fixture.anchor(),snapshot,fixture.documents());
            var bounded=ContinuityHistory.previewBounded(fixture.anchor(),snapshot,fixture.documents());
            assertArrayEquals(old.head().canonicalBytes(),bounded.head().canonicalBytes());
            assertEquals(old.headDigest(),ContinuityJson.digest(bounded.head().toJson()));
            assertEquals(snapshot.sequence()!=3,old.snapshotNeedsRecovery());
            assertEquals(old.snapshotNeedsRecovery(),bounded.snapshotNeedsRecovery());assertEquals(0,old.ledgerWrites());
            assertEquals(3,old.events().size());assertEquals(3,bounded.events().size());
            for(int index=0;index<3;index++) {
                ContinuityEvent expected=old.events().get(index);var actual=bounded.events().get(index);
                assertEquals(expected.sequence(),actual.sequence());assertEquals(expected.identity(),actual.identity());
                assertEquals(expected.sourceKey(),actual.sourceKey());
                assertEquals(index==2?Optional.of(fixture.beginPin()):Optional.empty(),actual.baselineBeginPin());
                assertArrayEquals(originals.get(index),fixture.documents().get(index));
            }
        }
        assertEquals(EpisodeWindow.Phase.ACTIVE,EpisodeWindow.state(fixture.baselineEvent().after()).orElseThrow().phase());
        System.out.println("SOFTWARE_EPISODE_HISTORY snapshots=3 events=3 old_new_full_head_equal=true exact_begin_pin=true no_input_mutation=true");
    }

    @Test void absentEarlierLifecycleAndWrongCommittedBeginHeadDigestAreRejected() {
        Chain fixture=chain();
        // Confirm the full original fixture before introducing either particular ancestry failure.
        assertEquals(3,ContinuityHistory.previewBounded(fixture.anchor(),fixture.anchor(),fixture.documents()).events().size());
        ContinuityState laterAnchor=fixture.lifecycle().after();
        List<byte[]> withoutLifecycle=List.of(fixture.documents().get(1),fixture.documents().get(2));
        ContinuityEvent.fromJson(fixture.beginEvent().toJson(),laterAnchor);
        var missingOld=assertThrows(ContractViolationException.class,()->ContinuityHistory.preview(laterAnchor,laterAnchor,withoutLifecycle));
        var missingNew=assertThrows(ContractViolationException.class,()->ContinuityHistory.previewBounded(laterAnchor,laterAnchor,withoutLifecycle));
        assertTrue(missingOld.getMessage().contains("must remain in the finite chain"));
        assertTrue(missingNew.getMessage().contains("must remain in the finite chain"));

        String actualDigest=ContinuityJson.digest(fixture.beginEvent().after().toJson());
        String wrongDigest=(actualDigest.charAt(0)=='0'?"1":"0")+actualDigest.substring(1);
        assertNotEquals(actualDigest,wrongDigest);
        var wrongBegin=new EpisodeWindow.CommittedBegin(fixture.begin(),2,fixture.beginEvent().identity(),wrongDigest,fixture.beginPin());
        EpisodeWindow.Baseline wrongBaseline=baseline(wrongBegin);
        // Rebuild the complete reducer result/identity/envelope, so rejection cannot be an invalid event shortcut.
        ContinuityEvent wrongEvent=event(fixture.beginEvent().after(),wrongBaseline.request(),
                EpisodeWindow.reduce(fixture.beginEvent().after(),wrongBaseline.request()));
        assertNotEquals(fixture.baselineEvent().identity(),wrongEvent.identity());
        List<byte[]> wrongDocuments=List.of(fixture.documents().get(0),fixture.documents().get(1),raw(wrongEvent));
        var headOld=assertThrows(ContractViolationException.class,()->ContinuityHistory.preview(fixture.anchor(),fixture.anchor(),wrongDocuments));
        var headNew=assertThrows(ContractViolationException.class,()->ContinuityHistory.previewBounded(fixture.anchor(),fixture.anchor(),wrongDocuments));
        assertTrue(headOld.getMessage().contains("exact actual earlier BEGIN state/details"));
        assertTrue(headNew.getMessage().contains("exact actual earlier BEGIN state/details"));
        System.out.println("SOFTWARE_EPISODE_ANCESTRY missing_earlier_original_rejected=true wrong_begin_head_rejected=true valid_envelopes=true");
    }

    @Test void changedLazyBeginOriginalFailsItsFirstValidatedFingerprint() {
        Chain fixture=chain();
        assertEquals(3,ContinuityHistory.previewBounded(fixture.anchor(),fixture.anchor(),fixture.documents()).events().size());
        ObjectNode changed=fixture.beginEvent().toJson();changed.put("at_utc","2026-10-24T00:00:01Z");
        byte[] replacement=ContinuityJson.canonical(changed);byte[] original=fixture.documents().get(1);
        assertEquals(original.length,replacement.length);assertNotEquals(sha(original),sha(replacement));
        ContinuityEvent independentlyValid=ContinuityEvent.fromJson(changed,fixture.lifecycle().after());
        assertEquals(fixture.beginEvent().identity(),independentlyValid.identity());
        var beginReads=new AtomicInteger();
        List<byte[]> changing=changingDocuments(fixture.documents(),replacement,beginReads);
        var delivered=new AtomicReference<ContinuityHistory.BoundedPreview>();
        var failure=assertThrows(ContractViolationException.class,()->delivered.set(
                ContinuityHistory.previewBounded(fixture.anchor(),fixture.anchor(),changing)));
        assertEquals(2,beginReads.get());assertNull(delivered.get());
        assertTrue(failure.getMessage().contains("changed after their original validation"));
        assertArrayEquals(original,fixture.documents().get(1));

        // A verifier comparing only the later reread to this replacement ref would accept.
        // The immutable replacement chain is legal; a first-seen different original must remain authoritative.
        Pin replacementPin=new Pin(exactRef("begin-event.json",replacement),fixture.beginPin().identity());
        var replacementBegin=new EpisodeWindow.CommittedBegin(fixture.begin(),2,fixture.beginEvent().identity(),
                ContinuityJson.digest(fixture.beginEvent().after().toJson()),replacementPin);
        EpisodeWindow.Baseline replacementBaseline=baseline(replacementBegin);
        ContinuityEvent replacementBaselineEvent=event(fixture.beginEvent().after(),replacementBaseline.request(),
                EpisodeWindow.reduce(fixture.beginEvent().after(),replacementBaseline.request()));
        byte[] baselineRaw=raw(replacementBaselineEvent);
        List<byte[]> immutableReplacement=List.of(fixture.documents().get(0),replacement,baselineRaw);
        var oldControl=ContinuityHistory.preview(fixture.anchor(),fixture.anchor(),immutableReplacement);
        var newControl=ContinuityHistory.previewBounded(fixture.anchor(),fixture.anchor(),immutableReplacement);
        assertArrayEquals(oldControl.head().canonicalBytes(),newControl.head().canonicalBytes());
        assertEquals(Optional.of(replacementPin),newControl.events().get(2).baselineBeginPin());
        List<byte[]> firstDifferent=List.of(fixture.documents().get(0),original,baselineRaw);
        var oldFirstReads=new AtomicInteger();var newFirstReads=new AtomicInteger();
        var oldFirstFailure=assertThrows(ContractViolationException.class,()->ContinuityHistory.preview(fixture.anchor(),fixture.anchor(),
                changingDocuments(firstDifferent,replacement,oldFirstReads)));
        var firstDelivered=new AtomicReference<ContinuityHistory.BoundedPreview>();
        var newFirstFailure=assertThrows(ContractViolationException.class,()->firstDelivered.set(ContinuityHistory.previewBounded(
                fixture.anchor(),fixture.anchor(),changingDocuments(firstDifferent,replacement,newFirstReads))));
        assertEquals(1,oldFirstReads.get());assertEquals(1,newFirstReads.get());assertNull(firstDelivered.get());
        assertTrue(oldFirstFailure.getMessage().contains("reference differs from its exact actual original bytes"));
        assertTrue(newFirstFailure.getMessage().contains("reference differs from its exact actual original bytes"));
        System.out.println("SOFTWARE_EPISODE_FINGERPRINT reread_begin_reads=2 first_original_begin_reads=1 immutable_replacement_control=true original_fingerprints_rejected=true results_delivered=false");
    }
}
