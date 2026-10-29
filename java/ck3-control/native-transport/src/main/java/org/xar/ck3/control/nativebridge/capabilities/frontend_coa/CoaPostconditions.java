package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.ObservedRoute;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Route;

/** Domain validators for fresh independent observations. These values do not themselves grant ledger settlement. */
public final class CoaPostconditions {
    private CoaPostconditions() { }
    public record ReadEvidence<T>(T value, String requestId, Instant observedAt, ExactRef originalEvidence) {
        public ReadEvidence { Objects.requireNonNull(value); text(requestId, 4096); Objects.requireNonNull(observedAt); Objects.requireNonNull(originalEvidence); require(originalEvidence.bytes() > 0, "original independent observation evidence required"); }
    }
    public enum DesignerAction {
        OPEN("activate-frontend-coat-of-arms-designer-v1", "open_coat_of_arms_designer", Route.RULER_DESIGNER, Route.COAT_OF_ARMS_DESIGNER),
        COMMIT("commit-frontend-dynasty-coat-of-arms-v1", "commit_dynasty_coat_of_arms", Route.COAT_OF_ARMS_DESIGNER, Route.RULER_DESIGNER),
        CUSTOM_MODE("activate-frontend-coat-of-arms-custom-mode-v1", "enter_coat_of_arms_custom_mode", Route.COAT_OF_ARMS_DESIGNER, Route.COAT_OF_ARMS_DESIGNER);
        private final String step, action; private final Route before, after;
        DesignerAction(String step, String action, Route before, Route after) { this.step = step; this.action = action; this.before = before; this.after = after; }
        public String step() { return step; } public String action() { return action; } public Route beforeRoute() { return before; } public Route afterRoute() { return after; }
    }
    public record DesignerVerified(DesignerAction action, ReadEvidence<ObservedRoute> before, ReadEvidence<Tree> beforeInspection,
            CoaCodec.ActivationAck acknowledgement, ReadEvidence<ObservedRoute> after, Optional<ReadEvidence<Tree>> afterInspection) {
        public DesignerVerified { Objects.requireNonNull(action); Objects.requireNonNull(before); Objects.requireNonNull(beforeInspection); Objects.requireNonNull(acknowledgement); Objects.requireNonNull(after); afterInspection = Objects.requireNonNull(afterInspection); }
        public boolean postconditionVerified() { return true; } public boolean usesOcr() { return false; } public boolean usesKeyboard() { return false; } public boolean usesMouse() { return false; }
    }
    public static void designerReady(DesignerAction action, ObservedRoute route, Tree tree) {
        require(route.route() == action.beforeRoute(), "CoA action requires its exact native route");
        require(tree.available(), "CoA action requires visible native root");
        switch (action) {
            case OPEN -> require(tree.scopeRootName().equals("ruler_designer") && tree.widgets().stream().anyMatch(row -> row.childPath().equals("0/0/0/0/0/0/0/3/1/0") && row.runtimeName().isEmpty() && row.childCount() == 2 && row.effectiveVisible() && row.enabled()), "native dynasty CoA parent target not ready");
            case COMMIT -> require(tree.scopeRootName().equals("ruler_designer") && tree.has("0/2/1/1", "dynasty_finish_button"), "native dynasty Finish target not ready");
            case CUSTOM_MODE -> require(tree.scopeRootName().equals("coat_of_arms_page") && tree.step().equals("inspect-frontend-coat-of-arms-tree-v1") && tree.widgets().stream().filter(row -> List.of("0/3/0/2/1/0/0/1/1/0", "0/3/0/2/1/0/0/2/1/0").contains(row.childPath()) && row.runtimeName().equals("button_custom_mode") && row.effectiveVisible() && row.enabled()).count() == 1, "exactly one visible custom-mode target required");
        }
    }
    public static boolean backgroundReady(Tree tree) {
        return tree.available() && tree.step().equals("inspect-frontend-coat-of-arms-tree-v1") && tree.scopeRootName().equals("coat_of_arms_page")
                && tree.has("0/3/0/2/0", "coa_designer_tabs") && tree.has("0/3/0/2/1/1", "background_panel")
                && tree.has("0/3/0/2/1/1/2", "patterns") && tree.has("0/3/0/2/1/1/2/0/0", "patterns_scrollbox");
    }
    public static DesignerVerified designer(DesignerAction action, ReadEvidence<ObservedRoute> before, ReadEvidence<Tree> beforeTree,
            CoaCodec.ActivationAck acknowledgement, String mutationRequestId, Instant submittedAt, ReadEvidence<ObservedRoute> after, Optional<ReadEvidence<Tree>> afterTree) {
        designerReady(action, before.value(), beforeTree.value()); require(acknowledgement.step().equals(action.step()), "designer ACK belongs to another operation");
        require(after.value().source().equals(before.value().source()) && after.value().route() == action.afterRoute(), "designer independent route postcondition not proven");
        require(after.value().querySequence().compareTo(before.value().querySequence()) > 0, "designer route observation is not newer");
        independent(mutationRequestId, submittedAt, after); if (action == DesignerAction.CUSTOM_MODE) {
            ReadEvidence<Tree> inspected = afterTree.orElseThrow(() -> new IllegalArgumentException("custom mode requires fresh independent background census")); independent(mutationRequestId, submittedAt, inspected);
            require(backgroundReady(inspected.value()), "custom-mode native background patterns not ready");
        }
        return new DesignerVerified(action, before, beforeTree, acknowledgement, after, afterTree);
    }
    public record SourceApplied(ProbeResult acknowledgement, ReadEvidence<ExportResult> observedSource) { public SourceApplied { Objects.requireNonNull(acknowledgement); Objects.requireNonNull(observedSource); } }
    public static SourceApplied sourceApplied(ProbeResult probe, String mutationRequestId, Instant submittedAt, ReadEvidence<ExportResult> after) {
        require(probe.status() == ProbeStatus.APPLIED, "native probe did not acknowledge apply"); independent(mutationRequestId, submittedAt, after); ExportResult actual = after.value();
        require(actual.status() == ExportStatus.EXPORTED && actual.binding().equals(probe.binding()) && actual.querySequence().compareTo(probe.querySequence()) > 0, "fresh source observer crossed binding or sequence");
        require(actual.source().equals(Optional.of(probe.source().source())) && actual.sourceSha256().equals(Optional.of(probe.source().sourceSha256())) && actual.sourceBytes() == probe.source().sourceBytes(), "actual current CoA source differs from submitted canonical bytes");
        return new SourceApplied(probe, after);
    }
    public record StableCapture<T>(T result, Binding binding, ReadEvidence<ObservedRoute> beforeRoute, ReadEvidence<Tree> beforeTree,
            ReadEvidence<ObservedRoute> afterRoute, ReadEvidence<Tree> afterTree) {
        public StableCapture { Objects.requireNonNull(result); Objects.requireNonNull(binding); Objects.requireNonNull(beforeRoute); Objects.requireNonNull(beforeTree); Objects.requireNonNull(afterRoute); Objects.requireNonNull(afterTree); }
        public boolean routeStable() { return true; } public boolean nativePageRootAvailableBefore() { return true; } public boolean nativePageRootAvailableAfter() { return true; }
    }
    public static <T> StableCapture<T> stableCapture(T result, Binding beforeBinding, Binding afterBinding,
            ReadEvidence<ObservedRoute> beforeRoute, ReadEvidence<Tree> beforeTree, ReadEvidence<ObservedRoute> afterRoute, ReadEvidence<Tree> afterTree) {
        require(beforeBinding.equals(afterBinding), "CoA framebuffer crossed source binding");
        require(beforeRoute.value().source().equals(afterRoute.value().source()) && beforeRoute.value().route() == Route.COAT_OF_ARMS_DESIGNER && afterRoute.value().route() == Route.COAT_OF_ARMS_DESIGNER, "CoA framebuffer route changed");
        require(afterRoute.value().querySequence().compareTo(beforeRoute.value().querySequence()) > 0, "CoA framebuffer lacks fresh after-route observation");
        for (Tree tree : List.of(beforeTree.value(), afterTree.value())) require(tree.available() && tree.scopeRootName().equals("coat_of_arms_page"), "CoA framebuffer native page root unavailable");
        require(beforeRoute.value().source().binding().bridgePid() == beforeBinding.bridgePid() && beforeRoute.value().source().binding().connectionGeneration().equals(beforeBinding.connectionGeneration()), "framebuffer route and source identities differ");
        return new StableCapture<>(result, beforeBinding, beforeRoute, beforeTree, afterRoute, afterTree);
    }
    private static void independent(String mutationId, Instant submittedAt, ReadEvidence<?> after) { require(!after.requestId().equals(mutationId) && !after.observedAt().isBefore(submittedAt), "ACK cannot substitute for independent later observation"); }
}
