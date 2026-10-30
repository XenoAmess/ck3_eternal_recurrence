package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import org.xar.ck3.control.application.history.*;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverReadHistoryFailureMaterial;
import org.xar.ck3.control.application.history.DriverPersistenceStatus;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer;
import org.xar.ck3.control.application.planning.finance.GiftResolvedEvidence;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.Candidate;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Retains original pure reads inside observation; commits their history only after that immutable scope ends. */
public final class DriverReadHistoryPublisher implements WriterContracts.TransitionAuthority {
    public static final String FAILED_ROW_KIND="ARMY_READ_FAILURE";
    public record Committed(WriterContracts.Head predecessor,WriterContracts.Receipt actual) {
        public Committed { Objects.requireNonNull(predecessor);Objects.requireNonNull(actual);
            StrictJson.require(actual.disposition()!=WriterContracts.Disposition.NO_CHANGE,"actual read-history commit required"); }
    }
    /** Retains the unchanged original receipt and the exact original typed decoder. Current eligibility is rechecked by the same owner. */
    public static final class CanonicalRead<T> {
        private final DriverReadHistoryPublisher owner;private final ReadContract<T> currentContract,originalContract;
        private final PlanningReadRequest currentRequest;private final PlanningReadResult.Known<T> original;
        private final ContinuityStorePort.Session issuedSession;private final Known issuedKnown;private final WriterContracts.Head issuedHead;
        private CanonicalRead(DriverReadHistoryPublisher owner,ReadContract<T> currentContract,PlanningReadRequest currentRequest,
                ReadContract<T> originalContract,PlanningReadResult.Known<T> original,ContinuityStorePort.Session issuedSession,Known issuedKnown,WriterContracts.Head issuedHead) {
            this.owner=owner;this.currentContract=currentContract;this.currentRequest=currentRequest;this.originalContract=originalContract;this.original=original;
            this.issuedSession=issuedSession;this.issuedKnown=issuedKnown;this.issuedHead=issuedHead;
        }
        public PlanningReadResult.Known<T> original(){return original;}
        public ReadContract<T> originalContract(){return originalContract;}
        public PlanningReadRequest currentRequest(){return currentRequest;}
        public PlanningReadResult.Known<T> requireCurrent(ContinuityStorePort.Session same,ReadContract<T> identicalCurrent,PlanningReadRequest actualCurrent) throws IOException {
            StrictJson.require(identicalCurrent==currentContract&&actualCurrent.equals(currentRequest),"canonical witness crossed its current installed query");
            return owner.authority.withFrozenFacts(same, frozen -> {
                StrictJson.require(frozen.state() instanceof Known,"canonical read requires the actual complete Driver owner");
                Known known=(Known)frozen.state();
                StrictJson.require(DriverStateAssembler.projectObservation(known,frozen.actions(),frozen.activeActionId()) instanceof DriverStateSnapshot.Complete,
                        "unresolved canonical actions cannot qualify an ordinary cached read");
                if (same == issuedSession && frozen.state() == issuedKnown && same.head() == issuedHead) {
                    var originals = owner.archive.withSession(same);
                    var read = originals.loadRead(original.originalReceipt());
                    StrictJson.require(read.equals(original.receipt()), "canonical original read DATA differs");
                    return original;
                }
                var current = owner.canonicalReadWitness(same, identicalCurrent, actualCurrent).orElseThrow(() -> new IOException("original canonical read no longer qualifies in the actual current frame"));
                StrictJson.require(current.originalContract == originalContract && current.original.originalReceipt().equals(original.originalReceipt())
                        && current.original.receipt().equals(original.receipt()), "canonical witness selected a different original source");
                return current.original;
            });
        }
    }
    /** Private producer proof of a complete canonical READ-only Driver extension. It grants no Crown or action eligibility itself. */
    public static final class ReadOnlyExtension {
        private final DriverReadHistoryPublisher owner;private final GuardEvidence queryGuard;private final DriverReadOnlyLineage.Verified verified;
        private ReadOnlyExtension(DriverReadHistoryPublisher owner,GuardEvidence queryGuard,DriverReadOnlyLineage.Verified verified) {
            this.owner=owner;this.queryGuard=queryGuard;this.verified=verified;
        }
        public DriverObservationAssembler.Complete queryObserved(){return verified.query();}
        public DriverObservationAssembler.Complete currentObserved(){return verified.current();}
        public ExactRef queryDriver(){return verified.queryDriver();}
        public ExactRef currentDriver(){return verified.currentDriver();}
        public List<ExactRef> eventSources(){return verified.events();}
        public ReadOnlyExtension requireCurrent(ContinuityStorePort.Session same) throws IOException {
            return owner.authority.withFrozenFacts(same,frozen -> {
                StrictJson.require(frozen.state() instanceof Known,"current actual Driver unavailable while rechecking READ-only lineage");
                var current=owner.requireReadOnlyExtension(same,queryGuard,verified.query(),(Known)frozen.state());
                StrictJson.require(current.verified.head().digest().equals(verified.head().digest())&&current.currentDriver().equals(currentDriver())
                        &&current.eventSources().equals(eventSources()),"READ-only extension changed after its private proof was minted");return current;
            });
        }
    }
    /** Historical READ DATA only. Its private constructor supplies no current frame, action guard or readiness. */
    public static final class HistoricalReadOnlyExtension {
        private final DriverReadHistoryPublisher owner;private final ContinuityStorePort.Session session;
        private final PlanningReadReceipt original;private final ExactRef originalReceipt;
        private final GuardEvidence targetGuard;private final DriverReadOnlyLineage.Verified verified;
        private HistoricalReadOnlyExtension(DriverReadHistoryPublisher owner,ContinuityStorePort.Session session,
                PlanningReadReceipt original,ExactRef originalReceipt,GuardEvidence targetGuard,DriverReadOnlyLineage.Verified verified) {
            this.owner=owner;this.session=session;this.original=original;this.originalReceipt=originalReceipt;this.targetGuard=targetGuard;this.verified=verified;
        }
        public PlanningReadReceipt originalRead(){return original;}
        public ExactRef originalReceipt(){return originalReceipt;}
        public DriverObservationAssembler.Complete queryObserved(){return verified.query();}
        public DriverObservationAssembler.Complete targetObserved(){return verified.current();}
        public ExactRef queryDriver(){return verified.queryDriver();}
        public ExactRef targetDriver(){return verified.currentDriver();}
        public List<ExactRef> eventSources(){return verified.events();}
        public org.xar.ck3.control.application.effects.RootGuardEvidence.WriterPoint targetWriterPoint(){return verified.targetPoint();}
        public HistoricalReadOnlyExtension requireHistorical(ContinuityStorePort.Session same) throws IOException {
            StrictJson.require(same==session,"historical READ proof escaped its original borrowed writer Session");
            var replay=owner.requireHistoricalReadOnlyExtension(same,original,targetGuard,verified.current());
            StrictJson.require(replay.originalReceipt.equals(originalReceipt)&&replay.verified.query().equals(verified.query())
                    &&replay.verified.current().equals(verified.current())&&replay.targetWriterPoint().equals(targetWriterPoint())
                    &&replay.queryDriver().equals(queryDriver())&&replay.targetDriver().equals(targetDriver())
                    &&replay.eventSources().equals(eventSources()),"historical READ endpoints or actual canonical interval changed");
            return replay;
        }
    }
    public static final String SUMMARY_ROW_KIND="ARMY_STRENGTHS_SUMMARY";
    public static final String EXECUTE_ROW_KIND="PUBLIC_EXECUTE_QUERY";
    public static final String PUBLIC_FAILURE_ROW_KIND="PUBLIC_EXECUTE_FAILURE";
    public static final String RETURNED_CONTROL_ROW_KIND="SAMPLING_CONTROL_RETURNED";
    private record PublicFailureItem(DriverPublicExecuteFailureMaterial.OriginalInvocation invocation,
            DriverPublicExecuteFailureRowProducer.Candidate candidate) { }
    private record ReturnedControlItem(DriverReturnedControlHistoryRowProducer.OriginalReturned invocation,
            DriverReturnedControlHistoryRowProducer.Candidate candidate) { }
    private record Item(ReadContract<?> contract,PlanningReadResult.Known<?> known,Candidate candidate) { }
    private record SummaryItem(ReadContract<?> contract,PlanningReadResult.Known<?> known,
            org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.Candidate candidate) { }
    private record ExecuteItem(ReadContract<?> contract,PlanningReadResult.Known<?> known,
            org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.Candidate candidate) { }
    private record Deferred(ReadContract<?> contract,PlanningReadResult.Known<?> known,Known before) { }
    private record ObservedItem(GiftResolvedEvidence.Inputs inputs,DriverObservedHistoryRowProducer.Candidate candidate) { }
    private record FreshGift(ContinuityStorePort.Session session,ReadContract<?> contract,PlanningReadResult.Known<?> known) { }
    private record FailedOriginal(ReadContract<?> contract,PlanningReadRequest request,PlanningReadResult.Unavailable<?> actual,
            PlanningReadCoordinator.FailedReadAttempt token,Known before) { }
    private record FailedItem(FailedOriginal original,DriverFailedReadHistoryRowProducer.Candidate candidate) { }
    public static final String POST_KNOWN_ROW_KIND="POST_KNOWN_READ_FAILURE",RETURNED_READ_ROW_KIND="RETURNED_PUBLIC_READ",RETURNED_ACTION_ROW_KIND="ARMY_STRUCTURE_RETURNED",EARLY_ROW_KIND="EARLY_EXECUTE_FAILURE";
    private record PostKnownItem(DriverPostKnownReadFailureRowProducer.Candidate candidate) { }
    private record ReturnedReadItem(DriverReturnedPublicReadHistoryMaterial.OriginalReturned invocation,DriverReturnedPublicReadHistoryRowProducer.Candidate candidate) { }
    private record ReturnedActionItem(DriverReturnedActionHistoryRowProducer.OriginalReturned invocation,DriverReturnedActionHistoryRowProducer.Candidate candidate) { }
    private record EarlyItem(DriverEarlyExecuteFailure.OriginalInvocation invocation,DriverEarlyExecuteFailureRowProducer.Candidate candidate) { }
    private static final class Queue {
        final ContinuityStorePort.Session session;final WriterContracts.Head head;final Known before;final ActionJournal.Snapshot baseline;
        WriterContracts.Head commitHead;org.xar.ck3.control.g2.common.G2Source source;
        final List<PostKnownItem> postKnown=new ArrayList<>();final List<ReturnedReadItem> returnedReads=new ArrayList<>();
        final List<ReturnedActionItem> returnedActions=new ArrayList<>();final List<EarlyItem> early=new ArrayList<>();
        final List<DriverPersistenceStatus.Attempt> storageAttempts=new ArrayList<>();
        final List<PublicFailureItem> publicFailures=new ArrayList<>();final List<ReturnedControlItem> returnedControls=new ArrayList<>();
        final List<Item> items=new ArrayList<>();final List<Deferred> deferred=new ArrayList<>();
        final List<SummaryItem> summaries=new ArrayList<>();
        final Set<ExactRef> invalidatedArmyCore=new LinkedHashSet<>();
        final List<ExecuteItem> executions=new ArrayList<>();
        final List<FailedOriginal> failedOriginals=new ArrayList<>();final List<FailedItem> failures=new ArrayList<>();
        final List<ObservedItem> observed=new ArrayList<>();Publication publication;WriterContracts.Prepared prepared;WriterContracts.Receipt receipt;boolean commitStarted;
        Queue(ContinuityStorePort.Session session,WriterContracts.Head head,Known before,ActionJournal.Snapshot baseline){this.session=session;this.head=head;this.before=before;this.baseline=baseline;source=before.observation().map(DriverObservationFacts::source).orElse(null);}
    }
    /** Only this publisher's actual archived-read preparation can mint a batch. */
    public static final class Publication {
        private final DriverReadHistoryPublisher owner;private final Queue queue;private final DriverStateSnapshot.Complete replacement;
        private final WriterContracts.Request request;private final ExactRef beforeDriver,afterDriver;
        private Publication(DriverReadHistoryPublisher owner,Queue queue,DriverStateSnapshot.Complete replacement,
                WriterContracts.Request request,ExactRef beforeDriver,ExactRef afterDriver) {
            this.owner=owner;this.queue=queue;this.replacement=replacement;this.request=request;this.beforeDriver=beforeDriver;this.afterDriver=afterDriver;
        }
        Known before(){return queue.before;}
        DriverStateSnapshot.Complete replacement(){return replacement;}
        boolean containsFailures(){return !queue.failures.isEmpty()||!queue.publicFailures.isEmpty()||!queue.returnedControls.isEmpty()||!queue.postKnown.isEmpty()||!queue.returnedReads.isEmpty()||!queue.returnedActions.isEmpty()||!queue.early.isEmpty();}
        WriterContracts.Request request(){return request;}
        void requireCurrent(ContinuityStorePort.Session same,WriterContracts.Prepared prepared) throws IOException {
            StrictJson.require(owner.pending.get()==queue&&queue.session==same&&queue.publication==this
                    &&prepared.request().identity().equals(request.identity())&&Arrays.equals(prepared.request().details(),request.details())
                    &&prepared.request().evidence().equals(request.evidence()),"read publication lost its actual private batch/request");
        }
    }
    private final DriverStateAssembler authority;
    private final ActionPorts.OutcomeArchive archive;
    private final RootReadContractCatalog catalog;
    private final List<ExactRef> sources;
    private final DriverPersistenceStatus persistenceStatus=new DriverPersistenceStatus(Optional.empty());
    private DriverReturnedPublicReadHistoryMaterial.Source returnedReadSource;
    private DriverReturnedActionHistoryRowProducer.Source returnedActionSource;
    private DriverEarlyExecuteFailure.Source earlyFailureSource;
    private DriverPublicExecuteFailureMaterial.Source publicFailureSource;
    private DriverReturnedControlHistoryRowProducer.Source returnedControlSource;
    private volatile java.util.function.Supplier<ContinuityStorePort.Session> armyCoreSessions;
    private final java.util.concurrent.atomic.AtomicReference<ExactRef> armyCoreUnavailable=new java.util.concurrent.atomic.AtomicReference<>();
    private final ThreadLocal<Queue> pending=new ThreadLocal<>();
    private final ThreadLocal<List<FreshGift>> freshGift=ThreadLocal.withInitial(ArrayList::new);
    public DriverReadHistoryPublisher(DriverStateAssembler authority,ActionPorts.OutcomeArchive archive,
            RootReadContractCatalog catalog,List<ExactRef> actualProducerSources) {
        this.authority=Objects.requireNonNull(authority);this.archive=Objects.requireNonNull(archive);this.catalog=Objects.requireNonNull(catalog);
        sources=List.copyOf(actualProducerSources);StrictJson.require(!sources.isEmpty()&&sources.size()<=64
                &&new LinkedHashSet<>(sources).size()==sources.size()&&sources.stream().allMatch(ref -> ref.bytes()>0),"actual finite read-publication sources required");
    }
    public void requireOwner(DriverStateAssembler same,ActionPorts.OutcomeArchive originals,RootReadContractCatalog installed) {
        StrictJson.require(authority==same&&archive==originals&&catalog==installed,"read publisher crossed its exact Driver/archive/catalog owner");
    }
    public RootReadContractCatalog catalog() { return catalog; }
    /** Same Root's technical cache only. The capabilities formatter separately preserves any original baseline error. */
    public DriverPersistenceStatus.Snapshot statusSnapshot(){return persistenceStatus.snapshot();}
    private void queued(Queue queue,String operation){queue.storageAttempts.add(persistenceStatus.dirty(operation));}
    private void lost(String operation,UncheckedIOException actual){
        var cause=actual.getCause();var ticket=persistenceStatus.dirty(operation);
        persistenceStatus.failed(ticket,new DriverPersistenceStatus.Failure(cause.getClass().getName(),Objects.toString(cause.getMessage(),""),Optional.empty()),DriverPersistenceStatus.FailureKind.LOST_ORIGINAL);
    }
    private void flushFailed(Queue queue,Exception actual){
        var cause=actual instanceof UncheckedIOException wrapped?wrapped.getCause():actual;
        var kind=queue.commitStarted&&queue.receipt==null?DriverPersistenceStatus.FailureKind.COMMIT_UNKNOWN:DriverPersistenceStatus.FailureKind.RETRYABLE;
        for(var ticket:queue.storageAttempts)persistenceStatus.failed(ticket,new DriverPersistenceStatus.Failure(cause.getClass().getName(),Objects.toString(cause.getMessage(),""),Optional.empty()),kind);
    }
    public static List<Class<?>> implementationTypes(){return List.of(DriverReadHistoryPublisher.class,DriverReadOnlyLineage.class,DriverUnresolvedHistoryLineage.class,DriverStateAssembler.class,DriverPersistenceStatus.class,org.xar.ck3.control.application.capabilities.DriverPersistenceCapabilities.class,DriverPostKnownReadFailureMaterial.class,DriverPostKnownReadFailureRowProducer.class,DriverReturnedPublicReadHistoryMaterial.class,DriverReturnedPublicReadHistoryRowProducer.class,DriverReturnedActionHistoryMaterial.class,DriverReturnedActionHistoryRowProducer.class,DriverEarlyExecuteFailure.class,DriverEarlyExecuteFailureRowProducer.class);}
    public synchronized void bindReturnedPublicReadSource(DriverReturnedPublicReadHistoryMaterial.Source actual){
        Objects.requireNonNull(actual);actual.requireOwner(authority,actual.journal(),archive,catalog);actual.requireCatalog(catalog);
        StrictJson.require(returnedReadSource==null||returnedReadSource==actual,"another returned-read issuer installed");returnedReadSource=actual;
    }
    public synchronized void bindReturnedActionHistorySource(DriverReturnedActionHistoryRowProducer.Source actual){
        Objects.requireNonNull(actual);actual.requireOwner(authority,actual.journal(),archive,catalog);actual.requireCatalog(catalog);
        StrictJson.require(returnedActionSource==null||returnedActionSource==actual,"another returned-action issuer installed");returnedActionSource=actual;
    }
    public synchronized void bindEarlyExecuteFailureSource(DriverEarlyExecuteFailure.Source actual){
        Objects.requireNonNull(actual);actual.requireOwner(authority,actual.journal(),archive,catalog);
        StrictJson.require(earlyFailureSource==null||earlyFailureSource==actual,"another early issuer installed");
        authority.bindEarlyExecuteFailureSource(actual,archive,catalog);earlyFailureSource=actual;
    }
    public void requirePostKnownFailureCustody(ContinuityStorePort.Session same,DriverStateAssembler actualAuthority,RootReadContractCatalog identicalCatalog,
            ReadContract<?> identicalFinal,PlanningReadResult.Known<?> actualFinal,List<? extends PlanningReadResult.Known<?>> earlier,Known exactBefore){
        Queue queue=pending.get();StrictJson.require(authority==actualAuthority&&catalog==identicalCatalog&&queue!=null&&queue.session==same&&catalog.containsIdentity(identicalFinal),"post-Known failure left its actual owner");
        var retained=queue.deferred.stream().anyMatch(value->value.contract()==identicalFinal&&value.known()==actualFinal&&value.before()==exactBefore);
        var finalized=queue.postKnown.stream().map(PostKnownItem::candidate).filter(value->value.identicalFinal()==identicalFinal&&value.finalKnown()==actualFinal&&value.before()==exactBefore).toList();
        StrictJson.require(retained||finalized.size()==1,"final read is not its private central custody object");
        for(var peer:earlier)StrictJson.require(queue.deferred.stream().anyMatch(value->value.known()==peer)||finalized.stream().anyMatch(value->value.earlierKnown().stream().anyMatch(original->original==peer)),"peer not retained by identity");
        if(!finalized.isEmpty())StrictJson.require(sameKnowns(finalized.getFirst().earlierKnown(),earlier),"peer order/identity changed");
    }
    private static boolean sameKnowns(List<? extends PlanningReadResult.Known<?>> a,List<? extends PlanningReadResult.Known<?>> b){if(a.size()!=b.size())return false;for(int i=0;i<a.size();i++)if(a.get(i)!=b.get(i))return false;return true;}
    public synchronized void bindPublicExecuteFailureSource(DriverPublicExecuteFailureMaterial.Source actual) {
        Objects.requireNonNull(actual);actual.requireOwner(authority,actual.journal(),archive,catalog);
        StrictJson.require(publicFailureSource==null||publicFailureSource==actual,"public failure issuer belongs to another Root");publicFailureSource=actual;
    }
    public synchronized void bindReturnedControlHistorySource(DriverReturnedControlHistoryRowProducer.Source actual) {
        Objects.requireNonNull(actual);actual.requireOwner(authority,actual.journal(),archive,catalog);actual.requireCatalog(catalog);
        StrictJson.require(returnedControlSource==null||returnedControlSource==actual,"returned issuer belongs to another Root");returnedControlSource=actual;
    }
    public static final class UnresolvedHistoryExtension {
        private final DriverReadHistoryPublisher owner;private final ContinuityStorePort.Session session;private final Known current;
        private final DriverUnresolvedHistoryLineage.Verified verified;
        private UnresolvedHistoryExtension(DriverReadHistoryPublisher owner,ContinuityStorePort.Session session,Known current,DriverUnresolvedHistoryLineage.Verified verified){this.owner=owner;this.session=session;this.current=current;this.verified=verified;}
        public ActionReceipt originalAction(){return verified.action();}
        public ExactRef originalDriver(){return verified.before();}
        public ExactRef currentDriver(){return verified.after();}
        public List<ExactRef> eventReferences(){return verified.events();}
        public UnresolvedHistoryExtension requireCurrent(ContinuityStorePort.Session same)throws IOException {
            StrictJson.require(same==session&&same.head().digest().equals(verified.target().digest()),"unresolved proof escaped its actual current writer Head");
            var replay=owner.requireUnresolvedHistoryExtension(same,originalAction(),originalDriver(),current);
            StrictJson.require(replay.currentDriver().equals(currentDriver())&&replay.eventReferences().equals(eventReferences()),"unresolved current history suffix changed");return replay;
        }
    }
    public static final class HistoricalUnresolvedHistoryExtension {
        private final DriverReadHistoryPublisher owner;private final ContinuityStorePort.Session session;private final DriverUnresolvedHistoryLineage.Verified verified;
        private HistoricalUnresolvedHistoryExtension(DriverReadHistoryPublisher owner,ContinuityStorePort.Session session,DriverUnresolvedHistoryLineage.Verified verified){this.owner=owner;this.session=session;this.verified=verified;}
        public ActionReceipt originalAction(){return verified.action();}
        public ExactRef originalDriver(){return verified.before();}
        public ExactRef currentDriver(){return verified.after();}
        public List<ExactRef> eventReferences(){return verified.events();}
        public HistoricalUnresolvedHistoryExtension requireHistorical(ContinuityStorePort.Session same)throws IOException {
            StrictJson.require(same==session,"historical unresolved proof escaped its borrowed writer");
            var replay=owner.requireHistoricalUnresolvedHistoryExtension(same,originalAction(),originalDriver(),currentDriver(),verified.target());
            StrictJson.require(replay.eventReferences().equals(eventReferences()),"historical unresolved canonical suffix changed");return replay;
        }
    }
    public UnresolvedHistoryExtension requireUnresolvedHistoryExtension(ContinuityStorePort.Session same,ActionReceipt actualUnresolved,
            ExactRef originalBeforeDriver,Known actualCurrent)throws IOException {
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==actualCurrent,"unresolved history requires the identical held current Driver owner");
            var bound=archive.withSession(same);ExactRef current=bound.materialReferenceOf(RawJson.fullMaterial(actualCurrent.driver().encode()));
            var verified=DriverUnresolvedHistoryLineage.verify(same,actualUnresolved,originalBeforeDriver,current,same.head(),bound,catalog,returnedControlSource,returnedActionSource);
            StrictJson.require(actualCurrent.stamp().driverVersion()==verified.version()&&actualCurrent.stamp().episodeEpoch()==verified.epoch()
                    &&actualCurrent.stamp().game().equals(actualUnresolved.command().before().game())
                    &&actualCurrent.stamp().episodeRunId().equals(actualUnresolved.command().before().frame().episodeRunId()),"unresolved suffix crossed the held actual Driver stamp");
            return new UnresolvedHistoryExtension(this,same,actualCurrent,verified);
        });
    }
    public HistoricalUnresolvedHistoryExtension requireHistoricalUnresolvedHistoryExtension(ContinuityStorePort.Session same,ActionReceipt actualOriginalUnknown,
            ExactRef originalBeforeDriver,ExactRef actualHistoricalCurrentDriver,WriterContracts.Head targetHead)throws IOException {
        var verified=DriverUnresolvedHistoryLineage.verify(same,actualOriginalUnknown,originalBeforeDriver,actualHistoricalCurrentDriver,targetHead,archive.withSession(same),catalog,returnedControlSource,returnedActionSource);
        return new HistoricalUnresolvedHistoryExtension(this,same,verified);
    }
    public DriverPublicExecuteFailureMaterial.Outcome enqueuePublicExecuteFailure(ContinuityStorePort.Session same,
            DriverPublicExecuteFailureMaterial.OriginalInvocation actual)throws IOException {
        Objects.requireNonNull(actual);StrictJson.require(publicFailureSource!=null&&actual.issuer()==publicFailureSource,"installed original failure issuer required");
        var bound=archive.withSession(same);var original=publicFailureSource.requireOriginal(same,authority,bound,actual);
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual current Driver unavailable for original failure");Known current=(Known)frozen.state();
            requireHistoricalSubject(original.before(),current);Queue queue=retainQueue(same,frozen,current);retainEventSource(queue,original.before());
            for(var item:queue.publicFailures)if(item.invocation()==actual){requirePublicFailure(same,item,bound);return new DriverPublicExecuteFailureMaterial.Queued(item.candidate().rowReference());}
            for(var entry:current.driver().commandHistory()){
                var raw=DriverJson.object(entry.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);if(!raw.members().containsKey(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD))continue;
                var row=DriverPublicExecuteFailureRowProducer.decode(entry.originalRow().json());if(!row.source().invocation().equals(original.invocation()))continue;
                DriverPublicExecuteFailureRowProducer.replayOriginals(bound,row);publicFailureSource.release(actual);removeEmpty();return new DriverPublicExecuteFailureMaterial.Queued(bound.materialReferenceOf(RawJson.fullMaterial(row.encode())));
            }
            StrictJson.require(rowCount(queue)<128,"finite original failure batch exhausted");
            try {
                var candidate=DriverPublicExecuteFailureRowProducer.prepare(same,bound,authority,actual,Math.addExact(current.driver().commandHistory().size(),rowCount(queue)+1L),sources);
                queue.publicFailures.add(new PublicFailureItem(actual,candidate));queued(queue,candidate.row().command());return new DriverPublicExecuteFailureMaterial.Queued(candidate.rowReference());
            }catch(UncheckedIOException storage){lost(original.originalCommand().value(),storage);publicFailureSource.release(actual);removeEmpty();return new DriverPublicExecuteFailureMaterial.StorageDiagnostic(storage.getCause().getClass().getName(),Objects.toString(storage.getCause().getMessage(),""));}
        });
    }
    public DriverReturnedControlHistoryRowProducer.Outcome enqueueReturnedControl(ContinuityStorePort.Session same,
            DriverReturnedControlHistoryRowProducer.OriginalReturned actual)throws IOException {
        Objects.requireNonNull(actual);StrictJson.require(returnedControlSource!=null&&actual.issuer()==returnedControlSource,"installed returned-control issuer required");
        var bound=archive.withSession(same);var original=returnedControlSource.requireOriginal(same,authority,bound,actual);
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual current Driver unavailable for returned history");Known current=(Known)frozen.state();
            requireHistoricalSubject(original.before(),current);Queue queue=retainQueue(same,frozen,current);retainEventSource(queue,original.before());
            for(var item:queue.returnedControls)if(item.invocation()==actual){DriverReturnedControlHistoryRowProducer.replay(same,bound,authority,returnedControlSource,catalog,item.candidate());return new DriverReturnedControlHistoryRowProducer.Queued(item.candidate().rowReference());}
            for(var entry:current.driver().commandHistory()){
                var raw=DriverJson.object(entry.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);if(!raw.members().containsKey(DriverReturnedControlHistoryRowProducer.SOURCE_FIELD))continue;
                var row=DriverReturnedControlHistoryRowProducer.decode(entry.originalRow().json());if(!row.source().canonicalReceipt().equals(original.canonicalReceipt()))continue;
                DriverReturnedControlHistoryRowProducer.replayOriginals(bound,catalog,returnedControlSource,row);returnedControlSource.release(actual);removeEmpty();return new DriverReturnedControlHistoryRowProducer.Queued(bound.materialReferenceOf(RawJson.fullMaterial(row.encode())));
            }
            StrictJson.require(rowCount(queue)<128,"finite returned-control batch exhausted");
            try {
                var candidate=DriverReturnedControlHistoryRowProducer.prepare(same,bound,authority,actual,Math.addExact(current.driver().commandHistory().size(),rowCount(queue)+1L),sources);
                queue.returnedControls.add(new ReturnedControlItem(actual,candidate));queued(queue,candidate.row().command());return new DriverReturnedControlHistoryRowProducer.Queued(candidate.rowReference());
            }catch(UncheckedIOException storage){lost(original.actual().command().operation().value(),storage);returnedControlSource.release(actual);removeEmpty();return new DriverReturnedControlHistoryRowProducer.StorageDiagnostic(storage.getCause().getClass().getName(),Objects.toString(storage.getCause().getMessage(),""));}
        });
    }
    public DriverReturnedActionHistoryRowProducer.Outcome enqueueReturnedAction(ContinuityStorePort.Session same,
            DriverReturnedActionHistoryRowProducer.OriginalReturned actual)throws IOException {
        Objects.requireNonNull(actual);StrictJson.require(returnedActionSource!=null&&actual.issuer()==returnedActionSource,"installed returned-control issuer required");
        var bound=archive.withSession(same);var original=returnedActionSource.requireOriginal(same,authority,bound,actual);
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual current Driver unavailable for returned history");Known current=(Known)frozen.state();
            requireHistoricalSubject(original.before(),current);Queue queue=retainQueue(same,frozen,current);retainEventSource(queue,original.before());
            for(var item:queue.returnedActions)if(item.invocation()==actual){DriverReturnedActionHistoryRowProducer.replay(same,bound,authority,returnedActionSource,catalog,item.candidate());return new DriverReturnedActionHistoryRowProducer.Queued(item.candidate().rowReference());}
            for(var entry:current.driver().commandHistory()){
                var raw=DriverJson.object(entry.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);if(!raw.members().containsKey(DriverReturnedActionHistoryRowProducer.SOURCE_FIELD))continue;
                var row=DriverReturnedActionHistoryRowProducer.decode(entry.originalRow().json());if(!row.source().canonicalReceipt().equals(original.canonicalReceipt()))continue;
                DriverReturnedActionHistoryRowProducer.replayOriginals(bound,catalog,returnedActionSource,row);returnedActionSource.release(actual);removeEmpty();return new DriverReturnedActionHistoryRowProducer.Queued(bound.materialReferenceOf(RawJson.fullMaterial(row.encode())));
            }
            StrictJson.require(rowCount(queue)<128,"finite returned-control batch exhausted");
            try {
                var candidate=DriverReturnedActionHistoryRowProducer.prepare(same,bound,authority,actual,Math.addExact(current.driver().commandHistory().size(),rowCount(queue)+1L),sources);
                queue.returnedActions.add(new ReturnedActionItem(actual,candidate));queued(queue,candidate.row().command());return new DriverReturnedActionHistoryRowProducer.Queued(candidate.rowReference());
            }catch(UncheckedIOException storage){lost(original.actual().command().operation().value(),storage);returnedActionSource.release(actual);removeEmpty();return new DriverReturnedActionHistoryRowProducer.StorageDiagnostic(storage.getCause().getClass().getName(),Objects.toString(storage.getCause().getMessage(),""));}
        });
    }
    public DriverReturnedPublicReadHistoryMaterial.Outcome enqueueReturnedPublicRead(ContinuityStorePort.Session same,
            DriverReturnedPublicReadHistoryMaterial.OriginalReturned actual)throws IOException {
        Objects.requireNonNull(actual);StrictJson.require(returnedReadSource!=null&&actual.issuer()==returnedReadSource,"installed returned-control issuer required");
        var bound=archive.withSession(same);var original=returnedReadSource.requireOriginal(same,authority,bound,actual);
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual current Driver unavailable for returned history");Known current=(Known)frozen.state();
            requireHistoricalSubject(original.before(),current);Queue queue=retainQueue(same,frozen,current);retainEventSource(queue,original.before());
            for(var item:queue.returnedReads)if(item.invocation()==actual){DriverReturnedPublicReadHistoryRowProducer.replay(same,bound,authority,returnedReadSource,catalog,item.candidate());return new DriverReturnedPublicReadHistoryMaterial.Queued(item.candidate().rowReference());}
            for(var entry:current.driver().commandHistory()){
                var raw=DriverJson.object(entry.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);if(!raw.members().containsKey(DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD))continue;
                var row=DriverReturnedPublicReadHistoryRowProducer.decode(entry.originalRow().json());if(!row.source().invocation().equals(original.invocation()))continue;
                DriverReturnedPublicReadHistoryRowProducer.replayOriginals(bound,catalog,returnedReadSource,row);returnedReadSource.release(actual);removeEmpty();return new DriverReturnedPublicReadHistoryMaterial.Queued(bound.materialReferenceOf(RawJson.fullMaterial(row.encode())));
            }
            StrictJson.require(rowCount(queue)<128,"finite returned-control batch exhausted");
            try {
                var candidate=DriverReturnedPublicReadHistoryRowProducer.prepare(same,bound,authority,actual,Math.addExact(current.driver().commandHistory().size(),rowCount(queue)+1L),sources);
                queue.returnedReads.add(new ReturnedReadItem(actual,candidate));queued(queue,candidate.row().command());return new DriverReturnedPublicReadHistoryMaterial.Queued(candidate.rowReference());
            }catch(UncheckedIOException storage){lost(original.originalCommand().value(),storage);returnedReadSource.release(actual);removeEmpty();return new DriverReturnedPublicReadHistoryMaterial.StorageDiagnostic(storage.getCause().getClass().getName(),Objects.toString(storage.getCause().getMessage(),""));}
        });
    }
    public DriverEarlyExecuteFailure.Outcome enqueueEarlyExecuteFailure(ContinuityStorePort.Session same,DriverEarlyExecuteFailure.OriginalInvocation actual)throws IOException{
        Objects.requireNonNull(actual);StrictJson.require(earlyFailureSource!=null&&actual.issuer()==earlyFailureSource,"installed private early issuer required");
        authority.requireEarlyExecuteFailureSource(earlyFailureSource);var bound=archive.withSession(same);var original=earlyFailureSource.requireOriginal(same,authority,bound,actual);
        if(original.retained() instanceof DriverEarlyExecuteFailure.Absent absent){earlyFailureSource.release(actual);return new DriverEarlyExecuteFailure.MissingFacts(absent.reason());}
        var cached=(DriverEarlyExecuteFailure.Cached)original.retained();
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==cached.before(),"early exception lost its identical real cached predecessor");
            Known current=cached.before();Queue queue=retainQueue(same,frozen,current);
            for(var item:queue.early)if(item.invocation()==actual){replayEarly(same,bound,item);return new DriverEarlyExecuteFailure.Queued(item.candidate().rowReference());}
            // NO_FRESH_FRAME is one mutually exclusive public invocation phase, never mixed with in-scope final components.
            StrictJson.require(rowCount(queue)==0&&queue.deferred.isEmpty(),"early exception cannot borrow another pending query batch");
            DriverEarlyExecuteFailureRowProducer.Preparation prepared;
            try{prepared=DriverEarlyExecuteFailureRowProducer.prepare(same,bound,authority,actual,Math.addExact(current.driver().commandHistory().size(),1L),sources);}
            catch(UncheckedIOException storage){lost(original.originalCommand().value(),storage);earlyFailureSource.release(actual);removeEmpty();return new DriverEarlyExecuteFailure.StorageDiagnostic(storage.getCause().getClass().getName(),Objects.toString(storage.getCause().getMessage(),""));}
            if(prepared instanceof DriverEarlyExecuteFailure.MissingFacts missing){earlyFailureSource.release(actual);removeEmpty();return missing;}
            var candidate=(DriverEarlyExecuteFailureRowProducer.Candidate)prepared;StrictJson.require(candidate.before()==current,"early candidate belongs to a different cached owner");
            queue.early.add(new EarlyItem(actual,candidate));queued(queue,candidate.row().command());return new DriverEarlyExecuteFailure.Queued(candidate.rowReference());
        });
    }
    private void replayEarly(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive bound,EarlyItem item)throws IOException{
        authority.requireEarlyExecuteFailureSource(earlyFailureSource);var actual=earlyFailureSource.requireOriginal(same,authority,bound,item.invocation());
        var candidate=item.candidate();StrictJson.require(actual.retained() instanceof DriverEarlyExecuteFailure.Cached cached&&cached.before()==candidate.before()
                &&actual.invocation().equals(candidate.source().invocation()),"early original lost its private cached identity");
        var producers=new LinkedHashSet<>(actual.producerSources());producers.addAll(sources);var data=DriverEarlyExecuteFailure.invocationData(actual);
        var expected=new DriverEarlyExecuteFailure.InvocationData(data.originalCommand(),data.error(),data.result(),data.publicNumbers(),data.retained(),data.caller(),data.epochManifest(),data.unsupportedCapabilities(),data.unresolvedAction(),data.headSequence(),data.headDigest(),List.copyOf(producers));
        StrictJson.require(expected.equals(candidate.source().data())&&candidate.headSequence()==same.head().state().sequence()&&candidate.headDigest().equals(same.head().digest()),"early original data/head changed");
        DriverEarlyExecuteFailureRowProducer.replayOriginals(bound,candidate.row());
    }
    private static void retainEventSource(Queue queue,Known original){
        var actual=original.observation().orElseThrow(()->new IllegalArgumentException("original invocation observation source required"));
        if(queue.source==null)queue.source=actual.source();else StrictJson.require(queue.source.equals(actual.source()),"original failure source changed");
    }
    private static void requireHistoricalSubject(Known entry,Known current){
        StrictJson.require(entry.stamp().game().equals(current.stamp().game())&&entry.stamp().episodeEpoch()==current.stamp().episodeEpoch()
                &&entry.stamp().episodeRunId().equals(current.stamp().episodeRunId())&&entry.stamp().driverVersion()<=current.stamp().driverVersion(),"original invocation crossed current Game/run/epoch/version");
        var old=entry.driver();var now=current.driver();
        var projected=new DriverStateSnapshot.Complete(now.session(),old.commandHistory(),now.lastCheckpoint(),now.rollbackWarFailure(),now.managedRestoreTransaction(),now.successionExpectation(),now.successionLifecycle(),now.campaignGoal(),now.rollbackWarFailures());
        StrictJson.require(Arrays.equals(old.encode(),projected.encode())&&now.commandHistory().size()>=old.commandHistory().size(),"original error cannot hide a changed Driver business slot");
        for(int i=0;i<old.commandHistory().size();i++)StrictJson.require(Arrays.equals(old.commandHistory().get(i).originalRow().json(),now.commandHistory().get(i).originalRow().json()),"original invocation history prefix changed");
    }
    public ReadOnlyExtension requireReadOnlyExtension(ContinuityStorePort.Session same,GuardEvidence originalQueryGuard,
            DriverObservationAssembler.Complete actualQueryObserved,Known exactCurrent) throws IOException {
        return authority.withFrozenFacts(same,frozen -> {
            StrictJson.require(frozen.state()==exactCurrent,"READ-only lineage must use the actual same held current Driver owner");
            var verified=DriverReadOnlyLineage.verify(same,originalQueryGuard,actualQueryObserved,exactCurrent,archive.withSession(same),catalog);
            return new ReadOnlyExtension(this,originalQueryGuard,verified);
        });
    }
    /** Strict original query -> original target interval; later canonical transitions are not absorbed or waived. */
    public HistoricalReadOnlyExtension requireHistoricalReadOnlyExtension(ContinuityStorePort.Session same,
            PlanningReadReceipt actualOriginalRead,GuardEvidence actualTargetGuard,DriverObservationAssembler.Complete actualTargetObserved) throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(actualOriginalRead);Objects.requireNonNull(actualTargetGuard);Objects.requireNonNull(actualTargetObserved);
        ActionPorts.OutcomeArchive originals=archive.withSession(same);
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(actualOriginalRead,originals);
        ExactRef originalReceipt=originals.readReferenceOf(actualOriginalRead);
        var queryGuard=actualOriginalRead.before().binding();
        var query=originalQueryObserved(queryGuard,originals);
        var verified=DriverReadOnlyLineage.verifyHistorical(same,queryGuard,query,actualTargetGuard,actualTargetObserved,originals,catalog);
        StrictJson.require(verified.readReceipts().contains(originalReceipt),
                "the original query has no actual canonical READ publication inside the verified historical interval");
        return new HistoricalReadOnlyExtension(this,same,actualOriginalRead,originalReceipt,actualTargetGuard,verified);
    }
    /** Explicit domain opt-in: this returns the unchanged original receipt, never a newly dated native read. */
    public <T> Optional<PlanningReadResult.Known<T>> canonicalRead(ContinuityStorePort.Session same,
            ReadContract<T> identicalInstalled,PlanningReadRequest current) throws IOException {
        return canonicalReadWitness(same,identicalInstalled,current).map(CanonicalRead::original);
    }
    public <T> Optional<CanonicalRead<T>> canonicalReadWitness(ContinuityStorePort.Session same,
            ReadContract<T> identicalInstalled,PlanningReadRequest current) throws IOException {
        StrictJson.require(catalog.containsIdentity(identicalInstalled)&&identicalInstalled.operation().equals(current.operation())
                &&current.origin() instanceof CommandOrigin.Gameplay,"canonical read requires the identical installed ordinary query");
        var installed=catalog.installed().stream().filter(binding -> binding.contract()==identicalInstalled).toList();
        StrictJson.require(installed.size()==1,"one actual original decoder source required for a cached read");
        ActionPorts.OutcomeArchive originals=archive.withSession(same);

        return authority.withFrozenFacts(same,frozen -> {
            StrictJson.require(frozen.state() instanceof Known,"canonical read requires the actual complete Driver owner");Known known=(Known)frozen.state();
            StrictJson.require(DriverStateAssembler.projectObservation(known,frozen.actions(),frozen.activeActionId()) instanceof DriverStateSnapshot.Complete,
                    "unresolved canonical actions cannot qualify an ordinary cached read");
            var observed=known.observation().orElseThrow();var frame=current.before().frame();
            StrictJson.require(current.before().game().equals(known.stamp().game())&&frame.episodeRunId().equals(known.stamp().episodeRunId())
                    &&frame.identity().player().equals(known.driver().session().actorId())&&frame.snapshotId().equals(observed.snapshotId())
                    &&frame.revision().equals(observed.publicRevision())&&frame.identity().nativeRevision().equals(observed.nativeRevision())
                    &&current.before().observationVersion()==observed.observationVersion()&&current.source().equals(observed.source())
                    &&current.sessionId().equals(observed.transport().sessionId()),"canonical read lookup crossed the current original native frame/source");
            ExactRef nativeCurrent=DriverObservationEvidenceReader.reference(known.auxiliary().get("capability_observed_native_source"));
            byte[] nativeCurrentBytes=originals.loadNativeFrame(nativeCurrent);
            StrictJson.require(nativeCurrentBytes.length==nativeCurrent.bytes()&&DriverJson.sha256(nativeCurrentBytes).equals(nativeCurrent.sha256()),"canonical current original Native packet differs");
            var manifest=originals.loadFullMaterial(observed.semanticFactsEvidence());
            var actualFrame=DriverObservationEvidenceReader.nativeFrame(observed.semanticFactsEvidence(),manifest,nativeCurrentBytes);
            var joined=new DriverObservationAssembler().assemble(actualFrame,observed,nativeCurrent);
            StrictJson.require(joined instanceof DriverObservationAssembler.Complete,"canonical reuse requires complete actual current facts");
            var currentComplete=(DriverObservationAssembler.Complete)joined;
            StrictJson.require(currentComplete.identity().equals(current.before())&&currentComplete.source().equals(current.source())
                    &&currentComplete.sessionId().equals(current.sessionId()),"current canonical request differs from actual full producer");
            if(identicalInstalled.requiredCapability().isPresent()) {
                var diagnostics=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(currentComplete.semantic().get("diagnostics"),"diagnostics");
                var hello=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(diagnostics.get("hello"),"actual hello");
                var capabilities=org.xar.ck3.control.planning.opportunity.OpportunityJson.array(hello.get("capabilities"),"capabilities");
                StrictJson.require(capabilities.contains(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(identicalInstalled.requiredCapability().orElseThrow())),"canonical query lacks its actual current advertised capability");
            }
            var history=known.driver().commandHistory();
            for(int index=history.size()-1;index>=0;index--) {
                byte[] bytes=history.get(index).originalRow().json();var originalRow=DriverJson.object(bytes,DriverJson.MAX_NATIVE_BYTES);
                if(originalRow.members().containsKey(DriverFailedReadHistoryRowProducer.SOURCE_FIELD))break;
                if(!originalRow.members().containsKey(DriverReadHistoryRowProducer.SOURCE_FIELD))continue;
                var row=DriverReadHistoryRowProducer.decode(bytes);var source=row.provenance();
                boolean readOnlyReusable=source.kind()==DriverReadHistoryRowProducer.Kind.CAMPAIGN_ROOT_CONTEXT
                        ||source.kind()==DriverReadHistoryRowProducer.Kind.GIFT_COLD_RECOVERY;
                if(!row.command().equals(current.operation().value())||(!readOnlyReusable&&!source.sourceFrame().equals(current.before()))||!source.source().equals(current.source())
                        ||!source.sessionId().equals(current.sessionId())||!source.arguments().equals(current.arguments())
                        ||!source.connectionGeneration().equals(observed.transport().connectionGeneration()))continue;
                StrictJson.require(source.definitionSource().equals(identicalInstalled.sourceRef())&&source.decoderSource().equals(installed.getFirst().decoderSource()),
                        "canonical read source differs from the identical currently installed definition/decoder");
                var read=originals.loadRead(source.originalReceipt());ExactRef originalNative=read.before().binding().nativeEvidence();
                if(originalNative.bytes()!=nativeCurrent.bytes()||!originalNative.sha256().equals(nativeCurrent.sha256()))continue;
                StrictJson.require(Arrays.equals(originals.loadNativeFrame(originalNative),nativeCurrentBytes),"canonical original Native packet bytes differ");
                var originalContract=catalog.originalContract(identicalInstalled,source.contractId());if(originalContract.isEmpty())continue;
                ReadContract<T> original=originalContract.orElseThrow();
                var replayed=DriverReadHistoryRowProducer.replayCanonical(originals,catalog,original,row);
                try { original.requireCanonicalReuse(replayed.receipt(),replayed.value(),current,currentComplete.semantic()); }
                catch(IllegalArgumentException mismatch) {continue;}
                if(readOnlyReusable) {
                    // Only finite PUBLIC_ROOT/GIFT_COLD_RECOVERY producers admit this branch. A domain opt-in is
                    // necessary, but the unchanged original receipt never proves its own current Driver lineage.
                    try {
                        var query=originalQueryObserved(replayed.receipt().before().binding(),originals);
                        var extension=requireReadOnlyExtension(same,replayed.receipt().before().binding(),query,known);
                        StrictJson.require(extension.currentObserved().equals(currentComplete),
                                "typed canonical lineage left the exact current complete Driver/native projection");
                    } catch(IllegalArgumentException stale) {continue;}
                }
                return Optional.of(new CanonicalRead<>(this,identicalInstalled,current,original,replayed,same,known,same.head()));
            }
            return Optional.empty();
        });
    }
    private static DriverObservationAssembler.Complete originalQueryObserved(GuardEvidence actualOriginal,ActionPorts.OutcomeArchive originals) {
        var basis=org.xar.ck3.control.application.effects.RootGuardEvidence.frameBasis(actualOriginal,originals);
        RawJson manifest=originals.loadFullMaterial(basis.driverFacts());
        ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(),manifest);
        var actual=DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(),manifest,originals.loadNativeFrame(basis.nativeFrame()));
        var facts=DriverObservationEvidenceReader.decode(basis.driverFacts(),manifest,originals.loadFullMaterial(driver),actual);
        var joined=new DriverObservationAssembler().assemble(actual,facts,basis.nativeFrame());
        StrictJson.require(joined instanceof DriverObservationAssembler.Complete,
                "typed canonical reuse requires its actual complete original query manifest/native frame");
        return (DriverObservationAssembler.Complete)joined;
    }
    public boolean hasPending(ContinuityStorePort.Session same) {
        Queue queue=pending.get();if(queue==null)return false;StrictJson.require(queue.session==same,"read queue belongs to another original writer scope");return !queue.items.isEmpty()||!queue.summaries.isEmpty()||!queue.executions.isEmpty()||!queue.deferred.isEmpty()||!queue.observed.isEmpty()||!queue.failures.isEmpty()||!queue.publicFailures.isEmpty()||!queue.returnedControls.isEmpty()||!queue.postKnown.isEmpty()||!queue.returnedReads.isEmpty()||!queue.returnedActions.isEmpty()||!queue.early.isEmpty();
    }
    private static int rowCount(Queue queue){return queue.items.size()+queue.summaries.size()+queue.executions.size()+queue.observed.size()+queue.failures.size()+queue.publicFailures.size()+queue.returnedControls.size()+queue.postKnown.size()+queue.returnedReads.size()+queue.returnedActions.size()+queue.early.size();}
    /** The central opaque attempt is retained as the identical live object, never reconstructed from unavailable DATA. */
    public void retainUnavailable(ContinuityStorePort.Session same,ReadContract<?> installed,PlanningReadRequest request,
            PlanningReadResult.Unavailable<?> actual,Optional<PlanningReadCoordinator.FailedReadAttempt> original) {
        Objects.requireNonNull(original);Objects.requireNonNull(actual);
        if(!failedKind(installed,request))return;
        if(original.isEmpty()){
            // A Known observer can fail after privately retaining its result. That is not a failed Native attempt.
            Queue queue=pending.get();if(queue!=null&&queue.session==same){
                queue.deferred.removeIf(value->value.contract()==installed&&value.known().receipt().request()==request);removeEmpty();
            }
            return;
        }
        StrictJson.require(catalog.containsIdentity(installed),"failed contract is not installed in this same publisher");
        try {authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual failed read Driver predecessor unavailable");
            Known before=(Known)frozen.state();var token=original.orElseThrow();
            token.requireOriginal(same,installed,request,actual,archive.withSession(same));
            Queue queue=retainQueue(same,frozen,before);
            StrictJson.require(queue.head.state().sequence()==token.headSequence()&&queue.head.digest().equals(token.headDigest()),
                    "failed read cannot join a batch from another original writer head");
            for(var retained:queue.failedOriginals)if(retained.actual()==actual){
                StrictJson.require(retained.contract()==installed&&retained.request()==request&&retained.token()==token,
                        "same unavailable object changed its actual central attempt");return null;
            }
            StrictJson.require(queue.failedOriginals.size()<128,"finite original failed read custody exhausted");
            queue.failedOriginals.add(new FailedOriginal(installed,request,actual,token,before));return null;
        });}catch(IOException failure){throw new UncheckedIOException("actual failed read original retention unavailable",failure);}
    }
    private static boolean failedKind(ReadContract<?> contract,PlanningReadRequest request){
        return contract.originalHistoryKind().filter(kind->kind==DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS).isPresent()
                &&request.origin() instanceof CommandOrigin.Gameplay&&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&request.operation().value().equals(DriverFailedReadHistoryRowProducer.STEP);
    }
    /** Final service failure only. There is no successful receipt, after-frame or caller error/result parameter. */
    public <T> DriverReadHistoryFailureMaterial.Outcome enqueueFailedRich(ReadContract<T> installed,
            PlanningReadResult.Unavailable<T> actual,List<? extends PlanningReadResult.Known<?>> actualEarlierComponents) {
        Objects.requireNonNull(installed);Objects.requireNonNull(actual);var components=List.copyOf(actualEarlierComponents);
        Queue queue=pending.get();
        if(queue==null)return new DriverReadHistoryFailureMaterial.Unrecorded(DriverReadHistoryFailureMaterial.Reason.NO_ORIGINAL_ATTEMPT,"no actual central failed attempt in this writer scope");
        var matches=queue.failedOriginals.stream().filter(value->value.actual()==actual).toList();
        if(matches.isEmpty())return new DriverReadHistoryFailureMaterial.Unrecorded(DriverReadHistoryFailureMaterial.Reason.NO_ORIGINAL_ATTEMPT,"unavailable has no identical live failed attempt");
        StrictJson.require(matches.size()==1&&matches.getFirst().contract()==installed,"failed service changed its installed contract or original object");
        var original=matches.getFirst();
        if(!failedKind(installed,original.request()))return new DriverReadHistoryFailureMaterial.Unrecorded(DriverReadHistoryFailureMaterial.Reason.UNSUPPORTED_CAUSE,"cause has no original failed Army recording contract");
        try{return authority.withFrozenFacts(queue.session,frozen->{
            StrictJson.require(frozen.state() instanceof Known&&retainQueue(queue.session,frozen,(Known)frozen.state())==queue,"failed service escaped its actual Driver scope");
            StrictJson.require(queue.head.digest().equals(queue.session.head().digest())&&queue.head.state().sequence()==original.token().headSequence(),"failed service writer head advanced");
            original.token().requireOriginal(queue.session,installed,original.request(),actual,archive.withSession(queue.session));
            StrictJson.require(components.size()<=1,"failed Army comparison has at most one earlier actual component");
            for(var retained:queue.failures)if(retained.original()==original){
                StrictJson.require(retained.candidate().source().componentReceipts().equals(components.stream().map(PlanningReadResult.Known::originalReceipt).toList()),"repeated failed component set changed");
                DriverFailedReadHistoryRowProducer.replay(archive.withSession(queue.session),catalog,retained.candidate());
                return new DriverReadHistoryFailureMaterial.Queued(retained.candidate().rowReference());
            }
            for(var component:components){
                var retained=queue.deferred.stream().filter(value->value.known()==component).toList();
                StrictJson.require(retained.size()==1,"earlier failed comparison component was not retained by the same central scope");
            }
            StrictJson.require(rowCount(queue)<128,"finite failed publication batch exhausted");
            DriverFailedReadHistoryRowProducer.Candidate candidate;
            try{candidate=DriverFailedReadHistoryRowProducer.prepare(queue.session,archive.withSession(queue.session),catalog,installed,
                    original.request(),actual,original.token(),original.before(),components,
                    Math.addExact(queue.before.driver().commandHistory().size(),rowCount(queue)+1L),sources);
            }catch(UncheckedIOException storage){
                lost(installed.operation().value(),storage);queue.failedOriginals.remove(original);queue.deferred.removeIf(value->components.stream().anyMatch(component->component==value.known()));removeEmpty();
                return new DriverReadHistoryFailureMaterial.StorageDiagnostic(storage.getCause().getClass().getName(),Objects.toString(storage.getCause().getMessage(),""));
            }
            queue.failures.add(new FailedItem(original,candidate));queued(queue,candidate.row().command());
            queue.deferred.removeIf(value->components.stream().anyMatch(component->component==value.known()));
            return new DriverReadHistoryFailureMaterial.Queued(candidate.rowReference());
        });}catch(IOException failure){throw new UncheckedIOException("actual failed service history scope unavailable",failure);}
    }
    public <T> DriverPostKnownReadFailureMaterial.Outcome enqueuePostKnownFailure(ReadContract<T> installed,
            PlanningReadResult.Known<T> actual,List<? extends PlanningReadResult.Known<?>> actualEarlier){
        Objects.requireNonNull(installed);Objects.requireNonNull(actual);var earlier=List.copyOf(actualEarlier);Queue queue=pending.get();
        if(installed.postKnownFailureKind().isEmpty())return new DriverPostKnownReadFailureMaterial.Unrecorded(DriverPostKnownReadFailureMaterial.Reason.NO_INSTALLED_VERIFIER,"no installed finite pure failure verifier");
        if(queue==null)return new DriverPostKnownReadFailureMaterial.Unrecorded(DriverPostKnownReadFailureMaterial.Reason.NO_LIVE_ORIGINALS,"no private central read custody");
        try{return authority.withFrozenFacts(queue.session,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"post-Known failure has no actual complete predecessor");Known before=(Known)frozen.state();
            requirePostKnownFailureCustody(queue.session,authority,catalog,installed,actual,earlier,before);retainQueue(queue.session,frozen,before);
            for(var item:queue.postKnown)if(item.candidate().finalKnown()==actual){
                replayPostKnown(queue.session,archive.withSession(queue.session),item);return new DriverPostKnownReadFailureMaterial.Queued(item.candidate().rowReference());}
            if(installed.reproducePostKnownFailure(actual.receipt(),earlier.stream().map(PlanningReadResult.Known::receipt).toList()).isEmpty())
                return new DriverPostKnownReadFailureMaterial.Unrecorded(DriverPostKnownReadFailureMaterial.Reason.NO_REPRODUCED_FAILURE,"owning pure verifier did not reproduce an original failure");
            StrictJson.require(rowCount(queue)<128,"finite post-Known row batch exhausted");
            DriverPostKnownReadFailureRowProducer.Candidate candidate;
            try{candidate=DriverPostKnownReadFailureRowProducer.prepare(queue.session,archive.withSession(queue.session),catalog,authority,this,installed,actual,earlier,before,
                    Math.addExact(before.driver().commandHistory().size(),rowCount(queue)+1L),sources);}
            catch(UncheckedIOException storage){lost(installed.operation().value(),storage);queue.deferred.removeIf(value->value.known()==actual||earlier.stream().anyMatch(peer->peer==value.known()));removeEmpty();
                return new DriverPostKnownReadFailureMaterial.StorageDiagnostic(storage.getCause().getClass().getName(),Objects.toString(storage.getCause().getMessage(),""));}
            queue.postKnown.add(new PostKnownItem(candidate));queued(queue,candidate.row().command());
            queue.deferred.removeIf(value->value.known()==actual||earlier.stream().anyMatch(peer->peer==value.known()));return new DriverPostKnownReadFailureMaterial.Queued(candidate.rowReference());
        });}catch(IOException failure){throw new UncheckedIOException("post-Known original scope unavailable",failure);}
    }
    private void replayPostKnown(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive bound,PostKnownItem item)throws IOException{
        var candidate=item.candidate();DriverPostKnownReadFailureRowProducer.replay(same,bound,catalog,authority,this,candidate.identicalFinal(),candidate.finalKnown(),candidate.earlierKnown(),candidate);
    }
    public void requireBeforeIntent(ContinuityStorePort.Session same,ActionCommand command) {
        if(hasPending(same))throw new ReadPublicationRequiredException(command,Optional.empty());
    }
    public void enqueue(ContinuityStorePort.Session same,ReadContract<?> identicalInstalled,PlanningReadResult.Known<?> actual) {
        if(actual.receipt().request().operation().value().equals("private-query-faction-gift-cold-recovery-v1")
                ||actual.receipt().request().operation().value().equals("query-player-faction-alerts-v1"))retainFreshGift(same,identicalInstalled,actual);
        if(identicalInstalled.originalHistoryKind().isPresent()) { retainRich(same,identicalInstalled,actual);return; }
        if(!DriverReadHistoryRowProducer.shouldRecord(actual))return;
        StrictJson.require(catalog.containsIdentity(identicalInstalled),"original read contract is not installed in this publisher");
        try {
            authority.withFrozenFacts(same,frozen -> {
                StrictJson.require(frozen.state() instanceof Known,"complete actual Driver required to retain read history");
                Known known=(Known)frozen.state();requireSource(known,actual.receipt());
                // A repeated original receipt reuses its first immutable row and never receives a new index.
                for(var history:known.driver().commandHistory()) {
                    var row=DriverJson.object(history.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
                    if(row.members().containsKey(DriverReadHistoryRowProducer.SOURCE_FIELD)
                            &&DriverReadHistoryRowProducer.decode(history.originalRow().json()).provenance().originalReceipt().equals(actual.originalReceipt()))return null;
                }
                Queue queue=pending.get();
                if(queue==null){queue=new Queue(same,same.head(),known,frozen.actions());pending.set(queue);}
                StrictJson.require(queue.session==same&&queue.head.digest().equals(same.head().digest())&&queue.prepared==null
                        &&queue.before.stamp().equals(known.stamp())&&Arrays.equals(queue.before.driver().encode(),known.driver().encode()),"read batch crossed its original Driver/head/scope");
                for(Item existing:queue.items)if(existing.known().originalReceipt().equals(actual.originalReceipt())) {
                    StrictJson.require(existing.contract()==identicalInstalled&&existing.known().receipt().equals(actual.receipt()),"same original read changed contract/receipt");return null;
                }
                StrictJson.require(rowCount(queue)<128,"finite actual read batch exhausted before publication");
                Candidate candidate;
                try{candidate=DriverReadHistoryRowProducer.prepare(archive.withSession(same),catalog,identicalInstalled,actual,
                        Math.addExact(known.driver().commandHistory().size(),Math.addExact(rowCount(queue),1)));}
                catch(UncheckedIOException storage){lost(identicalInstalled.operation().value(),storage);removeEmpty();return null;}
                queue.items.add(new Item(identicalInstalled,actual,candidate));queued(queue,candidate.row().command());return null;
            });
        }catch(IOException failure){removeEmpty();throw new UncheckedIOException("original read retained; history publication unavailable",failure);}
        catch(RuntimeException failure){removeEmpty();throw failure;}
    }
    /** Keeps actual central objects until the service selects its final component inside the same borrowed scope. */
    private void retainRich(ContinuityStorePort.Session same,ReadContract<?> installed,PlanningReadResult.Known<?> actual) {
        StrictJson.require(catalog.containsIdentity(installed),"rich contract is not installed in this publisher");
        try {
            authority.withFrozenFacts(same,frozen -> {
                StrictJson.require(frozen.state() instanceof Known,"complete actual Driver required to retain rich history");
                Known known=(Known)frozen.state();requireSource(known,actual.receipt());
                Queue queue=retainQueue(same,frozen,known);
                for(Item item:queue.items)if(item.known()==actual) {
                    StrictJson.require(item.contract()==installed,"finalized rich object changed contract");return null;
                }
                for(Deferred retained:queue.deferred)if(retained.known()==actual) {
                    StrictJson.require(retained.contract()==installed,"retained rich object changed contract");return null;
                }
                StrictJson.require(rowCount(queue)+queue.deferred.size()<128,"finite retained rich batch exhausted");
                queue.deferred.add(new Deferred(installed,actual,known));return null;
            });
        }catch(IOException failure){removeEmpty();throw new UncheckedIOException("rich original retention unavailable",failure);}
        catch(RuntimeException failure){removeEmpty();throw failure;}
    }
    private Queue retainQueue(ContinuityStorePort.Session same,DriverStateAssembler.Frozen frozen,Known known) throws IOException {
        Queue queue=pending.get();
        if(queue==null){queue=new Queue(same,same.head(),known,frozen.actions());pending.set(queue);}
        StrictJson.require(queue.session==same&&queue.head.digest().equals(same.head().digest())&&queue.prepared==null
                &&queue.before.stamp().equals(known.stamp())&&Arrays.equals(queue.before.driver().encode(),known.driver().encode()),
                "rich batch crossed its original Driver/head/borrowed scope");
        return queue;
    }
    /** Bind only the same per-Game writer that owns this publisher; this creates no new query authority. */
    public synchronized void bindArmyCorePublication(DriverStateAssembler same,ActionPorts.OutcomeArchive originals,
            java.util.function.Supplier<ContinuityStorePort.Session> sessions) {
        StrictJson.require(authority==same&&archive==originals,"Army Core publication crossed its actual owner");
        Objects.requireNonNull(sessions);
        StrictJson.require(armyCoreSessions==null||armyCoreSessions==sessions,"Army Core publication replaced its writer source");
        armyCoreSessions=sessions;
    }
    /** A refresh removes availability even if validation fails before the first Native attempt. */
    public void armyCoreRefreshStarted() {
        var sessions=armyCoreSessions;if(sessions==null)return;
        var same=Objects.requireNonNull(sessions.get());
        try {authority.withFrozenFacts(same,frozen->{
            if(frozen.state() instanceof Known known) {
                armyCoreUnavailable.set(DriverSemanticReadState.armyCoreSource(known.auxiliary()).orElse(null));
                Queue queue=pending.get();
                if(queue!=null) {
                    StrictJson.require(retainQueue(same,frozen,known)==queue&&queue.publication==null&&!queue.commitStarted,
                            "Core refresh crossed its mutable original batch");
                    for(Item item:queue.items)if(item.known().value() instanceof org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue)
                        queue.invalidatedArmyCore.add(item.known().originalReceipt());
                    for(SummaryItem item:queue.summaries)if(item.known().value() instanceof org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue)
                        queue.invalidatedArmyCore.add(item.known().originalReceipt());
                }
            }
            return null;
        });}catch(IOException failure){throw new UncheckedIOException("Army Core refresh owner unavailable",failure);}
    }
    public void armyCoreUnavailable(ExactRef olderSource) {armyCoreUnavailable.set(Objects.requireNonNull(olderSource));}
    public Optional<ExactRef> armyCoreUnavailable(org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj auxiliary) {
        ExactRef source=armyCoreUnavailable.get();
        if(source!=null&&!DriverSemanticReadState.armyCoreSource(auxiliary).equals(Optional.of(source))){
            armyCoreUnavailable.compareAndSet(source,null);source=null;
        }
        return Optional.ofNullable(source);
    }
    /** Only the final component already retained and validated by this same rich producer may publish Core. */
    public void publishCompletedArmyCore(ReadContract<?> installed,PlanningReadResult.Known<?> actual) {
        var sessions=armyCoreSessions;if(sessions==null)return;
        Queue queue=pending.get();if(queue==null)return;
        StrictJson.require(sessions.get()==queue.session&&catalog.containsIdentity(installed),
                "completed Army Core crossed its actual writer/catalog");
        try {authority.withFrozenFacts(queue.session,frozen->{
        StrictJson.require(frozen.state() instanceof Known,"completed Army Core needs its actual Driver owner");
        Known known=(Known)frozen.state();
        StrictJson.require(retainQueue(queue.session,frozen,known)==queue&&queue.publication==null&&!queue.commitStarted,
                "completed Army Core crossed its mutable original batch");
        if(queue.invalidatedArmyCore.contains(actual.originalReceipt()))return null;
        boolean finalized=false;
        for(Item item:queue.items)if(item.known()==actual){
            StrictJson.require(item.contract()==installed,"completed Army Core contract identity changed");
            DriverReadHistoryRowProducer.replay(archive.withSession(queue.session),catalog,installed,actual,item.candidate());
            finalized=true;
        }
        for(SummaryItem item:queue.summaries)if(item.known()==actual){
            StrictJson.require(item.contract()==installed,"completed Army Core summary contract identity changed");
            org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.replay(
                    archive.withSession(queue.session),catalog,installed,actual,item.candidate());
            finalized=true;
        }
        // A real persistence diagnostic cannot invent a completed semantic source.
        if(!finalized)return null;
        StrictJson.require(actual.value() instanceof org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue,
                "completed Army Core typed value required");
        requireSource(known,actual.receipt());
            var originals=archive.withSession(queue.session);var observed=known.observation().orElseThrow();
            ExactRef evidence=actual.receipt().after().binding().nativeEvidence();
            RawJson manifest=originals.loadMaterial(observed.semanticFactsEvidence());
            var nativeFrame=DriverObservationEvidenceReader.nativeFrame(observed.semanticFactsEvidence(),manifest,originals.loadNativeFrame(evidence));
            var joined=new DriverObservationAssembler().assemble(nativeFrame,observed,evidence);
            StrictJson.require(joined instanceof DriverObservationAssembler.Complete,"completed Army Core frame is unavailable");
            var complete=(DriverObservationAssembler.Complete)joined;
            var changed=DriverSemanticReadState.apply(complete,known.auxiliary(),installed,actual,originals);
            if(changed.equals(known.auxiliary()))return null;
            var publication=DriverCapabilityStateProducer.observeSemanticRead(
                    complete,known,installed,actual,originals);
            authority.publishCapabilityInputs(queue.session,known.stamp(),publication.expectedAuxiliarySha256(),publication);
            return null;
        });}catch(IOException failure){throw new UncheckedIOException("completed original Army Core publication unavailable",failure);}
    }
    /** No result body, reconstructed Known or caller Session can authorize a rich publication. */
    public <T> DriverReadHistoryRichMaterial.StorageOutcome enqueueRich(ReadContract<T> installed,
            PlanningReadResult.Known<T> actual,List<? extends PlanningReadResult.Known<?>> actualComponents) {
        Objects.requireNonNull(installed);Objects.requireNonNull(actual);
        List<? extends PlanningReadResult.Known<?>> components=List.copyOf(actualComponents);Queue queue=pending.get();
        StrictJson.require(queue!=null&&catalog.containsIdentity(installed)&&installed.originalHistoryKind().isPresent(),
                "rich publication requires its actual central object and identical installed projector");
        try {
            return authority.withFrozenFacts(queue.session,frozen -> {
                StrictJson.require(frozen.state() instanceof Known,"actual complete Driver unavailable for rich projection");
                Known known=(Known)frozen.state();StrictJson.require(retainQueue(queue.session,frozen,known)==queue,"rich owner changed");
                requireSource(known,actual.receipt());
                StrictJson.require(components.size()>=1&&components.size()<=2&&components.stream().anyMatch(value->value==actual),
                        "one final component and at most one actual comparison required");
                for(int i=0;i<components.size();i++)for(int j=0;j<i;j++)
                    StrictJson.require(components.get(i)!=components.get(j),"rich component identity duplicated");
                var references=components.stream().map(PlanningReadResult.Known::originalReceipt).toList();
                for(Item item:queue.items)if(item.known()==actual) {
                    StrictJson.require(item.contract()==installed&&item.candidate().provenance().componentReceipts().equals(references),
                            "finalized rich component set changed");
                    DriverReadHistoryRowProducer.replay(archive.withSession(queue.session),catalog,installed,actual,item.candidate());
                    return new DriverReadHistoryRichMaterial.FullStored(item.candidate().fullResultReference().orElseThrow());
                }
                for(SummaryItem item:queue.summaries)if(item.known()==actual) {
                    StrictJson.require(item.contract()==installed&&item.candidate().source().componentReceipts().equals(references),
                            "finalized summary component set changed");
                    org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.replay(archive.withSession(queue.session),catalog,installed,actual,item.candidate());
                    return new DriverReadHistoryRichMaterial.SummaryStored(item.candidate().rowReference());
                }
                for(ExecuteItem item:queue.executions)if(item.known()==actual) {
                    StrictJson.require(item.contract()==installed&&components.size()==1,"finalized execute-query identity/components changed");
                    org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.replay(archive.withSession(queue.session),catalog,installed,actual,item.candidate());
                    return new DriverReadHistoryRichMaterial.FullStored(item.candidate().fullResultReference());
                }
                for(var component:components) {
                    requireSource(known,component.receipt());
                    var retained=queue.deferred.stream().filter(value->value.known()==component).toList();
                    StrictJson.require(retained.size()==1,"component was not retained by this same actual central scope");
                    if(component==actual)StrictJson.require(retained.getFirst().contract()==installed,"final rich contract changed");
                }
                // Validation faults remain failures. Artifact I/O failure cannot change the successful live read/cache.
                var payload=installed.projectOriginalHistoryPayload(actual.receipt());
                if(payload instanceof DriverReadHistoryRichMaterial.ArmySummaryPlan) {
                    org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.Candidate candidate;
                    try {
                        candidate=org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.prepare(archive.withSession(queue.session),catalog,
                                installed,actual,components,Math.addExact(known.driver().commandHistory().size(),Math.addExact(rowCount(queue),1)),sources);
                    }catch(UncheckedIOException storageFailure) {
                        lost(installed.operation().value(),storageFailure);queue.deferred.removeIf(value->components.stream().anyMatch(component->component==value.known()));removeEmpty();
                        Throwable original=storageFailure.getCause();
                        return new DriverReadHistoryRichMaterial.StorageDiagnostic(Optional.empty(),original.getClass().getName(),Objects.toString(original.getMessage(),""));
                    }
                    queue.summaries.add(new SummaryItem(installed,actual,candidate));queued(queue,candidate.row().command());
                    queue.deferred.removeIf(value->components.stream().anyMatch(component->component==value.known()));
                    return new DriverReadHistoryRichMaterial.SummaryStored(candidate.rowReference());
                }
                if(payload instanceof DriverReadHistoryRichMaterial.ExecuteProjection) {
                    StrictJson.require(components.size()==1,"public execute-query is exactly one original read");
                    org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.Candidate candidate;
                    try {
                        candidate=org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.prepare(archive.withSession(queue.session),catalog,
                                installed,actual,Math.addExact(known.driver().commandHistory().size(),Math.addExact(rowCount(queue),1)),sources);
                    }catch(UncheckedIOException storageFailure) {
                        lost(installed.operation().value(),storageFailure);queue.deferred.removeIf(value->value.known()==actual);removeEmpty();
                        Throwable original=storageFailure.getCause();
                        return new DriverReadHistoryRichMaterial.StorageDiagnostic(Optional.empty(),original.getClass().getName(),Objects.toString(original.getMessage(),""));
                    }
                    queue.executions.add(new ExecuteItem(installed,actual,candidate));queued(queue,candidate.row().command());queue.deferred.removeIf(value->value.known()==actual);
                    return new DriverReadHistoryRichMaterial.FullStored(candidate.fullResultReference());
                }
                StrictJson.require(payload instanceof DriverReadHistoryRichMaterial.Projection,"this actual rich finalization requires a full result or the finite Army summary plan");
                Candidate candidate;
                try {
                    candidate=DriverReadHistoryRowProducer.prepareRich(archive.withSession(queue.session),catalog,installed,actual,components,
                            Math.addExact(known.driver().commandHistory().size(),Math.addExact(rowCount(queue),1)));
                }catch(UncheckedIOException storageFailure) {
                    lost(installed.operation().value(),storageFailure);queue.deferred.removeIf(value->components.stream().anyMatch(component->component==value.known()));removeEmpty();
                    Throwable original=storageFailure.getCause();
                    return new DriverReadHistoryRichMaterial.StorageDiagnostic(Optional.empty(),original.getClass().getName(),
                            Objects.toString(original.getMessage(),""));
                }
                queue.items.add(new Item(installed,actual,candidate));queued(queue,candidate.row().command());
                queue.deferred.removeIf(value->components.stream().anyMatch(component->component==value.known()));
                return new DriverReadHistoryRichMaterial.FullStored(candidate.fullResultReference().orElseThrow());
            });
        }catch(IOException failure){throw new UncheckedIOException("actual rich scope unavailable",failure);}
    }
    /** Cancels only an unfinalized central object; original artifacts and successful live query/cache values remain intact. */
    public void abandonRich(ReadContract<?> installed,PlanningReadResult.Known<?> actual) {
        Objects.requireNonNull(installed);Objects.requireNonNull(actual);Queue queue=pending.get();if(queue==null)return;
        var retained=queue.deferred.stream().filter(value->value.known()==actual).toList();if(retained.isEmpty())return;
        StrictJson.require(retained.size()==1&&retained.getFirst().contract()==installed,"rich abandonment crossed its installed object");
        try {
            authority.withFrozenFacts(queue.session,frozen -> {
                StrictJson.require(frozen.state() instanceof Known,"actual rich abandonment scope unavailable");
                Known known=(Known)frozen.state();StrictJson.require(retainQueue(queue.session,frozen,known)==queue,"rich owner changed");
                requireSource(known,actual.receipt());queue.deferred.remove(retained.getFirst());return null;
            });removeEmpty();
        }catch(IOException failure){throw new UncheckedIOException("rich abandonment escaped its original scope",failure);}
    }
    /** Pure logical observation with actual pair/alert receipts; no synthetic Native receipt or reconstructed current owner is accepted. */
    public RawJson publishGiftResolved(ContinuityStorePort.Session same,Known actualCurrent,GiftResolvedEvidence.Inputs actual,RawJson claimed) throws IOException {
        Objects.requireNonNull(actualCurrent);Objects.requireNonNull(actual);Objects.requireNonNull(claimed);
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==actualCurrent,"resolved Gift requires the actual held full Driver object");
            ActionPorts.OutcomeArchive originals=archive.withSession(same);requireObservedSource(actualCurrent,actual,originals);
            requireObservedRead(same,actualCurrent,actual.frame(),actual.pair(),originals);
            if(actual.alert().isPresent())requireObservedRead(same,actualCurrent,actual.frame(),actual.alert().orElseThrow(),originals);
            Queue queue=retainQueue(same,frozen,actualCurrent);
            for(ObservedItem prior:queue.observed)if(prior.candidate().source().requestId().equals(actual.requestId())) {
                StrictJson.require(prior.inputs().equals(actual),"same Gift observation identity changed original inputs");
                DriverObservedHistoryRowProducer.replay(originals,catalog,actual,prior.candidate());
                RawJson retained=originals.loadMaterial(prior.candidate().fullResultReference());
                StrictJson.require(DriverJson.object(retained.bytes(),RawJson.MAXIMUM_BYTES).equals(DriverJson.object(claimed.bytes(),RawJson.MAXIMUM_BYTES)),"same Gift observation result changed");return retained;
            }
            StrictJson.require(rowCount(queue)+queue.deferred.size()<128,"finite observed read batch exhausted");
            DriverObservedHistoryRowProducer.Candidate candidate;
            try{candidate=DriverObservedHistoryRowProducer.prepareGiftResolved(originals,catalog,actual,claimed,
                    Math.addExact(actualCurrent.driver().commandHistory().size(),Math.addExact(rowCount(queue),1)),sources);}
            catch(UncheckedIOException storage){lost("gift-outcome-observed",storage);removeEmpty();throw storage;}
            queue.observed.add(new ObservedItem(actual,candidate));queued(queue,candidate.row().command());return originals.loadMaterial(candidate.fullResultReference());
        });
    }
    private void requireObservedRead(ContinuityStorePort.Session same,Known current,DriverObservationAssembler.Complete observed,
            PlanningReadReceipt read,ActionPorts.OutcomeArchive originals) throws IOException {
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(read,originals);
        var query=originalQueryObserved(read.before().binding(),originals);
        StrictJson.require(query.source().equals(observed.source())&&query.sessionId().equals(observed.sessionId())
                &&query.connectionGeneration().equals(observed.connectionGeneration())&&query.identity().game().equals(observed.identity().game())
                &&Arrays.equals(originals.loadNativeFrame(query.originalEvidence()),originals.loadNativeFrame(observed.originalEvidence())),
                "Gift observation read crossed its real source/session/Game/original Native packet");
        if(query.equals(observed)) {
            var retained=freshGift.get().stream().filter(value->value.session()==same&&value.known().receipt().equals(read)).toList();
            StrictJson.require(retained.size()==1&&catalog.containsIdentity(retained.getFirst().contract()),
                    "fresh Gift input was not retained by this same actual installed central read scope");return;
        }
        var extension=requireReadOnlyExtension(same,read.before().binding(),query,current);
        StrictJson.require(extension.currentObserved().equals(observed)&&extension.verified.readReceipts().contains(originals.readReferenceOf(read)),
                "cached Gift input has no actual canonical READ interval to this exact current complete frame");
    }
    private static void requireObservedSource(Known current,GiftResolvedEvidence.Inputs actual,ActionPorts.OutcomeArchive originals) {
        StrictJson.require(Arrays.equals(current.driver().encode(),actual.driver().encode()),"observed Gift changed its actual full Driver input");
        var facts=current.observation().orElseThrow();var nativeRef=DriverObservationEvidenceReader.reference(current.auxiliary().get("capability_observed_native_source"));
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(facts.semanticFactsEvidence(),originals.loadFullMaterial(facts.semanticFactsEvidence()),originals.loadNativeFrame(nativeRef));
        var joined=new DriverObservationAssembler().assemble(nativeFrame,facts,nativeRef);
        StrictJson.require(joined instanceof DriverObservationAssembler.Complete&&joined.equals(actual.frame()),
                "observed Gift must use the actual complete current manifest/native/SEM projection");
    }
    private void retainFreshGift(ContinuityStorePort.Session same,ReadContract<?> installed,PlanningReadResult.Known<?> actual) {
        StrictJson.require(catalog.containsIdentity(installed),"fresh Gift contract is not actually installed");
        try {authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual fresh Gift Driver unavailable");requireSource((Known)frozen.state(),actual.receipt());
            var retained=freshGift.get();if(!retained.isEmpty()&&retained.getFirst().session()!=same)retained.clear();
            for(FreshGift value:retained)if(value.known()==actual){StrictJson.require(value.contract()==installed,"fresh Gift original changed contract");return null;}
            StrictJson.require(retained.size()<128,"finite fresh Gift original custody exhausted");retained.add(new FreshGift(same,installed,actual));return null;
        });}catch(IOException failure){throw new UncheckedIOException("fresh Gift original scope unavailable",failure);}
    }
    private void removeEmpty(){Queue queue=pending.get();if(queue!=null&&queue.items.isEmpty()&&queue.summaries.isEmpty()&&queue.executions.isEmpty()&&queue.deferred.isEmpty()&&queue.observed.isEmpty()&&queue.failures.isEmpty()&&queue.publicFailures.isEmpty()&&queue.returnedControls.isEmpty()&&queue.postKnown.isEmpty()&&queue.returnedReads.isEmpty()&&queue.returnedActions.isEmpty()&&queue.early.isEmpty()&&queue.prepared==null)pending.remove();}
    public Optional<Committed> flushActualReads(ContinuityStorePort.Session same) throws IOException {
        authority.requireOutsideObservationScope(same);
        if(!hasPending(same)){pending.remove();return Optional.empty();}Queue queue=pending.get();
        StrictJson.require(queue.deferred.isEmpty(),"rich components must finalize or abandon in their original service scope before publication");
        ActionPorts.OutcomeArchive originals=archive.withSession(same);
        try {
            if(queue.publication==null)queue.publication=prepare(same,queue,originals);
            if(queue.prepared==null)queue.prepared=same.preview(queue.publication.request);
            if(queue.receipt==null) {
                if(queue.commitStarted)queue.receipt=same.queryCommitted(queue.prepared).orElseThrow(()->new IOException("original read-history commit outcome unknown; no second commit"));
                else {queue.commitStarted=true;queue.receipt=same.commit(queue.prepared);}
            }
            same.requireCommitted(queue.prepared,queue.receipt);
            authority.publishReadHistory(same,queue.publication,queue.prepared,queue.receipt);
        }catch(IOException|UncheckedIOException storage){flushFailed(queue,storage);throw storage;}
        // Only the actual canonical writer commit followed by the locked Driver CAS covers these exact rows.
        // Token release is deliberately outside the storage catch: cleanup cannot re-fail already-covered attempts.
        if(!queue.storageAttempts.isEmpty())persistenceStatus.committed(queue.storageAttempts,queue.prepared,queue.receipt);
        Committed committed=new Committed(queue.prepared.predecessor(),queue.receipt);pending.remove();freshGift.remove();
        for(var item:queue.publicFailures)publicFailureSource.release(item.invocation());
        for(var item:queue.returnedControls)returnedControlSource.release(item.invocation());
        for(var item:queue.returnedReads)returnedReadSource.release(item.invocation());for(var item:queue.returnedActions)returnedActionSource.release(item.invocation());for(var item:queue.early)earlyFailureSource.release(item.invocation());return Optional.of(committed);
    }
    private Publication prepare(ContinuityStorePort.Session same,Queue queue,ActionPorts.OutcomeArchive originals) throws IOException {
        return authority.withFrozenFacts(same,frozen -> {
            queue.commitHead=requirePredecessor(same,queue,frozen);
            var history=new ArrayList<>(queue.before.driver().commandHistory());
            var appended=new ArrayList<DriverStateSnapshot.HistoryEntry>();
            for(Item item:queue.items) {
                DriverReadHistoryRowProducer.replay(originals,catalog,item.contract(),item.known(),item.candidate());
                appended.add(item.candidate().historyEntry());
            }
            for(ObservedItem item:queue.observed){DriverObservedHistoryRowProducer.replay(originals,catalog,item.inputs(),item.candidate());appended.add(item.candidate().historyEntry());}
            for(SummaryItem item:queue.summaries){
                org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.replay(originals,catalog,item.contract(),item.known(),item.candidate());
                appended.add(item.candidate().historyEntry());
            }
            for(ExecuteItem item:queue.executions){
                org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.replay(originals,catalog,item.contract(),item.known(),item.candidate());
                appended.add(item.candidate().historyEntry());
            }
            for(FailedItem item:queue.failures){DriverFailedReadHistoryRowProducer.replay(originals,catalog,item.candidate());appended.add(item.candidate().historyEntry());}
            for(var item:queue.publicFailures){requirePublicFailure(same,item,originals);appended.add(item.candidate().historyEntry());}
            for(var item:queue.returnedControls){DriverReturnedControlHistoryRowProducer.replay(same,originals,authority,returnedControlSource,catalog,item.candidate());appended.add(item.candidate().historyEntry());}
            replayAdditional(same,queue,originals);
            for(var item:queue.postKnown)appended.add(item.candidate().historyEntry());for(var item:queue.returnedReads)appended.add(item.candidate().historyEntry());
            for(var item:queue.returnedActions)appended.add(item.candidate().historyEntry());for(var item:queue.early)appended.add(item.candidate().historyEntry());
            appended.sort(java.util.Comparator.comparingLong(DriverStateSnapshot.HistoryEntry::index));
            for(var entry:appended){StrictJson.require(entry.index()==history.size()+1L,"retained mixed read index is not contiguous");history.add(entry);}
            var before=queue.before.driver();
            var after=new DriverStateSnapshot.Complete(before.session(),history,before.lastCheckpoint(),before.rollbackWarFailure(),before.managedRestoreTransaction(),
                    before.successionExpectation(),before.successionLifecycle(),before.campaignGoal(),before.rollbackWarFailures());
            ExactRef beforeRef=originals.materialReferenceOf(RawJson.fullMaterial(before.encode()));
            ExactRef afterRef=originals.preserveMaterial(RawJson.fullMaterial(after.encode()));
            StrictJson.require(Arrays.equals(after.encode(),originals.loadFullMaterial(afterRef).bytes()),"read-history complete Driver archive differs");
            ObjectNode details=StrictJson.object();details.put("schema",queue.source==null?"xar.driver-read-publication/v2":"xar.driver-read-publication/v1");
            details.put("evidence_id","driver-read:"+UUID.randomUUID());details.put("token",UUID.randomUUID().toString());
            if(queue.source==null){StrictJson.require(queue.early.size()==1&&rowCount(queue)==1,"only a genuine cached early exception can lack a semantic source");details.putNull("source");}
            else details.set("source",ProposalLifecycleCodec.source(queue.source));
            details.put("predecessor_head_sha256",queue.commitHead.digest());details.put("read_head_sha256",queue.head.digest());details.put("read_head_sequence",queue.head.state().sequence());details.put("before_version",queue.before.stamp().driverVersion());
            details.put("after_version",Math.addExact(queue.before.stamp().driverVersion(),1));details.put("episode_epoch",queue.before.stamp().episodeEpoch());
            details.set("before_driver",beforeRef.toJson());details.set("after_driver",afterRef.toJson());
            LinkedHashSet<ExactRef> evidence=new LinkedHashSet<>();evidence.add(beforeRef);evidence.add(afterRef);
            var rows=details.putArray("read_rows");var rowMetadata=new ArrayList<ObjectNode>();
            for(Item item:queue.items) {
                Candidate candidate=item.candidate();ObjectNode row=StrictJson.object();rowMetadata.add(row);row.put("index",candidate.row().index());row.put("contract_id",item.contract().contractId());
                row.set("row",candidate.rowReference().toJson());row.set("read",candidate.readReference().toJson());
                row.set("definition_source",candidate.definitionSource().toJson());row.set("decoder_source",candidate.decoderSource().toJson());
                evidence.add(candidate.rowReference());evidence.add(candidate.readReference());
                evidence.addAll(candidate.provenance().supportingEvidence());
            }
            for(ObservedItem item:queue.observed) {
                var candidate=item.candidate();var source=candidate.source();ObjectNode row=StrictJson.object();rowMetadata.add(row);
                row.put("row_kind","GIFT_RESOLVED");row.put("index",candidate.row().index());row.set("row",candidate.rowReference().toJson());
                row.set("before_driver",source.beforeDriver().toJson());row.set("pair_read",source.pairReference().toJson());
                if(source.alertReference().isPresent())row.set("alert_read",source.alertReference().orElseThrow().toJson());else row.putNull("alert_read");
                evidence.add(candidate.rowReference());evidence.addAll(source.evidence());
            }
            for(SummaryItem item:queue.summaries) {
                var candidate=item.candidate();ObjectNode row=StrictJson.object();rowMetadata.add(row);
                row.put("row_kind",SUMMARY_ROW_KIND);row.put("index",candidate.row().index());row.put("contract_id",item.contract().contractId());
                row.set("row",candidate.rowReference().toJson());row.set("read",candidate.readReference().toJson());
                row.set("definition_source",candidate.definitionSource().toJson());row.set("decoder_source",candidate.decoderSource().toJson());
                evidence.add(candidate.rowReference());evidence.addAll(candidate.source().evidence());
            }
            for(ExecuteItem item:queue.executions) {
                var candidate=item.candidate();ObjectNode row=StrictJson.object();rowMetadata.add(row);
                row.put("row_kind",EXECUTE_ROW_KIND);row.put("index",candidate.row().index());row.put("contract_id",item.contract().contractId());
                row.set("row",candidate.rowReference().toJson());row.set("read",candidate.readReference().toJson());
                row.set("definition_source",candidate.definitionSource().toJson());row.set("decoder_source",candidate.decoderSource().toJson());
                evidence.add(candidate.rowReference());evidence.addAll(candidate.source().evidence());
            }
            for(FailedItem item:queue.failures){
                var candidate=item.candidate();var source=candidate.source();ObjectNode row=StrictJson.object();rowMetadata.add(row);
                row.put("row_kind",FAILED_ROW_KIND);row.put("index",candidate.row().index());row.set("row",candidate.rowReference().toJson());
                row.set("before_driver",source.beforeDriver().toJson());row.set("attempt",source.attempt().toJson());
                evidence.add(candidate.rowReference());evidence.addAll(source.evidence());
            }
            for(var item:queue.publicFailures){
                var candidate=item.candidate();var source=candidate.source();var row=StrictJson.object();rowMetadata.add(row);
                row.put("row_kind",PUBLIC_FAILURE_ROW_KIND);row.put("index",candidate.row().index());row.set("row",candidate.rowReference().toJson());row.set("before_driver",source.beforeDriver().toJson());row.set("invocation",source.invocation().toJson());
                evidence.add(candidate.rowReference());evidence.addAll(source.evidence());
            }
            for(var item:queue.returnedControls){
                var candidate=item.candidate();var source=candidate.source();var row=StrictJson.object();rowMetadata.add(row);
                row.put("row_kind",RETURNED_CONTROL_ROW_KIND);row.put("index",candidate.row().index());row.set("row",candidate.rowReference().toJson());row.set("before_driver",source.beforeDriver().toJson());row.set("receipt",source.canonicalReceipt().toJson());row.set("record",source.canonicalRecord().toJson());
                evidence.add(candidate.rowReference());evidence.addAll(source.evidence());
            }
            for(var item:queue.postKnown){var c=item.candidate();additionalRow(rowMetadata,evidence,POST_KNOWN_ROW_KIND,c.historyEntry().index(),c.rowReference(),c.source().before().fullDriver(),c.finalReadReference(),c.source().supportingEvidence());}
            for(var item:queue.returnedReads){var c=item.candidate();additionalRow(rowMetadata,evidence,RETURNED_READ_ROW_KIND,c.historyEntry().index(),c.rowReference(),c.source().beforeDriver(),c.source().invocation(),c.source().evidence());}
            for(var item:queue.returnedActions){var c=item.candidate();additionalRow(rowMetadata,evidence,RETURNED_ACTION_ROW_KIND,c.historyEntry().index(),c.rowReference(),c.source().beforeDriver(),c.source().canonicalReceipt(),c.source().evidence());}
            for(var item:queue.early){var c=item.candidate();additionalRow(rowMetadata,evidence,EARLY_ROW_KIND,c.historyEntry().index(),c.rowReference(),((DriverEarlyExecuteFailure.CachedData)c.source().retained()).beforeDriver(),c.source().invocation(),c.source().evidence());}
            rowMetadata.sort(java.util.Comparator.comparingLong(row->StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER)));
            rowMetadata.forEach(rows::add);
            var request=new WriterContracts.Request(WriterContracts.DRIVER_READ_HISTORY_KIND,StrictJson.canonical(details),List.copyOf(evidence));
            return new Publication(this,queue,after,request,beforeRef,afterRef);
        });
    }
    @Override public String revalidate(ContinuityState predecessor,WriterContracts.Request request) throws IOException {
        throw new IOException("read-history qualification requires the actual original writer Head and retained private batch");
    }
    @Override public String revalidate(WriterContracts.Head actualHead,WriterContracts.Request request) throws IOException {
        Queue queue=actual(request);StrictJson.require(queue.commitHead!=null&&actualHead.digest().equals(queue.commitHead.digest()),"read-history publication Head changed after exact no-write ancestry validation");
        ActionPorts.OutcomeArchive originals=archive.withSession(queue.session);
        authority.withFrozenFacts(queue.session,frozen -> {
            requirePredecessor(queue.session,queue,frozen);
            for(Item item:queue.items)DriverReadHistoryRowProducer.replay(originals,catalog,item.contract(),item.known(),item.candidate());
            for(ObservedItem item:queue.observed)DriverObservedHistoryRowProducer.replay(originals,catalog,item.inputs(),item.candidate());
            for(SummaryItem item:queue.summaries)org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.replay(originals,catalog,item.contract(),item.known(),item.candidate());
            for(ExecuteItem item:queue.executions)org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.replay(originals,catalog,item.contract(),item.known(),item.candidate());
            for(FailedItem item:queue.failures)DriverFailedReadHistoryRowProducer.replay(originals,catalog,item.candidate());
            for(var item:queue.publicFailures)requirePublicFailure(queue.session,item,originals);
            for(var item:queue.returnedControls)DriverReturnedControlHistoryRowProducer.replay(queue.session,originals,authority,returnedControlSource,catalog,item.candidate());
            replayAdditional(queue.session,queue,originals);return null;
        });
        for(ExactRef source:request.evidence()) {var pin=queue.session.capturePin(source,WriterContracts.MAX_PIN_BYTES);queue.session.verifyPin(pin);}
        StrictJson.require(Arrays.equals(originals.loadFullMaterial(queue.publication.beforeDriver).bytes(),queue.before.driver().encode())
                &&Arrays.equals(originals.loadFullMaterial(queue.publication.afterDriver).bytes(),queue.publication.replacement.encode()),"read-history original full Driver bytes differ");
        ObjectNode guard=StrictJson.object();guard.put("head",actualHead.digest());guard.put("request",request.identity());
        guard.put("full_driver",queue.before.stamp().driverSha256());return ContinuityJson.digest(guard);
    }
    @Override public ContinuityState reduce(ContinuityState predecessor,WriterContracts.Request request) {
        Queue queue=actual(request);ObjectNode next=predecessor.toJson();
        next.set(WriterContracts.DRIVER_READ_HISTORY_FIELD,queue.publication.request.detailsObject());
        return ContinuityState.fromJson(next,predecessor.machineId());
    }
    private Queue actual(WriterContracts.Request request) {
        Queue queue=pending.get();StrictJson.require(request.kind().equals(WriterContracts.DRIVER_READ_HISTORY_KIND)&&queue!=null&&queue.publication!=null
                &&queue.publication.request.identity().equals(request.identity())&&Arrays.equals(queue.publication.request.details(),request.details())
                &&queue.publication.request.evidence().equals(request.evidence()),"no exact retained read-publication producer; JSON cannot mint a batch");return queue;
    }
    private WriterContracts.Head requirePredecessor(ContinuityStorePort.Session same,Queue queue,DriverStateAssembler.Frozen frozen) throws IOException {
        StrictJson.require(queue.session==same&&frozen.state() instanceof Known,"actual same read-publication predecessor unavailable");
        Known known=(Known)frozen.state();StrictJson.require(known.stamp().equals(queue.before.stamp())&&Arrays.equals(known.driver().encode(),queue.before.driver().encode()),"read-history Driver prefix/version changed");
        for(Item item:queue.items)requireSource(known,item.known().receipt());
        for(ObservedItem item:queue.observed)requireObservedSource(known,item.inputs(),archive.withSession(same));
        if(!queue.failures.isEmpty()||!queue.publicFailures.isEmpty()||!queue.returnedControls.isEmpty()||!queue.postKnown.isEmpty()||!queue.returnedReads.isEmpty()||!queue.returnedActions.isEmpty()||!queue.early.isEmpty()){
            var head=same.head();StrictJson.require(head.digest().equals(queue.head.digest())&&head.state().sequence()==queue.head.state().sequence(),
                    "failed read publication cannot absorb later canonical transitions");
            for(var item:queue.failures)StrictJson.require(item.candidate().headSequence()==head.state().sequence()
                    &&item.candidate().headDigest().equals(head.digest()),"failed attempt differs from the actual flush predecessor");
            for(var item:queue.publicFailures)StrictJson.require(item.candidate().headSequence()==head.state().sequence()&&item.candidate().headDigest().equals(head.digest()),"public error escaped its catch head");
            for(var item:queue.returnedControls)StrictJson.require(item.candidate().headSequence()==head.state().sequence()&&item.candidate().headDigest().equals(head.digest()),"returned control escaped its captured head");
            for(var item:queue.postKnown)requireCapturedHead(head,item.candidate().source().before().writerPoint().sequence(),item.candidate().source().before().writerPoint().digest());
            for(var item:queue.returnedReads)requireCapturedHead(head,item.candidate().headSequence(),item.candidate().headDigest());
            for(var item:queue.returnedActions)requireCapturedHead(head,item.candidate().headSequence(),item.candidate().headDigest());
            for(var item:queue.early)requireCapturedHead(head,item.candidate().headSequence(),item.candidate().headDigest());
            return head;
        }
        return ReadPublicationAncestry.require(same,queue.head,queue.baseline,frozen.actions(),archive.withSession(same));
    }
    private static void requireCapturedHead(WriterContracts.Head head,long sequence,String digest){StrictJson.require(head.state().sequence()==sequence&&head.digest().equals(digest),"original returned/error row left its captured head");}
    private void replayAdditional(ContinuityStorePort.Session same,Queue queue,ActionPorts.OutcomeArchive bound)throws IOException{
        for(var item:queue.postKnown)replayPostKnown(same,bound,item);
        for(var item:queue.returnedReads)DriverReturnedPublicReadHistoryRowProducer.replay(same,bound,authority,returnedReadSource,catalog,item.candidate());
        for(var item:queue.returnedActions)DriverReturnedActionHistoryRowProducer.replay(same,bound,authority,returnedActionSource,catalog,item.candidate());
        for(var item:queue.early)replayEarly(same,bound,item);
    }
    private static void additionalRow(List<ObjectNode> rows,java.util.Set<ExactRef> evidence,String kind,long index,ExactRef rowReference,ExactRef before,ExactRef original,List<ExactRef> originals){
        var row=StrictJson.object();row.put("row_kind",kind);row.put("index",index);row.set("row",rowReference.toJson());row.set("before_driver",before.toJson());row.set("original",original.toJson());rows.add(row);evidence.add(rowReference);evidence.addAll(originals);
    }
    private void requirePublicFailure(ContinuityStorePort.Session same,PublicFailureItem item,ActionPorts.OutcomeArchive bound)throws IOException {
        StrictJson.require(item.invocation().issuer()==publicFailureSource,"public failure changed installed issuer");
        var actual=publicFailureSource.requireOriginal(same,authority,bound,item.invocation());
        StrictJson.require(actual.invocation().equals(item.candidate().source().invocation())&&actual.headSequence()==item.candidate().headSequence()&&actual.headDigest().equals(item.candidate().headDigest()),"failure original changed after preparation");
        DriverPublicExecuteFailureRowProducer.replayOriginals(bound,item.candidate().row());
    }
    private static void requireSource(Known known,PlanningReadReceipt read) {
        StrictJson.require(read.request().origin() instanceof CommandOrigin.Gameplay&&known.observation().isPresent(),"actual ordinary observed read source required");
        var origin=read.request().before();var frame=origin.frame();var actual=known.observation().orElseThrow();
        StrictJson.require(origin.game().equals(known.stamp().game())&&frame.episodeRunId().equals(known.stamp().episodeRunId())
                &&frame.identity().player().equals(known.driver().session().actorId())&&origin.machineId().equals(actual.transport().machineId())
                &&frame.snapshotId().equals(actual.snapshotId())&&frame.revision().equals(actual.publicRevision())
                &&frame.identity().nativeRevision().equals(actual.nativeRevision())&&origin.observationVersion()==actual.observationVersion()
                &&read.request().source().equals(actual.source())&&read.request().sessionId().equals(actual.transport().sessionId())
                &&read.before().binding().connectionGeneration().equals(actual.transport().connectionGeneration()),"read history crossed current Game/episode/full frame/source");
    }
}
