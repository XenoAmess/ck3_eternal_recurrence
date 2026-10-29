package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original normally returned unresolved Army structural history. A row is not action settlement or retry authority. */
public final class DriverReturnedActionHistoryRowProducer {
    public static final String SOURCE_FIELD="returned_action_history_source";
    public static final String SOURCE_SCHEMA="xar.driver-returned-action-history-source/v1";
    public static final String INVOCATION_SCHEMA="xar.root-returned-action-invocation/v1";
    public enum Family { ARMY_STRUCTURE_COMMANDS }
    public static final Family FAMILY=Family.ARMY_STRUCTURE_COMMANDS;
    public static final int MAXIMUM_SOURCE_REFERENCES=256;
    private DriverReturnedActionHistoryRowProducer(){ }

    /** Implemented only by the actual installed Root source; the publisher binds that identical object once. */
    public interface Source {
        ActionJournal journal();
        void requireOwner(DriverStateAssembler authority,ActionJournal journal,OutcomeArchive archive,RootReadContractCatalog catalog);
        void requireCatalog(RootReadContractCatalog identical);
        List<ExactRef> sources();
        Originals requireOriginal(Session same,DriverStateAssembler authority,OutcomeArchive bound,OriginalReturned identical)throws IOException;
        /** Drop only the private in-memory invocation after a definite publication/cancel; never clear canonical UNKNOWN. */
        void release(OriginalReturned identical);
        /** Pure original NT formatter/decoder. No Native read, new invocation or current-Game qualification. */
        Projection project(ActionReceipt actual,OutcomeArchive bound,ExactRef projectionOriginal)throws IOException;
    }
    /** The actual Root source privately constructs this token; DATA decode never creates one. */
    public interface OriginalReturned { Source issuer(); }
    public record Projection(RawJson fullResult,PublicNumbers publicNumbers,List<ExactRef> sourceClosure,List<ExactRef> materialEvidence) {
        public Projection {
            Objects.requireNonNull(fullResult);Objects.requireNonNull(publicNumbers);sourceClosure=refs(sourceClosure,1,MAXIMUM_SOURCE_REFERENCES);materialEvidence=refs(materialEvidence,1,MAXIMUM_SOURCE_REFERENCES);
            publicNumbers.toPublic(object(fullResult));
        }
    }
    public record Originals(ActionReceipt actual,ExactRef canonicalReceipt,ExactRef canonicalRecord,Known before,
            ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,
            ExactRef invocation,ExactRef caller,Optional<ExactRef> epochManifest,ExactRef projectionOriginal,long headSequence,String headDigest,List<ExactRef> producerSources) {
        public Originals(ActionReceipt actual,ExactRef canonicalReceipt,ExactRef canonicalRecord,Known before,
            ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,
            ExactRef invocation,ExactRef caller,ExactRef epochManifest,ExactRef projectionOriginal,long headSequence,String headDigest,List<ExactRef> producerSources) {this(actual,canonicalReceipt,canonicalRecord,before,beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller,Optional.of(epochManifest),projectionOriginal,headSequence,headDigest,producerSources);}
        public Originals {
            Objects.requireNonNull(actual);Objects.requireNonNull(before);
            for(var ref:List.of(canonicalReceipt,canonicalRecord,beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller,projectionOriginal))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverReturnedActionHistoryRowProducer::positive);
            head(headSequence,headDigest);producerSources=refs(producerSources,1,MAXIMUM_SOURCE_REFERENCES);requireReturned(actual);
        }
    }
    /** Canonical serializer input only; this cannot create an OriginalReturned or admit a publication. */
    public record InvocationData(OperationKey operation,ExactRef canonicalReceipt,ExactRef canonicalRecord,
            ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,ExactRef caller,
            Optional<ExactRef> epochManifest,ExactRef projectionOriginal,long headSequence,String headDigest,List<ExactRef> producerSources) {
        public InvocationData(OperationKey operation,ExactRef canonicalReceipt,ExactRef canonicalRecord,
            ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,ExactRef caller,
            ExactRef epochManifest,ExactRef projectionOriginal,long headSequence,String headDigest,List<ExactRef> producerSources) {this(operation,canonicalReceipt,canonicalRecord,beforeDriver,originalKnown,nativeFrame,driverFacts,caller,Optional.of(epochManifest),projectionOriginal,headSequence,headDigest,producerSources);}
        public InvocationData {
            requireOperation(operation);
            for(var ref:List.of(canonicalReceipt,canonicalRecord,beforeDriver,originalKnown,nativeFrame,driverFacts,caller,projectionOriginal))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverReturnedActionHistoryRowProducer::positive);
            head(headSequence,headDigest);producerSources=refs(producerSources,1,MAXIMUM_SOURCE_REFERENCES);
        }
    }
    public record HistorySource(OperationKey operation,ExactRef canonicalReceipt,ExactRef canonicalRecord,
            ExactRef acknowledgement,ExactRef preparedRequest,NativeRequestChronology.PacketIdentity outbound,
            ExactRef fullResult,PublicNumbers publicNumbers,ExactRef beforeDriver,ExactRef originalKnown,
            ExactRef nativeFrame,ExactRef driverFacts,ExactRef invocation,ExactRef caller,Optional<ExactRef> epochManifest,ExactRef projectionOriginal,
            long headSequence,String headDigest,List<ExactRef> producerSources,List<ExactRef> projectionSources,List<ExactRef> projectionEvidence) {
        public HistorySource(OperationKey operation,ExactRef canonicalReceipt,ExactRef canonicalRecord,
            ExactRef acknowledgement,ExactRef preparedRequest,NativeRequestChronology.PacketIdentity outbound,
            ExactRef fullResult,PublicNumbers publicNumbers,ExactRef beforeDriver,ExactRef originalKnown,
            ExactRef nativeFrame,ExactRef driverFacts,ExactRef invocation,ExactRef caller,ExactRef epochManifest,ExactRef projectionOriginal,
            long headSequence,String headDigest,List<ExactRef> producerSources,List<ExactRef> projectionSources,List<ExactRef> projectionEvidence) {this(operation,canonicalReceipt,canonicalRecord,acknowledgement,preparedRequest,outbound,fullResult,publicNumbers,beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller,Optional.of(epochManifest),projectionOriginal,headSequence,headDigest,producerSources,projectionSources,projectionEvidence);}
        public HistorySource {
            requireOperation(operation);
            for(var ref:List.of(canonicalReceipt,canonicalRecord,acknowledgement,preparedRequest,fullResult,beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller,projectionOriginal))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverReturnedActionHistoryRowProducer::positive);
            Objects.requireNonNull(outbound);Objects.requireNonNull(publicNumbers);head(headSequence,headDigest);
            producerSources=refs(producerSources,1,MAXIMUM_SOURCE_REFERENCES);projectionSources=refs(projectionSources,1,MAXIMUM_SOURCE_REFERENCES);projectionEvidence=refs(projectionEvidence,1,MAXIMUM_SOURCE_REFERENCES);
            StrictJson.require(projectionEvidence.contains(projectionOriginal),"source-owned projection basis must retain its actual original role");
        }
        public List<ExactRef> evidence(){
            var all=new LinkedHashSet<ExactRef>(producerSources);all.addAll(projectionSources);all.addAll(projectionEvidence);
            all.addAll(List.of(canonicalReceipt,canonicalRecord,acknowledgement,preparedRequest,fullResult,beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller,projectionOriginal));epochManifest.ifPresent(all::add);
            return List.copyOf(all);
        }
    }
    public record RawHistoryRow(long index,HistorySource source,Obj result) {
        public RawHistoryRow {
            StrictJson.safe(index,1);Objects.requireNonNull(source);requireReturnedReport(source.operation(),Objects.requireNonNull(result));
            source.publicNumbers().toPublic(result);
        }
        public String command(){return source.operation().value();}
        public boolean ok(){return true;}
        public Obj toJson(){
            var fields=new LinkedHashMap<String,Value>();fields.put("index",number(index));fields.put("command",text(command()));
            fields.put("ok",new Bool(true));fields.put("result",result);fields.put(SOURCE_FIELD,sourceJson(source));return new Obj(fields);
        }
        public byte[] encode(){return DriverJson.encode(toJson());}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    public static final class Candidate {
        private final Source issuer;private final OriginalReturned invocation;private final RawHistoryRow row;private final ExactRef rowReference;
        private Candidate(Source issuer,OriginalReturned invocation,RawHistoryRow row,ExactRef rowReference){this.issuer=issuer;this.invocation=invocation;this.row=row;this.rowReference=rowReference;}
        public RawHistoryRow row(){return row;}
        public HistorySource source(){return row.source();}
        public ExactRef rowReference(){return rowReference;}
        public ExactRef fullResultReference(){return row.source().fullResult();}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public long headSequence(){return source().headSequence();}
        public String headDigest(){return source().headDigest();}
    }
    public sealed interface Outcome permits Queued,StorageDiagnostic { }
    public record Queued(ExactRef originalRow) implements Outcome {public Queued {positive(originalRow);}}
    public record StorageDiagnostic(String errorType,String message) implements Outcome {public StorageDiagnostic {StrictJson.text(errorType);Objects.requireNonNull(message);}}

    /** Every original and installed formatter is validated before the first new material. Full result precedes row. */
    public static Candidate prepare(Session same,OutcomeArchive bound,DriverStateAssembler authority,OriginalReturned invocation,
            long nextIndex,List<ExactRef> publisherSources)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(bound);Objects.requireNonNull(authority);Objects.requireNonNull(invocation);
        StrictJson.safe(nextIndex,1);publisherSources=refs(publisherSources,1,MAXIMUM_SOURCE_REFERENCES);Source issuer=Objects.requireNonNull(invocation.issuer());
        Originals originals=issuer.requireOriginal(same,authority,bound,invocation);requireHead(same,originals);
        StrictJson.require(issuer.sources().containsAll(originals.producerSources()),"returned action source is not the actual installed owner closure");
        requireCanonical(same,bound,originals.actual(),originals.canonicalReceipt(),originals.canonicalRecord());
        Projection projection=issuer.project(originals.actual(),bound,originals.projectionOriginal());requireProjection(originals.actual(),projection);full(bound,originals.projectionOriginal());
        StrictJson.require(projection.materialEvidence().contains(originals.projectionOriginal()),"returned projection omitted its actual retained original basis");
        var producers=new LinkedHashSet<ExactRef>(originals.producerSources());producers.addAll(publisherSources);
        List<ExactRef> complete=refs(List.copyOf(producers),1,MAXIMUM_SOURCE_REFERENCES);requireFiles(union(complete,projection.sourceClosure()));
        requireBefore(bound,originals.actual(),originals.beforeDriver(),originals.originalKnown(),originals.nativeFrame(),originals.driverFacts());
        StrictJson.require(Arrays.equals(originals.before().driver().encode(),full(bound,originals.beforeDriver()).bytes()),"actual returned beforeKnown differs from its complete Driver original");
        requireInvocation(bound,invocationData(originals),originals.invocation());
        requireCallerAndEpoch(bound,originals.actual(),originals.caller(),originals.epochManifest());
        var attempt=requireReturned(originals.actual());var ack=(NativeActionPort.AckReceived)((ActionState.Unknown)originals.actual().state()).dispatch().orElseThrow();
        ExactRef ackRef=bound.referenceOf(ack),requestRef=bound.requestReferenceOf(attempt.preparedRequest());
        requireAck(bound,originals.actual(),ackRef,requestRef,NativeRequestChronology.PacketIdentity.of(ack.outbound().orElseThrow().originalPacket()));
        ExactRef full=bound.preserveMaterial(RawJson.fullMaterial(projection.fullResult().bytes()));requireMaterial(bound,full,projection.fullResult());
        HistorySource source=new HistorySource(originals.actual().command().operation(),originals.canonicalReceipt(),originals.canonicalRecord(),
                ackRef,requestRef,NativeRequestChronology.PacketIdentity.of(ack.outbound().orElseThrow().originalPacket()),full,projection.publicNumbers(),
                originals.beforeDriver(),originals.originalKnown(),originals.nativeFrame(),originals.driverFacts(),originals.invocation(),originals.caller(),originals.epochManifest(),
                originals.projectionOriginal(),originals.headSequence(),originals.headDigest(),complete,projection.sourceClosure(),projection.materialEvidence());
        RawHistoryRow row=new RawHistoryRow(nextIndex,source,object(projection.fullResult()));RawJson wire=RawJson.fullMaterial(row.encode());
        ExactRef rowRef=bound.preserveMaterial(wire);requireMaterial(bound,rowRef,wire);
        StrictJson.require(decode(full(bound,rowRef).bytes()).equals(row),"returned row/source archive serialization changed");
        Originals rechecked=issuer.requireOriginal(same,authority,bound,invocation);requireHead(same,rechecked);
        StrictJson.require(rechecked.equals(originals),"returned private invocation changed while retaining its full original result");
        requireFiles(union(complete,projection.sourceClosure()));
        return new Candidate(issuer,invocation,row,rowRef);
    }
    /** Revalidates the exact private candidate, not a decoded DTO. No writes, queries, dispatch or new current scope. */
    public static Candidate replay(Session same,OutcomeArchive bound,DriverStateAssembler authority,Source identical,
            RootReadContractCatalog catalog,Candidate candidate)throws IOException {
        Objects.requireNonNull(candidate);StrictJson.require(candidate.issuer==identical&&candidate.invocation.issuer()==identical,"returned candidate crossed its actual issuer");
        Originals originals=identical.requireOriginal(same,authority,bound,candidate.invocation);requireHead(same,originals);
        requireCanonical(same,bound,originals.actual(),candidate.source().canonicalReceipt(),candidate.source().canonicalRecord());
        replayOriginals(bound,catalog,identical,candidate.row());requireMaterial(bound,candidate.rowReference(),RawJson.fullMaterial(candidate.row().encode()));return candidate;
    }
    /** Historical originals only. The caller still must establish canonical publication membership/ancestry. */
    public static RawHistoryRow replayOriginals(OutcomeArchive bound,RootReadContractCatalog catalog,Source identical,RawHistoryRow row)throws IOException {
        Objects.requireNonNull(bound);Objects.requireNonNull(catalog);Objects.requireNonNull(identical);Objects.requireNonNull(row);identical.requireCatalog(catalog);
        HistorySource source=row.source();ActionReceipt actual=requireReceipt(bound,source.canonicalReceipt(),source.canonicalRecord());
        full(bound,source.projectionOriginal());Projection projection=identical.project(actual,bound,source.projectionOriginal());requireProjection(actual,projection);
        StrictJson.require(source.operation().equals(actual.command().operation())&&source.projectionSources().equals(projection.sourceClosure())
                &&source.publicNumbers().equals(projection.publicNumbers())&&source.projectionEvidence().equals(projection.materialEvidence()),"returned action source-owned projection or number roles changed");
        requireMaterial(bound,source.fullResult(),projection.fullResult());
        StrictJson.require(row.result().equals(object(projection.fullResult())),"returned action result is truncated or differs from original NT formatter");
        requireAck(bound,actual,source.acknowledgement(),source.preparedRequest(),source.outbound());
        requireBefore(bound,actual,source.beforeDriver(),source.originalKnown(),source.nativeFrame(),source.driverFacts());
        InvocationData data=invocation(bound,source.invocation());
        StrictJson.require(sameInvocation(data,source)&&source.producerSources().containsAll(data.producerSources())
                &&identical.sources().containsAll(data.producerSources()),"returned invocation crossed its actual installed source/receipt/before/head");
        requireCallerAndEpoch(bound,actual,source.caller(),source.epochManifest());
        requireFiles(union(source.producerSources(),source.projectionSources()));
        requireMaterial(bound,bound.materialReferenceOf(RawJson.fullMaterial(row.encode())),RawJson.fullMaterial(row.encode()));return row;
    }
    public static void requireCanonical(Session same,OutcomeArchive bound,ActionReceipt actual,ExactRef receipt,ExactRef record)throws IOException {
        requireReceipt(bound,receipt,record);StrictJson.require(bound.loadReceipt(receipt).equals(actual)
                &&ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,bound).equals(record),"returned UNKNOWN is not the retained canonical writer member");
    }
    private static ActionReceipt requireReceipt(OutcomeArchive bound,ExactRef receipt,ExactRef record){
        ActionReceipt actual=bound.loadReceipt(receipt);requireReturned(actual);
        StrictJson.require(bound.receiptReferenceOf(actual).equals(receipt)&&bound.loadRecord(record).receipt().equals(actual)
                &&bound.recordReferenceOf(bound.loadRecord(record)).equals(record),"returned action lost original canonical receipt/record archive custody");return actual;
    }
    /** Original unresolved dispatch only. This DATA check supplies no private invocation or publication membership. */
    public static ActionState.Attempt requireReturned(ActionReceipt actual){
        Objects.requireNonNull(actual);var call=requireOperation(actual.command().operation());
        StrictJson.require(actual.command().origin() instanceof CommandOrigin.Gameplay&&!actual.settled()&&actual.applied().isEmpty()
                &&actual.state() instanceof ActionState.Unknown,"only actual unresolved structural RETURNED material is eligible");
        var unknown=(ActionState.Unknown)actual.state();var attempt=unknown.attempt().orElseThrow(()->new IllegalArgumentException("original attempt absent"));
        StrictJson.require(unknown.dispatch().orElseThrow() instanceof NativeActionPort.AckReceived,"returned structural action needs its original ACK");
        var ack=(NativeActionPort.AckReceived)unknown.dispatch().orElseThrow();
        StrictJson.require(attempt.requestId().equals(ack.requestId())&&attempt.guard().observed().equals(actual.command().before())
                &&attempt.guard().source().equals(actual.command().source())&&attempt.guard().sessionId().equals(actual.command().sessionId())
                &&attempt.guard().operation().equals(actual.command().operation())&&attempt.preparedRequest().step().equals(actual.command().operation().value()),
                "returned structural action changed original attempt/ACK/source/frame/step");
        var custody=ack.custody().orElseThrow(()->new IllegalArgumentException("original outbound custody absent"));custody.verify(ack,attempt.guard());
        StrictJson.require(!custody.writeEntered().observedAt().isBefore(attempt.submittedAt())
                &&custody.writeEntered().observedAt().isBefore(actual.command().deadline()),"returned original write escaped its canonical attempt/deadline");
        if(ack.nativeOk()){
            Obj token=object(ack.originalResultToken().orElseThrow(()->new IllegalArgumentException("original ACK result absent")));
            requireText(token,"step",actual.command().operation().value());OpportunityJson.bool(token.get("accepted"),"original structural accepted token");
        }else{
            Obj response=object(ack.originalFrame());
            StrictJson.require(call instanceof DriverReturnedActionHistoryMaterial.Halt&&new Bool(false).equals(response.get("ok"))
                    &&new Text("CK3 halt-army command validation failed").equals(response.get("error"))
                    &&!(response.get("result") instanceof Obj),"only the exact stock Halt refusal can produce a normal returned report");
            requireText(response,"type","command_result");requireText(response,"request_id",attempt.requestId());
        }
        return attempt;
    }
    private static void requireAck(OutcomeArchive bound,ActionReceipt actual,ExactRef ackRef,ExactRef requestRef,NativeRequestChronology.PacketIdentity outbound){
        var attempt=requireReturned(actual);var ack=(NativeActionPort.AckReceived)((ActionState.Unknown)actual.state()).dispatch().orElseThrow();
        StrictJson.require(bound.referenceOf(ack).equals(ackRef)&&bound.load(ackRef).equals(ack)
                &&bound.requestReferenceOf(attempt.preparedRequest()).equals(requestRef)&&bound.loadRequest(requestRef).equals(attempt.preparedRequest())
                &&outbound.matches(ack.outbound().orElseThrow().originalPacket()),"returned structural ACK/request/outbound original bytes changed");
    }
    private static void requireProjection(ActionReceipt actual,Projection projection){
        Objects.requireNonNull(projection);requireReturned(actual);Obj result=object(projection.fullResult());requireReturnedReport(actual.command().operation(),result);
        var ack=(NativeActionPort.AckReceived)((ActionState.Unknown)actual.state()).dispatch().orElseThrow();
        var action=OpportunityJson.object(result.get("war_action"),"original structural report");
        String status=OpportunityJson.text(action.get("status"),"original structural report status");
        boolean deferred=status.equals("halt_validator_rejected_current_route_retained");
        StrictJson.require(ack.nativeOk()!=deferred,"returned report changed its actual native ACK/refusal branch");
        if(!deferred)requireInteger(action,"submitted_date_raw",actual.command().before().frame().identity().dateRaw());
        if(requireOperation(actual.command().operation()) instanceof DriverReturnedActionHistoryMaterial.Merge){
            var before=actual.command().before();requireText(action,"submitted_snapshot_id",before.frame().snapshotId());
            requireInteger(action,"submitted_public_revision",before.frame().revision());
            requireInteger(action,"submitted_native_revision",before.frame().identity().nativeRevision());
            requireText(action,"submitted_episode_run_id",before.frame().episodeRunId());
        }
        projection.publicNumbers().toPublic(result);
    }
    /** Finite original report shape only. The installed source replays full frames/route/primitive through its sole formatter. */
    public static void requireReturnedReport(OperationKey operation,Obj result){
        var call=requireOperation(operation);Objects.requireNonNull(result);
        requireText(result,"step",operation.value());OpportunityJson.bool(result.get("accepted"),"original accepted");
        requireText(result,"backend_id","native-headless");Obj action=OpportunityJson.object(result.get("war_action"),"complete structural war_action");
        String status=OpportunityJson.text(action.get("status"),"original structural status");
        if(call instanceof DriverReturnedActionHistoryMaterial.Halt halt){
            requireInteger(action,"army_id",BigInteger.valueOf(halt.source()));
            if(status.equals("halt_validator_rejected_current_route_retained")){
                requireText(result,"schema","xar.halt-army-validator-deferred/v1");requireText(result,"status","deferred");
                StrictJson.require(new Bool(false).equals(result.get("accepted"))&&new Bool(false).equals(result.get("business_submission"))
                        &&new Bool(false).equals(result.get("replay_allowed")),"deferred Halt cannot acquire business submission or replay");
                OpportunityJson.object(result.get("halt_rejection_evidence"),"actual retained Halt refusal evidence");
            }else{
                StrictJson.require(status.equals("halt_submitted")&&new Bool(false).equals(action.get("postcondition_verified")),
                        "normal Halt is submitted-only");
                OpportunityJson.integer(action.get("submitted_date_raw"),"actual submitted date");
            }
        }else{
            requireInteger(action,"source_army_id",BigInteger.valueOf(call.source()));OpportunityJson.integer(action.get("submitted_date_raw"),"actual submitted date");
            if(call instanceof DriverReturnedActionHistoryMaterial.SplitHalf){
                StrictJson.require(status.equals("split_submitted")||status.equals("split_applied"),"original split report status required");
                if(status.equals("split_applied")){
                    BigInteger sibling=OpportunityJson.integer(action.get("sibling_army_id"),"actual original sibling CUnit");
                    StrictJson.require(sibling.signum()>=0&&sibling.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"original public sibling CUnit required");
                }
            }
            else{
                var merge=(DriverReturnedActionHistoryMaterial.Merge)call;requireInteger(action,"destination_army_id",BigInteger.valueOf(merge.destination()));
                StrictJson.require((status.equals("merge_submitted")||status.equals("merge_applied"))
                        &&new Bool(status.equals("merge_applied")).equals(action.get("postcondition_verified")),"original merge report status/postcondition pair required");
            }
        }
    }
    private static void requireBefore(OutcomeArchive bound,ActionReceipt actual,ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts){
        var attempt=requireReturned(actual);var basis=RootGuardEvidence.frameBasis(attempt.guard(),bound);
        StrictJson.require(basis.nativeFrame().equals(nativeFrame)&&basis.driverFacts().equals(driverFacts),"returned before Native/manifest differ from actual attempt guard");
        var knownWire=DriverSnapshotFacts.originalKnownJson(full(bound,originalKnown).bytes());RawJson manifest=full(bound,driverFacts);
        var nativeOriginal=DriverObservationEvidenceReader.nativeFrame(driverFacts,manifest,bound.loadNativeFrame(nativeFrame));
        var facts=DriverObservationEvidenceReader.decode(driverFacts,manifest,full(bound,DriverObservationEvidenceReader.currentDriverReference(driverFacts,manifest)),nativeOriginal);
        var presence=DriverSnapshotFacts.observationOriginalReference(knownWire);
        StrictJson.require(presence.isEmpty()||presence.orElseThrow().equals(facts.semanticFactsEvidence()),"returned original Known has another observation manifest");
        var known=DriverSnapshotFacts.decodeKnownOriginal(knownWire,presence.isPresent()?java.util.Optional.of(facts):java.util.Optional.empty());
        StrictJson.require(Arrays.equals(known.driver().encode(),full(bound,beforeDriver).bytes())&&Arrays.equals(facts.driver().encode(),known.driver().encode())
                &&facts.driverVersion()==known.stamp().driverVersion()&&facts.episodeEpoch()==known.stamp().episodeEpoch(),"returned before full Driver/Known/native facts differ");
        var joined=new DriverObservationAssembler().assemble(nativeOriginal,facts,nativeFrame);
        StrictJson.require(joined instanceof DriverObservationAssembler.Complete,"returned original paused living full frame is unavailable");
        var complete=(DriverObservationAssembler.Complete)joined;
        StrictJson.require(complete.identity().equals(actual.command().before())&&complete.source().equals(actual.command().source())
                &&complete.sessionId().equals(actual.command().sessionId())&&complete.connectionGeneration().equals(attempt.guard().connectionGeneration())
                &&complete.observedAt().equals(attempt.guard().observedAt()),"returned full Native/Driver frame differs from its actual canonical before guard");
        StrictJson.require(OpportunityJson.bool(complete.semantic().get("paused"),"actual paused map")
                &&OpportunityJson.bool(complete.semantic().get("map_ready"),"actual ready map")
                &&OpportunityJson.bool(OpportunityJson.object(complete.semantic().get("played_character"),"actual player").get("alive"),"actual living player"),
                "returned structural original did not belong to its actual paused living map");
        var command=actual.command();StrictJson.require(nativeOriginal.session().game().equals(command.before().game())
                &&nativeOriginal.session().sessionId().equals(command.sessionId())&&known.driver().session().actorId().equals(command.before().frame().identity().player())
                &&known.driver().session().episodeRunId().equals(command.before().frame().episodeRunId()),"returned before crossed Game/actor/episode/session");
    }
    private static void requireCallerAndEpoch(OutcomeArchive bound,ActionReceipt actual,ExactRef caller,Optional<ExactRef> epoch){
        Obj original=closed(full(bound,caller).bytes(),Set.of("step","arguments"));
        requireText(original,"step",actual.command().operation().value());OpportunityJson.object(original.get("arguments"),"actual typed public structural arguments");epoch.ifPresent(ref->full(bound,ref));
    }
    private static void requireHead(Session same,Originals originals)throws IOException {
        StrictJson.require(same.head().state().sequence()==originals.headSequence()&&same.head().digest().equals(originals.headDigest()),"returned original escaped its actual capture head");
    }
    public static InvocationData invocationData(Originals value){return new InvocationData(value.actual().command().operation(),value.canonicalReceipt(),value.canonicalRecord(),value.beforeDriver(),value.originalKnown(),value.nativeFrame(),value.driverFacts(),value.caller(),value.epochManifest(),value.projectionOriginal(),value.headSequence(),value.headDigest(),value.producerSources());}
    public static RawJson invocationJson(InvocationData data){return RawJson.fullMaterial(DriverJson.encode(invocationBody(data)));}
    private static Obj invocationBody(InvocationData data){
        var fields=new LinkedHashMap<String,Value>();fields.put("schema",text(INVOCATION_SCHEMA));fields.put("family",text(FAMILY.name()));fields.put("operation",text(data.operation().value()));
        fields.put("canonical_receipt",ref(data.canonicalReceipt()));fields.put("canonical_record",ref(data.canonicalRecord()));
        fields.put("before_driver",ref(data.beforeDriver()));fields.put("original_known",ref(data.originalKnown()));fields.put("native_frame",ref(data.nativeFrame()));
        fields.put("driver_facts",ref(data.driverFacts()));fields.put("caller",ref(data.caller()));fields.put("epoch_manifest",optionalRef(data.epochManifest()));
        fields.put("projection_original",ref(data.projectionOriginal()));fields.put("head_sequence",number(data.headSequence()));fields.put("head_digest",text(data.headDigest()));fields.put("producer_sources",array(data.producerSources()));return new Obj(fields);
    }
    private static void requireInvocation(OutcomeArchive bound,InvocationData expected,ExactRef reference){
        StrictJson.require(invocation(bound,reference).equals(expected),"private returned invocation DATA differs");
    }
    private static InvocationData invocation(OutcomeArchive bound,ExactRef reference){
        Obj row=closed(full(bound,reference).bytes(),INVOCATION_FIELDS);StrictJson.require(new Text(INVOCATION_SCHEMA).equals(row.get("schema"))&&new Text(FAMILY.name()).equals(row.get("family")),"exact returned invocation schema required");
        return new InvocationData(new OperationKey(string(row,"operation")),reference(row.get("canonical_receipt")),reference(row.get("canonical_record")),reference(row.get("before_driver")),
                reference(row.get("original_known")),reference(row.get("native_frame")),reference(row.get("driver_facts")),reference(row.get("caller")),optionalRef(row.get("epoch_manifest")),reference(row.get("projection_original")),
                integer(row,"head_sequence"),string(row,"head_digest"),readRefs(row.get("producer_sources"),1,MAXIMUM_SOURCE_REFERENCES));
    }
    private static boolean sameInvocation(InvocationData data,HistorySource source){
        return data.operation().equals(source.operation())&&data.canonicalReceipt().equals(source.canonicalReceipt())&&data.canonicalRecord().equals(source.canonicalRecord())
                &&data.beforeDriver().equals(source.beforeDriver())&&data.originalKnown().equals(source.originalKnown())&&data.nativeFrame().equals(source.nativeFrame())
                &&data.driverFacts().equals(source.driverFacts())&&data.caller().equals(source.caller())&&data.epochManifest().equals(source.epochManifest())
                &&data.projectionOriginal().equals(source.projectionOriginal())&&data.headSequence()==source.headSequence()&&data.headDigest().equals(source.headDigest());
    }
    private static final Set<String> INVOCATION_FIELDS=Set.of("schema","family","operation","canonical_receipt","canonical_record","before_driver","original_known","native_frame","driver_facts","caller","epoch_manifest","projection_original","head_sequence","head_digest","producer_sources");
    private static final Set<String> SOURCE_FIELDS=Set.of("schema","family","operation","canonical_receipt","canonical_record","acknowledgement","prepared_request","outbound_bytes","outbound_sha256","full_result","public_number_roles","before_driver","original_known","native_frame","driver_facts","invocation","caller","epoch_manifest","projection_original","head_sequence","head_digest","producer_sources","projection_sources","projection_evidence");
    public static Obj sourceJson(HistorySource source){
        var base=new LinkedHashMap<String,Value>(invocationBody(new InvocationData(source.operation(),source.canonicalReceipt(),source.canonicalRecord(),source.beforeDriver(),source.originalKnown(),source.nativeFrame(),source.driverFacts(),source.caller(),source.epochManifest(),source.projectionOriginal(),source.headSequence(),source.headDigest(),source.producerSources())).members());
        base.put("schema",text(SOURCE_SCHEMA));base.put("acknowledgement",ref(source.acknowledgement()));base.put("prepared_request",ref(source.preparedRequest()));
        base.put("outbound_bytes",number(source.outbound().bytes()));base.put("outbound_sha256",text(source.outbound().sha256()));
        base.put("full_result",ref(source.fullResult()));base.put("public_number_roles",source.publicNumbers().toJson());base.put("invocation",ref(source.invocation()));
        base.put("projection_sources",array(source.projectionSources()));base.put("projection_evidence",array(source.projectionEvidence()));return new Obj(base);
    }
    public static RawHistoryRow decode(byte[] bytes){
        Obj row=closed(bytes,Set.of("index","command","ok","result",SOURCE_FIELD));
        StrictJson.require(row.get("ok") instanceof Bool b&&b.value(),"returned action history must retain original ok=true");
        HistorySource source=decodeSource(row.get(SOURCE_FIELD));StrictJson.require(source.operation().value().equals(string(row,"command")),"returned row changed original command");
        return new RawHistoryRow(integer(row,"index"),source,OpportunityJson.object(row.get("result"),"complete original result"));
    }
    public static HistorySource decodeSource(Value value){
        Obj row=OpportunityJson.object(value,SOURCE_FIELD);StrictJson.require(optionalEpochFields(row,SOURCE_FIELDS)&&new Text(SOURCE_SCHEMA).equals(row.get("schema"))&&new Text(FAMILY.name()).equals(row.get("family")),"closed returned action history source required");
        return new HistorySource(new OperationKey(string(row,"operation")),reference(row.get("canonical_receipt")),reference(row.get("canonical_record")),reference(row.get("acknowledgement")),reference(row.get("prepared_request")),
                new NativeRequestChronology.PacketIdentity(integer(row,"outbound_bytes"),string(row,"outbound_sha256")),reference(row.get("full_result")),PublicNumbers.fromJson(row.get("public_number_roles")),
                reference(row.get("before_driver")),reference(row.get("original_known")),reference(row.get("native_frame")),reference(row.get("driver_facts")),reference(row.get("invocation")),reference(row.get("caller")),optionalRef(row.get("epoch_manifest")),reference(row.get("projection_original")),
                integer(row,"head_sequence"),string(row,"head_digest"),readRefs(row.get("producer_sources"),1,MAXIMUM_SOURCE_REFERENCES),readRefs(row.get("projection_sources"),1,MAXIMUM_SOURCE_REFERENCES),readRefs(row.get("projection_evidence"),1,MAXIMUM_SOURCE_REFERENCES));
    }
    public static PublicNumbers publicNumbersFromSource(Value value){return decodeSource(value).publicNumbers();}
    private static DriverReturnedActionHistoryMaterial.StructuralCall requireOperation(OperationKey operation){
        return DriverReturnedActionHistoryMaterial.parse(Objects.requireNonNull(operation)).orElseThrow(()->new IllegalArgumentException("only original ARMY_STRUCTURE_COMMANDS selectors have this RETURNED history"));
    }
    private static void requireFiles(List<ExactRef> sources)throws IOException {for(var source:sources){var witness=SharedSourceFiles.observe(Path.of(source.path()));StrictJson.require(witness.source().bytes()==source.bytes()&&witness.source().sha256().equals(source.sha256()),"returned actual producer source bytes changed");SharedSourceFiles.assertUnchanged(witness);}}
    private static List<ExactRef> union(List<ExactRef> first,List<ExactRef> second){var all=new LinkedHashSet<ExactRef>(first);all.addAll(second);return List.copyOf(all);}
    private static List<ExactRef> refs(List<ExactRef> values,int min,int max){values=List.copyOf(values);StrictJson.require(values.size()>=min&&values.size()<=max&&new LinkedHashSet<>(values).size()==values.size(),"finite distinct returned source references required");values.forEach(DriverReturnedActionHistoryRowProducer::positive);return values;}
    private static List<ExactRef> readRefs(Value value,int min,int max){return refs(OpportunityJson.array(value,"returned source references").stream().map(DriverReturnedActionHistoryRowProducer::reference).toList(),min,max);}
    private static void positive(ExactRef reference){StrictJson.require(Objects.requireNonNull(reference).bytes()>0,"nonempty returned original required");}
    private static void head(long sequence,String digest){StrictJson.safe(sequence,0);StrictJson.require(digest!=null&&digest.matches("[0-9a-f]{64}"),"returned original actual writer point required");}
    private static RawJson full(OutcomeArchive bound,ExactRef reference){positive(reference);RawJson raw=bound.loadFullMaterial(reference);StrictJson.require(raw.bytes().length==reference.bytes()&&DriverJson.sha256(raw.bytes()).equals(reference.sha256())&&bound.materialReferenceOf(raw).equals(reference),"returned full original bytes/hash/archive role differ");return raw;}
    private static void requireMaterial(OutcomeArchive bound,ExactRef reference,RawJson expected){StrictJson.require(Arrays.equals(full(bound,reference).bytes(),expected.bytes()),"returned original full material changed");}
    private static Obj object(RawJson raw){return DriverJson.object(raw.bytes(),DriverJson.MAX_NATIVE_BYTES);}
    private static Obj closed(byte[] bytes,Set<String> fields){Obj row=DriverJson.object(bytes,DriverJson.MAX_NATIVE_BYTES);StrictJson.require(optionalEpochFields(row,fields),"closed returned action fields required");return row;}
    private static String string(Obj row,String name){return OpportunityJson.text(row.get(name),name);}
    private static long integer(Obj row,String name){return OpportunityJson.integer(row.get(name),name).longValueExact();}
    private static void requireText(Obj row,String name,String expected){StrictJson.require(new Text(expected).equals(row.get(name)),"returned report changed original "+name);}
    private static void requireInteger(Obj row,String name,BigInteger expected){StrictJson.require(new IntegerValue(expected).equals(row.get(name)),"returned report changed original "+name);}
    private static boolean optionalEpochFields(Obj row,Set<String> fields){var expected=new java.util.HashSet<>(fields);if(fields.contains("epoch_manifest")&&!row.members().containsKey("epoch_manifest"))expected.remove("epoch_manifest");return row.members().keySet().equals(expected);}
    private static Value optionalRef(Optional<ExactRef> value){return value.<Value>map(DriverReturnedActionHistoryRowProducer::ref).orElse(Nil.INSTANCE);}
    private static Optional<ExactRef> optionalRef(Value value){return value==null||value==Nil.INSTANCE?Optional.empty():Optional.of(reference(value));}
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    private static Obj ref(ExactRef reference){return DriverJson.object(StrictJson.canonical(reference.toJson()),DriverJson.MAX_NATIVE_BYTES);}
    private static Arr array(List<ExactRef> refs){return new Arr(refs.stream().<Value>map(DriverReturnedActionHistoryRowProducer::ref).toList());}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Text text(String value){return new Text(value);}
}
