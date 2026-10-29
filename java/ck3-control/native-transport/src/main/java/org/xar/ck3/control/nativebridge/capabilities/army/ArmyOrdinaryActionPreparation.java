package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.ExecutionProfile;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPreflight.Role;

/** Ordinary native producers run under the coordinator's original writer, after complete current-frame revalidation. */
public final class ArmyOrdinaryActionPreparation implements ActionPorts.PreparationPort {
    @FunctionalInterface public interface WhitePeacePolicy {
        /** The migrated original policy must re-evaluate the full current CB/terms/force policy, not just native available. */
        void verify(Complete current, BigInteger warId, List<ArmyOrdinaryPreflight.Read> originals);
        default void verify(ContinuityStorePort.Session same, Complete current, BigInteger warId, List<ArmyOrdinaryPreflight.Read> originals) {
            Objects.requireNonNull(same); verify(current, warId, originals);
        }
    }
    @FunctionalInterface public interface OccupationProjection {
        /** Project only the existing complete occupation decoder's normalized output. */
        List<ArmyAssaultSelection.Holding> holdings(Complete actualFrame, PlanningReadReceipt original, ActionPorts.OutcomeArchive sameArchive);
    }
    @FunctionalInterface public interface FinalGates {
        /** The identical installed family decoder replays full native terms before dispatch. It may only read. */
        void verify(Complete actualFrame, ArmyOrdinaryActionArguments arguments, NativeRequest selectedPrimitive);
        default void verify(ContinuityStorePort.Session same, Complete actualFrame, ArmyOrdinaryActionArguments arguments, NativeRequest selectedPrimitive) {
            Objects.requireNonNull(same); verify(actualFrame, arguments, selectedPrimitive);
        }
    }
    public record Qualified(ArmyCalls.Call call, ArmyTypes.Context context, Complete actual,
            List<ArmyOrdinaryPreflight.Read> reads, ArmyOrdinaryActionArguments arguments, NativeRequest request, Claims claims) {
        public Qualified { Objects.requireNonNull(call); Objects.requireNonNull(context); Objects.requireNonNull(actual);
            reads = List.copyOf(reads); Objects.requireNonNull(arguments); Objects.requireNonNull(request); Objects.requireNonNull(claims); }
    }
    private final ContinuityWriter writer;
    private final java.util.function.Supplier<HeldDriverObservationPort> driver;
    private final PlanningReadPort reads;
    private final ActionPorts.OutcomeArchive archive;
    private final ArmyOrdinaryPreflight.Queries queries;
    private final WhitePeacePolicy whitePeace;
    private final OccupationProjection occupation;
    private final FinalGates finalGates;
    public ArmyOrdinaryActionPreparation(ContinuityWriter originalWriter, java.util.function.Supplier<HeldDriverObservationPort> actualDriver,
            PlanningReadPort soleReads, ActionPorts.OutcomeArchive sameArchive, ArmyOrdinaryPreflight.Queries actualQueries,
            WhitePeacePolicy originalWhitePeacePolicy, OccupationProjection actualOccupationProjection, FinalGates identicalFamilyGates) {
        writer = Objects.requireNonNull(originalWriter); driver = Objects.requireNonNull(actualDriver); reads = Objects.requireNonNull(soleReads);
        archive = Objects.requireNonNull(sameArchive); queries = Objects.requireNonNull(actualQueries); whitePeace = Objects.requireNonNull(originalWhitePeacePolicy);
        occupation = Objects.requireNonNull(actualOccupationProjection);
        finalGates = Objects.requireNonNull(identicalFamilyGates);
    }
    public Qualified qualify(ContinuityStorePort.Session same, ArmyCalls.Call call, ArmyTypes.Context context) {
        return qualifyProfile(same, call, context, ExecutionProfile.SDK_ORDINARY);
    }
    public Qualified qualifyGenericAutomaticSurrender(ContinuityStorePort.Session same, ArmyCalls.War call, ArmyTypes.Context context) {
        StrictJson.require(call.method() == PublicMethod.SURRENDER_WAR, "generic automatic route requires the exact surrender Call");
        return qualifyProfile(same, call, context, ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER);
    }
    public Qualified qualifyDirectFixedWindow(ContinuityStorePort.Session same, ArmyCalls.Frame call, ArmyTypes.Context context) {
        requireDirectWindow(call); return qualifyProfile(same, call, context, ExecutionProfile.DIRECT_FIXED_WINDOW);
    }
    private Qualified qualifyProfile(ContinuityStorePort.Session same, ArmyCalls.Call call, ArmyTypes.Context context, ExecutionProfile profile) {
        requireSession(same); Kind kind = kind(call); Complete before = profile == ExecutionProfile.DIRECT_FIXED_WINDOW
                ? currentDirectFixedWindow((ArmyCalls.Frame) call, context) : current(context); var bound = archive.withSession(same);
        List<ArmyOrdinaryPreflight.Read> observed = profile == ExecutionProfile.DIRECT_FIXED_WINDOW ? List.of()
                : ArmyOrdinaryPreflight.observe(same, call, context, before, queries, reads, bound);
        Complete afterQueries = profile == ExecutionProfile.DIRECT_FIXED_WINDOW
                ? currentDirectFixedWindow((ArmyCalls.Frame) call, context) : current(context);
        StrictJson.require(before.originalEvidence().equals(afterQueries.originalEvidence()) && before.fullBindingSha256().equals(afterQueries.fullBindingSha256()),
                "Army preflight changed its complete source frame");
        Optional<OrdinaryAutomaticSurrenderPolicy.Variant> variant = profile == ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER
                ? Optional.of(automaticEvidence(before, ((ArmyCalls.War) call).warId(), observed, bound).variant()) : Optional.empty();
        var args = new ArmyOrdinaryActionArguments(kind, ArmyCallCodec.encode(call), observed.stream().map(ArmyOrdinaryPreflight.Read::reference).toList(), profile, variant);
        NativeRequest request = validateProfile(same, call, context, before, observed, bound, args); requireSession(same);
        finalGates.verify(same, before, args, request); requireSession(same);
        return new Qualified(call, context, before, observed, args, request, claims(call, context, before));
    }
    @Override public NativeRequest prepare(ActionCommand command) { throw new IllegalStateException("Army action preparation requires the original writer Session"); }
    @Override public NativeRequest prepare(ActionCommand command, String requestId) { throw new IllegalStateException("Army action preparation requires the original writer Session"); }
    @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) {
        requireSession(same); StrictJson.text(requestId);
        var args = ArmyOrdinaryActionArguments.decode(command.arguments());
        ArmyCalls.Call call = ArmyCallCodec.decode(PublicMethod.valueOf(args.kind().name()), args.publicArguments());
        var context = new ArmyTypes.Context(command.before(), command.source(), command.sessionId(), command.deadline());
        Complete actual = args.executionProfile() == ExecutionProfile.DIRECT_FIXED_WINDOW
                ? currentDirectFixedWindow((ArmyCalls.Frame) call, context) : current(context); var bound = archive.withSession(same);
        var originals = args.executionProfile() == ExecutionProfile.DIRECT_FIXED_WINDOW ? List.<ArmyOrdinaryPreflight.Read>of()
                : ArmyOrdinaryPreflight.replay(call, context, actual, args.preflightReads(), queries, bound);
        NativeRequest request = validateProfile(same, call, context, actual, originals, bound, args);
        finalGates.verify(same, actual, args, request);
        StrictJson.require(kind(call) == args.kind() && command.operation().value().equals(request.step())
                && command.claims().equals(claims(call, context, actual)), "Army command changed its typed selection, primitive or actual resource claims");
        requireSession(same); return request;
    }
    /** Same held observation/source validation, with the original direct before-parser preceding stale comparison. */
    public Complete currentDirectFixedWindow(ArmyCalls.Frame input, ArmyTypes.Context context) {
        requireDirectWindowExpected(input);
        try {
            Complete actual = Objects.requireNonNull(driver.get(), "current held Driver has not been adopted").observe(context.deadline());
            ObjectNode frame = ArmyJson.object(org.xar.ck3.control.application.driver.DriverJson.toNode(actual.semantic()));
            requireDirectWindowBefore(input.method(), frame);
            StrictJson.require(actual.identity().equals(context.before()) && actual.source().equals(context.source())
                    && actual.sessionId().equals(context.sessionId()), "Army public request is stale or belongs to another physical/source session");
            requireDirectWindowSource(input, context, frame);
            return actual;
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); throw new IllegalStateException("Army current observation interrupted; no action was prepared", interrupted);
        }
    }
    public Complete current(ArmyTypes.Context context) {
        try {
            Complete actual = Objects.requireNonNull(driver.get(), "current held Driver has not been adopted").observe(context.deadline());
            StrictJson.require(actual.identity().equals(context.before()) && actual.source().equals(context.source())
                    && actual.sessionId().equals(context.sessionId()), "Army public request is stale or belongs to another physical/source session");
            ObjectNode frame = ArmyJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(actual.semantic()));
            requireTrue(frame.get("paused"), "Army action requires pause"); requireTrue(frame.get("map_ready"), "Army action requires a ready map");
            ObjectNode player = ArmyJson.object(frame.get("played_character")); requireTrue(player.get("alive"), "Army action requires a living played character");
            StrictJson.require(integer(player.get("character_id")).equals(context.playerId())
                    && integer(frame.get("native_revision")).equals(context.nativeRevision()) && integer(frame.get("date_raw")).equals(context.dateRaw()),
                    "Army semantic player/native revision/date differs from its actual identity");
            return actual;
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); throw new IllegalStateException("Army current observation interrupted; no action was prepared", interrupted);
        }
    }
    private void requireSession(ContinuityStorePort.Session same) {
        try { writer.requireSession(same); } catch (IOException failure) { throw new UncheckedIOException("Army action borrowed another writer/lock", failure); }
    }
    public static Kind kind(ArmyCalls.Call call) {
        Objects.requireNonNull(call);
        try { return Kind.valueOf(call.method().name()); }
        catch (IllegalArgumentException outside) { throw new IllegalArgumentException("this Army handler accepts only the seventeen ordinary action methods", outside); }
    }
    public static NativeRequest primitive(ArmyCalls.Call call, ArmyTypes.Context context, List<Long> allyCosts) {
        kind(call); call.revision().requireCurrent(context.before().frame().revision());
        String step; String capability; ObjectNode extra = ArmyJson.empty();
        switch (call) {
            case ArmyCalls.Frame c -> {
                step = switch (c.method()) {
                    case RAISE_TROOPS_DEFAULT -> "raise-troops-default";
                    case CLOSE_WAR_DECLARED_OVERVIEW_V1 -> "close-war-declared-overview-v1";
                    case CLOSE_WAR_RESULTS_WINDOW_V1 -> "close-war-results-window-v1";
                    default -> throw new IllegalArgumentException("read-only Frame cannot become an Army action"); };
                capability = "game.command." + step;
            }
            case ArmyCalls.Move c -> { step = "move-army-" + c.army().value() + "-to-" + c.target().value(); capability = "game.command.move-army-N-to-N"; }
            case ArmyCalls.Unit c -> { step = "disband-army-" + c.army().value(); capability = "game.command.disband-army-N"; }
            case ArmyCalls.Siege c -> { String prefix = c.method() == PublicMethod.START_ASSAULT ? "start-assault-" : "stop-assault-"; step = prefix + c.siege().value(); capability = "game.command." + prefix + "N"; }
            case ArmyCalls.War c -> { String prefix = switch (c.method()) {
                case ENFORCE_DEMANDS -> "enforce-demands-"; case SURRENDER_WAR -> "surrender-war-"; case OFFER_WHITE_PEACE -> "offer-white-peace-";
                default -> throw new IllegalArgumentException("read-only War cannot become an Army action"); };
                step = prefix + c.warId(); capability = "game.command." + prefix + "N"; }
            case ArmyCalls.Declaration c -> { step = "declare-war-" + c.declarationId(); capability = "game.command.declare-war-N"; }
            case ArmyCalls.CallAlly c -> {
                step = "submit-call-ally-to-war-v1-private"; capability = null;
                StrictJson.require(allyCosts != null && allyCosts.size() == 10, "call ally requires its ten current native cost slots");
                extra.put("war_id", c.war().value()).put("recipient_character_id", c.recipient().value());
                var costs = extra.putArray("expected_send_cost_raw"); allyCosts.forEach(costs::add);
            }
            case ArmyCalls.CreateMaa c -> { step = "maa-regular-personal-create-private-v1"; capability = null;
                extra.put("expected_snapshot_revision", context.nativeRevision()).put("expected_public_revision", context.before().frame().revision())
                        .put("expected_date_raw", context.dateRaw()).put("expected_player_character_id", context.playerId())
                        .put("type_index", c.typeIndex()).put("action_id", c.actionId()); }
            case ArmyCalls.Hire c -> { StrictJson.require(c.method() == PublicMethod.HIRE_HOLY_ORDER_V1,
                    "mercenary hire must use its existing complete finance producer");
                step = "hire-holy-order-v1"; capability = "game.command." + step; extra.put("holy_order_id", c.id().value()); }
            case ArmyCalls.AssignCommander ignored -> throw new IllegalArgumentException("commander assignment must use the existing CommanderBindings family");
            case ArmyCalls.Sampling c -> { step = (c.enabled() ? "enable-" : "disable-") + "army-gathering-research-sampling-v1"; capability = "game.command.query-army-strengths-v1"; }
            default -> throw new IllegalArgumentException("Army read/composite cannot become an ordinary native action");
        }
        return new NativeRequest(step, Optional.ofNullable(capability), new RawJson(ArmyJson.bytes(extra)));
    }
    private NativeRequest validateProfile(ContinuityStorePort.Session same, ArmyCalls.Call call, ArmyTypes.Context context,
            Complete actual, List<ArmyOrdinaryPreflight.Read> originals, ActionPorts.OutcomeArchive bound,
            ArmyOrdinaryActionArguments arguments) {
        if (arguments.executionProfile() == ExecutionProfile.DIRECT_FIXED_WINDOW) {
            requireDirectWindow(call); StrictJson.require(originals.isEmpty() && arguments.preflightReads().isEmpty(), "direct window close must retain its no-query producer");
            requireDirectWindowSource((ArmyCalls.Frame) call, context,
                    ArmyJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(actual.semantic())));
            return primitive(call, context, List.of());
        }
        call.revision().requireCurrent(context.before().frame().revision());
        if (arguments.executionProfile() == ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER) {
            StrictJson.require(call instanceof ArmyCalls.War && call.method() == PublicMethod.SURRENDER_WAR, "automatic profile changed its exact Call");
            var war = (ArmyCalls.War) call;
            var ready = automaticEvidence(actual, war.warId(), originals, bound);
            StrictJson.require(arguments.automaticSurrender().orElseThrow() == ready.variant(), "automatic surrender variant changed since command preparation");
            requireNoAutomaticHistory(actual, war.warId().intValueExact());
            try {
                ArmyOrdinaryActionService.rejectReplay(ContinuityActionJournal.receipts(same.head().state(), bound), call, context);
            } catch (IOException unavailable) { throw new UncheckedIOException("same-writer original surrender history unavailable", unavailable); }
            return primitive(call, context, List.of());
        }
        return validate(same, call, context, actual, originals, bound);
    }
    private static void requireDirectWindow(ArmyCalls.Call call) {
        StrictJson.require(call instanceof ArmyCalls.Frame && (call.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1
                || call.method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1), "direct fixed-window profile cannot prepare another action");
    }
    /** Pure original parser only: actual held frame DATA cannot issue a command or a dispatch permission. */
    public static void requireDirectFixedWindowBefore(PublicMethod method, Complete actual) {
        Objects.requireNonNull(actual);
        requireDirectWindowBefore(method, ArmyJson.object(org.xar.ck3.control.application.driver.DriverJson.toNode(actual.semantic())));
    }
    static void requireDirectWindowBefore(PublicMethod method, ObjectNode frame) {
        directWindowName(method); Objects.requireNonNull(frame);
        JsonNode actor = frame.get("played_character"), diagnostics = frame.get("diagnostics");
        JsonNode hello = diagnostics != null && diagnostics.isObject() ? diagnostics.get("hello") : null;
        StrictJson.require(frame.path("paused").isBoolean() && frame.path("paused").booleanValue()
                && frame.path("map_ready").isBoolean() && frame.path("map_ready").booleanValue()
                && actor != null && actor.isObject() && actor.path("alive").isBoolean() && actor.path("alive").booleanValue()
                && hello != null && hello.isObject(), "prewar query requires a living paused native map");
        JsonNode version = hello.get("expected_ck3_version"), sha = hello.get("expected_ck3_sha256");
        StrictJson.require(exactFrozenWindowBuild(version, sha), "native source does not match a frozen exact build");
        StrictJson.require(version.textValue().equals("1.20.0.4"), "prewar query requires the frozen exact .4 build");
        JsonNode snapshot = frame.get("snapshot_id"), episode = frame.get("episode_run_id");
        StrictJson.require(snapshot != null && snapshot.isTextual() && !snapshot.textValue().isEmpty(), "prewar query lacks a native snapshot identity");
        StrictJson.require(episode == null || episode.isNull() || episode.isTextual() && !episode.textValue().isEmpty(), "prewar query episode lease is malformed");
        BigInteger max = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
        originalWindowInteger(frame.get("revision"), "public revision", BigInteger.ONE, max);
        originalWindowInteger(frame.get("native_revision"), "native revision", BigInteger.ONE, max);
        originalWindowInteger(frame.get("date_raw"), "date", BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE));
        originalWindowInteger(actor.get("character_id"), "actor", BigInteger.ONE, BigInteger.valueOf(Integer.MAX_VALUE));
        originalWindowInteger(diagnostics.get("connection_generation"), "connection generation", BigInteger.ZERO, max);
        JsonNode generation = hello.get("connection_generation");
        StrictJson.require(generation != null && generation.isIntegralNumber() && generation.bigIntegerValue().signum() > 0
                && generation.bigIntegerValue().bitLength() <= 64, directWindowName(method) + " hello.connection_generation is outside its native integer range");
    }
    private static void originalWindowInteger(JsonNode value, String name, BigInteger low, BigInteger high) {
        StrictJson.require(value != null && value.isIntegralNumber() && value.bigIntegerValue().compareTo(low) >= 0
                && value.bigIntegerValue().compareTo(high) <= 0, "prewar transport " + name + " is outside [" + low + ", " + high + "]");
    }
    private static boolean exactFrozenWindowBuild(JsonNode version, JsonNode sha) {
        if (version == null || !version.isTextual() || sha == null || !sha.isTextual()) return false;
        String expected = switch (version.textValue()) {
            case "1.19.0.6" -> "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
            case "1.20.0.2" -> "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
            case "1.20.0.3" -> "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
            case "1.20.0.4" -> "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
            default -> "";
        };
        return !expected.isEmpty() && expected.equalsIgnoreCase(sha.textValue());
    }
    private static String directWindowName(PublicMethod method) {
        return switch (Objects.requireNonNull(method)) {
            case CLOSE_WAR_DECLARED_OVERVIEW_V1 -> "war overview";
            case CLOSE_WAR_RESULTS_WINDOW_V1 -> "war results";
            default -> throw new IllegalArgumentException("direct fixed-window profile cannot prepare another action");
        };
    }
    static void requireDirectWindowExpected(ArmyCalls.Frame input) {
        String name = directWindowName(input.method());
        StrictJson.require(input.revision().value() instanceof ArmyTypes.Present<BigInteger> present
                && present.value().signum() > 0 && present.value().bitLength() <= 64,
                name + " expected_revision is outside its native integer range");
    }
    static void requireDirectWindowSource(ArmyCalls.Frame input, ArmyTypes.Context context, ObjectNode frame) {
        requireDirectWindowExpected(input); Objects.requireNonNull(context);
        requireDirectWindowBefore(input.method(), frame);
        ObjectNode actor = ArmyJson.object(frame.get("played_character"));
        StrictJson.require(integer(actor.get("character_id")).equals(context.playerId()) && integer(frame.get("revision")).equals(context.before().frame().revision())
                && integer(frame.get("native_revision")).equals(context.nativeRevision()) && integer(frame.get("date_raw")).equals(context.dateRaw()),
                "direct window before DATA differs from its actual typed caller frame");
        StrictJson.require(frame.get("snapshot_id").textValue().equals(context.before().frame().snapshotId()), "direct window snapshot identity missing or different");
        JsonNode episode = frame.get("episode_run_id"); String originalEpisode = context.before().frame().episodeRunId();
        StrictJson.require(originalEpisode == null ? episode == null || episode.isNull() : episode != null && episode.isTextual() && originalEpisode.equals(episode.textValue()),
                "direct window episode identity differs");
        StrictJson.require(context.source().exactBuild().equals("1.20.0.4"), "direct fixed-window producer requires its original exact .4 executable hello");
        input.revision().requireCurrent(context.before().frame().revision());
    }
    private static OrdinaryAutomaticSurrenderPolicy.Ready automaticEvidence(Complete actual, BigInteger fullWar,
            List<ArmyOrdinaryPreflight.Read> originals, ActionPorts.OutcomeArchive bound) {
        int id = fullWar.intValueExact(); StrictJson.require(id > 0, "automatic surrender needs a positive full int31 WarID");
        StrictJson.require(originals.size() == 1 && originals.getFirst().role() == Role.WAR_OPTIONS, "automatic surrender requires its one exact original options read");
        var decision = OrdinaryAutomaticSurrenderPolicy.evaluate(NativeOrdinaryWarAdmission.policyView(actual, originals, bound), id);
        if (!(decision instanceof OrdinaryAutomaticSurrenderPolicy.Ready ready))
            throw new IllegalArgumentException("native surrender fresh validation failed: " + ((OrdinaryAutomaticSurrenderPolicy.Unavailable) decision).reason()
                    + (id == 16777231 ? "; WAR31 external original authorization/immutable R0197 sources/durable once gate unavailable" : ""));
        return ready;
    }
    private static void requireNoAutomaticHistory(Complete actual, int fullWar) {
        var semantic = actual.semantic(); var raw = semantic.get("native_command_history");
        StrictJson.require(raw instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr,
                "automatic surrender requires complete original Driver command history");
        var export = semantic.get("native_command_history_export");
        StrictJson.require(export == null || export == org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,
                "partial Driver command history cannot authorize automatic surrender");
        var episode = semantic.get("episode_run_id"); StrictJson.require(episode != null, "original Driver episode field missing");
        StrictJson.require(OrdinaryAutomaticSurrenderPolicy.previousSubmission((org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr) raw, fullWar, episode).isEmpty(),
                "native emergency surrender was already submitted for this active WarID and episode");
    }
    /** Pure immutable original-receipt replay for the complete legacy result presenter. No live read or new command. */
    public static OrdinaryAutomaticSurrenderPolicy.Ready replayAutomaticSurrenderEvidence(ActionCommand original, Complete originalBefore,
            ActionPorts.OutcomeArchive boundArchive) {
        Objects.requireNonNull(original); Objects.requireNonNull(originalBefore); Objects.requireNonNull(boundArchive);
        var args = ArmyOrdinaryActionArguments.decode(original.arguments());
        StrictJson.require(args.executionProfile() == ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER
                && args.kind() == Kind.SURRENDER_WAR && args.preflightReads().size() == 1,
                "original command is not the canonical automatic surrender producer");
        StrictJson.require(original.origin() instanceof CommandOrigin.Gameplay && original.before().equals(originalBefore.identity())
                && original.source().equals(originalBefore.source()) && original.sessionId().equals(originalBefore.sessionId()),
                "automatic result replay crossed its original full Driver/source identity");
        var call = (ArmyCalls.War) ArmyCallCodec.decode(PublicMethod.SURRENDER_WAR, args.publicArguments());
        StrictJson.require(original.operation().value().equals("surrender-war-" + call.warId()), "automatic result changed its original primitive");
        var ref = args.preflightReads().getFirst(); var receipt = boundArchive.loadRead(ref);
        var context = new ArmyTypes.Context(originalBefore.identity(), originalBefore.source(), originalBefore.sessionId(), receipt.request().deadline());
        var query = ArmyCallCodec.decode(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,
                new RawJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(receipt.request().arguments())));
        StrictJson.require(query instanceof ArmyCalls.War && ((ArmyCalls.War) query).warId().equals(call.warId()), "automatic original quote changed its complete WarID");
        var decoded = ArmyWarReadCodec.decode(new ArmyWarReadCodec.Scope(query, context, originalBefore.semantic(), Optional.empty()), receipt);
        var read = new ArmyOrdinaryPreflight.Read(Role.WAR_OPTIONS, receipt, ref,
                new RawJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(decoded.normalizedResult())));
        var ready = automaticEvidence(originalBefore, call.warId(), List.of(read), boundArchive);
        StrictJson.require(args.automaticSurrender().orElseThrow() == ready.variant(), "automatic original variant is not reproduced by its archived evidence");
        return ready;
    }
    private NativeRequest validate(ContinuityStorePort.Session same, ArmyCalls.Call call, ArmyTypes.Context context, Complete actual, List<ArmyOrdinaryPreflight.Read> preflight,
            ActionPorts.OutcomeArchive boundArchive) {
        call.revision().requireCurrent(context.before().frame().revision());
        ObjectNode frame = ArmyJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(actual.semantic()));
        List<Long> costs = List.of();
        switch (kind(call)) {
            case MOVE_ARMY -> {
                ArmyCalls.Move selected = (ArmyCalls.Move) call; ObjectNode unit = ownedArmy(frame, selected.army().value(), context);
                requireFalse(unit.get("in_combat"), "ordinary move cannot order active combat"); requireFalse(unit.get("retreating"), "ordinary move cannot order a retreating army");
                positive(unit.get("current_province_id")); requireTrue(frame.get("army_routes_supported"), "typed ordinary move requires the actual native route capability");
            }
            case DISBAND_ARMY -> ownedArmy(frame, ((ArmyCalls.Unit) call).army().value(), context);
            case START_ASSAULT, STOP_ASSAULT -> {
                ArmyCalls.Siege selected = (ArmyCalls.Siege) call; requireTrue(frame.get("war_objective_assault_supported"), "exact assault state capability is unavailable");
                List<ArmyAssaultSelection.Holding> holdings = preflight.stream().filter(read -> read.role() == Role.HOLDING_SIEGE)
                        .flatMap(read -> List.copyOf(occupation.holdings(actual, read.original(), boundArchive)).stream()).toList();
                var siege = ArmyAssaultSelection.select(actual.semantic(), holdings, selected.siege().value())
                        .orElseThrow(() -> new IllegalArgumentException("same full SiegeID is absent or ambiguous in actual objective/holding observations")).siege();
                boolean start = selected.method() == PublicMethod.START_ASSAULT;
                StrictJson.require(siege.inProgress() != start, "selected SiegeID is already in the requested assault state");
                StrictJson.require(start ? siege.canStart() : siege.canStop(), "same-SiegeID native assault gate is false");
            }
            case ENFORCE_DEMANDS -> activeWar(frame, ((ArmyCalls.War) call).warId());
            case SURRENDER_WAR -> explicitSurrender(frame, context, (ArmyCalls.War) call, preflight);
            case OFFER_WHITE_PEACE -> { ArmyCalls.War selected = (ArmyCalls.War) call; activeWar(frame, selected.warId());
                one(preflight, Role.WAR_OPTIONS); whitePeace.verify(same, actual, selected.warId(), preflight); }
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1 -> costs = ally(context, (ArmyCalls.CallAlly) call, preflight);
            case DECLARE_WAR -> declaration((ArmyCalls.Declaration) call, preflight);
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> { StrictJson.require(preflight.size() == 1,
                    "Gathering control requires exactly one actual before-state/epoch query"); one(preflight, Role.GATHERING); }
            case CLOSE_WAR_DECLARED_OVERVIEW_V1 -> one(preflight, Role.OVERVIEW);
            case CLOSE_WAR_RESULTS_WINDOW_V1 -> one(preflight, Role.RESULTS);
            case SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1, RAISE_TROOPS_DEFAULT, HIRE_MERCENARY_V1, HIRE_HOLY_ORDER_V1 -> { }
            case ASSIGN_ARMY_COMMANDER_V1 -> throw new IllegalArgumentException("commander uses the unique existing assignment producer");
        }
        return primitive(call, context, costs);
    }
    public static Claims claims(ArmyCalls.Call call, ArmyTypes.Context context) {
        Kind kind = kind(call); Set<BigInteger> units = Set.of(); Set<BigInteger> allies = Set.of(); Set<BigInteger> characters = Set.of();
        var scopeJson = ArmyJson.empty().put("player", context.playerId());
        if (context.before().frame().episodeRunId() == null) scopeJson.putNull("episode_run_id");
        else scopeJson.put("episode_run_id", context.before().frame().episodeRunId());
        String scope = "army-scope:" + org.xar.ck3.control.application.driver.DriverJson.sha256(StrictJson.canonical(scopeJson)) + ":";
        String commitment;
        switch (call) {
            case ArmyCalls.Move c -> { units = Set.of(BigInteger.valueOf(c.army().value())); commitment = "army:" + c.army().value(); }
            case ArmyCalls.Unit c -> { units = Set.of(BigInteger.valueOf(c.army().value())); commitment = "army:" + c.army().value(); }
            case ArmyCalls.AssignCommander c -> { units = Set.of(BigInteger.valueOf(c.army().value())); if (c.character().value() > 0) characters = Set.of(BigInteger.valueOf(c.character().value())); commitment = "army:" + c.army().value(); }
            case ArmyCalls.Siege c -> commitment = "siege:" + c.siege().value();
            case ArmyCalls.War c -> commitment = "war-exit:" + c.warId();
            case ArmyCalls.Declaration ignored -> commitment = "declaration";
            case ArmyCalls.CallAlly c -> { if (c.recipient().value() > 0) allies = Set.of(BigInteger.valueOf(c.recipient().value())); commitment = "ally-invitation:" + c.war().value() + ":" + c.recipient().value(); }
            case ArmyCalls.CreateMaa c -> commitment = "maa-create:" + c.actionId();
            case ArmyCalls.Hire c -> commitment = (c.method() == PublicMethod.HIRE_HOLY_ORDER_V1 ? "holy-order:" : "mercenary:") + c.id().value();
            case ArmyCalls.Sampling ignored -> commitment = "gathering-capture-control";
            case ArmyCalls.Frame ignored -> commitment = kind.wire();
            default -> throw new IllegalArgumentException("no ordinary Army resource claim for this call");
        }
        if (call instanceof ArmyCalls.War war) {
            Claims terminal = ArmyOrdinaryWarClaims.of(context.playerId(), war.warId(), Optional.empty());
            return new Claims(units, allies, terminal.characterIds(), Set.of(scope + commitment, "war:" + war.warId()));
        }
        return new Claims(units, allies, characters, Set.of(scope + commitment));
    }
    /** The actual command includes the complete same-frame terminal scope, including its observed primary opponent. */
    public static Claims claims(ArmyCalls.Call call, ArmyTypes.Context context, Complete actual) {
        StrictJson.require(actual.identity().equals(context.before()) && actual.source().equals(context.source())
                && actual.sessionId().equals(context.sessionId()), "Army claims crossed the actual source frame");
        Claims base = claims(call, context);
        if (!(call instanceof ArmyCalls.War war)) return base;
        ObjectNode frame = ArmyJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(actual.semantic()));
        ObjectNode selected = activeWar(frame, war.warId());
        JsonNode raw = selected.get("primary_opponent_character_id");
        Optional<BigInteger> opponent = raw == null || raw.isNull() ? Optional.empty() : Optional.of(integer(raw)).filter(id -> id.signum() > 0);
        Claims terminal = ArmyOrdinaryWarClaims.of(context.playerId(), war.warId(), opponent);
        return new Claims(base.armyIds(), base.allyCharacterIds(), terminal.characterIds(), base.commitmentKeys());
    }
    private static ObjectNode ownedArmy(ObjectNode frame, int army, ArmyTypes.Context context) {
        ObjectNode unit = unique(frame.get("player_armies"), "army_id", BigInteger.valueOf(army));
        requireTrue(unit.get("controllable"), "selected army is not controllable");
        StrictJson.require(integer(unit.get("owner_character_id")).equals(context.playerId()), "selected army belongs to another player"); return unit;
    }
    private static ObjectNode activeWar(ObjectNode frame, BigInteger war) { return unique(frame.get("active_wars"), "war_id", war); }
    private static ObjectNode one(List<ArmyOrdinaryPreflight.Read> values, Role role) {
        var selected = values.stream().filter(value -> value.role() == role).toList();
        StrictJson.require(selected.size() == 1, "required original Army preflight read is absent or ambiguous: " + role);
        return ArmyJson.parse(selected.getFirst().normalized().bytes());
    }
    private static List<Long> ally(ArmyTypes.Context context, ArmyCalls.CallAlly selected, List<ArmyOrdinaryPreflight.Read> reads) {
        StrictJson.require(!BigInteger.valueOf(selected.recipient().value()).equals(context.playerId()), "call ally recipient is the current player");
        ObjectNode top = one(reads, Role.FAMILY_OBLIGATIONS); ObjectNode obligations = ArmyJson.object(top.get("alliance_obligations"));
        StrictJson.require(ArmyJson.text(obligations.get("status")).equals("available")
                && integer(obligations.get("first_character_id")).equals(context.playerId())
                && integer(obligations.get("second_character_id")).equals(BigInteger.valueOf(Integer.toUnsignedLong(selected.recipient().value())))
                && integer(obligations.get("raw_scale")).equals(BigInteger.valueOf(100000)), "call ally selected pair/source/scale drift");
        var slots = obligations.get("send_cost_slot_keys"); List<String> keys = List.of("gold", "prestige", "piety", "renown", "influence", "herd", "treasury", "treasury_or_gold", "merit", "barter_goods");
        StrictJson.require(slots != null && slots.isArray() && slots.size() == keys.size(), "call ally cost slot inventory malformed");
        for (int i = 0; i < keys.size(); i++) StrictJson.require(ArmyJson.text(slots.get(i)).equals(keys.get(i)), "call ally native cost slot order changed");
        ObjectNode row = unique(obligations.get("first_wars"), "war_id", BigInteger.valueOf(Integer.toUnsignedLong(selected.war().value())));
        StrictJson.require(integer(row.get("caller_character_id")).equals(context.playerId())
                && integer(row.get("recipient_character_id")).equals(BigInteger.valueOf(Integer.toUnsignedLong(selected.recipient().value()))), "call ally war row belongs to another invitation");
        for (String flag : List.of("native_target_can_be_picked", "native_target_row_selectable", "native_complete_can_send"))
            requireTrue(row.get(flag), "native call ally final gate refused the selected invitation");
        JsonNode raw = row.get("send_cost_raw"); StrictJson.require(raw != null && raw.isArray() && raw.size() == 10, "complete native ten-slot send quote required");
        List<Long> costs = new ArrayList<>(); raw.forEach(value -> costs.add(integer(value).longValueExact())); return List.copyOf(costs);
    }
    private static void declaration(ArmyCalls.Declaration selected, List<ArmyOrdinaryPreflight.Read> reads) {
        ObjectNode top = one(reads, Role.DECLARATIONS); JsonNode rows = top.get("declarable_wars");
        StrictJson.require(rows != null && rows.isArray(), "complete original declaration choices required"); int matches = 0;
        for (JsonNode value : rows) { ObjectNode row = ArmyJson.object(value); if (ArmyJson.text(row.get("declaration_id")).equals(selected.declarationId())) matches++; }
        StrictJson.require(matches == 1, "selected declaration is absent or ambiguous in the current original query");
    }
    private static void explicitSurrender(ObjectNode frame, ArmyTypes.Context context, ArmyCalls.War selected, List<ArmyOrdinaryPreflight.Read> reads) {
        ObjectNode war = activeWar(frame, selected.warId()); ObjectNode top = one(reads, Role.WAR_OPTIONS);
        ObjectNode options = ArmyJson.object(top.get("war_termination_options"));
        StrictJson.require(integer(options.get("war_id")).equals(selected.warId()), "surrender quote WarID differs");
        String side = ArmyJson.text(war.get("player_side")); StrictJson.require(side.equals("attacker") || side.equals("defender"), "surrender player side unavailable");
        requireTrue(war.get("player_is_primary_war_leader"), "surrender requires the player primary war leader");
        requireTrue(options.get("player_is_primary_war_leader"), "native surrender quote lacks primary-leader identity");
        StrictJson.require(ArmyJson.text(options.get("player_side")).equals(side)
                && options.get("player_relative_war_score").equals(war.get("player_relative_war_score")), "surrender quote differs from the actual active war");
        ObjectNode offer = ArmyJson.object(ArmyJson.object(options.get("options")).get("surrender"));
        StrictJson.require(ArmyJson.text(offer.get("outcome")).equals(side.equals("attacker") ? "attacker_defeat" : "attacker_victory")
                && ArmyJson.text(offer.get("hostage_variant")).equals("none"), "surrender native outcome/hostage variant changed");
        for (String gate : List.of("context_constructed", "native_validator_passed", "available", "auto_accept_observable", "auto_accept"))
            requireTrue(offer.get(gate), "explicit surrender lacks its actual native final legality");
        ArmyJson.object(offer.get("recipient_response"));
        StrictJson.require(context.before().frame().revision().signum() > 0, "explicit surrender requires current positive public revision");
    }
    private static ObjectNode unique(JsonNode rows, String key, BigInteger value) {
        StrictJson.require(rows != null && rows.isArray(), "actual complete Army collection required"); List<ObjectNode> matches = new ArrayList<>();
        for (JsonNode raw : rows) { ObjectNode row = ArmyJson.object(raw); if (integer(row.get(key)).equals(value)) matches.add(row); }
        StrictJson.require(matches.size() == 1, "selected full Army identity is absent or ambiguous"); return matches.getFirst();
    }
    private static BigInteger integer(JsonNode value) { StrictJson.require(value != null && value.isIntegralNumber(), "native integer token required; bool, float, text and null are distinct"); return value.bigIntegerValue(); }
    private static void positive(JsonNode value) { StrictJson.require(integer(value).signum() > 0, "positive native province identity required"); }
    private static void requireTrue(JsonNode value, String reason) { StrictJson.require(value != null && value.isBoolean() && value.booleanValue(), reason); }
    private static void requireFalse(JsonNode value, String reason) { StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(), reason); }
}
