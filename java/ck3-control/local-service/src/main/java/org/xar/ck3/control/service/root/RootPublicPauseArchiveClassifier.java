package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.ExecutableStepBindings;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.g2.common.G2Source;

/** One installed public-pause source classifies only its own authenticated canonical controls. */
public final class RootPublicPauseArchiveClassifier {
    private final RootRuntimeContext context;
    private final RootExecutableBindings bindings;
    private final List<RootDomainInstallation> domains;
    private final RootPublicPauseRuntime.Installed publicPause;
    private final RootExecutableBindings.CompositeBinding composite;
    private final NativeRecordedEvidenceVerifier.Binding archived;

    private RootPublicPauseArchiveClassifier(RootRuntimeContext context,RootExecutableBindings bindings,
            List<RootDomainInstallation> domains,RootPublicPauseRuntime.Installed publicPause)throws IOException {
        this.context=Objects.requireNonNull(context);
        this.bindings=Objects.requireNonNull(bindings);
        this.domains=List.copyOf(domains);
        this.publicPause=Objects.requireNonNull(publicPause);
        publicPause.requireContext(context);
        var installation=publicPause.installation();
        require(installation.composites().size()==1&&installation.archived().size()==1,
                "public pause classification requires its complete single composite/replay installation");
        composite=installation.composites().getFirst();
        archived=installation.archived().getFirst();
        requireInventory();
    }

    /** Installation happens after inventory binding; no parsed DATA can construct an Installed issuer. */
    public static RootPublicPauseArchiveClassifier install(RootRuntimeContext context,RootExecutableBindings bindings,
            List<RootDomainInstallation> domains,RootPublicPauseRuntime.Installed publicPause)throws IOException {
        return new RootPublicPauseArchiveClassifier(context,bindings,domains,publicPause);
    }

    public RootPublicPauseRuntime.Installed publicPause(){return publicPause;}

    public void requireContext(RootRuntimeContext same)throws IOException {
        if(context!=Objects.requireNonNull(same))throw new IOException("public pause classifier crossed its actual context");
        publicPause.requireContext(same);
        requireInventory();
    }

    private void requireInventory()throws IOException {
        require(context.bindings()==bindings,
                "public pause classifier requires the identical bound Root inventory");
        require(domains.stream().filter(domain->domain==publicPause.installation()).count()==1,
                "public pause classifier requires its sole actual installed domain");
        require(bindings.compositeBindings().stream().filter(value->value==composite).count()==1
                &&composite.handler()==publicPause&&publicPause.handler()==publicPause
                &&RootPublicPauseRuntime.HANDLER.equals(composite.handler().handlerId())
                &&composite.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&composite.requiredCapability().isEmpty()
                &&composite.implementationSource().equals(publicPause.definitionSource()),
                "public pause classifier lost its identical handler, guard or source");
        require(archived.operation().equals(GenericPublicPauseRecovery.OPERATION)
                &&archived.definitionSource().equals(publicPause.definitionSource())
                &&bindings.actualArchivedVerifier(GenericPublicPauseRecovery.OPERATION).orElseThrow(
                        ()->new IOException("installed public pause archive replay is unavailable"))==archived,
                "public pause classifier lost its identical installed archive verifier");
        var sources=publicPause.historyProducerSources();
        require(sources.contains(composite.implementationSource())&&sources.contains(composite.decoderSource())
                &&sources.stream().allMatch(source->source.bytes()>0),
                "public pause classifier lost its actual runtime/algorithm source closure");
    }

    /** Metadata only. The canonical receipt must also pass verifyArchivedReceipt before use by planning. */
    public Optional<RootPlanningInputsFactory.Classification> classify(ActionCommand command)throws IOException {
        Objects.requireNonNull(command);
        if(!command.operation().equals(GenericPublicPauseRecovery.OPERATION))return Optional.empty();
        requireContext(context);
        requireParentContract(command,context.game().generation(),context.game().sessionId(),context.source());
        require(publicPause.matchesParent(command)&&bindings.requirePublicPauseAuthority(command)==publicPause,
                "public pause classification requires its identical private source authority");
        var installed=bindings.resolve(command.operation(),command.origin()).orElseThrow(
                ()->new IOException("public pause callable is not installed for this command origin"));
        require(installed.kind()==ExecutableStepBindings.Kind.COMPOSITE
                &&installed.implementationSource().equals(composite.implementationSource())
                &&installed.decoderSource().equals(composite.decoderSource()),
                "public pause classification crossed its actual callable/source pair");
        return Optional.of(new RootPlanningInputsFactory.SystemControl(
                RootPlanningInputsFactory.ControlKind.PUBLIC_PAUSE_CONTROL));
    }

    /** Deep replay uses the actual writer archive, never a callback supplied by a decoded report. */
    public void verifyArchivedReceipt(Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive originals)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(receipt);Objects.requireNonNull(originals);
        require(classify(receipt.command()).isPresent(),"only the exact installed public pause may use its archive classifier");
        context.writer().requireSession(same);
        require(originals instanceof NativeOutcomeArchive nativeArchive&&nativeArchive.writer()==context.writer(),
                "public pause planning requires its actual native writer archive");
        // Rebinding checks the supplied archive's held Session as well as its writer/store identity.
        var supplied=originals.withSession(same);
        var canonical=context.archive().withSession(same);
        var head=same.head();
        var retained=ContinuityActionJournal.lookup(head.state(),receipt.command().actionId(),canonical).orElseThrow(
                ()->new IOException("public pause planning receipt has no canonical history membership"));
        require(retained.equals(receipt)
                &&supplied.receiptReferenceOf(receipt).equals(canonical.receiptReferenceOf(retained)),
                "public pause planning replaced its canonical receipt or original archive identity");
        publicPause.verifyArchivedReceipt(same,retained,canonical);
        context.writer().requireSession(same);
        require(same.head().equals(head),"public pause archive classification changed the original writer head");
    }

    /** Strict contract validation is shared by the live classifier and pure wrong-scope regressions. */
    static void requireParentContract(ActionCommand command,GameGeneration game,String session,G2Source source) {
        Objects.requireNonNull(command);Objects.requireNonNull(game);Objects.requireNonNull(session);Objects.requireNonNull(source);
        require(command.origin() instanceof CommandOrigin.Gameplay&&command.origin().game().equals(game)
                &&command.sessionId().equals(session)&&command.source().equals(source),
                "public pause control crossed its actual gameplay Game/session/source");
        GenericPublicPauseRecovery.validateParent(command);
    }

    /** A decoded terminal is still DATA; only the same installed verifier above authenticates its originals. */
    public static void requireSettledReceipt(ActionReceipt receipt) {
        Objects.requireNonNull(receipt);
        GenericPublicPauseRecovery.validateParent(receipt.command());
        require(receipt.settled()&&!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                "an unresolved public pause blocks ordinary actions and grants no gameplay/day/SAVE credit");
        require(receipt.state() instanceof ActionState.CompositeSettled,
                "public pause requires its original canonical composite terminal");
        var terminal=(ActionState.CompositeSettled)receipt.state();
        require(RootPublicPauseRuntime.HANDLER.equals(terminal.execution().handlerId()),
                "public pause terminal changed its original installed handler");
        require(!terminal.execution().children().isEmpty()&&terminal.execution().children().size()<=2,
                "public pause terminal requires its original one or two reserved children");
        if(terminal.settlement() instanceof ActionState.ControlSequenceCompleted completed) {
            require(completed.observation().parent().equals(receipt.command())
                    &&receipt.command().expected().observerSchema().equals(ControlSequenceObservation.OBSERVER)
                    &&completed.observation().children().stream().map(child->
                        new org.xar.ck3.control.application.action.CompositeExecution.Child(child.actionId(),child.bodySha256()))
                            .toList().equals(terminal.execution().children()),
                    "public pause completion changed its original parent/result contract");
        }else if(terminal.settlement() instanceof ActionState.CompositeRejected rejected) {
            require(rejected.children().equals(terminal.execution().children())&&rejected.evidence().size()<=1,
                    "public pause rejection changed its finite canonical children/report");
        }else throw new IllegalArgumentException("public pause cannot borrow another composite settlement");
    }
}
