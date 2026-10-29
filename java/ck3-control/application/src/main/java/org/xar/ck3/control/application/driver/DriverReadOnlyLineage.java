package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The single read-only Driver lineage replay. It grants no new query, action, effect or budget. */
final class DriverReadOnlyLineage {
    private DriverReadOnlyLineage() { }
    record Verified(Complete query,Complete current,ExactRef queryDriver,ExactRef currentDriver,
            List<ExactRef> events,WriterContracts.Head head,RootGuardEvidence.WriterPoint targetPoint,List<ExactRef> readReceipts) { }
    private record Original(Complete frame,DriverObservationFacts facts,ExactRef driver) { }
    private record Guarded(Original original,RootGuardEvidence.WriterPoint point,ExactRef nativeFrame) { }
    private record Event(long sequence,WriterContracts.Pin pin,ObjectNode body) { }

    static Verified verify(ContinuityStorePort.Session same,GuardEvidence originalGuard,Complete claimedQuery,Known current,
            ActionPorts.OutcomeArchive originals,RootReadContractCatalog catalog) throws IOException {
        Guarded from=guarded(same,originalGuard,claimedQuery,originals);
        var observed=current.observation().orElseThrow(()->new IllegalArgumentException("current actual observed Driver unavailable"));
        ExactRef currentNative=DriverObservationEvidenceReader.reference(current.auxiliary().get("capability_observed_native_source"));
        Original now=load(observed.semanticFactsEvidence(),currentNative,originals);
        StrictJson.require(Arrays.equals(now.facts().driver().encode(),current.driver().encode())
                &&now.facts().driverVersion()==current.stamp().driverVersion()&&now.facts().episodeEpoch()==current.stamp().episodeEpoch()
                &&now.facts().transport().game().equals(current.stamp().game()),
                "read-only extension crossed the actual current full Driver");
        WriterContracts.Head head=same.head();
        var target=new RootGuardEvidence.WriterPoint(head.state().sequence(),head.digest());
        return verifyBetween(same,from,now,currentNative,target,head,originals,catalog);
    }

    /** Both endpoints are actual retained Root guards. No reconstructed Known is treated as the current repository owner. */
    static Verified verifyHistorical(ContinuityStorePort.Session same,GuardEvidence originalGuard,Complete claimedQuery,
            GuardEvidence targetGuard,Complete claimedTarget,ActionPorts.OutcomeArchive originals,RootReadContractCatalog catalog) throws IOException {
        Guarded from=guarded(same,originalGuard,claimedQuery,originals);
        Guarded target=guarded(same,targetGuard,claimedTarget,originals);
        WriterContracts.Head actualHead=same.head();
        StrictJson.require(target.point().sequence()<=actualHead.state().sequence(),"historical READ target is not an actual writer ancestor");
        same.requireHistoricalState(target.point().sequence(),target.point().digest());
        return verifyBetween(same,from,target.original(),target.nativeFrame(),target.point(),actualHead,originals,catalog);
    }

    private static Guarded guarded(ContinuityStorePort.Session same,GuardEvidence guard,Complete claimed,
            ActionPorts.OutcomeArchive originals) throws IOException {
        RootGuardEvidence.requireHistory(guard,originals,same);
        var point=RootGuardEvidence.writerPoint(guard,originals);
        var named=RootGuardEvidence.originalDriverSource(guard,originals);
        var basis=RootGuardEvidence.frameBasis(guard,originals);
        Original original=load(basis.driverFacts(),basis.nativeFrame(),originals);
        StrictJson.require(original.driver().equals(named.driverRef())&&original.frame().equals(claimed)
                &&guard.origin() instanceof CommandOrigin.Gameplay&&guard.observed().equals(original.frame().identity())
                &&guard.source().equals(original.frame().source())&&guard.sessionId().equals(original.frame().sessionId())
                &&guard.connectionGeneration().equals(original.frame().connectionGeneration())&&guard.observedAt().equals(original.frame().observedAt()),
                "READ lineage endpoint requires the exact complete original Root guard frame");
        var facts=original.facts();var driver=facts.driver();
        var stamp=new DriverSnapshotFacts.Stamp(facts.driverVersion(),facts.episodeEpoch(),facts.transport().game(),
                driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
        // This immutable historical value is solely an input to the existing stamp serializer. It never enters a current-owner API or repository.
        var historical=new Known(driver,stamp,original.driver(),List.of(),new OpportunityJson.Obj(java.util.Map.of()),Optional.empty(),Optional.of(facts));
        StrictJson.require(Arrays.equals(read(named.stampRef(),originals),NativeDriverStamp.encode(original.frame(),historical)),
                "original full Driver stamp differs from the replayed endpoint producer");
        return new Guarded(original,point,basis.nativeFrame());
    }

    private static Verified verifyBetween(ContinuityStorePort.Session same,Guarded from,Original now,ExactRef targetNative,
            RootGuardEvidence.WriterPoint targetPoint,WriterContracts.Head head,ActionPorts.OutcomeArchive originals,
            RootReadContractCatalog catalog) throws IOException {
        var previous=from.original();var point=from.point();var oldFacts=previous.facts();var oldDriver=oldFacts.driver();
        StrictJson.require(sameNativeIdentity(previous.frame().identity(),now.frame().identity())
                &&previous.frame().source().equals(now.frame().source())&&previous.frame().sessionId().equals(now.frame().sessionId())
                &&previous.frame().connectionGeneration().equals(now.frame().connectionGeneration())
                &&Arrays.equals(originals.loadNativeFrame(from.nativeFrame()),originals.loadNativeFrame(targetNative)),
                "read-only extension crossed original Native/Game/frame/source/session");
        StrictJson.require(targetPoint.sequence()>=point.sequence()&&targetPoint.sequence()-point.sequence()<=512,
                "finite canonical READ-only interval is reversed or exceeded");
        ContinuityState state=same.requireHistoricalState(point.sequence(),point.digest());
        same.requireHistoricalState(targetPoint.sequence(),targetPoint.digest());
        var events=events(same,head,point.sequence(),targetPoint.sequence());
        StrictJson.require(events.size()==targetPoint.sequence()-point.sequence(),"every intervening canonical READ event must be retained and replayed");
        DriverStateSnapshot.Complete driver=oldDriver;long version=oldFacts.driverVersion();ExactRef driverRef=previous.driver();
        var sources=new ArrayList<ExactRef>();var readReceipts=new ArrayList<ExactRef>();
        for(Event event:events) {
            ObjectNode body=event.body();
            StrictJson.require(event.sequence()==state.sequence()+1&&StrictJson.text(body.get("kind")).equals(WriterContracts.DRIVER_READ_HISTORY_KIND)
                    &&StrictJson.text(body.get("previous_sha256")).equals(ContinuityJson.digest(state.toJson())),
                    "read-only extension contains a non-READ transition or changed canonical predecessor");
            var details=StrictJson.object(body.get("details"),Set.of("schema","evidence_id","token","source","predecessor_head_sha256","read_head_sha256","read_head_sequence",
                    "before_version","after_version","episode_epoch","before_driver","after_driver","read_rows"));
            StrictJson.require(StrictJson.text(details.get("schema")).equals("xar.driver-read-publication/v1")
                    &&details.get("source").equals(ProposalLifecycleCodec.source(previous.frame().source()))
                    &&StrictJson.text(details.get("predecessor_head_sha256")).equals(ContinuityJson.digest(state.toJson()))
                    &&StrictJson.integer(details.get("before_version"),0,StrictJson.MAX_SAFE_INTEGER)==version
                    &&StrictJson.integer(details.get("after_version"),0,StrictJson.MAX_SAFE_INTEGER)==Math.addExact(version,1)
                    &&StrictJson.integer(details.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER)==oldFacts.episodeEpoch(),
                    "canonical READ metadata changed its full Driver/source/version binding");
            long readSeq=StrictJson.integer(details.get("read_head_sequence"),0,StrictJson.MAX_SAFE_INTEGER);
            StrictJson.require(readSeq==state.sequence()&&StrictJson.text(details.get("read_head_sha256")).equals(ContinuityJson.digest(state.toJson())),
                    "read-only extension cannot absorb action or other no-write descendants");
            same.requireHistoricalState(readSeq,StrictJson.text(details.get("read_head_sha256")));
            ExactRef beforeRef=ExactRef.fromJson(details.get("before_driver")),afterRef=ExactRef.fromJson(details.get("after_driver"));
            StrictJson.require(beforeRef.equals(driverRef)&&Arrays.equals(read(beforeRef,originals),driver.encode()),"canonical READ full Driver prefix differs");
            var appended=new ArrayList<>(driver.commandHistory());var rows=details.get("read_rows");
            StrictJson.require(rows!=null&&rows.isArray()&&!rows.isEmpty()&&rows.size()<=128,"actual finite original READ row batch required");
            for(var entry:rows) {
                StrictJson.require(!entry.has("row_kind")||!Set.of(DriverReadHistoryPublisher.FAILED_ROW_KIND,DriverReadHistoryPublisher.PUBLIC_FAILURE_ROW_KIND,DriverReadHistoryPublisher.RETURNED_CONTROL_ROW_KIND,DriverReadHistoryPublisher.POST_KNOWN_ROW_KIND,DriverReadHistoryPublisher.RETURNED_READ_ROW_KIND,DriverReadHistoryPublisher.RETURNED_ACTION_ROW_KIND,DriverReadHistoryPublisher.EARLY_ROW_KIND).contains(StrictJson.text(entry.get("row_kind"))),
                        "a failed read publication has no after-frame and cannot qualify READ-only lineage");
                if(entry.has("row_kind")&&StrictJson.text(entry.get("row_kind")).equals(DriverReadHistoryPublisher.SUMMARY_ROW_KIND)) {
                    ObjectNode row=StrictJson.object(entry,Set.of("row_kind","index","contract_id","row","read","definition_source","decoder_source"));
                    var decoded=org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.decode(read(ExactRef.fromJson(row.get("row")),originals));
                    var source=decoded.source();
                    StrictJson.require(decoded.index()==appended.size()+1L&&decoded.index()==StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER)
                            &&source.originalReceipt().equals(ExactRef.fromJson(row.get("read")))&&source.definitionSource().equals(ExactRef.fromJson(row.get("definition_source")))
                            &&source.decoderSource().equals(ExactRef.fromJson(row.get("decoder_source")))&&source.original().contractId().equals(StrictJson.text(row.get("contract_id"))),
                            "canonical Army summary row changed its actual original definition/read/index");
                    var installed=catalog.installed().stream().filter(binding->binding.contract().contractId().equals(source.original().contractId())).toList();
                    StrictJson.require(installed.size()==1&&installed.getFirst().contract().sourceRef().equals(source.definitionSource())
                            &&installed.getFirst().decoderSource().equals(source.decoderSource()),"actual original Army summary contract/decoder unavailable");
                    var original=org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.replayCanonical(originals,catalog,installed.getFirst().contract(),decoded);
                    requireNativeRead(original.receipt(),previous,now,from,originals);
                    for(ExactRef ref:source.evidence()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
                    appended.add(decoded.historyEntry());readReceipts.addAll(source.componentReceipts());continue;
                }
                if(entry.has("row_kind")&&StrictJson.text(entry.get("row_kind")).equals(DriverReadHistoryPublisher.EXECUTE_ROW_KIND)) {
                    ObjectNode row=StrictJson.object(entry,Set.of("row_kind","index","contract_id","row","read","definition_source","decoder_source"));
                    var decoded=org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.decode(read(ExactRef.fromJson(row.get("row")),originals));
                    var source=decoded.source();
                    StrictJson.require(decoded.index()==appended.size()+1L&&decoded.index()==StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER)
                            &&source.originalReceipt().equals(ExactRef.fromJson(row.get("read")))&&source.definitionSource().equals(ExactRef.fromJson(row.get("definition_source")))
                            &&source.decoderSource().equals(ExactRef.fromJson(row.get("decoder_source")))&&source.original().contractId().equals(StrictJson.text(row.get("contract_id"))),
                            "canonical public execute-query row changed its actual original definition/read/index");
                    var installed=catalog.installed().stream().filter(binding->binding.contract().contractId().equals(source.original().contractId())).toList();
                    StrictJson.require(installed.size()==1&&installed.getFirst().contract().sourceRef().equals(source.definitionSource())
                            &&installed.getFirst().decoderSource().equals(source.decoderSource()),"actual original public execute-query contract/decoder unavailable");
                    var original=org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.replayCanonical(originals,catalog,installed.getFirst().contract(),decoded);
                    requireNativeRead(original.receipt(),previous,now,from,originals);
                    for(ExactRef ref:source.evidence()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
                    appended.add(decoded.historyEntry());readReceipts.add(source.originalReceipt());continue;
                }
                if(entry.has("row_kind")) {
                    ObjectNode row=StrictJson.object(entry,Set.of("row_kind","index","row","before_driver","pair_read","alert_read"));
                    StrictJson.require(StrictJson.text(row.get("row_kind")).equals("GIFT_RESOLVED"),"unknown finite logical READ publication");
                    ExactRef rowRef=ExactRef.fromJson(row.get("row"));
                    var decoded=DriverObservedHistoryRowProducer.decode(read(rowRef,originals));var source=decoded.source();
                    StrictJson.require(decoded.index()==appended.size()+1L&&decoded.index()==StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER)
                            &&source.beforeDriver().equals(beforeRef)&&source.beforeDriver().equals(ExactRef.fromJson(row.get("before_driver")))
                            &&source.pairReference().equals(ExactRef.fromJson(row.get("pair_read")))
                            &&source.alertReference().equals(row.get("alert_read").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("alert_read"))))
                            &&sameNativeIdentity(previous.frame().identity(),source.frame())
                            &&source.frame().frame().revision().compareTo(now.frame().identity().frame().revision())<=0
                            &&Arrays.equals(originals.loadNativeFrame(source.nativeFrame()),originals.loadNativeFrame(from.nativeFrame())),
                            "logical READ row changed its real predecessor/receipts/native subject");
                    var retained=load(source.driverFacts(),source.nativeFrame(),originals);
                    StrictJson.require(retained.driver().equals(beforeRef)&&retained.frame().identity().equals(source.frame())
                            &&retained.frame().source().equals(previous.frame().source())&&retained.frame().sessionId().equals(previous.frame().sessionId())
                            &&retained.frame().connectionGeneration().equals(previous.frame().connectionGeneration()),
                            "logical READ manifest crossed its original source/session/complete Driver");
                    DriverObservedHistoryRowProducer.replayCanonical(originals,catalog,decoded);
                    for(ExactRef original:source.evidence()){var pin=same.capturePin(original,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
                    // An old pair used by an observation is not a new publication of that original Native receipt.
                    appended.add(decoded.historyEntry());continue;
                }
                ObjectNode row=StrictJson.object(entry,Set.of("index","contract_id","row","read","definition_source","decoder_source"));
                ExactRef rowRef=ExactRef.fromJson(row.get("row"));var decoded=DriverReadHistoryRowProducer.decode(read(rowRef,originals));
                StrictJson.require(decoded.index()==appended.size()+1L&&decoded.index()==StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER)
                        &&decoded.provenance().originalReceipt().equals(ExactRef.fromJson(row.get("read")))
                        &&decoded.provenance().definitionSource().equals(ExactRef.fromJson(row.get("definition_source")))
                        &&decoded.provenance().decoderSource().equals(ExactRef.fromJson(row.get("decoder_source")))
                        &&decoded.provenance().contractId().equals(StrictJson.text(row.get("contract_id"))),"canonical READ row differs from its immutable originals");
                var installed=catalog.installed().stream().filter(binding -> binding.contract().contractId().equals(decoded.provenance().contractId())).toList();
                StrictJson.require(installed.size()==1&&installed.getFirst().decoderSource().equals(decoded.provenance().decoderSource()),"exact installed original READ decoder unavailable");
                var original=DriverReadHistoryRowProducer.replayCanonical(originals,catalog,installed.getFirst().contract(),decoded);
                requireNativeRead(original.receipt(),previous,now,from,originals);
                for(ExactRef source:List.of(decoded.provenance().definitionSource(),decoded.provenance().decoderSource())) {
                    var pin=same.capturePin(source,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);
                }
                appended.add(decoded.historyEntry());readReceipts.add(decoded.provenance().originalReceipt());
            }
            var expected=new DriverStateSnapshot.Complete(driver.session(),appended,driver.lastCheckpoint(),driver.rollbackWarFailure(),driver.managedRestoreTransaction(),
                    driver.successionExpectation(),driver.successionLifecycle(),driver.campaignGoal(),driver.rollbackWarFailures());
            StrictJson.require(Arrays.equals(expected.encode(),read(afterRef,originals)),"READ changed a non-history Driver slot or omitted an original row");
            ContinuityState after=ContinuityState.fromJson(body.get("after"),head.state().machineId());
            requireOnlyReadField(state,after);
            StrictJson.require(after.sequence()==event.sequence()&&StrictJson.text(after.toJson().get("last_event_identity")).equals(StrictJson.text(body.get("identity")))
                    &&after.toJson().get(WriterContracts.DRIVER_READ_HISTORY_FIELD).equals(details),"READ canonical after state differs from its actual publication");
            same.requireHistoricalState(event.sequence(),ContinuityJson.digest(after.toJson()));
            state=after;driver=expected;driverRef=afterRef;version=Math.addExact(version,1);sources.add(event.pin().reference());
        }
        StrictJson.require(ContinuityJson.digest(state.toJson()).equals(targetPoint.digest())&&version==now.facts().driverVersion()
                &&oldFacts.episodeEpoch()==now.facts().episodeEpoch()&&driverRef.equals(now.driver())&&Arrays.equals(driver.encode(),now.facts().driver().encode()),
                "target Driver has no complete canonical READ-only lineage from the query originals");
        StrictJson.require(same.head().digest().equals(head.digest()),"read-only lineage actual canonical head changed during replay");
        return new Verified(previous.frame(),now.frame(),previous.driver(),now.driver(),List.copyOf(sources),head,targetPoint,List.copyOf(readReceipts));
    }
    private static void requireNativeRead(PlanningReadReceipt original,Original previous,Original now,Guarded from,ActionPorts.OutcomeArchive originals) {
        StrictJson.require(original.request().origin() instanceof CommandOrigin.Gameplay
                &&sameNativeIdentity(previous.frame().identity(),original.request().before())
                &&original.request().before().frame().revision().compareTo(now.frame().identity().frame().revision())<=0
                &&original.request().source().equals(previous.frame().source())&&original.request().sessionId().equals(previous.frame().sessionId())
                &&original.before().binding().connectionGeneration().equals(previous.frame().connectionGeneration())
                &&Arrays.equals(originals.loadNativeFrame(original.before().binding().nativeEvidence()),originals.loadNativeFrame(from.nativeFrame())),
                "intervening READ is from a different actual Native frame/source/session");
    }
    private static void requireOnlyReadField(ContinuityState before,ContinuityState after) {
        ObjectNode left=before.toJson(),right=after.toJson();var names=new java.util.HashSet<String>();left.fieldNames().forEachRemaining(names::add);right.fieldNames().forEachRemaining(names::add);
        for(String name:names)if(!Set.of("sequence","last_event_identity",WriterContracts.DRIVER_READ_HISTORY_FIELD).contains(name))
            StrictJson.require(left.has(name)==right.has(name)&&java.util.Objects.equals(left.get(name),right.get(name)),"READ changed unrelated canonical state: "+name);
    }
    private static List<Event> events(ContinuityStorePort.Session same,WriterContracts.Head head,long after,long through) throws IOException {
        var events=new ArrayList<Event>();
        for(var pin:head.documents()) {
            String name=Path.of(pin.reference().path()).getFileName().toString();if(!name.matches("[0-9]{8,16}\\.json"))continue;
            long sequence=Long.parseLong(name.substring(0,name.length()-5));if(sequence<=after||sequence>through)continue;
            ObjectNode row=ContinuityJson.parseObject(same.readPinned(pin,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
            StrictJson.object(row,Set.of("sequence","at_utc","kind","details","identity","previous_sha256","after"));
            StrictJson.require(StrictJson.integer(row.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER)==sequence,"actual captured READ event path/sequence differs");
            events.add(new Event(sequence,pin,row));
        }
        events.sort(Comparator.comparingLong(Event::sequence));return List.copyOf(events);
    }
    private static Original load(ExactRef manifestRef,ExactRef nativeRef,ActionPorts.OutcomeArchive originals) {
        RawJson manifest=RawJson.fullMaterial(read(manifestRef,originals));ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest);
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,originals.loadNativeFrame(nativeRef));
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(read(driver,originals)),nativeFrame);
        var joined=new DriverObservationAssembler().assemble(nativeFrame,facts,nativeRef);
        StrictJson.require(joined instanceof Complete,"READ lineage requires the complete original Driver/native producer");return new Original((Complete)joined,facts,driver);
    }
    private static boolean sameNativeIdentity(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity previous,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity current) {
        return previous.machineId().equals(current.machineId())&&previous.game().equals(current.game())
                &&previous.observationVersion()==current.observationVersion()&&previous.frame().episodeRunId().equals(current.frame().episodeRunId())
                &&previous.frame().identity().equals(current.frame().identity())&&current.frame().revision().compareTo(previous.frame().revision())>=0;
    }
    private static byte[] read(ExactRef ref,ActionPorts.OutcomeArchive originals) {
        byte[] bytes=originals.loadFullMaterial(ref).bytes();StrictJson.require(ref.bytes()==bytes.length&&ref.sha256().equals(DriverJson.sha256(bytes)),"exact original lineage bytes/SHA differ");return bytes;
    }
}
