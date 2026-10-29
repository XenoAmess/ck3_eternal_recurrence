package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Existing public consumers use the one Root writer and actual original finite war read families. */
public final class ArmyWarReadService {
    public record Reply(ArmyWarReads.Selection selection, PlanningReadResult.Known<ArmyWarReadCodec.Observation> original) {
        public Reply {
            Objects.requireNonNull(selection); Objects.requireNonNull(original);
            require(ArmyWarReadCodec.decode(ArmyWarReads.scope(selection, original.receipt().request()), original.receipt()).equals(original.value()), "war reply differs from full original native receipt");
        }
    }
    public record WarStateReply(ArmyRetreatFrames.Current frame, ArmyResponses.WarState value) {
        public WarStateReply {
            Objects.requireNonNull(frame); Objects.requireNonNull(value);
            require(ArmySnapshotCodec.state(OpportunityJson.encode(frame.actual().semantic()), frame.actual().identity().frame().snapshotId(),
                    frame.actual().identity().frame().revision(), frame.context().nativeRevision()).equals(value), "war_state differs from actual original full Driver snapshot");
        }
    }
    @FunctionalInterface public interface CollectionWork<T> {
        T apply(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete current) throws IOException;
    }
    public interface CollectionCurrent {
        <T> T withCurrent(ContinuityStorePort.Session same,java.time.Instant deadline,CollectionWork<T> work) throws IOException;
    }
    private final Optional<CollectionCurrent> collectionCurrent;
    private final ContinuityStorePort writer;
    private final ArmyWarReads reads;
    private final RootReadContractCatalog catalog;
    private final ArmyRetreatFrames frames;
    private final Clock clock;
    private final Duration timeout;
    public ArmyWarReadService(ContinuityStorePort originalWriter, ArmyWarReads actualReads, RootReadContractCatalog exactCatalog,
            ArmyRetreatFrames sameHeldFrames, Clock clock, Duration timeout) {
        this(originalWriter,actualReads,exactCatalog,sameHeldFrames,clock,timeout,Optional.empty());
    }
    /** Actual Root supplies a source-qualified no-I/O complete projection, including unpaused stale states. */
    public ArmyWarReadService(ContinuityStorePort originalWriter, ArmyWarReads actualReads, RootReadContractCatalog exactCatalog,
            ArmyRetreatFrames sameHeldFrames, Clock clock, Duration timeout, CollectionCurrent actualCollectionCurrent) {
        this(originalWriter,actualReads,exactCatalog,sameHeldFrames,clock,timeout,Optional.of(Objects.requireNonNull(actualCollectionCurrent)));
    }
    private ArmyWarReadService(ContinuityStorePort originalWriter, ArmyWarReads actualReads, RootReadContractCatalog exactCatalog,
            ArmyRetreatFrames sameHeldFrames, Clock clock, Duration timeout, Optional<CollectionCurrent> actualCollectionCurrent) {
        collectionCurrent=Objects.requireNonNull(actualCollectionCurrent);
        writer = Objects.requireNonNull(originalWriter); reads = Objects.requireNonNull(actualReads); catalog = Objects.requireNonNull(exactCatalog);
        frames = Objects.requireNonNull(sameHeldFrames); this.clock = Objects.requireNonNull(clock); this.timeout = Objects.requireNonNull(timeout);
        require(!timeout.isNegative() && !timeout.isZero(), "finite positive war read timeout required");
    }
    public Optional<ArmyWarReads.PendingDeclaration> pendingDeclaration() { return reads.pendingDeclaration(); }
    public Optional<ArmyWarReads.DeclarationLease> declarationLease(ArmyRetreatFrames.Current current) { return reads.currentDeclarations(current); }
    public WarStateReply war_state(ArmyCalls.Empty input) {
        Objects.requireNonNull(input);require(input.method()==PublicMethod.WAR_STATE,"war_state method differs");
        try { return writer.locked(same -> warStateHeld(same,input,observe(clock.instant().plus(timeout)))); }
        catch(IOException failure) { throw new UncheckedIOException(failure); }
    }
    public WarStateReply war_state(ContinuityStorePort.Session same,ArmyCalls.Empty input,java.time.Instant deadline) throws IOException {
        writer.requireSession(same);Objects.requireNonNull(input);Objects.requireNonNull(deadline);
        return requireCollectionCurrent().withCurrent(same,deadline,actual -> warStateHeld(same,input,new ArmyRetreatFrames.Current(actual,deadline)));
    }
    private WarStateReply warStateHeld(ContinuityStorePort.Session same,ArmyCalls.Empty input,ArmyRetreatFrames.Current frame) throws IOException {
        writer.requireSession(same);require(input.method()==PublicMethod.WAR_STATE,"war_state method differs");
        input.revision().requireCurrent(frame.context().before().frame().revision());
        return new WarStateReply(frame,ArmySnapshotCodec.state(OpportunityJson.encode(frame.actual().semantic()),frame.actual().identity().frame().snapshotId(),
                frame.actual().identity().frame().revision(),frame.context().nativeRevision()));
    }
    private ArmyRetreatFrames.Current observe(java.time.Instant deadline) {
        try {return frames.current(deadline);}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("original held war observation interrupted",interrupted);}
    }
    private CollectionCurrent requireCollectionCurrent() {
        return collectionCurrent.orElseThrow(() -> new IllegalStateException("actual same-Root no-query current projection is not installed"));
    }
    /** Collects only the original exact UNKNOWN request; no fresh Native command, read or request ID. */
    public ArmyDeclarationCollection.Reply collect_declarable_wars_result_v1(ArmyCalls.Collect input) {
        try { return writer.locked(same -> collect_declarable_wars_result_v1(same,input,clock.instant().plus(timeout))); }
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public ArmyDeclarationCollection.Reply collect_declarable_wars_result_v1(ContinuityStorePort.Session same,ArmyCalls.Collect input,
            java.time.Instant deadline) throws IOException {
        writer.requireSession(same);Objects.requireNonNull(input);Objects.requireNonNull(deadline);
        return requireCollectionCurrent().withCurrent(same,deadline,actual ->
                new ArmyDeclarationCollection.Reply(actual,deadline,reads.collectOriginal(same,input,actual,deadline)));
    }
    public Reply query_declarable_wars(ArmyCalls.Frame input) {
        require(input.method() == PublicMethod.QUERY_DECLARABLE_WARS, "declaration query route differs"); return query(input);
    }
    public Reply query_player_ordinary_holy_war_declaration_context_private_v1(ArmyCalls.Declaration input) {
        require(input.method() == PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1, "ordinary holy-war declaration query route differs"); return query(input);
    }
    public Reply query_war_occupation_targets_v1(ArmyCalls.War input) { return war(input, PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1); }
    public Reply query_war_termination_options(ArmyCalls.War input) { return war(input, PublicMethod.QUERY_WAR_TERMINATION_OPTIONS); }
    public Reply query_outbound_war_white_peace_status(ArmyCalls.War input) { return war(input, PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS); }
    public Reply query_war_termination_terms(ArmyCalls.War input) { return war(input, PublicMethod.QUERY_WAR_TERMINATION_TERMS); }
    public Reply query_prewar_force_coalition_coverage_v1(ArmyCalls.Declaration input) {
        require(input.method() == PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, "partial coalition query route differs"); return query(input);
    }
    public Reply query_prewar_force_coalition_coverage_v2(ArmyCalls.Declaration input) {
        require(input.method() == PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2, "coalition query route differs"); return query(input);
    }
    /** Preserve the original production guard before any read permit, Native write or optional preview construction. */
    public Reply query_war_termination_exit_terms(ArmyCalls.War input) {
        require(input.method() == PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS, "exit-terms route differs");
        throw new IllegalStateException("war-termination exit-terms v2 is disabled after a reproducible native loaded-effect preview crash");
    }
    private Reply war(ArmyCalls.War input, PublicMethod method) { require(input.method() == method, "war query route differs"); return query(input); }
    private Reply query(ArmyCalls.Call input) {
        try { return writer.locked(same -> readHeld(same,input,observe(clock.instant().plus(timeout)))); }
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    /** Actual Root supplies its borrowed Session and retains the held source scope throughout this read. */
    public Reply read(ContinuityStorePort.Session same,ArmyCalls.Call input,java.time.Instant deadline) throws IOException {
        writer.requireSession(same);Objects.requireNonNull(input);Objects.requireNonNull(deadline);
        require(ArmyWarReads.METHODS.contains(input.method()),"no installed ordinary war read for this public method");
        return requireCollectionCurrent().withCurrent(same,deadline,actual -> readHeld(same,input,new ArmyRetreatFrames.Current(actual,deadline)));
    }
    private Reply readHeld(ContinuityStorePort.Session same,ArmyCalls.Call input,ArmyRetreatFrames.Current frame) throws IOException {
        writer.requireSession(same);
        var selection=reads.selection(same,catalog,input,frame);var contract=reads.contract(catalog,selection);
        Duration requested=Duration.between(clock.instant(),frame.context().deadline());
        var result=input.method()==PublicMethod.QUERY_DECLARABLE_WARS ? reads.read(same,contract,selection,requested) : reads.read(same,contract,selection);
        if(result instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> known)return new Reply(selection,known);
        throw new IllegalStateException(((PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation>)result).reason());
    }
    public List<PublicBindings.BoundBinding> install(PublicBindings bindings, ExactRef actualSource) {
        var result = new java.util.ArrayList<PublicBindings.BoundBinding>(List.of(
                bindings.register(PublicMethod.WAR_STATE, ArmyCalls.Empty.class, WarStateReply.class, this::war_state, args -> {
                    if (!(args instanceof PublicBindings.Value value)) throw new IllegalArgumentException("war_state requires original empty named arguments");
                    return (ArmyCalls.Empty) ArmyCallCodec.decode(PublicMethod.WAR_STATE, value.original());
                }, ArmyWarReadService::encodeWarState, new PublicRoutes.Target(ArmyWarReadService.class.getName(), "war_state", actualSource), PublicRoutes.Status.IMPLEMENTED,
                        "actual full held Driver frame -> complete shared war/army codecs -> stable original union -> exact source-bound public fields"),
                register(bindings, PublicMethod.QUERY_DECLARABLE_WARS, ArmyCalls.Frame.class, this::query_declarable_wars, actualSource),
                register(bindings, PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1, ArmyCalls.Declaration.class,
                        this::query_player_ordinary_holy_war_declaration_context_private_v1, actualSource),
                register(bindings, PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1, ArmyCalls.War.class, this::query_war_occupation_targets_v1, actualSource),
                register(bindings, PublicMethod.QUERY_WAR_TERMINATION_OPTIONS, ArmyCalls.War.class, this::query_war_termination_options, actualSource),
                register(bindings, PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, ArmyCalls.War.class, this::query_outbound_war_white_peace_status, actualSource),
                register(bindings, PublicMethod.QUERY_WAR_TERMINATION_TERMS, ArmyCalls.War.class, this::query_war_termination_terms, actualSource),
                register(bindings, PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS, ArmyCalls.War.class, this::query_war_termination_exit_terms, actualSource),
                register(bindings, PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, ArmyCalls.Declaration.class, this::query_prewar_force_coalition_coverage_v1, actualSource),
                register(bindings, PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2, ArmyCalls.Declaration.class, this::query_prewar_force_coalition_coverage_v2, actualSource)));
        if(collectionCurrent.isPresent()) result.add(bindings.register(PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1,ArmyCalls.Collect.class,
                ArmyDeclarationCollection.Reply.class,this::collect_declarable_wars_result_v1,args -> {
                    if(!(args instanceof PublicBindings.Value value))throw new IllegalArgumentException("collection requires exact named request_id and expected_revision");
                    return (ArmyCalls.Collect)ArmyCallCodec.decode(PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1,value.original());
                },ArmyWarReadService::encodeCollection,new PublicRoutes.Target(ArmyWarReadService.class.getName(),"collect_declarable_wars_result_v1",actualSource),
                PublicRoutes.Status.IMPLEMENTED,"sole original UNKNOWN custody, nonblocking original response, central original read adoption and exact public four-state result"));
        return List.copyOf(result);
    }
    private static <Q extends ArmyCalls.Call> PublicBindings.TypedBinding<Q,Reply> register(PublicBindings bindings, PublicMethod method, Class<Q> type, PublicRoutes.Handler<Q,Reply> handler, ExactRef source) {
        return bindings.register(method, type, Reply.class, handler, args -> {
            if (!(args instanceof PublicBindings.Value value)) throw new IllegalArgumentException("war read requires exact named arguments");
            return type.cast(ArmyCallCodec.decode(method, value.original()));
        }, ArmyWarReadService::encode, new PublicRoutes.Target(ArmyWarReadService.class.getName(), method.pythonName(), source), PublicRoutes.Status.IMPLEMENTED,
                "actual single Root read receipt; source-only until installed and checked; loaded-effect preview remains disabled");
    }
    public static RawJson encodeCollection(ArmyDeclarationCollection.Reply reply) {
        return ArmyPublicWire.encodeExactSourceBound(ArmyDeclarationCollectionCodec.encode(reply.result()),reply.context());
    }
    public static RawJson encodeWarState(WarStateReply reply) {
        return ArmyPublicWire.encodeExactSourceBound(reply.value().normalized(), reply.frame().context());
    }
    public static RawJson encode(Reply reply) {
        return ArmyWarPublicResultCodec.encode(ArmyWarReads.scope(reply.selection(),reply.original().receipt().request()),
                reply.original().receipt(),reply.original().value(),reply.selection().declarations().map(lease -> lease.value().querySequence()));
    }
}
