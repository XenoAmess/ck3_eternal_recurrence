package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Finite native selector identities. An operation key is the canonical logical registration identity;
 * the native step and selector remain the original wire values. No caller can register a wire alias.
 */
public final class NativeStepDiscriminator {
    public static final String SCHEMA = "xar.java-native-step-identity/v2";
    public static final String LEGACY_SCHEMA = "xar.java-native-step-identity/v1";
    private static final String EXIT_STEP = "normal-exit-map-v1";
    private static final String RITE_STEP = "player-rite-creation-action-v1";
    private static final String RITE_CAPABILITY = "player_rite_creation_action_v1";
    private static final int MAXIMUM_SELECTOR_FIELDS = 1 << 20;
    private NativeStepDiscriminator() { }

    /** The sole operation selector contract shared with the Rite producer and every native consumer. */
    public sealed interface Selector permits RiteCreation, NormalExit, IngameWindow {
        String wire(); String nativeStep(); String capability(); String selectorField();
        ExecutableStepBindings.Kind kind(); OperationKey operationKey();
    }
    public enum IdentityVersion { HISTORICAL_V1, CURRENT_V2 }

    public enum RiteCreation implements Selector {
        PREVIEW("preview", ExecutableStepBindings.Kind.READ),
        OPEN_CREATE_DRAFT("open_create_draft", ExecutableStepBindings.Kind.ACTION),
        OPEN_EDIT_CURRENT_RITE_DRAFT("open_edit_current_rite_draft", ExecutableStepBindings.Kind.ACTION),
        SELECT_CORE_TENET("select_core_tenet", ExecutableStepBindings.Kind.ACTION),
        SELECT_DOCTRINE("select_doctrine", ExecutableStepBindings.Kind.ACTION),
        SET_NAME_FIELD("set_name_field", ExecutableStepBindings.Kind.ACTION),
        PREPARE_CONFIRMATION("prepare_confirmation", ExecutableStepBindings.Kind.ACTION),
        CONFIRM_ONCE("confirm_once", ExecutableStepBindings.Kind.ACTION);

        private final String wire;
        private final ExecutableStepBindings.Kind kind;
        private final OperationKey operation;
        RiteCreation(String wire, ExecutableStepBindings.Kind kind) {
            this.wire = wire; this.kind = kind; operation = new OperationKey(RITE_STEP + ":" + wire);
        }
        public String selectorField() { return "operation"; }
        public String wire() { return wire; }
        public String nativeStep() { return RITE_STEP; }
        public String capability() { return RITE_CAPABILITY; }
        public ExecutableStepBindings.Kind kind() { return kind; }
        public OperationKey operationKey() { return operation; }
        public static RiteCreation parse(String exactWire) {
            Objects.requireNonNull(exactWire);
            for (RiteCreation value : values()) if (value.wire.equals(exactWire)) return value;
            throw new IllegalArgumentException("unknown native Rite operation selector");
        }
    }

    /** Actual normal-exit parser uses the action field, never the Rite operation field. */
    public enum NormalExit implements Selector {
        QUERY_CONTEXT("query_context", ExecutableStepBindings.Kind.READ),
        PREPARE_CONFIRMATION("prepare_confirmation", ExecutableStepBindings.Kind.ACTION),
        CONTINUE_PREPARATION("continue_preparation", ExecutableStepBindings.Kind.ACTION),
        DISABLE_EXIT_AUTOSAVE("disable_exit_autosave", ExecutableStepBindings.Kind.ACTION),
        CONFIRM_DESKTOP("confirm_desktop", ExecutableStepBindings.Kind.ACTION);
        private final String wire; private final ExecutableStepBindings.Kind kind; private final OperationKey operation;
        NormalExit(String wire, ExecutableStepBindings.Kind kind) { this.wire = wire; this.kind = kind; operation = new OperationKey(EXIT_STEP + ":" + wire); }
        public String wire() { return wire; }
        public String nativeStep() { return EXIT_STEP; }
        public String capability() { return EXIT_STEP; }
        public String selectorField() { return "action"; }
        public ExecutableStepBindings.Kind kind() { return kind; }
        public OperationKey operationKey() { return operation; }
        public static NormalExit parse(String exactWire) {
            Objects.requireNonNull(exactWire);
            for (NormalExit value : values()) if (value.wire.equals(exactWire)) return value;
            throw new IllegalArgumentException("unknown native normal-exit action selector");
        }
    }

    /** Actual ingame window parser uses the window kind field, never the Rite operation or NormalExit action field. */
    public enum IngameWindow implements Selector {
        TITLE_APPOINTMENT("title_appointment", ExecutableStepBindings.Kind.READ);
        private final String wire;
        private final ExecutableStepBindings.Kind kind;
        private final OperationKey operation;
        IngameWindow(String wire, ExecutableStepBindings.Kind kind) {
            this.wire = wire; this.kind = kind; operation = new OperationKey("query-ingame-ui-window-v1:" + wire);
        }
        public String selectorField() { return "window_kind"; }
        public String wire() { return wire; }
        public String nativeStep() { return "query-ingame-ui-window-v1"; }
        public String capability() { return "game.command.query-current-title-appointment-v1"; }
        public ExecutableStepBindings.Kind kind() { return kind; }
        public OperationKey operationKey() { return operation; }
        public static IngameWindow parse(String exactWire) {
            Objects.requireNonNull(exactWire);
            for (IngameWindow value : values()) if (value.wire.equals(exactWire)) return value;
            throw new IllegalArgumentException("unknown native ingame window selector");
        }
    }

    /** This typed inventory descriptor derives from the logical identity; inconsistent combinations are invalid. */
    public record WireIdentity(OperationKey operation, String nativeStep, Optional<Selector> selector, IdentityVersion version) {
        public WireIdentity {
            Objects.requireNonNull(operation); Objects.requireNonNull(nativeStep); Objects.requireNonNull(selector);
            Objects.requireNonNull(version);
            Optional<Selector> actual = NativeStepDiscriminator.selector(operation);
            StrictJson.require(version != IdentityVersion.HISTORICAL_V1 || actual.stream().noneMatch(value -> value instanceof NormalExit || value instanceof IngameWindow),
                    "historical v1 native identity cannot recognize the new normal-exit or ingame-window selector families");
            StrictJson.require(version != IdentityVersion.HISTORICAL_V1 || ClaimsIdentity.parse(operation)
                            .map(claims -> claims.titles().size() == 1).orElse(true),
                    "historical v1 native identity cannot recognize a new multi-title claims identity");
            StrictJson.require(selector.equals(actual) && nativeStep.equals(canonicalNativeStep(operation, actual)),
                    "native step inventory changed its canonical logical operation or finite selector");
        }
        public WireIdentity(OperationKey operation, String nativeStep, Optional<? extends Selector> selector) {
            this(operation, nativeStep, selector.isPresent() ? Optional.of(selector.orElseThrow()) : Optional.empty(), IdentityVersion.CURRENT_V2);
        }
    }

    /** Empty means the original plain step identity, never an unrestricted selector route. */
    public static Optional<Selector> selector(OperationKey logicalOperation) {
        Objects.requireNonNull(logicalOperation); String value = logicalOperation.value();
        StrictJson.require(!value.equals(RITE_STEP), "ambiguous Rite fixed step requires its explicit finite selector identity");
        StrictJson.require(!value.equals(EXIT_STEP), "ambiguous normal-exit fixed step requires its explicit finite selector identity");
        if (value.startsWith(EXIT_STEP + ":")) return Optional.of(NormalExit.parse(value.substring(EXIT_STEP.length() + 1)));
        if (value.startsWith("query-ingame-ui-window-v1:")) return Optional.of(IngameWindow.parse(value.substring("query-ingame-ui-window-v1:".length())));
        if (!value.startsWith(RITE_STEP + ":")) return Optional.empty();
        RiteCreation selected = RiteCreation.parse(value.substring(RITE_STEP.length() + 1));
        StrictJson.require(selected.operationKey().equals(logicalOperation), "noncanonical Rite logical operation identity");
        return Optional.of(selected);
    }

    /** Ordered TitleIDs are in the native step, separate from finite additional-field selectors. */
    public record ClaimsIdentity(List<Integer> titles) {
        private static final String PREFIX = "query-player-claims-v1-";
        public ClaimsIdentity {
            titles = List.copyOf(Objects.requireNonNull(titles));
            StrictJson.require(!titles.isEmpty() && titles.size() <= 4096, "bounded nonempty claims titles required");
            StrictJson.require(titles.stream().distinct().count() == titles.size(), "claims titles must be distinct");
            for (int id : titles) StrictJson.require(id >= 0, "nonnegative int32 claims TitleID required");
            StrictJson.require((PREFIX + join(titles, ",")).getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 795,
                    "requested ordered claims list exceeds actual native wire step bound; no truncation");
        }
        private static String join(List<Integer> titles, String delimiter) {
            return titles.stream().map(String::valueOf).collect(java.util.stream.Collectors.joining(delimiter));
        }
        public OperationKey operationKey() { return new OperationKey(PREFIX + join(titles, ":")); }
        public String nativeStep() { return PREFIX + join(titles, ","); }
        /** Unrelated families return empty; malformed claims identities are rejected. */
        public static Optional<ClaimsIdentity> parse(OperationKey logicalOperation) {
            String value = Objects.requireNonNull(logicalOperation).value();
            if (!value.startsWith(PREFIX)) return Optional.empty();
            List<Integer> ids = new ArrayList<>();
            for (String part : value.substring(PREFIX.length()).split(":", -1)) {
                StrictJson.require(part.matches("0|[1-9][0-9]{0,9}"), "canonical decimal claims TitleID required");
                ids.add(Integer.parseInt(part));
            }
            ClaimsIdentity identity = new ClaimsIdentity(ids);
            StrictJson.require(identity.operationKey().equals(logicalOperation), "canonical ordered claims identity required");
            return Optional.of(identity);
        }
        /** Shared typed inverse wire parser for claims native steps. */
        public static Optional<ClaimsIdentity> parseNative(String nativeStep) {
            if (nativeStep == null || !nativeStep.startsWith(PREFIX)) return Optional.empty();
            List<Integer> ids = new ArrayList<>();
            for (String part : nativeStep.substring(PREFIX.length()).split(",", -1)) {
                StrictJson.require(part.matches("0|[1-9][0-9]{0,9}"), "canonical decimal claims TitleID required");
                ids.add(Integer.parseInt(part));
            }
            ClaimsIdentity identity = new ClaimsIdentity(ids);
            StrictJson.require(identity.nativeStep().equals(nativeStep), "canonical ordered claims native step required");
            return Optional.of(identity);
        }
    }

    /** Validate the original wire spelling; registration, source and submission checks remain separate. */
    static void requireNativeStep(String nativeStep) {
        Objects.requireNonNull(nativeStep);
        Optional<ClaimsIdentity> claims = ClaimsIdentity.parseNative(nativeStep);
        if (claims.isEmpty()) new OperationKey(nativeStep);
    }

    private static String canonicalNativeStep(OperationKey operation, Optional<Selector> selector) {
        return selector.map(Selector::nativeStep).orElseGet(() -> ClaimsIdentity.parse(operation)
                .map(ClaimsIdentity::nativeStep).orElse(operation.value()));
    }

    public static WireIdentity identity(OperationKey logicalOperation) {
        Optional<Selector> selector = selector(logicalOperation);
        return new WireIdentity(logicalOperation, canonicalNativeStep(logicalOperation, selector), selector);
    }

    public static void requireRegistration(OperationKey logicalOperation, ExecutableStepBindings.Kind kind,
            Optional<String> requiredCapability) {
        requireKind(logicalOperation, kind); Objects.requireNonNull(requiredCapability);
        selector(logicalOperation).ifPresent(value -> StrictJson.require(requiredCapability.equals(Optional.of(value.capability())),
                "finite native selector crossed its exact READ/ACTION kind or advertised capability"));
        if (ClaimsIdentity.parse(logicalOperation).isPresent()) {
            StrictJson.require(requiredCapability.equals(Optional.of("game.command.query-player-claims-v1-IDS")),
                    "claims identity crossed its exact capability");
        }
    }

    public static void requireKind(OperationKey logicalOperation, ExecutableStepBindings.Kind kind) {
        Objects.requireNonNull(kind);
        ClaimsIdentity.parse(logicalOperation).ifPresent(value -> StrictJson.require(kind == ExecutableStepBindings.Kind.READ,
                "claims identity requires READ registration and dispatch"));
        selector(logicalOperation).ifPresent(value -> StrictJson.require(value.kind() == kind,
                "finite native selector cannot cross READ/ACTION/COMPOSITE registration kinds"));
    }

    /** Validate the actual durable request. This check grants no source, origin, readiness or submission permission. */
    public static void requireRequest(OperationKey logicalOperation, ExecutableStepBindings.Kind kind, NativeRequest request) {
        Objects.requireNonNull(request); requireRegistration(logicalOperation, kind, request.requiredCapability());
        requireWire(logicalOperation, kind, request.step(), request.additionalFields());
    }

    /** Actual outbound inspection has no capability field; its original guard/contract must validate capability separately. */
    public static void requireWire(OperationKey logicalOperation, ExecutableStepBindings.Kind kind,
            String actualNativeStep, RawJson actualAdditionalFields) {
        Objects.requireNonNull(kind); Objects.requireNonNull(actualNativeStep); Objects.requireNonNull(actualAdditionalFields);
        requireKind(logicalOperation, kind);
        WireIdentity expected = identity(logicalOperation);
        StrictJson.require(expected.nativeStep().equals(actualNativeStep), "native request changed its original registered wire step");
        expected.selector().ifPresent(value -> {
            StrictJson.require(value.kind() == kind, "native selector cannot cross READ/ACTION dispatch kinds");
            JsonNode fields = StrictJson.parse(actualAdditionalFields.bytes(), MAXIMUM_SELECTOR_FIELDS);
            StrictJson.require(fields.isObject(), "actual finite native selector fields must be an object");
            StrictJson.require(fields.has(value.selectorField()) && fields.get(value.selectorField()).isTextual()
                            && value.wire().equals(fields.get(value.selectorField()).textValue()),
                    "actual finite native selector field differs from its exact finite selector");
        });
        // Claims identity has no selector field, but must have empty additional fields
        if (ClaimsIdentity.parse(logicalOperation).isPresent()) {
            JsonNode fields = StrictJson.parse(actualAdditionalFields.bytes(), MAXIMUM_SELECTOR_FIELDS);
            StrictJson.require(fields.isObject() && fields.isEmpty(), "claims identity requires empty additional fields");
        }
    }

    /** Boolean-only historical predicates may reject invalid data without weakening the strict validator. */
    public static boolean matchesRequest(OperationKey logicalOperation, ExecutableStepBindings.Kind kind, NativeRequest request) {
        if (logicalOperation == null || kind == null || request == null) return false;
        try { requireRequest(logicalOperation, kind, request); return true; }
        catch (IllegalArgumentException invalid) { return false; }
    }

    public static ObjectNode toJson(WireIdentity identity) {
        Objects.requireNonNull(identity); ObjectNode row = StrictJson.object();
        row.put("schema", identity.version() == IdentityVersion.HISTORICAL_V1 ? LEGACY_SCHEMA : SCHEMA); row.put("operation", identity.operation().value()); row.put("native_step", identity.nativeStep());
        if (identity.selector().isPresent()) row.put("selector", identity.selector().orElseThrow().wire()); else row.putNull("selector");
        return row;
    }

    public static WireIdentity fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "operation", "native_step", "selector"));
        String schema = StrictJson.text(row.get("schema"));
        StrictJson.require(SCHEMA.equals(schema) || LEGACY_SCHEMA.equals(schema), "exact current or historical native step identity schema required");
        JsonNode selector = Objects.requireNonNull(row.get("selector"), "explicit native selector or null required");
        OperationKey logical = new OperationKey(StrictJson.text(row.get("operation")));
        Optional<Selector> actual = selector(logical);
        StrictJson.require(selector.isNull() ? actual.isEmpty() : actual.isPresent()
                && actual.orElseThrow().wire().equals(StrictJson.text(selector)), "native selector changed its closed logical identity");
        return new WireIdentity(logical, StrictJson.text(row.get("native_step")), actual,
                LEGACY_SCHEMA.equals(schema) ? IdentityVersion.HISTORICAL_V1 : IdentityVersion.CURRENT_V2);
    }
}
