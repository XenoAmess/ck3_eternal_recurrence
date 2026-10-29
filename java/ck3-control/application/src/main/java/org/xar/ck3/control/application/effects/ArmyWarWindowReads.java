package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Root injects the actual producer's one contract/encoder; live and archive use the identical decoder. */
public final class ArmyWarWindowReads {
    private ArmyWarWindowReads() { }
    public enum View { DECLARATIONS, FINAL_CB_ROLES, FAMILY, HOLY_ORDER, OVERVIEW, RESULTS }
    public sealed interface Selection permits Declaration, CallAlly, HolyHire, Window {
        Kind kind();
        OperationKey operation();
    }
    public record Declaration(String declarationId) implements Selection {
        public Declaration {
            StrictJson.require(declarationId != null && declarationId.matches("(?:0|[1-9][0-9]*)-(?:0|[1-9][0-9]*)-(?:-1|0|[1-9][0-9]*)"),
                    "canonical original declaration identity required");
        }
        public Kind kind() { return Kind.DECLARE_WAR; }
        public OperationKey operation() { return new OperationKey("declare-war-" + declarationId); }
    }
    public record CallAlly(int warId, int recipientId) implements Selection {
        public CallAlly { StrictJson.require(warId != -1 && recipientId != -1, "complete signed war/recipient identity required"); }
        public Kind kind() { return Kind.SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1; }
        public OperationKey operation() { return new OperationKey("submit-call-ally-to-war-v1-private"); }
    }
    public record HolyHire(long holyOrderId) implements Selection {
        public HolyHire { StrictJson.require(holyOrderId >= 0 && holyOrderId < 0xffff_ffffL, "full uint32 holy-order reference excluding none required"); }
        public Kind kind() { return Kind.HIRE_HOLY_ORDER_V1; }
        public OperationKey operation() { return new OperationKey("hire-holy-order-v1"); }
    }
    public enum WindowKind { OVERVIEW, RESULTS }
    public record Window(WindowKind window) implements Selection {
        public Window { Objects.requireNonNull(window); }
        public Kind kind() { return window == WindowKind.OVERVIEW ? Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1 : Kind.CLOSE_WAR_RESULTS_WINDOW_V1; }
        public OperationKey operation() { return new OperationKey(window == WindowKind.OVERVIEW ? "close-war-declared-overview-v1" : "close-war-results-window-v1"); }
    }
    public record Request(Complete frame, Selection selection, java.time.Instant deadline,
            java.util.Optional<ReconciliationIdentity> reconciliation, List<PlanningReadReceipt> preflightOriginals) {
        public Request {
            Objects.requireNonNull(frame); Objects.requireNonNull(selection); Objects.requireNonNull(deadline);
            Objects.requireNonNull(reconciliation);
            preflightOriginals = List.copyOf(preflightOriginals);
            StrictJson.require(preflightOriginals.size() <= 16 && preflightOriginals.stream()
                    .map(PlanningReadReceipt::requestId).distinct().count() == preflightOriginals.size(),
                    "bounded unique original preflight inventory required");
            reconciliation.ifPresent(identity -> StrictJson.require(identity.factual().equals(frame.identity()) &&
                    identity.source().equals(frame.source()) && identity.sessionId().equals(frame.sessionId()) &&
                    identity.connectionGeneration().equals(frame.connectionGeneration()) &&
                    identity.nativeEvidence().equals(frame.originalEvidence()) && identity.observedAt().equals(frame.observedAt()),
                    "query route reconciliation identity differs from the actual complete frame"));
        }
        public Request(Complete frame, Selection selection, java.time.Instant deadline) {
            this(frame, selection, deadline, java.util.Optional.empty(), List.of());
        }
        public Request(Complete frame, Selection selection, java.time.Instant deadline,
                java.util.Optional<ReconciliationIdentity> reconciliation) {
            this(frame, selection, deadline, reconciliation, List.of());
        }
        public static Request fromReceipt(Complete frame, Selection selection, PlanningReadReceipt receipt) {
            return fromReceipt(frame, selection, receipt, List.of());
        }
        public static Request fromReceipt(Complete frame, Selection selection, PlanningReadReceipt receipt,
                List<PlanningReadReceipt> preflightOriginals) {
            Objects.requireNonNull(receipt);
            java.util.Optional<ReconciliationIdentity> original;
            if (receipt.request().origin() instanceof CommandOrigin.Reconciliation pending)
                original = java.util.Optional.of(pending.identity());
            else {
                StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay,
                        "war/window material has no frontend or terminal query route");
                original = java.util.Optional.empty();
            }
            Request actual = new Request(frame, selection, receipt.request().deadline(), original, preflightOriginals);
            actual.requireReceipt(receipt);
            return actual;
        }
        public PlanningReadRequest planning(OperationKey operation, OpportunityJson.Obj arguments) {
            return reconciliation.isPresent()
                    ? PlanningReadRequest.newReconciliation(reconciliation.orElseThrow(), operation, arguments, deadline)
                    : new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(), operation, arguments, deadline);
        }
        public void requireReceipt(PlanningReadReceipt receipt) {
            Objects.requireNonNull(receipt);
            boolean pending = reconciliation.isPresent();
            StrictJson.require(pending == (receipt.request().origin() instanceof CommandOrigin.Reconciliation),
                    "query route changed its original gameplay/reconciliation phase");
            if (pending) StrictJson.require(receipt.request().origin().requireReconciliation().sameGuardFrame(reconciliation.orElseThrow()),
                    "query route changed its original canonical pending identity");
            else StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay &&
                    receipt.request().before().equals(frame.identity()), "query route changed its original gameplay identity");
            StrictJson.require(receipt.request().source().equals(frame.source()) && receipt.request().sessionId().equals(frame.sessionId()) &&
                    receipt.request().deadline().equals(deadline), "query route crossed its original source/session/deadline");
            String binding = pending ? reconciliation.orElseThrow().bindingSha256() : frame.fullBindingSha256();
            for (PlanningReadGuard guard : List.of(receipt.before(), receipt.after())) {
                boolean sameOrigin = pending
                        ? guard.binding().origin() instanceof CommandOrigin.Reconciliation &&
                                guard.binding().origin().requireReconciliation().sameGuardFrame(reconciliation.orElseThrow()) &&
                                guard.readiness() instanceof PlanningReadGuard.Reconciliation
                        : guard.binding().origin() instanceof CommandOrigin.Gameplay &&
                                guard.binding().observed().equals(frame.identity()) &&
                                guard.readiness() instanceof PlanningReadGuard.Gameplay &&
                                guard.paused() && guard.mapReady() && guard.playerAlive();
                StrictJson.require(sameOrigin && guard.binding().source().equals(frame.source()) &&
                        guard.binding().sessionId().equals(frame.sessionId()) &&
                        guard.binding().connectionGeneration().equals(frame.connectionGeneration()) &&
                        guard.binding().nativeEvidence().equals(frame.originalEvidence()) &&
                        guard.originalBindingSha256().equals(binding),
                        "query route crossed its exact origin/native/Driver/connection binding");
            }
        }
    }
    public record Material(PlanningReadReceipt receipt, RawJson normalized) {
        public Material { Objects.requireNonNull(receipt); Objects.requireNonNull(normalized); }
    }
    /** The actual producer resolves one catalog contract for each original read frame; no secondary registry. */
    public record Query<T>(OperationKey operation, Function<Request, ReadContract<T>> contracts,
            Function<T, RawJson> encode, Function<Request, OpportunityJson.Obj> arguments) {
        public Query {
            Objects.requireNonNull(operation); Objects.requireNonNull(contracts);
            Objects.requireNonNull(encode); Objects.requireNonNull(arguments);
        }
        /** Only genuinely frame-independent producer contracts use this constructor. Scoped routes use the factory constructor. */
        public Query(ReadContract<T> contract, Function<T, RawJson> encode, Function<Request, OpportunityJson.Obj> arguments) {
            this(Objects.requireNonNull(contract).operation(), request -> contract, encode, arguments);
        }
        public ReadContract<T> contract(Request actual) {
            Objects.requireNonNull(actual);
            ReadContract<T> resolved = Objects.requireNonNull(contracts.apply(actual), "actual producer contract required");
            StrictJson.require(resolved.operation().equals(operation) &&
                    resolved.guardMode() == (actual.reconciliation().isPresent() ? ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                            : ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP),
                    "actual query factory changed its registered operation or gameplay/reconciliation phase");
            return resolved;
        }
        private ReadContract<T> originalContract(Request actual, PlanningReadReceipt receipt) {
            actual.requireReceipt(receipt);
            ReadContract<T> resolved = contract(actual);
            StrictJson.require(resolved.contractId().equals(receipt.contractId()) &&
                    operation.equals(receipt.request().operation()) &&
                    Objects.requireNonNull(arguments.apply(actual)).equals(receipt.request().arguments()),
                    "actual query factory crossed original contract identity, operation or arguments");
            return resolved;
        }
        public Material decode(Request actual, PlanningReadReceipt receipt) {
            return new Material(receipt, Objects.requireNonNull(encode.apply(originalContract(actual, receipt).decode(receipt))));
        }
        /** Archive resolution uses the loaded original Complete and original deadline; it never prepares or dispatches. */
        public Material replay(Request actual, PlanningReadReceipt receipt) {
            return new Material(receipt, Objects.requireNonNull(encode.apply(originalContract(actual, receipt).replay(receipt))));
        }
        public PlanningReadResult<T> read(PlanningReadPort reads, Complete frame, Selection selection, java.time.Instant deadline) {
            return read(reads, new Request(frame, selection, deadline));
        }
        public PlanningReadResult<T> read(PlanningReadPort reads, Request actual) {
            Objects.requireNonNull(reads); Objects.requireNonNull(actual);
            ReadContract<T> resolved = contract(actual);
            return reads.read(resolved, actual.planning(operation, Objects.requireNonNull(arguments.apply(actual))));
        }
    }
    /** An action owns only its actual read contracts. Missing routes never acquire a placeholder contract. */
    public static final class Queries {
        private final java.util.Map<View, Query<?>> supplied;
        public Queries(Query<?> declarations, Query<?> finalCbRoles,
                Query<?> family, Query<?> holyOrder, Query<?> overview, Query<?> results) {
            this(java.util.Map.of(View.DECLARATIONS, Objects.requireNonNull(declarations),
                    View.FINAL_CB_ROLES, Objects.requireNonNull(finalCbRoles), View.FAMILY, Objects.requireNonNull(family),
                    View.HOLY_ORDER, Objects.requireNonNull(holyOrder), View.OVERVIEW, Objects.requireNonNull(overview),
                    View.RESULTS, Objects.requireNonNull(results)));
        }
        private Queries(java.util.Map<View, Query<?>> supplied) {
            this.supplied = java.util.Map.copyOf(supplied);
            StrictJson.require(!this.supplied.isEmpty(), "at least one actual action read contract is required");
        }
        public static Queries forDeclaration(Query<?> declarations, Query<?> finalCbRoles) {
            return new Queries(java.util.Map.of(View.DECLARATIONS, Objects.requireNonNull(declarations),
                    View.FINAL_CB_ROLES, Objects.requireNonNull(finalCbRoles)));
        }
        public static Queries forCallAlly(Query<?> family) {
            return new Queries(java.util.Map.of(View.FAMILY, Objects.requireNonNull(family)));
        }
        public static Queries forHolyHire(Query<?> holyOrder) {
            return new Queries(java.util.Map.of(View.HOLY_ORDER, Objects.requireNonNull(holyOrder)));
        }
        public static Queries forWindow(WindowKind kind, Query<?> window) {
            Objects.requireNonNull(kind);
            return new Queries(java.util.Map.of(kind == WindowKind.OVERVIEW ? View.OVERVIEW : View.RESULTS,
                    Objects.requireNonNull(window)));
        }
        public boolean has(View view) { return supplied.containsKey(Objects.requireNonNull(view)); }
        public Query<?> get(View view) {
            Objects.requireNonNull(view);
            StrictJson.require(supplied.containsKey(view), "this action has no installed actual query for " + view);
            return supplied.get(view);
        }
        public Query<?> declarations() { return get(View.DECLARATIONS); }
        public Query<?> finalCbRoles() { return get(View.FINAL_CB_ROLES); }
        public Query<?> family() { return get(View.FAMILY); }
        public Query<?> holyOrder() { return get(View.HOLY_ORDER); }
        public Query<?> overview() { return get(View.OVERVIEW); }
        public Query<?> results() { return get(View.RESULTS); }
        public void require(Selection selection) {
            Objects.requireNonNull(selection);
            List<View> needed = switch (selection) {
                case Declaration ignored -> List.of(View.DECLARATIONS, View.FINAL_CB_ROLES);
                case CallAlly ignored -> List.of(View.FAMILY);
                case HolyHire ignored -> List.of(View.HOLY_ORDER);
                case Window window -> List.of(window.window() == WindowKind.OVERVIEW ? View.OVERVIEW : View.RESULTS);
            };
            needed.forEach(this::get);
        }
    }
    public static Selection selection(ArmyOrdinaryActionArguments arguments, OperationKey actualOperation) {
        var n = StrictJson.parse(arguments.publicArguments().bytes());
        StrictJson.require(n.isObject(), "public call object required");
        Set<String> required;
        Selection selected = switch (arguments.kind()) {
            case DECLARE_WAR -> {
                required = Set.of("declaration_id");
                yield new Declaration(StrictJson.text(n.get("declaration_id")));
            }
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1 -> {
                required = Set.of("war_id", "recipient_character_id", "expected_revision");
                yield new CallAlly(signed(n.get("war_id")), signed(n.get("recipient_character_id")));
            }
            case HIRE_HOLY_ORDER_V1 -> {
                required = Set.of("holy_order_id", "expected_revision");
                BigInteger id = integer(n.get("holy_order_id"));
                yield new HolyHire(id.longValueExact());
            }
            case CLOSE_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_RESULTS_WINDOW_V1 -> {
                required = Set.of("expected_revision");
                yield new Window(arguments.kind() == Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1 ? WindowKind.OVERVIEW : WindowKind.RESULTS);
            }
            default -> throw new IllegalArgumentException("action is outside the sole five war/window effects");
        };
        var keys = new java.util.HashSet<String>(); n.fieldNames().forEachRemaining(keys::add);
        StrictJson.require(keys.containsAll(required) && keys.stream().allMatch(k -> required.contains(k) || k.equals("expected_revision")),
                "wrong, missing or extra selected Army action fields");
        if (n.has("expected_revision") && !n.get("expected_revision").isNull()) revision(n.get("expected_revision"));
        else StrictJson.require(selected instanceof Declaration, "explicit public revision required");
        StrictJson.require(selected.kind() == arguments.kind() && selected.operation().equals(actualOperation), "selected kind/operation differs from the exact issued action");
        return selected;
    }
    static int signed(JsonNode value) {
        BigInteger n = integer(value); StrictJson.require(n.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0 &&
                n.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0 && !n.equals(BigInteger.valueOf(-1)), "full signed32 identity excluding none required");
        return n.intValueExact();
    }
    static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "actual integral JSON token required");
        return value.bigIntegerValue();
    }
    static BigInteger revision(JsonNode value) {
        BigInteger n;
        if (value.isTextual()) {
            String text = value.textValue(); StrictJson.require(text.matches("0|[1-9][0-9]*"), "canonical public revision decimal required");
            n = new BigInteger(text);
        } else {
            n = integer(value); StrictJson.require(n.compareTo(new BigInteger("9007199254740991")) <= 0, "unsafe public numeric revision");
        }
        StrictJson.require(n.signum() >= 0 && n.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 public revision required");
        return n;
    }
}
