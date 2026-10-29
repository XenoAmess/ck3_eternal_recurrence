package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Actual battle and route queries composed on one paused frame; it never submits a move. */
public final class ArmyRetreatPreview {
    public static final String STAGE = ArmyRetreatTokens.STAGE;
    public record Captured(ArmyRetreatFrames.Current before, ArmyRetreatFrames.Current after,
            PlanningReadResult.Known<ArmyBattleReads.Observation> control, Optional<PlanningReadResult.Known<ArmyRouteReads.Route>> route,
            Optional<PlanningReadResult.Unavailable<ArmyRouteReads.Route>> unavailableRoute, ArmyCalls.RetreatPreview input, Obj value) {
        public Captured { Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(control); Objects.requireNonNull(route); Objects.requireNonNull(unavailableRoute); Objects.requireNonNull(input); Objects.requireNonNull(value); require(!(route.isPresent() && unavailableRoute.isPresent()), "route cannot be both known and unavailable"); }
        public boolean ready() { return new OpportunityJson.Bool(true).equals(value.get("action_ready")); }
    }
    private final ArmyRetreatFrames frames;
    private final ArmyBattleReads battles;
    private final ArmyRouteReads routes;
    private final java.util.function.Supplier<RootReadContractCatalog> catalog;
    private final Optional<OriginalFrames> originals;
    private record OriginalFrames(OutcomeArchive archive, NativeEffectEvidence.FrameLoader loader) {
        private OriginalFrames { Objects.requireNonNull(archive); Objects.requireNonNull(loader); }
    }
    private final SecureRandom random = new SecureRandom();
    public ArmyRetreatPreview(ArmyRetreatFrames frames, ArmyBattleReads battles, ArmyRouteReads routes, RootReadContractCatalog catalog) {
        this(frames, battles, routes, () -> Objects.requireNonNull(catalog));
    }
    public ArmyRetreatPreview(ArmyRetreatFrames frames, ArmyBattleReads battles, ArmyRouteReads routes, java.util.function.Supplier<RootReadContractCatalog> actualCatalog) {
        this(frames,battles,routes,actualCatalog,Optional.empty());
    }
    public ArmyRetreatPreview(ArmyRetreatFrames frames, ArmyBattleReads battles, ArmyRouteReads routes,
            java.util.function.Supplier<RootReadContractCatalog> actualCatalog, OutcomeArchive originalArchive,
            NativeEffectEvidence.FrameLoader actualLoader) {
        this(frames,battles,routes,actualCatalog,Optional.of(new OriginalFrames(originalArchive,actualLoader)));
    }
    private ArmyRetreatPreview(ArmyRetreatFrames frames, ArmyBattleReads battles, ArmyRouteReads routes,
            java.util.function.Supplier<RootReadContractCatalog> actualCatalog, Optional<OriginalFrames> originals) {
        this.frames = Objects.requireNonNull(frames); this.battles = Objects.requireNonNull(battles); this.routes = Objects.requireNonNull(routes); this.catalog = Objects.requireNonNull(actualCatalog);
        this.originals=Objects.requireNonNull(originals);
    }
    public Captured capture(ContinuityStorePort.Session session, ArmyCalls.RetreatPreview input, java.time.Instant deadline) throws InterruptedException {
        return capture(session, input, frames.current(deadline));
    }
    public Captured capture(ContinuityStorePort.Session session, ArmyCalls.RetreatPreview input, ArmyRetreatFrames.Current before) throws InterruptedException {
        try {return capture(session,input,before,false);}
        catch(IOException failure) {throw new java.io.UncheckedIOException(failure);}
    }
    /** Uses the already-held Root frame and the actual query guards; no observation producer is called. */
    public Captured captureBorrowed(ContinuityStorePort.Session session, ArmyCalls.RetreatPreview input,
            ArmyRetreatFrames.Current before) throws IOException {
        if(originals.isEmpty())throw new IOException("borrowed retreat preview requires its original archive and frame loader");
        try {return capture(session,input,before,true);}
        catch(InterruptedException impossible) {Thread.currentThread().interrupt();throw new IOException("borrowed retreat preview was interrupted",impossible);}
    }
    private Captured capture(ContinuityStorePort.Session session, ArmyCalls.RetreatPreview input,
            ArmyRetreatFrames.Current before, boolean borrowed) throws IOException, InterruptedException {
        Objects.requireNonNull(session); Objects.requireNonNull(before); var deadline = before.deadline(); input.revision().requireCurrent(before.context().before().frame().revision());
        Obj selected = ArmyRetreatFrames.selected(before, input.selected()); PositiveId origin = new PositiveId(OpportunityJson.integer(selected.get("current_province_id"), "selected origin").intValueExact());
        var controlCall = new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, input.revision(), input.selected());
        var observed = battles.read(session, Objects.requireNonNull(catalog.get()), new ArmyBattleReads.Selection(controlCall, before.context()));
        var control = requireControl(observed); require(control.combatProvince().equals(origin), "semantic retreat origin differs from exact CombatID province");
        Optional<String> reason = Optional.empty(); Optional<PlanningReadResult.Known<ArmyRouteReads.Route>> route = Optional.empty(); Optional<PlanningReadResult.Unavailable<ArmyRouteReads.Route>> unavailable = Optional.empty();
        if (control.retreat().status() != Availability.AVAILABLE || !control.retreat().legalNow()) {
            String first = control.retreat().reasons().isEmpty() ? "native_legality_unavailable" : control.retreat().reasons().getFirst(); reason = Optional.of("retreat_not_legal:" + first);
        } else if (origin.equals(input.target())) reason = Optional.of("target_does_not_leave_combat_province");
        else {
            var collected = routes.collect(session, Objects.requireNonNull(catalog.get()), new ArmyRouteReads.Selection(before.context(), input.selected(), origin, input.target()));
            if (collected instanceof PlanningReadResult.Known<ArmyRouteReads.Route> known) route = Optional.of(known);
            else { unavailable = Optional.of((PlanningReadResult.Unavailable<ArmyRouteReads.Route>) collected); reason = Optional.of("target_route_preview_unavailable"); }
        }
        var after = borrowed ? afterOriginal(session,before,route.map(PlanningReadResult.Known::receipt).orElse(observed.receipt()))
                : frames.current(deadline); ArmyRetreatFrames.same(before, after);
        String token = null;
        if (reason.isEmpty()) { byte[] bytes = new byte[24]; random.nextBytes(bytes); token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes); }
        Obj value = compose(input, before.source(), control, route.map(PlanningReadResult.Known::value), Optional.ofNullable(token), reason);
        return new Captured(before, after, observed, route, unavailable, input, value);
    }
    private ArmyRetreatFrames.Current afterOriginal(ContinuityStorePort.Session same, ArmyRetreatFrames.Current before,
            PlanningReadReceipt actual) throws IOException {
        var source=originals.orElseThrow();var archive=source.archive().withSession(same);
        var ref=archive.readReferenceOf(actual);require(archive.loadRead(ref).equals(actual),"retreat query is not its archived original");
        RootGuardEvidence.requireHistory(actual.before().binding(),archive,same);
        RootGuardEvidence.requireHistory(actual.after().binding(),archive,same);
        var originalBefore=RootGuardEvidence.loadFrame(actual.before().binding(),archive,source.loader());
        var originalAfter=RootGuardEvidence.loadFrame(actual.after().binding(),archive,source.loader());
        require(originalBefore.fullBindingSha256().equals(actual.before().originalBindingSha256())
                && originalAfter.fullBindingSha256().equals(actual.after().originalBindingSha256()),"retreat query changed its complete original binding");
        ArmyRetreatFrames.same(before,new ArmyRetreatFrames.Current(originalBefore,before.deadline()));
        return new ArmyRetreatFrames.Current(originalAfter,before.deadline());
    }
    public static BattleResponses.Control requireControl(PlanningReadResult.Known<ArmyBattleReads.Observation> read) {
        require(read.value() instanceof ArmyBattleReads.Control, "exact battle-control observation required"); return ((ArmyBattleReads.Control) read.value()).value();
    }
    public static Obj compose(ArmyCalls.RetreatPreview input, org.xar.ck3.control.application.planning.military.ActiveRetreatProposal.SourceFrame source,
            BattleResponses.Control control, Optional<ArmyRouteReads.Route> route, Optional<String> token, Optional<String> reason) {
        require(input.selected().equals(control.selected()) && input.selected().equals(control.subject()), "preview subject differs from normalized battle");
        boolean ready = reason.isEmpty(); require(ready == route.isPresent() && ready == token.isPresent(), "available preview needs its actual route and generated token");
        var body = empty().put("schema_version", 1).put("contract_stage", STAGE).put("step", previewStep(input.selected(), input.target())).put("status", ready ? "available" : "unavailable")
                .put("action_ready", ready).put("selected_public_cunit_id", control.selected().value()).put("selected_native_carmy_id", control.selectedNative().value())
                .put("selected_owner_character_id", control.selectedOwner().value()).put("combat_id", control.combat().value()).put("combat_province_id", control.combatProvince().value())
                .put("side_index", control.side() == Side.ATTACKER ? 0 : 1).put("side_scope", wire(control.scope())).put("target_province_id", input.target().value()).put("backend_id", "native-headless");
        if (reason.isPresent()) body.put("unavailable_reason", reason.orElseThrow()); else body.putNull("unavailable_reason");
        body.set("source_binding", OpportunityJson.toNode(source.json())); body.set("battle_control_snapshot", OpportunityJson.toNode(control.originalFrame()));
        var affected = body.putArray("affected_public_cunit_ids_in_stored_order"); control.affected().forEach(id -> affected.add(id.value()));
        var unaffected = body.putArray("unaffected_same_side_public_cunit_ids_in_stored_order"); control.unaffected().forEach(id -> unaffected.add(id.value()));
        var target = ready ? parse(DriverJson.encode(route.orElseThrow().canonical())) : empty().put("army_id", input.selected().value()).put("origin_province_id", control.combatProvince().value())
                .put("target_province_id", input.target().value()).putNull("previewed_date_raw").putNull("move_mode").putNull("eta_date_raw").putNull("movement_days");
        if (!ready) target.putArray("route_province_ids");
        target.put("status", ready ? "available" : "unavailable").put("provenance", "planner_selected_exact_native_route_preview");
        if (ready) {
            require(control.retreat().status() == Availability.AVAILABLE && control.retreat().legalNow(), "native legality must approve an available retreat preview");
            String candidate = token.orElseThrow(); require(candidate.matches("[A-Za-z0-9_-]{32,128}"), "original URL-safe token contract required");
            target.putNull("unavailable_reason").put("candidate_token", candidate).put("order_step", orderStep(input.selected(), source.revision(), control.combat(), control.side() == Side.ATTACKER ? 0 : 1, control.scope(), input.target(), candidate));
        } else target.put("unavailable_reason", reason.orElseThrow()).putNull("candidate_token").putNull("order_step");
        body.set("target_preview", target); return DriverJson.object(bytes(body), DriverJson.MAX_NATIVE_BYTES);
    }
    public static String previewStep(PublicUnitId selected, PositiveId target) { return "preview-active-combat-retreat-v1-" + selected.value() + "-to-" + target.value(); }
    public static String orderStep(PublicUnitId selected, java.math.BigInteger revision, FullId combat, int side, Scope scope, PositiveId target, String token) {
        require((side == 0 || side == 1) && token.matches("[A-Za-z0-9_-]{32,128}"), "exact retreat order fields required");
        return "order-active-combat-retreat-v1-" + selected.value() + "-revision-" + revision + "-combat-" + combat.value() + "-side-" + side + "-scope-" + wire(scope) + "-to-" + target.value() + "-token-" + token;
    }
    private static String wire(Scope scope) { return scope.name().toLowerCase(java.util.Locale.ROOT); }
}
