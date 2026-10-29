package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original full preflight -> one real move child -> independent lifecycle post. UNKNOWN never reaches another submit. */
public final class ArmyRetreatComposite implements CompositeActionPort {
    public static final String HANDLER = "java-active-combat-retreat/v1";
    public static final String SCHEMA = "xar.army-active-retreat-composite/v1";
    public static final String OBSERVER = "xar.army-active-retreat-operational-post/v1";
    public static final String MOVE_SCHEMA = "xar.army-active-retreat-move/v1";
    public static final String MOVE_OBSERVER = "xar.ck3.native-active-retreat-move-postcondition/v1";
    private static final String EVIDENCE = "xar.army-active-retreat-original-evidence/v1";
    private static final Pattern STEP = Pattern.compile("order-active-combat-retreat-v1-(0|[1-9][0-9]*)-revision-(0|[1-9][0-9]*)-combat-(?:0|-?[1-9][0-9]*)-side-[01]-scope-(?:full_side|owner_subset)-to-[1-9][0-9]*-token-[A-Za-z0-9_-]{32,128}");
    public record Plan(ActiveRetreatProposal.Order order, ExactRef originalPreviewDomain) { public Plan { Objects.requireNonNull(order); Objects.requireNonNull(originalPreviewDomain); } }
    @FunctionalInterface public interface ReadOnlyDeadline { Instant open(ActionCommand original, CompositeExecution retained); }
    private final ArmyRetreatDomain domain; private final ArmyRetreatFrames frames; private final ArmyBattleReads battles; private final ArmyRouteReads routes;
    private final java.util.function.Supplier<RootReadContractCatalog> catalog; private final ContinuityActionJournal journal;
    private final ActionPorts.OutcomeArchive archive; private final NativeEffectEvidence.FrameLoader frameLoader;
    public ArmyRetreatComposite(ArmyRetreatDomain soleDomain, ArmyRetreatFrames actualFrames, ArmyBattleReads actualBattleReads, ArmyRouteReads actualRouteReads,
            RootReadContractCatalog exactCatalog, ArmyRetreatService actualPosts, ContinuityActionJournal originalJournal,
            ActionPorts.OutcomeArchive sameArchive, NativeEffectEvidence.FrameLoader actualFrameLoader, ReadOnlyDeadline actualFreshLeaseReadDeadline) {
        this(soleDomain, actualFrames, actualBattleReads, actualRouteReads, () -> Objects.requireNonNull(exactCatalog), actualPosts, originalJournal, sameArchive, actualFrameLoader, actualFreshLeaseReadDeadline);
    }
    public ArmyRetreatComposite(ArmyRetreatDomain soleDomain, ArmyRetreatFrames actualFrames, ArmyBattleReads actualBattleReads, ArmyRouteReads actualRouteReads,
            java.util.function.Supplier<RootReadContractCatalog> actualCatalog, ArmyRetreatService actualPosts, ContinuityActionJournal originalJournal,
            ActionPorts.OutcomeArchive sameArchive, NativeEffectEvidence.FrameLoader actualFrameLoader, ReadOnlyDeadline actualFreshLeaseReadDeadline) {
        domain = Objects.requireNonNull(soleDomain); frames = Objects.requireNonNull(actualFrames); battles = Objects.requireNonNull(actualBattleReads); routes = Objects.requireNonNull(actualRouteReads);
        catalog = Objects.requireNonNull(actualCatalog); Objects.requireNonNull(actualPosts); journal = Objects.requireNonNull(originalJournal); archive = Objects.requireNonNull(sameArchive); frameLoader = Objects.requireNonNull(actualFrameLoader);
        Objects.requireNonNull(actualFreshLeaseReadDeadline);
    }
    @Override public String handlerId() { return HANDLER; }
    public static boolean handles(OperationKey operation) { return STEP.matcher(operation.value()).matches(); }
    @Override public boolean supports(OperationKey operation) { return handles(operation); }
    /** Root invokes after the fresh initial guard and before the parent intent, inside the same existing writer callback. */
    public void prepareIntent(ContinuityStorePort.Session session, ActionCommand command) {
        require(supports(command.operation()), "not a registered retreat parent"); Plan plan = decode(command); try {
            var prior = domain.read(session); require(prior.original().reference().payload().equals(plan.originalPreviewDomain()), "retreat original domain changed before its atomic claim");
            ArmyRetreatOrders.matches(prior.state(), plan.order()); var actual = frames.current(command.deadline()); bind(command, plan, actual);
            domain.apply(session, new ActiveRetreatState.StartOrder(plan.order()), new ArmyRetreatDomain.Proof(actual.actual(), actual.actual(), List.of(), Optional.empty()));
        } catch (IOException error) { throw new UncheckedIOException(error); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("retreat preparation interrupted before native submission; retained claim is never replayed", interrupted); }
    }
    /** One registered move operation delegates ordinary requests unchanged and admits the explicit retreat branch only. */
    public ActionPorts.PreparationPort movePreparation(ActionPorts.PreparationPort ordinaryMoveProducer) {
        Objects.requireNonNull(ordinaryMoveProducer); return new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) { return prepare(journal.borrowedWriterSession(), command, RequestIds.forActionBody(ActionCodec.bodySha256(command))); }
            @Override public NativeRequest prepare(ContinuityStorePort.Session session, ActionCommand command, String requestId) {
                if (!command.expected().observerSchema().equals(MOVE_OBSERVER)) return ordinaryMoveProducer.prepare(session, command, requestId);
                var child = ArmyRetreatMoveRequest.decode(command.arguments()); var order = child.order(); var plan = new Plan(order, child.previewBody());
                require(command.operation().value().equals(moveStep(order)) && command.expected().values().equals(moveValues(order)), "retreat child native step/expected fields changed");
                try {
                    require(domain.read(session).state().pending().equals(Optional.of(order)), "retreat child lacks its original atomic durable claim"); ArmyRetreatOrders.matches(originalState(plan, archive.withSession(session)), order);
                    var current = frames.current(command.deadline()); require(current.actual().identity().equals(command.before()) && current.source().equals(order.source()), "retreat child frame changed before its one native write");
                    ArmyRetreatFrames.selected(current, new PublicUnitId(order.arguments().selectedPublicCunitId()));
                } catch (IOException error) { throw new UncheckedIOException(error); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("retreat child preparation interrupted before native write", interrupted); }
                return new NativeRequest(command.operation().value(), Optional.of("game.command.move-army-N-to-N"), new RawJson(new byte[]{'{','}'}));
            }
        };
    }
    @Override public void validate(ActionCommand parent) {
        Plan plan = decode(parent); try {
            var session = journal.borrowedWriterSession(); var actual = frames.current(parent.deadline()); bind(parent, plan, actual);
            require(domain.read(session).state().pending().equals(Optional.of(plan.order())), "retreat parent has no matching original atomic pending claim");
            ArmyRetreatOrders.matches(originalState(plan, archive.withSession(session)), plan.order());
        } catch (IOException error) { throw new UncheckedIOException(error); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("retreat original validation interrupted", interrupted); }
    }
    @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) throws InterruptedException {
        Plan plan = decode(parent); var session = journal.borrowedWriterSession(); var boundArchive = archive.withSession(session);
        try {
            var start = frames.current(parent.deadline()); bind(parent, plan, start); Obj preview = originalState(plan, boundArchive).preview().orElseThrow();
            ArmyRetreatOrders.matches(originalState(plan, boundArchive), plan.order());
            var control = battles.read(session, Objects.requireNonNull(catalog.get()), new ArmyBattleReads.Selection(new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, revision(start), new PublicUnitId(plan.order().arguments().selectedPublicCunitId())), start.context()));
            var normalized = ArmyRetreatPreview.requireControl(control); require(normalized.originalFrame().equals(preview.get("battle_control_snapshot")), "entire original normalized battle control changed before retreat submit");
            require(normalized.retreat().status() == Availability.AVAILABLE && normalized.retreat().legalNow(), "native retreat legality changed before submit");
            var route = routes.read(session, Objects.requireNonNull(catalog.get()), new ArmyRouteReads.Selection(start.context(), normalized.selected(), normalized.combatProvince(), new PositiveId(plan.order().arguments().targetProvinceId())));
            Obj target = OpportunityJson.object(preview.get("target_preview"), "original target preview");
            ObjectNode oldRoute = ArmyJson.object(OpportunityJson.toNode(target)).deepCopy(); oldRoute.remove(List.of("status", "unavailable_reason", "provenance", "candidate_token", "order_step"));
            require(route.value().canonical().equals(DriverJson.object(ArmyJson.bytes(oldRoute), DriverJson.MAX_NATIVE_BYTES)), "entire original canonical native route changed before submit");
            var beforeSubmit = frames.current(parent.deadline()); ArmyRetreatFrames.same(start, beforeSubmit); bind(parent, plan, beforeSubmit);
            var operation = new OperationKey(moveStep(plan.order())); var expected = new ExpectedPostcondition(1, beforeSubmit.actual().identity(), parent.source(), MOVE_OBSERVER, moveValues(plan.order()));
            var args = new ArmyRetreatMoveRequest(plan.order(), plan.originalPreviewDomain(), List.of(boundArchive.readReferenceOf(control.receipt()), boundArchive.readReferenceOf(route.receipt()))).encode();
            var child = new ActionCommand(children.nextActionId(), beforeSubmit.actual().identity(), parent.source(), parent.sessionId(), operation,
                    args, expected, parent.claims(), parent.deadline());
            ActionReceipt originalChild = children.submit(child);
            if (originalChild.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected rejected)
                return new ActionPorts.CompositeRejectionObserved(rejected.reason(), List.of(new CompositeExecution.Child(originalChild.command().actionId(), originalChild.bodySha256())));
            if (originalChild.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED) return new ActionPorts.Pending("original retreat move child is rejected or unresolved; no following mutation or retry", List.of(boundArchive.preserveReceipt(originalChild)));
            return completeFromChild(session,parent,plan,originalChild,boundArchive);
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    /** A retained parent can only read the original child and lifecycle. There is no submitter in this branch. */
    @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) {
        try {
            var session = journal.borrowedWriterSession(); var boundArchive = archive.withSession(session); Plan plan = decode(parent);
            require(retained.handlerId().equals(HANDLER) && retained.children().size() == 1, "retreat reconciliation requires its one original move child");
            var childKey = retained.children().getFirst(); var child = ContinuityActionJournal.lookup(session.head().state(), childKey.actionId(), boundArchive).orElseThrow();
            require(child.bodySha256().equals(childKey.bodySha256()) && child.command().operation().value().equals(moveStep(plan.order())), "original retreat child identity changed");
            if (child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected rejected)
                return new ActionPorts.CompositeRejectionObserved(rejected.reason(), List.of(childKey));
            if (child.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED) return new ActionPorts.Pending("original retreat move remains unresolved or rejected; no replay", List.of(boundArchive.preserveReceipt(child)));
            var current = domain.read(session);
            if (current.state().pending().isEmpty()) return new ActionPorts.Pending("retreat post already consumed by another original observer; original retained proof must be restored, never resubmit", List.of(current.original().reference().payload()));
            return completeFromChild(session,parent,plan,child,boundArchive);
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    /** The shared coordinator reconciles the original primitive first. A parent only consumes that child's retained evidence. */
    private ActionPorts.PostconditionResult completeFromChild(ContinuityStorePort.Session session,ActionCommand parent,Plan plan,ActionReceipt child,ActionPorts.OutcomeArchive originalArchive)throws IOException {
        var post=retainedChildPost(plan,child,originalArchive);
        if(post.result() instanceof ActiveRetreatPost.Observed) {
            var state=domain.read(session).state();
            var attempt=Optional.of(new ActiveRetreatState.Attempt(ActiveRetreatState.AttemptKind.OBSERVE,post.current().source()));
            if(!state.lastAttempt().equals(attempt))domain.apply(session,new ActiveRetreatState.StartObserve(post.current().source()),
                    new ArmyRetreatDomain.Proof(post.current().actual(),post.current().actual(),List.of(),Optional.of(child)));
        }
        return complete(parent,plan,child,post,originalArchive);
    }
    private ArmyRetreatService.CollectedPost retainedChildPost(Plan plan,ActionReceipt child,ActionPorts.OutcomeArchive originalArchive) {
        require(child.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&child.command().expected().observerSchema().equals(MOVE_OBSERVER),"retreat parent needs its independently observed original primitive");
        var request=ArmyRetreatMoveRequest.decode(child.command().arguments());
        require(request.order().equals(plan.order())&&request.previewBody().equals(plan.originalPreviewDomain()),"retreat child changed the original parent plan");
        var original=NativeEffectEvidence.load(child,originalArchive,frameLoader);var all=original.independentReads();
        require(all.size()>=3&&all.size()<=4&&all.subList(0,2).stream().map(originalArchive::readReferenceOf).toList().equals(request.preflightReads())
                &&original.supportingMaterials().equals(List.of(plan.originalPreviewDomain())),"retreat child omitted or changed its original preflight, preview or independent post custody");
        preflightVerifier().verify(request,original.frames().before(),all.subList(0,2),originalArchive);
        var reads=List.copyOf(all.subList(2,all.size()));
        var current=new ArmyRetreatFrames.Current(original.frames().after(),reads.getFirst().request().deadline());
        return new ArmyRetreatService.CollectedPost(current,ArmyRetreatDomain.post(plan.order(),current,reads),reads);
    }
    private ActionPorts.PostconditionResult complete(ActionCommand parent, Plan plan, ActionReceipt child, ArmyRetreatService.CollectedPost post, ActionPorts.OutcomeArchive archive) {
        if (!(post.result() instanceof ActiveRetreatPost.Observed)) return new ActionPorts.Pending("original retreat lifecycle is not independently complete", post.originals().stream().map(archive::readReferenceOf).toList());
        ObjectNode proof = StrictJson.object().put("schema", EVIDENCE).put("parent_body_sha256", ActionCodec.bodySha256(parent)); proof.set("preview_body", plan.originalPreviewDomain().toJson());
        var after = post.current().basis(); proof.set("after_native", after.nativeFrame().toJson()); proof.set("after_driver", after.driverFacts().toJson()); proof.set("child", archive.preserveReceipt(child).toJson());
        var reads = proof.putArray("reads"); post.originals().forEach(read -> reads.add(archive.readReferenceOf(read).toJson())); proof.set("result", OpportunityJson.toNode(post.result().json()));
        RawJson original = new RawJson(StrictJson.canonical(proof)); ExactRef evidence = archive.preserveMaterial(original); require(archive.loadMaterial(evidence).equals(original), "retreat independent proof archive changed");
        List<ExactRef> support = new ArrayList<>(List.of(evidence, plan.originalPreviewDomain(), after.nativeFrame(), after.driverFacts(), archive.receiptReferenceOf(child)));
        post.originals().forEach(read -> support.add(archive.readReferenceOf(read)));
        return new ActionPorts.EffectObserved(effect(parent, plan, post.current(), support.stream().distinct().toList()));
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey exactOperation, ExactRef actualSource) {
        require(supports(exactOperation), "not an exact retreat operation"); return new NativeRecordedEvidenceVerifier.Binding(exactOperation, actualSource, (head, receipt, originalArchive) -> {
            if (receipt.state() instanceof ActionState.CompositeSettled negative && negative.settlement() instanceof ActionState.CompositeRejected rejected) {
                Plan plan = decode(receipt.command()); require(receipt.command().operation().equals(exactOperation) && negative.execution().children().size() == 1 && rejected.children().equals(negative.execution().children()), "retreat rejection must retain its one exact original child");
                var key = rejected.children().getFirst(); var child = ContinuityActionJournal.lookup(head.state(), key.actionId(), originalArchive).orElseThrow();
                require(child.bodySha256().equals(key.bodySha256()) && child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected, "retreat rejection has no actual canonical native rejection");
                var request = ArmyRetreatMoveRequest.decode(child.command().arguments()); require(request.order().equals(plan.order()) && request.previewBody().equals(plan.originalPreviewDomain()), "rejected child changed original retreat plan");
                ArmyRetreatDomain.submission(plan.order(), child); ActionEffects.validateComposite(receipt.command(), negative.execution(), rejected); ActionEffects.validateCompositeChildren(negative.execution(), rejected, List.of(child)); return;
            }
            require(receipt.command().operation().equals(exactOperation) && receipt.state() instanceof ActionState.CompositeSettled settled && settled.settlement() instanceof ActionState.Applied, "retreat archived settlement is not the original complete composite");
            var settled = (ActionState.CompositeSettled) receipt.state(); var actual = ((ActionState.Applied) settled.settlement()).observation(); Plan plan = decode(receipt.command());
            require(actual.supportingEvidence().size() >= 6 && actual.supportingEvidence().size() <= 7, "retreat requires the complete explicit original proof closure");
            ObjectNode proof = StrictJson.object(StrictJson.parse(originalArchive.loadMaterial(actual.supportingEvidence().getFirst()).bytes()), Set.of("schema", "parent_body_sha256", "preview_body", "after_native", "after_driver", "child", "reads", "result"));
            require(StrictJson.text(proof.get("schema")).equals(EVIDENCE) && StrictJson.text(proof.get("parent_body_sha256")).equals(receipt.bodySha256()) && ExactRef.fromJson(proof.get("preview_body")).equals(plan.originalPreviewDomain()), "retreat proof crossed original parent/domain");
            ArmyRetreatOrders.matches(originalState(plan, originalArchive), plan.order());
            bind(receipt.command(), plan, new ArmyRetreatFrames.Current(RootGuardEvidence.loadFrame(settled.execution().guard(), originalArchive, frameLoader), receipt.command().deadline()));
            var child = originalArchive.loadReceipt(ExactRef.fromJson(proof.get("child"))); require(settled.execution().children().equals(List.of(new CompositeExecution.Child(child.command().actionId(), child.bodySha256())))
                    && ContinuityActionJournal.lookup(head.state(), child.command().actionId(), originalArchive).filter(child::equals).isPresent() && child.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "retreat proof lacks the canonical independently confirmed single child");
            ArmyRetreatDomain.submission(plan.order(), child);
            var childRequest = ArmyRetreatMoveRequest.decode(child.command().arguments()); var before = RootGuardEvidence.loadFrame(((ActionState.Settled) child.state()).attempt().guard(), originalArchive, frameLoader);
            preflightVerifier().verify(childRequest, before, childRequest.preflightReads().stream().map(originalArchive::loadRead).toList(), originalArchive);
            var after = frameLoader.load(new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(proof.get("after_native")), ExactRef.fromJson(proof.get("after_driver"))), originalArchive); var current = new ArmyRetreatFrames.Current(after, receipt.command().deadline());
            List<PlanningReadReceipt> reads = new ArrayList<>(); require(proof.get("reads").isArray() && proof.get("reads").size() >= 1 && proof.get("reads").size() <= 2, "retreat proof needs finite actual lifecycle queries");
            for (var value : proof.get("reads")) { var read = originalArchive.loadRead(ExactRef.fromJson(value)); NativeRecordedEvidenceVerifier.requireRead(read, originalArchive); reads.add(read); }
            var childPost=retainedChildPost(plan,child,originalArchive);
            require(childPost.originals().equals(reads)&&childPost.current().basis().equals(current.basis()),"parent lifecycle proof is not the original primitive's retained independent post");
            require(actual.supportingEvidence().containsAll(List.of(plan.originalPreviewDomain(), ExactRef.fromJson(proof.get("after_native")), ExactRef.fromJson(proof.get("after_driver")), ExactRef.fromJson(proof.get("child"))))
                    && reads.stream().map(originalArchive::readReferenceOf).allMatch(actual.supportingEvidence()::contains), "retreat supporting material closure omitted an actual source");
            var replayed = childPost.result(); require(replayed instanceof ActiveRetreatPost.Observed && OpportunityJson.toNode(replayed.json()).equals(proof.get("result")), "retreat original lifecycle replay did not independently complete");
            require(actual.equals(effect(receipt.command(), plan, current, actual.supportingEvidence())), "retreat semantic effect differs from full original-evidence replay");
            ActionEffects.validateComposite(receipt.command(), settled.execution(), new ActionState.Applied(actual)); ActionEffects.validateCompositeChildren(settled.execution(), settled.settlement(), List.of(child));
        });
    }
    /** Close the sole domain after the canonical parent settlement; crash recovery reopens this same archived proof. */
    public ArmyRetreatDomain.Known commitApplied(ContinuityStorePort.Session session, ActionReceipt parent) throws IOException {
        var bound = archive.withSession(session); Plan plan = decode(parent.command());
        require(ContinuityActionJournal.lookup(session.head().state(), parent.command().actionId(), bound).filter(parent::equals).isPresent()
                && parent.state() instanceof ActionState.CompositeSettled settled && settled.settlement() instanceof ActionState.Applied, "domain completion requires its actual canonical applied parent");
        var state = domain.read(session); if (state.state().pending().isEmpty()) { require(state.state().claims().stream().anyMatch(c -> c.key().equals(ActiveRetreatState.ClaimKey.of(plan.order())) && c.status() == ActiveRetreatState.ClaimStatus.OPERATIONAL_OBSERVED), "cleared retreat domain lacks its original observed exclusion"); return state; }
        require(state.state().pending().equals(Optional.of(plan.order())), "applied retreat cannot replace another pending intent");
        var effect = ((ActionState.Applied) ((ActionState.CompositeSettled) parent.state()).settlement()).observation();
        var proof = ArmyJson.parse(bound.loadMaterial(effect.supportingEvidence().getFirst()).bytes());
        var after = frameLoader.load(new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(proof.get("after_native")), ExactRef.fromJson(proof.get("after_driver"))), bound); var current = new ArmyRetreatFrames.Current(after, parent.command().deadline());
        List<PlanningReadReceipt> reads = new ArrayList<>(); for (var value : proof.get("reads")) reads.add(bound.loadRead(ExactRef.fromJson(value)));
        var result = ArmyRetreatDomain.post(plan.order(), current, reads); require(result instanceof ActiveRetreatPost.Observed, "canonical retreat original post no longer replays");
        return domain.apply(session, new ActiveRetreatState.FinishObserve(current.source(), result), new ArmyRetreatDomain.Proof(after, after, reads, Optional.of(parent)));
    }
    public ArmyRetreatPreflightVerifier preflightVerifier() {
        return (request, before, reads, originalArchive) -> {
            require(reads.size() == 2 && reads.stream().map(originalArchive::readReferenceOf).toList().equals(request.preflightReads()), "retreat original preflight receipt identity/order changed");
            Plan plan = new Plan(request.order(), request.previewBody()); var prior = originalState(plan, originalArchive); ArmyRetreatOrders.matches(prior, plan.order());
            var current = new ArmyRetreatFrames.Current(before, reads.getFirst().request().deadline()); require(current.source().equals(plan.order().source()), "retreat preflight actual frame changed original source");
            for (var read : reads) {
                NativeRecordedEvidenceVerifier.requireRead(read, originalArchive);
                require(read.request().before().equals(before.identity()) && read.request().source().equals(before.source()) && read.request().sessionId().equals(before.sessionId()), "retreat preflight crossed actual original before frame");
                for (var guard : List.of(read.before(), read.after())) { var actual = RootGuardEvidence.loadFrame(guard.binding(), originalArchive, frameLoader); ArmyRetreatFrames.same(current, new ArmyRetreatFrames.Current(actual, current.deadline())); }
            }
            var first = reads.getFirst(); var c = readContext(first); var input = new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, new ArmyCalls.Revision(new Present<>(c.before().frame().revision())), new PublicUnitId(plan.order().arguments().selectedPublicCunitId()));
            var control = (ArmyBattleReads.Control) ArmyBattleReads.decode(new ArmyBattleReads.Selection(input, c), first); Obj preview = prior.preview().orElseThrow();
            require(control.normalized().equals(preview.get("battle_control_snapshot")) && control.value().retreat().status() == Availability.AVAILABLE && control.value().retreat().legalNow(), "retreat full original control/legality requery changed");
            var second = reads.getLast(); var route = ArmyRouteReads.decode(new ArmyRouteReads.Selection(readContext(second), input.army(), control.value().combatProvince(), new PositiveId(plan.order().arguments().targetProvinceId())), second);
            var target = ArmyJson.object(OpportunityJson.toNode(preview.get("target_preview"))).deepCopy(); target.remove(List.of("status", "unavailable_reason", "provenance", "candidate_token", "order_step"));
            require(route.canonical().equals(DriverJson.object(ArmyJson.bytes(target), DriverJson.MAX_NATIVE_BYTES)), "retreat exact original route requery changed");
        };
    }
    /** Derived admission is reachable only from the shared Root guard after a real durable parent reserved this child. */
    public RootActionGuard.DerivedChildAdmission derivedAdmission() {
        return (session, head, child, lease, definition, sameArchive) -> {
            require(session.head().digest().equals(head.digest()) && definition.kind() == ExecutableStepBindings.Kind.ACTION && definition.operation().equals(child.operation())
                    && definition.requiredCapability().equals(Optional.of("game.command.move-army-N-to-N")) && child.expected().observerSchema().equals(MOVE_OBSERVER), "retreat derived admission crossed original writer or installed primitive definition");
            var request = ArmyRetreatMoveRequest.decode(child.arguments()); var plan = new Plan(request.order(), request.previewBody());
            require(child.operation().value().equals(moveStep(plan.order())) && child.expected().values().equals(moveValues(plan.order())) && child.before().equals(lease.frame().identity()), "retreat derived child changed its exact native step/expectation/current frame");
            var current = domain.read(session); require(current.state().pending().equals(Optional.of(plan.order())) && current.state().claims().stream().anyMatch(claim -> claim.key().equals(ActiveRetreatState.ClaimKey.of(plan.order())) && claim.status() == ActiveRetreatState.ClaimStatus.SUBMITTING), "retreat derived child lacks its original unconsumed atomic pending claim");
            var childKey = new CompositeExecution.Child(child.actionId(), ActionCodec.bodySha256(child));
            List<ActionReceipt> parents = ContinuityActionJournal.receipts(head.state(), sameArchive).stream().filter(receipt -> receipt.state() instanceof ActionState.CompositeRunning running
                    && running.execution().handlerId().equals(HANDLER) && running.execution().children().equals(List.of(childKey))).toList();
            require(parents.size() == 1, "retreat derived child has no unique actual durable reserved parent"); var parent = parents.getFirst(); var running = ((ActionState.CompositeRunning) parent.state()).execution(); var originalPlan = decode(parent.command());
            require(originalPlan.equals(plan) && parent.command().source().equals(child.source()) && parent.command().sessionId().equals(child.sessionId())
                    && parent.command().claims().equals(child.claims()) && !child.deadline().isAfter(parent.command().deadline()), "retreat derived primitive crossed its original parent source/claims/deadline");
            bind(parent.command(), plan, new ArmyRetreatFrames.Current(RootGuardEvidence.loadFrame(running.guard(), sameArchive, frameLoader), parent.command().deadline()));
            List<PlanningReadReceipt> reads = request.preflightReads().stream().map(sameArchive::loadRead).toList(); preflightVerifier().verify(request, lease.frame(), reads, sameArchive);
            var basis = NativeEffectEvidence.basis(lease.frame()); var proof = new ArmyDerivedAdmissionEvidence(head.state().sequence(),head.digest(), childKey.bodySha256(), parent.bodySha256(), sameArchive.preserveReceipt(parent), current.original().reference().payload(), plan.originalPreviewDomain(), request.preflightReads(), basis.nativeFrame(), basis.driverFacts());
            RawJson original = proof.encode(); ExactRef result = sameArchive.preserveMaterial(original); require(original.equals(sameArchive.loadMaterial(result)), "actual derived-child proof archive changed"); return result;
        };
    }
    /** Cold replay reads the real writer event chain; a detached CAS state can never establish an old submitting claim. */
    public NativeRecordedEvidenceVerifier.DerivedGuardVerifier derivedGuardVerifier() {
        return (actualHead,child,guard,sameArchive) -> {
            try {
                var same = journal.borrowedWriterSession(); require(same.head().digest().equals(actualHead.digest()),"derived replay crossed its actual locked writer Head");
                var proof = ArmyDerivedAdmissionEvidence.requireGuard(guard,sameArchive);
                require(child.bodySha256().equals(proof.childBodySha256()) && child.bodySha256().equals(ActionCodec.bodySha256(child.command()))
                        && ActionTransitions.attempt(child.state()).map(attempt -> attempt.guard().equals(guard)).orElse(false),"derived replay guard is not the actual exact child attempt");
                var historical = same.requireHistoricalState(proof.actualHeadSequence(),proof.actualHeadDigest());
                var originalDomain = org.xar.ck3.control.continuity.writer.DomainBodies.reference(historical,org.xar.ck3.control.continuity.writer.DomainBodies.Slot.ACTIVE_RETREAT).orElseThrow(() -> new IllegalArgumentException("canonical historical writer Head has no retreat domain"));
                require(originalDomain.payload().equals(proof.currentDomain()) && originalDomain.contractSchema().equals(ActiveRetreatState.SCHEMA),"derived submitting claim is not the historical canonical domain body");
                var request = ArmyRetreatMoveRequest.decode(child.command().arguments()); var plan = new Plan(request.order(),request.previewBody());
                require(request.previewBody().equals(proof.previewBody()) && request.preflightReads().equals(proof.preflightReads()) && child.command().operation().value().equals(moveStep(plan.order()))
                        && child.command().expected().observerSchema().equals(MOVE_OBSERVER) && child.command().expected().values().equals(moveValues(plan.order())),"derived child changed its original request/expectation");
                var state = ActiveRetreatState.decode(DriverJson.object(sameArchive.loadMaterial(proof.currentDomain()).bytes(),ContinuityJson.DOMAIN_MAX_BYTES));
                require(state.pending().equals(Optional.of(plan.order())) && state.claims().stream().anyMatch(claim -> claim.key().equals(ActiveRetreatState.ClaimKey.of(plan.order())) && claim.status() == ActiveRetreatState.ClaimStatus.SUBMITTING),"canonical historical retreat claim is not submitting this exact order");
                var parent = sameArchive.loadReceipt(proof.parentReceipt()); ContinuityActionJournal.requireHistoricalReceipt(historical,parent,sameArchive); ContinuityActionJournal.requireHistoricalReceipt(actualHead.state(),parent,sameArchive);
                var running = ((ActionState.CompositeRunning)parent.state()).execution();
                require(running.handlerId().equals(HANDLER) && running.children().equals(List.of(new CompositeExecution.Child(child.command().actionId(),child.bodySha256()))) && decode(parent.command()).equals(plan)
                        && parent.command().source().equals(child.command().source()) && parent.command().sessionId().equals(child.command().sessionId()) && parent.command().claims().equals(child.command().claims()) && !child.command().deadline().isAfter(parent.command().deadline()),"historical canonical parent did not reserve this exact derived child");
                var before = frameLoader.load(new NativeEffectEvidence.FrameBasis(proof.beforeNative(),proof.beforeDriver()),sameArchive);
                require(before.identity().equals(child.command().before()) && before.source().equals(child.command().source()) && before.sessionId().equals(child.command().sessionId()),"derived original before frame/source changed");
                ArmyRetreatFrames.same(new ArmyRetreatFrames.Current(before,child.command().deadline()),new ArmyRetreatFrames.Current(RootGuardEvidence.loadFrame(guard,sameArchive,frameLoader),child.command().deadline()));
                bind(parent.command(),plan,new ArmyRetreatFrames.Current(RootGuardEvidence.loadFrame(running.guard(),sameArchive,frameLoader),parent.command().deadline()));
                preflightVerifier().verify(request,before,request.preflightReads().stream().map(sameArchive::loadRead).toList(),sameArchive);
                require(same.head().digest().equals(actualHead.digest()),"derived replay mutated or crossed its actual canonical writer Head");
            } catch(IOException failure) { throw new UncheckedIOException("actual canonical historical retreat qualification unavailable",failure); }
        };
    }
    private static Context readContext(PlanningReadReceipt receipt) { var request = receipt.request(); return new Context(request.before(), request.source(), request.sessionId(), request.deadline()); }
    public static ActionCommand command(String actionId, ArmyRetreatFrames.Current before, Plan plan) {
        var args = StrictJson.object().put("schema", SCHEMA); args.set("order", OpportunityJson.toNode(ActiveRetreatState.order(plan.order()))); args.set("preview_body", plan.originalPreviewDomain().toJson());
        var a = plan.order().arguments(); Scope scope = a.expectedScope() == org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Scope.FULL_SIDE ? Scope.FULL_SIDE : Scope.OWNER_SUBSET;
        var operation = new OperationKey(ArmyRetreatPreview.orderStep(new PublicUnitId(a.selectedPublicCunitId()), a.expectedRevision(), new FullId(a.expectedCombatId()), a.expectedSideIndex(), scope, new PositiveId(a.targetProvinceId()), a.candidateToken()));
        var expected = new ExpectedPostcondition(1, before.actual().identity(), before.actual().source(), OBSERVER, values(plan.order()));
        Claims claims = new Claims(plan.order().affectedInStoredOrder().stream().map(BigInteger::valueOf).collect(java.util.stream.Collectors.toSet()), Set.of(), Set.of(), Set.of());
        return new ActionCommand(actionId, before.actual().identity(), before.actual().source(), before.actual().sessionId(), operation, DriverJson.object(StrictJson.canonical(args), ActionCommand.MAX_ARGUMENT_BYTES), expected, claims, before.deadline());
    }
    public static Plan decode(ActionCommand command) {
        ObjectNode args = StrictJson.object(OpportunityJson.toNode(command.arguments()), Set.of("schema", "order", "preview_body")); require(StrictJson.text(args.get("schema")).equals(SCHEMA), "exact retreat parent argument schema required");
        Plan plan = new Plan(ActiveRetreatState.order(DriverJson.object(StrictJson.canonical(args.get("order")), ActionCommand.MAX_ARGUMENT_BYTES)), ExactRef.fromJson(args.get("preview_body")));
        return validateDecoded(command, plan);
    }
    private static Plan validateDecoded(ActionCommand command, Plan plan) {
        var a = plan.order().arguments(); Scope scope = a.expectedScope() == org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Scope.FULL_SIDE ? Scope.FULL_SIDE : Scope.OWNER_SUBSET;
        require(command.operation().value().equals(ArmyRetreatPreview.orderStep(new PublicUnitId(a.selectedPublicCunitId()), a.expectedRevision(), new FullId(a.expectedCombatId()), a.expectedSideIndex(), scope, new PositiveId(a.targetProvinceId()), a.candidateToken()))
                && command.expected().observerSchema().equals(OBSERVER) && command.expected().values().equals(values(plan.order())), "retreat parent step/expected contract changed"); return plan;
    }
    private static void bind(ActionCommand parent, Plan plan, ArmyRetreatFrames.Current current) {
        require(current.actual().identity().equals(parent.before()) && current.actual().source().equals(parent.source()) && current.actual().sessionId().equals(parent.sessionId()) && current.source().equals(plan.order().source()), "retreat source changed before submit");
        ArmyRetreatFrames.selected(current, new PublicUnitId(plan.order().arguments().selectedPublicCunitId()));
        require(parent.claims().armyIds().containsAll(plan.order().affectedInStoredOrder().stream().map(BigInteger::valueOf).toList()), "retreat parent omitted an affected original army claim");
    }
    private static ActiveRetreatState.State originalState(Plan plan, ActionPorts.OutcomeArchive archive) { return ActiveRetreatState.decode(DriverJson.object(archive.loadMaterial(plan.originalPreviewDomain()).bytes(), ContinuityJson.DOMAIN_MAX_BYTES)); }
    private static ArmyCalls.Revision revision(ArmyRetreatFrames.Current current) { return new ArmyCalls.Revision(new Present<>(current.context().before().frame().revision())); }
    private static String moveStep(ActiveRetreatProposal.Order order) { return "move-army-" + order.arguments().selectedPublicCunitId() + "-to-" + order.arguments().targetProvinceId(); }
    private static List<ExpectedValue> moveValues(ActiveRetreatProposal.Order order) { return List.of(new ExpectedInteger(new FieldKey("army_id"), BigInteger.valueOf(order.arguments().selectedPublicCunitId())), new ExpectedInteger(new FieldKey("target_province_id"), BigInteger.valueOf(order.arguments().targetProvinceId())), new ExpectedBoolean(new FieldKey("retreat_order_observed"), true)); }
    private static List<ExpectedValue> values(ActiveRetreatProposal.Order order) {
        return List.of(new ExpectedInteger(new FieldKey("selected_public_cunit_id"), BigInteger.valueOf(order.arguments().selectedPublicCunitId())), new ExpectedInteger(new FieldKey("combat_id"), BigInteger.valueOf(order.arguments().expectedCombatId())),
                new ExpectedInteger(new FieldKey("target_province_id"), BigInteger.valueOf(order.arguments().targetProvinceId())), new ExpectedText(new FieldKey("scope"), order.arguments().expectedScope().wire()), new ExpectedBoolean(new FieldKey("operational_retreat_verified"), true));
    }
    private static ActionState.EffectObservation effect(ActionCommand parent, Plan plan, ArmyRetreatFrames.Current current, List<ExactRef> supporting) {
        List<ExpectedValue> actual = new ArrayList<>(values(plan.order())); actual.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true)); actual.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), false)); actual.add(new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), false)); actual.add(new ExpectedBoolean(new FieldKey("command_causation_verified"), false));
        var after = current.actual(); return new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), OBSERVER, actual, NativeEffectSnapshots.publication(after), after.observedAt(), after.originalEvidence(), supporting);
    }
}
