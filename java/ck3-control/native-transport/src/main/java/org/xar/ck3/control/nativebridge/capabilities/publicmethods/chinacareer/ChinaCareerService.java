package org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceNativeReads;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract.*;

/** Six real fixed read producers and original public-service precheck/capability ordering. */
public final class ChinaCareerService {
    @FunctionalInterface public interface ReadPort {
        PlanningReadResult<NativeObservation> read(ReadContract<NativeObservation> actual, PlanningReadRequest request);
    }
    public static final class Registration {
        private final EnumMap<Kind, ReadContract<NativeObservation>> contracts = new EnumMap<>(Kind.class);
        /** Original software DATA constructor. Actual Prepared always supplies its separately selected codec source. */
        public Registration(ExactRef actualServiceSource) { this(actualServiceSource,actualServiceSource); }
        public Registration(ExactRef actualServiceSource,ExactRef actualCodecSource) {
            Objects.requireNonNull(actualServiceSource);Objects.requireNonNull(actualCodecSource);
            List<ExactRef> historySources=List.copyOf(new java.util.LinkedHashSet<>(List.of(actualServiceSource,actualCodecSource)));
            for (Kind kind : Kind.values()) {
                ReadContract<NativeObservation> read = new ReadContract<>("public.china-career." + kind.name().toLowerCase(java.util.Locale.ROOT) + ".v1",
                        new OperationKey(kind.step()), Optional.of(kind.capability()), kind.capability(),
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, actualServiceSource,
                        (request, id) -> prepare(kind, request), receipt -> decode(kind, receipt), receipt -> decode(kind, receipt));
                read=read.withOriginalHistoryProjection(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY,
                        (receipt,replayed)->{
                            RawJson token=receipt.original().originalResultToken().orElseThrow(()->new IllegalArgumentException("original China career history result absent"));
                            RawJson numeric=ChinaCareerCodec.numericExecuteResult(replayed,token);
                            RawJson publicResult=ChinaCareerCodec.publicExecuteResult(replayed,token);
                            return new org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.ExecuteProjection(
                                    receipt.request().operation(),new OperationKey(ChinaCareerCodec.encodedExecuteStep(replayed)),numeric,
                                    org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromResults(numeric,publicResult),historySources);
                        });
                contracts.put(kind, read);
            }
        }
        public ReadContract<NativeObservation> contract(Kind kind) { return Objects.requireNonNull(contracts.get(kind)); }
        public List<ReadContract<NativeObservation>> all() { return Arrays.stream(Kind.values()).map(this::contract).toList(); }
    }
    private final Registration registration;
    public ChinaCareerService(Registration registration) { this.registration = Objects.requireNonNull(registration); }
    public Registration registration() { return registration; }

    /** Runs before ordinary read readiness in the actual physical snapshot DATA scope as well. */
    public static void precheck(Request input, Frame frame) {
        Objects.requireNonNull(input); Objects.requireNonNull(frame);
        precheck(input, frame.paused(), frame.mapReady(), frame.publicRevision());
    }
    public static void precheck(Request input, boolean paused, boolean mapReady, BigInteger publicRevision) {
        Objects.requireNonNull(input); Objects.requireNonNull(publicRevision);
        Kind kind = input.kind();
        boolean simple = kind == Kind.OWNER || kind == Kind.CAREER_HC || kind == Kind.MANAGER_SELECTOR;
        if (simple) {
            if (!paused || !publicRevision.equals(input.expectedRevision())
                    || kind == Kind.MANAGER_SELECTOR && !mapReady) {
                String message = kind == Kind.MANAGER_SELECTOR
                        ? kind.label() + " lacks its paused snapshot binding"
                        : kind.label() + " query lacks one stable paused player binding";
                throw failure(ErrorKind.BRIDGE_UNAVAILABLE, message, Optional.empty());
            }
        } else {
            if (!paused) throw failure(ErrorKind.BRIDGE_UNAVAILABLE,
                    kind.label() + " queries require a paused CK3 snapshot", Optional.empty());
            if (!publicRevision.equals(input.expectedRevision())) throw failure(ErrorKind.BRIDGE_UNAVAILABLE,
                    kind.label() + " revision mismatch: expected " + input.expectedRevision() + ", current " + publicRevision, Optional.empty());
        }
        if (!input.requestNonce().matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")) {
            String message = switch (kind) {
                case OWNER, CAREER_HC -> "request_nonce must be a bounded ASCII token";
                case COLLECTIVE, NORMAL_EXIT -> "request_nonce must be 1-64 ASCII token characters";
                case MANAGER_GOVERNANCE, MANAGER_SELECTOR -> "request_nonce must be a 1-64 byte ASCII token";
            };
            throw failure(ErrorKind.VALUE_ERROR, message, Optional.empty());
        }
    }
    public static void capability(Request input, Frame frame) {
        if (!frame.originalHello().capabilities().contains(input.kind().capability())) {
            String message = switch (input.kind()) {
                case OWNER -> "selected backend does not advertise the ZhongGuo Workforce owner postcondition query";
                case CAREER_HC -> "selected backend does not advertise the ZhongGuo career-HC/workforce postcondition query";
                case COLLECTIVE -> "selected backend cannot query received-self ZhongGuo Workforce collective state";
                case NORMAL_EXIT -> "selected backend cannot query received-self ZhongGuo Workforce normal-exit state";
                case MANAGER_GOVERNANCE -> "selected backend cannot query ZhongGuo manager governance";
                case MANAGER_SELECTOR -> "selected backend cannot query the ZhongGuo manager/subordinate selector";
            };
            throw failure(ErrorKind.UNSUPPORTED_STEP, message, Optional.empty());
        }
    }
    public Response query(Request input, Frame actual, PlanningReadRequest request, ReadPort originalPort) {
        Objects.requireNonNull(originalPort); precheck(input, actual); capability(input, actual);
        var contract = registration.contract(input.kind());
        StrictJson.require(request.operation().equals(contract.operation())
                && request.before().frame().revision().equals(actual.publicRevision())
                && request.before().frame().identity().nativeRevision().equals(actual.nativeRevision())
                && request.arguments().equals(arguments(input, actual)), "public China career query lost actual fixed arguments/frame");
        PlanningReadResult<NativeObservation> result = originalPort.read(contract, request);
        if (!(result instanceof PlanningReadResult.Known<NativeObservation> known)) {
            String reason = result instanceof PlanningReadResult.Unavailable<NativeObservation> missing ? missing.reason() : "unknown read result";
            throw failure(ErrorKind.BRIDGE_UNAVAILABLE, "actual registered " + input.kind().label() + " read unavailable: " + reason, Optional.empty());
        }
        StrictJson.require(known.receipt().request().equals(request)
                && known.receipt().contractId().equals(contract.contractId()), "China career read belongs to another installed contract/request");
        if (input.kind() == Kind.COLLECTIVE || input.kind() == Kind.NORMAL_EXIT || input.kind() == Kind.MANAGER_GOVERNANCE) {
            if (!actual.originalHello().bridgeVersion().equals(CareerJson.BRIDGE)
                    || !actual.originalHello().adapterId().equals(CareerJson.ADAPTER)
                    || !actual.originalHello().gameSha256().equalsIgnoreCase(CareerJson.EXE_SHA256))
                throw failure(ErrorKind.BRIDGE_UNAVAILABLE, input.kind().label()
                        + " build mirror disagrees with bridge hello", Optional.of(known.originalReceipt()));
        }
        return ChinaCareerCodec.response(input, actual, known.value());
    }
    public static OpportunityJson.Obj arguments(Request request, Frame frame) {
        var args = new OpportunityJson.Obj(java.util.Map.of()).with("request_nonce", new OpportunityJson.Text(request.requestNonce()));
        if (request.kind() != Kind.MANAGER_SELECTOR)
            args = args.with("owner_character_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(request.owner(frame))));
        if (request.kind().subjectArgument())
            args = args.with("subject_character_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(request.subject(frame))));
        return args;
    }
    private static NativeRequest prepare(Kind kind, PlanningReadRequest request) {
        parameters(kind, request);
        return new NativeRequest(kind.step(), Optional.of(kind.capability()), new RawJson(OpportunityJson.encode(request.arguments())));
    }
    private record Parameters(String nonce, int owner, int subject) { }
    private static Parameters parameters(Kind kind, PlanningReadRequest request) {
        ObjectNode args = ChinaCareerCodec.object(new RawJson(OpportunityJson.encode(request.arguments())));
        StrictJson.object(args, kind == Kind.MANAGER_SELECTOR ? Set.of("request_nonce") : kind.subjectArgument()
                ? Set.of("request_nonce", "owner_character_id", "subject_character_id") : Set.of("request_nonce", "owner_character_id"));
        StrictJson.require(request.operation().value().equals(kind.step()), "exact China career registered operation required");
        String nonce = CareerJson.nonce(StrictJson.text(args.get("request_nonce")));
        int player = request.before().frame().identity().player().intValueExact();
        int owner = kind == Kind.MANAGER_SELECTOR ? player : (int) StrictJson.integer(args.get("owner_character_id"), 1, Integer.MAX_VALUE);
        int subject = kind.subjectArgument() ? (int) StrictJson.integer(args.get("subject_character_id"), 1, Integer.MAX_VALUE) : player;
        StrictJson.require(kind != Kind.OWNER || owner == player, "Workforce owner must be actual played owner");
        return new Parameters(nonce, owner, subject);
    }
    private static NativeObservation decode(Kind kind, PlanningReadReceipt receipt) {
        GovernanceNativeReads.verifyGuards(receipt);
        var request = receipt.request(); Parameters parameters = parameters(kind, request);
        try {
            var ack = receipt.original(); NativeWire.Frame wire = NativeWire.decode(ack.originalPacket());
            StrictJson.require(wire instanceof NativeWire.CommandResult, "China career original query command result required");
            var nativeResult = (NativeWire.CommandResult) wire;
            StrictJson.require(nativeResult.nativeOk() && ack.nativeOk() && ack.requestId().equals(receipt.requestId())
                    && nativeResult.requestId().equals(receipt.requestId())
                    && Arrays.equals(nativeResult.payload().value(), ack.originalFrame().bytes())
                    && nativeResult.result().presence() == NativeWire.Presence.VALUE
                    && Arrays.equals(nativeResult.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes()),
                    "China career original packet/frame/token correlation changed");
            var outgoing = NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow(
                    () -> new IllegalArgumentException("actual original China career outgoing query absent")).originalPacket());
            StrictJson.require(outgoing.requestId().equals(receipt.requestId()) && outgoing.step().equals(kind.step())
                    && outgoing.expectedRevision().equals(Optional.of(request.before().frame().identity().nativeRevision()))
                    && ChinaCareerCodec.object(new RawJson(outgoing.normalizedAdditionalFields().value())).equals(
                            ChinaCareerCodec.object(new RawJson(OpportunityJson.encode(request.arguments())))),
                    "China career actual outgoing fixed step/fields/native revision changed");
            RawJson original = ack.originalResultToken().orElseThrow();
            ObjectNode envelope = StrictJson.object(ChinaCareerCodec.object(original), Set.of("step", "accepted", "status",
                    "query_sequence", "snapshot_revision", kind.payload(), "backend_id"));
            var identity = request.before().frame().identity();
            StrictJson.trueValue(envelope.get("accepted"));
            StrictJson.require(StrictJson.text(envelope.get("step")).equals(kind.step())
                    && StrictJson.integer(envelope.get("snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX).equals(identity.nativeRevision()),
                    "China career native envelope does not bind requested native frame");
            StrictJson.require(StrictJson.text(envelope.get("backend_id")).equals("native-headless"), "actual China career native backend changed");
            var binding = new CareerJson.FrameBinding(parameters.nonce(), request.before().frame().snapshotId(),
                    request.before().frame().revision(), identity.nativeRevision(), receipt.before().binding().connectionGeneration(),
                    identity.dateRaw().intValueExact(), identity.player().intValueExact(), parameters.subject(), parameters.owner());
            RawJson token = new RawJson(NativeWire.token(original.bytes(), kind.payload()));
            var observation = ChinaCareerCodec.nativeObservation(kind, token, binding,
                    StrictJson.integer(envelope.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX), StrictJson.text(envelope.get("backend_id")));
            String status = observation.domain().header().status() == CareerJson.Availability.AVAILABLE ? "available" : "unavailable";
            StrictJson.require(status.equals(StrictJson.text(envelope.get("status"))), "China career envelope/domain availability differs");
            return observation;
        } catch (IOException error) { throw new UncheckedIOException("original China career native packet malformed", error); }
    }
    public static Failure failure(ErrorKind kind, String message, Optional<ExactRef> original) {
        return new Failure(new Fault(kind, message, original));
    }
}
