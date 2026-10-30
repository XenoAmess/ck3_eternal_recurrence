package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.capabilities.FactionReadObservation;
import org.xar.ck3.control.application.capabilities.FactionReadReplay;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadCoordinator;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsBoundary;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;

/** Original public faction query through the one installed read coordinator and strict shared producer codec.
 * Family installation is required; this class supplies neither a transport nor a writer session.
 */
public final class FactionAlertReadService {
    public static final String STEP = FactionAlertModel.STEP;
    public static final String CAPABILITY = "game.command.query-player-faction-alerts-v1";
    public static final String PUBLIC_SCHEMA = "xar.faction-alert-public-read/v2";
    private static final BigInteger SAFE = new BigInteger("9007199254740991");
    public record Query(BigInteger expectedRevision) {
        public Query { uint64(expectedRevision, false); }
    }
    /** The active-war source is attached to the same original observation, not an unbound cached list. */
    public record SameFrameWars(ObservationIdentity before, RawJson activeWars) {
        public SameFrameWars {
            Objects.requireNonNull(before); Objects.requireNonNull(activeWars);
            StrictJson.require(parse(activeWars.bytes()).isArray(), "original same-frame active_wars array required");
        }
    }
    public record Context(ObservationIdentity before, G2Source source, String sessionId, Instant deadline,
                          SameFrameWars wars, String snapshotBackendId) {
        public Context {
            Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId);
            Objects.requireNonNull(deadline); Objects.requireNonNull(wars); StrictJson.text(snapshotBackendId);
            StrictJson.require(before.machineId().equals(source.machineId()) && before.equals(wars.before()), "faction source/wars observation drift");
            StrictJson.require(source.exactBuild().equals("1.20.0.4"), "current exact faction source required");
            before.frame().identity().dateRaw().intValueExact();
            NativeCharacterId.of(before.frame().identity().player());
            uint64(before.frame().identity().nativeRevision(), true);
        }
        public BigInteger nativeRevision() { return before.frame().identity().nativeRevision(); }
        public int dateRaw() { return before.frame().identity().dateRaw().intValueExact(); }
        public int player() { return before.frame().identity().player().intValueExact(); }
    }
    public record Selection(Query query, Context context) {
        public Selection {
            Objects.requireNonNull(query); Objects.requireNonNull(context);
            if(!query.expectedRevision().equals(context.before().frame().revision()))
                throw revisionMismatch(query,context.before().frame().revision());
        }
    }
    public enum QueryFailureKind { BRIDGE_UNAVAILABLE, NATIVE_COMMAND_REJECTED }
    /** Source-owned public error DATA only. It grants no retry, read permission, submission or UNKNOWN settlement. */
    public static final class QueryFailure extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final QueryFailureKind kind;
        // Explicit failure DATA encoding retains these Optional evidence fields.
        @SuppressWarnings("serial")
        private final Optional<ExactRef> originalCandidate,preparedCandidate;
        @SuppressWarnings("serial")
        private final Optional<String> actualRequestId;
        private QueryFailure(QueryFailureKind kind,String message,Optional<ExactRef> originalCandidate,
                Optional<ExactRef> preparedCandidate,Optional<String> actualRequestId) {
            super(Objects.requireNonNull(message));StrictJson.require(!message.isEmpty(),"original faction failure message required");
            this.kind=Objects.requireNonNull(kind);this.originalCandidate=Objects.requireNonNull(originalCandidate);
            this.preparedCandidate=Objects.requireNonNull(preparedCandidate);this.actualRequestId=Objects.requireNonNull(actualRequestId);
        }
        public QueryFailureKind kind(){return kind;}
        public Optional<ExactRef> originalCandidate(){return originalCandidate;}
        public Optional<ExactRef> preparedCandidate(){return preparedCandidate;}
        public Optional<String> actualRequestId(){return actualRequestId;}
    }
    /** The original public preflight uses these actual revisions before issuing any Native READ. */
    public static QueryFailure revisionMismatch(Query expected,BigInteger current) {
        Objects.requireNonNull(expected);uint64(current,false);
        return new QueryFailure(QueryFailureKind.BRIDGE_UNAVAILABLE,
                "player faction alert revision mismatch: expected "+expected.expectedRevision()+", current "+current,
                Optional.empty(),Optional.empty(),Optional.empty());
    }
    /** Native integer representation remains untouched here; public serialization has its own decimal64 domain. */
    public record Observation(BigInteger querySequence, FactionAlertModel.Frame frame, RawJson normalizedAlert,
                              RawJson originalResult, String originalResultSha256) implements FactionReadObservation {
        public Observation {
            uint64(querySequence, true); Objects.requireNonNull(frame); Objects.requireNonNull(normalizedAlert);
            Objects.requireNonNull(originalResult); Objects.requireNonNull(originalResultSha256);
            StrictJson.require(digest(originalResult.bytes()).equals(originalResultSha256), "original faction result digest mismatch");
        }
        public boolean exactDemandClockObserved() { return false; }
        public boolean componentStrengthCachesObserved() { return false; }
    }
    public record PublicProjection(BigInteger querySequence, FactionAlertModel.Frame frame, RawJson normalizedAlert,
                                   String originalResultSha256) {
        public PublicProjection {
            uint64(querySequence, true); Objects.requireNonNull(frame); Objects.requireNonNull(normalizedAlert);
            StrictJson.require(originalResultSha256 != null && originalResultSha256.matches("[0-9a-f]{64}"), "original result digest required");
        }
    }
    public static final class Reply {
        private final Selection selection;
        private final PlanningReadResult.Known<Observation> original;
        private Reply(Selection selection, PlanningReadResult.Known<Observation> original) {
            this.selection = Objects.requireNonNull(selection); this.original = Objects.requireNonNull(original);
            StrictJson.require(original.value().equals(decode(selection, original.receipt())), "faction reply differs from original held read");
        }
        public Selection selection() { return selection; }
        public PlanningReadResult.Known<Observation> original() { return original; }
    }
    @FunctionalInterface public interface Current { Context current(); }
    private final Current current;
    private final PlanningReadPort reads;
    private final RootReadContractCatalog catalog;
    private final RootReadContractCatalog.Family<Selection,Observation> family;
    public FactionAlertReadService(Current current, PlanningReadPort reads, RootReadContractCatalog catalog,
            Contracts contracts) {
        this.current = Objects.requireNonNull(current); this.reads = Objects.requireNonNull(reads);
        this.catalog = Objects.requireNonNull(catalog); this.family = Objects.requireNonNull(contracts).family;
    }
    /** A composition root creates this factory, installs families(), and uses the identical instance in the service. */
    public static final class Contracts {
        private final RootReadContractCatalog.Family<Selection,Observation> family;
        public Contracts(ExactRef definitionSource, ExactRef decoderSource) {
            Objects.requireNonNull(definitionSource); Objects.requireNonNull(decoderSource);
            family = new RootReadContractCatalog.Family<>("player-faction-alerts-v1", Selection.class,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.of(CAPABILITY), definitionSource, decoderSource,
                    FactionAlertReadService::key, selected -> new OperationKey(STEP), selected -> new ReadContract<>(
                        contractId(selected), new OperationKey(STEP), Optional.of(CAPABILITY),
                        CAPABILITY, ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definitionSource, (request, requestId) -> {
                            verify(request, selected);
                            return new NativeRequest(STEP, Optional.of(CAPABILITY), new RawJson(StrictJson.canonical(StrictJson.object())));
                        }, receipt -> decode(selected, receipt), receipt -> decode(selected, receipt)));
        }
        public List<RootReadContractCatalog.Family<?,?>> families() { return List.of(family); }
        public ReadContract<Observation> issue(RootReadContractCatalog installed, Selection selected) {
            return Objects.requireNonNull(installed).issue(family, Objects.requireNonNull(selected));
        }
    }
    public Reply query_player_faction_alerts_v1(Query query) {
        Selection selected = new Selection(query, Objects.requireNonNull(current.current()));
        ReadContract<Observation> contract=catalog.issue(family,selected);PlanningReadRequest request=request(selected);
        var actualFailure=new AtomicReference<QueryFailure>();
        var failedResult=new AtomicReference<PlanningReadResult.Unavailable<?>>();
        var result = reads.readWithFailureEvidence(contract,request,(same,identical,actual,unavailable,attempted,originals)->{
            StrictJson.require(identical==contract&&actual==request,"faction failed READ lost its identical issued request/contract");
            Optional<QueryFailure> failure=captureNativeFailure(same,identical,actual,unavailable,attempted,originals);
            if(failure.isPresent()) {
                StrictJson.require(failedResult.compareAndSet(null,unavailable),"faction failed READ callback repeated");
                actualFailure.set(failure.orElseThrow());
            }
        });
        if(actualFailure.get()!=null&&result==failedResult.get()) {
            throw actualFailure.get();
        }
        if (result instanceof PlanningReadResult.Known<Observation> known) return new Reply(selected, known);
        throw new IllegalStateException(((PlanningReadResult.Unavailable<Observation>) result).reason());
    }
    /** Only the coordinator's real single-read callback supplies the private consumed permit and exact archived originals. */
    public static Optional<QueryFailure> captureNativeFailure(Session same,ReadContract<?> identical,
            PlanningReadRequest request,PlanningReadResult.Unavailable<?> unavailable,
            Optional<PlanningReadCoordinator.FailedReadAttempt> attempted,ActionPorts.OutcomeArchive originals)throws IOException {
        Objects.requireNonNull(attempted);Objects.requireNonNull(unavailable);
        StrictJson.require(identical.operation().value().equals(STEP)&&request.operation().value().equals(STEP),
                "faction failure source belongs to another operation");
        if(attempted.isEmpty())return Optional.empty();
        var proof=attempted.orElseThrow();proof.requireOriginal(same,identical,request,unavailable,originals);
        StrictJson.require(proof.prepared().step().equals(STEP)&&proof.before().binding().observed().equals(request.before())
                &&proof.before().binding().source().equals(request.source())&&proof.before().binding().sessionId().equals(request.sessionId())
                &&identical.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                "faction failure crossed its actual source, request or original guard");
        if(proof.original() instanceof NativeActionPort.AckReceived ack&&!ack.nativeOk()) {
            ack.custody().orElseThrow(()->new IOException("faction rejected READ lacks actual request/response custody")).verify(ack,proof.before().binding());
            byte[] packet=ack.originalPacket(),raw=ack.originalFrame().bytes();
            StrictJson.require(packet.length>=5&&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4
                    &&Arrays.equals(Arrays.copyOfRange(packet,4,packet.length),raw),"faction rejected READ lost its original framed bytes");
            ObjectNode frame=object(StrictJson.parse(raw,RawJson.MAXIMUM_BYTES));
            equal(frame.get("type"),"command_result");equal(frame.get("protocol_version"),BigInteger.ONE);
            equal(frame.get("request_id"),proof.requestId());
            StrictJson.require(frame.get("ok")!=null&&frame.get("ok").isBoolean()&&!frame.get("ok").booleanValue(),
                    "faction Native rejection disagrees with its actual original ACK");
            JsonNode nativeError=frame.get("error");String message=nativeError!=null&&nativeError.isTextual()?nativeError.textValue():"unknown error";
            JsonNode typed=frame.get("typed_query_failure_v1");
            if(typed!=null&&typed.isObject())message+="; typed_query_failure_v1="+pythonDiagnostic(typed);
            return Optional.of(new QueryFailure(QueryFailureKind.NATIVE_COMMAND_REJECTED,"native gameplay step failed: "+message,
                    Optional.of(proof.originalRef()),Optional.of(proof.preparedRef()),Optional.of(proof.requestId())));
        }
        if(proof.original() instanceof NativeActionPort.Unknown unknown&&unknown.failureCause().isPresent()) {
            var cause=unknown.failureCause().orElseThrow();
            if(cause.kind()==NativeActionPort.FailureKind.DEADLINE_EXPIRED&&cause.stage()==NativeActionPort.FailureStage.RESPONSE_WAIT
                    &&cause.deadline().isPresent()&&unknown.rawReturn().isEmpty()) {
                var deadline=cause.deadline().orElseThrow();
                StrictJson.require(deadline.suppliedDeadline().equals(request.deadline())
                        &&(deadline.monotonicExpired()||!deadline.observedAt().isBefore(deadline.suppliedDeadline())),
                        "faction timeout lacks its actual original response-wait deadline");
                byte[] packet=unknown.originalRequestPacket();
                StrictJson.require(packet.length>=5&&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4,
                        "faction timeout lost its actual original outbound packet");
                var outbound=object(StrictJson.parse(Arrays.copyOfRange(packet,4,packet.length),RawJson.MAXIMUM_BYTES));
                equal(outbound.get("type"),"execute_step");equal(outbound.get("protocol_version"),BigInteger.ONE);
                equal(outbound.get("request_id"),proof.requestId());equal(outbound.get("step"),STEP);
                equal(outbound.get("expected_revision"),request.before().frame().identity().nativeRevision());
                return Optional.of(new QueryFailure(QueryFailureKind.BRIDGE_UNAVAILABLE,
                        "native command_result timed out for gameplay step "+STEP,
                        Optional.of(proof.originalRef()),Optional.of(proof.preparedRef()),Optional.of(proof.requestId())));
            }
        }
        // A successful ACK containing a business Frame.Unavailable is not a transport error.
        // Unknown without the exact typed response deadline never qualifies by its reason text.
        return Optional.empty();
    }
    /** Native typed diagnostics use the shared exact integer JSON domain; Python's error string also escapes non-ASCII. */
    private static String pythonDiagnostic(JsonNode actual) {
        String canonical=new String(StrictJson.canonical(actual,RawJson.MAXIMUM_BYTES),java.nio.charset.StandardCharsets.UTF_8);
        StringBuilder output=new StringBuilder();String hexadecimal="0123456789abcdef";
        for(int index=0;index<canonical.length();index++) {
            char value=canonical.charAt(index);
            if(value<0x7f)output.append(value);
            else output.append("\\u").append(hexadecimal.charAt(value>>>12)).append(hexadecimal.charAt((value>>>8)&15))
                    .append(hexadecimal.charAt((value>>>4)&15)).append(hexadecimal.charAt(value&15));
        }
        return output.toString();
    }
    /** Ordinary finance reuses this identical installed family instead of creating a second same-operation contract. */
    public PlanningReadResult<PlanningReadReceipt> readOriginal(Query query) {
        Selection selected = new Selection(query, Objects.requireNonNull(current.current()));
        return original(reads.read(catalog.issue(family, selected), request(selected)));
    }
    /** Final-lock callers borrow the sole writer transaction and keep the same original read authority. */
    public PlanningReadResult<PlanningReadReceipt> readOriginal(Session borrowed, Query query) {
        Selection selected = new Selection(query, Objects.requireNonNull(current.current()));
        return original(reads.read(Objects.requireNonNull(borrowed), catalog.issue(family, selected), request(selected)));
    }
    private static PlanningReadResult<PlanningReadReceipt> original(PlanningReadResult<Observation> result) {
        if (result instanceof PlanningReadResult.Known<Observation> known)
            return new PlanningReadResult.Known<>(known.receipt(), known.receipt(), known.originalReceipt());
        var unavailable = (PlanningReadResult.Unavailable<Observation>) result;
        return new PlanningReadResult.Unavailable<>(unavailable.reason(), unavailable.original(),unavailable.decodeFailure());
    }
    public PublicBindings.TypedBinding<Query,Reply> install(PublicBindings bindings, ExactRef serviceSource) {
        return Objects.requireNonNull(bindings).register(PublicMethod.QUERY_PLAYER_FACTION_ALERTS_V1, Query.class, Reply.class,
                this::query_player_faction_alerts_v1, arguments -> {
                    if (!(arguments instanceof PublicBindings.Value value)) throw new IllegalArgumentException("named faction query arguments required");
                    return decodeQuery(value.original());
                }, FactionAlertReadService::encode, new PublicRoutes.Target(FactionAlertReadService.class.getName(),
                    "query_player_faction_alerts_v1", serviceSource), PublicRoutes.Status.IMPLEMENTED,
                "strict original native faction producer; identical Root family installation and runtime acceptance required");
    }
    public static Query decodeQuery(RawJson input) {
        ObjectNode n = object(parse(input.bytes()), Set.of("expected_revision"));
        return new Query(publicInteger(n.get("expected_revision"), false));
    }
    public static RawJson encodeQuery(Query input) {
        return new RawJson(StrictJson.canonical(StrictJson.object().put("expected_revision", input.expectedRevision().toString())));
    }
    public static PlanningReadRequest request(Selection selected) {
        Context c = selected.context();
        return new PlanningReadRequest(c.before(), c.source(), c.sessionId(), new OperationKey(STEP),
                OpportunityJson.object(OpportunityJson.parse(encodeQuery(selected.query()).bytes()), "faction named arguments"), c.deadline());
    }
    private static void verify(PlanningReadRequest request, Selection selected) {
        StrictJson.require(request.equals(request(selected)), "faction contract crossed complete selection or arguments");
    }
    /** Exact selection binding shared by the installed factory and offline original-receipt consumers. */
    public static String contractId(Selection selected) {
        return FactionReadReplay.contractId(evidence(selected),selected.query().expectedRevision());
    }
    /** Offline replay uses wars/backend from the independently verified archived before-frame. */
    public static Observation decodeArchivedOriginal(PlanningReadReceipt receipt,SameFrameWars wars,String snapshotBackendId) {
        Objects.requireNonNull(wars);StrictJson.require(wars.before().equals(Objects.requireNonNull(receipt).request().before()),"faction source/wars observation drift");
        return observation(FactionReadReplay.replayArchived(receipt,wars.activeWars(),snapshotBackendId));
    }
    public static Observation decode(Selection selected,PlanningReadReceipt receipt) {
        return observation(FactionReadReplay.decode(evidence(selected),selected.query().expectedRevision(),receipt));
    }
    /** Exact original frame/token agreement; pure decoding grants no held read guard. */
    public static Observation decodeOriginal(Selection selected,String requestId,RawJson fullOriginal,RawJson resultToken) {
        return observation(FactionReadReplay.decodeOriginal(evidence(selected),selected.query().expectedRevision(),requestId,fullOriginal,resultToken));
    }
    /** Pure original decoder delegates to the same lower implementation as cold replay. */
    public static Observation decodeToken(Selection selected,RawJson raw) {
        return observation(FactionReadReplay.decodeToken(evidence(selected),selected.query().expectedRevision(),raw));
    }
    private static FactionReadReplay.Context evidence(Selection selected) {
        Context c=Objects.requireNonNull(selected).context();
        return new FactionReadReplay.Context(c.before(),c.source(),c.sessionId(),c.deadline(),c.wars().activeWars(),c.snapshotBackendId());
    }
    private static Observation observation(FactionReadObservation value) {
        return new Observation(value.querySequence(),value.frame(),value.normalizedAlert(),value.originalResult(),value.originalResultSha256());
    }
    public static RawJson encode(Reply reply) { return encodePublic(reply.selection(), reply.original().value()); }
    /** Public decimal64 projection. The original numeric packet remains available only in the retained read receipt. */
    public static RawJson encodePublic(Selection selected, Observation observed) {
        Objects.requireNonNull(observed);
        StrictJson.require(observed.equals(decodeToken(Objects.requireNonNull(selected), observed.originalResult())),
                "faction public projection must match the complete validated original observation");
        Context c = selected.context(); ObjectNode n = object(parse(observed.originalResult().bytes()));
        ObjectNode alert = object(parse(observed.normalizedAlert().bytes()));
        alert=object(parse(encodeSemanticBody(new RawJson(StrictJson.canonical(alert)),expected(c)).bytes()));
        n.set("player_faction_alerts", alert); n.put("query_sequence", observed.querySequence().toString());
        n.put("snapshot_revision", c.nativeRevision().toString()).put("queried_snapshot_id", c.before().frame().snapshotId())
                .put("queried_revision", c.before().frame().revision().toString()).put("queried_native_revision", c.nativeRevision().toString())
                .put("public_wire_schema", PUBLIC_SCHEMA).put("original_result_sha256", observed.originalResultSha256())
                .put("schema_version", 1).put("scope", "exact-player-faction-alerts");
        n.set("build", StrictJson.object().put("version", observed.frame().provenance().version()).put("exe_sha256", observed.frame().provenance().sha256()));
        n.set("source", source(c)); n.set("binding", binding(selected));
        return new RawJson(StrictJson.canonical(n, FactionAlertsCodec.MAX_BYTES));
    }
    /** Original EXECUTE driver envelope, with the shared public decimal64 projection and no MCP-only wrapper. */
    public static RawJson encodeExecution(Reply actual) {
        Objects.requireNonNull(actual);
        return encodeExecution(actual.selection(),actual.original().value());
    }
    /** DATA projection only. Revalidates the complete original token, same-frame wars and normalized alert. */
    public static RawJson encodeExecution(Selection selected,Observation observed) {
        Objects.requireNonNull(selected);Objects.requireNonNull(observed);
        StrictJson.require(observed.equals(decodeToken(selected,observed.originalResult())),
                "faction EXECUTE projection must match the complete validated original observation");
        Context c=selected.context();ObjectNode n=object(parse(observed.originalResult().bytes()));
        ObjectNode alert=object(parse(observed.normalizedAlert().bytes()));
        alert=object(parse(encodeSemanticBody(new RawJson(StrictJson.canonical(alert)),expected(c)).bytes()));n.set("player_faction_alerts",alert);
        n.set("status",alert.get("status"));n.set("player_faction_alerts_ready",object(alert.get("readiness")).get("alert_ready"));
        n.put("query_sequence",observed.querySequence().toString()).put("snapshot_revision",c.nativeRevision().toString())
                .put("queried_snapshot_id",c.before().frame().snapshotId())
                .put("queried_revision",c.before().frame().revision().toString())
                .put("queried_native_revision",c.nativeRevision().toString());
        return new RawJson(StrictJson.canonical(n,FactionAlertsCodec.MAX_BYTES));
    }
    /** Public round-trip validation is a projection check and cannot manufacture an original Native read receipt. */
    public static PublicProjection decodePublic(Selection selected, RawJson encoded) {
        Set<String> keys = new java.util.HashSet<>(FactionAlertsBoundary.CURRENT_NATIVE_RESULT_FIELDS);
        Set<String> projectionFields = Set.of("queried_snapshot_id", "queried_revision", "queried_native_revision", "public_wire_schema", "original_result_sha256", "schema_version", "scope", "build", "source", "binding");
        keys.addAll(projectionFields);
        ObjectNode n = object(parse(encoded.bytes()), keys); Context c = selected.context();
        equal(n.get("public_wire_schema"), PUBLIC_SCHEMA); equal(n.get("queried_snapshot_id"), c.before().frame().snapshotId());
        StrictJson.require(decimal(n.get("queried_revision"), false).equals(c.before().frame().revision()), "public faction revision drift");
        StrictJson.require(decimal(n.get("queried_native_revision"), true).equals(c.nativeRevision()), "public faction native revision drift");
        equal(n.get("schema_version"), BigInteger.ONE); equal(n.get("scope"), "exact-player-faction-alerts");
        StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(source(c)), StrictJson.canonical(n.get("source"))) && java.util.Arrays.equals(StrictJson.canonical(binding(selected)), StrictJson.canonical(n.get("binding"))), "public faction source/binding drift");
        ObjectNode build = object(n.get("build"), Set.of("version", "exe_sha256"));
        StrictJson.require(FactionAlertModel.Build.exact(text(build.get("version")), text(build.get("exe_sha256"))) == FactionAlertModel.Build.CK3_12004, "public faction build drift");
        String sha = text(n.get("original_result_sha256"));
        n.remove(projectionFields);
        n.put("query_sequence", decimal(n.get("query_sequence"), true)); n.put("snapshot_revision", decimal(n.get("snapshot_revision"), true));
        ObjectNode alert = object(n.get("player_faction_alerts"));
        n.set("player_faction_alerts",parse(decodeSemanticBody(new RawJson(StrictJson.canonical(alert)),expected(c)).bytes()));
        Observation v = decodeToken(selected, new RawJson(StrictJson.canonical(n, FactionAlertsCodec.MAX_BYTES)));
        return new PublicProjection(v.querySequence(), v.frame(), v.normalizedAlert(), sha);
    }
    /** Body-only DATA uses the same lower shared codec as full Snapshot persistence/public replay. */
    public static RawJson encodeSemanticBody(RawJson originalNumeric,FactionAlertModel.ExpectedFrame expected) {
        return FactionReadReplay.encodeSemanticBody(originalNumeric,expected);
    }
    public static RawJson decodeSemanticBody(RawJson publicBody,FactionAlertModel.ExpectedFrame expected) {
        return FactionReadReplay.decodeSemanticBody(publicBody,expected);
    }
    private static FactionAlertModel.ExpectedFrame expected(Context c) {
        return new FactionAlertModel.ExpectedFrame(c.dateRaw(),c.nativeRevision(),Optional.of(FactionAlertModel.Build.CK3_12004));
    }
    private static RawJson key(Selection selected) {
        return FactionReadReplay.key(evidence(selected),selected.query().expectedRevision());
    }
    private static ObjectNode source(Context c) {
        return StrictJson.object().put("snapshot_id", c.before().frame().snapshotId()).put("revision", c.before().frame().revision().toString())
                .put("native_revision", c.nativeRevision().toString()).put("date_raw", c.dateRaw()).put("paused", true).put("backend_id", c.snapshotBackendId());
    }
    private static ObjectNode binding(Selection selected) {
        Context c = selected.context();
        return StrictJson.object().put("snapshot_id", c.before().frame().snapshotId()).put("revision", c.before().frame().revision().toString())
                .put("native_revision", c.nativeRevision().toString()).put("date_raw", c.dateRaw()).put("expected_revision", selected.query().expectedRevision().toString());
    }
    private static JsonNode parse(byte[] input) { return StrictJson.parse(input, FactionAlertsCodec.MAX_BYTES); }
    private static ObjectNode object(JsonNode n) { StrictJson.require(n instanceof ObjectNode, "faction object required"); return (ObjectNode) n; }
    private static ObjectNode object(JsonNode n, Set<String> fields) {
        ObjectNode object = object(n); Set<String> names = new java.util.HashSet<>(); object.fieldNames().forEachRemaining(names::add);
        StrictJson.require(names.equals(fields), "wrong, missing or extra faction envelope fields"); return object;
    }
    private static String text(JsonNode n) { StrictJson.require(n != null && n.isTextual() && !n.textValue().isEmpty(), "faction text required"); return n.textValue(); }
    private static void equal(JsonNode n, String expected) { StrictJson.require(text(n).equals(expected), "faction text/frame mirror drift"); }
    private static void equal(JsonNode n, BigInteger expected) { StrictJson.require(nativeInteger(n, false).equals(expected), "faction numeric/frame mirror drift"); }
    private static void yes(JsonNode n) { StrictJson.require(n != null && n.isBoolean() && n.booleanValue(), "faction true flag required"); }
    private static BigInteger nativeInteger(JsonNode n, boolean positive) {
        StrictJson.require(n != null && n.isIntegralNumber(), "exact original faction integer required"); return uint64(n.bigIntegerValue(), positive);
    }
    private static BigInteger decimal(JsonNode n, boolean positive) {
        String value = text(n); StrictJson.require(value.matches("0|[1-9][0-9]{0,19}"), "canonical faction decimal64 required");
        return uint64(new BigInteger(value), positive);
    }
    private static BigInteger publicInteger(JsonNode n, boolean positive) {
        if (n != null && n.isTextual()) return decimal(n, positive);
        BigInteger v = nativeInteger(n, positive); StrictJson.require(v.compareTo(SAFE) <= 0, "numeric faction public revision exceeds safe integer range"); return v;
    }
    private static BigInteger uint64(BigInteger v, boolean positive) {
        StrictJson.require(v != null && v.signum() >= (positive ? 1 : 0) && v.bitLength() <= 64, "faction uint64 range"); return v;
    }
    private static String digest(byte[] input) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(input)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("SHA256 unavailable", impossible); }
    }
}
