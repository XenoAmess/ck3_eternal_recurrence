package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.FrontendFrame;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.*;

/** These exact object instances are installed in the sole PlanningReadCoordinator registry by the root. */
public final class FrontendRulesDefinitions {
    private final Build exactBuild;
    private final ExactRef originalDriverSource;
    private final ReadContract<RuleSelections> appliedRules;
    private final ReadContract<RuleSelections> selections;
    private final ReadContract<RuleWindow> window;
    private final ReadContract<ObservedRoute> route;
    private final ReadContract<GuiTree> tree;
    private final ReadContract<BookmarkModel> bookmark;
    private final ReadContract<BookmarkModel> scenarioBookmark;
    private final ReadContract<LoadedFeaturesData.Observation> loadedFeatures;
    public FrontendRulesDefinitions(Build exactBuild, ExactRef originalDriverSource) {
        this.exactBuild = Objects.requireNonNull(exactBuild); this.originalDriverSource = Objects.requireNonNull(originalDriverSource);
        require(originalDriverSource.bytes() > 0, "actual original driver source required");
        appliedRules = frontend(Primitive.APPLIED_RULES, value -> FrontendRulesCodec.selections(result(value), source(value), sequence(value), true));
        selections = frontend(Primitive.RULE_SELECTIONS, value -> FrontendRulesCodec.selections(result(value), source(value), sequence(value), false));
        window = frontend(Primitive.RULES_WINDOW, value -> FrontendRulesCodec.window(result(value), source(value), sequence(value)));
        route = frontend(Primitive.ROUTE, value -> FrontendRulesCodec.route(result(value), source(value), sequence(value)));
        tree = frontend(Primitive.TREE, value -> FrontendRulesCodec.tree(result(value), source(value), sequence(value)));
        bookmark = frontend(Primitive.BOOKMARK_MODEL, value -> FrontendRulesCodec.bookmarkModel(result(value), source(value), sequence(value)));
        scenarioBookmark = frontend(Primitive.SCENARIO_PROBE, value -> {
            require(exactBuild == Build.CK3_12004, "scenario probe is actual .4 only");
            return FrontendRulesCodec.bookmarkModel(result(value), source(value), sequence(value));
        });
        loadedFeatures = new ReadContract<>("frontend-rules.loaded-features.v1", Primitive.LOADED_FEATURES.operation(), Optional.of(Primitive.LOADED_FEATURES.capability()),
                "original-driver.loaded-feature-manifest-v1", ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, originalDriverSource, request -> empty(request, Primitive.LOADED_FEATURES), value -> {
                    var before = value.request().before(); var frame = before.frame(); var identity = frame.identity();
                    var decoded = LoadedFeaturesCodec.decode(result(value), exactBuild, identity.nativeRevision(), identity.dateRaw().intValueExact());
                    return new LoadedFeaturesData.Observation(decoded.manifest(), decoded.querySequence(), frame.snapshotId(), frame.revision(), "native-headless", Optional.ofNullable(frame.episodeRunId()));
                });
    }
    private <T> ReadContract<T> frontend(Primitive primitive, Function<PlanningReadReceipt, T> decoder) {
        return new ReadContract<>("frontend-rules." + primitive.operation().value(), primitive.operation(), Optional.of(primitive.capability()),
                "original-driver." + primitive.operation().value(), ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.FRONTEND_SESSION, originalDriverSource, request -> empty(request, primitive), decoder);
    }
    private static NativeRequest empty(PlanningReadRequest request, Primitive primitive) {
        require(FrontendRulesCodec.object(new RawJson(OpportunityJson.encode(request.arguments()))).isEmpty(), "read does not accept unregistered additional fields");
        require(primitive.frontend() == (request.origin() instanceof CommandOrigin.Frontend), "query origin/profile mismatch");
        if (primitive.frontend()) require(request.origin().requireFrontend().frame() instanceof FrontendFrame.Menu,
                "frontend rules and route queries require the actual zero revision Menu profile");
        return primitive.emptyRequest();
    }
    public Build exactBuild() { return exactBuild; }
    public ExactRef originalDriverSource() { return originalDriverSource; }
    public List<ReadContract<?>> contracts() { return List.of(appliedRules, selections, window, route, tree, bookmark, scenarioBookmark, loadedFeatures); }
    public ReadContract<RuleSelections> appliedRules() { return appliedRules; }
    public ReadContract<RuleSelections> selections() { return selections; }
    public ReadContract<RuleWindow> window() { return window; }
    public ReadContract<ObservedRoute> route() { return route; }
    public ReadContract<GuiTree> tree() { return tree; }
    public ReadContract<BookmarkModel> bookmark() { return bookmark; }
    public ReadContract<BookmarkModel> scenarioBookmark() { return scenarioBookmark; }
    public ReadContract<LoadedFeaturesData.Observation> loadedFeatures() { return loadedFeatures; }
    public Source source(PlanningReadReceipt receipt) {
        require(receipt.after().binding().origin() instanceof CommandOrigin.Frontend, "frontend query lost its typed origin");
        var frontend = (CommandOrigin.Frontend) receipt.after().binding().origin();
        require(frontend.identity().frame() instanceof FrontendFrame.Menu, "frontend rules cannot adopt a positive snapshot revision");
        return new Source(new Binding(frontend.identity().bridgePid(), frontend.identity().connectionGeneration()), exactBuild);
    }
    public static BigInteger sequence(PlanningReadReceipt receipt) {
        require(receipt.after().binding().origin() instanceof CommandOrigin.Frontend, "frontend query sequence requires original typed frontend frame");
        return ((CommandOrigin.Frontend) receipt.after().binding().origin()).identity().frame().querySequence();
    }
    public static RawJson result(PlanningReadReceipt receipt) {
        require(receipt.original().nativeOk(), "native query ACK rejected"); return receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("original native result token absent"));
    }
}
