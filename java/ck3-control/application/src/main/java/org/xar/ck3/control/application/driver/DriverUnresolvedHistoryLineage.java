package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer;
import java.nio.file.Path;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Exact history-only suffix for one unresolved original. This grants no frame, effect, retry or Ready. */
final class DriverUnresolvedHistoryLineage {
    private DriverUnresolvedHistoryLineage(){ }
    record Verified(ActionReceipt action,ExactRef before,ExactRef after,List<ExactRef> events,
            WriterContracts.Head target,long version,long epoch) { }
    private record Event(long sequence,WriterContracts.Pin pin,ObjectNode body) { }
    private static final Set<String> DETAILS=Set.of("schema","evidence_id","token","source","predecessor_head_sha256","read_head_sha256","read_head_sequence",
            "before_version","after_version","episode_epoch","before_driver","after_driver","read_rows");

    static Verified verify(Session same,ActionReceipt action,ExactRef originalDriver,ExactRef targetDriver,
            WriterContracts.Head requestedTarget,OutcomeArchive bound,RootReadContractCatalog catalog,
            DriverReturnedControlHistoryRowProducer.Source returnedSource,DriverReturnedActionHistoryRowProducer.Source returnedActionSource)throws IOException {
        requireUnknown(action);var opening=same.head();
        var target=same.requireHistoricalHead(requestedTarget.state().sequence(),requestedTarget.digest());
        StrictJson.require(target.digest().equals(requestedTarget.digest())&&target.state().toJson().equals(requestedTarget.state().toJson()),"unresolved history target is not its actual canonical Head");
        var record=ContinuityActionJournal.requireHistoricalReceipt(target.state(),action,bound);
        StrictJson.require(bound.loadRecord(record).receipt().equals(action)&&bound.loadReceipt(bound.receiptReferenceOf(action)).equals(action),"unresolved original lost canonical receipt/record custody");
        var attempt=((ActionState.Unknown)action.state()).attempt().orElseThrow();
        var named=RootGuardEvidence.originalDriverSource(attempt.guard(),bound);
        StrictJson.require(named.driverRef().equals(originalDriver),"unresolved history starts at another original Driver");
        var basis=RootGuardEvidence.frameBasis(attempt.guard(),bound);var manifest=bound.loadFullMaterial(basis.driverFacts());
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(),manifest,bound.loadNativeFrame(basis.nativeFrame()));
        var facts=DriverObservationEvidenceReader.decode(basis.driverFacts(),manifest,bound.loadFullMaterial(originalDriver),nativeFrame);
        StrictJson.require(facts.transport().game().equals(action.command().before().game())&&facts.source().equals(action.command().source())
                &&facts.transport().sessionId().equals(action.command().sessionId()),"unresolved predecessor crossed original Game/source/session");
        var all=events(same,target);var selected=new ArrayList<Event>();ExactRef cursor=targetDriver;
        long maximum=target.state().sequence();long nextVersion=-1;long epoch=facts.episodeEpoch();
        while(!cursor.equals(originalDriver)){
            ExactRef wanted=cursor;long limit=maximum;
            var matches=all.stream().filter(e->e.sequence()<=limit&&WriterContracts.DRIVER_READ_HISTORY_KIND.equals(StrictJson.text(e.body().get("kind")))
                    &&ExactRef.fromJson(e.body().get("details").get("after_driver")).equals(wanted)).toList();
            StrictJson.require(matches.size()==1&&selected.size()<128,"no unique finite canonical unresolved history predecessor");
            var event=matches.getFirst();var details=StrictJson.object(event.body().get("details"),DETAILS);
            StrictJson.require("xar.driver-read-publication/v1".equals(StrictJson.text(details.get("schema")))
                    &&details.get("source").equals(ProposalLifecycleCodec.source(action.command().source()))
                    &&StrictJson.integer(details.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER)==epoch,"unresolved history source/epoch changed");
            long beforeVersion=StrictJson.integer(details.get("before_version"),0,StrictJson.MAX_SAFE_INTEGER),afterVersion=StrictJson.integer(details.get("after_version"),1,StrictJson.MAX_SAFE_INTEGER);
            StrictJson.require(afterVersion==Math.addExact(beforeVersion,1)&&(nextVersion<0||afterVersion==nextVersion),"unresolved history has an unproved Driver version gap");nextVersion=beforeVersion;
            var before=ExactRef.fromJson(details.get("before_driver"));replayRows(same,event,details,action,originalDriver,basis.nativeFrame(),before,cursor,bound,catalog,returnedSource,returnedActionSource);
            selected.add(event);cursor=before;maximum=event.sequence()-1;
        }
        StrictJson.require(!selected.isEmpty()&&nextVersion==facts.driverVersion(),"unresolved current Driver needs a real history-only suffix from the original version");
        selected.sort(Comparator.comparingLong(Event::sequence));
        long start=selected.getFirst().sequence()-1;
        StrictJson.require(target.state().sequence()-start<=512,"unresolved history canonical interval exceeded its finite bound");
        var first=selected.getFirst().body();String startDigest=StrictJson.text(first.get("previous_sha256"));
        var state=same.requireHistoricalState(start,startDigest);long expected=start+1;
        for(var event:all)if(event.sequence()>start){
            StrictJson.require(event.sequence()==expected++&&StrictJson.text(event.body().get("previous_sha256")).equals(ContinuityJson.digest(state.toJson())),"unresolved interval skipped a canonical event");
            var after=ContinuityState.fromJson(event.body().get("after"),target.state().machineId());
            StrictJson.require(after.sequence()==event.sequence()&&StrictJson.text(after.toJson().get("last_event_identity")).equals(StrictJson.text(event.body().get("identity"))),"unresolved canonical event envelope differs");
            if(selected.contains(event))requireOnly(state,after,WriterContracts.DRIVER_READ_HISTORY_FIELD);
            else requireSameActionTransition(state,after,event,action,bound);
            same.requireHistoricalState(after.sequence(),ContinuityJson.digest(after.toJson()));state=after;
        }
        StrictJson.require(ContinuityJson.digest(state.toJson()).equals(target.digest())&&same.head().digest().equals(opening.digest()),"unresolved target or actual writer changed during read-only verification");
        long afterVersion=StrictJson.integer(selected.getLast().body().get("details").get("after_version"),1,StrictJson.MAX_SAFE_INTEGER);
        return new Verified(action,originalDriver,targetDriver,all.stream().filter(e->e.sequence()>start).map(e->e.pin().reference()).toList(),target,afterVersion,epoch);
    }
    private static void requireUnknown(ActionReceipt action){
        Objects.requireNonNull(action);StrictJson.require(!action.settled()&&action.state() instanceof ActionState.Unknown
                &&((ActionState.Unknown)action.state()).attempt().isPresent(),"actual original unresolved native attempt required");
    }
    private static void requireSameOriginal(ActionReceipt expected,ActionReceipt actual){
        requireUnknown(actual);requireUnknown(expected);var a=(ActionState.Unknown)expected.state();var b=(ActionState.Unknown)actual.state();
        StrictJson.require(actual.command().equals(expected.command())&&actual.bodySha256().equals(expected.bodySha256())
                &&a.attempt().equals(b.attempt())&&a.dispatch().equals(b.dispatch()),"history source names a different unresolved command/attempt/dispatch");
    }
    private static void replayRows(Session same,Event event,ObjectNode details,ActionReceipt action,ExactRef originalDriver,ExactRef originalNative,
            ExactRef beforeRef,ExactRef afterRef,OutcomeArchive bound,RootReadContractCatalog catalog,
            DriverReturnedControlHistoryRowProducer.Source returnedSource,DriverReturnedActionHistoryRowProducer.Source returnedActionSource)throws IOException {
        String predecessor=StrictJson.text(event.body().get("previous_sha256"));long sequence=event.sequence()-1;
        StrictJson.require(StrictJson.text(details.get("predecessor_head_sha256")).equals(predecessor)
                &&StrictJson.text(details.get("read_head_sha256")).equals(predecessor)
                &&StrictJson.integer(details.get("read_head_sequence"),0,StrictJson.MAX_SAFE_INTEGER)==sequence,"unresolved history absorbed another writer head");
        var previous=same.requireHistoricalState(sequence,predecessor);
        var before=DriverStateSnapshot.decodeComplete(material(bound,beforeRef));var appended=new ArrayList<>(before.commandHistory());
        var rows=details.get("read_rows");StrictJson.require(rows!=null&&rows.isArray()&&!rows.isEmpty()&&rows.size()<=128,"finite actual unresolved history rows required");
        for(var value:rows){
            String kind=StrictJson.text(value.get("row_kind"));
            var keys=kind.equals(DriverReadHistoryPublisher.RETURNED_CONTROL_ROW_KIND)?Set.of("row_kind","index","row","before_driver","receipt","record")
                    :kind.equals(DriverReadHistoryPublisher.RETURNED_ACTION_ROW_KIND)||kind.equals(DriverReadHistoryPublisher.EARLY_ROW_KIND)?Set.of("row_kind","index","row","before_driver","original")
                    :Set.of("row_kind","index","row","before_driver","invocation");
            var row=StrictJson.object(value,keys);ExactRef rowRef=ExactRef.fromJson(row.get("row"));
            List<ExactRef> evidence;DriverStateSnapshot.HistoryEntry history;
            if(kind.equals(DriverReadHistoryPublisher.RETURNED_CONTROL_ROW_KIND)){
                StrictJson.require(returnedSource!=null,"actual installed returned-control decoder source missing");
                var decoded=DriverReturnedControlHistoryRowProducer.decode(material(bound,rowRef));var source=decoded.source();
                DriverReturnedControlHistoryRowProducer.replayOriginals(bound,catalog,returnedSource,decoded);
                var actual=bound.loadReceipt(source.canonicalReceipt());requireSameOriginal(action,actual);
                StrictJson.require(ContinuityActionJournal.requireHistoricalReceipt(previous,actual,bound).equals(source.canonicalRecord())
                        &&source.canonicalReceipt().equals(ExactRef.fromJson(row.get("receipt")))&&source.canonicalRecord().equals(ExactRef.fromJson(row.get("record")))
                        &&source.beforeDriver().equals(originalDriver)&&source.beforeDriver().equals(ExactRef.fromJson(row.get("before_driver")))
                        &&source.nativeFrame().equals(originalNative)&&source.headSequence()==sequence&&source.headDigest().equals(predecessor),"returned history source changed canonical receipt/record/original frame/head");
                history=decoded.historyEntry();evidence=source.evidence();
            }else if(kind.equals(DriverReadHistoryPublisher.RETURNED_ACTION_ROW_KIND)){
                StrictJson.require(returnedActionSource!=null,"actual installed returned-action decoder missing");
                var decoded=DriverReturnedActionHistoryRowProducer.decode(material(bound,rowRef));var source=decoded.source();
                DriverReturnedActionHistoryRowProducer.replayOriginals(bound,catalog,returnedActionSource,decoded);
                var actual=bound.loadReceipt(source.canonicalReceipt());requireSameOriginal(action,actual);
                StrictJson.require(ContinuityActionJournal.requireHistoricalReceipt(previous,actual,bound).equals(source.canonicalRecord())
                        &&source.canonicalReceipt().equals(ExactRef.fromJson(row.get("original")))&&source.beforeDriver().equals(originalDriver)
                        &&source.beforeDriver().equals(ExactRef.fromJson(row.get("before_driver")))&&source.nativeFrame().equals(originalNative)
                        &&source.headSequence()==sequence&&source.headDigest().equals(predecessor),"returned Army history lost same actual UNKNOWN/Native/head provenance");
                history=decoded.historyEntry();evidence=source.evidence();
            }else if(kind.equals(DriverReadHistoryPublisher.EARLY_ROW_KIND)){
                var decoded=DriverEarlyExecuteFailureRowProducer.decode(material(bound,rowRef));var source=decoded.source();
                DriverEarlyExecuteFailureRowProducer.replayOriginals(bound,decoded);var cached=(DriverEarlyExecuteFailure.CachedData)source.retained();
                var receipt=source.data().unresolvedAction().orElseThrow(()->new IllegalArgumentException("early cached failure has no actual same UNKNOWN original"));
                var actual=bound.loadReceipt(receipt);requireSameOriginal(action,actual);ContinuityActionJournal.requireHistoricalReceipt(previous,actual,bound);
                var basis=RootGuardEvidence.frameBasis(((ActionState.Unknown)actual.state()).attempt().orElseThrow().guard(),bound);
                StrictJson.require(cached.beforeDriver().equals(originalDriver)&&cached.beforeDriver().equals(ExactRef.fromJson(row.get("before_driver")))
                        &&cached.historicalSource().filter(basis.driverFacts()::equals).isPresent()&&basis.nativeFrame().equals(originalNative)
                        &&source.invocation().equals(ExactRef.fromJson(row.get("original")))&&source.headSequence()==sequence&&source.headDigest().equals(predecessor),"early history cannot substitute missing cached source/current frame authority");
                var manifest=bound.loadFullMaterial(basis.driverFacts());var nativeFrame=DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(),manifest,bound.loadNativeFrame(originalNative));
                var observation=DriverObservationEvidenceReader.decode(basis.driverFacts(),manifest,bound.loadFullMaterial(originalDriver),nativeFrame);
                var known=DriverSnapshotFacts.decodeKnownOriginal(bound.loadFullMaterial(cached.originalKnown()),Optional.of(observation));
                StrictJson.require(known.stamp().driverVersion()==StrictJson.integer(details.get("before_version"),0,StrictJson.MAX_SAFE_INTEGER),"early cached Driver version differs from real history predecessor");
                history=decoded.historyEntry();evidence=source.evidence();
            }else{
                StrictJson.require(kind.equals(DriverReadHistoryPublisher.PUBLIC_FAILURE_ROW_KIND),"unresolved history cannot borrow a READ or unrelated failure row");
                var decoded=DriverPublicExecuteFailureRowProducer.decode(material(bound,rowRef));var source=decoded.source();
                DriverPublicExecuteFailureRowProducer.replayOriginals(bound,decoded);
                var receipt=source.unresolvedAction().orElseThrow(()->new IllegalArgumentException("this original public failure has no actual same-action binding"));
                var actual=bound.loadReceipt(receipt);requireSameOriginal(action,actual);ContinuityActionJournal.requireHistoricalReceipt(previous,actual,bound);
                StrictJson.require(source.beforeDriver().equals(originalDriver)&&source.beforeDriver().equals(ExactRef.fromJson(row.get("before_driver")))
                        &&source.nativeFrame().equals(originalNative)&&source.invocation().equals(ExactRef.fromJson(row.get("invocation")))
                        &&source.headSequence()==sequence&&source.headDigest().equals(predecessor),"public failure history changed its original source/head/pending binding");
                history=decoded.historyEntry();evidence=source.evidence();
            }
            StrictJson.require(history.index()==appended.size()+1L&&history.index()==StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER),"unresolved history row is not its unique contiguous append");
            pin(same,rowRef);for(var ref:evidence)pin(same,ref);appended.add(history);
        }
        var expected=new DriverStateSnapshot.Complete(before.session(),appended,before.lastCheckpoint(),before.rollbackWarFailure(),before.managedRestoreTransaction(),
                before.successionExpectation(),before.successionLifecycle(),before.campaignGoal(),before.rollbackWarFailures());
        StrictJson.require(Arrays.equals(expected.encode(),material(bound,afterRef)),"unresolved history changed a non-history Driver slot or old row");
        var after=ContinuityState.fromJson(event.body().get("after"),previous.machineId());
        StrictJson.require(after.toJson().get(WriterContracts.DRIVER_READ_HISTORY_FIELD).equals(details),"canonical history state lost its actual publication");
        pin(same,beforeRef);pin(same,afterRef);
    }
    private static void requireSameActionTransition(ContinuityState before,ContinuityState after,Event event,ActionReceipt action,OutcomeArchive bound){
        StrictJson.require(ContinuityActionJournal.KIND.equals(StrictJson.text(event.body().get("kind"))),"unresolved interval contains another domain or Driver transition");
        requireOnly(before,after,ContinuityActionJournal.STATE_FIELD);
        var old=ContinuityActionJournal.receipts(before,bound);var now=ContinuityActionJournal.receipts(after,bound);
        StrictJson.require(old.size()==now.size(),"unresolved history interval introduced another action");
        var actual=now.stream().filter(r->r.command().actionId().equals(action.command().actionId())).toList();StrictJson.require(actual.size()==1,"original unresolved action missing from canonical interval");requireSameOriginal(action,actual.getFirst());
        for(var item:old)if(!item.command().actionId().equals(action.command().actionId()))StrictJson.require(now.contains(item),"unresolved interval changed another canonical action");
    }
    private static void requireOnly(ContinuityState before,ContinuityState after,String allowed){
        ObjectNode left=before.toJson(),right=after.toJson();var names=new HashSet<String>();left.fieldNames().forEachRemaining(names::add);right.fieldNames().forEachRemaining(names::add);
        for(var name:names)if(!Set.of("sequence","last_event_identity",allowed).contains(name))StrictJson.require(left.has(name)==right.has(name)&&Objects.equals(left.get(name),right.get(name)),"unresolved suffix changed canonical business state: "+name);
    }
    private static List<Event> events(Session same,WriterContracts.Head head)throws IOException {
        var result=new ArrayList<Event>();
        for(var pin:head.documents()){
            String name=Path.of(pin.reference().path()).getFileName().toString();if(!name.matches("[0-9]{8,16}\\.json"))continue;
            long sequence=Long.parseLong(name.substring(0,name.length()-5));if(sequence>head.state().sequence()||sequence<Math.max(1,head.state().sequence()-511))continue;
            var body=ContinuityJson.parseObject(same.readPinned(pin,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
            StrictJson.object(body,Set.of("sequence","at_utc","kind","details","identity","previous_sha256","after"));
            StrictJson.require(StrictJson.integer(body.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER)==sequence,"canonical unresolved event path/sequence differs");result.add(new Event(sequence,pin,body));
        }
        result.sort(Comparator.comparingLong(Event::sequence));return List.copyOf(result);
    }
    private static byte[] material(OutcomeArchive bound,ExactRef ref){
        byte[] bytes=bound.loadFullMaterial(ref).bytes();StrictJson.require(ref.bytes()==bytes.length&&ref.sha256().equals(DriverJson.sha256(bytes)),"unresolved history original bytes/SHA differ");return bytes;
    }
    private static void pin(Session same,ExactRef ref)throws IOException {var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
}
