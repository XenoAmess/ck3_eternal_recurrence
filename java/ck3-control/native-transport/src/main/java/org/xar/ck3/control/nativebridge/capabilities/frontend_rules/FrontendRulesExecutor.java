package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.*;

/** Public typed frontend operations use the one guarded read coordinator and one action coordinator. */
public final class FrontendRulesExecutor {
    public record Context(String actionId, FrontendIdentity identity, G2Source source, Instant deadline) {
        public Context { Objects.requireNonNull(actionId); Objects.requireNonNull(identity); Objects.requireNonNull(source); Objects.requireNonNull(deadline);
            require(identity.frame() instanceof FrontendFrame.Menu && identity.machineId().equals(source.machineId()), "actual Menu/frontend source required"); }
        Context after(PlanningReadReceipt read) { return new Context(actionId, read.after().binding().origin().requireFrontend(), source, deadline); }
    }
    public sealed interface Execution permits Submitted, AlreadyObserved { }
    public record Submitted(ActionReceipt receipt) implements Execution { public Submitted { Objects.requireNonNull(receipt); } }
    public record AlreadyObserved(PlanningReadReceipt receipt) implements Execution { public AlreadyObserved { Objects.requireNonNull(receipt); } }
    public record CandidateRead(Candidate candidate, PlanningReadReceipt receipt, ExactRef originalReceipt) {
        public CandidateRead { Objects.requireNonNull(candidate); Objects.requireNonNull(receipt); Objects.requireNonNull(originalReceipt); }
    }
    private final FrontendRulesDefinitions definitions;
    private final FrontendRulesEffects effects;
    private final PlanningReadPort reads;
    private final ActionCoordinatorPort coordinator;
    public FrontendRulesExecutor(FrontendRulesInstaller installed, PlanningReadPort soleReads, ActionCoordinatorPort soleCoordinator, ActionPorts.OutcomeArchive sameArchive) {
        Objects.requireNonNull(installed); definitions = installed.definitions(); effects = installed.effects(); reads = Objects.requireNonNull(soleReads);
        coordinator = Objects.requireNonNull(soleCoordinator); Objects.requireNonNull(sameArchive);
    }
    public PlanningReadResult<RuleSelections> queryAppliedRules(Context context) { return read(definitions.appliedRules(), context); }
    public PlanningReadResult<RuleSelections> querySelections(Context context) { return read(definitions.selections(), context); }
    public PlanningReadResult<RuleWindow> queryWindow(Context context) { return read(definitions.window(), context); }
    public PlanningReadResult<ObservedRoute> queryRoute(Context context) { return read(definitions.route(), context); }
    public PlanningReadResult<GuiTree> inspectTree(Context context) { return read(definitions.tree(), context); }
    public PlanningReadResult<BookmarkModel> queryBookmarkModel(Context context) { return read(definitions.bookmark(), context); }
    public PlanningReadResult<LoadedFeaturesData.Observation> queryLoadedFeatures(PlanningReadRequest actualGameplayRequest) {
        require(actualGameplayRequest.origin() instanceof CommandOrigin.Gameplay, "loaded features require the actual paused gameplay origin");
        return reads.read(definitions.loadedFeatures(), actualGameplayRequest);
    }
    public CandidateRead querySelected1066Candidate(Context context, String exactCharacterKey) {
        var read = known(read(definitions.bookmark(), context));
        return new CandidateRead(read.value().selected(exactCharacterKey, false, true), read.receipt(), read.originalReceipt());
    }
    public Submitted selectRule(Context context, SelectRule request) {
        var selections = known(read(definitions.selections(), context)); context = context.after(selections.receipt());
        var window = known(read(definitions.window(), context)); context = context.after(window.receipt());
        var arguments = FrontendRulesArguments.selection(new FrontendRulesArguments.Select(request, selections.originalReceipt(), window.originalReceipt()));
        return submit(context, Primitive.SELECT_RULE, arguments);
    }
    public Submitted applyAndHideRules(Context context) { return closure(context, RulesAction.APPLY_AND_HIDE); }
    public Submitted hideRules(Context context) { return closure(context, RulesAction.HIDE); }
    private Submitted closure(Context context, RulesAction action) {
        var selections = known(read(definitions.selections(), context)); context = context.after(selections.receipt());
        var window = known(read(definitions.window(), context)); context = context.after(window.receipt());
        var arguments = FrontendRulesArguments.closure(new FrontendRulesArguments.Closure(action, selections.originalReceipt(), window.originalReceipt()));
        return submit(context, action == RulesAction.HIDE ? Primitive.HIDE_RULES : Primitive.APPLY_HIDE_RULES, arguments);
    }
    public Execution openRules(Context context) {
        var selections = known(read(definitions.selections(), context));
        if (selections.value().ready()) return new AlreadyObserved(selections.receipt());
        return route(context.after(selections.receipt()), Primitive.OPEN_RULES, false);
    }
    public Submitted newGame(Context context) { return route(context, Primitive.NEW_GAME, false); }
    public Submitted pickAnyCharacter(Context context) { return route(context, Primitive.PICK_ANY, false); }
    public Submitted rulerDesigner(Context context) { return route(context, Primitive.RULER_DESIGNER, true); }
    public Submitted selectRandomPlayable(Context context) { return route(context, Primitive.SELECT_RANDOM, true); }
    public Execution selectSupported1066Bookmark(Context context) {
        var model = known(read(definitions.bookmark(), context));
        if (model.value().supported1066BookmarkSelected()) return new AlreadyObserved(model.receipt());
        return route(context.after(model.receipt()), Primitive.SELECT_1066_BOOKMARK, false);
    }
    public Execution selectSupported1066Character(Context context, String exactCharacterKey) {
        var model = known(read(definitions.bookmark(), context)); var candidate = model.value().selected(exactCharacterKey, false, false);
        if (model.value().selectedIndex() == model.value().targetIndex()) return new AlreadyObserved(model.receipt());
        context = context.after(model.receipt());
        return submit(context, Primitive.SELECT_1066, FrontendRulesArguments.model(new FrontendRulesArguments.ModelInput(candidate.characterNameKey(), model.originalReceipt(), false)));
    }
    private Submitted route(Context context, Primitive primitive, boolean targetTree) {
        var route = known(read(definitions.route(), context)); context = context.after(route.receipt()); Optional<ExactRef> tree = Optional.empty();
        if (targetTree) { var observed = known(read(definitions.tree(), context)); context = context.after(observed.receipt()); tree = Optional.of(observed.originalReceipt()); }
        return submit(context, primitive, FrontendRulesArguments.route(new FrontendRulesArguments.RouteInput(route.originalReceipt(), tree)));
    }
    private Submitted submit(Context context, Primitive primitive, org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj arguments) {
        var expected = effects.expected(context.identity(), context.source(), primitive, arguments);
        var command = new ActionCommand(context.actionId(), new CommandOrigin.Frontend(context.identity()), context.source(), context.identity().frontendSessionId(),
                primitive.operation(), arguments, new CommandExpectation.Frontend(expected), new Claims(Set.of(), Set.of(), Set.of(), Set.of()), context.deadline());
        return new Submitted(coordinator.execute(command));
    }
    private <T> PlanningReadResult<T> read(ReadContract<T> contract, Context context) {
        return reads.read(contract, new PlanningReadRequest(new CommandOrigin.Frontend(context.identity()), context.source(), context.identity().frontendSessionId(),
                contract.operation(), FrontendRulesArguments.empty(), context.deadline()));
    }
    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> result) {
        if (result instanceof PlanningReadResult.Known<T> known) return known;
        throw new IllegalStateException("actual native frontend query unavailable; no action was submitted");
    }
}
