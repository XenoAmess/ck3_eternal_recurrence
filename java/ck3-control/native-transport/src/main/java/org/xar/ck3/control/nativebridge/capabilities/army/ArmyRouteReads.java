package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Native preview-move query used by active retreat; all optional siblings are validated by their sole shared codec. */
public final class ArmyRouteReads {
    public static final String CAPABILITY = "game.command.preview-move-army-N-to-N";
    public record Selection(Context context, PublicUnitId army, PositiveId origin, PositiveId target) {
        public Selection { Objects.requireNonNull(context); Objects.requireNonNull(army); Objects.requireNonNull(origin); Objects.requireNonNull(target); require(!origin.equals(target), "retreat route must leave the combat province"); }
        public String step() { return "preview-move-army-" + army.value() + "-to-" + target.value(); }
    }
    public record Route(PublicUnitId army, PositiveId origin, PositiveId target, List<PositiveId> provinces, long previewedDateRaw, Obj completeNativePreview) {
        public Route {
            Objects.requireNonNull(army); Objects.requireNonNull(origin); Objects.requireNonNull(target); Objects.requireNonNull(completeNativePreview); provinces = List.copyOf(provinces);
            require(!provinces.isEmpty() && provinces.getLast().equals(target) && !origin.equals(target), "exact retreat route endpoint required");
        }
        public Obj canonical() {
            var n = empty().put("army_id", army.value()).put("origin_province_id", origin.value()).put("target_province_id", target.value()).put("previewed_date_raw", previewedDateRaw)
                    .putNull("move_mode").putNull("eta_date_raw").putNull("movement_days");
            var path = n.putArray("route_province_ids"); provinces.forEach(p -> path.add(p.value()));
            return OpportunityJson.object(OpportunityJson.parse(bytes(n)), "canonical retreat route");
        }
    }
    private final RootReadContractCatalog.Family<Selection,Route> family;
    private final PlanningReadPort reads;
    public ArmyRouteReads(ExactRef definitionSource, ExactRef decoderSource, PlanningReadPort reads) {
        this.reads = Objects.requireNonNull(reads);
        family = new RootReadContractCatalog.Family<>("army-active-retreat-exact-route", Selection.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.of(CAPABILITY),
                definitionSource, decoderSource, ArmyRouteReads::key, s -> new OperationKey(s.step()), s -> new ReadContract<>(
                        "army-active-retreat-route-" + ArmyReadKey.digest(key(s)), new OperationKey(s.step()), Optional.of(CAPABILITY), CAPABILITY,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definitionSource,
                        (request,id) -> { verify(request, s); return new NativeRequest(s.step(), Optional.of(CAPABILITY), new RawJson(new byte[]{'{','}'})); },
                        receipt -> { verify(receipt.request(), s); return decode(s, receipt); }, receipt -> { verify(receipt.request(),s);return decode(s,receipt); },
                        (original,value,current,semantic) -> ArmyNativeReadEvidence.requireCanonicalEquivalent(original,current)));
    }
    public RootReadContractCatalog.Family<Selection,Route> family() { return family; }
    public PlanningReadResult.Known<Route> read(ContinuityStorePort.Session borrowed, RootReadContractCatalog catalog, Selection s) {
        var result = collect(borrowed, catalog, s);
        if (result instanceof PlanningReadResult.Known<Route> known) return known;
        throw new IllegalStateException(((PlanningReadResult.Unavailable<Route>) result).reason());
    }
    public PlanningReadResult<Route> collect(ContinuityStorePort.Session borrowed, RootReadContractCatalog catalog, Selection s) {
        Objects.requireNonNull(borrowed); var contract = catalog.issue(family, s); Context c = s.context();
        var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), contract.operation(), arguments(s), c.deadline());
        return reads.read(borrowed, contract, request);
    }
    public static Route decode(Selection s, PlanningReadReceipt receipt) {
        verify(receipt.request(),s); var current=ArmyNativeReadEvidence.contextForRequest(s.context(),receipt.request());
        var result = closed(ArmyNativeReadEvidence.result(current, receipt), "step", "accepted", "status", "route_preview");
        equal(result.get("step"), s.step()); yes(result.get("accepted")); equal(result.get("status"), "available");
        var preview = object(result.get("route_preview")); Set<String> required = Set.of("status", "army_id", "origin_province_id", "target_province_id", "route_province_ids");
        var extra = new java.util.HashSet<>(names(preview)); require(extra.containsAll(required), "native route required field missing"); extra.removeAll(required);
        require(Set.of("province_supply", "county_entry_condition_v1").containsAll(extra), "unknown native route extension");
        Obj normalized = ArmyRouteOptionalCodec.normalize(org.xar.ck3.control.application.driver.DriverJson.object(bytes(preview), org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES));
        equal(preview.get("status"), "available"); require(unit(preview.get("army_id")).equals(s.army()) && id(preview.get("origin_province_id")).equals(s.origin())
                && id(preview.get("target_province_id")).equals(s.target()), "native route crossed original subject/origin/target");
        List<PositiveId> route = array(preview.get("route_province_ids"), ArmyJson::id);
        return new Route(s.army(), s.origin(), s.target(), route, s.context().dateRaw().longValueExact(), normalized);
    }
    private static RawJson key(Selection s) {
        var input = new ArmyCalls.RetreatPreview(new ArmyCalls.Revision(new Present<>(s.context().before().frame().revision())), s.army(), s.target());
        var n = parse(ArmyReadKey.key(input, s.context()).bytes()).put("origin_province_id", s.origin().value()); return new RawJson(bytes(n));
    }
    private static Obj arguments(Selection s) { return OpportunityJson.object(OpportunityJson.parse(bytes(empty().put("army_id", s.army().value()).put("origin_province_id", s.origin().value()).put("target_province_id", s.target().value()))), "route query selection"); }
    private static void verify(PlanningReadRequest request, Selection s) {
        Context c = s.context(); require(request.before().equals(c.before()) && request.source().equals(c.source()) && request.sessionId().equals(c.sessionId())
                && request.arguments().equals(arguments(s)), "route query crossed its complete source or selected scope");
    }
}
