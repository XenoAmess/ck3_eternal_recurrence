package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.TransportKind;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
public final class PhysicalActionRegistry {
    public sealed interface Observation permits Completed, Pending { }
    public record Completed(List<ExactRef> evidence) implements Observation {
        public Completed { evidence = List.copyOf(evidence); StrictJson.require(!evidence.isEmpty(), "independent physical completion originals required"); }
    }
    public record Pending(String reason, List<ExactRef> evidence) implements Observation {
        public Pending { StrictJson.text(reason); evidence = List.copyOf(evidence); }
    }
    @FunctionalInterface public interface Queue { void enqueue(ActionCommand command); }
    public record DeferredResult(ActionCommand command,ActionState state) {
        public DeferredResult { Objects.requireNonNull(command);Objects.requireNonNull(state); }
    }
    public interface Producer {
        default boolean automatic(ActionCommand command) { return false; }
        default void beforeNative(ContinuityStorePort.Session same,ActionCommand command,GuardEvidence guard,List<ActionReceipt> history,Queue queue) throws IOException { }
        default org.xar.ck3.control.contracts.presentation.PresentationIntent automaticIntent(ActionCommand command) {
            throw new IllegalStateException("actual automatic intent producer unavailable");
        }
        default void verifyOptional(ContinuityStorePort.Session same,ActionReceipt receipt)throws IOException {
            throw new IOException("actual optional presentation verifier unavailable");
        }
        default void verifyDeferredOwner(ActionCommand command)throws IOException { throw new IOException("actual automatic owner unavailable"); }
        default boolean liveCustody(ContinuityStorePort.Session same, ActionCommand command) throws IOException { return false; }
        default void committed(String actionId) { }
        default void queued(ContinuityStorePort.Session same,ActionCommand command,GuardEvidence guard,PresentationPermit permit) throws IOException {
            throw new IOException("automatic deferred presentation is not installed");
        }
        default List<DeferredResult> collect(ContinuityStorePort.Session same) throws IOException { return List.of(); }
        GuardEvidence guard(WriterContracts.Head actual, ActionCommand command) throws IOException;
        PreparedAction prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) throws IOException;
        PhysicalOutcome post(PhysicalSubmission actualPermit, PreparedAction exact, Instant deadline) throws IOException, InterruptedException;
        Observation observe(ContinuityStorePort.Session same, ActionCommand command, PhysicalActionState original, Instant deadline) throws IOException;
        void verifyArchived(WriterContracts.Head actual, ActionReceipt receipt, ActionPorts.OutcomeArchive originals) throws IOException;
    }
    public record Binding(OperationKey operation, TransportKind transportKind, List<ExactRef> sources, Producer producer) {
        public Binding {
            Objects.requireNonNull(operation); Objects.requireNonNull(transportKind); sources = List.copyOf(sources); Objects.requireNonNull(producer);
            StrictJson.require(transportKind != TransportKind.NATIVE_PIPE && !sources.isEmpty()
                    && sources.stream().distinct().count() == sources.size(), "actual finite non-pipe producer closure required");
        }
    }
    private final Map<OperationKey, Binding> bindings;
    private volatile ActionCoordinator originalCoordinator;
    void bindCoordinator(ActionCoordinator actual) { originalCoordinator=Objects.requireNonNull(actual); }
    public ActionReceipt deferAutomatic(ContinuityStorePort.Session same,ActionCommand command) {
        var actual=originalCoordinator;if(actual==null)throw new IllegalStateException("original coordinator unavailable");
        return actual.deferAutomatic(same,command);
    }
    public ActionReceipt observeAutomatic(ContinuityStorePort.Session same,String actionId) {
        var actual=originalCoordinator;if(actual==null)throw new IllegalStateException("original coordinator unavailable");return actual.reconcile(same,actionId);
    }
    public void collectAutomatic(ContinuityStorePort.Session same) {
        var actual=originalCoordinator;if(actual==null)throw new IllegalStateException("original coordinator unavailable");actual.collectAutomatic(same);
    }

    public PhysicalActionRegistry(List<Binding> actualInstalled) {
        var index = new java.util.LinkedHashMap<OperationKey, Binding>();
        for (Binding binding : List.copyOf(actualInstalled))
            StrictJson.require(index.putIfAbsent(binding.operation(), binding) == null, "two physical producers claim the same operation");
        StrictJson.require(!index.isEmpty() && index.size() <= 32, "bounded actual physical products required"); bindings = Map.copyOf(index);
    }
    public Optional<Binding> find(OperationKey operation) { return Optional.ofNullable(bindings.get(operation)); }
    private boolean optionalPresentation(ActionReceipt receipt) {
        var found=find(receipt.command().operation());
        return found.isPresent()&&found.orElseThrow().transportKind()==TransportKind.PRESENTATION_MMAP
                &&found.orElseThrow().producer().automatic(receipt.command());
    }
    public static final class VerifiedPresentations {
        private final java.util.Set<ActionReceipt> receipts;private final ContinuityStorePort.Session same;private final String head;
        private VerifiedPresentations(List<ActionReceipt> actual,ContinuityStorePort.Session same,String head){receipts=java.util.Set.copyOf(actual);this.same=same;this.head=head;}
        public boolean contains(ActionReceipt exact){if(!receipts.contains(exact))return false;try{StrictJson.require(head.equals(same.head().digest()),"presentation proof left its original writer head");return receipts.contains(exact);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}}
    }
    public VerifiedPresentations verified(ContinuityStorePort.Session same,ActionJournal.Snapshot snapshot)throws IOException {
        if(snapshot.actions().stream().noneMatch(this::optionalPresentation))return new VerifiedPresentations(List.of(),same,snapshot.headSha256());
        StrictJson.require(snapshot.headSha256().equals(same.head().digest())&&snapshot.ledgerSequence()==same.head().state().sequence(),"presentation proof requires actual canonical writer head");
        var result=new java.util.ArrayList<ActionReceipt>();
        for(var receipt:snapshot.actions())if(optionalPresentation(receipt)){
            require(receipt.command()).producer().verifyOptional(same,receipt);result.add(receipt);
        }
        return new VerifiedPresentations(result,same,snapshot.headSha256());
    }
    public List<Binding> installed() { return List.copyOf(bindings.values()); }
    public Binding require(ActionCommand command) {
        var actual = find(command.operation()).orElseThrow(() -> new IllegalStateException("physical producer is not installed"));
        StrictJson.require(command.protocolIdentity() instanceof ProtocolRequestIdentity.BodyDerived, "physical planes have their own body-derived original request identity");
        StrictJson.require(actual.transportKind() == TransportKind.PRESENTATION_MMAP ? command.origin() instanceof CommandOrigin.Gameplay
                : command.origin() instanceof CommandOrigin.Frontend, "physical request crossed its actual gameplay/frontend source");
        return actual;
    }
}
