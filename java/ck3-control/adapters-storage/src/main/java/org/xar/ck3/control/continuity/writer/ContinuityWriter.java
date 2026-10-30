package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.continuity.ContinuityEvent;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** The original continuity ledger's sole Java writer. Contains no Game, SDK or Driver operation. */
public final class ContinuityWriter implements ContinuityStorePort, DomainBodies.Store, RollbackPair.Store {
    /** At most one original writer session on a thread; a borrowed scope never acquires another lock. */
    private static final ThreadLocal<ContinuityStorePort.Session> ACTIVE_SESSION = new ThreadLocal<>();
    public record Extensions(List<DomainBodies.Registration> domains, java.util.Optional<ImmutableArtifactStore> artifacts,
                             java.util.Optional<RollbackPair.Authority> rollbackAuthority) {
        public Extensions {
            domains = List.copyOf(domains); Objects.requireNonNull(artifacts); Objects.requireNonNull(rollbackAuthority);
            StrictJson.require(domains.isEmpty() || artifacts.isPresent(), "domain import requires the one immutable artifact store");
            StrictJson.require(domains.stream().map(DomainBodies.Registration::slot).distinct().count() == domains.size(), "one authoritative registration per domain slot");
        }
        public static Extensions none() { return new Extensions(List.of(), java.util.Optional.empty(), java.util.Optional.empty()); }
    }
    private final Layout layout;
    private final List<ExactRef> sources;
    private final TransitionAuthority authority;
    private final Clock clock;
    private final Extensions extensions;
    private final WriterFaultProbe faults;
    private final StorageWriteGuard storageGuard;
    /** One captured history cache is reused across same-process writer sessions. */
    private final ContinuityStore store;
    /** Exact physical outputs only; this is neither Game admission nor an observed initial window. */
    public record Initialized(Layout layout,Pin anchor,Pin snapshot,Pin lock,Head initialHead) {
        public Initialized {Objects.requireNonNull(layout);Objects.requireNonNull(anchor);Objects.requireNonNull(snapshot);
            Objects.requireNonNull(lock);Objects.requireNonNull(initialHead);}
    }
    /** The sole writer's initial CREATE_NEW path, using its existing storage owner and original lock. */
    public static Initialized initializeFresh(org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan plan,
            ExactRef actualPlanOriginal,InitialLayout paths,StorageWriteGuard storage)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(actualPlanOriginal);Objects.requireNonNull(paths);Objects.requireNonNull(storage);
        if(ACTIVE_SESSION.get()!=null)throw new IOException("genesis cannot nest an original writer session");
        StrictJson.require(plan.machineId().equals(paths.machineId()),"genesis plan and actual output machine differ");
        var request=LedgerFiles.exact(actualPlanOriginal,org.xar.ck3.control.continuity.FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES);
        StrictJson.require(org.xar.ck3.control.continuity.FreshContinuityGenesis.decode(request.bytes()).equals(plan),
                "genesis requires its exact original configured request");
        ContinuityState initial=org.xar.ck3.control.continuity.FreshContinuityGenesis.initial(plan,actualPlanOriginal);
        storage.requireInitialization(paths.lock(),List.of(paths.snapshot().getParent(),paths.events()));
        try(WindowsLedgerLock held=WindowsLedgerLock.acquire(paths.lock())) {
            LedgerFiles.verify(request.pin());
            LedgerFiles.requireAbsent(paths.anchor());LedgerFiles.requireAbsent(paths.snapshot());LedgerFiles.requireAbsent(paths.events());
            var anchorWrite=LedgerFiles.prepareAtomic(paths.anchor(),initial.canonicalBytes(),false,ContinuityJson.LEDGER_MAX_BYTES);
            var snapshotWrite=LedgerFiles.prepareAtomic(paths.snapshot(),initial.canonicalBytes(),false,ContinuityJson.LEDGER_MAX_BYTES);
            var directory=new StorageWriteGuard.DirectoryCreate(paths.events());
            List<StorageWriteGuard.Mutation> mutations=new ArrayList<>();mutations.add(directory);
            mutations.addAll(anchorWrite.mutations());mutations.addAll(snapshotWrite.mutations());
            storage.write(new StorageWriteGuard.WritePlan(paths.lock(),mutations),()->{
                storage.write(new StorageWriteGuard.WritePlan(paths.lock(),List.of(directory)),()->{
                    java.nio.file.Files.createDirectory(paths.events());return null;
                });
                LedgerFiles.atomic(storage,paths.lock(),anchorWrite);LedgerFiles.atomic(storage,paths.lock(),snapshotWrite);
                return null;
            });
            LedgerFiles.verify(request.pin());
            var anchor=LedgerFiles.read(paths.anchor(),ContinuityJson.LEDGER_MAX_BYTES);
            var snapshot=LedgerFiles.read(paths.snapshot(),ContinuityJson.LEDGER_MAX_BYTES);
            StrictJson.require(java.util.Arrays.equals(anchor.bytes(),snapshot.bytes())
                    &&ContinuityJson.same(ContinuityJson.parseObject(anchor.bytes(),ContinuityJson.LEDGER_MAX_BYTES),initial.toJson()),
                    "initial canonical anchor/snapshot readback differ");
            Layout layout=new Layout(paths.snapshot(),anchor.pin().reference(),paths.machineId());
            Head head=new ContinuityStore(layout).head();
            StrictJson.require(head.state().sequence()==0&&!head.snapshotNeedsRecovery()&&head.indexRepairs().isEmpty()
                    &&head.state().status()==ContinuityState.Status.AWAITING_INITIAL_ENTRY,"fresh store must have an empty canonical chain");
            return new Initialized(layout,anchor.pin(),snapshot.pin(),held.readOriginalPin(),head);
        }
    }
    /** Read the original completed initialization after a lost return. Missing/partial outputs never authorize another write. */
    public static Initialized readFreshInitialization(org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan plan,
            ExactRef actualPlanOriginal,InitialLayout paths)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(paths);
        if(ACTIVE_SESSION.get()!=null)throw new IOException("genesis query cannot nest an original writer session");
        StrictJson.require(plan.machineId().equals(paths.machineId()),"genesis query machine differs");
        var request=LedgerFiles.exact(actualPlanOriginal,org.xar.ck3.control.continuity.FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES);
        StrictJson.require(org.xar.ck3.control.continuity.FreshContinuityGenesis.decode(request.bytes()).equals(plan),"original genesis query request changed");
        var expected=org.xar.ck3.control.continuity.FreshContinuityGenesis.initial(plan,actualPlanOriginal);
        try(WindowsLedgerLock held=WindowsLedgerLock.acquire(paths.lock())) {
            var anchor=LedgerFiles.read(paths.anchor(),ContinuityJson.LEDGER_MAX_BYTES);
            var snapshot=LedgerFiles.read(paths.snapshot(),ContinuityJson.LEDGER_MAX_BYTES);
            StrictJson.require(java.util.Arrays.equals(anchor.bytes(),snapshot.bytes())
                    &&ContinuityJson.same(ContinuityJson.parseObject(anchor.bytes(),ContinuityJson.LEDGER_MAX_BYTES),expected.toJson()),
                    "only the exact original completed genesis may be queried");
            Layout layout=new Layout(paths.snapshot(),anchor.pin().reference(),paths.machineId());
            Head head=new ContinuityStore(layout).head();
            StrictJson.require(head.state().sequence()==0&&!head.snapshotNeedsRecovery()&&head.indexRepairs().isEmpty(),"initialization query found a later or incomplete canonical chain");
            LedgerFiles.verify(request.pin());
            return new Initialized(layout,anchor.pin(),snapshot.pin(),held.readOriginalPin(),head);
        }
    }
    public ContinuityWriter(Layout layout,List<ExactRef> trustedSources,TransitionAuthority authority,
            StorageWriteGuard storageGuard)throws IOException {
        this(layout,trustedSources,authority,Clock.systemUTC(),Extensions.none(),storageGuard);
    }
    public ContinuityWriter(Layout layout,List<ExactRef> trustedSources,TransitionAuthority authority,Clock clock,
            StorageWriteGuard storageGuard)throws IOException {
        this(layout,trustedSources,authority,clock,Extensions.none(),storageGuard);
    }
    public ContinuityWriter(Layout layout,List<ExactRef> trustedSources,TransitionAuthority authority,Clock clock,
            Extensions extensions,StorageWriteGuard storageGuard)throws IOException {
        this(layout,trustedSources,authority,clock,extensions,storageGuard,WriterFaultProbe.NONE);
    }
    ContinuityWriter(Layout layout,List<ExactRef> trustedSources,TransitionAuthority authority,Clock clock,
            Extensions extensions,StorageWriteGuard storageGuard,WriterFaultProbe faults)throws IOException {
        this.layout=Objects.requireNonNull(layout);sources=List.copyOf(trustedSources);
        StrictJson.require(!sources.isEmpty()&&sources.size()<=MAXIMUM_CONFIGURED_SOURCES,"reviewed finite reducer/writer source closure");
        this.authority=Objects.requireNonNull(authority);this.clock=Objects.requireNonNull(clock);
        this.extensions=Objects.requireNonNull(extensions);this.storageGuard=Objects.requireNonNull(storageGuard);
        this.faults=Objects.requireNonNull(faults);
        this.store=new ContinuityStore(layout);
        storageGuard.requireInitialization(layout.lock(),List.of(layout.snapshot().getParent(),layout.events()));
        if(extensions.artifacts().isPresent()){
            ImmutableArtifactStore actual=extensions.artifacts().orElseThrow();
            StrictJson.require(actual.originalWriterLock().equals(layout.lock())
                    &&actual.storageGuard()==storageGuard,
                    "writer and immutable artifacts require the identical admitted whole-storage authority");
        }
    }
    /** Actual configured allocation authority; no constructor or write has an unguarded fallback. */
    public StorageWriteGuard storageGuard(){return storageGuard;}
    public Prepared preview(Request request) throws IOException { return locked(session -> session.preview(request)); }
    public java.nio.file.Path originalLockPath() { return layout.lock(); }
    /** Actual immutable configuration handle; this getter never creates or rebinds a store. */
    public java.util.Optional<ImmutableArtifactStore> artifactStore() { return extensions.artifacts(); }
    /** Lock-path equality alone does not prove which reviewed authority owns a borrowed session. */
    @Override public void requireSession(ContinuityStorePort.Session borrowed) throws IOException {
        if (!(borrowed instanceof ContinuityWriter.Session session) || session.writer() != this)
            throw new IOException("borrowed session belongs to a different ContinuityWriter authority");
        session.requireWriter(layout.lock());
    }
    /** Supplies the exact existing authority for source loaders invoked by any installed domain. */
    public ContinuityStorePort.Session borrowedSession() throws IOException {
        ContinuityStorePort.Session borrowed = ACTIVE_SESSION.get();
        if (borrowed == null) throw new IOException("no original writer session is active on this thread");
        requireSession(borrowed);
        return borrowed;
    }
    /** Empty only when this thread has no original writer scope. A foreign scope is never absence. */
    public java.util.Optional<ContinuityStorePort.Session> activeSession() throws IOException {
        ContinuityStorePort.Session active = ACTIVE_SESSION.get();
        if (active == null) return java.util.Optional.empty();
        requireSession(active);
        return java.util.Optional.of(active);
    }
    public Receipt commit(Prepared prepared) throws IOException { return locked(session -> session.commit(prepared)); }
    @Override public DomainBodies.Read read(DomainBodies.Slot slot) throws IOException { return locked(session -> session.readDomain(slot)); }
    @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request) throws IOException { return locked(session -> session.previewImport(request)); }
    @Override public Receipt commitImport(DomainBodies.PreparedImport prepared) throws IOException { return locked(session -> session.commitImport(prepared)); }
    @Override public RollbackPair.Plan previewRollback(ExactRef proof) throws IOException {
        return locked(session -> { Head head = session.head(); return RollbackPair.plan(head, rollbackEvidence(head, proof)); });
    }
    @Override public RollbackPair.Commit commitRollback(RollbackPair.Plan plan) throws IOException {
        return locked(session -> RollbackPairTransaction.commit(layout, new ContinuityStore(layout), plan, this::rollbackEvidence,
                OffsetDateTime.ofInstant(clock.instant(), ZoneOffset.UTC).toString(), faults, storageGuard));
    }
    private RollbackPair.Evidence rollbackEvidence(Head original, ExactRef proof) throws IOException {
        var configured = extensions.rollbackAuthority().orElseThrow(() -> new IOException("actual shared recovery authority unavailable"));
        List<Pin> actualSources = captureDomain(sources);
        Pin proofPin = LedgerFiles.exact(proof, ContinuityJson.DOCUMENT_MAX_BYTES).pin();
        RollbackPair.Evidence checked = configured.revalidate(original, proof);
        StrictJson.require(checked.proof().equals(proof), "actual rollback authority binds the requested exact proof");
        for (Pin source : actualSources) LedgerFiles.verify(source);
        LedgerFiles.verify(proofPin);
        for (Pin source : checked.qualificationSources()) LedgerFiles.verify(source);
        List<Pin> closure = new ArrayList<>(checked.qualificationSources()); closure.addAll(actualSources);
        if (!closure.contains(proofPin)) closure.add(proofPin);
        return new RollbackPair.Evidence(checked.proof(), checked.savedBasis(), checked.currentFrame(), checked.currentCycles(), closure, checked.preconditionDigest());
    }
    public ExactRef persistedHead() throws IOException {
        return locked(session -> LedgerFiles.read(layout.snapshot(), ContinuityJson.LEDGER_MAX_BYTES).pin().reference());
    }
    public <T> T locked(SessionWork<T> work) throws IOException {
        Objects.requireNonNull(work);
        if (ACTIVE_SESSION.get() != null) throw new IOException("nested original writer sessions are not permitted; borrow the active session");
        try (WindowsLedgerLock ignored = WindowsLedgerLock.acquire(layout.lock())) {
            Session session = new Session();
            ACTIVE_SESSION.set(session);
            try { return work.run(session); }
            finally { session.open = false; ACTIVE_SESSION.remove(); }
        }
    }
    public final class Session implements ContinuityStorePort.Session {
        private final ContinuityStore store = ContinuityWriter.this.store;
        private final Thread owner = Thread.currentThread();
        private boolean open = true;
        private Head retainedHead;
        private Head retainedDomainHead;
        private Session() { }
        private ContinuityWriter writer() { return ContinuityWriter.this; }
        private void checkOpen() {
            StrictJson.require(open && Thread.currentThread() == owner, "live original-lock session on owning thread required");
        }
        @Override public void requireWriter(java.nio.file.Path originalWriterLock) throws IOException {
            checkOpen(); Objects.requireNonNull(originalWriterLock);
            StrictJson.require(originalWriterLock.toAbsolutePath().normalize().equals(layout.lock()), "borrowed session belongs to another canonical writer");
            WindowsLedgerLock.requireHeld(layout.lock());
        }
        @Override public List<Pin> captureSources() throws IOException {
            requireWriter(layout.lock());Head actual=store.head();List<Pin> retained=captureDomain(sources);
            for(Pin pin:retained)LedgerFiles.verify(pin);
            requireSameHead(actual,store.head());return List.copyOf(retained);
        }
        @Override public HistoricalTransition readHistoricalTransition(Pin actualEvent) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(actualEvent);Head actual=store.head();
            Pin captured=actual.documents().stream().filter(actualEvent::equals).findFirst()
                    .orElseThrow(()->new IOException("event pin is not in this actual captured canonical history"));
            ObjectNode document=ContinuityJson.parseObject(readPinned(captured,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
            long sequence=StrictJson.integer(document.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER);
            StrictJson.require(java.nio.file.Path.of(captured.reference().path()).toAbsolutePath().normalize().equals(layout.event(sequence)),
                    "historical event must retain its actual canonical sequence path");
            ObjectNode event=capturedEventAt(actual,sequence);
            ContinuityState before=capturedStateAt(actual,Math.subtractExact(sequence,1)),after=capturedStateAt(actual,sequence);
            StrictJson.require(StrictJson.text(event.get("previous_sha256")).equals(ContinuityJson.digest(before.toJson()))
                    &&ContinuityJson.same(event.get("after"),after.toJson()),"historical canonical edge predecessor/after differs");
            ObjectNode identity=StrictJson.object();identity.set("kind",event.get("kind"));identity.set("details",event.get("details"));
            String eventIdentity=StrictJson.text(event.get("identity"));
            StrictJson.require(ContinuityJson.digest(identity).equals(eventIdentity),"historical canonical event identity differs");
            HistoricalTransition retained=new HistoricalTransition(sequence,StrictJson.text(event.get("kind")),
                    ContinuityJson.canonical(event.get("details")),eventIdentity,before,after,captured);
            for(Pin pin:actual.documents())LedgerFiles.verify(pin);
            requireSameHead(actual,store.head());return retained;
        }
        @Override public java.util.List<HistoricalTransition> readHistoricalTransitions(java.util.List<Pin> actualEvents) throws IOException {
            requireWriter(layout.lock());
            actualEvents=java.util.List.copyOf(Objects.requireNonNull(actualEvents));
            StrictJson.require(!actualEvents.isEmpty()
                    &&actualEvents.size()<=org.xar.ck3.control.continuity.ContinuityHistory.maximumEvents(),
                    "finite actual canonical event batch required");
            Head actual = store.head();
            try {
                return readHistoricalTransitions(actualEvents, actual);
            } catch (IOException changed) {
                // Historical reads have no mutation to replay. Only an actual stale/missing
                // captured original triggers one cold recapture; successful reads stay warm.
                retainedHead = null;
                return readHistoricalTransitions(actualEvents, store.refreshHead());
            }
        }
        private java.util.List<HistoricalTransition> readHistoricalTransitions(
                java.util.List<Pin> actualEvents, Head actual) throws IOException {
            final class CachedHistory {
                private final java.util.Map<Pin,ObjectNode> documents=new java.util.HashMap<>();
                private final java.util.Map<Long,ContinuityState> states=new java.util.HashMap<>();
                private ContinuityState anchored;
                ObjectNode document(Pin captured)throws IOException {
                    ObjectNode retained=documents.get(captured);
                    if(retained!=null)return retained;
                    ObjectNode document=ContinuityJson.parseObject(readPinned(captured,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
                    StrictJson.object(document,java.util.Set.of("sequence","at_utc","kind","details","identity","previous_sha256","after"));
                    long sequence=StrictJson.integer(document.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER);
                    StrictJson.require(java.nio.file.Path.of(captured.reference().path()).toAbsolutePath().normalize().equals(layout.event(sequence)),
                            "historical event must retain its actual canonical sequence path");
                    documents.put(captured,document);return document;
                }
                ObjectNode event(long sequence)throws IOException {
                    java.nio.file.Path path=layout.event(sequence);
                    Pin captured=actual.documents().stream().filter(pin->java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(path))
                            .findFirst().orElseThrow(()->new IOException("requested state is absent from the actual finite canonical history"));
                    return document(captured);
                }
                ContinuityState anchor()throws IOException {
                    if(anchored!=null)return anchored;
                    Pin pin=actual.documents().stream().filter(value->value.reference().equals(layout.anchor())).findFirst()
                            .orElseThrow(()->new IOException("canonical anchor is absent from captured history"));
                    anchored=ContinuityState.fromJson(ContinuityJson.parseObject(readPinned(pin,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES),layout.machineId());
                    return anchored;
                }
                ContinuityState state(long sequence)throws IOException {
                    ContinuityState retained=states.get(sequence);
                    if(retained!=null)return retained;
                    ContinuityState initial=anchor();
                    if(sequence==initial.sequence()){states.put(sequence,initial);return initial;}
                    StrictJson.require(sequence>initial.sequence()&&sequence<=actual.state().sequence(),
                            "requested historical state is outside the actual finite canonical chain");
                    ObjectNode event=event(sequence);
                    ContinuityState value=ContinuityState.fromJson(event.get("after"),layout.machineId());
                    StrictJson.require(value.sequence()==sequence
                            &&StrictJson.text(value.toJson().get("last_event_identity")).equals(StrictJson.text(event.get("identity"))),
                            "captured canonical event after state binding differs");
                    states.put(sequence,value);return value;
                }
            }
            CachedHistory history=new CachedHistory();
            java.util.List<HistoricalTransition> results=new java.util.ArrayList<>();
            for(Pin actualEvent:actualEvents) {
                Pin captured=actual.documents().stream().filter(actualEvent::equals).findFirst()
                        .orElseThrow(()->new IOException("event pin is not in this actual captured canonical history"));
                ObjectNode event=history.document(captured);
                long sequence=StrictJson.integer(event.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER);
                ContinuityState before=history.state(Math.subtractExact(sequence,1)),after=history.state(sequence);
                StrictJson.require(StrictJson.text(event.get("previous_sha256")).equals(ContinuityJson.digest(before.toJson()))
                        && ContinuityJson.same(event.get("after"), after.toJson()), "historical canonical edge predecessor/after differs");
                ObjectNode identity = StrictJson.object(); identity.set("kind", event.get("kind")); identity.set("details", event.get("details"));
                String eventIdentity = StrictJson.text(event.get("identity"));
                StrictJson.require(ContinuityJson.digest(identity).equals(eventIdentity), "historical canonical event identity differs");
                HistoricalTransition retained = new HistoricalTransition(sequence, StrictJson.text(event.get("kind")),
                        ContinuityJson.canonical(event.get("details")), eventIdentity, before, after, captured);
                results.add(retained);
            }
            for (Pin pin : actual.documents()) LedgerFiles.verify(pin);
            // Every captured document is still exact, including anchor/snapshot/indexes, and
            // every captured absent path remains absent. Re-projecting these identical bytes
            // would yield the same Head; no full-chain replay is needed for each requested edge.
            for (Path path : actual.absent()) LedgerFiles.requireAbsent(path);
            return java.util.List.copyOf(results);
        }
        @Override public Pin capturePin(ExactRef reference, int maximumBytes) throws IOException {
            requireWriter(layout.lock());
            StrictJson.require(maximumBytes > 0 && maximumBytes <= MAX_PIN_BYTES, "explicit finite original packet bound");
            return LedgerFiles.exact(Objects.requireNonNull(reference), maximumBytes).pin();
        }
        @Override public void verifyPin(Pin pin) throws IOException {
            requireWriter(layout.lock()); LedgerFiles.verify(Objects.requireNonNull(pin));
        }
        @Override public byte[] readPinned(Pin pin, int maximumBytes) throws IOException {
            requireWriter(layout.lock()); Objects.requireNonNull(pin);
            StrictJson.require(maximumBytes > 0 && maximumBytes <= MAX_PIN_BYTES, "explicit finite original packet bound");
            var actual = LedgerFiles.exact(pin.reference(), maximumBytes);
            if (!actual.pin().equals(pin)) throw new IOException("read must retain the exact captured native file identity");
            return actual.bytes(); // Document.bytes() already returns its detached clone.
        }
        @Override public void requireCommitted(Prepared original, Receipt receipt) throws IOException {
            requireWriter(layout.lock()); Objects.requireNonNull(receipt);
            lookupCommitted(original, java.util.Optional.of(receipt))
                    .orElseThrow(() -> new IOException("the original request has no exact durable event in this canonical chain"));
        }
        @Override public java.util.Optional<Receipt> queryCommitted(Prepared original) throws IOException {
            requireWriter(layout.lock());
            return lookupCommitted(original, java.util.Optional.empty());
        }
        @Override public void requireCommitted(DomainBodies.PreparedImport original,Receipt receipt) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(original);Objects.requireNonNull(receipt);
            var request=original.request();var registered=registration(request.slot());
            StrictJson.require(request.contractSchema().equals(registered.contractSchema()),"historical domain import registered schema differs");
            List<ExactRef> expectedSources=List.copyOf(sources);
            StrictJson.require(original.sources().stream().map(Pin::reference).toList().equals(expectedSources)
                    &&original.evidence().stream().map(Pin::reference).toList().equals(request.evidence())
                    &&original.originalBody().reference().equals(request.originalBody()),"historical domain import changed its actual source/evidence/body closure");
            List<Pin> pins=new ArrayList<>(original.sources());pins.addAll(original.evidence());pins.add(original.originalBody());
            for(Pin pin:pins)LedgerFiles.verify(pin);
            var raw=LedgerFiles.exact(request.originalBody(),registered.maximumBodyBytes());
            StrictJson.require(raw.pin().equals(original.originalBody()),"historical domain original Win32 identity changed");
            domainCanonical(raw.bytes(),registered.maximumBodyBytes());
            // referenceOf only reopens already published immutable originals; this history check never publishes.
            Pin body=artifacts().referenceOf(raw.bytes(),registered.maximumBodyBytes());
            Pin input=artifacts().referenceOf(request.producerInput(),ContinuityJson.DOCUMENT_MAX_BYTES);
            StrictJson.require(java.util.Arrays.equals(artifacts().read(body,registered.maximumBodyBytes()),raw.bytes())
                    &&java.util.Arrays.equals(artifacts().read(input,ContinuityJson.DOCUMENT_MAX_BYTES),request.producerInput()),"historical durable domain body/input differs");
            pins.add(body);pins.add(input);Request expected=domainEvent(original,registered,body,input);
            StrictJson.require(receipt.disposition()!=Disposition.NO_CHANGE&&receipt.eventIdentity().equals(expected.identity()),"actual domain-import event receipt required");
            Head actual=store.head();var event=store.duplicate(expected,actual).orElseThrow(()->new IOException("actual canonical domain-import event is absent"));
            StrictJson.require(event.sequence()==Math.addExact(original.predecessor().state().sequence(),1)
                    &&event.previousSha256().equals(original.predecessor().digest())
                    &&ContinuityJson.same(capturedStateAt(actual,original.predecessor().state().sequence()).toJson(),original.predecessor().state().toJson()),"domain-import event changed its exact prepared predecessor");
            DomainBodies.BodyRef ref=new DomainBodies.BodyRef(request.slot(),registered.contractSchema(),body.reference(),body.identity(),registered.producerSources());
            verifyPreviousBody(DomainBodies.reference(original.predecessor().state(),request.slot()),registered);
            ContinuityState reduced=DomainBodies.reduceImport(original.predecessor().state(),ref);validateReduction(original.predecessor().state(),reduced,expected);
            StrictJson.require(!ContinuityJson.same(reduced.toJson(),original.predecessor().state().toJson()),"no-change import cannot claim a durable mutation");
            ObjectNode projected=reduced.toJson();projected.put("sequence",event.sequence());projected.put("last_event_identity",expected.identity());
            StrictJson.require(ContinuityJson.same(projected,event.after().toJson())
                    &&ContinuityJson.same(capturedStateAt(actual,event.sequence()).toJson(),projected),"domain-import full historical reducer result differs");
            StrictJson.require(receipt.head().sequence()>=event.sequence()&&receipt.head().sequence()<=actual.state().sequence()
                    &&ContinuityJson.same(capturedStateAt(actual,receipt.head().sequence()).toJson(),receipt.head().toJson()),"domain-import receipt is not an exact actual canonical descendant");
            if(receipt.disposition()==Disposition.COMMITTED)StrictJson.require(ContinuityJson.same(receipt.head().toJson(),projected),"COMMITTED domain receipt must bind its own exact after state");
            for(Pin pin:pins)LedgerFiles.verify(pin);requireSameHead(actual,store.head());
        }
        @Override public ContinuityState requireHistoricalState(long sequence, String expectedDigest) throws IOException {
            requireWriter(layout.lock());
            if (sequence < 0 || expectedDigest == null || !expectedDigest.matches("[0-9a-f]{64}"))
                throw new IOException("exact finite historical sequence and lowercase state digest required");
            try {
                Head actual = this.head();
                if (sequence > actual.state().sequence())
                    throw new IOException("requested historical state is beyond the actual canonical head");
                ContinuityState retained = capturedStateAt(actual, sequence);
                if (!ContinuityJson.digest(retained.toJson()).equals(expectedDigest))
                    throw new IOException("historical state differs from the exact expected canonical digest");
                requireSameHead(actual, this.head());
                return retained;
            } catch (org.xar.ck3.control.contracts.ContractViolationException invalidHistory) {
                throw new IOException("actual finite canonical historical state is unavailable", invalidHistory);
            }
        }
        @Override public Head requireHistoricalHead(long sequence,String expectedDigest) throws IOException {
            requireWriter(layout.lock());StrictJson.safe(sequence,0);requireDigest(expectedDigest);
            Head actual=store.head();ContinuityState retained=capturedStateAt(actual,sequence);
            StrictJson.require(ContinuityJson.digest(retained.toJson()).equals(expectedDigest),"historical Head state digest differs from actual ancestry");
            // Retain the actual complete canonical proof, including descendants. The returned ancestor State
            // is explicitly read-only: its state/pins cannot pass requireSameHead as the live writer Head.
            List<Pin> pins=new ArrayList<>(actual.documents());pins.addAll(captureDomain(sources));
            for(var slot:DomainBodies.Slot.values()) {
                var stored=DomainBodies.reference(retained,slot);if(stored.isEmpty())continue;
                var body=stored.orElseThrow();var registered=registration(slot);
                StrictJson.require(body.contractSchema().equals(registered.contractSchema()),"historical domain contract differs");
                Pin material=new Pin(body.payload(),body.identity());
                domainCanonical(artifacts().read(material,registered.maximumBodyBytes()),registered.maximumBodyBytes());pins.add(material);
            }
            // This proves the historical state and its referenced durable bodies. Individual import
            // input/evidence replays use requireHistoricalImport; old external CAS input inodes are
            // not a permanent archive identity contract for every unrelated earlier import.
            for(Pin pin:pins)LedgerFiles.verify(pin);requireSameHead(actual,store.head());
            return new Head(retained,pins.stream().distinct().toList(),actual.absent(),actual.indexRepairs(),actual.snapshotNeedsRecovery());
        }
        @Override public DomainBodies.RecordedImport requireHistoricalImport(DomainBodies.Slot slot,long sequence,String afterDigest) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(slot);StrictJson.safe(sequence,1);requireDigest(afterDigest);
            Head actual=store.head();ObjectNode event=capturedEventAt(actual,sequence);
            StrictJson.require(DomainBodies.IMPORT_KIND.equals(StrictJson.text(event.get("kind"))),"exact recorded DOMAIN_IMPORT event required");
            ContinuityState after=ContinuityState.fromJson(event.get("after"),layout.machineId());
            StrictJson.require(ContinuityJson.digest(after.toJson()).equals(afterDigest),"recorded import differs from requested canonical after state");
            String predecessor=StrictJson.text(event.get("previous_sha256"));
            Head before=requireHistoricalHead(Math.subtractExact(sequence,1),predecessor);
            ObjectNode details=StrictJson.object(event.get("details"),java.util.Set.of("evidence_id","machine_id","source","domain_body","precondition_digest"));
            StrictJson.require(StrictJson.text(details.get("machine_id")).equals(layout.machineId()),"recorded domain import changed machine");
            requireDigest(StrictJson.text(details.get("precondition_digest")));
            DomainBodies.BodyRef body=DomainBodies.BodyRef.fromJson(details.get("domain_body"));
            DomainBodies.Registration registered=registration(slot);
            StrictJson.require(body.slot()==slot&&body.contractSchema().equals(registered.contractSchema()),"recorded import changed its exact slot/registered contract");
            ObjectNode source=StrictJson.object(details.get("source"),java.util.Set.of("original_body","producer_input","producer_sources","evidence"));
            List<ExactRef> producers=domainReferences(source.get("producer_sources"),64);
            StrictJson.require(producers.equals(body.producerSources()),"recorded import original producer closure differs from body data");
            List<Pin> current=new ArrayList<>(captureDomain(sources));
            List<ExactRef> evidence=domainReferences(source.get("evidence"),64);current.addAll(captureDomain(evidence));
            Pin durable=new Pin(body.payload(),body.identity());byte[] raw=artifacts().read(durable,registered.maximumBodyBytes());
            domainCanonical(raw,registered.maximumBodyBytes());current.add(durable);
            ExactRef originalBody=ExactRef.fromJson(source.get("original_body"));
            StrictJson.require(originalBody.bytes()==raw.length&&originalBody.sha256().equals(LedgerFiles.sha(raw)),"durable body differs from original external input content");
            // originalBody's external CAS inode is deliberately not inferred or made permanent.
            // The durable payload keeps its genuine serialized native identity and immutable archive custody.
            ExactRef inputRef=ExactRef.fromJson(source.get("producer_input"));byte[] input=artifacts().read(inputRef,ContinuityJson.DOCUMENT_MAX_BYTES);
            var inputFile=LedgerFiles.exact(inputRef,ContinuityJson.DOCUMENT_MAX_BYTES);current.add(inputFile.pin());
            StrictJson.require(java.util.Arrays.equals(input,inputFile.bytes())&&java.util.Arrays.equals(input,canonical(input)),"recorded producer input is not its exact immutable canonical original");
            String evidenceId=StrictJson.text(details.get("evidence_id")),prefix="domain-body:"+slot.name()+":";
            StrictJson.require(evidenceId.startsWith(prefix)&&evidenceId.length()>prefix.length(),"recorded import changed its exact slot/evidence identity");
            var request=new DomainBodies.ImportRequest(slot,body.contractSchema(),originalBody,input,evidence,evidenceId.substring(prefix.length()));
            Request envelope=new Request(DomainBodies.IMPORT_KIND,ContinuityJson.canonical(details),List.of(inputRef));
            StrictJson.require(envelope.identity().equals(StrictJson.text(event.get("identity"))),"recorded domain event identity differs");
            verifyPreviousBody(DomainBodies.reference(before.state(),slot),registered);
            ContinuityState reduced=DomainBodies.reduceImport(before.state(),body);validateReduction(before.state(),reduced,envelope);
            StrictJson.require(!ContinuityJson.same(before.state().toJson(),reduced.toJson()),"recorded import is not a real state change");
            ObjectNode projected=reduced.toJson();projected.put("sequence",sequence);projected.put("last_event_identity",envelope.identity());
            StrictJson.require(ContinuityJson.same(projected,after.toJson())
                    &&ContinuityJson.same(capturedStateAt(actual,sequence).toJson(),after.toJson()),"recorded DOMAIN_IMPORT changed a non-domain field or canonical reducer result");
            Pin eventPin=actual.documents().stream().filter(pin->java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(layout.event(sequence)))
                    .findFirst().orElseThrow(()->new IOException("recorded domain event lacks its actual captured file identity"));current.add(eventPin);
            for(Pin pin:current)LedgerFiles.verify(pin);requireSameHead(actual,store.head());
            return new DomainBodies.RecordedImport(before,new Receipt(Disposition.ALREADY_COMMITTED,after,envelope.identity(),0,false),request,body,eventPin.reference(),current.stream().distinct().toList());
        }
        /** Read-only exact ancestry consisting solely of the registered canonical domain-import reducer. */
        @Override public void requireDomainImportContinuation(long originalSequence,String originalDigest) throws IOException {
            requireWriter(layout.lock());
            if(originalSequence<0||originalDigest==null||!originalDigest.matches("[0-9a-f]{64}"))
                throw new IOException("exact original domain-continuation sequence and digest required");
            try {
                Head actual=store.head();ContinuityState cursor=capturedStateAt(actual,originalSequence);
                StrictJson.require(ContinuityJson.digest(cursor.toJson()).equals(originalDigest),"original attachment canonical state digest differs");
                List<Pin> originals=new ArrayList<>(captureDomain(sources));
                for(long sequence=Math.addExact(originalSequence,1);sequence<=actual.state().sequence();sequence++){
                    ObjectNode event=capturedEventAt(actual,sequence);
                    StrictJson.require(DomainBodies.IMPORT_KIND.equals(StrictJson.text(event.get("kind"))),"only actual domain imports may continue an attachment");
                    ObjectNode details=StrictJson.object(event.get("details"),java.util.Set.of("evidence_id","machine_id","source","domain_body","precondition_digest"));
                    StrictJson.require(StrictJson.text(details.get("machine_id")).equals(layout.machineId()),"domain continuation changed actual machine");
                    requireDigest(StrictJson.text(details.get("precondition_digest")));
                    DomainBodies.BodyRef body=DomainBodies.BodyRef.fromJson(details.get("domain_body"));
                    DomainBodies.Registration registered=registration(body.slot());
                    StrictJson.require(body.contractSchema().equals(registered.contractSchema()),"historical import differs from its actual registered contract");
                    ObjectNode source=StrictJson.object(details.get("source"),java.util.Set.of("original_body","producer_input","producer_sources","evidence"));
                    List<ExactRef> producerSources=domainReferences(source.get("producer_sources"),64);
                    StrictJson.require(producerSources.equals(body.producerSources()),"historical import producer closure differs from body data");
                    List<ExactRef> evidence=domainReferences(source.get("evidence"),64);originals.addAll(captureDomain(evidence));
                    ExactRef originalRef=ExactRef.fromJson(source.get("original_body"));
                    var original=LedgerFiles.exact(originalRef,registered.maximumBodyBytes());originals.add(original.pin());
                    domainCanonical(original.bytes(),registered.maximumBodyBytes());
                    Pin bodyPin=new Pin(body.payload(),body.identity());
                    byte[] durableBody=artifacts().read(bodyPin,registered.maximumBodyBytes());originals.add(bodyPin);
                    StrictJson.require(java.util.Arrays.equals(original.bytes(),durableBody),"historical original body differs from the exact durable domain payload");
                    ExactRef inputRef=ExactRef.fromJson(source.get("producer_input"));
                    byte[] input=artifacts().read(inputRef,ContinuityJson.DOCUMENT_MAX_BYTES);
                    var actualInput=LedgerFiles.exact(inputRef,ContinuityJson.DOCUMENT_MAX_BYTES);originals.add(actualInput.pin());
                    StrictJson.require(java.util.Arrays.equals(input,actualInput.bytes())&&java.util.Arrays.equals(input,canonical(input)),
                            "historical producer input differs from its actual canonical immutable original");
                    String evidenceId=StrictJson.text(details.get("evidence_id"));
                    StrictJson.require(evidenceId.startsWith("domain-body:"+body.slot().name()+":")
                            &&evidenceId.length()>("domain-body:"+body.slot().name()+":").length(),"historical import evidence identity/slot differs");
                    Request request=new Request(DomainBodies.IMPORT_KIND,ContinuityJson.canonical(details),List.of(inputRef));
                    StrictJson.require(request.identity().equals(StrictJson.text(event.get("identity")))
                            &&ContinuityJson.digest(cursor.toJson()).equals(StrictJson.text(event.get("previous_sha256"))),
                            "domain continuation event identity or exact predecessor differs");
                    java.util.Optional<DomainBodies.BodyRef> previous=DomainBodies.reference(cursor,body.slot());
                    verifyPreviousBody(previous,registered);
                    previous.ifPresent(retained->originals.add(new Pin(retained.payload(),retained.identity())));
                    ContinuityState reduced=DomainBodies.reduceImport(cursor,body);
                    validateReduction(cursor,reduced,request);
                    StrictJson.require(!ContinuityJson.same(cursor.toJson(),reduced.toJson()),"a domain import event cannot invent a no-change publication");
                    ObjectNode projected=reduced.toJson();projected.put("sequence",sequence);projected.put("last_event_identity",request.identity());
                    StrictJson.require(ContinuityJson.same(projected,event.get("after")),"historical import contains a non-domain mutation or field rollback");
                    cursor=ContinuityState.fromJson(event.get("after"),layout.machineId());
                }
                StrictJson.require(ContinuityJson.same(cursor.toJson(),actual.state().toJson()),"actual import continuation does not reach the exact captured head");
                for(Pin pin:originals)LedgerFiles.verify(pin);
                requireSameHead(actual,store.head());
            } catch(org.xar.ck3.control.contracts.ContractViolationException invalid){
                throw new IOException("actual domain-import-only continuation is unavailable",invalid);
            }
        }
        @Override public org.xar.ck3.control.continuity.EpisodeWindow.CommittedBegin beginEpisodeWindow(org.xar.ck3.control.continuity.EpisodeWindow.Begin begin) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(begin);Request request=begin.request();
            Receipt receipt=commit(preview(request));Head actual=store.head();
            ContinuityEvent event=store.duplicate(request,actual).orElseThrow(()->new IOException("BEGIN has no actual committed canonical event"));
            org.xar.ck3.control.continuity.EpisodeWindow.CommittedBegin result=new org.xar.ck3.control.continuity.EpisodeWindow.CommittedBegin(
                    begin,event.sequence(),event.identity(),ContinuityJson.digest(event.after().toJson()),eventPin(actual,event.sequence()));
            requireEpisodeWindowBegin(result);requireSameHead(actual,store.head());return result;
        }
        @Override public org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline baselineEpisodeWindow(org.xar.ck3.control.continuity.EpisodeWindow.Baseline baseline) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(baseline);requireEpisodeWindowBegin(baseline.begin());
            Request request=baseline.request();commit(preview(request));Head actual=store.head();
            ContinuityEvent event=store.duplicate(request,actual).orElseThrow(()->new IOException("BASELINE has no actual committed canonical event"));
            var result=new org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline(baseline,event.sequence(),event.identity(),
                    ContinuityJson.digest(event.after().toJson()),eventPin(actual,event.sequence()));
            requireEpisodeWindowActive(result);requireSameHead(actual,store.head());return result;
        }
        @Override public void requireEpisodeWindowBegin(org.xar.ck3.control.continuity.EpisodeWindow.CommittedBegin begin) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(begin);Head actual=store.head();
            requireHistoricalWindowBegin(actual,begin);
            var current=org.xar.ck3.control.continuity.EpisodeWindow.state(actual.state()).orElseThrow(()->new IOException("current episode BEGIN unavailable"));
            StrictJson.require(current.begin().equals(begin.begin()),"BEGIN belongs to an earlier or different episode window");
            requireSameHead(actual,store.head());
        }
        private void requireHistoricalWindowBegin(Head actual,org.xar.ck3.control.continuity.EpisodeWindow.CommittedBegin begin) throws IOException {
            requireWindowEvent(actual,begin.sequence(),begin.eventIdentity(),begin.headDigest(),begin.eventPin(),begin.begin().request());
            var lifecycle=capturedEventAt(actual,begin.begin().lifecycleSequence());
            Pin lifecyclePin=eventPin(actual,begin.begin().lifecycleSequence());
            StrictJson.require(lifecyclePin.reference().equals(begin.begin().lifecycleEventRef())
                    &&StrictJson.text(lifecycle.get("identity")).equals(begin.begin().lifecycleEventIdentity()),"BEGIN original lifecycle event differs");
            LedgerFiles.verify(lifecyclePin);for(ExactRef ref:begin.begin().request().evidence())LedgerFiles.verify(LedgerFiles.exact(ref,MAX_PIN_BYTES).pin());
        }
        @Override public void requireEpisodeWindowActive(org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline baseline) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(baseline);Head actual=store.head();requireHistoricalWindowBaseline(actual,baseline);
            var active=org.xar.ck3.control.continuity.EpisodeWindow.requireActive(actual.state());
            StrictJson.require(active.baseline().orElseThrow().equals(baseline.baseline()),"current ACTIVE window has another original first SAVE pair");
            requireSameHead(actual,store.head());
        }
        @Override public void requireHistoricalEpisodeWindowBaseline(org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline baseline) throws IOException {
            requireWriter(layout.lock());Objects.requireNonNull(baseline);Head actual=store.head();
            requireHistoricalWindowBaseline(actual,baseline);requireSameHead(actual,store.head());
        }
        private void requireHistoricalWindowBaseline(Head actual,org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline baseline) throws IOException {
            requireHistoricalWindowBegin(actual,baseline.baseline().begin());
            requireWindowEvent(actual,baseline.sequence(),baseline.eventIdentity(),baseline.headDigest(),baseline.eventPin(),baseline.baseline().request());
            var original=org.xar.ck3.control.continuity.EpisodeWindow.requireActive(capturedStateAt(actual,baseline.sequence()));
            StrictJson.require(original.baseline().orElseThrow().equals(baseline.baseline()),"historical BASELINE changed its original first SAVE pair");
            for(ExactRef ref:baseline.baseline().request().evidence())LedgerFiles.verify(LedgerFiles.exact(ref,MAX_PIN_BYTES).pin());
        }
        private Pin eventPin(Head actual,long sequence) throws IOException {
            Path path=layout.event(sequence);return actual.documents().stream().filter(pin->Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(path))
                    .findFirst().orElseThrow(()->new IOException("exact immutable episode event absent from current history"));
        }
        private void requireWindowEvent(Head actual,long sequence,String identity,String digest,Pin original,Request expected) throws IOException {
            StrictJson.require(eventPin(actual,sequence).equals(original),"original window event native file identity changed");LedgerFiles.verify(original);
            ObjectNode event=capturedEventAt(actual,sequence);ContinuityState after=capturedStateAt(actual,sequence);
            StrictJson.require(StrictJson.text(event.get("identity")).equals(identity)&&expected.identity().equals(identity)
                    &&StrictJson.text(event.get("kind")).equals(expected.kind())&&ContinuityJson.same(event.get("details"),expected.detailsObject())
                    &&ContinuityJson.digest(after.toJson()).equals(digest),"exact original window event/body/head digest differs");
            ContinuityState before=capturedStateAt(actual,Math.subtractExact(sequence,1));
            org.xar.ck3.control.continuity.EpisodeWindow.requireReduction(before,after,expected,true);
        }
        private List<ExactRef> domainReferences(com.fasterxml.jackson.databind.JsonNode value,int maximum){
            StrictJson.require(value!=null&&value.isArray()&&value.size()<=maximum,"finite exact historical domain reference list required");
            List<ExactRef> refs=new ArrayList<>();value.forEach(item->refs.add(ExactRef.fromJson(item)));return List.copyOf(refs);
        }
        private void verifyHistoricalSources(Prepared original) throws IOException {
            StrictJson.require(original.sources().stream().map(Pin::reference).toList().equals(sources)
                    && original.evidence().stream().map(Pin::reference).toList().equals(original.request().evidence()),
                    "historical preparation must retain the configured source and evidence closure");
            for (Pin pin : original.sources()) LedgerFiles.verify(pin);
            for (Pin pin : original.evidence()) LedgerFiles.verify(pin);
        }
        private java.util.Optional<Receipt> lookupCommitted(Prepared original, java.util.Optional<Receipt> supplied) throws IOException {
            requireWriter(layout.lock()); Objects.requireNonNull(original); Objects.requireNonNull(supplied);
            Request request = original.request();
            if (supplied.isPresent()) {
                Receipt receipt = supplied.orElseThrow();
                StrictJson.require(receipt.disposition() != Disposition.NO_CHANGE
                        && receipt.eventIdentity().equals(request.identity()), "an actual durable event receipt is required");
            }
            verifyHistoricalSources(original);
            Head actual = head();
            java.util.Optional<ContinuityEvent> committed = store.duplicate(request, actual);
            if (committed.isEmpty()) {
                verifyHistoricalSources(original);
                for (Pin pin : actual.documents()) LedgerFiles.verify(pin);
                for (Path path : actual.absent()) LedgerFiles.requireAbsent(path);
                return java.util.Optional.empty(); // Absence is not permission to dispatch or retry an unknown native action.
            }
            ContinuityEvent event = committed.orElseThrow();
            StrictJson.require(event.sequence() == Math.addExact(original.predecessor().state().sequence(), 1)
                    && event.previousSha256().equals(original.predecessor().digest()),
                    "durable event does not follow the exact prepared predecessor");
            StrictJson.require(ContinuityJson.same(capturedStateAt(actual, original.predecessor().state().sequence()).toJson(),
                    original.predecessor().state().toJson()), "prepared predecessor is outside the current canonical lineage");
            validateReduction(original.predecessor().state(), original.reduced(), request);
            ObjectNode projected = original.reduced().toJson();
            projected.put("sequence", event.sequence()); projected.put("last_event_identity", request.identity());
            StrictJson.require(ContinuityJson.same(projected, event.after().toJson())
                    && ContinuityJson.same(capturedStateAt(actual, event.sequence()).toJson(), event.after().toJson()),
                    "complete durable event kind/details/reduced state differs from the original preparation");
            Receipt receipt = supplied.orElseGet(() -> new Receipt(Disposition.ALREADY_COMMITTED, actual.state(), request.identity(), 0, false));
            StrictJson.require(receipt.head().sequence() >= event.sequence()
                    && receipt.head().sequence() <= actual.state().sequence()
                    && ContinuityJson.same(capturedStateAt(actual, receipt.head().sequence()).toJson(), receipt.head().toJson()),
                    "receipt head is not an exact retained canonical descendant");
            if (receipt.disposition() == Disposition.COMMITTED)
                StrictJson.require(ContinuityJson.same(receipt.head().toJson(), event.after().toJson()),
                        "COMMITTED receipt must bind the event's own complete resulting head");
            verifyHistoricalSources(original);
            for (Pin pin : actual.documents()) LedgerFiles.verify(pin);
            for (Path path : actual.absent()) LedgerFiles.requireAbsent(path);
            return java.util.Optional.of(receipt);
        }
        private ContinuityState capturedStateAt(Head actual, long sequence) throws IOException {
            Pin anchor = actual.documents().stream().filter(pin -> pin.reference().equals(layout.anchor())).findFirst()
                    .orElseThrow(() -> new IOException("canonical anchor is absent from captured history"));
            ContinuityState anchored = ContinuityState.fromJson(ContinuityJson.parseObject(readPinned(anchor, ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES), layout.machineId());
            if (sequence == anchored.sequence()) return anchored;
            StrictJson.require(sequence > anchored.sequence() && sequence <= actual.state().sequence(),
                    "requested historical state is outside the actual finite canonical chain");
            return ContinuityState.fromJson(capturedEventAt(actual,sequence).get("after"),layout.machineId());
        }
        private ObjectNode capturedEventAt(Head actual,long sequence) throws IOException {
            java.nio.file.Path path = layout.event(sequence);
            Pin captured = actual.documents().stream().filter(pin -> java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(path))
                    .findFirst().orElseThrow(() -> new IOException("requested state is absent from the actual finite canonical history"));
            ObjectNode document = ContinuityJson.parseObject(readPinned(captured, ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
            StrictJson.object(document, java.util.Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
            StrictJson.require(StrictJson.integer(document.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER) == sequence,
                    "captured canonical event sequence differs");
            ContinuityState state = ContinuityState.fromJson(document.get("after"), layout.machineId());
            StrictJson.require(state.sequence() == sequence
                    && StrictJson.text(state.toJson().get("last_event_identity")).equals(StrictJson.text(document.get("identity"))),
                    "captured canonical event after state binding differs");
            return document;
        }
        public Head head() throws IOException {
            checkOpen();
            Head retained=retainedHead;retainedHead=null;
            if(retained!=null&&!retained.snapshotNeedsRecovery()&&retained.indexRepairs().isEmpty()) {
                Pin snapshot=retained.documents().stream()
                        .filter(pin->layout.snapshot().equals(java.nio.file.Path.of(pin.reference().path())))
                        .findFirst().orElseThrow(()->new IOException("captured ledger snapshot is absent"));
                if(snapshot.identity().equals(LedgerFiles.identity(layout.snapshot()))) {
                    java.nio.file.Path next=layout.event(Math.addExact(retained.state().sequence(),1));
                    if(!java.nio.file.Files.exists(next,java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
                        LedgerFiles.requireAbsent(next);retainedHead=retained;return retained;
                    }
                }
            }
            Head actual=store.head();retainedHead=actual;return actual;
        }
        public ExactRef persistedHead() throws IOException {
            checkOpen(); return LedgerFiles.read(layout.snapshot(), ContinuityJson.LEDGER_MAX_BYTES).pin().reference();
        }
        public Prepared preview(Request request) throws IOException {
            StrictJson.require(!DomainBodies.IMPORT_KIND.equals(request.kind()), "domain imports use their registered original-producer path");
            return previewInternal(request, authority);
        }
        private Prepared previewInternal(Request request, TransitionAuthority selectedAuthority) throws IOException {
            checkOpen(); Objects.requireNonNull(request);
            Head before = this.head(); List<Pin> actualSources = captureDomain(sources), evidence = capture(request);
            var committed = store.duplicate(request, before);
            if (committed.isPresent()) {
                // Like the original WindowLedger.apply, recover an exact durable outcome before
                // consulting expired live business preconditions. This is already-committed DATA:
                // its digest is the captured event identity, never fresh reducer qualification.
                for (Pin pin : actualSources) LedgerFiles.verify(pin);
                for (Pin pin : evidence) LedgerFiles.verify(pin);
                requireSameHead(before, store.head());
                return new Prepared(before, request, actualSources, evidence, before.state(), committed.orElseThrow().identity());
            }
            String precondition = selectedAuthority.revalidate(before, request); requireDigest(precondition);
            ContinuityState reduced = selectedAuthority.reduce(before.state(), request);
            validateReduction(before.state(), reduced, request);
            return new Prepared(before, request, actualSources, evidence, reduced, precondition);
        }
        public Receipt commit(Prepared prepared) throws IOException {
            StrictJson.require(!DomainBodies.IMPORT_KIND.equals(prepared.request().kind()), "domain imports use their registered original-producer path");
            return commitInternal(prepared, authority);
        }
        private Receipt commitInternal(Prepared prepared, TransitionAuthority selectedAuthority) throws IOException {
            checkOpen();
            retainedDomainHead = null;
            try {
                Receipt receipt = commitPrepared(prepared,selectedAuthority);
                if (receipt.disposition() != Disposition.COMMITTED) retainedHead = null;
                // Retain the Head validated by commitPrepared's readback to avoid re-parsing history in requireCommitted.
                // If commitPrepared throws, retainedHead remains null (cleared at start), preventing stale cache use.
                return receipt;
            } catch (IOException | RuntimeException | Error error) {
                retainedHead = null;
                throw error;
            } finally {
                // Authority callbacks can read domains while a commit is being validated.
                // Their pre-write view must not survive any commit outcome.
                retainedDomainHead = null;
            }
        }
        private Receipt commitPrepared(Prepared prepared, TransitionAuthority selectedAuthority) throws IOException {
            Objects.requireNonNull(prepared);
            Request request = prepared.request();
            // Sources and evidence are checked before any recovery or durable write.
            for (Pin pin : prepared.sources()) LedgerFiles.verify(pin);
            StrictJson.require(prepared.sources().stream().map(Pin::reference).toList().equals(sources), "configured source closure");
            for (Pin pin : prepared.evidence()) LedgerFiles.verify(pin);
            StrictJson.require(prepared.evidence().stream().map(Pin::reference).toList().equals(request.evidence()), "evidence closure");
            Head actual = this.head();
            // Exact duplicate only repairs already committed persistence; no reducer rerun or new credit.
            if (store.duplicate(request, actual).isPresent()) {
                return recoverDuplicate(request, actual);
            }
            requireSameHead(prepared.predecessor(), actual);
            String precondition = selectedAuthority.revalidate(actual, request); requireDigest(precondition);
            StrictJson.require(precondition.equals(prepared.preconditionDigest()), "actual domain preconditions changed inside original writer lock");
            ContinuityState reduced = selectedAuthority.reduce(actual.state(), request);
            validateReduction(actual.state(), reduced, request);
            StrictJson.require(ContinuityJson.same(reduced.toJson(), prepared.reduced().toJson()), "same reducer result changed after preview");
            // Re-read sources after actual validation/reduction, before durable mutation.
            for (Pin pin : prepared.sources()) LedgerFiles.verify(pin);
            for (Pin pin : prepared.evidence()) LedgerFiles.verify(pin);
            // This held operation already projected the full history. Recheck its exact
            // bytes/native identities and every absence without parsing that history again.
            for (Pin pin : actual.documents()) LedgerFiles.verify(pin);
            for (Path path : actual.absent()) LedgerFiles.requireAbsent(path);
            long sequence = Math.addExact(actual.state().sequence(), 1);
            ObjectNode after = reduced.toJson(); after.put("sequence", sequence); after.put("last_event_identity", request.identity());
            ContinuityState committed = ContinuityState.fromJson(after, layout.machineId());
            ContinuityEvent event = new ContinuityEvent(sequence, OffsetDateTime.ofInstant(clock.instant(), ZoneOffset.UTC).toString(),
                    request.kind(), request.details(), request.identity(), actual.digest(), committed);
            // Apply the retained envelope validator and both output caps before the first write.
            byte[] eventBytes = ContinuityJson.canonical(ContinuityEvent.fromJson(event.toJson(), actual.state()).toJson());
            if (eventBytes.length + 1 > ContinuityJson.LEDGER_MAX_BYTES || committed.canonicalBytes().length + 1 > ContinuityJson.LEDGER_MAX_BYTES)
                throw new IOException("original writer output cap");
            LedgerFiles.requireAbsent(layout.event(sequence)); LedgerFiles.requireAbsent(layout.sourceIndex(request.sourceKey()));
            boolean unchanged=ContinuityJson.same(actual.state().toJson(),reduced.toJson());
            List<LedgerFiles.AtomicWrite> recovery=store.recoveryWrites(actual);
            List<LedgerFiles.AtomicWrite> writes=new ArrayList<>(recovery);
            LedgerFiles.AtomicWrite eventWrite=LedgerFiles.prepareAtomic(layout.event(sequence),eventBytes,false,ContinuityJson.LEDGER_MAX_BYTES);
            LedgerFiles.AtomicWrite snapshotWrite=LedgerFiles.prepareAtomic(layout.snapshot(),committed.canonicalBytes(),true,ContinuityJson.LEDGER_MAX_BYTES);
            LedgerFiles.AtomicWrite indexWrite=LedgerFiles.prepareAtomic(layout.sourceIndex(request.sourceKey()),
                    ContinuityJson.canonical(new IndexRepair(layout.sourceIndex(request.sourceKey()),sequence,request.identity()).toJson()),false);
            if(!unchanged){writes.add(eventWrite);writes.add(snapshotWrite);writes.add(indexWrite);}
            try {
                if(writes.isEmpty())return new Receipt(Disposition.NO_CHANGE,actual.state(),request.identity(),0,false);
                // Quote the entire physical commit/recovery before the first pending file is created.
                return storageGuard.write(LedgerFiles.plan(layout.lock(),writes),()->{
                    retainedHead=null;
                    retainedDomainHead=null;
                    int recovered=store.recover(recovery,storageGuard);
                    if(unchanged)return new Receipt(Disposition.NO_CHANGE,actual.state(),request.identity(),recovered,recovered>0);
                    LedgerFiles.atomic(storageGuard,layout.lock(),eventWrite);
                    faults.reached(WriterFaultProbe.Boundary.EVENT_PUBLISHED,sequence);
                    LedgerFiles.atomic(storageGuard,layout.lock(),snapshotWrite);
                    faults.reached(WriterFaultProbe.Boundary.SNAPSHOT_PUBLISHED,sequence);
                    LedgerFiles.atomic(storageGuard,layout.lock(),indexWrite);
                    faults.reached(WriterFaultProbe.Boundary.SOURCE_INDEX_PUBLISHED,sequence);
                    Head readback=store.head();
                    StrictJson.require(ContinuityJson.same(readback.state().toJson(),committed.toJson())
                            &&!readback.snapshotNeedsRecovery()&&readback.indexRepairs().isEmpty(),"committed ledger readback");
                    retainedHead = readback;
                    return new Receipt(Disposition.COMMITTED,committed,request.identity(),recovered+3,recovered>0);
                });
            }catch(IOException|RuntimeException error){throw new CommitUncertainException(request.identity(),sequence,error);}
        }
        private Receipt recoverDuplicate(Request request, Head actual) throws IOException {
            retainedHead=null; // Recovery may mutate persistence; only a normal commit retains its validated readback.
            retainedDomainHead=null;
            try {
                int recovered = store.recover(actual, storageGuard);
                Head readback = store.head();
                StrictJson.require(ContinuityJson.same(actual.state().toJson(), readback.state().toJson())
                        && !readback.snapshotNeedsRecovery() && readback.indexRepairs().isEmpty(), "exact committed receipt recovery readback");
                return new Receipt(Disposition.ALREADY_COMMITTED, readback.state(), request.identity(), recovered, recovered > 0);
            } catch (IOException | RuntimeException error) {
                throw new CommitUncertainException(request.identity(), actual.state().sequence(), error);
            } finally {
                retainedDomainHead=null;
            }
        }
        private DomainBodies.Registration registration(DomainBodies.Slot slot) throws IOException {
            return extensions.domains().stream().filter(registration -> registration.slot() == slot).findFirst()
                    .orElseThrow(() -> new IOException("canonical domain slot not registered: " + slot));
        }
        private ImmutableArtifactStore artifacts() throws IOException {
            return extensions.artifacts().orElseThrow(() -> new IOException("the canonical immutable artifact store is unavailable"));
        }
        @Override public DomainBodies.Read readDomain(DomainBodies.Slot slot) throws IOException {
            requireWriter(layout.lock());
            Head head = retainedDomainHead;
            if (head == null) {
                // This view belongs only to the current held writer session. Each new session
                // reads the current canonical head; actual writes invalidate this local view.
                head = head();
                retainedDomainHead = head;
            }
            ExactRef headRef = head.documents().stream()
                    .filter(pin -> layout.snapshot().equals(java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize()))
                    .findFirst().orElseThrow(() -> new IOException("captured ledger snapshot is absent")).reference();
            if (extensions.domains().stream().noneMatch(registration -> registration.slot() == slot))
                return new DomainBodies.Unavailable(DomainBodies.Reason.SLOT_UNREGISTERED, java.util.Optional.of(headRef), "no authoritative domain producer registration");
            java.util.Optional<DomainBodies.BodyRef> reference;
            try { reference = DomainBodies.reference(head.state(), slot); }
            catch (org.xar.ck3.control.contracts.ContractViolationException error) {
                return new DomainBodies.Unavailable(DomainBodies.Reason.INVALID_BODY, java.util.Optional.of(headRef), error.getMessage());
            }
            if (reference.isEmpty()) return new DomainBodies.Unavailable(DomainBodies.Reason.UNIMPORTED, java.util.Optional.of(headRef), "original domain body has not been imported; missing is not clear");
            if (head.snapshotNeedsRecovery() || !head.indexRepairs().isEmpty())
                return new DomainBodies.Unavailable(DomainBodies.Reason.SOURCE_UNAVAILABLE, java.util.Optional.of(headRef), "canonical snapshot/index recovery is pending");
            try {
                DomainBodies.Registration registration = registration(slot); DomainBodies.BodyRef body = reference.orElseThrow();
                StrictJson.require(registration.contractSchema().equals(body.contractSchema()), "explicit original domain contract version");
                // Always read the actual body from the artifact store to detect body changes.
                byte[] raw = artifacts().read(new Pin(body.payload(), body.identity()), registration.maximumBodyBytes());
                byte[] canonical = domainCanonical(raw, registration.maximumBodyBytes());
                return new DomainBodies.Available(body, canonical, headRef, head.documents());
            } catch (IOException error) {
                return new DomainBodies.Unavailable(DomainBodies.Reason.BODY_IDENTITY_CHANGED, java.util.Optional.of(headRef), error.getMessage());
            } catch (org.xar.ck3.control.contracts.ContractViolationException error) {
                return new DomainBodies.Unavailable(DomainBodies.Reason.INVALID_BODY, java.util.Optional.of(headRef), error.getMessage());
            }
        }
        @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request) throws IOException {
            checkOpen(); DomainBodies.Registration registration = registration(request.slot());
            StrictJson.require(registration.contractSchema().equals(request.contractSchema()), "exact registered domain body contract");
            Head head = this.head(); var original = LedgerFiles.exact(request.originalBody(), registration.maximumBodyBytes());
            domainCanonical(original.bytes(), registration.maximumBodyBytes());
            List<Pin> configured = new ArrayList<>(captureDomain(sources));
            List<Pin> evidence = captureDomain(request.evidence());
            java.util.Optional<DomainBodies.BodyRef> previous = DomainBodies.reference(head.state(), request.slot());
            verifyPreviousBody(previous, registration);
            String checked = registration.verifier().verify(head, previous, request, original.bytes()); requireDigest(checked);
            LedgerFiles.verify(original.pin()); for (Pin pin : configured) LedgerFiles.verify(pin); for (Pin pin : evidence) LedgerFiles.verify(pin);
            requireSameHead(head, store.head());
            return new DomainBodies.PreparedImport(head, request, original.pin(), configured, evidence, checked);
        }
        @Override public Receipt commitImport(DomainBodies.PreparedImport prepared) throws IOException {
            checkOpen();
            retainedDomainHead=null;
            try {
                return commitDomainImport(prepared);
            } finally {
                retainedDomainHead=null;
            }
        }
        private Receipt commitDomainImport(DomainBodies.PreparedImport prepared) throws IOException {
            checkOpen(); DomainBodies.ImportRequest request = prepared.request(); DomainBodies.Registration registration = registration(request.slot());
            StrictJson.require(registration.contractSchema().equals(request.contractSchema()), "registered domain schema");
            List<ExactRef> expectedConfigured = new ArrayList<>(sources);
            StrictJson.require(prepared.sources().stream().map(Pin::reference).toList().equals(expectedConfigured)
                    && prepared.evidence().stream().map(Pin::reference).toList().equals(request.evidence())
                    && prepared.originalBody().reference().equals(request.originalBody()), "exact prepared original domain source closure");
            for (Pin pin : prepared.sources()) LedgerFiles.verify(pin); for (Pin pin : prepared.evidence()) LedgerFiles.verify(pin);
            LedgerFiles.verify(prepared.originalBody());
            var original = LedgerFiles.exact(request.originalBody(), registration.maximumBodyBytes());
            StrictJson.require(original.pin().equals(prepared.originalBody()), "actual original body identity CAS");
            byte[] canonical = domainCanonical(original.bytes(), registration.maximumBodyBytes());
            Head beforePublish = this.head();
            if (!ContinuityJson.same(beforePublish.state().toJson(), prepared.predecessor().state().toJson())) {
                // A known outcome can be recovered using existing immutable artifacts; this branch never publishes new bytes.
                Pin knownBody = artifacts().referenceOf(original.bytes(), registration.maximumBodyBytes());
                Pin knownInput = artifacts().referenceOf(request.producerInput(), ContinuityJson.DOCUMENT_MAX_BYTES);
                Request knownRequest = domainEvent(prepared, registration, knownBody, knownInput);
                if (store.duplicate(knownRequest, beforePublish).isPresent())
                    return recoverDuplicate(knownRequest, beforePublish);
            }
            requireSameHead(prepared.predecessor(), beforePublish);
            java.util.Optional<DomainBodies.BodyRef> previousBeforePublish = DomainBodies.reference(beforePublish.state(), request.slot());
            verifyPreviousBody(previousBeforePublish, registration);
            String beforeProof = registration.verifier().verify(beforePublish, previousBeforePublish, request, original.bytes()); requireDigest(beforeProof);
            StrictJson.require(beforeProof.equals(prepared.preconditionDigest()), "actual domain prerequisites changed before immutable publication");
            // Archive publication is immutable payload storage under this same lock, not a second ledger writer.
            Pin durableBody = artifacts().publish(original.bytes(), registration.maximumBodyBytes());
            Pin durableInput = artifacts().publish(request.producerInput(), ContinuityJson.DOCUMENT_MAX_BYTES);
            DomainBodies.BodyRef body = new DomainBodies.BodyRef(request.slot(), registration.contractSchema(), durableBody.reference(), durableBody.identity(), registration.producerSources());
            Request eventRequest = domainEvent(prepared, registration, durableBody, durableInput);
            Head actual = this.head();
            if (store.duplicate(eventRequest, actual).isPresent())
                return recoverDuplicate(eventRequest, actual);
            requireSameHead(prepared.predecessor(), actual);
            TransitionAuthority importAuthority = new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request supplied) throws IOException {
                    StrictJson.require(supplied.identity().equals(eventRequest.identity())
                            && ContinuityJson.same(predecessor.toJson(), prepared.predecessor().state().toJson()), "domain original predecessor/details CAS");
                    for (Pin pin : prepared.sources()) LedgerFiles.verify(pin); for (Pin pin : prepared.evidence()) LedgerFiles.verify(pin);
                    var currentOriginal = LedgerFiles.exact(request.originalBody(), registration.maximumBodyBytes());
                    StrictJson.require(currentOriginal.pin().equals(prepared.originalBody()), "original domain body changed after qualification");
                    java.util.Optional<DomainBodies.BodyRef> previous = DomainBodies.reference(predecessor, request.slot()); verifyPreviousBody(previous, registration);
                    Head actualHead = Session.this.head(); StrictJson.require(ContinuityJson.same(actualHead.state().toJson(), predecessor.toJson()), "same-lock domain source head");
                    String actualProof = registration.verifier().verify(actualHead, previous, request, currentOriginal.bytes()); requireDigest(actualProof);
                    StrictJson.require(actualProof.equals(prepared.preconditionDigest()), "actual original producer/reducer result changed inside writer lock");
                    StrictJson.require(java.util.Arrays.equals(canonical, domainCanonical(artifacts().read(durableBody, registration.maximumBodyBytes()), registration.maximumBodyBytes())), "durable original body readback");
                    return actualProof;
                }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request supplied) {
                    StrictJson.require(supplied.identity().equals(eventRequest.identity()), "exact domain import event");
                    return DomainBodies.reduceImport(predecessor, body);
                }
            };
            return commitInternal(previewInternal(eventRequest, importAuthority), importAuthority);
        }
        private void verifyPreviousBody(java.util.Optional<DomainBodies.BodyRef> previous, DomainBodies.Registration registration) throws IOException {
            if (previous.isEmpty()) return;
            DomainBodies.BodyRef old = previous.orElseThrow();
            StrictJson.require(old.slot() == registration.slot() && old.contractSchema().equals(registration.contractSchema()), "explicit previous domain contract version");
            domainCanonical(artifacts().read(new Pin(old.payload(), old.identity()), registration.maximumBodyBytes()), registration.maximumBodyBytes());
        }
    }
    private static Request domainEvent(DomainBodies.PreparedImport prepared, DomainBodies.Registration registration, Pin durableBody, Pin durableInput) {
        DomainBodies.ImportRequest request = prepared.request();
        DomainBodies.BodyRef body = new DomainBodies.BodyRef(request.slot(), registration.contractSchema(), durableBody.reference(), durableBody.identity(), registration.producerSources());
        ObjectNode details = StrictJson.object(); details.put("evidence_id", "domain-body:" + request.slot().name() + ":" + request.evidenceId());
        details.put("machine_id", prepared.predecessor().state().machineId()); ObjectNode source = details.putObject("source");
        source.set("original_body", request.originalBody().toJson()); source.set("producer_input", durableInput.reference().toJson());
        var producerSources = source.putArray("producer_sources"); registration.producerSources().forEach(ref -> producerSources.add(ref.toJson()));
        var evidenceRefs = source.putArray("evidence"); request.evidence().forEach(ref -> evidenceRefs.add(ref.toJson()));
        details.set("domain_body", body.toJson()); details.put("precondition_digest", prepared.preconditionDigest());
        return new Request(DomainBodies.IMPORT_KIND, ContinuityJson.canonical(details), List.of(durableInput.reference()));
    }
    private static byte[] domainCanonical(byte[] raw, int maximum) {
        return ContinuityJson.canonical(ContinuityJson.parseObject(raw, maximum), maximum);
    }
    /** All named originals share the finite full-material bound; the reference still binds exact bytes and SHA. */
    private static List<Pin> captureDomain(List<ExactRef> references) throws IOException {
        List<Pin> pins = new ArrayList<>();
        for (ExactRef reference : references) pins.add(LedgerFiles.exact(reference, MAX_PIN_BYTES).pin());
        return List.copyOf(pins);
    }
    private static List<Pin> capture(Request request) throws IOException {
        List<Pin> result = new ArrayList<>();
        for (ExactRef reference : request.evidence()) {
            result.add(LedgerFiles.exact(reference, MAX_PIN_BYTES).pin());
        }
        return List.copyOf(result);
    }
    static void requireSameHead(Head expected, Head actual) {
        StrictJson.require(ContinuityJson.same(expected.state().toJson(), actual.state().toJson())
                && expected.documents().equals(actual.documents()) && expected.absent().equals(actual.absent())
                && expected.indexRepairs().equals(actual.indexRepairs())
                && expected.snapshotNeedsRecovery() == actual.snapshotNeedsRecovery(), "real head/source/file-identity CAS drift");
    }
    private static void validateReduction(ContinuityState before, ContinuityState after, Request request) {
        Objects.requireNonNull(after);
        StrictJson.require(before.machineId().equals(after.machineId()) && before.sequence() == after.sequence(), "reducer cannot own sequence/machine");
        if(org.xar.ck3.control.continuity.EpisodeWindow.isTransition(request.kind())) {
            if(!ContinuityJson.same(before.toJson(),after.toJson()))org.xar.ck3.control.continuity.EpisodeWindow.requireReduction(before,after,request,false);
            return; // The exact whole-state reducer already preserves every unrelated/UNKNOWN field.
        }
        if(org.xar.ck3.control.continuity.OriginalLegacyResume.KIND.equals(request.kind())) {
            StrictJson.require(before.status()!=ContinuityState.Status.AWAITING_FIRST_SAVE,
                    "original legacy resume cannot bypass an awaiting first SAVE window");
            if(!ContinuityJson.same(before.toJson(),after.toJson()))
                org.xar.ck3.control.continuity.OriginalLegacyResume.requireReduction(before,after,request,false);
            return; // The shared closed reducer owns only its baseline and explicit original-resume descriptor.
        }
        if(DRIVER_ACTION_HISTORY_KIND.equals(request.kind())) {
            if(!ContinuityJson.same(before.toJson(),after.toJson()))
                requireDriverActionHistoryReduction(before,after,request,false);
            return; // No other canonical field, counter, action record or unrelated pending value may change.
        }
        if(org.xar.ck3.control.continuity.ObservedGameplayEntry.KIND.equals(request.kind())) {
            if(!ContinuityJson.same(before.toJson(),after.toJson()))
                org.xar.ck3.control.continuity.ObservedGameplayEntry.requireReduction(before,after,request,false);
            return;
        }
        if(GAMEPLAY_ENTRY_KIND.equals(request.kind())) {
            if(!ContinuityJson.same(before.toJson(),after.toJson()))
                requireGameplayEntryReduction(before,after,request,false);
            return; // The fixed application authority separately replays actual Entry proof in this same lock.
        }
        StrictJson.require(before.initializedOrigin().equals(after.initializedOrigin()),"only a versioned first SAVE BASELINE may reset original window");
        if(before.status()==ContinuityState.Status.AWAITING_FIRST_SAVE)StrictJson.require(!ORDINARY_CYCLE_KIND.equals(request.kind())
                &&!ORDINARY_BATCH_KIND.equals(request.kind())&&!ORDINARY_NEXT_BASELINE_KIND.equals(request.kind()),
                "ordinary cycle/batch qualification awaits the actual first SAVE BASELINE");
        ObjectNode old = before.toJson(), next = after.toJson();
        preserveField(old,next,DRIVER_ACTION_HISTORY_FIELD);
        preserveField(old,next,org.xar.ck3.control.continuity.OriginalLegacyResume.STATE_FIELD);
        preserveField(old,next,"schema");preserveField(old,next,org.xar.ck3.control.continuity.EpisodeWindow.FIELD);
        preserveField(old,next,org.xar.ck3.control.continuity.FreshContinuityGenesis.FIELD);
        preserveField(old,next,org.xar.ck3.control.continuity.EpisodeWindow.ORIGINAL_OPERATOR_FIELD);
        for (String field : PRESERVED_RUNTIME_FIELDS) {
            StrictJson.require(old.has(field) == next.has(field)
                    && (!old.has(field) || ContinuityJson.same(old.get(field), next.get(field))), "pending/UNKNOWN/NEXT must remain exact: " + field);
        }
        if (DRIVER_READ_HISTORY_KIND.equals(request.kind())) {
            StrictJson.require(next.has(DRIVER_READ_HISTORY_FIELD) && next.get(DRIVER_READ_HISTORY_FIELD).isObject(),
                    "private Driver read publication requires its complete typed history registry");
            java.util.Set<String> fields = new java.util.HashSet<>();
            old.fieldNames().forEachRemaining(fields::add); next.fieldNames().forEachRemaining(fields::add);
            fields.remove(DRIVER_READ_HISTORY_FIELD);
            for (String field : fields) preserveField(old, next, field);
        } else preserveField(old, next, DRIVER_READ_HISTORY_FIELD);
        if (!DomainBodies.IMPORT_KIND.equals(request.kind())) preserveField(old, next, DomainBodies.FIELD);
        if (!ACTION_LIFECYCLE_KIND.equals(request.kind())) preserveField(old, next, ACTION_LIFECYCLE_FIELD);
        if (!GAMEPLAY_ENTRY_KIND.equals(request.kind())) {
            preserveField(old, next, DRIVER_HISTORY_BASELINE_FIELD);
            preserveField(old, next, GAMEPLAY_ENTRY_FIELD);
        }
        if (!ORDINARY_CYCLE_KIND.equals(request.kind())&&!ORDINARY_NEXT_BASELINE_KIND.equals(request.kind())) {
            preserveField(old, next, ORDINARY_CYCLE_FIELD);
            preserveField(old, next, ORDINARY_CYCLE_REBIND_FIELD);
        }
        if (!ORDINARY_BATCH_KIND.equals(request.kind())&&!ORDINARY_NEXT_BASELINE_KIND.equals(request.kind())) {
            preserveField(old, next, ORDINARY_SAVED_CYCLE_FIELD);
        }
        if (!ORDINARY_BATCH_KIND.equals(request.kind())) {
            preserveField(old, next, ORDINARY_BATCH_BOUNDARY_FIELD);
        }
    }
    private static void preserveField(ObjectNode before, ObjectNode after, String field) {
        StrictJson.require(before.has(field) == after.has(field) && (!before.has(field) || ContinuityJson.same(before.get(field), after.get(field))),
                "unrelated reducer cannot clear another canonical writer contract: " + field);
    }
}
